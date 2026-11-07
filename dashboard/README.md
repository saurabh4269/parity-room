# Parity Room dashboard

Read-only, zero-build dashboard for one change verified across several agent environments.
Vanilla HTML/CSS/JS: no framework, no bundler, no CDN dependency. Open it over HTTP and it works.

```
dashboard/
  index.html          page skeleton + landmarks
  app.js              data sources, derived values, DOM rendering
  style.css           design tokens + components (from design/DESIGN.md)
  fixtures/           state-{pending,failing,running,verified}.json  (the data contract, schema 1)
  check-fixtures.py   stdlib-only contract validator
  screenshots/        headless-Chrome captures of the four fixtures (1440x1200)
  design/             DESIGN.md + Stitch reference (layout/token reference only; nothing is shipped from it)
```

## Run

Serve the directory with any static server (fetch does not work from `file://`):

```sh
python3 -m http.server 8099 --directory dashboard
# then open
#   http://localhost:8099/index.html?fixture=failing      static fixture, no polling
#   http://localhost:8099/index.html?play=1               auto-play all four states
#   http://localhost:8099/index.html                      live mode (needs GET /api/state)
```

Live mode fetches `/api/state` from the **same origin as the page**, so the real server must serve
the static files and `GET /api/state` (or a reverse proxy must). With a plain static server the page
correctly shows a `DISCONNECTED` chip and an explanatory empty state.

Validate the contract:

```sh
python3 dashboard/check-fixtures.py            # all fixtures, exit 0 = valid, 1 = violation
python3 dashboard/check-fixtures.py my.json    # any file(s); `warn:` lines are advisory only
```

## Query parameters

| Param | Effect |
|---|---|
| *(none)* | Poll `GET /api/state` every 1000 ms. On failure: `DISCONNECTED` chip, last good state stays on screen, polling continues. Invalid payloads show `BAD DATA` and are ignored. |
| `?fixture=pending\|failing\|running\|verified` | Load `./fixtures/state-<name>.json` once (relative to the page). No polling. Chip reads `FIXTURE`. Unknown names show a `BAD DATA` chip (names are whitelisted). |
| `?play=1` | Cycle pending, failing, running, verified every 4 s (loops). For design review and video b-roll. Chip reads `AUTO-PLAY step n/4`. Takes precedence over `fixture`. |

## Data contract (schema 1)

```jsonc
{
  "schema": 1,
  "updated_at": "ISO-8601",
  "status": "pending | running | failing | verified",       // overall chip, taken as given
  "change": { "branch", "head_sha", "author", "title" },
  "environments": [ { "id", "label", "agent", "provider", "machine",
                      "facts": { "os", "python", "tz", "fs" /* any string facts */ } } ],
  "checks":       [ { "id", "title", "test" } ],
  "results": { "<env id>": { "<check id>": {
      "status": "pass | fail | running | pending",
      "at": "ISO-8601 | null", "detail": "string | null" } } },
  "room": { "name",
            "agents": [ { "name", "provider", "machine", "online": bool,
                          "roles": [ { "name", "mode": "exclusive | shared" } ] } ],
            "humans": [ { "name", "title" } ] },
  "timeline": [ { "at", "actor", "kind": "human | agent", "title", "detail" } ],
  "links": { "room": "https://..." }                        // optional; adds a read-only "Open room" link
}
```

The UI renders only what is in this shape. Nothing else is invented: no extra controls, hosts, models or nav.

## What is derived from the data

- **Parity alert** (shown only when it applies): at least one environment has passes and no failures while another has
  failures, e.g. "Mac passes 3/3 but Linux fails 3/3: environment-dependent failures." It also lists every environment
  `fact` whose value differs between environments (the same facts carry a `≠` marker in the matrix).
- Per-environment badge (`PASSING 3/3`, `FAILING 0/3`, ...), summary counts, "N of M results in".
- Overall chip subline ("3 of 6 checks passing") is computed from the results; the chip itself uses `status` verbatim.
- Timeline is sorted oldest first, newest last, with the newest marked `LATEST`.
- Times are viewer-local `HH:MM:SS` (hover shows the full local date and the original ISO string).

## Behavior and robustness

- Rendering is per section and only when that section's data changed, so hover, focus and animations are not reset by
  each poll. Matrix cells whose status changed get a short flip animation; new timeline events slide in.
- `prefers-reduced-motion: reduce` disables all animation (including the spinner and live beacon).
- Every data string is inserted via `textContent` / text nodes. `innerHTML` is never used. `links.room` is only used
  if it starts with `http://` or `https://`.
- Fonts: `Inter` and `JetBrains Mono` from an optional, non-blocking Google Fonts `<link>`; the UI is fully styled with
  `ui-sans-serif/system-ui` and `ui-monospace/SF Mono/Menlo` when offline (verified).

## Accessibility

Status is always icon + text + color (check / x / spinner arc / dashed clock), never color alone. Text contrast on the
dark theme is 6.5:1 or better (most pairs above 10:1). `tabular-nums` on all numbers, visible 2 px focus rings,
skip link, landmarks (`banner`, `main`, `complementary`), ARIA table roles on the matrix, `role=status` live regions for the
overall and connection chips, `role=alert` for the parity alert.

## Deviations from the design reference (deliberate)

- Mock-only content was removed (nav tabs, release candidate, mesh sync, protocol versions, host names, model names,
  stack traces, action buttons, scroll-lock, filters).
- `label-sm` is 11 px instead of 10 px, and small status text uses lighter tints of the semantic colors
  (`#34D399` pass, `#FB7185` fail) so every text pair clears WCAG AA+; icons, borders and fills use the spec colors.
- Below 1100 px the right rail stacks under the main column (agents and humans side by side) instead of shrinking the matrix.
