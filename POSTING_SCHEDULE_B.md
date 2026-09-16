# Threshold Physics — posting schedule (Channel B)

**Channel:** separate YouTube account from After Hours Japan  
**Promise:** One question. One physics limit. One image.  
**Generation:** `CHANNEL=b` + `ENGINE=ltx|wan|hunyuan` (see [local_runner/render_channel_b.sh](local_runner/render_channel_b.sh))  
**Cadence:** Mon–Fri, **12:00 IST** (cold start)  
**File source:** `final_videos/ready/sci_*_hook.mp4`  
**Rule:** never reuse After Hours hashtags or cross-promote

Shared hashtags (every description):

```
#ThresholdPhysics #space #physics #whatif #astronomy #shorts
```

---

## QC before `ready/`

1. Watch `final_videos/sci_ep0N_*_complete.mp4`
2. First 2s: motion + question readable in captions
3. No gibberish text / logos in any shot
4. VO ends; last 3–5s mostly quiet linger
5. Total ~30–45s
6. Copy: `cp final_videos/sci_ep0N_*_complete.mp4 final_videos/ready/sci_ep0N_*_hook.mp4`

Or: `./local_runner/promote_to_ready.sh sci_ep01_sun_closer`

---

## Batch 1 — queue (fill dates when first upload goes live)

### Mon — sci_ep01_sun_closer
- **File:** `sci_ep01_sun_closer_hook.mp4`
- **Title:** `What If the Sun Were 10% Closer? The Limit That Fails First`
- **Description:**
```
What if the Sun moved 10% closer — which physics limit fails first?

Not instant melted rock. The first break is Earth's energy budget (~21% more sunlight), then an expanding upper atmosphere.

One threshold. One principle. One image.

#ThresholdPhysics #space #physics #whatif #astronomy #shorts
```

### Tue — sci_ep02_dyson_heat
- **File:** `sci_ep02_dyson_heat_hook.mp4`
- **Title:** `How Does a Dyson Swarm Dump Waste Heat?`
- **Description:**
```
A Dyson swarm doesn't fail by blocking starlight — it fails on waste heat.

Every watt used must be radiated away. The limit is thermodynamics at stellar scale.

#ThresholdPhysics #space #physics #whatif #astronomy #shorts
```

### Wed — sci_ep03_black_hole_outer
- **File:** `sci_ep03_black_hole_outer_hook.mp4`
- **Title:** `A Black Hole in the Outer Solar System — What Breaks First?`
- **Description:**
```
If a stellar-mass black hole drifted into the outer solar system, orbital chaos comes long before any event horizon reaches Earth.

The threshold is rewritten comet paths — not a cinematic plunge.

#ThresholdPhysics #space #physics #whatif #astronomy #shorts
```

### Thu — sci_ep04_atmosphere_freeze
- **File:** `sci_ep04_atmosphere_freeze_hook.mp4`
- **Title:** `How Cold Before a Planet's Atmosphere Freezes Out?`
- **Description:**
```
Cold enough, gases condense and fall from the sky. The atmosphere stops being a permanent ocean and becomes frost on the ground.

The threshold is phase change — not instant vacuum.

#ThresholdPhysics #space #physics #whatif #astronomy #shorts
```

### Fri — sci_ep05_elevator_snap
- **File:** `sci_ep05_elevator_snap_hook.mp4`
- **Title:** `Where Does a Space Elevator Snap First?`
- **Description:**
```
A space elevator fails at the tension limit — often in the lower atmosphere, not at orbit.

Cross the material threshold and the cable whips faster than the ground can survive.

#ThresholdPhysics #space #physics #whatif #astronomy #shorts
```

---

## Analytics log (first 14 days)

| Short | Stayed to watch | Engaged views | APV | Subs delta | Notes |
|-------|-----------------|---------------|-----|------------|-------|
| ep01 | | | | | |
| ep02 | | | | | |
| ep03 | | | | | |
| ep04 | | | | | |
| ep05 | | | | | |

---

## YouTube Studio steps (each upload)

1. Upload → that day’s `sci_*_hook.mp4`
2. Title + Description = copy from above
3. Visibility: **Schedule** for 12:00 IST
4. Confirm Shorts shelf
5. Pin comment: “Which limit should we cross next?”

---

## Render commands (operator)

```bash
cd local_runner
# Episode 1 (LTX)
CHANNEL=b ENGINE=ltx VIDEO_ID=sci_ep01_sun_closer python run_test_batch.py

# Episode 2 (Wan)
CHANNEL=b ENGINE=wan VIDEO_ID=sci_ep02_dyson_heat python run_test_batch.py

# Episode 3 (LTX)
CHANNEL=b ENGINE=ltx VIDEO_ID=sci_ep03_black_hole_outer python run_test_batch.py

# Episode 4 (Hunyuan)
CHANNEL=b ENGINE=hunyuan VIDEO_ID=sci_ep04_atmosphere_freeze python run_test_batch.py

# Episode 5 (Wan)
CHANNEL=b ENGINE=wan VIDEO_ID=sci_ep05_elevator_snap python run_test_batch.py
```

Or run all five in engine order: `./render_channel_b.sh`
