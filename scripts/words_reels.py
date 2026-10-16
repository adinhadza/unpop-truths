#!/usr/bin/env python3
"""Original Words That Stay quote-card Reels, with synthesized piano-like audio."""
import argparse, datetime, math, os, random, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

MESSAGES = [
 ("Some people are a blessing\njust by being there.", "Never forget the quiet ones who stayed."),
 ("One day, the ordinary moments\nbecome your favorite memories.", "Hold your family close today."),
 ("You are never too old\nto begin again.", "Your next chapter still matters."),
 ("1. Call your parents.\n2. Keep your promises.\n3. Say thank you.", "The little things become everything."),
 ("1. Choose peace.\n2. Forgive slowly.\n3. Love deeply.", "Growing older teaches us what lasts."),
 ("1. Listen more.\n2. Judge less.\n3. Be kind.", "A gentle heart is never wasted."),
 ("The strongest people\nare often the ones\nwho cry in private.", "Be gentle with what you cannot see."),
 ("Years from now,\nyou won't remember the dishes.\nYou'll remember who was at the table.", "Make time for the people you love."),
 ("Sometimes a simple\n'I'm proud of you'\nheals years of silence.", "Say the words while you can."),
]
def font(size):
 for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf"):
  if os.path.exists(path): return ImageFont.truetype(path,size)
 raise RuntimeError("Serif font not found")
def wrap(draw, text, f, width):
 lines=[]
 for paragraph in text.split("\n"):
  words=paragraph.split(); line=""
  for word in words:
   nxt=(line+" "+word).strip()
   if draw.textbbox((0,0),nxt,font=f)[2]>width and line: lines.append(line);line=word
   else:line=nxt
  lines.append(line)
 return lines
KEYWORDS = ["blessing", "memories", "begin", "promises", "peace", "kind", "strongest", "remember", "proud"]
def card(path, headline, subtitle, keyword):

 im=Image.new("RGB",(1080,1920),(238,230,213));d=ImageDraw.Draw(im)
 rng=random.Random(17)
 for _ in range(9500):
  x=rng.randrange(1080);y=rng.randrange(1920);v=rng.randrange(-10,11)
  d.point((x,y),fill=tuple(max(0,min(255,c+v)) for c in (238,230,213)))
 d.line((125,280,955,280),fill=(160,157,132),width=2)
 d.line((125,1640,955,1640),fill=(160,157,132),width=2)
 d.text((540,355),"WORDS THAT STAY",font=font(33),fill=(90,105,83),anchor="mm")
 f=font(66); lines=wrap(d,headline,f,840)
 while len(lines)>8:
  f=font(f.size-4);lines=wrap(d,headline,f,840)
 lineheight=f.size*1.42
 y=950-(len(lines)*lineheight)/2
 for line in lines:
  # Draw centered words separately so exactly one meaningful word stands out.
  parts=line.split(" ")
  widths=[d.textlength(word,font=f) for word in parts]
  gap=d.textlength(" ",font=f)
  xpos=540-(sum(widths)+gap*max(0,len(parts)-1))/2
  for word,w in zip(parts,widths):
   clean=word.strip(".,!?\\"'0123456789").lower()
   color=(166,92,67) if clean==keyword else (48,44,40)
   d.text((int(xpos),int(y)),word,font=f,fill=color,stroke_width=1 if clean==keyword else 0,anchor="lt")
   xpos+=w+gap
  y+=lineheight
 sf=font(34);sub=wrap(d,subtitle,sf,800)
 for i,line in enumerate(sub):d.text((540,1350+i*52),line,font=sf,fill=(96,98,87),anchor="mt")
 d.text((540,1730),"A LITTLE REMINDER FOR TODAY",font=font(25),fill=(110,117,101),anchor="mm")
 im.save(path)
def audio(path,seconds,seed):
 sr=22050; t=np.arange(int(sr*seconds))/sr; out=np.zeros(len(t),dtype=np.float64)
 # Original generated tones, not a sampled or copyrighted recording.
 notes=[(220,0),(261.63,1.5),(329.63,3),(392,4.5),(329.63,6),(261.63,7.5),(246.94,9)]
 shift=seed%3-1
 for freq,start in notes:
  start+=0.05; n=int(start*sr);end=min(len(t),n+int(2.8*sr))
  if n>=end:continue
  tt=np.arange(end-n)/sr
  env=(1-np.exp(-tt*28))*np.exp(-tt*1.7)
  sig=(np.sin(2*np.pi*freq*(2**(shift/12))*tt)+.22*np.sin(2*np.pi*2*freq*tt)+.09*np.sin(2*np.pi*3*freq*tt))*env
  out[n:end]+=sig*.13
 out*=np.minimum(1,np.minimum(t/.4,(seconds-t)/.7)).clip(0,1)
 pcm=np.int16(np.clip(out,-1,1)*32767)
 with wave.open(str(path),"wb") as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm.tobytes())
def main():
 p=argparse.ArgumentParser();p.add_argument("--output",default="output/words");p.add_argument("--count",type=int,default=1);p.add_argument("--start",type=int,default=0);a=p.parse_args()
 if not 1<=a.count<=9: p.error("count must be 1..9")
 out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 for k in range(a.count):
  i=(a.start+k)%len(MESSAGES);name=f"words-{i+1:02d}"
  png=out/(name+".png");wav=out/(name+".wav");mp4=out/(name+".mp4")
  card(png,*MESSAGES[i],KEYWORDS[i]);audio(wav,12,i)
  subprocess.run(["ffmpeg","-nostdin","-loglevel","error","-y","-loop","1","-framerate","24","-i",str(png),"-i",str(wav),"-t","12","-vf","scale=1080:1920,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","27","-r","24","-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",str(mp4)],check=True)
  (out/(name+".txt")).write_text(MESSAGES[i][1]+"\n\n#WordsThatStay #LifeLessons #Family #Gratitude\n")
  print(mp4)
if __name__=="__main__":main()
