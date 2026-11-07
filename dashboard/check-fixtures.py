#!/usr/bin/env python3
"""Validate Parity Room state fixtures against the schema-1 data contract.

Dependency-free (stdlib only). Usage:
    python3 check-fixtures.py                # checks fixtures/state-*.json next to this script
    python3 check-fixtures.py path/a.json ...
Exit code: 0 = all valid, 1 = at least one contract violation, 2 = usage/IO error.
Soft consistency findings are printed as "warn:" and never change the exit code.
"""
import glob
import json
import os
import sys
from datetime import datetime

OVERALL = ("pending", "running", "failing", "verified")
RESULT = ("pass", "fail", "running", "pending")
KINDS = ("human", "agent")
MODES = ("exclusive", "shared")


def is_str(v):
    return isinstance(v, str)


def is_obj(v):
    return isinstance(v, dict)


def iso_ok(v):
    if not is_str(v):
        return False
    try:
        datetime.fromisoformat(v.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def err(self, path, msg):
        self.errors.append("%s: %s" % (path, msg))

    def warn(self, path, msg):
        self.warnings.append("%s: %s" % (path, msg))


def need(r, obj, path, key, check, what):
    """Require obj[key] to exist and satisfy check(value); return value or None."""
    if not is_obj(obj) or key not in obj:
        r.err(path + "." + key if path else key, "missing required key")
        return None
    v = obj[key]
    if not check(v):
        r.err(path + "." + key if path else key, "expected %s, got %r" % (what, v))
        return None
    return v


def one_of(values):
    return lambda v: is_str(v) and v in values


def validate(s):
    r = Report()
    if not is_obj(s):
        r.err("$", "top level must be an object")
        return r

    if s.get("schema") != 1 or isinstance(s.get("schema"), bool):
        r.err("schema", "must be the integer 1, got %r" % (s.get("schema"),))
    need(r, s, "", "updated_at", iso_ok, "ISO-8601 timestamp string")
    status = need(r, s, "", "status", one_of(OVERALL), "one of %s" % "|".join(OVERALL))

    # change
    change = need(r, s, "", "change", is_obj, "object")
    if change is not None:
        for k in ("branch", "head_sha", "author", "title"):
            need(r, change, "change", k, is_str, "string")

    # environments
    env_ids = []
    envs = need(r, s, "", "environments", lambda v: isinstance(v, list), "array")
    for i, e in enumerate(envs or []):
        p = "environments[%d]" % i
        if not is_obj(e):
            r.err(p, "must be an object")
            continue
        for k in ("id", "label", "agent", "provider", "machine"):
            need(r, e, p, k, is_str, "string")
        facts = need(r, e, p, "facts", is_obj, "object")
        for fk, fv in (facts or {}).items():
            if not is_str(fv):
                r.err("%s.facts.%s" % (p, fk), "expected string, got %r" % (fv,))
        if is_str(e.get("id")):
            if e["id"] in env_ids:
                r.err(p + ".id", "duplicate id %r" % e["id"])
            env_ids.append(e["id"])

    # checks
    check_ids = []
    checks = need(r, s, "", "checks", lambda v: isinstance(v, list), "array")
    for i, c in enumerate(checks or []):
        p = "checks[%d]" % i
        if not is_obj(c):
            r.err(p, "must be an object")
            continue
        for k in ("id", "title", "test"):
            need(r, c, p, k, is_str, "string")
        if is_str(c.get("id")):
            if c["id"] in check_ids:
                r.err(p + ".id", "duplicate id %r" % c["id"])
            check_ids.append(c["id"])

    # results: results[env_id][check_id] = {status, at, detail}
    results = need(r, s, "", "results", is_obj, "object")
    all_statuses = []
    if results is not None:
        for eid in results:
            if eid not in env_ids:
                r.err("results." + eid, "unknown environment id")
        for eid in env_ids:
            row = results.get(eid)
            if not is_obj(row):
                r.err("results." + eid, "missing or not an object")
                continue
            for cid in row:
                if cid not in check_ids:
                    r.err("results.%s.%s" % (eid, cid), "unknown check id")
            for cid in check_ids:
                p = "results.%s.%s" % (eid, cid)
                cell = row.get(cid)
                if not is_obj(cell):
                    r.err(p, "missing or not an object")
                    continue
                st = need(r, cell, p, "status", one_of(RESULT), "one of %s" % "|".join(RESULT))
                if st:
                    all_statuses.append(st)
                need(r, cell, p, "at", lambda v: v is None or iso_ok(v), "ISO-8601 string or null")
                need(r, cell, p, "detail", lambda v: v is None or is_str(v), "string or null")
                if st == "fail" and not (is_str(cell.get("detail")) and cell.get("detail")):
                    r.warn(p, "failing result has no detail line")
                if st in ("pass", "fail") and cell.get("at") is None:
                    r.warn(p, "completed result has no 'at' timestamp")

    # room
    room = need(r, s, "", "room", is_obj, "object")
    if room is not None:
        need(r, room, "room", "name", is_str, "string")
        agents = need(r, room, "room", "agents", lambda v: isinstance(v, list), "array")
        for i, a in enumerate(agents or []):
            p = "room.agents[%d]" % i
            if not is_obj(a):
                r.err(p, "must be an object")
                continue
            for k in ("name", "provider", "machine"):
                need(r, a, p, k, is_str, "string")
            need(r, a, p, "online", lambda v: isinstance(v, bool), "boolean")
            roles = need(r, a, p, "roles", lambda v: isinstance(v, list), "array")
            for j, ro in enumerate(roles or []):
                rp = "%s.roles[%d]" % (p, j)
                if not is_obj(ro):
                    r.err(rp, "must be an object")
                    continue
                need(r, ro, rp, "name", is_str, "string")
                need(r, ro, rp, "mode", one_of(MODES), "one of %s" % "|".join(MODES))
        humans = need(r, room, "room", "humans", lambda v: isinstance(v, list), "array")
        for i, h in enumerate(humans or []):
            p = "room.humans[%d]" % i
            if not is_obj(h):
                r.err(p, "must be an object")
                continue
            need(r, h, p, "name", is_str, "string")
            need(r, h, p, "title", is_str, "string")
        # environments should reference an agent in the room
        names = [a.get("name") for a in (agents or []) if is_obj(a)]
        for i, e in enumerate(envs or []):
            if is_obj(e) and is_str(e.get("agent")) and e["agent"] not in names:
                r.warn("environments[%d].agent" % i, "agent %r is not listed in room.agents" % e["agent"])

    # timeline
    tl = need(r, s, "", "timeline", lambda v: isinstance(v, list), "array")
    for i, ev in enumerate(tl or []):
        p = "timeline[%d]" % i
        if not is_obj(ev):
            r.err(p, "must be an object")
            continue
        need(r, ev, p, "at", iso_ok, "ISO-8601 timestamp string")
        need(r, ev, p, "actor", is_str, "string")
        need(r, ev, p, "kind", one_of(KINDS), "one of %s" % "|".join(KINDS))
        need(r, ev, p, "title", is_str, "string")
        need(r, ev, p, "detail", is_str, "string (may be empty)")

    # optional
    if "links" in s:
        links = s["links"]
        if not is_obj(links):
            r.err("links", "expected object")
        elif "room" in links and not is_str(links["room"]):
            r.err("links.room", "expected string")

    # soft consistency between overall status and cell statuses
    if status and all_statuses and not r.errors:
        if status == "verified" and any(x != "pass" for x in all_statuses):
            r.warn("status", "'verified' but not every result is 'pass'")
        if status == "failing" and "fail" not in all_statuses:
            r.warn("status", "'failing' but no result is 'fail'")
        if status == "running" and "running" not in all_statuses:
            r.warn("status", "'running' but no result is 'running'")
        if status == "pending" and any(x != "pending" for x in all_statuses):
            r.warn("status", "'pending' but some results are not 'pending'")
    return r


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    paths = argv[1:] or sorted(glob.glob(os.path.join(here, "fixtures", "state-*.json")))
    if not paths:
        print("no fixtures found", file=sys.stderr)
        return 2
    bad = 0
    for path in paths:
        name = os.path.relpath(path)
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as exc:
            print("FAIL %s\n  - cannot read/parse: %s" % (name, exc))
            bad += 1
            continue
        rep = validate(data)
        if rep.errors:
            bad += 1
            print("FAIL %s" % name)
            for m in rep.errors:
                print("  - %s" % m)
        else:
            print("ok   %s" % name)
        for m in rep.warnings:
            print("  warn: %s" % m)
    print("%d file(s) checked, %d invalid" % (len(paths), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
