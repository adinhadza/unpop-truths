#!/usr/bin/env bash
# Publishes one photo post to a Facebook Page using the Graph API.
# Needs: NEWS_PAGE_ID, NEWS_PAGE_TOKEN, IMAGE_URL.
# Optional: CAPTION, MODE (auto|hosted|upload),
#           PUBLISH_AT (a date and time such as 2026-10-08T15:00:00+02:00; empty = publish now),
#           DRY_RUN (true = fetch and check the image but do not post), GRAPH_VERSION.
set -euo pipefail

: "${NEWS_PAGE_ID:?NEWS_PAGE_ID secret is missing}"
NEWS_PAGE_TOKEN="$(bash "$(dirname "$0")/page_token.sh" "$NEWS_PAGE_ID" "${NEWS_PAGE_TOKEN:-}")"
[ -n "$NEWS_PAGE_TOKEN" ] || { echo "::error::no Facebook token: save FB_SYSTEM_TOKEN or NEWS_PAGE_TOKEN"; exit 1; }
: "${IMAGE_URL:?IMAGE_URL is missing}"
CAPTION="${CAPTION:-}"
MODE="${MODE:-auto}"
DRY_RUN="${DRY_RUN:-false}"
PUBLISH_AT="${PUBLISH_AT:-}"
PUBLISH_TS=""
VER="${GRAPH_VERSION:-v23.0}"
GRAPH="https://graph.facebook.com/${VER}"
echo "::add-mask::${IMAGE_URL}"

# Errors and progress are written as annotations so they can be read without opening the log.
fail() { echo "::error::$1"; exit 1; }
note() { echo "::notice::$1"; }

download_image() {
  curl -sSL --fail --connect-timeout 20 --max-time 120 -o card.img "$IMAGE_URL" || fail "could not download the image link"
  local size kind
  size=$(stat -c %s card.img)
  kind=$(file -b --mime-type card.img)
  case "$kind" in
    image/png|image/jpeg) ;;
    *) fail "the link did not return a PNG or JPEG (got ${kind})" ;;
  esac
  [ "$size" -gt 20000 ] || fail "downloaded image is too small (${size} bytes)"
  # Facebook rejects photos over 10 MB; large PNG exports are converted to JPEG.
  if [ "$size" -gt 9500000 ]; then
    command -v convert >/dev/null 2>&1 || fail "image is ${size} bytes (over Facebook's 10 MB limit) and cannot be converted here"
    convert card.img -quality 92 card.jpg && mv card.jpg card.img
    size=$(stat -c %s card.img)
  fi
  note "Image ready: ${size} bytes, ${kind}"
}

if [ -n "$PUBLISH_AT" ]; then
  PUBLISH_TS=$(date -u -d "$PUBLISH_AT" +%s 2>/dev/null) || fail "could not read the publish time '${PUBLISH_AT}'"
  NOW=$(date -u +%s)
  [ "$PUBLISH_TS" -ge $((NOW + 660)) ] || fail "publish time must be at least 11 minutes from now"
  [ "$PUBLISH_TS" -le $((NOW + 29 * 86400)) ] || fail "publish time must be within 29 days"
fi

# The image is always downloaded once so a broken link is caught before anything is sent to Facebook.
download_image

if [ "$DRY_RUN" = "true" ]; then
  note "Dry run: image checked, nothing was posted"
  exit 0
fi

SCHEDULE_ARGS=()
if [ -n "$PUBLISH_TS" ]; then
  SCHEDULE_ARGS=(-F "published=false" -F "scheduled_publish_time=${PUBLISH_TS}" -F "unpublished_content_type=SCHEDULED")
fi

post_hosted() {
  curl -sS --connect-timeout 20 --max-time 120 -X POST "${GRAPH}/${NEWS_PAGE_ID}/photos" \
    -F "url=${IMAGE_URL}" -F "caption=${CAPTION}" "${SCHEDULE_ARGS[@]}" \
    -F "access_token=${NEWS_PAGE_TOKEN}"
}
post_upload() {
  curl -sS --connect-timeout 20 --max-time 180 -X POST "${GRAPH}/${NEWS_PAGE_ID}/photos" \
    -F "source=@card.img" -F "caption=${CAPTION}" "${SCHEDULE_ARGS[@]}" \
    -F "access_token=${NEWS_PAGE_TOKEN}"
}
ok() { echo "$1" | jq -e '.id // .post_id' >/dev/null 2>&1; }
err_msg() { echo "$1" | jq -r '.error.message // "no error message returned"' 2>/dev/null || echo "unreadable response"; }

RESP=""
case "$MODE" in
  hosted) RESP=$(post_hosted) ;;
  upload) RESP=$(post_upload) ;;
  auto)
    RESP=$(post_hosted) || RESP=""
    if ! ok "$RESP"; then
      note "Facebook could not fetch the link itself ($(err_msg "$RESP")); uploading the file instead"
      RESP=$(post_upload)
    fi
    ;;
  *) fail "unknown mode '${MODE}'" ;;
esac

ok "$RESP" || fail "Facebook refused the photo: $(err_msg "$RESP")"
PHOTO_ID=$(echo "$RESP" | jq -r '.id // empty')
POST_ID=$(echo "$RESP" | jq -r '.post_id // empty')
if [ -n "$PUBLISH_TS" ]; then
  note "Photo scheduled for $(date -u -d "@${PUBLISH_TS}" '+%Y-%m-%d %H:%M UTC'), photo id ${PHOTO_ID}"
else
  note "Photo published, photo id ${PHOTO_ID}${POST_ID:+, post id ${POST_ID}}"
fi
