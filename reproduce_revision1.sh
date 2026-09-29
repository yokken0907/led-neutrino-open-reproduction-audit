#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$ROOT/results/revision1}"
SCOAP3_RECORD="107173"
SCOAP3_API="https://repo.scoap3.org/api/records/$SCOAP3_RECORD"

rm -rf "$OUT"
mkdir -p "$OUT/figure1" "$OUT/d29c" "$OUT/d30a" "$OUT/d30b" "$OUT/target"

echo "[1/9] Reproduce original Figure-1 numerical core (D29A/D29B)"
bash "$ROOT/reproduce_figure1.sh" "$OUT/figure1"

echo "[2/9] Validate all 3552 roots directly at 80-digit precision (D29C)"
python "$ROOT/code/d29c_all_root_80digit_direct_validation.py"   --input-dir "$OUT/figure1" --outdir "$OUT/d29c" --self-test
python "$ROOT/code/d29c_all_root_80digit_direct_validation.py"   --input-dir "$OUT/figure1" --outdir "$OUT/d29c"

echo "[3/9] Acquire the published article from the SCOAP3 open repository"
PDF="$OUT/target/JHEP05_2026_152_SCOAP3.pdf"
META="$OUT/target/SCOAP3_RECORD_107173.json"
curl -fL --retry 3 --retry-delay 2 "$SCOAP3_API" -o "$META"
readarray -t PDF_INFO < <(python - "$META" <<'PY'
import json,sys
m=json.load(open(sys.argv[1]))
entries=m.get('files',{}).get('entries',{})
cand=[]
for name,e in entries.items():
    if name.lower().endswith('.pdf'):
        cand.append((name,e.get('links',{}).get('content'),e.get('checksum','')))
if not cand:
    print('SCOAP3_SCHEMA_DEBUG='+json.dumps(m,sort_keys=True))
    raise SystemExit('SCOAP3_RECORD_HAS_NO_PDF')
cand.sort(key=lambda q:(0 if ('pdfa' in q[0].lower() or 'pdf-a' in q[0].lower()) else 1,q[0]))
name,url,checksum=cand[0]
if not url:
    raise SystemExit('SCOAP3_PDF_CONTENT_LINK_MISSING')
print(name); print(url); print(checksum)
PY
)
PDF_NAME="${PDF_INFO[0]}"
PDF_URL="${PDF_INFO[1]}"
PDF_CHECKSUM="${PDF_INFO[2]}"
echo "SCOAP3_PDF_NAME=$PDF_NAME"
echo "SCOAP3_PDF_CHECKSUM=$PDF_CHECKSUM"
curl -fL --retry 3 --retry-delay 2 "$PDF_URL" -o "$PDF"
python - "$PDF" "$PDF_CHECKSUM" <<'PY'
from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); spec=sys.argv[2]
if ':' not in spec:
    raise SystemExit(f'UNSUPPORTED_SCOAP3_CHECKSUM {spec!r}')
alg,expected=spec.split(':',1)
if alg not in hashlib.algorithms_available:
    raise SystemExit(f'UNSUPPORTED_SCOAP3_CHECKSUM_ALGORITHM {alg}')
h=hashlib.new(alg); h.update(p.read_bytes())
actual=h.hexdigest()
if actual.lower()!=expected.lower():
    raise SystemExit(f'SCOAP3_CHECKSUM_MISMATCH expected={spec} actual={alg}:{actual}')
print('SCOAP3_SOURCE_CHECKSUM_PASS')
PY
PDF_SHA="$(sha256sum "$PDF" | awk '{print $1}')"
echo "$PDF_SHA  $(basename "$PDF")" > "$OUT/target/TARGET_PDF_SHA256.txt"
echo "TARGET_PDF_SHA256=$PDF_SHA"

echo "[4/9] Run D30A static regression tests"
python "$ROOT/tests/test_d30a_static.py"

echo "[5/9] Direct target-output validation against published Figure 1 (D30A)"
python "$ROOT/code/d30a_figure1_direct_output_validation.py"   --pdf "$PDF" --outdir "$OUT/d30a"

echo "[6/9] Freeze the exact fresh D30A source directory for D30B provenance"
python - "$OUT/d30a" "$OUT/D30A_SOURCE.zip" <<'PY'
from pathlib import Path
import sys, zipfile
src=Path(sys.argv[1]); dst=Path(sys.argv[2])
with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(src.rglob('*')):
        if p.is_file():
            z.write(p,arcname='d30a/'+str(p.relative_to(src)))
PY
SRC_SHA="$(sha256sum "$OUT/D30A_SOURCE.zip" | awk '{print $1}')"
printf '%s  %s\n' "$SRC_SHA" "D30A_SOURCE.zip" > "$OUT/D30A_SOURCE.zip.sha256"

echo "[7/9] Run D30B static regression tests"
python "$ROOT/tests/test_d30b_static.py"

echo "[8/9] Adjudicate the two D30A overplot/occlusion contradictions (D30B)"
python "$ROOT/code/d30b_occlusion_adjudication.py"   --run-dir "$OUT/d30a"   --source-zip "$OUT/D30A_SOURCE.zip"   --expected-source-sha "$SRC_SHA"   --outdir "$OUT/d30b"

echo "[9/9] Apply bounded Revision-1 manuscript gates"
python - "$OUT" "$PDF_SHA" <<'PY'
from pathlib import Path
import json, sys
out=Path(sys.argv[1]); expected_pdf_sha=sys.argv[2]
a=json.loads((out/'figure1'/'D29A_RESULT.json').read_text())
b=json.loads((out/'figure1'/'D29B_RESULT.json').read_text())
c=json.loads((out/'d29c'/'D29C_RESULT.json').read_text())
d=json.loads((out/'d30a'/'D30A_RESULT.json').read_text())
e=json.loads((out/'d30b'/'D30B_RESULT.json').read_text())

assert a['verdict']=='FAIL_FIGURE1_COMPUTATIONAL_CORE_REPLICATION_GATE'
assert all(x['pass'] for x in a['triangulation'])
assert all(v['sum_Nlambda2']>0.99 for v in a['unitarity'].values())

assert b['verdict']=='PASS_FIGURE1_COMPUTATIONAL_CORE_INDEPENDENT_REPLICATION_AFTER_CONDITIONING_AUDIT'
assert b['root_count_checked']==3552
assert b['all_within_requested_solver_tolerance'] is True

assert c['verdict']=='PASS_D29C_ALL_3552_ROOTS_HIGH_PRECISION_DIRECT_VALIDATION'
assert c['root_count_checked']==3552
assert c['primary_binary64_statistics']['all_within_solver_tolerance'] is True
assert c['primary_binary64_statistics']['max_ratio'] < 1.0

assert d['target']['pdf_sha256']==expected_pdf_sha
assert d['axis_cross_dpi']['pass'] is True
assert d['verdict']=='FAIL_DIRECT_TARGET_OUTPUT_DISAGREEMENT'
mismatch=sorted(f"{x['mu1']}|{x['n']}" for x in d['anchors'] if x['status']=='ROBUST_MISMATCH')
assert mismatch==['10.0|10','10.0|5'], mismatch
coverage=d['coverage_robust_match_count_by_mu1']
assert coverage=={'10.0':3,'1.0':5,'0.1':4}, coverage
insufficient=sorted(f"{x['mu1']}|{x['n']}" for x in d['anchors'] if x['status']=='INSUFFICIENT_GRAPHICAL_SUPPORT')
assert insufficient==['0.1|20'], insufficient

assert e['verdict']=='PASS_D30B_OCCLUSION_ARTIFACT_CONFIRMED'
for n in ('5','10'):
    assert e['summary_by_n'][n]['robust_registration_pass'] is True
    assert e['summary_by_n'][n]['robust_occlusion_signature'] is True

combined={
  '10.0': coverage['10.0']+2,
  '1.0': coverage['1.0'],
  '0.1': coverage['0.1'],
}
assert combined=={'10.0':5,'1.0':5,'0.1':4}
result={
  'phase':'RESCIENCE_REVISION1_PUBLIC_REPRODUCTION',
  'bounded_verdict':'PASS_RESCIENCE_REVISION1_FIGURE1_PARTIAL_REPLICATION_GATES',
  'D29A_frozen_verdict':a['verdict'],
  'D29B_verdict':b['verdict'],
  'D29C_verdict':c['verdict'],
  'D30A_frozen_machine_verdict':d['verdict'],
  'D30B_verdict':e['verdict'],
  'combined_supported_anchor_count_by_mu1':combined,
  'remaining_insufficient_graphical_support':insufficient,
  'target_pdf_sha256':expected_pdf_sha,
  'claim_boundary':{
    'successful_replication':'Figure 1 Brane-Dirac spectrum subset only',
    'figure5_replication_claimed':False,
    'target_author_likelihood_reproduced':False,
    'new_LED_signal_claimed':False,
    'error_in_original_article_claimed':False
  }
}
(out/'REVISION1_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
print('REVISION1_REPRODUCTION_CI_PASS')
PY
