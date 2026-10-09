# Daily performance review

Instructions for the unattended daily run (every morning) that reviews every page and improves the upcoming plan.
The pages to review are listed in `docs/pages.md`.
Work without asking questions. Adin reads the result on his phone.

## 0. Set up
Attach the repo (`add_repo` owner `adinhadza`, repo `unpop-truths`, access `push`), clone it, work inside it.

## 1. Get the numbers
```
gh api -X POST repos/adinhadza/unpop-truths/actions/workflows/page-report.yml/dispatches -f ref=main -f 'inputs[save]=true'
```
Wait about 3 minutes, check the newest `page-report.yml` run completed with success, then `git pull`.
The full reports are in `reports/<date>-unpopular-truths.json`, `reports/<date>-unpopular-truths-posts.json`
and `reports/<date>-news-page.json`. If the run failed or a report shows errors instead of numbers
(for example a missing permission), say so in the review and the notification instead of guessing.

## 2. Unpopular Truths Reels
- Match each Reel to its plan entry in `schedule/unpopular-truths-*.json` by its caption text (the Reel's
  description starts with the plan's `caption`). That gives its key, slot, theme, mood and background.
- Per Reel: plays (`blue_reels_play_count`, or `fb_reels_total_plays`), reach (`post_impressions_unique`),
  average watch time (`post_video_avg_time_watched`, milliseconds) divided by the video length = share watched,
  likes, comments, and engagement per 1,000 plays.
- Use a rolling window: posts from the last 7 days that are at least 48 hours old. Compare only Reels at least 48 hours old; list newer ones separately as "too early".
- Find patterns: by slot time, by mood, by theme, by background type (water, sky, candle, city, nature),
  by line length. Name the top 5 and bottom 5 Reels with their first line.
- Sample sizes are small. Call something a pattern only when it holds across at least 4 Reels.

## 3. 50 State Wire posts
Per post: impressions, reach, reactions, comments, shares, clicks. Compare breaking news with good news,
and the posting times. Top 3 and bottom 3 by headline.

## 3b. Competitor patterns
Read the newest file in `reports/competitors/` (written by the evening competitor scan), if there is one.
Keep at most 2 competitor patterns under test at any time (listed in `reports/tests.md`; add, judge after 5 days, then keep or drop) (for example a theme or hook style), and say
in the review which ones you are testing, so next week's review can judge them.

## 4. Improve the upcoming plan (small daily steps)
Reels plan (`schedule/unpopular-truths-<YYYY>-<MM>.json`), for dates after tomorrow only (never touch posts
already queued):
- Keep 10 posts a day and the same JSON structure.
- Rewrite at most 10 upcoming posts per day (dates after tomorrow) so they lean towards the best themes, moods and backgrounds, and away from
  the weakest. New lines must be original and not repeat any line in any schedule file.
- If one slot time was the weakest on the rolling 7-day window for 7 days in a row, move it by up to 1 hour, staying between 6 AM and
  10 PM Chicago time and at least 1 hour from the next slot. Update `publish_at` for every upcoming post in that slot.
- If the plan has fewer than 10 days left, add days with the best-performing themes.

News guidance: update `docs/news-notes.md` (create it if missing) with at most 6 short, concrete rules for the
next days, for example "good news about animals and rescues does 3x better than average; use 3 such stories a day".
The daily news task reads that file.

Commit everything with the message "Daily review <date>" and push to main.

## 5. Write the review and notify
- Save the review as `reports/daily/<date>.md`: totals for yesterday and the rolling 7 days (posts, plays, reach, followers),
  the best and worst posts, the patterns found, and exactly what was changed in the plan.
- Commit and push it.
- Send ONE phone notification (PushNotification tool, load it with ToolSearch), under 200 characters, for example:
  "Yesterday: 10 Reels, 2.1k plays, 58% watched (7d avg 52%). Best: family/nostalgic at 6 PM. Plan: 6 posts rewritten."
  Always send this one, even when nothing changed.

## Never
Change the number of posts per day, delete or edit anything already published or scheduled on Facebook,
change secrets or the posting workflows, or invent numbers that are not in the reports.
