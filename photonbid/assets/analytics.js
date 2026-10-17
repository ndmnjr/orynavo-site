/* PhotonBid first-party aggregate counters; no cookies or visitor identifiers. */
(() => {
  if (!['/photonbid/', '/photonbid/index.html'].includes(location.pathname) ||
      navigator.doNotTrack === '1' || navigator.globalPrivacyControl === true) return;
  const allowed = new Set(['pageview', 'sample_request_click', 'profile_cta_click',
    'profile_section_click', 'report_click', 'video_start', 'video_complete', 'video_link_click']);
  // Per-document dedupe only: no cookie, localStorage, sessionStorage or visitor ID.
  const sent = new Set();
  const send = event => {
    if (!allowed.has(event) || sent.has(event)) return;
    sent.add(event);
    fetch('https://control.orynavo.com/photonbid/events', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({event, test: document.documentElement.dataset.photonbidAnalyticsTest === 'true'}),
      credentials: 'omit', referrerPolicy: 'no-referrer', cache: 'no-store', keepalive: true
    }).catch(() => {});
  };
  send('pageview');
  document.addEventListener('click', event => {
    const link = event.target.closest?.('[data-photonbid-event]');
    if (link) send(link.dataset.photonbidEvent);
  });
  document.querySelectorAll('video').forEach(video => {
    video.addEventListener('play', () => send('video_start'));
    video.addEventListener('ended', () => send('video_complete'));
  });
})();
