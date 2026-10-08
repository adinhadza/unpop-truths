import subprocess, os, sys, math
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from kokoro_onnx import Kokoro
S=os.path.dirname(os.path.abspath(__file__)); W,H,FPS=1080,1920,30
K="/tmp/claude-0/-home-claude/aafc61c1-2e74-5f59-9ff9-dda5998f22ae/scratchpad/kok/"
PB="/usr/share/fonts/truetype/google-fonts/Poppins-"
F=lambda w,s: ImageFont.truetype(PB+w+".ttf",s)
YEL=(255,214,10); INK=(15,18,28); WHITE=(255,255,255); RED=(226,45,45); MAG=(150,24,84)
kok=Kokoro(K+"kokoro.onnx",K+"voices.bin")
mascot=Image.open("/home/claude/unpop-truths/drbeetroot/assets/mascot.jpg").convert("RGB").resize((130,130),Image.LANCZOS)
def voice(lines,name,pad=0.35):
    aud=[];d=[]
    for t in lines:
        a,sr=kok.create(t,voice="af_heart",speed=0.97,lang="en-us"); a=np.concatenate([a,np.zeros(int(sr*pad),dtype=a.dtype)]); aud.append(a); d.append(len(a)/sr)
    sf.write(f"{S}/{name}.wav",np.concatenate(aud),sr); return d
def ctext(d,cx,y,t,font,fill,**kw):
    w=d.textlength(t,font=font); d.text((cx-w/2,y),t,font=font,fill=fill,**kw)
def fit(d,t,weight,size,maxw):
    while d.textlength(t,font=F(weight,size))>maxw: size-=2
    return F(weight,size)
def badge(im,y,dark=False):
    d=ImageDraw.Draw(im); d.ellipse((40,y,190,y+150),fill=WHITE,outline=(220,220,220),width=3)
    m=Image.new("L",(130,130),0); ImageDraw.Draw(m).ellipse((0,0,130,130),fill=255); im.paste(mascot,(50,y+10),m)
    d.text((210,y+28),"Dr. Beetroot",font=F("Bold",44),fill=WHITE if dark else INK)
    d.text((210,y+88),"General wellness info. Not medical advice.",font=F("Medium",26),fill=(225,225,225) if dark else (110,110,110))
class Enc:
    def __init__(s,out,wav,extra=None):
        s.p=subprocess.Popen(["ffmpeg","-nostdin","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",wav,"-c:v","libx264","-crf","19","-preset","fast","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",out],stdin=subprocess.PIPE)
    def w(s,im): s.p.stdin.write(im.tobytes())
    def close(s): s.p.stdin.close(); s.p.wait()
ease=lambda x: 1-(1-min(max(x,0),1))**3

# ---------- 1. Whiteboard: problem -> food (inspired by Health Tips Daily) ----------
def v1():
    lines=["Three everyday problems, three simple foods.","Tired in the afternoon? Banana and oats give you steady energy.","Dry skin? Avocado and walnuts feed your skin with healthy fats.","Restless nights? Kiwi and warm milk help you wind down.","Follow Doctor Beetroot for more."]
    d=voice(lines,"v1"); src=Image.open(S+"/img2.jpg").convert("RGB")
    rows=[src.crop((0,int(i*1376/3)+(34 if i else 0),768,int((i+1)*1376/3)+(34 if i<2 else 0))).resize((1080,645),Image.LANCZOS) for i in range(3)]
    labs=[("TIRED AFTERNOONS","BANANA + OATS"),("DRY SKIN","AVOCADO + WALNUTS"),("RESTLESS NIGHTS","KIWI + WARM MILK")]
    def base(title2):
        im=Image.new("RGB",(W,H),WHITE); dr=ImageDraw.Draw(im)
        ctext(dr,540,170,"3 everyday problems",F("Bold",76),INK); ctext(dr,540,270,title2,F("Bold",76),MAG)
        dr.line((330,385,750,385),fill=RED,width=8); badge(im,1700); return im
    e=Enc(S+"/1-whiteboard-problem-food.mp4",S+"/v1.wav")
    scenes=[None,0,1,2,None]
    for si,(sc,dur) in enumerate(zip(scenes,d)):
        n=int(round(dur*FPS)); b=base("3 simple foods")
        if sc is None:
            if si==0:
                # preview: all three rows small, fading in
                for f in range(n):
                    im=b.copy()
                    for r in range(3):
                        a=ease((f/FPS-0.25*r)/0.5)
                        if a>0:
                            small=rows[r].resize((756,451),Image.LANCZOS); x=int(162+(1-a)*60); im.paste(small,(x,440+r*410))
                    e.w(im)
            else:
                for f in range(n):
                    im=Image.new("RGB",(W,H),WHITE); dr=ImageDraw.Draw(im)
                    big=Image.open("/home/claude/unpop-truths/drbeetroot/assets/logo.jpg").convert("RGB").resize((700,700),Image.LANCZOS); im.paste(big,(190,380))
                    ctext(dr,540,1130,"Dr. Beetroot",F("Bold",110),MAG); ctext(dr,540,1280,"Follow for daily wellness tips",F("Bold",52),INK)
                    ctext(dr,540,1780,"General wellness info. Not medical advice.",F("Medium",28),(110,110,110)); e.w(im)
            continue
        row=rows[sc]; l,r=labs[sc]
        for f in range(n):
            t=f/FPS; im=b.copy(); dr=ImageDraw.Draw(im)
            ctext(dr,540,450,f"{sc+1} of 3",F("Medium",40),(120,120,120))
            pl=ease(t/0.9); pr=ease((t-1.3)/0.9)   # hand-drawn wipe: problem first, then food
            if pl>0: im.paste(row.crop((0,0,int(540*pl),645)),(0,560))
            if pr>0: im.paste(row.crop((540,0,540+int(540*pr),645)),(540,560))
            if t>0.7: ctext(dr,270,1240,l,fit(dr,l,"Bold",50,500),INK)
            if t>1.2:
                a=ease((t-1.2)/0.4); dr.line((470,880,470+int(140*a),880),fill=RED,width=12)
                if a>0.95: dr.polygon([(610,855),(650,880),(610,905)],fill=RED)
            if t>2.0:
                ctext(dr,810,1240,r,fit(dr,r,"Bold",50,500),MAG); a=ease((t-2.0)/0.5); dr.line((810-230*a,1312,810+230*a,1312),fill=RED,width=8)
            e.w(im)
    e.close()

# ---------- 2. Food -> body infographic with flowing streams (inspired by Beyond The Surface) ----------
def v2():
    lines=["Six foods, six body connections.","Blueberries for your brain.","Carrots for your eyes.","Yogurt for your gut.","Spinach for your muscles.","Almonds for your skin.","And water for your kidneys.","Follow Doctor Beetroot for more."]
    d=voice(lines,"v2",pad=0.25); src=Image.open(S+"/img3.jpg").convert("RGB")
    sc=1740/1376; iw=int(768*sc); img=src.resize((iw,1740),Image.LANCZOS); ox=(W-iw)//2
    bgc=src.resize((1,1)).getpixel((0,0)); bg=src.resize((W,H)).filter(ImageFilter.GaussianBlur(60)); bg.paste(img,(ox,0))
    dr=ImageDraw.Draw(bg); dr.rectangle((0,1740,W,H),fill=(8,40,56)); badge(bg,1756,dark=True)
    ys=[int(v/1376*1740) for v in (150,375,600,825,1040,1250)]
    cols=[(110,140,255),(255,150,40),(250,250,240),(90,220,110),(230,170,110),(120,210,255)]
    x0=ox+int(250*sc); x1=ox+int(545*sc)
    def stream(layer,i,p):
        if p<=0: return
        pts=[]; n=60
        for k in range(int(n*p)+1):
            u=k/n; x=x0+(x1-x0)*u; y=ys[i]-10+math.sin(u*math.pi*2)*26*(1-u*0.3); pts.append((x,y))
        if len(pts)>1:
            dl=ImageDraw.Draw(layer); dl.line(pts,fill=cols[i]+(255,),width=20,joint="curve")
            hx,hy=pts[-1]; dl.ellipse((hx-18,hy-18,hx+18,hy+18),fill=cols[i]+(255,))
    e=Enc(S+"/2-food-to-body-streams.mp4",S+"/v2.wav")
    starts=np.cumsum([0]+d); total=starts[-1]; N=int(round(total*FPS))
    for f in range(N):
        t=f/FPS; layer=Image.new("RGBA",(W,H),(0,0,0,0))
        for i in range(6):
            stream(layer,i,ease((t-starts[i+1])/0.9))
        glow=layer.filter(ImageFilter.GaussianBlur(14)); im=bg.copy().convert("RGBA")
        im=Image.alpha_composite(im,glow); im=Image.alpha_composite(im,layer)
        # shimmer highlight along finished streams
        dl=ImageDraw.Draw(im)
        for i in range(6):
            if t>starts[i+1]+0.9:
                u=((t*0.6+i*0.17)%1); x=x0+(x1-x0)*u; y=ys[i]-10+math.sin(u*math.pi*2)*26*(1-u*0.3); dl.ellipse((x-9,y-9,x+9,y+9),fill=(255,255,255,230))
        e.w(im.convert("RGB"))
    e.close()

# ---------- 4. Habit grid with red underline (inspired by Health & Kids Care) ----------
def v4():
    lines=["Six daily habits your body loves.","A ten minute walk lifts your mood.","A glass of water in the morning wakes up your body.","Seven to nine hours of sleep sharpens your focus.","A morning stretch loosens your joints.","Morning sunlight helps set your sleep clock.","Slow, deep breathing calms your mind.","Follow Doctor Beetroot for more."]
    d=voice(lines,"v4",pad=0.3)
    labs=[("10-MINUTE WALK","BETTER MOOD"),("MORNING WATER","HYDRATION"),("7 TO 9 HOURS SLEEP","SHARPER FOCUS"),("MORNING STRETCH","LOOSER JOINTS"),("MORNING SUNLIGHT","STEADY SLEEP CLOCK"),("DEEP BREATHING","CALMER MIND")]
    cells=[]
    for name in ("img1.jpg","img0.jpg"):
        g=Image.open(S+"/"+name).convert("RGB")
        for r in range(3):
            row=[g.crop((c*384+12,int(r*1376/3)+10,(c+1)*384-12,int((r+1)*1376/3)-10)).resize((300,366),Image.LANCZOS) for c in range(2)]
            cells.append(row)
    def base():
        im=Image.new("RGB",(W,H),WHITE); dr=ImageDraw.Draw(im)
        ctext(dr,540,110,"6 daily habits",F("Bold",84),INK); ctext(dr,540,215,"your body loves",F("Bold",84),MAG); badge(im,1740); return im
    e=Enc(S+"/4-habit-grid.mp4",S+"/v4.wav")
    starts=np.cumsum([0]+d)
    def screen(im,dr,page,t):
        for r in range(3):
            idx=page*3+r; ts=starts[idx+1]
            if t<ts: continue
            a=ease((t-ts)/0.35); y=350+r*455
            for c in range(2):
                cx=285+c*510; cell=cells[idx][c]
                if a<1: cell=cell.resize((max(2,int(300*(0.7+0.3*a))),max(2,int(366*(0.7+0.3*a)))))
                im.paste(cell,(cx-cell.width//2,y+183-cell.height//2))
                lab=labs[idx][c]; fo=fit(dr,lab,"Bold",40,480); ctext(dr,cx,y+372,lab,fo,INK)
                u=ease((t-ts-0.45-0.35*c)/0.45)
                if u>0:
                    w=dr.textlength(lab,font=fo); dr.line((cx-w/2,y+430,cx-w/2+w*u,y+430),fill=RED,width=7)
            if t>ts+0.3:
                dr.line((505,y+183,575,y+183),fill=(170,170,170),width=6); dr.polygon([(575,y+168),(600,y+183),(575,y+198)],fill=(170,170,170))
    for f in range(int(round(starts[-1]*FPS))):
        t=f/FPS; im=base(); dr=ImageDraw.Draw(im)
        if t<starts[1]:
            ctext(dr,540,820,"Small habits.",F("Bold",90),INK); ctext(dr,540,940,"Big difference.",F("Bold",90),RED)
        elif t<starts[4]: screen(im,dr,0,t)
        elif t<starts[7]: screen(im,dr,1,t)
        else:
            big=Image.open("/home/claude/unpop-truths/drbeetroot/assets/logo.jpg").convert("RGB").resize((640,640),Image.LANCZOS); im.paste(big,(220,480))
            ctext(dr,540,1180,"Follow Dr. Beetroot",F("Bold",84),MAG); ctext(dr,540,1300,"for daily wellness tips",F("Bold",52),INK)
        e.w(im)
    e.close()

# ---------- 3. Realistic recipe clip (inspired by Good Health Daily) ----------
def v3():
    lines=["Try this warm ginger lemon tea.","Simmer fresh ginger, lemon and mint for ten minutes.","Pour it into a mug and stir in a spoon of honey.","A cozy drink that soothes your throat.","Follow Doctor Beetroot for more."]
    d=voice(lines,"v3",pad=0.45); starts=np.cumsum([0]+d); total=starts[-1]
    texts=[("GINGER LEMON TEA","warm and soothing"),("SIMMER 10 MINUTES","ginger · lemon · mint"),("ADD HONEY","one spoon, stir well"),("SIP SLOWLY","soothes your throat"),("FOLLOW","for daily wellness tips")]
    ovs=[]
    for i,(big,sub) in enumerate(texts):
        im=Image.new("RGBA",(W,H),(0,0,0,0)); g=Image.new("L",(1,H))
        for y in range(H): g.putpixel((0,y),int(205*max(0,(y-950)/970)**1.2))
        im.paste(Image.new("RGBA",(W,H),(0,0,0,255)),(0,0),g.resize((W,H))); dr=ImageDraw.Draw(im)
        fo=fit(dr,big,"Bold",130,W-110); ctext(dr,540,1230,big,fo,YEL,stroke_width=6,stroke_fill=INK)
        ctext(dr,540,1230+fo.size+34,sub,F("Bold",64),WHITE,stroke_width=4,stroke_fill=INK)
        badge(im,1700,dark=True); p=f"{S}/v3ov{i}.png"; im.save(p); ovs.append(p)
    da=starts[2]; db=total-starts[2]; sa=8.0/da; sb=8.0/db   # pot clip covers the first two lines, pour clip the rest
    fc=f"[0:v]scale={W}:{H}:flags=lanczos,setpts=PTS/{sa:.4f},fps={FPS},trim=0:{da:.3f},setpts=PTS-STARTPTS[a];[1:v]scale={W}:{H}:flags=lanczos,setpts=PTS/{sb:.4f},fps={FPS},trim=0:{db:.3f},setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1[v0]"
    last="v0"
    for i,p in enumerate(ovs):
        fc+=f";[{last}][{i+3}:v]overlay=0:0:enable='between(t,{starts[i]:.3f},{starts[i+1]:.3f})'[v{i+1}]"; last=f"v{i+1}"
    fc+=f";[0:a]atempo={max(sa,0.5):.4f}[x];[1:a]atempo={max(sb,0.5):.4f}[y];[x][y]concat=n=2:v=0:a=1,volume=0.22[amb];[2:a][amb]amix=inputs=2:duration=first:normalize=0[aout]"
    cmd=["ffmpeg","-nostdin","-y","-loglevel","error","-i",S+"/pot.mp4","-i",S+"/pour.mp4","-i",S+"/v3.wav"]+sum((["-loop","1","-i",p] for p in ovs),[])+["-filter_complex",fc,"-map",f"[{last}]","-map","[aout]","-t",f"{total:.3f}","-c:v","libx264","-crf","19","-preset","fast","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",S+"/3-recipe-ginger-lemon-tea.mp4"]
    subprocess.run(cmd,check=True)
for fn in sys.argv[1:]: globals()[fn](); print(fn,"done")
