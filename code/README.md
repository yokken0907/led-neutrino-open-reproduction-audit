# Platform and execution information

This directory supports the manuscript-facing Figure-1 replication.

## Reference platform

Docker provides the most explicit platform pin:

- Python: 3.12.3 (`python:3.12.3-slim`)
- NumPy: 2.5.3
- SciPy: 1.18.1
- matplotlib: 3.10.7
- mpmath: 1.3.0
- Pillow: 11.3.0
- PyMuPDF: 1.26.4

The hosted CI uses GitHub's Ubuntu runner with Python 3.12 and installs the same version-pinned Python dependencies from `environment/requirements-figure1-exact.txt`.

## Reviewer execution

From the repository root:

```bash
python -m pip install -r environment/requirements-figure1-exact.txt
bash reproduce_figure1_revision2.sh
```

or:

```bash
docker build -t led-figure1-replication .
docker run --rm led-figure1-replication
```

Expected terminal line:

`FIGURE1_REVISION2_END_TO_END_REPRODUCTION_PASS`

The current successful [Re] claim is Figure 1 only. Historical D25-D27 material is retained for provenance and is not part of the reviewer execution route.
