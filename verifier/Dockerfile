# Parity Room "linux-box": a deliberately different environment from the author's Mac.
#   Ubuntu 22.04 · Python 3.10 · TZ=UTC · case-sensitive container filesystem · Codex CLI
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive TZ=UTC LANG=C.UTF-8 LC_ALL=C.UTF-8
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip git curl ca-certificates socat xz-utils procps tini ripgrep \
 && rm -rf /var/lib/apt/lists/*
# Node >= 22.13 is required by the Switch agent controller (node:sqlite).
ARG NODE_VERSION=22.13.1
RUN set -eux; arch="$(dpkg --print-architecture)"; \
    case "$arch" in amd64) n=x64;; arm64) n=arm64;; *) echo "unsupported arch $arch"; exit 1;; esac; \
    curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${n}.tar.xz" | tar -xJ -C /usr/local --strip-components=1; \
    node --version
RUN pip3 install --no-cache-dir pytest && npm install -g @openai/codex && codex --version
# The Switch agent controller, built from source at the pinned release tag (see Makefile: controller-pkg).
# Installed with --ignore-scripts. Not downloaded as an unsigned binary.
COPY vendor/switch-agent-controller-0.31.0.tgz /tmp/controller.tgz
RUN npm install --global --ignore-scripts /tmp/controller.tgz && rm /tmp/controller.tgz \
 && switch-agent-controller --help 2>&1 | head -3
RUN useradd -m -s /bin/bash verifier
COPY --chown=verifier entrypoint.sh /home/verifier/entrypoint.sh
RUN mkdir -p /home/verifier/.switch-controller /home/verifier/.codex && chown -R verifier:verifier /home/verifier
USER verifier
WORKDIR /home/verifier
ENV TZ=UTC
ENV CODEX_HOME=/home/verifier/.codex
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["/home/verifier/entrypoint.sh"]
