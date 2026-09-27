# D27B — Publication repository hardening (v4.2.1)

Status: **PASS_D27B_LOCAL_REPOSITORY_REPRODUCTION / D27C_GITHUB_CI_PENDING**

This repository is the public-facing reproducibility core extracted from the larger
higher-dimension verification project.

It does **not** claim discovery of LED physics and does **not** claim that the target published
papers are wrong. Its purpose is to make the bounded open-reconstruction results independently
runnable.

## One-command reproduction

Requirements:
- Linux / WSL / macOS with Python 3.12 available as `python3.12`
- internet access for PyPI and public input retrieval

Run:

```bash
bash reproduce_all.sh
```

A successful reproducibility run ends with:

```text
PUBLIC_REPOSITORY_REPRODUCTION_PASS
```

Important: the D26C1 scientific result is expected to be
`FAIL_CLEAN_PUBLIC_DAYABAY_STANDARD3NU_CALIBRATION`. Reproducing that scientific FAIL is a
successful computational reproduction.

## What is reproduced

- D25G-R2:
  - N=192 crossing count = 39
  - N=384 crossing count = 17
  - topology verdict = `TOPOLOGY_N_DEPENDENT_HOLD`
- D26C1:
  - all 24 anchors execute successfully
  - absolute public-best χ² difference ≈ 16.1365 -> scientific FAIL
  - Spearman ≈ 0.904544 -> scientific FAIL
  - median |ΔΔχ²| ≈ 0.571954 -> PASS
  - p90 |ΔΔχ²| ≈ 2.553545 -> PASS
  - final scientific verdict = `FAIL_CLEAN_PUBLIC_DAYABAY_STANDARD3NU_CALIBRATION`

## Independent CI

`.github/workflows/reproduce.yml` is included. After publication to GitHub, it can execute the
same full reproduction on a GitHub-hosted Ubuntu runner.

## Licensing

Original code/documentation: MIT.

Third-party data/code are fetched from their authoritative locations and keep their upstream
licenses. See `licenses/THIRD_PARTY_MATERIALS.md`.

## Scientific scope

Read:
- `JOURNAL_FIT_AND_CLAIM_SCOPE.md`
- `REPRODUCIBILITY_STATEMENT.md`
- `paper/CLAIM_LEDGER.md`
- `SELF_HALLUCINATION_AUDIT.md`

## v4.2.1 runner-path correction

v4.2.0 incorrectly treated the parent directory of the repository as `ROOT` because
`reproduce_all.sh` is stored at repository root. v4.2.1 fixes only that path calculation
and adds an early repository-layout check. Scientific gates, expected results, and tolerances
are unchanged.

## v4.2.2 input-acquisition correction

The official Daya Bay `DayaBay_DeltaChiSq_NO_3158days.txt` file is acquired at runtime from official CaltechAUTHORS/arXiv routes with a frozen SHA-256 check. The five Newtrinos inputs remain commit-pinned runtime downloads. Scientific thresholds and expected results are unchanged.

## v4.2.3 result packaging

Every run now emits a result directory and, automatically:

```text
results/RUN_<timestamp>.zip
results/RUN_<timestamp>.zip.sha256
```

Upload those two files for audit. Scientific gates and expected results are unchanged.

## D27C GitHub CI

This repository is the publication-facing D27C source. Pushes to `main` run the full reproduction on GitHub-hosted Ubuntu.

## Publish this frozen D27C source

From this directory run:

```bash
bash publish_to_github.sh
```

The first push to `main` triggers the GitHub-hosted Ubuntu reproduction workflow.
