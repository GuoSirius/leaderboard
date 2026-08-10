# -*- coding: utf-8 -*-
"""报告图表组件与格式化工具(被 make_report.py 引用)。"""
import json, os, html, datetime

BASE = os.path.join(os.path.dirname(__file__), "..")
D = lambda n: os.path.join(BASE, "data", n)
OUT = os.path.join(BASE, "output", "A股市场情绪日报_20260724.html")

UP, DOWN, FLAT = "#ff4d4f", "#12c48b", "#8b93a7"
GOLD = "#e8b339"


def load(n):
    with open(D(n), encoding="utf-8") as f:
        return json.load(f)


def money(v):
    """金额格式化: 亿 / 万"""
    if v is None:
        return "—"
    a = abs(v)
    if a >= 1e8:
        return f"{v/1e8:,.2f}亿"
    if a >= 1e4:
        return f"{v/1e4:,.0f}万"
    return f"{v:,.0f}"


def yuan(v):
    if v is None:
        return "—"
    s = money(v)
    return ("-¥" + s[1:]) if s.startswith("-") else ("¥" + s)


def cls(v):
    return "up" if v > 0 else ("down" if v < 0 else "flat")


def col(v):
    return UP if v > 0 else (DOWN if v < 0 else FLAT)


def pct(v, plus=True):
    if v is None:
        return "—"
    return f"{v:+.2f}%" if plus else f"{v:.2f}%"


def esc(s):
    return html.escape(str(s or ""))


# ══════════════════════ SVG 组件 ══════════════════════
def svg_diverging(items, width=1180, row_h=26, pad_l=112, pad_r=96,
                  value_fmt=lambda v: f"{v:+.2f}", title_key="label",
                  val_key="value", sub_key=None, unit=""):
    """双向横条(0 为中轴, 正红负绿)。items: [{label, value, sub}]"""
    n = len(items)
    h = n * row_h + 34
    inner = width - pad_l - pad_r
    vmax = max(abs(i[val_key]) for i in items) or 1
    zero = pad_l + inner * 0.5
    half = inner * 0.5 - 4

    p = [f'<svg viewBox="0 0 {width} {h}" width="100%" '
         f'preserveAspectRatio="xMidYMin meet" role="img">']
    # 网格
    for f in (-1, -0.5, 0, 0.5, 1):
        x = zero + half * f
        p.append(f'<line x1="{x:.1f}" y1="18" x2="{x:.1f}" y2="{h-14}" '
                 f'stroke="{"#39445c" if f == 0 else "#20273a"}" stroke-width="1"/>')
        p.append(f'<text x="{x:.1f}" y="12" fill="#6b7488" font-size="10" '
                 f'text-anchor="middle">{value_fmt(vmax*f)}{unit}</text>')

    for k, it in enumerate(items):
        y = 22 + k * row_h
        v = it[val_key]
        w = abs(v) / vmax * half
        c = col(v)
        x0 = zero if v >= 0 else zero - w
        p.append(f'<rect x="{x0:.1f}" y="{y+4}" width="{max(w,1.2):.1f}" '
                 f'height="{row_h-11}" fill="{c}" fill-opacity="0.82" rx="2"/>')
        p.append(f'<text x="{pad_l-8}" y="{y+row_h-9}" fill="#c8d0e0" '
                 f'font-size="11.5" text-anchor="end">{esc(it[title_key])}</text>')
        tx = (zero + w + 7) if v >= 0 else (zero - w - 7)
        anc = "start" if v >= 0 else "end"
        p.append(f'<text x="{tx:.1f}" y="{y+row_h-9}" fill="{c}" font-size="11.5" '
                 f'text-anchor="{anc}" font-weight="600">'
                 f'{value_fmt(v)}{unit}</text>')
        if sub_key and it.get(sub_key):
            sx = width - pad_r + 74
            p.append(f'<text x="{sx}" y="{y+row_h-9}" fill="#7d8799" font-size="10.5" '
                     f'text-anchor="end">{esc(it[sub_key])}</text>')
    p.append("</svg>")
    return "".join(p)


def svg_bars(items, width=1180, row_h=27, pad_l=132, pad_r=150):
    """单向横条(题材热度)。items: [{label, value, sub, chg}]"""
    n = len(items)
    h = n * row_h + 30
    inner = width - pad_l - pad_r
    vmax = max(i["value"] for i in items) or 1
    p = [f'<svg viewBox="0 0 {width} {h}" width="100%" '
         f'preserveAspectRatio="xMidYMin meet" role="img">']
    for f in (0, 0.25, 0.5, 0.75, 1):
        x = pad_l + inner * f
        p.append(f'<line x1="{x:.1f}" y1="16" x2="{x:.1f}" y2="{h-12}" '
                 f'stroke="#20273a" stroke-width="1"/>')
        p.append(f'<text x="{x:.1f}" y="11" fill="#6b7488" font-size="10" '
                 f'text-anchor="middle">{vmax*f:.0f}</text>')
    for k, it in enumerate(items):
        y = 20 + k * row_h
        w = it["value"] / vmax * inner
        c = col(it.get("chg", 1))
        p.append(f'<defs><linearGradient id="g{k}" x1="0" x2="1">'
                 f'<stop offset="0" stop-color="{c}" stop-opacity="0.95"/>'
                 f'<stop offset="1" stop-color="{c}" stop-opacity="0.45"/>'
                 f'</linearGradient></defs>')
        p.append(f'<rect x="{pad_l}" y="{y+4}" width="{max(w,2):.1f}" '
                 f'height="{row_h-11}" fill="url(#g{k})" rx="2"/>')
        p.append(f'<text x="{pad_l-8}" y="{y+row_h-9}" fill="#d3daea" '
                 f'font-size="12" text-anchor="end">{esc(it["label"])}</text>')
        p.append(f'<text x="{pad_l+w+8:.1f}" y="{y+row_h-9}" fill="#e6ebf5" '
                 f'font-size="11.5" font-weight="600">{it["value"]:.0f} 只</text>')
        if it.get("sub"):
            p.append(f'<text x="{width-6}" y="{y+row_h-9}" fill="{c}" '
                     f'font-size="11" text-anchor="end">{esc(it["sub"])}</text>')
    p.append("</svg>")
    return "".join(p)


def svg_breadth(up, down, flat, limit_up, limit_down, width=1180, h=76):
    """市场宽度带状图"""
    tot = up + down + flat or 1
    p = [f'<svg viewBox="0 0 {width} {h}" width="100%" '
         f'preserveAspectRatio="none" role="img">']
    x = 0
    segs = [(up, UP, f"上涨 {up}"), (flat, "#4b5568", f"平盘 {flat}"),
            (down, DOWN, f"下跌 {down}")]
    for v, c, lab in segs:
        w = v / tot * width
        p.append(f'<rect x="{x:.1f}" y="20" width="{w:.1f}" height="30" '
                 f'fill="{c}" fill-opacity="0.88"/>')
        if w > 78:
            p.append(f'<text x="{x+w/2:.1f}" y="40" fill="#0a0e14" font-size="13" '
                     f'font-weight="700" text-anchor="middle">{lab}</text>')
        x += w
    p.append(f'<text x="0" y="13" fill="{UP}" font-size="11.5">'
             f'涨停 {limit_up} 家</text>')
    p.append(f'<text x="{width}" y="13" fill="{DOWN}" font-size="11.5" '
             f'text-anchor="end">跌停 {limit_down} 家</text>')
    p.append(f'<text x="0" y="66" fill="#7d8799" font-size="11">'
             f'涨跌比 {up/(down or 1):.2f} : 1</text>')
    p.append(f'<text x="{width}" y="66" fill="#7d8799" font-size="11" '
             f'text-anchor="end">统计样本 {tot} 只</text>')
    p.append("</svg>")
    return "".join(p)
