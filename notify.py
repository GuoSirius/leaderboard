# -*- coding: utf-8 -*-
"""日报生成后的推送模块：个人微信(Server酱/PushPlus) + 163邮箱(SMTP)。

配置来源（notify_config.json，凭据不要写进脚本/提交）：
{
  "wechat": {
    "provider": "serverchan",          # serverchan | pushplus
    "key": "SCTxxxxxxxx",              # serverchan 的 SendKey
    "token": "xxxxxxxx"                # pushplus 的 token（provider=pushplus 时用）
  },
  "email": {
    "smtp_host": "smtp.163.com",
    "smtp_port": 465,
    "sender": "you@163.com",
    "auth_code": "你的163授权码",       # 不是登录密码，是邮箱设置里生成的授权码
    "receiver": "you@163.com"          # 可省略，默认同 sender
  }
}
也可改用环境变量：NOTIFY_WX_KEY / NOTIFY_WX_PROVIDER / NOTIFY_WX_TOKEN /
NOTIFY_MAIL_SENDER / NOTIFY_MAIL_AUTH / NOTIFY_MAIL_RECEIVER / NOTIFY_MAIL_HOST / NOTIFY_MAIL_PORT
"""
import os, json, smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import requests

CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notify_config.json")


def load_cfg():
    cfg = {}
    if os.path.exists(CFG_PATH):
        try:
            cfg.update(json.load(open(CFG_PATH, encoding="utf-8")))
        except Exception:
            pass
    # 环境变量覆盖
    wx = cfg.setdefault("wechat", {})
    if os.environ.get("NOTIFY_WX_KEY"):
        wx["key"] = os.environ["NOTIFY_WX_KEY"]
    if os.environ.get("NOTIFY_WX_TOKEN"):
        wx["token"] = os.environ["NOTIFY_WX_TOKEN"]
    if os.environ.get("NOTIFY_WX_PROVIDER"):
        wx["provider"] = os.environ["NOTIFY_WX_PROVIDER"]
    em = cfg.setdefault("email", {})
    for k, ev in (("sender", "NOTIFY_MAIL_SENDER"), ("auth_code", "NOTIFY_MAIL_AUTH"),
                  ("receiver", "NOTIFY_MAIL_RECEIVER"), ("smtp_host", "NOTIFY_MAIL_HOST"),
                  ("smtp_port", "NOTIFY_MAIL_PORT")):
        if os.environ.get(ev):
            em[k] = os.environ[ev]
    return cfg


def push_wechat(title, content, cfg):
    w = cfg.get("wechat") or {}
    provider = (w.get("provider") or "serverchan").lower()
    try:
        if provider == "serverchan":
            key = w.get("key") or os.environ.get("NOTIFY_WX_KEY")
            if not key:
                return False, "缺少 serverchan key"
            url = f"https://sctapi.ftqq.com/{key}.send"
            r = requests.post(url, data={"title": title, "desp": content},
                             timeout=15)
            d = r.json()
            return (d.get("code") == 0 or d.get("errno") == 0), d
        elif provider == "pushplus":
            token = w.get("token") or os.environ.get("NOTIFY_WX_TOKEN")
            if not token:
                return False, "缺少 pushplus token"
            r = requests.post("https://www.pushplus.plus/send",
                              json={"token": token, "title": title,
                                    "content": content, "template": "markdown"},
                              timeout=15)
            d = r.json()
            return d.get("code") == 200, d
        else:
            return False, f"未知 provider: {provider}"
    except Exception as e:
        return False, repr(e)


def push_email(subject, html_path, cfg):
    e = cfg.get("email") or {}
    sender = e.get("sender")
    auth = e.get("auth_code")
    if not (sender and auth):
        return False, "缺少 email sender/auth_code"
    host = e.get("smtp_host", "smtp.163.com")
    port = int(e.get("smtp_port", 465))
    receiver = e.get("receiver") or sender
    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = receiver
        msg["Subject"] = subject
        # 纯文本摘要
        msg.attach(MIMEText("A股每日市场情绪日报，详见附件 HTML。",
                            _subtype="plain", _charset="utf-8"))
        # HTML 附件
        with open(html_path, "rb") as f:
            att = MIMEApplication(f.read(), _subtype="html")
        att.add_header("Content-Disposition", "attachment",
                       filename=os.path.basename(html_path))
        msg.attach(att)

        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=ctx) as s:
            s.login(sender, auth)
            s.sendmail(sender, [receiver], msg.as_string())
        return True, f"已发送至 {receiver}"
    except Exception as ex:
        return False, repr(ex)


def notify(title, content, html_path, cfg=None):
    """返回 [(渠道, (成功bool, 信息)), ...]"""
    cfg = cfg or load_cfg()
    res = []
    if cfg.get("wechat"):
        res.append(("wechat", push_wechat(title, content, cfg)))
    if cfg.get("email"):
        res.append(("email", push_email(title, html_path, cfg)))
    if not res:
        res.append(("none", (False, "未配置任何推送渠道（notify_config.json 为空）")))
    return res


if __name__ == "__main__":
    # 自检：无配置时优雅退出
    c = load_cfg()
    print("wechat 配置:", bool(c.get("wechat")))
    print("email  配置:", bool(c.get("email")))
    print("notify_config.json 路径:", CFG_PATH)
