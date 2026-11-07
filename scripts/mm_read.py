#!/usr/bin/env python3
"""Print the parity-room channel from Mattermost (read as the MM admin; reading is fine, only admin *posts* are dropped by the bridge).
  scripts/mm_read.py [--n 30] [--watch SECONDS]"""
import json, os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MM = os.environ.get("MM_URL", "http://localhost:8065") + "/api/v4"
def env(p):
    o = {}
    for l in open(p):
        l = l.strip()
        if l and not l.startswith("#") and "=" in l: k, v = l.split("=", 1); o[k] = v
    return o
def call(path, tok, method="GET", body=None):
    r = urllib.request.Request(MM + path, method=method, data=None if body is None else json.dumps(body).encode(),
                               headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r))
def login():
    e = env(os.path.join(ROOT, "stack", ".env"))
    r = urllib.request.Request(MM + "/users/login", method="POST", headers={"Content-Type": "application/json"},
        data=json.dumps({"login_id": e["MATTERMOST_ADMIN_USER"], "password": e["MATTERMOST_ADMIN_PASSWORD"]}).encode())
    return urllib.request.urlopen(r).headers["Token"]
def channel(tok):
    team = call("/teams/name/switch", tok)
    from gw import room_name
    return call(f"/teams/{team['id']}/channels/name/{room_name()}", tok)
def show(tok, ch, n):
    posts = call(f"/channels/{ch['id']}/posts?per_page={n}", tok)
    users = {}
    out = []
    for pid in sorted(posts["order"], key=lambda i: posts["posts"][i]["create_at"]):
        p = posts["posts"][pid]
        uid = p["user_id"]
        if uid not in users:
            u = call(f"/users/{uid}", tok); users[uid] = (u["username"], u.get("is_bot", False))
        name, bot = users[uid]
        ts = time.strftime("%H:%M:%S", time.localtime(p["create_at"] / 1000))
        out.append(f"[{ts}] {'BOT ' if bot else 'user'} {name:12s}{' (thread)' if p.get('root_id') else ''}\n    " + p["message"].replace("\n", "\n    ")[:900])
    return out
if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 30
    tok = login(); ch = channel(tok)
    print(f"# {ch['display_name']} ({ch['name']}) id={ch['id'][:8]}")
    print("\n".join(show(tok, ch, n)))
