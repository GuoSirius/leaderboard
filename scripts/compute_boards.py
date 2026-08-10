# -*- coding: utf-8 -*-
"""还原 2026-07-24 东财行业板块涨跌幅（东财板块历史K线接口已被风控封禁，故自算还原）。

口径选择: 用最新交易日(2026-08-07)真实个股涨跌幅做了三种口径的对照实验——
      流通市值加权 MAE 0.559 / 总市值加权 MAE 0.540 / 等权算术平均 MAE 0.108。
      结论: 东财行业板块涨跌幅 = 板块内成分股涨跌幅的【等权算术平均】。
      仅看成分股覆盖完整的行业, 等权口径 MAE 0.068pct、P90 0.159pct。
方法: chg_board = mean(chg_i for i in 成分股)
"""
import sys, io, json, os, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.join(os.path.dirname(__file__), "..")
D = lambda n: os.path.join(BASE, "data", n)
TARGET = os.environ.get("REPORT_DATE", "2026-07-24")
TARGET_KEY = TARGET.replace("-", "")
VERIFY_DAY = os.environ.get("VERIFY_DATE", "2026-08-07")


def load(n):
    with open(D(n), encoding="utf-8") as f:
        return json.load(f)


def board_chg(items):
    """东财口径: 成分股涨跌幅等权算术平均"""
    v = [i["chg"] for i in items]
    return statistics.mean(v) if v else None


def day_chg(series, day):
    """从收盘序列取指定日涨跌幅 {code: (chg, close)}"""
    out = {}
    for code, v in series.items():
        d, c = v["d"], v["c"]
        if day not in d:
            continue
        i = d.index(day)
        if i == 0 or c[i - 1] <= 0:
            continue
        out[code] = ((c[i] / c[i - 1] - 1) * 100, c[i], v["name"])
    return out


def board_calc(daymap, shares, ind_of):
    """按行业聚合 -> {行业: [items]}。成分股不要求有市值数据，最大化覆盖率"""
    g = {}
    for code, (chg, close, name) in daymap.items():
        ind = ind_of.get(code)
        if not ind or ind == "-":
            continue
        g.setdefault(ind, []).append(
            {"code": code, "name": name, "chg": chg,
             "mcap": (shares.get(code) or 0) * close})
    return g


def main():
    series = load("series.json")["series"]
    si = load("stock_industry.json")["map"]
    fs = load("float_shares.json")["map"]
    boards = load("boards.json")["boards"]
    by_name = {b["name"]: b for b in boards}
    ind_of = {c: v["industry"] for c, v in si.items()}

    # 流通股本 = 流通市值 / 最新价
    shares = {}
    for c, v in fs.items():
        p = v.get("price") or 0
        fm = v.get("float_mcap_yi") or 0
        if p > 0 and fm > 0:
            shares[c] = fm * 1e8 / p

    # ── 1. 校验 ──
    vday = day_chg(series, VERIFY_DAY)
    vg = board_calc(vday, shares, ind_of)
    errs, detail = [], []
    for ind, items in vg.items():
        b = by_name.get(ind)
        if not b or not isinstance(b.get("latest_chg"), (int, float)):
            continue
        if len(items) < 2:
            continue
        mine = board_chg(items)
        if mine is None:
            continue
        e = abs(mine - b["latest_chg"])
        errs.append(e)
        detail.append((e, ind, mine, b["latest_chg"], len(items)))

    errs.sort()
    print(f"=== 算法校验 ({VERIFY_DAY}: 自算 vs 东财官方) ===")
    print(f"可比行业板块 {len(errs)} 个 | 样本个股 {len(vday)} 只")
    if errs:
        mae = statistics.mean(errs)
        p90 = errs[int(len(errs) * 0.9)]
        print(f"平均绝对误差 {mae:.3f} pct | 中位数 {statistics.median(errs):.3f} "
              f"| P90 {p90:.3f} | 最大 {errs[-1]:.3f}")
        print(f"误差<0.10pct: {sum(1 for e in errs if e<0.10)/len(errs)*100:.1f}%  "
              f"误差<0.30pct: {sum(1 for e in errs if e<0.30)/len(errs)*100:.1f}%")
        detail.sort(reverse=True)
        print("误差最大的 5 个行业:")
        for e, ind, mine, off, n in detail[:5]:
            print(f"  {ind:<12} 自算{mine:+.2f}% 官方{off:+.2f}% 差{e:.2f} ({n}只)")
    else:
        mae = p90 = None

    # ── 2. 目标日全市场涨跌幅 ──
    tday = day_chg(series, TARGET)
    day = {c: {"name": v[2], "chg": round(v[0], 2), "close": v[1],
               "src": "mootdx"} for c, v in tday.items()}
    try:
        fill = load(f"sina_fill_{TARGET_KEY}.json")["stocks"]
        for c, v in fill.items():
            if c not in day:
                day[c] = {"name": v["name"], "chg": v["chg_pct"],
                          "close": v["close"], "src": "sina"}
        print(f"\n新浪补齐(主板等) {len(fill)} 只")
    except FileNotFoundError:
        print("\n!! 未找到 sina 补齐文件, 跳过")

    n_bj = 0
    try:
        bj = load(f"bj_fill_{TARGET_KEY}.json")["stocks"]
        for c, v in bj.items():
            if c not in day:
                day[c] = {"name": v["name"], "chg": v["chg_pct"],
                          "close": v["close"], "src": "sina_bj"}
                n_bj += 1
        print(f"北交所补齐 {n_bj} 只")
    except FileNotFoundError:
        print("!! 未找到 北交所 补齐文件, 跳过")

    n_mo = sum(1 for v in day.values() if v["src"] == "mootdx")
    n_si = len(day) - n_mo - n_bj
    print(f"=== {TARGET} 全市场覆盖 {len(day)} 只 "
          f"(通达信 {n_mo} + 新浪主板 {n_si} + 北交所 {n_bj}) ===")

    # ── 3. 目标日板块指标 ──
    tmap = {c: (v["chg"], v["close"], v["name"]) for c, v in day.items()}
    g = board_calc(tmap, shares, ind_of)
    rows = []
    for ind, items in g.items():
        if len(items) < 2:
            continue
        chg = board_chg(items)
        if chg is None:
            continue
        up = sum(1 for i in items if i["chg"] > 0)
        dn = sum(1 for i in items if i["chg"] < 0)
        lead = max(items, key=lambda i: i["chg"])
        lag = min(items, key=lambda i: i["chg"])
        b = by_name.get(ind, {})
        rows.append({
            "code": b.get("code", ""), "name": ind,
            "chg": round(chg, 2), "count": len(items),
            "up": up, "down": dn, "flat": len(items) - up - dn,
            "leader_name": lead["name"], "leader_code": lead["code"],
            "leader_chg": round(lead["chg"], 2),
            "lagger_name": lag["name"], "lagger_code": lag["code"],
            "lagger_chg": round(lag["chg"], 2),
            "mcap_yi": round(sum(i["mcap"] for i in items) / 1e8, 1),
        })
    rows.sort(key=lambda r: r["chg"], reverse=True)

    print(f"\n有效行业板块 {len(rows)} 个")
    print("领涨 TOP8:")
    for r in rows[:8]:
        print(f"  {r['name']:<12} {r['chg']:+6.2f}%  涨{r['up']:>3}/跌{r['down']:>3}"
              f"  领涨 {r['leader_name']}({r['leader_chg']:+.2f}%)")
    print("领跌 TOP8:")
    for r in rows[-8:][::-1]:
        print(f"  {r['name']:<12} {r['chg']:+6.2f}%  涨{r['up']:>3}/跌{r['down']:>3}"
              f"  领跌 {r['lagger_name']}({r['lagger_chg']:+.2f}%)")
    ups = sum(1 for r in rows if r["chg"] > 0)
    print(f"\n板块红盘 {ups} / 绿盘 {len(rows)-ups}")

    with open(D(f"boards_{TARGET_KEY}.json"), "w", encoding="utf-8") as f:
        json.dump({"date": TARGET, "count": len(rows), "rows": rows,
                   "verify": {"day": VERIFY_DAY, "n": len(errs),
                              "mae": round(mae, 3) if mae else None,
                              "p90": round(p90, 3) if p90 else None}},
                  f, ensure_ascii=False)
    with open(D(f"market_full_{TARGET_KEY}.json"), "w", encoding="utf-8") as f:
        json.dump({"date": TARGET, "count": len(day),
                   "src": {"mootdx": n_mo, "sina": n_si, "bj": n_bj},
                   "stocks": day},
                  f, ensure_ascii=False)
    print("已保存 boards_20260724.json / market_full_20260724.json")


if __name__ == "__main__":
    main()
