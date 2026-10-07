#!/usr/bin/env bash
# Mixes a music track into a video at a steady low level, with a short fade in and fade out.
# Usage: add_music.sh VIDEO_IN MUSIC_FILE VIDEO_OUT [LEVEL_DB]
# - Silence at the very start of the track is skipped, so the music is audible from the first second.
# - The part of the track that will be heard is measured and adjusted to LEVEL_DB (average level),
#   so quiet and loud tracks end up sounding equally soft under the text.
# - The picture is copied untouched. Any sound already in the video is replaced by the music.
set -euo pipefail
in="$1"; music="$2"; out="$3"; level="${4:--27}"

dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
fade_out=$(awk -v d="$dur" 'BEGIN { s = d - 1.5; if (s < 0) s = 0; printf "%.3f", s }')
trim="silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05"

# Measure the average level of the section that will actually be used.
measured=$(ffmpeg -nostdin -hide_banner -stream_loop -1 -i "$music" -vn -af "${trim},volumedetect" -t "$dur" -f null - 2>&1 \
  | sed -n 's/.*mean_volume: \(-\{0,1\}[0-9.]*\) dB.*/\1/p' | tail -1)
[ -n "$measured" ] || { echo "could not measure the music level" >&2; exit 1; }
gain=$(awk -v t="$level" -v m="$measured" 'BEGIN { g = t - m; if (g > 15) g = 15; if (g < -40) g = -40; printf "%.1f", g }')

ffmpeg -nostdin -v error -y -i "$in" -stream_loop -1 -i "$music" \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 160k -ar 44100 \
  -af "${trim},volume=${gain}dB,afade=t=in:st=0:d=0.6,afade=t=out:st=${fade_out}:d=1.5" \
  -t "$dur" -movflags +faststart "$out"
echo "measured=${measured}dB gain=${gain}dB"
