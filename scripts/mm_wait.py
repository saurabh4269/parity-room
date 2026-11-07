#!/usr/bin/env python3
"""Block until <user> posts in #parity-room something matching <regex> (after --since epoch-ms). Prints elapsed + the post.
  mm_wait.py --user qa-linux --match 'FAIL|fail' --since 1699999999000 --timeout 300"""
import argparse, re, sys, time
sys.path.insert(0, __import__("os").path.dirname(__file__))
import mm_read as m
ap = argparse.ArgumentParser(); ap.add_argument("--user", required=True); ap.add_argument("--match", default=".")
ap.add_argument("--since", type=int, default=0); ap.add_argument("--timeout", type=int, default=300)
a = ap.parse_args()
tok = m.login(); ch = m.channel(tok); t0 = time.time(); uid = {}
while time.time() - t0 < a.timeout:
    posts = m.call(f"/channels/{ch['id']}/posts?per_page=60", tok)
    for pid in sorted(posts["order"], key=lambda i: posts["posts"][i]["create_at"]):
        p = posts["posts"][pid]
        if p["create_at"] <= a.since: continue
        u = uid.get(p["user_id"]) or uid.setdefault(p["user_id"], m.call(f"/users/{p['user_id']}", tok)["username"])
        if u == a.user and re.search(a.match, p["message"], re.S | re.I):
            print(f"MATCH after {time.time()-t0:.0f}s by {u}:\n{p['message'][:1500]}"); sys.exit(0)
    time.sleep(3)
print(f"TIMEOUT after {a.timeout}s waiting for {a.user} /{a.match}/"); sys.exit(1)
