#!/usr/bin/env python3
"""Run templates/parity-room.template.yaml against the local Switch server (headless; no Console GUI).
Creates the two agents on their machines AND the room, in one call. Rolls back automatically if the room fails.
  scripts/run-template.py [--dry-run]
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from gw import Gateway, ROOT

def main():
    dry = "--dry-run" in sys.argv
    tpl = open(os.path.join(ROOT, "templates", "parity-room.template.yaml")).read()
    g = Gateway()
    code, lint = g.call("POST", "/gateway/templates/validate", {"content": tpl})
    print("lint:", code, json.dumps(lint))
    if code != 200 or lint.get("blocked") or lint.get("errors"):
        sys.exit("template lint failed")
    inputs = {
        "mac_machine": "mac-host", "linux_machine": "linux-box",
        "dev_dir": os.path.join(ROOT, "work", "dev"), "tools_dir": os.path.join(ROOT, "tools"),
        "human_pm": "maya", "human_qa": "sam", "room_name": os.environ.get("PARITY_ROOM", "parity-room"),
    }
    if dry:
        print("dry run ok; inputs:", inputs); return
    code, data = g.call("POST", "/gateway/rooms/from-template-document",
                        {"template": tpl, "inputs": inputs, "filled": {}, "template_name": "parity-room"})
    print("run:", code)
    print(json.dumps(data, indent=2) if not isinstance(data, str) else data)
    sys.exit(0 if code == 201 else 1)

if __name__ == "__main__":
    main()
