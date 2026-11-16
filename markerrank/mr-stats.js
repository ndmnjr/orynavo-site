/* Orynavo landing: cookieless statistics beacon (GoatCounter, self-hosted at stats.orynavo.com). No cookies, no storage.
   Host this file as /markerrank/mr-stats.js (same origin as the page, so no third-party script is loaded). */
(function () {
  'use strict';
  var s = document.currentScript;
  var ep = s && s.getAttribute('data-endpoint');
  if (!ep) return;
  var n = navigator;
  if (n.doNotTrack === '1' || window.doNotTrack === '1' || n.msDoNotTrack === '1' || n.globalPrivacyControl === true || n.webdriver) return;
  if (/^(localhost$|127\.|10\.|192\.168\.)/.test(location.hostname)) return;
  var enc = encodeURIComponent;
  // only campaign parameters are forwarded (ref, utm_source/medium/campaign); everything else in the query string is dropped
  var keep = {ref: 1, utm_source: 1, utm_medium: 1, utm_campaign: 1}, q = [];
  location.search.replace(/^\?/, '').split('&').forEach(function (kv) {
    var k = kv.split('=')[0]; if (keep[k] && /^[A-Za-z0-9_.%-]{1,60}=[A-Za-z0-9_.%+-]{1,80}$/.test(kv)) q.push(kv);
  });
  var path = location.pathname.replace(/\/index\.html$/, '/').replace(/(.)\/$/, '$1');
  var ref = '';
  try { if (document.referrer) { var r = new URL(document.referrer); if (r.origin !== location.origin) ref = r.origin + '/'; } } catch (e) {}
  function send(p, isEvent) {
    var u = ep + '?p=' + enc(p) + '&t=' + enc(p) + '&s=' + enc(screen.width || 0) + '&rnd=' + Math.random().toString(36).slice(2, 7);
    if (isEvent) u += '&e=true'; else { if (ref) u += '&r=' + enc(ref); if (q.length) u += '&q=' + enc('?' + q.join('&')); }
    var ok = false; try { ok = n.sendBeacon && n.sendBeacon(u); } catch (e) {}
    if (!ok) { var i = new Image(1, 1); i.alt = ''; i.src = u; }
  }
  window.mrStats = { event: function (name) { if (/^[a-z0-9-]{1,40}$/.test(name)) send(name, true); } };
  send(path || '/', false);
  // declarative hooks: data-stat-click="cta-signup-click-hero" on any link/button; data-stat-video="hero" on a <video>
  document.addEventListener('click', function (ev) {
    var el = ev.target && ev.target.closest ? ev.target.closest('[data-stat-click]') : null;
    if (el) window.mrStats.event(el.getAttribute('data-stat-click'));
  }, true);
  document.addEventListener('play', function (ev) {
    var v = ev.target; if (v && v.getAttribute && v.getAttribute('data-stat-video') !== null && !v.__mrPlayed) { v.__mrPlayed = 1; window.mrStats.event('video-play'); }
  }, true);
  document.addEventListener('ended', function (ev) {
    var v = ev.target; if (v && v.getAttribute && v.getAttribute('data-stat-video') !== null && !v.__mrDone) { v.__mrDone = 1; window.mrStats.event('video-complete'); }
  }, true);
})();
