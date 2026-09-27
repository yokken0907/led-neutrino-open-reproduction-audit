#!/usr/bin/env python3
"""
D25F — Ref.[74]/Newtrinos open-likelihood bridge.

This phase implements, in Python, the Daya Bay forward-likelihood structure
visible in the pinned Newtrinos.jl Daya Bay module:
  - EH3 background-subtracted observed spectrum;
  - no-oscillation EH3 spectrum reconstructed from Daya Bay best-fit prediction;
  - baseline-averaged survival probability;
  - 26x26 systematic correlation matrix from arXiv:1607.05378;
  - parameter-dependent Gaussian covariance:
      D(exp*rel_unc) Corr D(exp*rel_unc) * covmat_prefactor + Diag(exp).

It evaluates only the same four Figure-5 anchors at:
  1) the published JHEP Figure-5 boundary;
  2) the current custom-proxy boundary.

It is an OPEN COMPARATOR linked to Ref.[74], not an exact JHEP likelihood replay.
"""
from __future__ import annotations

from pathlib import Path
import argparse, csv, hashlib, json, math, urllib.request
import numpy as np

from dirac_bulk_kernel import (
    SURPROB_ARG_CONVERSION,
    electron_weights,
    physical_masses,
    pee_array,
)

REPO = "Newtrinos-org/Newtrinos.jl"
COMMIT = "4388c2782248c37b08a8749247f49566fd89deac"
BASE_PATH = "src/experiments/daya_bay/daya_bay_3158days"

FILES = {
    "dayabay.jl": ("f32c8a25ae52b275680f73e0f378802d4c54a8ee", "dayabay.jl"),
    "test.jl": ("6fe95b154343ff57b703a90700103eb0383468aa", "test.jl"),
    "corr.txt": ("ab85196d2141cb47ec6d1ee5aa5e3590aafcee10", "DayaBay_CorrMat_arXiv_1607.05378.txt"),
    "ibd_eh3.txt": ("28f57ce2d55a376e050602e4f46242a708e22c68", "DayaBay_IBDPromptSpectrum_EH3_3158days.txt"),
    "bkg_eh3.txt": ("065da75bd8cb06d8b6420b11efcbf40e5aedfc3a", "DayaBay_BackgroundSpectrum_EH3_3158days.txt"),
}

THRESH = 4.605170185988092
AUTHORITY = "NUFIT6_IC24_SK"
NKK = 192

# Same authority values used by the previous proxy.
AUTHORITIES = {
    "NO": {
        "sin22theta12": 4*.308*(1-.308),
        "sin22theta13": 4*.02215*(1-.02215),
        "dm21": 7.49e-5,
        "dm32abs": 2.513e-3 - 7.49e-5,
        "nmo": +1,
    },
    "IO": {
        "sin22theta12": 4*.308*(1-.308),
        "sin22theta13": 4*.02231*(1-.02231),
        "dm21": 7.49e-5,
        "dm32abs": 2.484e-3,
        "nmo": -1,
    },
}

# EH3 rows from pinned Newtrinos dayabay.jl.
TARGET_KG = np.array([19917., 19989., 19892., 19931.])
EFF = np.array([0.9513, 0.9514, 0.9512, 0.9513])
BASELINES = np.array([
    [1919.63, 1894.34, 1533.18, 1533.63, 1551.38, 1524.94],
    [1917.52, 1891.98, 1534.92, 1535.03, 1554.77, 1528.05],
    [1925.26, 1899.86, 1538.93, 1539.47, 1556.34, 1530.08],
    [1923.15, 1897.51, 1540.67, 1540.87, 1559.72, 1533.18],
])
ACTIVE = {
    "Six": np.array([True, True, True, False]),
    "Eight": np.array([True, True, True, True]),
    "Seven": np.array([True, True, True, True]),
}
PERIODS = ("Six", "Eight", "Seven")

def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def acquire_sources(outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    ledger = {}
    for local, (expected_blob, remote_name) in FILES.items():
        url = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{BASE_PATH}/{remote_name}"
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = r.read()
        except Exception as e:
            raise RuntimeError(f"authority download failed: {url}: {e!r}")
        got_blob = git_blob_sha1(data)
        if got_blob != expected_blob:
            raise RuntimeError(
                f"authority blob mismatch for {remote_name}: expected {expected_blob}, got {got_blob}"
            )
        p = outdir / local
        p.write_bytes(data)
        ledger[local] = {
            "remote_name": remote_name,
            "url": url,
            "git_blob_sha1": got_blob,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        }
    (outdir / "SOURCE_LEDGER.json").write_text(json.dumps(ledger, indent=2))
    return ledger

def load_targets(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_authority_data(srcdir: Path):
    corrraw = np.loadtxt(srcdir / "corr.txt", skiprows=1)
    if corrraw.shape != (26, 30):
        raise RuntimeError(f"unexpected corr shape {corrraw.shape}")
    rel_unc = corrraw[:, 3]
    corr = corrraw[:, 4:]
    if corr.shape != (26, 26):
        raise RuntimeError(corr.shape)

    ibd = np.loadtxt(srcdir / "ibd_eh3.txt", comments="#")
    if ibd.shape != (26, 9):
        raise RuntimeError(f"unexpected IBD shape {ibd.shape}")

    bkg_all = np.loadtxt(srcdir / "bkg_eh3.txt", comments="#")
    if bkg_all.shape != (78, 9):
        raise RuntimeError(f"unexpected BKG shape {bkg_all.shape}")
    bkg = {
        "Six": bkg_all[0:26, 3],
        "Eight": bkg_all[26:52, 3],
        "Seven": bkg_all[52:78, 3],
    }

    # columns: Emin Emax Ec Nobs_6 Nobs_8 Nobs_7 Npred_6 Npred_8 Npred_7
    ec = ibd[:, 2]
    E_nu = ec + 0.78
    nobs = {"Six": ibd[:, 3], "Eight": ibd[:, 4], "Seven": ibd[:, 5]}
    npred = {"Six": ibd[:, 6], "Eight": ibd[:, 7], "Seven": ibd[:, 8]}
    observed = nobs["Six"] + nobs["Eight"] + nobs["Seven"] - bkg["Six"] - bkg["Eight"] - bkg["Seven"]

    return {
        "rel_unc": rel_unc,
        "corr": corr,
        "E_nu": E_nu,
        "npred": npred,
        "observed": observed,
    }

def bestfit_standard_pee(E, L):
    # Pinned Newtrinos Daya Bay reconstruction values.
    s12 = 0.307
    sin22_13 = 0.0851
    s13 = 0.5 * (1.0 - math.sqrt(1.0 - sin22_13))
    ue2 = np.array([(1-s12)*(1-s13), s12*(1-s13), s13])
    dm21 = 7.53e-5
    dm32 = 2.466e-3
    m2sq = np.array([0.0, dm21, dm21 + dm32])
    phase_pref = SURPROB_ARG_CONVERSION * float(L) * 0.5e-3
    amp = np.zeros_like(E, dtype=np.complex128)
    for w, msq in zip(ue2, m2sq):
        amp += w * np.exp(-1j * (1.0/E) * msq * phase_pref)
    return np.abs(amp)**2

def authority_standard_pee(E, L, ordering):
    p = AUTHORITIES[ordering]
    ue2 = electron_weights(p["sin22theta12"], p["sin22theta13"])
    masses = physical_masses(
        0.0, p["dm21"], p["dm32abs"], p["nmo"], "dm32"
    )
    phase_pref = SURPROB_ARG_CONVERSION * float(L) * 0.5e-3
    amp = np.zeros_like(E, dtype=np.complex128)
    for w, m in zip(ue2, masses):
        amp += w * np.exp(-1j * (1.0/E) * (m*m) * phase_pref)
    return np.abs(amp)**2

def led_pee(E, L, ordering, m0, radius):
    p = AUTHORITIES[ordering]
    vals, _ = pee_array(
        E, float(L), float(radius), float(m0), 0.0,
        p["sin22theta12"], p["sin22theta13"],
        p["dm21"], p["dm32abs"], p["nmo"],
        leading="dm32", nkk=NKK,
    )
    return np.asarray(vals, dtype=float)

def period_baselines(period):
    return BASELINES[ACTIVE[period], :].reshape(-1)

def baseline_avg_prob(E, baselines, probfunc):
    L = np.asarray(baselines, dtype=float)
    invL2 = 1.0 / (L*L)
    probs = np.stack([probfunc(E, x) for x in L], axis=0)
    return np.sum(probs * invL2[:, None], axis=0) / np.sum(invL2)

def covmat_prefactor():
    contrib = []
    for period in PERIODS:
        mask = ACTIVE[period]
        for j in range(6):
            L = BASELINES[mask, j]
            contrib.extend((1.0/(L*L)) * TARGET_KG[mask] * EFF[mask])
    a = np.asarray(contrib, dtype=float)
    a = a / np.sum(a)
    return float(np.sum(a*a))

def reconstruct_noosc(data):
    out = {}
    for period in PERIODS:
        L = period_baselines(period)
        pav = baseline_avg_prob(data["E_nu"], L, bestfit_standard_pee)
        out[period] = data["npred"][period] / pav
    return out

def expected_spectrum(data, noosc, ordering, mode, m0=None, radius=None):
    total = np.zeros(26, dtype=float)
    for period in PERIODS:
        L = period_baselines(period)
        if mode == "SM":
            pav = baseline_avg_prob(
                data["E_nu"], L,
                lambda E, ll: authority_standard_pee(E, ll, ordering)
            )
        elif mode == "LED":
            pav = baseline_avg_prob(
                data["E_nu"], L,
                lambda E, ll: led_pee(E, ll, ordering, m0, radius)
            )
        else:
            raise KeyError(mode)
        total += noosc[period] * pav
    return total

def gaussian_loglike(obs, exp, rel_unc, corr, pref):
    scale = exp * rel_unc
    cov = pref * (scale[:, None] * corr * scale[None, :]) + np.diag(exp)
    sign, logdet = np.linalg.slogdet(cov)
    if sign <= 0:
        raise RuntimeError("non-positive covariance determinant")
    r = obs - exp
    q = float(r @ np.linalg.solve(cov, r))
    return -0.5 * (q + logdet + len(obs)*math.log(2*math.pi)), q, float(logdet)

def evaluate_point(data, noosc, ordering, m0, radius, sm_logl, pref):
    exp = expected_spectrum(data, noosc, ordering, "LED", m0, radius)
    logl, q, logdet = gaussian_loglike(data["observed"], exp, data["rel_unc"], data["corr"], pref)
    delta = -2.0 * (logl - sm_logl)
    return {
        "delta_chi2": float(delta),
        "log_likelihood": float(logl),
        "quadratic_term": q,
        "logdet_covariance": logdet,
        "expected_total": float(np.sum(exp)),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True)
    ap.add_argument("--d25e", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    srcdir = out / "authority_sources"
    ledger = acquire_sources(srcdir)
    data = load_authority_data(srcdir)
    noosc = reconstruct_noosc(data)
    pref = covmat_prefactor()
    targets = load_targets(args.targets)
    d25e = json.loads(Path(args.d25e).read_text())

    sm = {}
    for ordering in ("NO", "IO"):
        exp = expected_spectrum(data, noosc, ordering, "SM")
        logl, q, logdet = gaussian_loglike(
            data["observed"], exp, data["rel_unc"], data["corr"], pref
        )
        sm[ordering] = {
            "log_likelihood": float(logl),
            "quadratic_term": q,
            "logdet_covariance": logdet,
            "expected_total": float(np.sum(exp)),
        }

    d25e_by_key = {
        (r["ordering"], float(r["m_lightest_eV"])): r for r in d25e["results"]
    }

    rows = []
    all_pub_closer_than_native = True
    all_custom_frontier_below = True
    for i, t in enumerate(targets, 1):
        ordering = t["ordering"]
        m0 = float(t["m_lightest_eV"])
        rpub = float(t["published_R_um"])
        rproxy = float(t["custom_proxy_R_um"])
        pub = evaluate_point(data, noosc, ordering, m0, rpub, sm[ordering]["log_likelihood"], pref)
        proxy = evaluate_point(data, noosc, ordering, m0, rproxy, sm[ordering]["log_likelihood"], pref)

        prev = d25e_by_key[(ordering, m0)]
        native_pub = float(prev["native_delta_chi2_at_published_R"])
        ref74_pub_closer = abs(pub["delta_chi2"]-THRESH) < abs(native_pub-THRESH)
        ref74_proxy_below = proxy["delta_chi2"] < THRESH

        all_pub_closer_than_native &= ref74_pub_closer
        all_custom_frontier_below &= ref74_proxy_below

        rec = {
            "ordering": ordering,
            "m_lightest_eV": m0,
            "published_R_um": rpub,
            "published_x_um_inv": float(t["published_x_um_inv"]),
            "custom_proxy_R_um": rproxy,
            "custom_proxy_x_um_inv": float(t["custom_proxy_x_um_inv"]),
            "D25E_native_delta_at_published": native_pub,
            "D25E_native_delta_at_custom_frontier": float(prev["native_delta_chi2_at_custom_frontier"]),
            "ref74_open_delta_at_published": pub["delta_chi2"],
            "ref74_open_delta_at_custom_frontier": proxy["delta_chi2"],
            "ref74_published_closer_to_threshold_than_D25E_native": bool(ref74_pub_closer),
            "ref74_custom_frontier_below_threshold": bool(ref74_proxy_below),
            "published_point_detail": pub,
            "custom_frontier_detail": proxy,
        }
        rows.append(rec)
        (out/"D25F_PROGRESS_CHECKPOINT.json").write_text(json.dumps({
            "completed": i, "total": len(targets), "current": rec
        }, indent=2))

    pub_deltas = [r["ref74_open_delta_at_published"] for r in rows]
    proxy_deltas = [r["ref74_open_delta_at_custom_frontier"] for r in rows]

    if all_pub_closer_than_native and all_custom_frontier_below:
        verdict = "REF74_OPEN_COMPARATOR_MOVES_CLOSER_THAN_NATIVE_CNP"
        next_status = "GO_D25G_REF74_OPEN_BOUNDARY_RECONSTRUCTION"
    else:
        verdict = "MIXED_REF74_OPEN_COMPARATOR"
        next_status = "HOLD_BOUNDARY_RECONSTRUCTION_PENDING_LAYER_AUDIT"

    doc = {
        "phase": "D25F_REF74_NEWTRINOS_LIKELIHOOD_BRIDGE",
        "source_freeze": {
            "repository": REPO,
            "commit": COMMIT,
            "authority_ledger": ledger,
            "exact_ref74_paper_commit_claimed": False,
        },
        "model": {
            "scenario": "vanilla_Dirac_brane",
            "bulk_ratio": 0.0,
            "authority": AUTHORITY,
            "NKK": NKK,
        },
        "likelihood": {
            "observed": "EH3 total background-subtracted spectrum",
            "systematics": "pinned Newtrinos correlation matrix and fractional uncertainties",
            "covariance": "pref*D(exp*rel_unc)*Corr*D(exp*rel_unc)+Diag(exp)",
            "nuisance_parameters": "none in pinned dayabay.jl module",
            "covmat_prefactor": pref,
        },
        "data_summary": {
            "observed_total": float(np.sum(data["observed"])),
            "observed_bins": int(len(data["observed"])),
        },
        "SM": sm,
        "results": rows,
        "summary": {
            "published_delta_chi2_min": min(pub_deltas),
            "published_delta_chi2_max": max(pub_deltas),
            "published_delta_chi2_median": float(np.median(pub_deltas)),
            "custom_frontier_delta_chi2_min": min(proxy_deltas),
            "custom_frontier_delta_chi2_max": max(proxy_deltas),
            "all_published_points_closer_to_threshold_than_D25E_native": bool(all_pub_closer_than_native),
            "all_custom_frontiers_below_threshold": bool(all_custom_frontier_below),
        },
        "verdict": verdict,
        "next_status": next_status,
        "claim_control": {
            "exact_JHEP_likelihood_replay": False,
            "exact_Ref74_commit_replay": False,
            "current_open_Newtrinos_comparator": True,
            "bulk_mapping_exonerated_completely": False,
            "posthoc_match_tolerance": False,
        },
    }
    (out/"D25F_RESULT.json").write_text(json.dumps(doc, indent=2))
    print(json.dumps({
        "verdict": verdict,
        "next_status": next_status,
        "published_delta_chi2_range": [min(pub_deltas), max(pub_deltas)],
        "published_delta_chi2_median": float(np.median(pub_deltas)),
        "custom_frontier_delta_chi2_range": [min(proxy_deltas), max(proxy_deltas)],
        "observed_total": float(np.sum(data["observed"])),
        "covmat_prefactor": pref,
    }, indent=2))

if __name__ == "__main__":
    main()
