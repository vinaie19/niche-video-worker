"""
Threshold Physics (Channel B) — episode jobs for LTX / Wan / Hunyuan batches.

Run: CHANNEL=b ENGINE=ltx VIDEO_ID=sci_ep01_sun_closer python run_test_batch.py
"""

_SCI_SUFFIX = (
    "photo-realistic cinematic CGI, vertical 9:16, locked camera, "
    "no people, no faces, NO text, NO letters, NO logos, no watermarks"
)

_VO_DEFAULTS = {
    "shot_mode": "multi_cut",
    "voice": "davis",
    "captions": "minimal",
    "ambient": "space",
    "ambient_volume": 0.28,
    "vo_delay_ms": 400,
}


def _science_job(video_id, script, shots, num_frames, steps):
    return {
        "video_id": video_id,
        "num_frames": num_frames,
        "steps": steps,
        "script": script.strip(),
        "shots": list(shots),
        **_VO_DEFAULTS,
    }


# --- Episode 1: Sun 10% closer ---

_EP01_SCRIPT = """
What if the Sun moved ten percent closer tomorrow—
which limit fails first?

Not melting rock.
Not the oceans boiling overnight.

First: Earth's energy budget.
Ten percent closer means roughly twenty-one percent more sunlight—
enough to shatter the climate balance we evolved under.

Then: the upper atmosphere expands,
satellites start dying in denser air,
and the runaway isn't sci-fi theater—
it's thermodynamics with nowhere to hide.

The Sun doesn't need to touch us.
It only needs to cross a threshold.
""".strip()

_EP01_SHOTS = [
    f"Cinematic locked extreme close-up of the Sun's limb, violent white-gold prominence arching and flickering, intense glare and heat shimmer, deep black space void, immediate plasma motion, {_SCI_SUFFIX}",
    f"Cinematic locked wide shot of Earth from space, cool blue oceans and thin white atmosphere against deep black void, soft sunlight from off-frame, serene orbital stillness, {_SCI_SUFFIX}",
    f"Cinematic locked wide shot of Earth under harsher closer sunlight, oceans shifting from blue to burned amber glare, atmosphere glowing brighter, heat-haze shimmer on the limb, {_SCI_SUFFIX}",
    f"Cinematic locked medium-wide shot of Earth's upper atmosphere expanding into a thicker glowing shell, tiny dark satellite silhouettes tumbling as sparks of debris, orbital heat shimmer, {_SCI_SUFFIX}",
    f"Cinematic locked medium shot of Earth limb with violent amber glare and boiling cloud tops under excess solar flux, heat distortion waves, {_SCI_SUFFIX}",
    f"Cinematic locked ultra-wide shot of a visibly closer Sun dominating the frame as a blinding white-gold disc, tiny Earth offset near the edge, deep black void, quiet catastrophic scale, minimal motion, {_SCI_SUFFIX}",
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
    ("sci_ep01_sun_closer", _EP01_SCRIPT, _EP01_SHOTS),
    ("sci_ep02_dyson_heat", _EP02_SCRIPT, _EP02_SHOTS),
    ("sci_ep03_black_hole_outer", _EP03_SCRIPT, _EP03_SHOTS),
    ("sci_ep04_atmosphere_freeze", _EP04_SCRIPT, _EP04_SHOTS),
    ("sci_ep05_elevator_snap", _EP05_SCRIPT, _EP05_SHOTS),
]


def build_science_jobs(num_frames, steps):
    return [
        _science_job(vid, script, shots, num_frames, steps)
        for vid, script, shots in _EPISODES
    ]


science_ltx_jobs = build_science_jobs(num_frames=129, steps=8)
science_wan_jobs = build_science_jobs(num_frames=81, steps=16)
science_hunyuan_jobs = build_science_jobs(num_frames=129, steps=20)

# Preferred ENGINE per episode (for render_channel_b.sh)
SCIENCE_ENGINE_BY_ID = {
    "sci_ep01_sun_closer": "ltx",
    "sci_ep02_dyson_heat": "wan",
    "sci_ep03_black_hole_outer": "ltx",
    "sci_ep04_atmosphere_freeze": "hunyuan",
    "sci_ep05_elevator_snap": "wan",
}
