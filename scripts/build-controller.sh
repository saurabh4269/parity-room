#!/usr/bin/env bash
# Build the Switch agent controller FROM SOURCE at the pinned release tag (no unsigned binary download, no install scripts).
# Output: verifier/vendor/switch-agent-controller-0.31.0.tgz   (needs git, node >= 24, pnpm >= 10.28)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; TAG="${CONTROLLER_TAG:-switch-agent-controller-v0.31.0}"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
git clone -q --depth 1 --branch "$TAG" https://github.com/sandbox-quantum/switch.git "$WORK/src"
echo "building $TAG @ $(git -C "$WORK/src" rev-parse --short HEAD)"
cd "$WORK/src/console"
pnpm install --frozen-lockfile --ignore-scripts --filter '@switch-console/agent-controller...' >/dev/null
pnpm -r --filter './packages/**' run build >/dev/null
pnpm --filter @switch-console/agent-controller run package >/dev/null
mkdir -p "$ROOT/verifier/vendor"
cp packages/agent-controller/dist-package/switch-agent-controller-*.tgz "$ROOT/verifier/vendor/switch-agent-controller-0.31.0.tgz"
shasum -a 256 "$ROOT/verifier/vendor/switch-agent-controller-0.31.0.tgz"
