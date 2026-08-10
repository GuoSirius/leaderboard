# -*- coding: utf-8 -*-
"""龙虎榜按个股聚合。

一只股票当日可能因多个原因分别上榜, 东财会输出多条记录。
其中"单日榜"(涨跌幅偏离7%/换手率20%等)的席位数据是同一份,
而"连续三日累计榜"是三日累计口径, 金额不可与单日相加。
=> 取 |净买入| 最大的一条作为该股主榜代表, 上榜原因合并展示。
"""
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.join(os.path.dirname(__file__), "..")
D = lambda n: os.path.join(BASE, "data", n)


def main():
    raw = json.load(open(D("lhb.json"), encoding="utf-8"))
    rows = raw["rows"]
    print(f"原始记录 {len(rows)} 条")

    by_code = {}
    for r in rows:
        by_code.setdefault(r["code"], []).append(r)
    print(f"去重个股 {len(by_code)} 只")

    multi = {c: v for c, v in by_code.items() if len(v) > 1}
    print(f"多次上榜 {len(multi)} 只")
    for c, v in list(multi.items())[:6]:
        amts = [round(x["net_buy"] / 1e4, 1) for x in v]
        print(f"  {c} {v[0]['name']}: {len(v)}条 净买入(万) {amts}")

    out = []
    for c, v in by_code.items():
        main_r = max(v, key=lambda x: abs(x.get("net_buy") or 0))
        reasons = []
        for x in v:
            rs = x.get("reason", "")
            if rs and rs not in reasons:
                reasons.append(rs)
        out.append({
            "code": c,
            "name": main_r["name"],
            "chg_pct": main_r["chg_pct"],
            "close": main_r["close"],
            "net_buy": main_r["net_buy"],
            "buy_amt": main_r["buy_amt"],
            "sell_amt": main_r["sell_amt"],
            "deal_amt": main_r["deal_amt"],
            "turnover_pct": main_r["turnover_pct"],
            "accum_amount": main_r.get("accum_amount"),
            "free_mcap": main_r.get("free_mcap"),
            "market": main_r.get("market"),
            "deal_ratio": main_r.get("deal_ratio"),
            "reasons": reasons,
            "reason_n": len(v),
            "explain": main_r.get("explain", ""),
        })

    out.sort(key=lambda x: x["net_buy"], reverse=True)

    net_sum = sum(x["net_buy"] for x in out)
    buy_sum = sum(x["buy_amt"] for x in out)
    sell_sum = sum(x["sell_amt"] for x in out)
    deal_sum = sum(x["deal_amt"] for x in out)
    ups = sum(1 for x in out if x["chg_pct"] > 0)
    dns = sum(1 for x in out if x["chg_pct"] < 0)
    limit_up = sum(1 for x in out if x["chg_pct"] >= 9.8)
    net_pos = sum(1 for x in out if x["net_buy"] > 0)

    print(f"\n净买入合计 ¥{net_sum/1e8:.2f}亿 (买入{buy_sum/1e8:.2f}亿 / "
          f"卖出{sell_sum/1e8:.2f}亿)")
    print(f"龙虎榜成交总额 ¥{deal_sum/1e8:.2f}亿")
    print(f"上涨 {ups} / 下跌 {dns} / 涨停 {limit_up} / 净买入为正 {net_pos}")
    print("\n净买入 TOP10:")
    for x in out[:10]:
        print(f"  {x['code']} {x['name']:<8} {x['chg_pct']:+6.2f}%  "
              f"净买 ¥{x['net_buy']/1e8:.2f}亿  换手 {x['turnover_pct']:.1f}%")
    print("\n净卖出 TOP5:")
    for x in out[-5:][::-1]:
        print(f"  {x['code']} {x['name']:<8} {x['chg_pct']:+6.2f}%  "
              f"净买 ¥{x['net_buy']/1e8:.2f}亿")

    json.dump({
        "date": raw["date"], "raw_count": len(rows), "count": len(out),
        "stat": {"net_sum": net_sum, "buy_sum": buy_sum, "sell_sum": sell_sum,
                 "deal_sum": deal_sum, "ups": ups, "downs": dns,
                 "limit_up": limit_up, "net_pos": net_pos},
        "rows": out,
    }, open(D("lhb_agg.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("\n已保存 lhb_agg.json")


if __name__ == "__main__":
    main()
