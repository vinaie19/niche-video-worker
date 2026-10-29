"""LF01 thumbnails (1280x720): three options built from the same real imagery as the video."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lf01_render as R  # noqa: E402
from PIL import Image  # noqa: E402

OUT = os.path.join(R.ROOT, "final_videos")


def save(F, name):
    im = F.rgb().resize((1280, 720), Image.LANCZOS)
    p = os.path.join(OUT, f"lf01_universe_scale_thumb_{name}.jpg")
    im.save(p, quality=92); print("✅", p, f"{os.path.getsize(p)/1e6:.2f} MB")


# A: the whole Milky Way vs a 1 cm Earth
F = R.Frame()
F.photo("milkyway", zoom=1.25, cx=0.5, cy=0.5, rot=-8, fit="cover")
F.fade(0.15)
F.planet("earth", 330, 720, 150, halo=0.5, halo_col=(120, 170, 255))
F.ruler(255, 405, 820, 150, 1, step_lbl=1)
F.label("1 cm", 330, 905, 64, R.AMBER)
F.label("IF EARTH WERE 1 cm...", 1180, 330, 104, R.WHITE)
F.label("the Milky Way would be", 1180, 470, 64, R.WHITE)
F.label("740 MILLION km WIDE", 1180, 580, 84, R.AMBER)
save(F, "A")

# B: Sun ball vs Earth dot, with the distance
F = R.Frame()
F.stars(0.8)
F.planet("sun", 1520, 560, 860, halo=0.4, halo_col=(255, 150, 60))
F.planet("earth", 210, 540, 70, halo=0.6, halo_col=(120, 170, 255))
F.dashed(260, 540, 980, 540, (255, 220, 150), 6, dash=26, gap=18)
F.label("EARTH = 1 cm", 230, 420, 54, R.WHITE)
F.label("THE SUN?", 540, 190, 120, R.WHITE)
F.label("117 METRES AWAY", 540, 320, 76, R.AMBER)
save(F, "B")

# C: deep field + the question
F = R.Frame()
F.photo("udf", zoom=1.3, cx=0.55, cy=0.45)
F.fade(0.35)
F.label("HOW BIG IS", 960, 360, 150, R.WHITE)
F.label("THE UNIVERSE?", 960, 540, 150, R.AMBER)
F.planet("earth", 960, 800, 110, halo=0.6, halo_col=(120, 170, 255))
F.label("Earth = 1 cm", 960, 900, 48, R.WHITE)
save(F, "C")
