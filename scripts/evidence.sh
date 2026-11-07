#!/usr/bin/env bash
# Tier 1 (no Switch needed, never touches the live demo): the same 3 checks on the Mac and in a Linux container, side by side.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
"$ROOT/scripts/seed-remote.sh" "$T/remote.git"
git clone -q "$T/remote.git" "$T/mac" && git -C "$T/mac" checkout -q feat/weekly-report
echo "=== Mac"; (cd "$T/mac" && TZ="${PARITY_MAC_TZ:-Asia/Kolkata}" uv run --quiet --no-project --with pytest python "$ROOT/tools/parity_matrix.py" --repo . --env mac --text)
echo; echo "=== Linux container (Ubuntu 22.04, Python 3.10, UTC)"
if ! docker image inspect parity-verifier:dev >/dev/null 2>&1; then
  docker build -q -t parity-verifier-lite - <<'DF' >/dev/null
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip git ca-certificates && pip3 install --no-cache-dir pytest && rm -rf /var/lib/apt/lists/*
DF
fi
IMG=$(docker image inspect parity-verifier:dev >/dev/null 2>&1 && echo parity-verifier:dev || echo parity-verifier-lite)
docker run --rm -e TZ=UTC -v "$T/remote.git":/remote.git:ro -v "$ROOT/tools":/opt/parity-tools:ro --entrypoint bash "$IMG" -lc 'git config --global --add safe.directory "*" && git clone -q /remote.git /tmp/sut && cd /tmp/sut && git checkout -q feat/weekly-report && python3 /opt/parity-tools/parity_matrix.py --repo . --env linux --text'
