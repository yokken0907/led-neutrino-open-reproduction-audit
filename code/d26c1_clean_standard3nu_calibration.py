#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, json, math, subprocess, sys
import numpy as np
from scipy.stats import spearmanr

PUBLIC_S=0.0854238209633967
PUBLIC_D=0.0024708320336013817
PUBLIC_FUN=557.9755550235543
LEVELS=[2.30,6.18,11.83]
GATE={
    "profiled_public_best_abs_chi2_difference_max":0.01,
    "official_delta_at_public_best_max":2.30,
    "profiled_delta_at_official_best_max":2.30,
    "spearman_rho_min":0.95,
    "median_abs_delta_difference_max":1.00,
    "p90_abs_delta_difference_max":3.00,
    "diagnostic_anchor_count_min":20,
}
HERE=Path(__file__).resolve().parent

def parse_surface(path):
    raw=np.loadtxt(path,comments="#")
    sx=np.unique(raw[:,0]); dm=np.unique(raw[:,1])
    grid=np.full((len(dm),len(sx)),np.nan)
    ii={float(v):i for i,v in enumerate(dm)}
    jj={float(v):j for j,v in enumerate(sx)}
    for s,d,y in raw:
        grid[ii[float(d)],jj[float(s)]]=float(y)
    if np.isnan(grid).any():
        raise RuntimeError("incomplete official surface")
    ij=np.unravel_index(np.argmin(grid),grid.shape)
    best={"sin22theta13":float(sx[ij[1]]),"dm32_eV2":float(dm[ij[0]]),
          "delta_chi2":float(grid[ij])}
    return sx,dm,grid,best

def interp(sx,dm,grid,s,d):
    j=np.searchsorted(sx,s);i=np.searchsorted(dm,d)
    j=max(1,min(j,len(sx)-1));i=max(1,min(i,len(dm)-1))
    s0,s1=sx[j-1],sx[j];d0,d1=dm[i-1],dm[i]
    tx=(s-s0)/(s1-s0);ty=(d-d0)/(d1-d0)
    return float((1-tx)*(1-ty)*grid[i-1,j-1]+tx*(1-ty)*grid[i-1,j]+
                 (1-tx)*ty*grid[i,j-1]+tx*ty*grid[i,j])

def choose_anchors(sx,dm,grid,best):
    s0=best["sin22theta13"];d0=best["dm32_eV2"]
    ss=sx[-1]-sx[0];dd=dm[-1]-dm[0]
    out=[]
    for level in LEVELS:
        cand=[]
        for i,d in enumerate(dm):
            for j,s in enumerate(sx):
                y=float(grid[i,j])
                ang=math.atan2((d-d0)/dd,(s-s0)/ss)
                cand.append((abs(y-level),ang,float(s),float(d),y))
        for k in range(8):
            lo=-math.pi+k*2*math.pi/8
            hi=-math.pi+(k+1)*2*math.pi/8
            sec=[x for x in cand if lo<=x[1]<(hi if k<7 else math.pi+1e-12)]
            x=min(sec,key=lambda t:t[0])
            out.append({"target_level":level,"sector":k,"sin22theta13":x[2],
                        "dm32_eV2":x[3],"official_delta_chi2":x[4]})
    uniq={}
    for a in out:uniq[(a["sin22theta13"],a["dm32_eV2"])]=a
    return list(uniq.values())

def run_point(py,worker,outdir,label,s,d):
    p=outdir/f"{label}.json"
    cmd=[py,str(worker),"--sin22",repr(float(s)),"--dm32",repr(float(d)),"--out",str(p)]
    rr=subprocess.run(cmd,text=True,capture_output=True)
    (outdir/f"{label}.stdout.txt").write_text(rr.stdout)
    (outdir/f"{label}.stderr.txt").write_text(rr.stderr)
    if rr.returncode!=0:
        raise RuntimeError(f"{label} worker rc={rr.returncode}: {rr.stderr[-2000:]}")
    return json.loads(p.read_text())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--surface",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    points=out/"points";points.mkdir()
    sx,dm,grid,official_best=parse_surface(Path(a.surface))
    anchors=choose_anchors(sx,dm,grid,official_best)
    if len(anchors)!=24: raise RuntimeError(len(anchors))

    py=sys.executable
    worker=HERE/"worker_profile_point.py"

    # Strict invariant: profile at public best must reproduce public global fit.
    pbest=run_point(py,worker,points,"public_best",PUBLIC_S,PUBLIC_D)
    baseline=float(pbest["chi2"])
    public_abs_diff=abs(baseline-PUBLIC_FUN)

    obest=run_point(py,worker,points,"official_best",
                    official_best["sin22theta13"],official_best["dm32_eV2"])

    rows=[]
    for i,a0 in enumerate(anchors,1):
        r=run_point(py,worker,points,f"anchor_{i:02d}",
                    a0["sin22theta13"],a0["dm32_eV2"])
        rec=dict(a0)
        rec["profiled_chi2"]=r["chi2"]
        rec["profiled_delta_chi2"]=float(r["chi2"]-baseline)
        rec["abs_delta_difference"]=abs(rec["profiled_delta_chi2"]-rec["official_delta_chi2"])
        rec["fit_success"]=r["success"]
        rec["fit_nfev"]=r["nfev"]
        rows.append(rec)
        (out/"D26C1_PROGRESS.json").write_text(json.dumps({
            "completed":i,"total":len(anchors),"current":rec
        },indent=2))
        print(f"[anchor] {i}/24 official={rec['official_delta_chi2']:.4f} "
              f"profiled={rec['profiled_delta_chi2']:.4f} diff={rec['abs_delta_difference']:.4f}",
              flush=True)

    off=np.array([r["official_delta_chi2"] for r in rows])
    pro=np.array([r["profiled_delta_chi2"] for r in rows])
    dif=np.abs(pro-off)
    rho=float(spearmanr(off,pro).statistic)

    metrics={
        "profiled_public_best_chi2":baseline,
        "public_reference_chi2":PUBLIC_FUN,
        "profiled_public_best_abs_chi2_difference":public_abs_diff,
        "official_delta_at_public_best":interp(sx,dm,grid,PUBLIC_S,PUBLIC_D),
        "profiled_delta_at_official_best":float(obest["chi2"]-baseline),
        "spearman_rho":rho,
        "median_abs_delta_difference":float(np.median(dif)),
        "p90_abs_delta_difference":float(np.quantile(dif,0.90)),
        "diagnostic_anchor_count":len(rows),
        "all_anchor_fits_success":all(r["fit_success"] for r in rows),
    }
    gates={
        "profiled_public_best_abs_chi2_difference":"PASS" if metrics["profiled_public_best_abs_chi2_difference"]<=GATE["profiled_public_best_abs_chi2_difference_max"] else "FAIL",
        "official_delta_at_public_best":"PASS" if metrics["official_delta_at_public_best"]<=GATE["official_delta_at_public_best_max"] else "FAIL",
        "profiled_delta_at_official_best":"PASS" if metrics["profiled_delta_at_official_best"]<=GATE["profiled_delta_at_official_best_max"] else "FAIL",
        "spearman_rho":"PASS" if rho>=GATE["spearman_rho_min"] else "FAIL",
        "median_abs_delta_difference":"PASS" if metrics["median_abs_delta_difference"]<=GATE["median_abs_delta_difference_max"] else "FAIL",
        "p90_abs_delta_difference":"PASS" if metrics["p90_abs_delta_difference"]<=GATE["p90_abs_delta_difference_max"] else "FAIL",
        "diagnostic_anchor_count":"PASS" if len(rows)>=GATE["diagnostic_anchor_count_min"] else "FAIL",
        "all_anchor_fits_success":"PASS" if metrics["all_anchor_fits_success"] else "FAIL",
    }
    passed=all(v=="PASS" for v in gates.values())
    verdict=("PASS_CLEAN_PUBLIC_DAYABAY_STANDARD3NU_CALIBRATION"
             if passed else "FAIL_CLEAN_PUBLIC_DAYABAY_STANDARD3NU_CALIBRATION")
    next_status=("GO_D26C2_N6_LED_OPEN_BENCHMARK"
                 if passed else "CLOSE_REACTOR_CALIBRATION_BRANCH")

    doc={
        "phase":"D26C1_CLEAN_DAYABAY_STANDARD3NU_CALIBRATION",
        "method":{
            "fresh_subprocess_per_point":True,
            "old_D25_imports":False,
            "R2_imports":False,
            "parameter_setting":"model.set_parameters public API",
            "statistic":"outputs.statistic.full.covmat.chi2cnp",
            "profiled_each_point":"19 neutrino_per_fission_factor spectrum-shape parameters",
            "data":"Daya Bay 3158-day public final data",
        },
        "official_best":official_best,
        "public_best":{"sin22theta13":PUBLIC_S,"dm32_eV2":PUBLIC_D,"chi2":PUBLIC_FUN},
        "gates_frozen_before_run":GATE,
        "metrics":metrics,
        "gates":gates,
        "anchors":rows,
        "verdict":verdict,
        "next_status":next_status,
        "claim_control":{
            "LED_computed":False,"KK_modes_used":0,
            "2021_unfolded_spectrum_used_in_this_phase":False,
            "exact_Elacmaz_replay_claimed":False,
            "posthoc_gate_change":False,
            "further_calibration_debug_authorized_after_scientific_fail":False,
        }
    }
    (out/"D26C1_RESULT.json").write_text(json.dumps(doc,indent=2))
    print(json.dumps({"verdict":verdict,"next_status":next_status,
                      "metrics":metrics,"gates":gates},indent=2))
    if not passed: raise SystemExit(3)

if __name__=="__main__":
    main()
