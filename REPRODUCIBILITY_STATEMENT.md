# Reproducibility statement

The repository is designed so that a third party can run:

```bash
bash reproduce_all.sh
```

The runner:
1. obtains public third-party inputs from pinned authoritative locations;
2. verifies their SHA-256 hashes;
3. creates two clean Python 3.12 environments;
4. installs frozen dependencies;
5. reruns the D26C1 public standard-3ν calibration and D25G-R2 KK-truncation topology test;
6. compares the outputs to frozen expected results using predeclared tolerances and exact categorical checks;
7. records manifests and SHA-256 inventories.

A GitHub Actions workflow is included to make the same test executable on an independent
GitHub-hosted Ubuntu runner after publication of the repository.

The expected scientific outcome includes a D26C1 scientific FAIL. That FAIL is itself a
reproduced result and must not be treated as an execution failure.
