/* Orynavo Retention first-party aggregate counters; no cookies or visitor IDs. */
(() => {
  if (!new Set(['/retentionos/', '/retentionos/index.html']).has(location.pathname) ||
      navigator.doNotTrack === '1' || navigator.globalPrivacyControl === true) return;
  const allowed = new Set(['pageview', 'design_partner_click', 'design_partner_footer_click', 'workflow_click']);
  const sent = new Set();
  const send = event => {
    if (!allowed.has(event) || sent.has(event)) return;
    sent.add(event);
    fetch('https://control.orynavo.com/retention/events', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({event, test: document.documentElement.dataset.retentionAnalyticsTest === 'true'}),
      credentials: 'omit',
      referrerPolicy: 'no-referrer',
      cache: 'no-store',
      keepalive: true
    }).catch(() => {});
  };
  send('pageview');
  document.addEventListener('click', event => {
    const link = event.target.closest?.('[data-retention-event]');
    if (link) send(link.dataset.retentionEvent);
  });
})();
