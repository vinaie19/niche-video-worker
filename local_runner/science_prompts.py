"""
Threshold Physics (Channel B) — episode jobs for LTX-2.5 batches.

Run: CHANNEL=b ENGINE=ltx VIDEO_ID=sci_ep01_sun_closer python run_test_batch.py
"""

_SCI_SUFFIX = (
    "photo-realistic cinematic CGI, vertical 9:16, locked camera, "
    "no people, no faces, NO text, NO letters, NO logos, no watermarks"
)

_VO_DEFAULTS = {
    # Separate T2V clips → hard visual cuts (one-pass ltx_multishot morphs between scenes).
    # For soft linger takes: shot_mode="ltx_multishot", join_style="cut"|"continue".
    "shot_mode": "multi_cut",
    "join_style": "cut",  # ignored unless shot_mode is ltx_multishot
    "voice": "guy",
    "voice_rate": "+0%",  # fallback when a beat omits rate
    "voice_pitch": "-1Hz",
    "captions": "clean",
    # Continuous bed under VO (per-clip LTX audio jumps on stitch).
    # Use ambient="ltx" only if you want native beds and accept cut jumps.
    "ambient": "space",
    "ambient_volume": 0.4,
    "vo_delay_ms": 500,
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


# --- Episode 1: Sun 10% closer ---
# 1 VO beat ↔ 1 literal shot. num_frames on LTX 8k+1 grid (~24fps).
# Sized from measured Edge-TTS beat+pause (+vo_delay on shot1) so cuts match captions.
# Stitch also pad/trims if TTS drift remains.

_EP01_BEATS = [
    {
        "text": "What if the Sun moved ten percent closer tomorrow—\nwhich limit fails first?",
        "rate": "-12%",
        "pause_ms": 450,
        "num_frames": 193,  # ~8.0s: vo_delay+beat1+pause
        "shot": (
            "An ultra-wide locked vertical shot reveals the full Sun as a small bright "
            "white-gold disc centered in deep black void, thin corona flickering once, "
            "vast empty space around the whole star so scale is readable, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Not melting rock.\nNot the oceans boiling overnight.",
        "rate": "+0%",
        "pause_ms": 350,
        "num_frames": 129,  # ~5.4s: beat2+pause
        "shot": (
            "A wide locked vertical orbital shot of Earth's blue ocean dayside, thick "
            "white steam plumes and boiling vapor columns rising from the sea surface "
            "into a glowing amber sky, heat haze over the water, planet limb visible, "
            "no people, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "First: Earth's energy budget.\nTen percent closer means roughly twenty-one percent more sunlight.",
        "rate": "+5%",
        "pause_ms": 300,
        "num_frames": 169,  # ~7.0s: beat3+pause
        "shot": (
            "A wide locked vertical shot shows both bodies: an oversized brighter Sun "
            "as a white-gold disc in the upper third and a smaller blue Earth below, "
            "harsh excess sunlight washing the dayside into burned amber glare, "
            "clear orbital scale, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "Then satellites start dying in denser air.",
        "rate": "-4%",
        "pause_ms": 500,
        "num_frames": 97,  # ~4.0s: beat4+pause
        "shot": (
            "A locked vertical medium shot of a metallic CubeSat with rectangular solar "
            "panels filling the center of frame, tumbling and sparking as it drags through "
            "a thicker glowing orange atmosphere shell, Earth curve soft in the background, "
            "satellite clearly readable as a spacecraft, "
            f"{_SCI_SUFFIX}"
        ),
    },
    {
        "text": "The Sun doesn't need to touch us.\nIt only needs to cross a threshold.",
        "rate": "-15%",
        "pause_ms": 150,
        "num_frames": 161,  # ~6.7s: beat5+pause
        "shot": (
            "An ultra-wide locked vertical linger: a huge closer Sun dominates the upper "
            "half as a blinding white-gold disc, tiny Earth near the bottom edge for scale, "
            "deep black void, almost no motion, quiet catastrophic composition, "
            f"{_SCI_SUFFIX}"
        ),
    },
]

_EP01_SCRIPT = "\n\n".join(b["text"] for b in _EP01_BEATS)
_EP01_SHOTS = [
    {"prompt": b["shot"], "num_frames": b["num_frames"]} for b in _EP01_BEATS
]

# --- Episode 2: Dyson heat dump ---

_EP02_SCRIPT = """
A Dyson swarm doesn't break because it blocks sunlight.
It breaks on waste heat.

Every watt you use becomes heat you must dump.
At stellar scale, that means enormous infrared radiators—
not a solid shell, but countless collectors bleeding energy into space.

If the swarm can't radiate fast enough,
the structure cooks itself long before the star goes dark.

The limit isn't power.
It's thermodynamics at cosmic scale.
""".strip()

_EP02_SHOTS = [
    f"Cinematic locked extreme close-up of a solar collector panel vibrating under intense sunlight, molten heat shimmer, deep black starfield, {_SCI_SUFFIX}",
    f"Cinematic locked wide shot of countless thin solar collectors orbiting a bright star in a sparse swarm, glinting metal geometry, {_SCI_SUFFIX}",
    f"Cinematic locked medium shot of massive infrared radiator fins glowing dull red against the void, heat waves rippling, {_SCI_SUFFIX}",
    f"Cinematic locked wide shot of crimson heat plumes venting from radiator arrays into deep space, {_SCI_SUFFIX}",
    f"Cinematic locked medium shot of a warped collector structure overheating, metal stress shimmer, {_SCI_SUFFIX}",
    f"Cinematic locked ultra-wide shot of star plus swarm with glowing red waste-heat halo dominating the frame, linger on scale, {_SCI_SUFFIX}",
]

# --- Episode 3: Black hole outer solar system ---

_EP03_SCRIPT = """
What if a stellar-mass black hole drifted into the outer solar system—
which orbital limit breaks first?

Not Earth swallowed in a day.
Gravity works at distance.

First: comets and ice giants get their orbits rewritten.
Resonances stack until paths cross.

Then: the Oort cloud becomes a storm of inbound trajectories—
a slow, statistical siege, not a cinematic plunge.

The threshold is orbital chaos long before the event horizon touches us.
""".strip()

_EP03_SHOTS = [
    f"Cinematic locked extreme close-up of accretion disk edge glowing white-blue, violent swirling plasma, deep black void, {_SCI_SUFFIX}",
    f"Cinematic locked wide shot of outer solar system with faint ice giant and distant starfield, cold blue lighting, {_SCI_SUFFIX}",
    f"Cinematic locked medium shot of comet trails bending toward an invisible gravity well, curved trajectories, {_SCI_SUFFIX}",
    f"Cinematic locked wide shot of scattered comet paths crossing like tangled threads around a dark central point, {_SCI_SUFFIX}",
    f"Cinematic locked medium shot of ice giant atmosphere rippling under tidal stress, aurora-like glow, {_SCI_SUFFIX}",
    f"Cinematic locked ultra-wide shot of tiny black hole silhouette with lensed starfield and chaotic comet streaks, {_SCI_SUFFIX}",
]

# --- Episode 4: Atmosphere freeze ---

_EP04_SCRIPT = """
How cold can a planet get before the atmosphere itself starts to fail?

Not instant vacuum.
Phase change.

As temperature drops, gases begin to condense and freeze out of the sky—
first the trace gases, then the bulk atmosphere rains down as snow and frost.

The threshold is when air stops behaving like a permanent ocean
and becomes a seasonal surface deposit.

Cold enough, the sky falls.
""".strip()

_EP04_SHOTS = [
    f"Cinematic locked extreme close-up of frost crystals forming on rock in thin alien air, sharp micro motion, {_SCI_SUFFIX}",
    f"Cinematic locked wide shot of a grey alien planet under dim distant starlight, thin atmosphere haze, {_SCI_SUFFIX}",
    f"Cinematic locked medium shot of nitrogen fog condensing and falling like snow from a dark sky, particle drift, {_SCI_SUFFIX}",
    f"Cinematic locked close-up of atmospheric gases freezing into layered ice on a cliff face, crackling texture, {_SCI_SUFFIX}",
    f"Cinematic locked wide shot of a planet with pale frozen atmosphere pools on the surface, empty sky, {_SCI_SUFFIX}",
    f"Cinematic locked ultra-wide shot of a cold world with star and frozen atmospheric shell glinting, minimal motion linger, {_SCI_SUFFIX}",
]

# --- Episode 5: Space elevator snap ---

_EP05_SCRIPT = """
Where does a space elevator snap first—
not at the top, but at the tension limit.

The cable isn't one material.
It's a line under its own weight plus payload, plus weather, plus Coriolis drag.

The threshold is where stress exceeds strength along the longest span—
often lower atmosphere, not orbit.

The failure isn't drama.
It's a material limit crossing, then a whip the ground can't survive.
""".strip()

_EP05_SHOTS = [
    f"Cinematic locked extreme close-up of carbon-fiber tether strands vibrating under tension, specular highlights, sky background, {_SCI_SUFFIX}",
    f"Cinematic locked wide shot of a single impossibly thin cable rising from equatorial platform into cloud deck, {_SCI_SUFFIX}",
    f"Cinematic locked medium shot of cable bowing under wind shear in lower atmosphere, stress shimmer, {_SCI_SUFFIX}",
    f"Cinematic locked close-up of fraying tether fibers at a stress node, sparks of fiber snap, {_SCI_SUFFIX}",
    f"Cinematic locked wide shot of cable whipping after snap, motion blur against ocean and clouds, no people, {_SCI_SUFFIX}",
    f"Cinematic locked ultra-wide shot of broken elevator cable arc falling toward horizon, equatorial dawn light, {_SCI_SUFFIX}",
]

_EPISODES = [
    ("sci_ep01_sun_closer", _EP01_SCRIPT, _EP01_SHOTS, _EP01_BEATS),
    ("sci_ep02_dyson_heat", _EP02_SCRIPT, _EP02_SHOTS, None),
    ("sci_ep03_black_hole_outer", _EP03_SCRIPT, _EP03_SHOTS, None),
    ("sci_ep04_atmosphere_freeze", _EP04_SCRIPT, _EP04_SHOTS, None),
    ("sci_ep05_elevator_snap", _EP05_SCRIPT, _EP05_SHOTS, None),
]


def build_science_jobs(num_frames, steps):
    return [
        _science_job(vid, script, shots, num_frames, steps, script_beats=beats)
        for vid, script, shots, beats in _EPISODES
    ]


science_ltx_jobs = build_science_jobs(num_frames=129, steps=8)

# Preferred ENGINE per episode (LTX-2.5 only)
SCIENCE_ENGINE_BY_ID = {
    "sci_ep01_sun_closer": "ltx",
    "sci_ep02_dyson_heat": "ltx",
    "sci_ep03_black_hole_outer": "ltx",
    "sci_ep04_atmosphere_freeze": "ltx",
    "sci_ep05_elevator_snap": "ltx",
}
