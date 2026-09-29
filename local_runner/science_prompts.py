"""
Threshold Physics (Channel B) — Top 12 limit episodes for LTX batches.

Strategy: ../THRESHOLD_PHYSICS_STRATEGY.md
Schedule: ../POSTING_SCHEDULE_B.md

Run: CHANNEL=b ENGINE=ltx VIDEO_ID=sci_ep01_sound_194db python run_test_batch.py
"""

import os

# Approved I2V first frames: i2v_stills/<video_id>/shot_N.png (auto-attached when present).
_I2V_STILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i2v_stills")

_SCI_SUFFIX = (
    "photo-realistic cinematic CGI, vertical 9:16, locked camera, "
    "no people, no faces, NO text, NO letters, NO logos, no watermarks"
)

_VO_DEFAULTS = {
    # Separate T2V clips → soft crossfades in stitch (see crossfade_s).
    # For one-pass linger: shot_mode="ltx_multishot", join_style="cut"|"continue".
    "shot_mode": "multi_cut",
    "join_style": "cut",  # ignored unless shot_mode is ltx_multishot
    "crossfade_s": 0.35,  # video xfade + audio acrossfade between beats
    "voice": "guy",
    "voice_rate": "+0%",  # fallback when a beat omits rate
    "voice_pitch": "-1Hz",
    "captions": "clean",
    # Keep LTX native AV under VO (was "space" synth — replaced clip audio).
    "ambient": "ltx",
    "ambient_volume": 0.55,
    # Hard hook: start VO near frame zero (strategy §2).
    "vo_delay_ms": 100,
    "voice_volume": 1.0,
}


def _science_job(video_id, script, shots, num_frames, steps, script_beats=None):
    job = {
        "video_id": video_id,
        "num_frames": num_frames,
        "steps": steps,
        "shots": list(shots),
        **_VO_DEFAULTS,
    }
    if script_beats:
        job["script_beats"] = list(script_beats)
        job["script"] = "\n\n".join(
            (b.get("text") or "").strip() for b in script_beats if (b.get("text") or "").strip()
        )
        # Prefer per-beat shot dicts when present (1 VO beat ↔ 1 visual).
        beat_shots = []
        for b in script_beats:
            shot_text = (b.get("shot") or b.get("prompt") or "").strip()
            if not shot_text:
                continue
            entry = {"prompt": shot_text}
            if b.get("num_frames") is not None:
                entry["num_frames"] = int(b["num_frames"])
            if b.get("steps") is not None:
                entry["steps"] = int(b["steps"])
            for key in ("start_image", "start_image_url"):
                if b.get(key):
                    entry[key] = b[key]
            beat_shots.append(entry)
        if beat_shots:
            job["shots"] = beat_shots
    else:
        job["script"] = (script or "").strip()
    for i, entry in enumerate(job["shots"]):
        if not isinstance(entry, dict) or entry.get("start_image") or entry.get("start_image_url"):
            continue
        still = os.path.join(_I2V_STILLS_DIR, video_id, f"shot_{i + 1}.png")
        if os.path.isfile(still):
            job["shots"][i] = {**entry, "start_image": still}
    return job


def _beats_script(beats):
    return "\n\n".join(b["text"] for b in beats)


def _beats_shots(beats):
    return [{"prompt": b["shot"], "num_frames": b["num_frames"]} for b in beats]


# =============================================================================
# TOP 12 — Physics Limits / Thresholds (primary posting queue)
# Formula: threshold → paradox → one law → visual climax (~55–65 words VO)
# num_frames on LTX 8k+1 grid (~24fps); stitch still pad/trims for TTS drift.
# =============================================================================

# --- Ep 01: 194 dB Sound Barrier ---

_EP01_BEATS = [
    {
        "text": "At the 194-decibel sound barrier,\nsound stops being sound and becomes a shockwave.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked extreme close-up of a razor-sharp circular compression "
            "shockwave ripping through a dense luminescent gas cloud into black void, "
            "violent compression ripples, high contrast particulate haze, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Air can only vibrate so hard.\nPast that limit, the wave carries more energy than the atmosphere can hold.",
        "rate": "+0%",
        "pause_ms": 300,
        "num_frames": 169,
        "shot": (
            "Cinematic locked medium shot of layered air density sheets buckling under a "
            "passing pressure wave, translucent shock rings expanding through fog, "
            "deep black background, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "So the medium itself fails—\nmolecules shoved aside instead of oscillating.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 145,
        "shot": (
            "Cinematic locked close-up of glowing gas molecules blasted into a hollow "
            "vacuum tunnel behind a luminous shock front, particles streaming sideways, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "The threshold isn't loudness.\nIt's when sound becomes pure destruction.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 153,
        "shot": (
            "Cinematic locked wide shot of a spherical shock shell expanding through a "
            "dark chamber of glowing gas, center voided to black, quiet catastrophic linger, "
            f"{_SCI_SUFFIX}"
        ),
    },
]

# --- Ep 02: Roche Limit ---

_EP02_BEATS = [
    {
        "text": "Cross the Roche limit,\nand planetary gravity shreds an entire moon.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked wide shot of a cracked grey lunar body fracturing into "
            "luminous debris beside a huge banded gas giant, tidal stress cracks glowing, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Too close, and the near side feels stronger pull than the far side.",
        "rate": "+0%",
        "pause_ms": 300,
        "num_frames": 145,
        "shot": (
            "Cinematic locked medium shot of a moon stretching egg-shaped toward a giant "
            "planet, near face brighter under tidal strain, cold blue rim light, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "That tidal difference\noverpowers the moon's own gravity.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 153,
        "shot": (
            "Cinematic locked medium shot of rocky crust peeling into arcs of debris "
            "streaming into a thin ring plane, sparks of colliding rubble, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Cross it, and a world becomes a ring.",
        "rate": "-15%",
        "pause_ms": 200,
        "num_frames": 129,
        "shot": (
            "Cinematic locked ultra-wide linger: gas giant with a bright newly formed "
            "ring system, last moon fragments dissolving into the plane, deep black void, "
            f"{_SCI_SUFFIX}"
        ),
    },
]

# --- Ep 03: Neutron Star Surface Impact ---

_EP03_BEATS = [
    {
        "text": "On a neutron star, drop a solid mass one meter—\nand it hits with nuclear force.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked extreme close-up of a dense metallic sphere falling toward "
            "a glowing blue crystalline neutron-star crust, extreme foreshortening, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Surface gravity near two hundred million g\nturns a tiny fall into a hypersonic impact.",
        "rate": "+0%",
        "pause_ms": 300,
        "num_frames": 169,
        "shot": (
            "Cinematic locked medium shot of a blinding white motion trail streaking downward "
            "toward an azure crust, faint blue aurora glow illuminating the descent, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Kinetic energy dumps into heat and gamma flash\nbefore the object even looks like itself.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 153,
        "shot": (
            "Cinematic locked close-up of a blinding white-hot circular shockwave detonating "
            "across a blue crystalline surface, violent flash of plasma erasing the center "
            "of the frame, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "The threshold isn't height.\nIt's gravity so extreme that one meter is a bomb.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 161,
        "shot": (
            "Cinematic locked wide linger: glowing white-hot impact scar on a neutron-star "
            "surface, expanding plasma halo fading into deep black space above the limb, "
            f"{_SCI_SUFFIX}"
        ),
    },
]

# --- Ep 04: Absolute Zero ---
# Retention fix: ~50 words, named 0 K hook, Beat 3 = hard visual scale reset.

_EP04_BEATS = [
    {
        "text": "At absolute zero—zero kelvin—\nall atomic motion completely vanishes.",
        "rate": "-8%",
        "pause_ms": 300,
        "num_frames": 145,
        "shot": (
            "Cinematic locked extreme macro close-up of a translucent faceted geometric "
            "crystal with pulsating interior light nodes jittering violently, white-gold "
            "sparks, dark void around, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Temperature is motion.\nHit that floor and kinetic energy reaches pure zero.",
        "rate": "+0%",
        "pause_ms": 250,
        "num_frames": 129,
        "shot": (
            "Cinematic locked medium shot of the same crystal, interior light nodes "
            "dimming and freezing into place, cold blue specular reflections, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "You can approach it—\nbut thermodynamics forbids a perfect stop.",
        "rate": "-4%",
        "pause_ms": 250,
        "num_frames": 129,
        "shot": (
            "Cinematic locked ultra-wide shot of an entire frozen alien planet under a "
            "dim distant star, nitrogen frost storms falling from a black sky onto icy "
            "continents, sudden scale jump from crystal to world, high contrast blue-white "
            "against void, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Absolute zero is the coldest possible state of matter.",
        "rate": "-12%",
        "pause_ms": 150,
        "num_frames": 113,
        "shot": (
            "Cinematic locked wide linger: perfectly still dark crystal silhouette in "
            "void, almost no motion, last faint blue edge glow dying out, "
            f"{_SCI_SUFFIX}"
        ),
    },
]

# --- Ep 05: Spaghettification Radius ---

_EP05_BEATS = [
    {
        # Retention: Roche-style one object transforming; stakes before jargon.
        # ~60 spoken words total — Shorts cap; clarity in mechanism beats.
        "text": "Spaghettification: too close to a black hole,\ngravity stretches matter into spaghetti.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked ultra-wide establishing shot of a small grey rocky asteroid "
            "with sharp cratered detail already stretching lengthwise toward a pitch-black "
            "compact core, white-gold tidal stress seams glowing along its long axis, "
            "immediate elongation motion from frame one, thin accretion dust starting to "
            "peel off the near face, deep pure black void, high contrast photoreal space CGI, "
            "vertical 9:16, locked camera, no people, no faces, NO text, NO letters, NO logos, "
            "no watermarks"
        ),
    },
    {
        "text": "The near side is pulled harder than the far side—\nso the body tears along that pull.",
        "rate": "+0%",
        "pause_ms": 280,
        "num_frames": 153,
        "shot": (
            "Cinematic locked medium shot of the SAME grey rocky asteroid pulled into a "
            "clear egg shape pointing at the dark core, near hemisphere brighter and "
            "fracturing under stronger tidal pull, far hemisphere dimmer and lagging, "
            "cool blue rim light on the crust, fine rock dust streaming from the near tip, "
            "readable solid silhouette (not melting goo), black void, photoreal cinematic CGI, "
            "vertical 9:16, locked camera, no people, no faces, NO text, NO letters, NO logos, "
            "no watermarks"
        ),
    },
    {
        "text": "That tidal gradient—not the darkness—\npulls the rock into thin glowing filaments.",
        "rate": "-4%",
        "pause_ms": 280,
        "num_frames": 169,
        "shot": (
            "Cinematic locked close-up of the SAME asteroid crust splitting into parallel "
            "luminous white-gold filaments like stretched taffy of rock and light, strands "
            "streaming into a thin curved accretion ribbon toward the black core, "
            "individual filament edges still visible (not blurry smoke), high contrast "
            "against pure black, photoreal cinematic CGI, vertical 9:16, locked camera, "
            "no people, no faces, NO text, NO letters, NO logos, no watermarks"
        ),
    },
    {
        "text": "The threshold is the tidal radius.\nThe strand is what remains.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 145,
        "shot": (
            "Cinematic locked ultra-wide linger: only a single bright luminous filament "
            "remains, falling slowly toward a pitch-black compact core, faint gravitational "
            "lensing on a sparse starfield at the rim, almost still, quiet catastrophic "
            "aftermath, photoreal cinematic CGI, vertical 9:16, locked camera, no people, "
            "no faces, NO text, NO letters, NO logos, no watermarks"
        ),
    },
]

# --- Ep 06: Absolute Hot / Planck Temperature ---
# 2026-09-22 v3: plain storytelling VO (no em dashes), multi_cut + SAME plasma
# sphere with cracked stellar-photosphere surface (Claude + Grok). Readable
# heat ramp white-gold → blue-white → violet-white; not soft blob / continue.

_EP06_BEATS = [
    {
        "text": "Imagine heating something, hotter and hotter,\n"
            "with no limit in sight.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked extreme close-up of the SAME churning plasma sphere, "
            "glowing white-gold ionized surface cracked into vivid orange-white fissures "
            "venting solar flares, sharp circular silhouette against pure black void, "
            "surface plates of light constantly shifting like a stellar photosphere, "
            "no lensing, no camera movement, photoreal cinematic CGI, vertical 9:16, locked camera, no people, no faces, NO text, NO letters, NO logos, no watermarks"
        ),
    },
    {
        "text": "But push far enough, and the heat gets so extreme\n"
            "it starts warping space itself.",
        "rate": "+0%",
        "pause_ms": 280,
        "num_frames": 153,
        "shot": (
            "Cinematic locked extreme close-up of the SAME plasma sphere, surface now "
            "blazing blue-white at the fissure edges while the core stays molten orange-gold, "
            "wider glowing cracks venting brighter plasma flares, sharp circular silhouette "
            "still fully intact against black void, faint heat-shimmer just barely bending "
            "the space directly behind it, no visible lensing arcs yet, photoreal cinematic CGI, vertical 9:16, locked camera, no people, no faces, NO text, NO letters, NO logos, no watermarks"
        ),
    },
    {
        "text": "Go further still, and temperature as an idea\n"
            "simply falls apart.",
        "rate": "-4%",
        "pause_ms": 280,
        "num_frames": 169,
        "shot": (
            "Cinematic locked extreme close-up of the SAME plasma sphere, surface now "
            "dominant blinding blue-white ionized plasma, fissures fused into rippling "
            "bright seams, faint gravitational lensing arcs bending the black void behind "
            "it, circular silhouette still the clear readable center of frame despite the "
            "bending light, plasma streamers licking off the edge, photoreal cinematic CGI, vertical 9:16, locked camera, no people, no faces, NO text, NO letters, NO logos, no watermarks"
        ),
    },
    {
        "text": "Scientists call that edge the Planck temperature, ten to the thirty two kelvin,\n"
            "the hottest anything can ever be.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 145,
        # 2026-09-23: I2V v1 drifted to oval/egg + soft swirling blob center ~0:25.
        # Lock rigid circular solid sphere every frame; lensing kept off the rim.
        "shot": (
            "Cinematic locked extreme close-up of the SAME solid plasma sphere, a rigid "
            "perfectly round filled opaque ball, final most extreme heat state, surface "
            "blazing violet-white and impossibly bright like a collapsing star, cracked "
            "stellar photosphere with glowing violet-white fissures and bright seams "
            "flickering across a solid surface, subtle plasma streamers at the rim, "
            "sharp crisp perfectly circular silhouette holding the exact same round shape "
            "and size in every frame from first to last, never stretching into an oval "
            "or egg, the center stays a solid bright surface never a soft swirl, hole, "
            "vortex or portal, faint gravitational lensing arcs only in the distant black "
            "void behind it never touching or distorting the sphere outline, "
            "photoreal cinematic CGI, vertical 9:16, locked camera, no people, no faces, NO text, NO letters, NO logos, no watermarks"
        ),
    },
]

# --- Ep 07: Chandrasekhar Limit ---
# 2026-09-23 v4: shot prompts rewritten as I2V MOTION prompts (were still-gen text).
# Rules learned from ep06: the worker has no negative-prompt field (run_test_batch
# _build_shot_payload), so every "NO vortex / NO portal / NO ring" token was fed to
# T5 as a positive concept -- that is what summoned the swirl/portal failures. Bans
# are now stated positively ("stays a solid opaque ball"). Identity, size and framing
# are carried by the approved start_image, not by words. Still prompts live in
# CHANDRASEKHAR_PROMPTS.md. VO: companion-star theft gives the story an agent.

_EP07_BEATS = [
    {
        "text": "This dead star is only the size of Earth,\n"
            "but it weighs almost as much as the Sun.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "A small dense white dwarf star hangs still in black space, its blue-white "
            "crust finely cracked, a thin ribbon of glowing gas trailing in from off "
            "frame and curling down onto its upper edge. Through the shot the ribbon "
            "drifts and slowly feeds into the surface, the glow at the limb swells very "
            "gently, and faint light ripples travel across the crust. The star holds as "
            "a solid opaque ball, perfectly round and the same size from first frame to "
            "last. Calm, heavy, patient. Locked camera, no camera movement, photoreal "
            "cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks"
        ),
    },
    {
        "text": "It is stealing gas from a neighbouring star,\n"
            "and every gram it steals crushes it tighter.",
        "rate": "+0%",
        "pause_ms": 280,
        "num_frames": 153,
        "shot": (
            "The same white dwarf fills the frame, its rigid blue-white crust broken "
            "into plates by sharp fracture lines. Through the shot a pale blue sheet of "
            "gas settles onto the upper left of the surface and spreads flat across the "
            "crust, the fracture lines slowly widen, and cool white light rises brighter "
            "through the cracks from the solid core beneath. The whole ball contracts a "
            "little and stays an opaque sphere with a hard round edge. Pressure "
            "building, nothing escaping. Locked camera, no camera movement, photoreal "
            "cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks"
        ),
    },
    {
        "text": "Inside, electrons hold the whole star up.\n"
            "Add too much weight and they give way, all at once.",
        "rate": "-4%",
        "pause_ms": 280,
        "num_frames": 169,
        "shot": (
            "The same white dwarf, smaller now and blazing, its cracked crust shearing "
            "apart along one side. Through the shot angular crust shards peel away and "
            "fall inward, striking the surface, while the whole sphere visibly shrinks "
            "and its light climbs to a hard blue-white blaze. Every piece moves toward "
            "the centre. The core stays a solid opaque ball, bright evenly across its "
            "whole face, its edge staying sharp as it contracts. Fast, violent, "
            "collapsing inward. Locked camera, no camera movement, photoreal cinematic "
            "CGI, vertical 9:16, no people, no text, no logos, no watermarks"
        ),
    },
    {
        "text": "That breaking point is the Chandrasekhar limit, 1.44 Suns.\n"
            "Cross it, and the star tears itself apart.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 145,
        "shot": (
            "A blinding blue-white core burns at the centre of a wide field of sharp "
            "crust fragments and torn filaments of pale blue gas. Through the shot the "
            "fragments and the gas drift slowly outward in every direction, the "
            "filaments stretch and thin as they travel, and the core flares once and "
            "then settles to a steady burn. The movement is slow and heavy, wreckage "
            "coasting through vacuum long after the blast. Quiet catastrophic aftermath. "
            "Locked camera, no camera movement, photoreal cinematic CGI, vertical 9:16, "
            "no people, no text, no logos, no watermarks"
        ),
    },
]

# --- Ep 08: Metallic Hydrogen ---
# 2026-09-25 v3 VO: Chandrasekhar-shaped arc (paradox -> law -> named limit+number
# -> stakes). Title keeps Exact-Pressure (400 GPa). Number lands late like ep07,
# not in the first spoken line. Motion prompts unchanged (stills LOCK v12i).
# Pack: METALLIC_HYDROGEN_PROMPTS.md

_EP08_BEATS = [
    {
        "text": "Hydrogen is the lightest gas there is,\n"
            "but crush it hard enough and it turns into liquid metal.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "A thick wall of pale grey hydrogen fog fills the upper two thirds of frame "
            "above a small pool of mirror-bright liquid silver at the bottom. Through the "
            "shot the fog is pressed straight down from above, its layers squeezing "
            "tighter and darker as they sink, and where the fog touches the pool it turns "
            "into shining liquid metal. The silver pool rises and spreads outward to both "
            "edges until it fills the lower half, its surface flat and level like "
            "mercury, reflecting the fog above. Fast, heavy, crushing downward. Locked "
            "camera, no camera movement, photoreal cinematic CGI, vertical 9:16, no "
            "people, no text, no logos, no watermarks"
        ),
    },
    {
        "text": "Force the atoms that close and their electrons break free.\n"
            "Those free electrons are why metal shines.",
        "rate": "+0%",
        "pause_ms": 300,
        "num_frames": 169,
        "shot": (
            "The SAME liquid silver sea fills the lower half of frame under a heavy "
            "charcoal storm deck with faint brown-grey bands, a sharp level horizon "
            "across the middle. Through the shot the last thin wisps of grey fog drift "
            "down onto the metal and melt into it, and the reflection in the sea sharpens "
            "until the storm clouds appear crisp and upside down in the silver, like a "
            "flawless mirror. The cloud bands above crawl slowly left to right and their "
            "reflection follows them exactly. The surface stays flat, level and perfectly "
            "still. Calm, eerie, heavy. Locked camera, no camera movement, photoreal "
            "cinematic CGI, vertical 9:16, no people, no text, no logos, no watermarks"
        ),
    },
    {
        "text": "That breaking point is four hundred gigapascals,\n"
            "four million times the air on your skin.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 145,
        "shot": (
            "Close on the SAME liquid silver sea, the mercury-bright surface filling the "
            "lower three quarters of frame, a strip of dark storm sky across the top. "
            "Through the shot thousands of tiny bright white glints stream across the "
            "metal from left to right like sparks flowing in a current, low ripples roll "
            "the same way, and the whole surface grows steadily brighter until it gleams "
            "like polished chrome. The metal stays one smooth opaque liquid sheet, flat "
            "and level, the glints riding on top of it. Fast, alive, electric. Locked "
            "camera, no camera movement, photoreal cinematic CGI, vertical 9:16, no "
            "people, no text, no logos, no watermarks"
        ),
    },
    {
        "text": "Cross it, and an invisible cloud becomes a chrome sea.\n"
            "Deep in Jupiter, that ocean is wider than Earth.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 153,
        "shot": (
            "Ultra-wide on the SAME liquid silver sea stretching to a gently curved "
            "horizon in the lower third of frame, a vast charcoal storm deck with "
            "brown-grey bands filling the sky above. Through the shot a single blue-white "
            "lightning bolt strikes the center of the sea, and the entire mirror surface "
            "flashes bright white all the way to the horizon, then fades back to silver. "
            "One flat circular ripple spreads slowly outward from the strike point across "
            "the metal. Cloud bands crawl slowly left to right. Enormous, quiet, final. "
            "Locked camera, no camera movement, photoreal cinematic CGI, vertical 9:16, "
            "no people, no text, no logos, no watermarks"
        ),
    },
]

# --- Ep 09: Solar Escape Velocity (swap) ---

_EP09_BEATS = [
    {
        # VO Pass lock — EP09_VO_BEATS.md (do not rewrite without VO QA)
        # VISUAL REWRITE 2026-09-26: subject is a PLASMA EMBER, not a spacecraft.
        # Prior vehicle-based passes failed: hard-surface identity + scale drifted
        # every shot and stacked negations ("engines OFF", "never") were ignored.
        # A luminous phenomenon has no rigid geometry to drift, so it holds.
        "text": "The Sun will not let you leave. Escaping its gravity from the surface takes six hundred seventeen point five kilometers a second.",
        # VO speaks the words; caption shows the numeral (strategy: numbers highlighted).
        "caption_text": "The Sun will not let you leave. Escaping its gravity from the surface takes 617.5 km/s.",
        "rate": "+0%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked wide shot of a colossal white-gold Sun photosphere limb filling the left "
            "and lower frame, granulation cells boiling, deep black space to the right; "
            "a single small brilliant white-hot ember of plasma lifts off the limb and drifts steadily "
            "outbound into the void, trailing a short soft glowing wake that fades within a body length, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "One push, then coasting — no engine, no matter your mass.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 161,
        "shot": (
            "Cinematic locked medium shot of the same small white-hot plasma ember coasting up a steep "
            "outbound arc through deep black space, its thin luminous gold trail thinning and cooling behind it; "
            "a dominant white-gold Sun limb with thick bright corona anchors the bottom of the frame, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Farther out, the pull weakens — from Earth's orbit, that number drops to forty two kilometers a second.",
        "caption_text": "Farther out, the pull weakens — from Earth's orbit, that number drops to 42 km/s.",
        "rate": "-8%",
        "pause_ms": 300,
        "num_frames": 145,
        "shot": (
            # 2026-09-26 shot-3 fix: "towering arches" made LTX build ONE frame-filling
            # symmetric arch that closed into a glowing oval (read as a portal, not corona),
            # blew out the exposure, and flipped the ember to horizontal travel.
            # Fix: corona pushed to a distant band at the bottom edge, black kept dominant,
            # ember held small on the same upward diagonal as shots 1-2.
            "Cinematic locked medium-wide shot of vast deep black space filling most of the frame, "
            "a curved white-gold Sun limb with a few small distant coronal loops resting low along the "
            "bottom edge of frame, the same small white-hot plasma ember racing outbound along a steep "
            "diagonal from lower-left toward upper-right, its compact pinpoint-bright core trailing a "
            "long thin luminous gold velocity streak stretched far behind it into the darkness, the "
            "streak sharp and elongated while the ember itself stays small and dense against the "
            "surrounding black, the Sun limb and its loops occupying only the lower edge of frame with "
            "open black space dominating everything above and around the ember's path, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Reach that speed, and the Sun shrinks behind you forever. Fall short, and it pulls you back.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 153,
        "shot": (
            "Cinematic locked ultra-wide linger on vast deep black void; the same plasma ember, now a small "
            "steady cool-white point of light, drifts free toward the upper right with almost no motion; "
            "the white-gold Sun and its flare recede and dim in the lower left, quiet heavy freedom, "
            f"{_SCI_SUFFIX}"
        ),
    },
]
_EP10_BEATS = [
    # Rebuilt 2026-09-28 against real analytics. THRESHOLD IS THE MASS CAP, not the
    # Eddington luminosity: L_Edd is a RATIO (scales with M), and every episode that
    # performed had a FIXED number (617.5 km/s, 716 Hz, 1.44 Mo, 8.87 mm). "300 suns"
    # is chosen over the often-quoted 150 because it is hardest to falsify — if the
    # true cap is lower, "nothing exceeds 300" is still true — and because R136a1
    # (~196 Mo, Kalari 2022, heaviest known) must sit BELOW the wall for beat 4's
    # open loop to work. "Suns" means MASS everywhere; no luminosity multiplier
    # appears in the VO, which avoids the per-solar-mass qualifier entirely.
    # THIS EPISODE CHANGES ONE VARIABLE vs ep14: THE ENDING. Everything else held.
    {
        "text": "There's a wall no star can grow past: three hundred suns of mass.",
        "caption_text": "There's a wall no star can grow past: 300 suns of mass.",
        "rate": "+0%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked medium shot of a massive young star blazing at its core, streams "
            "of infalling gas glowing brighter as they collide with the outward light and "
            "scatter into flares that surge and break across its surface, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "You'd think more falling gas makes a bigger star. Instead its own light shoves the gas away.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 169,
        "shot": (
            "Cinematic locked medium shot of a brilliant star filling the lower half of the "
            "frame and lighting the whole scene, dense filaments of glowing gas streaming "
            "inward toward it and curving sharply away as they near its surface, driven back "
            "outward in bright sweeping streams, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "A star's limit grows with mass, but brightness grows faster — the heaviest stars shove their extra gas away.",
        "rate": "-8%",
        "pause_ms": 300,
        "num_frames": 169,
        "shot": (
            "Cinematic locked wide shot of shafts of light streaming outward through drifting "
            "gas, sweeping loose streams of matter steadily away from a massive star that dims "
            "low at the edge of the frame, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        # Fable targeted luma 19 but described "a star's surface pulsing in bright
        # waves" — a surface filling frame renders BRIGHT, so cut 3->4 would have
        # JUMPED UP and killed the loop this episode exists to test. Rewritten so the
        # action ITSELF produces darkness: the star DIMS. Same trick as ep13 shot 4,
        # where "shrinking into the distance" gave calm motion and darkness together.
        "text": "Right now, the heaviest star ever found sits near two hundred suns — still short of the wall.",
        "caption_text": "Right now, the heaviest star ever found sits near 200 suns — still short of the wall.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 169,
        "shot": (
            "Cinematic locked wide shot of a lone massive star far off in deep black space, its "
            "glow steadily fading as thin streams of gas lift away from it and spread outward, "
            "the darkness deepening around it as it dims, "
            f"{_SCI_SUFFIX}"
        ),
    },
]

# --- Ep 11: Vacuum Decay ---

_EP11_BEATS = [
    {
        "text": "This is vacuum decay:\nif space drops into a lower energy state, physics resets instantly.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked wide shot of a perfectly smooth dark void bubble expanding "
            "across a field of stars, extinguishing them cleanly at the edge, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Our vacuum might be metastable—\na false floor above a deeper true vacuum.",
        "rate": "+0%",
        "pause_ms": 300,
        "num_frames": 153,
        "shot": (
            "Cinematic locked medium shot of a nucleation speck of absolute black "
            "appearing in glowing quantum foam, stars still visible beyond, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "A bubble of true vacuum expands at light speed,\nrewriting constants as it goes.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 161,
        "shot": (
            "Cinematic locked medium shot of the dark sphere growing, starlight cutting "
            "off at a razor-sharp boundary, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "The threshold isn't an explosion.\nIt's a new set of physical laws, advancing forever.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 161,
        "shot": (
            "Cinematic locked ultra-wide linger: mostly erased starfield, smooth true-"
            "vacuum darkness dominating the frame, quiet existential scale, "
            f"{_SCI_SUFFIX}"
        ),
    },
]

# --- Ep 12: Neutron Drip / Critical Density (swap) ---

_EP12_BEATS = [
    {
        "text": "Past the neutron-drip density—400 billion grams per centimeter—\natoms vanish.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 169,
        "shot": (
            "Cinematic locked extreme macro shot of an interlocking geometric crystalline "
            "cube imploding under crushing pressure, bright white stress fractures, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Electrons are forced into protons.\nNeutron drip begins—the structure dissolves.",
        "rate": "+0%",
        "pause_ms": 300,
        "num_frames": 153,
        "shot": (
            "Cinematic locked medium shot of a faceted crystal collapsing inward, "
            "material merging into denser blue-glowing nodes, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Normal atomic shells cannot survive that density.\nMatter becomes a neutron-rich slab.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 153,
        "shot": (
            "Cinematic locked close-up of the crystal flattening into a solid ultra-dense "
            "glowing blue slab, specular stress fractures, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "The threshold is critical density—\nwhere chemistry ends and nuclear matter begins.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 153,
        "shot": (
            "Cinematic locked wide linger: featureless dense blue slab in void, faint "
            "edge glow, almost no motion, "
            f"{_SCI_SUFFIX}"
        ),
    },
]


# --- Ep 13: Earth -> Black Hole (Schwarzschild radius) — SWAP, off original Top 12 ---
# Built 2026-09-26 against real channel analytics (see POSTING_SCHEDULE_B.md):
#   Two independent levers — Stayed% (first-2s hook; best ep07 69.2%) and AVD% (loop;
#   best ep09 107.1%). Nothing has had both. This targets both.
# Physics: r_s = 2GM/c^2. Earth (5.9722e24 kg) -> 8.870 mm RADIUS (horizon 17.74 mm
#   across — a marble, NOT a pea). Earth radius / r_s = 718,255,480. Human 70 kg
#   -> r_s = 1.04e-25 m, genuinely smaller than an atom (~1e-10 m).
# LTX staging: Earth appears in SHOT 1 ONLY. Shots 2-4 are phenomena, because a
#   recognizable solid object re-rendered across a cut is what destroyed three ep09
#   passes (a dart probe became a chrome rocket). Shot 2 is a plural SWARM, not a
#   sphere — a lone sphere tempts LTX to paint another Earth-like orb.
# num_frames run long on purpose: the stitch TRIMS to the VO beat (lossless) whereas
#   stretching adds slow-motion. ep09 needed 1.43x stretch; render long, trim down.
_EP13_BEATS = [
    {
        "text": "Crush Earth into a black hole, and it fits in eight point eight seven millimetres.",
        "caption_text": "Crush Earth into a black hole, and it fits in 8.87 mm.",
        "rate": "+0%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked wide shot of a perfectly round spherical blue and white planet "
            "filling most of the frame, thick white cloud bands churning and rolling visibly "
            "across its surface, bright silent lightning flashes pulsing inside the clouds along "
            "its dark night side, the planet turning steadily, deep black space at the edges, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        # "you" planted here so beat 4's pivot to the viewer reads as payoff, not detour.
        "text": "Nothing is removed. No mass is lost. Every atom you stand on is still there.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 161,
        "shot": (
            "Cinematic locked medium shot of a loose swarm of glowing rock fragments rushing "
            "inward toward a common centre, the gaps between them visibly closing as they fall "
            "together, bright amber fracture light flaring brighter as they compress, dust and "
            "sparks streaming inward behind them, deep black space surrounding on all sides, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Squeeze any mass inside its critical radius, and even light itself cannot climb back out.",
        "rate": "-8%",
        "pause_ms": 300,
        "num_frames": 161,
        "shot": (
            "Cinematic locked medium shot of a small brilliant white sphere low in the frame, thin "
            "arcs of distant starlight visibly bending and sliding around its edge into a bright "
            "thin ring that shimmers and shifts, faint distant stars drifting slowly past behind "
            "it, deep black space dominating the frame, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        # Dark, quiet, near-empty ending cutting back to shot 1's bright full-frame Earth:
        # this is the mechanic that produced ep09's 107.1% AVD.
        "text": "Every mass has this radius. Earth's is a marble. Yours is smaller than an atom.",
        "caption_text": "Every mass has this radius. Earth's is a marble. Yours is \u224810\u207b\u00b2\u2075 m.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 169,
        "shot": (
            "Cinematic locked shot of a small bright white sphere shrinking steadily into the "
            "distance at the centre of the frame, growing smaller and dimmer as it recedes, "
            "faint distant stars becoming visible around it as it fades, black space filling "
            "the frame, "
            f"{_SCI_SUFFIX}"
        ),
    },
]


# --- Ep 14: Fastest-spinning pulsar PSR J1748-2446ad (716 Hz) — analytics-driven ---
# Chosen because BOTH retention levers come free from the subject itself:
#   HOOK  — a strobing pulsar is in motion at frame zero (ep13's weakness is a calm
#           static Earth; the 25%-stayed worst-ever opened on something inert).
#   LOOP  — rotation is inherently loopable: the end state IS the start state.
# Physics (verified): 716 Hz spin = one rotation every 1.397 ms. Earth turns once per
#   24 h, so this is ~6.19e7x faster (~62 million). Neutron star ~20-32 km across.
#   Equatorial speed is RADIUS-DEPENDENT (15% c at 10 km, 18% at 12 km, 24% at 16 km)
#   and the radius is model-dependent — so the VO hedges "nears a fifth of light
#   speed" rather than asserting a false precision. 716 Hz is the exact figure.
# EVERY shot says "clockwise": four clips are generated independently and nothing
#   else enforces a shared rotation handedness. Without it the match-cut loop breaks
#   at the seam — which is the whole reason this episode was picked.
# Rates DESCEND +0 -> -12%: the quiet heavy close is what produced ep09's 107.1% AVD.
_EP14_BEATS = [
    {
        "text": "This star spins seven hundred sixteen times every second. Nothing solid should survive that.",
        "caption_text": "This star spins 716 times every second. Nothing solid should survive that.",
        "rate": "+0%",
        "pause_ms": 350,
        "num_frames": 145,
        "shot": (
            "Cinematic locked extreme close-up of a blinding white-hot neutron star low in the "
            "left of the frame, its surface roiling and convulsing as molten plasma arcs tear "
            "across it, a razor-thin beam of light whipping outward and sweeping clockwise across "
            "the upper frame in rapid strobing flashes, each pass leaving a sharp bright "
            "after-streak, deep black space filling the rest of the frame, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        # Earth stays in the VO only — a second recognizable solid object on screen
        # would reopen the identity-drift risk, and ep13 just used Earth.
        "text": "Earth turns once a day. This pulsar beats that sixty two million times over.",
        "caption_text": "Earth turns once a day. This pulsar beats that 62 million times over.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 169,
        "shot": (
            "Cinematic locked medium-wide shot of the white-hot neutron star filling the lower "
            "half of the frame, its surface churning and flaring as it turns, twin thick beams "
            "of light sweeping clockwise past the camera in fast continuous strobing pulses, "
            "each sweep washing bright light across the whole frame, black space above it, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Collapse conserves spin — a skater pulling in their arms spins faster — its edge nears a fifth of light speed.",
        "rate": "-8%",
        "pause_ms": 300,
        "num_frames": 169,
        "shot": (
            "Cinematic locked medium shot of the neutron star glowing deep orange-red low in the "
            "frame, thin bright streaks of light whipping clockwise past its edge one after "
            "another in a fast continuous strobe, the glow cooling and dimming as the streaks "
            "pass, deep black space surrounding it, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Only gravity holds it together — spin fast enough, and the star tears itself apart.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 169,
        "shot": (
            "Cinematic locked extreme wide shot of the neutron star reduced to a single small "
            "point of light low in the frame, its beam sweeping clockwise in a steady continuous "
            "strobe, the point pulsing rhythmically and dimming further with each pulse, deep "
            "black space filling the frame, "
            f"{_SCI_SUFFIX}"
        ),
    },
]


# --- Ep 15: Magnetar — first episode built on the REVISED hook rule ---
# Two levers, from 10 published episodes:
#   STAYED% <- opening style. Concrete image/object openings avg 57.5%; openings on
#     a number/unit/technical term avg 34.0%. Beat 1 names a wallet and the Moon —
#     zero technical units, nothing to learn first. The number lands at beat 3.
#   AVD% <- whether something HAPPENS. ep10 (nothing happens) scored 51.7% AVD and
#     was the worst cosmic result. Here atoms come apart at 1,000 km, and beat 4 is
#     a real recorded event with a consequence.
# Numbers pre-verified before drafting: field ~1e11 T; falls as 1/r^3; atoms distort
#   at ~1,000 km; wipes a magnetic stripe at ~215,000 km (Earth-Moon is 384,400 km,
#   so "halfway to the Moon" — NOT "farther than", an error I made and caught).
#   SGR 1806-20 giant flare, 27 Dec 2004, ionised Earth's upper atmosphere; distance
#   estimates 20,000-50,000 ly, hence "tens of thousands" rather than one figure.
# VISUALS ARE ALL COSMIC. The draft rendered a credit card in shots 1 and 4; cosmic
#   subjects average 660 views vs 15 for non-cosmic, and a card carries text/numbers
#   that LTX would render despite the no-text suffix (it ignores negations).
_EP15_BEATS = [
    {
        "text": "This star could wipe the card in your wallet from halfway to the Moon.",
        "rate": "+0%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked medium shot of a compact neutron star burning violet and white "
            "low in the frame, tight jets of plasma tearing off it and whipping outward into "
            "the surrounding darkness, its surface churning and pulsing, deep dark space "
            "across the upper frame, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "It's a magnetar — a dead star with the strongest magnetic field in the universe.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 169,
        "shot": (
            "Cinematic locked medium shot of the same blazing star sitting lower in the frame, "
            "thick violet plasma threads erupting and twisting outward from it, streaming past "
            "the camera and fading into the dark, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "That field fades fast with distance. Within a thousand kilometres, it warps the atoms in your body apart.",
        "caption_text": "That field fades fast with distance. Within 1,000 kilometres, it warps the atoms in your body apart.",
        "rate": "-8%",
        "pause_ms": 300,
        "num_frames": 169,
        "shot": (
            "Cinematic locked wide shot of streaks of electric blue light sweeping outward from a "
            "bright star low in the frame, passing through the frame and fading, faint matter "
            "visibly stretching and pulling apart along each streak, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        # Draft ended on "only thirty of these are known" — an inventory fact, and it
        # restated the hook. Replaced with the recorded 2004 event: a consequence,
        # which is what AVD responds to.
        "text": "In two thousand four, one flared — and lit our atmosphere from tens of thousands of light years away.",
        "caption_text": "In 2004, one flared — and lit our atmosphere from tens of thousands of light years away.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 169,
        "shot": (
            "Cinematic locked ultra-wide shot of a single bright flare front expanding outward "
            "across deep black space, spreading and thinning as it travels, dimming steadily as "
            "it disperses, "
            f"{_SCI_SUFFIX}"
        ),
    },
]


# --- Ep 08N: Neutron Star (20 km) ---
# 2026-09-29: "Part 2" of ep07 (same star still). Title:
#   The Exact Size a Collapsed Star Crushes Down To (20 km)
# I2V first frames: i2v_stills/sci_ep08_neutron_star/shot_1..4.png (shot_4 == shot_1
# == end_frame.png so the last frame loops back to the hook). end_frame.png is NOT
# wired: the worker has no end-keyframe input. Negatives are also NOT wired: the
# worker has no negative-prompt field (see ep07 note), so they are kept here only
# for reference and must not be pasted into the positive prompts:
#   all shots: portal, ring, hollow center, halo, lens flare, jets, beams, explosion,
#              expanding, breaking apart, motion blur, text, second star
#   shot 2 +:  spoon melting, spoon bending, liquid spilling, steam, fire
# Beat windows 0-5s / 5-12s / 12-22s / 22-30s -> num_frames on the 8k+1 grid @24fps.
# v2 (2026-09-29, no GPU): shots 1 and 4 replaced by locally animated clips
# (temp_clips/sci_ep08_neutron_star_shot_{1,4}_local.mp4, LTX grew the star); new
# beat-1 hook + beat-4 loop line; "SIZE OF A CITY" overlay burned on shot 1 at
# assembly. Output: final_videos/sci_ep08_neutron_star_complete_v2.mp4.

_EP08N_BEATS = [
    {
        # v2: TTS speaks one line (a "\n" in "text" makes Edge-TTS pause ~0.9s and
        # pushes the line past shot 1); the caption keeps the two-line break.
        "text": "This star is the size of a city, and it's heavier than the Sun.",
        "caption_text": "This star is the size of a city,\n"
            "and it's heavier than the Sun.",
        "rate": "+0%",
        # v2: pause sized so vo_delay + VO + pause = 4.65s -> shot 1 stays 5.0s
        # (4.65 + 0.35 crossfade) and the line finishes inside shot 1.
        "pause_ms": 182,
        "num_frames": 121,
        "shot": (
            "A small, dense blue-white star with a cracked glowing surface hovers low over "
            "a dark city with warm orange lights, seen from directly above. Its edge stays "
            "sharp and solid. The cracks pulse slowly with light, and the city lights below "
            "flicker faintly. Camera locked, very slow push in."
        ),
    },
    {
        "text": "A single teaspoon of it would weigh more\n"
            "than every human on Earth combined.",
        "rate": "+0%",
        "pause_ms": 280,
        "num_frames": 169,
        "shot": (
            "A metal teaspoon rests still on a black background, its bowl filled with "
            "glowing blue-white star material with a cracked surface. Bright seams of light "
            "pulse slowly across the material. The spoon does not move or bend. Camera "
            "locked, very slow push in."
        ),
    },
    {
        "text": "The squeeze crushes every atom until it turns into neutrons,\n"
            "packed tighter than anything except a black hole.",
        "rate": "-4%",
        # v3: pause 0 and the ~0.9s Edge-TTS trailing silence trimmed from this beat's
        # wav at assembly (cut at 6.68s), so beat 4 follows after ~0.28s, not ~1.5s.
        "pause_ms": 0,
        "num_frames": 241,
        "shot": (
            "A small blue-white star with a cracked surface sits alone on a black "
            "background. It tightens slightly and grows brighter, and its surface cracks "
            "close up as it is squeezed from all sides. Its outline stays a sharp, solid "
            "circle. Camera locked."
        ),
    },
    {
        "text": "Some of them spin hundreds of times every second.\n"
            "So what's left when a star dies?\n"
            "This star is the size of a city...",
        "rate": "-8%",
        "pause_ms": 200,
        "num_frames": 193,
        "shot": (
            "A small blue-white star with a cracked glowing surface hovers over a dark city "
            "with warm orange lights, seen from directly above. The cracked surface turns "
            "slowly and steadily, and a faint pulse of light repeats. The star stays in the "
            "same position with a sharp, solid outline. Camera locked, no zoom."
        ),
    },
]


# Primary queue (Top 12)
_EPISODES = [
    ("sci_ep01_sound_194db", _beats_script(_EP01_BEATS), _beats_shots(_EP01_BEATS), _EP01_BEATS),
    ("sci_ep02_roche_limit", _beats_script(_EP02_BEATS), _beats_shots(_EP02_BEATS), _EP02_BEATS),
    ("sci_ep03_neutron_impact", _beats_script(_EP03_BEATS), _beats_shots(_EP03_BEATS), _EP03_BEATS),
    ("sci_ep04_absolute_zero", _beats_script(_EP04_BEATS), _beats_shots(_EP04_BEATS), _EP04_BEATS),
    ("sci_ep05_spaghettification", _beats_script(_EP05_BEATS), _beats_shots(_EP05_BEATS), _EP05_BEATS),
    ("sci_ep06_absolute_hot", _beats_script(_EP06_BEATS), _beats_shots(_EP06_BEATS), _EP06_BEATS),
    ("sci_ep07_chandrasekhar", _beats_script(_EP07_BEATS), _beats_shots(_EP07_BEATS), _EP07_BEATS),
    ("sci_ep08_metallic_hydrogen", _beats_script(_EP08_BEATS), _beats_shots(_EP08_BEATS), _EP08_BEATS),
    ("sci_ep09_solar_escape", _beats_script(_EP09_BEATS), _beats_shots(_EP09_BEATS), _EP09_BEATS),
    # SWAP 2026-09-26: Earth->black hole jumps ahead of Eddington (analytics-driven).
    # Eddington is NOT dropped — it keeps its place in the queue below.
    ("sci_ep13_earth_black_hole", _beats_script(_EP13_BEATS), _beats_shots(_EP13_BEATS), _EP13_BEATS),
    ("sci_ep14_pulsar_716hz", _beats_script(_EP14_BEATS), _beats_shots(_EP14_BEATS), _EP14_BEATS),
    ("sci_ep15_magnetar", _beats_script(_EP15_BEATS), _beats_shots(_EP15_BEATS), _EP15_BEATS),
    ("sci_ep10_eddington", _beats_script(_EP10_BEATS), _beats_shots(_EP10_BEATS), _EP10_BEATS),
    ("sci_ep11_vacuum_decay", _beats_script(_EP11_BEATS), _beats_shots(_EP11_BEATS), _EP11_BEATS),
    ("sci_ep12_neutron_drip", _beats_script(_EP12_BEATS), _beats_shots(_EP12_BEATS), _EP12_BEATS),
    ("sci_ep08_neutron_star", _beats_script(_EP08N_BEATS), _beats_shots(_EP08N_BEATS), _EP08N_BEATS),
]


def build_science_jobs(num_frames, steps):
    return [
        _science_job(vid, script, shots, num_frames, steps, script_beats=beats)
        for vid, script, shots, beats in _EPISODES
    ]


science_ltx_jobs = build_science_jobs(num_frames=129, steps=8)

# ep09 solar escape: keep LTX bed quiet under VO (ep08 lesson)
for _j in science_ltx_jobs:
    if _j.get("video_id") in ("sci_ep09_solar_escape", "sci_ep08_neutron_star"):
        _j["ambient_volume"] = 0.10

# ep14: first episode on word-pop captions (strategy §2 "1-3 words/pop, numbers
# highlighted"). Opt-in so ep01-ep13 keep the existing full-sentence "clean" style.
for _j in science_ltx_jobs:
    if _j.get("video_id") == "sci_ep15_magnetar":
        # Subject sits low in frame in all 4 shots (the prompts say so, to stop
        # blow-out), so bottom captions land on top of it. Anchor to the top instead.
        _j["captions"] = "clean_high"
        _j["ambient_volume"] = 0.10
    if _j.get("video_id") in ("sci_ep14_pulsar_716hz", "sci_ep10_eddington"):
        # Word-pop reverted 2026-09-28. ep09 (full-sentence "clean") holds the best
        # AVD on the channel at 107%; ep14, the only episode to ship word-pop, came
        # in at 92.1%. Confounded, but not encouraging — and the style reads as
        # confusing on playback. Keep caption_text so numerals still render as
        # "8.87 mm" instead of spelled out; only the chunking is dropped.
        _j["captions"] = "clean"
        # ep09 (107% AVD, best on channel) runs the LTX bed at 0.10; ep13 (53% AVD)
        # inherited the 0.55 default — 5.5x louder. A loud bed competes with the VO
        # and stops the tail reading as a quiet linger. Match the winner.
        _j["ambient_volume"] = 0.10

# Preferred ENGINE per episode (LTX only for Top 12)
SCIENCE_ENGINE_BY_ID = {
    "sci_ep01_sound_194db": "ltx",
    "sci_ep02_roche_limit": "ltx",
    "sci_ep03_neutron_impact": "ltx",
    "sci_ep04_absolute_zero": "ltx",
    "sci_ep05_spaghettification": "ltx",
    "sci_ep06_absolute_hot": "ltx",
    "sci_ep07_chandrasekhar": "ltx",
    "sci_ep08_metallic_hydrogen": "ltx",
    "sci_ep09_solar_escape": "ltx",
    "sci_ep13_earth_black_hole": "ltx",
    "sci_ep14_pulsar_716hz": "ltx",
    "sci_ep15_magnetar": "ltx",
    "sci_ep10_eddington": "ltx",
    "sci_ep11_vacuum_decay": "ltx",
    "sci_ep12_neutron_drip": "ltx",
    "sci_ep08_neutron_star": "ltx",
    # Parked Batch-0 (files may exist; not in active _EPISODES)
    "sci_ep01_sun_closer": "ltx",
    "sci_ep02_dyson_heat": "ltx",
    "sci_ep03_black_hole_outer": "ltx",
    "sci_ep04_atmosphere_freeze": "ltx",
    "sci_ep05_elevator_snap": "ltx",
}
