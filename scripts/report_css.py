# -*- coding: utf-8 -*-
"""报告样式(内联 CSS)"""

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#080b11; --panel:#111722; --panel2:#0d131d; --bd:#1e2736;
  --tx:#dfe5f0; --mut:#828da3; --dim:#5d6879;
  --up:#ff4d4f; --down:#12c48b; --flat:#8b93a7; --gold:#e8b339;
}
html{-webkit-text-size-adjust:100%}
body{
  background:var(--bg); color:var(--tx); font-size:14px; line-height:1.55;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",
    "Hiragino Sans GB","Microsoft YaHei",sans-serif;
  padding:0 0 60px;
}
.num{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,
  "Liberation Mono",monospace; font-variant-numeric:tabular-nums}
.wrap{max-width:1280px;margin:0 auto;padding:0 22px}
.up{color:var(--up)} .down{color:var(--down)} .flat{color:var(--flat)}

/* ── 页头 ── */
header{
  border-bottom:1px solid var(--bd); padding:26px 0 20px; margin-bottom:22px;
  background:linear-gradient(180deg,#0e141f 0%,rgba(8,11,17,0) 100%);
}
.htop{display:flex;align-items:flex-end;justify-content:space-between;
  flex-wrap:wrap;gap:14px}
h1{font-size:25px;font-weight:700;letter-spacing:.5px}
h1 .bar{color:var(--gold)}
.hsub{color:var(--mut);font-size:12.5px;margin-top:6px}
.hdate{text-align:right}
.hdate .d{font-size:22px;font-weight:700;color:var(--gold)}
.hdate .w{font-size:11.5px;color:var(--mut);letter-spacing:1px}
.badge{display:inline-block;padding:2px 8px;border:1px solid var(--bd);
  border-radius:3px;font-size:11px;color:var(--mut);margin-left:6px}

/* ── KPI ── */
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:24px}
.kpi{background:var(--panel);border:1px solid var(--bd);border-radius:5px;
  padding:13px 14px;position:relative;overflow:hidden}
.kpi::before{content:"";position:absolute;left:0;top:0;bottom:0;width:2px;
  background:var(--gold);opacity:.65}
.kpi .k{font-size:11px;color:var(--mut);letter-spacing:.5px;margin-bottom:7px}
.kpi .v{font-size:21px;font-weight:700;line-height:1.15}
.kpi .u{font-size:12px;font-weight:500;color:var(--mut);margin-left:2px}
.kpi .s{font-size:11px;color:var(--dim);margin-top:5px}
.kpi.g::before{background:var(--up)} .kpi.r::before{background:var(--down)}

/* ── 区块 ── */
section{margin-bottom:30px}
.sh{display:flex;align-items:baseline;gap:11px;padding-bottom:9px;
  margin-bottom:14px;border-bottom:1px solid var(--bd)}
.sh .no{font-size:11px;color:var(--gold);border:1px solid var(--gold);
  border-radius:2px;padding:1px 6px;font-weight:700;opacity:.9}
.sh h2{font-size:16.5px;font-weight:650;letter-spacing:.3px}
.sh .src{margin-left:auto;font-size:11px;color:var(--dim)}
.panel{background:var(--panel);border:1px solid var(--bd);border-radius:5px;
  padding:14px 16px;margin-bottom:13px}
.ptitle{font-size:12.5px;color:var(--mut);margin-bottom:9px;
  display:flex;justify-content:space-between;align-items:center}
.ptitle b{color:var(--tx);font-weight:600;font-size:13px}

/* ── 表格 ── */
.tw{overflow-x:auto;border:1px solid var(--bd);border-radius:5px;
  background:var(--panel2)}
.tw.scroll{max-height:560px;overflow-y:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
thead th{position:sticky;top:0;background:#161d2b;color:var(--mut);
  font-weight:600;font-size:11.5px;text-align:right;padding:9px 10px;
  white-space:nowrap;border-bottom:1px solid var(--bd);z-index:2;
  letter-spacing:.3px}
thead th:first-child,thead th.l{text-align:left}
tbody td{padding:7px 10px;text-align:right;white-space:nowrap;
  border-bottom:1px solid #161d29}
tbody td.l{text-align:left}
tbody tr:nth-child(even){background:rgba(255,255,255,.014)}
tbody tr:hover{background:rgba(232,179,57,.07)}
tbody tr:last-child td{border-bottom:none}
.code{color:var(--dim);font-size:11.5px}
.nm{font-weight:600;color:#eef2f9}
.rsn{color:var(--mut);font-size:11.5px;max-width:330px;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap;display:inline-block;
  vertical-align:bottom}
.tag{display:inline-block;background:#1b2334;color:#9fb0cc;font-size:10.5px;
  padding:1px 5px;border-radius:2px;margin:0 3px 2px 0;border:1px solid #232d40}
.tag.hot{background:#2a1c1c;color:#ffa8a8;border-color:#402525}
.rk{color:var(--dim);font-size:11px;width:26px}
.pill{display:inline-block;padding:1px 6px;border-radius:9px;font-size:10.5px;
  border:1px solid currentColor;opacity:.9}

/* ── 题材卡 ── */
.tgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.tcard{background:var(--panel);border:1px solid var(--bd);border-radius:5px;
  padding:11px 13px}
.tcard .th{display:flex;justify-content:space-between;align-items:baseline;
  margin-bottom:7px}
.tcard .tn{font-size:13.5px;font-weight:650;color:#f0f4fa}
.tcard .tc{font-size:11px;color:var(--mut)}
.tcard .tl{font-size:11.5px;color:var(--mut);line-height:1.75}
.tcard .tl b{color:#c3cddd;font-weight:500}

.note{font-size:11.5px;color:var(--dim);line-height:1.75;
  background:var(--panel2);border:1px solid var(--bd);border-left:2px solid var(--gold);
  border-radius:4px;padding:10px 13px;margin-top:11px}
.note b{color:var(--mut)}

footer{border-top:1px solid var(--bd);margin-top:34px;padding-top:18px;
  font-size:11.5px;color:var(--dim);line-height:1.9}
footer b{color:var(--mut);font-weight:600}
footer .srcs{display:flex;flex-wrap:wrap;gap:8px;margin:9px 0}
footer .s1{background:var(--panel);border:1px solid var(--bd);border-radius:3px;
  padding:4px 9px;color:var(--mut);font-size:11px}

@media (max-width:1080px){
  .kpis{grid-template-columns:repeat(3,1fr)}
  .tgrid{grid-template-columns:repeat(2,1fr)}
}
@media (max-width:680px){
  .kpis{grid-template-columns:repeat(2,1fr)}
  .tgrid{grid-template-columns:1fr}
  .wrap{padding:0 12px}
}
"""
