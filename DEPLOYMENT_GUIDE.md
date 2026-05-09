# IAR Analytics — Complete Deployment Guide

## What This Does

Makes your admin.html dashboard show **real visitor data** instead of sample data by:
1. Adding analytics tracking endpoints to your existing server
2. Adding a lightweight tracking script to your public pages
3. Updating admin.html to fetch from the real API

## Files to Update in Your GitHub Repo

### 1. Replace `server.js`
**Location:** Root of your repo  
**Action:** Replace your current server.js with the new one that includes analytics endpoints

The new server.js adds:
- `POST /api/track` — Collects pageview, event, and session data
- `GET /api/analytics` — Returns analytics data for the admin dashboard

### 2. Add `iar-track.js`
**Location:** Root of your repo (same folder as server.js, index.html, etc.)  
**Action:** Add this new file

This lightweight script tracks:
- Pageviews when pages load
- Button clicks (Donate, Volunteer, Watch, Merch, Social, etc.)
- Session duration and scroll depth

### 3. Update Your HTML Pages

Add this ONE line to the bottom of each public page (just before `</body>`):

```html
<!-- IAR Analytics -->
<script src="iar-track.js"></script>
```

**Files to update:**
- index.html
- where-you-stand.html
- get-started.html
- get-involved.html
- merch.html

**DO NOT add to:**
- admin.html (admins shouldn't be tracked)
- social-agent.html (internal tool)

### Example: Adding to index.html

Find the end of the file where you see:

```html
<script src="shared.js"></script>
<script>
function openTrailer() {
  window.open('https://www.imdb.com/video/vi2476917273/', '_blank');
}
</script>
</body>
</html>
```

Change it to:

```html
<script src="shared.js"></script>
<script>
function openTrailer() {
  window.open('https://www.imdb.com/video/vi2476917273/', '_blank');
}
</script>

<!-- IAR Analytics -->
<script src="iar-track.js"></script>

</body>
</html>
```

Repeat for where-you-stand.html, get-started.html, get-involved.html, and merch.html.

### 4. Replace `admin.html`
**Location:** Root of your repo  
**Action:** Replace your current admin.html with the updated version

The new admin.html calls the real `/api/analytics` API instead of using sample data.

## Deployment Steps

### Step 1: Update GitHub

1. Open your iamredemption GitHub repository
2. Replace `server.js` with the new version
3. Add `iar-track.js` as a new file
4. Replace `admin.html` with the new version
5. Update the 5 HTML pages (index, where-you-stand, get-started, get-involved, merch) to include the tracking script
6. Commit and push all changes

### Step 2: Redeploy on Render

Your Render service should auto-deploy when you push to GitHub. If not:

1. Go to your Render dashboard
2. Find your iamredemption service
3. Click "Manual Deploy" → "Deploy latest commit"

That's it! No environment variables or build command changes needed — your existing setup already has everything.

### Step 3: Test

1. Visit your website at https://iamredemption.com
2. Click around on a few pages
3. Click some buttons (Donate, Get Started, etc.)
4. Wait 1-2 minutes for data to accumulate
5. Go to https://iamredemption.com/admin
6. Log in and check if you see real numbers

## What You'll See

Initially (first few hours):
- Low numbers because you're just starting to collect data
- Only visitors since deployment will be counted

After 24-48 hours:
- Real pageview counts
- Actual visitor numbers
- Device breakdown (Mobile vs Desktop)
- Traffic sources (Direct, Google, Facebook, etc.)
- Button click events
- Session duration and bounce rate

## Data Storage

- **In-memory:** Data resets when the server restarts (which is fine for a nonprofit site)
- **Privacy-first:** No cookies, no personal data, no third-party services
- **Lightweight:** Minimal impact on performance

If you want data to persist across server restarts, you can add a database later (PostgreSQL is free on Render).

## Troubleshooting

### "Stats still showing 0"
- Check that iar-track.js is accessible: visit https://iamredemption.com/iar-track.js
- Open browser console (F12 → Console) and check for errors
- Verify the tracking script was added to public pages (not just admin.html)

### "Analytics API returns error"
- Check Render logs for errors
- Verify server.js was updated correctly
- Make sure you redeployed after pushing changes

### "Tracking script not loading"
- Verify iar-track.js is in the root of your repo (same folder as index.html)
- Check for typos in the script tag
- Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)

## File Checklist

Before you push to GitHub, verify you have:

- ✅ Updated server.js (with analytics endpoints)
- ✅ Added iar-track.js (new file)
- ✅ Updated admin.html (fetches from API)
- ✅ Updated index.html (includes tracking script)
- ✅ Updated where-you-stand.html (includes tracking script)
- ✅ Updated get-started.html (includes tracking script)
- ✅ Updated get-involved.html (includes tracking script)
- ✅ Updated merch.html (includes tracking script)

## Need Help?

If something isn't working, check:
1. Render deployment logs (in Render dashboard)
2. Browser console for JavaScript errors (F12 → Console)
3. Network tab to see if API calls are working (F12 → Network)

The setup is designed to fail gracefully — if analytics aren't working, your site will still function normally.
