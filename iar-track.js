// IAR Analytics Tracking Script
// Tracks pageviews, events, and session data for the admin dashboard

(function() {
  const API_URL = '/api/track';
  
  let sessionStart = Date.now();
  let maxScroll = 0;
  let tracked = new Set();
  let sessionTracked = false;

  // Track pageview on load
  function trackPageview() {
    const data = {
      type: 'pageview',
      page: window.location.pathname,
      referrer: document.referrer || null
    };
    
    fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).catch(() => {}); // Silent fail
  }

  // Track event (button clicks, etc.)
  function trackEvent(eventName) {
    const key = `${eventName}_${window.location.pathname}`;
    if (tracked.has(key)) return; // Don't double-track
    tracked.add(key);

    const data = {
      type: 'event',
      event: eventName,
      page: window.location.pathname
    };
    
    fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).catch(() => {});
  }

  // Track scroll depth
  function updateScroll() {
    const scrolled = (window.scrollY + window.innerHeight) / document.body.scrollHeight;
    maxScroll = Math.max(maxScroll, Math.round(scrolled * 100));
  }

  // Track session on exit
  function trackSession() {
    if (sessionTracked) return;
    sessionTracked = true;
    
    const duration = Math.round((Date.now() - sessionStart) / 1000);
    
    const data = {
      type: 'session',
      duration,
      scroll: maxScroll,
      page: window.location.pathname
    };
    
    // Use standard fetch with keepalive for better reliability
    fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      keepalive: true
    }).catch(() => {});
  }
  
  // Periodic session update (every 30 seconds while on page)
  function updateSession() {
    const duration = Math.round((Date.now() - sessionStart) / 1000);
    
    // Only send if user has been on page for at least 10 seconds
    if (duration < 10) return;
    
    const data = {
      type: 'session',
      duration,
      scroll: maxScroll,
      page: window.location.pathname
    };
    
    fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).catch(() => {});
  }

  // Initialize tracking
  trackPageview();
  
  // Scroll tracking
  window.addEventListener('scroll', updateScroll, { passive: true });
  
  // Session tracking on exit
  window.addEventListener('beforeunload', trackSession);
  window.addEventListener('pagehide', trackSession);
  
  // Periodic session updates (every 30 seconds)
  setInterval(updateSession, 30000);

  // Auto-track common button clicks
  document.addEventListener('click', (e) => {
    const target = e.target.closest('a, button');
    if (!target) return;

    const text = target.textContent?.trim() || '';
    const href = target.getAttribute('href') || '';

    // Track specific actions
    if (text.toLowerCase().includes('donate') || href.includes('donate') || href.includes('givebutter')) {
      trackEvent('Click: Donate Button');
    }
    else if (text.toLowerCase().includes('volunteer') || href.includes('volunteer')) {
      trackEvent('Click: Volunteer Button');
    }
    else if (text.toLowerCase().includes('get started') || href.includes('get-started')) {
      trackEvent('Click: Get Started');
    }
    else if (text.toLowerCase().includes('watch') || href.includes('prime') || href.includes('tubi')) {
      trackEvent('Click: Watch Documentary');
    }
    else if (text.toLowerCase().includes('podcast') || href.includes('podcast')) {
      trackEvent('Click: Podcast Link');
    }
    else if (text.toLowerCase().includes('merch') || href.includes('merch') || href.includes('square.site')) {
      trackEvent('Click: Shop Merch');
    }
    else if (href.includes('facebook') || href.includes('instagram') || href.includes('youtube')) {
      trackEvent('Click: Social Media');
    }
    else if (text.toLowerCase().includes('story') || href.includes('#story')) {
      trackEvent('Click: Submit Story');
    }
    else if (text.toLowerCase().includes('partner') || href.includes('#partner')) {
      trackEvent('Click: Partner With Us');
    }
  });

  // Expose manual tracking for custom events
  window.iarTrack = trackEvent;
})();
