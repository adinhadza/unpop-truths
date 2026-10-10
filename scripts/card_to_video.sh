#!/usr/bin/env bash
# Turns one finished card image (for example a 1080x1350 news card) into a short vertical video for a Reel.
# Usage: card_to_video.sh IMAGE_IN VIDEO_OUT [SECONDS]
# - The video is 1080x1920 at 30 frames a second, with no sound (music is added afterwards).
# - The card sits near the top of the frame and grows very slowly, so the picture is not completely still.
#   It is placed a little above the middle so the footer stays clear of the caption Facebook draws at the bottom.
# - The space above and below the card is filled with a dark, blurred copy of the card.
set -euo pipefail
in="$1"; out="$2"; secs="${3:-10}"
frames=$(( secs * 30 ))

ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i "$in" -filter_complex "
  [0:v]format=rgb24,split=2[bgsrc][fgsrc];
  [bgsrc]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:4,eq=brightness=-0.28:saturation=0.7[bg];
  [fgsrc]scale=1080:1350:force_original_aspect_ratio=decrease,pad=1080:1350:(ow-iw)/2:(oh-ih)/2:black,scale=2160:2700:flags=lanczos,
         zoompan=z='1+0.03*on/${frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1350:fps=30[fg];
  [bg][fg]overlay=0:200,format=yuv420p[v]" \
  -map "[v]" -frames:v "$frames" -r 30 -c:v libx264 -preset medium -crf 18 -movflags +faststart "$out"
