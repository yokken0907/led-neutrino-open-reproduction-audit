# Platform and execution information

This directory supports the manuscript-facing Figure-1 replication.

## Reference platform

Docker provides the most explicit reference environment:

- Platform: Linux
- Architecture: x86_64 for the hosted reference run
- Reference container: `python:3.12.3-slim`
- Python: 3.12.3
- NumPy: 2.5.3
- SciPy: 1.18.1
- matplotlib: 3.10.7
- mpmath: 1.3.0
- Pillow: 11.3.0
- PyMuPDF: 1.26.4

The hosted CI uses GitHub Ubuntu 24.04 with Python 3.12 and installs the same version-pinned Python dependencies from `environment/requirements-figure1-exact.txt`. Each run writes `PLATFORM_INFO.txt` into the archived result artifact so that the tested operating system, kernel release, machine architecture, Python version, and implementation are recorded rather than inferred.

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
