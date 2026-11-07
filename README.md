# Parity Room

> **Status: work in progress, built during the Flip the Switch hackathon (Nov 4-7, 2026).** The README is being finalised; sections marked _(verified)_ were run end to end.

**"It works on my machine" is a coordination problem.** In Parity Room a **Claude Code agent on a Mac** and a **Codex agent on Linux** share one [Switch](https://github.com/sandbox-quantum/switch) room. The Linux agent finds what the Mac can't see, the Mac agent fixes it using the room's shared context, the Linux agent re-verifies, and a human approves, all in one chat.

## What's verified so far
- One Switch template creates **both agents on two different machines** and the room with its roles and a human-authored `conventions` document _(verified)_.
- The Mac agent (`dev-mac`) and the Linux agent (`qa-linux`) take the `implementer` (exclusive) and `verifier` (shared) roles, hand work to each other **by role**, and write evidence into room documents _(verified)_.
- The seeded bugs are genuinely environment-dependent: **3/3 checks pass on the Mac, 0/3 on the Linux container**, with three distinct error signatures _(verified)_.

## Honest limits
- The "Linux machine" is a **container on the same Mac** (Ubuntu 22.04, Python 3.10, TZ=UTC, case-sensitive filesystem). It is a different *environment*, not different hardware. Swap it for any SSH-able host and nothing else changes.
- The bugs are seeded on purpose, so "3 of 3 caught" is true by construction: this is a demonstration, not a benchmark.
- One of the three bugs also reproduces on the Mac if you set `TZ=UTC`. The point is not that the Mac *cannot* see it; it is who notices, who decides which side is wrong, and where that decision is recorded.

_Full architecture, run instructions, Switch coverage map and demo transcript: coming in the next commits._
