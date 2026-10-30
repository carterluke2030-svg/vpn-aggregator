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
    # Keep the whole message under Telegram's 4096-char limit.
    chosen, size = [], 0
    for l in fresh[:COUNT]:
        line = rename(l, remark(len(chosen) + 1))
        if size + len(line) + 1 > 2900 and chosen:
            break
        chosen.append(line)
        size += len(line) + 1
    fresh = fresh[:len(chosen)]
    # Collapsed quote (3 lines) holding one <code> span: one tap copies every config.
    text = (f"🔵 <b>{len(chosen)} کانفیگ جدید | BlueRay VPN</b>\n"
            f"<blockquote expandable><code>{html.escape(chr(10).join(chosen))}</code></blockquote>\n"
            "👆 روی کادر بزنید تا همه‌ی کانفیگ‌ها یکجا کپی شوند، بعد در برنامه «افزودن از کلیپ‌بورد» را بزنید\n\n"
            "🚀 سرعت بالا | 📶 مناسب همه‌ی اپراتورها\n"
            "⚠️ اگر یکی وصل نشد، چند کانفیگ دیگر را هم امتحان کنید\n"
            "❤️ اگر به کارتان آمد، برای دوستانتان بفرستید\n"
            "🔔 اعلان کانال را روشن کنید تا کانفیگ جدید را از دست ندهید\n\n"
            f"📢 {html.escape(CHANNEL)}")
    r = send(text)
    print([e['type'] for e in r['result'].get('entities', [])], r['result']['message_id'])
    for l in fresh:
        posted[key(l)] = now
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(posted, open(STATE, "w"))
    print(f"posted {len(fresh)}")


if __name__ == "__main__":
    main()
