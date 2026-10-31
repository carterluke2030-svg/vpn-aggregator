import base64
import html
import json
import os
import socket
import time
import urllib.parse as up
import urllib.request

from brand import CHANNEL, rename, remark
from convert import to_outbound

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


FA = {"DE": "آلمان", "US": "آمریکا", "NL": "هلند", "GB": "انگلیس", "FR": "فرانسه", "FI": "فنلاند", "SE": "سوئد",
      "TR": "ترکیه", "CA": "کانادا", "SG": "سنگاپور", "JP": "ژاپن", "HK": "هنگ‌کنگ", "AE": "امارات", "RU": "روسیه",
      "PL": "لهستان", "CH": "سوئیس", "IT": "ایتالیا", "ES": "اسپانیا", "UA": "اوکراین", "IN": "هند",
      "KR": "کره جنوبی", "AU": "استرالیا", "IE": "ایرلند", "NO": "نروژ", "AT": "اتریش", "CZ": "چک", "RO": "رومانی",
      "LT": "لیتوانی", "BG": "بلغارستان", "LV": "لتونی", "EE": "استونی", "KZ": "قزاقستان", "AM": "ارمنستان",
      "BR": "برزیل", "TW": "تایوان", "MD": "مولداوی", "BE": "بلژیک", "DK": "دانمارک", "PT": "پرتغال", "IL": "اسرائیل"}


def country(link):
    """(flag, name) of the server behind a link, or None. CDN-fronted servers show the CDN's country."""
    try:
        ip = socket.gethostbyname(to_outbound(link, "x")["server"])
        with urllib.request.urlopen(f"https://ipwho.is/{ip}?fields=success,country,country_code", timeout=10) as r:
            j = json.load(r)
        if j.get("success"):
            cc = j["country_code"]
            return "".join(chr(0x1F1E6 + ord(c) - 65) for c in cc), FA.get(cc, j["country"])
    except Exception:
        pass
    return None


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
    places = list(dict.fromkeys(c for c in map(country, fresh) if c))
    lines = [f"🔵 <b>{len(chosen)} کانفیگ جدید | BlueRay VPN</b>",
             f"<blockquote expandable><code>{html.escape(chr(10).join(chosen))}</code></blockquote>"]
    if places:
        lines.append("🌍 " + " · ".join(f"{f} {n}" for f, n in places))
    if os.environ.get("TUTORIAL_URL"):
        lines.append(f"📚 آموزش اتصال: {html.escape(os.environ['TUTORIAL_URL'])}")
    lines.append(f"📢 {html.escape(CHANNEL)}")
    text = "\n".join(lines)
    r = send(text)
    print([e['type'] for e in r['result'].get('entities', [])], r['result']['message_id'])
    for l in fresh:
        posted[key(l)] = now
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(posted, open(STATE, "w"))
    print(f"posted {len(fresh)}")


if __name__ == "__main__":
    main()
