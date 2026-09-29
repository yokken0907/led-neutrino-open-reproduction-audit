> **SUPERSEDED — retained for provenance only.**
> This document predates the current ReScience C manuscript and contains withdrawn or obsolete interpretations. Do not use it to interpret the current manuscript. See the repository README and REPRODUCTION_EVIDENCE.md for the current claim and reproduction route.

# D27B submission readiness

## Passed
- D27A clean-environment rerun: PASS.
- Frozen D25G categorical results reproduced.
- Frozen D26C1 gates and key metrics reproduced.
- Exact dependency versions captured.
- Public-repository runner no longer depends on the user's pre-existing virtual environments.
- Runtime third-party input fetches are hash-pinned.
- Original code has an explicit open-source license.
- GitHub Actions clean-machine workflow prepared.
- Manuscript claim boundaries frozen.

## Pending before actual journal submission
1. Publish this repository to a public Git host.
2. Run the included GitHub Actions workflow successfully on the hosted runner.
3. Archive the successful tagged release in Zenodo and obtain a DOI.
4. Build the journal manuscript from the blueprint.
5. Decide the journal after final manuscript-fit audit.
6. If targeting ReScience C specifically, phrase the work as partial/open replication unless
   substantially stronger evidence justifies a failed-replication claim.

## Current verdict
**`PASS_D27B_LOCAL_REPOSITORY_REPRODUCTION / D27C_GITHUB_CI_PENDING`**

## D27B local full reproduction evidence

`RUN_20260927T203511.zip` was independently audited with SHA-256 `b53453545c8f3293f6ee4656f5f882ad6da87a0241a88a8dd9df27c3412b2952`.
All internal SHA entries passed and the frozen D25G/D26C1 comparison returned overall PASS.
