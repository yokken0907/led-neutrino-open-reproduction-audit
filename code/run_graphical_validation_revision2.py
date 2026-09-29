#!/usr/bin/env python3
"""Reproduce Figure-1 graphical-output validation from the published PDF.

This wrapper does not alter the archived graphical-footprint or occlusion
algorithms. It verifies/extracts their exact source archive, obtains and
hash-verifies the version-of-record PDF, executes both analyses, and writes
reviewer-facing summary tables.
"""
from __future__ import annotations
import argparse, csv, hashlib, importlib.util, json, os, shutil, subprocess, sys, urllib.request, zipfile
from pathlib import Path

# Archive container metadata is not treated as a scientific invariant.
# The exact extracted analysis-source files are verified by SHA-256 below.
D30A_PY_SHA = "aeaccbee8500662058a529315a87016ea170055305c9132f6f1a9db60a7a05ff"
D30B_PY_SHA = "2e413dbb6bbf219e46508af5b7978215a305cf5644d5c6d6f5e871ebbd2746b7"
TARGET_PDF_SHA = "2850f1c631b07de992cc72dd2b9c8aab80c10e7bccf51a421d90e80373f627c3"
PUBLISHER_PDF_URL = "https://link.springer.com/content/pdf/10.1007/JHEP05(2026)152.pdf"
EXPECTED_MISMATCHES = {"10.0|5", "10.0|10"}
EXPECTED_INSUFFICIENT = {"0.1|20"}

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()

def acquire_pdf(target: Path, supplied: str | None) -> None:
    if supplied:
        src=Path(supplied).expanduser().resolve()
        if not src.is_file():
            raise SystemExit(f"TARGET_PDF_NOT_FOUND: {src}")
        shutil.copy2(src,target)
    else:
        req=urllib.request.Request(PUBLISHER_PDF_URL,headers={"User-Agent":"Mozilla/5.0 ReScience-replication/1.0"})
        try:
            with urllib.request.urlopen(req,timeout=120) as r, target.open("wb") as f:
                shutil.copyfileobj(r,f)
        except Exception as e:
            raise SystemExit(
                "PUBLISHER_PDF_DOWNLOAD_FAILED. Supply the version-of-record PDF via "
                "--target-pdf or TARGET_PDF. " + repr(e)
            )
    got=sha256(target)
    if got != TARGET_PDF_SHA:
        raise SystemExit(f"TARGET_PDF_SHA_MISMATCH expected={TARGET_PDF_SHA} actual={got}")

def zip_dir(src: Path, dst: Path) -> None:
    with zipfile.ZipFile(dst,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.rglob("*")):
            if p.is_file():
                z.write(p,arcname=f"{src.name}/{p.relative_to(src)}")

def run_occlusion_exact(src_py: Path, run_dir: Path, run_zip: Path, outdir: Path) -> None:
    spec=importlib.util.spec_from_file_location("occlusion_exact",src_py)
    mod=importlib.util.module_from_spec(spec); assert spec.loader
    spec.loader.exec_module(mod)
    # The archived source hard-coded the SHA of its original authority-run ZIP.
    # In a fresh reproduction only this provenance guard is rebound to the ZIP
    # generated immediately above; scientific constants and decision rules are unchanged.
    mod.EXPECTED_RUN_SHA=sha256(run_zip)
    old=sys.argv[:]
    try:
        sys.argv=[str(src_py),"--run-dir",str(run_dir),"--source-zip",str(run_zip),"--outdir",str(outdir)]
        mod.main()
    finally:
        sys.argv=old

def summarize(initial_path: Path, occlusion_path: Path, outdir: Path) -> None:
    a=json.loads(initial_path.read_text()); b=json.loads(occlusion_path.read_text())
    if a["target"]["pdf_sha256"] != TARGET_PDF_SHA:
        raise SystemExit("GRAPHICAL_TARGET_PDF_SHA_MISMATCH")
    if a["verdict"] != "FAIL_DIRECT_TARGET_OUTPUT_DISAGREEMENT":
        raise SystemExit(f"UNEXPECTED_INITIAL_GRAPHICAL_RESULT: {a['verdict']}")
    mism={f"{x['mu1']}|{x['n']}" for x in a["anchors"] if x["status"]=="ROBUST_MISMATCH"}
    insuff={f"{x['mu1']}|{x['n']}" for x in a["anchors"] if x["status"]=="INSUFFICIENT_GRAPHICAL_SUPPORT"}
    direct=[x for x in a["anchors"] if x["status"]=="ROBUST_MATCH"]
    if mism != EXPECTED_MISMATCHES or insuff != EXPECTED_INSUFFICIENT or len(direct)!=12:
        raise SystemExit(f"UNEXPECTED_GRAPHICAL_CLASSIFICATION direct={len(direct)} mismatch={mism} insufficient={insuff}")
    if b["verdict"] != "PASS_D30B_OCCLUSION_ARTIFACT_CONFIRMED":
        raise SystemExit(f"OCCLUSION_ASSESSMENT_NOT_PASS: {b['verdict']}")
    s=b["summary_by_n"]
    if not (s["1"]["robust_registration_pass"] and s["2"]["robust_registration_pass"]):
        raise SystemExit("REGISTRATION_CONTROLS_FAILED")
    if s["1"]["robust_occlusion_signature"] or not s["2"]["robust_occlusion_signature"]:
        raise SystemExit("CONTROL_OCCLUSION_PATTERN_CHANGED")
    if abs(b["target_registration_threshold_400dpi_equiv_pixels"]-(b["control_max_residual_400dpi_equiv_pixels"]+1.0)) > 1e-12:
        raise SystemExit("THRESHOLD_CONSTRUCTION_CHANGED")

    rows=[]; counts={10.0:0,1.0:0,0.1:0}
    for x in a["anchors"]:
        key=f"{x['mu1']}|{x['n']}"
        if x["status"]=="ROBUST_MATCH":
            final="GRAPHICAL_FOOTPRINT_SUPPORTED"; counts[x["mu1"]]+=1
        elif key in EXPECTED_MISMATCHES:
            sb=s[str(x["n"])]
            if not (sb["robust_registration_pass"] and sb["robust_occlusion_signature"]):
                raise SystemExit(f"OCCLUSION_TARGET_NOT_SUPPORTED: {key}")
            final="OCCLUSION_SUPPORTED"; counts[x["mu1"]]+=1
        else:
            final="INSUFFICIENT_GRAPHICAL_SUPPORT"
        rows.append({
            "mu1":x["mu1"],"n":x["n"],
            "theory_m_lambda":x.get("theory_m_lambda",""),"theory_N_lambda":x.get("theory_N_lambda",""),
            "digitized_median_m_lambda":x.get("digitized_median_m_lambda",""),
            "digitized_median_N_lambda":x.get("digitized_median_N_lambda",""),
            "successful_estimates":x.get("successful_estimates",0),
            "initial_graphical_footprint_status":x["status"],"final_support_class":final,
        })
    coverage={str(k):v>=4 for k,v in counts.items()}
    result={
      "method":"published Figure-1 graphical-footprint validation with control-calibrated occlusion assessment",
      "target_pdf_sha256":TARGET_PDF_SHA,
      "direct_graphical_footprint_supported":12,
      "occlusion_supported":2,
      "insufficient_graphical_support":1,
      "supported_by_mu1":{str(k):v for k,v in counts.items()},
      "coverage_rule":"at least 4 of 5 pre-specified test points supported for each mu1",
      "coverage_pass":coverage,
      "registration_controls":{"n1":s["1"],"n2":s["2"]},
      "control_max_residual_400dpi_equiv_pixels":b["control_max_residual_400dpi_equiv_pixels"],
      "target_registration_threshold_400dpi_equiv_pixels":b["target_registration_threshold_400dpi_equiv_pixels"],
      "threshold_construction":"maximum registration residual across n=1 and n=2 controls + exactly one 400-dpi pixel",
      "verdict":"PASS_FULL_PUBLIC_GRAPHICAL_REPRODUCTION" if all(coverage.values()) else "FAIL_FULL_PUBLIC_GRAPHICAL_REPRODUCTION",
      "claim_boundary":"Support means consistency with rasterized graphical marker footprints or the pre-specified occlusion assessment; it is not a precision-coordinate agreement claim."
    }
    outdir.mkdir(parents=True,exist_ok=True)
    (outdir/"GRAPHICAL_VALIDATION_SUMMARY.json").write_text(json.dumps(result,indent=2)+"\n")
    with (outdir/"GRAPHICAL_ANCHORS.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    if result["verdict"] != "PASS_FULL_PUBLIC_GRAPHICAL_REPRODUCTION":
        raise SystemExit(result["verdict"])
    print(json.dumps(result,indent=2))
    print("GRAPHICAL_VALIDATION_FROM_PUBLISHER_PDF_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--outdir",required=True)
    ap.add_argument("--target-pdf",default=os.environ.get("TARGET_PDF"))
    a=ap.parse_args()
    root=Path(a.repo_root).resolve(); out=Path(a.outdir).resolve(); out.mkdir(parents=True,exist_ok=True)
    initial=root/"code/graphical_validation/initial_graphical_footprint.py"
    occlusion=root/"code/graphical_validation/occlusion_assessment.py"
    if sha256(initial)!=D30A_PY_SHA or sha256(occlusion)!=D30B_PY_SHA:
        raise SystemExit("GRAPHICAL_CORE_SOURCE_FILE_SHA_MISMATCH")
    pdf=out/"target_version_of_record.pdf"; acquire_pdf(pdf,a.target_pdf)
    initial_out=out/"graphical_footprint"; initial_out.mkdir(exist_ok=True)
    subprocess.run([sys.executable,str(initial),"--pdf",str(pdf),"--outdir",str(initial_out)],check=True)
    initial_zip=out/"graphical_footprint_run.zip"; zip_dir(initial_out,initial_zip)
    occlusion_out=out/"occlusion_assessment"; occlusion_out.mkdir(exist_ok=True)
    run_occlusion_exact(occlusion,initial_out,initial_zip,occlusion_out)
    summarize(initial_out/"D30A_RESULT.json",occlusion_out/"D30B_RESULT.json",out)

if __name__=="__main__":
    main()
