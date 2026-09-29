# LED-neutrino open reproduction audit

Current manuscript-facing target: **partial replication of the Brane--Dirac spectrum in Figure 1**, with an end-to-end public validation route.

Target article:

A. de Giorgi, D. Pasari, J. Turner, *Do neutrinos dream in 5D? Towards a comprehensive extra-dimensional neutrino phenomenology*, JHEP 05 (2026) 152.

This repository does **not** claim a new LED signal, an error in the target article, or replication of the target authors' experimental likelihoods.

## One-command manuscript reproduction

```bash
python -m pip install -r environment/requirements-figure1-exact.txt
bash reproduce_figure1_revision2.sh
```

Expected terminal line:

```text
FIGURE1_REVISION2_END_TO_END_REPRODUCTION_PASS
```

The workflow:
1. solves the published infinite-tower eigensystem and cross-checks nine pre-specified roots with a mathematically distinct finite-KK calculation;
2. validates all 3552 binary64 roots generated over the Figure-1 plotting range by direct 80-digit re-solution;
3. obtains the exact version-of-record PDF identified by SHA-256 `2850f1c631b07de992cc72dd2b9c8aab80c10e7bccf51a421d90e80373f627c3`, rasterizes Figure 1 at 400/600/800 dpi, calibrates its axes, detects the colored marker footprints, and regenerates the 15-point graphical-validation table and overlay;
4. applies the separately specified marker-overlap assessment to the two purple markers requiring occlusion treatment.

If publisher transport bytes change, supply the exact identified PDF locally with `FIGURE1_TARGET_PDF`; the checksum requirement is not relaxed.

## Graphical validation semantics

The graphical comparison evaluates support by the detected **rasterized colored-marker footprint**. It is not a claim that the median digitized marker coordinate equals the theoretical coordinate to high precision.

The 15 pre-specified test points yield 12 direct graphical-footprint supports, two `mu1=10` markers requiring the control-calibrated overlap/occlusion assessment, and one `mu1=0.1,n=20` point with insufficient graphical support.

For the occlusion assessment, `n=0` is the full purple-marker shape reference, `n=1` is the registration control, and `n=2` is the registration plus overplot/occlusion control.

See `docs/FIGURE1_GRAPHICAL_VALIDATION.md`.

## Docker

```bash
docker build -t led-figure1-replication .
docker run --rm led-figure1-replication
```

## Scope boundary

Successful replication claim: Figure 1 / Brane--Dirac spectrum only.

Not claimed:
- Figure-5 exclusion-contour replication;
- exact target-author likelihood replay;
- Daya Bay or MINOS/MINOS+ experimental-constraint replication;
- new extra-dimensional physics;
- an error in the original JHEP article.

Only `.github/workflows/reproduce-figure1-revision2.yml` is retained as an active reproduction workflow. Earlier workflows, runners, and documents containing withdrawn pre-revision interpretations are retained under `provenance/superseded/` with explicit superseded notices.

The current claim is summarized in `paper/CURRENT_CLAIM.md`. The current executable scope is stated in `REPRODUCIBILITY_STATEMENT.md`. Repository integrity conventions are described in `manifest.json` and `INTEGRITY.md`.

## Licensing

Citation metadata is maintained in `CITATION.cff`.

Original code/documentation: MIT. Third-party material retains its upstream license; see `licenses/THIRD_PARTY_MATERIALS.md`.
