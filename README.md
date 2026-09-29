# LED-neutrino open reproduction audit

Current manuscript-facing status: **ReScience Revision-1 public reproducibility integration in progress; bounded Figure-1 partial replication only**

This repository contains the public reproducibility record for the higher-dimensional neutrino audit. It preserves earlier audit phases for provenance, but the current manuscript interpretation is narrower than some historical phase verdicts.

It does **not** claim discovery of LED physics, does **not** claim that the target publication is wrong, and does **not** claim an exact replay of the target experimental likelihood.

## Current successful partial-replication target

The current ReScience-C manuscript is bounded to the Brane-Dirac eigensystem shown in Figure 1 of:

A. de Giorgi, D. Pasari, J. Turner, *Do neutrinos dream in 5D? Towards a comprehensive extra-dimensional neutrino phenomenology*, JHEP 05 (2026) 152.

The independent Figure-1 calculation:
- starts from published Eqs. (3.26)-(3.28);
- uses (m_D=1) and (mu_1={10,1,0.1});
- independently triangulates the infinite-tower roots against a finite-KK implementation;
- verifies the paper's >99% unitarity truncation criterion;
- preserves the original D29A raw-residual FAIL in the audit trail;
- diagnoses that FAIL with a D29B Newton-correction / derivative-scaled-residual audit;\n- directly re-solves all 3552 plotted roots at 80-digit precision in D29C;\n- compares pre-specified Figure-1 anchors with the published graphical output in D30A and adjudicates two deterministic overplot/occlusion cases in D30B without rewriting the frozen D30A machine verdict.

Run locally:

```bash
python -m pip install -r environment/requirements-figure1-exact.txt
bash reproduce_figure1.sh
```

Expected bounded final verdict:

```text
PASS_FIGURE1_COMPUTATIONAL_CORE_INDEPENDENT_REPLICATION_AFTER_CONDITIONING_AUDIT
```

GitHub Actions workflow:

```text
.github/workflows/reproduce-figure1.yml
```

Reviewer-facing evidence index:

```text
REPRODUCTION_EVIDENCE.md
```

## Important supersession notice

The older D27 reproducibility pipeline remains in this repository as historical evidence of what the project computed at that stage. Later reviewer-driven audits changed the manuscript-level interpretation.

The following historical outputs must **not** be read as current scientific conclusions:

- the old D25G comparison of 39 threshold crossings at N=192 versus 17 at N=384;
- the old attribution of that difference to KK-truncation dependence;
- the old D26C1 binary verdict `FAIL_CLEAN_PUBLIC_DAYABAY_STANDARD3NU_CALIBRATION`;
- the earlier use of project-defined calibration cutoffs as scientific PASS/FAIL criteria.

Later matched-grid and public-fit controls showed:
- threshold-crossing count was not converged under R-grid refinement, so the old 39-versus-17 KK interpretation was withdrawn;
- the public Daya Bay covariance full fit itself is reproducible in the frozen environment;
- the project's fixed-coordinate D26 profiling route was not equivalent to that public reference fit;
- Figure-5 pointwise exclusion replication was not established because the open comparator had unresolved local threshold topology.

Those historical files are retained for audit provenance, not deleted or rewritten.

## Scope boundary

The current successful replicated subset is **Figure 1 / Brane-Dirac spectrum only**.

Not claimed:
- Figure-5 exclusion-contour replication;
- exact target-author likelihood replay;
- experimental-constraint replication;
- a new LED signal;
- an error in the original JHEP article.

## Historical D27 external-CI record

The earlier D27B/D27C repository-hardening workflow remains available through:

```bash
bash reproduce_all.sh
```

and

```text
.github/workflows/reproduce.yml
```

Those workflows reproduce the frozen historical project outputs. They do not, by themselves, define the current manuscript's scientific interpretation.

## Licensing

Original code/documentation: MIT.

Third-party data/code retain their upstream licenses. See `licenses/THIRD_PARTY_MATERIALS.md`.
