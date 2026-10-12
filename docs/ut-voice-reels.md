# Unpopular Truths: voice Reels (format approved 12 Oct 2026)

Replaces the Canva quote-Reel build (docs/reels-agent.md, paused 12 Oct 2026).
Runs from Adin's Claude chat every evening around 19:15 Serbia, on his laptop, and
schedules the NEXT day's three Reels on Facebook.

## Format
- 3 still illustrations (Google Flow, Nano Banana, 9:16, 0 credits), moody
  anime/graphic-novel style: lone figure, night, rain, train stations, windows,
  muted browns/blues, warm single light source. No text in the image.
- Slow push-in, film grain, dust, vignette (all done by `scripts/build_ut_reel.py`).
- Calm male narrator: openai.fm, voice **Onyx**, vibe text below. ~12–14 s of speech.
- Script: 6 short lines, 2 per picture, one quiet "unpopular truth" with a turn at
  the end. One line on screen at a time (Caveat handwriting font).
- Music under the voice: rotate the 8 chosen calm tracks, one per Reel:
  moments-emotional, float, stardust-instrumental, there-for-you, the-pearly-gates,
  hymn-for-peace, autumn-reverie, reflections-instrumental (`music/calm/`).
- Length ~15 s. **Every Reel MUST be at least 10 seconds** (the build script never outputs less than 11 s; check with ffprobe before posting).

Approved example script:
```
I forgave everyone who hurt me
except the one
who stayed up at night
replaying every mistake
I was kind to the whole world
and a stranger to myself
```

openai.fm vibe text:
```
Voice: Calm, low, intimate male narrator, close to the microphone.
Tone: Quiet, reflective, slightly melancholic and tired, never dramatic.
Pacing: Very slow and unhurried. Clear pauses between lines, a longer pause after each pair of lines.
Delivery: Soft, almost a whisper, warm. No emphasis, no performance.
```
Write the script for openai.fm with a line break after each line and an empty line
after each pair, so the pauses fall where the text changes.

## Posting times
3 a day at US peak times, America/Chicago: **07:00, 13:00, 20:00**
(Serbia: 14:00, 20:00, 03:00 until 24 Oct; 13:00, 19:00, 02:00 from 25 Oct to 1 Nov;
then back to +7 h when the US also changes clocks on 1 Nov).

## Evening routine (steps)
1. Plan 3 new scripts + 3×3 image prompts. Check `reports/ut-voice-log.md` and never
   repeat a script or a main image idea.
2. Flow (built-in browser on the laptop): Image, 9:16, Nano Banana, x1. Generate the 9 images,
   download each (⋮ → Download media → Original size). Copy them to
   `Downloads\unpopular-truths\<date>\`.
3. openai.fm: voice Onyx, vibe text above, script, Download → `openai-fm-onyx-audio.mp3`;
   rename to `<date>-<n>.mp3` in the same folder.
4. Stage files into the cloud workspace and build:
   `python3 scripts/build_ut_reel.py --images a.jpg b.jpg c.jpg --voice v.mp3 --lines lines.txt --music music/calm/<track>.m4a --out ut-<date>-<n>.mp4`
   Check a contact sheet: text readable, lines in sync, nothing cropped.
5. Push the MP4s to branch `reel-files` (replace older files) → public URL
   `https://raw.githubusercontent.com/adinhadza/unpop-truths/reel-files/<file>`.
6. Dispatch `post-reel.yml`: page `main`, video_url, caption, mode `upload`,
   **music `none`** (anything else replaces the voice), publish_at with Chicago offset
   (e.g. `2026-10-13T07:00:00-05:00`), post_key `ut-<date>-<n>`. One at a time; each run must
   succeed and log "the video keeps its own sound".
7. Append to `reports/ut-voice-log.md`, commit, push. Send the 3 videos to Adin in chat.

Caption: the first line of the script as a hook, then one short reflective line, then
3 hashtags (#unpopulartruths #selfgrowth #healing style). No "follow/share" prompts.

Fallbacks: if openai.fm fails, post nothing that day and tell Adin; if Flow is out of
images, reuse no old images — build fewer Reels and say so. If the laptop is off, tell Adin.
Facebook AI label: the posting job cannot set it; Adin knows the images and voice are AI.
