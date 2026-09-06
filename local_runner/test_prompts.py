test_jobs = [
    {
        "video_id": "video_01_continuous_smoke",
        "shot_mode": "continuous",
        "chunks": 2,  # ~10s continuous (2 x 81 frames @ 16fps, minus 1-frame overlap)
        "upscale": True,  # lanczos 1080x1920 after stitch (UltraSharp skipped in continuous smoke)
        "shots": [
            "Cinematic continuous single take, cyberpunk neon rain alley, glowing blue eyes close-up slowly pulling back to reveal the city, photo-realistic, vertical framing, smooth camera move, no cuts"
        ],
    }
]
