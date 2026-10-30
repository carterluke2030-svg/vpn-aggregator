import base64
import json
import os
import urllib.parse as up

CHANNEL = os.environ.get("CHANNEL", "@BlueRay_VPN")


def remark(n):
    return f"🔵 {CHANNEL} ⚡ کانفیگ جدید هر ۳ ساعت | {n}"


def rename(link, name):
    """Set the display name of a proxy link (vmess keeps it in its JSON, others in the #fragment)."""
    if link.startswith("vmess://"):
        try:
            body = link[8:].split("#")[0]
            j = json.loads(base64.b64decode(body + "=" * (-len(body) % 4)))
            j["ps"] = name
            return "vmess://" + base64.b64encode(json.dumps(j, ensure_ascii=False).encode()).decode()
        except Exception:
            return link
    return link.split("#")[0] + "#" + up.quote(name)
