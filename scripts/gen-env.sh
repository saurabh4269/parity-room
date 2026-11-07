#!/usr/bin/env bash
# Generate stack/.env for the pinned Switch release (0.31.0) with fresh random secrets.
# Refuses to overwrite an existing .env (so it never rotates live secrets).
set -euo pipefail
cd "$(dirname "$0")/../stack"
[ -e .env ] && { echo ".env exists; delete it to regenerate (this wipes nothing, but old DB volumes keep old passwords)."; exit 0; }
command -v openssl >/dev/null || { echo "openssl required" >&2; exit 1; }
cp .env.example .env
fill() { sed -i.bak "s|^$1=.*|$1=$2|" .env; }
for k in DB_PASSWORD DB_OWNER_PASSWORD AGENT_REGISTRATION_TOKEN GATEWAY_ADMIN_PASSWORD MATTERMOST_ADMIN_PASSWORD MATTERMOST_USER_PASSWORD; do fill $k "$(openssl rand -hex 24)"; done
fill SECRET_KEYS "local:$(openssl rand -hex 32)"
fill CONTROLLER_TOKEN_SECRET "$(openssl rand -base64 48 | tr -d '\n/+=' | cut -c1-48)"
fill SWITCH_VERSION 0.31.0
fill FEATURE_FLAGS_ENABLED agent_management
fill GATEWAY_PUBLIC_URL http://localhost:8000
sed -i.bak 's|^# GATEWAY_PUBLIC_URL=|GATEWAY_PUBLIC_URL=|' .env && sed -i.bak "s|^GATEWAY_PUBLIC_URL=.*|GATEWAY_PUBLIC_URL=http://localhost:8000|" .env
fill FRONTEND_BASE_URL http://localhost:8000
rm -f .env.bak
echo "wrote stack/.env  (admin: $(grep '^GATEWAY_ADMIN_EMAIL=' .env | cut -d= -f2-))"
