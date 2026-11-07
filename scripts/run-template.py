#!/usr/bin/env python3
"""Run templates/parity-room.template.yaml against the local Switch server (headless; no Console GUI).
Creates the two agents on their machines AND the room, in one call. Rolls back automatically if the room fails.
  scripts/run-template.py [--dry-run]
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from gw import Gateway, ROOT

def fresh_name():
    """Mattermost keeps archived channel names reserved, so each take gets a new room name."""
    if os.environ.get("PARITY_ROOM"): return os.environ["PARITY_ROOM"]
    import mm_read as m
    tok = m.login(); team = m.call("/teams/name/switch", tok); n, name = 1, "parity-room"
    while True:
        try: m.call(f"/teams/{team['id']}/channels/name/{name}", tok)
        except Exception: return name        # 404: free
        n += 1; name = f"parity-room-{n}"

def main():
    dry = "--dry-run" in sys.argv
    tpl = open(os.path.join(ROOT, "templates", "parity-room.template.yaml")).read()
    g = Gateway()
    code, lint = g.call("POST", "/gateway/templates/validate", {"content": tpl})
    print("lint:", code, json.dumps(lint))
    if code != 200 or lint.get("blocked") or lint.get("errors"):
        sys.exit("template lint failed")
    ROOMNAME = fresh_name()
    inputs = {
        "mac_machine": "mac-host", "linux_machine": "linux-box",
        "dev_dir": os.path.join(ROOT, "work", "dev"), "tools_dir": os.path.join(ROOT, "tools"),
        "human_pm": "maya", "human_qa": "sam", "room_name": ROOMNAME,
    }
    if dry:
        print("dry run ok; inputs:", inputs); return
    code, data = g.call("POST", "/gateway/rooms/from-template-document",
                        {"template": tpl, "inputs": inputs, "filled": {}, "template_name": "parity-room"})
    print("run:", code, "room:", ROOMNAME)
    if code == 201: open(os.path.join(ROOT, "work", "room.txt"), "w").write(ROOMNAME)
    print(json.dumps(data, indent=2) if not isinstance(data, str) else data)
    sys.exit(0 if code == 201 else 1)

if __name__ == "__main__":
    main()
