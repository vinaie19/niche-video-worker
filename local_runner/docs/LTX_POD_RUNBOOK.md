# LTX multi-shot pod runbook (LOCKED by youtube expert 2026-09-26)

## Rule
For any multi-shot LTX pass (2→3→4 or 1→4):
1. **Keep the same pod UP** for the entire pass.
2. **No stop/resume between cuts** — model load once.
3. Stop the pod only after remux is handed to video QA, or on HARD/BLOCK stop.
4. Never spin a new pod per shot.

## Anti-pattern (do not repeat)
Looping `ONLY_SHOT=N` via separate `run_test_batch.py` invocations that stop the pod after each shot. That reboots the worker and reloads LTX every cut.

## Preferred
One acquire → render shots in one warm session → remux → hand to video QA → then stop pod.
