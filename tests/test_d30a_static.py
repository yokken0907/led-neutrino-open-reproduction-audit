from pathlib import Path
import importlib.util, math, numpy as np

root=Path(__file__).resolve().parents[1]
p=root/"code"/"d30a_figure1_direct_output_validation.py"
sp=importlib.util.spec_from_file_location("d30a",p)
m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m)

# Equation anchors already independently known from D29A.
assert abs(m.root_eq326(10.0,0)-0.9838450147121393)<1e-12
assert abs(m.nlambda(m.root_eq326(10.0,0),10.0)-0.9837434208391374)<1e-12
assert abs(m.root_eq326(0.1,0)-0.04994939072873661)<1e-12

# Calibration algebra sanity.
cal={
"log10x_per_pixel":0.01,"log10x_intercept":-2.0,
"log10y_per_pixel":-0.01,"log10y_intercept":0.2
}
for x,y in [(0.1,1.0),(1.0,0.1),(10.0,0.01)]:
    px,py=m.xy_to_pix(x,y,cal)
    xx,yy=m.pix_to_xy(px,py,cal)
    assert abs(xx/x-1)<1e-12 and abs(yy/y-1)<1e-12

assert sum(len(v) for v in m.ANCHORS.values())==15
print("D30A_STATIC_EQUATION_CALIBRATION_TEST_PASS")

# Synthetic x-axis identification: exact major-decade ticks plus nearby minor peaks.
pw=1000
strength=np.zeros(pw+1,float)
maj=np.rint(m.X_EXPECTED_FRAC*pw).astype(int)
for j in maj:
    strength[j]=25
    strength[j+18]=20
    strength[j-14]=19
xt=m.choose_x_major_tick_tuple(strength,pw)
picked=np.rint(xt["indices"]).astype(int)
assert np.max(np.abs(picked-maj))<=2, (picked,maj,xt)
print("D30A_V511_X_TICK_TUPLE_TEST_PASS")

assert m._parse_numeric_word("0.1")==0.1
assert m._parse_numeric_word("100")==100.0
assert m._parse_numeric_word("(100)") is None
print("D30A_V512_VECTOR_TEXT_HELPER_TEST_PASS")

pw=2400
strength=np.zeros(pw+1,float)
for j in [313,867,1421]:
    strength[j]=30
for j in [330,850,1440,2176]:
    strength[j]=25
tri=m.choose_x_major_tick_triplet(strength,pw)
picked=np.rint(tri["indices"]).astype(int)
assert np.max(np.abs(picked-np.array([313,867,1421])))<=2, (picked,tri)
assert abs(tri["inferred_fourth_decade_pixel"]-1975)<=3
print("D30A_V513_THREE_DECADE_CALIBRATION_TEST_PASS")

h,w=900,1600
rgb=np.full((h,w,3),255,np.uint8)
L,R,T,B=355,1470,245,805
rgb[T:T+3,L:R+1]=0
rgb[B-2:B+1,L:R+1]=0
rgb[T:B+1,L:L+3]=0
rgb[T:B+1,R-2:R+1]=0
rgb[80:82,60:520]=0
rgb[520:522,30:500]=0
rgb[100:430,120:122]=0
spines,dark,diag=m.detect_spines(rgb)
assert abs(spines["left"]-L)<=3, (spines,diag)
assert abs(spines["right"]-R)<=3, (spines,diag)
assert abs(spines["top"]-T)<=3, (spines,diag)
assert abs(spines["bottom"]-B)<=3, (spines,diag)
assert "no expected frame position" in diag["method"]
print("D30A_V514_FRAME_DETECTOR_NO_POSITION_PRIOR_TEST_PASS")
