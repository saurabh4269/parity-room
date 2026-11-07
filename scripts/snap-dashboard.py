#!/usr/bin/env python3
"""Wait until the live dashboard feed reaches <status>, then screenshot it with headless Chrome.
  scripts/snap-dashboard.py failing docs/img/dashboard-failing.png [timeout_s]
Needs `make dashboard` running on :8090 and Google Chrome installed (macOS path below)."""
import json, subprocess, sys, time, urllib.request
status, out = sys.argv[1], sys.argv[2]; timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 600
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
t0 = time.time()
while time.time() - t0 < timeout:
    try: s = json.load(urllib.request.urlopen("http://localhost:8090/api/state", timeout=5))["status"]
    except Exception: s = None
    if s == status: break
    time.sleep(1)
else: sys.exit(f"timeout waiting for status {status}")
time.sleep(1.5)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1440,1250", f"--screenshot={out}", "http://localhost:8090/"], capture_output=True, timeout=60)
print("captured", status, "->", out)
