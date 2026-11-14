/* ProduceWatch first party aggregate counters. No cookies, no storage, no visitor ID, no third party.
   Disabled until ENDPOINT is set to a collector the owner runs (see ../../06-ANALYTICS-PLAN.md). */
(() => {
  const ENDPOINT = '';              // e.g. 'https://control.orynavo.com/producewatch/events' once that route exists
  if (!ENDPOINT || navigator.doNotTrack === '1' || navigator.globalPrivacyControl === true) return;
  const allowedEvents = new Set(['pageview', 'signup_click', 'sample_click', 'commodity_page_view']);
  const allowedVariants = new Set(['a1', 'a2', 'a3']);
  const q = new URLSearchParams(location.search).get('v');
  const variant = allowedVariants.has(q) ? q : 'none';
  const page = document.documentElement.dataset.pwPage || 'home';
  const sent = new Set();
  const send = ev => {
    if (!allowedEvents.has(ev) || sent.has(ev)) return; sent.add(ev);
    fetch(ENDPOINT, {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({event: ev, variant, page}), credentials: 'omit', referrerPolicy: 'no-referrer', cache: 'no-store', keepalive: true}).catch(() => {});
  };
  send(page === 'home' ? 'pageview' : 'commodity_page_view');
  document.addEventListener('click', e => { const el = e.target.closest && e.target.closest('[data-pw-event]'); if (el) send(el.dataset.pwEvent); });
})();
