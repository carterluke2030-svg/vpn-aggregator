import base64
import html
import json
import os
import time
import urllib.parse as up
import urllib.request

from brand import CHANNEL, rename, remark

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state", "posted.json")
COUNT = int(os.environ.get("POST_COUNT", "10"))
HOLD_HOURS = 24
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]


def key(link):
    u = up.urlparse(link)
    return f"{u.scheme}://{u.hostname}:{u.port}"


def send(text):
    data = up.urlencode({"chat_id": CHAT, "text": text, "parse_mode": "HTML",
                         "disable_web_page_preview": "true"}).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data, timeout=30) as r:
        return json.load(r)


def main():
    links = base64.b64decode(open(os.path.join(ROOT, "out", "sub.txt")).read()).decode().split()
    posted = json.load(open(STATE)) if os.path.exists(STATE) else {}
    now = time.time()
    posted = {k: t for k, t in posted.items() if now - t < HOLD_HOURS * 3600}
    fresh, seen = [], set()
    for l in links:
        k = key(l)
        if k not in posted and k not in seen:
            seen.add(k)
            fresh.append(l)
    fresh = fresh[:COUNT]
    if not fresh:
        print("nothing new to post")
        return
    # One <pre> block: a single tap copies all links; lines don't wrap, so the post stays short.
    block = "\n".join(rename(l, remark(i + 1)) for i, l in enumerate(fresh))
    text = (f"🔵 <b>{len(fresh)} کانفیگ جدید</b>\n"
            "با یک ضربه روی کادر، همه‌ی کانفیگ‌ها کپی می‌شوند ← در برنامه «افزودن از کلیپ‌بورد» را بزنید\n"
            f"<pre>{html.escape(block)}</pre>\n"
            f"📢 {html.escape(CHANNEL)} | برای کانفیگ‌های تازه هر چند ساعت سر بزنید")
    send(text)
    for l in fresh:
        posted[key(l)] = now
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(posted, open(STATE, "w"))
    print(f"posted {len(fresh)}")


if __name__ == "__main__":
    main()
