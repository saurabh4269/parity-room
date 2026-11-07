# Feedback on Switch 0.31.0 (from building Parity Room)

Each item says how I know it: **observed** (I hit it while running this repo), or **read** (found in the source/docs while building, not exercised).

## What worked really well
- **One template → two agents on two named machines + the room** (`POST /gateway/rooms/from-template-document`, 201). It also lints first (`/gateway/templates/validate`) and rolls back if the room fails. _(observed)_
- **Roles are the right abstraction for agents on different machines.** `@verifier` / `@implementer` resolved to the right agent, and agents handed work to each other by role with no glue code. An exclusive role makes "one agent pushes at a time" a platform fact. _(observed)_
- **Single-writer room documents** turned out to be a good constraint: each agent owns its evidence document, and a human-authored `conventions` document is read-only to agents, so it can settle disputes. _(observed)_
- **Addressing policy is real enforcement.** With a rule on `dev-mac`, an unlisted user's instruction was refused by Switch and the agent never acted on it. _(observed)_
- **Headless controllers** (`enroll`, `run`) made a two-machine setup scriptable with no Console GUI. _(observed)_
- Progress cards ("Working… 25s / ✓ 3 done · ✗ 2 failed") make agent work legible in plain Mattermost. _(observed)_

## Friction, with suggestions
1. **Controller on a container needs a network trick.** `--server` accepts plain `http` only for loopback, so a container can't use `http://host.docker.internal:8000`. I joined the container to the Switch container's network namespace (`--network container:…`). A documented "controller in Docker" recipe (or a flag for private networks) would save time. _(observed)_
2. **Docs/version drift on a controller flag.** The controller README on `main` documents `--no-self-update`; the 0.31.0 controller answers `Unknown option '--no-self-update'`. Pinning docs to the release tag would avoid this. _(observed)_
3. **The documented one-line controller install can't install stable releases.** `install.sh` on `main` requires a `.sig` asset and stable releases (e.g. `switch-agent-controller-v0.31.0`) don't have one. I built the controller from source at the release tag instead. Publishing signatures for stable releases, or a documented checksum path, would fix it. _(read)_
4. **Refusal wording is misleading under a custom rule.** When a user outside my rule addressed `dev-mac`, Switch replied: "I only take instructions from my owner, and this chat account isn't linked to a Switch user yet". But the policy also admitted two named people. Something like "you're not on this agent's allow-list" would be clearer. _(observed)_
5. **No gateway endpoint lists the human identities that addressing rules need.** Rules match on `ExternalUser` row ids; I read them from Postgres (`scripts/policy.py`). A "list people in this room with their ids" endpoint would make scripting policies possible. _(observed)_
6. **Template docs vs reality.** Roles can't be assigned to agents in a template (agents must `assume_role`, so it has to be in their instructions); there's no template key for reasoning `effort` (it lives in `advanced_config`); in v2 a `references` list whose entries all have `value:` collapses and the run fails; and the docs say `red-blue-workroom.template.yaml` documents every field but it contains no roles, documents or aliases. _(read)_
7. **Default addressing mismatch.** `docs/TEMPLATES.md` says a template agent's default addressing is `owner`; the server applies owner + the owner's agents. _(read)_
8. **Why was a command declined?** Codex's auto-reviewer declined a `git reset --hard origin/<branch>` ("⊘ 1 declined") and the agent worked around it, which cost ~30 s on the first run. A short reason on the card would help; I switched the instruction to the non-destructive `git checkout -B`. _(observed)_
9. **A room's documents are invisible from the chat app.** The docs say so, and it's why I built a small dashboard that reads them through the gateway. Showing "📄 updated room document X" (already there) with a link/preview would help. _(observed)_

## Event-side (not the product)
- The hackathon page says the agent protocol is "server-sent events in, HTTP out"; the docs say WebSocket (SSE deprecated).
- The "Switch Discord" invite linked from the DevTools Academy page and the Switch README returned `Invite is expired` from Discord's API when checked.
- Track 3 prize count differs across the WeMakeDevs and DevTools Academy pages (top 10 vs top 20).
