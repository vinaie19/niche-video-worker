"""ep19 thumbnails: TON 618 accretion disk (LTX shot 1 frame) + "66 BILLION SUNS" in the black centre.

Run from local_runner/ after the ep19 render:  python make_thumbnail_ep18.py
Writes final_videos/sci_ep19_ton618_thumb.jpg (1080x1920) and _thumb_16x9.jpg (1280x720).
"""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SHOT = os.path.join(HERE, "temp_clips", "sci_ep19_ton618_shot_1.mp4")
FRAME_T = "1.0"  # disk filling the frame, black shadow centred
OUT = os.path.join(HERE, "final_videos", "sci_ep19_ton618_thumb.jpg")
OUT_WIDE = os.path.join(HERE, "final_videos", "sci_ep19_ton618_thumb_16x9.jpg")
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COND = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
AMBER = (255, 176, 72); WHITE = (255, 255, 255)
def f(p, s): return ImageFont.truetype(p, s)


def grab_frame():
    tmp = os.path.join(HERE, "temp_clips", "sci_ep19_thumb_frame.png")
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

# 9:16 — the number sits inside the black shadow; nothing in the bottom 20% (Shorts UI).
tall = src.resize((1080, 1920))
tall = text(tall, (540, 880), "66 BILLION", f(BOLD, 150), AMBER, stroke=12, rad=26)
tall = text(tall, (540, 1050), "SUNS", f(BOLD, 150), AMBER, stroke=12, rad=26)
tall = text(tall, (540, 1250), "ONE BLACK HOLE", f(COND, 70), WHITE, stroke=8, rad=18)
tall.save(OUT, quality=90)

# 16:9 — band through the shadow, number centred on it.
band = src.crop((0, 660, 1080, 660 + 608)).resize((1280, 720))
wide = text(band, (640, 300), "66 BILLION SUNS", f(BOLD, 120), AMBER, stroke=12, rad=24)
wide = text(wide, (640, 440), "ONE BLACK HOLE", f(COND, 64), WHITE, stroke=8, rad=16)
wide.save(OUT_WIDE, quality=90)

for p in (OUT, OUT_WIDE):
    print(f"✅ {p} ({os.path.getsize(p) / 1e6:.2f} MB)")
