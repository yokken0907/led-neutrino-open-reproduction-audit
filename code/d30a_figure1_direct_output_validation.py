#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, math, itertools
import numpy as np
import fitz
from scipy import ndimage
from scipy.signal import find_peaks
from scipy.optimize import brentq
from PIL import Image, ImageDraw
from matplotlib.colors import rgb_to_hsv

DPIS=(400,600,800)
SAT_LEVELS=(0.25,0.35,0.45)
MD=1.0

# Pre-specified before target-image extraction. Five roots per published mu1.
ANCHORS={
    10.0:(0,1,2,5,10),
    1.0:(0,1,2,5,10),
    0.1:(0,1,5,10,20),
}

# Figure-1 marker hue windows, broad by design; saturation levels are varied above.
HUE_WINDOWS={
    10.0:(0.72,0.92), # purple
    1.0:(0.50,0.70),  # blue
    0.1:(0.18,0.45),  # green
}

# Published major-tick labels.
X_TICK_VALUES=np.array([0.1,1.0,10.0,100.0],float)
Y_TICK_VALUES=np.array([1.0,0.5,0.1,0.05,0.01,0.005],float)

# Weak geometry priors read from the published figure layout, used only to identify
# which raster tick strokes correspond to the printed major tick labels.
X_EXPECTED_FRAC=np.array([0.18,0.41,0.64,0.87],float)
Y_EXPECTED_FRAC=np.array([0.06,0.18,0.45,0.57,0.84,0.96],float)

CAPTION_NEEDLE="Figure 1. Brane-Dirac spectrum"


def eq326_residual(m:float,mu:float)->float:
    return math.pi/math.tan(math.pi*m/mu) - mu*m/(MD*MD)


def root_eq326(mu:float,n:int)->float:
    alpha=(mu/MD)**2
    def f(y):
        return math.pi/math.tan(math.pi*y)-alpha*y
    eps=1e-10
    return mu*brentq(f,n+eps,n+0.5-eps,xtol=1e-14,rtol=1e-13,maxiter=300)


def nlambda(m:float,mu:float)->float:
    return (0.5*(math.pi**2*MD**2/mu**2 + m*m/MD**2 + 1.0))**-0.5


def find_figure1_page(doc):
    cand=[]
    for i in range(len(doc)):
        txt=" ".join(doc[i].get_text("text").split())
        score=0
        ev=[]
        if "Figure 1." in txt:
            score+=5; ev.append("figure_number_caption_form")
        if "Brane-Dirac spectrum" in txt:
            score+=6; ev.append("caption_title")
        if "dashed lines and the dots represent" in txt:
            score+=5; ev.append("caption_graphic_definition")
        if "representative values of" in txt and "mD = 1" in txt:
            score+=3; ev.append("caption_parameters")
        if score>=11:
            cand.append({"page_index_zero_based":i,"score":score,"evidence":ev})
    if not cand:
        raise RuntimeError("Figure 1 caption page not found")
    cand.sort(key=lambda x:(x["score"],-x["page_index_zero_based"]),reverse=True)
    return cand[0],cand


def render_top(page,dpi):
    W,H=page.rect.width,page.rect.height
    clip=fitz.Rect(0.02*W,0.00*H,0.98*W,0.36*H)
    s=dpi/72.0
    pix=page.get_pixmap(matrix=fitz.Matrix(s,s),clip=clip,alpha=False)
    arr=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,pix.n)[...,:3]
    return arr.copy(),clip


def _longest_dark_run(bits, max_gap):
    """Return (span_length, start, end) for the longest near-contiguous dark run.

    max_gap bridges only tiny antialiasing/raster gaps. It is deliberately far too
    small to join ordinary words or unrelated graphical objects into a frame edge.
    """
    pos=np.flatnonzero(bits)
    if pos.size==0:
        return 0,None,None
    cut=np.flatnonzero(np.diff(pos)>max_gap+1)
    starts=np.r_[0,cut+1]
    ends=np.r_[cut,pos.size-1]
    spans=pos[ends]-pos[starts]+1
    k=int(np.argmax(spans))
    return int(spans[k]),int(pos[starts[k]]),int(pos[ends[k]])


def _cluster_line_candidates(records,coord_key,merge_radius):
    """Merge adjacent raster rows/columns belonging to one physical dark line."""
    if not records:
        return []
    records=sorted(records,key=lambda r:r[coord_key])
    groups=[]; cur=[records[0]]
    for r in records[1:]:
        if r[coord_key]-cur[-1][coord_key] <= merge_radius:
            cur.append(r)
        else:
            groups.append(cur); cur=[r]
    groups.append(cur)
    out=[]
    for g in groups:
        # Use the member with the longest literal run; ties prefer the group centre.
        centre=float(np.median([q[coord_key] for q in g]))
        best=max(g,key=lambda q:(q["length"],-abs(q[coord_key]-centre)))
        rec=dict(best)
        rec["band_min"]=int(min(q[coord_key] for q in g))
        rec["band_max"]=int(max(q[coord_key] for q in g))
        rec["band_members"]=len(g)
        out.append(rec)
    return out


def detect_spines(rgb):
    """Detect the Figure-1 rectangular plot frame from literal long dark lines.

    v5.1.4 deliberately removes the v5.1.3 expected-position frame prior. Candidate
    edges are generated only from the longest near-contiguous horizontal/vertical
    dark runs in the rendered image. The selected four edges must form one coherent
    rectangle by endpoint agreement. No scientific anchor or acceptance threshold is
    involved in this technical frame-localisation step.
    """
    h,w,_=rgb.shape
    gray=np.mean(rgb,axis=2)
    dark=gray<105

    # Scale the permitted raster gap with DPI/image size, but keep it tiny relative
    # to typography. This bridges antialiasing breaks without joining text words.
    gap=max(1,int(round(max(h,w)/1800.0)))
    row_merge=max(2,int(round(h/700.0)))
    col_merge=max(2,int(round(w/700.0)))

    hraw=[]
    hmin=max(40,int(round(0.35*w)))
    for y in range(h):
        ln,x0,x1=_longest_dark_run(dark[y,:],gap)
        if ln>=hmin:
            hraw.append({"row":int(y),"start":int(x0),"end":int(x1),"length":int(ln)})

    vraw=[]
    vmin=max(40,int(round(0.30*h)))
    for x in range(w):
        ln,y0,y1=_longest_dark_run(dark[:,x],gap)
        if ln>=vmin:
            vraw.append({"col":int(x),"start":int(y0),"end":int(y1),"length":int(ln)})

    hc=_cluster_line_candidates(hraw,"row",row_merge)
    vc=_cluster_line_candidates(vraw,"col",col_merge)
    # Restrict combinatorics to the strongest literal line candidates, not to any
    # expected location. Stable ties are resolved by coordinate only.
    hc=sorted(hc,key=lambda r:(-r["length"],r["row"]))[:12]
    vc=sorted(vc,key=lambda r:(-r["length"],r["col"]))[:12]
    if len(hc)<2 or len(vc)<2:
        raise RuntimeError(
            f"insufficient long-line frame candidates horizontal={len(hc)} vertical={len(vc)}"
        )

    best=None
    for ha,hb in itertools.combinations(hc,2):
        top,bottom=sorted((ha,hb),key=lambda r:r["row"])
        T=top["row"]; B=bottom["row"]
        if B-T < 0.20*h:
            continue
        for va,vb in itertools.combinations(vc,2):
            left,right=sorted((va,vb),key=lambda r:r["col"])
            L=left["col"]; R=right["col"]
            if R-L < 0.25*w:
                continue

            # The true frame's horizontal runs terminate at the two vertical edges,
            # and the vertical runs terminate at the two horizontal edges.
            end_err=(
                abs(top["start"]-L)+abs(top["end"]-R)+
                abs(bottom["start"]-L)+abs(bottom["end"]-R)
            )/(4.0*w)
            side_err=(
                abs(left["start"]-T)+abs(left["end"]-B)+
                abs(right["start"]-T)+abs(right["end"]-B)
            )/(4.0*h)

            target_w=R-L+1; target_h=B-T+1
            span_err=(
                abs(top["length"]-target_w)+abs(bottom["length"]-target_w)
            )/(2.0*w) + (
                abs(left["length"]-target_h)+abs(right["length"]-target_h)
            )/(2.0*h)

            # Literal darkness at all four corners is independent confirmation that
            # the four long lines belong to one rectangle.
            rr=max(1,int(round(max(h,w)/2200.0)))
            corner=[]
            for yy,xx in ((T,L),(T,R),(B,L),(B,R)):
                ya=max(0,yy-rr); yb=min(h,yy+rr+1)
                xa=max(0,xx-rr); xb=min(w,xx+rr+1)
                corner.append(float(np.mean(dark[ya:yb,xa:xb])))
            corner_mean=float(np.mean(corner))

            # Small preference for longer coherent rectangles only after endpoint
            # agreement; no absolute/expected frame position appears in the score.
            coverage=0.5*((R-L)/w + (B-T)/h)
            score=end_err+side_err+0.75*span_err-0.08*corner_mean-0.02*coverage
            rec={
                "score":float(score),"left":int(L),"right":int(R),
                "top":int(T),"bottom":int(B),
                "endpoint_error":float(end_err),"side_error":float(side_err),
                "span_error":float(span_err),"corner_dark_fraction":corner_mean,
                "coverage":float(coverage),
                "selected_horizontal":[top,bottom],
                "selected_vertical":[left,right],
            }
            if best is None or rec["score"]<best["score"]:
                best=rec

    if best is None:
        raise RuntimeError("no coherent rectangular plot frame from long dark lines")

    # Guard only against self-inconsistent line geometry. These are not layout priors.
    if best["endpoint_error"]>0.04 or best["side_error"]>0.04 or best["span_error"]>0.08:
        raise RuntimeError(f"long-line frame candidates are not rectangle-consistent: {best}")

    sp={k:best[k] for k in ("left","right","top","bottom")}
    diag={
        "method":"longest literal horizontal/vertical dark-line rectangle; no expected frame position",
        "dark_threshold_mean_rgb_lt":105,
        "max_bridged_gap_pixels":int(gap),
        "horizontal_candidate_count":len(hc),
        "vertical_candidate_count":len(vc),
        "selected":best,
        "normalized_frame":{
            "left":sp["left"]/w,"right":sp["right"]/w,
            "top":sp["top"]/h,"bottom":sp["bottom"]/h,
        },
    }
    return sp,dark,diag

def x_tick_strength(dark,sp):
    """Major/minor vertical tick-stroke strength from both bottom and top axes.

    v5.1.0 used a heavily smoothed bottom-only profile. On the published Figure 1
    raster that can merge neighbouring log-minor ticks and shift a local maximum
    away from the printed major-decade stroke. v5.1.1 keeps the science gate
    unchanged and only makes tick identification more literal.
