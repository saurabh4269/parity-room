// Real screenshots of Switch's own Gateway UI (for the README, the blog and the project site)
import fs from 'node:fs';
import { launch } from './lib.mjs';
import { gwSession } from './rt_lib.mjs';
const [rid, outdir] = process.argv.slice(2); fs.mkdirSync(outdir, { recursive: true });
const gw = await gwSession(); const b = await launch(); const c = await b.createBrowserContext(); const p = await c.newPage();
await p.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1.5 }); await p.setCookie(...gw.cookies);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const shot = async (url, name, scrollText) => { await p.goto('http://localhost:3000' + url, { waitUntil: 'networkidle2' }); await sleep(1800);
  if (scrollText) await p.evaluate(t => { const el = [...document.querySelectorAll('h1,h2,h3,h4,h5,div,span,p')].find(e => e.children.length === 0 && e.textContent.trim().startsWith(t)); if (el) el.scrollIntoView({ block: 'start' }); }, scrollText);
  await sleep(900); await p.screenshot({ path: `${outdir}/${name}.png` }); console.log(name); };
await shot('/machines', 'gateway-machines');
await shot('/agents', 'gateway-agents');
await shot('/rooms/' + rid, 'gateway-room-roles');
await shot('/rooms/' + rid, 'gateway-room-documents', 'Room-scoped');
await b.close();
