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
- **Spoken hook:** `At the Chandrasekhar limit—1.44 solar masses—a white dwarf cannot hold itself up.`
- **Status:** Pending
- **Description:**
```
The physical limit where atomic electrons can no longer support a dying star against gravity.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### Sat 26 Sep 2026 — ep08 metallic hydrogen
- **File:** `sci_ep08_metallic_hydrogen_hook.mp4`
- **Slug:** `sci_ep08_metallic_hydrogen`
- **Title:** `The Exact Pressure That Turns Gas into Liquid Metal (400 GPa)`
- **Spoken hook:** `This is the metallic hydrogen threshold: compress gas to 4 million atmospheres, and it turns into metal.`
- **Status:** Pending
- **Description:**
```
Descending into the deep planetary core where extreme pressure forces gas into a liquid metallic sea.

One threshold. One law. One image.

#ThresholdPhysics #physics #science #space #universe
```

### Sun 27 Sep 2026 — ep09 solar escape *(swap)*
- **File:** `sci_ep09_solar_escape_hook.mp4`
- **Slug:** `sci_ep09_solar_escape`
- **Title:** `The Exact Speed Needed to Escape the Sun (617.5 km/s)`
- **Spoken hook:** `Below solar escape velocity—617 kilometers a second—the Sun traps you.`
- **Status:** Pending
- **Description:**
```
The solar escape-velocity threshold — below it, gravity wins; above it, you leave the star’s grip.

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

| Date | Short | Stayed to watch | Engaged views | APV | Viewed vs swiped | Subs Δ | Agent review | Notes |
|------|-------|-----------------|---------------|-----|------------------|--------|--------------|-------|
| 19 Sep | ep01 | | | | | | | |
| 20 Sep | ep02 | | | | | | | |
| 21 Sep | ep03 | | | | | | | |
| 22 Sep | ep04 | | | | | | | |
| 23 Sep | ep05 | | | | | | | |
| 24 Sep | ep06 | | | | | | | |
| 25 Sep | ep07 | | | | | | | |
| 26 Sep | ep08 | | | | | | | |
| 27 Sep | ep09 | | | | | | | |
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
