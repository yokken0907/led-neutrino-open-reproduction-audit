# Reproduction evidence index

This file is a reviewer-facing index to the currently supported manuscript claim.

## Supported replicated subset

The successful replicated subset is **Figure 1 / the Brane-Dirac spectrum** of:

A. de Giorgi, D. Pasari, J. Turner, *Do neutrinos dream in 5D? Towards a comprehensive extra-dimensional neutrino phenomenology*, JHEP 05 (2026) 152.

The replication is limited to the computational core defined by the published Brane-Dirac eigensystem:
- physical roots of Eq. (3.26);
- normalization coefficients of Eq. (3.27);
- the unitarity sum of Eq. (3.28);
- the published Figure-1 parameter choices (m_D=1) and (mu_1={10,1,0.1}).

The calculation does not use target-author analysis code, Daya Bay likelihood code, Newtrinos, or the project's earlier LED likelihood kernel.

## Public source freeze

Manuscript-facing repository commit:

`73728590833e10c85eb2dd75bf844b825271b53d`

This is the merge commit for the Figure-1 partial-replication workflow.

Relevant public files:
- `code/d29a_figure1_replication.py`
- `code/d29b_conditioning_validation.py`
- `environment/requirements-figure1-exact.txt`
- `reproduce_figure1.sh`
- `.github/workflows/reproduce-figure1.yml`

## Independent numerical checks

D29A uses two independent numerical routes:
1. direct roots of the published infinite-tower Eq. (3.26);
2. a finite-KK implementation at (N=5000,10000,20000), followed by (1/N) Richardson extrapolation.

All nine frozen triangulation anchors pass. The maximum absolute root difference is:

`1.2910152946687958e-09`

The paper's >99% unitarity criterion is also satisfied for all three Figure-1 parameter choices:
- (mu_1=10): (sum N_lambda^2=0.9996850466854103)
- (mu_1=1): (sum N_lambda^2=0.9921727356755364)
- (mu_1=0.1): (sum N_lambda^2=0.9938965788157853)

## Preserved D29A diagnostic failure and D29B correction

D29A deliberately preserves the original automatic result:

`FAIL_FIGURE1_COMPUTATIONAL_CORE_REPLICATION_GATE`

The only failing diagnostic is a raw Eq. (3.26) residual threshold applied to high cotangent modes.

D29B does not relax that raw-residual threshold. It evaluates conditioning-aware coordinate backward error across all 3552 plotted roots and checks the two diagnostic worst cases at high precision.

D29B results:
- roots checked: `3552`
- all roots within requested solver coordinate tolerance: `true`
- maximum normalized backward error: `0.25009539975842393`
- high-precision worst-case mass differences: approximately (2.9	imes10^{-12}) and (2.7	imes10^{-12})

Bounded final verdict:

`PASS_FIGURE1_COMPUTATIONAL_CORE_INDEPENDENT_REPLICATION_AFTER_CONDITIONING_AUDIT`

The original D29A automatic FAIL remains in the audit trail.

## External GitHub-hosted reproduction

GitHub Actions run:

`36403948683`

Workflow:
`Reproduce Figure-1 partial replication`

Runner:
- Ubuntu 24.04.5
- Python 3.12.14

The hosted run completed successfully and emitted:

`FIGURE1_REPLICATION_CI_PASS`

Uploaded artifact:
- name: `figure1-replication-results`
- artifact ID: `10962090038`
- size: `203948` bytes
- SHA-256: `9f0d1b782f9995f2c4379446e5af4c7aadb46c375a7096b66610dba36823cea3`

The downloaded artifact SHA-256 was independently rechecked against the GitHub-recorded digest and matched exactly.

## One-command local reproduction

```bash
python -m pip install -r environment/requirements-figure1-exact.txt
bash reproduce_figure1.sh
```

Expected final bounded verdict:

```text
PASS_FIGURE1_COMPUTATIONAL_CORE_INDEPENDENT_REPLICATION_AFTER_CONDITIONING_AUDIT
```

## Explicit claim boundary

This evidence supports a **partial computational replication of Figure 1 only**.

It does not establish:
- Figure-5 exclusion-contour replication;
- exact replay of the target experimental likelihood;
- replication of the Daya Bay or MINOS/MINOS+ exclusion analysis;
- a new LED signal;
- an error in the original JHEP article.

Reviewer-driven follow-up found the Figure-5 open reconstruction to have unresolved local threshold topology. Historical D25/D26 outputs are retained for provenance but do not define the current manuscript claim.
