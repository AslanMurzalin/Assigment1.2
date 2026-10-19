Link Saver: v1 scope

Product

Public website, anyone can sign up (email + password)
Side project, may grow later
Responsive website only (no PWA or native app)

Saving links

Add via paste field on the website or a browser extension (one-click)
Stored per link: URL, auto-fetched metadata, user notes
Organized with tags
Basic search over title, notes and tags
Duplicates allowed, no snapshots of pages

Downloads and extraction

Per-site handlers, added in order of site popularity:
YouTube: download video at one fixed quality (e.g. 720p)
Ozon: save the item description
Any other site: save the URL only
Starts only when the user clicks a Download button
Files are not stored; they stream straight to the user’s device

Tech and hosting

FastAPI + React, running locally for now, deploy later

Out of v1

Sharing, import/export, reminders, audio-only, quality picker, page archives

Risks to keep in mind

A disclaimer doesn’t remove the YouTube ToS risk. A public service can still get blocked or receive takedown requests.
Streaming downloads through your server uses bandwidth and CPU, so it will be costly once you deploy publicly.
Public signup means you’ll need basic abuse protection (rate limits, email verification).