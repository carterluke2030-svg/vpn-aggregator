import base64
import json
import urllib.parse as up


FINGERPRINTS = {"chrome", "firefox", "edge", "safari", "360", "qq", "ios", "android", "random", "randomized"}


def _b64(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)).decode("utf-8", "ignore")


def _transport(net, host, path, svc=None):
    if net == "ws":
        t = {"type": "ws", "path": path or "/"}
        if host:
            t["headers"] = {"Host": host}
        return t
    if net == "grpc":
        return {"type": "grpc", "service_name": svc or path or ""}
    return None


def _tls(sni, security, q, insecure=True):
    if security not in ("tls", "reality"):
        return None
    t = {"enabled": True, "server_name": sni or "", "insecure": insecure}
    if q.get("fp") in FINGERPRINTS:
        t["utls"] = {"enabled": True, "fingerprint": q["fp"]}
    if q.get("alpn"):
        t["alpn"] = q["alpn"].split(",")
    if security == "reality":
        t.setdefault("utls", {"enabled": True, "fingerprint": "chrome"})
        t["reality"] = {"enabled": True, "public_key": q.get("pbk", ""), "short_id": q.get("sid", "")}
        t["insecure"] = False
    return t


def to_outbound(link, tag):
    """Return a sing-box outbound dict, or None if unsupported."""
    try:
        scheme = link.split("://", 1)[0]
        if scheme == "vmess":
            j = json.loads(_b64(link[8:].split("#")[0]))
            o = {"type": "vmess", "tag": tag, "server": j["add"], "server_port": int(j["port"]),
                 "uuid": j["id"], "security": j.get("scy", "auto"), "alter_id": int(j.get("aid", 0))}
            tr = _transport(j.get("net"), j.get("host"), j.get("path"))
            if tr:
                o["transport"] = tr
            tls = _tls(j.get("sni") or j.get("host"), "tls" if j.get("tls") == "tls" else "", {"fp": j.get("fp", "")})
            if tls:
                o["tls"] = tls
            return o
        u = up.urlparse(link)
        q = {k: v[0] for k, v in up.parse_qs(u.query).items()}
        host, port = u.hostname, u.port
        if scheme == "vless":
            o = {"type": "vless", "tag": tag, "server": host, "server_port": port, "uuid": up.unquote(u.username)}
            if q.get("flow"):
                o["flow"] = q["flow"]
            tr = _transport(q.get("type"), q.get("host"), up.unquote(q.get("path", "")), q.get("serviceName"))
            if tr:
                o["transport"] = tr
            tls = _tls(q.get("sni") or q.get("host"), q.get("security"), q)
            if tls:
                o["tls"] = tls
            return o
        if scheme == "trojan":
            o = {"type": "trojan", "tag": tag, "server": host, "server_port": port, "password": up.unquote(u.username)}
            tr = _transport(q.get("type"), q.get("host"), up.unquote(q.get("path", "")), q.get("serviceName"))
            if tr:
                o["transport"] = tr
            o["tls"] = _tls(q.get("sni") or host, "tls", q)
            return o
        if scheme == "ss":
            body = link[5:].split("#")[0].split("?")[0]
            if "@" not in body:
                body = _b64(body)
            cred, _, addr = body.rpartition("@")
            if ":" not in cred:
                cred = _b64(cred)
            method, _, pw = cred.partition(":")
            h, _, p = addr.rpartition(":")
            return {"type": "shadowsocks", "tag": tag, "server": h, "server_port": int(p), "method": method, "password": pw}
        if scheme in ("hysteria2", "hy2"):
            return {"type": "hysteria2", "tag": tag, "server": host, "server_port": port, "password": up.unquote(u.username),
                    "tls": {"enabled": True, "server_name": q.get("sni") or host, "insecure": q.get("insecure") == "1"}}
    except Exception:
        return None
    return None
