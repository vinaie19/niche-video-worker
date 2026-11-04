"""3D star-field flight layer: the camera flies forward through stars at different depths, so near stars
stream past fast (with motion streaks) and far ones barely move. Parallax is what makes a zoom read as
travel through space (owner, 4 Nov: the flat photo zoom "looks like some photo zoomed").

This is a visualisation of flying, drawn on top of the real destination image; it is not observational data.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
F = 620.0          # focal length in px (field of view ~ 82 deg vertically)
DEPTH = 60.0       # stars live between z = 0.5 and z = DEPTH ahead of the camera


class StarFlight:
    def __init__(self, n=2600, seed=7):
        rng = np.random.default_rng(seed)
        self.x = rng.uniform(-14, 14, n)
        self.y = rng.uniform(-24, 24, n)
        self.z0 = rng.uniform(0.5, DEPTH, n)
        self.mag = rng.power(3.0, n)                       # most stars faint, a few bright
        t = rng.random(n)                                  # colour: blue-white to warm yellow, like real stars
        self.col = np.stack([200 + 55 * t, 210 + 35 * (1 - abs(t - 0.5) * 2), 255 - 90 * t], 1).astype(np.uint8)

    def layer(self, dist, speed, cx=W / 2, cy=H / 2):
        """RGB star layer after the camera has flown `dist` units; `speed` = units per frame (streak length)."""
        z = (self.z0 - dist) % DEPTH + 0.5                 # stars recycle behind the far plane: an endless field
        sx = cx + F * self.x / z
        sy = cy + F * self.y / z
        ok = (sx > -40) & (sx < W + 40) & (sy > -40) & (sy < H + 40) & (z > 0.6)
        im = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(im)
        order = np.argsort(-z[ok])                         # far first, near on top
        xs, ys, zs = sx[ok][order], sy[ok][order], z[ok][order]
        ms, cs = self.mag[ok][order], self.col[ok][order]
        for x, y, zz, m, c in zip(xs, ys, zs, ms, cs):
            near = 1.0 / zz
            size = 0.6 + 7.0 * near * (0.4 + m)
            bright = min(1.0, 0.25 + 1.6 * near * (0.3 + m)) * min(1.0, (DEPTH - zz) / 8.0)  # fade in far away
            col = tuple(int(v * bright) for v in c)
            # streak: where this star was a moment ago (it moves away from the centre as it nears)
            z_prev = zz + speed * 2.2
            px, py = cx + (x - cx) * zz / z_prev, cy + (y - cy) * zz / z_prev
            if math.hypot(x - px, y - py) > 1.5:
                d.line((px, py, x, y), fill=col, width=max(1, int(size * 0.7)))
            d.ellipse((x - size / 2, y - size / 2, x + size / 2, y + size / 2), fill=col)
        glow = im.filter(ImageFilter.GaussianBlur(3))
        return np.maximum(np.asarray(im), (np.asarray(glow).astype(np.float32) * 1.4).clip(0, 255).astype(np.uint8))
