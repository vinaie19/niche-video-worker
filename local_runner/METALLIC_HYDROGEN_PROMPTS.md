# Metallic Hydrogen (sci_ep08) — v2 multi_cut + liquid metal sea

**Title:** The Exact Pressure That Turns Gas into Liquid Metal (400 GPa)
**Spoken hook:** Four hundred gigapascals. Hydrogen, the lightest gas, becomes liquid metal.
**Mode:** `multi_cut` (default) — four SAME metallic-hydrogen sea shots, Spaghetti path
**VO words:** 59 (no em dashes)
**First 8 spoken words:** Four hundred gigapascals Hydrogen the lightest gas
**Status:** Prompt pack v2 + draft stills in `i2v_stills/sci_ep08_metallic_hydrogen/`. Awaiting your stills QC before LTX.

```bash
CHANNEL=b ENGINE=ltx VIDEO_ID=sci_ep08_metallic_hydrogen ./venv/bin/python run_test_batch.py
```

## Two prompts per beat — do not mix them

| | Still prompt | Motion prompt |
|---|---|---|
| Feeds | the image model, offline | LTX, as `shot["prompt"]` |
| Lives in | this doc + `_refs/` | `science_prompts.py` `_EP08_BEATS` |
| Describes | one frozen composition | what changes over ~6–7 s |
| Owns | identity, framing, palette | motion, pace, direction |

Once a still is approved and saved to `i2v_stills/sci_ep08_metallic_hydrogen/shot_N.png`, frame 1 is locked by the image.

## Identity lock (all 4 stills and all 4 motion prompts)

The SAME place in every shot:

- **Sea:** flat, opaque, mirror-bright liquid silver, looks exactly like mercury.
- **Sky:** heavy charcoal storm deck with faint brown-grey horizontal cloud bands.
- **Horizon:** one sharp, level line (shot 4 gently curved, lower third).
- **Palette:** cool silver + charcoal; white-blue only for lightning in shot 4.
- **Camera:** locked, eye level just above the surface, vertical 9:16, 1080x1920.

## VO (full script)

1. Four hundred gigapascals. Hydrogen, the lightest gas, becomes liquid metal.
2. That is four million times the air on your skin. An invisible cloud turns into a chrome sea.
3. Crush the atoms that close and electrons break free. Those free electrons are why metal shines.
4. Deep in Jupiter this is not theory. An ocean of liquid metal wider than Earth.

---

## Beat 1 — Threshold (gas → metal)

**VO:** Four hundred gigapascals. Hydrogen, the lightest gas, becomes liquid metal.

**Still prompt:**
Cinematic locked shot, One frozen moment: a thick wall of pale grey hydrogen fog fills the upper two thirds of frame above a small pool of mirror-bright liquid silver at the bottom. The fog presses against the silver and is already turning into shining liquid metal where they meet. The silver pool sits low, flat and level like mercury. Cool silver and charcoal palette only. Locked camera, no camera movement, photoreal cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks

**Motion prompt:**
A thick wall of pale grey hydrogen fog fills the upper two thirds of frame above a small pool of mirror-bright liquid silver at the bottom. Through the shot the fog is pressed straight down from above, its layers squeezing tighter and darker as they sink, and where the fog touches the pool it turns into shining liquid metal. The silver pool rises and spreads outward to both edges until it fills the lower half, its surface flat and level like mercury, reflecting the fog above. Fast, heavy, crushing downward. Locked camera, no camera movement, photoreal cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks

---

## Beat 2 — Paradox (invisible gas → mirror)

**VO:** That is four million times the air on your skin. An invisible cloud turns into a chrome sea.

**Still prompt:**
Cinematic locked shot, One frozen moment: the SAME liquid silver sea fills the lower half of frame under a heavy charcoal storm deck with faint brown-grey bands, a sharp level horizon across the middle. Thin wisps of grey fog hang just above the metal. The storm clouds appear crisp and upside down in the silver, like a flawless mirror. The surface stays flat, level and perfectly still. Cool silver and charcoal palette only. Locked camera, no camera movement, photoreal cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks

**Motion prompt:**
The SAME liquid silver sea fills the lower half of frame under a heavy charcoal storm deck with faint brown-grey bands, a sharp level horizon across the middle. Through the shot the last thin wisps of grey fog drift down onto the metal and melt into it, and the reflection in the sea sharpens until the storm clouds appear crisp and upside down in the silver, like a flawless mirror. The cloud bands above crawl slowly left to right and their reflection follows them exactly. The surface stays flat, level and perfectly still. Calm, eerie, heavy. Locked camera, no camera movement, photoreal cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks

---

## Beat 3 — Law (free electrons shine)

**VO:** Crush the atoms that close and electrons break free. Those free electrons are why metal shines.

**Still prompt:**
Cinematic locked shot, One frozen moment: close on the SAME liquid silver sea, the mercury-bright surface filling the lower three quarters of frame, a strip of dark storm sky across the top. Thousands of tiny bright white glints sit across the metal like sparks frozen in a current. The metal is one smooth opaque liquid sheet, flat and level, gleaming like polished chrome. Cool silver and charcoal palette only. Locked camera, no camera movement, photoreal cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks

**Motion prompt:**
Close on the SAME liquid silver sea, the mercury-bright surface filling the lower three quarters of frame, a strip of dark storm sky across the top. Through the shot thousands of tiny bright white glints stream across the metal from left to right like sparks flowing in a current, low ripples roll the same way, and the whole surface grows steadily brighter until it gleams like polished chrome. The metal stays one smooth opaque liquid sheet, flat and level, the glints riding on top of it. Fast, alive, electric. Locked camera, no camera movement, photoreal cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks

---

## Beat 4 — Climax (Jupiter-scale ocean + lightning)

**VO:** Deep in Jupiter this is not theory. An ocean of liquid metal wider than Earth.

**Still prompt:**
Cinematic locked shot, One frozen moment: ultra-wide on the SAME liquid silver sea stretching to a gently curved horizon in the lower third of frame, a vast charcoal storm deck with brown-grey bands filling the sky above. A single blue-white lightning bolt is frozen mid-strike into the center of the sea, with a bright white flash reflection on the metal and one flat circular ripple just starting at the strike point. Cool silver and charcoal palette only. Locked camera, no camera movement, photoreal cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks

**Motion prompt:**
Ultra-wide on the SAME liquid silver sea stretching to a gently curved horizon in the lower third of frame, a vast charcoal storm deck with brown-grey bands filling the sky above. Through the shot a single blue-white lightning bolt strikes the center of the sea, and the entire mirror surface flashes bright white all the way to the horizon, then fades back to silver. One flat circular ripple spreads slowly outward from the strike point across the metal. Cloud bands crawl slowly left to right. Enormous, quiet, final. Locked camera, no camera movement, photoreal cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks

---
