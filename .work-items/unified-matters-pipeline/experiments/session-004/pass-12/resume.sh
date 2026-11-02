#!/usr/bin/env bash
# Resume after the preserved provider schema-size rejection; do not repeat valid earlier stages.
set -uo pipefail
D=.work-items/unified-matters-pipeline/experiments/session-004/pass-12
R=$D/run12.py; L=$D/generation.log
run() { echo "=== $*" >> "$L"; .venv/bin/python "$R" "$@" >> "$L" 2>&1 || { echo "FAILED: $*" >> "$L"; exit 1; }; }
echo "RESUME: compact per-kind classification schema; previous provider failure preserved" >> "$L"
run step3 --session 001 --scenes s001-step1 --threads s001-step2 --out s001-step3
run check --session 001 --run s001-step3
run chain s001
run seed s001 002
run step1 --session 002 --out s002-step1
run step2 --session 002 --scenes s002-step1 --out s002-step2
run step2c --session 002 --scenes s002-step1 --threads s002-step2 --out s002-step2c
run step3 --session 002 --scenes s002-step1 --threads s002-step2 --out s002-step3
run check --session 002 --run s002-step3
run chain s002
date -u +%FT%TZ >> "$L"
echo "ALL DONE" >> "$L"
