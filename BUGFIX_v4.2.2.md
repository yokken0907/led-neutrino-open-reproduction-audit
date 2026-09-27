# v4.2.2 bugfix

Observed v4.2.1 failure:

```text
urllib.error.HTTPError: HTTP Error 403: Forbidden
```

The five pinned Newtrinos files downloaded successfully. The failure occurred only for the
CaltechAUTHORS supplemental-file endpoint.

v4.2.2 removes that fragile runtime dependency by bundling the exact official Daya Bay
supplemental file already used and audited in D26C1/D27A:

- file: `inputs/d26c1/DayaBay_DeltaChiSq_NO_3158days.txt`
- source: CaltechAUTHORS record `1g2ty-5pk30`, supplemental material to
  Daya Bay, Phys. Rev. Lett. 130, 161802 (2023)
- SHA-256: `52986e39f7844f157d064ba8c88ca2a692b39e6e915a994c039fb15a9538fa84`

The file is verified before every run. The repository MIT license does not relicense this
third-party supplemental material; attribution and upstream rights remain intact.

No scientific gate, expected result, tolerance, or interpretation was changed.
