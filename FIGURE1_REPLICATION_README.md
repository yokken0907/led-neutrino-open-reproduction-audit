# Figure-1 partial replication - Revision 1

The successful ReScience C replication target is the Brane-Dirac spectrum in Figure 1 of de Giorgi, Pasari & Turner, JHEP 05 (2026) 152.

## One-command run

```bash
python -m pip install -r environment/requirements-figure1-exact.txt
bash reproduce_figure1_revision1.sh
```

This run:
1. executes D29A and preserves its historical raw-residual automatic FAIL;
2. executes the D29B conditioning-aware diagnostic;
3. executes D29C, directly comparing all 3552 plotted binary64 roots with 80-digit roots under the inherited Brent coordinate tolerance;
4. rechecks the frozen D30 direct-output evidence tables and fixed 4/5-per-mu_1 coverage rule.

Expected terminal line:

`FIGURE1_REVISION1_REPRODUCTION_PASS`

D30 boundary: hosted CI rechecks the frozen D30A/D30B evidence tables rather than rerasterizing the publisher PDF. The underlying raster authority runs remain archived separately.

Scope: Figure-1 Brane-Dirac spectrum only. Figure-5 exclusion likelihoods and experimental constraints are not claimed as replicated.
