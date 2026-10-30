# VPN aggregator

1. Put sources in `sources.txt` (`url:...` or `telegram:channel`).
2. Push to a GitHub repo; Actions runs `build/main.py` every 20 min and commits `out/`.
3. Deploy `worker/worker.js` on Cloudflare; set variable `BASE` = `https://raw.githubusercontent.com/USER/REPO/main/out`.
4. Add the Worker URL as a subscription in Hiddify / v2rayNG / v2box.

Local run: `python3 build/main.py` (install `sing-box` for real connection tests).

- Hiddify/sing-box clients get `singbox.json` (urltest auto-switch, interval in `build/render.py`).
- Other clients get `sub.txt` (plain list, no auto-switch).
