"""ep23 thumbnails: the full planet stack between Earth and the Moon + "EVERY PLANET FITS".

Re-renders the final frame of ep23_planet_stack.py with the column shifted down to leave room
for the title (thumbnails have no captions or Shorts UI to dodge). Run after the ep23 render:
  python make_thumbnail_ep23.py
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import ep23_planet_stack as e

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
AMBER = (255, 176, 72); WHITE = (255, 255, 255)
def f(p, s): return ImageFont.truetype(p, s)


def text(img, xy, txt, fnt, fill, anchor="mm", stroke=10, rad=22):
    """soft dark glow + hard dark outline (same look as the ep18-21 thumbnails)"""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text(xy, txt, font=fnt, fill=(0, 0, 0, 220), anchor=anchor, stroke_width=stroke)
    out = Image.alpha_composite(img.convert("RGBA"), lay.filter(ImageFilter.GaussianBlur(rad)))
    ImageDraw.Draw(out).text(xy, txt, font=fnt, fill=fill, anchor=anchor, stroke_width=stroke // 2,
                             stroke_fill=(10, 10, 20))
    return out.convert("RGB")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "final_videos", f"{e.VID}_thumb.jpg")
OUT_WIDE = os.path.join(HERE, "final_videos", f"{e.VID}_thumb_16x9.jpg")

targets, words = e.voice_timeline()
e.EARTH_BOTTOM, e.MOON_TOP = 1840, 470
e.S0 = (e.EARTH_BOTTOM - e.MOON_TOP) / e.WORLD_SPAN
e.EARTH_Y0 = e.EARTH_BOTTOM - e.D["earth"] / 2 * e.S0
img = e.render(targets, words, None, preview_times=[sum(targets) - 0.05])[0]

tall = text(img, (540, 170), "EVERY PLANET", f(BOLD, 116), WHITE, stroke=12, rad=24)
tall = text(tall, (540, 330), "FITS IN HERE", f(BOLD, 112), AMBER, stroke=12, rad=22)
tall.save(OUT, quality=90)

# 16:9: the upright column in the middle (planets stay the right way up), title either side.
col = img.crop((0, 420, 1080, 1920)).resize((518, 720), Image.LANCZOS)
wide = Image.new("RGB", (1280, 720), "black"); wide.paste(col, (381, 0))
for xy, line, colr in (((200, 300), "EVERY", WHITE), ((200, 420), "PLANET", WHITE),
                       ((1080, 300), "FITS IN", AMBER), ((1080, 420), "HERE", AMBER)):
    wide = text(wide, xy, line, f(BOLD, 84), colr, stroke=10, rad=18)
wide.save(OUT_WIDE, quality=90)
for p in (OUT, OUT_WIDE):
    print(f"✅ {p} ({os.path.getsize(p) / 1e6:.2f} MB)")
