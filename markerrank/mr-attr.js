/* Orynavo landing: campaign attribution carry-over. First-party only: no cookie, no third party, no personal data, no network request.
   Reads utm_source/utm_medium/utm_campaign/utm_content/utm_term/ref and gclid from the landing URL (falls back to the referrer HOST, e.g. youtube.com).
   FIRST TOUCH WINS: the first campaign-tagged visit is kept in localStorage for 30 days (survives closing the tab/browser, new tabs and later
   visits); a later untagged or differently tagged visit never replaces it (a tagged visit only replaces a plain referrer/direct record).
   The value is added as src/med/camp/cont/gclid/ref to every link to markerrank.orynavo.com (the app is another origin: URL parameters carry it).
   Without JavaScript the links keep their default ?ref=landing. Independent of the statistics script (works with Do Not Track too:
   it only decorates our own links, nothing is sent anywhere by this script). */
(function () {
  'use strict';
  var APP = 'markerrank.orynavo.com', KEY = 'mr_attr2', OLD = 'mr_attr', MAX = 64, TTL = 30 * 86400000;
  function clean(v) { return String(v == null ? '' : v).replace(/[^A-Za-z0-9._~-]/g, '').slice(0, MAX); }
  function param(p, k) { try { return clean(p.get(k) || ''); } catch (e) { return ''; } }
  function tagged(o) { return !!(o && (o.src || o.camp || o.gclid) && o.med !== 'referral'); }
  var now = Date.now(), cur = null, store = null;
  try { store = window.localStorage; store.getItem(KEY); } catch (e) { store = null; }
  try {
    var s = JSON.parse((store && store.getItem(KEY)) || 'null');
    if (s && s.v && s.ts && now - s.ts < TTL) cur = s.v;
  } catch (e) { cur = null; }
  var p = new URLSearchParams(location.search);
  var us = param(p, 'utm_source'), um = param(p, 'utm_medium'), uc = param(p, 'utm_campaign'), ref = param(p, 'ref'), gclid = param(p, 'gclid');
  var fresh = null;
  if (us || um || uc || ref || gclid || param(p, 'utm_content') || param(p, 'utm_term')) {
    fresh = { src: us || ref, med: um, camp: uc, ref: ref, cont: param(p, 'utm_content'), term: param(p, 'utm_term'), gclid: gclid };
    if (fresh.src === 'direct') fresh.src = '';
  } else if (!cur || !cur.src) {
    var host = '';
    try { if (document.referrer) { var r = new URL(document.referrer); if (r.hostname !== location.hostname && !/(^|\.)orynavo\.com$/.test(r.hostname)) host = clean(r.hostname.replace(/^www\./, '')); } } catch (e) {}
    if (host) fresh = { src: host, med: 'referral', camp: '', ref: '', cont: '', term: '', gclid: '' };
  }
  // first touch wins: replace only when nothing is stored, or the stored record is just a referrer/empty and the new one carries a campaign tag
  if (fresh && (!cur || (!tagged(cur) && (tagged(fresh) || !cur.src)))) {
    cur = fresh;
    if (store) { try { store.setItem(KEY, JSON.stringify({ v: cur, ts: now })); } catch (e) {} }
  }
  if (!cur) {   // seed written by the SEO guide pages (sessionStorage, this tab only): used for the links, not stored as a first touch
    try { var g = JSON.parse(window.sessionStorage.getItem(OLD) || 'null'); if (g && g.src) cur = g; } catch (e) {}
  }
  cur = cur || {};
  var out = { src: cur.src || 'direct', med: cur.med || '', camp: cur.camp || '', cont: cur.cont || '', gclid: cur.gclid || '', ref: cur.ref || 'landing' };
  function decorate() {
    var links = document.querySelectorAll('a[href*="' + APP + '"]');
    for (var i = 0; i < links.length; i++) {
      var a = links[i], u;
      try { u = new URL(a.getAttribute('href'), location.href); } catch (e) { continue; }
      if (u.hostname !== APP) continue;
      ['src', 'med', 'camp', 'cont', 'gclid', 'ref'].forEach(function (k) { if (out[k]) u.searchParams.set(k, out[k]); else u.searchParams.delete(k); });
      a.setAttribute('href', u.toString());
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', decorate); else decorate();
})();
