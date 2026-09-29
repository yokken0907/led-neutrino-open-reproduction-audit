# Figure-1 partial replication — reviewer instructions

The manuscript's successful [Re] claim is limited to the Brane--Dirac spectrum in Figure 1 of de Giorgi, Pasari & Turner, JHEP 05 (2026) 152.

## Run

```bash
python -m pip install -r environment/requirements-figure1-exact.txt
bash reproduce_figure1_revision2.sh
```

Expected terminal line:

`FIGURE1_REVISION2_END_TO_END_REPRODUCTION_PASS`

This single route regenerates the equation-level spectrum, the finite-KK cross-check, the 3552-root high-precision comparison, and the published-output graphical validation directly from the identified version-of-record PDF.

The graphical step is defined as support by a detected rasterized marker footprint, not precision equality of the marker's digitized median coordinate. The output file
`results/figure1-revision2/graphical_summary/GRAPHICAL_VALIDATION_ANCHORS.csv`
lists every pre-specified test point and its status.

If the publisher changes PDF transport bytes, use a local copy matching
`expected/FIGURE1_TARGET_PDF_SHA256.txt` via `FIGURE1_TARGET_PDF`; the checksum requirement is not relaxed.

Scope: Figure 1 only. Figure-5 exclusion contours and experiment-level likelihoods are not claimed as replicated.
