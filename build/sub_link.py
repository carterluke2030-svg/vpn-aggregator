"""Daily time-limited subscription link.

  new      create a fresh secret link valid for HOURS and write it to state/sub.json
  refresh  keep the active link's content current; replace it with a placeholder once expired
  post     announce the active link in the channel
"""
import base64
import html
import json
import os
import secrets
import sys
import time
import urllib.parse as up
import urllib.request

from brand import CHANNEL, rename

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state", "sub.json")
OUT = os.path.join(ROOT, "out", "s")
HOURS = float(os.environ.get("SUB_HOURS", "12"))
IRAN = 3.5 * 3600  # UTC+3:30


def load():
    return json.load(open(STATE)) if os.path.exists(STATE) else None


def save(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(st, open(STATE, "w"))


def live_content():
    return open(os.path.join(ROOT, "out", "sub.txt")).read()


def expired_content():
    dead = rename("vless://00000000-0000-0000-0000-000000000000@127.0.0.1:1?type=tcp&security=none",
                  f"⛔ این لینک منقضی شد؛ لینک جدید در {CHANNEL}")
    return base64.b64encode(dead.encode()).decode()


def write(token, content):
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, f"{token}.txt"), "w").write(content)


def url(token):
    return f"https://raw.githubusercontent.com/{os.environ['GITHUB_REPOSITORY']}/main/out/s/{token}.txt"


def new():
    st = load()
    if st and not st.get("expired"):
        write(st["token"], expired_content())
    token = secrets.token_urlsafe(9)
    st = {"token": token, "expires": time.time() + HOURS * 3600, "expired": False}
    write(token, live_content())
    save(st)
    print("new link", token)


def refresh():
    st = load()
    if not st or st.get("expired"):
        return
    if time.time() < st["expires"]:
        write(st["token"], live_content())
    else:
        write(st["token"], expired_content())
        st["expired"] = True
        save(st)
        print("link expired")


def post():
    st = load()
    until = time.strftime("%H:%M", time.gmtime(st["expires"] + IRAN))
    text = (f"🔄 <b>لینک اشتراک امروز (آپدیت خودکار)</b>\n"
            f"⏳ فعال تا ساعت {until} به وقت ایران؛ بعد از آن غیرفعال می‌شود و لینک جدید همین‌جا قرار می‌گیرد.\n\n"
            f"<code>{html.escape(url(st['token']))}</code>\n"
            "(با یک ضربه روی لینک، کپی می‌شود)\n\n"
            "📲 <b>آموزش</b>\n"
            "۱. لینک بالا را کپی کنید.\n"
            "۲. در برنامه، بخش «اشتراک / Subscription» را باز کنید و لینک را اضافه کنید:\n"
            "• Hiddify: افزودن پروفایل ← افزودن از کلیپ‌بورد\n"
            "• v2rayNG: منو ← Subscription group setting ← علامت + ← لینک را بچسبانید\n"
            "• v2box: بخش Config ← + ← Subscription\n"
            "۳. گزینه‌ی «به‌روزرسانی خودکار» را روشن کنید تا لیست خودش تازه شود.\n"
            "۴. اگر اتصال کند یا قطع شد: «آپدیت اشتراک» را بزنید (فقط «تست پینگ» لیست را عوض نمی‌کند، فقط پینگ را می‌سنجد).\n"
            "💡 در Hiddify بهترین کانفیگ خودکار انتخاب می‌شود.\n\n"
            f"📢 {html.escape(CHANNEL)}")
    data = up.urlencode({"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": text, "parse_mode": "HTML",
                         "disable_web_page_preview": "true"}).encode()
    api = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage"
    with urllib.request.urlopen(api, data, timeout=30) as r:
        print(json.load(r)["ok"])


if __name__ == "__main__":
    {"new": new, "refresh": refresh, "post": post}[sys.argv[1]]()
