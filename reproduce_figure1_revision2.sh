#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$ROOT/results/figure1-revision2}"
mkdir -p "$OUT"

{
  printf 'platform_system='
  python -c 'import platform; print(platform.system())'
  printf 'platform_release='
  python -c 'import platform; print(platform.release())'
  printf 'architecture='
  python -c 'import platform; print(platform.machine())'
  printf 'python_version='
  python -c 'import platform; print(platform.python_version())'
  printf 'python_implementation='
  python -c 'import platform; print(platform.python_implementation())'
} > "$OUT/PLATFORM_INFO.txt"

EXPECTED_PDF_SHA="$(head -n1 "$ROOT/expected/FIGURE1_TARGET_PDF_SHA256.txt" | awk '{print $1}')"
PDF="${FIGURE1_TARGET_PDF:-$OUT/JHEP05_2026_152.pdf}"
if [[ ! -s "$PDF" ]]; then
  curl -fL --retry 3 --retry-delay 2 \
    'https://link.springer.com/content/pdf/10.1007/JHEP05(2026)152.pdf' \
    -o "$PDF"
fi
ACTUAL_PDF_SHA="$(sha256sum "$PDF" | awk '{print $1}')"
if [[ "$ACTUAL_PDF_SHA" != "$EXPECTED_PDF_SHA" ]]; then
  echo "Target PDF SHA-256 mismatch" >&2
  echo "expected=$EXPECTED_PDF_SHA" >&2
  echo "actual=$ACTUAL_PDF_SHA" >&2
  echo "Set FIGURE1_TARGET_PDF=/path/to/the exact version-of-record PDF if the publisher changes transport bytes." >&2
  exit 20
fi
printf '%s  %s\n' "$ACTUAL_PDF_SHA" "$PDF" > "$OUT/TARGET_PDF_SHA256.txt"

# Equation-level replication and all-root high-precision validation.
python "$ROOT/code/d29a_figure1_replication.py" --outdir "$OUT/numerical"
python "$ROOT/code/d29b_conditioning_validation.py" --d29a-result "$OUT/numerical/D29A_RESULT.json" --roots-dir "$OUT/numerical" --out "$OUT/numerical/D29B_RESULT.json"
python "$ROOT/code/d29c_all_root_high_precision.py" --roots-dir "$OUT/numerical" --out "$OUT/numerical/D29C_RESULT.json"

# From-scratch published-output graphical validation.
mkdir -p "$OUT/graphical_initial" "$OUT/graphical_occlusion" "$OUT/graphical_summary"
python "$ROOT/code/graphical_validation/figure1_graphical_validation.py" --pdf "$PDF" --outdir "$OUT/graphical_initial"
python "$ROOT/code/graphical_validation/figure1_occlusion_validation.py" --run-dir "$OUT/graphical_initial" --outdir "$OUT/graphical_occlusion"
python "$ROOT/code/graphical_validation/summarize_graphical_validation.py" \
  --initial "$OUT/graphical_initial/D30A_RESULT.json" \
  --occlusion "$OUT/graphical_occlusion/D30B_RESULT.json" \
  --outdir "$OUT/graphical_summary"

python - <<PY
import json
from pathlib import Path
p=Path(r"$OUT")
a=json.loads((p/'numerical/D29A_RESULT.json').read_text())
b=json.loads((p/'numerical/D29B_RESULT.json').read_text())
c=json.loads((p/'numerical/D29C_RESULT.json').read_text())
g=json.loads((p/'graphical_summary/GRAPHICAL_VALIDATION_SUMMARY.json').read_text())
assert a['verdict']=='FAIL_FIGURE1_COMPUTATIONAL_CORE_REPLICATION_GATE'
assert b['verdict']=='PASS_FIGURE1_COMPUTATIONAL_CORE_INDEPENDENT_REPLICATION_AFTER_CONDITIONING_AUDIT'
assert c['verdict']=='PASS_D29C_ALL_3552_ROOTS_HIGH_PRECISION_DIRECT_VALIDATION'
assert g['verdict']=='PASS_END_TO_END_GRAPHICAL_OUTPUT_VALIDATION'
print('FIGURE1_REVISION2_END_TO_END_REPRODUCTION_PASS')
PY