# I2V (image-to-video first frame)

LTX-2.5 renders support an optional first-frame image conditioning pass
(`workflow_ltx_i2v.json`) alongside the default T2V path. No start image =
T2V, unchanged.

## Usage in a shot dict

Add `start_image` (local file) or `start_image_url` (already-hosted URL) to
any shot entry in your batch config:

```python
"shots": [
    {"prompt": "wide shot of...", "start_image": "shot_1.png"},
    "plain prompt string shot with no image, unaffected",
]
```

- `start_image`: local path. Put stills under
  `local_runner/i2v_stills/<video_id>/shot_1.png`, `shot_2.png`, ... and
  reference them from the shot dict. `run_test_batch.py` uploads the file to
  R2 (`stills/<video_id>/shot_N.png`) and passes `start_image_url` to the
  worker automatically.
- `start_image_url`: skip the upload and point directly at an existing
  public URL (takes priority over `start_image` if both are set).

## Worker API

`POST /render` (or `/prompt`) accepts:

- `start_image_url` — public URL to download.
- `start_image_b64` — base64-encoded image (data URLs accepted; `data:...,`
  prefix stripped automatically).

When either is present, the worker downloads/decodes the image to
`/comfyui/input/<job_id>_start.png`, loads `workflow_ltx_i2v.json` (LoadImage
→ LTXVPreprocess → LTXVImgToVideoInplace feeding the video latent) instead of
`workflow_ltx_t2v.json`, and otherwise behaves like a normal render. `/health`
reports `"i2v": true`.
