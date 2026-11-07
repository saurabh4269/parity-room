#!/usr/bin/env python3
"""Create the demo humans (maya = PM, sam = QA lead, dave = intern with NO right to instruct the dev agent) in the bundled Mattermost and add them to team `switch`.
Idempotent. Passwords are random, written to work/humans.json (chmod 600, gitignored). stdlib only."""
import json, os, secrets, sys, urllib.error, urllib.request
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MM = os.environ.get("MM_URL", "http://localhost:8065") + "/api/v4"

def env(path):
    out = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1); out[k] = v
    return out

def req(path, method="GET", body=None, tok=None):
    r = urllib.request.Request(MM + path, method=method, data=None if body is None else json.dumps(body).encode(),
                               headers={"Content-Type": "application/json", **({"Authorization": "Bearer " + tok} if tok else {})})
    try:
        with urllib.request.urlopen(r) as resp:
            return json.load(resp), resp.headers
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:200]}, e.headers

def main():
    e = env(os.path.join(ROOT, "stack", ".env"))
    r = urllib.request.Request(MM + "/users/login", method="POST", headers={"Content-Type": "application/json"},
        data=json.dumps({"login_id": e["MATTERMOST_ADMIN_USER"], "password": e["MATTERMOST_ADMIN_PASSWORD"]}).encode())
    with urllib.request.urlopen(r) as resp: tok = resp.headers["Token"]
    team, _ = req("/teams/name/" + e.get("MATTERMOST_TEAM_NAME", "switch"), tok=tok)
    path = os.path.join(ROOT, "work", "humans.json")
    humans = json.load(open(path)) if os.path.exists(path) else {}
    for name, title in (("maya", "PM"), ("sam", "QA lead"), ("dave", "Intern")):
        pw = humans.get(name, {}).get("password") or secrets.token_urlsafe(14) + "9aA!"
        u, _ = req("/users/username/" + name, tok=tok)
        if "_error" in u:
            u, _ = req("/users", "POST", {"email": f"{name}@parity-room.local", "username": name, "password": pw,
                                          "first_name": name.capitalize(), "position": title}, tok)
            assert "_error" not in u, u
        req(f"/teams/{team['id']}/members", "POST", {"team_id": team["id"], "user_id": u["id"]}, tok)
        humans[name] = {"id": u["id"], "password": pw, "title": title}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh: json.dump(humans, fh, indent=2)
    os.chmod(path, 0o600)
    print("humans ready:", ", ".join(f"{n} ({h['title']})" for n, h in humans.items()), "-> work/humans.json (0600)")

if __name__ == "__main__":
    sys.exit(main())
