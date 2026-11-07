#!/usr/bin/env python3
"""Parity Room observer: live data feed for the dashboard (stdlib only, read-only).

Serves ../dashboard/ at / and GET /api/state (data contract, schema 1) + GET /healthz.
A background thread polls the Switch gateway and Mattermost every ~2 s (read-only GETs),
composes the state with `compose()` and caches it; HTTP requests only ever read the cache.

  python3 observer/server.py [--port 8090] [--host 127.0.0.1] [--interval 2]

Credentials come from ../stack/.env (GATEWAY_ADMIN_EMAIL/PASSWORD, MATTERMOST_ADMIN_USER/PASSWORD)
and are never logged. See observer/README.md for how the state is derived.
"""
import argparse
import functools
import http.cookiejar
import json
import os
import re
import signal
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DASHBOARD_DIR = os.path.join(ROOT, "dashboard")
DEFAULT_ENV_FILE = os.path.join(ROOT, "stack", ".env")

SWITCH_URL = "http://localhost:8000"
MM_URL = "http://localhost:8065"
ROOM_NAME = "parity-room"
MM_TEAM = "switch"


def active_room():
    """$PARITY_ROOM, else work/room.txt (written by scripts/run-template.py), else the default."""
    if os.environ.get("PARITY_ROOM"):
        return os.environ["PARITY_ROOM"]
    try:
        with open(os.path.join(ROOT, "work", "room.txt")) as fh:
            return fh.read().strip() or ROOM_NAME
    except OSError:
        return ROOM_NAME

# ---- static configuration (the demo's cast; everything else is read live) -----------------
CHANGE_TITLE = "feat: weekly digest report"
CHANGE_AUTHOR = "Priya"
ENV_DEFS = [  # default agent/provider/machine; live gateway data overrides provider + machine
    {"id": "mac", "label": "Mac", "agent": "dev-mac", "provider": "Claude Code", "machine": "mac-host",
     "doc": "matrix-mac"},
    {"id": "linux", "label": "Linux", "agent": "qa-linux", "provider": "Codex", "machine": "linux-box",
     "doc": "matrix-linux"},
]
CHECKS = [  # keep in sync with tools/parity_matrix.py and dashboard/fixtures
    {"id": "settings", "title": "Settings file loads", "test": "test_load_settings"},
    {"id": "stamp", "title": "UTC timestamp helper", "test": "test_stamp_is_utc_iso"},
    {"id": "buckets", "title": "Day bucketing", "test": "test_bucket_by_day"},
]
FACT_KEYS = ("os", "python", "tz", "fs")
HUMAN_TITLES = {"maya": "PM", "sam": "QA lead"}   # fallback when Mattermost has no `position`
PROVIDER_LABELS = {"claude-code": "Claude Code", "codex": "Codex"}  # gateway known_agent_type
IGNORED_USERS = {"admin", "switch-admin"}
TIMELINE_MAX = 12
TITLE_MAX = 110
DETAIL_MAX = 220
RESULT_STATUSES = ("pass", "fail", "running", "pending")

# Bot chatter that is bookkeeping, not an event worth showing.
NOISE_PATTERNS = [re.compile(p) for p in (
    r"^\W*(created|updated) room document",
    r"^Starting a session",
    r"^\W*assumed the `?\w+`? role",
    r"^(Hello|Hey)! (I'm ready|Ping @)",
    r"^Template kickoff",
    r"^\**(Working|Worked)\b",
)]


def log(msg):
    print("[observer %s] %s" % (time.strftime("%H:%M:%S"), msg), file=sys.stderr, flush=True)


# ---- small helpers --------------------------------------------------------------------------
def utcnow():
    return datetime.now(timezone.utc)


def iso_z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(v):
    if not isinstance(v, str):
        return None
    try:
        dt = datetime.fromisoformat(v.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def as_list(v):
    return v if isinstance(v, list) else []


def as_dict(v):
    return v if isinstance(v, dict) else {}


def load_env_file(path):
    out = {}
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    v = v.strip()
                    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                        v = v[1:-1]
                    out[k.strip()] = v
    except OSError as exc:
        log("cannot read env file %s: %s" % (path, exc.strerror or exc))
    return out


# ---- markdown -> plain text for the timeline --------------------------------------------------
def strip_markdown_lines(text):
    """Return the non-empty lines of `text` with common markdown syntax removed."""
    t = re.sub(r"```[A-Za-z0-9_+-]*", "", text or "")
    t = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"`([^`\n]*)`", r"\1", t)
    t = re.sub(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1", r"\2", t)
    t = re.sub(r"(?<![\w*])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![\w*])", r"\1", t)
    t = re.sub(r"~~(.+?)~~", r"\1", t)
    lines = []
    for ln in t.splitlines():
        ln = re.sub(r"^\s*(#{1,6}\s+|>\s?|[-*+•]\s+|\d+[.)]\s+)", "", ln)
        ln = re.sub(r"\s+", " ", ln).strip()
        if ln:
            lines.append(ln)
    return lines


def clip(s, n):
    s = s.strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def title_and_detail(message):
    """First line -> title (<=110, cut at a word boundary), the rest -> detail (<=220)."""
    lines = strip_markdown_lines(message)
    if not lines:
        return "", ""
    first, rest = lines[0], " ".join(lines[1:])
    if len(first) <= TITLE_MAX:
        return first, clip(rest, DETAIL_MAX)
    # Too long for a title: prefer the last sentence end that fits, else cut at a word boundary.
    ends = [m.start() + 1 for m in re.finditer(r"[.!?](?=\s)", first) if 20 <= m.start() + 1 <= TITLE_MAX]
    if ends:
        return first[: ends[-1]], clip((first[ends[-1]:].strip() + " " + rest).strip(), DETAIL_MAX)
    cut = first[: TITLE_MAX - 1]
    sp = cut.rfind(" ")
    if sp >= TITLE_MAX // 2:
        cut = cut[:sp]
    title = cut.rstrip(" ,;:-—") + "…"
    overflow = first[len(cut):].strip()
    return title, clip(("…" + overflow + " " + rest).strip(), DETAIL_MAX)


# ---- state composition (pure: raw API data in, schema-1 state out) --------------------------
def find_room(rooms, name):
    for r in as_list(rooms):
        if isinstance(r, dict) and r.get("name") == name and not r.get("archived"):
            return r
    return None


def parse_matrix(env, doc):
    """Interpret one matrix-* document. Returns a dict with state missing | invalid | ok."""
    content = as_dict(doc).get("content")
    if content is None or (isinstance(content, str) and not content.strip()):
        return {"state": "missing"}
    try:
        data = json.loads(content)
    except (TypeError, ValueError):
        return {"state": "invalid", "reason": "matrix document is not valid JSON"}
    if not isinstance(data, dict) or not isinstance(data.get("results"), dict):
        return {"state": "invalid", "reason": "matrix document is not a schema-1 evidence object"}
    if data.get("schema") != 1:
        return {"state": "invalid", "reason": "matrix document has unsupported schema %r" % (data.get("schema"),)}
    if data.get("env") not in (None, env["id"]):
        return {"state": "invalid", "reason": "matrix document is for env %r, expected %r" % (data.get("env"), env["id"])}
    change = as_dict(data.get("change"))
    return {
        "state": "ok",
        "ran_at": parse_iso(data.get("ran_at")),
        "branch": change.get("branch") if isinstance(change.get("branch"), str) else "",
        "head_sha": change.get("head_sha") if isinstance(change.get("head_sha"), str) else "",
        "facts": as_dict(data.get("facts")),
        "results": data["results"],
    }


def cell(status="pending", at=None, detail=None):
    return {"status": status, "at": at, "detail": detail}


def results_from_doc(res):
    out = {}
    for c in CHECKS:
        r = res.get(c["id"])
        if not isinstance(r, dict):
            out[c["id"]] = cell("pending", None, "check missing from matrix document")
            continue
        st = r.get("status")
        if st not in RESULT_STATUSES:
            out[c["id"]] = cell("pending", None, "unrecognised status %r in matrix document" % (st,))
            continue
        at = r.get("at") if parse_iso(r.get("at")) else None
        d = r.get("detail")
        out[c["id"]] = cell(st, at, d if d is None or isinstance(d, str) else str(d))
    return out


def machine_by_agent_id(controllers):
    out = {}
    for c in as_list(controllers):
        c = as_dict(c)
        for a in as_list(as_dict(c.get("status")).get("agents")):
            a = as_dict(a)
            if a.get("agent_id") and isinstance(c.get("name"), str):
                out[a["agent_id"]] = c["name"]
    return out


def provider_label(agent):
    agent = as_dict(agent)
    return PROVIDER_LABELS.get(agent.get("known_agent_type")) or agent.get("connector_type") or None


def build_timeline(raw, users):
    """Meaningful Mattermost posts, oldest first, newest 12. Returns (events, posting human names)."""
    posts = as_dict(raw.get("mm_posts"))
    by_id = as_dict(posts.get("posts"))
    events, posters = [], set()
    for pid in as_list(posts.get("order")):
        p = by_id.get(pid)
        if not isinstance(p, dict) or p.get("type") or p.get("delete_at"):
            continue  # system posts (joins/adds), deleted posts
        u = as_dict(users.get(p.get("user_id")))
        name = u.get("username")
        if not name or name in IGNORED_USERS:
            continue
        is_bot = bool(u.get("is_bot"))
        if not is_bot:
            posters.add(name)
        msg = p.get("message") if isinstance(p.get("message"), str) else ""
        if as_dict(p.get("props")).get("attachments"):
            continue  # "Worked for ..." progress cards
        if any(rx.search(msg.strip()) for rx in NOISE_PATTERNS):
            continue
        title, detail = title_and_detail(msg)
        ts = p.get("create_at")
        if not title or not isinstance(ts, (int, float)):
            continue
        events.append((ts, {
            "at": iso_z(datetime.fromtimestamp(ts / 1000.0, timezone.utc)),
            "actor": name,
            "kind": "agent" if is_bot else "human",
            "title": title,
            "detail": detail,
        }))
    events.sort(key=lambda e: e[0])
    return [e for _, e in events][-TIMELINE_MAX:], posters


def build_humans(raw, users, posters, room_item):
    if users:
        humans_by_name = {u["username"]: u for u in users.values()
                          if u.get("username") and not u.get("is_bot") and u["username"] not in IGNORED_USERS}
        member_ids = {m.get("user_id") for m in as_list(raw.get("mm_members")) if isinstance(m, dict)}
        candidates = {u["username"] for uid, u in users.items() if uid in member_ids} & set(humans_by_name)
        candidates |= posters & set(humans_by_name)
        humans = {n: humans_by_name[n].get("position") or HUMAN_TITLES.get(n, "") for n in candidates}
        # an untitled member who never posted (e.g. a service account) is not shown
        humans = {n: t for n, t in humans.items() if t or n in posters}
    else:  # Mattermost unavailable: only gateway-connected users that we can title
        humans = {n: HUMAN_TITLES[n] for n in as_list(as_dict(room_item).get("connected_user_names")) if n in HUMAN_TITLES}
    order = list(HUMAN_TITLES)
    return [{"name": n, "title": humans[n]} for n in sorted(humans, key=lambda x: (order.index(x) if x in order else 99, x))]


def compose(raw, now=None, room_name=ROOM_NAME, mm_url=MM_URL):
    """Build the schema-1 state. `raw` holds the last good API responses (any key may be missing)."""
    raw = as_dict(raw)
    now = now or utcnow()
    room_item = find_room(raw.get("rooms"), room_name)
    room = as_dict(raw.get("room")) if room_item else {}
    docs = as_dict(raw.get("documents")) if room_item else {}
    agents = [a for a in as_list(raw.get("agents")) if isinstance(a, dict)]
    by_name = {a.get("name"): a for a in agents}
    by_id = {a.get("id"): a for a in agents}
    machines = machine_by_agent_id(raw.get("controllers"))

    # --- environments + per-env evidence
    parsed = {e["id"]: parse_matrix(e, docs.get(e["doc"])) for e in ENV_DEFS}
    ok = [(e, parsed[e["id"]]) for e in ENV_DEFS if parsed[e["id"]]["state"] == "ok"]
    newest = None
    if ok:  # newest ran_at wins; unparseable ran_at counts as oldest
        floor = datetime.min.replace(tzinfo=timezone.utc)
        newest = max(ok, key=lambda ep: ep[1]["ran_at"] or floor)[1]

    environments, results = [], {}
    for e in ENV_DEFS:
        p = parsed[e["id"]]
        ag = by_name.get(e["agent"])
        facts = {k: "unknown" for k in FACT_KEYS}
        if p["state"] == "ok":
            for k in FACT_KEYS:
                v = p["facts"].get(k)
                if isinstance(v, str) and v:
                    facts[k] = v
            if p["head_sha"] != newest["head_sha"]:   # stale: the other env verified a newer commit
                results[e["id"]] = {c["id"]: cell("running") for c in CHECKS}
            else:
                results[e["id"]] = results_from_doc(p["results"])
        elif p["state"] == "invalid":
            results[e["id"]] = {c["id"]: cell("pending", None, p["reason"]) for c in CHECKS}
        else:
            results[e["id"]] = {c["id"]: cell("pending") for c in CHECKS}
        environments.append({
            "id": e["id"], "label": e["label"], "agent": e["agent"],
            "provider": provider_label(ag) or e["provider"],
            "machine": machines.get(as_dict(ag).get("id")) or e["machine"],
            "facts": facts,
        })

    statuses = [c["status"] for row in results.values() for c in row.values()]
    if not ok:
        status = "pending"
    elif "fail" in statuses:
        status = "failing"
    elif "running" in statuses:
        status = "running"
    elif all(s == "pass" for s in statuses):
        status = "verified"
    else:
        status = "pending"   # e.g. one environment has no usable evidence yet

    # --- room
    statuses_by_id = as_dict(room.get("agent_statuses"))
    roles = as_list(raw.get("roles")) or as_list(room.get("roles"))
    room_agents = []
    for aid in as_list(room.get("agent_ids")):
        a = by_id.get(aid)
        if not a or not isinstance(a.get("name"), str):
            continue
        default = next((e for e in ENV_DEFS if e["agent"] == a["name"]), {})
        room_agents.append({
            "name": a["name"],
            "provider": provider_label(a) or default.get("provider", "unknown"),
            "machine": machines.get(aid) or default.get("machine", "unknown"),
            "online": statuses_by_id.get(aid) == "live",
            "roles": [{"name": r["name"], "mode": "exclusive" if r.get("exclusive") else "shared"}
                      for r in roles if isinstance(r, dict) and isinstance(r.get("name"), str)
                      and a["name"] in as_list(r.get("held_by"))],
        })

    users = {k: v for k, v in as_dict(raw.get("mm_users")).items() if isinstance(v, dict)}
    timeline, posters = build_timeline(raw, users) if room_item else ([], set())
    humans = build_humans(raw, users, posters, room_item) if room_item else []

    return {
        "schema": 1,
        "updated_at": iso_z(now),
        "status": status,
        "change": {
            "branch": newest["branch"] if newest else "",
            "head_sha": newest["head_sha"] if newest else "",
            "author": CHANGE_AUTHOR,
            "title": CHANGE_TITLE,
        },
        "environments": environments,
        "checks": [dict(c) for c in CHECKS],
        "results": results,
        "room": {"name": room_name, "agents": room_agents, "humans": humans},
        "timeline": timeline,
        "links": {"room": "%s/%s/channels/%s" % (mm_url.rstrip("/"), MM_TEAM, room_name)},
    }


# ---- HTTP clients (read-only GETs after login) ----------------------------------------------
class SourceError(Exception):
    pass


class _Client:
    timeout = 5

    def _open(self, opener, req, what):
        try:
            with opener(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
                return resp, (json.loads(raw) if raw.strip() else None)
        except urllib.error.HTTPError as exc:
            raise SourceError("%s: HTTP %d" % (what, exc.code))
        except (urllib.error.URLError, OSError) as exc:
            raise SourceError("%s: %s" % (what, getattr(exc, "reason", exc)))
        except ValueError:
            raise SourceError("%s: response is not JSON" % what)


class GatewayClient(_Client):
    """Switch gateway: cookie session from POST /gateway/auth/login; re-login once on 401."""

    def __init__(self, base, email, password):
        self.base, self._cred = base.rstrip("/"), {"email": email, "password": password}
        self._jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._jar))
        self._logged_in = False
        self._lock = threading.Lock()

    def _request(self, method, path, body=None):
        req = urllib.request.Request(self.base + path, method=method, headers={"Content-Type": "application/json"},
                                     data=None if body is None else json.dumps(body).encode())
        return self._open(self._opener.open, req, "%s %s" % (method, path))[1]

    def login(self):
        self._request("POST", "/gateway/auth/login", self._cred)
        self._logged_in = True

    def get(self, path):
        with self._lock:
            if not self._logged_in:
                self.login()
            try:
                return self._request("GET", path)
            except SourceError as exc:
                if not str(exc).endswith("HTTP 401"):
                    raise
                self.login()
                return self._request("GET", path)


class MattermostClient(_Client):
    """Mattermost REST v4 as the MM admin (read-only use): Token header from /users/login."""

    def __init__(self, base, user, password):
        self.base, self._cred = base.rstrip("/") + "/api/v4", {"login_id": user, "password": password}
        self._token = None
        self._lock = threading.Lock()

    def login(self):
        req = urllib.request.Request(self.base + "/users/login", method="POST",
                                     headers={"Content-Type": "application/json"},
                                     data=json.dumps(self._cred).encode())
        resp, _ = self._open(urllib.request.urlopen, req, "POST /users/login")
        self._token = resp.headers.get("Token")
        if not self._token:
            raise SourceError("POST /users/login: no Token header")

    def _get(self, path):
        req = urllib.request.Request(self.base + path, headers={"Authorization": "Bearer " + self._token})
        return self._open(urllib.request.urlopen, req, "GET " + path)[1]

    def get(self, path):
        with self._lock:
            if not self._token:
                self.login()
            try:
                return self._get(path)
            except SourceError as exc:
                if not str(exc).endswith("HTTP 401"):
                    raise
                self.login()
                return self._get(path)


# ---- poller + cache ---------------------------------------------------------------------------
class Observer:
    """Polls the sources, keeps the last good raw data per key, caches the composed state."""

    def __init__(self, gateway=None, mattermost=None, interval=2.0, slow_every=5.0, mm_url=MM_URL):
        self.gw, self.mm = gateway, mattermost
        self.interval, self.slow_every, self.mm_url = interval, slow_every, mm_url
        self.raw = {}
        self._slow_at = {"gateway": float("-inf"), "mattermost": float("-inf")}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self.sources = {"gateway": {"ok": None, "error": None, "last_ok_at": None},
                        "mattermost": {"ok": None, "error": None, "last_ok_at": None}}
        self.polls = 0
        self.last_poll_at = None
        self._body = b""
        self._status = "pending"
        self.publish()

    # -- cache
    def publish(self):
        state = compose(self.raw, mm_url=self.mm_url, room_name=active_room())
        body = json.dumps(state, indent=2, ensure_ascii=False).encode("utf-8")
        with self._lock:
            self._body, self._status = body, state["status"]

    def state_bytes(self):
        with self._lock:
            return self._body

    def health(self):
        with self._lock:
            return {"ok": True, "status": self._status, "polls": self.polls, "last_poll_at": self.last_poll_at,
                    "sources": json.loads(json.dumps(self.sources))}

    # -- polling
    def _note(self, source, err):
        s = self.sources[source]
        prev = s["error"]
        s["ok"], s["error"] = err is None, err
        if err is None:
            s["last_ok_at"] = iso_z(utcnow())
        if err != prev:
            log("%s: %s" % (source, err) if err else "%s: recovered" % source)

    def _slow_due(self, source):
        now = time.monotonic()
        if now - self._slow_at[source] >= self.slow_every:
            self._slow_at[source] = now
            return True
        return False

    def _try(self, key, fn, errors):
        """Refresh raw[key]; on failure keep the last good value and remember the error."""
        try:
            self.raw[key] = fn()
            return True
        except Exception as exc:  # noqa: BLE001 - the poller must never die
            errors.append("%s: %s" % (key, exc))
            return False

    def poll_gateway(self):
        if not self.gw:
            return
        errors = []
        if self._try("rooms", lambda: self.gw.get("/gateway/rooms"), errors):
            room = find_room(self.raw.get("rooms"), active_room())
            if room is None:  # the room genuinely does not exist (yet): drop room-scoped data
                for k in ("room", "roles", "documents"):
                    self.raw.pop(k, None)
                self.raw.pop("_room_id", None)
            else:
                rid = room["id"]
                if self.raw.get("_room_id") != rid:
                    for k in ("room", "roles", "documents"):
                        self.raw.pop(k, None)
                    self.raw["_room_id"] = rid
                self._try("room", lambda: self.gw.get("/gateway/rooms/%s" % rid), errors)
                self._try("roles", lambda: self.gw.get("/gateway/rooms/%s/roles" % rid), errors)
                self._poll_documents(rid, errors)
        if self._slow_due("gateway"):
            self._try("agents", lambda: self.gw.get("/gateway/agents"), errors)
            self._try("controllers", lambda: self.gw.get("/gateway/management/controllers"), errors)
        self._note("gateway", "; ".join(errors) if errors else None)

    def _poll_documents(self, rid, errors):
        try:
            listing = as_list(self.gw.get("/gateway/rooms/%s/documents" % rid))
        except Exception as exc:  # noqa: BLE001
            errors.append("documents: %s" % exc)
            return
        docs = self.raw.setdefault("documents", {})
        for e in ENV_DEFS:
            item = next((d for d in listing if isinstance(d, dict) and d.get("name") == e["doc"]), None)
            if item is None:
                docs[e["doc"]] = None     # not written yet: a truthful "missing"
                continue
            try:
                docs[e["doc"]] = self.gw.get("/gateway/rooms/%s/documents/%s" % (rid, item["id"]))
            except Exception as exc:  # noqa: BLE001
                errors.append("document %s: %s" % (e["doc"], exc))

    def poll_mattermost(self):
        if not self.mm:
            return
        errors = []
        try:
            room_now = active_room()
            if not self.raw.get("mm_channel") or self.raw.get("_mm_channel_for") != room_now:
                team = self.mm.get("/teams/name/%s" % MM_TEAM)
                self.raw["mm_channel"] = self.mm.get("/teams/%s/channels/name/%s" % (team["id"], room_now))
                self.raw["_mm_channel_for"] = room_now
            cid = self.raw["mm_channel"]["id"]
            self.raw["mm_posts"] = self.mm.get("/channels/%s/posts?per_page=200" % cid)
            slow = self._slow_due("mattermost")
            if slow or "mm_members" not in self.raw:
                self.raw["mm_members"] = self.mm.get("/channels/%s/members?per_page=200" % cid)
            users = self.raw.setdefault("mm_users", {})
            wanted = {p.get("user_id") for p in as_dict(as_dict(self.raw["mm_posts"]).get("posts")).values()
                      if isinstance(p, dict)}
            wanted |= {m.get("user_id") for m in as_list(self.raw["mm_members"]) if isinstance(m, dict)}
            for uid in sorted(x for x in wanted if isinstance(x, str)):
                if uid in users and not slow:
                    continue
                u = self.mm.get("/users/%s" % uid)   # keep only non-PII fields
                users[uid] = {"id": uid, "username": u.get("username"), "is_bot": bool(u.get("is_bot")),
                              "position": u.get("position") or ""}
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))
            if isinstance(exc, SourceError) and "channels/name" in str(exc):
                self.raw.pop("mm_channel", None)
        self._note("mattermost", "; ".join(errors) if errors else None)

    def poll_once(self):
        for fn in (self.poll_gateway, self.poll_mattermost):
            try:
                fn()
            except Exception as exc:  # noqa: BLE001
                log("poller error in %s: %r" % (fn.__name__, exc))
        try:
            self.publish()
        except Exception as exc:  # noqa: BLE001
            log("compose failed, keeping previous state: %r" % (exc,))
        self.polls += 1
        self.last_poll_at = iso_z(utcnow())

    def run(self):
        while not self._stop.is_set():
            t0 = time.monotonic()
            self.poll_once()
            self._stop.wait(max(0.2, self.interval - (time.monotonic() - t0)))

    def start(self):
        t = threading.Thread(target=self.run, name="observer-poller", daemon=True)
        t.start()
        return t

    def stop(self):
        self._stop.set()


# ---- HTTP server ------------------------------------------------------------------------------
class Handler(SimpleHTTPRequestHandler):
    server_version = "ParityObserver/1"
    QUIET = ("/api/state", "/healthz")

    def _path(self):
        return self.path.split("?", 1)[0].split("#", 1)[0]

    def _send_json(self, code, body, head=False):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def _api(self, head):
        path = self._path()
        obs = self.server.observer
        if path == "/api/state":
            self._send_json(200, obs.state_bytes(), head)
        elif path == "/healthz":
            self._send_json(200, json.dumps(obs.health()).encode(), head)
        elif path.startswith("/api/"):
            self._send_json(404, b'{"error":"not found"}', head)
        else:
            return False
        return True

    def do_GET(self):
        if not self._api(False):
            super().do_GET()

    def do_HEAD(self):
        if not self._api(True):
            super().do_HEAD()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        if self._path() in self.QUIET and not getattr(self.server, "verbose", False):
            return
        super().log_message(fmt, *args)


def make_server(observer, host="127.0.0.1", port=8090, directory=DASHBOARD_DIR, verbose=False):
    srv = ThreadingHTTPServer((host, port), functools.partial(Handler, directory=directory))
    srv.daemon_threads = True
    srv.observer, srv.verbose = observer, verbose
    return srv


def main(argv=None):
    ap = argparse.ArgumentParser(description="Parity Room live data feed + dashboard server (read-only).")
    ap.add_argument("--port", type=int, default=8090)
    ap.add_argument("--host", default="127.0.0.1", help="bind address (default 127.0.0.1)")
    ap.add_argument("--interval", type=float, default=2.0, help="poll interval in seconds")
    ap.add_argument("--env-file", default=DEFAULT_ENV_FILE)
    ap.add_argument("--switch-url", default=os.environ.get("SWITCH_URL", SWITCH_URL))
    ap.add_argument("--mm-url", default=os.environ.get("MM_URL", MM_URL))
    ap.add_argument("--verbose", action="store_true", help="also log /api/state and /healthz requests")
    a = ap.parse_args(argv)

    env = load_env_file(a.env_file)
    gw = mm = None
    if env.get("GATEWAY_ADMIN_EMAIL") and env.get("GATEWAY_ADMIN_PASSWORD"):
        gw = GatewayClient(a.switch_url, env["GATEWAY_ADMIN_EMAIL"], env["GATEWAY_ADMIN_PASSWORD"])
    else:
        log("GATEWAY_ADMIN_EMAIL/PASSWORD missing in %s: serving pending state only" % a.env_file)
    if env.get("MATTERMOST_ADMIN_USER") and env.get("MATTERMOST_ADMIN_PASSWORD"):
        mm = MattermostClient(a.mm_url, env["MATTERMOST_ADMIN_USER"], env["MATTERMOST_ADMIN_PASSWORD"])
    else:
        log("MATTERMOST_ADMIN_USER/PASSWORD missing in %s: no timeline" % a.env_file)

    obs = Observer(gw, mm, interval=a.interval, mm_url=a.mm_url)
    srv = make_server(obs, a.host, a.port, verbose=a.verbose)
    obs.start()
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=srv.shutdown, daemon=True).start())
    log("serving dashboard + /api/state on http://%s:%d/ (polling %s and %s every %.1fs)"
        % (a.host, a.port, a.switch_url, a.mm_url, a.interval))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        obs.stop()
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
