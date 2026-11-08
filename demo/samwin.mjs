// "sam" teammate window: a normal Chrome window (own profile) signed in as sam, plus a tiny local control server (127.0.0.1:9334).
//   GET  /read?n=10   -> the last n messages in the room (author, time, text), via Mattermost's API as sam
//   POST /type        -> body {"text": "..."}: types the message into the real composer with human-like timing and presses Enter
//   POST /raise       -> brings the window to the front
// It can only read and write in this one channel. It never logs in with a typed password: the session cookie comes from the API login of the demo account.
import fs from 'node:fs';
import http from 'node:http';
import { execFileSync } from 'node:child_process';
import puppeteer from 'puppeteer-core';
import { CHROME, ROOT, MM } from './lib.mjs';
const [room, x = '700', y = '60', w = '1000', h = '780'] = process.argv.slice(2);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const humans = JSON.parse(fs.readFileSync(`${ROOT}/work/humans.json`, 'utf8'));
const lr = await fetch(MM + '/api/v4/users/login', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }, body: JSON.stringify({ login_id: 'sam', password: humans.sam.password }) });
const tok = lr.headers.get('token');
const cookies = lr.headers.getSetCookie().map(c => { const [nv] = c.split(';'); const i = nv.indexOf('='); return { name: nv.slice(0, i), value: nv.slice(i + 1), domain: 'localhost', path: '/' }; });
const api = async p => (await fetch(MM + '/api/v4' + p, { headers: { Authorization: 'Bearer ' + tok } })).json();
const team = await api('/teams/name/switch'); const ch = await api(`/teams/${team.id}/channels/name/${room}`);
const names = {}; const who = async id => (names[id] ??= (await api('/users/' + id)).username);
const browser = await puppeteer.launch({ executablePath: CHROME, headless: false, defaultViewport: null, ignoreDefaultArgs: ['--enable-automation'],
  args: [`--window-position=${x},${y}`, `--window-size=${w},${h}`, '--force-color-profile=srgb', '--no-first-run', '--no-default-browser-check', '--disable-infobars', '--deny-permission-prompts', '--disable-notifications'] });
await sleep(1500); const _ps = await browser.pages(); for (const x of _ps.slice(1)) { try { await x.close(); } catch {} } const page = _ps[0]; await page.bringToFront(); await page.setCookie(...cookies);
await page.goto(`${MM}/switch/channels/${room}`, { waitUntil: 'networkidle2' });
if (await page.evaluate(() => !![...document.querySelectorAll('a,button')].find(e => e.textContent.trim() === 'View in Browser'))) { await page.evaluate(() => [...document.querySelectorAll('a,button')].find(e => e.textContent.trim() === 'View in Browser').click()); await sleep(3000); }
await sleep(2000); for (let k = 0; k < 3; k++) { await page.evaluate(() => document.querySelectorAll('.announcement-bar__close').forEach(b => b.click())); await sleep(500); }
const pid = browser.process().pid; fs.writeFileSync('/tmp/samwin.pid', String(pid));
const raise = p => execFileSync('osascript', ['-e', `tell application "System Events" to set frontmost of (first process whose unix id is ${p}) to true`]);
const log = m => fs.appendFileSync('samwin.log', JSON.stringify({ t: Date.now(), ...m }) + '\n');
http.createServer(async (req, res) => {
  const u = new URL(req.url, 'http://x'); const send = (o, c = 200) => { res.writeHead(c, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(o, null, 1)); };
  try {
    if (u.pathname === '/read') {
      const n = +(u.searchParams.get('n') || 10); const ps = await api(`/channels/${ch.id}/posts?per_page=${n + 15}`); const out = [];
      for (const id of ps.order.slice().reverse()) { const p = ps.posts[id]; const m = p.message.trim(); if (/^\*\*(Working|Worked)/.test(m) || m.startsWith('Starting a session')) continue; out.push({ at: new Date(p.create_at).toLocaleTimeString(), from: await who(p.user_id), text: m }); }
      return send(out.slice(-n));
    }
    if (u.pathname === '/raise') { raise(pid); return send({ ok: true }); }
    if (u.pathname === '/type' && req.method === 'POST') {
      let body = ''; for await (const c of req) body += c; const text = String(JSON.parse(body).text || '').slice(0, 400); if (!text) return send({ error: 'empty' }, 400);
      raise(pid); await page.bringToFront(); await sleep(900); const box = await page.$('#post_textbox'); await box.click(); await sleep(400);
      for (const chr of text) { await page.keyboard.type(chr); await sleep(35 + Math.random() * 55); }
      await sleep(700); await page.keyboard.press('Enter'); log({ typed: text }); await sleep(3500); try { raise(+fs.readFileSync('/tmp/rt_mainpid', 'utf8')); } catch {} return send({ ok: true, typed: text });
    }
    send({ error: 'unknown' }, 404);
  } catch (e) { send({ error: String(e) }, 500); }
}).listen(9334, '127.0.0.1', () => console.log('sam window ready, pid', pid));
