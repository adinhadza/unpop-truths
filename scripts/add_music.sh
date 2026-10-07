#!/usr/bin/env bash
# Mixes a music track into a video at low volume, with a short fade in and fade out.
# Usage: add_music.sh VIDEO_IN MUSIC_FILE VIDEO_OUT [VOLUME]
# The picture is copied untouched. Any sound already in the video is replaced by the music.
set -euo pipefail
in="$1"; music="$2"; out="$3"; vol="${4:-0.35}"

dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
fade_out=$(awk -v d="$dur" 'BEGIN { s = d - 1.5; if (s < 0) s = 0; printf "%.3f", s }')

ffmpeg -nostdin -v error -y -i "$in" -stream_loop -1 -i "$music" \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 160k -ar 44100 \
  -af "volume=${vol},afade=t=in:st=0:d=0.6,afade=t=out:st=${fade_out}:d=1.5" \
  -t "$dur" -movflags +faststart "$out"
