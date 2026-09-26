from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import os
S="/tmp/claude-1000/-home-fl-lpt-587-Desktop-niche-video-worker/ca15bdf0-d8ad-49c9-9dde-d11122fc9f7f/scratchpad/thumb"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COND="/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
GOLD=(255,214,140); WHITE=(255,255,255); CYAN=(120,210,255)
W,H=1080,1920

def load(p): return Image.open(p).convert("RGB").resize((W,H))
def f(path,size): return ImageFont.truetype(path,size)

def track(d, xy, text, font, fill, spacing=0, anchor_center=True):
    """draw letter-spaced text; returns width"""
    widths=[d.textlength(c,font=font) for c in text]
    total=sum(widths)+spacing*(len(text)-1)
    x = xy[0]-total/2 if anchor_center else xy[0]
    for c,w in zip(text,widths):
        d.text((x,xy[1]),c,font=font,fill=fill)
        x += w+spacing
    return total

def shadow_text(d, xy, text, font, fill, anchor="mm", blur=6):
    # cheap drop shadow for legibility over bright areas
    for dx,dy in ((0,4),(0,-4),(4,0),(-4,0),(3,3),(-3,3),(3,-3),(-3,-3)):
        d.text((xy[0]+dx,xy[1]+dy),text,font=font,fill=(0,0,0),anchor=anchor)
    d.text(xy,text,font=font,fill=fill,anchor=anchor)

def darken_top(img, frac=0.55, amount=0.45):
    """darken the upper band so text pops"""
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
    h=int(H*frac)
    for y in range(h):
        a=int(255*amount*(1-y/h))
        od.line([(0,y),(W,y)],fill=(0,0,0,a))
    return Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")

# ---------- Variant A : number dominant ----------
a=load(f"{S}/clean_10.png"); a=darken_top(a,0.60,0.60)
d=ImageDraw.Draw(a)
track(d,(W//2,235),"SOLAR ESCAPE VELOCITY",f(COND,46),CYAN,spacing=7)
shadow_text(d,(W//2,400),"617.5",f(BOLD,265),WHITE)
shadow_text(d,(W//2,560),"KM / S",f(COND,92),GOLD)
d.line([(W//2-170,640),(W//2+170,640)],fill=CYAN,width=5)
a.save(f"{S}/thumb_A.png")

# ---------- Variant B : number + stakes line ----------
b=load(f"{S}/clean_11.png"); b=darken_top(b,0.62,0.62)
d=ImageDraw.Draw(b)
shadow_text(d,(W//2,300),"617.5",f(BOLD,300),WHITE)
shadow_text(d,(W//2,480),"KM / S",f(COND,100),GOLD)
d.line([(W//2-200,575),(W//2+200,575)],fill=CYAN,width=5)
shadow_text(d,(W//2,660),"OR THE SUN",f(COND,78),WHITE)
shadow_text(d,(W//2,748),"KEEPS YOU",f(COND,78),WHITE)
b.save(f"{S}/thumb_B.png")

# ---------- Variant C : editorial, left rule ----------
c=load(f"{S}/clean_12.png"); c=darken_top(c,0.58,0.58)
d=ImageDraw.Draw(c)
x0=95
d.line([(x0,200),(x0,400)],fill=CYAN,width=8)
d.text((x0+46,195),"ESCAPE",font=f(COND,74),fill=GOLD)
d.text((x0+46,285),"THE SUN",font=f(COND,74),fill=GOLD)
shadow_text(d,(x0+46,530),"617.5",f(BOLD,215),WHITE,anchor="lm")
d.text((x0+52,655),"KILOMETRES PER SECOND",font=f(COND,42),fill=(210,210,210))
c.save(f"{S}/thumb_C.png")

# contact sheet
ims=[Image.open(f"{S}/thumb_{k}.png").resize((320,569)) for k in "ABC"]
g=Image.new("RGB",(320*3+40,569),"#111")
for i,im in enumerate(ims): g.paste(im,(i*(320+20),0))
g.save(f"{S}/variants.jpg",quality=93)
print("built A, B, C")
