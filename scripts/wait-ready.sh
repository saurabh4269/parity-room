#!/usr/bin/env bash
# Wait until a URL answers 200 (default: Switch readiness). usage: wait-ready.sh <url> [seconds]
URL="${1:-http://localhost:8000/health/ready}"; T="${2:-180}"
for i in $(seq 1 "$T"); do [ "$(curl -s -o /dev/null -w '%{http_code}' "$URL")" = 200 ] && { echo "ready: $URL"; exit 0; }; sleep 1; done
echo "timeout waiting for $URL" >&2; exit 1
