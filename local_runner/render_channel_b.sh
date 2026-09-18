#!/usr/bin/env bash
# Threshold Physics Top 12 — one RunPod session per episode (LTX).
# Strategy: ../THRESHOLD_PHYSICS_STRATEGY.md
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

# Top 12 posting order (POSTING_SCHEDULE_B.md)
render_one sci_ep01_sound_194db
render_one sci_ep02_roche_limit
render_one sci_ep03_neutron_impact
render_one sci_ep04_absolute_zero
render_one sci_ep05_spaghettification
render_one sci_ep06_absolute_hot
render_one sci_ep07_chandrasekhar
render_one sci_ep08_metallic_hydrogen
render_one sci_ep09_solar_escape
render_one sci_ep10_eddington
render_one sci_ep11_vacuum_decay
render_one sci_ep12_neutron_drip

echo ""
echo "Done. QC complete MP4s in ../final_videos/ then promote with promote_to_ready.sh"
echo "Per episode: local QC → YouTube AI review → schedule (see POSTING_SCHEDULE_B.md)"
