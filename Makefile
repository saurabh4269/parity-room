# Parity Room: reproduce the whole thing locally.  Needs: Docker (OrbStack/Docker Desktop), Node >= 24 + pnpm >= 10.28,
# uv, git, Claude Code and Codex signed in on this machine.   `make demo` then open http://localhost:8065 (Mattermost).
COMPOSE = docker compose -f stack/standalone-docker-compose.yml -f stack-overrides/mattermost.yml --profile collab --profile gateway --project-directory stack

.PHONY: up help demo stack machines codex-auth room policy evidence reset down clean-secrets
help:
	@echo "make demo       # stack + machines + seeded repo + agents + room (about 1-2 min with cached images, 5-8 min the first time)"
	@echo "make up         # (re)start the server and both machines, e.g. after a reboot; does not touch the room"
	@echo "make stack      # Switch 0.31.0 + Mattermost in Docker, demo humans (maya, sam, dave)"
	@echo "make codex-auth  # (once) copy your Codex login into a Docker volume for the Linux box; see README before running"
	@echo "make machines   # enroll the Mac and the Linux container as Switch machines"
	@echo "make room       # seed the git repo and create both agents + the room from ONE template"
	@echo "make policy     # lock dev-mac down: only maya, sam and its owner may instruct it"
	@echo "make evidence   # no Switch needed: run the 3 checks on the Mac and in the Linux container, side by side"
	@echo "make reset      # clean slate for another take: fresh room, clean repo, access policy re-applied (keeps server + machines)"
	@echo "make down       # stop everything (keeps volumes)"
up: stack machines   ## (re)start the server and both machines; safe to repeat; does not touch the room
demo: stack machines room
	@echo; echo "Switch's own UI:  Gateway http://localhost:3000 (machines, agents, rooms)   Chat http://localhost:8065 (team 'switch', channel parity-room)"; echo "Sign in as maya (password in work/humans.json) and say:"; echo '  @verifier please verify branch feat/weekly-report on your side and tell us what you find.'; echo "Step by step, with what to look at in each UI: docs/replicate.md"
stack:
	scripts/fetch-stack.sh
	scripts/gen-env.sh
	$(COMPOSE) up -d
	scripts/wait-ready.sh http://localhost:8000/health/ready 240
	scripts/wait-ready.sh http://localhost:8065/api/v4/system/ping 240
	sleep 20
	python3 scripts/mm_users.py
codex-auth:
	scripts/seed-codex-auth.sh
machines:
	@docker volume inspect parity-codex-home >/dev/null 2>&1 || { echo; echo 'No Codex login for the Linux box yet. Run `make codex-auth` (copies ~/.codex/auth.json into a Docker volume; read the caveat in scripts/seed-codex-auth.sh) or log in inside the container with: docker run -it --rm -v parity-codex-home:/home/verifier/.codex parity-verifier:dev codex login --device-auth'; echo; exit 1; }
	@test -f verifier/vendor/switch-agent-controller-0.31.0.tgz || scripts/build-controller.sh
	scripts/mac-controller.sh start
	scripts/linux-box.sh up
	sleep 10
room:
	scripts/seed-sut.sh
	python3 scripts/run-template.py
policy:
	python3 scripts/policy.py apply
evidence:
	scripts/evidence.sh
reset:
	python3 scripts/reset-demo.py && python3 scripts/run-template.py
	-python3 scripts/policy.py apply
down:
	scripts/mac-controller.sh stop || true
	scripts/linux-box.sh down || true
	$(COMPOSE) down
clean-secrets:
	-docker volume rm parity-codex-home parity-ctrl-data
	rm -f work/humans.json
