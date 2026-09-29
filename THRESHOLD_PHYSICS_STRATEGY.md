# Threshold Physics — Niche Strategy (Locked)

**Status:** Locked for 30-day test (Sep 2026)  
**Channel:** separate YouTube account from After Hours Japan  
**Primary goal:** Shorts YPP monetization speed  
**Infra:** LTX cinematic CGI + Edge-TTS VO + burned-in captions + ambient bed  
**Hard constraints:** no faces / no people / no crowds / no paid video APIs  

Related docs:

- Posting queue + dates → [`POSTING_SCHEDULE_B.md`](POSTING_SCHEDULE_B.md)
- Channel rules → [`.cursor/rules/channel-strategy.mdc`](.cursor/rules/channel-strategy.mdc)
- Render → `local_runner/render_channel_b.sh`

---

## 1) Niche lock

| Item | Decision |
|---|---|
| **Public niche** | Physics Limits / Thresholds |
| **Promise** | Visualizing the exact numerical limits where physical reality breaks down. |
| **One-liner** | One threshold → one law → one lingering image. |
| **Not this** | Silent ambient Japan (Channel A), kitchen-sink What If, faces, meme hyper-cuts |
| **Sub-angles (inside niche only)** | Scale comparisons, extreme depth/pressure, deep time — never separate channels |

### Why this wins (vs A and alternatives)

- Spoken VO + captions attack swipe-away better than silent ambient.
- Named/numeric limits create clear curiosity gaps and comment debate.
- LTX strengths (voids, glow, scale, locked cinematic camera) match the visuals.
- Scale / depth / deep-time are **episode modes**, not rival niches.

### Common Shorts advice to IGNORE

- Cut every ~0.8s (destroys cinematic scale)
- Over-hyped shouting VO
- Face cams / character acting / crowds
- Soft intros (“Did you know…”, “Scientists have long…”)

---

## 2) Content formula (26–36s target)

```
00:00–00:03 | HOOK       | Hard numeric / named threshold + high-contrast motion
00:03–00:10 | CONFLICT   | Why normal intuition fails
00:10–00:22 | MECHANISM  | One physical rule (intuitive metaphor, not jargon)
00:22–00:28 | PAYOFF     | Visual / existential consequence of crossing the limit
00:28–00:30 | LOOP       | Last beat feeds the opening paradox (optional)
```

> ### ⚠️ HOOK RULE REVISED 2026-09-28 — from 10 published episodes
> The original rule below said the hook is a "hard numeric / named threshold".
> **The data says the opposite.** Ranked by Stayed-to-watch:
>
> | Opens with | Mean stayed |
> |---|---|
> | a CONCRETE image / object / action | **57.5%** (n=6) |
> | a NUMBER, UNIT, or TECHNICAL TERM | **34.0%** (n=4) |
>
> A 23.5-point gap. Every opening that leads with a unit or jargon is in the bottom
> four: "At absolute zero — zero kelvin" (25%), "At the 194-decibel sound barrier"
> (25%), "Cross the Roche limit" (40.3%), "There's a wall... 300 suns of mass" (45.7%).
> The best hook on the channel — 68.5% — contains **no number at all**:
> *"This dead star is only the size of Earth, but it weighs almost as much as the Sun."*
> Two familiar objects held against each other.
>
> **THE NUMBER IS NOT THE HOOK. THE NUMBER IS THE PAYOFF.** Open on something a
> person can picture without being taught anything; land the figure at 3-6s.
> Familiar-object units (Earth, the Sun, a mountain) are fine — technical units
> (kelvin, decibels, solar masses, hertz) are what kill it.
>
> **Two levers, two causes** (this model fits all 10 episodes):
> STAYED% is driven by the OPENING STYLE. AVD% is driven by whether something
> HAPPENS at the threshold. ep07 had a concrete opening but a static subject
> (68.5% stay / 77.6% AVD). ep09 had a weaker opening but a real event and a loop
> (52.9% / 106.9%). ep10 had neither (45.7% / 51.7%).

**Rules**

- ~~Stakes in the **first 8 spoken words**~~ → **Open on a concrete image; number lands by ~6s**
- Audio + motion start at **frame ~0** (no dead 0.5s)
- Script cap: **~55–65 words** for a ~30s Short
- Reveal: **threshold early**, **consequence late**
- Captions: bold center, 1–3 words/pop, numbers highlighted
- Visible anchor object in frame 1 (planet, sphere, wave, star — not abstract noise)

---

## 3) Packaging standards

### Titles (prefer numeric / named)

1. `The Exact Point Where [X] Breaks`
2. `What Happens At [Exact Number/Limit]?`
3. `The Exact [Distance/Mass/Temp/Pressure] That [Consequence]`

Numeric/threshold titles outperform poetic titles.

### Description

One concise payoff line, then hashtags.

### Hashtags (5 max — every Short)

```
#ThresholdPhysics #physics #science #space #universe
```

### Pin comment (default)

`Which limit should we cross next?`

---

## 4) Hardened Top 12 slate (posting order)

Order ranked for **visual clarity + hook punch**.  
Episodes 9 and 12 use the **recommended swaps** (lower render/confusion risk).

| # | Topic | File slug (planned) | Risk |
|---|---|---|---|
| 1 | 194 dB Sound Barrier | `sci_ep01_sound_194db` | Low–Med |
| 2 | Roche Limit | `sci_ep02_roche_limit` | Low |
| 3 | Neutron Star Surface Impact | `sci_ep03_neutron_impact` | Low |
| 4 | Absolute Zero (0 K) | `sci_ep04_absolute_zero` | Low |
| 5 | Spaghettification Radius | `sci_ep05_spaghettification` | Low |
| 6 | Absolute Hot (Planck T) | `sci_ep06_absolute_hot` | Med |
| 7 | Chandrasekhar Limit (1.44 M☉) | `sci_ep07_chandrasekhar` | Low |
| 8 | Metallic Hydrogen (400 GPa) | `sci_ep08_metallic_hydrogen` | Low |
| 9 | Solar Escape Velocity (617.5 km/s) | `sci_ep09_solar_escape` | Low *(swap)* |
| 10 | Eddington Luminosity Limit | `sci_ep10_eddington` | Low |
| 11 | Vacuum Decay (True Vacuum) | `sci_ep11_vacuum_decay` | Med |
| 12 | Neutron Drip / Critical Density | `sci_ep12_neutron_drip` | Low *(swap)* |

### Cut from earlier drafts (do not use early)

Planck Length, Degenerate Matter (abstract), GZK Limit, Landauer Limit, Superfluid Rollin Film (confusing CGI), Last Iron Star (too static).

### Delayed / saturated angles (later, after retention proven)

Generic “inside a black hole”, bare “speed of light”, multiverse theory dumps.

### Parked Batch-0 ideas (old queue — not primary)

`sci_ep01_sun_closer`, `sci_ep02_dyson_heat`, `sci_ep03_black_hole_outer`, `sci_ep04_atmosphere_freeze`, `sci_ep05_elevator_snap` — keep files if rendered; do **not** let them override this Top 12 posting order unless analytics say otherwise.

---

## 5) Episode packaging blueprint

### Ep 01 — 194 dB Sound Barrier

- **Title:** `The Exact Point Where Sound Destroys Matter (194 dB)`
- **Spoken hook:** At 194 decibels, sound stops being sound and becomes a shockwave.
- **Description:** What happens when an acoustic wave carries more energy than the atmosphere can physically hold?
- **Frame 1:** Glowing acoustic shockwave tearing pressurized gas into a dark void.

### Ep 02 — Roche Limit

- **Title:** `The Exact Distance Where Gravity Shatters a Moon`
- **Spoken hook:** Cross this exact boundary, and planetary gravity shreds an entire moon.
- **Description:** The Roche Limit is the exact gravitational threshold where celestial bodies get ripped into rings.
- **Frame 1:** Cracked lunar body fracturing into luminous debris around a gas giant.

### Ep 03 — Neutron Star Surface Impact

- **Title:** `Dropping an Object 1 Meter at 200 Million Gs`
- **Spoken hook:** On a neutron star, drop a solid mass one meter—and it hits with nuclear force.
- **Description:** The extreme gravitational threshold where a one-meter fall releases the energy of a nuclear blast.
- **Frame 1:** Dense metallic sphere flattening into an ultra-bright plasma ring on a glowing blue crust.

### Ep 04 — Absolute Zero (0 K)

- **Title:** `The Exact Temperature Where Atomic Motion Stops (0 K)`
- **Spoken hook:** Cool matter to absolute zero, and all motion completely vanishes.
- **Description:** The absolute lower limit of thermodynamics where atomic kinetic energy hits pure zero.
- **Frame 1:** Hyper-vibrating crystalline lattice freezing into a motionless dark structure.

### Ep 05 — Spaghettification Radius

- **Title:** `The Exact Point Where Gravity Stretches Matter Into Spaghetti`
- **Spoken hook:** Spaghettification: too close to a black hole, gravity stretches matter into spaghetti.
- **Description:** Too close to a black hole, tidal gravity stretches matter into thin filaments — spaghetti.
- **Frame 1:** Small cratered rocky asteroid already elongating toward a pitch-black compact core, white-gold tidal seams, immediate stretch.

### Ep 06 — Absolute Hot (Planck Temperature)

- **Title:** `The Temperature Where Physics Completely Breaks (10^32 K)`
- **Spoken hook:** Heat an object past 141 nonillion degrees, and physics collapses.
- **Description:** At the Planck temperature, thermal radiation creates gravitational fields strong enough to collapse space.
- **Frame 1:** Piercing white core vibrating then disintegrating into a pitch-black rupture.

### Ep 07 — Chandrasekhar Limit

- **Title:** `The Exact Mass That Causes a White Dwarf Collapse (1.44 M☉)`
- **Spoken hook:** This tiny dead star is the size of Earth, but it weighs almost as much as the Sun.
- **Description:** The physical limit where atomic electrons can no longer support a dying star against gravity.
- **Frame 1:** SAME solid white dwarf, rigid round blue-white crust with sharp circular silhouette, a thin wisp of companion gas starting to trickle on. (Arc: stable → crust cracks → shrinks and caves in → bursts with solid core + sharp debris; never soft blob / hollow ring.)

### Ep 08 — Metallic Hydrogen (400 GPa)

- **Title:** `The Exact Pressure That Turns Gas into Liquid Metal (400 GPa)`
- **Spoken hook:** Squeeze hydrogen to 400 gigapascals, and the lightest gas there is turns into liquid metal.
- **Description:** Descending into the deep planetary core where extreme pressure forces gas into a liquid metallic sea.
- **Frame 1:** Descent through pitch-black storms onto a turbulent mirror-reflective liquid silver surface.

### Ep 09 — Solar Escape Velocity *(swap for Superfluid)*

- **Title:** `The Exact Speed Needed to Escape the Sun (617.5 km/s)`
- **Spoken hook:** Move slower than 617 kilometers per second, and the Sun traps you.
- **Description:** The solar escape-velocity threshold — below it, gravity wins; above it, you leave the star’s grip.
- **Frame 1:** Object accelerating away from a massive solar flare arc into deep space.

### Ep 10 — Eddington Luminosity Limit

- **Title:** `The Exact Brightness That Blows a Star Apart`
- **Spoken hook:** Shine brighter than this limit, and radiation pressure tears you apart.
- **Description:** The maximum outward radiation force a star can produce before stripping its own atmosphere.
- **Frame 1:** Hyper-luminous blue giant shedding outer gas in violent glowing radial plumes.

### Ep 11 — Vacuum Decay (True Vacuum)

- **Title:** `The Speed-of-Light Sphere That Deletes the Universe`
- **Spoken hook:** If space drops into a lower energy state, physics resets instantly.
- **Description:** How a true-vacuum nucleation bubble would expand at light speed, altering physical constants forever.
- **Frame 1:** Smooth dark void bubble expanding across stars, extinguishing them cleanly.

### Ep 12 — Neutron Drip / Critical Density *(swap for Iron Star)*

- **Title:** `The Exact Density Where Protons and Electrons Fuse`
- **Spoken hook:** Compress matter past 400 billion grams per centimeter, atoms vanish.
- **Description:** The critical density threshold where electron-capture / neutron drip erases normal atomic structure.
- **Frame 1:** Glowing molecular lattice crushed into a solid ultra-dense glowing blue slab.

---

## 6) Hook templates (ranked)

1. **Hard Boundary Paradox** — “There is a maximum… but it isn’t about X.”
2. **Temperature / Number Inversion** — “Past [N], [familiar thing] stops existing.”
3. **Proximity Death Clock** — “At [distance], [body] is ripped into…”
4. **Universal Decay Rule** — “Every [particle/system] has an expiration…”
5. **Scale Inversion** — “Compress [object] to [size], this happens.”
6. **Pressure Threshold** — “At [P], [gas/phase] becomes [new state].”
7. **Time / Perspective Paradox** — use sparingly after retention is proven.

---

## 7) QC + YouTube agent review (per render)

### Local QC before `ready/`

1. Watch `final_videos/sci_epNN_*_complete.mp4`
2. First 2s: motion + threshold readable in captions / VO
3. No gibberish text / logos
4. VO ends; last 3–5s mostly quiet linger (or clean loop)
5. Total ~26–36s (ok up to ~45s if retention holds)
6. Promote only if QC pass:  
   `./local_runner/promote_to_ready.sh <slug>`

### YouTube Studio AI review (after each render, before schedule)

Paste into YouTube’s AI assistant with the video / draft metadata:

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

Only schedule after: **local QC pass** + **agent review = pass or minor copy tweaks**.

---

## 8) Metric scorecard

Evaluate across recent uploads (exclude one-off spikes).

| Metric | Double down | Tweak hooks | Tweak script | Pivot |
|---|---|---|---|---|
| Viewed vs swiped | >70% | <60% but APV >85% | >70% but APV <75% | <55% and APV <65% |
| APV | >85% (ideal >90%) | — | cut ~20% words | pivot |
| Comments | >1 / 100 views good | — | — | flatline + bad retention |

**Pivot (same infra):** Extreme planetary pressure / depth journeys (countdown descent structure).

**Checkpoints:** after Shorts **10** and **20** (and soft read after first 5).

---

## 9) 30-day decision memo (copy block)

```
NICHE PROMISE:
Visualizing the exact numerical limits where physical reality breaks down.

CONTENT FORMULA (~30s):
[0-3s]   Hard numeric/named threshold + high-contrast motion
[4-10s]  Intuitive paradox
[11-22s] One underlying law
[23-28s] Visual consequence
[29-30s] Optional seamless loop

WHAT TO POST:
• Top 12 slate in POSTING_SCHEDULE_B.md order
• Hard numbers in titles + opening sentence
• Deep blacks vs piercing glows

WHAT TO IGNORE:
• Faces, crowds, meme hyper-cuts, hyped shouting, soft intros

CONTINUE / KILL:
• Double down: Viewed >70% AND APV >85%
• Tweak hooks: Viewed <60% BUT APV >85%
• Tweak script: Viewed >70% BUT APV <75%
• Pivot: Viewed <55% AND APV <65% → Extreme Depth Descents
```

---

## 10) Channel A note

After Hours Japan stays **parked as primary monetization bet**. Finish A backlog only if desired; do not spend GPU chasing YPP on silent ambient while B is the growth test.
