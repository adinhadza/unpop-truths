#!/usr/bin/env bash
# Publishes one Reel to a Facebook Page using Meta's Reels Publishing API.
# Needs: FB_PAGE_ID, FB_PAGE_TOKEN, VIDEO_URL.
# Optional: CAPTION, MODE (auto|hosted|upload), MUSIC (auto|none|a mood folder or file in music/),
#           MUSIC_LEVEL (average loudness in dB, default -27), DRY_RUN (true = prepare the video but do not post), GRAPH_VERSION.
set -euo pipefail

: "${FB_PAGE_ID:?FB_PAGE_ID secret is missing}"
: "${FB_PAGE_TOKEN:?FB_PAGE_TOKEN secret is missing}"
: "${VIDEO_URL:?VIDEO_URL is missing}"
CAPTION="${CAPTION:-}"
MODE="${MODE:-auto}"
MUSIC="${MUSIC:-auto}"
MUSIC_LEVEL="${MUSIC_LEVEL:--27}"
DRY_RUN="${DRY_RUN:-false}"
HERE="$(cd "$(dirname "$0")" && pwd)"
MUSIC_DIR="${HERE}/../music"
LOCAL_FILE=""
VER="${GRAPH_VERSION:-v23.0}"
GRAPH="https://graph.facebook.com/${VER}"
echo "::add-mask::${VIDEO_URL}"

# Errors and progress are written as annotations so they can be read without opening the log.
fail() { echo "::error::$1"; exit 1; }
note() { echo "::notice::$1"; }

download_video() {
  curl -sSL --fail --connect-timeout 20 --max-time 180 -o reel.mp4 "$VIDEO_URL" || fail "could not download the video link"
  local size; size=$(stat -c %s reel.mp4)
  [ "$size" -gt 10000 ] || fail "downloaded file is too small (${size} bytes) to be a video"
  note "Downloaded ${size} bytes"
  LOCAL_FILE="reel.mp4"
}

list_tracks() {
  find "$1" -type f \( -name '*.m4a' -o -name '*.mp3' -o -name '*.wav' \) 2>/dev/null | sort
}

pick_track() {
  # Prints the chosen track path, or nothing when no music should be added.
  # MUSIC can be: none, auto (any track), a mood folder inside music/, or one file inside music/.
  [ "$MUSIC" = "none" ] && return 0
  local pool="$MUSIC_DIR"
  if [ "$MUSIC" != "auto" ]; then
    if [ -f "${MUSIC_DIR}/${MUSIC}" ]; then echo "${MUSIC_DIR}/${MUSIC}"; return 0; fi
    if [ -d "${MUSIC_DIR}/${MUSIC}" ] && [ -n "$(list_tracks "${MUSIC_DIR}/${MUSIC}")" ]; then
      pool="${MUSIC_DIR}/${MUSIC}"
    else
      echo "::notice::No tracks found for '${MUSIC}', choosing from all tracks instead" >&2
    fi
  fi
  local tracks=()
  while IFS= read -r f; do tracks+=("$f"); done < <(list_tracks "$pool")
  [ "${#tracks[@]}" -gt 0 ] || return 0
  echo "${tracks[$(( ${GITHUB_RUN_NUMBER:-0} % ${#tracks[@]} ))]}"
}

prepare_music() {
  local track; track=$(pick_track)
  if [ -z "$track" ]; then note "No music added"; return 0; fi
  command -v ffmpeg >/dev/null 2>&1 || fail "ffmpeg is not installed on this machine"
  download_video
  bash "${HERE}/add_music.sh" reel.mp4 "$track" reel_music.mp4 "$MUSIC_LEVEL" >/dev/null || fail "could not mix the music into the video"
  local a d; a=$(ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 reel_music.mp4 | head -1)
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 reel_music.mp4)
  [ -n "$a" ] || fail "the mixed video has no sound track"
  LOCAL_FILE="reel_music.mp4"
  note "Music added: ${track#"${MUSIC_DIR}/"} at level ${MUSIC_LEVEL} dB, video length ${d}s, audio ${a}"
}

start_session() {
  local res
  res=$(curl -sS -X POST "${GRAPH}/${FB_PAGE_ID}/video_reels" \
    -d "upload_phase=start" -d "access_token=${FB_PAGE_TOKEN}")
  VIDEO_ID=$(echo "$res" | jq -r '.video_id // empty')
  [ -n "$VIDEO_ID" ] || fail "could not start upload: $(echo "$res" | jq -c '.error // .')"
  UPLOAD_URL="https://rupload.facebook.com/video-upload/${VER}/${VIDEO_ID}"
  note "Started upload session, video id ${VIDEO_ID}"
}

upload_hosted() {
  local res
  res=$(curl -sS -X POST "$UPLOAD_URL" \
    -H "Authorization: OAuth ${FB_PAGE_TOKEN}" -H "file_url: ${VIDEO_URL}")
  [ "$(echo "$res" | jq -r '.success // false')" = "true" ] && return 0
  note "Hosted fetch was not accepted: $(echo "$res" | jq -c '.error // .' 2>/dev/null || echo "$res" | head -c 300)"
  return 1
}

upload_bytes() {
  [ -n "$LOCAL_FILE" ] || download_video
  local size res
  size=$(stat -c %s "$LOCAL_FILE")
  res=$(curl -sS -X POST "$UPLOAD_URL" \
    -H "Authorization: OAuth ${FB_PAGE_TOKEN}" -H "offset: 0" -H "file_size: ${size}" \
    --data-binary @"$LOCAL_FILE")
  [ "$(echo "$res" | jq -r '.success // false')" = "true" ] \
    || fail "file upload failed: $(echo "$res" | jq -c '.error // .' 2>/dev/null || echo "$res")"
}

prepare_music
if [ "$DRY_RUN" = "true" ]; then
  note "Dry run: video prepared, nothing was posted"
  exit 0
fi
# A video with music added exists only on this machine, so it has to be uploaded as a file.
[ -n "$LOCAL_FILE" ] && MODE="upload"

start_session
case "$MODE" in
  hosted) upload_hosted || fail "hosted mode failed" ;;
  upload) upload_bytes ;;
  auto)   upload_hosted || { echo "Falling back to download and upload"; start_session; upload_bytes; } ;;
  *)      fail "unknown MODE '${MODE}'" ;;
esac
note "Video handed to Facebook"

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
    note "Reel published: https://www.facebook.com/reel/${VIDEO_ID}"
    echo "### Reel published: https://www.facebook.com/reel/${VIDEO_ID}" >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
    exit 0
  fi
  [ "$vs" = "error" ] && fail "Facebook reported a processing error: $(echo "$st" | jq -c '.status')"
  sleep 10
done
fail "timed out waiting for Facebook to finish processing video ${VIDEO_ID}"
