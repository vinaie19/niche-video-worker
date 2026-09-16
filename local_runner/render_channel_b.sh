#!/usr/bin/env bash
# Threshold Physics batch — one RunPod session per episode (LTX-2.5 only).
set -euo pipefail
cd "$(dirname "$0")"

if [[ -z "${RUNPOD_API_KEY:-}" ]]; then
  echo "RUNPOD_API_KEY is not set. Export it and ensure the network volume is attached."
  exit 1
fi

render_one() {
  local vid="$1"
  echo ""
  echo "========== CHANNEL=b ENGINE=ltx VIDEO_ID=${vid} =========="
  CHANNEL=b ENGINE=ltx VIDEO_ID="${vid}" python run_test_batch.py
}

render_one sci_ep01_sun_closer
render_one sci_ep02_dyson_heat
render_one sci_ep03_black_hole_outer
render_one sci_ep04_atmosphere_freeze
render_one sci_ep05_elevator_snap

echo ""
echo "Done. QC complete MP4s in ../final_videos/ then promote with promote_to_ready.sh"
