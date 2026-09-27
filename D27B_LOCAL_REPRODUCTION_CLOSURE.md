# D27B local public-repository reproduction closure

**Verdict: `PASS_PUBLIC_REPOSITORY_REPRODUCTION`.**

Audited result:
- archive: `RUN_20260927T203511.zip`
- outer SHA-256: `b53453545c8f3293f6ee4656f5f882ad6da87a0241a88a8dd9df27c3412b2952`
- outer sidecar: PASS
- internal SHA inventory: 93/93 PASS
- manifest status: `PUBLIC_REPOSITORY_REPRODUCTION_PASS`
- D25G-R2 categorical comparison: PASS
- D26C1 verdict/gates comparison: PASS
- D26C1 key metric deltas: all exactly `0.0`
- overall comparison: PASS

This establishes that the public-facing repository runner, using newly created environments
and the repository-packaged/pinned inputs, reproduced the selected D25G and D26C1 results on
the user's WSL host.

It does not upgrade the physics claim. The D26C1 scientific calibration verdict remains FAIL,
and no LED signal or exact reproduction of the target published contours is claimed.

Remaining external step:
- run the same repository on an independent hosted Ubuntu environment (e.g. GitHub Actions).

v4.2.3 changes only result packaging: every normal PASS/HOLD run and early runner failure now
attempts to emit `<RUN>.zip` plus `<RUN>.zip.sha256`.
