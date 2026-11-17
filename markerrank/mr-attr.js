/* Orynavo landing: campaign attribution carry-over. First-party only: no cookie, no third party, no personal data, no network request.
   Reads utm_source/utm_medium/utm_campaign/utm_content/utm_term/ref from the landing URL (falls back to the referrer HOST, e.g. youtube.com),
   keeps them in sessionStorage for this tab session and adds src/med/camp/ref to every link to markerrank.orynavo.com.
   Without JavaScript the links keep their default ?ref=landing. Independent of the statistics script (works with Do Not Track too:
   it only decorates our own links, nothing is sent anywhere by this script). */
(function () {
  'use strict';
  var APP = 'markerrank.orynavo.com', KEY = 'mr_attr', MAX = 64;
  function clean(v) { return String(v == null ? '' : v).replace(/[^A-Za-z0-9._~-]/g, '').slice(0, MAX); }
  function param(p, k) { try { return clean(p.get(k) || ''); } catch (e) { return ''; } }
  var cur = {};
  try { cur = JSON.parse(sessionStorage.getItem(KEY) || '{}') || {}; } catch (e) { cur = {}; }
  var p = new URLSearchParams(location.search);
  var us = param(p, 'utm_source'), um = param(p, 'utm_medium'), uc = param(p, 'utm_campaign'), ref = param(p, 'ref');
  var fresh = {};
  if (us || um || uc || ref || param(p, 'utm_content') || param(p, 'utm_term')) {
    fresh = { src: us || ref, med: um, camp: uc, ref: ref, cont: param(p, 'utm_content'), term: param(p, 'utm_term') };
  } else if (!cur.src) {
    var host = '';
    try { if (document.referrer) { var r = new URL(document.referrer); if (r.hostname !== location.hostname && !/(^|\.)orynavo\.com$/.test(r.hostname)) host = clean(r.hostname.replace(/^www\./, '')); } } catch (e) {}
    fresh = { src: host, med: host ? 'referral' : '', camp: '', ref: '' };
  }
  if (fresh.src !== undefined) { cur = fresh; try { sessionStorage.setItem(KEY, JSON.stringify(cur)); } catch (e) {} }
  var out = { src: cur.src || 'direct', med: cur.med || '', camp: cur.camp || '', ref: cur.ref || 'landing' };
  function decorate() {
    var links = document.querySelectorAll('a[href*="' + APP + '"]');
    for (var i = 0; i < links.length; i++) {
      var a = links[i], u;
      try { u = new URL(a.getAttribute('href'), location.href); } catch (e) { continue; }
      if (u.hostname !== APP) continue;
      ['src', 'med', 'camp', 'ref'].forEach(function (k) { if (out[k]) u.searchParams.set(k, out[k]); else u.searchParams.delete(k); });
      a.setAttribute('href', u.toString());
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', decorate); else decorate();
})();
