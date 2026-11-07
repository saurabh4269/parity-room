#!/usr/bin/env bash
# Copy the host's Codex login into a Docker VOLUME (never an image layer, never git) for the linux-box container.
# CAUTION: ChatGPT-mode logins use rotating refresh tokens. If Codex refreshes inside the container, the host's copy
# may be invalidated (re-run `codex login` on the host). Check ~/.codex/auth.json `last_refresh` first (refreshes ~8d).
# Alternative with no shared credential: `docker run -it --rm -v parity-codex-home:/home/verifier/.codex parity-verifier:dev codex login --device-auth`.
set -euo pipefail
SRC="${CODEX_AUTH:-$HOME/.codex/auth.json}"
[ -f "$SRC" ] || { echo "no $SRC (run: codex login)"; exit 1; }
docker volume create parity-codex-home >/dev/null
docker run --rm -v parity-codex-home:/h -v "$SRC":/src/auth.json:ro ubuntu:22.04 \
  sh -c 'cp /src/auth.json /h/auth.json && printf "sandbox_mode = \"danger-full-access\"\n" > /h/config.toml && chown -R 1000:1000 /h && chmod 600 /h/auth.json'
echo "seeded volume parity-codex-home (auth.json + config.toml: sandbox_mode=danger-full-access; the container is the sandbox)"
