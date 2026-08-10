# A股每日市场情绪日报（龙虎榜 · 题材热点 · 行业轮动）

一键抓取真实行情，生成**单文件、可离线打开**的暗色复盘风 HTML 日报。

- **① 龙虎榜资金博弈**（东方财富）：当日全部上榜个股、净买入排名、上榜原因
- **② 题材热点归因**（同花顺）：强势股题材标签词频、热门题材与成分股
- **③ 行业板块轮动**（东方财富行业分类 + 全市场个股等权还原）：领涨/领跌行业、成分股涨跌
- 顶部概览 + 内联 SVG 图表（题材热度、行业涨跌榜、龙虎榜净买入），涨红跌绿，金额以 ¥/亿/万 呈现
- 页脚标注全部数据来源与交易日期

> 数据全部由公开行情接口实时抓取，非模拟。仅用于研究与复盘，不构成投资建议。

---

## 目录结构

```
.
├── run_daily.py                 # 一键编排整条流水线（入口）
├── run_daily.bat                # Windows 双击运行
├── notify.py                    # 生成后推送（个人微信 Server酱/PushPlus + 163邮箱）
├── notify_config.example.json   # 推送配置样例（复制为 notify_config.json 后填真实值）
├── requirements.txt
├── .github/workflows/daily.yml  # GitHub Actions 定时执行
├── scripts/                     # 流水线各步骤脚本
│   ├── fetch_lhb_ths.py         # ① 龙虎榜 + 同花顺题材
│   ├── fetch_industry_map.py    # 行业映射 / 板块列表（参考库，缓存）
│   ├── fetch_tencent_mcap.py    # 流通市值（参考库，缓存）
│   ├── fetch_mootdx_series.py    # 全市场30日行情序列（通达信 TCP, mootdx）
│   ├── fetch_bj.py              # 北交所补齐（新浪）
│   ├── compute_lhb.py           # 龙虎榜按个股聚合
│   ├── compute_boards.py        # 行业板块等权还原
│   ├── make_report.py           # 渲染 HTML
│   ├── build_report.py          # SVG/格式化工具
│   └── report_css.py            # 内联 CSS
├── examples/
│   └── sample-2026-07-24.html   # 一份样例报告，克隆后即可直接打开查看
├── data/                        # 运行时拉取的数据（Git 忽略）
└── output/                      # 生成的 HTML（Git 忽略；CI 会回传）
```

---

## 环境要求

- Python 3.11+
- 网络可访问：通达信 TCP(7709, mootdx)、东方财富、同花顺、新浪、腾讯
- 依赖：`requests`、`mootdx`、`pandas`

```bash
pip install -r requirements.txt
```

> 提示：`mootdx` 负责拉全市场行情（走通达信行情服务器，不封 IP，但**仅覆盖沪深主板/创业板/科创板/深市，不含北交所**）；北交所由 `fetch_bj.py` 经新浪补齐。

---

## 快速开始（手动）

```bash
# 生成最近交易日报告（周末自动回退到周五）
python run_daily.py

# 指定历史交易日
python run_daily.py --date 2026-08-07

# 已有数据，仅重新渲染 HTML（不联网，秒级）
python run_daily.py --only-report

# 强制刷新行业映射 / 流通市值参考库
python run_daily.py --refresh-ref

# 跳过北交所补齐，跑得更快
python run_daily.py --skip-bj
```

输出：`output/A股市场情绪日报_<YYYY-MM-DD>.html`（单文件，双击即可在浏览器打开）。

Windows 用户可直接双击 `run_daily.bat`。

### 命令行参数

| 参数 | 说明 |
|---|---|
| `--date YYYY-MM-DD` | 指定交易日，缺省=最近交易日 |
| `--only-report` | 跳过抓取，仅重新渲染 HTML |
| `--refresh-ref` | 强制刷新参考库（行业映射 / 流通市值） |
| `--skip-bj` | 跳过北交所(新浪)补齐 |
| `--notify` | 生成后推送微信 / 邮件（需 `notify_config.json`） |

---

## 自动推送（微信 / 163 邮箱）

报告生成后可自动推送。配置见 `notify_config.example.json`（复制为 `notify_config.json`）：

- **个人微信**：通过 **Server酱（sct.ftqq.com）** 或 **PushPlus（pushplus.plus）**。用个人微信扫码关注其公众号，拿到 key/token（免费额度足够每日一份）。
- **163 邮箱**：SMTP `smtp.163.com:465`（SSL），需在 163 邮箱设置中生成 **授权码**（不是登录密码）。

```bash
python run_daily.py --notify          # 生成并推送
python run_daily.py --only-report --notify --date 2026-07-24   # 先试推一次
```

凭据仅存于本机 `notify_config.json`，不会进入脚本或报告。

---

## 定时执行

### 本机定时（推荐，数据最完整）
直接用操作系统定时任务指向 `run_daily.py --notify` 即可（Windows 任务计划程序 / macOS `launchd` / Linux `cron`）。

### GitHub Actions（见 `.github/workflows/daily.yml`）
已内置工作日 18:00（北京时间）定时 + 手动触发。它会安装依赖、执行全流程、把生成的 HTML 作为 **Actions 产物** 上传，并提交回仓库 `output/`。

⚠️ **GitHub Runner 可行性说明**：GitHub 的 Runner 在海外，通常能访问公网 HTTP（东方财富 / 同花顺 / 新浪 / 腾讯 均可用），但 **通达信 TCP(7709) 很可能不可达**，导致「全市场广度 / 北交所」部分缺失。届时龙虎榜 + 题材 + 行业（均为 HTTP 源）仍可正常生成，仅全市场宽度统计不完整。**如需完整报告，请在能直连通达信的本机运行。**

---

## 口径说明

- 龙虎榜：同股可能因多原因上榜，按「净买入绝对值最大」的一条作为主榜，原因合并展示。净买入 = 买入前五 − 卖出前五。
- 行业板块涨跌幅：东方财富板块历史 K 线接口被风控，本报告用全市场个股当日真实涨跌幅按东财口径**等权算术平均**还原（与官方比对 MAE≈0.11pct）。个股行业取自东方财富行业分类。
- 全市场样本覆盖沪深 A 股（mootdx）+ 北交所（新浪补齐）。

## 免责声明
本报告数据由公开行情接口抓取，仅供研究与复盘参考，不构成任何投资建议。行业涨跌幅为还原值，与交易软件展示可能存在细微差异。
