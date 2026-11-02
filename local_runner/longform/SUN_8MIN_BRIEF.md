# Next Short brief: "You're Seeing the Sun 8 Minutes Late"

Slot: Wed 4 Nov 2026, 6:30 PM IST (ep27 slot went to the Great Red Spot Short; this becomes the next build). Playlist: Space at Impossible Scale. $0 laptop build (real NASA imagery, code camera moves).
Rules: full-frame bright real imagery every frame (no black, no small diagrams), constant motion, whoosh on every cut,
music bed, Andrew voice, ~18 s, punchline is the last word, last frame matches the first (loop).

| # | Voice | Picture |
|---|---|---|
| 1 | If the Sun vanished right now, you wouldn't know. | SDO full-disc Sun, close, slow push-in, flares |
| 2 | For eight minutes, it would keep shining. | ISS sunrise over Earth's limb |
| 3 | Its light needs that long to reach you. | Light streak racing Sun to Earth, Earth growing to full frame |
| 4 | Even its gravity takes eight minutes. | Earth (Blue Marble) moving along its orbit arc |
| 5 | Earth would keep circling a Sun that's already gone. | Sunlit Earth, Sun's glow fading behind it |
| 6 | So the Sun you see is never the Sun now. It's the Sun eight minutes ago. | Back to frame-1 Sun (loop) |

Physics: 1 AU / c = 8 min 19 s; changes in gravity also propagate at c (confirmed by GW170817).
Title: You're Seeing the Sun 8 Minutes Late
Description: Sunlight takes about 8 minutes 20 seconds to reach Earth, and so does a change in the Sun's gravity. So if the Sun vanished, we'd keep seeing it and keep orbiting it for 8 minutes. Images: NASA/SDO, NASA (public domain). #ThresholdPhysics #sun #space #shorts
Pinned comment: "What would you do with your last 8 minutes of sunlight?"

## v2 script (2026-11-02, after the user rejected ep26/ep27 quality)

Why a rewrite: "the Sun is 8 minutes old" is one of the most-posted space Shorts, and v1 ended on a summary
("the Sun you see is never the Sun now"), which our data says kills rewatches. v2 uses the 8 minutes as the
hook everyone half-knows, then turns it: the light is actually thousands of years old. The last word is the payoff.

| # | Voice (~51 words, ~18 s) | Picture |
|---|---|---|
| 1 | If the Sun vanished right now, you wouldn't even know. | SDO Sun fills the frame, flares moving; "IF THE SUN VANISHED..." from frame 1; clock 0:00 starts |
| 2 | Its light would keep coming for eight more minutes. | ISS sunrise over Earth's limb; clock races toward 8:20 |
| 3 | That's how long it takes to reach you. | Clock hits 8:20 and turns red; city lights go dark for a beat |
| 4 | But that light is far older than eight minutes. | Snap back to the Sun, hard push into the surface granules (the turn) |
| 5 | It spent thousands of years trapped inside the Sun first. | Deep zoom into the glowing interior; counter "10,000+ YEARS" |
| 6 | So the sunlight on your face right now is older than the pyramids. | Real Giza pyramids photo (PD) with the Sun low behind them; "OLDER THAN THE PYRAMIDS"; last frame dissolves to frame-1 Sun (loop) |

Physics: 1 AU / c = 8 min 19 s. Photons random-walk out of the radiative zone; mainstream estimates are
~10,000 to ~170,000 years (NASA often quotes ~100,000), so "thousands of years" and "older than the pyramids"
(~4,500 years) are safe. Strictly the photon is re-emitted many times; "that light's energy" is the honest
reading, and the description says so.
Title: Your Sunlight Is Older Than the Pyramids
Description: Sunlight takes about 8 minutes 20 seconds to reach Earth. But the energy in it was made in the Sun's core and spent thousands of years (estimates run from about 10,000 to over 100,000) bouncing its way out before it ever left the surface. Images: NASA/SDO, NASA (public domain). #sun #space #physics #astronomy #science
Pinned comment: "How long do you think sunlight spends inside the Sun before it escapes?"
Build rules: sub-pixel sprites (lf01_render.paste_sprite), 0.6 s room after the last word, and
`python qa_check.py <mp4> --script longform/short_sun_8min.py` must PASS before the owner's phone check.
