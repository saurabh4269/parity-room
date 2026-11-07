#!/usr/bin/env bash
# The second environment ("linux-box"): Ubuntu 22.04 · Python 3.10 · TZ=UTC · case-sensitive FS · Codex CLI.
#   scripts/linux-box.sh up|down|logs|shell
# It joins the Switch server's network namespace so the controller can use http://localhost:8000
# (controllers refuse plain http to anything but loopback). Recreate it whenever the `switch` container is recreated.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; NAME=parity-linux-box
case "${1:-up}" in
  up)
    [ -f "$ROOT/verifier/vendor/switch-agent-controller-0.31.0.tgz" ] || "$ROOT/scripts/build-controller.sh"
    docker build -q -t parity-verifier:dev "$ROOT/verifier" >/dev/null
    docker rm -f "$NAME" >/dev/null 2>&1 || true
    docker volume inspect parity-codex-home >/dev/null 2>&1 || echo "WARN: no Codex login in volume parity-codex-home. Run scripts/seed-codex-auth.sh (or: docker run -it --rm -v parity-codex-home:/home/verifier/.codex parity-verifier:dev codex login --device-auth)"
    CODE=""; docker run --rm -v parity-ctrl-data:/d ubuntu:22.04 test -f /d/controller.db 2>/dev/null || CODE="$(python3 "$ROOT/scripts/gw.py" enroll-code)"
    docker run -d --name "$NAME" --network container:stack-switch-1 -e ENROLL_CODE="$CODE" \
      -v parity-codex-home:/home/verifier/.codex -v parity-ctrl-data:/home/verifier/.switch-controller \
      -v "$ROOT/work/remote.git":/remote.git:ro -v "$ROOT/tools":/opt/parity-tools:ro parity-verifier:dev >/dev/null
    echo "linux-box started"; ;;
  down) docker rm -f "$NAME" >/dev/null 2>&1 || true; echo "linux-box removed";;
  logs) docker logs --tail 40 "$NAME";;
  shell) docker exec -it "$NAME" bash;;
esac
