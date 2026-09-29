# Repository integrity model

The obsolete D27 whole-tree `SHA256SUMS.txt` is no longer presented at repository root as if it described the current tree.

For the current submission:

1. the exact Git commit named in the manuscript identifies the repository state;
2. `expected/FIGURE1_TARGET_PDF_SHA256.txt` fixes the target version-of-record PDF;
3. `environment/requirements-figure1-exact.txt` fixes Python package versions;
4. the successful GitHub Actions run records the clean hosted execution;
5. the SHA-256 digest reported by GitHub for the uploaded end-to-end artifact identifies the generated result bundle.

The former D27 checksum list and manifest are retained under `provenance/superseded/d27/` for historical traceability only.
