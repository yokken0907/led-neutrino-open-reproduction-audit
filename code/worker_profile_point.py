#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, json, importlib.metadata as im
import numpy as np
from dayabay_model import model_dayabay
from dgm_fit.iminuit_minimizer import IMinuitMinimizer

EXPECTED = {
    "numpy":"2.3.5",
    "dayabay-model":"1.8.0",
    "dayabay-data-official":"1.0.1",
    "dgm-reactor-neutrino":"0.3.0",
    "dag-modelling":"0.15.0",
    "dgm-fit":"0.4.0",
    "iminuit":"2.33.0",
}

PUBLIC_BEST = {
"survival_probability.SinSq2Theta13":0.0854238209633967,
"survival_probability.DeltaMSq32":0.0024708320336013817,
"neutrino_per_fission_factor.spec_scale_00":-0.017311211876546086,
"neutrino_per_fission_factor.spec_scale_01":-0.08610087594583543,
"neutrino_per_fission_factor.spec_scale_02":-0.08610841081872854,
"neutrino_per_fission_factor.spec_scale_03":-0.0833178644294709,
"neutrino_per_fission_factor.spec_scale_04":-0.10828986177393639,
"neutrino_per_fission_factor.spec_scale_05":-0.06330908671992146,
"neutrino_per_fission_factor.spec_scale_06":-0.10254285253871658,
"neutrino_per_fission_factor.spec_scale_07":-0.05674357528680113,
"neutrino_per_fission_factor.spec_scale_08":-0.0645552748460088,
"neutrino_per_fission_factor.spec_scale_09":-0.06679132385658493,
"neutrino_per_fission_factor.spec_scale_10":-0.054842498949633584,
"neutrino_per_fission_factor.spec_scale_11":0.011412357429422322,
"neutrino_per_fission_factor.spec_scale_12":0.03325175462884603,
"neutrino_per_fission_factor.spec_scale_13":0.07240465870940195,
"neutrino_per_fission_factor.spec_scale_14":-0.016702107328537014,
"neutrino_per_fission_factor.spec_scale_15":-0.004246536656167282,
"neutrino_per_fission_factor.spec_scale_16":-0.06536991878583376,
"neutrino_per_fission_factor.spec_scale_17":-0.016374854994200237,
"neutrino_per_fission_factor.spec_scale_18":-0.315993895573724,
}
PUBLIC_FUN=557.9755550235543

def versions():
    out={}
    ok=True
    for p,want in EXPECTED.items():
        got=im.version(p)
        out[p]={"expected":want,"found":got,"pass":got==want}
        ok &= got==want
    return ok,out

def shape_parameters(m):
    grp=m.storage["parameters.free"]["neutrino_per_fission_factor"]
    pars={
        f"neutrino_per_fission_factor.{path}":par
        for path,par in grp.walkjoineditems()
        if path.startswith("spec_scale_")
    }
    if len(pars)!=19:
        raise RuntimeError(f"expected 19 shape parameters, got {len(pars)}")
    return pars

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--sin22",type=float,required=True)
    ap.add_argument("--dm32",type=float,required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    vok,vv=versions()
    if not vok:
        raise RuntimeError(f"version contract failed: {vv}")

    # Fresh process + fresh model for each single point.
    m=model_dayabay(concatenation_mode="detector_period")
    m.switch_data("real")

    init=dict(PUBLIC_BEST)
    init["survival_probability.SinSq2Theta13"]=float(a.sin22)
    init["survival_probability.DeltaMSq32"]=float(a.dm32)
    # Public API only: no direct private setter and no imports from old D25/R2.
    m.set_parameters(init)

    stat=m.storage["outputs.statistic.full.covmat.chi2cnp"]
    pars=shape_parameters(m)
    fit=IMinuitMinimizer(stat,parameters=pars,nbins=m.nbins).fit()

    doc={
        "sin22theta13":float(a.sin22),
        "dm32_eV2":float(a.dm32),
        "chi2":float(fit["fun"]),
        "success":bool(fit["success"]),
        "nfev":int(fit["nfev"]),
        "shape_xdict":{k:float(v) for k,v in fit["xdict"].items()},
        "versions":vv,
    }
    Path(a.out).write_text(json.dumps(doc,indent=2))
    print(json.dumps({k:v for k,v in doc.items() if k!="shape_xdict"},indent=2))
    if not fit["success"]:
        raise SystemExit(4)

if __name__=="__main__":
    main()
