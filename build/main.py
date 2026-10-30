import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from collect import collect
from convert import to_outbound
from probe import prefilter, real_test
from render import write

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEP = int(os.environ.get("KEEP", "100"))


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
    ok = sorted(real_test(items), key=lambda r: r[2])[:KEEP]
    print(f"working {len(ok)}; best {ok[0][2] if ok else '-'} ms")
    if not ok:
        print("nothing working, keeping previous output")
        return
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    write([l for l, _, _ in ok], [o for _, o, _ in ok], os.path.join(ROOT, "out"))


if __name__ == "__main__":
    main()
