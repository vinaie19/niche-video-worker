"""ep20 thumbnails: Jupiter beside a small red star (LTX shot 4 frame) + "JUPITER" / "A FAILED STAR".

Run from local_runner/ after the ep20 render:  python make_thumbnail_ep18.py
Writes final_videos/sci_ep20_jupiter_star_thumb.jpg (1080x1920) and _thumb_16x9.jpg (1280x720).
"""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SHOT = os.path.join(HERE, "temp_clips", "sci_ep20_jupiter_star_shot_4.mp4")
FRAME_T = "3.0"  # Jupiter left, red dwarf right, black space above
OUT = os.path.join(HERE, "final_videos", "sci_ep20_jupiter_star_thumb.jpg")
OUT_WIDE = os.path.join(HERE, "final_videos", "sci_ep20_jupiter_star_thumb_16x9.jpg")
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COND = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
AMBER = (255, 176, 72); WHITE = (255, 255, 255)
def f(p, s): return ImageFont.truetype(p, s)


def grab_frame():
    tmp = os.path.join(HERE, "temp_clips", "sci_ep20_thumb_frame.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", FRAME_T, "-i", SHOT, "-frames:v", "1", tmp], check=True)
    img = Image.open(tmp).convert("RGB"); os.remove(tmp)
    return img


def text(img, xy, txt, fnt, fill, anchor="mm", stroke=10, rad=22):
    """soft dark glow + hard dark outline, so it reads on clouds and on black"""
    W, H = img.size
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text(xy, txt, font=fnt, fill=(0, 0, 0, 220), anchor=anchor, stroke_width=stroke)
    out = Image.alpha_composite(img.convert("RGBA"), lay.filter(ImageFilter.GaussianBlur(rad)))
    ImageDraw.Draw(out).text(xy, txt, font=fnt, fill=fill, anchor=anchor,
                             stroke_width=stroke // 2, stroke_fill=(10, 10, 20))
    return out.convert("RGB")


src = grab_frame()

# 9:16 — text in the black space above the planet; nothing in the bottom 20% (Shorts UI).
tall = src.resize((1080, 1920))
tall = text(tall, (540, 250), "JUPITER", f(BOLD, 190), WHITE, stroke=12, rad=26)
tall = text(tall, (540, 430), "A FAILED STAR", f(BOLD, 110), AMBER, stroke=10, rad=22)
tall.save(OUT, quality=90)

# 16:9 — band through Jupiter and the red star, text across the top.
band = src.crop((0, 560, 1080, 560 + 608)).resize((1280, 720))
wide = text(band, (640, 110), "JUPITER", f(BOLD, 140), WHITE, stroke=12, rad=24)
wide = text(wide, (640, 240), "A FAILED STAR", f(BOLD, 84), AMBER, stroke=10, rad=18)
wide.save(OUT_WIDE, quality=90)

for p in (OUT, OUT_WIDE):
    print(f"✅ {p} ({os.path.getsize(p) / 1e6:.2f} MB)")
