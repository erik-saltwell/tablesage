#!/usr/bin/env bash
# Generate pass 12 Sessions 001-002 in order, stopping at the first failure. Run from the repository root.
set -uo pipefail
D=.work-items/unified-matters-pipeline/experiments/session-004/pass-12
R=$D/run12.py; L=$D/generation.log
date -u +%FT%TZ > "$L"
run() { echo "=== $*" >> "$L"; .venv/bin/python "$R" "$@" >> "$L" 2>&1 || { echo "FAILED: $*" >> "$L"; exit 1; }; }
for S in 001 002; do
  run step1 --session $S --out s$S-step1
  run step2 --session $S --scenes s$S-step1 --out s$S-step2
  run step2c --session $S --scenes s$S-step1 --threads s$S-step2 --out s$S-step2c
  run step3 --session $S --scenes s$S-step1 --threads s$S-step2 --out s$S-step3
  run check --session $S --run s$S-step3
  run chain s$S
  [ $S = 001 ] && run seed s001 002
done
date -u +%FT%TZ >> "$L"; echo "ALL DONE" >> "$L"
