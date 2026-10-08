# Dr. Beetroot: project notes

Updated 8 October 2026, 02:10 Serbia time.

## What exists

- **Build job** `Build Dr. Beetroot Reel` (`.github/workflows/build-beetroot.yml`, `scripts/build_beetroot.py`):
  one script file in `drbeetroot/scripts/` in, one 1080x1920 MP4 out (stock or AI clips, Kokoro voice, labels, mascot badge).
  The latest build is published to the `dr-beetroot-out` branch. It does not post to Facebook.
- **Five finished videos** in `drbeetroot/ready/`, approved by Adin on 8 Oct and waiting to be scheduled:
  1. whiteboard problem to food, 2. food to body streams, 3. ginger lemon tea recipe, 4. habit grid, 5. five foods (stock footage).
- `drbeetroot/tools/make_style_tests.py` is the one-off script that rendered videos 1 to 4. Its paths point at a
  session scratch folder, so treat it as a reference for the layouts, not something to run as is.
- Mascot: option B (3D beetroot in a doctor's coat), `drbeetroot/assets/logo.jpg` and `mascot.jpg`.

## Decisions

- Page name Dr. Beetroot. Wording is direct ("helps", "supports", "feeds"), never "cures", "treats" or "prevents".
  No claims about cancer, diabetes or heart conditions. Every video carries "General wellness info. Not medical advice."
- Main format: stock footage with narration. One Google Flow AI clip per Reel as the opening hook.
- Google Flow free plan on Adin's account: 50 credits a day, refreshed at 18:47 Serbia time. One 8 second vertical
  Veo 3.1 Lite clip costs 10 credits; Nano Banana images cost 0. Flow is driven through the Claude desktop app's
  browser on Adin's PC, so the PC must be on with the app open.

## Still open

1. Which Facebook page these post to. The saved `FB_PAGE_ID` and `FB_PAGE_TOKEN` belong to Unpopular Truths.
2. Posting job for Dr. Beetroot (the existing `post-reel` job takes a video link, not a file in the repository).
3. Daily automation: Adin plans to set it up on the evening of 8 Oct.
4. Flow's terms for free-plan output on a monetized page, and Facebook's AI label for the AI clips.
5. Adin will send more health pages to scan; for each, rank the visible Reels by views and recreate the best idea with a twist.
