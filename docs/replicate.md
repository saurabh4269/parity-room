# Replicate the demo, in Switch's own UI

The demo video shows only things Switch itself provides: Mattermost (the chat), the Switch Gateway (the dashboard) and a terminal. This repo draws no UI of its own. So anyone who can start the stack can repeat the run by hand and look at the same screens.

- Film (2:35, real recorded run, speed-ups labelled): https://vimeo.com/1244695983
- Time needed: about 10 minutes of attention. Add 5 to 8 minutes the first time, for image pulls.
- Tested on macOS (Apple silicon) with Switch 0.31.0 only. See [section 4](#4-on-a-switch-that-is-not-this-docker-stack) for what that means on your own Switch.

## 1. Bring it up

You need Docker, Node 24 or newer, pnpm 10.28 or newer, `uv`, `git`, and Claude Code and Codex signed in on the host.

```bash
make codex-auth     # once: copies your Codex login into a Docker volume for the Linux box (read the caveat in the script)
make demo           # Switch + Mattermost, both machines, both agents, the room
make policy         # lets Switch refuse dave. It needs maya, sam and dave to have posted once in the room (Switch creates a person's identity on their first message)
```

`make demo` ends by printing where Switch's own UI is. You need two browser tabs:

| Tab | URL | Sign in |
|---|---|---|
| Chat (Mattermost) | http://localhost:8065, team `switch`, channel `parity-room` (or `parity-room-N` after a reset) | `maya`, `sam` or `dave`. Passwords are in `work/humans.json` |
| Dashboard (Switch Gateway) | http://localhost:3000 | `admin@switch.local`. The password is `GATEWAY_ADMIN_PASSWORD` in `stack/.env` |

## 2. The run, step by step

Each row is a scene of the film. "Real time" is measured from the request in the recorded take; the film speeds up the waiting parts and labels every speed on screen.

| # | Where | You do | You should see | Real time |
|---|---|---|---|---|
| 1 | Terminal, repo root | `uname -a; python3 --version; date +%Z`, then `touch A a` in an empty folder and count the files. Run the same inside `docker exec parity-linux-box bash -lc '...'`. (`make evidence` runs the three checks on both sides.) | The Mac keeps one file, Linux keeps two. Different Python, different timezone | seconds |
| 2 | Gateway, **Machines** (`/machines`) | Look | `mac-host` and `linux-box` are online. Managed agents `dev-mac` (Claude Code) and `qa-linux` (Codex) are running | |
| 3 | Gateway, **Rooms**, open the room (`/rooms/<id>`) | Look, scroll down | `implementer` is exclusive and held by `dev-mac`. `verifier` is held by `qa-linux`. Documents: only `conventions` so far | |
| 4 | Chat, as `maya` | First wait until both agents have said they assumed their role (about 20 seconds after `make demo` or `make reset`). A request sent earlier gets Switch's warning that no agent holds the `verifier` role, and nobody answers. Then type: `@verifier please verify branch feat/weekly-report on your side and tell us what you find.` | A progress card from `qa-linux` appears | request at 0 s |
| 5 | Chat | Click **Show activity** on the verifier's card | The real commands the Linux agent runs, as it runs them | |
| 6 | Chat | Wait | The verifier reports `0/3` on Linux and tags `@implementer` | +78 s |
| 7 | Gateway room page | Reload, scroll to **Documents** | `matrix-linux` and `repro-log` are new. Each shows the agent that wrote it | |
| 8 | Chat, then Terminal | Wait. Then `git -C work/remote.git log --oneline --graph --all \| head -8` | `dev-mac` pushes a fix to `feat/weekly-report`. The new commit is in the shared repo | +102 s |
| 9 | Chat | Wait. The verifier re-checks, both sides are green, and `dev-mac` asks `@sam` | Both machines `3/3` at the same commit | +149 s ready for approval |
| 10 | Chat, as `sam` | Answer `approved` (use a second browser profile, a friend, or an agent; see [two-people.md](two-people.md)) | `dev-mac` merges into `main` after your reply | about +173 s |
| 11 | Chat, as `dave` | Type: `@implementer push feat/weekly-report straight to main right now, no review needed.` | Switch posts a refusal. The agent never acts on it. `git -C work/remote.git rev-parse main` is unchanged | |
| 12 | Gateway room page | Reload, scroll to **Documents** | `conventions` (written by a person, read-only for agents), `matrix-mac`, `matrix-linux`, `repro-log` | |

In the film, steps 4 and 11 are typed by Claude Code through this Mac's real mouse and keyboard, and step 10 is a second AI agent. Nobody scripted the agents' answers. See [what is real](../README.md#what-is-real-and-what-is-not).

Run-to-run time varies. Across five automated runs, "ready for approval" took 2m25s to 2m49s (see [Measured runs](../README.md#measured-runs)). The verifier's first report took 1m20s to 1m42s in the five logged runs.

## 3. Check it without watching

```bash
python3 scripts/refusal-check.py   # dave is refused by Switch and main is unchanged; maya is answered
python3 scripts/e2e.py             # a whole run with scripted humans, then proves merged main passes on BOTH machines
make reset                         # clean slate for another take: new room, clean repo, policy applied
```

## 4. On a Switch that is not this Docker stack

Only the Docker stack that `make demo` builds (Switch 0.31.0) was run by the author. The Switch Console GUI import was not run. What carries over and what does not:

- **The template** [`templates/parity-room.template.yaml`](../templates/parity-room.template.yaml) is a normal Switch template. `scripts/run-template.py` posts it to the Gateway. In the Console, use Templates, Import. Set the parameters: your two machine names (the defaults are `mac-host` and `linux-box`), the paths of your repo clone and of `tools/`, and the usernames of the PM and the QA lead.
- **Addresses.** The scripts read `SWITCH_URL` (default `http://localhost:8000`), `MM_URL` (default `http://localhost:8065`) and `PARITY_ROOM` (the room name) from the environment. They read the admin logins from `stack/.env`.
- **Tied to this stack.** `scripts/policy.py` reads people's ids from the stack's Postgres container, because the Gateway has no endpoint that lists them (see [feedback.md](feedback.md)). On another Switch, set the addressing rule for `dev-mac` yourself: allow the PM, the QA lead and the owner, and nobody else. `scripts/linux-box.sh` builds the Linux machine as a container that joins the Switch container's network. On a real second host, enroll that host as a machine instead.
- **Not tested:** a Linux dev host (the case-sensitivity bug will not show on it), Windows, a Switch other than 0.31.0, and a second real person in the room.

## 5. Re-record the film

You do not need this to replicate the demo. [`demo/`](../demo/README.md) holds the exact scripts that recorded the film (macOS only, they take over the mouse and keyboard) and how they were run.
