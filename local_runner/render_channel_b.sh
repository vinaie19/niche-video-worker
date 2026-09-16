#!/usr/bin/env bash
# Threshold Physics batch 1 — one RunPod session per episode (preferred engine).
set -euo pipefail
cd "$(dirname "$0")"

if [[ -z "${RUNPOD_API_KEY:-}" ]]; then
  echo "RUNPOD_API_KEY is not set. Export it and ensure the network volume is attached."
  exit 1
fi

render_one() {
  local engine="$1"
  local vid="$2"
  echo ""
  echo "========== CHANNEL=b ENGINE=${engine} VIDEO_ID=${vid} =========="
  CHANNEL=b ENGINE="${engine}" VIDEO_ID="${vid}" python run_test_batch.py
}

render_one ltx sci_ep01_sun_closer
render_one wan sci_ep02_dyson_heat
render_one ltx sci_ep03_black_hole_outer
render_one hunyuan sci_ep04_atmosphere_freeze
render_one wan sci_ep05_elevator_snap

echo ""
echo "Done. QC complete MP4s in ../final_videos/ then promote with promote_to_ready.sh"
