import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
export const ROOT = new URL('..', import.meta.url).pathname.replace(/\/$/, '');   // the repo root (this file lives in demo/)
export const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
export const MM = 'http://localhost:8065';
export async function mmLogin(user) {
  const pw = JSON.parse(fs.readFileSync(`${ROOT}/work/humans.json`, 'utf8'))[user].password;
  const r = await fetch(`${MM}/api/v4/users/login`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }, body: JSON.stringify({ login_id: user, password: pw }) });
  if (!r.ok) throw new Error('login failed ' + r.status);
  const cookies = r.headers.getSetCookie().map(c => { const [nv] = c.split(';'); const i = nv.indexOf('='); return { name: nv.slice(0, i), value: nv.slice(i + 1), domain: 'localhost', path: '/' }; });
  return { token: r.headers.get('token'), cookies, user: await r.json() };
}
export async function launch() {
  // sandbox stays ON; fresh temp profile each run
  return puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--hide-scrollbars', '--force-color-profile=srgb', '--disable-features=Translate'], defaultViewport: null });
}
