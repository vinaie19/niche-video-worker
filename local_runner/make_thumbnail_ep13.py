from PIL import Image, ImageDraw, ImageFont
S="/tmp/claude-1000/-home-fl-lpt-587-Desktop-niche-video-worker/ca15bdf0-d8ad-49c9-9dde-d11122fc9f7f/scratchpad/th13"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COND="/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
GOLD=(255,214,140); WHITE=(255,255,255); CYAN=(120,210,255)
W,H=1080,1920
def f(p,s): return ImageFont.truetype(p,s)
def load(p): return Image.open(p).convert("RGB").resize((W,H))
def shadow(d,xy,t,fnt,fill,anchor="mm"):
    for dx,dy in ((0,5),(0,-5),(5,0),(-5,0),(4,4),(-4,4),(4,-4),(-4,-4)):
        d.text((xy[0]+dx,xy[1]+dy),t,font=fnt,fill=(0,0,0),anchor=anchor)
    d.text(xy,t,font=fnt,fill=fill,anchor=anchor)
def track(d,xy,t,fnt,fill,sp=0):
    ws=[d.textlength(c,font=fnt) for c in t]; tot=sum(ws)+sp*(len(t)-1); x=xy[0]-tot/2
    for c,w in zip(t,ws):
        d.text((x,xy[1]),c,font=fnt,fill=fill); x+=w+sp
def scrim(img,top_frac,bot_frac,amt=0.72):
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
    ht=int(H*top_frac)
    for y in range(ht):
        od.line([(0,y),(W,y)],fill=(0,0,0,int(255*amt*(1-y/ht))))
    hb=int(H*bot_frac)
    for y in range(hb):
        od.line([(0,H-1-y),(W,H-1-y)],fill=(0,0,0,int(255*amt*(1-y/hb))))
    return Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")

src=f"{S}/e0.3.png"   # frame with the lightning bolt

# A — number dominant, label above
a=scrim(load(src),0.42,0.30); d=ImageDraw.Draw(a)
track(d,(W//2,215),"EARTH AS A BLACK HOLE",f(COND,46),CYAN,sp=7)
shadow(d,(W//2,400),"8.87",f(BOLD,290),WHITE)
shadow(d,(W//2,585),"MM",f(COND,110),GOLD)
d.line([(W//2-150,680),(W//2+150,680)],fill=CYAN,width=6)
shadow(d,(W//2,1735),"THE WHOLE PLANET",f(COND,72),WHITE)
a.save(f"{S}/thumb13_A.png")

# B — number + stakes, tighter
b=scrim(load(src),0.46,0.26); d=ImageDraw.Draw(b)
shadow(d,(W//2,320),"8.87 MM",f(BOLD,200),WHITE)
d.line([(W//2-230,455),(W//2+230,455)],fill=CYAN,width=6)
shadow(d,(W//2,560),"AND EARTH",f(COND,86),GOLD)
shadow(d,(W//2,660),"BECOMES A BLACK HOLE",f(COND,60),WHITE)
b.save(f"{S}/thumb13_B.png")

# C — question framing
c=scrim(load(src),0.40,0.34); d=ImageDraw.Draw(c)
track(d,(W//2,205),"CRUSH EARTH TO THIS SIZE",f(COND,44),CYAN,sp=6)
shadow(d,(W//2,390),"8.87",f(BOLD,300),WHITE)
shadow(d,(W//2,580),"MILLIMETRES",f(COND,74),GOLD)
shadow(d,(W//2,1700),"IT BECOMES",f(COND,64),WHITE)
shadow(d,(W//2,1780),"A BLACK HOLE",f(COND,64),WHITE)
c.save(f"{S}/thumb13_C.png")

big=Image.new("RGB",(330*3+40,587),"#111")
for i,k in enumerate("ABC"):
    big.paste(Image.open(f"{S}/thumb13_{k}.png").resize((330,587)),(i*(330+20),0))
big.save(f"{S}/variants.jpg",quality=93)
small=Image.new("RGB",(150*3+40,267),"#111")
for i,k in enumerate("ABC"):
    small.paste(Image.open(f"{S}/thumb13_{k}.png").resize((150,267)),(i*(150+20),0))
small.save(f"{S}/small.jpg",quality=93)
print("built A B C")
