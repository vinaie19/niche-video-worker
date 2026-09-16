#!/usr/bin/env bash
# Create EU-RO-1 network volume (if missing) and download LTX weights on a cheap GPU.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1
export ENGINE="${ENGINE:-ltx}"
export LTX_VARIANT="${LTX_VARIANT:-distilled}"
export POD_ACQUIRE_SLEEP_S="${POD_ACQUIRE_SLEEP_S:-20}"

.venv/bin/python <<'PY'
import json, os, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv("local_runner/.env", override=True)
import runpod
from runpod.api.graphql import run_graphql_query

runpod.api_key = os.getenv("RUNPOD_API_KEY")
assert runpod.api_key, "RUNPOD_API_KEY missing"

r = run_graphql_query(
    "query { myself { networkVolumes { id name size dataCenterId } } }"
)
vols = r["data"]["myself"]["networkVolumes"] or []
print("existing volumes:", vols)

if vols:
    vol = next((v for v in vols if v.get("dataCenterId") == "EU-RO-1"), vols[0])
else:
    print("creating niche-threshold-models 100GB @ EU-RO-1 ...")
    m = run_graphql_query(
        """
        mutation {
          createNetworkVolume(input: {
            name: "niche-threshold-models"
            size: 100
            dataCenterId: "EU-RO-1"
          }) {
            id name size dataCenterId
          }
        }
        """
    )
    if "errors" in m:
        raise SystemExit(m["errors"])
    vol = m["data"]["createNetworkVolume"]
    print("created:", vol)
    time.sleep(5)
    r2 = run_graphql_query(
        "query { myself { networkVolumes { id name size dataCenterId } } }"
    )
    print("listed after create:", r2["data"]["myself"]["networkVolumes"])

vid = vol["id"]
dc = vol.get("dataCenterId") or "EU-RO-1"
env_path = Path("local_runner/.env")
lines = env_path.read_text().splitlines() if env_path.exists() else []
out, seen_v, seen_d = [], False, False
for line in lines:
    if line.startswith("NETWORK_VOLUME_ID="):
        out.append(f"NETWORK_VOLUME_ID={vid}")
        seen_v = True
    elif line.startswith("DATA_CENTER_ID="):
        out.append(f"DATA_CENTER_ID={dc}")
        seen_d = True
    else:
        out.append(line)
if not seen_v:
    out += ["", f"NETWORK_VOLUME_ID={vid}"]
if not seen_d:
    out += [f"DATA_CENTER_ID={dc}"]
env_path.write_text("\n".join(out) + "\n")
print(f"ACTIVE_VOLUME={vid} DC={dc}")
PY

exec .venv/bin/python local_runner/bootstrap_volume.py
