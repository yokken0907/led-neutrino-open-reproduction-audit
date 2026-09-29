# Reproducibility statement

The current ReScience Revision-1 claim is intentionally bounded to the Figure-1 Brane-Dirac spectrum subset.

A third party can install the version-pinned environment and run:

```bash
python -m pip install -r environment/requirements-revision1-exact.txt
bash reproduce_revision1.sh
```

The runner:
1. reruns the public D29A/D29B Figure-1 numerical-core workflow;
2. directly re-solves all 3552 plotted roots at 80-digit precision in D29C;
3. downloads the version-of-record target article from the publisher and requires the fixed SHA-256 before any graphical analysis;
4. runs the D30A direct published-output comparison at 400/600/800 dpi;
5. preserves the frozen D30A automatic mismatch verdict rather than rewriting it;
6. runs the separately frozen D30B occlusion adjudication for only the two pre-identified contradictory anchors;
7. applies a final bounded gate requiring the combined Figure-1 evidence while leaving Figure 5 outside the successful-replication claim.

The expected terminal marker is:

`REVISION1_REPRODUCTION_CI_PASS`

The workflow is also exercised by:

`.github/workflows/reproduce-revision1.yml`

GitHub-hosted CI is supporting evidence, not a substitute for the ReScience reviewer rerunning the code.

## Historical workflow

`bash reproduce_all.sh` and `.github/workflows/reproduce.yml` remain as the earlier D27 historical reproducibility record. They do not define the current manuscript interpretation.
