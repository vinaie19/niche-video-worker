# Voice presets: christopher | guy | davis | jenny | aria | sara | michelle |
#                andrew | emma | ryan | sonia | prabhat
# Or full Edge-TTS id e.g. "en-US-JennyNeural"
#
# Captions: False / "off"  → voice only
#           True / "on"    → burn-in (use caption_style, default minimal)
#           "minimal" | "clean" | "boxed" | "yellow" | "tiny"  → that style

test_jobs = [
    {
        "video_id": "video_01_wan22_smoke",
        "shot_mode": "multi_cut",
        "script": (
            "Golden hour on a forgotten midway. A young man in a worn denim jacket "
            "stands still, watching a rusted Ferris wheel turn against the dust. "
            "No crowds. Just wind, and the quiet pull of nostalgia."
        ),
        "voice": "christopher",
        "captions": False,
        # "captions": "minimal",
        # "caption_style": "clean",  # only needed when captions=True
        "shots": [
            "Cinematic medium shot, young man in a worn denim jacket standing still on a dusty country amusement park midway at golden hour, looking toward a rusted Ferris wheel, soft wind moving his hair, photo-realistic, vertical framing, shallow depth of field, no walking, no orbit"
        ],
    }
]
