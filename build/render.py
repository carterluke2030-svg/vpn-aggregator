import base64
import json

from brand import remark, rename

URLTEST_INTERVAL = "30s"


def sub_txt(links):
    return base64.b64encode("\n".join(links).encode()).decode()


def singbox(outbounds):
    tags = [o["tag"] for o in outbounds]
    return {
        "outbounds": [
            {"type": "selector", "tag": "select", "outbounds": ["auto"] + tags, "default": "auto"},
            {"type": "urltest", "tag": "auto", "outbounds": tags, "url": "http://cp.cloudflare.com/generate_204",
             "interval": URLTEST_INTERVAL, "tolerance": 50, "idle_timeout": "30m"},
            *outbounds,
            {"type": "direct", "tag": "direct"},
        ],
        "route": {"final": "select"},
    }


def write(links, outbounds, outdir):
    links = [rename(l, remark(i + 1)) for i, l in enumerate(links)]
    outbounds = [{**o, "tag": remark(i + 1)} for i, o in enumerate(outbounds)]
    open(f"{outdir}/sub.txt", "w").write(sub_txt(links))
    json.dump(singbox(outbounds), open(f"{outdir}/singbox.json", "w"), ensure_ascii=False)
