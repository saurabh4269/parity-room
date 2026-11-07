#!/usr/bin/env bash
# Create the shared bare git remote (work/remote.git) with:
#   main                 healthy baseline
#   feat/weekly-report   the "PR" to verify (works on the author's Mac, breaks on Linux)
# and the Mac agent's working clone (work/dev).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; W="$ROOT/work"
rm -rf "$W/remote.git" "$W/dev"; mkdir -p "$W"
git init -q --bare -b main "$W/remote.git"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
cd "$tmp"
git init -q -b main
git config user.name "Priya (PR author)"; git config user.email "priya@example.com"
cp -R "$ROOT/sut/base/." .
git add -A; git commit -qm "chore: baseline weekly-report package"
git remote add origin "$W/remote.git"; git push -q origin main
git checkout -q -b feat/weekly-report
cp -R "$ROOT/sut/feature/." .
git add -A; git commit -qm "feat: weekly digest report"
git push -q origin feat/weekly-report
git clone -q "$W/remote.git" "$W/dev"
git -C "$W/dev" config user.name "dev (Claude Code)"; git -C "$W/dev" config user.email "dev@parity-room.local"
echo "seeded: $W/remote.git (main, feat/weekly-report) and Mac clone $W/dev"
