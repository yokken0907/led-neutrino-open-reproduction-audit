#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$ROOT/results/figure1-revision2}"
rm -rf "$OUT"
mkdir -p "$OUT"

echo "[1/4] numerical Figure-1 reproduction"
python "$ROOT/code/d29a_figure1_replication.py" --outdir "$OUT/numerical"
python "$ROOT/code/d29b_conditioning_validation.py" --d29a-result "$OUT/numerical/D29A_RESULT.json" --roots-dir "$OUT/numerical" --out "$OUT/numerical/D29B_RESULT.json"
python "$ROOT/code/d29c_all_root_high_precision.py" --roots-dir "$OUT/numerical" --out "$OUT/numerical/D29C_RESULT.json"

echo "[2/4] published Figure-1 graphical validation from version-of-record PDF"
python "$ROOT/code/run_graphical_validation_revision2.py" --repo-root "$ROOT" --outdir "$OUT/graphical"

echo "[3/4] bounded result checks"
python - <<PY
import json
from pathlib import Path
p=Path(r"$OUT")
a=json.loads((p/"numerical/D29A_RESULT.json").read_text())
b=json.loads((p/"numerical/D29B_RESULT.json").read_text())
c=json.loads((p/"numerical/D29C_RESULT.json").read_text())
g=json.loads((p/"graphical/GRAPHICAL_VALIDATION_SUMMARY.json").read_text())
assert a["verdict"]=="FAIL_FIGURE1_COMPUTATIONAL_CORE_REPLICATION_GATE"
assert b["verdict"]=="PASS_FIGURE1_COMPUTATIONAL_CORE_INDEPENDENT_REPLICATION_AFTER_CONDITIONING_AUDIT"
assert c["verdict"]=="PASS_D29C_ALL_3552_ROOTS_HIGH_PRECISION_DIRECT_VALIDATION"
assert g["verdict"]=="PASS_FULL_PUBLIC_GRAPHICAL_REPRODUCTION"
print("Figure-1 numerical and graphical validations passed.")
PY

echo "[4/4] complete"
echo "FIGURE1_REVISION2_REPRODUCTION_PASS"
