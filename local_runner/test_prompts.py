# Voice presets: christopher | guy | davis | jenny | aria | sara | michelle |
#                andrew | emma | ryan | sonia | prabhat
# Captions: False | "minimal" | "clean" | "boxed" | "yellow" | "tiny"
# Ambient: False | "rain" | "rain_city" | path/to.wav  (starts at 0:00)
# Title: optional one-line overlay at 0:00 (not Whisper captions)
#
# 5090 profile (Wan): 49 frames @ 16fps ≈ 3.1s/shot, 24 steps (see .env WAN_*)
# Hunyuan A/B: ENGINE=hunyuan HY_VARIANT=480p_distilled HY_NUM_FRAMES=73 HY_STEPS=20
#   → 73 frames @ 24fps ≈ 3.0s/shot (matches Wan shot length for retention compare)
# Retention test: 3 shots ≈ 9s, no VO, rain from 0, one quiet title.
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
        "ambient_volume": 0.45, # Bumped slightly since it's the only audio
        "title": "2AM.",
        "shots": [
            # Hook — Frame 0 is entirely moving water. Location established via reflection only.
            "Cinematic locked extreme close-up of heavy rain rapidly sliding down a large glass window at night, full frame water motion, out-of-focus bright warm orange capsule hotel lights reflecting on the wet glass, vibrant cyan city neon outside, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            
            # Context — Window dominates. The pod is just a framing device in the foreground.
            "Cinematic locked shot dominated by a large wet window lashed with heavy rain at night, glowing city lights outside, the bright orange fiberglass lip of an open capsule hotel pod in the immediate foreground, constant water motion on the glass, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            
            # Anchor — The "Ramen Signal" (heat/human trace) with the window still dominating the background.
            "Cinematic locked close-up of a steaming paper tea cup resting on a wooden ledge, thick steam rising rapidly, a large window covered in heavy moving rain directly behind it, glowing warm orange light filling the space, photo-realistic, vertical 9:16, no people, no faces, no camera move",
        ],
    }
]

# Hunyuan A/B twin (same ep05 prompts). Enable by pointing test_jobs at this list, or:
#   ENGINE=hunyuan HY_NUM_FRAMES=73 HY_STEPS=20 python local_runner/run_test_batch.py
# Prefer dropping num_frames/steps here so HY_* / WAN_* env controls duration.
hunyuan_ab_jobs = [
    {
        "video_id": "ep05_capsule_rain_hy",
        "shot_mode": "multi_cut",
        "num_frames": 73,
        "steps": 20,
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
