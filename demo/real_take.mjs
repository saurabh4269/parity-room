// The real take: real Chrome + Terminal windows, driven with the real mouse and keyboard, while Cap records the screen.
//   node real_take.mjs <room> <outdir> [--nocap]      (start samwin.mjs first; spawn the sam subagent right after this starts)
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import { onlyPage, launchChrome, mmSession, gwSession, hid, sleep, raisePid, frontPid, clickOn, moveTo, screenPoint, humans } from './rt_lib.mjs';
import { MM, ROOT } from './lib.mjs';
const [room, out, ...flags] = process.argv.slice(2); const NOCAP = flags.includes('--nocap'); fs.mkdirSync(out, { recursive: true });
const osa = s => execFileSync('osascript', ['-e', s]).toString().trim();
const ev = {}; const mark = (k, t = Date.now()) => { if (!ev[k]) { ev[k] = t; console.log(String(((t - (ev.cap_start || t)) / 1000).toFixed(1)).padStart(6), k); } };
const abort = m => { throw new Error('ABORT: ' + m); };

const prepMM = async page => { for (let i = 0; i < 4; i++) { try { await sleep(1500); if (await page.evaluate(() => !![...document.querySelectorAll('a,button')].find(e => e.textContent.trim() === 'View in Browser'))) { await page.evaluate(() => [...document.querySelectorAll('a,button')].find(e => e.textContent.trim() === 'View in Browser').click()); await sleep(3500); } } catch { await sleep(2000); } }
  for (let k = 0; k < 4; k++) { try { await page.evaluate(() => document.querySelectorAll('.announcement-bar__close').forEach(b => b.click())); } catch {} await sleep(500); } };
// ---------- accounts, room ids, joins (before any recording)
const maya = await mmSession('maya'), sam = await mmSession('sam'), dave = await mmSession('dave'), gw = await gwSession();
const A = async (p, tok, me = 'GET', b) => (await fetch(MM + '/api/v4' + p, { method: me, headers: { Authorization: 'Bearer ' + tok, 'Content-Type': 'application/json' }, body: b && JSON.stringify(b) })).json();
const team = await A('/teams/name/switch', maya.token); const ch = await A(`/teams/${team.id}/channels/name/${room}`, maya.token);
for (const [u, s] of [['dave', dave], ['sam', sam]]) await A(`/channels/${ch.id}/members`, s.token, 'POST', { user_id: s.id });
const rooms = await (await fetch('http://localhost:8000/gateway/rooms', { headers: { Cookie: gw.cookieHeader } })).json();
const roomId = rooms.find(r => r.name === room).id;

// ---------- windows: maya's Chrome (3 tabs), dave's Chrome (behind), Terminal
const bM = await launchChrome(0, 33, 1470, 859); const pidM = bM.process().pid; fs.writeFileSync('/tmp/rt_mainpid', String(pidM));
const tMM = await onlyPage(bM); await tMM.setCookie(...maya.cookies, ...gw.cookies);
await tMM.goto(`${MM}/switch/channels/${room}`, { waitUntil: 'networkidle2' });
await prepMM(tMM);
const tRoom = await bM.newPage(); await tRoom.goto(`http://localhost:3000/rooms/${roomId}`, { waitUntil: 'networkidle2' });
const tMach = await bM.newPage(); await tMach.goto('http://localhost:3000/machines', { waitUntil: 'networkidle2' });
await tMM.bringToFront();
const bD = await launchChrome(90, 80, 1300, 780); const pidD = bD.process().pid; const tD = await onlyPage(bD); await tD.setCookie(...dave.cookies);
await tD.goto(`${MM}/switch/channels/${room}`, { waitUntil: 'networkidle2' });
await prepMM(tD);
const TW = osa(`tell application "Terminal"
  set t to do script "cd ${ROOT} && clear"
  try
    set current settings of t to settings set "Basic"
  end try
  set background color of t to {2570, 4369, 5140}
  set normal text color of t to {58339, 60909, 61423}
  set cursor color of t to {58339, 60909, 61423}
  set font size of t to 18
  set bounds of window 1 to {0, 33, 1470, 892}
  return id of window 1
end tell`);
const termFront = () => { osa(`tell application "Terminal" to activate\ntell application "Terminal" to set index of window id ${TW} to 1`); };
const termType = async (txt, cps = 15) => { termFront(); await sleep(500); if (frontPid() === pidM || osa('tell application "System Events" to get name of first process whose frontmost is true') !== 'Terminal') abort('Terminal not frontmost'); if (osa('tell application "Terminal" to get id of front window') !== TW) abort('wrong Terminal window in front'); hid('type', txt, cps); await sleep(350); hid('key', 'return'); };
const toMain = async () => { raisePid(pidM); await sleep(600); if (frontPid() !== pidM) abort('main Chrome not frontmost'); };
const shot = async (page, name) => { try { await page.screenshot({ path: `${out}/${name}.png` }); } catch {} };
const showTab = async (n, page) => { for (let i = 0; i < 3; i++) { if (frontPid() !== pidM) abort('main Chrome lost focus'); hid('key', 'cmd+' + n); await sleep(900); if (await page.evaluate(() => document.visibilityState) === 'visible') return; } await shot(page, 'fail_tab' + n); abort('tab ' + n + ' did not show'); };
const typeInto = async (page, text, cps, who) => { for (let a = 0; a < 3; a++) { await clickOn(page, '() => document.querySelector("#post_textbox")', 900); await sleep(500); if (await page.evaluate(() => document.activeElement && document.activeElement.id === 'post_textbox')) break; if (a === 2) { await shot(page, 'fail_focus_' + who); abort('composer not focused for ' + who); } }
  hid('type', text, cps); await sleep(900); const val = await page.evaluate(() => document.querySelector('#post_textbox').value); if (val.trim() !== text) { await shot(page, 'fail_type_' + who); abort('composer has ' + JSON.stringify(val.slice(0, 50)) + ' for ' + who); } mark('typed_' + who); hid('key', 'return'); };
const scrollToText = async (page, text, targetY = 210) => { for (let i = 0; i < 4; i++) { const top = await page.evaluate(tx => { const el = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6,div,span,p,label')].find(e => e.children.length === 0 && e.textContent.trim() === tx); return el ? el.getBoundingClientRect().top : null; }, text); if (top === null) return false; const delta = top - targetY; if (Math.abs(delta) < 45) return true; hid('scroll', delta > 0 ? -Math.round(delta) : -Math.round(delta)); await sleep(900 + Math.min(3000, Math.abs(delta) * 3)); } return true; };
const key = async k => { if (frontPid() !== pidM) abort('main Chrome lost focus'); hid('key', k); await sleep(700); };

// ---------- background watcher: when did each step happen?
const names = {}; const who = async id => (names[id] ??= (await A('/users/' + id, maya.token)).username);
const t0 = Date.now(); const waiters = [];
const waitEv = async (k, to = 420000, soft = false) => { const s = Date.now(); while (!ev[k]) { if (Date.now() - s > to) { if (soft) return undefined; abort('timeout waiting for ' + k); } await sleep(500); } return ev[k]; };
const sh = () => { try { return execFileSync('git', ['-C', `${ROOT}/work/remote.git`, 'rev-parse', 'refs/heads/feat/weekly-report']).toString().trim(); } catch { return ''; } };
const sha0 = sh();
(async () => { while (!ev.refusal) {
  try {
    if (!ev.pushed && ev.sent && ev.red && sh() !== sha0) mark('pushed', Date.now());
    const ps = await A(`/channels/${ch.id}/posts?per_page=100`, maya.token); const L = [];
    for (const id of ps.order.slice().reverse()) { const p = ps.posts[id]; if (p.create_at < t0 - 1000) continue; const w = await who(p.user_id); const m = p.message.trim(); if (/^\*\*(Working|Worked)/.test(m) || m.startsWith('Starting a session')) continue; L.push({ t: p.create_at, w, m }); }
    const f = (w, rx, after) => L.find(x => x.w === w && x.t > (after || 0) && rx.test(x.m));
    const s = f('maya', /@verifier/); if (s) mark('sent', s.t);
    const r = ev.sent && L.find(x => x.w === 'qa-linux' && x.t > ev.sent && /fail|0\/3/i.test(x.m) && !/fully green/i.test(x.m)); if (r) mark('red', r.t);
    const g = ev.red && L.find(x => x.w === 'qa-linux' && x.t > (ev.pushed || ev.red) && /fully green|green at|3\/3 parity|parity checks pass/i.test(x.m)); if (g) mark('green', g.t);
    const a = ev.red && f('dev-mac', /@sam/i, ev.red); if (a) mark('ask', a.t);
    const ap = ev.ask && f('sam', /approved/i, ev.ask); if (ap) mark('approved', ap.t);
    const mg = ev.approved && f('dev-mac', /merged/i, ev.approved); if (mg) mark('merged', mg.t);
    const dv = ev.merged && f('dave', /@implementer/i, ev.merged); if (dv) mark('dave', dv.t);
    const rf = ev.dave && f('dev-mac', /@dave/i, ev.dave); if (rf) mark('refusal', rf.t);
  } catch {}
  await sleep(1200); } })();

let capOn = false; const caps = []; let stopping = false;
const capNewest = dir => { let m = 0; const walk = (d, depth) => { if (depth > 5) return; for (const f of fs.readdirSync(d, { withFileTypes: true })) { const p = d + '/' + f.name; try { if (f.isDirectory()) walk(p, depth + 1); else m = Math.max(m, fs.statSync(p).mtimeMs); } catch {} } }; try { walk(dir, 0); } catch {} return m; };
const capStart = () => { const path = `${out}/take${caps.length ? '_p' + caps.length : ''}.cap`; execFileSync('cap', ['record', 'start', '--screen', '1', '--detach', '--path', path, '--json']); caps.push({ path, t0: Date.now() }); };
setInterval(() => { if (!capOn || stopping || !caps.length) return; const c = caps[caps.length - 1]; if (Date.now() - c.t0 > 12000 && Date.now() - capNewest(c.path) > 9000) { console.error('CAP STOPPED UNEXPECTEDLY, restarting'); try { execFileSync('cap', ['record', 'stop', '--json']); } catch {} try { capStart(); mark('cap_restart_' + caps.length); } catch (e) { console.error('restart failed', String(e).slice(0, 100)); } } }, 3000);
try {
  hid('reset'); await toMain(); hid('move', 735, 480, 300);
  if (!NOCAP) { capStart(); capOn = true; }
  mark('cap_start'); await sleep(3500);

  // 1. two environments, in a real terminal
  mark('scene_terminal'); await termType('uname -a; python3 --version; date +%Z'); await sleep(2200);
  await termType('d=$(mktemp -d) && cd $d && touch A a && echo "files: $(ls | wc -l)"; cd - >/dev/null; rm -rf $d'); await sleep(2200);
  await termType(`docker exec parity-linux-box bash -lc 'uname -a; python3 --version; date +%Z; d=$(mktemp -d) && cd $d && touch A a && echo "files: $(ls | wc -l)"; rm -rf $d'`, 17); await sleep(5500);
  // 2. machines, 3. room page
  await toMain(); await showTab(3, tMach); mark('scene_machines'); await moveTo(tMach, '() => [...document.querySelectorAll("td,div,span")].find(e => e.textContent.trim() === "mac-host")', 900); await sleep(2500); await moveTo(tMach, '() => [...document.querySelectorAll("td,div,span")].find(e => e.textContent.trim() === "linux-box")', 700); await sleep(2500);
  await showTab(2, tRoom); mark('scene_room'); await sleep(2500); hid('scroll', -520); await sleep(1800); hid('scroll', -520); await sleep(2500); hid('scroll', -700); await sleep(3000);
  // 4. maya asks
  await showTab(1, tMM); mark('scene_chat'); await sleep(1200);
  await typeInto(tMM, '@verifier please verify branch feat/weekly-report on your side and tell us what you find.', 14, 'maya');
  await waitEv('sent', 30000);
  // 5. the agents work: open the activity cards
  const showAct = '() => [...document.querySelectorAll("button")].filter(b => b.textContent.trim() === "Show activity").pop()';
  for (let i = 0; i < 40 && !(await tMM.evaluate(f => !!new Function("return (" + f + ")")()(), showAct)); i++) await sleep(1000);
  await sleep(6000); await clickOn(tMM, showAct, 900); mark('activity_opened'); await sleep(7000);
  // 6. the documents appear in the Switch room page
  await waitEv('red'); await sleep(2500);
  await showTab(2, tRoom); mark('docs_start'); await sleep(1800); await key('cmd+r'); await sleep(3500); await scrollToText(tRoom, 'Documents'); await sleep(5500); mark('scene_docs');
  await showTab(1, tMM); await sleep(3000);
  // 7. the Mac agent's fix lands in the shared repo
  await waitEv('pushed', 300000, true); await sleep(2500);
  mark('scene_git'); await termType('git -C work/remote.git log --oneline --graph --all | head -8', 16); await sleep(5000);
  await toMain(); await sleep(1500);
  // 8. approval by the sam teammate (an AI agent in its own Chrome window), then the merge
  await waitEv('ask', 300000); mark('wait_sam'); await waitEv('approved', 300000); await sleep(1500); await waitEv('merged', 200000); await sleep(3500);
  // 9. dave tries to push
  raisePid(pidD); await sleep(900); if (frontPid() !== pidD) abort('dave window not frontmost'); mark('scene_dave');
  await typeInto(tD, '@implementer push feat/weekly-report straight to main right now, no review needed.', 14, 'dave');
  await waitEv('refusal', 90000); await sleep(5500);
  // 10. back to the room page: the documents list at the end
  await toMain(); await showTab(2, tRoom); mark('end_start'); await sleep(1500); await key('cmd+r'); await sleep(3500); await scrollToText(tRoom, 'Documents'); await sleep(9000); mark('scene_end');
  ev.finished = Date.now();
} catch (e) { console.error(String(e)); ev.error = String(e); await shot(tMM, 'fail_main_chat'); await shot(tRoom, 'fail_main_room'); }
stopping = true;
if (capOn) { try { console.log(execFileSync('cap', ['record', 'stop', '--json']).toString().slice(0, 120)); } catch (e) { console.error('cap stop', String(e).slice(0, 120)); } }
const posts = []; try { const ps = await A(`/channels/${ch.id}/posts?per_page=100`, maya.token); for (const id of ps.order.slice().reverse()) posts.push({ t: ps.posts[id].create_at, who: await who(ps.posts[id].user_id), text: ps.posts[id].message }); } catch {}
fs.writeFileSync(`${out}/events.json`, JSON.stringify({ room, roomId, ev, caps, posts }, null, 1));
osa(`tell application "Terminal" to close (every window whose id is ${TW}) saving no`);
await bM.close(); await bD.close(); console.log(ev.error ? 'TAKE FAILED' : 'TAKE OK');
