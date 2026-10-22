# Threshold Physics — posting schedule (Channel B)

**Strategy (locked):** [`THRESHOLD_PHYSICS_STRATEGY.md`](THRESHOLD_PHYSICS_STRATEGY.md)  
**Channel:** separate YouTube account from After Hours Japan  
**Promise:** Visualizing the exact numerical limits where physical reality breaks down.  
**Generation:** `CHANNEL=b` + `ENGINE=ltx` (see [`local_runner/render_channel_b.sh`](local_runner/render_channel_b.sh))  
**Cadence:** **1 Short / day**, **12:00 IST**  
**Start:** **Sat 19 Sep 2026** (tomorrow from lock date)  
**File source:** `final_videos/ready/sci_*_hook.mp4`  
**Rule:** never reuse After Hours hashtags or cross-promote  

Shared hashtags (every description):

```
#ThresholdPhysics #physics #science #space #universe
```

---

## Workflow each episode (render → review → schedule)

1. **Render** LTX batch for that slug  
2. **Local QC** (checklist below)  
3. **YouTube AI assistant review** — paste the prompt from strategy §7 with title/hook/description  
4. Apply copy tweaks if agent says revise; **re-render only if visual/hook fail**  
5. Promote to `ready/` and **Schedule** for that day’s **12:00 IST**  
6. Log analytics after ~24–48h  

Do **not** post two on the same day. Skip / hold if QC or agent review fails.

---

## QC before `ready/`

1. Watch `final_videos/sci_epNN_*_complete.mp4`
2. First 2s: motion + threshold readable in VO/captions (stakes in first ~8 words)
3. No gibberish text / logos in any shot
4. VO ends; last 3–5s mostly quiet linger (or clean loop)
5. Total ~26–36s (acceptable up to ~45s)
6. Promote: `./local_runner/promote_to_ready.sh <slug>`

---

## Batch 2 — Top 12 thresholds (dates fixed)

> Old Batch 1 (`sun_closer`, `dyson_heat`, etc.) is **parked**. See strategy §4.

### Sat 19 Sep 2026 — ep01 sound 194 dB
- **File:** `sci_ep01_sound_194db_hook.mp4`
- **Slug:** `sci_ep01_sound_194db`
- **Title:** `The Exact Point Where Sound Destroys Matter (194 dB)`
- **Spoken hook:** `At the 194-decibel sound barrier, sound stops being sound and becomes a shockwave.`
- **Status:** Pending render → agent review → schedule
- **Description:**
```
What happens when an acoustic wave carries more energy than the atmosphere can physically hold?

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### Sun 20 Sep 2026 — ep02 Roche Limit
- **File:** `sci_ep02_roche_limit_hook.mp4`
- **Slug:** `sci_ep02_roche_limit`
- **Title:** `The Exact Distance Where Gravity Shatters a Moon`
- **Spoken hook:** `Cross the Roche limit, and planetary gravity shreds an entire moon.`
- **Status:** Pending
- **Description:**
```
The Roche Limit is the exact gravitational threshold where celestial bodies get ripped into rings.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### Mon 21 Sep 2026 — ep03 neutron star impact
- **File:** `sci_ep03_neutron_impact_hook.mp4`
- **Slug:** `sci_ep03_neutron_impact`
- **Title:** `Dropping an Object 1 Meter on a Neutron Star (200 Million Gs)`
- **Spoken hook:** `On a neutron star, drop a solid mass one meter—and it hits with nuclear force.`
- **Status:** Pending
- **Description:**
```
On a neutron star, surface gravity is so extreme that a one-meter fall hits with nuclear force.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### Tue 22 Sep 2026 — ep04 absolute zero
- **File:** `sci_ep04_absolute_zero_hook.mp4`
- **Slug:** `sci_ep04_absolute_zero`
- **Title:** `The Exact Temperature Where Atomic Motion Stops (0 K)`
- **Spoken hook:** `At absolute zero—zero kelvin—all atomic motion completely vanishes.`
- **Status:** Pending
- **Description:**
```
At absolute zero (0 K), atomic motion hits the thermodynamic floor — the coldest possible state of matter.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### Wed 23 Sep 2026 — ep05 spaghettification
- **File:** `sci_ep05_spaghettification_hook.mp4`
- **Slug:** `sci_ep05_spaghettification`
- **Title:** `The Exact Point Where Gravity Stretches Matter Into Spaghetti`
- **Spoken hook:** `Spaghettification: too close to a black hole, gravity stretches matter into spaghetti.`
- **Status:** Pending
- **Description:**
```
Too close to a black hole, tidal gravity stretches matter into thin filaments — spaghetti.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### Thu 24 Sep 2026 — ep06 absolute hot
- **File:** `sci_ep06_absolute_hot_hook.mp4`
- **Slug:** `sci_ep06_absolute_hot`
- **Title:** `The Exact Temperature Where Physics Completely Breaks (10^32 K)`
- **Spoken hook:** `This is the exact temperature where physics itself stops making sense.`
- **Shot mode:** `multi_cut` (4 SAME plasma-sphere shots; Spaghetti path)
- **Status:** Prompt ready v3 (plain VO, cracked photosphere/fissure plasma) — pending re-render → QC
- **Description:**
```
Imagine heating something with no limit. Push far enough and heat starts warping space, then temperature itself stops making sense.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```


### Fri 25 Sep 2026 — ep07 Chandrasekhar
- **File:** `sci_ep07_chandrasekhar_hook.mp4`
- **Slug:** `sci_ep07_chandrasekhar`
- **Title:** `The Exact Mass That Causes a White Dwarf Collapse (1.44 M☉)`
- **Spoken hook:** `This tiny dead star is the size of Earth, but it weighs almost as much as the Sun.`
- **Shot mode:** `multi_cut` (4 SAME solid white-dwarf shots, cracked crust / bright core; Spaghetti path)
- **Status:** Prompt ready v2 (plain VO, solid white dwarf) — draft stills ready — awaiting stills QC before LTX (no RunPod until approved)
- **Description:**
```
A dead star the size of Earth. Keep adding mass and it cracks, then past one exact weight, 1.44 Suns, it caves in and explodes.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### Sat 26 Sep 2026 — ep08 metallic hydrogen
- **File:** `sci_ep08_metallic_hydrogen_hook.mp4`
- **Slug:** `sci_ep08_metallic_hydrogen`
- **Title:** `The Exact Pressure That Turns Gas into Liquid Metal (400 GPa)`
- **Spoken hook:** `Hydrogen is the lightest gas there is, but crush it hard enough and it turns into liquid metal.`
- **Shot mode:** `multi_cut` (4 SAME metallic-hydrogen sea shots; Spaghetti path)
- **Status:** v3 VO locked (Chandrasekhar-shaped: paradox → law → 400 GPa → Jupiter). Stills FULL SET LOCK v12i — LTX clear. Pack: `local_runner/METALLIC_HYDROGEN_PROMPTS.md`. Source VO: `local_runner/science_prompts.py` `_EP08_BEATS`.
- **Description:**
```
Descending into the deep planetary core where extreme pressure forces gas into a liquid metallic sea.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### ep08N neutron star 20 km *(NEW — Part 2 of ep07, same star)*
- **File:** `sci_ep08_neutron_star_complete_v3.mp4` (v3 = v2 minus the 1.2s dead air before beat 4; v1/v2 kept)
- **Slug:** `sci_ep08_neutron_star`
- **Title:** `The Exact Size a Collapsed Star Crushes Down To (20 km)`
- **Spoken hook:** `This star is the size of a city, and it's heavier than the Sun.` (on-screen: SIZE OF A CITY)
- **Shot mode:** `multi_cut` (city+star / teaspoon / star on black / city+star loop back to hook)
- **Status:** Stills QC passed (built locally, no image API; `i2v_stills/sci_ep08_neutron_star/SOURCES.md`). One LTX render 2026-09-29; v2 reassembled with no GPU (shots 1+4 animated locally, new hook/loop VO); v3 trims beat 3's trailing silence (27.6s). Source VO: `local_runner/science_prompts.py` `_EP08N_BEATS`.

### Sun 27 Sep 2026 — ep09 solar escape *(swap)*
- **File:** `sci_ep09_solar_escape_hook.mp4`
- **Slug:** `sci_ep09_solar_escape`
- **Title:** `The Exact Speed Needed to Escape the Sun (617.5 km/s)`
- **Spoken hook:** `Below solar escape velocity—617 kilometers a second—the Sun traps you.`
- **Status:** ✅ RENDERED & PROMOTED 2026-09-26 — `final_videos/ready/sci_ep09_solar_escape_hook.mp4` (28.1s, 1080x1920, 0 decode errors).
  Subject is a **plasma ember**, not a spacecraft. Prior vehicle-based passes were rejected: subject identity broke
  (shot 1 dart vs shots 2-4 chrome rocket), scale swung across cuts, and shot 2 showed an exhaust plume against the
  VO line "No more thrust". Root cause: locking a hard-surface vehicle across 4 cuts with stacked negations
  ("engines hard OFF", "never", "zero exhaust") — diffusion ignores negations in a positive prompt.
  A luminous phenomenon has no rigid geometry to drift, matching every episode that has worked here.
  Shot 3 took a second pass: "towering coronal arches" made LTX build one frame-filling symmetric arch that closed
  into a glowing oval (read as a portal), blew out exposure, and flipped the ember to horizontal travel. Reworded to
  pin the corona low on the bottom edge, keep black dominant, and lock the same lower-left→upper-right diagonal.
  Rendered pure **T2V** — I2V stills deleted.
  **VO v3 (2026-09-26, retention rewrite):** the old beat 3 spent 21% of runtime restating the number from beat 1
  and the formula's 10-22s MECHANISM slot was never filled. Beat 3 now delivers the mechanism — escape velocity is
  617.5 km/s at the photosphere but only ~42 km/s from Earth's orbit, because you start deep in the gravity well.
  Beat 2 carries the ballistic/mass-independent rule. Rates descend +0/-4/-8/-12%. 61 words, 29.7s, 3.2s tail linger.
  Register deliberately kept clipped/declarative per strategy section 1 — storytelling VO considered and declined.
  **VO v5 (final, comprehension pass):** cold-open orientation was the blocker — the script never named its own
  premise. Fixes: beat 1 now says "escaping its gravity from the surface" (names the topic AND anchors where the
  number applies, so beat 3's 42 km/s reads as a revelation, not a contradiction); beat 3 reworded from the jargon
  "the Sun's well" to "Farther out, the pull weakens ... that number drops to"; beat 4's dangling "Clear it" (no
  antecedent within 20s) became "Reach that speed". "forty two" spelled without a hyphen so the caption does not
  wrap as "forty / -two". 67 words, 32.0s, 3.2s tail linger, 0 decode errors.
  **Captions now show NUMERALS (617.5 km/s, 42 km/s) while the VO speaks the words** — per strategy section 2
  ("numbers highlighted"). Required a pipeline change: added a `caption_text` key on a beat that overrides the
  burned caption while TTS still speaks `text`. Two edits in `local_runner/audio_post.py` —
  `create_subtitles_from_beats` reads `caption_text or text`, and `normalize_script_beats` had to be taught to
  PRESERVE the key (it previously rebuilt each beat with only text/rate/pitch/pause_ms and silently dropped it).
  This is reusable: any episode can now set `caption_text` per beat. Worth back-applying to ep01-ep08.
- **Description:**
```
The solar escape-velocity threshold — below it, gravity wins; above it, you leave the star’s grip.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### ep14 pulsar 716 Hz *(NEW — queued after ep13)*
- **Slug:** `sci_ep14_pulsar_716hz`
- **Title:** `The Exact Spin Rate That Breaks a Star (716 Hz)`
- **Spoken hook:** `This star spins seven hundred sixteen times every second.`
- **Why this subject:** the first concept where BOTH retention levers come free from the
  subject itself. A strobing pulsar is in motion at frame zero (ep13's weak point is a calm
  static Earth; the 25%-stayed worst-ever opened on something inert). And rotation is
  inherently loopable — the end state IS the start state, which is what ep09's 107.1% AVD
  needed. Chosen over the remaining slate: ep10 Eddington has no crisp number, ep11 vacuum
  decay has NO number at all (breaks the "Exact [X]" formula), ep12 neutron drip is
  microscopic — the category that produced the 25% and 40% hooks.
- **Physics (verified):** PSR J1748−2446ad, 716 Hz = one rotation every 1.397 ms. Earth turns
  once per 24 h → ~62 million times slower. Neutron star ~20–32 km across. Equatorial speed is
  RADIUS-DEPENDENT (15% c at 10 km · 18% at 12 km · 24% at 16 km) and the radius is
  model-dependent, so the VO hedges "nears a fifth of light speed". 716 Hz is the exact figure.
- **Two fixes applied to the drafted script:** the rate curve was inverted (−12% on the hook,
  +0% on the payoff) which would have made the video get faster and lighter toward the end,
  attacking the quiet-close that drives the loop — restored to +0/−4/−8/−12. And the loop
  depends on all four clips sharing a rotation handedness, but no shot prompt said so; every
  shot now specifies **clockwise**. Earth was also removed from shot 2's visual (it stayed in
  the VO) to avoid a second recognizable solid object and repetition with ep13.
- **FIRST EPISODE ON WORD-POP CAPTIONS** — `captions="pop"`, `caption_chunk_words=3`.
- **Status:** ✅ RENDERED & POSTED 2026-09-27. 31.1s, 0 decode errors. Cost $1.05.
- **Title used:** `The Fastest Anything Has Ever Spun (716 Hz)` — deliberately DROPPED the
  "Exact [X]" pattern. The drafted title "The Exact Spin Rate That Breaks a Star" claimed
  716 Hz is a breaking point; it is not (neutron-star break-up is ~1000-1500 Hz depending on
  equation of state). 716 Hz is the fastest OBSERVED spin. Accuracy beat pattern consistency.
- **FOUR variables changed vs ep13 — attribution will be ambiguous:**
  1. Brightness arc 58→65→33→17, no cut over 45% (ep13 had -54% and -65% cliffs)
  2. Word-pop captions (`captions="pop"`, chunk=3) — first episode ever to use them
  3. `ambient_volume` 0.55 → 0.10, matching ep09 (107% AVD) instead of ep13 (53%)
  4. VO rewritten so beat 3 delivers an actual MECHANISM (angular momentum / skater
     analogy) instead of restating size+speed; beat 4 stopped re-serving 716 Hz as "1.4 ms"
- **WHAT TO WATCH:**
  - Stayed% — ep13 50.9%, best ever ep07 69.2%. Above ~60% means the dramatic hook worked.
  - AVD% — ep13 53%, best ever ep09 107%. Above ~80% means the brightness arc worked.
  - Shares — only ep07 has ever earned any (7). Any share count is signal.
- **NEXT EPISODE RULE: change ONE variable.** Four at once was the right call for a video
  that was already underperforming, but it makes this result unattributable. Hold the next
  one to a single change so the data means something.

### ep19 TON 618 *(NEW — built on the YouTube agent's answers, 2026-10-22)*
- **Slug:** `sci_ep19_ton618`
- **Title:** `The Black Hole That Weighs 66 Billion Suns (TON 618)`
- **Spoken hook:** `This black hole weighs sixty six billion Suns.` (big "66 BILLION SUNS" alone for 1.5s)
- **Why:** "This [extreme object] + number" openers hold 62-70% on this channel; "you"/question
  openers lose (ep18 40.5%). "ton 618" is a real search term. Keeps ep18's story pacing and
  phrase captions (110% APV).
- **Physics:** ~6.6e10 M☉ → horizon ~2,600 AU across ≈ 43x Neptune's orbit; light ~15 days to cross.
- **Build:** first-shot check `ONLY_SHOT=1 CHANNEL=b ENGINE=ltx VIDEO_ID=sci_ep19_ton618 python run_test_batch.py`,
  then the full render without ONLY_SHOT.
- **Playlist:** Space at Impossible Scale (supermassive, not a stellar death, so not Dead stars). **Related video:** Saturn star. **Post:** 4-6 PM IST (Fri-Sun best).
- **Pinned comment:** `Which monster in space should we cover next?`
- **Description:**
```
How big can a black hole get? TON 618, one of the largest known, weighs about 66 billion times the mass of the Sun, and its edge is over 40 times wider than Neptune's orbit. Even light takes more than two weeks to cross it.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #blackhole
```

### ep18 How fast is Earth moving? *(NEW — full LTX, built on the ep17 lessons)*
- **Slug:** `sci_ep18_earth_speed`
- **Title:** `How Fast Is Earth Moving Through Space? (30 km/s)`
- **Spoken hook:** `This planet moves thirty kilometres every second, and you're on it right now.`
- **Why:** ep17 (stills, number at word 14, quiet tail) held 38.8% stayed. This one has LTX motion
  from frame 0, a "This [thing]" opener with the number by word 6, Earth as the anchor, and ends on
  the spoken "230 km a second" with no linger so it loops.
- **Physics:** orbital speed 29.8 km/s; fast rifle rounds ~1-1.7 km/s (≈20x slower); we feel
  acceleration, not speed; the Sun circles the Milky Way at ~230 km/s.
- **Build (RunPod, ~$1):** `cd local_runner && CHANNEL=b ENGINE=ltx VIDEO_ID=sci_ep18_earth_speed python run_test_batch.py`
- **Playlist:** Exact Limits. **Related video:** solar escape (km/s follow-up).
- **Status:** script + LTX prompts ready; pending render → QC
- **Description:**
```
How fast is Earth moving through space? About 30 km every second around the Sun, so you travel about 100 km in the time it takes to say it. We can't feel it because only changes in speed are felt. And the Sun carries us around the galaxy at about 230 km/s.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### ep17 Sun as a black hole *(NEW — first planned zero-GPU still build)*
- **Slug:** `sci_ep17_sun_black_hole`
- **Title:** `What If the Sun Turned Into a Black Hole? (6 km Wide)`
- **Spoken hook:** `If the Sun collapsed into a black hole right now, it would be just six kilometres wide.`
- **Why:** familiar anchor (Sun, Earth) + hard number + an evergreen search question, and the
  "Earth wouldn't fall in" twist at the midpoint. Script tightened per YouTube review 2026-10-19.
- **Physics:** r_s = 2.95 km for 1 M☉ → 5.9 km across. Orbits depend only on mass → Earth's orbit unchanged.
- **Build ($0):** `VIDEO_ID=sci_ep17_sun_black_hole python fetch_still_assets.py` (NASA images from
  Wikimedia, PD only) → `CHANNEL=b VIDEO_ID=sci_ep17_sun_black_hole python still_video.py`
- **Status:** script + still specs ready; pending first laptop build → QC
- **Description:**
```
What would happen if the Sun turned into a black hole? It would shrink to just 6 km wide, and Earth would keep orbiting exactly as before, just in the dark.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### Mon 28 Sep 2026 — ep13 Earth → black hole *(SWAP, analytics-driven)*
- **File:** `sci_ep13_earth_black_hole_hook.mp4`
- **Slug:** `sci_ep13_earth_black_hole`
- **Title:** `The Exact Size Earth Must Shrink to Become a Black Hole (8.87 mm)`
- **Spoken hook:** `Crush Earth into a black hole, and it fits in eight point eight seven millimetres.`
- **Why this jumped the queue:** built against the first analytics pull. Stayed% and AVD% are
  independent levers and nothing has had both (ep07 hook 69.2% / ep09 loop 107.1%). This targets
  both: a universally recognizable subject for the hook, and ep09's dark-quiet-into-bright ending
  for the loop. Earth is also the most forwardable subject yet — shares are the biggest multiplier
  and only ep07 has earned any. **ep10 Eddington is NOT dropped**, it keeps its place in the queue.
- **Physics (verified):** r_s = 2GM/c². Earth → 8.870 mm RADIUS, so the horizon is 17.74 mm across
  — a marble, NOT a pea. Earth radius / r_s = 718,255,480. A 70 kg human → 1.04e-25 m.
- **Status:** Prompts + VO locked (2 review rounds). Pure T2V, no stills. Numeral captions via
  `caption_text`. Pending render → QC → schedule.
- **Pin comment — PICK ONE AT UPLOAD:** safe default `Which limit should we cross next?` OR the
  higher-engagement `Every mass has a Schwarzschild radius — drop your weight in kilograms below
  and I'll tell you how small you'd have to get.` (the second drives replies but COMMITS you to
  answering them; unanswered it reads worse than not asking).
- **Description:**
```
Compress Earth's entire mass into 8.87 millimetres and its gravity becomes inescapable — the exact threshold where a planet becomes a black hole.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### Mon 28 Sep 2026 — ep10 Eddington
- **File:** `sci_ep10_eddington_hook.mp4`
- **Slug:** `sci_ep10_eddington`
- **Title:** `The Exact Brightness That Blows a Star Apart`
- **Spoken hook:** `Above the Eddington limit, radiation pressure tears a star apart.`
- **Status:** Pending
- **Description:**
```
The maximum outward radiation force a star can produce before stripping its own atmosphere.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### Tue 29 Sep 2026 — ep11 vacuum decay
- **File:** `sci_ep11_vacuum_decay_hook.mp4`
- **Slug:** `sci_ep11_vacuum_decay`
- **Title:** `The Speed-of-Light Sphere That Deletes the Universe`
- **Spoken hook:** `This is vacuum decay: if space drops into a lower energy state, physics resets instantly.`
- **Status:** Pending
- **Description:**
```
How a true-vacuum nucleation bubble would expand at light speed, altering physical constants forever.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### Wed 30 Sep 2026 — ep12 neutron drip *(swap)*
- **File:** `sci_ep12_neutron_drip_hook.mp4`
- **Slug:** `sci_ep12_neutron_drip`
- **Title:** `The Exact Density Where Protons and Electrons Fuse`
- **Spoken hook:** `Past the neutron-drip density—400 billion grams per centimeter—atoms vanish.`
- **Status:** Pending
- **Description:**
```
The critical density threshold where electron-capture / neutron drip erases normal atomic structure.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

---

## Analytics log

> **Reading this table:** view counts are CONFOUNDED by channel age — ep01/ep04 were early posts to a
> cold channel, so their low views are not a quality signal (ep01 has a 75.5% AVD). Judge on the two
> retention levers instead, which move independently:
> **Stayed %** = the first-2s hook (best: ep07 69.2% · worst: ep04 25.0%).
> **AVD %** = whether the ending loops (best: ep09 107.1% — re-watches are what drove its 1,185 views).
> Target for every new episode: **ep07's hook + ep09's loop.**
> **2026-09-28 RESULT — ep14 is the first to move BOTH.** vs ep13: views 262 -> 971 (3.7x),
> stayed 48.9% -> 59.6% (+10.7pts), AVD 55.4% -> 92.1% (+36.7pts). Four variables changed at
> once (brightness arc / word-pop captions / ambient 0.55->0.10 / mechanism-driven VO), so
> strict attribution is impossible — but the biggest gain (AVD) landed exactly where the
> brightness-arc fix was aimed, and `shot_qc.py` caught a -70% cliff + a frozen shot before
> that render ever shipped. STILL SHORT: 92.1% vs ep09's 106.9%. Above 100% = replays.
> NEXT TEST: hold everything constant, change ONLY the ending, and try to buy the loop.
> Shares are the biggest distribution multiplier and only ep07 earned any (7); drama is what gets forwarded.

| Date | Short | Stayed to watch | Engaged views | APV | Viewed vs swiped | Subs Δ | Agent review | Notes |
|------|-------|-----------------|---------------|-----|------------------|--------|--------------|-------|
| 19 Sep | ep01 | 40.0% | 8 views | 75.5% (22s) | — | | | 194 dB. Good AVD, tiny views — channel had no audience yet. NOT a quality signal. |
| 20 Sep | ep02 | 40.3% | 290 views | 73.7% (16s) | — | | | Roche limit. Weak hook (40.3%) — opening did not stop the swipe. |
| 21 Sep | ep03 | | | | | | | |
| 22 Sep | ep04 | 25.0% | 12 views | 62.3% (15s) | — | | | 0 K. WORST hook on channel (25%). Abstract topic, no visual payoff in first 2s. |
| 23 Sep | ep05 | 64.1% | 444 views | 72.5% (20s) | — | | | Spaghettification. Strong hook — evocative named concept. |
| 24 Sep | ep06 | | | | | | | |
| 25 Sep | ep07 | **69.2%** | 889 views | 78.3% (24s) | — | | | White dwarf 1.44 M☉. BEST HOOK (69.2%) and the ONLY video with shares (7). Drama = forwardable. |
| 26 Sep | ep08 | | | | | | | |
| 27 Sep | ep09 | 52.9% | 1185 views | **107.1% (34s)** | — | | | BEST VIEWS. Won on LOOP not hook: AVD>100% = re-watches. Dark/quiet ending vs bright opening. |
| 28 Sep | ep10 | | | | | | | |
| 29 Sep | ep11 | | | | | | | |
| 30 Sep | ep12 | | | | | | | |

**Scorecard:** see [`THRESHOLD_PHYSICS_STRATEGY.md`](THRESHOLD_PHYSICS_STRATEGY.md) §8 — checkpoints after ep10 and after the full 12.

---

## YouTube Studio steps (each upload)

1. Upload → that day’s `sci_*_hook.mp4`
2. Title + Description = copy from above (after agent review tweaks)
3. Visibility: **Schedule** for **12:00 IST**
4. Confirm Shorts shelf
5. Pin comment: `Which limit should we cross next?`

---

## YouTube agent review prompt (copy each time)

```
Review this Threshold Physics Short before I schedule it.

NICHE RULES
- Promise: exact numerical limits where physical reality breaks down
- Formula: threshold (0–3s) → paradox → one law → visual climax
- No faces, cinematic CGI, VO + captions
- Target: 26–36s, high contrast, number/named limit in first 8 spoken words

MY DRAFT
- Title: [paste]
- Hook VO: [paste]
- Description: [paste]
- Length: [Ns]
- Frame-1 description: [paste]
- Known weak spots from my watch: [optional]

REVIEW FOR
1) Hook strength (0–3s) — swipe risk
2) Title match to content (CTR vs retention honesty)
3) Mid-video drop risk (jargon / drag)
4) Caption / packaging tweaks (keep ≤5 hashtags, keep #ThresholdPhysics)
5) Pass / revise / re-render — be blunt

If revise: give exact new title + first sentence + what to cut.
```

---

## Render notes (operator)

Prompts live in [`local_runner/science_prompts.py`](local_runner/science_prompts.py) (Top 12 beat scripts).

```bash
cd local_runner
# Single episode (start here):
CHANNEL=b ENGINE=ltx VIDEO_ID=sci_ep01_sound_194db python run_test_batch.py

# Full Top 12 (one RunPod session each):
./render_channel_b.sh
```

Then: local QC → YouTube AI review (prompt above) → `./promote_to_ready.sh <slug>` → schedule 12:00 IST.

**Zero-GPU option (no RunPod):** build the same episode from still images on the laptop.
Same VO, captions and crossfades; each beat is a still with a slow camera move. Uses
`i2v_stills/<slug>/shot_N.png` if present, else a `still` spec on the beat, else a starfield.
Output is `final_videos/<slug>_still_complete.mp4` (never overwrites an LTX render).

```bash
cd local_runner
CHANNEL=b VIDEO_ID=sci_ep08_metallic_hydrogen python still_video.py
```

ep16 (2.5 Suns, 53.4% stayed) and ep08N v2/v3 (20 km) were made this way and held up
against LTX episodes, so it suits familiar-object comparisons (star vs city, planet vs star).
