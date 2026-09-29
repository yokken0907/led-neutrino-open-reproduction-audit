# SUPERSEDED - historical runner only; not the manuscript-facing entry point.
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$ROOT/results/figure1}"
mkdir -p "$OUT"
python "$ROOT/code/d29a_figure1_replication.py" --outdir "$OUT"
python "$ROOT/code/d29b_conditioning_validation.py"   --d29a-result "$OUT/D29A_RESULT.json"   --roots-dir "$OUT"   --out "$OUT/D29B_RESULT.json"
python - <<PY2
import json
from pathlib import Path
out=Path(r"$OUT")
a=json.loads((out/'D29A_RESULT.json').read_text())
b=json.loads((out/'D29B_RESULT.json').read_text())
print('D29A automatic verdict:', a['verdict'])
print('D29B corrected verdict:', b['verdict'])
assert b['verdict']=='PASS_FIGURE1_COMPUTATIONAL_CORE_INDEPENDENT_REPLICATION_AFTER_CONDITIONING_AUDIT', b
print('FIGURE1_REPLICATION_ONE_COMMAND_PASS')
PY2
