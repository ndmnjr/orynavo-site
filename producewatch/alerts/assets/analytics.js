/* ProduceWatch first party aggregate counters. No cookies, no storage, no visitor ID, no third party.

   OFF while ENDPOINT is empty. Sends only {event, variant, page, ref}; ref is the referrer HOSTNAME only. Honors DNT and GPC. */

(() => {

  const ENDPOINT = '';  // 'https://control.orynavo.com/producewatch/events' once the server route exists (see analytics-server/ROOT-STEPS.md)

  if (!ENDPOINT || navigator.doNotTrack === '1' || window.doNotTrack === '1' || navigator.globalPrivacyControl === true) return;

  const events = new Set(['page_view', 'sample_view', 'cta_click', 'commodity_view']);

  const variants = new Set(['a1', 'a2', 'a3']);

  const q = new URLSearchParams(location.search).get('v');

  const variant = variants.has(q) ? q : 'none';

  const page = document.documentElement.dataset.pwPage || 'home';

  let ref = '';

  try { ref = new URL(document.referrer).hostname.toLowerCase(); if (ref === location.hostname || ref.length > 64) ref = ''; } catch (e) { ref = ''; }

  const sent = new Set();

  const send = ev => {

    if (!events.has(ev) || sent.has(ev)) return; sent.add(ev);

    fetch(ENDPOINT, {method: 'POST', headers: {'Content-Type': 'application/json'},

      body: JSON.stringify({event: ev, variant, page, ref}), credentials: 'omit', referrerPolicy: 'no-referrer', cache: 'no-store', keepalive: true}).catch(() => {});

  };

  send(page === 'home' || page === 'sample-index' ? 'page_view' : 'commodity_view');

  document.addEventListener('click', e => { const el = e.target.closest && e.target.closest('[data-pw-event]'); if (el) send(el.dataset.pwEvent); });

})();

