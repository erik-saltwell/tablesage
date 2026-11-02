#!/usr/bin/env bash
# Generate pass 16 Sessions 001-002 from step 6, on pass 14's copied step 1-5 outputs and seeds, stopping at the
# first failure. Step 5 (code) is recomputed; steps 6 to 8 run fresh, because pass 16 changed step 6's obstacle wording.
# For a split-only comparison on pass 14's writing, use --from 6b instead. Run from the repository root.
set -uo pipefail
D=.work-items/unified-matters-pipeline/experiments/session-004/pass-16
R=$D/run16.py; L=$D/generation.log
date -u +%FT%TZ > "$L"
run() { echo "=== $*" >> "$L"; .venv/bin/python "$R" "$@" >> "$L" 2>&1 || { echo "FAILED: $*" >> "$L"; exit 1; }; }
for S in 001 002; do
  run chain s$S --from 6
done
date -u +%FT%TZ >> "$L"; echo "ALL DONE" >> "$L"
