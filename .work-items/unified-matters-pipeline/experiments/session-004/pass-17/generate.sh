#!/usr/bin/env bash
# Generate pass 17 Sessions 001-002 from step 6, on copied step 1-4 outputs and seeds (pass 16's, which are pass 14's),
# stopping at the first failure. Step 5 (code) is recomputed with the one-item-per-anchor-beat rule; steps 6 to 8 run
# fresh. Run from the repository root.
set -uo pipefail
D=.work-items/unified-matters-pipeline/experiments/session-004/pass-17
R=$D/run17.py; L=$D/generation.log
date -u +%FT%TZ > "$L"
run() { echo "=== $*" >> "$L"; .venv/bin/python "$R" "$@" >> "$L" 2>&1 || { echo "FAILED: $*" >> "$L"; exit 1; }; }
for S in 001 002; do
  run chain s$S --from 6
done
date -u +%FT%TZ >> "$L"; echo "ALL DONE" >> "$L"
