#!/usr/bin/env python3
"""Render templates/parity-room.template.yaml from room/*.md (so the prose is edited in one place)."""
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
def block(name, indent):
    t = open(os.path.join(ROOT, "room", name)).read().rstrip("\n")
    return "\n".join((" " * indent + l) if l.strip() else "" for l in t.splitlines())
tpl = f'''# Parity Room: ONE template creates both agents (on two different machines) and the room.
# Headless: scripts/run-template.py     Console: Templates -> Import template -> Use
version: 1
params:
  bridge:
    type: bridge
    label: Messaging app
    description: Where the room is mirrored. Mattermost ships with the local stack.
    default: [Mattermost, $first]
  room_name:
    type: string
    label: Room name
    default: parity-room
  mac_machine:
    type: machine
    label: Machine for the dev agent (Claude Code)
    default: [mac-host]
  linux_machine:
    type: machine
    label: Machine for the QA agent (Codex)
    default: [linux-box]
  dev_dir:
    type: string
    label: Absolute path of the dev agent's repo clone (on the Mac)
  tools_dir:
    type: string
    label: Absolute path of parity-room/tools (on the Mac)
  human_pm:
    type: string
    label: Mattermost username of the PM
    default: maya
  human_qa:
    type: string
    label: Mattermost username of the QA lead
    default: sam
agents:
  - name: dev-mac
    display_name: dev (Claude Code, Mac)
    description: Implements fixes. Holds the implementer role. Runs on the Mac.
    provider: claude
    model: sonnet
    machine: "{{mac_machine}}"
    directory: "{{dev_dir}}"
    addressing: anyone
    instructions: |
      Take the role `implementer` when the room opens (assume_role).
{block("agent-dev.md", 6)}
  - name: qa-linux
    display_name: qa (Codex, Linux)
    description: Verifies changes on Linux. Holds the verifier role. Never edits code.
    provider: codex
    machine: "{{linux_machine}}"
    directory: /home/verifier/sut
    addressing: anyone
    instructions: |
      Take the role `verifier` when the room opens (assume_role).
{block("agent-verifier.md", 6)}
room:
  name: "{{room_name}}"
  description: Agents on two different environments verify one change; humans decide.
  bridge: "{{bridge}}"
  channel_type: channel_public
  agents: [dev-mac, qa-linux]
  users: ["{{$creator}}", "{{human_pm}}", "{{human_qa}}"]
  aliases:
    dev-mac: dev
    qa-linux: qa
  instructions: |
{block("instructions.md", 4)}
  roles:
    - name: implementer
      exclusive: true
      instructions: Fix what the verifier reports, in the dev environment. One holder at a time so two agents never push over each other.
    - name: verifier
      exclusive: false
      instructions: Run the checks in your own environment and report evidence verbatim. Never edit code or push.
  docs:
    - name: conventions
      description: Team conventions written by maya (PM). Read-only for agents. These decide ties between code and tests.
      instructions: Read this before changing any expectation. When a test and a convention disagree, the convention wins.
      content: |
{block("conventions.md", 8)}
kickoff: |
  @dev-mac @qa-linux welcome. Take your roles (dev-mac: implementer, qa-linux: verifier), then say hello in one line, including the OS and Python version you run on.
'''
open(os.path.join(ROOT, "templates", "parity-room.template.yaml"), "w").write(tpl)
print("wrote templates/parity-room.template.yaml", len(tpl), "bytes")
