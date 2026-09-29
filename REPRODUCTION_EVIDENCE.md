# Reproduction evidence index - Revision 1

## Supported subset

Successful [Re] claim: **Figure 1 / Brane-Dirac spectrum only** from de Giorgi, Pasari & Turner, JHEP 05 (2026) 152.

The calculation is based on published Eqs. (3.26)-(3.28) for m_D=1 and mu_1={10,1,0.1}, without target-author analysis code.

## Public Revision-1 workflow

Relevant files:
- `code/d29a_figure1_replication.py`
- `code/d29b_conditioning_validation.py`
- `code/d29c_all_root_high_precision.py`
- `code/d30c_revision1_evidence_check.py`
- `expected/D30_DIRECT_OUTPUT_ANCHORS.csv`
- `expected/D30_OCCLUSION_ADJUDICATION.csv`
- `environment/requirements-figure1-exact.txt`
- `reproduce_figure1_revision1.sh`
- `.github/workflows/reproduce-figure1-revision1.yml`

## Numerical evidence

Nine finite-KK/infinite-tower pre-specified anchors agree to at worst 1.2910152946687958e-09 in mass.

The >99% unitarity criterion is satisfied:
- mu_1=10: 0.9996850466854103
- mu_1=1: 0.9921727356755364
- mu_1=0.1: 0.9938965788157853

D29A's historical raw-residual automatic FAIL is preserved. D29B diagnoses the conditioning issue. D29C then directly re-solves all 3552 plotted roots at 80-digit precision; all pass the inherited Brent coordinate tolerance. The authority-run maximum binary64 error/tolerance ratio is 0.2503313317163729.

## Published-output evidence

Frozen D30 direct-output evidence:
- mu_1=10: 3 direct robust matches + 2 separately adjudicated marker-occlusion cases = 5/5 supported;
- mu_1=1: 5/5 direct robust matches;
- mu_1=0.1: 4/5 direct robust matches; n=20 remains insufficient graphical support.

The fixed adequacy rule is at least 4/5 supported anchors for each mu_1. The manuscript does not claim 15/15 direct graphical recovery.

The hosted D30C check validates these frozen machine-readable tables and coverage logic; it does not rerasterize the publisher PDF.

## One-command local reproduction

```bash
python -m pip install -r environment/requirements-figure1-exact.txt
bash reproduce_figure1_revision1.sh
```

Expected terminal line:

`FIGURE1_REVISION1_REPRODUCTION_PASS`

## Claim boundary

This does not establish Figure-5 exclusion-contour replication, exact replay of the target likelihood, a new LED signal, or an error in the original article.
