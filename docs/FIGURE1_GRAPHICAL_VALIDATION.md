# Published Figure 1 graphical-output validation

This workflow makes the manuscript's published-output check reproducible from the version-of-record PDF rather than rechecking archived evidence tables.

## Input identity

The target is the open-access version-of-record PDF for de Giorgi, Pasari & Turner, JHEP 05 (2026) 152. The workflow requires SHA-256

`2850f1c631b07de992cc72dd2b9c8aab80c10e7bccf51a421d90e80373f627c3`.

The PDF is not committed to this repository. It is downloaded from the publisher by default and its hash is checked before analysis. A reviewer may instead set `FIGURE1_TARGET_PDF` to a local copy with the same hash.

## Initial graphical-footprint validation

The PDF page containing Figure 1 is located from caption text, then rendered independently at 400, 600, and 800 dpi. Axis coordinates are calibrated from printed major-tick strokes at each resolution. Fifteen pre-specified mode indices are tested across three saturation thresholds. A supported point means that the theoretical coordinate is consistent with the detected rasterized colored-marker footprint after only the measured axis-calibration residual and one raster-pixel allowance. It does **not** mean that the digitized median coordinate is a precision measurement of the theoretical coordinate.

The initial detector gives 12 robust graphical-footprint supports, two apparent contradictions for the purple mu1=10 series (n=5,10), and one point with insufficient graphical support (mu1=0.1,n=20).

## Occlusion assessment

The apparent n=5 and n=10 contradictions are assessed separately using the visible edges of the purple downward-triangle glyphs.

Control roles are deliberately distinguished:

- mu1=10,n=0: full-marker glyph reference;
- mu1=10,n=1: registration control. It passes registration in 9/9 estimates and does not show the positive occlusion signature (0/9);
- mu1=10,n=2: registration control and positive overplot/occlusion-signature control. It passes both in 9/9 estimates.

The registration threshold is target-independent. The maximum registration residual across n=1 and n=2 is 1.262472543657173 400-dpi-equivalent pixels. Adding exactly one 400-dpi-equivalent raster pixel gives the target threshold 2.262472543657173 pixels. The n=5 and n=10 target residuals are not used to construct the threshold.

The occlusion signature requires all four of the following conditions: the visible purple component is at most 80% of the reference width, at most 80% of the reference height, blue/green pixels occupy at least 10% of the predicted full-marker box, and the visible purple bounding box remains contained within the reference-derived full-marker box with a one-scaled-pixel allowance.

Both targets pass registration and this independently specified occlusion signature in all 9/9 dpi/saturation estimates. The original initial-detector result is retained unchanged; the second test explains those two apparent contradictions as marker-overplot/occlusion cases.

## Combined manuscript-facing result

- mu1=10: 3 direct graphical-footprint supports + 2 occlusion-supported markers = 5/5 supported;
- mu1=1: 5/5 direct graphical-footprint supports;
- mu1=0.1: 4/5 direct graphical-footprint supports; n=20 remains insufficient.

The fixed adequacy rule is at least 4/5 supported pre-specified test points for each mu1.

The generated `GRAPHICAL_VALIDATION_ANCHORS.csv` lists all 15 mode indices, theoretical coordinates, digitized median coordinates, initial detector status, and manuscript-facing interpretation.