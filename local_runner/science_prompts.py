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
    {
        "text": "Above the Eddington limit,\nradiation pressure tears a star apart.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked wide shot of a hyper-luminous blue giant star shedding "
            "outer gas layers in violent glowing radial plumes, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Light itself carries momentum.\nToo much outward push, and gravity loses grip on the atmosphere.",
        "rate": "+0%",
        "pause_ms": 300,
        "num_frames": 169,
        "shot": (
            "Cinematic locked medium shot of stellar atmosphere lifting off in luminous "
            "sheets against inward gravity, blue-white glare, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "That balance point is the maximum brightness\na star can sustain before it strips itself.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 153,
        "shot": (
            "Cinematic locked close-up of outer envelope ripping into glowing filaments "
            "streaming into space, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Cross it, and the star blows its own skin into the void.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 145,
        "shot": (
            "Cinematic locked ultra-wide linger: stripped luminous core with expanding "
            "shell of ejected gas, deep black surroundings, "
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
    ("sci_ep10_eddington", _beats_script(_EP10_BEATS), _beats_shots(_EP10_BEATS), _EP10_BEATS),
    ("sci_ep11_vacuum_decay", _beats_script(_EP11_BEATS), _beats_shots(_EP11_BEATS), _EP11_BEATS),
    ("sci_ep12_neutron_drip", _beats_script(_EP12_BEATS), _beats_shots(_EP12_BEATS), _EP12_BEATS),
]


def build_science_jobs(num_frames, steps):
    return [
        _science_job(vid, script, shots, num_frames, steps, script_beats=beats)
        for vid, script, shots, beats in _EPISODES
    ]


science_ltx_jobs = build_science_jobs(num_frames=129, steps=8)

# ep09 solar escape: keep LTX bed quiet under VO (ep08 lesson)
for _j in science_ltx_jobs:
    if _j.get("video_id") == "sci_ep09_solar_escape":
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
    "sci_ep10_eddington": "ltx",
    "sci_ep11_vacuum_decay": "ltx",
    "sci_ep12_neutron_drip": "ltx",
    # Parked Batch-0 (files may exist; not in active _EPISODES)
    "sci_ep01_sun_closer": "ltx",
    "sci_ep02_dyson_heat": "ltx",
    "sci_ep03_black_hole_outer": "ltx",
    "sci_ep04_atmosphere_freeze": "ltx",
    "sci_ep05_elevator_snap": "ltx",
}
