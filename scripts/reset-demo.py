#!/usr/bin/env python3
"""Reset the demo to a clean starting point WITHOUT touching the Switch server, Mattermost, or the two machines:
delete the room(s) and the two managed agents, reseed git (in place), then you can run scripts/run-template.py again.
  scripts/reset-demo.py"""
import os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from gw import Gateway, ROOT

g = Gateway()
_, rooms = g.call("GET", "/gateway/rooms")
for r in rooms:
    if r["name"].startswith("parity-room"):
        code, _ = g.call("DELETE", f"/gateway/rooms/{r['id']}")
        print("delete room", r["name"], code)
_, agents = g.call("GET", "/gateway/agents")
for a in agents:
    if a["name"] in ("dev-mac", "qa-linux"):
        code, data = g.call("DELETE", f"/gateway/management/agents/{a['id']}")       # un-place it (controller stops it)
        print("unplace agent", a["name"], code, "" if code < 300 else str(data)[:150])
        code, data = g.call("DELETE", f"/gateway/agents/{a['id']}")                    # free the name (registry record)
        print("delete agent record", a["name"], code, "" if code < 300 else str(data)[:150])
for _ in range(30):                                                                  # wait until the names are really free
    _, left = g.call("GET", "/gateway/agents")
    if not [a for a in left if a["name"] in ("dev-mac", "qa-linux")]: break
    time.sleep(1)
subprocess.run([os.path.join(ROOT, "scripts", "seed-sut.sh")], check=True)
print("reset done; now: scripts/run-template.py")
