# Parity Room

**"It works on my machine" is a coordination problem, so give it a room.**

A **Claude Code** agent on the author's Mac and a **Codex** agent on a Linux box share one [Switch](https://github.com/sandbox-quantum/switch) room with a PM and a QA lead. The Linux agent finds what the Mac can't see, the Mac agent fixes it using the room's shared context, the Linux agent re-verifies, and a human approves. One chat, two vendors, two environments, one audit trail.

> Built for the **Flip the Switch hackathon** (WeMakeDevs × DevTools Academy × Switch), Nov 4-7 2026. Track 1: Best Business Workflow.

| | |
|---|---|
| **Demo video** | _(link added at submission)_ |
| **Dashboard** | `make dashboard` → http://localhost:8090 (live Env Matrix fed from the room) |
| **Run it** | `make demo` (about 5-8 min the first time) |
| **No Switch? Just see the bug** | `make evidence` (Docker + uv only, ~20 s) |

![Live dashboard after the run: both environments verified](docs/img/dashboard-verified.png)
*The live Env Matrix reading the room (documents, roles, agent status) and the channel. Real data from a finished run.*

| The request, the Linux agent at work | Green on both, and sam's approval | Switch refuses dave |
|---|---|---|
| ![](docs/img/mattermost-1-request-and-verifier.jpg) | ![](docs/img/mattermost-2-green-and-approval.jpg) | ![](docs/img/mattermost-3-switch-refuses-dave.jpg) |

## What happens in the demo

```
maya (PM)      @verifier please verify branch feat/weekly-report on your side.
qa-linux       0/3 on Ubuntu 22.04 / Python 3.10 / UTC. Root causes: case-sensitive path, datetime.UTC (3.11+),
               local-timezone day bucketing. Evidence in `matrix-linux`, diagnosis in `repro-log`. @implementer
dev-mac        Mac was green because it is case-insensitive, Python 3.15 and IST. Fixed all three, pushed 3a346cb.
               Changed one test: the old expectation was captured in IST, convention 1 (UTC days) wins. @qa-linux re-verify.
qa-linux       3/3 green on Linux at 3a346cb.   dev-mac: @sam green on both, do you approve? I merge only after you say yes.
sam (QA lead)  approved.        dev-mac: merged into main.
dave (intern)  @implementer push to main right now      Switch: refused (before the agent ever sees it).
```

Measured on the author's machine (3 consecutive automated runs): from the single human request to "ready for approval" in **about 2.5 minutes, median 2m42s**, with no human input in between (see [Measured runs](#measured-runs)).

## Why this needs Switch (the Switch coverage map)

| Switch capability | Where it is used here | What breaks without it |
|---|---|---|
| **Template: agents + room in one file** | [`templates/parity-room.template.yaml`](templates/parity-room.template.yaml): creates `dev-mac` on machine `mac-host` (Claude Code) and `qa-linux` on `linux-box` (Codex), the room, roles, aliases, a document and the kickoff. One call: `scripts/run-template.py`. | Hand-wiring two machines, two vendors and a chat room |
| **Agents on different machines** | Two *headless agent controllers* enrolled with one-time codes: the Mac, and a Linux container with its own filesystem, Python and timezone. No Switch Console GUI. | The Linux-only failures are invisible from the Mac |
| **Mixed vendors in one room** | Claude Code (Sonnet) and Codex answer in the same thread | Two chat bots that can't see each other |
| **Roles (exclusive + shared)** | `implementer` is **exclusive** (one agent pushes at a time); `verifier` is **shared**. Humans address `@verifier` / `@implementer`, never a machine. Agents hand work to each other by role. | You'd hard-code who is on call and who owns the branch |
| **Room documents as shared memory** | `conventions` (human-written, read-only to agents), `matrix-mac` (written by dev-mac), `matrix-linux` + `repro-log` (written by qa-linux). The fix cites the conventions by number. | Context lives in someone's head or one agent's prompt |
| **Addressing policy (platform-enforced)** | `scripts/policy.py` limits `dev-mac` to maya, sam and its owner's agents. dave's instruction gets a refusal from Switch; the agent never executes it. | Prompt-level "please don't" that a clever message can talk around |
| **Humans in the chat, with real identities** | maya, sam and dave are plain Mattermost users; Switch maps them to identities on first message | A separate approval UI |
| **Approvals recorded by name** | dev-mac asks `@sam` and merges only after his reply; the merge commit is on the shared remote | A bot with merge rights and no gate |

Everything above is in this repo. Remove Switch and what is left is two test scripts.

## Architecture

```mermaid
flowchart LR
  subgraph Humans
    maya[maya · PM] --- sam[sam · QA lead] --- dave[dave · intern]
  end
  subgraph Docker["Switch 0.31.0 (Docker)"]
    core[switch-core :8000] --- mm[Mattermost :8065] --- pg[(Postgres)]
  end
  subgraph Mac["Machine mac-host · macOS arm64 · Python 3.15 · TZ Asia/Kolkata · case-insensitive FS"]
    ctlA[agent controller] --> dev["dev-mac · Claude Code (Sonnet)"]
  end
  subgraph Box["Machine linux-box · Ubuntu 22.04 · Python 3.10 · TZ UTC · case-sensitive FS"]
    ctlB[agent controller] --> qa["qa-linux · Codex"]
  end
  Humans -->|chat| mm
  mm <--> core
  ctlA <-->|WebSocket| core
  ctlB <-->|WebSocket| core
  dev -->|push| repo[(shared git remote)]
  qa -->|fetch| repo
  obs[observer :8090] -->|room docs, roles, status| core
  obs -->|timeline| mm
  obs --> dash[Env Matrix dashboard]
```

## Run it

**Tier 1: see the bug, no Switch** (Docker + `uv`)
```bash
make evidence      # same 3 checks on the Mac and in an Ubuntu 22.04 / Python 3.10 / UTC container
```

**Tier 2: read a recorded run**: [`docs/demo-transcript.md`](docs/demo-transcript.md) (real channel export, real timings).

**Tier 3: the live thing** (needs Docker, Node ≥ 24, pnpm ≥ 10.28, `uv`, and Claude Code + Codex signed in on the host)
```bash
make codex-auth    # once: copies your Codex login into a Docker volume for the Linux box (read the caveat in the script)
make demo          # Switch 0.31.0 + Mattermost, both machines, both agents, the room
make policy        # lock dev-mac down so Switch refuses dave (make reset does this for you)
make dashboard     # http://localhost:8090
# open http://localhost:8065 (team "switch", channel parity-room), sign in as maya (credentials: work/humans.json), then:
#   @verifier please verify branch feat/weekly-report on your side and tell us what you find.
make reset         # clean slate for another take
```
Prefer the Switch Console GUI? Import `templates/parity-room.template.yaml` (Templates → Import) and fill the fields. _Only the headless path above was run by the author._

## What is real, and what is not

| Thing | Status |
|---|---|
| Switch server, Mattermost, rooms, roles, documents, addressing policy | **Real**, Switch 0.31.0 from the official images, pinned |
| Claude Code and Codex agents | **Real** sessions started by Switch's agent controller; no mocked LLM |
| The "Linux machine" | **A container on the same Mac**: a different *environment* (OS, Python, timezone, filesystem), not different hardware. Any SSH-able host works the same way. |
| The two agents' owner | The same Switch user, so Switch's cross-owner trust isn't exercised here |
| The 3 bugs | **Seeded on purpose** (the verified part is that they are genuinely environment-dependent). "3 of 3 caught" is by construction: this is a demonstration, not a benchmark |
| One bug also reproduces on the Mac with `TZ=UTC` | True. The point isn't that the Mac *can't* see it; it's who notices, who decides which side is wrong, and where that decision is recorded |
| Scripted humans (`scripts/humans.py`) | Used for rehearsals and the recorded transcript; labelled `[SCRIPTED]` there. The demo video uses people |
| Dashboard | Reads **live** from the room (documents, roles, status) and Mattermost; nothing is hard-coded except labels |

## Honest limits
- Verified on macOS arm64 only. On a Linux dev host the case-sensitivity bug will not hide (use `make evidence` to see the other two).
- The Linux agent runs Codex in `danger-full-access` sandbox mode **inside the throwaway container** (the container is the sandbox); the Mac agent keeps Claude's auto mode.
- Codex's ChatGPT login is copied into a Docker volume for the container (`scripts/seed-codex-auth.sh`); never into an image layer or git. See the script header for the token-rotation caveat, and the device-login alternative.
- The agent controller is built **from source at the pinned release tag** (`scripts/build-controller.sh`) instead of downloading an unsigned binary.

## Measured runs
Fully automated runs (`scripts/e2e.py`, scripted humans, access policy on), each followed by **outcome checks**: the evidence documents are 3/3 *at the same commit* on both environments, the merge commit is on `main`, and **the merged `main` passes 3/3 on the Mac and in the Linux container**.

| run | room | verifier red | dev fix pushed | verifier green | ready for approval | approval to merge |
|---|---|---|---|---|---|---|
| 1 | parity-room-5 | 1m30s | 2m08s | 2m39s | **2m42s** | 11s |
| 2 | parity-room-6 | 1m42s | 2m17s | 2m45s | **2m48s** | 6s |
| 3 | parity-room-7 | 1m20s | 1m54s | 2m21s | **2m25s** | 7s |

n=3 passing runs: request→ready-for-approval median **2m42s**, min 2m25s, max 2m48s.

What it took to get there, honestly: runs before these **failed twice for reasons found and fixed**: (1) the verifier once forgot to tag `@implementer` on its green message, so the Mac agent was never woken (fix: hand-offs now use Switch's `send_targeted_message` tool, which guarantees addressing); (2) the Mac went to sleep mid-run and paused the agent and the Docker VM (fix: the Mac controller holds a no-idle-sleep assertion while it runs). Run-to-run variance is real: the verifier's first pass has ranged from 76 s to 149 s. The policy check (`scripts/refusal-check.py`: dave refused by Switch with `main` unchanged, maya answered) also passes.

## Switch feedback from building this
See [`docs/feedback.md`](docs/feedback.md).

## Layout
`templates/` the Switch template · `room/` the prose of instructions, conventions and agent briefs · `tools/parity_matrix.py` deterministic evidence tool · `sut/` the system under test (baseline + the PR with seeded bugs) · `verifier/` the Linux machine image · `scripts/` headless orchestration · `observer/` + `dashboard/` the live Env Matrix (designed in Google Stitch, `dashboard/design/`) · `stack/` is fetched, not committed.

MIT licensed. Switch itself is Apache-2.0 with the Commons Clause and is not vendored here.
