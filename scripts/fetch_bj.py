# -*- coding: utf-8 -*-
"""专补北交所(920/8xx/43x)在 2026-07-24 的涨跌幅。
mootdx 不支持北交所, 东财/腾讯历史K线不可用, 新浪可用但有累积型频控 -> 放慢到 1s/次。
修复: 旧版要求 float_shares 含该代码且市值>0, 但 float_shares 仅覆盖 5552 只(几乎不含北交所),
     导致 345 只北交所全部被过滤掉。改为仅以 stock_industry 行业映射为存在性依据。
"""
import json, sys, io, time, random, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests

BASE = 'D:/workspace/workbuddy/2026-08-10-08-24-44'
TARGET = os.environ.get("REPORT_DATE", "2026-07-24")
OUT = f'{BASE}/data/bj_fill_20260724.json'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36',
      'Referer': 'https://finance.sina.com.cn/'}
URL = ('https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/'
       'CN_MarketData.getKLineData')

BJ_PRE = ('920', '430', '830', '831', '832', '833', '834', '835', '836', '837',
          '838', '839', '870', '871', '872', '873', '874', '875', '876', '877',
          '879', '880', '882', '885', '887', '889', '890', '899')


def fetch(sess, code, tries=3):
    for _ in range(tries):
        try:
            r = sess.get(URL, params={'symbol': 'bj' + code, 'scale': 240,
                                      'ma': 'no', 'datalen': 40},
                         headers=UA, timeout=12)
            txt = r.text.strip()
            if not txt or txt == 'null':
                return None
            arr = json.loads(txt)
            idx = next((k for k, d in enumerate(arr)
                        if d['day'][:10] == TARGET), None)
            if idx is None or idx == 0:
                return 'notrade'
            c1, c0 = float(arr[idx]['close']), float(arr[idx - 1]['close'])
            if c0 <= 0:
                return None
            return (round(c1, 3), round(c0, 3), round((c1 - c0) / c0 * 100, 2))
        except Exception:
            time.sleep(1.2 + random.random())
    return None


def main():
    si = json.load(open(f'{BASE}/data/stock_industry.json', encoding='utf-8'))['map']
    done = {}
    if os.path.exists(OUT):
        done = json.load(open(OUT, encoding='utf-8')).get('stocks', {})

    bj = [c for c in sorted(si) if c.startswith(BJ_PRE) and c not in done]
    print(f'北交所待补 {len(bj)} 只 (已有 {len(done)})', flush=True)

    out = dict(done)
    fail, notrade = [], []
    sess = requests.Session()
    t0 = time.time()
    for i, code in enumerate(bj, 1):
        res = fetch(sess, code)
        if res is None:
            fail.append(code)
        elif res == 'notrade':
            notrade.append(code)
        else:
            c1, c0, chg = res
            out[code] = {'name': si.get(code, {}).get('name', ''),
                         'close': c1, 'pre_close': c0, 'chg_pct': chg,
                         'src': 'sina'}
        if i % 40 == 0:
            print(f'  {i}/{len(bj)} ok={len(out)} 无交易={len(notrade)} '
                  f'失败={len(fail)} {time.time()-t0:.0f}s', flush=True)
            json.dump({'date': TARGET, 'count': len(out), 'stocks': out},
                      open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
        time.sleep(0.9 + random.random() * 0.4)

    json.dump({'date': TARGET, 'count': len(out), 'fail': fail,
               'notrade': notrade, 'stocks': out},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'DONE ok={len(out)} 无交易={len(notrade)} 失败={len(fail)} '
          f'{time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
