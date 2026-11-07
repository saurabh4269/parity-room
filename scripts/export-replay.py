#!/usr/bin/env python3
"""Export a REAL run from a Mattermost channel into site/data/replay.json, the data behind the website's replay.
Nothing is invented: events are the channel's posts (agent progress cards dropped); the dashboard state is reconstructed from
those events (documents' contents aren't versioned), and the three error strings are the real evidence from parity_matrix.py.
  scripts/export-replay.py --room parity-room-2 --out site/data/replay.json --total-s 169"""
import argparse, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import mm_read as m
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ap = argparse.ArgumentParser(); ap.add_argument("--room", required=True); ap.add_argument("--out", default=os.path.join(ROOT, "site/data/replay.json"))
ap.add_argument("--run", default=""); ap.add_argument("--total-s", type=int, default=0); a = ap.parse_args()
tok = m.login(); team = m.call("/teams/name/switch", tok); ch = m.call(f"/teams/{team['id']}/channels/name/{a.room}", tok)
posts = m.call(f"/channels/{ch['id']}/posts?per_page=200", tok); users = {}
def who(uid):
    if uid not in users:
        u = m.call(f"/users/{uid}", tok); users[uid] = (u["username"], bool(u.get("is_bot")), u.get("position") or "")
    return users[uid]
ev = []
for pid in sorted(posts["order"], key=lambda i: posts["posts"][i]["create_at"]):
    p = posts["posts"][pid]; name, bot, pos = who(p["user_id"]); msg = p["message"].strip()
    if not msg or name == "admin" or re.search(r"joined the channel|added to the channel", msg): continue
    if re.match(r"\*\*(Working|Worked)", msg) or msg.startswith("Starting a session"): continue
    kind = "system" if name == "switch-admin" else ("agent" if bot else "human")
    doc = re.search(r"(created|updated) room document [“\"]([^”\"]+)[”\"]", msg)
    role = re.search(r"assumed the `?(\w+)`? role", msg)
    ev.append({"t": p["create_at"] / 1000, "who": name, "kind": kind, "text": msg, **({"doc": [doc.group(1), doc.group(2)]} if doc else {}), **({"role": role.group(1)} if role else {})})
last_h = max(i for i, e in enumerate(ev) if e["who"] == "maya")
end_i = next((i for i in range(last_h + 1, len(ev)) if ev[i]["kind"] == "agent" and not re.match(r"(Hi!|Hey there!|Hello!)", ev[i]["text"])), last_h)
ev = ev[: end_i + 1]
t0 = ev[0]["t"]
for e in ev: e["t"] = round(e["t"] - t0, 1)
req = next(e["t"] for e in ev if e["who"] == "maya")
def first(pred, after=0):
    return next((e for e in ev if e["t"] >= after and pred(e)), None)
shas = re.findall(r"\b[0-9a-f]{7}\b", " ".join(e["text"] for e in ev if e["who"] in ("qa-linux", "dev-mac")))
red = first(lambda e: e["who"] == "qa-linux" and e["kind"] == "agent" and re.search(r"FAIL|fail", e["text"]) and "doc" not in e, req)
macdoc = first(lambda e: e["who"] == "dev-mac" and "doc" not in e and re.search(r"green|reproduc|3/3", e["text"], re.I), (red or {"t": req})["t"])
push = first(lambda e: e["who"] == "dev-mac" and re.search(r"push", e["text"], re.I) and "doc" not in e, (red or {"t": req})["t"])
macdoc2 = first(lambda e: e.get("doc") == ["updated", "matrix-mac"], (push or {"t": req})["t"]) if push else None
green = first(lambda e: e["who"] == "qa-linux" and re.search(r"fully green|3/3|all (three )?(checks )?pass", e["text"], re.I) and "doc" not in e, (push or {"t": req})["t"])
ask = first(lambda e: e["who"] == "dev-mac" and "@sam" in e["text"], (green or {"t": req})["t"])
appr = first(lambda e: e["who"] == "sam", (ask or {"t": req})["t"])
merged = first(lambda e: e["who"] == "dev-mac" and re.search(r"merged", e["text"], re.I) and "doc" not in e, (appr or {"t": req})["t"])
dave = first(lambda e: e["who"] == "dave" and "implementer" in e["text"], (merged or {"t": req})["t"])
refuse = first(lambda e: e["who"] == "dev-mac" and "@dave" in e["text"], (dave or {"t": req})["t"])
if refuse:  # Switch's own refusal text, delivered under the agent's chat identity; show it as a Switch notice
    refuse["kind"] = "system"; refuse["via"] = refuse["who"]
sha1 = shas[0] if shas else ""; sha2 = next((s for s in shas if s != sha1), sha1)
ERR = {"settings": "FileNotFoundError: [Errno 2] No such file or directory: 'config/Settings.json'",
       "stamp": "AttributeError: module 'datetime' has no attribute 'UTC'",
       "buckets": "AssertionError: assert {'2024-11-01': 4} == {'2024-11-01': 2, '2024-11-02': 2}"}
cells = lambda s: {k: {"status": s, **({"detail": ERR[k]} if s == "fail" else {})} for k in ERR}
FACT = {"mac": {"os": "macOS arm64", "python": "3.15.2", "tz": "Asia/Kolkata", "fs": "case-insensitive"},
        "linux": {"os": "Ubuntu 22.04 arm64", "python": "3.10.12", "tz": "UTC", "fs": "case-sensitive"}}
states = [{"t": 0, "status": "pending", "mac": {"facts": None, "cells": cells("pending")}, "linux": {"facts": None, "cells": cells("pending")}, "sha": ""}]
cur = json.loads(json.dumps(states[0]))
def push_state(t, **kw):
    global cur
    cur = json.loads(json.dumps(cur)); cur["t"] = t
    for k, v in kw.items(): cur[k] = v
    states.append(cur)
if red: push_state(red["t"], status="failing", linux={"facts": FACT["linux"], "cells": cells("fail")}, sha=sha1)
if macdoc: push_state(macdoc["t"], mac={"facts": FACT["mac"], "cells": cells("pass")})
if push: push_state(push["t"], status="running", linux={"facts": FACT["linux"], "cells": cells("running")}, mac={"facts": FACT["mac"], "cells": cells("running")}, sha=sha2)
if macdoc2: push_state(macdoc2["t"], mac={"facts": FACT["mac"], "cells": cells("pass")})
if green: push_state(green["t"], status="verified", linux={"facts": FACT["linux"], "cells": cells("pass")}, mac={"facts": FACT["mac"], "cells": cells("pass")})
chap = [("Room opens", 0), ("The request", req), ("Linux finds 3 failures", red and red["t"]), ("Mac fixes and pushes", push and push["t"]), ("Linux re-verifies", green and green["t"]),
        ("Human approves", appr and appr["t"]), ("Merged", merged and merged["t"]), ("Switch refuses dave", (refuse or dave or {}).get("t"))]
out = {"meta": {"run": a.run or a.room, "room": a.room, "request_to_ready_s": a.total_s or int(((ask or green or {"t": req})["t"]) - req),
                "duration_s": ev[-1]["t"], "humans_scripted": True, "sha_before": sha1, "sha_after": sha2,
                "note": "Real channel export. The humans' lines were posted by script; every agent message and Switch notice is real. Dashboard states are reconstructed from the event stream."},
       "chapters": [{"label": l, "t": t} for l, t in chap if t is not None], "events": ev, "states": states}
os.makedirs(os.path.dirname(a.out), exist_ok=True); json.dump(out, open(a.out, "w"), indent=1, ensure_ascii=False)
print("events", len(ev), "| states", len(states), "| chapters", [(c["label"], c["t"]) for c in out["chapters"]], "| shas", sha1, sha2, "| duration", out["meta"]["duration_s"])
