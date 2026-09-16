# Voice presets: christopher | guy | davis | jenny | aria | sara | michelle |
#                andrew | emma | ryan | sonia | prabhat
# Captions: False | "minimal" | "clean" | "boxed" | "yellow" | "tiny"
# Ambient: False | "rain" | "rain_city" | "space" | path/to.wav  (starts at 0:00)
# Channel B (Threshold Physics): CHANNEL=b → science_ltx_jobs in science_prompts.py
# Title: optional one-line overlay at 0:00 (not Whisper captions)
#
# LTX-2.5: 3×97 @ 24fps ≈ 4.0s/shot ≈ 12s total | distilled ManualSigmas (~8) | native AV
# Native latent 1088×1920 → ffmpeg 1080×1920 delivery
# Batch flow: generate all shots of one short → stitch → next short
#
# Series 2 done: s2_ep01–s2_ep07
# Series 3 — Places That Stay Open (LTX): s3_ep01–s3_ep07
# Series 3 on Blackwell PRO 6000 (96GB): FORCE_OFFLOAD=false + LTX_TE_DEVICE=default (GPU).

import os

from science_prompts import science_ltx_jobs

_AMBIENT_DIR = os.path.join(os.path.dirname(__file__), "ambient")
LAUNDRY_RAIN_BED = os.path.join(_AMBIENT_DIR, "laundry_rain_bed.wav")


def _ltx_place(video_id, title, shots):
    return {
        "video_id": video_id,
        "shot_mode": "multi_cut",
        "num_frames": 97,
        "steps": 8,
        "captions": False,
        "ambient": False,  # keep LTX native AV
        "title": title,
        "shots": shots,
    }


# Channel A — Series 3: Places That Stay Open (LTX-2.5)
ltx_ab_jobs = [
    _ltx_place(
        "s3_ep01_parking_fluorescent",
        "Level B2.",
        [
            "Cinematic locked extreme close-up of a flickering fluorescent tube buzzing over wet concrete in an empty underground parking garage at night, moths circling the light, immediate flicker motion, harsh buzz and soft drip audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text, NO letters",
            "Cinematic locked wide shot of an empty multi-level parking garage at night, long rows of pillars, cold green-white fluorescents, wet tire-shine on the floor, distant traffic rumble and echo drip audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
            "Cinematic locked medium shot of a yellow concrete parking barrier and painted curb under stuttering overhead light, dust motes in the beam, soft electrical buzz and distant engine audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
        ],
    ),
    _ltx_place(
        "s3_ep02_florist_fridge",
        "Still fresh.",
        [
            "Cinematic locked extreme close-up of condensation racing down the glass door of a flower-shop cooler at night, bright blooms blurred behind fogged glass, constant water motion, soft compressor hum and drip audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
            "Cinematic locked medium shot of an empty tiny florist at night, open glass coolers glowing pink and green, buckets of wrapped stems, soft fridge hum and distant rain audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
            "Cinematic locked close-up of water droplets beading on rose petals inside a lit cooler, soft mist, gentle refrigeration fan and drip audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
        ],
    ),
    _ltx_place(
        "s3_ep03_bowling_lanes",
        "Last frame.",
        [
            "Cinematic locked extreme close-up of polished bowling-lane wood reflecting neon scoring lights at night, subtle vibration ripple across the varnish, soft mechanical pinsetter hum audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text, NO readable scores",
            "Cinematic locked wide shot of an empty bowling alley at night, glowing lanes stretching away, pink and cyan overhead neon, pin decks lit, quiet machine drones and HVAC audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
            "Cinematic locked medium shot of a rack of colorful bowling balls under warm counter light, soft reflections, distant pinsetter clunk and ambient hum audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
        ],
    ),
    _ltx_place(
        "s3_ep04_manga_cafe",
        "All-nighter.",
        [
            "Cinematic locked extreme close-up of stacked manga spines under a small desk lamp in a night manga cafe booth, dust drifting in the warm beam, soft page-rustle and rain on window audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text, NO readable titles",
            "Cinematic locked wide shot of an empty manga cafe corridor of private booths at night, soft orange lamps, carpeted floor, quiet fluorescent spill, calm room-tone and distant rain audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
            "Cinematic locked medium shot of an empty booth with headphones and a glowing drink fridge in the background, soft fridge hum and lamp buzz audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
        ],
    ),
    _ltx_place(
        "s3_ep05_karaoke_corridor",
        "Room still lit.",
        [
            "Cinematic locked extreme close-up of a glowing karaoke room door indicator light pulsing in a narrow hallway at night, soft pink neon spill, muffled bass thump and corridor hum audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
            "Cinematic locked wide shot of an empty karaoke hallway at night, rows of closed doors with soft LED strips, patterned carpet, quiet bass leakage and HVAC audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
            "Cinematic locked medium shot of a drink cart with ice melting in a bucket under magenta hallway light, soft ice crackle and distant muffled music audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
        ],
    ),
    _ltx_place(
        "s3_ep06_fish_market_ice",
        "Before dawn.",
        [
            "Cinematic locked extreme close-up of crushed ice glistening under cold fluorescent light at a closed fish market stall, meltwater dripping fast, soft drip and compressor hum audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
            "Cinematic locked wide shot of an empty covered fish market corridor at night, shuttered stalls, wet concrete, cool blue-white lights, distant drip echo and fridge hum audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
            "Cinematic locked medium shot of stacked polystyrene boxes and a running hose trickle over ice, steam of cold air, soft water and night market hush audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
        ],
    ),
    _ltx_place(
        "s3_ep07_hotel_ice_machine",
        "Floor 7.",
        [
            "Cinematic locked extreme close-up of ice cubes tumbling into a hotel ice machine chute at night, cold blue interior glow, clatter and motor whir audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
            "Cinematic locked wide shot of an empty mid-rise hotel corridor at night, patterned carpet, evenly spaced wall sconces, soft ice-machine hum at the far end, quiet HVAC audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
            "Cinematic locked medium shot of a glowing ice and vending alcove, soft drink fridge light, carpet reflections, gentle machine idle and distant elevator ding undertone audio, photo-realistic, vertical 9:16, no people, no faces, no camera move, NO text",
        ],
    ),
]

# Alias for callers that still say test_jobs
test_jobs = ltx_ab_jobs
