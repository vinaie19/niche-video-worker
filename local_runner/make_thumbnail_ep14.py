from PIL import Image, ImageDraw, ImageFont, ImageFilter
S="/tmp/claude-1000/-home-fl-lpt-587-Desktop-niche-video-worker/ca15bdf0-d8ad-49c9-9dde-d11122fc9f7f/scratchpad/th14"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COND="/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
W,H=1080,1920
AMBER=(255,176,72); CYAN=(120,210,255); WHITE=(255,255,255)
def f(p,s): return ImageFont.truetype(p,s)
def load(p): return Image.open(p).convert("RGB").resize((W,H))
def glow(img,xy,txt,fnt,fill,anchor="mm",rad=18):
    """text with a soft glow instead of a hard scrim — keeps the artwork clean"""
    lay=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    d.text(xy,txt,font=fnt,fill=(0,0,0,235),anchor=anchor)
    lay=lay.filter(ImageFilter.GaussianBlur(rad))
    out=Image.alpha_composite(img.convert("RGBA"),lay)
    d2=ImageDraw.Draw(out); d2.text(xy,txt,font=fnt,fill=fill,anchor=anchor)
    return out.convert("RGB")
def track(d,xy,t,fnt,fill,sp=0):
    ws=[d.textlength(c,font=fnt) for c in t]; x=xy[0]-(sum(ws)+sp*(len(t)-1))/2
    for c,w in zip(t,ws): d.text((x,xy[1]),c,font=fnt,fill=fill); x+=w+sp

# A — ORANGE STAR, number owns the empty upper half. No scrim.
a=load(f"{S}/p15.png")
a=glow(a,(W//2,430),"716",f(BOLD,420),WHITE,rad=26)
d=ImageDraw.Draw(a); track(d,(W//2,690),"ROTATIONS PER SECOND",f(COND,56),AMBER,sp=8)
a.save(f"{S}/thumb14_A.png")

# B — WHITE STAR, text stacked in the natural black gutter on the right.
b=load(f"{S}/p3.png")
# right-hand black gutter is only ~480px wide — size the type to FIT it
b=glow(b,(620,600),"716",f(BOLD,200),WHITE,anchor="lm",rad=22)
b=glow(b,(624,742),"TIMES",f(COND,64),AMBER,anchor="lm",rad=14)
b=glow(b,(624,812),"A SECOND",f(COND,64),AMBER,anchor="lm",rad=14)
d=ImageDraw.Draw(b); d.line([(622,868),(1000,868)],fill=CYAN,width=6)
b=glow(b,(624,922),"FASTEST SPINNING",f(COND,38),CYAN,anchor="lm",rad=10)
b=glow(b,(624,972),"OBJECT KNOWN",f(COND,38),CYAN,anchor="lm",rad=10)
b.save(f"{S}/thumb14_B.png")

# C — ORANGE STAR, rule echoes the equatorial streak, number below it.
c=load(f"{S}/p17.png")
d=ImageDraw.Draw(c)
c=glow(c,(W//2,300),"THIS STAR SPINS",f(COND,64),CYAN,rad=14)
c=glow(c,(W//2,1430),"716",f(BOLD,400),WHITE,rad=26)
c=glow(c,(W//2,1690),"TIMES A SECOND",f(COND,72),AMBER,rad=16)
c.save(f"{S}/thumb14_C.png")

for name,sz in (("variants",330),("small",150)):
    g=Image.new("RGB",(sz*3+40,int(sz*16/9)),"#111")
    for i,k in enumerate("ABC"):
        g.paste(Image.open(f"{S}/thumb14_{k}.png").resize((sz,int(sz*16/9))),(i*(sz+20),0))
    g.save(f"{S}/{name}.jpg",quality=93)
print("built A B C")
