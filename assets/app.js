/* Parity Room. No framework, no build step, no third-party request until you press play.
   Four small jobs: the sticky header, the film (Vimeo loads on press), copy buttons, and the current-section marker in the nav. */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* sticky header: a hairline appears once the page scrolls */
  function header() {
    const top = $('.top'); if (!top) return;
    const on = () => top.classList.toggle('is-stuck', scrollY > 8);
    on(); addEventListener('scroll', on, { passive: true });
  }

  /* the film: the poster is a link to Vimeo (works without JS); with JS it becomes an embed at the second you chose */
  function film() {
    const box = $('#film'); if (!box) return;
    const id = box.dataset.vimeo, first = $('.stage__go', box), chapters = $$('#chapters [data-seek]');
    const mark = t => {
      let cur = -1; chapters.forEach((b, i) => { if (+b.dataset.seek <= t + 0.5) cur = i; });
      chapters.forEach((b, i) => b.toggleAttribute('aria-current', i === cur));
    };
    const start = t => {
      box.textContent = '';
      const f = document.createElement('iframe');
      f.src = 'https://player.vimeo.com/video/' + id + '?dnt=1&autoplay=1&title=0&byline=0&portrait=0#t=' + Math.max(0, Math.floor(t)) + 's';
      f.title = 'Parity Room demo film, 2 minutes 35 seconds (Vimeo)';
      f.allow = 'autoplay; fullscreen; picture-in-picture'; f.allowFullscreen = true; f.referrerPolicy = 'strict-origin-when-cross-origin';
      box.appendChild(f); mark(t);
    };
    const show = () => box.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
    first.addEventListener('click', e => { e.preventDefault(); start(0); });
    $$('[data-play]').forEach(b => b.addEventListener('click', e => { e.preventDefault(); start(0); show(); }));
    $$('[data-seek]').forEach(b => b.addEventListener('click', () => { start(+b.dataset.seek); show(); }));
    const m = /#t=(\d+)/.exec(location.hash);              // page#t=98 scrolls to the film and marks the chapter; press play to start it
    if (m) { mark(+m[1]); box.scrollIntoView({ block: 'center' }); }
  }

  /* click a figure to read the zoomed frame from the film */
  function zoom() {
    const links = $$('a[data-zoom]'); if (!links.length || typeof HTMLDialogElement === 'undefined') return;
    let dlg = null, img, cap;
    const build = () => {                                  // created on the first click, so the page holds no empty image
      dlg = document.createElement('dialog'); dlg.className = 'lb'; dlg.setAttribute('aria-label', 'Zoomed frame from the film');
      dlg.innerHTML = '<button type="button" aria-label="Close">Close</button><img alt=""><p></p>';
      document.body.appendChild(dlg); img = $('img', dlg); cap = $('p', dlg);
      $('button', dlg).addEventListener('click', () => dlg.close());
      dlg.addEventListener('click', e => { if (e.target === dlg) dlg.close(); });
    };
    links.forEach(a => a.addEventListener('click', e => {
      e.preventDefault(); if (!dlg) build();
      img.src = a.href; img.alt = $('img', a).alt;
      const fc = $('figcaption', a.closest('figure')); cap.textContent = 'Zoomed frame from the film. ' + (fc ? fc.textContent : '');
      dlg.showModal();
    }));
  }

  /* copy buttons: comment lines are left out of what you copy */
  function copy() {
    $$('.copy').forEach(b => b.addEventListener('click', async () => {
      const txt = $('pre', b.parentElement).innerText.replace(/^# .*\n?/gm, '').trim();
      try { await navigator.clipboard.writeText(txt); } catch (e) { const t = document.createElement('textarea'); t.value = txt; document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove(); }
      b.textContent = 'Copied'; setTimeout(() => { b.textContent = 'Copy'; }, 1600);
    }));
  }

  /* nav: mark the section you are in */
  function spy() {
    const links = $$('.nav a'); if (!links.length || !('IntersectionObserver' in window)) return;
    const map = new Map(links.map(a => [a.getAttribute('href').slice(1), a]));
    const io = new IntersectionObserver(es => es.forEach(x => {
      const a = map.get(x.target.id); if (!a) return;
      if (x.isIntersecting) { links.forEach(l => l.removeAttribute('aria-current')); a.setAttribute('aria-current', 'true'); }
    }), { rootMargin: '-45% 0px -50% 0px' });
    ['film', 'how', 'proof', 'real', 'feedback', 'run'].forEach(id => { const el = document.getElementById(id); if (el) io.observe(el); });
  }

  header(); film(); zoom(); copy(); spy();
})();
