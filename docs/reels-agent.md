# Daily Reels agent: Unpopular Truths

Instructions for the unattended daily run that builds and schedules the day's Reels.
Work without asking questions. Adin is not at his computer. When something needs his
attention, send ONE phone notification (PushNotification tool, load it with ToolSearch)
with a one-line reason.

## 0. Set up
1. Attach the repo: `add_repo` owner `adinhadza`, repo `unpop-truths`, access `push`; clone it as instructed and work inside it.
2. Today's date is the date in **America/Chicago** (`TZ=America/Chicago date +%F`). All posts are for US viewers.

## 1. (Manual mode: skip the Facebook connection check below; build the videos regardless.)
## 1-old. Check the Facebook connection first
```
gh api -X POST repos/adinhadza/unpop-truths/actions/workflows/check-facebook.yml/dispatches -f ref=main
```
Wait about 40 seconds, find the newest run of `check-facebook.yml`, and read its annotations
(`gh api repos/adinhadza/unpop-truths/commits/<head_sha>/check-runs` → the `check` job id →
`gh api repos/adinhadza/unpop-truths/check-runs/<id>/annotations`).
If the `unpopular-truths` line is an error, do NOT build anything. Send:
"Unpopular Truths: Facebook key not working (<short error>). No Reels queued today. Fix the key in GitHub, then tell Claude."
and stop.

## 1b. (Manual mode: skip this check; Adin posts the Reels himself.)
## 1b-old. Check that yesterday's Reels actually went out
Dispatch `page-report.yml` the same way, wait about 90 seconds, and read its annotations
(the `unpopular-truths` notices hold a JSON report split into parts; join them in order).
Count yesterday's Reels (Chicago date) that show `published: true`, and compare with the number of
`post-reel.yml` runs for yesterday's keys that ended with conclusion `success`.
If fewer were published than queued, or any shows an error state, include it in the phone
notification at the end ("Yesterday: 8 queued, 6 published"). If the report itself fails, mention that too.

## 2. Pick today's posts
- The plan is `schedule/unpopular-truths-<YYYY>-<MM>.json`. Each post has `key`, `publish_at` (Chicago time), `line1`, `line2`, `caption`, `hashtags`, `mood`, `background`.
- Take the posts whose `date` is today.
- Skip any post already queued: list `gh api "repos/adinhadza/unpop-truths/actions/workflows/post-reel.yml/runs?per_page=100"` and skip keys that appear in a run's `display_title` ("Post Reel <key>") with conclusion `success`.
- Skip any post whose `publish_at` is less than 20 minutes from now. Never post late.
- **No posts for today in the plan** (the plan has run out): write 10 new posts for today in the same style and format as the plan (one theme for the day, the same 10 slot times, original lines that are not already in any schedule file, a mood from calm, warm, hopeful, bittersweet, nostalgic, uplifting). Add them to the right month's file (create it if needed, same structure), commit with message "Add Reels plan for <date>" and push to main. Then continue. If the plan has 3 days or fewer left, write and commit the next 7 days the same way.

## 3. Build each video in Canva
Master design: **DAHXXLLSR6U** (1080x1920). Never edit the master; always copy it.
Element locators in the copy (page `PBYSHskBPy9HJ1K7`; confirm with read-design, ids are kept when copying):
- background video: `PBYSHskBPy9HJ1K7-LBwhXlJ20flkbyXt` (a full-page rect with a video fill)
- dark overlay: `PBYSHskBPy9HJ1K7-LB3w1kd50w5g38yj` (opacity 0.38; leave it)
- line 1: `PBYSHskBPy9HJ1K7-LBWGlC1pByVbK5Qt` (white, 104px, centred, width 1000, left 40)
- line 2: `PBYSHskBPy9HJ1K7-LBPKkyLSMCp6jJjF` (same style)
- handle "@unpopular truths": `PBYSHskBPy9HJ1K7-LBkYc5VXwHFyYFKL` (leave it)

For each post:
1. **Background clip.** `orshot_search_stock_media` with the post's `background` term, type video. Choose a slow, calm clip, 8 to 20 seconds long, no visible text, logo or watermark, no close-up faces. Then `orshot_use_stock_media` to get a permanent `storage.orshot.com` link, and Canva `upload-asset-from-url` with that link to get a video asset id (wait for the upload job to finish). If nothing fits, try a simpler term (for example "sunset sky", "rain window", "ocean waves").
2. `copy-design` DAHXXLLSR6U. `read-design` the copy with `open_transaction: true` and `fields: ["design_content","thumbnails"]`.
3. `edit-design` (finalize `keep_open`, page_index 1):
   - `update_title` → `Unpopular Truths - <key>`
   - `update_fill` on the background video locator, asset_type `video`, the new asset id, alt text = the background term.
   - `replace_text` line 1 and line 2 with the post's lines. Break each into balanced lines with `\n` at a natural pause, about 14 to 20 characters per line, never more than 3 lines each.
4. Layout. Read the text heights from the edit result (or read-design with the transaction id). Keep the two lines as one block centred around y = 950: `gap = 70`, `block = h1 + gap + h2`, line 1 top = `950 - block/2`, line 2 top = line 1 top + h1 + gap, both left 40 (`position_element`). If the block is taller than 900, set both lines to font_size 92 (`format_text`) and redo the positions.
5. Look at the preview thumbnail. Check: both lines fully visible, no overlap, nothing cut at the edges, text readable over the footage, handle visible near the bottom. Fix and look again if needed. Then `edit-design` with finalize `commit` and no operations.
6. `export-design` type `mp4`, quality `vertical_1080p`. The link expires within hours, so post it straight away.

## 4. Save it for Adin (he posts the Reels himself; do NOT post to Facebook)
Mode: MANUAL since 2026-10-11. Never dispatch post-reel.yml. Videos stay silent: Adin adds music
inside Facebook when he posts.
- In Canva, find or create the folder `Unpopular Truths <YYYY-MM-DD>` (search-folders first; create-folder if
  missing) and move the finished design into it (move-item-to-folder). Title each design
  `<HH:MM Serbia> - <first words of line 1>` so the folder sorts in posting order
  (Serbia time = Chicago time + 7 hours until Oct 24, + 6 hours from Oct 25).
- If Google Drive tools are available, also follow docs/drive-delivery.md.
- Write `drafts/<YYYY-MM-DD>.md` with one row per video: Serbia time, Chicago time, design title, caption
  + hashtags (ready to paste), and a suggested music mood. Commit and push.
- The "already queued" check in step 2 now means: a design titled for that key's time already exists in
  today's Canva folder.

## 5. Finish
End with a short summary: each key, its time, line 1, and where it was saved, or why it was skipped.
Send a phone notification only when a post was skipped or something failed (one notification for the whole run, under 200 characters).
