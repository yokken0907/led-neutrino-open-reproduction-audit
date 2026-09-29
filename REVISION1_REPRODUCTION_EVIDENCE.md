# Revision-1 Figure-1 reproduction evidence

The manuscript's successful claim remains limited to the Brane--Dirac spectrum in Figure 1 of de Giorgi, Pasari & Turner, JHEP 05 (2026) 152.

Run:

```bash
python -m pip install -r environment/requirements-figure1-exact.txt
bash reproduce_figure1_revision1.sh
```

The workflow performs:
1. D29A published-equation Figure-1 calculation, preserving its historical raw-residual automatic FAIL.
2. D29B conditioning-aware diagnostic.
3. D29C direct 80-digit comparison of all 3552 plotted roots against the inherited Brent coordinate tolerance.
4. D30C recheck of the frozen direct target-output evidence tables: 12 direct robust matches, two mu1=10 anchors adjudicated as overlap/occlusion artifacts, and one mu1=0.1,n=20 anchor retained as insufficient graphical support. The pre-specified 4/5 coverage rule is satisfied for each mu1.

Important boundary: the hosted D30C step rechecks the frozen evidence tables; it does not rerasterize the publisher PDF. The underlying D30A/D30B authority runs and overlays are preserved in the manuscript audit archive.

Expected terminal line:

`FIGURE1_REVISION1_REPRODUCTION_PASS`
