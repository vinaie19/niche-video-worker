# Voice presets: christopher | guy | davis | jenny | aria | sara | michelle |
#                andrew | emma | ryan | sonia | prabhat
# Captions: False | "minimal" | "clean" | "boxed" | "yellow" | "tiny"
# Ambient: False | "rain" | "rain_city" | path/to.wav  (rain before VO = Shorts hook)
#
# 5090 profile: 49 frames @ 16fps ≈ 3.1s/shot, 16 steps (see .env WAN_*)
# ~22s Short ≈ 7 shots. Override per job with num_frames / steps if needed.
#
# Retention checklist (palate-cleanser Shorts):
#   1. Visual hook — shot 1 first frame must be gorgeous (reroll if flat)
#   2. Audio hook  — ambient rain/city starts immediately; VO delayed ~900ms
#   3. Pacing      — 7×49f ≈ 22s (still Shorts-safe; avoid 30s+)

test_jobs = [
    {
        "video_id": "ep01_ramen_window",
        "shot_mode": "multi_cut",
        "num_frames": 49,
        "steps": 16,
        "script": (
            "Late night. Rain softens the neon. "
            "Steam ghosts the glass. Inside, the broth waits. "
            "Outside, the city finally exhales."
        ),
        "voice": "aria",
        "captions": False,
        "ambient": "rain_city",
        "vo_delay_ms": 900,
        "ambient_volume": 0.40,
        "shots": [
            # Visual hook: steaming ramen + pink/cyan neon — curate lighting hard
            "Cinematic locked shot through a rain-streaked shop window at night, steaming tonkotsu ramen bowl on wooden counter, chopsticks beside it, pink and cyan neon reflections on wet glass, gentle rising steam, shallow depth of field, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            "Cinematic locked close-up of raindrops sliding down a shop window at night, blurred warm interior lights and soft neon bokeh behind the glass, subtle droplet motion only, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            "Cinematic locked shot of a wet empty sidewalk outside a tiny ramen shop at night, neon reflecting in puddles, soft rain falling, warm window glow spilling onto wet asphalt, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            "Cinematic locked close-up of chopsticks resting beside a steaming ramen bowl, soft neon color wash, gentle rising steam only, shallow depth of field, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            "Cinematic locked medium shot of a ceramic ramen spoon resting in rich tonkotsu broth, soft steam rising, pink and cyan neon rim light, shallow depth of field, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            "Cinematic locked shot of a glowing noren curtain swaying gently in a ramen shop doorway at night, warm interior spill, rain mist outside, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            "Cinematic locked wide shot of a tiny ramen shop exterior at night in light rain, glowing noren curtain doorway, neon sign reflections on wet street, empty sidewalk, photo-realistic, vertical 9:16, no people, no faces, no camera move",
        ],
    }
]
