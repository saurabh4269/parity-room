// Shared helpers for the real take: real OS-level mouse and keyboard (via /tmp/hid/hid) driving real windows.
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import puppeteer from 'puppeteer-core';
import { CHROME, ROOT, MM } from './lib.mjs';
export const sleep = ms => new Promise(r => setTimeout(r, ms));
export const HID = '/tmp/hid/hid';
export const hid = (...a) => execFileSync(HID, a.map(String)).toString().trim();
export const humans = JSON.parse(fs.readFileSync(`${ROOT}/work/humans.json`, 'utf8'));
const env = Object.fromEntries(fs.readFileSync(`${ROOT}/stack/.env`, 'utf8').split('\n').filter(l => l.includes('=') && !l.startsWith('#')).map(l => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1)]));
const cookiesOf = (r, domain = 'localhost') => r.headers.getSetCookie().map(c => { const [nv] = c.split(';'); const i = nv.indexOf('='); return { name: nv.slice(0, i), value: nv.slice(i + 1), domain, path: '/' }; });
export async function mmSession(user) {
  const r = await fetch(MM + '/api/v4/users/login', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }, body: JSON.stringify({ login_id: user, password: humans[user].password }) });
  return { cookies: cookiesOf(r), token: r.headers.get('token'), id: (await r.json()).id };
}
export async function gwSession() {
  const r = await fetch('http://localhost:8000/gateway/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: env.GATEWAY_ADMIN_EMAIL, password: env.GATEWAY_ADMIN_PASSWORD }) });
  return { cookies: cookiesOf(r), cookieHeader: r.headers.getSetCookie().map(c => c.split(';')[0]).join('; ') };
}
export const win = (x, y, w, h) => [`--window-position=${x},${y}`, `--window-size=${w},${h}`];
export const chromeArgs = (x, y, w, h) => [...win(x, y, w, h), '--force-color-profile=srgb', '--no-first-run', '--no-default-browser-check', '--disable-infobars', '--deny-permission-prompts', '--disable-notifications', '--hide-crash-restore-bubble', '--disable-features=Translate'];
export const launchChrome = (x, y, w, h) => puppeteer.launch({ executablePath: CHROME, headless: false, defaultViewport: null, ignoreDefaultArgs: ['--enable-automation'], args: chromeArgs(x, y, w, h) });
export const raisePid = pid => execFileSync('osascript', ['-e', `tell application "System Events" to set frontmost of (first process whose unix id is ${pid}) to true`]);
export const frontPid = () => +execFileSync('osascript', ['-e', 'tell application "System Events" to get unix id of first process whose frontmost is true']).toString().trim();
// screen coordinates of an element in a Chrome page (CSS px == points on macOS)
export async function screenPoint(page, finder) {
  return page.evaluate(f => {
    const el = new Function('return (' + f + ')')()(); if (!el) return null; el.scrollIntoView({ block: 'nearest' });
    const b = el.getBoundingClientRect(); return { x: window.screenX + b.x + b.width / 2, y: window.screenY + (window.outerHeight - window.innerHeight) + b.y + b.height / 2 };
  }, finder);
}
export async function moveTo(page, finder, ms = 800) { const p = await screenPoint(page, finder); if (!p) throw new Error('target not found: ' + finder); hid('move', Math.round(p.x), Math.round(p.y), ms); return p; }
export async function clickOn(page, finder, ms = 800) { const p = await moveTo(page, finder, ms); await sleep(180); hid('click'); return p; }

// Chrome opens an extra New Tab page on startup: keep exactly one tab, and make it the active one
export async function onlyPage(b) { await sleep(1500); const ps = await b.pages(); for (const x of ps.slice(1)) { try { await x.close(); } catch {} } await ps[0].bringToFront(); return ps[0]; }
