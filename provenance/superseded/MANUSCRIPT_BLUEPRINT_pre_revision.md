> **SUPERSEDED — retained for provenance only.**
> This document predates the current ReScience C manuscript and contains withdrawn or obsolete interpretations. Do not use it to interpret the current manuscript. See the repository README and REPRODUCTION_EVIDENCE.md for the current claim and reproduction route.

# Manuscript blueprint

## Working title
**An open computational audit of large-extra-dimension neutrino constraints**

## Article type
Partial/open computational replication and reproducibility audit.

## Core question
To what extent can published LED-neutrino exclusion behavior be reconstructed from public
data and open implementations, and which apparent residual structures survive numerical and
standard-3ν calibration checks?

## Abstract skeleton
We report an independent open reconstruction attempt of published neutrino constraints on
large extra dimensions. Rather than treating visual contour agreement as sufficient evidence,
we used frozen acceptance gates, alternative public likelihood implementations, KK-truncation
tests, and a clean standard-three-neutrino calibration. The open implementations materially
shifted inferred exclusion boundaries. A high-KK threshold topology changed from 39 crossings
at N=192 to 17 at N=384 and failed the frozen stability criterion. In a clean public Daya Bay
standard-3ν calibration, all 24 anchors executed successfully, but the absolute best-fit χ²
difference (16.1365) and Spearman rank correlation (0.9045 < 0.95) failed predeclared gates,
while median and p90 ΔΔχ² diagnostics passed. A full clean-environment rerun reproduced these
results. We therefore do not claim a new LED signal, an exact reproduction of the target
published contours, or an error in the original analyses. The result is instead a bounded
reproducibility finding: under available public reconstruction routes, the inferred boundary
is materially implementation-sensitive and residual micro-topology is not stable enough for
physical interpretation.

## Main sections
1. Motivation and scope
2. Target published analyses and public authority boundary
3. Reproduction protocol and frozen gates
4. Figure-5/6 open reconstruction mismatch
5. Public-likelihood implementation sensitivity
6. KK-truncation topology test
7. Standard-3ν calibration
8. D27 clean-environment reproducibility hardening
9. Limitations: public/private analysis boundary
10. Conclusions

## Mandatory limitations
- No exact JHEP author-likelihood replay.
- No exact Elaçmaz replay.
- No author-private dataset reconstruction.
- No claim that the published analyses are wrong.
- No physical interpretation of N-dependent micro-crossings.

## Proposed central contribution
A gate-frozen, independently rerunnable open audit demonstrating how an apparently attractive
near-match was prevented from becoming a new-physics claim when truncation stability and
standard-model calibration failed.
