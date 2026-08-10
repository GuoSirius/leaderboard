# -*- coding: utf-8 -*-
"""抓取 ① 全市场龙虎榜(东财 datacenter) ② 同花顺当日强势股题材归因。"""
import sys, io, json, os, time, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import requests
from collections import Counter

TARGET = os.environ.get("REPORT_DATE", "2026-07-24")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
S = requests.Session()
S.headers.update({"User-Agent": UA})
DATACENTER_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"


def em_datacenter(report_name, filter_str, page_size=500, page_number=1,
                  sort_columns="", sort_types="-1", tries=4):
    params = {
        "reportName": report_name, "columns": "ALL", "filter": filter_str,
        "pageNumber": str(page_number), "pageSize": str(page_size),
        "sortColumns": sort_columns, "sortTypes": sort_types,
        "source": "WEB", "client": "WEB",
    }
    last = None
    for i in range(tries):
        try:
            r = S.get(DATACENTER_URL, params=params, timeout=25)
            d = r.json()
            res = d.get("result") or {}
            return (res.get("data") or []), (res.get("pages") or 0)
        except Exception as e:
            last = e
            time.sleep(2.5 + random.uniform(0, 1.5))
    print("  [WARN] datacenter 失败:", repr(last))
    return [], 0


# ───────────────────── ① 全市场龙虎榜 ─────────────────────
print("① 抓取全市场龙虎榜", TARGET, flush=True)
all_rows, page, pages = [], 1, 1
while page <= pages and page <= 10:
    rows, pg = em_datacenter(
        "RPT_DAILYBILLBOARD_DETAILSNEW",
        f"(TRADE_DATE>='{TARGET}')(TRADE_DATE<='{TARGET}')",
        page_size=500, page_number=page,
        sort_columns="BILLBOARD_NET_AMT", sort_types="-1",
    )
    if pg:
        pages = pg
    if not rows:
        break
    all_rows.extend(rows)
    print(f"  第{page}页 {len(rows)} 条 (总页数 {pages})", flush=True)
    page += 1
    time.sleep(2.0 + random.uniform(0, 0.8))

lhb = []
for r in all_rows:
    lhb.append({
        "code": r.get("SECURITY_CODE", ""),
        "name": r.get("SECURITY_NAME_ABBR", ""),
        "reason": r.get("EXPLANATION", ""),
        "explain": r.get("EXPLAIN", ""),
        "close": r.get("CLOSE_PRICE") or 0,
        "chg_pct": round(float(r.get("CHANGE_RATE") or 0), 2),
        "net_buy": float(r.get("BILLBOARD_NET_AMT") or 0),      # 元
        "buy_amt": float(r.get("BILLBOARD_BUY_AMT") or 0),
        "sell_amt": float(r.get("BILLBOARD_SELL_AMT") or 0),
        "deal_amt": float(r.get("BILLBOARD_DEAL_AMT") or 0),
        "turnover_pct": round(float(r.get("TURNOVERRATE") or 0), 2),
        "accum_amount": float(r.get("ACCUM_AMOUNT") or 0),
        "free_mcap": float(r.get("FREE_MARKET_CAP") or 0),
        "market": r.get("MARKET", ""),
        "deal_ratio": round(float(r.get("DEAL_AMOUNT_RATIO") or 0), 2),
        "net_ratio": round(float(r.get("DEAL_NET_RATIO") or 0), 2),
    })
lhb.sort(key=lambda x: x["net_buy"], reverse=True)
print(f"  龙虎榜记录合计: {len(lhb)} 条", flush=True)

with open(os.path.join(DATA_DIR, "lhb.json"), "w", encoding="utf-8") as f:
    json.dump({"date": TARGET, "count": len(lhb), "rows": lhb},
              f, ensure_ascii=False)

# ───────────────────── ② 同花顺题材归因 ─────────────────────
print("\n② 抓取同花顺强势股题材归因", TARGET, flush=True)
url = (f"http://zx.10jqka.com.cn/event/api/getharden/"
       f"date/{TARGET}/orderby/date/orderway/desc/charset/GBK/")
r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
d = r.json()
if d.get("errocode", 0) != 0:
    raise RuntimeError("同花顺错误: " + str(d.get("errormsg")))
raw = d.get("data") or []
hot = []
for x in raw:
    hot.append({
        "code": x.get("code", ""),
        "name": x.get("name", ""),
        "reason": x.get("reason", "") or "",
        "close": x.get("close", 0),
        "chg_pct": round(float(x.get("zhangfu") or 0), 2),
        "chg_amt": x.get("zhangdie", 0),
        "turnover_pct": round(float(x.get("huanshou") or 0), 2),
        "amount_wan": float(x.get("chengjiaoe") or 0),   # 万元
        "volume": float(x.get("chengjiaoliang") or 0),
        "dde": x.get("ddejingliang", 0),
    })
hot.sort(key=lambda x: x["chg_pct"], reverse=True)
print(f"  强势股: {len(hot)} 只", flush=True)

# 题材词频（按 + 拆分）
cnt = Counter()
tag_stocks = {}
for h in hot:
    tags = [t.strip() for t in str(h["reason"]).split("+") if t.strip()]
    for t in set(tags):          # 同一只股票同题材只计一次
        cnt[t] += 1
        tag_stocks.setdefault(t, []).append(
            {"code": h["code"], "name": h["name"], "chg_pct": h["chg_pct"]})

themes = []
for tag, n in cnt.most_common():
    sl = sorted(tag_stocks[tag], key=lambda x: x["chg_pct"], reverse=True)
    themes.append({
        "tag": tag, "count": n,
        "avg_chg": round(sum(s["chg_pct"] for s in sl) / len(sl), 2),
        "stocks": sl,
    })
print("  题材标签总数:", len(themes), flush=True)
print("  TOP15 题材:", flush=True)
for t in themes[:15]:
    print(f"    {t['tag']}: {t['count']} 只, 均涨 {t['avg_chg']}%", flush=True)

with open(os.path.join(DATA_DIR, "ths_hot.json"), "w", encoding="utf-8") as f:
    json.dump({"date": TARGET, "count": len(hot),
               "stocks": hot, "themes": themes}, f, ensure_ascii=False)

print("\n完成，已保存 lhb.json / ths_hot.json", flush=True)
