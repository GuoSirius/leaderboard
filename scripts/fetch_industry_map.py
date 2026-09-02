# -*- coding: utf-8 -*-
"""用 push2delay 抓取：(a) 东财行业板块列表 (b) 全市场个股所属行业映射。
保守限流，避免触发东财风控。
"""
import sys, io, json, os, time, random, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
UT = "bd1d9ddb04089700cf9c27f6f7426281"
CLIST = "https://push2delay.eastmoney.com/api/qt/clist/get"
FS_ALL = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"

S = requests.Session()
S.headers.update({"User-Agent": UA, "Referer": "https://quote.eastmoney.com/",
                  "Accept": "*/*", "Accept-Language": "zh-CN,zh;q=0.9",
                  "Connection": "keep-alive"})
INTERVAL = 1.6
_last = [0.0]


def get(params, tries=5):
    for i in range(tries):
        w = INTERVAL - (time.time() - _last[0])
        if w > 0:
            time.sleep(w + random.uniform(0.1, 0.4))
        try:
            r = S.get(CLIST, params=params, timeout=20)
            _last[0] = time.time()
            return r.json()
        except Exception:
            _last[0] = time.time()
            time.sleep(2.0 + i * 1.5)
    return {}


def page_all(fs, fields, label, max_pages=80):
    """分页抓取（push2delay 每页固定 100 条）"""
    out, pn, total = [], 1, None
    while pn <= max_pages:
        d = get({"pn": str(pn), "pz": "100", "po": "1", "np": "1", "ut": UT,
                 "fltt": "2", "invt": "2", "fs": fs, "fields": fields})
        dd = d.get("data") or {}
        if total is None:
            total = dd.get("total")
        items = dd.get("diff") or []
        if not items:
            break
        out.extend(items)
        print(f"  [{label}] 第{pn}页 +{len(items)} 累计{len(out)}/{total}", flush=True)
        if total and len(out) >= total:
            break
        pn += 1
    return out, total


# ── (a) 行业板块列表 ──
print("(a) 抓取东财行业板块列表 (m:90+t:2)", flush=True)
boards, btotal = page_all(
    "m:90+t:2",
    "f2,f3,f4,f12,f14,f104,f105,f128,f136,f140,f207,f208,f209,f62,f184",
    "行业板块", max_pages=12)
board_rows = []
for b in boards:
    board_rows.append({
        "code": b.get("f12", ""),
        "name": b.get("f14", ""),
        "latest_chg": b.get("f3"),
        "up_count_latest": b.get("f104"),
        "down_count_latest": b.get("f105"),
        "leader_name_latest": b.get("f128"),
        "leader_code_latest": b.get("f140"),
    })
print(f"  行业板块合计: {len(board_rows)} 个 (接口 total={btotal})", flush=True)
with open(os.path.join(DATA_DIR, "boards.json"), "w", encoding="utf-8") as f:
    json.dump({"count": len(board_rows), "boards": board_rows},
              f, ensure_ascii=False)

# 记录官方板块涨幅对应的交易日，供 compute_boards 校验对齐使用
# （东财板块历史K线被风控封禁，本地只有"抓取当天"这一份官方锚点，
#  校验必须拿同一天的自算值去比，否则会出现跨日错位假误差）
def _last_trading_day(d=None):
    d = d or datetime.date.today()
    while d.weekday() >= 5:  # 5=周六 6=周日
        d -= datetime.timedelta(days=1)
    return d.strftime("%Y-%m-%d")
meta = {"day": _last_trading_day(),
        "fetched_at": datetime.datetime.now().isoformat(timespec="seconds")}
with open(os.path.join(DATA_DIR, "boards_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False)

# ── (b) 全市场个股所属行业 ──
print("\n(b) 抓取全市场个股所属行业 (f100)", flush=True)
stocks, stotal = page_all(FS_ALL, "f12,f14,f100,f13", "全市场", max_pages=80)
smap = {}
for s in stocks:
    c = s.get("f12", "")
    if c:
        smap[c] = {"name": s.get("f14", ""), "industry": s.get("f100", "")}
print(f"  个股合计: {len(smap)} 只 (接口 total={stotal})", flush=True)
with open(os.path.join(DATA_DIR, "stock_industry.json"), "w", encoding="utf-8") as f:
    json.dump({"count": len(smap), "map": smap}, f, ensure_ascii=False)

print("\n完成: boards.json / stock_industry.json", flush=True)
