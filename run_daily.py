# -*- coding: utf-8 -*-
"""A股每日市场情绪日报 · 一键生成脚本
================================================
把「龙虎榜 + 题材热点 + 行业轮动」整条数据流水线串成一条命令，
自动按交易日抓取真实行情并产出单文件离线 HTML。

用法（在 workspace 根目录执行）:
  python run_daily.py                  # 自动取最近交易日（今天；若为周末则回退到周五）
  python run_daily.py --date 2026-08-07   # 指定交易日
  python run_daily.py --only-report     # 已有数据，仅重新渲染 HTML（不抓取）
  python run_daily.py --refresh-ref     # 强制刷新行业映射 / 流通市值等参考库
  python run_daily.py --skip-bj         # 跳过北交所(新浪)补齐，跑得更快

依赖:
  - 虚拟环境 C:/Users/Admin/.workbuddy/binaries/python/envs/default
    （需含 requests、mootdx；已预装）
  - 网络：通达信 TCP(7709, mootdx)、东方财富、同花顺、新浪、腾讯
  - 可用 PYTHON_BIN 环境变量覆盖解释器路径

输出:
  output/A股市场情绪日报_<YYYY-MM-DD>.html
"""
import argparse, os, sys, subprocess, json, datetime, time

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
SCRIPTS = os.path.join(ROOT, "scripts")
OUTDIR = os.path.join(ROOT, "output")
PY = os.environ.get(
    "PYTHON_BIN",
    r"C:/Users/Admin/.workbuddy/binaries/python/envs/default/Scripts/python.exe",
)


def log(*a):
    print(*a, flush=True)


def last_trading_day(d=None):
    """最近交易日：默认今天，遇周末回退到周五。"""
    d = d or datetime.date.today()
    while d.weekday() >= 5:  # 5=周六 6=周日
        d -= datetime.timedelta(days=1)
    return d


def run(script, env_extra=None, label=""):
    """用虚拟环境 python 跑一个子脚本，继承并追加环境变量。"""
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    cmd = [PY, os.path.join(SCRIPTS, script)]
    log(f"\n>>> [{label or script}] {script}")
    t0 = time.time()
    p = subprocess.run(cmd, cwd=ROOT, env=env)
    log(f"<<< {script} 退出码 {p.returncode}  用时 {time.time() - t0:.0f}s")
    return p.returncode == 0


def ref_stale():
    """参考库（行业映射/市值）超过 7 天视为过期需刷新。"""
    f = os.path.join(DATA, "stock_industry.json")
    if not os.path.exists(f):
        return True
    return (time.time() - os.path.getmtime(f)) > 7 * 86400


def latest_series_date():
    """从 series.json 采样找出最新交易日，用作板块还原精度校验基准日。"""
    p = os.path.join(DATA, "series.json")
    if not os.path.exists(p):
        return None
    try:
        d = json.load(open(p, encoding="utf-8")).get("series", {})
        dates = set()
        for v in list(d.values())[:300]:
            dates.update(v.get("d", []))
        return max(dates) if dates else None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description="A股每日市场情绪日报生成器")
    ap.add_argument("--date", help="交易日 YYYY-MM-DD，缺省=最近交易日")
    ap.add_argument("--only-report", action="store_true",
                    help="跳过抓取，仅用已有数据重新渲染 HTML")
    ap.add_argument("--refresh-ref", action="store_true",
                    help="强制刷新参考库（行业映射 / 流通市值）")
    ap.add_argument("--skip-bj", action="store_true",
                    help="跳过北交所(新浪)补齐，速度更快但全市场样本不含北交所")
    ap.add_argument("--notify", action="store_true",
                    help="生成后推送个人微信/163邮箱（需 notify_config.json）")
    args = ap.parse_args()

    date = args.date or last_trading_day().strftime("%Y-%m-%d")
    key = date.replace("-", "")
    log(f"目标交易日: {date}   (文件key={key})")

    # 参考库刷新策略
    if not args.only_report:
        if args.refresh_ref or ref_stale():
            run("fetch_industry_map.py", label="参考库-行业映射")
            run("fetch_tencent_mcap.py", label="参考库-流通市值")
        else:
            log("\n* 参考库较新，跳过刷新（用 --refresh-ref 强制）")

        run("fetch_lhb_ths.py", env_extra={"REPORT_DATE": date},
            label="① 龙虎榜 + 同花顺题材")
        run("fetch_mootdx_series.py", label="② 全市场30日行情序列")
        run("compute_lhb.py", label="③ 龙虎榜按个股聚合")
        if not args.skip_bj:
            run("fetch_bj.py", env_extra={"REPORT_DATE": date},
                label="④ 北交所补齐(新浪)")

    # 板块计算需要 VERIFY_DATE（校验基准日，取序列里最新交易日）
    verify = latest_series_date() or "2026-08-07"
    env = {"REPORT_DATE": date, "VERIFY_DATE": verify}

    ok_b = run("compute_boards.py", env_extra=env, label="⑤ 行业板块计算(等权还原)")
    ok_r = run("make_report.py", env_extra=env, label="⑥ 渲染 HTML 报告")

    out = os.path.join(OUTDIR, f"A股市场情绪日报_{date}.html")
    if os.path.exists(out):
        log(f"\n完成 ✓ 报告已生成:\n  {out}  ({os.path.getsize(out) / 1024:.0f} KB)")
        if not ok_b or not ok_r:
            log("提示：部分步骤异常，报告可能不完整，请检查上方日志。")
    else:
        log("\n!! 报告未生成，请检查上面步骤的报错。")
        sys.exit(1)

    # 生成后推送
    if args.notify:
        try:
            import notify as _notify
            mkt = json.load(open(os.path.join(DATA, f"market_full_{key}.json"),
                                encoding="utf-8"))
            bds = json.load(open(os.path.join(DATA, f"boards_{key}.json"),
                                encoding="utf-8"))
            chgs = [v["chg"] for v in mkt["stocks"].values()]
            up = sum(1 for c in chgs if c > 0)
            dn = sum(1 for c in chgs if c < 0)
            fl = len(chgs) - up - dn
            rows = bds.get("rows", [])
            top, bot = rows[:3], rows[-3:]
            content = (f"全市场 {len(chgs)} 只：涨 {up} / 跌 {dn} / 平 {fl}\n\n"
                       f"**领涨行业**\n"
                       + "\n".join(f"- {r['name']} {r['chg']:+.2f}% （领涨 {r['leader_name']}）" for r in top)
                       + f"\n\n**领跌行业**\n"
                       + "\n".join(f"- {r['name']} {r['chg']:+.2f}%" for r in bot))
            title = f"A股情绪日报 {date}"
            for ch, (ok, msg) in _notify.notify(title, content, out):
                log(f"推送[{ch}]: {'✓' if ok else '✗'} {msg}")
        except Exception as e:
            log(f"推送失败（不影响报告）: {e}")


if __name__ == "__main__":
    main()
