"""
Threshold Physics (Channel B) — Top 12 limit episodes for LTX batches.

Strategy: ../THRESHOLD_PHYSICS_STRATEGY.md
Schedule: ../POSTING_SCHEDULE_B.md

Run: CHANNEL=b ENGINE=ltx VIDEO_ID=sci_ep01_sound_194db python run_test_batch.py
"""

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
            beat_shots.append(entry)
        if beat_shots:
            job["shots"] = beat_shots
    else:
        job["script"] = (script or "").strip()
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

_EP04_BEATS = [
    {
        "text": "Cool matter to absolute zero,\nand all motion completely vanishes.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked extreme macro close-up of a translucent faceted geometric "
            "crystal with pulsating interior light nodes jittering violently, white-gold "
            "sparks, dark void around, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Temperature is motion.\nZero kelvin is the floor where kinetic energy hits pure zero.",
        "rate": "+0%",
        "pause_ms": 300,
        "num_frames": 169,
        "shot": (
            "Cinematic locked medium shot of a translucent faceted geometric crystal, "
            "interior light nodes dimming and freezing into place, cold blue specular "
            "reflections, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "You can approach it—\nbut thermodynamics forbids ever reaching a perfect stop.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 153,
        "shot": (
            "Cinematic locked close-up of the crystal almost frozen, last faint interior "
            "glimmers dying out, frost-like light fading to dim blue, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "The threshold is the coldest possible state of matter.",
        "rate": "-15%",
        "pause_ms": 200,
        "num_frames": 129,
        "shot": (
            "Cinematic locked wide linger: perfectly still dark crystal structure in "
            "void, almost no motion, high contrast silhouette, "
            f"{_SCI_SUFFIX}"
        ),
    },
]

# --- Ep 05: Spaghettification Radius ---

_EP05_BEATS = [
    {
        "text": "Cross the spaghettification radius,\nand gravity stretches matter into strings.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked wide shot of a glowing celestial sphere violently stretching "
            "into a thin luminous thread toward a pitch-black center, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Near a compact mass, your feet feel stronger pull than your head.",
        "rate": "+0%",
        "pause_ms": 300,
        "num_frames": 145,
        "shot": (
            "Cinematic locked medium shot of a metallic test sphere elongating into an "
            "oval under tidal shear, cool blue highlights, black void, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "That gradient—not the darkness—\nrenders objects into one-dimensional filaments.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 161,
        "shot": (
            "Cinematic locked close-up of matter pulling into glowing atom-thin strands "
            "streaming into an accretion ribbon, white-gold against black, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "The threshold is tidal force.\nThe strand is what remains.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 145,
        "shot": (
            "Cinematic locked ultra-wide linger: single luminous filament falling toward "
            "a dark compact core, sparse starfield lensed at the edge, "
            f"{_SCI_SUFFIX}"
        ),
    },
]

# --- Ep 06: Absolute Hot / Planck Temperature ---

_EP06_BEATS = [
    {
        "text": "Past the Planck temperature—141 nonillion degrees—\nphysics collapses.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 169,
        "shot": (
            "Cinematic locked extreme close-up of a piercing white-hot core vibrating "
            "violently, blinding glare, edges fraying into black rupture, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "At the Planck temperature, heat isn't just energy—\nit curves spacetime itself.",
        "rate": "+0%",
        "pause_ms": 300,
        "num_frames": 161,
        "shot": (
            "Cinematic locked medium shot of a blinding white sphere warping and "
            "distorting background cosmic light and distant star rays, gravitational "
            "lensing shimmer, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Radiation densifies until gravity wins\nand the concept of temperature breaks.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 153,
        "shot": (
            "Cinematic locked close-up of the white core imploding into a pitch-black "
            "dimensional rupture, light folding inward, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "The threshold is absolute hot—\nthe ceiling where known physics ends.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 145,
        "shot": (
            "Cinematic locked wide linger: black rupture scar in void with fading white "
            "embers, almost still, catastrophic quiet, "
            f"{_SCI_SUFFIX}"
        ),
    },
]

# --- Ep 07: Chandrasekhar Limit ---

_EP07_BEATS = [
    {
        "text": "At the Chandrasekhar limit—1.44 solar masses—\na white dwarf cannot hold itself up.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked wide shot of a glowing white dwarf star, dense white-blue "
            "disc in deep black void, subtle surface shimmer, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Electron degeneracy pressure fights gravity—\nuntil that mass threshold is crossed.",
        "rate": "+0%",
        "pause_ms": 300,
        "num_frames": 169,
        "shot": (
            "Cinematic locked medium shot of a glowing white dwarf star rapidly "
            "shrinking under severe gravitational strain, surface fracturing with "
            "intense internal light, brighter core, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Electrons can no longer support the star.\nCollapse runs away.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 145,
        "shot": (
            "Cinematic locked close-up of the star imploding into a blinding point then "
            "blasting outward as an expanding supernova shockwave shell, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "The threshold is exact.\nOne mass line separates dwarf from detonation.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 153,
        "shot": (
            "Cinematic locked ultra-wide linger: expanding supernova remnant ring, "
            "white-gold shock against void, quiet aftermath scale, "
            f"{_SCI_SUFFIX}"
        ),
    },
]

# --- Ep 08: Metallic Hydrogen ---

_EP08_BEATS = [
    {
        "text": "This is the metallic hydrogen threshold:\ncompress gas to 4 million atmospheres, and it turns into metal.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked descending POV through pitch-black Jovian storm clouds "
            "toward a turbulent mirror-reflective liquid silver surface, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Deep inside a gas giant, pressure forces molecules so close\nelectrons delocalize.",
        "rate": "+0%",
        "pause_ms": 300,
        "num_frames": 169,
        "shot": (
            "Cinematic locked medium shot of translucent hydrogen gas layers crushing "
            "downward into denser glowing bands, amber to silver transition, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Gas becomes a liquid metallic sea—\nconductive, reflective, alien.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 145,
        "shot": (
            "Cinematic locked close-up of a churning liquid metal ocean surface, "
            "mirror reflections of storm light, mercury-like ripples, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "The threshold is 400 gigapascals.\nPast it, hydrogen stops being a gas.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 153,
        "shot": (
            "Cinematic locked wide linger: vast metallic hydrogen sea under dark cloud "
            "deck, silver horizon curve, deep pressure gloom, "
            f"{_SCI_SUFFIX}"
        ),
    },
]

# --- Ep 09: Solar Escape Velocity (swap) ---

_EP09_BEATS = [
    {
        "text": "Below solar escape velocity—617 kilometers a second—\nthe Sun traps you.",
        "rate": "-8%",
        "pause_ms": 350,
        "num_frames": 161,
        "shot": (
            "Cinematic locked wide shot of a small metallic probe accelerating away from "
            "a massive solar flare arc into deep space, white-gold sun limb dominating, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Escape velocity is the speed to climb out of a gravity well\nwithout further thrust.",
        "rate": "+0%",
        "pause_ms": 300,
        "num_frames": 161,
        "shot": (
            "Cinematic locked medium shot of curved gravitational path lines around the "
            "Sun, probe on a steep outbound trajectory, corona flicker, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "From the solar surface, that number is about 617.5 kilometers a second.",
        "rate": "-4%",
        "pause_ms": 300,
        "num_frames": 145,
        "shot": (
            "Cinematic locked close-up of the probe punching through bright coronal "
            "loops, heat shimmer, velocity streak, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Below the limit, gravity wins.\nAbove it, you leave the star's grip.",
        "rate": "-12%",
        "pause_ms": 200,
        "num_frames": 153,
        "shot": (
            "Cinematic locked ultra-wide linger: tiny probe clear of the Sun, flare "
            "receding, deep black void ahead, "
            f"{_SCI_SUFFIX}"
        ),
    },
]

# --- Ep 10: Eddington Luminosity ---

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
