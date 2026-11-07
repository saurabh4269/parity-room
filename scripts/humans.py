#!/usr/bin/env python3
"""SCRIPTED humans for rehearsal/e2e: post to #parity-room as maya (PM) or sam (QA lead) via the Mattermost REST API.
A REST post by a normal user reaches Switch exactly like a typed one. NEVER script as `admin` (the bridge drops admin posts).
These lines are SCRIPTED: label them as such in any recording.   scripts/humans.py maya "@verifier please verify ..." """
import json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MM = os.environ.get("MM_URL", "http://localhost:8065") + "/api/v4"
from gw import room_name
_tok = {}
def req(path, method="GET", body=None, tok=None):
    r = urllib.request.Request(MM + path, method=method, data=None if body is None else json.dumps(body).encode(),
                               headers={"Content-Type": "application/json", **({"Authorization": "Bearer " + tok} if tok else {})})
    return urllib.request.urlopen(r)
def login(user):
    if user in _tok: return _tok[user]
    pw = json.load(open(os.path.join(ROOT, "work", "humans.json")))[user]["password"]
    resp = req("/users/login", "POST", {"login_id": user, "password": pw})
    _tok[user] = resp.headers["Token"]; return _tok[user]
def channel_id(tok):
    team = json.load(req("/teams/name/switch", tok=tok))
    return json.load(req(f"/teams/{team['id']}/channels/name/{room_name()}", tok=tok))["id"]
def say(user, text, root_id=None):
    tok = login(user)
    body = {"channel_id": channel_id(tok), "message": text}
    if root_id: body["root_id"] = root_id
    return json.load(req("/posts", "POST", body, tok))
if __name__ == "__main__":
    p = say(sys.argv[1], sys.argv[2]); print("posted as", sys.argv[1], "id", p["id"][:8])
