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
#
# Series 1 — Places That Stay Open:
#   ep01 ramen window | ep02 konbini glow | ep03 vending alley
#   ep04 midnight platform | ep05 capsule hall | ep06 coin laundry | ep07 noren closing

test_jobs = [
    {
        "video_id": "ep03_vending_alley",
        "shot_mode": "multi_cut",
        "num_frames": 49,
        "steps": 16,
        "script": (
            "A narrow alley. Machines stand like quiet sentries. "
            "Coins wait in a forgotten tray. Neon drinks the rain. "
            "Nothing is sold tonight. Everything still glows. "
            "The city hums. You walk on."
        ),
        "voice": "aria",
        "captions": "minimal",
        "ambient": "rain_city",
        "vo_delay_ms": 900,
        "ambient_volume": 0.40,
        "shots": [
            # Hook: narrow alley corridor of machines (not facade / not konbini interior)
            "Cinematic locked shot down a narrow Japanese alley lined with glowing drink vending machines at night, wet brick walls, pink and cyan neon spill, light rain mist, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            # Coin slot / panel detail
            "Cinematic locked extreme close-up of a vending machine coin slot and lit selection buttons, soft neon glow on scratched metal, subtle button light flicker only, shallow depth of field, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            # Dispense flap / empty tray still life
            "Cinematic locked close-up of an open vending machine dispense flap with a forgotten coin resting in the change tray, warm machine light, shallow depth of field, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            # Rain on lit glass front + blurred cans (staple aesthetic)
            "Cinematic locked medium shot of rain beading and sliding down the glossy front of a drink vending machine at night, colorful can rows blurred behind glass, subtle droplet motion only, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            # Side profile row of machines
            "Cinematic locked side-angle shot of a row of brightly lit vending machines along a wet alley wall at night, repeating neon rectangles receding into darkness, soft rain, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            # Low angle: wet cobble + machine feet glow
            "Cinematic locked low-angle shot of wet alley cobblestones reflecting vending-machine neon at night, machine bases glowing above frame edge, subtle puddle ripple only, photo-realistic, vertical 9:16, no people, no faces, no camera move",
            # Closing: distant alley mouth, machines as light sources (not puddle clone of ep02)
            "Cinematic locked wide shot from deep inside a dark alley toward a bright street mouth, silhouetted vending machines glowing on both sides, light rain falling, empty path, photo-realistic, vertical 9:16, no people, no faces, no camera move",
        ],
    }
]
