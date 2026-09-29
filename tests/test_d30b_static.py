#!/usr/bin/env python3
import importlib.util, math
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'code'/'d30b_occlusion_adjudication.py'
spec=importlib.util.spec_from_file_location('d30b',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
expected={
 (10.0,0):(0.9838450147121393,0.9837434208391374),
 (10.0,5):(50.01999174363085,0.028266761058919412),
 (10.0,10):(100.00999896731601,0.014139945099144981),
}
for k,(em,en) in expected.items():
    x=m.root_eq326(*k); y=m.nlambda(x,k[0])
    assert abs(x-em)<1e-10,(k,x,em)
    assert abs(y-en)<1e-12,(k,y,en)
ref_center=(100.2,200.1); ref_bbox=(88,189,114,211)
offR=ref_bbox[2]-ref_center[0]; offT=ref_bbox[1]-ref_center[1]
for target,visible in [((250.7,330.4),(251,319,264,327)),((390.5,460.2),(394,449,404,455))]:
    rec=(visible[2]-offR,visible[1]-offT)
    assert math.hypot(rec[0]-target[0],rec[1]-target[1])<=1.5,(target,visible,rec)
print('D30B_STATIC_EQUATION_TEST_PASS')
print('D30B_STATIC_OCCLUSION_EDGE_REGISTRATION_TEST_PASS')
