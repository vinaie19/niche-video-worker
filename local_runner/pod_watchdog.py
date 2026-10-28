"""
RunPod safety net that does not depend on the shell (or Claude session) that started a render.

Start it detached right before a render; it outlives the session that launched it:
  setsid nohup venv/bin/python pod_watchdog.py > /dev/null 2>&1 &
Every 60s it checks whether a run_test_batch.py process is alive and which pods are RUNNING.
When no render is alive (after a short grace period for the render to start), or MAX_MIN
minutes have passed since it started, whichever is first, it stops every RUNNING pod,
verifies they are EXITED, logs to local_runner/watchdog.log and exits.

  python pod_watchdog.py --status   # print balance + pod states once, then exit

The API key is read from local_runner/.env and never printed. Stopped pods cost nothing;
only the network volume bills while idle.
"""
import os
import subprocess
import sys
import time

import requests
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "watchdog.log")
MAX_MIN = float(os.getenv("WATCHDOG_MAX_MIN", "45"))
GRACE_S = 120  # let a render that is started just after the watchdog show up
POLL_S = 60

load_dotenv(os.path.join(HERE, ".env"))
KEY = os.environ["RUNPOD_API_KEY"]


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    with open(LOG, "a") as f:
        f.write(line + "\n")
    print(line, flush=True)


def gql(query):
    r = requests.post("https://api.runpod.io/graphql", headers={"Authorization": f"Bearer {KEY}"},
                      json={"query": query}, timeout=30)
    r.raise_for_status()
    return r.json()["data"]


def account():
    return gql("{ myself { clientBalance currentSpendPerHr pods { id desiredStatus costPerHr } } }")["myself"]


def render_alive():
    out = subprocess.run(["pgrep", "-f", "python.*run_test_batch.py"], capture_output=True, text=True)
    return bool(out.stdout.strip())


def stop_running():
    """Stop every RUNNING pod and confirm EXITED. Returns the ids that are still not EXITED."""
    import runpod

    runpod.api_key = KEY
    running = [p["id"] for p in account()["pods"] if p["desiredStatus"] == "RUNNING"]
    for pid in running:
        log(f"stopping pod {pid}")
        try:
            runpod.stop_pod(pid)
        except Exception as e:  # keep going; re-checked below
            log(f"stop_pod {pid} failed: {e}")
    for _ in range(20):
        left = [p["id"] for p in account()["pods"] if p["desiredStatus"] == "RUNNING"]
        if not left:
            return []
        time.sleep(3)
    return left


def status():
    a = account()
    print(f"balance {a['clientBalance']:.4f} spend/hr {a['currentSpendPerHr']}")
    for p in a["pods"]:
        print(f"pod {p['id']} {p['desiredStatus']} {p['costPerHr']}")


def watch():
    start = time.time()
    log(f"watchdog start (cap {MAX_MIN:.0f} min, pid {os.getpid()})")
    while True:
        elapsed = time.time() - start
        alive = render_alive()
        reason = None
        if elapsed > MAX_MIN * 60:
            reason = f"{MAX_MIN:.0f}-minute cap reached"
        elif not alive and elapsed > GRACE_S:
            reason = "no render process alive"
        if reason:
            if alive:
                log(f"{reason}: interrupting run_test_batch.py")
                subprocess.run(["pkill", "-INT", "-f", "python.*run_test_batch.py"])
                time.sleep(20)
            try:
                left = stop_running()
            except Exception as e:
                log(f"API error while stopping pods: {e}; retrying in 60s")
                time.sleep(POLL_S)
                continue
            if left:
                log(f"pods still not EXITED: {left}; retrying in 60s")
                time.sleep(POLL_S)
                continue
            a = account()
            log(f"{reason}; all pods EXITED, balance {a['clientBalance']:.4f}. watchdog exit")
            return
        time.sleep(POLL_S)


if __name__ == "__main__":
    status() if "--status" in sys.argv else watch()
