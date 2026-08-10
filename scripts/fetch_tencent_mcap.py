# -*- coding: utf-8 -*-
"""腾讯财经批量抓取全市场流通市值/现价 → 推算流通股本(不随日期变化)。
腾讯接口不封 IP，可高频批量。
输出: data/float_shares.json  {code: {name, price, float_mcap_yi, float_shares}}
"""
import sys, io, json, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import urllib.request

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def prefix(c):
    if c.startswith(("6", "9")):
        return "sh" + c
    if c.startswith(("8", "4")):
        return "bj" + c
    return "sz" + c


def fetch(codes):
    url = "https://qt.gtimg.cn/q=" + ",".join(prefix(c) for c in codes)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read().decode("gbk", errors="replace")
    out = {}
    for line in data.strip().split(";"):
        if "=" not in line or '"' not in line:
            continue
        vals = line.split('"')[1].split("~")
        if len(vals) < 53:
            continue
        code = line.split("=")[0].split("_")[-1][2:]
        try:
            price = float(vals[3]) if vals[3] else 0.0
            fmcap = float(vals[45]) if vals[45] else 0.0   # 流通市值(亿)
            tmcap = float(vals[44]) if vals[44] else 0.0   # 总市值(亿)
        except ValueError:
            continue
        fshares = (fmcap * 1e8 / price) if price > 0 else 0.0
        out[code] = {"name": vals[1], "price": price,
                     "float_mcap_yi": fmcap, "total_mcap_yi": tmcap,
                     "float_shares": fshares}
    return out


def main():
    src = os.path.join(DATA_DIR, "stock_industry.json")
    if not os.path.exists(src):
        print("等待 stock_industry.json ...")
        return
    smap = json.load(open(src, encoding="utf-8"))["map"]
    codes = sorted(smap.keys())
    print("待查股票:", len(codes), flush=True)

    result = {}
    B = 60
    t0 = time.time()
    for i in range(0, len(codes), B):
        batch = codes[i:i + B]
        for attempt in range(3):
            try:
                result.update(fetch(batch))
                break
            except Exception:
                time.sleep(1.0)
        if (i // B) % 20 == 0:
            print(f"  {i+len(batch)}/{len(codes)} 已得 {len(result)} "
                  f"耗时 {time.time()-t0:.0f}s", flush=True)
        time.sleep(0.06)

    print(f"完成: {len(result)} 只, 耗时 {time.time()-t0:.0f}s", flush=True)
    with open(os.path.join(DATA_DIR, "float_shares.json"), "w",
              encoding="utf-8") as f:
        json.dump({"count": len(result), "map": result}, f, ensure_ascii=False)
    print("已保存 float_shares.json", flush=True)


if __name__ == "__main__":
    main()
