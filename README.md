# LED-neutrino open reproduction audit

Current manuscript-facing status: **Figure-1 partial replication with Revision-1 hosted reproducibility**

This repository is the public reproducibility record for the higher-dimensional neutrino audit. Historical phases are retained for provenance, but the current ReScience C claim is intentionally narrow.

It does **not** claim discovery of LED physics, does **not** claim that the target publication is wrong, and does **not** claim an exact replay of the target experimental likelihood.

## Current successful partial-replication target

The [Re] claim is bounded to the Brane-Dirac eigensystem shown in Figure 1 of:

A. de Giorgi, D. Pasari, J. Turner, *Do neutrinos dream in 5D? Towards a comprehensive extra-dimensional neutrino phenomenology*, JHEP 05 (2026) 152.

The public Revision-1 workflow:
- solves the published infinite-tower eigensystem for m_D=1 and mu_1={10,1,0.1};
- cross-checks nine pre-specified roots with a mathematically distinct finite-KK route;
- verifies the paper's >99% unitarity truncation criterion;
- preserves the historical D29A raw-residual automatic FAIL;
- retains the D29B conditioning diagnostic without describing |F/F'| as a strict backward error;
- directly re-solves all 3552 plotted roots at 80-digit precision (D29C);
- rechecks the frozen D30 direct published-output evidence and the fixed per-mu_1 coverage rule.

Run locally:

```bash
python -m pip install -r environment/requirements-figure1-exact.txt
bash reproduce_figure1_revision1.sh
```

Expected terminal result:

```text
FIGURE1_REVISION1_REPRODUCTION_PASS
```

Workflow:

```text
.github/workflows/reproduce-figure1-revision1.yml
```

Reviewer-facing detail:
- `REVISION1_REPRODUCTION_EVIDENCE.md`
- `REPRODUCTION_EVIDENCE.md`

## D30 boundary

The hosted D30C step rechecks frozen machine-readable D30A/D30B evidence tables. It does **not** rerasterize the publisher PDF. The underlying multi-resolution raster authority runs, overlays, and marker-occlusion adjudication are preserved in the manuscript audit archive. The manuscript reports 12 direct graphical matches, two separately adjudicated occlusion cases, and one unresolved graphical anchor; it does not claim 15/15 direct graphical recovery.

## Important supersession notice

Older D25-D27 outputs remain for audit provenance. Later reviewer-driven audits withdrew:
- the old 39-versus-17 threshold-crossing attribution to KK truncation;
- the old binary Daya Bay calibration-failure interpretation;
- use of project-defined calibration cutoffs as current scientific pass/fail criteria.

The public Daya Bay covariance full fit is reproducible in the frozen environment, while the earlier fixed-coordinate project profile was non-equivalent. Figure-5 pointwise exclusion replication remains unresolved in the tested open comparator.

## Scope boundary

Not claimed:
- Figure-5 exclusion-contour replication;
- exact target-author likelihood replay;
- experimental-constraint replication;
- a new LED signal;
- an error in the original JHEP article.

## Historical workflow

`reproduce_all.sh` and `.github/workflows/reproduce.yml` preserve the older D27 reproducibility record; they do not define the current manuscript claim.

## Licensing

Original code/documentation: MIT. Third-party data/code retain their upstream licenses; see `licenses/THIRD_PARTY_MATERIALS.md`.
