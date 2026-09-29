# Reproducibility statement

The manuscript-facing successful replication claim is restricted to the Brane--Dirac spectrum in Figure 1 of de Giorgi, Pasari & Turner, JHEP 05 (2026) 152.

A third party can run the current workflow with:

```bash
python -m pip install -r environment/requirements-figure1-exact.txt
bash reproduce_figure1_revision2.sh
```

or equivalently with the repository Dockerfile. The workflow:

1. solves the published eigensystem and performs the finite-KK cross-check;
2. directly re-solves all 3552 roots generated over the Figure-1 plotting range at 80-digit precision;
3. verifies the version-of-record PDF by SHA-256;
4. rasterizes Figure 1 at 400, 600 and 800 dpi, calibrates the axes, and regenerates the 15-point graphical-footprint table and overlay;
5. applies the separately calibrated overlap/occlusion assessment to the two partially obscured purple markers.

Expected terminal line:

```text
FIGURE1_REVISION2_END_TO_END_REPRODUCTION_PASS
```

The current manuscript does not claim replication of Figure 5 or of the target authors' experimental likelihoods. Earlier exploratory Figure-5 and Daya Bay analyses are retained only as provenance and scope history; they do not define the current [Re] result or its executable acceptance path.

Older workflows and documents have been moved under `provenance/superseded/` when they contain withdrawn interpretations. They are retained for research history only.
