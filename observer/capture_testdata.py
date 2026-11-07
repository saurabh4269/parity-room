#!/usr/bin/env python3
"""Capture the LIVE raw API responses the observer consumes into observer/testdata/*.json.

Read-only (same GETs as the poller). Credentials are read from stack/.env, used only to log in, and are
never written. Controller public keys are dropped; Mattermost users are already reduced by the poller to
{id, username, is_bot, position} (no emails). Re-run to refresh the fixtures for test_state.py.
"""
import json
import os
import sys

import server

OUT = os.path.join(server.HERE, "testdata")
FILES = {  # raw key -> file name
    "rooms": "gateway_rooms.json",
    "room": "gateway_room.json",
    "roles": "gateway_roles.json",
    "agents": "gateway_agents.json",
    "controllers": "gateway_controllers.json",
    "mm_channel": "mm_channel.json",
    "mm_posts": "mm_posts.json",
    "mm_members": "mm_members.json",
    "mm_users": "mm_users.json",
}


def dump(name, data):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False, sort_keys=False)
        fh.write("\n")
    print("wrote testdata/%s" % name)


def main():
    env = server.load_env_file(server.DEFAULT_ENV_FILE)
    gw = server.GatewayClient(server.SWITCH_URL, env["GATEWAY_ADMIN_EMAIL"], env["GATEWAY_ADMIN_PASSWORD"])
    mm = server.MattermostClient(server.MM_URL, env["MATTERMOST_ADMIN_USER"], env["MATTERMOST_ADMIN_PASSWORD"])
    obs = server.Observer(gw, mm)
    obs.poll_once()
    for src, st in obs.sources.items():
        if not st["ok"]:
            print("source %s failed: %s" % (src, st["error"]), file=sys.stderr)
            return 1
    os.makedirs(OUT, exist_ok=True)
    raw = obs.raw
    for c in raw.get("controllers") or []:
        c.pop("public_key", None)   # not secret, but not needed either
    for key, name in FILES.items():
        dump(name, raw[key])
    for doc_name, doc in (raw.get("documents") or {}).items():
        dump("gateway_doc_%s.json" % doc_name, doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
