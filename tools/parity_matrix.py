#!/usr/bin/env python3
"""parity_matrix: run the SUT's tests in THIS environment and emit machine-readable evidence.

Deterministic on purpose: the agents reason about *why* things fail; this script records *what*
happened (so the room's matrix documents can't be hallucinated).

  python3 parity_matrix.py --repo <dir> --env linux          # prints JSON on stdout
  python3 parity_matrix.py --repo <dir> --env mac --out m.json

Needs only the stdlib + pytest (run it with the interpreter that has pytest).
Compatible with Python >= 3.8 (it must run on the old-Python Linux box too).
"""
import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# check id -> (human title, pytest test name).
CHECKS = [
    ("settings", "Settings file loads", "test_load_settings"),
    ("stamp", "UTC timestamp helper", "test_stamp_is_utc_iso"),
    ("buckets", "Day bucketing", "test_bucket_by_day"),
]


def sh(cmd, cwd=None):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def fs_case_sensitive(directory):
    """Real probe: create 'Aa' then look for 'aA'."""
    try:
        with tempfile.TemporaryDirectory(dir=directory) as d:
            open(os.path.join(d, "ProbeFile"), "w").close()
            return not os.path.exists(os.path.join(d, "probefile"))
    except OSError:
        return None


def os_label():
    system = platform.system()
    if system == "Darwin":
        return "macOS %s %s" % (platform.mac_ver()[0] or "", platform.machine())
    if system == "Linux":
        try:
            with open("/etc/os-release") as fh:
                kv = dict(l.strip().split("=", 1) for l in fh if "=" in l)
            return "%s %s" % (kv.get("PRETTY_NAME", "Linux").strip('"'), platform.machine())
        except OSError:
            pass
    return "%s %s" % (system, platform.machine())


def facts(repo):
    cs = fs_case_sensitive(repo)
    return {
        "os": os_label(),
        "python": platform.python_version(),
        "tz": os.environ.get("TZ") or time.tzname[0],
        "fs": {True: "case-sensitive", False: "case-insensitive", None: "unknown"}[cs],
        "locale": os.environ.get("LC_ALL") or os.environ.get("LANG") or "unset",
    }


def run_tests(repo):
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tf:
        xml_path = tf.name
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=line", "-p", "no:cacheprovider", "--junitxml", xml_path],
        cwd=repo, capture_output=True, text=True, timeout=300,
    )
    results = {}
    try:
        root = ET.parse(xml_path).getroot()
        cases = {tc.get("name"): tc for tc in root.iter("testcase")}
    except (ET.ParseError, OSError):
        cases = {}
    finally:
        try:
            os.unlink(xml_path)
        except OSError:
            pass
    at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for cid, _title, test in CHECKS:
        tc = cases.get(test)
        if tc is None:
            results[cid] = {"status": "fail", "at": at, "detail": "test not collected (import/collection error)"}
            continue
        bad = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
        if bad is None:
            results[cid] = {"status": "pass", "at": at, "detail": None}
        else:
            msg = (bad.get("message") or bad.text or "").strip().splitlines()
            results[cid] = {"status": "fail", "at": at, "detail": (msg[0] if msg else "failed")[:300]}
    return results, proc.returncode, (proc.stdout + proc.stderr)[-1500:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--env", required=True, choices=["mac", "linux"])
    ap.add_argument("--out")
    ap.add_argument("--text", action="store_true", help="print the verbatim human summary instead of JSON")
    a = ap.parse_args()
    repo = os.path.abspath(a.repo)
    results, rc, tail = run_tests(repo)
    passed = sum(1 for r in results.values() if r["status"] == "pass")
    doc = {
        "schema": 1,
        "env": a.env,
        "ran_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "change": {
            "branch": sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo),
            "head_sha": sh(["git", "rev-parse", "--short", "HEAD"], repo),
        },
        "facts": facts(repo),
        "results": results,
        "summary": {"passed": passed, "failed": len(results) - passed, "total": len(results)},
        "pytest_exit": rc,
        "pytest_tail": tail,
    }
    text = json.dumps(doc, indent=2)
    if a.out:
        with open(a.out, "w") as fh:
            fh.write(text + "\n")
    if a.text:
        f = doc["facts"]
        lines = ["[%s] %s | Python %s | TZ %s | filesystem %s | %s@%s" % (
            a.env, f["os"], f["python"], f["tz"], f["fs"], doc["change"]["branch"], doc["change"]["head_sha"]),
            "result: %d/%d checks pass" % (passed, len(results))]
        titles = {c[0]: c[1] for c in CHECKS}
        for cid, r in results.items():
            lines.append("  %s %-22s %s" % ("PASS" if r["status"] == "pass" else "FAIL", titles[cid], r["detail"] or ""))
        print("\n".join(lines))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
