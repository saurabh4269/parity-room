/* Parity Room site. No framework, no build step. Motion exists in exactly two places:
   the hero terminals printing once on load, and things that respond to what you do (seam, toggle, replay). */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fmt = s => { s = Math.max(0, Math.round(s)); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };
  const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  /* ---------- hero: terminals print once ---------- */
  function printTerminals() {
    const pres = $$('.term pre[data-type]');
    if (reduce) { pres.forEach(p => $$('.ln', p).forEach(l => { l.style.visibility = 'visible'; })); return; }
    pres.forEach(pre => {
      const lines = $$('.ln', pre); const cmd = lines[0]; const full = cmd.textContent;
      cmd.textContent = ''; cmd.style.visibility = 'visible'; cmd.classList.add('caret');
      let i = 0;
      const typing = setInterval(() => {
        cmd.textContent = full.slice(0, ++i);
        if (i >= full.length) {
          clearInterval(typing); cmd.classList.remove('caret');
          lines.slice(1).forEach((l, k) => setTimeout(() => { l.style.visibility = 'visible'; }, 150 * (k + 1)));
        }
      }, 46);
    });
  }

  /* ---------- hero: the draggable seam ---------- */
  function seamControl() {
    const hero = $('.hero'), seam = $('.seam'), tip = $('.seam__tip');
    let drag = false, v = 50;
    const set = x => {
      v = Math.min(62, Math.max(40, x)); hero.style.setProperty('--seam', v + '%');
      seam.setAttribute('aria-valuenow', Math.round(v)); seam.setAttribute('aria-valuetext', Math.round(v) + ' percent');
    };
    const hideTip = () => { if (tip) tip.style.display = 'none'; };
    seam.addEventListener('pointerdown', e => { drag = true; seam.setPointerCapture(e.pointerId); hideTip(); });
    seam.addEventListener('pointermove', e => { if (!drag) return; const r = hero.getBoundingClientRect(); set(((e.clientX - r.left) / r.width) * 100); });
    const end = () => { drag = false; };
    seam.addEventListener('pointerup', end); seam.addEventListener('pointercancel', end);
    seam.addEventListener('dblclick', () => set(50));
    seam.addEventListener('keydown', e => {
      const k = { ArrowLeft: -2, ArrowDown: -2, ArrowRight: 2, ArrowUp: 2 }[e.key];
      if (k) { e.preventDefault(); hideTip(); set(v + k); }
      else if (e.key === 'Home') { e.preventDefault(); set(40); } else if (e.key === 'End') { e.preventDefault(); set(62); }
    });
  }

  /* ---------- three bugs: choose a machine ---------- */
  const BUGS = {
    case: {
      mac: { ok: 1, text: 'macOS ignores letter case by default, so the file opens.' },
      linux: { ok: 0, text: 'Linux keeps letter case: Settings.json and settings.json are different files.', err: "FileNotFoundError: [Errno 2] No such file or directory: 'config/Settings.json'" },
    },
    api: {
      mac: { ok: 1, text: 'Python 3.15.2 has datetime.UTC.' },
      linux: { ok: 0, text: 'Python 3.10.12 predates it.', err: "AttributeError: module 'datetime' has no attribute 'UTC'" },
    },
    tz: {
      mac: { ok: 1, text: 'The Mac runs in Asia/Kolkata, so two events fall on Nov 2: {2024-11-01: 2, 2024-11-02: 2}.' },
      linux: { ok: 0, text: 'In UTC all four events fall on Nov 1.', err: "AssertionError: assert {'2024-11-01': 4} == {'2024-11-01': 2, '2024-11-02': 2}" },
    },
  };
  function bugToggle() {
    const btns = $$('.seg [data-m]'), rows = $$('#bugtbl [data-row]');
    const live = document.createElement('div'); live.className = 'vh'; live.setAttribute('role', 'status'); $('#bugtbl').after(live);
    const draw = m => {
      btns.forEach(b => b.setAttribute('aria-checked', String(b.dataset.m === m)));
      let fails = 0;
      rows.forEach(r => {
        const x = BUGS[r.dataset.row][m]; if (!x.ok) fails++;
        r.querySelector('[data-cell]').innerHTML = `<div class="res"><span class="chip ${x.ok ? 'chip--pass' : 'chip--fail'}">${x.ok ? 'Pass' : 'Fail'}</span><div><p style="margin:0">${esc(x.text)}</p>${x.err ? `<p class="err" style="margin-top:.5rem">${esc(x.err)}</p>` : ''}</div></div>`;
      });
      live.textContent = (m === 'mac' ? 'On the Mac' : 'On Linux') + ': ' + (fails ? fails + ' of 3 fail' : 'all three pass');
    };
    btns.forEach(b => b.addEventListener('click', () => draw(b.dataset.m)));
    btns.forEach((b, i) => b.addEventListener('keydown', e => { if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.preventDefault(); const n = btns[(i + 1) % btns.length]; n.focus(); draw(n.dataset.m); } }));
    draw('linux');
  }

  /* ---------- the replay ---------- */
  const PEOPLE = {
    'dev-mac': { agent: 1, sub: 'Claude Code on the Mac' }, 'qa-linux': { agent: 1, sub: 'Codex on Linux' },
    maya: { sub: 'PM' }, sam: { sub: 'QA lead' }, dave: { sub: 'intern' },
  };
  const CHECKS = ['settings', 'stamp', 'buckets'];
  const STATUS = { pending: 'Pending', failing: 'Failing', running: 'Running', verified: 'Verified' };
  const CELL = { pass: 'Pass', fail: 'Fail', running: 'Running', pending: 'Pending' };

  function fmtText(s) {
    let h = esc(s).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    h = h.replace(/(^|[\s(])(@[A-Za-z][\w.-]*)/g, '$1<span class="mention">$2</span>');
    return h.replace(/\n- /g, '<br>&bull; ').replace(/\n/g, '<br>');
  }
  const strip = s => s.replace(/^[\u{1F3AD}\u{1F4C4}]\s*/u, '').replace(/[\u{1F3AD}\u{1F4C4}]\s*/gu, '');

  async function replay() {
    const root = $('#replay'); if (!root) return;
    let D; try { D = await (await fetch('data/replay.json')).json(); } catch (e) { $('#chat').textContent = 'The replay data could not be loaded. The transcript is in docs/demo-transcript.md in the repository.'; return; }
    const ev = D.events, dur = Math.ceil(D.meta.duration_s) + 2, chat = $('#chat');
    $('#r-room').textContent = D.meta.room; $('#r-meta').textContent = 'Run: ' + D.meta.run + '. Commits ' + D.meta.sha_before + ' to ' + D.meta.sha_after + '. Real time ' + fmt(D.meta.duration_s) + '; replay speed is yours to choose.';
    const scrub = $('#x-scrub'); scrub.max = dur;
    const S = { t: 0, playing: false, speed: 4, shown: 0, last: 0, raf: 0, touched: false, stick: true };

    // chapters + ticks
    const chap = D.chapters; const kind = l => /failure/i.test(l) ? 'fail' : /fixes|push/i.test(l) ? 'run' : /re-verif|approve|merged/i.test(l) ? 'pass' : '';
    $('#ticks').innerHTML = chap.map(c => `<i class="tick" data-k="${kind(c.label)}" style="left:${(c.t / dur) * 100}%"></i>`).join('');
    $('#chapters').innerHTML = chap.map((c, i) => `<button type="button" data-ch="${i}">${esc(c.label)}</button>`).join('');
    $$('#chapters button').forEach(b => b.addEventListener('click', () => { S.touched = true; seek(chap[+b.dataset.ch].t); pause(); }));

    // static transcript
    $('#tx-list').innerHTML = ev.map(e => `<li><strong>${fmt(e.t)} ${esc(e.who)}</strong> ${fmtText(strip(e.text))}</li>`).join('');

    const who = n => PEOPLE[n] || { sub: '' };
    function node(e) {
      const d = document.createElement('div');
      if (e.doc) { d.className = 'sys'; d.innerHTML = `<span><b>${esc(e.who)}</b> ${e.doc[0] === 'created' ? 'created' : 'updated'} the room document <code>${esc(e.doc[1])}</code></span><span class="msg__t">${fmt(e.t)}</span>`; return d; }
      if (e.role) { d.className = 'sys'; d.innerHTML = `<span><b>${esc(e.who)}</b> took the <code>${esc(e.role)}</code> role</span><span class="msg__t">${fmt(e.t)}</span>`; return d; }
      if (e.kind === 'system') { d.className = 'sys'; d.innerHTML = `<span><b>Switch</b>${e.via ? ` <i class="via">(posted as ${esc(e.via)})</i>` : ''} ${fmtText(strip(e.text))}</span><span class="msg__t">${fmt(e.t)}</span>`; return d; }
      const p = who(e.who);
      d.className = 'msg';
      d.innerHTML = `<span class="av ${p.agent ? 'av--agent' : 'av--human'}" aria-hidden="true">${esc(e.who[0].toUpperCase())}</span>` +
        `<div class="msg__who"><span>${esc(e.who)}</span><span class="msg__sub">${esc(p.sub)}</span><span class="msg__t">${fmt(e.t)}</span></div>` +
        `<div class="msg__body">${fmtText(strip(e.text))}</div>`;
      return d;
    }
    function drawChat(t) {
      const n = ev.filter(e => e.t <= t + 0.05).length;
      if (n < S.shown) { chat.textContent = ''; S.shown = 0; }
      for (; S.shown < n; S.shown++) chat.appendChild(node(ev[S.shown]));
      if (S.stick) chat.scrollTop = chat.scrollHeight;
    }
    chat.addEventListener('scroll', () => { S.stick = chat.scrollTop + chat.clientHeight >= chat.scrollHeight - 24; });

    const st = t => { let s = D.states[0]; for (const x of D.states) if (x.t <= t + 0.05) s = x; return s; };
    function drawSide(t) {
      const s = st(t);
      const sEl = $('#r-status'); sEl.textContent = STATUS[s.status]; sEl.className = 'st-' + s.status; $('#r-sha').textContent = s.sha ? 'commit ' + s.sha : '';
      const row = (k, label, sub) => `<tr><th scope="row">${label}<small>${sub}</small></th>` + CHECKS.map(c => { const q = s[k].cells[c].status; return `<td><span class="cell cell--${q}">${CELL[q]}</span></td>`; }).join('') + '</tr>';
      const f = k => s[k].facts ? `Python ${s[k].facts.python}, TZ ${s[k].facts.tz}, ${s[k].facts.fs}` : 'no evidence yet';
      $('#mx').innerHTML = row('mac', 'Mac', f('mac')) + row('linux', 'Linux', f('linux'));
      const taken = {}; ev.filter(e => e.role && e.t <= t + 0.05).forEach(e => { taken[e.role] = e.who; });
      $('#roles').innerHTML = [['implementer', 'exclusive'], ['verifier', 'shared']].map(([r, m]) => `<span class="badge" data-on="${taken[r] ? 1 : 0}"><b>${r}</b> (${m}) ${taken[r] ? 'held by ' + taken[r] : 'not taken yet'}</span>`).join('');
      const made = {}; ev.filter(e => e.doc && e.t <= t + 0.05).forEach(e => { made[e.doc[1]] = e.who; });
      const docs = [['conventions', 'written by maya, read-only for agents', true], ['matrix-mac', 'evidence from dev-mac', made['matrix-mac']], ['matrix-linux', 'evidence from qa-linux', made['matrix-linux']], ['repro-log', 'diagnosis from qa-linux', made['repro-log']]];
      $('#docs').innerHTML = docs.map(([n, d, on]) => `<li data-on="${on ? 1 : 0}"><code>${n}</code><span>${on ? d : 'not written yet'}</span></li>`).join('');
    }
    function drawBar(t) {
      scrub.value = t; scrub.style.setProperty('--p', (t / dur) * 100 + '%'); scrub.setAttribute('aria-valuetext', fmt(t) + ' of ' + fmt(dur));
      $('#x-clock').textContent = fmt(t) + ' / ' + fmt(dur);
      let cur = 0; chap.forEach((c, i) => { if (c.t <= t + 0.05) cur = i; });
      $$('#chapters button').forEach((b, i) => b.toggleAttribute('aria-current', i === cur));
      $('#x-play').textContent = S.playing ? 'Pause' : (t >= dur - 0.2 ? 'Replay' : 'Play');
    }
    function render() { drawChat(S.t); drawSide(S.t); drawBar(S.t); }
    function seek(t) { S.t = Math.min(dur, Math.max(0, t)); S.stick = true; render(); }
    function tick(now) {
      if (!S.playing) return;
      S.t = Math.min(dur, S.t + ((now - S.last) / 1000) * S.speed); S.last = now; render();
      if (S.t >= dur) { pause(); return; }
      S.raf = requestAnimationFrame(tick);
    }
    function play() { if (S.t >= dur - 0.2) S.t = 0; S.playing = true; S.last = performance.now(); cancelAnimationFrame(S.raf); S.raf = requestAnimationFrame(tick); drawBar(S.t); }
    function pause() { S.playing = false; cancelAnimationFrame(S.raf); drawBar(S.t); }

    $('#x-play').addEventListener('click', () => { S.touched = true; S.playing ? pause() : play(); });
    $$('.speed [data-s]').forEach(b => b.addEventListener('click', () => { S.speed = +b.dataset.s; $$('.speed [data-s]').forEach(x => x.setAttribute('aria-checked', String(x === b))); }));
    scrub.addEventListener('input', () => { S.touched = true; seek(+scrub.value); });
    root.addEventListener('keydown', e => {
      if (e.target.matches('button, input')) { if (e.target === scrub || e.code !== 'Space') { if (!(e.target === scrub && (e.key === 'ArrowLeft' || e.key === 'ArrowRight'))) return; } else return; }
      if (e.code === 'Space') { e.preventDefault(); S.touched = true; S.playing ? pause() : play(); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); seek(S.t + 5); } else if (e.key === 'ArrowLeft') { e.preventDefault(); seek(S.t - 5); }
      else if (e.key === ']' || e.key === '[') { e.preventDefault(); const i = chap.findIndex(c => c.t > S.t + 0.05); const cur = i < 0 ? chap.length : i; const to = e.key === ']' ? chap[Math.min(chap.length - 1, cur)] : chap[Math.max(0, cur - 2)]; seek(to.t); }
    });

    // "Show me" buttons elsewhere on the page jump to a moment and pause there
    $$('[data-seek]').forEach(b => b.addEventListener('click', () => {
      S.touched = true; seek(+b.dataset.seek); pause();
      $('#replay').scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
      chat.focus({ preventScroll: true });
    }));

    // play once, quietly, the first time the replay is mostly in view
    if (!reduce && 'IntersectionObserver' in window) {
      let fired = false;
      new IntersectionObserver((es, io) => es.forEach(x => { if (x.isIntersecting && !fired && !S.touched) { fired = true; io.disconnect(); seek(0); play(); } }), { threshold: 0.6 }).observe(root);
    }
    document.addEventListener('visibilitychange', () => { if (document.hidden && S.playing) pause(); });
    const m = /#t=(\d+(?:\.\d+)?)/.exec(location.hash); if (m) { S.touched = true; seek(+m[1]); }
    else seek(reduce ? D.chapters.find(c => /re-verif/i.test(c.label))?.t ?? dur : 0);
  }

  /* ---------- copy buttons ---------- */
  function copyButtons() {
    $$('.copy').forEach(b => b.addEventListener('click', async () => {
      const txt = $('pre', b.parentElement).innerText.replace(/^# .*\n/gm, '');
      try { await navigator.clipboard.writeText(txt); } catch (e) { const t = document.createElement('textarea'); t.value = txt; document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove(); }
      b.textContent = 'Copied'; setTimeout(() => { b.textContent = 'Copy'; }, 1600);
    }));
  }

  seamControl(); bugToggle(); copyButtons(); printTerminals(); replay();
})();
