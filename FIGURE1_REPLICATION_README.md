# Figure-1 partial replication update

This update adds the manuscript's current successful replication target: the Brane-Dirac spectrum in Figure 1 of de Giorgi, Pasari & Turner, JHEP 05 (2026) 152.

Run locally from the repository root:

```bash
python -m pip install -r environment/requirements-figure1-exact.txt
bash reproduce_figure1.sh
```

The one-command run intentionally preserves the D29A automatic raw-residual FAIL and then executes the conditioning-aware D29B audit. The manuscript-level bounded result is the D29B verdict:

`PASS_FIGURE1_COMPUTATIONAL_CORE_INDEPENDENT_REPLICATION_AFTER_CONDITIONING_AUDIT`

Scope boundary: this is a partial replication of the Figure-1 Brane-Dirac spectrum/eigensystem only. It is not a reproduction of the Figure-5 exclusion likelihood or an experimental constraint replication.
