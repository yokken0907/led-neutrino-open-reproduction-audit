#!/usr/bin/env bash
set -u -o pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON312:-python3.12}"
STAMP="$(date +%Y%m%dT%H%M%S)"
OUT="$ROOT/results/RUN_$STAMP"
mkdir -p "$OUT"/{d25g,d26c1,logs,env}

for req in   "$ROOT/code/fetch_public_inputs.py"   "$ROOT/code/compare_results.py"   "$ROOT/environment/requirements-led-exact.txt"   "$ROOT/environment/requirements-public-exact.txt"   "$ROOT/expected/D25G_R2_RESULT.json"   "$ROOT/expected/D26C1_RESULT.json"; do
  [[ -f "$req" ]] || { echo "ERROR: repository layout check failed; missing $req" >&2; exit 2; }
done

finalize_result_bundle(){
  local out="$1"
  local parent base
  parent="$(dirname "$out")"
  base="$(basename "$out")"
  (
    cd "$parent"
    rm -f "${base}.zip" "${base}.zip.sha256"
    zip -qr "${base}.zip" "$base"
    sha256sum "${base}.zip" > "${base}.zip.sha256"
  )
  echo "Result ZIP: ${out}.zip"
  echo "Result SHA sidecar: ${out}.zip.sha256"
}

fail(){
  echo "ERROR: $*" >&2
  echo "$*" > "$OUT/FAILURE.txt"
  if [[ -d "$OUT" ]]; then
    (
      cd "$OUT"
      find . -type f ! -name SHA256SUMS.txt ! -name INTEGRITY_VERIFY.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt 2>/dev/null || true
      sha256sum -c SHA256SUMS.txt > INTEGRITY_VERIFY.txt 2>&1 || true
    )
    finalize_result_bundle "$OUT" || true
  fi
  exit 2
}

command -v "$PY" >/dev/null 2>&1 || fail "Python 3.12 is required (set PYTHON312 if needed)."

"$PY" "$ROOT/code/fetch_public_inputs.py" >"$OUT/logs/fetch_inputs.txt" 2>&1 || fail "public input acquisition failed"

VBASE="$ROOT/.repro_venvs"
LED="$VBASE/led"
PUB="$VBASE/public"
rm -rf "$VBASE"
"$PY" -m venv "$LED" || fail "LED venv creation failed"
"$PY" -m venv "$PUB" || fail "public venv creation failed"

"$LED/bin/python" -m pip install --upgrade pip >"$OUT/logs/led_install.txt" 2>&1 || fail "LED pip upgrade failed"
"$LED/bin/python" -m pip install -r "$ROOT/environment/requirements-led-exact.txt" >>"$OUT/logs/led_install.txt" 2>&1 || fail "LED dependency installation failed"

"$PUB/bin/python" -m pip install --upgrade pip >"$OUT/logs/public_install.txt" 2>&1 || fail "public pip upgrade failed"
"$PUB/bin/python" -m pip install -r "$ROOT/environment/requirements-public-exact.txt" >>"$OUT/logs/public_install.txt" 2>&1 || fail "public dependency installation failed"

"$LED/bin/python" - <<'PY' > "$OUT/env/led_versions.txt"
import sys,numpy,scipy
print(sys.version)
print("numpy",numpy.__version__)
print("scipy",scipy.__version__)
PY

"$PUB/bin/python" - <<'PY' > "$OUT/env/public_versions.txt"
import sys, importlib.metadata as im
print(sys.version)
for p in ["numpy","scipy","dayabay-model","dayabay-data-official","dgm-reactor-neutrino","dag-modelling","dgm-fit","iminuit"]:
    print(p, im.version(p))
PY

# D26C1 exits non-zero by scientific design because the frozen scientific gate FAILS.
D26RC=0
"$PUB/bin/python" "$ROOT/code/d26c1_clean_standard3nu_calibration.py" \
  --surface "$ROOT/inputs/d26c1/DayaBay_DeltaChiSq_NO_3158days.txt" \
  --out "$OUT/d26c1" >"$OUT/logs/d26c1_stdout.txt" 2>"$OUT/logs/d26c1_stderr.txt" || D26RC=$?
[[ -f "$OUT/d26c1/D26C1_RESULT.json" ]] || fail "D26C1 did not produce D26C1_RESULT.json (rc=$D26RC)"

PYTHONPATH="$ROOT/code" "$LED/bin/python" "$ROOT/code/d25g_r2_published_neighborhood_topology.py" \
  --anchor "$ROOT/inputs/d25g/FROZEN_ANCHOR.json" \
  --authority-sources "$ROOT/inputs/d25g/authority_sources" \
  --out "$OUT/d25g" >"$OUT/logs/d25g_stdout.txt" 2>"$OUT/logs/d25g_stderr.txt" || fail "D25G execution failed"

CMPRC=0
"$PY" "$ROOT/code/compare_results.py" \
  --d25g "$OUT/d25g/D25G_R2_RESULT.json" \
  --d26c1 "$OUT/d26c1/D26C1_RESULT.json" \
  --out "$OUT/D27B_COMPARISON.json" || CMPRC=$?

if [[ "$CMPRC" -eq 0 ]]; then
  STATUS="PUBLIC_REPOSITORY_REPRODUCTION_PASS"
else
  STATUS="HOLD_REPRODUCIBILITY_NO_SUBMISSION"
fi

"$PY" - "$OUT" "$STATUS" "$D26RC" <<'PY'
from pathlib import Path
import json,sys
o=Path(sys.argv[1])
(o/"manifest.json").write_text(json.dumps({
  "bundle":"D27B_PUBLIC_REPOSITORY_RUN",
  "status":sys.argv[2],
  "d26c1_process_return_code":int(sys.argv[3]),
  "note":"D26C1 non-zero process status is expected when its frozen scientific gate remains FAIL; reproducibility is judged by compare_results.py."
},indent=2)+"\n")
PY

(
  cd "$OUT"
  find . -type f ! -name SHA256SUMS.txt ! -name INTEGRITY_VERIFY.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt
  sha256sum -c SHA256SUMS.txt > INTEGRITY_VERIFY.txt
)

finalize_result_bundle "$OUT"

echo "$STATUS"
echo "Result directory: $OUT"
[[ "$CMPRC" -eq 0 ]]
