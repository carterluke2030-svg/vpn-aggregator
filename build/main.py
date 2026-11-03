import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from collect import collect
from convert import to_outbound
from probe import prefilter, real_test
from render import write

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEP = int(os.environ.get("KEEP", "100"))
KEEP_ME = int(os.environ.get("KEEP_ME", "200"))
PERSONAL_ID = os.environ.get("PERSONAL_ID", "")
HISTORY = os.path.join(ROOT, "state", "history.json")
INSECURE_PENALTY = 400  # plain ss/vmess/ws without TLS get blocked fastest in Iran
STABLE_BONUS = 30       # per successful run in the last 24h, up to 12 runs


def server_key(o):
    return f"{o['type']}://{o['server']}:{o['server_port']}"


def rank(results):
    """Sort by latency, favouring encrypted transports and configs that kept working across runs."""
    hist = json.load(open(HISTORY)) if os.path.exists(HISTORY) else {}
    now = time.time()
    for _, o, _ in results:
        hist.setdefault(server_key(o), []).append(now)
    hist = {k: [t for t in v if now - t < 86400] for k, v in hist.items()}
    hist = {k: v for k, v in hist.items() if v}
    os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
    json.dump(hist, open(HISTORY, "w"))

    def score(r):
        _, o, ms = r
        secure = o["type"] == "hysteria2" or (o.get("tls") or {}).get("enabled")
        return ms + (0 if secure else INSECURE_PENALTY) - min(len(hist.get(server_key(o), [])), 12) * STABLE_BONUS
    return sorted(results, key=score)


def main():
    links = collect(os.path.join(ROOT, "sources.txt"))
    print(f"collected {len(links)} unique links")
    items = []
    for i, l in enumerate(links):
        o = to_outbound(l, f"cfg{i}")
        if o and o.get("server") and o.get("server_port"):
            items.append((l, o))
    print(f"parsed {len(items)}")
    items = prefilter(items)
    print(f"tcp-reachable {len(items)}")
    ranked = rank(real_test(items))
    ok = ranked[:KEEP]
    print(f"working {len(ranked)}; best {ok[0][2] if ok else '-'} ms")
    if not ok:
        print("nothing working, keeping previous output")
        return
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    write([l for l, _, _ in ok], [o for _, o, _ in ok], os.path.join(ROOT, "out"))
    if PERSONAL_ID:
        me = ranked[:KEEP_ME]
        os.makedirs(os.path.join(ROOT, "out", "me"), exist_ok=True)
        write([l for l, _, _ in me], [o for _, o, _ in me], os.path.join(ROOT, "out", "me"),
              name=PERSONAL_ID, label=lambda n: f"⭐ {n}")


if __name__ == "__main__":
    main()
