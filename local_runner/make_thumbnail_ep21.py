"""ep21 thumbnails: Saturn floating on an ocean at sunset (LTX shot 7 frame) + "SATURN FLOATS".

Run from local_runner/ after the ep21 render:  python make_thumbnail_ep18.py
Writes final_videos/sci_ep21_saturn_float_thumb.jpg (1080x1920) and _thumb_16x9.jpg (1280x720).
"""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SHOT = os.path.join(HERE, "temp_clips", "sci_ep21_saturn_float_shot_7.mp4")
FRAME_T = "2.0"  # Saturn on the water, sunset sky above
OUT = os.path.join(HERE, "final_videos", "sci_ep21_saturn_float_thumb.jpg")
OUT_WIDE = os.path.join(HERE, "final_videos", "sci_ep21_saturn_float_thumb_16x9.jpg")
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COND = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
AMBER = (255, 176, 72); WHITE = (255, 255, 255)
def f(p, s): return ImageFont.truetype(p, s)


def grab_frame():
    tmp = os.path.join(HERE, "temp_clips", "sci_ep21_thumb_frame.png")
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

# 9:16 — text in the sky above the planet; nothing in the bottom 20% (Shorts UI).
tall = src.resize((1080, 1920))
tall = text(tall, (540, 250), "SATURN", f(BOLD, 200), WHITE, stroke=12, rad=26)
tall = text(tall, (540, 440), "FLOATS", f(BOLD, 200), AMBER, stroke=12, rad=26)
tall.save(OUT, quality=90)

# 16:9 — band through Saturn and the water, text across the top.
band = src.crop((0, 520, 1080, 520 + 608)).resize((1280, 720))
wide = text(band, (640, 110), "SATURN FLOATS", f(BOLD, 120), WHITE, stroke=12, rad=24)
wide = text(wide, (640, 230), "IN WATER", f(BOLD, 84), AMBER, stroke=10, rad=18)
wide.save(OUT_WIDE, quality=90)

for p in (OUT, OUT_WIDE):
    print(f"✅ {p} ({os.path.getsize(p) / 1e6:.2f} MB)")
