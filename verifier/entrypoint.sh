#!/usr/bin/env bash
# linux-box entrypoint: clone the repo onto the container's OWN filesystem (case-sensitive),
# enroll this machine with Switch once, then run the agent controller under a tiny supervisor.
set -uo pipefail
DATA="${SWITCH_CONTROLLER_DATA_DIR:-$HOME/.switch-controller}"
SERVER="${SWITCH_SERVER:-http://localhost:8000}"   # loopback on purpose: controllers refuse plain http elsewhere
NAME="${MACHINE_NAME:-linux-box}"
git config --global --add safe.directory '*'
if [ ! -d "$HOME/sut/.git" ]; then git clone -q /remote.git "$HOME/sut"; fi
git -C "$HOME/sut" config user.name  "qa (Codex, Linux)"
git -C "$HOME/sut" config user.email "qa@parity-room.local"
if [ ! -f "$DATA/controller.db" ]; then
  [ -n "${ENROLL_CODE:-}" ] || { echo "first start needs ENROLL_CODE (one-time, 10 min)"; exit 2; }
  switch-agent-controller enroll --server "$SERVER" --code "$ENROLL_CODE" --name "$NAME" \
    --description "Ubuntu 22.04 container: Python 3.10, TZ=UTC, case-sensitive filesystem" \
    --secret-store file --data-dir "$DATA" || exit $?
fi
# Supervisor rule from the controller docs: restart only on exit codes 1 and 7.
while true; do
  switch-agent-controller run --data-dir "$DATA"; rc=$?
  case "$rc" in 1|7) echo "[entrypoint] controller exited $rc; restarting in 3s"; sleep 3;; *) echo "[entrypoint] controller exited $rc"; exit "$rc";; esac
done
