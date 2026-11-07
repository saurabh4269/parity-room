#!/usr/bin/env bash
# Build/refresh a bare git remote from sut/ : `main` (healthy) + `feat/weekly-report` (the PR with 3 env-dependent bugs).
#   scripts/seed-remote.sh <bare-repo-dir>      (created if missing; refreshed IN PLACE otherwise)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; BARE="${1:?usage: seed-remote.sh <bare-repo-dir>}"
[ -d "$BARE" ] || git init -q --bare -b main "$BARE"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
cd "$tmp"; git init -q -b main
git config user.name "Priya (PR author)"; git config user.email "priya@example.com"
cp -R "$ROOT/sut/base/." .; git add -A; git commit -qm "chore: baseline weekly-report package"
git remote add origin "$BARE"; git push -q --force origin main
git checkout -q -b feat/weekly-report; cp -R "$ROOT/sut/feature/." .; git add -A; git commit -qm "feat: weekly digest report"
git push -q --force origin feat/weekly-report
for b in $(git -C "$BARE" for-each-ref --format='%(refname:short)' refs/heads | grep -vxE 'main|feat/weekly-report'); do git -C "$BARE" branch -D "$b" >/dev/null; done
