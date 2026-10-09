# Daily competitor scan

Find the top-performing US Facebook pages in Adin's niches and report what they do, so the Monday
review can borrow what works. Work unattended. Never copy their lines or videos; learn patterns only.

Niches: one per page listed in `docs/pages.md` (read it every run; Adin adds pages there).
Keep a running list of pages already found in `reports/competitors/tracked.md` (name, link, niche,
date first found, last check). Each day: add up to 5 new pages per niche, re-check up to 5 tracked pages
(oldest check first) for changes in themes, volume or followers, and drop pages that went inactive.

## Limits to respect
- Facebook pages mostly need a login to view. Do not log in to anything and do not use Adin's Facebook
  account or browser. Use WebSearch and WebFetch only, on pages that open without a login.
- Monetization status is not public. Report it only as signals with a confidence level, never as fact.
  Signals: ads shown inside their Reels or videos, a Stars or Subscribe button, "Facebook creator" or
  partner program mentions, articles or interviews where the owner talks about earnings.

## Steps
1. Search for candidate pages: lists of top quote/motivation pages, viral quote Reels in US news or blogs,
   creator-statistics sites (for example CreatorDB, Social Blade, Fanpage Karma or Socialinsider public pages),
   Facebook page links that appear in search results with follower counts. Same for US news and good-news pages
   (for example Good News Network, Upworthy, local-news style pages, "positive news" pages).
2. Prefer pages that look US-based (US locations, US spelling, US topics). Prefer pages
   with recent activity.
3. For each page record what you can actually find, with the source link:
   name, link, followers, country signals, main themes, post formats (Reels, photos, text-on-video, carousel),
   posting volume per day (count recent dated posts if visible, otherwise "unknown"),
   typical caption style, video length, music style, visual style, monetization signals + confidence.
4. Compare with Adin's pages: what they do that his pages don't (themes, hooks, posting times, volume, formats).
5. Write `reports/competitors/<date>.md`: what is new today (new pages, changes, 3 to 5 patterns worth testing),
   then one table per niche for the pages checked today, then sources. Update `tracked.md`. Mark every number with where it came from; write "unknown"
   rather than guessing. Commit and push to main.
6. Send ONE phone notification (PushNotification, load with ToolSearch), under 200 characters:
   the single most useful finding and how many pages were checked. Skip the notification if nothing new was found.
