# Code and data availability

The manuscript-facing replication code is public in this repository under the MIT license.

The successful [Re] claim is restricted to the Figure-1 Brane--Dirac spectrum. It requires no experimental event-level data or Daya Bay likelihood surface. The numerical spectrum is regenerated from the published equations, while the graphical validation uses the exact version-of-record target PDF identified by SHA-256:

`2850f1c631b07de992cc72dd2b9c8aab80c10e7bccf51a421d90e80373f627c3`.

The target article PDF and any other third-party material retain their upstream copyright and license terms; see `licenses/THIRD_PARTY_MATERIALS.md`.

Current reviewer entry point:

```bash
python -m pip install -r environment/requirements-figure1-exact.txt
bash reproduce_figure1_revision2.sh
```

The same route is the Docker entry point and the only active GitHub Actions reproduction workflow.

Daya Bay material appears only in historical auxiliary analyses that are outside the successful [Re] claim. Those historical analyses are retained as provenance and are not inputs to the manuscript-facing Figure-1 workflow.
