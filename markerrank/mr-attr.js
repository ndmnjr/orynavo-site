/* Orynavo landing: campaign attribution carry-over, STORAGE-FREE. Nothing is written to the visitor's device: no cookie, no web storage of any kind,
   no third party, no personal data, no network request.
   Reads utm_source/utm_medium/utm_campaign/utm_content/utm_term/ref and gclid from the URL of THIS page view (falls back to the referrer HOST,
   e.g. youtube.com, or to a seed set by a guide page: window.mrAttrSeed) and adds them as src/med/camp/cont/gclid/ref to every link to
   markerrank.orynavo.com (the app is another origin: URL parameters carry it; the app also accepts the utm_* names).
   Limit (by design): attribution only covers clicks made on the same page view that carried the campaign tags. A visitor who comes back
   later or opens the app directly counts as direct. Without JavaScript the links keep their default ?ref=landing.
   Independent of the statistics script (works with Do Not Track too: it only decorates our own links, nothing is sent anywhere). */
(function () {
  'use strict';
  var APP = 'markerrank.orynavo.com', MAX = 64;
  function clean(v) { return String(v == null ? '' : v).replace(/[^A-Za-z0-9._~-]/g, '').slice(0, MAX); }
  function param(p, k) { try { return clean(p.get(k) || ''); } catch (e) { return ''; } }
  var cur = null, p;
  try { p = new URLSearchParams(location.search); } catch (e) { p = { get: function () { return ''; } }; }
  var us = param(p, 'utm_source'), um = param(p, 'utm_medium'), uc = param(p, 'utm_campaign'), ref = param(p, 'ref'), gclid = param(p, 'gclid');
  if (us || um || uc || ref || gclid || param(p, 'utm_content') || param(p, 'utm_term')) {
    cur = { src: us || ref, med: um, camp: uc, ref: ref, cont: param(p, 'utm_content'), gclid: gclid };
    if (cur.src === 'direct') cur.src = '';
  } else if (window.mrAttrSeed && window.mrAttrSeed.src) {          // set by SEO guide pages: a constant in the page, nothing stored
    var g = window.mrAttrSeed;
    cur = { src: clean(g.src), med: clean(g.med), camp: clean(g.camp), ref: clean(g.ref), cont: '', gclid: '' };
  } else {
    var host = '';
    try { if (document.referrer) { var r = new URL(document.referrer); if (r.hostname !== location.hostname && !/(^|\.)orynavo\.com$/.test(r.hostname)) host = clean(r.hostname.replace(/^www\./, '')); } } catch (e) {}
    if (host) cur = { src: host, med: 'referral', camp: '', ref: '', cont: '', gclid: '' };
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
