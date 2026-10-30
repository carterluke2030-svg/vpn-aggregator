import base64
import re
import urllib.request

LINK_RE = re.compile(r"(?:vless|vmess|trojan|ss|hysteria2|hy2)://[^\s<>\"'`]+")
UA = {"User-Agent": "Mozilla/5.0"}


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def maybe_b64(text):
    s = "".join(text.split())
    if not s or "://" in s[:20]:
        return text
    try:
        return base64.b64decode(s + "=" * (-len(s) % 4)).decode("utf-8", "ignore")
    except Exception:
        return text


def extract(text):
    text = text.replace("&amp;", "&")
    return LINK_RE.findall(maybe_b64(text)) + LINK_RE.findall(text)


def load_sources(path):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def collect(path):
    links = {}
    for src in load_sources(path):
        kind, _, val = src.partition(":")
        url = f"https://t.me/s/{val}" if kind == "telegram" else val
        try:
            found = extract(fetch(url))
        except Exception as e:
            print(f"[skip] {src}: {e}")
            continue
        print(f"[ok] {src}: {len(found)} links")
        for l in found:
            links[l.split("#")[0]] = l
    return list(links.values())
