# Reproduction evidence index

## Supported replicated subset

The successful [Re] claim is restricted to the **Figure 1 Brane--Dirac spectrum** of de Giorgi, Pasari & Turner, JHEP 05 (2026) 152.

The public reproduction route starts from the published eigensystem, uses no target-author analysis code, and is invoked with:

```bash
python -m pip install -r environment/requirements-figure1-exact.txt
bash reproduce_figure1_revision2.sh
```

## Numerical checks

- nine pre-specified finite-KK / infinite-tower comparison points;
- target paper's >99% unitarity truncation criterion for all three Figure-1 parameter choices;
- all 3552 plotted roots directly compared with 80-digit solutions using the solver settings `xtol=1e-14`, `rtol=1e-13`.

The initial raw equation-residual acceptance criterion is retained in the provenance record; the final coordinate validation does not loosen it.

## Published-output graphical validation

Input identity:

`expected/FIGURE1_TARGET_PDF_SHA256.txt`

The workflow performs the following from scratch:
1. retrieve or accept the exact identified version-of-record PDF;
2. locate Figure 1 from its caption;
3. rasterize at 400, 600 and 800 dpi;
4. detect the plot frame and calibrate both logarithmic axes;
5. identify colored marker footprints at 15 pre-specified theoretical points;
6. generate the overlay and machine-readable point table;
7. evaluate the two partially obscured purple markers using a control-calibrated overlap test.

Result semantics:
- 12 points have direct graphical-footprint support;
- `mu1=10,n=5` and `mu1=10,n=10` are supported by the overlap/occlusion assessment;
- `mu1=0.1,n=20` remains insufficiently supported graphically.

The overlap controls are explicitly separated:
- `n=0`: full-marker shape reference;
- `n=1`: registration control;
- `n=2`: registration plus overplot/occlusion control.

The target registration threshold is the maximum control residual
`1.262472543657173` plus exactly one 400-dpi-equivalent pixel, giving
`2.262472543657173`.

See `docs/FIGURE1_GRAPHICAL_VALIDATION.md`.

## Claim boundary

This evidence does not establish Figure-5 exclusion-contour replication, exact target-likelihood replay, a new LED signal, or an error in the original article.
