#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse,json,math,time
import numpy as np

import d25f_ref74_newtrinos_bridge as base
from dirac_bulk_kernel import (
    SURPROB_ARG_CONVERSION,
    electron_weights,physical_masses,solve_brane_mD,tower,
)

ORDERING="NO"
M0=0.3
THRESH=base.THRESH
N192=192
N384=384

# Frozen scan design
N192_FULL_N=49
N192_HIGH_N=97
N384_TARGET_N=49
N192_REFINE_ITERS=10
N384_REFINE_ITERS=7
PERSIST_N192=31
PERSIST_N384=17

def precompute_modes(radius,nkk):
    p=base.AUTHORITIES[ORDERING]
    ue2=electron_weights(p["sin22theta12"],p["sin22theta13"])
    phys=physical_masses(M0,p["dm21"],p["dm32abs"],p["nmo"],leading="dm32")
    out=[]
    for u2,mphys in zip(ue2,phys):
        md=solve_brane_mD(float(mphys),float(radius),0.0,int(nkk))
        masses,w=tower(md,float(radius),0.0,int(nkk))
        out.append({
            "u2":float(u2),
            "m2":np.asarray(masses*masses,dtype=float),
            "w":np.asarray(w,dtype=float)
        })
    return out

def pee_cached(E,L,species):
    E=np.asarray(E,dtype=float)
    invE=1.0/E
    phase_pref=SURPROB_ARG_CONVERSION*float(L)*0.5e-3
    amp=np.zeros(E.shape,dtype=np.complex128)
    for s in species:
        amp += s["u2"]*(np.exp(-1j*np.outer(invE,s["m2"])*phase_pref) @ s["w"])
    return np.abs(amp)**2

def expected_cached(data,noosc,radius,nkk):
    species=precompute_modes(radius,nkk)
    total=np.zeros(26,dtype=float)
    for period in base.PERIODS:
        L=base.period_baselines(period)
        invL2=1.0/(L*L)
        probs=np.stack([pee_cached(data["E_nu"],ll,species) for ll in L],axis=0)
        pav=np.sum(probs*invL2[:,None],axis=0)/np.sum(invL2)
        total += noosc[period]*pav
    return total

def standard_logl(data,noosc,pref):
    exp=base.expected_spectrum(data,noosc,ORDERING,"SM")
    logl,_,_=base.gaussian_loglike(data["observed"],exp,data["rel_unc"],data["corr"],pref)
    return float(logl)

def delta(data,noosc,pref,sm,radius,nkk):
    exp=expected_cached(data,noosc,float(radius),int(nkk))
    logl,_,_=base.gaussian_loglike(data["observed"],exp,data["rel_unc"],data["corr"],pref)
    return float(-2.0*(logl-sm))

def sign_class(y):
    if y < THRESH: return "below"
    if y > THRESH: return "above"
    return "equal"

def crossings(rows):
    xs=[]
    for a,b in zip(rows[:-1],rows[1:]):
        fa=a["delta_chi2"]-THRESH
        fb=b["delta_chi2"]-THRESH
        if fa*fb<0:
            xs.append({
                "lo_R_um":a["R_um"],"hi_R_um":b["R_um"],
                "lo_delta_chi2":a["delta_chi2"],"hi_delta_chi2":b["delta_chi2"],
                "direction":"up" if fa<0 and fb>0 else "down"
            })
    return xs

def eval_grid(data,noosc,pref,sm,radii,nkk,stage,out):
    rows=[]
    t0=time.perf_counter()
    for i,r in enumerate(radii,1):
        y=delta(data,noosc,pref,sm,float(r),nkk)
        rec={"R_um":float(r),"x_um_inv":1.0/float(r),"delta_chi2":y,"class":sign_class(y)}
        rows.append(rec)
        (out/"D25G_R2_PROGRESS.json").write_text(json.dumps({
            "stage":stage,"completed":i,"total":len(radii),
            "N":nkk,"current":rec,
            "elapsed_seconds":time.perf_counter()-t0
        },indent=2))
        print(f"[{stage}] {i}/{len(radii)} N={nkk} R={r:.9g} dchi2={y:.6f}",flush=True)
    return rows

def refine(data,noosc,pref,sm,x,nkk,iters):
    lo=float(x["lo_R_um"]); hi=float(x["hi_R_um"])
    ylo=delta(data,noosc,pref,sm,lo,nkk)
    yhi=delta(data,noosc,pref,sm,hi,nkk)
    direction=x["direction"]
    for _ in range(iters):
        mid=math.sqrt(lo*hi)
        ym=delta(data,noosc,pref,sm,mid,nkk)
        if direction=="up":
            if ym>=THRESH: hi=mid; yhi=ym
            else: lo=mid; ylo=ym
        else:
            if ym<THRESH: hi=mid; yhi=ym
            else: lo=mid; ylo=ym
    r=math.sqrt(lo*hi)
    y=delta(data,noosc,pref,sm,r,nkk)
    return {
        "direction":direction,
        "R_um":r,"x_um_inv":1.0/r,"delta_chi2":y,
        "lo_R_um":lo,"hi_R_um":hi,
        "width_fraction":hi/lo-1.0
    }

def merge_rows(*grids):
    d={}
    for g in grids:
        for r in g:
            d[round(r["R_um"],15)]=r
    return [d[k] for k in sorted(d)]

def sequence(xs):
    return [x["direction"] for x in xs]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--anchor",required=True)
    ap.add_argument("--authority-sources",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    anchor=json.loads(Path(a.anchor).read_text())

    data=base.load_authority_data(Path(a.authority_sources))
    noosc=base.reconstruct_noosc(data)
    pref=base.covmat_prefactor()
    sm=standard_logl(data,noosc,pref)

    r_custom=float(anchor["custom_R_um"])
    r_pub=float(anchor["published_R_um"])

    # N192: broad bracket + dense published-neighborhood window.
    full=np.geomspace(r_custom,r_pub,N192_FULL_N)
    high_lo=0.01730
    high=np.linspace(high_lo,r_pub,N192_HIGH_N)
    g192_full=eval_grid(data,noosc,pref,sm,full,N192,"N192_FULL",out)
    g192_high=eval_grid(data,noosc,pref,sm,high,N192,"N192_HIGH",out)
    g192=merge_rows(g192_full,g192_high)
    x192=crossings(g192)
    r192=[refine(data,noosc,pref,sm,x,N192,N192_REFINE_ITERS) for x in x192]

    # N384: targeted window chosen before this run from archived N384 crossings.
    n384_lo=0.01730
    n384_hi=r_pub
    grid384=np.linspace(n384_lo,n384_hi,N384_TARGET_N)
    g384=eval_grid(data,noosc,pref,sm,grid384,N384,"N384_TARGET",out)
    x384=crossings(g384)
    r384=[refine(data,noosc,pref,sm,x,N384,N384_REFINE_ITERS) for x in x384]

    # Persistence after the final upward crossing, independently for each N.
    def persistence(refined,nkk,npts,label):
        ups=[x for x in refined if x["direction"]=="up"]
        if not ups:
            return {"available":False}
        last=ups[-1]
        start=last["hi_R_um"]*(1+1e-6)
        if start>=r_pub:
            return {"available":True,"last_up":last,"below_count":0,"min_delta_chi2":None,"rows":[]}
        rs=np.linspace(start,r_pub,npts)
        rows=eval_grid(data,noosc,pref,sm,rs,nkk,label,out)
        return {
            "available":True,
            "last_up":last,
            "below_count":sum(r["delta_chi2"]<THRESH for r in rows),
            "min_delta_chi2":min(r["delta_chi2"] for r in rows),
            "rows":rows
        }

    p192=persistence(r192,N192,PERSIST_N192,"N192_PERSIST")
    p384=persistence(r384,N384,PERSIST_N384,"N384_PERSIST")

    # Strict topology classification: same number and same crossing-direction sequence.
    topology_same=(len(r192)==len(r384) and sequence(r192)==sequence(r384))
    persistence_both=(p192.get("available") and p384.get("available") and
                      p192.get("below_count")==0 and p384.get("below_count")==0)

    if topology_same and persistence_both:
        verdict="TOPOLOGY_STABLE_PERSISTENT_FRONTIER_IDENTIFIED"
    else:
        verdict="TOPOLOGY_N_DEPENDENT_HOLD"

    doc={
        "phase":"D25G_R2_PUBLISHED_NEIGHBORHOOD_TOPOLOGY",
        "anchor":{
            "ordering":ORDERING,"m_lightest_eV":M0,
            "published_R_um":r_pub,"published_x_um_inv":float(anchor["published_x_um_inv"]),
            "custom_R_um":r_custom,"custom_x_um_inv":float(anchor["custom_x_um_inv"])
        },
        "scan_design":{
            "N192_full_points":N192_FULL_N,
            "N192_high_points":N192_HIGH_N,
            "N192_high_lo_R_um":high_lo,
            "N384_target_points":N384_TARGET_N,
            "N384_target_lo_R_um":n384_lo,
            "N384_target_hi_R_um":n384_hi,
            "N192_refine_iters":N192_REFINE_ITERS,
            "N384_refine_iters":N384_REFINE_ITERS,
        },
        "N192":{
            "crossing_count":len(r192),
            "crossing_sequence":sequence(r192),
            "refined_crossings":r192,
            "persistence":p192,
        },
        "N384":{
            "crossing_count":len(r384),
            "crossing_sequence":sequence(r384),
            "refined_crossings":r384,
            "persistence":p384,
        },
        "comparison":{
            "same_crossing_count_and_direction_sequence":bool(topology_same),
            "both_last_upward_frontiers_persistent_to_published_boundary":bool(persistence_both),
        },
        "verdict":verdict,
        "next_status":(
            "DESCRIPTIVE_FIRST_ANCHOR_CLOSED_NO_D25H_GATE_RESTORATION"
            if verdict=="TOPOLOGY_STABLE_PERSISTENT_FRONTIER_IDENTIFIED"
            else
            "HOLD_FIRST_ANCHOR_TOPOLOGY_NO_D25H"
        ),
        "claim_control":{
            "restores_original_D25G_4of4_gate":False,
            "remaining_three_anchor_outcomes_inferred":False,
            "exact_JHEP_likelihood_replay":False,
            "exact_Ref74_paper_commit_replay":False,
            "posthoc_numeric_tolerance":False,
        }
    }

    if p192.get("available"):
        x=p192["last_up"]["x_um_inv"]
        doc["N192"]["last_up_over_published_x_ratio"]=x/float(anchor["published_x_um_inv"])
    if p384.get("available"):
        x=p384["last_up"]["x_um_inv"]
        doc["N384"]["last_up_over_published_x_ratio"]=x/float(anchor["published_x_um_inv"])

    (out/"D25G_R2_RESULT.json").write_text(json.dumps(doc,indent=2))
    print(json.dumps({
        "verdict":doc["verdict"],
        "next_status":doc["next_status"],
        "N192_crossings":len(r192),
        "N384_crossings":len(r384),
        "N192_sequence":sequence(r192),
        "N384_sequence":sequence(r384),
        "N192_persistence_below":p192.get("below_count"),
        "N384_persistence_below":p384.get("below_count"),
        "N192_last_up_ratio":doc["N192"].get("last_up_over_published_x_ratio"),
        "N384_last_up_ratio":doc["N384"].get("last_up_over_published_x_ratio"),
    },indent=2))

if __name__=="__main__":
    main()
