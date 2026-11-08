#!/usr/bin/env python3
"""End-to-end acceptance run (SCRIPTED humans): drives maya and sam through the whole workflow, waits for each agent step,
and then PROVES the outcome: main contains the merge, the room documents exist, and merged `main` passes on BOTH environments.
Appends timings to work/runs.jsonl.   scripts/e2e.py [--room parity-room]"""
import json, os, re, subprocess, sys, tempfile, time
sys.path.insert(0, os.path.dirname(__file__))
import humans, mm_read as m
from gw import Gateway, ROOT, room_name

ROOM = sys.argv[sys.argv.index("--room") + 1] if "--room" in sys.argv else room_name()
tok = m.login(); team = m.call("/teams/name/switch", tok); ch = m.call(f"/teams/{team['id']}/channels/name/{ROOM}", tok)
names = {}
def bot_posts(after_ms):
    posts = m.call(f"/channels/{ch['id']}/posts?per_page=100", tok); out = []
    for pid in sorted(posts["order"], key=lambda i: posts["posts"][i]["create_at"]):
        p = posts["posts"][pid]
        if p["create_at"] <= after_ms: continue
        n = names.get(p["user_id"]) or names.setdefault(p["user_id"], m.call(f"/users/{p['user_id']}", tok)["username"])
        msg = p["message"].strip()
        if re.match(r"\*\*(Working|Worked)", msg) or msg.startswith("Starting a session"): continue
        out.append((p["create_at"], n, msg))
    return out
def wait(user, rx, after_ms, timeout=300):
    t0 = time.time()
    while time.time() - t0 < timeout:
        for ts, n, msg in bot_posts(after_ms):
            if n == user and re.search(rx, msg, re.I | re.S): return ts, msg
        time.sleep(3)
    raise SystemExit(f"FAIL: timeout waiting for {user} /{rx}/")
def step(label, ts0, ts):
    print(f"  {label:<34} +{(ts - ts0) / 1000:5.0f}s", flush=True)

print(f"e2e on #{ROOM} (scripted humans)")
# Both agents must hold their role before the request: a message sent earlier gets "no agent currently holds the verifier role"
wait("dev-mac", r"assumed the .?implementer", 0, 240); wait("qa-linux", r"assumed the .?verifier", 0, 240)
print("  both agents hold their roles", flush=True)
t_req = int(time.time() * 1000)
humans.say("maya", "@verifier please verify branch feat/weekly-report on your side and tell us what you find.")
red, msg = wait("qa-linux", r"red|0/3|fail", t_req);                      step("verifier reports red", t_req, red)
pushed, _ = wait("dev-mac", r"push", red);                              step("dev pushed a fix", t_req, pushed)
green, msg = wait("qa-linux", r"fully green|3/3|all (three )?(checks )?pass|green", pushed);                step("verifier green", t_req, green)
ask, _ = wait("dev-mac", r"@sam", green);                                 step("dev asks sam to approve", t_req, ask)
t_appr = int(time.time() * 1000)
humans.say("sam", "@implementer approved. Merge feat/weekly-report into main and confirm.")
merged, _ = wait("dev-mac", r"merged", t_appr);                           step("merged", t_appr, merged)

print("verifying the OUTCOME:")
_ev = {}
g = Gateway(); _, rooms = g.call("GET", "/gateway/rooms"); rid = next(r["id"] for r in rooms if r["name"] == ROOM)
_, docs = g.call("GET", f"/gateway/rooms/{rid}/documents"); dn = {d["name"] for d in docs}
assert {"conventions", "matrix-mac", "matrix-linux", "repro-log"} <= dn, dn
for d in docs:
    if d["name"] in ("matrix-mac", "matrix-linux"):
        _, full = g.call("GET", f"/gateway/rooms/{rid}/documents/{d['id']}"); _ev[d["name"]] = json.loads(full["content"])
for k in ("matrix-mac", "matrix-linux"):
    assert _ev[k]["summary"]["passed"] == 3, (k, _ev[k]["summary"])
    print(f"  {k}: {_ev[k]['summary']['passed']}/3 at {_ev[k]['change']['head_sha']} ({_ev[k]['facts']['os']}, py {_ev[k]['facts']['python']}, TZ {_ev[k]['facts']['tz']}, fs {_ev[k]['facts']['fs']})")
assert _ev["matrix-mac"]["change"]["head_sha"] == _ev["matrix-linux"]["change"]["head_sha"], "mac and linux evidence are for different commits"
print("  room documents:", sorted(dn))
log = subprocess.run(["git", "-C", os.path.join(ROOT, "work", "remote.git"), "log", "--oneline", "--merges", "main"], capture_output=True, text=True).stdout
assert "Merge" in log, "no merge commit on main"; print("  main has the merge commit:", log.strip().splitlines()[0])
with tempfile.TemporaryDirectory() as t:
    subprocess.run(["git", "clone", "-q", os.path.join(ROOT, "work", "remote.git"), t + "/main"], check=True)
    mac = subprocess.run(["uv", "run", "--quiet", "--no-project", "--with", "pytest", "python", os.path.join(ROOT, "tools", "parity_matrix.py"), "--repo", t + "/main", "--env", "mac", "--text"],
                         capture_output=True, text=True, env={**os.environ, "TZ": "Asia/Kolkata"}).stdout
    lin = subprocess.run(["docker", "run", "--rm", "-e", "TZ=UTC", "-v", os.path.join(ROOT, "work", "remote.git") + ":/remote.git:ro", "-v", os.path.join(ROOT, "tools") + ":/opt/parity-tools:ro", "--entrypoint", "bash", "parity-verifier:dev", "-lc",
                          'git config --global --add safe.directory "*" && git clone -q /remote.git /tmp/s && cd /tmp/s && python3 /opt/parity-tools/parity_matrix.py --repo . --env linux --text'], capture_output=True, text=True).stdout
for lbl, out in (("mac", mac), ("linux", lin)):
    ok = "3/3 checks pass" in out; print(f"  merged main on {lbl}: {out.splitlines()[1] if out else 'NO OUTPUT'}"); assert ok, out
total = (merged - t_req) / 1000
rec = {"ts": time.strftime("%H:%M:%S"), "room": ROOM, "red_s": (red - t_req) / 1000, "pushed_s": (pushed - t_req) / 1000, "green_s": (green - t_req) / 1000, "ask_s": (ask - t_req) / 1000, "merge_after_approval_s": (merged - t_appr) / 1000, "pass": True}
open(os.path.join(ROOT, "work", "runs.jsonl"), "a").write(json.dumps(rec) + "\n")
print(f"PASS  request→ready-for-approval {rec['ask_s']:.0f}s   (approval→merge {rec['merge_after_approval_s']:.0f}s)")
