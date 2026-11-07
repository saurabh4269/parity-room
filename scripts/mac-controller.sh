#!/usr/bin/env bash
# Run the Switch agent controller for the Mac ("mac-host"): headless, no Switch Console needed.
#   scripts/mac-controller.sh start|stop|status|logs
# The Mac agent's environment is pinned to the author's reality: TZ=Asia/Kolkata (set below).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG="$ROOT/verifier/vendor/switch-agent-controller-0.31.0.tgz"
PREFIX="$ROOT/work/controller-mac"; DATA="$ROOT/work/controller-mac-data"; LOG="$ROOT/work/logs/controller-mac.log"
BIN="$PREFIX/node_modules/.bin/switch-agent-controller"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH" TZ="${PARITY_MAC_TZ:-Asia/Kolkata}"
mkdir -p "$ROOT/work/logs"
case "${1:-status}" in
  start)
    [ -x "$BIN" ] || { echo "installing controller (ignore-scripts) into work/controller-mac"; npm install --prefix "$PREFIX" --ignore-scripts --no-audit --no-fund "$PKG" >/dev/null; }
    if [ ! -f "$DATA/controller.db" ]; then
      CODE="$(python3 "$ROOT/scripts/gw.py" enroll-code)"
      "$BIN" enroll --server http://localhost:8000 --code "$CODE" --name mac-host \
        --description "The author's Mac: macOS arm64, Python 3.15, TZ=$TZ, case-insensitive filesystem" \
        --secret-store file --data-dir "$DATA"
    fi
    nohup "$BIN" run --data-dir "$DATA" >> "$LOG" 2>&1 &
    echo $! > "$ROOT/work/controller-mac.pid"; echo "mac-host controller started (pid $(cat "$ROOT/work/controller-mac.pid")), log: work/logs/controller-mac.log";;
  stop)   [ -f "$ROOT/work/controller-mac.pid" ] && kill "$(cat "$ROOT/work/controller-mac.pid")" 2>/dev/null || true; echo stopped;;
  status) "$BIN" status --data-dir "$DATA";;
  logs)   tail -n 40 "$LOG";;
esac
