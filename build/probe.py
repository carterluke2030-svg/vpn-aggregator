import json
import re
import shutil
import socket
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

TEST_URL = "http://cp.cloudflare.com/generate_204"
BASE_PORT = 20000


def tcp_ok(host, port, timeout=4):
    t = time.time()
    try:
        socket.create_connection((host, port), timeout=timeout).close()
        return int((time.time() - t) * 1000)
    except Exception:
        return None


def prefilter(items, workers=200):
    """items: [(link, outbound)] -> those whose server:port accepts TCP."""
    def one(it):
        o = it[1]
        return it if tcp_ok(o["server"], o["server_port"]) is not None else None
    with ThreadPoolExecutor(workers) as ex:
        return [r for r in ex.map(one, items) if r]


def _curl(port):
    cmd = ["curl", "-s", "-o", "/dev/null", "--max-time", "8", "-x", f"socks5h://127.0.0.1:{port}",
           "-w", "%{http_code} %{time_total}", TEST_URL]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=12).stdout.split()
        if out and out[0] in ("204", "200"):
            return int(float(out[1]) * 1000)
    except Exception:
        pass
    return None


def real_test(items, batch=150):
    """Run each outbound through sing-box and time a request. Returns [(link, outbound, ms)]."""
    if not shutil.which("sing-box"):
        print("[warn] sing-box not found, skipping real test")
        return [(l, o, 9999) for l, o in items]
    results = []
    for i in range(0, len(items), batch):
        chunk = items[i:i + batch]
        p = None
        while chunk:
            cfg = {"log": {"level": "error"}, "inbounds": [], "outbounds": [{"type": "direct", "tag": "direct"}],
                   "route": {"rules": [], "final": "direct"}}
            for n, (_, o) in enumerate(chunk):
                tag_in = f"in{n}"
                cfg["inbounds"].append({"type": "socks", "tag": tag_in, "listen": "127.0.0.1", "listen_port": BASE_PORT + n})
                cfg["outbounds"].append(o)
                cfg["route"]["rules"].append({"inbound": [tag_in], "outbound": o["tag"]})
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
                json.dump(cfg, f)
            p = subprocess.Popen(["sing-box", "run", "-c", f.name], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            for _ in range(20):
                time.sleep(0.1)
                if p.poll() is not None:
                    break
            else:
                time.sleep(1)
            if p.poll() is None:
                break
            err = p.stderr.read().decode()
            m = re.search(r"outbound\[(\d+)\]", err)
            if not m:
                print("[warn] sing-box failed:", err[:200])
                p = None
                break
            del chunk[int(m.group(1)) - 1]  # outbound[0] is the direct one
        if p is None or not chunk:
            continue
        try:
            with ThreadPoolExecutor(50) as ex:
                ms = list(ex.map(_curl, [BASE_PORT + n for n in range(len(chunk))]))
        finally:
            p.terminate()
        results += [(l, o, m) for (l, o), m in zip(chunk, ms) if m is not None]
    return results
