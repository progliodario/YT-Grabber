/* YT Grabber - user interface. Deliberately "classic" JavaScript (no ?. ?? etc.) so it runs in any browser. */
(function () {
  'use strict';

  var ROW = 64;   // row height: 92 on narrow screens (see CSS), updated in calcRow()
  function calcRow() { ROW = window.innerWidth <= 760 ? 92 : 64; }
  var TABS = [['all', 'All'], ['a', 'Downloading'], ['p', 'Converting'], ['q', 'Queued'], ['d', 'Completed'], ['e', 'Errors'], ['c', 'Cancelled']];

  var S = {
    settings: {}, jobs: [], cards: {}, openId: null, detail: null, errmeta: {}, local: false, tools: {},
    concurrency: 10, browsers: [], hasCookies: false, ytdlp: '', formInit: false, online: true, serverOffset: 0
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
    if (d.toDateString() === now.toDateString()) { return 'today ' + hm; }
    return d.getDate() + '/' + (d.getMonth() + 1) + ' ' + hm;
  }
  function setH(el, html) { if (el._h !== html) { el._h = html; el.innerHTML = html; } }
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
        else { reject(new Error((d && d.error) || ('Error ' + x.status))); }
      };
      x.onerror = function () { reject(new Error('Server not reachable')); };
      x.ontimeout = function () { reject(new Error('The server is not responding')); };
      x.send(body !== undefined ? JSON.stringify(body) : null);
    });
  }
  function toast(msg, bad) {
    var el = document.createElement('div');
    el.className = 'toast' + (bad ? ' bad' : '');
    el.textContent = msg;
    $('#toasts').appendChild(el);
    setTimeout(function () { if (el.parentNode) { el.parentNode.removeChild(el); } }, bad ? 7000 : 3500);
  }
  function copyText(text) {
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      toast(ok ? 'List copied to the clipboard' : 'Copy failed', !ok);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { toast('List copied to the clipboard'); }, fallback);
    } else { fallback(); }
  }
  function findAct(el, stop) {
    while (el && el !== stop) {
      if (el.getAttribute && el.getAttribute('data-act')) { return el; }
      el = el.parentNode;
    }
    return null;
  }
  function errLabel(k) { return (S.errmeta[k] && S.errmeta[k][0]) || 'Error'; }
  function errHint(k) { return (S.errmeta[k] && S.errmeta[k][1]) || ''; }

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
  function btn(act, id, label, icon, cls, extra) {
    return '<button type="button" class="btn sm ' + (cls || '') + '" data-act="' + act + '" data-id="' + id + '"' + (extra || '') + '>' + (icon || '') + label + '</button>';
  }

  // ------------------------------------------------------------------ theme
  var THEMES = ['auto', 'light', 'dark'], THEME_LABEL = { auto: 'automatic', light: 'light', dark: 'dark' };
  function getTheme() { var t = 'auto'; try { t = localStorage.getItem('ytg-theme') || 'auto'; } catch (e) { t = 'auto'; } return THEMES.indexOf(t) < 0 ? 'auto' : t; }
  function applyTheme(t) {
    if (t === 'auto') { document.documentElement.removeAttribute('data-theme'); } else { document.documentElement.setAttribute('data-theme', t); }
    var b = $('#btnTheme');
    b.innerHTML = IC[t]; b.title = 'Theme: ' + THEME_LABEL[t] + ' (click to change)';
    b.setAttribute('aria-label', 'Theme: ' + THEME_LABEL[t]);
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
    if (n.playlist) { h += '<span class="dchip ok">' + n.playlist + (n.playlist === 1 ? ' playlist / album / channel' : ' playlists / albums / channels') + '</span>'; }
    if (n.video) { h += '<span class="dchip ok">' + n.video + (n.video === 1 ? ' video' : ' videos') + '</span>'; }
    if (n.other) { h += '<span class="dchip">' + n.other + (n.other === 1 ? ' other link' : ' other links') + '</span>'; }
    if (n.bad) { h += '<span class="dchip bad">' + n.bad + (n.bad === 1 ? ' not recognized' : ' not recognized') + '</span>'; }
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
        ? 'The video is merged with ffmpeg into MP4 (H.264 + AAC when available). For huge playlists pick 720p or 1080p: less space and less time.'
        : (af === 'mp3'
          ? 'MP3 is re-encoded (slower). For playlists with thousands of songs M4A or Opus are 2-3 times faster, with no quality loss.'
          : 'No re-encoding: the fastest way to download very large playlists.');
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
      if (!urls) { self.msg('Paste at least one YouTube or YouTube Music link.'); self.el('urls').focus(); return; }
      self.msg('');
      var opts = self.collect();
      var btnGo = self.el('btnGo'); btnGo.disabled = true;
      var payload = {}, k;
      for (k in S.settings) { if (Object.prototype.hasOwnProperty.call(S.settings, k)) { payload[k] = S.settings[k]; } }
      for (k in opts) { if (Object.prototype.hasOwnProperty.call(opts, k)) { payload[k] = opts[k]; } }
      api('POST', '/api/settings', payload).then(function (r) { S.settings = r.settings; }, function () { /* non-blocking */ })
        .then(function () { return api('POST', '/api/jobs', { urls: urls, opts: opts }); })
        .then(function (r) {
          self.el('urls').value = ''; updateDetect();
          var n = r.created.length;
          toast(n === 1 ? 'Download added' : n + ' downloads added');
          var notes = [];
          if (r.rejected && r.rejected.length) { notes.push('Links ignored because they were not recognized: ' + r.rejected.slice(0, 3).join(', ')); }
          if (r.duplicates && r.duplicates.length) { notes.push('Already in progress (not added again): ' + r.duplicates.length); }
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
    S.settings = st.settings; S.errmeta = st.errmeta || {}; S.local = !!st.local; S.tools = st.tools || {}; S.android = !!st.android;
    $('#grpAndroidHint').hidden = S.android;
    S.concurrency = st.concurrency; S.browsers = st.browsers || []; S.hasCookies = !!st.has_cookies; S.ytdlp = st.ytdlp;
    S.serverOffset = st.now - Date.now() / 1000;
    if (!S.formInit) { S.formInit = true; form.fill(st.settings); updateDetect(); }
    else { $('#destDir').textContent = st.settings.download_dir; $('#destDir').title = st.settings.download_dir; }
    var warn = [];
    if (!S.tools.ffmpeg) { warn.push('ffmpeg not found: conversions will not work. Run Start.bat again to reinstall it.'); }
    $('#toolsWarn').hidden = !warn.length; $('#toolsWarn').textContent = warn.join(' ');

    var thr = st.throttle || {}, tb = $('#throttle');
    if (thr.until && thr.until > st.now) {
      tb.hidden = false;
      tb.textContent = 'YouTube is limiting requests (' + (thr.reason || 'limit') + '). Automatic safety pause: ' + Math.ceil(thr.until - st.now) + ' s left, then downloads resume by themselves.';
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
    var pct = tot ? Math.floor(done / tot * 100) : 0;
    document.title = running && tot ? '(' + pct + '%) YT Grabber' : 'YT Grabber';
    $('#jobsCount').textContent = S.jobs.length ? S.jobs.length + (S.jobs.length === 1 ? ' item' : ' items') : '';
    $('#btnClearDone').hidden = finishedJobs === 0;
    $('#empty').hidden = S.jobs.length > 0;
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
      sp.textContent = (speed > 0 ? fmtBytes(speed) + '/s' : '') + (speed > 0 && p > 0 ? ' · ' : '') + (p > 0 ? p + ' converting' : '');
    } else { sp.hidden = true; }
  }

  // ------------------------------------------------------------------ job cards
  function badge(j) {
    if (j.status === 'error') { return '<span class="badge bad">Error</span>'; }
    if (j.status === 'cancelled') { return '<span class="badge">Cancelled</span>'; }
    if (j.status === 'done') {
      return j.counts.e ? '<span class="badge bad">Completed with errors</span>' : '<span class="badge done">Completed</span>';
    }
    if (j.paused) { return '<span class="badge pause">' + (j.interrupted ? 'Interrupted: press Resume' : 'Paused') + '</span>'; }
    if (j.status === 'enumerating') { return '<span class="badge run">Reading list + downloading</span>'; }
    return '<span class="badge run">In progress</span>';
  }

  function errNums(j) {
    var ids = j.err_idx || [], w = j.pad || Math.max(2, String(j.total).length), out = [];
    for (var i = 0; i < ids.length && i < 60; i++) { out.push('#' + padNum(ids[i], w)); }
    var rest = j.counts.e - Math.min(ids.length, 60);
    return '<b>' + out.join(' ') + '</b>' + (rest > 0 ? ' and ' + rest + ' more' : '');
  }

  function ringHtml(j) {
    var T = j.total || 0, pct = T ? Math.floor(j.processed / T * 100) : 0, r = 25, c = 2 * Math.PI * r;
    var cls = j.status === 'done' ? (j.counts.e ? 'bad' : 'ok') : (j.status === 'running' || j.status === 'enumerating') && !j.paused ? 'run' : '';
    return '<svg class="ring" viewBox="0 0 62 62" role="img" aria-label="' + pct + '% complete"><circle class="rt" cx="31" cy="31" r="' + r + '"/>' +
      '<circle class="rv ' + cls + '" cx="31" cy="31" r="' + r + '" stroke-dasharray="' + c.toFixed(1) + '" stroke-dashoffset="' + (c * (1 - pct / 100)).toFixed(1) + '" transform="rotate(-90 31 31)"/>' +
      '<text x="31" y="36">' + pct + '%</text></svg>';
  }

  function tile(cls, n, label) { return '<div class="stat ' + cls + (n ? '' : ' zero') + '"><b>' + n + '</b><span>' + label + '</span></div>'; }

  function statsHtml(j) {
    var c = j.counts;
    return tile('ok', c.d, 'Completed') + (c.s ? tile('ok', c.s, 'Already present') : '') + tile('info', c.a, 'Downloading') + tile('warn', c.p, 'Converting') +
      tile('', c.q, 'Queued') + (c.c ? tile('', c.c, 'Cancelled') : '') +
      (c.e ? '<button type="button" class="stat err" data-act="goerr" data-id="' + j.id + '" title="Show which ones"><b>' + c.e + '</b><span>Errors: show which</span></button>' : tile('err', 0, 'Errors'));
  }

  function liveHtml(j) {
    if (!((j.status === 'running' || j.status === 'enumerating') && !j.paused)) { return ''; }
    var h = '';
    if (j.speed > 0) { h += '<span>Speed <b>' + fmtBytes(j.speed) + '/s</b></span>'; }
    if (j.eta) { h += '<span>About <b>' + fmtEta(j.eta) + '</b> left</span>'; }
    if (j.status === 'enumerating' && j.declared) { h += '<span>Read <b>' + j.total + '</b> of ' + j.declared + ' items</span>'; }
    return h;
  }

  function alertsHtml(j) {
    var c = j.counts, h = '';
    if (j.status === 'error' && j.message) { h += '<div class="alert">' + esc(j.message) + '</div>'; }
    if (j.warning) { h += '<div class="alert warn">' + esc(j.warning) + '</div>'; }
    if (j.status === 'done') {
      var okN = c.d + c.s;
      h += '<div class="alert ' + (c.e ? '' : 'ok') + '">' + (c.e
        ? 'Finished: ' + okN + ' downloaded, <strong>' + c.e + ' with errors</strong>. Numbers: ' + errNums(j) + '. Open the list to see the reason for each one.'
        : 'Finished: all ' + okN + ' items were downloaded.') + '</div>';
    } else if (c.e && (j.err_idx || []).length) {
      h += '<div class="alert">Errors so far at numbers: ' + errNums(j) + '</div>';
    }
    return h;
  }

  function actionsHtml(j) {
    var c = j.counts, id = j.id, h = '';
    var live = j.status === 'running' || j.status === 'enumerating';
    if (live && j.paused) { h += btn('resume', id, 'Resume', IC.play, 'solid'); }
    if (live && !j.paused) { h += btn('pause', id, 'Pause', IC.pause); }
    if (j.status === 'cancelled' || j.status === 'error') { h += btn('resume', id, 'Resume', IC.play, 'solid'); }
    if (c.e && !live) { h += btn('retry_failed', id, 'Retry the errors (' + c.e + ')', IC.retry, 'solid'); }
    h += btn('toggle', id, S.openId === id ? 'Close list' : 'Open list', IC.list);
    if (live) { h += btn('cancel', id, 'Cancel', IC.stop, 'danger'); }
    if (S.local && !S.android && j.dir) { h += btn('open_folder', id, 'Folder', IC.folder); }
    if (c.d + c.s > 0 && j.kind !== 'single') { h += '<a class="btn sm" href="/api/jobs/' + id + '/playlist.m3u8" download>' + IC.m3u + 'Playlist M3U</a>'; }
    if (c.d + c.s > 0 && !live) { h += btn('redownload', id, 'Download all again', IC.retry); }
    h += btn('remove', id, 'Remove', IC.trash, 'ghost');
    return h;
  }

  function makeCard(j) {
    var el = document.createElement('article');
    el.className = 'job'; el.setAttribute('data-id', j.id);
    el.innerHTML =
      '<div class="jbody"><div class="jmain">' +
      '<div class="jcover" data-act="toggle" data-id="' + j.id + '"><span class="jicon"></span><img alt="" referrerpolicy="no-referrer"></div>' +
      '<div class="jinfo"><div class="jtitle" data-act="toggle" data-id="' + j.id + '" role="button" tabindex="0"></div><div class="jmeta"></div></div>' +
      '<div class="jring"></div></div>' +
      '<div class="bar"></div><div class="stats"></div><div class="jlive"></div><div class="jalerts"></div><div class="jact"></div></div>' +
      '<div class="jdetail" hidden></div>';
    var body = el.firstChild, main = body.firstChild, img = main.firstChild.lastChild;
    var card = {
      el: el, err: false, cover: null, img: img, icon: main.firstChild.firstChild, title: main.children[1].firstChild, meta: main.children[1].lastChild,
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
    var sub = [j.kind === 'single' ? 'Single videos' : 'Playlist', T + (T === 1 ? ' item' : ' items')];
    setH(card.meta, badge(j) + '<span>' + esc(sub.join(' · ')) + '</span>' + (j.dir ? '<span class="path" title="' + esc(j.dir) + '">' + esc(j.dir) + '</span>' : '') + '<span>' + fmtDate(j.created) + '</span>');
    setH(card.ring, ringHtml(j));
    setH(card.bar, '<i class="g" style="width:' + w(c.d + c.s) + '%"></i><i class="a" style="width:' + w(c.p) + '%"></i><i class="b" style="width:' + w(c.a) + '%"></i><i class="r" style="width:' + w(c.e) + '%"></i>');
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
    var box = $('#jobs'), jobs = S.jobs.slice().reverse(), seen = {}, i, j, card;
    for (i = 0; i < jobs.length; i++) {
      j = jobs[i]; seen[j.id] = true; card = S.cards[j.id];
      if (!card) { card = S.cards[j.id] = makeCard(j); }
      updateCard(card, j);
      if (box.children[i] !== card.el) { box.insertBefore(card.el, box.children[i] || null); }
    }
    for (var id in S.cards) {
      if (Object.prototype.hasOwnProperty.call(S.cards, id) && !seen[id]) {
        if (S.cards[id].el.parentNode) { S.cards[id].el.parentNode.removeChild(S.cards[id].el); }
        delete S.cards[id];
        if (S.openId === id) { closeDetail(); }
      }
    }
  }

  // ------------------------------------------------------------------ detail with virtual list
  function closeDetail() {
    if (S.openId && S.cards[S.openId]) { S.cards[S.openId].detail.hidden = true; S.cards[S.openId].detail.innerHTML = ''; }
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
        '<div class="tabs"><span class="tabbtns"></span><input class="search" type="search" placeholder="Search title or number" aria-label="Search the list"></div>' +
        '<div class="vbox"><div class="vspacer"></div><div class="vempty" hidden></div></div>';
      S.detail = {
        id: id, items: [], seq: 0, tab: 'all', q: '', kind: '', view: [], summary: null, rowEls: {}, busy: false,
        panel: el.children[0], tabsEl: el.children[1].firstChild, box: el.children[2], spacer: el.children[2].children[0],
        empty: el.children[2].children[1], tabsHtml: '', panelHtml: ''
      };
      var raf = 0, d = S.detail, sInp = el.children[1].lastChild;
      sInp.addEventListener('input', function () { d.q = sInp.value; d.box.scrollTop = 0; rebuildView(d); renderVList(); });
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
      ph = '<h3>' + c.e + (c.e === 1 ? ' item not downloaded' : ' items not downloaded') + '</h3><div class="errgroups">';
      for (var k in byKind) {
        if (Object.prototype.hasOwnProperty.call(byKind, k)) {
          ph += '<button type="button" class="errgroup" data-act="errkind" data-kind="' + esc(k) + '" title="' + esc(errHint(k)) + '">' + esc(errLabel(k)) + ': ' + byKind[k] + '</button>';
        }
      }
      ph += '</div><div class="errnums">';
      var nums = [];
      for (i = 0; i < errs.length && i < 400; i++) { nums.push('#' + padNum(errs[i].i, pad)); }
      ph += esc(nums.join(' ')) + (errs.length > 400 ? ' ...' : '') + '</div>' +
        '<div class="jact">' + btn('retry_failed', d.id, 'Retry all errors', IC.retry, 'solid') +
        btn('copyerrs', d.id, 'Copy list', IC.list) +
        '<a class="btn sm" href="/api/jobs/' + d.id + '/errors.txt" download>' + IC.save + 'Download list (.txt)</a></div>';
    }
    if (ph !== d.panelHtml) { d.panelHtml = ph; d.panel.innerHTML = ph; }
    d.panel.hidden = !c.e;

    var th = '', t, n;
    for (i = 0; i < TABS.length; i++) {
      t = TABS[i];
      n = t[0] === 'all' ? s.total : t[0] === 'd' ? c.d + c.s : c[t[0]];
      if (t[0] === 'c' && !n) { continue; }
      th += '<button type="button" class="tab t-' + t[0] + (d.tab === t[0] ? ' on' : '') + '" data-act="tab" data-tab="' + t[0] + '">' + t[1] + '<b>' + n + '</b></button>';
    }
    if (d.kind) { th += '<button type="button" class="tab on" data-act="clearkind">Filter: ' + esc(errLabel(d.kind)) + ' ✕</button>'; }
    if (th !== d.tabsHtml) { d.tabsHtml = th; d.tabsEl.innerHTML = th; }
    rebuildView(d);
    renderVList();
  }

  // persistent row: the children are created once and updated only if they change (no thumbnail flicker)
  function makeRow() {
    var el = document.createElement('div');
    el.className = 'row';
    el.innerHTML = '<div class="rthumb"><img alt="" referrerpolicy="no-referrer"></div><div class="rnum"></div>' +
      '<div class="rmain"><div class="rtitle"></div><div class="rsub"></div></div><div class="rside"></div><div class="ract"></div>';
    var r = { el: el, img: el.firstChild.firstChild, num: el.children[1], title: el.children[2].firstChild, sub: el.children[2].lastChild, side: el.children[3], act: el.children[4], k: {} };
    r.img.onload = function () { r.img.style.visibility = 'visible'; };
    r.img.onerror = function () { r.img.style.visibility = 'hidden'; };
    return r;
  }

  function updateRow(r, it, pad, jid, top) {
    var k = r.k, link = it.v ? 'https://www.youtube.com/watch?v=' + encodeURIComponent(it.v) : '';
    var title = it.t || (it.v ? 'Video ' + it.v : 'Reading title...');
    var sub = '', side = '', act = '', tip = '';
    switch (it.s) {
      case 'a':
        sub = esc(it.st) + (it.eta != null && it.eta > 0 ? ' · ' + fmtEta(it.eta) + ' left' : '');
        side = '<div class="st info">' + Math.floor(it.p) + '%</div><div class="pbar"><i style="width:' + it.p + '%"></i></div>' +
          [it.sp ? fmtBytes(it.sp) + '/s' : '', it.sz ? fmtBytes(it.sz) : ''].filter(Boolean).join(' · ');
        break;
      case 'p':
        sub = esc(it.st || 'Converting');
        side = '<div class="st warn">Converting</div><div class="pbar cv"><i></i></div>';
        break;
      case 'q':
        if (it.rt > 0) {
          sub = esc(it.st) + ' in ' + it.rt + ' s' + (it.ek ? ' · ' + esc(errLabel(it.ek)) : '');
          side = '<span class="st warn">Retrying</span>'; tip = it.em || '';
        } else { sub = it.a > 0 ? esc(it.st || 'Waiting for a new attempt') : 'Waiting'; side = 'Queued'; }
        break;
      case 'd':
        sub = esc(it.f || ''); side = '<div class="st ok">Completed</div>' + (it.sz ? fmtBytes(it.sz) : '');
        // on the phone the file is already in the Download folder: a "Save" button would make a useless copy
        act = S.android ? '' : '<a class="btn sm" href="/api/jobs/' + jid + '/file/' + it.i + '" download title="Download this file from the server">' + IC.save + '</a>';
        break;
      case 's':
        sub = esc(it.f || ''); side = '<div class="st ok">Already present</div>';
        break;
      case 'e':
        sub = '<b>' + esc(errLabel(it.ek)) + '</b> · ' + esc(trunc(it.em, 160));
        side = '<div class="st bad">Error</div>' + (it.a > 1 ? it.a + ' attempts' : '');
        tip = errLabel(it.ek) + '\n' + errHint(it.ek) + '\n\n' + (it.em || '');
        act = '<button class="btn sm" data-act="retry_item" data-id="' + jid + '" data-idx="' + it.i + '" title="Retry">' + IC.retry + '</button>' +
          (link ? '<a class="btn sm" href="' + link + '" target="_blank" rel="noopener noreferrer" title="Open on YouTube">' + IC.open + '</a>' : '');
        break;
      case 'c':
        sub = 'Cancelled'; side = 'Cancelled';
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
    if (k.act !== act) { k.act = act; r.act.innerHTML = act; }
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
    if (!n) { d.empty.textContent = d.items.length === 0 ? 'Reading the list...' : 'No items in this view.'; }
    var st = d.box.scrollTop, h = d.box.clientHeight || 400;
    var first = Math.max(0, Math.floor(st / ROW) - 6), last = Math.min(n, Math.ceil((st + h) / ROW) + 6), need = {}, k, it, key, r;
    for (k = first; k < last; k++) {
      it = d.items[d.view[k]]; key = it.i; need[key] = true; r = d.rowEls[key];
      if (!r) { r = d.rowEls[key] = makeRow(); d.spacer.appendChild(r.el); }
      updateRow(r, it, pad, d.id, k * ROW);
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
    chain.then(function () { toast('Removed from the list: ' + ids.length + ' (the files stay in the folder)'); pollState(); })
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
      case 'cancel': if (window.confirm('Cancel this download? Files already downloaded stay in the folder.')) { jobAction(id, 'cancel'); } break;
      case 'retry_failed': jobAction(id, 'retry_failed', null, 'Retrying the items with errors'); break;
      case 'retry_item': jobAction(id, 'retry_failed', [parseInt(el.getAttribute('data-idx'), 10)], 'Retrying the item'); break;
      case 'redownload': if (window.confirm('Download ALL the items of this list again, even those already present?')) { jobAction(id, 'redownload', null, 'Downloading everything again'); } break;
      case 'open_folder': jobAction(id, 'open_folder'); break;
      case 'remove': if (window.confirm('Remove from the list? The downloaded files are NOT deleted.')) { jobAction(id, 'remove'); } break;
      case 'tab': if (d) { d.tab = el.getAttribute('data-tab'); d.box.scrollTop = 0; renderDetail(); } break;
      case 'errkind': if (d) { d.kind = el.getAttribute('data-kind'); d.tab = 'e'; d.box.scrollTop = 0; renderDetail(); } break;
      case 'clearkind': if (d) { d.kind = ''; renderDetail(); } break;
      case 'copyerrs': if (d && d.summary) { copyText(errorsText(d)); } break;
    }
  }

  function errorsText(d) {
    var s = d.summary, pad = s.pad || Math.max(2, String(s.total).length), lines = [s.title, s.url, ''], i, it;
    for (i = 0; i < d.items.length; i++) {
      it = d.items[i];
      if (it && it.s === 'e') {
        lines.push('#' + padNum(it.i, pad) + ' | ' + (it.t || '(unknown title)') + ' | ' + errLabel(it.ek) + ' | ' + (it.v ? 'https://www.youtube.com/watch?v=' + it.v : ''));
      }
    }
    return lines.join('\n');
  }

  // ------------------------------------------------------------------ settings
  function openSettings() {
    var s = S.settings;
    $('#setDir').value = s.download_dir || '';
    var sel = $('#setCookiesBrowser'), html = '<option value="">None</option>', i;
    var names = { firefox: 'Firefox', chrome: 'Chrome', edge: 'Edge', brave: 'Brave', opera: 'Opera', vivaldi: 'Vivaldi', chromium: 'Chromium', whale: 'Whale', safari: 'Safari' };
    for (i = 0; i < S.browsers.length; i++) { html += '<option value="' + S.browsers[i] + '">' + (names[S.browsers[i]] || S.browsers[i]) + '</option>'; }
    sel.innerHTML = html; sel.value = s.cookies_browser || '';
    $('#cookiesState').textContent = S.hasCookies ? 'cookies.txt file loaded and in use (if you do not choose a browser).' : 'No cookies.txt file loaded.';
    $('#verInfo').textContent = 'yt-dlp ' + S.ytdlp + ' · ffmpeg ' + (S.tools.ffmpeg ? 'ok' : 'MISSING') + ' · JavaScript runtime ' + (S.tools.deno ? 'ok' : 'absent') + ' · ' + S.concurrency + ' simultaneous downloads';
    $('#setBrowse').hidden = !S.local || S.android; $('#btnUpdate').hidden = !S.local;
    $('#setMsg').hidden = true; $('#setCookiesFile').value = '';
    $('#settingsOv').hidden = false;
  }
  function closeSettings() { $('#settingsOv').hidden = true; }
  function setMsg(t, ok) { var m = $('#setMsg'); m.hidden = !t; m.textContent = t || ''; m.className = 'msg' + (ok ? ' ok' : ''); }

  function saveSettings() {
    var payload = {}, k;
    for (k in S.settings) { if (Object.prototype.hasOwnProperty.call(S.settings, k)) { payload[k] = S.settings[k]; } }
    payload.download_dir = $('#setDir').value.trim();
    payload.cookies_browser = $('#setCookiesBrowser').value;
    api('POST', '/api/settings', payload).then(function (r) {
      S.settings = r.settings; form.fill(r.settings); closeSettings(); toast('Settings saved');
    }).catch(function (e) { setMsg(e.message); });
  }

  function waitServer(tries) {
    api('GET', '/api/ping').then(function () { toast('Server restarted'); window.location.reload(); })
      .catch(function () { if (tries > 0) { setTimeout(function () { waitServer(tries - 1); }, 1500); } else { toast('Restart Start.bat by hand', true); } });
  }

  function init() {
    applyTheme(getTheme());
    $('#btnTheme').addEventListener('click', cycleTheme);
    document.addEventListener('click', onClick);
    document.addEventListener('keydown', function (ev) {
      if ((ev.key === 'Enter' || ev.key === ' ') && ev.target && ev.target.className === 'jtitle') { ev.preventDefault(); openJob(ev.target.getAttribute('data-id')); }
      if (ev.key === 'Escape' && !$('#settingsOv').hidden) { closeSettings(); }
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
        if (!t0) { toast('The clipboard is empty', true); return; }
        ta.value = (ta.value ? ta.value.replace(/\s+$/, '') + '\n' : '') + t0; updateDetect(); ta.focus();
      } else if (navigator.clipboard && navigator.clipboard.readText) {
        navigator.clipboard.readText().then(function (t) {
          if (!t) { toast('The clipboard is empty', true); return; }
          ta.value = (ta.value ? ta.value.replace(/\s+$/, '') + '\n' : '') + t.trim(); updateDetect(); ta.focus();
        }, function () { toast('The browser does not allow reading the clipboard: use Ctrl+V in the box.', true); ta.focus(); });
      } else { toast('Use Ctrl+V in the box to paste.', true); ta.focus(); }
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
          S.hasCookies = r.has_cookies; $('#cookiesState').textContent = 'cookies.txt file loaded and in use.'; setMsg('cookies.txt loaded', true);
        }).catch(function (e) { setMsg(e.message); });
      };
      rd.readAsText(f);
    });
    $('#setCookiesClear').addEventListener('click', function () {
      api('POST', '/api/cookies', { text: '' }).then(function () { S.hasCookies = false; $('#cookiesState').textContent = 'No cookies.txt file loaded.'; setMsg('cookies.txt removed', true); })
        .catch(function (e) { setMsg(e.message); });
    });
    $('#btnUpdate').addEventListener('click', function () {
      if (!window.confirm('Update yt-dlp and restart the server? Downloads in progress are interrupted (you can resume them).')) { return; }
      var b = this; b.disabled = true; setMsg('Updating, this can take a minute...', true);
      api('POST', '/api/update', {}).then(function () { setMsg('Updated. Restarting...', true); setTimeout(function () { waitServer(40); }, 2500); })
        .catch(function (e) { setMsg(e.message); b.disabled = false; });
    });
    document.addEventListener('visibilitychange', function () { if (!document.hidden) { pollState(); if (S.detail) { fetchDetail(); } } });
    window.addEventListener('resize', function () { calcRow(); if (S.detail) { renderVList(); } });
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
    pollState();
  }

  init();
}());
