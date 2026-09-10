# Voice presets: christopher | guy | davis | jenny | aria | sara | michelle |
#                andrew | emma | ryan | sonia | prabhat
# Captions: False | "minimal" | "clean" | "boxed" | "yellow" | "tiny"
# Ambient: False | "rain" | "rain_city" | path/to.wav  (starts at 0:00)
# Title: optional one-line overlay at 0:00 (not Whisper captions)
#
# Wan: 49 frames @ 16fps ≈ 3.1s/shot
# Hunyuan: 3×81 @ 24fps ≈ 3.4s/shot ≈ 10s total (3s target; 81 is 4k+1-safe on current image)
#          steps=30. Soft VO + real laundry/rain bed (not pink-noise hiss).
# LTX-2.3: 3×97 @ 24fps ≈ 4.0s/shot ≈ 12s total | distilled ManualSigmas (~8) | native AV
#
# Series 1 — Places That Stay Open:
#   ep01 ramen window | ep02 konbini glow | ep03 vending alley
#   ep04 midnight platform | ep05 capsule hall | ep06 coin laundry | ep07 noren closing

import os

_AMBIENT_DIR = os.path.join(os.path.dirname(__file__), "ambient")
LAUNDRY_RAIN_BED = os.path.join(_AMBIENT_DIR, "laundry_rain_bed.wav")

test_jobs = [
    {
        "video_id": "ep05_capsule_rain",
        "shot_mode": "multi_cut",
        "num_frames": 49,
        "steps": 24,
        "captions": False,
        "ambient": "rain_city",
        "ambient_volume": 0.45,
        "title": "2AM.",
        "shots": [
            "Cinematic locked extreme close-up of heavy rain rapidly sliding down a large glass window at night, full frame water motion, out-of-focus bright warm orange capsule hotel lights reflecting on the wet glass, vibrant cyan city neon outside, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            "Cinematic locked shot dominated by a large wet window lashed with heavy rain at night, glowing city lights outside, the bright orange fiberglass lip of an open capsule hotel pod in the immediate foreground, constant water motion on the glass, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            "Cinematic locked close-up of a steaming paper tea cup resting on a wooden ledge, thick steam rising rapidly, a large window covered in heavy moving rain directly behind it, glowing warm orange light filling the space, photo-realistic, vertical 9:16, no people, no faces, no camera move",
        ],
    }
]

# Used when ENGINE=hunyuan.
hunyuan_ab_jobs = [
    {
        "video_id": "ep06_coin_laundry_soothing",
        "shot_mode": "multi_cut",
        "num_frames": 81,
        "steps": 30,
        "captions": False,
        "ambient": LAUNDRY_RAIN_BED,
        "ambient_volume": 0.48,
        "title": "Still open.",
        "shots": [
            # 1 Hook — Soft pastel clothes tumbling + Calming light
            "Cinematic locked medium close-up of a Japanese coin laundry washing machine door at night, soft pastel-colored clothes tumbling clearly behind the round glass, gentle warm white and muted teal light spilling across the metal chassis, soft rain on the shop window in the background, soothing pastel color palette, low contrast, calm atmosphere, photo-realistic, vertical 9:16, medium framing so the whole machine door is visible, no people, no faces, no camera move",
            
            # 2 Wide establish — Soft seafoam/cream machines + Gentle reflections
            "Cinematic locked wide shot of a small empty Japanese coin laundry at night, a row of pale seafoam green and soft cream retro washers, gentle warm interior light reflecting softly across the wet tile floor, muted rain and dark teal night outside the windows, soothing cinematic color grading, photo-realistic, vertical 9:16, wide establishing frame, no people, no faces, no camera move",
            
            # 3 Anchor — Pale basket + Warm glowing spill
            "Cinematic locked medium shot of a soft peach-colored plastic laundry basket and pale mint detergent bottles on a bench inside an empty Japanese coin laundry at night, one dryer door slightly open with gentle warm golden light spilling out, soft steam, soothing pastel aesthetic, calm rain on the window behind, photo-realistic, vertical 9:16, subject fully readable in frame, no people, no faces, no camera move",
        ],
    }
]

# Used when ENGINE=ltx — ep07 noren closing (motion-first hook for retention).
# ambient=False: keep LTX native AV (do not replace with rain bed).
ltx_ab_jobs = [
    {
        "video_id": "ep07_noren_closing_ltx",
        "shot_mode": "multi_cut",
        "num_frames": 97,
        "steps": 8,
        "captions": False,
        "ambient": False,
        "title": "Last call.",
        "shots": [
            # 1 Hook — Full-frame noren sway + fabric/rain sound for LTX AV
            "Cinematic locked extreme close-up of a dark indigo Japanese noren curtain with bold white kanji swaying hard in a night doorway, fabric snapping and settling, warm amber shop light bleeding through the split, rain droplets on the cloth edge, immediate motion, soft rain and cloth flutter audio, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            # 2 Establish — Empty shop mouth after closing
            "Cinematic locked medium shot of a narrow Tokyo alley shop entrance at night with indigo noren half-drawn across the doorway, warm interior lamp still on, wet pavement reflecting neon cyan and red, light rain falling, quiet after-hours atmosphere, distant rain and faint street hum audio, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            # 3 Anchor — Handwritten closed sign + steam / rain
            "Cinematic locked close-up of a small handwritten Japanese closed sign hanging beside a swaying noren at night, soft steam from a hidden kitchen vent, rain on dark wood and metal fixtures, warm tungsten spill, melancholic still-open glow, gentle rain and soft wood creak audio, photo-realistic, vertical 9:16, no people, no faces, no camera move",
        ],
    }
]
