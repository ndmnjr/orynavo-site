/* Orynavo first-party aggregate counter. No cookies, no localStorage or sessionStorage, no identifiers, no IP storage.
   Sends fixed events (landing_view, cta_click) with the page path and an optional campaign tag from the URL to control.orynavo.com.
   Does nothing when Do Not Track or Global Privacy Control is on. */
(() => {
  const nav = navigator;
  if (nav.doNotTrack === '1' || window.doNotTrack === '1' || nav.msDoNotTrack === '1' || nav.globalPrivacyControl === true) return;
  const path = location.pathname.replace(/index\.html$/, '').replace(/^\/+|\/+$/g, '').toLowerCase();
  if (!/^[a-z0-9][a-z0-9\/-]{0,78}[a-z0-9]$/.test(path)) return;
  const parts = path.split('/');
  const counted = (parts[0] === 'photonbid' && ['tenders', 'plans', 'sample-alert', 'open-tenders', 'products', 'guides', 'data'].includes(parts[1])) ||
                  (parts[0] === 'labwatch' && (parts.length === 1 || ['de', 'fr', 'sample-alert', 'open-tenders', 'tenders'].includes(parts[1])) && !['terms', 'refund'].includes(parts[parts.length - 1]));
  if (!counted) return;
  let tag = '';
  const q = new URLSearchParams(location.search);
  for (const k of ['em', 'tag', 'utm_source', 'utm_campaign', 'src']) {
    const v = (q.get(k) || '').toLowerCase();
    if (/^[a-z0-9-]{3,40}$/.test(v)) { tag = v; break; }
  }
  const test = document.documentElement.dataset.orynavoCounterTest === 'true';
  const sent = new Set();   // per document dedupe only
  const send = (event, cta) => {
    const key = event + ':' + (cta || '');
    if (sent.has(key)) return;
    sent.add(key);
    const body = {event, page: path};
    if (tag) body.tag = tag;
    if (cta) body.cta = cta;
    if (test) body.test = true;
    fetch('https://control.orynavo.com/photonbid/events', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body),
      credentials: 'omit', referrerPolicy: 'no-referrer', cache: 'no-store', keepalive: true
    }).catch(() => {});
  };
  send('landing_view');
  document.addEventListener('click', e => {
    const el = e.target.closest && e.target.closest('[data-cta]');
    const id = el && el.getAttribute('data-cta');
    if (id && /^[a-z0-9-]{2,40}$/.test(id)) send('cta_click', id);
  });
})();
