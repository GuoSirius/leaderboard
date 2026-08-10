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

报告生成后通过 `--notify` 自动推送。所有凭据只存于本机 `notify_config.json`（已被 `.gitignore` 忽略，不入库）或仓库环境变量，**绝不会写进脚本或 HTML**。

### 第 1 步：准备配置文件

```bash
cp notify_config.example.json notify_config.json
```

然后按要用的渠道编辑 `notify_config.json`。**原则：不用的渠道把对应对象留空 `{}` 即可关闭**，避免误报。

### 第 2 步（任选其一或多选）：配置渠道

#### A. 个人微信 · Server酱（免费，微信扫码即用）

1. 打开 <https://sct.ftqq.com>，用**微信扫码**登录。
2. 登录后在「Key」/「发送消息」处复制你的 **SendKey**（形如 `SCTxxxxxxxxxxxxxxxxxxxxxxxx`）。
3. 微信关注 **「Server酱」** 服务号，推送会发到这里。
4. 免费版每日 5 条额度，足够每天一份。

`notify_config.json` 填法：

```json
{
  "wechat": {
    "provider": "serverchan",
    "key": "SCTxxxxxxxxxxxxxxxxxxxxxxxx",
    "token": ""
  },
  "email": {}
}
```

#### B. 个人微信 · PushPlus（免费，额度更大）

1. 打开 <https://www.pushplus.plus>，用**微信扫码**登录。
2. 控制台首页复制你的 **token**（一对一推送）。
3. 微信关注 **「PushPlus 推送加」** 公众号接收。
4. 免费版每日 200 条额度。

`notify_config.json` 填法：

```json
{
  "wechat": {
    "provider": "pushplus",
    "key": "",
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  },
  "email": {}
}
```

#### C. 163 邮箱（SMTP）

1. 浏览器登录 <https://mail.163.com> 网页版（**必须网页版**，客户端里找不到设置入口）。
2. 右上角 **设置 → POP3/SMTP/IMAP**。
3. 开启 **SMTP 服务（IMAP/SMTP 服务）**，按提示用绑定手机发短信验证。
4. 验证后页面会显示一串 **16 位授权码**——**一次性显示，务必立即保存**。
   ⚠️ 授权码 ≠ 登录密码，推送用的是授权码。
5. `sender` 填你的 163 邮箱；`receiver` 填接收邮箱（163 / QQ / 企业邮箱均可，默认同 `sender`）。

`notify_config.json` 填法：

```json
{
  "wechat": {},
  "email": {
    "smtp_host": "smtp.163.com",
    "smtp_port": 465,
    "sender": "你的账号@163.com",
    "auth_code": "16位授权码",
    "receiver": "接收邮箱@163.com"
  }
}
```

> 想用其它邮箱？改 `smtp_host`/`smtp_port` 即可（如 QQ 邮箱 `smtp.qq.com:465`，同样用授权码而非登录密码）。

### 第 3 步：测试推送

```bash
# 用已生成的样例报告试推一次（不联网、秒级）
python run_daily.py --only-report --notify --date 2026-07-24

# 或完整跑一遍并推送
python run_daily.py --notify
```

推送结果会在终端逐渠道打印 `[(渠道, (成功, 信息))]`，便于排查。

### 环境变量覆盖（可选）

不想写文件时，也可用环境变量驱动（CI 场景最常用）：

| 变量 | 含义 |
|---|---|
| `NOTIFY_WX_PROVIDER` | `serverchan` 或 `pushplus` |
| `NOTIFY_WX_KEY` | Server酱 SendKey |
| `NOTIFY_WX_TOKEN` | PushPlus token |
| `NOTIFY_MAIL_SENDER` | 发件 163 邮箱 |
| `NOTIFY_MAIL_AUTH` | 163 授权码 |
| `NOTIFY_MAIL_RECEIVER` | 收件邮箱（默认同 sender） |
| `NOTIFY_MAIL_HOST` / `NOTIFY_MAIL_PORT` | SMTP 主机 / 端口（默认 `smtp.163.com` / `465`） |

### 常见问题

- **微信收不到**：检查 `provider` 拼写、key/token 是否复制完整、是否已**关注对应公众号**。
- **邮件 535 认证失败**：授权码错误或 SMTP 未开启，重做第 2 步 C。
- **邮件被拒收**：163 对外发信偶有频率/内容限制；可改用 QQ 邮箱或精简内容后重试。
- **没配置任何渠道**：打印「未配置任何推送渠道」并跳过，**不影响报告生成**。

---

## 定时执行

### 本机定时（推荐，数据最完整）

用操作系统定时任务指向 `run_daily.py --notify` 即可：

- **Windows 任务计划程序**：触发器设「每工作日 17:30」，操作 `python run_daily.py --notify`（建议填写 `run_daily.bat` 绝对路径）。
- **macOS `launchd` / Linux `cron`**：`30 17 * * 1-5 python /path/to/run_daily.py --notify`。

> 本机运行能直连通达信 TCP(7709)，可拉全市场行情 + 北交所，报告最完整。

### GitHub Actions 工作流接入配置

仓库已内置 `.github/workflows/daily.yml`，可全自动在云端生成并回传报告。

#### 1. 启用工作流

- **公开仓库**：默认已启用，无需额外操作。
- **私有仓库**：`Settings → Actions → General → Allow all actions and reusable workflows` 开启。

#### 2. 权限说明（无需配 Secret）

工作流使用 GitHub 自带的 `GITHUB_TOKEN`，已在文件头声明：

```yaml
permissions:
  contents: write   # 用于将生成的 HTML 提交回仓库
```

无需你创建任何 Personal Access Token。

#### 3. 触发方式

- **定时触发**：`cron: '0 10 * * 1-5'`。GitHub 定时任务使用 **UTC**，换算：
  `10:00 UTC = 18:00 北京时间`（中国不实行夏令时，全年固定）。
  即每周一~周五 18:00（北京时间）自动跑——A 股 15:00 收盘后留有充分数据延迟。
  *想改时间？北京时间 = UTC + 8。例如 17:30 北京 → `30 9 * * 1-5`。*
- **手动触发**：仓库 `Actions` 标签页 → 选「每日A股情绪日报」→ 右上角 **Run workflow**。

#### 4. 运行结果去哪看

- **Artifacts**：每次运行在 Artifacts 区上传 `output/*.html`，可直接下载查看。
- **提交回仓库**：成功后用 `GITHUB_TOKEN` 自动 `git commit` + `push` 到 `main`（commit 信息 `chore: 自动生成日报 <日期>`）。

#### 5.（可选）让 CI 也推送微信 / 邮件

默认 CI 不带 `notify_config.json`（被 `.gitignore` 忽略），且工作流未加 `--notify`。
若想在云端也推送，用 **GitHub Secrets** 注入环境变量：

1. `Settings → Secrets and variables → Actions → New repository secret`，逐条添加：
   - `NOTIFY_WX_PROVIDER`（值如 `serverchan` 或 `pushplus`）
   - `NOTIFY_WX_KEY`（Server酱 key；用 PushPlus 则留空）
   - `NOTIFY_WX_TOKEN`（PushPlus token；用 Server酱 则留空）
   - `NOTIFY_MAIL_SENDER` / `NOTIFY_MAIL_AUTH`（163 邮箱 + 授权码）
   - `NOTIFY_MAIL_RECEIVER`（收件邮箱）
2. 把 `daily.yml` 的「生成日报」步骤改为：

```yaml
      - name: 生成日报（含推送）
        env:
          NOTIFY_WX_PROVIDER: ${{ secrets.NOTIFY_WX_PROVIDER }}
          NOTIFY_WX_KEY: ${{ secrets.NOTIFY_WX_KEY }}
          NOTIFY_WX_TOKEN: ${{ secrets.NOTIFY_WX_TOKEN }}
          NOTIFY_MAIL_SENDER: ${{ secrets.NOTIFY_MAIL_SENDER }}
          NOTIFY_MAIL_AUTH: ${{ secrets.NOTIFY_MAIL_AUTH }}
          NOTIFY_MAIL_RECEIVER: ${{ secrets.NOTIFY_MAIL_RECEIVER }}
        run: python run_daily.py --notify
```

#### 6. ⚠️ GitHub Runner 可行性说明

GitHub Runner 在**海外**，通常能访问公网 HTTP（东方财富 / 同花顺 / 新浪 / 腾讯 均可用），但 **通达信 TCP(7709) 很可能不可达**，导致「全市场广度 / 北交所」部分缺失。届时：

- ✅ 龙虎榜 + 题材 + 行业（均为 HTTP 源）仍可正常生成；
- ⚠️ 全市场宽度统计 / 北交所补齐可能缺失，报告顶部概览的股票数会偏少。

**如需完整报告，请在能直连通达信的本机运行定时任务**（见上「本机定时」）。CI 更适合作为「轻量备份 / 多设备查看」通道。

---

## 口径说明

- 龙虎榜：同股可能因多原因上榜，按「净买入绝对值最大」的一条作为主榜，原因合并展示。净买入 = 买入前五 − 卖出前五。
- 行业板块涨跌幅：东方财富板块历史 K 线接口被风控，本报告用全市场个股当日真实涨跌幅按东财口径**等权算术平均**还原（与官方比对 MAE≈0.11pct）。个股行业取自东方财富行业分类。
- 全市场样本覆盖沪深 A 股（mootdx）+ 北交所（新浪补齐）。

## 免责声明
本报告数据由公开行情接口抓取，仅供研究与复盘参考，不构成任何投资建议。行业涨跌幅为还原值，与交易软件展示可能存在细微差异。
