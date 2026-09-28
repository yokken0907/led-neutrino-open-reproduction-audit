#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import math
import hashlib

import numpy as np
from scipy.optimize import brentq
import matplotlib.pyplot as plt

MD = 1.0
MU_VALUES = (10.0, 1.0, 0.1)
PLOT_X_MIN = 0.03
PLOT_X_MAX = 320.0

# Numerical-identity gate for independent finite-sum -> infinite-tower
# Richardson extrapolation. This is not a physics tolerance.
TRIANGULATION_ABS_TOL = 1.0e-7

# Paper's explicit numerical truncation criterion in Eq. (4.2).
UNITARITY_MIN = 0.99

FINITE_N_LEVELS = (5000, 10000, 20000)
TRIANGULATION_MODES = (0, 1, 5)


def cot(x: float) -> float:
    return 1.0 / math.tan(x)


def eq326_residual(m: float, mu1: float, mD: float = MD) -> float:
    return math.pi * cot(math.pi * m / mu1) - (mu1 * m) / (mD * mD)


def root_eq326(mu1: float, n: int, mD: float = MD) -> float:
    """Solve Eq. (3.26) on the positive-cot branch n < m/mu1 < n+1/2."""
    alpha = (mu1 / mD) ** 2

    def f(y: float) -> float:
        return math.pi * cot(math.pi * y) - alpha * y

    eps = 1.0e-10
    lo = float(n) + eps
    hi = float(n) + 0.5 - eps
    return float(mu1 * brentq(f, lo, hi, xtol=1e-14, rtol=1e-13, maxiter=200))


def nlambda_eq327(m: float, mu1: float, mD: float = MD) -> float:
    # Eq. (3.27), N -> infinity closed form.
    bracket = 0.5 * (
        (math.pi * math.pi * mD * mD) / (mu1 * mu1)
        + (m * m) / (mD * mD)
        + 1.0
    )
    return float(bracket ** -0.5)


def finite_sum_residual(m: float, mu1: float, N: int, mD: float = MD) -> float:
    """Finite-N left side of Eq. (3.26) minus 1.

    Brane Dirac wavefunctions at the brane are chi_0=1 and chi_n=sqrt(2), n>=1.
    """
    k = np.arange(0, N + 1, dtype=float)
    mu = k * mu1
    chi2 = np.ones_like(k)
    chi2[1:] = 2.0
    denom = m*m - mu*mu
    return float(np.sum((chi2 * mD*mD) / denom) - 1.0)


def root_finite_sum(mu1: float, n: int, N: int, mD: float = MD) -> float:
    eps = max(1e-12, 1e-9 * mu1)
    lo = n * mu1 + eps if n > 0 else eps
    hi = (n + 0.5) * mu1 - eps

    def f(m):
        return finite_sum_residual(m, mu1, N, mD)

    return float(brentq(f, lo, hi, xtol=1e-12, rtol=1e-12, maxiter=300))


def richardson_1_over_N(vN: float, v2N: float) -> float:
    return 2.0 * v2N - vN


def solve_plot_roots(mu1: float):
    nmax = int(math.ceil(PLOT_X_MAX / mu1)) + 2
    roots = []
    for n in range(nmax):
        m = root_eq326(mu1, n)
        if m > PLOT_X_MAX:
            break
        if m >= PLOT_X_MIN:
            roots.append((n, m, nlambda_eq327(m, mu1)))
    return roots


def adaptive_unitarity(mu1: float):
    # Increase tower size until paper's >99% criterion is met.
    N = 64
    while N <= 100000:
        vals = []
        for n in range(N):
            m = root_eq326(mu1, n)
            vals.append(nlambda_eq327(m, mu1) ** 2)
        s = float(sum(vals))
        if s > UNITARITY_MIN:
            return {"modes": N, "sum_Nlambda2": s}
        N *= 2
    raise RuntimeError(f"unitarity > {UNITARITY_MIN} not reached for mu1={mu1}")


def asymptotic_diagnostics(mu1: float):
    m0 = root_eq326(mu1, 0)
    N0 = nlambda_eq327(m0, mu1)

    out = {
        "mu1": mu1,
        "m0_exact": m0,
        "N0_exact": N0,
    }

    if mu1 >= 5.0:
        # Eq. (3.29) first-order lightest-mode approximation.
        approx = MD * (1.0 - math.pi**2 * MD**2 / (6.0 * mu1**2))
        out["eq329_m0_approx"] = approx
        out["eq329_relative_difference"] = abs(m0-approx)/abs(m0)

    if mu1 <= 0.2:
        # Eq. (3.31) plateau.
        plateau = math.sqrt(2.0) / math.pi * mu1 / MD
        first50 = [
            nlambda_eq327(root_eq326(mu1, n), mu1)
            for n in range(50)
        ]
        out["eq331_plateau"] = plateau
        out["eq331_first50_median"] = float(np.median(first50))
        out["eq331_first50_median_relative_difference"] = abs(
            float(np.median(first50))-plateau
        ) / plateau

        # Eq. (3.32), reported as a qualitative estimate.
        nstar = (math.pi * MD / (math.sqrt(2.0) * mu1))**2
        nround = int(round(nstar))
        mstar = root_eq326(mu1, nround)
        Nstar = nlambda_eq327(mstar, mu1)
        out["eq332_nstar_estimate"] = nstar
        out["eq332_nearest_integer_mode"] = nround
        out["eq332_mass_at_nearest_mode"] = mstar
        out["eq332_Nlambda_at_nearest_mode"] = Nstar
        out["eq332_Nlambda_over_eq331_plateau"] = Nstar/plateau
    return out


def make_replica_plot(all_roots, outpath: Path):
    fig, ax = plt.subplots(figsize=(7.2, 5.2))

    # Avoid specifying colors: matplotlib cycle is deterministic and sufficient.
    markers = {10.0:"v", 1.0:"^", 0.1:"d"}

    for mu1 in MU_VALUES:
        xs = np.geomspace(PLOT_X_MIN, PLOT_X_MAX, 1800)
        ys = np.array([nlambda_eq327(float(x), mu1) for x in xs])
        ax.plot(xs, ys, linestyle="--", linewidth=1.0, label=rf"$\mu_1={mu1:g}$ continuous")

        rows = all_roots[str(mu1)]
        mx = [r["m_lambda"] for r in rows]
        my = [r["N_lambda"] for r in rows]
        # Thin display for mu=.1 to keep markers readable, while CSV keeps all roots.
        step = max(1, len(mx)//450)
        ax.scatter(mx[::step], my[::step], marker=markers[mu1], s=10,
                   label=rf"$\mu_1={mu1:g}$ roots")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(PLOT_X_MIN, PLOT_X_MAX)
    ax.set_ylim(0.003, 1.6)
    ax.set_xlabel(r"$m_\lambda/m_D$")
    ax.set_ylabel(r"$N_\lambda$")
    ax.legend(fontsize=8)
    ax.set_title("Independent reproduction of JHEP 2026 Figure 1 computational core")
    fig.tight_layout()
    fig.savefig(outpath, dpi=220)
    plt.close(fig)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--outdir",required=True)
    ap.add_argument("--target-pdf",default="")
    args=ap.parse_args()
    out=Path(args.outdir).resolve()
    out.mkdir(parents=True,exist_ok=True)

    pdf_record=None
    if args.target_pdf:
        p=Path(args.target_pdf)
        if p.exists():
            pdf_record={
                "path":str(p.resolve()),
                "sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                "bytes":p.stat().st_size,
                "role":"authority provenance only; numerical calculation does not parse the PDF",
            }

    all_roots={}
    root_residual_max=0.0
    for mu1 in MU_VALUES:
        rows=[]
        for n,m,Nl in solve_plot_roots(mu1):
            residual=abs(eq326_residual(m,mu1))
            root_residual_max=max(root_residual_max,residual)
            rows.append({
                "n":n,
                "m_lambda":m,
                "N_lambda":Nl,
                "eq326_abs_residual":residual,
            })
        all_roots[str(mu1)]=rows

        with (out/f"FIG1_ROOTS_mu1_{mu1:g}.csv").open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["n","m_lambda","N_lambda","eq326_abs_residual"])
            w.writeheader()
            w.writerows(rows)

    # Independent route triangulation.
    triang=[]
    for mu1 in MU_VALUES:
        for n in TRIANGULATION_MODES:
            exact=root_eq326(mu1,n)
            finite=[]
            for N in FINITE_N_LEVELS:
                finite.append(root_finite_sum(mu1,n,N))
            # Use the final two levels for 1/N Richardson extrapolation.
            extrap=richardson_1_over_N(finite[-2],finite[-1])
            diff=abs(extrap-exact)
            triang.append({
                "mu1":mu1,
                "mode_n":n,
                "closed_form_root":exact,
                "finite_N_values":{
                    str(N):v for N,v in zip(FINITE_N_LEVELS,finite)
                },
                "richardson_N10000_N20000":extrap,
                "abs_difference":diff,
                "pass":diff <= TRIANGULATION_ABS_TOL,
            })

    unitarity={str(mu):adaptive_unitarity(mu) for mu in MU_VALUES}
    asym={str(mu):asymptotic_diagnostics(mu) for mu in MU_VALUES}

    # Paper-stated qualitative feature checks, kept deliberately minimal.
    N0={mu:nlambda_eq327(root_eq326(mu,0),mu) for mu in MU_VALUES}
    qualitative={
        "lightest_overlap_orders_as_mu_decreases":
            bool(N0[10.0] > N0[1.0] > N0[0.1]),
        "mu10_lightest_near_unity_value":N0[10.0],
        "mu01_first50_coefficient_of_variation":float(
            np.std([
                nlambda_eq327(root_eq326(0.1,n),0.1) for n in range(50)
            ]) /
            np.mean([
                nlambda_eq327(root_eq326(0.1,n),0.1) for n in range(50)
            ])
        ),
        "note":"These are descriptive checks of Figure-1 textual features, not independent acceptance tolerances."
    }

    core_pass=(
        all(x["pass"] for x in triang)
        and all(v["sum_Nlambda2"] > UNITARITY_MIN for v in unitarity.values())
        and root_residual_max < 1e-9
        and qualitative["lightest_overlap_orders_as_mu_decreases"]
    )

    verdict=(
        "PASS_FIGURE1_COMPUTATIONAL_CORE_INDEPENDENT_REPLICATION"
        if core_pass else
        "FAIL_FIGURE1_COMPUTATIONAL_CORE_REPLICATION_GATE"
    )

    result={
        "phase":"D29A_FIGURE1_BRANE_DIRAC_SPECTRUM_REPLICATION",
        "version":"5.0.0",
        "primary_target":{
            "article":"de Giorgi, Pasari & Turner, JHEP 05 (2026) 152",
            "figure":"Figure 1, Brane-Dirac spectrum",
            "published_parameters":{"mD":1.0,"mu1":[10.0,1.0,0.1]},
            "authority_equations":["3.26","3.27","3.28","3.29","3.31","3.32"],
        },
        "independence":{
            "uses_existing_project_LED_kernel":False,
            "uses_DayaBay_likelihood":False,
            "uses_Newtrinos":False,
            "uses_target_author_code":False,
            "route_A":"closed-form N->infinity Eq. (3.26) root solver",
            "route_B":"finite-KK Eq. (3.26) sum at N=5000,10000,20000 with 1/N Richardson extrapolation",
        },
        "target_pdf":pdf_record,
        "gates":{
            "triangulation_abs_tolerance":TRIANGULATION_ABS_TOL,
            "triangulation_tolerance_role":"numerical identity only",
            "unitarity_min":UNITARITY_MIN,
            "unitarity_source":"paper Eq. (4.2): >99% numerical truncation criterion",
            "root_residual_max_allowed":1e-9,
        },
        "root_residual_max":root_residual_max,
        "triangulation":triang,
        "unitarity":unitarity,
        "asymptotic_diagnostics":asym,
        "qualitative_text_checks":qualitative,
        "verdict":verdict,
        "rescience_consequence":(
            "[Re]_PARTIAL_SUPPORTING_CORE_CANDIDATE"
            if core_pass else
            "CLOSE_RESCIENCE_ROUTE_UNLESS_ANOTHER_ORIGINAL_RESULT_IS_REPLICATED"
        ),
        "claim_control":{
            "figure5_replication_claimed":False,
            "experiment_level_constraint_replication_claimed":False,
            "figure1_computational_core_only":True,
            "visual_similarity_used_as_acceptance_gate":False,
            "new_physics_claimed":False,
        },
    }

    make_replica_plot(all_roots,out/"FIGURE1_INDEPENDENT_REPLICA.png")
    (out/"D29A_RESULT.json").write_text(json.dumps(result,indent=2)+"\n")

    print(json.dumps({
        "verdict":verdict,
        "rescience_consequence":result["rescience_consequence"],
        "root_residual_max":root_residual_max,
        "triangulation_max_abs_difference":max(x["abs_difference"] for x in triang),
        "unitarity":unitarity,
        "N0":{
            str(k):v for k,v in N0.items()
        },
        "asymptotic":asym,
    },indent=2))
    print("D29A_EXECUTION_COMPLETE")


if __name__=="__main__":
    main()
