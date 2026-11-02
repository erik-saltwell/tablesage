#!/usr/bin/env bash
set -euo pipefail
D=.work-items/unified-matters-pipeline/experiments/session-004/pass-12
R=$D/run12.py
L=$D/generation.log
run() { echo "=== $*" >> "$L"; .venv/bin/python "$R" "$@" >> "$L" 2>&1; }
echo "TARGETED RETRY: Session 002 thread_2; unchanged prompt and inputs" >> "$L"
run step3 --session 002 --scenes s002-step1 --threads s002-step2 --out s002-step3 --only thread_2
.venv/bin/python /tmp/tablesage-reassemble-pass12.py >> "$L" 2>&1
run check --session 002 --run s002-step3
run chain s002
date -u +%FT%TZ >> "$L"
echo "ALL DONE" >> "$L"
