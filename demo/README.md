# How the demo film was recorded

Film: https://vimeo.com/1244695983 (2:35). You do not need anything in this folder to replicate the demo: follow [`docs/replicate.md`](../docs/replicate.md) by hand. This folder shows exactly how the film was made, so you can check it and re-record it.

## What these scripts do
- **`real_take.mjs`** is the scene script. It opens a real Google Chrome window (tab strip, address bar) and a real Terminal window, and drives them with the **real mouse and keyboard** while Cap records the screen. Nothing is restyled and no page is faked. It waits for real events (a Mattermost post, a new commit on the shared remote) and cuts the film from those times, not from a clock.
- **`hid.swift`** posts operating-system mouse and keyboard events, so the cursor in the film is the real cursor and the typing is real keystrokes.
- **`samwin.mjs`** and **`SAM_BRIEF.md`**: `sam` is a second AI agent (a Claude subagent). It has its own Chrome window signed in as sam, and a tiny local controller on `127.0.0.1:9334` that can only read and write this one channel. It decides to approve from what it reads in the room.
- **`rt_lib.mjs`**, **`lib.mjs`**: helpers (sessions from an API login, so no password is typed; window and pointer helpers).
- **`gateway_shots.mjs`**: takes screenshots of Switch's own Gateway pages (used for the README and the project page).
- **`narration.json`**, **`narration.srt`**: the narration text and the subtitles. The voice, the music and the sound effects are AI-generated with ElevenLabs.

Who types what, as the film says: Claude Code typed `maya` and `dave` through this Mac's real mouse and keyboard. `sam` is the second AI agent. There is no human teammate in the recording. The Linux machine is a container, and the bugs are seeded.

## Re-record it
**Warning:** the take drives your mouse and keyboard for about six minutes. Do not touch the Mac while it runs. Synthetic key events inherit the real modifier state, so a held key corrupts the typing.

You need macOS with a 1470x956 screen (the window sizes assume it), Google Chrome, Node 24 or newer, `swiftc`, the [Cap](https://cap.so) CLI, and Accessibility permission for the terminal app that starts node.

```bash
cd demo && npm install
mkdir -p /tmp/hid && swiftc -O hid.swift -o /tmp/hid/hid       # the driver the scripts expect at /tmp/hid/hid
# in the repo root: make demo   (or make reset), then make policy
node samwin.mjs <room> 700 60 1000 780 &                       # the sam window and its local controller
node real_take.mjs <room> out/ --nocap                         # rehearsal, no recording
node real_take.mjs <room> out/                                 # the take, recorded with Cap
```
Right after the take starts, start the `sam` agent with the brief in `SAM_BRIEF.md` (change the room name in it). Edit the film from `out/events.json` and the Cap project; the edit itself (Cap zoom and styling, ffmpeg captions and sound) is not part of this repo.

## Honest status
- These are the scripts as they ran for the recorded take, on the author's Mac only. The one change since: `lib.mjs` found the repo with a hard-coded path on the author's disk, and now computes it from the file's location. The scripts were **not re-run end to end after being copied here**, because a run takes over the screen.
- macOS only. Terminal.app only. One screen size.
- The first takes of this film failed for reasons that are now handled in the scripts (a stuck modifier key, a stray new tab, a translucent Terminal, a stale recording being stopped). The scripts abort and save a screenshot instead of typing into the wrong window.
