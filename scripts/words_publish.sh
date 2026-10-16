#!/usr/bin/env bash
set -euo pipefail
: "${FB_PAGE_ID:?missing Words That Stay page ID}"
: "${FB_SYSTEM_TOKEN:?missing system token}"
: "${VIDEO_FILE:?missing local MP4}"
: "${CAPTION_FILE:?missing caption file}"
[ -s "$VIDEO_FILE" ] || { echo "::error::Missing rendered MP4"; exit 1; }
token="$(bash scripts/page_token.sh "$FB_PAGE_ID" "")"
[ -n "$token" ] || { echo "::error::Could not obtain Words That Stay page token"; exit 1; }
echo "::add-mask::$token"
if [ "${DRY_RUN:-false}" = "true" ]; then echo "::notice::Dry run: no Facebook upload"; exit 0; fi
graph="https://graph.facebook.com/v23.0"
res="$(curl -fsS -X POST "$graph/$FB_PAGE_ID/video_reels" -d upload_phase=start --data-urlencode "access_token=$token")"
id="$(jq -r '.video_id // empty' <<<"$res")"
[ -n "$id" ] || { echo "::error::Could not start Facebook Reel upload: $(jq -c '.error // .' <<<"$res")"; exit 1; }
size="$(stat -c %s "$VIDEO_FILE")"
res="$(curl -fsS -X POST "https://rupload.facebook.com/video-upload/v23.0/$id" -H "Authorization: OAuth $token" -H "offset: 0" -H "file_size: $size" --data-binary @"$VIDEO_FILE")"
[ "$(jq -r '.success // false' <<<"$res")" = true ] || { echo "::error::Upload failed: $(jq -c '.error // .' <<<"$res")"; exit 1; }
res="$(curl -fsS -X POST "$graph/$FB_PAGE_ID/video_reels" -d upload_phase=finish -d "video_id=$id" -d video_state=PUBLISHED --data-urlencode "description=$(cat "$CAPTION_FILE")" --data-urlencode "access_token=$token")"
[ "$(jq -r '.success // false' <<<"$res")" = true ] || { echo "::error::Publishing failed: $(jq -c '.error // .' <<<"$res")"; exit 1; }
echo "::notice::Facebook accepted Words That Stay Reel $id"
echo "Facebook Reel ID: $id" >> "$GITHUB_STEP_SUMMARY"
