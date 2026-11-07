#!/usr/bin/env bash
# Fetch Switch's standalone compose + env template at the PINNED release tag (not vendored in this repo).
# Uses curl; falls back to `gh api` if raw.githubusercontent.com is unreachable (some networks block it).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; mkdir -p "$ROOT/stack"; cd "$ROOT/stack"
TAG="${SWITCH_TAG:-switch-v0.31.0}"
for f in deploy/local/standalone-docker-compose.yml .env.example; do
  out="$(basename "$f")"
  if ! curl -fsSL --max-time 30 "https://raw.githubusercontent.com/sandbox-quantum/switch/$TAG/$f" -o "$out" 2>/dev/null; then
    command -v gh >/dev/null || { echo "cannot fetch $f (curl failed and gh is not installed)" >&2; exit 1; }
    gh api "repos/sandbox-quantum/switch/contents/$f?ref=$TAG" -H "Accept: application/vnd.github.raw" > "$out"
  fi
  [ -s "$out" ] || { echo "empty download: $f" >&2; exit 1; }
done
echo "fetched compose + .env.example @ $TAG into stack/"
