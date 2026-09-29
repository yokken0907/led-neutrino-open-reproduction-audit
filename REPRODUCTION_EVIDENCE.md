# Reproduction evidence index

This is the reviewer-facing index for the bounded ReScience C manuscript claim.

## Supported replicated subset

The successful replicated subset is **Figure 1 / the Brane-Dirac spectrum** of:

A. de Giorgi, D. Pasari, J. Turner, *Do neutrinos dream in 5D? Towards a comprehensive extra-dimensional neutrino phenomenology*, JHEP 05 (2026) 152.

The claim is restricted to the computational content of the published Brane-Dirac eigensystem:
- physical roots of Eq. (3.26);
- normalization coefficients of Eq. (3.27);
- the unitarity sum of Eq. (3.28);
- the published Figure-1 parameter choices `m_D=1` and `mu_1={10,1,0.1}`.

Not claimed: Figure-5 exclusion-contour replication, replay of the target-author experimental likelihood, a new LED signal, or an error in the original article.

## Numerical core: D29A/D29B

D29A independently reimplements the published infinite-tower equation and cross-checks it with a mathematically distinct finite-KK route at N=5000,10000,20000 followed by leading-1/N Richardson extrapolation.

All nine pre-specified triangulation anchors pass. The maximum absolute root difference is:

`1.2910152946687958e-09`

The paper's >99% unitarity truncation criterion is satisfied for all three published Figure-1 parameter choices:
- mu1=10: `0.9996850466854103`
- mu1=1: `0.9921727356755364`
- mu1=0.1: `0.9938965788157853`

D29A deliberately preserves the original automatic raw-equation-residual verdict:

`FAIL_FIGURE1_COMPUTATIONAL_CORE_REPLICATION_GATE`

D29B diagnoses why that raw residual is a poor coordinate-accuracy metric near cotangent poles using the Newton correction / derivative-scaled residual `|F/F'|`. It does not erase the D29A failure.

## Direct all-root high-precision validation: D29C

D29C directly re-solves all 3552 plotted roots at 80-digit precision and compares the stored binary64 roots with the high-precision solutions using the pre-existing Brent coordinate tolerance `xtol + rtol*|y|`.

Authority-run result:
- roots checked: 3552 / 3552
- maximum binary64 error / inherited solver tolerance: `0.25033133171637295`
- maximum binary64 |Delta m|: `7.65012708620728e-12`
- maximum stored high-precision equation residual: approximately `2.80e-54`
- verdict: `PASS_D29C_ALL_3552_ROOTS_HIGH_PRECISION_DIRECT_VALIDATION`

This direct comparison is the primary root-coordinate accuracy evidence in Revision 1.

## Direct comparison with the published Figure 1: D30A/D30B

D30A compares 15 pre-specified graphical anchors with the version-of-record Figure 1 at 400/600/800 dpi and multiple saturation thresholds. The target PDF is SHA-pinned.

The frozen D30A machine result is preserved:
- 12 / 15 robust direct graphical matches;
- two robust machine mismatches at mu1=10, n=5 and n=10;
- one insufficient-support anchor at mu1=0.1, n=20;
- machine verdict: `FAIL_DIRECT_TARGET_OUTPUT_DISAGREEMENT`.

D30B separately adjudicates only the two D30A contradictions. Its positive-control-derived threshold excludes the target anchors from threshold construction. Both n=5 and n=10 pass registration and independent occlusion-signature checks across all tested dpi/saturation combinations.

D30B verdict:

`PASS_D30B_OCCLUSION_ARTIFACT_CONFIRMED`

Combined bounded graphical support:
- mu1=10: 3/5 direct + 2/5 occlusion-adjudicated = 5/5 supported;
- mu1=1: 5/5 direct;
- mu1=0.1: 4/5 direct; n=20 remains insufficient graphical support.

The D30A machine FAIL is not retroactively rewritten.

## Local one-command workflows

Original numerical-core workflow:

```bash
python -m pip install -r environment/requirements-figure1-exact.txt
bash reproduce_figure1.sh
```

Revision-1 reviewer-facing workflow:

```bash
python -m pip install -r environment/requirements-revision1-exact.txt
bash reproduce_revision1.sh
```

The Revision-1 runner performs D29A/B, all-root D29C, SHA-pinned version-of-record acquisition, D30A, D30B, and a final bounded claim gate.

## Hosted CI

The earlier public D29A/D29B workflow passed on GitHub Actions run `36403948683`, artifact ID `10962090038`.

Revision-1 hosted CI is defined in:

`.github/workflows/reproduce-revision1.yml`

Its fresh hosted result is intentionally not claimed until the pull-request/main run has completed and its artifact has been independently audited.

## Historical supersession

Historical D25/D26/D27 files remain for provenance. Later matched-grid and public-fit controls superseded earlier interpretations of Figure-5 threshold topology and Daya Bay calibration. Those historical files are not the current manuscript claim.
