# Parity Room observer

Live data feed for `../dashboard/`. Python 3, standard library only, **read-only** against Switch and Mattermost.

```sh
python3 observer/server.py                 # http://127.0.0.1:8090/   (--port, --host, --interval, --env-file, --verbose)
python3 observer/test_state.py              # 37 offline tests against responses captured from the live system
python3 observer/capture_testdata.py        # re-capture testdata/*.json from the running stack (read-only GETs)
```

| Route | |
|---|---|
| `GET /` | the static dashboard (`../dashboard/`), `Cache-Control: no-store` |
| `GET /api/state` | schema-1 state (exactly the dashboard contract; validated against `dashboard/check-fixtures.py` in the tests) |
| `GET /healthz` | `{ok, status, polls, last_poll_at, sources:{gateway,mattermost:{ok,error,last_ok_at}}}` |

A background thread polls every ~2 s and caches the composed state; requests never block on the upstream systems.
Credentials come from `stack/.env` (`GATEWAY_ADMIN_*`, `MATTERMOST_ADMIN_*`), are only used to log in, and are never
logged or stored. Binds to `127.0.0.1` by default. Errors go to stderr once per change (not every poll).

## Sources (all GET after login)

| Source | Calls |
|---|---|
| Gateway (cookie session, re-login on 401) | `/gateway/rooms` (list item key is `id`), `/gateway/rooms/{id}` (`agent_ids`, `agent_statuses`), `/gateway/rooms/{id}/roles` (`exclusive`, `held_by`), `/gateway/rooms/{id}/documents` then `/documents/{id}` for `matrix-mac` and `matrix-linux` (field `content`), `/gateway/agents` (`known_agent_type`, `connector_type`), `/gateway/management/controllers` (machine names) |
| Mattermost (admin token) | team `switch`, channel `parity-room`: `/channels/{id}/posts?per_page=200`, `/channels/{id}/members`, `/users/{id}` (only `username`, `is_bot`, `position` are kept) |

Agents and controllers, member list and user titles are refreshed every ~5 s; the rest every poll. If a source fails the
**last good data for that source is kept** (state is served from it); if nothing was ever fetched the state is `pending`
with an empty timeline. Nothing is invented: unknown values are `"unknown"` / `""` / `null`.

## How the state is derived

- **environments**: `mac` = agent `dev-mac`, `linux` = agent `qa-linux` (static ids/labels). `provider` from the gateway agent
  (`known_agent_type` `claude-code` to "Claude Code", `codex` to "Codex"); `machine` from the controller whose
  `status.agents[]` contains the agent id (`mac-host`, `linux-box`); static defaults only if the lookup fails.
  `facts` = `os, python, tz, fs` from that environment's matrix document (`locale` is in the doc but not in the contract's fixtures, so it is omitted).
- **checks**: `settings`, `stamp`, `buckets` with the fixture titles and test names.
- **results[env][check]** come from the document's `results`. Document states:
  - missing / empty: all `pending`, `detail: null`, facts `"unknown"`;
  - not valid JSON: all `pending`, `detail: "matrix document is not valid JSON"` (other malformed cases get their own reason: not an object,
    schema other than 1, `env` mismatch, unknown status, check missing);
  - valid: pass / fail pass through with their `at` and `detail`.
- **change**: `branch` + `head_sha` from the valid document with the newest `ran_at` (blank if there is none); `title`
  "feat: weekly digest report" and `author` "Priya" are static.
- **stale**: if an environment's `head_sha` differs from that newest `head_sha`, all its results become `running` (`at`/`detail` null):
  the other environment is on a newer commit, so these results no longer describe the change.
- **status** (precedence): `pending` if no valid document; else `failing` if any current `fail`; else `running` if any `running`;
  else `verified` if every result is `pass` (which implies both documents are valid and on the same sha); otherwise `pending`
  (e.g. one environment has no usable evidence yet).
- **room**: `name`; `agents` from the room's `agent_ids` (real names `dev-mac`, `qa-linux`; `online` = `agent_statuses[id] == "live"`;
  roles = roles whose `held_by` has the agent, `mode` = `exclusive`/`shared` from `exclusive`). `humans` = non-bot Mattermost channel
  members (plus non-bot posters) excluding `admin`/`switch-admin`; `title` = Mattermost `position`, else a static map (maya PM, sam QA lead);
  an untitled member who never posted is not shown. Without Mattermost: gateway `connected_user_names` that have a static title.
- **timeline**: Mattermost posts, oldest first, newest 12 meaningful ones. Skipped: system posts (joins/adds), deleted posts, `admin` and
  `switch-admin`, progress cards ("Worked for ...", posts with `attachments`), room-document bookkeeping, "Starting a session",
  role-assumed lines, greeting stubs. `at` = post time (UTC ISO), `actor` = username, `kind` = `agent` if the MM user is a bot else `human`.
  `title` = first line with markdown stripped, at most 110 chars (if longer: cut at the last sentence end that fits, else at a word boundary with the
  remainder carried into `detail`), `detail` = remaining text, at most 220 chars.
- `links.room` = `http://localhost:8065/switch/channels/parity-room`; `updated_at` = compose time.

## Notes

- The gateway room list item uses `id` (not `room_id`); agents carry no machine name (it comes from the controllers endpoint);
  roles use `exclusive: bool` + `held_by: [agent names]`.
- `testdata/` holds raw responses captured from the live stack (controller public keys dropped, Mattermost users reduced to
  `id/username/is_bot/position`). No passwords, cookies or tokens are stored.
- `screenshots/live.png` is the dashboard served by this server against the real stack; `screenshots/simulated-verified.png` is the same
  pipeline fed with captured data where the mac document's `head_sha` was edited to match linux's (to show the verified state).
