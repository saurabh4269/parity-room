# Playing it with a real second person

The submission asks for "a real chat with your teammates", so use a real person for `sam` (QA lead).

## A. Friend on the same Wi-Fi (simplest)
1. Find your Mac's LAN IP: `ipconfig getifaddr en0`.
2. In `stack/.env` set `SWITCH_BIND_ADDR=0.0.0.0`, then `docker compose -f stack/standalone-docker-compose.yml --profile collab --profile gateway --project-directory stack up -d mattermost switch` and recreate the Linux box (`scripts/linux-box.sh up`, because it joins the switch container's network).
3. Your friend opens `http://<your-ip>:8065`, signs in as `sam` (password in `work/humans.json`), and joins channel `parity-room`.
4. **Turn it back to `127.0.0.1` afterwards.** `0.0.0.0` exposes Mattermost and the Switch API to everyone on that network; the generated passwords are random but this is a throwaway demo stack.

## B. You alone, two browser profiles
Sign in as `maya` in one profile and `sam` in another. It is the same person, so say so (the form's "teammates" wording), or label the lines `[SCRIPTED]` as in `docs/demo-transcript.md`.

## C. Scripted humans (rehearsal only)
`scripts/humans.py maya "@verifier please verify branch feat/weekly-report"` posts through the Mattermost API exactly like a typed message. Never script a human as `admin`: the Switch bridge drops admin posts.
