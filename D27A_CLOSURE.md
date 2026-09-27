# D27A closure

**Verdict: `PASS_FULL_CLEAN_RERUN`.**

The uploaded `FRESH_20260927T164208.zip` passed:
- outer SHA-256 sidecar verification;
- internal SHA inventory;
- D25G-R2 verdict, N=192/N=384 crossing counts and crossing-direction sequences;
- D26C1 verdict and gates;
- zero observed difference for the four key D26C1 comparison metrics in the frozen D27 comparison.

This establishes reproducibility of the project's selected computational outputs in newly created
clean virtual environments on the same WSL host. It does **not** establish an exact reproduction
of the target JHEP/Elaçmaz analyses.
