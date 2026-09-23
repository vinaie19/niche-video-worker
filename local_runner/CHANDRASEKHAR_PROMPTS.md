# Chandrasekhar Limit (sci_ep07) — v4 multi_cut + solid white dwarf

**Title:** The Exact Mass That Causes a White Dwarf Collapse (1.44 M☉)
**Spoken hook:** This dead star is only the size of Earth, but it weighs almost as much as the Sun.
**Mode:** `multi_cut` (default) — four SAME solid white-dwarf shots, Spaghetti path
**VO words:** 69 (no em dashes, no jargon opener)
**Status:** Stills approved (shot_1..4.png). Motion prompts rewritten for I2V, not yet rendered.

```bash
CHANNEL=b ENGINE=ltx VIDEO_ID=sci_ep07_chandrasekhar ./venv/bin/python run_test_batch.py
```

## Two prompts per beat — do not mix them

Each beat has two different prompts with two different jobs. They are not
interchangeable, and pasting one into the other's slot is what broke v3.

| | Still prompt | Motion prompt |
|---|---|---|
| Feeds | the image model, offline | LTX, as `shot["prompt"]` |
| Lives in | this doc + `_refs/` | `science_prompts.py` `_EP07_BEATS` |
| Describes | one frozen composition | what changes over ~6–7 s |
| Owns | identity, size, framing, palette | motion, pace, direction of travel |

Once a still is approved and saved to `i2v_stills/sci_ep07_chandrasekhar/shot_N.png`,
frame 1 is locked by the image. The motion prompt does not need to restate the
subject's size, centring or silhouette — those tokens are spent, not free.

### Why v4 rewrote the motion prompts

- **The worker has no negative-prompt field.** `_build_shot_payload` in
  `run_test_batch.py` sends a single `prompt` string. Every `NO vortex`,
  `NO portal`, `NO ring`, `NO doughnut` in v3 went to the T5 encoder as a
  *positive* concept. The ep06 swirl/portal failures were plausibly caused by
  the very lines written to prevent them. v4 states constraints positively:
  "the star holds as a solid opaque ball" instead of "no portal, no hole".
- **v3 told LTX to hold still.** "one frozen moment", "frozen at many different
  distances", "almost no motion" produce a static 6–7 s clip. Dead air on Shorts.
- **v3 ran 190–230 words.** LTX dilutes the tail; the motion intent was buried
  under the ban list. v4 runs 92–102 words with the motion in the middle.

### VO change

v3 beat 2 ("Feed it more mass") had no agent — it instructed the viewer instead
of telling them what the star was doing. v4 gives the story a villain: the dwarf
is *stealing* gas from a companion, which also pays off the gas wisp already
visible in shot 1's still. Beat 3 names electron degeneracy in plain words
("electrons hold the whole star up") so the collapse has a stated cause.

## Beat 1

**VO:** This dead star is only the size of Earth, but it weighs almost as much as the Sun.

**Frames:** 161 · **Rate:** -8% · **Pause:** 350 ms

**Motion prompt (LTX, live in `science_prompts.py`):**

```
A small dense white dwarf star hangs still in black space, its blue-white crust finely cracked, a thin ribbon of glowing gas trailing in from off frame and curling down onto its upper edge. Through the shot the ribbon drifts and slowly feeds into the surface, the glow at the limb swells very gently, and faint light ripples travel across the crust. The star holds as a solid opaque ball, perfectly round and the same size from first frame to last. Calm, heavy, patient. Locked camera, no camera movement, photoreal cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks
```

**Still prompt (already rendered → `shot_1.png`):**

```
Cinematic locked wide shot, one frozen moment: a single small solid white dwarf star, a rigid perfectly round opaque ball of dense blue-white crust with fine hairline surface texture and a thin bright glow at the limb, perfectly circular silhouette, filled opaque disk, same center of frame, occupying about one third of frame width, calm and stable, pure black void with a sparse starfield, one thin wisp of glowing gas from a distant companion star just touching its upper edge, photoreal cinematic CGI, vertical 9:16, locked camera, no people, no faces, NO text, NO letters, NO logos, no watermarks, not a soft blob, not a ring, not hollow
```

## Beat 2

**VO:** It is stealing gas from a neighbouring star, and every gram it steals crushes it tighter.

**Frames:** 153 · **Rate:** +0% · **Pause:** 280 ms

**Motion prompt (LTX, live in `science_prompts.py`):**

```
The same white dwarf fills the frame, its rigid blue-white crust broken into plates by sharp fracture lines. Through the shot a pale blue sheet of gas settles onto the upper left of the surface and spreads flat across the crust, the fracture lines slowly widen, and cool white light rises brighter through the cracks from the solid core beneath. The whole ball contracts a little and stays an opaque sphere with a hard round edge. Pressure building, nothing escaping. Locked camera, no camera movement, photoreal cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks
```

**Still prompt (already rendered → `shot_2.png`):**

```
Cinematic locked medium shot, one frozen moment: the SAME solid blue-white white dwarf star as shot 1, same center of frame, the same size or slightly smaller (the disk spans about two-thirds of the frame width and never more), perfectly sharp circular silhouette, filled opaque disk. A broad, diffuse curtain of pale blue-white gas arcs in from off-frame at the lower left and upper right and pours onto the star, spreading across a wide patch of its upper-left surface as a low, flat glowing splash that hugs the crust. The mass lands on the surface; it does not shoot out from it. The star's hard, rigid, rock-like blue-white crust is split by sharp jagged fracture lines, with cool white light glowing up through the cracks from a bright solid core beneath. The crust plates are rigid and unbroken in shape, the round edge fully intact, and the only light comes from the surface, the cracks and the infalling gas. At most one faint thin secondary wisp near the edge, far dimmer than the infall. Pure black void, cool blue-white palette throughout, photoreal cinematic CGI, vertical 9:16, locked camera, no people, no faces, NO text, NO letters, NO logos, no watermarks, NO polar jet, no beam, no light column, no pillar, no bipolar outflow, no vertical shaft of light from the top or bottom of the star, no gold, no orange, not melting goo, not a soft blob, not a ring, not hollow, no halo
```

## Beat 3

**VO:** Inside, electrons hold the whole star up. Add too much weight and they give way, all at once.

**Frames:** 169 · **Rate:** -4% · **Pause:** 280 ms

**Motion prompt (LTX, live in `science_prompts.py`):**

```
The same white dwarf, smaller now and blazing, its cracked crust shearing apart along one side. Through the shot angular crust shards peel away and fall inward, striking the surface, while the whole sphere visibly shrinks and its light climbs to a hard blue-white blaze. Every piece moves toward the centre. The core stays a solid opaque ball, bright evenly across its whole face, its edge staying sharp as it contracts. Fast, violent, collapsing inward. Locked camera, no camera movement, photoreal cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks
```

**Still prompt (already rendered → `shot_3.png`):**

```
Cinematic locked close-up, one frozen moment: the SAME solid blue-white white dwarf star as shot 1, already collapsed to a clearly smaller sphere at the same center of frame. The disk spans only about one quarter to one third of the frame width, much smaller than in shot 1. Perfectly sharp circular silhouette, filled opaque disk, a bright blue-white solid surface evenly lit all the way across, with a cracked crust of fine jagged fracture lines. Broken blue-white crust shards are caught mid-fall, dropping INWARD onto the surface. They are asymmetrical: a dense lopsided cluster over the upper-left and right side, packed tightly just above the crust and thinning quickly farther out, while the lower half is mostly bare, with only a few scattered fragments. Each shard is a sharp angular rock-like fragment, stretched into a short streak that points straight at the star's center, as if pulled down onto it. Some shards are touching or striking the surface. Spacing is irregular and clumped, with large empty gaps, and the shards never trace the outline of the sphere. Pure black void, cool blue-white palette, photoreal cinematic CGI, vertical 9:16, locked camera, no people, no faces, NO text, NO letters, NO logos, no watermarks, NO ring of shards, NO halo, NO orbit, no shards evenly spaced around the edge, no circular perimeter of debris, no doughnut, no torus, no portal, no swirl, no hole, no vortex, no lensing, no dark center, not a plasma blob, no gold
```

## Beat 4

**VO:** That breaking point is the Chandrasekhar limit, 1.44 Suns. Cross it, and the star tears itself apart.

**Frames:** 145 · **Rate:** -12% · **Pause:** 200 ms

**Motion prompt (LTX, live in `science_prompts.py`):**

```
A blinding blue-white core burns at the centre of a wide field of sharp crust fragments and torn filaments of pale blue gas. Through the shot the fragments and the gas drift slowly outward in every direction, the filaments stretch and thin as they travel, and the core flares once and then settles to a steady burn. The movement is slow and heavy, wreckage coasting through vacuum long after the blast. Quiet catastrophic aftermath. Locked camera, no camera movement, photoreal cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks
```

**Still prompt (already rendered → `shot_4.png`):**

```
Cinematic locked ultra-wide shot, one frozen moment just after the explosion: a small, blinding, solid blue-white sphere at the exact center of frame, about one sixth of the frame width, perfectly sharp circular silhouette, filled opaque disk, the SAME star identity as shot 1. Around it hang sharp, chunky, angular rock-like crust shards in cool blue-white and silver. They are frozen at many different distances from the center, tilted at random angles, and scattered unevenly in clumps with empty gaps. They are discrete solid fragments, not motion streaks. Lumpy, patchy clouds of filamentary pale-blue and white gas with crisp, torn filament edges fill the frame unevenly: bright and dense near the core, broken and asymmetrical farther out, never a clean outer edge. Deep black void, strictly cool blue-white and silver palette, photoreal cinematic CGI, vertical 9:16, locked camera, no people, no faces, NO text, NO letters, NO logos, no watermarks, NO radial streaks, NO speed lines, NO light tunnel, NO starburst rays, NO warp-speed effect, NO vortex, NO swirl, no gold, no amber, no orange, no warm tones, not a ring, not a hollow circle, no hole, no portal, no dark center, not blurry smoke
```
