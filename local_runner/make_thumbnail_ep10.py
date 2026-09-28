from PIL import Image, ImageDraw, ImageFont, ImageFilter
S="/tmp/claude-1000/-home-fl-lpt-587-Desktop-niche-video-worker/ca15bdf0-d8ad-49c9-9dde-d11122fc9f7f/scratchpad/th10"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COND="/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
W,H=1080,1920
AMBER=(255,176,72); CYAN=(120,210,255); WHITE=(255,255,255)
def f(p,s): return ImageFont.truetype(p,s)
def load(p): return Image.open(p).convert("RGB").resize((W,H))
def glow(img,xy,txt,fnt,fill,anchor="mm",rad=20):
    """soft glow behind type — keeps the artwork at full contrast, no grey scrim"""
    lay=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    d.text(xy,txt,font=fnt,fill=(0,0,0,240),anchor=anchor)
    lay=lay.filter(ImageFilter.GaussianBlur(rad))
    out=Image.alpha_composite(img.convert("RGBA"),lay)
    ImageDraw.Draw(out).text(xy,txt,font=fnt,fill=fill,anchor=anchor)
    return out.convert("RGB")
def track(d,xy,t,fnt,fill,sp=0):
    ws=[d.textlength(c,font=fnt) for c in t]; x=xy[0]-(sum(ws)+sp*(len(t)-1))/2
    for c,w in zip(t,ws): d.text((x,xy[1]),c,font=fnt,fill=fill); x+=w+sp

src=f"{S}/s0.3.png"   # the golden fireball, fully formed

# A — fireball clean up top, colossal number in the black lower third
a=load(src)
a=glow(a,(W//2,1330),"300",f(BOLD,460),WHITE,rad=30)
a=glow(a,(W//2,1600),"SUNS",f(COND,150),AMBER,rad=20)
d=ImageDraw.Draw(a); d.line([(W//2-260,1710),(W//2+260,1710)],fill=CYAN,width=7)
a=glow(a,(W//2,1800),"NO STAR GROWS PAST THIS",f(COND,54),CYAN,rad=14)
a.save(f"{S}/thumb10_A.png")

# B — statement-first, number as the punchline
b=load(src)
b=glow(b,(W//2,1270),"NO STAR",f(COND,132),WHITE,rad=20)
b=glow(b,(W//2,1395),"GROWS PAST",f(COND,132),WHITE,rad=20)
b=glow(b,(W//2,1640),"300 SUNS",f(BOLD,200),AMBER,rad=26)
b.save(f"{S}/thumb10_B.png")

# C — "THE WALL" framing, cyan rule under the number
c=load(src)
d=ImageDraw.Draw(c); track(d,(W//2,1240),"THE HARD CEILING ON STARS",f(COND,50),CYAN,sp=6)
c=glow(c,(W//2,1480),"300",f(BOLD,440),WHITE,rad=30)
c=glow(c,(W//2,1735),"SOLAR MASSES",f(COND,84),AMBER,rad=18)
c.save(f"{S}/thumb10_C.png")

for name,sz in (("variants",330),("small",150)):
    g=Image.new("RGB",(sz*3+40,int(sz*16/9)),"#111")
    for i,k in enumerate("ABC"):
        g.paste(Image.open(f"{S}/thumb10_{k}.png").resize((sz,int(sz*16/9))),(i*(sz+20),0))
    g.save(f"{S}/{name}.jpg",quality=93)
print("built A B C")
