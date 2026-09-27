# v4.2.3 packaging correction

v4.2.2 successfully reproduced the public-repository result but left only the result directory.
v4.2.3 adds automatic packaging:

- `<RUN>.zip`
- `<RUN>.zip.sha256`

The package is emitted after the internal SHA inventory is written. Early runner failures also
make a best-effort evidence bundle.

No scientific code, gate, expected value, tolerance, or interpretation is changed.
