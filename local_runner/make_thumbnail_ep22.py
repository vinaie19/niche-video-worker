"""ep22 thumbnails: the real white Sun from the ISS + "THE SUN IS NOT YELLOW".

Run from local_runner/ after fetch_still_assets.py:  python make_thumbnail_ep22.py
Writes final_videos/sci_ep22_sun_white_thumb.jpg (1080x1920) and _thumb_16x9.jpg (1280x720).
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "i2v_stills", "sci_ep22_sun_white", "sun_iss.jpg")
OUT = os.path.join(HERE, "final_videos", "sci_ep22_sun_white_thumb.jpg")
OUT_WIDE = os.path.join(HERE, "final_videos", "sci_ep22_sun_white_thumb_16x9.jpg")
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
AMBER = (255, 176, 72); WHITE = (255, 255, 255)
def f(p, s): return ImageFont.truetype(p, s)


def cover(img, w, h, fx=0.5):
    """fx: horizontal point to keep centred; the Sun sits near the left edge of the photo."""
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    l = min(max(0, round(img.width * fx - w / 2)), img.width - w)
    t = (img.height - h) // 2
    return img.crop((l, t, l + w, t + h))


def text(img, xy, txt, fnt, fill, anchor="mm", stroke=10, rad=22):
    """soft dark glow + hard dark outline, so it reads on glare and on black"""
    W, H = img.size
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text(xy, txt, font=fnt, fill=(0, 0, 0, 220), anchor=anchor, stroke_width=stroke)
    out = Image.alpha_composite(img.convert("RGBA"), lay.filter(ImageFilter.GaussianBlur(rad)))
    ImageDraw.Draw(out).text(xy, txt, font=fnt, fill=fill, anchor=anchor,
                             stroke_width=stroke // 2, stroke_fill=(10, 10, 20))
    return out.convert("RGB")


src = Image.open(SRC).convert("RGB")

# 9:16 — text across the top; nothing in the bottom 20% (Shorts UI).
tall = cover(src, 1080, 1920, fx=0.24)
tall = text(tall, (540, 240), "THE SUN", f(BOLD, 190), WHITE, stroke=12, rad=26)
tall = text(tall, (540, 430), "IS NOT", f(BOLD, 150), WHITE, stroke=12, rad=26)
tall = text(tall, (540, 610), "YELLOW", f(BOLD, 190), AMBER, stroke=12, rad=26)
tall.save(OUT, quality=90)

# 16:9
wide = cover(src, 1280, 720)
wide = text(wide, (640, 110), "THE SUN IS NOT", f(BOLD, 110), WHITE, stroke=12, rad=24)
wide = text(wide, (640, 230), "YELLOW", f(BOLD, 120), AMBER, stroke=12, rad=24)
wide.save(OUT_WIDE, quality=90)

for p in (OUT, OUT_WIDE):
    print(f"✅ {p} ({os.path.getsize(p) / 1e6:.2f} MB)")
