# Scripts and tools

Everything is plain bash or Python 3 standard library (the evidence tool needs only `pytest`, which `uv` provides). Nothing here draws a UI: the demo is shown in Switch's own Gateway and in Mattermost.

## Make targets
| Target | What it does |
|---|---|
| `make evidence` | Level 1. The same 3 checks on the Mac and in an Ubuntu 22.04 / Python 3.10 / UTC container, side by side. No Switch needed, and it never touches a running demo |
| `make demo` | Level 3. `stack`, `machines` and `room` in one go |
| `make stack` | Fetch Switch's compose file at the pinned tag, generate `stack/.env` with fresh random secrets, start Switch 0.31.0 and Mattermost, create the demo humans |
| `make codex-auth` | Once. Copy your Codex login into a Docker volume for the Linux box |
| `make machines` | Enroll the Mac and the Linux container as Switch machines |
| `make room` | Seed the git repo, then create both agents and the room from one template |
| `make policy` | Lock `dev-mac` down so only maya, sam and its owner may instruct it. Switch refuses everyone else |
| `make up` | Restart the server and both machines after a reboot. Does not touch the room |
| `make reset` | Clean slate for another run: a fresh room, a clean repo, the policy applied. Keeps the server and the machines |
| `make down` | Stop everything and keep the volumes |
| `make clean-secrets` | Remove the Codex login volume, the controller data volume and `work/humans.json`. `stack/.env` and `work/controller-mac-data` stay |

## Scripts (`scripts/`)
| Script | What it does |
|---|---|
| `evidence.sh` | Level 1. See `make evidence` |
| `fetch-stack.sh` | Fetch Switch's standalone compose file and env template at the pinned release tag. Uses `curl`, falls back to `gh api` |
| `gen-env.sh` | Generate `stack/.env` for Switch 0.31.0 with fresh random secrets. Refuses to overwrite an existing file, so it never rotates live secrets |
| `wait-ready.sh` | Wait until a URL answers 200 |
| `build-controller.sh` | Build the Switch agent controller from source at the pinned tag. No unsigned binary, no install scripts |
| `mac-controller.sh` | Run the headless agent controller for the Mac (`start`, `stop`, `status`, `logs`). Defaults the Mac agent's timezone to `Asia/Kolkata` (`PARITY_MAC_TZ` overrides it) and holds a no-idle-sleep assertion |
| `linux-box.sh` | The second environment: Ubuntu 22.04, Python 3.10, UTC, case-sensitive, with the Codex CLI (`up`, `down`, `logs`, `shell`). It joins the Switch container's network |
| `seed-codex-auth.sh` | Copy the host's Codex login into a Docker volume. Read its header for the token-rotation caveat and the device-login alternative |
| `seed-sut.sh`, `seed-remote.sh` | Build the shared bare git remote from `sut/`: a healthy `main` and the branch `feat/weekly-report` with three environment-dependent bugs. Refreshes in place, and recreates the Mac agent's clone and the container's clone |
| `mm_users.py` | Create the demo people (maya the PM, sam the QA lead, dave the intern) in Mattermost. Idempotent. Passwords are random and go to `work/humans.json` (gitignored) |
| `gen-template.py` | Render `templates/parity-room.template.yaml` from the prose in `room/` |
| `run-template.py` | Run the template against the Switch server: both agents on their machines and the room, in one call. Rolls back if the room fails (`--dry-run` lints only) |
| `policy.py` | Apply or clear the addressing policy (`apply`, `clear`). Rules match people by their Switch identity id, which it reads from Postgres because the Gateway has no endpoint for that |
| `reset-demo.py` | Delete the room and the two managed agents, reseed git in place. Leaves Switch, Mattermost and the machines running |
| `gw.py` | A minimal Switch Gateway client: cookie login and JSON calls. Reads the admin login from `stack/.env` |
| `mm_read.py` | Print the channel from Mattermost, optionally following it |
| `mm_wait.py` | Block until a user posts something matching a regex |
| `humans.py` | Post as maya, sam or dave through the Mattermost API, exactly like a typed message. Used by rehearsals and `e2e.py`, and labelled `[SCRIPTED]` wherever it is shown |
| `e2e.py` | End-to-end acceptance run with scripted humans. It drives the whole workflow, then proves the outcome: `main` has the merge, the room documents exist, and merged `main` passes on both machines. Appends timings to `work/runs.jsonl` |
| `refusal-check.py` | Acceptance check for the addressing policy: dave is refused and `main` is unchanged, maya gets an answer |
| `summarize-runs.py` | Turn `work/runs.jsonl` into the markdown table used in the README |
| `export-transcript.py` | Export the channel as a transcript with timings (`--scripted` labels the people's lines) |

## Tool (`tools/`)
| Tool | What it does |
|---|---|
| `parity_matrix.py` | Runs the system under test's tests in the environment it is in, and prints machine-readable evidence. It is deterministic on purpose: the agents reason about why something fails, and this script records what happened, so the evidence documents cannot be made up |

## Other folders
| Folder | What is in it |
|---|---|
| `templates/` | The Switch template: both agents, their machines, the room, roles, aliases, a document and the kickoff |
| `room/` | The prose of the room's instructions, the `conventions` document and the two agent briefs |
| `sut/` | The system under test: `base` (healthy) and `feature` (the change with three seeded bugs) |
| `verifier/` | The Dockerfile and entrypoint of the Linux machine |
| `stack-overrides/` | A demo-only Mattermost tweak: show agents' thread replies inline, because Mattermost 11 collapses them behind a link |
| `demo/` | The scripts that recorded the film. See [`demo/README.md`](../demo/README.md) |
| `site/` | The project page. See [`site/README.md`](../site/README.md) |
| `work/`, `stack/`, `verifier/vendor/` | Local state, generated or fetched. All gitignored |
