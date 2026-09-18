#!/usr/bin/env bash
# Copy a QC-passed complete Short into final_videos/ready as *_hook.mp4
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VID="${1:?usage: promote_to_ready.sh sci_ep01_sound_194db}"
SRC="${ROOT}/final_videos/${VID}_complete.mp4"
DST="${ROOT}/final_videos/ready/${VID}_hook.mp4"
if [[ ! -f "$SRC" ]]; then
  echo "Missing: $SRC"
  exit 1
fi
mkdir -p "${ROOT}/final_videos/ready"
cp -f "$SRC" "$DST"
echo "Ready: $DST"
