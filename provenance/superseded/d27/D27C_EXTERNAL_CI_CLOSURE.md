> **SUPERSEDED — historical provenance only.**
> This file predates the current ReScience C manuscript and is retained only to preserve analysis history. It must not be used as current scientific interpretation or current execution instructions. See `README.md`, `paper/CURRENT_CLAIM.md`, `REPRODUCTION_EVIDENCE.md`, and `REPRODUCIBILITY_STATEMENT.md`.

# D27C External CI Closure

**Verdict: PASS_EXTERNAL_GITHUB_HOSTED_UBUNTU_REPRODUCTION**

Repository: `yokken0907/led-neutrino-open-reproduction-audit`

GitHub Actions evidence:
- workflow run: `36330798891`
- commit: `5095642ab8dfcf91d8d227dfd1c9d164033dd640`
- overall workflow conclusion: `success`
- full reproduction step: `success`
- evidence upload step: `success`
- artifact: `d27b-reproduction-results`
- artifact digest: `sha256:e5cbf7ad5b9c53ba953d1896b59a96bac944fae47da280c79ed07a24dd19dbbc`

Independent artifact audit:
- artifact ZIP SHA-256: `e5cbf7ad5b9c53ba953d1896b59a96bac944fae47da280c79ed07a24dd19dbbc`
- internal integrity: `93/93 PASS`
- D27B comparison: `overall_pass = true`
- D25G-R2 verdict: `TOPOLOGY_N_DEPENDENT_HOLD`
- N=192 crossing count: `39`
- N=384 crossing count: `17`
- D26C1 verdict: `FAIL_CLEAN_PUBLIC_DAYABAY_STANDARD3NU_CALIBRATION`
- D26C1 all gate statuses reproduced
- D26C1 metric deltas versus frozen expected results:
  - profiled public-best absolute chi-square difference: `3.410605131648481e-13`
  - Spearman rho: `0.0`
  - median absolute delta difference: `2.1435653252410702e-10`
  - p90 absolute delta difference: `5.004885395010206e-13`

Interpretation boundary:
- This is strong evidence that the selected open reconstruction outputs are reproducible on an independent GitHub-hosted Ubuntu runner.
- It does not establish a new LED signal.
- It does not establish an exact reproduction of the target published JHEP contours or Elaçmaz analysis.
- It does not establish that the original papers are wrong.
- The D26C1 scientific calibration remains FAIL by the frozen gates; reproducing that FAIL is the successful reproducibility result.

D27C is closed PASS.
