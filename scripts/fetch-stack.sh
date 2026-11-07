#!/usr/bin/env bash
# Fetch Switch's standalone compose + env template at the PINNED release tag (not vendored in this repo).
set -euo pipefail
cd "$(dirname "$0")/../stack" 2>/dev/null || { mkdir -p "$(dirname "$0")/../stack"; cd "$(dirname "$0")/../stack"; }
TAG="${SWITCH_TAG:-switch-v0.31.0}"
for f in deploy/local/standalone-docker-compose.yml .env.example; do
  curl -fsSL "https://raw.githubusercontent.com/sandbox-quantum/switch/$TAG/$f" -o "$(basename "$f")"
done
echo "fetched compose + .env.example @ $TAG into stack/"
