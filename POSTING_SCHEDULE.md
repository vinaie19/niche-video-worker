# After Hours Japan — posting schedule

**Phase:** ship QC-good backlog only → pause for analytics → then continue or pivot.  
**Generation:** paused (network volume down until we restart on purpose).  
**Cadence:** 1 public Short per day  
**Window:** same time daily (suggested **21:00 IST**)  
**File source:** `final_videos/ready/*_hook.mp4`  
**Rule:** do not publish two on the same day; skip broken videos

Paste **Title** + **Description** into YouTube Studio for each upload.

Shared hashtags (already included in every description):

```
#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

---

## Shipped

### Fri 11 Sep 2026 — s2_ep01 izakaya
- **File:** `s2_ep01_izakaya_lantern_hook.mp4`
- **Title:** `After Hours Japan | Still Warm | Izakaya After Hours`
- **Status:** Live

### Sat 12 Sep 2026 — s2_ep02 sento
- **File:** `s2_ep02_sento_steam_hook.mp4`
- **Title:** `After Hours Japan | Sento after everyone went home`
- **Status:** Live

### Sun 13 Sep 2026 — s2_ep04 taxi stand
- **File:** `s2_ep04_taxi_stand_rain_hook.mp4`
- **Title:** `After Hours Japan | Rain at an empty taxi stand`
- **Status:** Live

### SKIP — s2_ep05 temple
- **File:** `s2_ep05_temple_incense_hook.mp4`
- **Reason:** skipped in queue (not posted between taxi and ferry/arcade).
- Hold out of queue unless we deliberately revisit.

### ~Mon 14 Sep 2026 — s2_ep06 ferry
- **File:** `s2_ep06_ferry_waiting_hook.mp4`
- **Title:** `After Hours Japan | Ferry terminal with nobody waiting`
- **Status:** Live

### Tue 15 Sep 2026 — s2_ep07 arcade
- **File:** `s2_ep07_arcade_glow_hook.mp4`
- **Title:** `After Hours Japan | Empty arcade still running at night`
- **Status:** Live (posted early; took the old Wed 16 slot)

### SKIP — s2_ep03 bookstore
- **File:** `s2_ep03_bookstore_lamp_hook.mp4`
- **Reason:** last shot has floating AI gibberish text. Do not post unless trimmed/regenerated.
- Hold out of queue for now.

---

## Season 3 — Places That Stay Open

(S3 order is strongest-hook-first, not episode number. Dates pulled forward one day after arcade posted early.)

### Wed 16 Sep 2026 — s3_ep07 hotel ice
- **File:** `s3_ep07_hotel_ice_machine_hook.mp4`
- **Title:** `After Hours Japan | Every hotel has this lonely machine`
- **Description:**
```
Every hotel has this lonely ice machine in an empty corridor.
Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

### Thu 17 Sep 2026 — s3_ep05 karaoke
- **File:** `s3_ep05_karaoke_corridor_hook.mp4`
- **Title:** `After Hours Japan | Empty karaoke hallway at 2AM`
- **Description:**
```
Someone left the karaoke lights on in an empty hallway.
Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

### Fri 18 Sep 2026 — s3_ep02 florist
- **File:** `s3_ep02_florist_fridge_hook.mp4`
- **Title:** `After Hours Japan | Flower shop cooler that never sleeps`
- **Description:**
```
Flowers waiting all night in the shop cooler.
Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

### Sat 19 Sep 2026 — s3_ep04 manga cafe
- **File:** `s3_ep04_manga_cafe_hook.mp4`
- **Title:** `After Hours Japan | Manga cafe at 3AM with nobody inside`
- **Description:**
```
All-night manga booth. Empty.
Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```
- **QC note:** check for fake spine text; skip if bad.

### Sun 20 Sep 2026 — s3_ep06 fish market
- **File:** `s3_ep06_fish_market_ice_hook.mp4`
- **Title:** `After Hours Japan | Closed fish market on ice`
- **Description:**
```
Fish market ice before the city wakes.
Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

### Mon 21 Sep 2026 — s3_ep03 bowling
- **File:** `s3_ep03_bowling_lanes_hook.mp4`
- **Title:** `After Hours Japan | Bowling alley after the last game`
- **Description:**
```
Bowling lanes still lit after the last frame.
Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

### Tue 22 Sep 2026 — s3_ep01 parking
- **File:** `s3_ep01_parking_fluorescent_hook.mp4`
- **Title:** `After Hours Japan | Empty parking garage at night`
- **Description:**
```
Fluorescent buzz in an empty underground parking garage.
Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

---

## Early analytics notes (mid-Sep 2026)

Direction only — finish backlog before restoring generation.

| Metric | Early winner | Takeaway |
|---|---|---|
| Stayed to watch | Sento ~29% | First-frame steam/sound/light stops scroll |
| Avg % viewed + browse CTR | Late Night Ramen ~83% APV | Comfort + rain + food holds and converts |
| Theme | Food / cozy rain > abstract voids | Prefer sensory scenes over place labels |

**If continuing After Hours after the gate:** lead with 0.5–1s audio+motion hook; bias subjects toward late-night food / wet streets / warm interiors; write sensory titles; optional sub-15s loops for rewatch.

---



---

## Series 4 — Sensory night (generate → QC → pick winners)

**Pattern locked:** warm food / steam / drip + cold rain; motion in first frames; no people; no readable text.
**Batch:** `local_runner/test_prompts.py` (`s4_ep01`–`s4_ep10`). Prompt pack: `local_runner/SEASON4_PROMPTS.md`.
**Render:** `CHANNEL=a ENGINE=ltx VIDEO_ID=<slug> python run_test_batch.py`
**Rule:** render all (or a subset), QC locally, promote only keepers to `ready/`, upload the best.

### s4_ep01_ramen_steam_rain
- **File:** `s4_ep01_ramen_steam_rain_hook.mp4`
- **Overlay:** `Still steaming.`
- **Title:** `After Hours Japan | Late night ramen still steaming in the rain`
- **Status:** Prompt ready — pending render → QC
- **Description:**
```
Late night ramen still steaming while the rain keeps the street empty.

Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

### s4_ep02_taiyaki_griddle
- **File:** `s4_ep02_taiyaki_griddle_hook.mp4`
- **Overlay:** `Still sizzling.`
- **Title:** `After Hours Japan | Taiyaki griddle still hot at 1AM`
- **Status:** Prompt ready — pending render → QC
- **Description:**
```
Fish-shaped cakes still sizzling on the iron molds after midnight.

Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

### s4_ep03_convenience_oden
- **File:** `s4_ep03_convenience_oden_hook.mp4`
- **Overlay:** `Still simmering.`
- **Title:** `After Hours Japan | Conbini oden pot that never sleeps`
- **Status:** Prompt ready — pending render → QC
- **Description:**
```
The convenience-store oden pot keeps simmering under fluorescent light.

Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

### s4_ep04_yakitori_grill_drip
- **File:** `s4_ep04_yakitori_grill_drip_hook.mp4`
- **Overlay:** `Fat still drips.`
- **Title:** `After Hours Japan | Yakitori coals still glowing after last call`
- **Status:** Prompt ready — pending render → QC
- **Description:**
```
Skewers over charcoal — fat still drips into the coals after last call.

Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

### s4_ep05_udon_noodle_steam
- **File:** `s4_ep05_udon_noodle_steam_hook.mp4`
- **Overlay:** `Still boiling.`
- **Title:** `After Hours Japan | Udon pot still boiling at midnight`
- **Status:** Prompt ready — pending render → QC
- **Description:**
```
Thick udon noodles lifted from water that never quite stops boiling.

Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

### s4_ep06_hotpot_solo_booth
- **File:** `s4_ep06_hotpot_solo_booth_hook.mp4`
- **Overlay:** `Table for one.`
- **Title:** `After Hours Japan | Solo hotpot booth still bubbling at 2AM`
- **Status:** Prompt ready — pending render → QC
- **Description:**
```
A one-person hotpot keeps bubbling in an empty booth.

Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

### s4_ep07_rain_gutter_alley
- **File:** `s4_ep07_rain_gutter_alley_hook.mp4`
- **Overlay:** `Still raining.`
- **Title:** `After Hours Japan | Rain gutter alley that never dries`
- **Status:** Prompt ready — pending render → QC
- **Description:**
```
Rainwater keeps streaming down a narrow Tokyo alley drain.

Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

### s4_ep08_vending_condensation
- **File:** `s4_ep08_vending_condensation_hook.mp4`
- **Overlay:** `Glass still fogged.`
- **Title:** `After Hours Japan | Vending machine fogged up in the rain`
- **Status:** Prompt ready — pending render → QC
- **Description:**
```
A glowing drink machine stands alone, glass fogged with cold condensation.

Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

### s4_ep09_dumpling_steamer
- **File:** `s4_ep09_dumpling_steamer_hook.mp4`
- **Overlay:** `Lids still venting.`
- **Title:** `After Hours Japan | Dumpling steamers still venting at night`
- **Status:** Prompt ready — pending render → QC
- **Description:**
```
Stacked bamboo steamers keep venting over the burner after the crowd is gone.

Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

### s4_ep10_okonomiyaki_griddle
- **File:** `s4_ep10_okonomiyaki_griddle_hook.mp4`
- **Overlay:** `Still on the iron.`
- **Title:** `After Hours Japan | Okonomiyaki still sizzling on the iron`
- **Status:** Prompt ready — pending render → QC
- **Description:**
```
Okonomiyaki keeps sizzling on the flat-top after the last order.

Empty places after midnight in Japan.

#AfterHoursJapan #japan #asmr #aesthetic #liminal #nightwalk #shorts
```

## After backlog (~23 Sep)

1. Stop posting new AI batches.
2. Read Analytics for ~7–14 days of data: views, avg % viewed / engaged views, stayed-to-watch, subs.
3. **Continue After Hours** only if a few shorts clearly retain; then restore network volume and generate (apply early-analytics bias above).
4. **Otherwise** explore next niche (speculative science first) — don’t burn GPU on more of the same first.

---

## YouTube Studio steps (each day)

1. Upload → that day’s `*_hook.mp4`
2. Title + Description = copy from above
3. Visibility: **Schedule** for 21:00 IST (or Publish at that time)
4. Confirm it lands in the **Shorts** shelf
