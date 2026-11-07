# Parity Room: reproduce the whole thing locally.  Needs: Docker (OrbStack/Docker Desktop), Node >= 24 + pnpm >= 10.28,
# uv, git, Claude Code and Codex signed in on this machine.   `make demo` then open http://localhost:8065 (Mattermost).
COMPOSE = docker compose -f stack/standalone-docker-compose.yml --profile collab --profile gateway --project-directory stack
.PHONY: help demo stack machines room policy dashboard evidence reset down clean-secrets
help:
	@echo "make demo       # stack + machines + seeded repo + agents + room (about 5-8 min the first time)"
	@echo "make stack      # Switch 0.31.0 + Mattermost in Docker, demo humans (maya, sam, dave)"
	@echo "make machines   # enroll the Mac and the Linux container as Switch machines"
	@echo "make room       # seed the git repo and create both agents + the room from ONE template"
	@echo "make policy     # lock dev-mac down: only maya, sam and its owner may instruct it"
	@echo "make dashboard  # live Env Matrix on http://localhost:8090"
	@echo "make evidence   # no Switch needed: run the 3 checks on the Mac and in the Linux container, side by side"
	@echo "make reset      # clean slate for another take (keeps server + machines)"
	@echo "make down       # stop everything (keeps volumes)"
demo: stack machines room
	@echo; echo "Open http://localhost:8065 (team 'switch', channel parity-room), then say as maya:"; echo '  @verifier please verify branch feat/weekly-report on your side and tell us what you find.'
stack:
	scripts/fetch-stack.sh
	scripts/gen-env.sh
	$(COMPOSE) up -d
	scripts/wait-ready.sh http://localhost:8000/health/ready 240
	scripts/wait-ready.sh http://localhost:8065/api/v4/system/ping 240
	sleep 20
	python3 scripts/mm_users.py
machines:
	scripts/build-controller.sh || true
	scripts/mac-controller.sh start
	scripts/linux-box.sh up
	sleep 10
room:
	scripts/seed-sut.sh
	python3 scripts/run-template.py
policy:
	python3 scripts/policy.py apply
dashboard:
	python3 observer/server.py --port 8090
evidence:
	scripts/evidence.sh
reset:
	python3 scripts/reset-demo.py && python3 scripts/run-template.py
down:
	scripts/mac-controller.sh stop || true
	scripts/linux-box.sh down || true
	$(COMPOSE) down
clean-secrets:
	-docker volume rm parity-codex-home parity-ctrl-data
	rm -f work/humans.json
