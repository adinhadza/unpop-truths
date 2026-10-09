# Daily scan: competitors, new niches and our numbers

Find the top-performing US Facebook pages in Adin's niches and report what they do, so the 5-day
review can borrow what works. Work unattended. Never copy their lines or videos; learn patterns only.

Niches: one per page listed in `docs/pages.md` (read it every run; Adin adds pages there).
Each run covers 8 to 12 top-performing US pages per niche. Keep a running list in
`reports/competitors/tracked.md` (name, link, niche, date first found, last check): reuse the strongest
tracked pages, replace inactive or weak ones with new finds, so the list stays the current top 8 to 12.

## Niche exploration (outside our niches)
Each day also explore 2 or 3 niches we do not run yet, rotating so a niche is not repeated within 14 days
(keep the log in `reports/competitors/niches.md`: niche, date explored, score, verdict).
Ideas to rotate through: faith and prayer, pets and animal rescue, nostalgia (50s to 90s America),
relationships and marriage advice, cooking and old family recipes, gardening and homesteading, true stories
and history, health and aging tips, money lessons, trucker and blue-collar life, military and veterans,
small-town America, cars and classic trucks, funny everyday moments, wildlife and nature, DIY and home fixes,
and any niche you see trending. For each niche find 3 to 5 leading US pages and score it 1 to 10 on:
audience size and views shown, engagement, how easy it is to make with our setup (Canva + stock footage
or photos + music, fully automated), competition, and monetization signals. Recommend the top niches for
a new page with a one-line content formula for each.

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
2. Keep 8 to 12 pages per niche that look US-based (US locations, US spelling, US topics). Prefer pages
   with recent activity.
3. For each page record what you can actually find, with the source link:
   name, link, followers, country signals, main themes, post formats (Reels, photos, text-on-video, carousel),
   posting volume per day (count recent dated posts if visible, otherwise "unknown"),
   typical caption style, video length, music style, visual style, monetization signals + confidence.
4. Compare with Adin's pages: what they do that his pages don't (themes, hooks, posting times, volume, formats).
5. Write `reports/competitors/<date>.md`: what is new today (new pages, changes, 3 to 5 patterns worth testing),
   then one table per niche for the pages checked today, then sources. Update `tracked.md`. Mark every number with where it came from; write "unknown"
   rather than guessing. Commit and push to main.
6. Top-performing Reels. For each niche, pick the 5 to 10 best-performing recent Reels you can find on those pages
   (highest views or engagement that is publicly shown). For each: page, link, views/likes if shown, the hook
   (described in your own words, not copied), text style, background footage type, length, music feel, caption style.
7. Make a PDF report `reports/competitors/<date>-inspiration.pdf` (use Python with reportlab; install it with
   pip --break-system-packages if missing). Contents, in this order:
   a. Summary: the 5 most important takeaways.
   b. Top pages table per niche (name, followers, posts per day, themes, formats, monetization signals + confidence).
   c. Top Reels list with the breakdown from step 6 and links.
   d. Our numbers yesterday: dispatch page-report.yml (without save), read its annotations, and list
      each of Adin's pages with yesterday's posts, plays or reach, and the best and worst post. Numbers only;
      do not change any plan (the 5-day review does that).
      Note: a Reel's `created` time in the report is when it was uploaded, not when it went public. Scheduled
      Reels are uploaded in a batch hours ahead; take the real publish time from the plan's `publish_at`
      (match by caption) before drawing any conclusion about timing.
   e. New niches explored today with scores, and the running top 5 niches from niches.md.
   f. "What to upgrade on Unpopular Truths": 5 to 8 concrete, prioritized changes for the motivation page
      (themes, hooks, text length, footage, music, posting volume and times, captions), each with the evidence
      behind it and how to test it. Also 2 to 4 suggestions for the news page.
   Keep it readable on a phone: large text, short lines, one idea per bullet.
   Commit the PDF and the markdown report and push to main.
8. Send ONE phone notification (PushNotification, load with ToolSearch), under 200 characters:
   the single most useful finding, and the PDF link
   https://github.com/adinhadza/unpop-truths/blob/main/reports/competitors/<date>-inspiration.pdf
