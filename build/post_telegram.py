import base64
import html
import json
import os
import re
import time
import urllib.parse as up
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state", "posted.json")
COUNT = int(os.environ.get("POST_COUNT", "10"))
HOLD_HOURS = 24
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]
SUB_URL = os.environ.get("SUB_URL", "")


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
    posted = {}
    if os.path.exists(STATE):
        posted = json.load(open(STATE))
    now = time.time()
    posted = {k: t for k, t in posted.items() if now - t < HOLD_HOURS * 3600}
    fresh = [l for l in links if key(l) not in posted][:COUNT]
    if not fresh:
        print("nothing new to post")
        return
    # Telegram text limit is 4096 chars: send in chunks
    chunks, cur = [], ""
    for l in fresh:
        label = re.sub(r"[^a-z0-9]", "", l.split("://")[0])
        item = f"<code>{html.escape(l.split('#')[0])}</code>\n\n"
        if len(cur) + len(item) > 3500:
            chunks.append(cur)
            cur = ""
        cur += item
    chunks.append(cur)
    footer = f"\n\n{html.escape(CHAT)}"
    if SUB_URL:
        footer = f"\n\nلینک اشتراک (آپدیت خودکار):\n<code>{html.escape(SUB_URL)}</code>" + footer
    for i, c in enumerate(chunks):
        head = "🔵 کانفیگ‌های جدید (روی متن بزنید تا کپی شود)\n\n" if i == 0 else ""
        send(head + c + (footer if i == len(chunks) - 1 else ""))
        time.sleep(1)
    for l in fresh:
        posted[key(l)] = now
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(posted, open(STATE, "w"))
    print(f"posted {len(fresh)}")


if __name__ == "__main__":
    main()
