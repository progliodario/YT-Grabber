/* YT Grabber - user interface. Deliberately "classic" JavaScript (no ?. ?? etc.) so it runs in any browser. */
(function () {
  'use strict';

  // ------------------------------------------------------------------ language
  // Texts live in lang/<code>.js (lang/en.js is loaded with the page, the others on demand).
  var LANGS = [['en', 'English'], ['it', 'Italiano'], ['es', 'Español'], ['fr', 'Français'], ['de', 'Deutsch'],
    ['pt', 'Português'], ['nl', 'Nederlands'], ['pl', 'Polski'], ['ru', 'Русский'], ['tr', 'Türkçe'],
    ['ar', 'العربية'], ['hi', 'हिन्दी'], ['id', 'Bahasa Indonesia'], ['zh', '中文（简体）'], ['ja', '日本語'], ['ko', '한국어']];
  var LANG = 'en';
  function hasLang(code) { var i; for (i = 0; i < LANGS.length; i++) { if (LANGS[i][0] === code) { return true; } } return false; }
  function pluralForm(n) {
    try { return new Intl.PluralRules(LANG).select(n); } catch (e) { return n === 1 ? 'one' : 'other'; }
  }
  // tr('key', { name: value }): the text of the current language (English when a key is missing)
  function tr(key, vars) {
    var v = I18N[LANG] && I18N[LANG][key];
    if (v === undefined) { v = I18N.en[key]; }
    if (v === undefined) { return key; }
    if (typeof v === 'object') {
      var f = pluralForm(vars && vars.n != null ? vars.n : 1);
      v = v[f] !== undefined ? v[f] : v.other;
    }
    return vars ? String(v).replace(/\{(\w+)\}/g, function (m, k) { return vars[k] === undefined ? m : vars[k]; }) : String(v);
  }
  function detectLang() {
    var saved = null, list = [], i, l;
    try { saved = localStorage.getItem('ytg-lang'); } catch (e) { saved = null; }
    if (saved && hasLang(saved)) { return saved; }
    list = (navigator.languages && navigator.languages.length) ? navigator.languages : [navigator.language || 'en'];
    for (i = 0; i < list.length; i++) {
      l = String(list[i]).toLowerCase().split('-')[0];
      if (l === 'in') { l = 'id'; }
      if (hasLang(l)) { return l; }
    }
    return 'en';
  }
  function loadLang(code, done) {
    if (I18N[code]) { done(); return; }
    var s = document.createElement('script');
    s.src = 'lang/' + code + '.js';
    s.onload = done; s.onerror = done;
    document.head.appendChild(s);
  }
  function applyStatic() {
    var els, i, j, parts, p;
    els = document.querySelectorAll('[data-i18n]');
    for (i = 0; i < els.length; i++) { els[i].textContent = tr(els[i].getAttribute('data-i18n')); }
    els = document.querySelectorAll('[data-i18n-html]');
    for (i = 0; i < els.length; i++) { els[i].innerHTML = tr(els[i].getAttribute('data-i18n-html')); }
    els = document.querySelectorAll('[data-i18n-attr]');
    for (i = 0; i < els.length; i++) {
      parts = els[i].getAttribute('data-i18n-attr').split(',');
      for (j = 0; j < parts.length; j++) { p = parts[j].split(':'); els[i].setAttribute(p[0], tr(p[1])); }
    }
    var sh = $('#subHours'), cur = sh.value || '24', html = '';
    for (i = 0; i < SUB_HOURS.length; i++) { html += '<option value="' + SUB_HOURS[i] + '">' + esc(tr('every.' + SUB_HOURS[i])) + '</option>'; }
    sh.innerHTML = html; sh.value = cur;
  }
  function setLanguage(code, remember) {
    if (!hasLang(code)) { code = 'en'; }
    loadLang(code, function () {
      if (!I18N[code]) { code = 'en'; }
      LANG = code;
      document.documentElement.lang = code;
      document.documentElement.dir = code === 'ar' ? 'rtl' : 'ltr';
      if (remember) {
        try { localStorage.setItem('ytg-lang', code); } catch (e) { /* ignore */ }
        var payload = {}, k;   // also kept by the server, so the Windows tray menu speaks the same language
        for (k in S.settings) { if (Object.prototype.hasOwnProperty.call(S.settings, k)) { payload[k] = S.settings[k]; } }
        payload.lang = code;
        api('POST', '/api/settings', payload).then(function (r) { S.settings = r.settings; }, function () { /* non-blocking */ });
      }
      $('#langSel').value = code;
      applyStatic();
      applyTheme(getTheme());
      form.reflect(); updateDetect();
      if (S.lastState) {
        applyState(S.lastState);
        if (S.detail) {
          S.detail.panelHtml = ''; S.detail.tabsHtml = '';
          var inp = S.detail.box.parentNode.querySelector('.search');
          if (inp) { inp.placeholder = tr('detail.search'); inp.setAttribute('aria-label', tr('detail.searchLabel')); }
          S.detail.tabsEl.setAttribute('aria-label', tr('detail.filters')); S.detail.box.setAttribute('aria-label', tr('list.label'));
          var lh = document.getElementById('lh-' + S.detail.id); if (lh) { lh.textContent = tr('list.help'); }
          renderDetail();
        }
      }
    });
  }
  var STAGE_KEYS = { 'Starting': 'stage.starting', 'Analyzing': 'stage.analyzing', 'Download': 'stage.download', 'Converting': 'stage.converting',
    'Converting audio': 'stage.convaudio', 'Merging video+audio': 'stage.merging', 'Cover art': 'stage.cover', 'Metadata': 'stage.metadata',
    'Saving': 'stage.saving', 'Converting video': 'stage.convvideo', 'Fixing file': 'stage.fixing', 'Completed': 'stage.completed',
    'Already present': 'stage.present', 'Error': 'stage.error', 'Cancelled': 'stage.cancelled' };
  function stageText(s) {
    s = s || '';
    if (STAGE_KEYS[s]) { return tr(STAGE_KEYS[s]); }
    var m = /^Download \((\d+)\/(\d+)\)$/.exec(s);
    if (m) { return tr('stage.downloadN', { a: m[1], b: m[2] }); }
    m = /^Retry (\d+)\/(\d+)$/.exec(s);
    if (m) { return tr('stage.retry', { a: m[1], b: m[2] }); }
    return s;
  }
  var SUB_HOURS = [1, 3, 6, 12, 24, 72, 168];

  var ROW = 64;   // row height: 92 on narrow screens (see CSS), updated in calcRow()
  // The rows of the list follow the text size (the font size of the page, which the user may have enlarged) as well as the width.
  function calcRow() {
    var rem = parseFloat(window.getComputedStyle(document.documentElement).fontSize) || 16;
    ROW = Math.round(rem * (window.innerWidth <= 760 ? 5.75 : 4));
    document.documentElement.style.setProperty('--row', ROW + 'px');
  }
  var TABS = ['all', 'a', 'p', 'q', 'd', 'e', 'c'];

  var S = {
    settings: {}, jobs: [], cards: {}, openId: null, detail: null, errmeta: {}, local: false, tools: {},
    concurrency: 10, browsers: [], hasCookies: false, ytdlp: '', formInit: false, online: true, serverOffset: 0,
    lastState: null, subs: [], subIntervals: []
  };

  // ------------------------------------------------------------------ utilities
  function $(sel, root) { return (root || document).querySelector(sel); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function trunc(s, n) { s = String(s || ''); return s.length > n ? s.slice(0, n - 1) + '…' : s; }
  function padNum(n, w) { var s = String(n); while (s.length < w) { s = '0' + s; } return s; }
  function fmtBytes(b) {
    if (b == null || isNaN(b)) { return ''; }
    var u = ['B', 'KB', 'MB', 'GB', 'TB'], i = 0;
    while (b >= 1024 && i < u.length - 1) { b /= 1024; i++; }
    return (i === 0 ? b.toFixed(0) : b.toFixed(b >= 100 ? 0 : 1)) + ' ' + u[i];
  }
  function fmtEta(s) {
    if (s == null || isNaN(s)) { return ''; }
    s = Math.round(s);
    if (s < 60) { return s + 's'; }
    var m = Math.floor(s / 60);
    if (m < 60) { return m + 'm ' + (s % 60) + 's'; }
    var h = Math.floor(m / 60);
    if (h < 48) { return h + 'h ' + (m % 60) + 'm'; }
    return Math.floor(h / 24) + 'd ' + (h % 24) + 'h';
  }
  function fmtDate(ts) {
    var d = new Date(ts * 1000), now = new Date();
    var hm = padNum(d.getHours(), 2) + ':' + padNum(d.getMinutes(), 2);
    if (d.toDateString() === now.toDateString()) { return tr('date.today', { t: hm }); }
    return d.getDate() + '/' + (d.getMonth() + 1) + ' ' + hm;
  }
  // Replaces the content of an element but keeps the keyboard focus on the same control when it is still there:
  // the page refreshes itself every second or so, and a button that loses focus under your fingers is unusable.
  function focusKey(f) { return [f.getAttribute('data-act'), f.getAttribute('data-id'), f.getAttribute('data-idx'), f.getAttribute('data-tab'), f.getAttribute('data-kind')].join('|'); }
  function setHtmlKeepFocus(el, html) {
    var f = document.activeElement, key = (f && f !== document.body && el.contains(f) && f.getAttribute('data-act')) ? focusKey(f) : null, i, list;
    el.innerHTML = html;
    if (key) {
      list = el.querySelectorAll('[data-act]');
      for (i = 0; i < list.length; i++) { if (focusKey(list[i]) === key) { list[i].focus(); break; } }
    }
  }
  function setH(el, html) { if (el._h !== html) { el._h = html; setHtmlKeepFocus(el, html); } }
  function api(method, url, body) {
    return new Promise(function (resolve, reject) {
      var x = new XMLHttpRequest();
      x.open(method, url, true);
      x.setRequestHeader('X-YTG', '1');
      if (body !== undefined) { x.setRequestHeader('Content-Type', 'application/json'); }
      x.timeout = 60000;
      x.onload = function () {
        var d = null;
        try { d = JSON.parse(x.responseText); } catch (e) { d = null; }
        if (x.status >= 200 && x.status < 300) { resolve(d); }
        else { reject(new Error((d && d.error) || tr('err.http', { code: x.status }))); }
      };
      x.onerror = function () { reject(new Error(tr('err.unreachable'))); };
      x.ontimeout = function () { reject(new Error(tr('err.noResponse'))); };
      x.send(body !== undefined ? JSON.stringify(body) : null);
    });
  }
  // A message for screen readers only (a download finished, a problem). Emptying the region first makes them read a message that did not change.
  function announce(msg) {
    var el = $('#announce');
    el.textContent = '';
    setTimeout(function () { el.textContent = msg; }, 60);
  }
  // A short message in the corner. It has a close button, stays while the pointer or the focus is on it, and lasts long enough to be read.
  function toast(msg, bad) {
    var el = document.createElement('div'), tx = document.createElement('span'), x = document.createElement('button'), t = null, left = bad ? 15000 : 7000, started = 0;
    el.className = 'toast' + (bad ? ' bad' : '');
    tx.textContent = msg; el.appendChild(tx);
    x.type = 'button'; x.className = 'toast-x'; x.textContent = '×'; x.setAttribute('aria-label', tr('close'));
    el.appendChild(x);
    $('#toasts').appendChild(el);
    function gone() { if (t) { clearTimeout(t); t = null; } if (el.parentNode) { el.parentNode.removeChild(el); } }
    function start() { if (!t) { started = Date.now(); t = setTimeout(gone, left); } }
    function pause() { if (t) { clearTimeout(t); t = null; left = Math.max(4000, left - (Date.now() - started)); } }
    x.addEventListener('click', gone);
    el.addEventListener('mouseenter', pause); el.addEventListener('mouseleave', start);
    el.addEventListener('focusin', pause); el.addEventListener('focusout', start);
    start();
  }
  function copyText(text) {
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      toast(ok ? tr('toast.copied') : tr('toast.copyFail'), !ok);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { toast(tr('toast.copied')); }, fallback);
    } else { fallback(); }
  }
  function findAct(el, stop) {
    while (el && el !== stop) {
      if (el.getAttribute && el.getAttribute('data-act')) { return el; }
      el = el.parentNode;
    }
    return null;
  }
  function errLabel(k) {
    var v = tr('ek.' + k);
    return v !== 'ek.' + k ? v : ((S.errmeta[k] && S.errmeta[k][0]) || tr('err.default'));
  }
  function errHint(k) {
    var v = tr('eh.' + k);
    return v !== 'eh.' + k ? v : ((S.errmeta[k] && S.errmeta[k][1]) || '');
  }

  var IC = {
    pause: '<svg class="ic" viewBox="0 0 24 24"><path d="M8 5v14M16 5v14"/></svg>',
    play: '<svg class="ic" viewBox="0 0 24 24"><path d="M7 4.5v15l12-7.5z"/></svg>',
    stop: '<svg class="ic" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>',
    retry: '<svg class="ic" viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 3-6.7M3 4v5h5"/></svg>',
    list: '<svg class="ic" viewBox="0 0 24 24"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>',
    folder: '<svg class="ic" viewBox="0 0 24 24"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>',
    m3u: '<svg class="ic" viewBox="0 0 24 24"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>',
    trash: '<svg class="ic" viewBox="0 0 24 24"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3"/></svg>',
    video: '<svg class="ic" viewBox="0 0 24 24"><rect x="2" y="5" width="14" height="14" rx="3"/><path d="m16 10 6-3v10l-6-3z"/></svg>',
    stack: '<svg class="ic" viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h10"/><path d="m17 15 4 3-4 3z"/></svg>',
    save: '<svg class="ic" viewBox="0 0 24 24"><path d="M12 4v11m0 0-4-4m4 4 4-4M5 20h14"/></svg>',
    open: '<svg class="ic" viewBox="0 0 24 24"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>',
    auto: '<svg class="ic" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></svg>',
    light: '<svg class="ic" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
    dark: '<svg class="ic" viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>'
  };
  (function () {   // the icons only decorate: the text of the button is its name
    var k;
    for (k in IC) { if (Object.prototype.hasOwnProperty.call(IC, k)) { IC[k] = IC[k].replace('<svg class="ic"', '<svg class="ic" aria-hidden="true" focusable="false"'); } }
  }());
  function btn(act, id, label, icon, cls, extra) {
    return '<button type="button" class="btn sm ' + (cls || '') + '" data-act="' + act + '" data-id="' + id + '"' + (extra || '') + '>' + (icon || '') + label + '</button>';
  }

  // ------------------------------------------------------------------ text size
  // A percentage of the size set in the browser (everything on the page is sized in rem, so one value enlarges all of it).
  var TEXT_SIZES = [100, 125, 150, 200];
  function getTextSize() {
    var z = 100;
    try { z = parseInt(localStorage.getItem('ytg-textsize'), 10) || 100; } catch (e) { z = 100; }
    return TEXT_SIZES.indexOf(z) < 0 ? 100 : z;
  }
  function applyTextSize(z) {
    document.documentElement.style.fontSize = z === 100 ? '' : z + '%';
    calcRow();
    if (S.detail) { renderVList(); }
  }

  // ------------------------------------------------------------------ theme
  var THEMES = ['auto', 'light', 'dark'];
  function getTheme() { var t = 'auto'; try { t = localStorage.getItem('ytg-theme') || 'auto'; } catch (e) { t = 'auto'; } return THEMES.indexOf(t) < 0 ? 'auto' : t; }
  function applyTheme(t) {
    if (t === 'auto') { document.documentElement.removeAttribute('data-theme'); } else { document.documentElement.setAttribute('data-theme', t); }
    var b = $('#btnTheme');
    b.innerHTML = IC[t]; b.title = tr('theme.title', { t: tr('theme.' + t) });
    b.setAttribute('aria-label', tr('theme.label', { t: tr('theme.' + t) }));
  }
  function cycleTheme() {
    var t = THEMES[(THEMES.indexOf(getTheme()) + 1) % THEMES.length];
    try { localStorage.setItem('ytg-theme', t); } catch (e) { /* ignore */ }
    applyTheme(t);
  }

  // ------------------------------------------------------------------ preview of the pasted links
  function classifyLocal(tok, singleOnly) {
    if (/^[\w-]{11}$/.test(tok)) { return 'video'; }
    if (/^(PL|OLAK5uy_|UU|FL|LL|RDCLAK5uy_|VL|PU)[\w-]{8,}$/.test(tok)) { return 'playlist'; }
    var m = tok.match(/^(?:https?:\/\/)?((?:www\.|m\.|music\.|gaming\.)?(?:youtube(?:-nocookie)?\.com|youtu\.be))(\/[^?#]*)?(?:\?([^#]*))?/i);
    if (!m) { return /^https?:\/\/\S+/i.test(tok) ? 'other' : 'bad'; }
    var host = m[1].toLowerCase(), path = m[2] || '/', qs = m[3] || '';
    var v = qs.match(/(?:^|&)v=([\w-]{11})/), l = qs.match(/(?:^|&)list=([\w-]+)/);
    if (host.indexOf('youtu.be') >= 0 && path.length > 1) { return 'video'; }
    if (/^\/(shorts|live|embed|v)\/[\w-]{11}/.test(path)) { return 'video'; }
    if (/^\/playlist/.test(path) && l) { return 'playlist'; }
    if (l && v) { return (singleOnly || /^(RD|UL)/.test(l[1])) ? 'video' : 'playlist'; }
    if (v) { return 'video'; }
    if (l) { return 'playlist'; }
    if (/^\/(@|channel\/|c\/|user\/|browse\/)/.test(path)) { return 'playlist'; }
    return 'bad';
  }
  function updateDetect() {
    var ta = $('#urls'), box = $('#detect'), toks = ta.value.split(/[\s,;]+/), seen = {}, n = { video: 0, playlist: 0, other: 0, bad: 0 }, i, t, c;
    var so = $('#singleOnly').checked;
    for (i = 0; i < toks.length; i++) {
      t = toks[i];
      if (!t || seen[t]) { continue; }
      seen[t] = 1; c = classifyLocal(t, so); n[c]++;
    }
    var h = '';
    if (n.playlist) { h += '<span class="dchip ok">' + esc(tr('det.playlist', { n: n.playlist })) + '</span>'; }
    if (n.video) { h += '<span class="dchip ok">' + esc(tr('det.video', { n: n.video })) + '</span>'; }
    if (n.other) { h += '<span class="dchip">' + esc(tr('det.other', { n: n.other })) + '</span>'; }
    if (n.bad) { h += '<span class="dchip bad">' + esc(tr('det.bad', { n: n.bad })) + '</span>'; }
    box.hidden = !h; box.innerHTML = h;
    $('#btnClear').hidden = !ta.value;
  }

  // ------------------------------------------------------------------ form
  var form = {
    el: function (id) { return document.getElementById(id); },
    radio: function (name) {
      var els = document.getElementsByName(name), i;
      for (i = 0; i < els.length; i++) { if (els[i].checked) { return els[i].value; } }
      return '';
    },
    setRadio: function (name, val) {
      var els = document.getElementsByName(name), i, any = false;
      for (i = 0; i < els.length; i++) { els[i].checked = (els[i].value === String(val)); any = any || els[i].checked; }
      if (!any && els.length) { els[0].checked = true; }
    },
    mode: function () { return this.radio('mode'); },
    reflect: function () {
      var video = this.mode() === 'video';
      this.el('gAudio').hidden = video;
      this.el('gBitrate').hidden = video || this.radio('audioFormat') !== 'mp3';
      this.el('gHeight').hidden = !video;
      var af = this.radio('audioFormat');
      this.el('fmtHint').textContent = video
        ? tr('hint.video')
        : (af === 'mp3'
          ? tr('hint.mp3')
          : tr('hint.fast'));
    },
    fill: function (s) {
      this.setRadio('mode', s.mode); this.setRadio('audioFormat', s.audio_format);
      this.setRadio('mp3Bitrate', s.mp3_bitrate); this.setRadio('videoHeight', s.video_height);
      this.el('embed').checked = !!s.embed;
      this.el('singleOnly').checked = !!s.single_only;
      this.el('force').checked = !!s.force;
      this.el('destDir').textContent = s.download_dir; this.el('destDir').title = s.download_dir;
      this.reflect();
    },
    collect: function () {
      return {
        mode: this.mode(), audio_format: this.radio('audioFormat'), mp3_bitrate: this.radio('mp3Bitrate'),
        video_height: this.radio('videoHeight'), embed: this.el('embed').checked,
        single_only: this.el('singleOnly').checked, force: this.el('force').checked,
        cookies_browser: S.settings.cookies_browser || ''
      };
    },
    msg: function (text, ok) {
      var m = this.el('formMsg');
      m.hidden = !text; m.textContent = text || '';
      m.className = 'msg' + (ok ? ' ok' : '');
    },
    submit: function (ev) {
      ev.preventDefault();
      var self = form, urls = self.el('urls').value.trim();
      if (!urls) { self.msg(tr('form.pasteOne')); self.el('urls').focus(); return; }
      self.msg('');
      askNotifyPermission();
      var opts = self.collect();
      var btnGo = self.el('btnGo'); btnGo.disabled = true;
      var payload = {}, k;
      for (k in S.settings) { if (Object.prototype.hasOwnProperty.call(S.settings, k)) { payload[k] = S.settings[k]; } }
      for (k in opts) { if (Object.prototype.hasOwnProperty.call(opts, k)) { payload[k] = opts[k]; } }
      api('POST', '/api/settings', payload).then(function (r) { S.settings = r.settings; }, function () { /* non-blocking */ })
        .then(function () { return api('POST', '/api/jobs', { urls: urls, opts: opts, subscribe: self.el('subscribe').checked ? parseInt(self.el('subHours').value, 10) : undefined, only_new: self.el('subscribe').checked && self.el('onlyNew').checked }); })
        .then(function (r) {
          self.el('urls').value = ''; updateDetect();
          var n = r.created.length;
          toast(tr('toast.added', { n: n }));
          var notes = [];
          if (r.rejected && r.rejected.length) { notes.push(tr('form.ignored', { links: r.rejected.slice(0, 3).join(', ') })); }
          if (r.duplicates && r.duplicates.length) { notes.push(tr('form.dups', { n: r.duplicates.length })); }
          if (notes.length) { self.msg(notes.join(' · ')); }
          pollState();
          if (n === 1) { setTimeout(function () { openJob(r.created[0]); }, 500); }
        })
        .catch(function (e) { self.msg(e.message); })
        .then(function () { btnGo.disabled = false; });
    }
  };

  // ------------------------------------------------------------------ global state
  var stateTimer = null, detailTimer = null, polling = false;

  function setOnline(ok) {
    if (S.online === ok) { return; }
    S.online = ok;
    $('#offline').hidden = ok;
  }

  function pollState() {
    if (polling) { return; }
    polling = true;
    if (stateTimer) { clearTimeout(stateTimer); stateTimer = null; }
    api('GET', '/api/state').then(function (st) { setOnline(true); applyState(st); })
      .catch(function () { setOnline(false); })
      .then(function () { polling = false; stateTimer = setTimeout(pollState, document.hidden ? 5000 : 1500); });
  }

  function applyState(st) {
    S.lastState = st; S.subs = st.subs || []; S.subIntervals = st.sub_intervals || [];
    S.settings = st.settings; S.errmeta = st.errmeta || {};
    if (!S.langInit) {
      S.langInit = true;
      var savedLang = null;
      try { savedLang = localStorage.getItem('ytg-lang'); } catch (e) { savedLang = null; }
      if (!savedLang && st.settings.lang && hasLang(st.settings.lang) && st.settings.lang !== LANG) { setLanguage(st.settings.lang, false); }
    } S.local = !!st.local; S.tools = st.tools || {}; S.android = !!st.android;
    $('#grpAndroidHint').hidden = S.android;
    S.concurrency = st.concurrency; S.browsers = st.browsers || []; S.hasCookies = !!st.has_cookies; S.ytdlp = st.ytdlp;
    S.serverOffset = st.now - Date.now() / 1000;
    if (S.version && st.version && S.version !== st.version) { window.location.reload(); return; }   // the program was updated and restarted: load its new page
    S.update = st.update || {}; S.nativeNotify = !!st.native_notify; S.version = st.version;
    if (!S.formInit) { S.formInit = true; form.fill(st.settings); updateDetect(); }
    else { $('#destDir').textContent = st.settings.download_dir; $('#destDir').title = st.settings.download_dir; }
    var warn = [];
    if (!S.tools.ffmpeg) { warn.push(tr('warn.ffmpeg')); }
    $('#toolsWarn').hidden = !warn.length; $('#toolsWarn').textContent = warn.join(' ');

    var thr = st.throttle || {}, tb = $('#throttle');
    if (thr.until && thr.until > st.now) {
      tb.hidden = false;
      tb.textContent = tr('throttle', { reason: thr.reason || tr('throttle.limit'), s: Math.ceil(thr.until - st.now) });
    } else { tb.hidden = true; }

    S.jobs = st.jobs;
    var a = 0, p = 0, speed = 0, done = 0, tot = 0, running = false, finishedJobs = 0, j, i;
    for (i = 0; i < S.jobs.length; i++) {
      j = S.jobs[i];
      a += j.counts.a; p += j.counts.p; speed += j.speed;
      if ((j.status === 'running' || j.status === 'enumerating') && !j.paused) {
        running = true; done += j.processed; tot += j.total;
      }
      if (j.status === 'done' || j.status === 'cancelled') { finishedJobs++; }
    }
    renderMeter(a, p, speed);
    renderJobs();
    renderSubs();
    renderUpdate();
    trackFinished();
    var pct = tot ? Math.floor(done / tot * 100) : 0;
    document.title = running && tot ? '(' + pct + '%) YT Grabber' : 'YT Grabber';
    $('#jobsCount').textContent = S.jobs.length ? tr('items.count', { n: S.jobs.length }) : '';
    $('#btnClearDone').hidden = finishedJobs === 0;
    $('#empty').hidden = S.jobs.length > 0;
  }

  // ------------------------------------------------------------------ new version banner, "download finished" notices
  function renderUpdate() {
    var u = S.update || {}, inst = u.install || {}, hidden = null, show, text;
    var busy = inst.state === 'downloading' || inst.state === 'installing';
    try { hidden = localStorage.getItem('ytg-update-hidden'); } catch (e) { hidden = null; }
    show = !!(u.newer && S.settings.check_updates !== false && (hidden !== u.latest || busy || inst.state === 'error'));
    $('#updateBanner').hidden = !show;
    if (show) {
      if (inst.state === 'downloading') { text = tr('update.downloading', { pct: Math.floor((inst.pct || 0) / 10) * 10 }); }   // in steps of 10: no chatter for screen readers
      else if (inst.state === 'installing') { text = tr('update.installing'); }
      else if (inst.state === 'error') { text = tr('update.failed', { msg: inst.error || '' }); }
      else { text = tr('update.available', { v: u.latest }); }
      $('#updateText').textContent = text;
      if (/^https:\/\//.test(u.url || '')) { $('#updateLink').href = u.url; }
      $('#updateLink').hidden = busy;
      $('#updateInstall').hidden = !u.can_install || busy;
      $('#updateHide').hidden = busy;
      if (inst.state !== S.updState && (inst.state === 'installing' || inst.state === 'error')) { announce(text); }
    }
    S.updState = inst.state;
  }

  function notifyDone(j) {
    if (S.nativeNotify || S.settings.notify_done === false || !j.counts || (!j.counts.d && !j.counts.e)) { return; }
    if (!window.Notification || Notification.permission !== 'granted') { return; }
    if (!document.hidden && document.hasFocus()) { return; }   // the page is in front: the card already shows it
    try {
      var n = new Notification(tr('notify.title'), {
        body: tr(j.counts.e ? 'notify.err' : 'notify.ok', { title: j.title, n: j.counts.d, e: j.counts.e }),
        icon: 'icons/icon-192.png', tag: 'ytg-' + j.id
      });
      n.onclick = function () { window.focus(); openJob(j.id); n.close(); };
    } catch (e) { /* notifications not available here */ }
  }

  function trackFinished() {
    var seen = S.seen || {}, first = !S.seen, i, j, now = {};
    for (i = 0; i < S.jobs.length; i++) {
      j = S.jobs[i]; now[j.id] = j.status;
      if (!first && j.status === 'done' && (seen[j.id] === 'running' || seen[j.id] === 'enumerating')) {
        notifyDone(j);
        if (j.counts && (j.counts.d || j.counts.e)) { announce(tr(j.counts.e ? 'notify.err' : 'notify.ok', { title: j.title, n: j.counts.d, e: j.counts.e })); }   // for screen readers, whatever the notification settings
      } else if (!first && j.status === 'error' && (seen[j.id] === 'running' || seen[j.id] === 'enumerating') && j.message) {
        announce(j.title + ': ' + j.message);
      }
    }
    S.seen = now;
  }

  function askNotifyPermission() {
    if (S.android || S.nativeNotify || S.settings.notify_done === false) { return; }
    if (window.Notification && Notification.permission === 'default') {
      try { Notification.requestPermission(); } catch (e) { /* ignored */ }
    }
  }

  function showUpdateInfo() {
    var u = S.update || {}, el = $('#updateInfo');
    if (u.error && !u.latest) { el.textContent = tr('set.updateFail', { msg: u.error }); }
    else if (u.newer) { el.textContent = tr('set.updateNewer', { v: u.latest }); }
    else if (u.latest) { el.textContent = tr('set.upToDate', { v: S.version }); }
    else { el.textContent = ''; }
  }

  function renderMeter(a, p, speed) {
    var max = S.concurrency, dots = $('#meterDots');
    if (dots.childNodes.length !== max) {
      dots.innerHTML = '';
      for (var i = 0; i < max; i++) { dots.appendChild(document.createElement('i')); }
    }
    for (var k = 0; k < dots.childNodes.length; k++) { dots.childNodes[k].className = k < a ? 'on' : ''; }
    $('#meterN').textContent = a; $('#meterMax').textContent = max;
    var sp = $('#speedPill');
    if (speed > 0 || p > 0) {
      sp.hidden = false;
      sp.textContent = (speed > 0 ? fmtBytes(speed) + '/s' : '') + (speed > 0 && p > 0 ? ' · ' : '') + (p > 0 ? tr('speed.converting', { n: p }) : '');
    } else { sp.hidden = true; }
  }

  // ------------------------------------------------------------------ job cards
  function badge(j) {
    if (j.status === 'error') { return '<span class="badge bad">' + esc(tr('badge.error')) + '</span>'; }
    if (j.status === 'cancelled') { return '<span class="badge">' + esc(tr('badge.cancelled')) + '</span>'; }
    if (j.status === 'done') {
      return j.counts.e ? '<span class="badge bad">' + esc(tr('badge.completedErr')) + '</span>' : '<span class="badge done">' + esc(tr('badge.completed')) + '</span>';
    }
    if (j.paused) { return '<span class="badge pause">' + esc(j.interrupted ? tr('badge.interrupted') : tr('badge.paused')) + '</span>'; }
    if (j.status === 'enumerating') { return '<span class="badge run">' + esc(tr('badge.reading')) + '</span>'; }
    return '<span class="badge run">' + esc(tr('badge.running')) + '</span>';
  }

  function errNums(j) {
    var ids = j.err_idx || [], w = j.pad || Math.max(2, String(j.total).length), out = [];
    for (var i = 0; i < ids.length && i < 60; i++) { out.push('#' + padNum(ids[i], w)); }
    var rest = j.counts.e - Math.min(ids.length, 60);
    return '<b>' + out.join(' ') + '</b>' + (rest > 0 ? esc(tr('nums.more', { n: rest })) : '');
  }

  function ringHtml(j) {
    var T = j.total || 0, pct = T ? Math.floor(j.processed / T * 100) : 0, r = 25, c = 2 * Math.PI * r;
    var cls = j.status === 'done' ? (j.counts.e ? 'bad' : 'ok') : (j.status === 'running' || j.status === 'enumerating') && !j.paused ? 'run' : '';
    return '<svg class="ring" viewBox="0 0 62 62" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + pct + '" aria-valuetext="' + esc(tr('ring.label', { pct: pct })) + '" aria-label="' + esc(tr('a11y.progress')) + '"><circle class="rt" cx="31" cy="31" r="' + r + '"/>' +
      '<circle class="rv ' + cls + '" cx="31" cy="31" r="' + r + '" stroke-dasharray="' + c.toFixed(1) + '" stroke-dashoffset="' + (c * (1 - pct / 100)).toFixed(1) + '" transform="rotate(-90 31 31)"/>' +
      '<text x="31" y="36">' + pct + '%</text></svg>';
  }

  function tile(cls, n, label) { return '<div class="stat ' + cls + (n ? '' : ' zero') + '"><b>' + n + '</b><span>' + label + '</span></div>'; }

  function statsHtml(j) {
    var c = j.counts;
    return tile('ok', c.d, esc(tr('stat.completed'))) + (c.s ? tile('ok', c.s, esc(tr('stat.present'))) : '') + tile('info', c.a, esc(tr('stat.downloading'))) + tile('warn', c.p, esc(tr('stat.converting'))) +
      tile('', c.q, esc(tr('stat.queued'))) + (c.c ? tile('', c.c, esc(tr('stat.cancelled'))) : '') + (c.k ? tile('', c.k, esc(tr('stat.skipped'))) : '') +
      (c.e ? '<button type="button" class="stat err" data-act="goerr" data-id="' + j.id + '" title="' + esc(tr('stat.errorsTitle')) + '"><b>' + c.e + '</b><span>' + esc(tr('stat.errorsShow')) + '</span></button>' : tile('err', 0, esc(tr('stat.errors'))));
  }

  function liveHtml(j) {
    if (!((j.status === 'running' || j.status === 'enumerating') && !j.paused)) { return ''; }
    var h = '';
    if (j.speed > 0) { h += '<span>' + esc(tr('live.speed')) + ' <b>' + fmtBytes(j.speed) + '/s</b></span>'; }
    if (j.eta) { h += '<span>' + tr('live.eta', { t: '<b>' + fmtEta(j.eta) + '</b>' }) + '</span>'; }
    if (j.status === 'enumerating' && j.declared) { h += '<span>' + tr('live.read', { n: '<b>' + j.total + '</b>', d: j.declared }) + '</span>'; }
    return h;
  }

  function alertsHtml(j) {
    var c = j.counts, h = '';
    if (j.status === 'error' && j.message) { h += '<div class="alert">' + esc(j.message) + '</div>'; }
    if (j.warning) { h += '<div class="alert warn">' + esc(j.warning) + '</div>'; }
    if (j.status === 'done') {
      var okN = c.d + c.s;
      h += '<div class="alert ' + (c.e ? '' : 'ok') + '">' + (c.e
        ? tr('alert.finishedErr', { ok: okN, e: c.e, nums: errNums(j) })
        : (okN || !c.k ? tr('alert.finishedOk', { n: okN }) : tr('alert.skipped', { n: c.k }))) + '</div>';
    } else if (c.e && (j.err_idx || []).length) {
      h += '<div class="alert">' + tr('alert.errorsSoFar', { nums: errNums(j) }) + '</div>';
    }
    return h;
  }

  function actionsHtml(j) {
    var c = j.counts, id = j.id, h = '';
    var live = j.status === 'running' || j.status === 'enumerating';
    if (live && j.paused) { h += btn('resume', id, esc(tr('act.resume')), IC.play, 'solid'); }
    if (live && !j.paused) { h += btn('pause', id, esc(tr('act.pause')), IC.pause); }
    if (j.status === 'cancelled' || j.status === 'error') { h += btn('resume', id, esc(tr('act.resume')), IC.play, 'solid'); }
    if (c.e && !live) { h += btn('retry_failed', id, esc(tr('act.retryErrors', { n: c.e })), IC.retry, 'solid'); }
    h += btn('toggle', id, esc(S.openId === id ? tr('act.closeList') : tr('act.openList')), IC.list, '', ' aria-expanded="' + (S.openId === id) + '" aria-controls="jd-' + id + '"');
    if (live) { h += btn('cancel', id, esc(tr('act.cancel')), IC.stop, 'danger'); }
    if (S.local && !S.android && j.dir) { h += btn('open_folder', id, esc(tr('act.folder')), IC.folder); }
    if (c.d + c.s > 0 && j.kind !== 'single') { h += '<a class="btn sm" href="/api/jobs/' + id + '/playlist.m3u8" download>' + IC.m3u + esc(tr('act.m3u')) + '</a>'; }
    if (c.d + c.s > 0 && !live) { h += btn('redownload', id, esc(tr('act.redownload')), IC.retry); }
    h += btn('remove', id, esc(tr('act.remove')), IC.trash, 'ghost');
    return h;
  }

  function makeCard(j) {
    var el = document.createElement('article');
    el.className = 'job'; el.setAttribute('data-id', j.id);
    el.innerHTML =
      '<div class="jbody"><div class="jmain">' +
      '<div class="jcover" data-act="toggle" data-id="' + j.id + '" aria-hidden="true"><span class="jicon"></span><img alt="" referrerpolicy="no-referrer"></div>' +
      '<div class="jinfo"><h3 class="jtitle"><button type="button" class="jtitle-btn" id="jt-' + j.id + '" data-act="toggle" data-id="' + j.id + '" aria-expanded="false" aria-controls="jd-' + j.id + '" dir="auto"></button></h3><div class="jmeta"></div></div>' +
      '<div class="jring"></div></div>' +
      '<div class="bar" aria-hidden="true"></div><div class="stats"></div><div class="jlive"></div><div class="jalerts"></div><div class="jact"></div></div>' +
      '<div class="jdetail" id="jd-' + j.id + '" role="region" aria-labelledby="jt-' + j.id + '" hidden></div>';
    el.setAttribute('aria-labelledby', 'jt-' + j.id);
    var body = el.firstChild, main = body.firstChild, img = main.firstChild.lastChild;
    var card = {
      el: el, err: false, cover: null, img: img, icon: main.firstChild.firstChild, title: main.children[1].firstChild.firstChild, meta: main.children[1].lastChild,
      ring: main.children[2], bar: body.children[1], stats: body.children[2], live: body.children[3], alerts: body.children[4], act: body.children[5],
      detail: el.lastChild
    };
    img.onload = function () { img.style.display = 'block'; };
    img.onerror = function () { img.style.display = 'none'; };
    return card;
  }

  function updateCard(card, j) {
    var c = j.counts, T = j.total || 0;
    var w = function (n) { return T ? (n / T * 100).toFixed(2) : 0; };
    if (card.title._t !== j.title) { card.title._t = j.title; card.title.textContent = j.title; }
    card.title.setAttribute('aria-expanded', S.openId === j.id ? 'true' : 'false');
    var sub = [j.kind === 'single' ? tr('job.single') : tr('job.playlist'), tr('items.count', { n: T })];
    setH(card.meta, badge(j) + '<span>' + esc(sub.join(' · ')) + '</span>' + (j.dir ? '<span class="path" title="' + esc(j.dir) + '">' + esc(j.dir) + '</span>' : '') + '<span>' + fmtDate(j.created) + '</span>');
    setH(card.ring, ringHtml(j));
    setH(card.bar, '<i class="g" style="width:' + w(c.d + c.s) + '%"></i><i class="k" style="width:' + w(c.k) + '%"></i><i class="a"style="width:' + w(c.p) + '%"></i><i class="b" style="width:' + w(c.a) + '%"></i><i class="r" style="width:' + w(c.e) + '%"></i>');
    setH(card.stats, statsHtml(j));
    var lv = liveHtml(j); setH(card.live, lv); card.live.style.display = lv ? '' : 'none';
    setH(card.alerts, alertsHtml(j));
    setH(card.act, actionsHtml(j));
    setH(card.icon, j.kind === 'single' ? IC.video : IC.stack);
    if (j.cover !== card.cover) {
      card.cover = j.cover;
      if (j.cover) { card.img.style.display = 'none'; card.img.src = 'https://i.ytimg.com/vi/' + encodeURIComponent(j.cover) + '/mqdefault.jpg'; }
      else { card.img.style.display = 'none'; card.img.removeAttribute('src'); }
    }
    var hasErr = c.e > 0;
    if (hasErr !== card.err) { card.err = hasErr; card.el.className = 'job' + (hasErr ? ' has-err' : ''); }
  }

  function renderJobs() {
    var box = $('#jobs'), jobs = S.jobs.slice().reverse(), seen = {}, i, j, card, lostFocus = false;
    for (i = 0; i < jobs.length; i++) {
      j = jobs[i]; seen[j.id] = true; card = S.cards[j.id];
      if (!card) { card = S.cards[j.id] = makeCard(j); }
      updateCard(card, j);
      if (box.children[i] !== card.el) { box.insertBefore(card.el, box.children[i] || null); }
    }
    for (var id in S.cards) {
      if (Object.prototype.hasOwnProperty.call(S.cards, id) && !seen[id]) {
        if (S.cards[id].el.contains(document.activeElement)) { lostFocus = true; }
        if (S.cards[id].el.parentNode) { S.cards[id].el.parentNode.removeChild(S.cards[id].el); }
        delete S.cards[id];
        if (S.openId === id) { closeDetail(); }
      }
    }
    if (lostFocus) { $('#jobsTitle').focus(); }   // the card that had the focus is gone: do not drop the keyboard user at the top of the page
  }

  // ------------------------------------------------------------------ detail with virtual list
  function closeDetail() {
    if (S.openId && S.cards[S.openId]) {
      var cd = S.cards[S.openId];
      if (cd.detail.contains(document.activeElement)) { cd.title.focus(); }   // the focus was inside the list that is closing
      cd.detail.hidden = true; cd.detail.innerHTML = '';
    }
    S.openId = null; S.detail = null;
    if (detailTimer) { clearTimeout(detailTimer); detailTimer = null; }
  }

  function openJob(id, tab) {
    if (!S.cards[id]) { return; }
    if (S.openId === id && !tab) { closeDetail(); renderJobs(); return; }
    var wasOpen = S.openId === id;
    if (!wasOpen) {
      closeDetail();
      S.openId = id;
      var el = S.cards[id].detail;
      el.hidden = false;
      el.innerHTML =
        '<div class="errpanel" hidden></div>' +
        '<div class="tabs"><div class="tabbtns" role="group" aria-label="' + esc(tr('detail.filters')) + '"></div><input class="search" type="search" placeholder="' + esc(tr('detail.search')) + '" aria-label="' + esc(tr('detail.searchLabel')) + '"></div>' +
        '<div class="vbox" role="region" tabindex="0" aria-label="' + esc(tr('list.label')) + '" aria-describedby="lh-' + id + '"><div class="vspacer" role="list"></div><div class="vempty" hidden></div></div>' +
        '<p class="sr-only" id="lh-' + id + '">' + esc(tr('list.help')) + '</p>';
      S.detail = {
        id: id, items: [], seq: 0, tab: 'all', q: '', kind: '', view: [], summary: null, rowEls: {}, busy: false,
        panel: el.children[0], tabsEl: el.children[1].firstChild, box: el.children[2], spacer: el.children[2].children[0],
        empty: el.children[2].children[1], tabsHtml: '', panelHtml: ''
      };
      var raf = 0, d = S.detail, sInp = el.children[1].lastChild;
      sInp.addEventListener('input', function () { d.q = sInp.value; d.box.scrollTop = 0; rebuildView(d); renderVList(); });
      d.box.addEventListener('keydown', function (ev) { listKey(d, ev); });
      d.box.addEventListener('scroll', function () {
        if (raf) { return; }
        raf = (window.requestAnimationFrame || window.setTimeout)(function () { raf = 0; renderVList(); });
      });
      renderJobs();
    }
    if (tab) { S.detail.tab = tab; S.detail.box.scrollTop = 0; }
    fetchDetail();
    if (S.cards[id] && S.cards[id].el.scrollIntoView) { S.cards[id].el.scrollIntoView({ block: 'nearest' }); }
  }

  // Arrow keys move between the items of the list (the list takes one Tab stop, like a list box); Tab then goes to the buttons of the
  // current item. Home, End, Page Up and Page Down jump. Only the rows near the screen exist, so the list is scrolled first.
  function focusItem(d, pos) {
    var it = d.items[d.view[pos]], top = pos * ROW, h = d.box.clientHeight, r;
    if (!it) { return; }
    d.cur = it.i;
    if (top < d.box.scrollTop) { d.box.scrollTop = top; }
    else if (top + ROW > d.box.scrollTop + h) { d.box.scrollTop = top + ROW - h; }
    renderVList();
    r = d.rowEls[it.i];
    if (r) { r.el.focus(); }
  }
  function listKey(d, ev) {
    var k = ev.key, n = d.view.length, row, cur = -1, page, pos;
    if (!n || ev.altKey || ev.ctrlKey || ev.metaKey) { return; }
    if (k !== 'ArrowDown' && k !== 'ArrowUp' && k !== 'Home' && k !== 'End' && k !== 'PageDown' && k !== 'PageUp') { return; }
    row = ev.target && ev.target.closest ? ev.target.closest('.row') : null;
    if (row) { cur = d.view.indexOf(parseInt(row.getAttribute('aria-posinset'), 10) - 1); }
    page = Math.max(1, Math.floor((d.box.clientHeight || ROW) / ROW) - 1);
    if (k === 'ArrowDown') { pos = cur < 0 ? 0 : Math.min(n - 1, cur + 1); }
    else if (k === 'ArrowUp') { pos = cur < 0 ? 0 : Math.max(0, cur - 1); }
    else if (k === 'Home') { pos = 0; }
    else if (k === 'End') { pos = n - 1; }
    else if (k === 'PageDown') { pos = cur < 0 ? Math.min(n - 1, page) : Math.min(n - 1, cur + page); }
    else { pos = cur < 0 ? 0 : Math.max(0, cur - page); }
    ev.preventDefault();
    focusItem(d, pos);
  }

  function fetchDetail() {
    var d = S.detail;
    if (!d || d.busy) { return; }
    d.busy = true;
    if (detailTimer) { clearTimeout(detailTimer); detailTimer = null; }
    api('GET', '/api/jobs/' + d.id + '?since=' + d.seq).then(function (res) {
      if (S.detail !== d) { return; }
      setOnline(true);
      for (var i = 0; i < res.items.length; i++) { d.items[res.items[i].i - 1] = res.items[i]; }
      d.seq = res.seq; d.summary = res;
      renderDetail();
    }).catch(function (e) {
      if (S.detail === d && /not found/i.test(e.message)) { closeDetail(); renderJobs(); }
    }).then(function () {
      d.busy = false;
      if (S.detail === d) { detailTimer = setTimeout(fetchDetail, document.hidden ? 5000 : 1000); }
    });
  }

  function matchTab(it, tab) {
    switch (tab) {
      case 'all': return true;
      case 'd': return it.s === 'd' || it.s === 's';
      default: return it.s === tab;
    }
  }

  function rebuildView(d) {
    var q = d.q.toLowerCase(), v = [], i, it;
    var qn = /^#?\d+$/.test(q) ? parseInt(q.replace('#', ''), 10) : null;
    for (i = 0; i < d.items.length; i++) {
      it = d.items[i];
      if (!it || !matchTab(it, d.tab)) { continue; }
      if (d.kind && it.ek !== d.kind) { continue; }
      if (q) {
        if (qn !== null) { if (it.i !== qn) { continue; } }
        else if ((it.t || '').toLowerCase().indexOf(q) < 0 && (it.v || '').toLowerCase().indexOf(q) < 0 && (it.ek ? errLabel(it.ek).toLowerCase().indexOf(q) < 0 : true)) { continue; }
      }
      v.push(i);
    }
    d.view = v;
  }

  function renderDetail() {
    var d = S.detail, s = d.summary;
    if (!d || !s) { return; }
    var c = s.counts, pad = s.pad || Math.max(2, String(s.total).length);

    var errs = [], byKind = {}, i, it;
    if (c.e) {
      for (i = 0; i < d.items.length; i++) {
        it = d.items[i];
        if (it && it.s === 'e') { errs.push(it); byKind[it.ek] = (byKind[it.ek] || 0) + 1; }
      }
    }
    var ph = '';
    if (c.e) {
      ph = '<h4>' + esc(tr('err.notdl', { n: c.e })) + '</h4><div class="errgroups">';
      for (var k in byKind) {
        if (Object.prototype.hasOwnProperty.call(byKind, k)) {
          ph += '<button type="button" class="errgroup" data-act="errkind" data-kind="' + esc(k) + '" title="' + esc(errHint(k)) + '">' + esc(errLabel(k)) + ': ' + byKind[k] + '</button>';
        }
      }
      ph += '</div><div class="errnums">';
      var nums = [];
      for (i = 0; i < errs.length && i < 400; i++) { nums.push('#' + padNum(errs[i].i, pad)); }
      ph += esc(nums.join(' ')) + (errs.length > 400 ? ' ...' : '') + '</div>' +
        '<div class="jact">' + btn('retry_failed', d.id, esc(tr('detail.retryAll')), IC.retry, 'solid') +
        btn('copyerrs', d.id, esc(tr('detail.copy')), IC.list) +
        '<a class="btn sm" href="/api/jobs/' + d.id + '/errors.txt" download>' + IC.save + esc(tr('detail.downloadList')) + '</a></div>';
    }
    if (ph !== d.panelHtml) { d.panelHtml = ph; d.panel.innerHTML = ph; }
    d.panel.hidden = !c.e;

    var th = '', tk, n;
    for (i = 0; i < TABS.length; i++) {
      tk = TABS[i];
      n = tk === 'all' ? s.total : tk === 'd' ? c.d + c.s : c[tk];
      if (tk === 'c' && !n) { continue; }
      th += '<button type="button" class="tab t-' + tk + (d.tab === tk ? ' on' : '') + '" data-act="tab" data-tab="' + tk + '" aria-pressed="' + (d.tab === tk) + '">' + esc(tr('tab.' + tk)) + '<b>' + n + '</b></button>';
    }
    if (d.kind) { th += '<button type="button" class="tab on" data-act="clearkind">' + esc(tr('detail.filter', { k: errLabel(d.kind) })) + ' ✕</button>'; }
    if (th !== d.tabsHtml) { d.tabsHtml = th; d.tabsEl.innerHTML = th; }
    rebuildView(d);
    renderVList();
  }

  // persistent row: the children are created once and updated only if they change (no thumbnail flicker)
  function makeRow() {
    var el = document.createElement('div');
    el.className = 'row';
    el.setAttribute('role', 'listitem');   // only the rows near the screen exist: the position and the size tell where this one is in the whole list
    el.tabIndex = -1;                      // reached with the arrow keys, not with Tab
    el.innerHTML = '<div class="rthumb"><img alt="" referrerpolicy="no-referrer"></div><div class="rnum"></div>' +
      '<div class="rmain"><div class="rtitle" dir="auto"></div><div class="rsub"></div></div><div class="rside"></div><div class="ract"></div>';
    var r = { el: el, img: el.firstChild.firstChild, num: el.children[1], title: el.children[2].firstChild, sub: el.children[2].lastChild, side: el.children[3], act: el.children[4], k: {} };
    r.img.onload = function () { r.img.style.visibility = 'visible'; };
    r.img.onerror = function () { r.img.style.visibility = 'hidden'; };
    return r;
  }

  function updateRow(r, it, pad, jid, top, total, cur) {
    var k = r.k, link = it.v ? 'https://www.youtube.com/watch?v=' + encodeURIComponent(it.v) : '';
    var title = it.t || (it.v ? tr('row.video', { id: it.v }) : tr('row.reading'));
    var sub = '', side = '', act = '', tip = '';
    switch (it.s) {
      case 'a':
        sub = esc(stageText(it.st)) + (it.eta != null && it.eta > 0 ? ' · ' + esc(tr('row.left', { t: fmtEta(it.eta) })) : '');
        side = '<div class="st info">' + Math.floor(it.p) + '%</div><div class="pbar"><i style="width:' + it.p + '%"></i></div>' +
          [it.sp ? fmtBytes(it.sp) + '/s' : '', it.sz ? fmtBytes(it.sz) : ''].filter(Boolean).join(' · ');
        break;
      case 'p':
        sub = esc(it.st ? stageText(it.st) : tr('row.converting'));
        side = '<div class="st warn">' + esc(tr('row.converting')) + '</div><div class="pbar cv"><i></i></div>';
        break;
      case 'q':
        if (it.rt > 0) {
          sub = esc(tr('row.retryIn', { st: stageText(it.st), s: it.rt })) + (it.ek ? ' · ' + esc(errLabel(it.ek)) : '');
          side = '<span class="st warn">' + esc(tr('row.retrying')) + '</span>'; tip = it.em || '';
        } else { sub = it.a > 0 ? esc(it.st ? stageText(it.st) : tr('row.waitNew')) : esc(tr('row.waiting')); side = esc(tr('row.queued')); }
        break;
      case 'd':
        sub = esc(it.f || ''); side = '<div class="st ok">' + esc(tr('row.completed')) + '</div>' + (it.sz ? fmtBytes(it.sz) : '');
        // on the phone the file is already in the Download folder: a "Save" button would make a useless copy
        act = S.android ? '' : '<a class="btn sm" href="/api/jobs/' + jid + '/file/' + it.i + '" download title="' + esc(tr('row.saveTitle')) + '" aria-label="' + esc(tr('row.saveTitle')) + '">' + IC.save + '</a>';
        break;
      case 's':
        sub = esc(it.f || ''); side = '<div class="st ok">' + esc(tr('row.present')) + '</div>';
        break;
      case 'e':
        sub = '<b>' + esc(errLabel(it.ek)) + '</b> · ' + esc(trunc(it.em, 160));
        side = '<div class="st bad">' + esc(tr('row.error')) + '</div>' + (it.a > 1 ? esc(tr('row.attempts', { n: it.a })) : '');
        tip = errLabel(it.ek) + '\n' + errHint(it.ek) + '\n\n' + (it.em || '');
        act = '<button type="button" class="btn sm" data-act="retry_item" data-id="' + jid + '" data-idx="' + it.i + '" title="' + esc(tr('row.retryTitle')) + '" aria-label="' + esc(tr('row.retryTitle')) + '">' + IC.retry + '</button>' +
          (link ? '<a class="btn sm" href="' + link + '" target="_blank" rel="noopener noreferrer" title="' + esc(tr('row.openYT')) + '" aria-label="' + esc(tr('row.openYT') + ' ' + tr('a11y.newTab')) + '">' + IC.open + '</a>' : '');
        break;
      case 'c':
        sub = esc(tr('row.cancelled')); side = esc(tr('row.cancelled'));
        break;
      case 'k':
        sub = esc(tr('row.skippedWhy')); side = esc(tr('row.skipped'));
        break;
    }
    if (k.top !== top) { k.top = top; r.el.style.top = top + 'px'; }
    var cls = 'row s-' + it.s;
    if (k.cls !== cls) { k.cls = cls; r.el.className = cls; }
    var src = it.v ? 'https://i.ytimg.com/vi/' + encodeURIComponent(it.v) + '/mqdefault.jpg' : '';
    if (k.src !== src) {
      k.src = src;
      if (src) { r.img.style.visibility = 'hidden'; r.img.src = src; } else { r.img.removeAttribute('src'); r.img.style.visibility = 'hidden'; }
    }
    var num = '#' + padNum(it.i, pad);
    if (k.num !== num) { k.num = num; r.num.textContent = num; }
    if (k.title !== title) { k.title = title; r.title.textContent = title; }
    if (k.sub !== sub) { k.sub = sub; r.sub.innerHTML = sub; }
    if (k.side !== side) { k.side = side; r.side.innerHTML = side; }
    if (k.act !== act) { k.act = act; setHtmlKeepFocus(r.act, act); k.tab = null; }
    var pos = it.i + '/' + total;
    if (k.pos !== pos) { k.pos = pos; r.el.setAttribute('aria-posinset', it.i); r.el.setAttribute('aria-setsize', total); }
    // only the buttons of the current item are in the Tab order (otherwise a long list would hold the keyboard for ever)
    var want = cur === it.i ? 0 : -1;
    if (k.tab !== want) { k.tab = want; var bs = r.act.querySelectorAll('a, button'), bi; for (bi = 0; bi < bs.length; bi++) { bs[bi].tabIndex = want; } }
    var tt = tip || title;
    if (k.tip !== tt) { k.tip = tt; r.el.title = tt; }
  }

  function renderVList() {
    var d = S.detail;
    if (!d) { return; }
    var n = d.view.length, s = d.summary || { pad: 0, total: 0 };
    var pad = s.pad || Math.max(2, String(s.total).length);
    d.spacer.style.height = (n * ROW) + 'px';
    d.empty.hidden = n > 0;
    if (!n) { d.empty.textContent = d.items.length === 0 ? tr('list.reading') : tr('list.none'); }
    var st = d.box.scrollTop, h = d.box.clientHeight || 400;
    var first = Math.max(0, Math.floor(st / ROW) - 6), last = Math.min(n, Math.ceil((st + h) / ROW) + 6), need = {}, k, it, key, r;
    for (k = first; k < last; k++) {
      it = d.items[d.view[k]]; key = it.i; need[key] = true; r = d.rowEls[key];
      if (!r) { r = d.rowEls[key] = makeRow(); d.spacer.appendChild(r.el); }
      updateRow(r, it, pad, d.id, k * ROW, s.total, d.cur);
    }
    for (key in d.rowEls) {
      if (Object.prototype.hasOwnProperty.call(d.rowEls, key) && !need[key]) {
        if (d.rowEls[key].el.parentNode) { d.rowEls[key].el.parentNode.removeChild(d.rowEls[key].el); }
        delete d.rowEls[key];
      }
    }
  }

  // ------------------------------------------------------------------ actions
  function jobAction(id, action, ids, okMsg) {
    var body = { action: action };
    if (ids) { body.ids = ids; }
    return api('POST', '/api/jobs/' + id + '/action', body).then(function () {
      if (okMsg) { toast(okMsg); }
      pollState();
      if (S.detail && S.detail.id === id) { S.detail.seq = 0; fetchDetail(); }
    }).catch(function (e) { toast(e.message, true); });
  }

  function clearFinished() {
    var ids = [], i, j;
    for (i = 0; i < S.jobs.length; i++) { j = S.jobs[i]; if (j.status === 'done' || j.status === 'cancelled') { ids.push(j.id); } }
    if (!ids.length) { return; }
    var chain = Promise.resolve();
    ids.forEach(function (id) { chain = chain.then(function () { return api('POST', '/api/jobs/' + id + '/action', { action: 'remove' }); }); });
    chain.then(function () { toast(tr('toast.removed', { n: ids.length })); pollState(); })
      .catch(function (e) { toast(e.message, true); });
  }

  function onClick(ev) {
    var el = findAct(ev.target, document.body);
    if (!el) { return; }
    var act = el.getAttribute('data-act'), id = el.getAttribute('data-id'), d = S.detail;
    switch (act) {
      case 'toggle': openJob(id); break;
      case 'goerr': openJob(id, 'e'); break;
      case 'pause': jobAction(id, 'pause'); break;
      case 'resume': jobAction(id, 'resume'); break;
      case 'cancel': if (window.confirm(tr('confirm.cancel'))) { jobAction(id, 'cancel'); } break;
      case 'retry_failed': jobAction(id, 'retry_failed', null, tr('toast.retryingErrors')); break;
      case 'retry_item': jobAction(id, 'retry_failed', [parseInt(el.getAttribute('data-idx'), 10)], tr('toast.retryingItem')); break;
      case 'redownload': if (window.confirm(tr('confirm.redownload'))) { jobAction(id, 'redownload', null, tr('toast.redownloading')); } break;
      case 'open_folder': jobAction(id, 'open_folder'); break;
      case 'remove': if (window.confirm(tr('confirm.remove'))) { jobAction(id, 'remove'); } break;
      case 'tab': if (d) { d.tab = el.getAttribute('data-tab'); d.box.scrollTop = 0; renderDetail(); } break;
      case 'errkind': if (d) { d.kind = el.getAttribute('data-kind'); d.tab = 'e'; d.box.scrollTop = 0; renderDetail(); } break;
      case 'clearkind': if (d) { d.kind = ''; renderDetail(); } break;
      case 'copyerrs': if (d && d.summary) { copyText(errorsText(d)); } break;
      case 'sub_check': subAction(id, { action: 'check' }, tr('toast.subChecking')); break;
      case 'sub_toggle': subAction(id, { action: 'toggle' }); break;
      case 'sub_remove': if (window.confirm(tr('subs.confirmRemove'))) { subAction(id, { action: 'remove' }, tr('toast.subRemoved')); } break;
    }
  }

  function errorsText(d) {
    var s = d.summary, pad = s.pad || Math.max(2, String(s.total).length), lines = [s.title, s.url, ''], i, it;
    for (i = 0; i < d.items.length; i++) {
      it = d.items[i];
      if (it && it.s === 'e') {
        lines.push('#' + padNum(it.i, pad) + ' | ' + (it.t || tr('unknownTitle')) + ' | ' + errLabel(it.ek) + ' | ' + (it.v ? 'https://www.youtube.com/watch?v=' + it.v : ''));
      }
    }
    return lines.join('\n');
  }

  // ------------------------------------------------------------------ settings
  
  // ------------------------------------------------------------------ subscriptions
  function fmtWhen(ts) {
    if (!ts) { return tr('subs.never'); }
    var d = new Date(ts * 1000), now = new Date(), hm = padNum(d.getHours(), 2) + ':' + padNum(d.getMinutes(), 2);
    if (d.toDateString() === now.toDateString()) { return tr('date.today', { t: hm }); }
    return d.getDate() + '/' + (d.getMonth() + 1) + ' ' + hm;
  }
  function subHtml(s) {
    var h = '<div class="sub' + (s.enabled ? '' : ' off') + '" role="group" aria-label="' + esc(s.title || s.url) + '"><div class="sub-main"><b class="sub-title" dir="auto">' + esc(s.title || s.url) + '</b>';
    var st = s.status === 'checking' ? tr('subs.checking') : s.status === 'error' ? tr('subs.error') : s.status === 'errors' ? tr('subs.errors') : '';
    var res = s.last_new == null ? '' : (s.last_new ? tr('subs.new', { n: s.last_new }) : tr('subs.nothingNew'));
    h += '<div class="sub-meta">' + (s.enabled ? '' : '<span class="badge pause">' + esc(tr('subs.pausedTag')) + '</span>') +
      (s.only_new ? '<span class="badge done">' + esc(tr('subs.onlyNew')) + '</span>' : '') +
      (st ? '<span class="badge ' + (s.status === 'checking' ? 'run' : 'bad') + '">' + esc(st) + '</span>' : '') +
      '<span>' + esc(tr('subs.last', { t: fmtWhen(s.last_check) })) + (res ? ' · ' + esc(res) : '') + '</span>' +
      (s.enabled ? '<span>' + esc(tr('subs.next', { t: fmtWhen(s.next_check) })) + '</span>' : '') + '</div>';
    if (s.message) { h += '<div class="sub-msg">' + esc(s.message) + '</div>'; }
    h += '</div><div class="sub-act"><select class="mini-select" data-subint="' + s.id + '" aria-label="' + esc(tr('subs.every')) + '">';
    var i, hrs = S.subIntervals.length ? S.subIntervals : SUB_HOURS;
    for (i = 0; i < hrs.length; i++) { h += '<option value="' + hrs[i] + '"' + (hrs[i] === s.hours ? ' selected' : '') + '>' + esc(tr('every.' + hrs[i])) + '</option>'; }
    h += '</select>' + btn('sub_check', s.id, tr('subs.checkNow'), IC.retry) +
      btn('sub_toggle', s.id, s.enabled ? tr('subs.pause') : tr('subs.resume'), s.enabled ? IC.pause : IC.play) +
      btn('sub_remove', s.id, tr('subs.remove'), IC.trash, 'ghost') + '</div></div>';
    return h;
  }
  function renderSubs() {
    var sec = $('#subsSec'), h = '', i;
    sec.hidden = !S.subs.length;
    for (i = 0; i < S.subs.length; i++) { h += subHtml(S.subs[i]); }
    // do not rebuild the list while one of its drop-down menus is open (it would close under the pointer)
    if (document.activeElement && document.activeElement.getAttribute && document.activeElement.getAttribute('data-subint')) { return; }
    setH($('#subs'), h);
  }
  function subAction(id, body, okMsg) {
    return api('POST', '/api/subs/' + id + '/action', body).then(function () {
      if (okMsg) { toast(okMsg); }
      pollState();
    }).catch(function (e) { toast(e.message, true); });
  }

  function openSettings() {
    var s = S.settings;
    $('#setDir').value = s.download_dir || '';
    var sel = $('#setCookiesBrowser'), html = '<option value="">' + esc(tr('set.none')) + '</option>', i;
    var names = { firefox: 'Firefox', chrome: 'Chrome', edge: 'Edge', brave: 'Brave', opera: 'Opera', vivaldi: 'Vivaldi', chromium: 'Chromium', whale: 'Whale', safari: 'Safari' };
    for (i = 0; i < S.browsers.length; i++) { html += '<option value="' + S.browsers[i] + '">' + (names[S.browsers[i]] || S.browsers[i]) + '</option>'; }
    sel.innerHTML = html; sel.value = s.cookies_browser || '';
    $('#cookiesState').textContent = S.hasCookies ? tr('set.cookiesLoaded') : tr('set.cookiesNone');
    $('#verInfo').textContent = tr('set.ver', { v: S.ytdlp, ff: S.tools.ffmpeg ? tr('set.ok') : tr('set.missing'), js: S.tools.deno ? tr('set.ok') : tr('set.absent'), c: S.concurrency });
    $('#setBrowse').hidden = !S.local || S.android; $('#btnUpdate').hidden = !S.local;
    $('#setMsg').hidden = true; $('#setCookiesFile').value = '';
    $('#setNotify').checked = s.notify_done !== false; $('#setCheckUpdates').checked = s.check_updates !== false;
    var ts = '', zi, cur = getTextSize();
    for (zi = 0; zi < TEXT_SIZES.length; zi++) { ts += '<option value="' + TEXT_SIZES[zi] + '"' + (TEXT_SIZES[zi] === cur ? ' selected' : '') + '>' + esc(tr('text.' + TEXT_SIZES[zi])) + '</option>'; }
    $('#setTextSize').innerHTML = ts;
    $('#notifyHint').hidden = S.nativeNotify;   // the Windows app (tray icon) and the Android app (notification) do it themselves: no browser permission needed
    $('#notifyHint').textContent = (window.Notification && Notification.permission === 'denied') ? tr('set.notifyBlocked') : tr('set.notifyHint');
    showUpdateInfo();
    settingsOpener = document.activeElement;
    $('#settingsOv').hidden = false;
    setBackgroundInert(true);
    $('#setTitle').focus();   // a screen reader reads the name of the dialog, and Tab starts from its first control
  }
  function closeSettings() {
    $('#settingsOv').hidden = true;
    setBackgroundInert(false);
    if (settingsOpener && settingsOpener.focus && document.body.contains(settingsOpener)) { settingsOpener.focus(); }
    settingsOpener = null;
  }
  // While the settings dialog is open nothing behind it can be reached (keyboard, screen reader or pointer).
  var settingsOpener = null;
  function setBackgroundInert(on) {
    var els = document.querySelectorAll('.top, #main, .foot, .skip'), i;
    for (i = 0; i < els.length; i++) {
      if (on) { els[i].setAttribute('inert', ''); els[i].setAttribute('aria-hidden', 'true'); }
      else { els[i].removeAttribute('inert'); els[i].removeAttribute('aria-hidden'); }
    }
  }
  function keepFocusInDialog(ev) {
    var box = $('#settingsOv .modal'), list = box.querySelectorAll('a[href], button, input, select, textarea, [tabindex]'), ok = [], i, first, last;
    for (i = 0; i < list.length; i++) {
      if (!list[i].disabled && list[i].tabIndex >= 0 && list[i].offsetParent !== null) { ok.push(list[i]); }
    }
    if (!ok.length) { return; }
    first = ok[0]; last = ok[ok.length - 1];
    if (ev.shiftKey && (document.activeElement === first || document.activeElement === $('#setTitle'))) { ev.preventDefault(); last.focus(); }
    else if (!ev.shiftKey && document.activeElement === last) { ev.preventDefault(); first.focus(); }
  }
  function setMsg(t, ok) { var m = $('#setMsg'); m.hidden = !t; m.textContent = t || ''; m.className = 'msg' + (ok ? ' ok' : ''); }

  function saveSettings() {
    var payload = {}, k;
    for (k in S.settings) { if (Object.prototype.hasOwnProperty.call(S.settings, k)) { payload[k] = S.settings[k]; } }
    payload.download_dir = $('#setDir').value.trim();
    payload.cookies_browser = $('#setCookiesBrowser').value;
    payload.notify_done = $('#setNotify').checked; payload.check_updates = $('#setCheckUpdates').checked;
    api('POST', '/api/settings', payload).then(function (r) {
      S.settings = r.settings; form.fill(r.settings); closeSettings(); toast(tr('toast.saved'));
    }).catch(function (e) { setMsg(e.message); });
  }

  function waitServer(tries) {
    api('GET', '/api/ping').then(function () { toast(tr('toast.restarted')); window.location.reload(); })
      .catch(function () { if (tries > 0) { setTimeout(function () { waitServer(tries - 1); }, 1500); } else { toast(tr('toast.restartBy'), true); } });
  }

  function init() {
    var lsel = $('#langSel'), lh = '', li;
    for (li = 0; li < LANGS.length; li++) { lh += '<option value="' + LANGS[li][0] + '" lang="' + LANGS[li][0] + '" translate="no">' + LANGS[li][1] + '</option>'; }
    lsel.innerHTML = lh;
    lsel.addEventListener('change', function () { setLanguage(lsel.value, true); });
    $('#subscribe').addEventListener('change', function () { $('#subHours').hidden = !this.checked; $('#onlyNewRow').hidden = !this.checked; });
    $('#subs').addEventListener('change', function (ev) {
      var id = ev.target && ev.target.getAttribute('data-subint');
      if (id) { subAction(id, { action: 'interval', hours: parseInt(ev.target.value, 10) }); ev.target.blur(); }
    });
    applyTheme(getTheme());
    $('#btnTheme').addEventListener('click', cycleTheme);
    document.addEventListener('click', onClick);
    document.addEventListener('keydown', function (ev) {
      if (!$('#settingsOv').hidden) {
        if (ev.key === 'Escape') { closeSettings(); }
        else if (ev.key === 'Tab') { keepFocusInDialog(ev); }
      }
    });
    $('#form').addEventListener('submit', form.submit);
    $('#form').addEventListener('change', function (ev) {
      var n = ev.target && ev.target.name;
      if (n === 'mode' || n === 'audioFormat') { form.reflect(); }
      if (ev.target && ev.target.id === 'singleOnly') { updateDetect(); }
    });
    $('#urls').addEventListener('input', updateDetect);
    $('#urls').addEventListener('keydown', function (ev) { if (ev.key === 'Enter' && (ev.ctrlKey || ev.metaKey)) { form.submit(ev); } });
    $('#btnClear').addEventListener('click', function () { $('#urls').value = ''; updateDetect(); $('#urls').focus(); });
    $('#btnPaste').addEventListener('click', function () {
      var ta = $('#urls');
      if (window.AndroidBridge && window.AndroidBridge.paste) {   // Android app: the WebView cannot read the clipboard by itself
        var t0 = String(window.AndroidBridge.paste() || '').trim();
        if (!t0) { toast(tr('toast.clipEmpty'), true); return; }
        ta.value = (ta.value ? ta.value.replace(/\s+$/, '') + '\n' : '') + t0; updateDetect(); ta.focus();
      } else if (navigator.clipboard && navigator.clipboard.readText) {
        navigator.clipboard.readText().then(function (t) {
          if (!t) { toast(tr('toast.clipEmpty'), true); return; }
          ta.value = (ta.value ? ta.value.replace(/\s+$/, '') + '\n' : '') + t.trim(); updateDetect(); ta.focus();
        }, function () { toast(tr('toast.clipBlocked'), true); ta.focus(); });
      } else { toast(tr('toast.pasteHint'), true); ta.focus(); }
    });
    $('#btnChangeDir').addEventListener('click', function () { openSettings(); setTimeout(function () { $('#setDir').focus(); }, 30); });
    $('#btnClearDone').addEventListener('click', clearFinished);
    $('#btnSettings').addEventListener('click', openSettings);
    $('#setClose').addEventListener('click', closeSettings);
    $('#setCancel').addEventListener('click', closeSettings);
    $('#setSave').addEventListener('click', saveSettings);
    $('#settingsOv').addEventListener('mousedown', function (ev) { if (ev.target === this) { closeSettings(); } });
    $('#setBrowse').addEventListener('click', function () {
      var b = this; b.disabled = true;
      api('POST', '/api/choose-dir', { start: $('#setDir').value }).then(function (r) { if (r.path) { $('#setDir').value = r.path; } })
        .catch(function (e) { setMsg(e.message); }).then(function () { b.disabled = false; });
    });
    $('#setCookiesFile').addEventListener('change', function () {
      var f = this.files && this.files[0];
      if (!f) { return; }
      var rd = new FileReader();
      rd.onload = function () {
        api('POST', '/api/cookies', { text: String(rd.result) }).then(function (r) {
          S.hasCookies = r.has_cookies; $('#cookiesState').textContent = tr('set.cookiesLoaded'); setMsg(tr('set.cookiesLoadedMsg'), true);
        }).catch(function (e) { setMsg(e.message); });
      };
      rd.readAsText(f);
    });
    $('#setCookiesClear').addEventListener('click', function () {
      api('POST', '/api/cookies', { text: '' }).then(function () { S.hasCookies = false; $('#cookiesState').textContent = tr('set.cookiesNone'); setMsg(tr('set.cookiesRemovedMsg'), true); })
        .catch(function (e) { setMsg(e.message); });
    });
    $('#setTextSize').addEventListener('change', function () {   // takes effect at once, so that the result can be seen before closing the window
      var z = parseInt(this.value, 10);
      try { localStorage.setItem('ytg-textsize', String(z)); } catch (e) { /* ignored */ }
      applyTextSize(z);
    });
    $('#setNotify').addEventListener('change', function () { if (this.checked) { S.settings.notify_done = true; askNotifyPermission(); } });
    $('#updateInstall').addEventListener('click', function () {
      if (!window.confirm(tr('update.confirm'))) { return; }
      api('POST', '/api/appupdate/install', {}).then(function () { pollState(); })
        .catch(function (e) { toast(tr('update.failed', { msg: e.message }), true); });
    });
    $('#updateHide').addEventListener('click', function () {
      try { localStorage.setItem('ytg-update-hidden', (S.update || {}).latest || ''); } catch (e) { /* ignored */ }
      $('#updateBanner').hidden = true;
    });
    $('#btnCheckUpdate').addEventListener('click', function () {
      var b = this; b.disabled = true; $('#updateInfo').textContent = tr('subs.checking');
      api('POST', '/api/appupdate', {}).then(function (u) { S.update = u; showUpdateInfo(); renderUpdate(); })
        .catch(function (e) { $('#updateInfo').textContent = tr('set.updateFail', { msg: e.message }); })
        .then(function () { b.disabled = false; });
    });
    $('#btnUpdate').addEventListener('click', function () {
      if (!window.confirm(tr('confirm.update'))) { return; }
      var b = this; b.disabled = true; setMsg(tr('set.updating'), true);
      api('POST', '/api/update', {}).then(function () { setMsg(tr('set.updated'), true); setTimeout(function () { waitServer(40); }, 2500); })
        .catch(function (e) { setMsg(e.message); b.disabled = false; });
    });
    document.addEventListener('visibilitychange', function () { if (!document.hidden) { pollState(); if (S.detail) { fetchDetail(); } } });
    window.addEventListener('resize', function () { calcRow(); if (S.detail) { renderVList(); } });
    // Android app: make the text as large as the system font size asks for (a WebView does not always do it by itself).
    // The page sizes everything in rem, so one change of the root font size enlarges all of it.
    try {
      if (window.AndroidBridge && window.AndroidBridge.fontScale) {
        var fs = parseFloat(window.AndroidBridge.fontScale());
        if (fs > 1.02 && Math.abs(parseFloat(window.getComputedStyle(document.documentElement).fontSize) - 16) < 0.5) {
          document.documentElement.style.fontSize = Math.round(fs * 100) + '%';
        }
      }
    } catch (e) { /* ignored */ }
    calcRow();
    // link received from "Share" (Android app): /?u=<text>
    try {
      var qm = /[?&]u=([^&]*)/.exec(window.location.search);
      if (qm) {
        var shared = decodeURIComponent(qm[1].replace(/\+/g, ' '));
        $('#urls').value = shared; updateDetect();
        if (window.history && window.history.replaceState) { window.history.replaceState(null, '', window.location.pathname); }
      }
    } catch (e) { /* ignore */ }
    setLanguage(detectLang(), false);
    pollState();
  }

  init();
}());
