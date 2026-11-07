#!/usr/bin/env python3
"""Summarise work/runs.jsonl (written by scripts/e2e.py) as a markdown table for the README."""
import json, os, statistics as st
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src = os.path.join(ROOT, "docs", "measured-runs.jsonl")
rows = [json.loads(l) for l in open(src) if l.strip()]
rows = [r for r in rows if r.get("pass")]
def fmt(s): return f"{int(s)//60}m{int(s)%60:02d}s"
print("| run | room | verifier red | dev fix pushed | verifier green | ready for approval | approval to merge |\n|---|---|---|---|---|---|---|")
for i, r in enumerate(rows, 1):
    print(f"| {i} | {r['room']} | {fmt(r['red_s'])} | {fmt(r['pushed_s'])} | {fmt(r['green_s'])} | **{fmt(r['ask_s'])}** | {int(r['merge_after_approval_s'])}s |")
if len(rows) > 1:
    a = [r["ask_s"] for r in rows]
    print(f"\nn={len(rows)} passing runs: request→ready-for-approval median **{fmt(st.median(a))}**, min {fmt(min(a))}, max {fmt(max(a))}.")
