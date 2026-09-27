# v4.2.1 bugfix

Observed v4.2.0 failure:

```text
python3.12: can't open file '/mnt/c/Users/KEI/Downloads/code/fetch_public_inputs.py'
```

Cause: `reproduce_all.sh` is located at repository root, but computed `ROOT` as the
parent of its own directory.

Correction:

```bash
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
```

No scientific gate, expected value, tolerance, authority hash, or interpretation was changed.
