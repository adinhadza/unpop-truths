#!/usr/bin/env bash
# Publishes one Reel to a Facebook Page using Meta's Reels Publishing API.
# Needs: FB_PAGE_ID, FB_PAGE_TOKEN, VIDEO_URL. Optional: CAPTION, MODE (auto|hosted|upload), GRAPH_VERSION.
set -euo pipefail

: "${FB_PAGE_ID:?FB_PAGE_ID secret is missing}"
: "${FB_PAGE_TOKEN:?FB_PAGE_TOKEN secret is missing}"
: "${VIDEO_URL:?VIDEO_URL is missing}"
CAPTION="${CAPTION:-}"
MODE="${MODE:-auto}"
VER="${GRAPH_VERSION:-v23.0}"
GRAPH="https://graph.facebook.com/${VER}"
echo "::add-mask::${VIDEO_URL}"

fail() { echo "ERROR: $1" >&2; exit 1; }

start_session() {
  local res
  res=$(curl -sS -X POST "${GRAPH}/${FB_PAGE_ID}/video_reels" \
    -d "upload_phase=start" -d "access_token=${FB_PAGE_TOKEN}")
  VIDEO_ID=$(echo "$res" | jq -r '.video_id // empty')
  [ -n "$VIDEO_ID" ] || fail "could not start upload: $(echo "$res" | jq -c '.error // .')"
  UPLOAD_URL="https://rupload.facebook.com/video-upload/${VER}/${VIDEO_ID}"
  echo "Started upload session, video id ${VIDEO_ID}"
}

upload_hosted() {
  local res
  res=$(curl -sS -X POST "$UPLOAD_URL" \
    -H "Authorization: OAuth ${FB_PAGE_TOKEN}" -H "file_url: ${VIDEO_URL}")
  [ "$(echo "$res" | jq -r '.success // false')" = "true" ] && return 0
  echo "Hosted fetch was not accepted: $(echo "$res" | jq -c '.error // .' 2>/dev/null || echo "$res")"
  return 1
}

upload_bytes() {
  curl -sSL --fail -o reel.mp4 "$VIDEO_URL" || fail "could not download the video link"
  local size res
  size=$(stat -c %s reel.mp4)
  [ "$size" -gt 10000 ] || fail "downloaded file is too small (${size} bytes) to be a video"
  echo "Downloaded ${size} bytes"
  res=$(curl -sS -X POST "$UPLOAD_URL" \
    -H "Authorization: OAuth ${FB_PAGE_TOKEN}" -H "offset: 0" -H "file_size: ${size}" \
    --data-binary @reel.mp4)
  [ "$(echo "$res" | jq -r '.success // false')" = "true" ] \
    || fail "file upload failed: $(echo "$res" | jq -c '.error // .' 2>/dev/null || echo "$res")"
}

start_session
case "$MODE" in
  hosted) upload_hosted || fail "hosted mode failed" ;;
  upload) upload_bytes ;;
  auto)   upload_hosted || { echo "Falling back to download and upload"; start_session; upload_bytes; } ;;
  *)      fail "unknown MODE '${MODE}'" ;;
esac
echo "Video handed to Facebook"

res=$(curl -sS -X POST "${GRAPH}/${FB_PAGE_ID}/video_reels" \
  -d "upload_phase=finish" -d "video_id=${VIDEO_ID}" -d "video_state=PUBLISHED" \
  --data-urlencode "description=${CAPTION}" -d "access_token=${FB_PAGE_TOKEN}")
[ "$(echo "$res" | jq -r '.success // false')" = "true" ] \
  || fail "publish step failed: $(echo "$res" | jq -c '.error // .')"

# Facebook processes the video after publishing; wait and report the outcome.
for i in $(seq 1 30); do
  st=$(curl -sS -G "${GRAPH}/${VIDEO_ID}" -d "fields=status" -d "access_token=${FB_PAGE_TOKEN}")
  vs=$(echo "$st" | jq -r '.status.video_status // "unknown"')
  ps=$(echo "$st" | jq -r '.status.publishing_phase.status // "unknown"')
  echo "check ${i}: video=${vs} publishing=${ps}"
  if [ "$ps" = "complete" ] || [ "$vs" = "ready" ]; then
    echo "Reel published: https://www.facebook.com/reel/${VIDEO_ID}"
    echo "### Reel published: https://www.facebook.com/reel/${VIDEO_ID}" >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
    exit 0
  fi
  [ "$vs" = "error" ] && fail "Facebook reported a processing error: $(echo "$st" | jq -c '.status')"
  sleep 10
done
fail "timed out waiting for Facebook to finish processing video ${VIDEO_ID}"
