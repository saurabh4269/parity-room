#!/usr/bin/env python3
"""Export the #parity-room channel as a transcript with relative timings + key milestone durations.
  scripts/export-transcript.py [--room parity-room] [--out docs/demo-transcript.md] [--scripted]
--scripted labels maya/sam/dave lines [SCRIPTED] (use it for rehearsal exports)."""
import argparse, datetime, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import mm_read as m
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ap = argparse.ArgumentParser(); from gw import room_name
ap.add_argument("--room", default=room_name()); ap.add_argument("--out", default=os.path.join(ROOT, "docs", "demo-transcript.md"))
ap.add_argument("--scripted", action="store_true"); a = ap.parse_args()
tok = m.login(); team = m.call("/teams/name/switch", tok); ch = m.call(f"/teams/{team['id']}/channels/name/{a.room}", tok)
posts = m.call(f"/channels/{ch['id']}/posts?per_page=200", tok); uid = {}
rows = []
for pid in sorted(posts["order"], key=lambda i: posts["posts"][i]["create_at"]):
    p = posts["posts"][pid]
    if p["user_id"] not in uid: u = m.call(f"/users/{p['user_id']}", tok); uid[p["user_id"]] = (u["username"], u.get("is_bot", False))
    name, bot = uid[p["user_id"]]; msg = p["message"].strip()
    if name in ("admin", "switch-admin") or not msg: continue
    if re.match(r"\*\*(Working|Worked)", msg) or msg.startswith("Starting a session"): continue
    rows.append((p["create_at"] / 1000, name, bot, msg, bool(p.get("root_id"))))
humans = ("maya", "sam", "dave", "user")
first = next((r for r in rows if r[1] == "maya"), rows[0]); t0 = first[0]
def rel(t):
    s = int(t - t0)
    return "setup" if s < 0 else f"+{s//60}:{s%60:02d}"
def find(user, rx, after=0):
    for r in rows:
        if r[1] == user and r[0] >= after and re.search(rx, r[3], re.I | re.S): return r[0]
mile = {}
mile["red"] = find("qa-linux", r"red|0/3|failed", t0); 
mile["pushed"] = find("dev-mac", r"pushed|3 failures fixed|fixes? (pushed|applied)", mile["red"] or t0)
mile["green"] = find("qa-linux", r"fully green|3/3 checks passed", mile["pushed"] or t0)
mile["ask"] = find("dev-mac", r"@sam", mile["green"] or t0)
mile["approved"] = find("sam", r"approv", mile["ask"] or t0)
mile["merged"] = find("dev-mac", r"merged", mile["approved"] or t0)
steps = [("verifier first report (red)", "red", t0), ("dev fix pushed", "pushed", mile["red"]), ("verifier green", "green", mile["pushed"]),
         ("dev asks sam to approve", "ask", mile["green"]), ("merged after sam's approval", "merged", mile["approved"])]
out = [f"# Demo transcript (real run, exported {datetime.datetime.now():%Y-%m-%d %H:%M} local time)\n",
       f"Channel `{a.room}` on a local Switch 0.31.0 + Mattermost. Agents: `dev-mac` (Claude Code · Sonnet · Mac) and `qa-linux` (Codex · Linux container)."
       + (" Human lines are **[SCRIPTED]** (posted through the Mattermost API for rehearsal).\n" if a.scripted else "\n"), "## Key timings\n", "| step | at | since previous |", "|---|---|---|"]
prev = t0
for label, key, base in steps:
    t = mile.get(key)
    if t: out.append(f"| {label} | {rel(t)} | {int(t - (base if base else prev))}s |"); prev = t
if mile.get("green"): out.append(f"\n**Request → ready for approval: {int((mile['ask'] or mile['green']) - t0)//60}m {int((mile['ask'] or mile['green']) - t0)%60:02d}s** (no human input in between).\n")
out += ["## Conversation\n", "| t | who | message |", "|---|---|---|"]
for t, name, bot, msg, thread in rows:
    tag = ("[SCRIPTED] " if a.scripted and name in humans else "") + ("agent" if bot else "human")
    out.append(f"| {rel(t)} | **{name}** ({tag}) | " + msg.replace("|", "\\|").replace("\n", "<br>")[:900] + " |")
out += ["\n## Resulting git history (shared remote)\n", "```", subprocess.run(["git", "-C", os.path.join(ROOT, "work", "remote.git"), "log", "--oneline", "--graph", "main"], capture_output=True, text=True).stdout.strip(), "```\n"]
os.makedirs(os.path.dirname(a.out), exist_ok=True); open(a.out, "w").write("\n".join(out))
print("wrote", a.out, "| milestones:", {k: (rel(v) if v else None) for k, v in mile.items()})
