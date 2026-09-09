# Voice presets: christopher | guy | davis | jenny | aria | sara | michelle |
#                andrew | emma | ryan | sonia | prabhat
# Captions: False | "minimal" | "clean" | "boxed" | "yellow" | "tiny"
# Ambient: False | "rain" | "rain_city" | path/to.wav  (starts at 0:00)
# Title: optional one-line overlay at 0:00 (not Whisper captions)
#
# Wan: 49 frames @ 16fps ≈ 3.1s/shot
# Hunyuan: prefer 5×49 @ 24fps ≈ 10.2s total (retention cuts), or 3×73 ≈ 9.1s
# Framing: medium/wide so the location is readable — avoid extreme close-ups as the only view
#
# Series 1 — Places That Stay Open:
#   ep01 ramen window | ep02 konbini glow | ep03 vending alley
#   ep04 midnight platform | ep05 capsule hall | ep06 coin laundry | ep07 noren closing

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

# Used when ENGINE=hunyuan. Preference: 5 shots × 49 @ 24fps ≈ 10s, steps=30, wider readable frames.
hunyuan_ab_jobs = [
    {
        "video_id": "ep06_coin_laundry",
        "shot_mode": "multi_cut",
        "num_frames": 49,
        "steps": 30,
        "captions": False,
        "ambient": "rain_city",
        "ambient_volume": 0.42,
        "title": "Still open.",
        "shots": [
            # 1 Hook — motion first, but readable as a washer drum (not abstract blur)
            "Cinematic locked medium close-up of a Japanese coin laundry washing machine door at night, soapy water and clothes tumbling clearly behind the round glass, cool white fluorescent light, soft rain streaks on the shop window in the background, vibrant saturated colors, photo-realistic, vertical 9:16, medium framing so the whole machine door is visible, no people, no faces, no camera move",
            # 2 Wide establish — full row of machines readable as a coin laundry
            "Cinematic locked wide shot of a small empty Japanese coin laundry at night, a full row of white washers and dryers clearly visible along the wall, bright fluorescent ceiling lights, large front windows wet with rain showing dark street neon outside, wet tile floor reflections, vivid color contrast, photo-realistic, vertical 9:16, wide establishing frame, no people, no faces, no camera move",
            # 3 Medium — change machine / detergent shelf as location detail
            # 4 Atmosphere — rain on glass with laundry interior readable behind
            # 5 Anchor — human trace without faces
            "Cinematic locked medium shot of a coin-operated change machine and detergent boxes on a metal shelf inside a Japanese laundromat at night, fluorescent light, rain visible through the window behind, clean readable subject, vibrant colors, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            "Cinematic locked medium-wide shot looking out from inside a Japanese coin laundry through a large rain-lashed front window at night, glowing wet street and neon outside, rows of washers softly visible in the reflection and foreground edges, constant rain motion on glass, saturated cyan and warm interior light, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            "Cinematic locked medium shot of a lone plastic laundry basket on a bench inside an empty Japanese coin laundry at night, one dryer door slightly open with warm light spilling out, soft steam or heat shimmer, rain on the windows behind, cozy saturated colors, photo-realistic, vertical 9:16, subject fully readable in frame, no people, no faces, no camera move",
        ],
    }
]
