# -*- coding: utf-8 -*-
"""用 mootdx 抓全市场 A 股最近 30 个交易日收盘序列(一次抓取, 多日复用)。
输出: data/series.json {code: {name, d:[日期...], c:[收盘...], a:[成交额...]}}
"""
import sys, io, json, os, time, logging
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
logging.getLogger("mootdx").setLevel(logging.ERROR)

from mootdx.quotes import Quotes

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "series.json")


def is_a_share(code, market):
    if not code or len(code) != 6 or not code.isdigit():
        return False
    if market == 1:
        return code.startswith(("600", "601", "603", "605", "688", "689"))
    return code.startswith(("000", "001", "002", "003", "300", "301"))


def main():
    # 防止通达信行情服务器(TCP 7709)在海外/CI 环境不可达时长时间挂起
    import socket
    socket.setdefaulttimeout(10)
    try:
        client = Quotes.factory(market="std")
    except Exception as e:
        print(f"[跳过] 通达信行情服务器不可达（CI/海外环境常见）：{e}", flush=True)
        print("[跳过] 全市场行情序列将缺失；龙虎榜/题材/行业(HTTP源)仍正常生成。", flush=True)
        return
    codes, seen = [], set()
    for mkt in (1, 0):
        df = client.stocks(market=mkt)
        for _, row in df.iterrows():
            c = str(row["code"]).strip()
            if is_a_share(c, mkt) and c not in seen:
                seen.add(c)
                codes.append((c, str(row["name"]).strip()))
    print(f"A股正股 {len(codes)} 只", flush=True)

    res, miss, t0 = {}, 0, time.time()
    for i, (code, name) in enumerate(codes, 1):
        try:
            bars = client.bars(symbol=code, category=4, offset=30)
            if bars is None or len(bars) == 0:
                miss += 1
                continue
            res[code] = {
                "name": name,
                "d": [str(x)[:10] for x in bars["datetime"]],
                "c": [round(float(x), 3) for x in bars["close"]],
                "a": [float(x) for x in bars["amount"]],
            }
        except Exception:
            miss += 1
        if i % 800 == 0:
            el = time.time() - t0
            print(f"  {i}/{len(codes)} 得{len(res)} 用时{el:.0f}s "
                  f"余{el/i*(len(codes)-i):.0f}s", flush=True)

    print(f"完成 {len(res)} 只, 缺 {miss}, 耗时 {time.time()-t0:.0f}s", flush=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"count": len(res), "series": res}, f, ensure_ascii=False)

    # 最近交易日
    from collections import Counter
    cnt = Counter()
    for v in res.values():
        for d in v["d"][-6:]:
            cnt[d] += 1
    print("最近交易日:", sorted(cnt.items())[-6:], flush=True)


if __name__ == "__main__":
    main()
