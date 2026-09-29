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

The workflow performs four layers:

1. solve the published infinite-tower eigensystem and cross-check nine pre-specified roots with a mathematically distinct finite-KK calculation;
2. validate all 3552 binary64 roots generated over the Figure-1 plotting range by direct 80-digit re-solution;
3. obtain the exact version-of-record PDF identified by SHA-256
   `2850f1c631b07de992cc72dd2b9c8aab80c10e7bccf51a421d90e80373f627c3`,
   rasterize Figure 1 at 400/600/800 dpi, calibrate its axes, detect the colored marker footprints, and regenerate the 15-point graphical-validation table and overlay;
4. apply the separately specified marker-overlap assessment to the two purple markers requiring occlusion treatment.

If publisher transport bytes change, supply the exact identified PDF locally:

```bash
FIGURE1_TARGET_PDF=/path/to/JHEP05_2026_152.pdf bash reproduce_figure1_revision2.sh
```

The SHA-256 check is not relaxed.

## Graphical validation semantics

The initial graphical comparison evaluates whether each theoretical point is supported by the detected **rasterized colored-marker footprint**. It is not a claim that the median digitized marker coordinate equals the theoretical coordinate to high precision.

The 15 pre-specified test points yield:
- 12 direct graphical-footprint supports;
- two `mu1=10` markers (`n=5,10`) that require a control-calibrated overlap/occlusion assessment;
- one `mu1=0.1,n=20` point with insufficient graphical support.

For the occlusion assessment:
- `n=0` is the full purple-marker shape reference;
- `n=1` is the registration control;
- `n=2` is the registration plus overplot/occlusion control;
- `n=5,10` are the assessed targets.

The registration threshold is constructed as the maximum control edge-registration residual,
`1.262472543657173` 400-dpi-equivalent pixels, plus exactly one 400-dpi-equivalent pixel:
`2.262472543657173` pixels.

See `docs/FIGURE1_GRAPHICAL_VALIDATION.md`. The one-command workflow writes
`GRAPHICAL_VALIDATION_ANCHORS.csv` containing all 15 test points, theory coordinates, graphical estimates, and statuses.

## Docker

The Docker entry point is the same manuscript workflow:

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

The older `reproduce_all.sh` and D25--D27 material are retained only as historical provenance and do not define the manuscript-facing reproduction route.

Documents containing withdrawn pre-revision interpretations have been moved under `provenance/superseded/` and carry an explicit superseded notice. The current claim is summarized in `paper/CURRENT_CLAIM.md`; the current executable scope is stated in `REPRODUCIBILITY_STATEMENT.md`.

## Licensing

Original code/documentation: MIT. Third-party material retains its upstream license; see `licenses/THIRD_PARTY_MATERIALS.md`.
