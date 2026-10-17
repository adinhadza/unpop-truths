#!/usr/bin/env python3
"""Original Words That Stay quote-card Reels, with synthesized piano-like audio."""
import argparse, datetime, math, os, random, subprocess, wave, re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
def vintage_background(index):
 """Three original warm editorial designs: sunlit wall, floral still life, parchment."""
 style=index%10
 # Five sunlit walls, three floral still lifes, two parchment cards per ten.
 kind="wall" if style in (0,1,3,5,8) else ("flowers" if style in (2,4,7) else "paper")
 palettes={"wall":((238,228,209),(218,200,172)),
           "flowers":((234,220,198),(201,175,145)),
           "paper":((243,230,207),(224,204,173))}
 top,bottom=palettes[kind]
 yy,xx=np.mgrid[0:1920,0:1080]
 t=(yy/1919.0)[...,None]
 sun=np.maximum(0,1-np.hypot((xx-180)/1100,(yy-300)/1800))
 shade=9*sun-8*((xx-540)/540)**2
 grain=np.random.default_rng(index*17+31).normal(0,2.4,(1920,1080))
 colors=np.asarray(top)[None,None,:]*(1-t)+np.asarray(bottom)[None,None,:]*t
 pixels=np.uint8(np.clip(colors+shade[...,None]+grain[...,None],0,255))
 im=Image.fromarray(pixels,"RGB")
 # Blurred organic shadow shapes stay outside the central reading zone.
 shadow=Image.new("RGBA",im.size,(0,0,0,0));s=ImageDraw.Draw(shadow)
 if kind in ("wall","flowers"):
  for side in (-1,1):
   xbase=30 if side<0 else 1060
   for j in range(5):
    cy=170+j*180+(index%3)*30
    cx=xbase+side*(-45-j*11)
    s.ellipse((cx-85,cy-25,cx+85,cy+35),fill=(84,76,51,32))
  shadow=shadow.filter(ImageFilter.GaussianBlur(46))
  im=Image.alpha_composite(im.convert("RGBA"),shadow)
 if kind=="flowers":
  decor=Image.new("RGBA",im.size,(0,0,0,0));dd=ImageDraw.Draw(decor)
  # Vase and dried stems confined to the lower-right corner.
  dd.ellipse((810,1665,1040,1735),fill=(89,65,47,45))
  dd.polygon([(857,1580),(998,1580),(973,1702),(880,1702)],fill=(160,120,85,125))
  dd.ellipse((857,1561,998,1600),fill=(177,136,97,150))
  for j in range(11):
   ex=865+j*14;ey=1280+(j%4)*44
   dd.line((925,1585,ex,ey),fill=(117,100,65,130),width=3)
   dd.ellipse((ex-12,ey-21,ex+12,ey+21),fill=(164,132,91,95))
  im=Image.alpha_composite(im,decor)
 if kind=="paper":
  decor=Image.new("RGBA",im.size,(0,0,0,0));dd=ImageDraw.Draw(decor)
  dd.rectangle((65,110,1015,1805),outline=(135,110,80,42),width=3)
  for j in range(4):
   yy=245+j*445
   dd.line((100,yy,980,yy+22),fill=(145,120,94,17),width=2)
  im=Image.alpha_composite(im,decor)
 return im.convert("RGB")

def card(path, headline, subtitle, keyword):

 im=vintage_background(KEYWORDS.index(keyword));d=ImageDraw.Draw(im)
 d.line((125,280,955,280),fill=(164,145,119),width=2)
 d.line((125,1640,955,1640),fill=(164,145,119),width=2)
 d.text((540,355),"WORDS THAT STAY",font=font(33),fill=(90,105,83),anchor="mm")
 # Fit the author's intended lines before wrapping: no orphaned highlight words.
 # Keep all text inside a generous safe margin for Facebook's mobile viewer.
 paragraphs=headline.split("\n")
 f=font(76)
 while f.size>36 and (any(d.textlength(p,font=f)>920 for p in paragraphs) or len(paragraphs)*f.size*1.65>790):
  f=font(f.size-2)
 lines=wrap(d,headline,f,920)
 lineheight=f.size*1.65
 y=925-(len(lines)-1)*lineheight/2
 for line in lines:
  # Draw centered words separately so exactly one meaningful word stands out.
  parts=line.split(" ")
  widths=[d.textlength(word,font=f) for word in parts]
  gap=d.textlength(" ",font=f)
  xpos=540-(sum(widths)+gap*max(0,len(parts)-1))/2
  for word,w in zip(parts,widths):
   clean=re.sub(r'[^a-z]', '', word.lower())
   if clean==keyword:
    # A soft terracotta marker behind the word, with warm dark text on top.
    bbox=d.textbbox((int(xpos),int(y)),word,font=f,anchor="lt")
    d.rounded_rectangle((bbox[0]-9,bbox[1]-4,bbox[2]+9,bbox[3]+6),radius=8,fill=(201,151,125))
   d.text((int(xpos),int(y)),word,font=f,fill=(48,44,40),anchor="lt")
   xpos+=w+gap
  y+=lineheight
 sf=font(33);sub=wrap(d,subtitle,sf,780)
 for i,line in enumerate(sub):d.text((540,1470+i*60),line,font=sf,fill=(96,98,87),anchor="mt")
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
