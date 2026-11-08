#!/usr/bin/env python3
"""Lock the code-writing agent down with a Switch *addressing policy* (platform-enforced, not prompt-enforced):
`dev-mac` may be instructed only by maya, sam, its owner, and the owner's own agents (qa-linux).
Anyone else (e.g. dave, the intern) gets a visible refusal FROM SWITCH before the agent ever sees the message.
  scripts/policy.py apply|clear
NOTE: rules match humans by their ExternalUser row id; the gateway has no endpoint that lists them, so we read them from Postgres."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from gw import Gateway, ROOT, env

def external_ids(names):
    e = env(os.path.join(ROOT, "stack", ".env"))
    out = subprocess.run(["docker", "exec", "-e", "PGPASSWORD=" + e["DB_OWNER_PASSWORD"], "stack-postgres-1", "psql", "-U", e["DB_OWNER_USER"],
                          "-d", e["DB_NAME"], "-At", "-F", "|", "-c", "select external_username, id from external_users"],
                         capture_output=True, text=True, check=True).stdout
    rows = dict(l.split("|") for l in out.strip().splitlines())
    missing = [n for n in names if n not in rows]
    if missing: sys.exit(f"no Switch identity yet for {missing}: they must post once in the room first (for example: python3 scripts/humans.py maya hello, then the same for sam and dave), then run this again")
    return [rows[n] for n in names]

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "apply"
    g = Gateway()
    _, agents = g.call("GET", "/gateway/agents")
    dev = next(a for a in agents if a["name"] == "dev-mac")
    if cmd == "clear":
        policy = None
    else:
        policy = {"rules": [{"rooms": "*", "users": external_ids(["maya", "sam"]), "agents": [], "owner": True, "owner_agents": True}]}
    code, data = g.call("PUT", f"/gateway/agents/{dev['id']}/addressing-policy", {"policy": policy})
    print(code, "policy:", json.dumps(data.get("addressing_policy") if isinstance(data, dict) else data)[:300])
    sys.exit(0 if code == 200 else 1)

if __name__ == "__main__":
    main()
