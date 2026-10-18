#!/usr/bin/env bash
# Two Paths Mindset: 8s Flow clip + 2s summary card + 2s logo card = 12s reel.
# usage: build_reel.sh RAW.mp4 EMBLEM.png "summary line 1" "summary line 2 (gold)" OUT.mp4
set -euo pipefail
RAW="$1"; LOGO="$2"; L1="$3"; L2="$4"; OUT="$5"
F=${FONTDIR:-$(cd "$(dirname "$0")/../assets/fonts" && pwd)}
T=$(mktemp -d); printf '%s' "$L1" > "$T/l1.txt"; printf '%s' "$L2" > "$T/l2.txt"
ffmpeg -v error -y -i "$RAW" -loop 1 -t 2 -i "$LOGO" -filter_complex "
[0:v]fps=30,scale=720:1280,format=yuv420p,split[a][b];
[b]trim=start=7.9,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=2,trim=duration=2,gblur=sigma=14,eq=brightness=-0.22:saturation=0.8,
drawtext=fontfile=$F/Poppins-Bold.ttf:textfile=$T/l1.txt:fontsize=50:fontcolor=white:x=(w-text_w)/2:y=h*0.44:borderw=2:bordercolor=black@0.4:alpha='min(1,t/0.35)',
drawtext=fontfile=$F/Poppins-Bold.ttf:textfile=$T/l2.txt:fontsize=50:fontcolor=0xE8C36A:x=(w-text_w)/2:y=h*0.44+70:borderw=2:bordercolor=black@0.4:alpha='min(1,max(0,(t-0.3)/0.35))',
setsar=1[sum];
[a]trim=duration=8,setpts=PTS-STARTPTS,setsar=1[main];
color=c=0x0A1726:s=720x1280:r=30:d=2,format=rgb24,geq=r='10+8*(1-Y/H)':g='16+14*(1-Y/H)':b='26+18*(1-Y/H)'[bg];
[1:v]scale=680:-1,format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='255*min(1,min(min(X,W-X),min(Y,H-Y))/70)',fps=30[lg];
[bg][lg]overlay=(W-w)/2:(H-h)/2-30,format=yuv420p,fade=t=in:d=0.4,setsar=1[logo];
[main][sum]concat=n=2:v=1:a=0,drawtext=fontfile=$F/Poppins-Medium.ttf:text='TWO PATHS MINDSET':fontsize=24:fontcolor=white@0.92:x=w-text_w-22:y=h-text_h-24:borderw=2:bordercolor=black@0.45[body];
[body][logo]concat=n=2:v=1:a=0[v];
[0:a]atrim=duration=8,afade=t=out:st=7.2:d=0.8,apad=whole_dur=12[a]" \
 -map "[v]" -map "[a]" -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart "$OUT"
rm -rf "$T"
