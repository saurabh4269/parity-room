#!/usr/bin/env bash
# (Re)create the shared bare git remote with:
#   main                 healthy baseline
#   feat/weekly-report   the "PR" to verify (works on the author's Mac, breaks on Linux)
# IN PLACE: the linux-box container bind-mounts work/remote.git, so the directory must never be replaced.
# Also (re)creates the Mac agent's working clone (work/dev) and, if running, the container's clone.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; W="$ROOT/work"
mkdir -p "$W"
[ -d "$W/remote.git" ] || git init -q --bare -b main "$W/remote.git"
"$ROOT/scripts/seed-remote.sh" "$W/remote.git"
# Mac agent's clone
rm -rf "${W:?}/dev"; git clone -q "$W/remote.git" "$W/dev"
git -C "$W/dev" config user.name "dev (Claude Code)"; git -C "$W/dev" config user.email "dev@parity-room.local"
# the Linux container's own clone (on ITS filesystem), if the container is up
if docker ps --format '{{.Names}}' | grep -qx parity-linux-box; then
  docker exec parity-linux-box bash -c 'rm -rf "$HOME/sut" && git clone -q /remote.git "$HOME/sut" && git -C "$HOME/sut" config user.name "qa (Codex, Linux)" && git -C "$HOME/sut" config user.email qa@parity-room.local'
  echo "reset linux-box clone"
fi
echo "seeded: main + feat/weekly-report on work/remote.git; Mac clone work/dev"
