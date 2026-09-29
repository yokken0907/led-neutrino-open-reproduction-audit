#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$ROOT/results/figure1-revision1}"
mkdir -p "$OUT"
python "$ROOT/code/d29a_figure1_replication.py" --outdir "$OUT"
python "$ROOT/code/d29b_conditioning_validation.py" --d29a-result "$OUT/D29A_RESULT.json" --roots-dir "$OUT" --out "$OUT/D29B_RESULT.json"
python "$ROOT/code/d29c_all_root_high_precision.py" --roots-dir "$OUT" --out "$OUT/D29C_RESULT.json"
python "$ROOT/code/d30c_revision1_evidence_check.py" --anchors "$ROOT/expected/D30_DIRECT_OUTPUT_ANCHORS.csv" --occlusion "$ROOT/expected/D30_OCCLUSION_ADJUDICATION.csv" --out "$OUT/D30C_RESULT.json"
python - <<PY
import json
from pathlib import Path
p=Path(r"$OUT")
a=json.loads((p/'D29A_RESULT.json').read_text())
b=json.loads((p/'D29B_RESULT.json').read_text())
c=json.loads((p/'D29C_RESULT.json').read_text())
d=json.loads((p/'D30C_RESULT.json').read_text())
assert a['verdict']=='FAIL_FIGURE1_COMPUTATIONAL_CORE_REPLICATION_GATE'
assert b['verdict']=='PASS_FIGURE1_COMPUTATIONAL_CORE_INDEPENDENT_REPLICATION_AFTER_CONDITIONING_AUDIT'
assert c['verdict']=='PASS_D29C_ALL_3552_ROOTS_HIGH_PRECISION_DIRECT_VALIDATION'
assert d['verdict']=='PASS_D30C_FROZEN_DIRECT_OUTPUT_EVIDENCE'
print('FIGURE1_REVISION1_REPRODUCTION_PASS')
PY
