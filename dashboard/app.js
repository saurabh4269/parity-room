/* Parity Room dashboard. Vanilla JS, no build step, no dependencies.
 *
 * Renders the schema-1 state contract (see README.md). Every string that comes
 * from data is inserted with textContent / createTextNode / setAttribute only;
 * innerHTML is never used.
 *
 * Data sources (picked from the query string):
 *   (default)         poll GET /api/state every 1000 ms, keep last state on failure
 *   ?fixture=<name>   load ./fixtures/state-<name>.json once (no polling)
 *   ?play=1           step pending -> failing -> running -> verified every ~4 s
 */
(() => {
  'use strict';

  /* ---------------------------------------------------------------- config */
  const SVGNS = 'http://www.w3.org/2000/svg';
  const RESULT_STATUSES = ['pass', 'fail', 'running', 'pending'];
  const OVERALL_STATUSES = ['pending', 'running', 'failing', 'verified'];
  const FIXTURE_NAMES = ['pending', 'failing', 'running', 'verified'];
  const POLL_MS = 1000;
  const PLAY_MS = 4000;
  const FETCH_TIMEOUT_MS = 2500;
  const API_URL = '/api/state';

  const RESULT_LABEL = { pass: 'PASS', fail: 'FAIL', running: 'RUNNING', pending: 'PENDING' };
  const OVERALL_LABEL = { verified: 'VERIFIED', failing: 'FAILING', running: 'RUNNING', pending: 'PENDING' };
  // overall status -> class + icon
  const OVERALL_VIEW = {
    verified: { cls: 's-verified', icon: 'shield' },
    failing: { cls: 's-failing', icon: 'fail' },
    running: { cls: 's-running', icon: 'running' },
    pending: { cls: 's-pending', icon: 'pending' },
  };
  const FACT_ORDER = ['os', 'python', 'tz', 'fs'];
  const FACT_LABEL = { os: 'OS', python: 'PY', tz: 'TZ', fs: 'FS' };

  const reduceMotion = window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)')
    : { matches: false };

  /* ---------------------------------------------------------------- icons */
  // 24x24 stroke icons. Geometry is constant (never data driven).
  const ICONS = {
    pass: [['circle', { cx: 12, cy: 12, r: 9 }], ['path', { d: 'M8 12.4l2.8 2.8 5.2-5.6' }]],
    fail: [['circle', { cx: 12, cy: 12, r: 9 }], ['path', { d: 'M9 9l6 6M15 9l-6 6' }]],
    running: [['circle', { cx: 12, cy: 12, r: 9, opacity: '.28' }], ['path', { d: 'M12 3a9 9 0 0 1 9 9' }]],
    pending: [
      ['circle', { cx: 12, cy: 12, r: 9, 'stroke-dasharray': '2.6 3.1' }],
      ['path', { d: 'M12 7.6V12l3 1.9' }],
    ],
    shield: [
      ['path', { d: 'M12 3l7.5 3v5.4c0 4.6-3.1 8-7.5 9.6-4.4-1.6-7.5-5-7.5-9.6V6z' }],
      ['path', { d: 'M8.6 12l2.5 2.5 4.4-4.8' }],
    ],
    branch: [
      ['circle', { cx: 6, cy: 5.5, r: 2.4 }],
      ['circle', { cx: 6, cy: 18.5, r: 2.4 }],
      ['circle', { cx: 18, cy: 8, r: 2.4 }],
      ['path', { d: 'M6 7.9v8.2M18 10.4c0 4.2-4.6 4-10.2 6.6' }],
    ],
    commit: [['circle', { cx: 12, cy: 12, r: 3.6 }], ['path', { d: 'M3 12h5.4M15.6 12H21' }]],
    monitor: [['rect', { x: 3, y: 4, width: 18, height: 12, rx: 2 }], ['path', { d: 'M8 20h8M12 16v4' }]],
    server: [
      ['rect', { x: 4, y: 4, width: 16, height: 6.5, rx: 1.6 }],
      ['rect', { x: 4, y: 13.5, width: 16, height: 6.5, rx: 1.6 }],
      ['path', { d: 'M8 7.2h.01M8 16.8h.01' }],
    ],
    user: [['circle', { cx: 12, cy: 8, r: 3.5 }], ['path', { d: 'M5 20c0-3.6 3.1-6 7-6s7 2.4 7 6' }]],
    bot: [
      ['rect', { x: 4, y: 8.5, width: 16, height: 10.5, rx: 2.5 }],
      ['path', { d: 'M12 8.5V5' }],
      ['circle', { cx: 12, cy: 3.8, r: 1.1 }],
      ['path', { d: 'M9 13.3h.01M15 13.3h.01M9.6 16.2h4.8' }],
    ],
    lock: [['rect', { x: 5, y: 11, width: 14, height: 9, rx: 2 }], ['path', { d: 'M8 11V8a4 4 0 0 1 8 0v3' }]],
    users: [
      ['circle', { cx: 9, cy: 8, r: 3 }],
      ['path', { d: 'M3 19c0-3 2.7-5 6-5s6 2 6 5' }],
      ['circle', { cx: 17.2, cy: 9, r: 2.4 }],
      ['path', { d: 'M16.4 14.1c2.9.2 4.6 1.9 4.6 4.7' }],
    ],
    alert: [['path', { d: 'M12 3.6l9.2 16H2.8z' }], ['path', { d: 'M12 10v4.4M12 17.2h.01' }]],
    external: [['path', { d: 'M14 4h6v6M20 4l-8.5 8.5M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5' }]],
    grid: [
      ['rect', { x: 4, y: 4, width: 7, height: 7, rx: 1.4 }],
      ['rect', { x: 13, y: 4, width: 7, height: 7, rx: 1.4 }],
      ['rect', { x: 4, y: 13, width: 7, height: 7, rx: 1.4 }],
      ['rect', { x: 13, y: 13, width: 7, height: 7, rx: 1.4 }],
    ],
    activity: [['path', { d: 'M3 12h4l3-8 4 16 3-8h4' }]],
    hub: [
      ['circle', { cx: 12, cy: 12, r: 2.6 }],
      ['circle', { cx: 5, cy: 6, r: 2 }],
      ['circle', { cx: 19, cy: 6, r: 2 }],
      ['circle', { cx: 12, cy: 20, r: 2 }],
      ['path', { d: 'M6.6 7.4l3.3 3M17.4 7.4l-3.3 3M12 14.6V18' }],
    ],
  };

  function icon(name, size = 16, cls = '') {
    const svg = document.createElementNS(SVGNS, 'svg');
    const attrs = {
      viewBox: '0 0 24 24',
      width: size,
      height: size,
      fill: 'none',
      stroke: 'currentColor',
      'stroke-width': 1.8,
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round',
      'aria-hidden': 'true',
      focusable: 'false',
      class: ('ico ' + cls).trim(),
    };
    for (const k of Object.keys(attrs)) svg.setAttribute(k, attrs[k]);
    for (const [tag, a] of ICONS[name] || []) {
      const node = document.createElementNS(SVGNS, tag);
      for (const k of Object.keys(a)) node.setAttribute(k, a[k]);
      svg.append(node);
    }
    return svg;
  }

  /* ------------------------------------------------------------ DOM helper */
  // el('div', {class:'x', text:'hello', 'aria-label':'y'}, child, [child, child], 'text')
  function el(tag, props, ...kids) {
    const n = document.createElement(tag);
    if (props) {
      for (const k of Object.keys(props)) {
        const v = props[k];
        if (v == null || v === false) continue;
        if (k === 'class') n.className = v;
        else if (k === 'text') n.textContent = String(v);
        else n.setAttribute(k, v === true ? '' : String(v));
      }
    }
    n.append(...norm(kids));
    return n;
  }
  // Flatten nested arrays, drop null/false, wrap strings as text nodes (never HTML).
  function norm(kids) {
    return kids.flat(Infinity)
      .filter((k) => k != null && k !== false)
      .map((k) => (k instanceof Node ? k : document.createTextNode(String(k))));
  }
  function fill(node, ...kids) {
    node.replaceChildren(...norm(kids));
  }
  const $ = (id) => document.getElementById(id);

  /* ----------------------------------------------------------------- time */
  const pad2 = (n) => String(n).padStart(2, '0');
  function parseDate(iso) {
    if (typeof iso !== 'string' || !iso) return null;
    const d = new Date(iso);
    return Number.isNaN(d.getTime()) ? null : d;
  }
  // Viewer local time, HH:MM:SS.
  function fmtTime(iso) {
    const d = parseDate(iso);
    return d ? pad2(d.getHours()) + ':' + pad2(d.getMinutes()) + ':' + pad2(d.getSeconds()) : null;
  }
  function fmtFull(iso) {
    const d = parseDate(iso);
    if (!d) return '';
    let local;
    try {
      local = d.toLocaleString([], { dateStyle: 'medium', timeStyle: 'medium' });
    } catch (e) {
      local = d.toString();
    }
    return local + ' (' + iso + ')';
  }
  function tzName() {
    try {
      const part = new Intl.DateTimeFormat([], { timeZoneName: 'short' })
        .formatToParts(new Date())
        .find((p) => p.type === 'timeZoneName');
      return part ? part.value : '';
    } catch (e) {
      return '';
    }
  }
  function timeEl(iso, cls) {
    const t = fmtTime(iso);
    if (!t) return el('span', { class: (cls + ' is-empty').trim(), text: '—', 'aria-label': 'no time' });
    return el('time', { class: cls, datetime: iso, title: fmtFull(iso), text: t });
  }

  /* ----------------------------------------------------------- validation */
  function validate(s) {
    if (!s || typeof s !== 'object' || Array.isArray(s)) return 'state is not an object';
    if (s.schema !== 1) return 'unsupported schema ' + String(s.schema);
    if (!OVERALL_STATUSES.includes(s.status)) return 'unknown status ' + String(s.status);
    if (!s.change || typeof s.change !== 'object') return 'change missing';
    for (const k of ['environments', 'checks', 'timeline']) {
      if (!Array.isArray(s[k])) return k + ' is not an array';
    }
    if (!s.results || typeof s.results !== 'object') return 'results missing';
    if (!s.room || typeof s.room !== 'object' || !Array.isArray(s.room.agents) || !Array.isArray(s.room.humans)) {
      return 'room malformed';
    }
    return null;
  }

  /* -------------------------------------------------------------- derived */
  const str = (v, fallback = '') => (typeof v === 'string' ? v : v == null ? fallback : String(v));

  function cellOf(s, envId, chkId) {
    const r = s.results[envId] && s.results[envId][chkId];
    const status = r && RESULT_STATUSES.includes(r.status) ? r.status : 'pending';
    return {
      status,
      at: r && typeof r.at === 'string' ? r.at : null,
      detail: r && typeof r.detail === 'string' && r.detail ? r.detail : null,
    };
  }

  function envSummary(s, env) {
    const c = { pass: 0, fail: 0, running: 0, pending: 0, total: s.checks.length };
    for (const chk of s.checks) c[cellOf(s, env.id, chk.id).status]++;
    c.status = c.fail ? 'fail' : c.running ? 'running' : c.pending ? 'pending' : c.total ? 'pass' : 'pending';
    return c;
  }

  function totals(s) {
    const t = { pass: 0, fail: 0, running: 0, pending: 0, total: 0 };
    for (const env of s.environments) {
      for (const chk of s.checks) {
        t[cellOf(s, env.id, chk.id).status]++;
        t.total++;
      }
    }
    return t;
  }

  const envLabel = (env) => str(env.label) || str(env.id);

  function factKeys(s) {
    const seen = new Set();
    for (const env of s.environments) Object.keys(env.facts || {}).forEach((k) => seen.add(k));
    const rest = [...seen].filter((k) => !FACT_ORDER.includes(k)).sort();
    return FACT_ORDER.filter((k) => seen.has(k)).concat(rest);
  }

  // Facts whose values differ between environments.
  function factDiffs(s) {
    const out = [];
    for (const k of factKeys(s)) {
      const vals = s.environments.map((e) => str((e.facts || {})[k], '—'));
      if (new Set(vals).size > 1) out.push({ key: k, values: vals, labels: s.environments.map(envLabel) });
    }
    return out;
  }

  // Parity alert: at least one environment has no failures (and some passes) while
  // at least one other environment has failures.
  function parityAlert(s) {
    const sums = s.environments.map((env) => ({ env, c: envSummary(s, env) }));
    const passing = sums.filter((x) => x.c.fail === 0 && x.c.pass > 0);
    const failing = sums.filter((x) => x.c.fail > 0);
    if (!passing.length || !failing.length) return null;
    const parts = passing
      .map((x) => envLabel(x.env) + ' passes ' + x.c.pass + '/' + x.c.total)
      .join(', ');
    const fails = failing.map((x) => envLabel(x.env) + ' fails ' + x.c.fail + '/' + x.c.total).join(', ');
    return { text: parts + ' but ' + fails + ': environment-dependent failures.', diffs: factDiffs(s) };
  }

  const safeHref = (u) => (typeof u === 'string' && /^https?:\/\//i.test(u) ? u : null);

  /* ------------------------------------------------------------- renderers */
  const prevCells = new Map(); // "env\0check" -> status, for flip animation
  let hasRendered = false;
  let prevEventCount = 0;

  function renderChange(s) {
    const c = s.change;
    const node = $('change');
    const branch = str(c.branch, 'unknown branch');
    fill(node, 
      el('span', { class: 'chip chip-branch', title: str(c.title) ? str(c.title) : branch },
        icon('branch', 14),
        el('span', { class: 'mono branch', text: branch })),
      c.head_sha
        ? el('span', { class: 'chip chip-sha', 'aria-label': 'commit ' + str(c.head_sha) },
            icon('commit', 14),
            el('span', { class: 'mono', text: str(c.head_sha) }))
        : null,
      c.author ? el('span', { class: 'by' }, 'by ', el('strong', { text: str(c.author) })) : null
    );
  }

  function renderOverall(s) {
    const view = OVERALL_VIEW[s.status];
    const t = totals(s);
    let sub;
    if (!t.total) sub = 'no checks defined';
    else if (s.status === 'pending' && t.pass === 0 && t.fail === 0) sub = t.total + ' checks pending';
    else sub = t.pass + ' of ' + t.total + ' checks passing';
    const node = $('overall');
    node.className = 'overall ' + view.cls;
    node.setAttribute('aria-label', 'Overall status ' + OVERALL_LABEL[s.status] + ', ' + sub);
    fill(node, 
      icon(view.icon, 24, s.status === 'running' ? 'spin' : ''),
      el('span', { class: 'overall-text' },
        el('span', { class: 'overall-label', text: OVERALL_LABEL[s.status] }),
        el('span', { class: 'overall-sub', text: sub }))
    );
    if (hasRendered) retrigger(node, 'flip');
    document.title = 'Parity Room · ' + OVERALL_LABEL[s.status] + (s.change.branch ? ' · ' + str(s.change.branch) : '');
  }

  function retrigger(node, cls) {
    if (reduceMotion.matches) return;
    node.classList.remove(cls);
    void node.offsetWidth; // restart animation
    node.classList.add(cls);
  }

  function statusBadge(status, text, extraCls) {
    return el('span', { class: ('badge s-' + status + ' ' + (extraCls || '')).trim() },
      icon(status, 12, status === 'running' ? 'spin' : ''),
      el('span', { text }));
  }

  function renderMatrix(s) {
    const matrix = $('matrix');
    const cols = Math.max(1, s.checks.length);
    matrix.style.setProperty('--cols', String(cols));
    const diffKeys = new Set(factDiffs(s).map((d) => d.key));
    const keys = factKeys(s);
    const t = totals(s);

    // Panel sub line + summary chips
    $('matrix-sub').textContent = str(s.change.title);
    const chips = [];
    for (const st of ['pass', 'fail', 'running', 'pending']) {
      if (t[st] > 0) {
        chips.push(el('span', { class: 'count s-' + st },
          icon(st, 14, st === 'running' ? 'spin' : ''),
          el('span', { class: 'mono num', text: t[st] }),
          ' ' + { pass: 'passing', fail: 'failing', running: 'running', pending: 'pending' }[st]));
      }
    }
    if (!t.total) chips.push(el('span', { class: 'count s-pending', text: 'No checks defined' }));
    const done = t.pass + t.fail;
    let note;
    if (t.total && t.pass === t.total) {
      note = el('span', { class: 'note s-pass' }, icon('shield', 14),
        'All ' + t.total + ' checks pass on ' + s.environments.length + ' of ' + s.environments.length + ' environments · parity verified');
    } else if (t.total) {
      note = el('span', { class: 'note' }, done + ' of ' + t.total + ' results in · ' +
        s.checks.length + ' checks × ' + s.environments.length + ' environments');
    }
    fill($('matrix-summary'), chips, note);

    // Header row
    const head = el('div', { class: 'mrow mhead', role: 'row' },
      el('div', { class: 'mcell corner label-md', role: 'columnheader', text: 'Environment & agent' }),
      s.checks.map((chk, i) =>
        el('div', { class: 'mcell chk', role: 'columnheader' },
          el('span', { class: 'label-md', text: 'Check ' + (i + 1) + ' · ' + str(chk.title, chk.id) }),
          chk.test ? el('code', { class: 'chk-test', text: str(chk.test) }) : null)));

    // Environment rows
    const rows = s.environments.map((env) => {
      const sum = envSummary(s, env);
      const agent = s.room.agents.find((a) => a.name === env.agent);
      const facts = env.facts || {};
      const envCell = el('div', { class: 'envcell', role: 'rowheader' },
        el('div', { class: 'env-top' },
          icon('monitor', 18, 'env-ico'),
          el('h3', { class: 'env-name', text: envLabel(env) }),
          statusBadge(sum.status, { pass: 'PASSING', fail: 'FAILING', running: 'RUNNING', pending: 'PENDING' }[sum.status] + ' ' + sum.pass + '/' + sum.total)),
        el('dl', { class: 'facts' },
          keys.filter((k) => k in facts).map((k) =>
            el('div', { class: 'fact' + (diffKeys.has(k) ? ' differs' : '') },
              el('dt', { class: 'label-sm' },
                FACT_LABEL[k] || k.toUpperCase(),
                diffKeys.has(k) ? el('span', { class: 'neq', title: 'Differs between environments', 'aria-label': 'differs between environments', text: '≠' }) : null),
              el('dd', { class: 'mono', text: str(facts[k]) })))),
        el('div', { class: 'env-agent' },
          el('div', { class: 'agent-line' },
            agent
              ? el('span', { class: 'pip ' + (agent.online ? 'on' : 'off'), title: agent.online ? 'online' : 'offline' },
                  el('span', { class: 'sr-only', text: agent.online ? 'online' : 'offline' }))
              : null,
            el('span', { class: 'mono agent-name', text: str(env.agent) }),
            env.provider ? el('span', { class: 'provider', text: str(env.provider) }) : null),
          env.machine
            ? el('div', { class: 'machine' }, icon('server', 13), el('span', { class: 'mono', text: str(env.machine) }))
            : null));

      const cells = s.checks.map((chk) => {
        const r = cellOf(s, env.id, chk.id);
        const key = str(env.id) + '\u0000' + str(chk.id);
        const prev = prevCells.get(key);
        const flipped = hasRendered && prev !== undefined && prev !== r.status && !reduceMotion.matches;
        prevCells.set(key, r.status);
        const time = fmtTime(r.at);
        const aria = envLabel(env) + ', ' + str(chk.title, chk.id) + ': ' + RESULT_LABEL[r.status].toLowerCase() + (time ? ' at ' + time : '');
        return el('div', { class: 'cell s-' + r.status + (flipped ? ' flip' : ''), role: 'cell', 'aria-label': aria },
          el('div', { class: 'cell-top' },
            el('span', { class: 'result' },
              icon(r.status, 18, r.status === 'running' ? 'spin' : ''),
              el('span', { class: 'result-label', text: RESULT_LABEL[r.status] })),
            timeEl(r.at, 'cell-time mono')),
          chk.test ? el('code', { class: 'cell-test', text: str(chk.test) }) : null,
          r.detail ? el('div', { class: 'detail mono', text: r.detail }) : null);
      });

      return el('div', { class: 'mrow env-row', role: 'row' }, envCell, cells);
    });

    if (!s.environments.length) {
      fill(matrix, head, el('p', { class: 'empty', text: 'No environments in state.' }));
    } else {
      fill(matrix, head, rows);
    }
  }

  function renderAlert(s) {
    const slot = $('alert-slot');
    const a = parityAlert(s);
    if (!a) {
      fill(slot, );
      return;
    }
    fill(slot, 
      el('div', { class: 'alert s-fail', role: 'alert' },
        icon('alert', 20, 'alert-ico'),
        el('div', { class: 'alert-body' },
          el('div', { class: 'alert-head' },
            el('span', { class: 'label-md alert-label', text: 'Parity alert' }),
            el('p', { class: 'alert-text', text: a.text })),
          a.diffs.length
            ? el('div', { class: 'alert-diffs' },
                el('span', { class: 'label-sm', text: 'Differs between environments' }),
                el('ul', null,
                  a.diffs.map((d) =>
                    el('li', null,
                      el('span', { class: 'label-sm dk', text: FACT_LABEL[d.key] || d.key.toUpperCase() }),
                      d.values.map((v, i) => [
                        i > 0 ? el('span', { class: 'neq-sep', 'aria-label': 'differs from', text: '≠' }) : null,
                        el('code', { class: 'mono', title: d.labels[i], text: v }),
                      ])))))
            : null)));
  }

  function renderRoom(s) {
    const room = s.room;
    $('room-title').textContent = str(room.name, '—');
    const link = s.links && safeHref(s.links.room);
    fill($('room-link-slot'), 
      link
        ? el('a', { class: 'btn-link', href: link, target: '_blank', rel: 'noopener noreferrer' }, 'Open room', icon('external', 13))
        : null);

    const agents = room.agents.map((a) => {
      const roles = Array.isArray(a.roles) ? a.roles : [];
      return el('li', { class: 'agent-card' },
        el('div', { class: 'ac-top' },
          el('span', { class: 'pip ' + (a.online ? 'on' : 'off') }),
          icon('bot', 15, 'ac-ico'),
          el('span', { class: 'mono ac-name', text: str(a.name) }),
          el('span', { class: 'ac-state ' + (a.online ? 'on' : 'off'), text: a.online ? 'ONLINE' : 'OFFLINE' })),
        el('div', { class: 'ac-meta' },
          a.provider ? el('span', { class: 'provider', text: str(a.provider) }) : null,
          a.machine ? el('span', { class: 'machine' }, icon('server', 13), el('span', { class: 'mono', text: str(a.machine) })) : null),
        el('div', { class: 'roles', 'aria-label': 'Roles held by ' + str(a.name) },
          roles.length
            ? roles.map((r) => {
                const excl = r.mode === 'exclusive';
                return el('span', { class: 'role ' + (excl ? 'exclusive' : 'shared') },
                  el('span', { class: 'role-name mono', text: str(r.name) }),
                  el('span', { class: 'mode' },
                    icon(excl ? 'lock' : 'users', 11),
                    str(r.mode).toUpperCase()));
              })
            : el('span', { class: 'no-roles', text: 'No roles held' })));
    });

    const humans = room.humans.map((h) =>
      el('li', { class: 'human-card' },
        avatar(str(h.name), 'human'),
        el('div', { class: 'hc-text' },
          el('span', { class: 'hc-name', text: str(h.name) }),
          el('span', { class: 'hc-title', text: str(h.title) })),
        el('span', { class: 'kind-badge human' }, icon('user', 11), 'HUMAN')));

    fill($('rail-body'), 
      el('div', { class: 'rail-sec' },
        el('h3', { class: 'sec-title label-md' }, 'Agents ', el('span', { class: 'mono num', text: '(' + room.agents.length + ')' })),
        agents.length ? el('ul', { class: 'cards' }, agents) : el('p', { class: 'empty', text: 'No agents in room.' })),
      el('div', { class: 'rail-sec' },
        el('h3', { class: 'sec-title label-md' }, 'Humans ', el('span', { class: 'mono num', text: '(' + room.humans.length + ')' })),
        humans.length ? el('ul', { class: 'cards' }, humans) : el('p', { class: 'empty', text: 'No humans in room.' })));
  }

  function avatar(name, kind) {
    const initial = (Array.from(name.trim())[0] || '?').toUpperCase();
    return el('span', { class: 'avatar ' + kind, 'aria-hidden': 'true', text: initial });
  }

  function renderTimeline(s) {
    const events = s.timeline
      .map((e, i) => ({ e, i, t: (parseDate(e.at) || { getTime: () => NaN }).getTime() }))
      .sort((a, b) => (Number.isNaN(a.t) || Number.isNaN(b.t) || a.t === b.t ? a.i - b.i : a.t - b.t))
      .map((x) => x.e);
    $('timeline-sub').textContent = events.length + (events.length === 1 ? ' event' : ' events') + ' · oldest first';
    const startNew = hasRendered && !reduceMotion.matches ? prevEventCount : events.length;
    prevEventCount = events.length;
    if (!events.length) {
      fill($('timeline'), el('li', { class: 'empty', text: 'No activity yet.' }));
      return;
    }
    fill($('timeline'), 
      events.map((e, i) => {
        const kind = e.kind === 'human' ? 'human' : e.kind === 'agent' ? 'agent' : 'other';
        const latest = i === events.length - 1;
        return el('li', { class: 'event ' + kind + (latest ? ' latest' : '') + (i >= startNew ? ' enter' : ''), 'aria-current': latest ? 'true' : null },
          avatar(str(e.actor), kind),
          el('div', { class: 'ev-card' },
            el('div', { class: 'ev-head' },
              el('h3', { class: 'ev-title', text: str(e.title) }),
              kind !== 'other'
                ? el('span', { class: 'kind-badge ' + kind }, icon(kind === 'agent' ? 'bot' : 'user', 11), kind.toUpperCase())
                : null,
              e.actor ? el('span', { class: 'mono ev-actor', text: str(e.actor) }) : null,
              el('span', { class: 'ev-when' },
                latest ? el('span', { class: 'latest-tag label-sm', text: 'LATEST' }) : null,
                timeEl(e.at, 'ev-time mono'))),
            e.detail ? el('p', { class: 'ev-detail', text: str(e.detail) }) : null));
      }));
  }

  function renderFooter(s) {
    const tz = tzName();
    fill($('foot'), 
      el('span', null, 'Updated ', timeEl(s.updated_at, 'mono')),
      el('span', { class: 'sep', 'aria-hidden': 'true', text: '·' }),
      el('span', { class: 'mono', text: 'schema ' + s.schema }),
      el('span', { class: 'sep', 'aria-hidden': 'true', text: '·' }),
      el('span', { text: 'Times in your local time' + (tz ? ' (' + tz + ')' : '') }));
  }

  /* section registry: [name, signature-slice, renderer] */
  const SECTIONS = [
    ['change', (s) => s.change, renderChange],
    ['overall', (s) => [s.status, s.change, totals(s)], renderOverall],
    ['matrix', (s) => [s.change.title, s.environments, s.checks, s.results, s.room.agents], renderMatrix],
    ['alert', (s) => [s.environments, s.checks, s.results], renderAlert],
    ['room', (s) => [s.room, s.links], renderRoom],
    ['timeline', (s) => s.timeline, renderTimeline],
    ['footer', (s) => [s.updated_at, s.schema], renderFooter],
  ];
  const lastSig = {};

  function render(s) {
    for (const [name, pick, fn] of SECTIONS) {
      let sig;
      try {
        sig = JSON.stringify(pick(s));
      } catch (e) {
        sig = String(Math.random());
      }
      if (sig === lastSig[name]) continue;
      try {
        fn(s);
        lastSig[name] = sig;
      } catch (err) {
        console.error('[parity-room] render failed for', name, err);
        delete lastSig[name];
      }
    }
    hasRendered = true;
  }

  /* ------------------------------------------------------------ connection */
  let state = null;
  let conn = { kind: 'connecting', detail: '' };

  function setConn(kind, detail) {
    detail = detail || '';
    if (conn.kind === kind && conn.detail === detail) return;
    conn = { kind, detail };
    renderConn();
    if (!state) renderEmpty();
  }

  function renderConn() {
    const node = $('conn');
    const hasState = !!state;
    const map = {
      connecting: { cls: 'c-connecting', label: 'CONNECTING', sub: API_URL },
      live: { cls: 'c-live', label: 'LIVE', sub: 'polling ' + API_URL + ' · 1s' },
      disconnected: {
        cls: 'c-down',
        label: 'DISCONNECTED',
        sub: hasState ? 'showing last known state' : 'no state received yet',
      },
      invalid: { cls: 'c-down', label: 'BAD DATA', sub: hasState ? 'showing last valid state' : 'no valid state yet' },
      fixture: { cls: 'c-static', label: 'FIXTURE', sub: conn.detail },
      play: { cls: 'c-static', label: 'AUTO-PLAY', sub: conn.detail },
    };
    const v = map[conn.kind] || map.connecting;
    node.className = 'conn ' + v.cls;
    node.title = conn.kind === 'disconnected' || conn.kind === 'invalid' ? conn.detail : '';
    node.setAttribute('aria-label', 'Connection: ' + v.label.toLowerCase() + ', ' + v.sub);
    fill(node, 
      conn.kind === 'disconnected' || conn.kind === 'invalid'
        ? icon('alert', 16, 'conn-ico')
        : el('span', { class: 'pip live-pip' }),
      el('span', { class: 'conn-text' },
        el('span', { class: 'conn-label', text: v.label }),
        el('span', { class: 'conn-sub', text: v.sub })));
  }

  // Shown inside the panels while no state has ever arrived.
  function renderEmpty() {
    let msg = 'Waiting for state…';
    if (conn.kind === 'disconnected') msg = 'No state received. Waiting for ' + API_URL + '…';
    else if (conn.kind === 'invalid') msg = 'Cannot render state: ' + conn.detail + '.';
    const matrix = $('matrix');
    if (!matrix.querySelector('.mrow')) fill(matrix, el('p', { class: 'empty', id: 'matrix-empty', text: msg }));
  }

  function applyState(next, kind, detail) {
    const problem = validate(next);
    if (problem) {
      setConn('invalid', problem);
      return false;
    }
    state = next;
    setConn(kind, detail);
    render(state);
    return true;
  }

  /* ----------------------------------------------------------- data sources */
  async function getJSON(url) {
    const ctrl = typeof AbortController === 'function' ? new AbortController() : null;
    const timer = ctrl ? setTimeout(() => ctrl.abort(), FETCH_TIMEOUT_MS) : null;
    try {
      const res = await fetch(url, { cache: 'no-store', signal: ctrl ? ctrl.signal : undefined, headers: { Accept: 'application/json' } });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return await res.json();
    } finally {
      if (timer) clearTimeout(timer);
    }
  }

  function startPolling() {
    setConn('connecting');
    const tick = async () => {
      const started = Date.now();
      try {
        const data = await getJSON(API_URL);
        applyState(data, 'live');
      } catch (err) {
        setConn('disconnected', err && err.name === 'AbortError' ? 'request timed out' : String((err && err.message) || err));
      }
      setTimeout(tick, Math.max(0, POLL_MS - (Date.now() - started)));
    };
    tick();
  }

  async function startFixture(name) {
    if (!FIXTURE_NAMES.includes(name)) {
      setConn('invalid', 'unknown fixture "' + String(name).slice(0, 40) + '" (use ' + FIXTURE_NAMES.join('|') + ')');
      return;
    }
    try {
      const data = await getJSON('./fixtures/state-' + name + '.json');
      applyState(data, 'fixture', 'static · ' + name);
    } catch (err) {
      setConn('disconnected', 'could not load fixture ' + name + ': ' + String((err && err.message) || err));
    }
  }

  async function startPlay() {
    setConn('connecting');
    let frames;
    try {
      frames = await Promise.all(FIXTURE_NAMES.map((n) => getJSON('./fixtures/state-' + n + '.json')));
    } catch (err) {
      setConn('disconnected', 'could not load fixtures: ' + String((err && err.message) || err));
      return;
    }
    let i = 0;
    const show = () => {
      applyState(frames[i], 'play', 'step ' + (i + 1) + '/' + frames.length + ' · ' + FIXTURE_NAMES[i]);
      i = (i + 1) % frames.length;
    };
    show();
    setInterval(show, PLAY_MS);
  }

  /* ------------------------------------------------------------------ init */
  function buildLegend() {
    fill($('legend'), 
      ['pass', 'fail', 'running', 'pending'].map((st) =>
        el('span', { class: 'lg s-' + st }, icon(st, 13), RESULT_LABEL[st].toLowerCase())));
    fill($('matrix-title-icon'), icon('grid', 18));
    fill($('timeline-title-icon'), icon('activity', 18));
  }

  function init() {
    buildLegend();
    renderConn();
    const q = new URLSearchParams(window.location.search);
    if (q.get('play') === '1' || q.get('play') === 'true') startPlay();
    else if (q.has('fixture')) startFixture(q.get('fixture'));
    else startPolling();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
