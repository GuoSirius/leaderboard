# -*- coding: utf-8 -*-
"""组装单文件暗色 HTML 市场情绪日报(全内联, 可离线打开)。"""
import sys, io, os, json, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_report import (load, money, yuan, cls, col, pct, esc,
                          svg_diverging, svg_bars, svg_breadth, BASE, UP, DOWN)
from report_css import CSS

OUT_DIR = os.path.join(BASE, "output")
TARGET = os.environ.get("REPORT_DATE", "2026-07-24")
TARGET_KEY = TARGET.replace("-", "")
OUT = os.path.join(OUT_DIR, f"A股市场情绪日报_{TARGET}.html")
WEEK = "一二三四五六日"


def main():
    lhb = load("lhb_agg.json")
    ths = load("ths_hot.json")
    bds = load(f"boards_{TARGET_KEY}.json")
    mkt = load(f"market_full_{TARGET_KEY}.json")

    date = lhb["date"]
    dt = datetime.datetime.strptime(date, "%Y-%m-%d")
    wd = "星期" + WEEK[dt.weekday()]
    st, rows = lhb["stat"], lhb["rows"]
    themes, hots = ths["themes"], ths["stocks"]
    brows = bds["rows"]
    vf = bds.get("verify", {})

    chgs = [v["chg"] for v in mkt["stocks"].values()]
    m_up = sum(1 for c in chgs if c > 0)
    m_dn = sum(1 for c in chgs if c < 0)
    m_fl = len(chgs) - m_up - m_dn
    m_lu = sum(1 for c in chgs if c >= 9.8)
    m_ld = sum(1 for c in chgs if c <= -9.8)

    top_theme = themes[0] if themes else {"tag": "—", "count": 0, "avg_chg": 0.0}
    top_board = brows[0] if brows else {"name": "—", "chg": 0.0, "leader_name": "—"}
    b_up = sum(1 for r in brows if r["chg"] > 0)

    P = []
    A = P.append

    A('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">')
    A('<meta name="viewport" content="width=device-width,initial-scale=1">')
    A(f'<title>A股市场情绪日报 · {date}</title>')
    A(f'<style>{CSS}</style></head><body><div class="wrap">')

    # ══ 页头 ══
    A('<header><div class="htop"><div>')
    A('<h1>A股市场情绪日报 <span class="bar">龙虎榜 · 题材热点 · 行业轮动</span></h1>')
    A(f'<div class="hsub">全市场资金博弈与情绪结构复盘'
      f'<span class="badge">真实行情数据</span>'
      f'<span class="badge">全市场样本 {len(mkt["stocks"]):,} 只</span>'
      f'<span class="badge">离线单文件</span></div>')
    A(f'</div><div class="hdate"><div class="d num">{date}</div>'
      f'<div class="w">{wd} · 交易日</div></div></div></header>')

    # ══ KPI ══
    A('<div class="kpis">')

    def kpi(k, v, u="", s="", c="", ex=""):
        A(f'<div class="kpi {ex}"><div class="k">{k}</div>'
          f'<div class="v num {c}">{v}<span class="u">{u}</span></div>'
          f'<div class="s">{s}</div></div>')

    ns = st["net_sum"]
    kpi("龙虎榜上榜", f'{lhb["count"]}', " 家",
        f'{lhb["raw_count"]} 条榜单记录 · 涨停 {st["limit_up"]} 家')
    kpi("净买入合计", f'{"+" if ns>0 else ""}{ns/1e8:.2f}', " 亿元",
        f'买入 {yuan(st["buy_sum"])} / 卖出 {yuan(st["sell_sum"])}',
        cls(ns), "g" if ns > 0 else "r")
    kpi("龙虎榜成交", f'{st["deal_sum"]/1e8:,.1f}', " 亿元",
        f'净买为正 {st["net_pos"]} 家 · 为负 {lhb["count"]-st["net_pos"]} 家')
    kpi("最热题材", esc(top_theme["tag"]), "",
        f'{top_theme["count"]} 只强势股 · 均涨 {top_theme["avg_chg"]:+.2f}%', "up")
    kpi("领涨行业", esc(top_board["name"]), "",
        f'{top_board["chg"]:+.2f}% · 领涨 {esc(top_board["leader_name"])}',
        cls(top_board["chg"]), "g" if top_board["chg"] > 0 else "r")
    kpi("全市场涨跌", f'{m_up}', f" / {m_dn}",
        f'涨停 {m_lu} · 跌停 {m_ld} · 平盘 {m_fl}',
        "up" if m_up > m_dn else "down", "g" if m_up > m_dn else "r")
    A('</div>')

    # ══ 市场宽度 ══
    A('<div class="panel"><div class="ptitle"><b>市场宽度</b>'
      f'<span>全市场 {len(mkt["stocks"]):,} 只个股当日涨跌分布 · '
      f'板块红盘 {b_up} / 绿盘 {len(brows)-b_up}</span></div>')
    A(svg_breadth(m_up, m_dn, m_fl, m_lu, m_ld))
    A('</div>')

    # ══════ ① 龙虎榜 ══════
    A('<section><div class="sh"><span class="no">01</span>'
      '<h2>龙虎榜资金博弈</h2>'
      '<span class="src">数据源：东方财富 · 每日龙虎榜详情</span></div>')

    # 净买入排名图
    topn = rows[:18]
    botn = rows[-12:]
    chart = [{"label": f'{r["name"]}', "value": r["net_buy"] / 1e8,
              "sub": f'{r["chg_pct"]:+.2f}%'} for r in topn + botn[::-1]]
    A('<div class="panel"><div class="ptitle">'
      '<b>净买入排名 · 前18名与后12名</b>'
      '<span>红色为资金净买入，绿色为净卖出（单位：亿元）</span></div>')
    A(svg_diverging(chart, value_fmt=lambda v: f"{v:+.2f}",
                    sub_key="sub", unit=""))
    A('</div>')

    # 全表
    A(f'<div class="ptitle" style="margin:14px 0 8px">'
      f'<b>全部上榜个股明细（{lhb["count"]} 只，按净买入降序）</b>'
      f'<span>原始榜单 {lhb["raw_count"]} 条，同股多原因上榜按主榜合并</span></div>')
    A('<div class="tw scroll"><table><thead><tr>'
      '<th class="l">#</th><th class="l">代码</th><th class="l">名称</th>'
      '<th>收盘价</th><th>涨跌幅</th><th>净买入</th><th>买入额</th>'
      '<th>卖出额</th><th>换手率</th><th>占成交</th>'
      '<th class="l">上榜原因</th></tr></thead><tbody>')
    for i, r in enumerate(rows, 1):
        rs = "；".join(r["reasons"])
        tail = f'<span class="tag">+{r["reason_n"]-1}榜</span>' if r["reason_n"] > 1 else ""
        A(f'<tr><td class="l rk num">{i}</td>'
          f'<td class="l code num">{r["code"]}</td>'
          f'<td class="l nm">{esc(r["name"])}</td>'
          f'<td class="num">{r["close"]:.2f}</td>'
          f'<td class="num {cls(r["chg_pct"])}">{r["chg_pct"]:+.2f}%</td>'
          f'<td class="num {cls(r["net_buy"])}"><b>{yuan(r["net_buy"])}</b></td>'
          f'<td class="num">{yuan(r["buy_amt"])}</td>'
          f'<td class="num">{yuan(r["sell_amt"])}</td>'
          f'<td class="num">{r["turnover_pct"]:.2f}%</td>'
          f'<td class="num">{(r.get("deal_ratio") or 0):.1f}%</td>'
          f'<td class="l"><span class="rsn" title="{esc(rs)}">{esc(rs)}</span>{tail}</td>'
          f'</tr>')
    A('</tbody></table></div>')
    A(f'<div class="note"><b>口径说明：</b>同一只个股当日可能因多个原因分别上榜'
      f'（本日 {lhb["raw_count"]} 条记录对应 {lhb["count"]} 只个股）。'
      f'其中「单日榜」与「连续三日累计榜」的席位金额口径不同、不可相加，'
      f'故按每只个股净买入绝对值最大的一条作为主榜代表，上榜原因合并展示。'
      f'净买入 = 龙虎榜买入前五席位金额 − 卖出前五席位金额。</div>')
    A('</section>')

    # ══════ ② 题材热点 ══════
    A('<section><div class="sh"><span class="no">02</span>'
      '<h2>题材热点归因</h2>'
      '<span class="src">数据源：同花顺 · 当日强势股异动归因</span></div>')

    t15 = themes[:15]
    A('<div class="panel"><div class="ptitle">'
      '<b>题材热度排行 · 按上榜强势股只数</b>'
      f'<span>{len(hots)} 只强势股共拆出 {len(themes)} 个题材标签'
      f'（同花顺 reason 字段按「+」拆分后词频统计）</span></div>')
    A(svg_bars([{"label": t["tag"], "value": t["count"],
                 "chg": t["avg_chg"],
                 "sub": f'均涨 {t["avg_chg"]:+.2f}%'} for t in t15]))
    A('</div>')

    # 题材卡片
    A('<div class="ptitle" style="margin:14px 0 8px">'
      '<b>热门题材成分股</b><span>TOP12 题材及其代表个股</span></div>')
    A('<div class="tgrid">')
    for t in themes[:12]:
        lst = "、".join(
            f'<b>{esc(s["name"])}</b> <span class="{cls(s["chg_pct"])}">'
            f'{s["chg_pct"]:+.2f}%</span>' for s in t["stocks"][:6])
        A(f'<div class="tcard"><div class="th">'
          f'<span class="tn">{esc(t["tag"])}</span>'
          f'<span class="tc">{t["count"]} 只 · 均涨 '
          f'<span class="{cls(t["avg_chg"])}">{t["avg_chg"]:+.2f}%</span></span>'
          f'</div><div class="tl">{lst}</div></div>')
    A('</div>')

    # 强势股表
    hs = sorted(hots, key=lambda x: x["chg_pct"], reverse=True)
    A(f'<div class="ptitle" style="margin:16px 0 8px">'
      f'<b>当日强势股明细（{len(hs)} 只）</b>'
      f'<span>按涨幅降序 · DDE 为同花顺大单净量指标</span></div>')
    A('<div class="tw scroll"><table><thead><tr>'
      '<th class="l">#</th><th class="l">代码</th><th class="l">名称</th>'
      '<th>收盘价</th><th>涨跌幅</th><th>换手率</th><th>成交额</th>'
      '<th>DDE</th><th class="l">题材归因</th></tr></thead><tbody>')
    for i, s in enumerate(hs, 1):
        tags = "".join(
            f'<span class="tag{" hot" if tg in [t["tag"] for t in t15[:6]] else ""}">'
            f'{esc(tg)}</span>'
            for tg in str(s.get("reason", "")).split("+") if tg.strip())
        A(f'<tr><td class="l rk num">{i}</td>'
          f'<td class="l code num">{s["code"]}</td>'
          f'<td class="l nm">{esc(s["name"])}</td>'
          f'<td class="num">{s["close"]:.2f}</td>'
          f'<td class="num {cls(s["chg_pct"])}"><b>{s["chg_pct"]:+.2f}%</b></td>'
          f'<td class="num">{(s.get("turnover_pct") or 0):.2f}%</td>'
          f'<td class="num">{yuan((s.get("amount_wan") or 0)*1e4)}</td>'
          f'<td class="num {cls(s.get("dde") or 0)}">{(s.get("dde") or 0):+.2f}</td>'
          f'<td class="l">{tags}</td></tr>')
    A('</tbody></table></div>')
    A('<div class="note"><b>口径说明：</b>题材标签来自同花顺对当日强势股的异动归因字段，'
      '原始形如「AI服务器上游+一体成型电感+防雷+一季报增长」，'
      '本报告按「+」拆分为独立标签后做词频统计，'
      '「只数」= 携带该标签的强势股数量，「均涨」= 这些个股当日涨幅算术平均。</div>')
    A('</section>')

    # ══════ ③ 行业轮动 ══════
    A('<section><div class="sh"><span class="no">03</span>'
      '<h2>行业板块轮动</h2>'
      '<span class="src">数据源：东方财富行业板块 + 全市场个股行情还原</span></div>')

    lead12, lag12 = brows[:14], brows[-14:]
    chart2 = [{"label": r["name"], "value": r["chg"],
               "sub": f'{r["up"]}↑/{r["down"]}↓'}
              for r in lead12 + lag12[::-1]]
    A('<div class="panel"><div class="ptitle">'
      '<b>行业涨跌榜 · 领涨14与领跌14</b>'
      f'<span>共 {len(brows)} 个行业板块，红盘 {b_up} 个 / '
      f'绿盘 {len(brows)-b_up} 个（单位：%）</span></div>')
    A(svg_diverging(chart2, value_fmt=lambda v: f"{v:+.2f}",
                    sub_key="sub", unit="%"))
    A('</div>')

    A(f'<div class="ptitle" style="margin:14px 0 8px">'
      f'<b>全部行业板块明细（{len(brows)} 个，按涨跌幅降序）</b>'
      f'<span>成分股涨跌幅等权平均口径</span></div>')
    A('<div class="tw scroll"><table><thead><tr>'
      '<th class="l">#</th><th class="l">板块代码</th><th class="l">行业名称</th>'
      '<th>涨跌幅</th><th>成分股</th><th>上涨</th><th>下跌</th>'
      '<th class="l">领涨股</th><th>涨幅</th>'
      '<th class="l">领跌股</th><th>跌幅</th></tr></thead><tbody>')
    for i, r in enumerate(brows, 1):
        A(f'<tr><td class="l rk num">{i}</td>'
          f'<td class="l code num">{esc(r["code"])}</td>'
          f'<td class="l nm">{esc(r["name"])}</td>'
          f'<td class="num {cls(r["chg"])}"><b>{r["chg"]:+.2f}%</b></td>'
          f'<td class="num">{r["count"]}</td>'
          f'<td class="num up">{r["up"]}</td>'
          f'<td class="num down">{r["down"]}</td>'
          f'<td class="l">{esc(r["leader_name"])}'
          f'<span class="code num"> {r["leader_code"]}</span></td>'
          f'<td class="num {cls(r["leader_chg"])}">{r["leader_chg"]:+.2f}%</td>'
          f'<td class="l">{esc(r["lagger_name"])}'
          f'<span class="code num"> {r["lagger_code"]}</span></td>'
          f'<td class="num {cls(r["lagger_chg"])}">{r["lagger_chg"]:+.2f}%</td>'
          f'</tr>')
    A('</tbody></table></div>')
    A(f'<div class="note"><b>还原方法与精度：</b>东方财富板块历史K线接口当前触发风控不可用，'
      f'本报告的行业涨跌幅由全市场个股当日真实行情按东财口径还原。'
      f'口径经对照实验确定：以最新交易日 {vf.get("day","")} 的真实个股涨跌幅分别用'
      f'「流通市值加权 / 总市值加权 / 等权算术平均」三种方式回算，'
      f'再与东方财富官方板块涨跌幅逐一比对，等权口径误差最小'
      f'（平均绝对误差 {vf.get("mae","—")} 个百分点，'
      f'P90 {vf.get("p90","—")}，可比板块 {vf.get("n","—")} 个），故采用等权口径。'
      f'个股所属行业取自东方财富行业分类（f100 字段）。</div>')
    A('</section>')

    # ══════ 页脚 ══════
    gen = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    A('<footer>')
    A(f'<div><b>数据来源</b></div><div class="srcs">')
    A('<span class="s1">① 龙虎榜：东方财富 datacenter-web · '
      'RPT_DAILYBILLBOARD_DETAILSNEW</span>')
    A('<span class="s1">② 题材热点：同花顺 · zx.10jqka.com.cn 当日强势股异动归因</span>')
    A('<span class="s1">③ 行业板块：东方财富行业板块列表（BK 代码/行业分类）</span>')
    A('<span class="s1">④ 全市场行情：通达信行情（mootdx）+ 新浪财经历史行情</span>')
    A('<span class="s1">⑤ 流通市值：腾讯财经 qt.gtimg.cn</span>')
    A('</div>')
    src = mkt.get("src", {})
    A(f'<div><b>交易日期：</b>{date}（{wd}） &nbsp;·&nbsp; '
      f'<b>全市场样本：</b>{len(mkt["stocks"]):,} 只'
      f'（通达信 {src.get("mootdx","—")} + 新浪主板 {src.get("sina","—")}'
      f' + 北交所 {src.get("bj","—")}） &nbsp;·&nbsp; '
      f'<b>报告生成：</b>{gen}</div>')
    A('<div><b>免责声明：</b>本报告数据均由公开行情接口实时抓取，'
      '不构成任何投资建议。龙虎榜与题材归因反映的是当日资金行为与市场情绪，'
      '不代表未来走势。行业涨跌幅为还原值，与交易软件展示可能存在细微差异。</div>')
    A('</footer>')

    A('</div></body></html>')

    os.makedirs(OUT_DIR, exist_ok=True)
    html_str = "".join(P)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html_str)
    size = os.path.getsize(OUT) / 1024
    print(f"已生成: {os.path.abspath(OUT)}")
    print(f"大小 {size:.0f} KB | 龙虎榜 {lhb['count']} 只 | "
          f"题材 {len(themes)} 个 | 强势股 {len(hots)} 只 | 行业 {len(brows)} 个")
    print(f"全市场 {len(mkt['stocks'])} 只: 涨{m_up}/跌{m_dn}/平{m_fl} "
          f"涨停{m_lu}/跌停{m_ld}")


if __name__ == "__main__":
    main()
