#!/usr/bin/env python3
"""Minimal Switch gateway client (stdlib only): cookie login + JSON calls.
  gw.py GET  /gateway/management/controllers
  gw.py POST /gateway/templates/validate '{"content":"..."}'
Reads admin credentials from stack/.env (GATEWAY_ADMIN_EMAIL / GATEWAY_ADMIN_PASSWORD)."""
import http.cookiejar, json, os, sys, urllib.error, urllib.request
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE = os.environ.get("SWITCH_URL", "http://localhost:8000")

def room_name():
    """The active room: $PARITY_ROOM, else work/room.txt (written by run-template.py), else 'parity-room'."""
    if os.environ.get("PARITY_ROOM"): return os.environ["PARITY_ROOM"]
    try: return open(os.path.join(ROOT, "work", "room.txt")).read().strip() or "parity-room"
    except OSError: return "parity-room"

def env(path):
    out = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1); out[k] = v
    return out

class Gateway:
    def __init__(self):
        e = env(os.path.join(ROOT, "stack", ".env"))
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.call("POST", "/gateway/auth/login", {"email": e["GATEWAY_ADMIN_EMAIL"], "password": e["GATEWAY_ADMIN_PASSWORD"]})

    def call(self, method, path, body=None):
        r = urllib.request.Request(BASE + path, method=method, headers={"Content-Type": "application/json"},
                                   data=None if body is None else json.dumps(body).encode())
        try:
            with self.op.open(r, timeout=60) as resp:
                raw = resp.read().decode()
                return resp.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            raw = e.read().decode()
            try: return e.code, json.loads(raw)
            except ValueError: return e.code, raw

if __name__ == "__main__":
    g = Gateway()
    if sys.argv[1] == "enroll-code":          # prints only the one-time code (valid 10 min)
        code, data = g.call("POST", "/gateway/management/enrollment-codes")
        assert code == 201, (code, data)
        print(data["code"]); sys.exit(0)
    method, path = sys.argv[1], sys.argv[2]
    body = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
    code, data = g.call(method, path, body)
    print(code); print(json.dumps(data, indent=2) if not isinstance(data, str) else data)
