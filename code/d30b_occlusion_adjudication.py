#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, math
import numpy as np
from scipy import ndimage
from scipy.optimize import brentq
from PIL import Image, ImageDraw

EXPECTED_RUN_SHA="5a042794e97d4bfebfcc3c547de25d0d5ac7e3731d86aaf364477b603bce62da"
DPIS=(400,600,800)
SATS=(0.25,0.35,0.45)
MU=10.0
REF_N=0
CONTROL_NS=(1,2)
TARGET_NS=(5,10)
MD=1.0
PURPLE=(0.72,0.92)
BLUE=(0.50,0.70)
GREEN=(0.18,0.45)
CONTROL_GUARD_400PX=2.0
ROBUST_MIN_EST=4
SHRINK_MAX_RATIO=0.80
OCCLUDER_MIN_FRAC=0.10


def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def root_eq326(mu:float,n:int)->float:
    alpha=(mu/MD)**2
    def f(y): return math.pi/math.tan(math.pi*y)-alpha*y
    eps=1e-10
    return mu*brentq(f,n+eps,n+0.5-eps,xtol=1e-14,rtol=1e-13,maxiter=300)


def nlambda(m:float,mu:float)->float:
    return (0.5*(math.pi**2*MD**2/mu**2 + m*m/MD**2 + 1.0))**-0.5


def xy_to_pix(x,y,cal):
    px=(math.log10(x)-cal['log10x_intercept'])/cal['log10x_per_pixel']
    py=(math.log10(y)-cal['log10y_intercept'])/cal['log10y_per_pixel']
    return float(px),float(py)


def hue_mask_from_hsv(hsv,window,sat_min):
    # Pillow HSV is uint8: H,S,V in [0,255]. Keep full-image memory bounded.
    h,s,v=hsv[...,0],hsv[...,1],hsv[...,2]
    lo,hi=window
    hlo=int(math.floor(lo*255.0)); hhi=int(math.ceil(hi*255.0))
    smin=int(math.floor(sat_min*255.0)); vmin=int(math.floor(0.15*255.0)); vmax=int(math.ceil(0.98*255.0))
    return (h>=hlo)&(h<=hhi)&(s>=smin)&(v>=vmin)&(v<=vmax)


def detect_purple_component(rgb,hsv,sp,cal,n,sat_min):
    m=root_eq326(MU,n); nl=nlambda(m,MU)
    px,py=xy_to_pix(m,nl,cal)
    L,R,T,B=[sp[k] for k in ('left','right','top','bottom')]
    pw=R-L; ph=B-T
    rx=max(8,int(0.040*pw)); ry=max(8,int(0.055*ph))
    xa=max(L,int(px-rx)); xb=min(R,int(px+rx)+1)
    ya=max(T,int(py-ry)); yb=min(B,int(py+ry)+1)
    mask=hue_mask_from_hsv(hsv[ya:yb,xa:xb],PURPLE,sat_min)
    lab,num=ndimage.label(mask)
    if num==0:
        return {'status':'NO_PURPLE_COMPONENT','n':n,'sat_min':sat_min,'predicted_pixel':[px,py]}
    objs=ndimage.find_objects(lab)
    min_area=max(3,int(round(4*(rgb.shape[1]/1800.0)**2)))
    cand=[]
    for label_id,sl in enumerate(objs,1):
        if sl is None: continue
        yy,xx=sl; yy0,yy1=yy.start,yy.stop; xx0,xx1=xx.start,xx.stop
        comp=(lab[yy0:yy1,xx0:xx1]==label_id)
        area=int(comp.sum())
        if area<min_area: continue
        cy,cx=ndimage.center_of_mass(comp)
        gx=xa+xx0+cx; gy=ya+yy0+cy
        bw=xx1-xx0; bh=yy1-yy0
        if bw>0.075*pw or bh>0.10*ph: continue
        dist=((gx-px)/pw)**2+((gy-py)/ph)**2
        cand.append((dist,-area,gx,gy,xa+xx0,ya+yy0,xa+xx1-1,ya+yy1-1,area,bw,bh))
    if not cand:
        return {'status':'NO_ADMISSIBLE_PURPLE_COMPONENT','n':n,'sat_min':sat_min,'predicted_pixel':[px,py]}
    cand.sort()
    _,neg_area,gx,gy,x0,y0,x1,y1,area,bw,bh=cand[0]
    return {
      'status':'DETECTED','n':n,'sat_min':sat_min,
      'theory_m_lambda':m,'theory_N_lambda':nl,
      'predicted_pixel':[px,py],
      'visible_center_pixel':[float(gx),float(gy)],
      'bbox':[int(x0),int(y0),int(x1),int(y1)],
      'area_pixels':int(area),'width_pixels':int(bw),'height_pixels':int(bh)
    }


def robust_pass(records,key='registration_pass'):
    passed=[r for r in records if r.get('status')=='DETECTED' and r.get(key)]
    return len(passed)>=ROBUST_MIN_EST and len({r['dpi'] for r in passed})>=2


def robust_fail(records,key='registration_pass'):
    good=[r for r in records if r.get('status')=='DETECTED']
    failed=[r for r in good if not r.get(key,False)]
    return len(failed)>=ROBUST_MIN_EST and len({r['dpi'] for r in failed})>=2


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run-dir',required=True)
    ap.add_argument('--source-zip',required=True)
    ap.add_argument('--outdir',required=True)
    a=ap.parse_args()
    run=Path(a.run_dir).resolve(); srczip=Path(a.source_zip).resolve(); out=Path(a.outdir).resolve()
    out.mkdir(parents=True,exist_ok=True)

