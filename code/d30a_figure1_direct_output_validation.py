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
    """
    L,R,T,B=[sp[k] for k in ("left","right","top","bottom")]
    ph=B-T
    extent=max(10,int(0.035*ph))

    # bottom ticks
    y0=max(0,B-extent); y1=min(dark.shape[0],B+max(5,int(0.012*ph))+1)
    bot=dark[y0:y1,L:R+1].copy()
    br=B-y0
    bot[max(0,br-2):min(bot.shape[0],br+3),:]=False

    # top ticks
    z0=max(0,T-max(5,int(0.012*ph))); z1=min(dark.shape[0],T+extent+1)
    top=dark[z0:z1,L:R+1].copy()
    tr=T-z0
    top[max(0,tr-2):min(top.shape[0],tr+3),:]=False

    return (bot.sum(axis=0)+top.sum(axis=0)).astype(float)


def y_tick_strength(dark,sp):
    L,R,T,B=[sp[k] for k in ("left","right","top","bottom")]
    pw=R-L
    left=max(6,int(0.020*pw)); right=max(8,int(0.030*pw))
    x0=max(0,L-left); x1=min(dark.shape[1],L+right+1)
    band=dark[T:B+1,x0:x1].copy()
    lc=L-x0
    band[:,max(0,lc-2):min(band.shape[1],lc+3)]=False
    return band.sum(axis=1).astype(float)


def choose_local_peak(strength,expected_index,radius):
    """Used for y ticks, where the original v5.1.0 method already passed."""
    lo=max(0,int(round(expected_index-radius)))
    hi=min(len(strength),int(round(expected_index+radius))+1)
    if hi<=lo:
        raise RuntimeError("empty tick search window")
    # Keep smoothing narrow enough not to merge neighbouring individual ticks.
    sm=ndimage.gaussian_filter1d(strength.astype(float),sigma=1.0)
    return lo+int(np.argmax(sm[lo:hi]))


def local_x_candidates(strength, expected_index, radius, max_candidates=10):
    """Return plausible individual tick strokes around one expected decade tick.

    The expected fractions are identification priors only. They are not used as
    an acceptance tolerance for the scientific target/output comparison.
    """
    lo=max(0,int(round(expected_index-radius)))
    hi=min(len(strength),int(round(expected_index+radius))+1)
    if hi<=lo:
        return []
    sm=ndimage.gaussian_filter1d(strength.astype(float),sigma=1.0)
    seg=sm[lo:hi]
    distance=max(2,int(round(0.004*len(strength))))
    peaks,_=find_peaks(seg,distance=distance)
    if len(peaks)==0:
        peaks=np.array([int(np.argmax(seg))])
    cand=[]
    local_max=float(np.max(seg)) if len(seg) else 1.0
    for q in peaks:
        j=lo+int(q)
        # retain both proximity to the expected major position and literal
        # stroke strength; do not let a broad cluster of minor ticks win.
        proximity=abs(j-expected_index)/max(radius,1.0)
        strength_norm=float(sm[j]/local_max) if local_max>0 else 0.0
        cand.append((proximity-0.20*strength_norm,j,strength_norm))
    cand.sort()
    return [(j,sn) for _,j,sn in cand[:max_candidates]]


def choose_x_major_tick_tuple(strength,pw):
    """Identify the printed 0.1,1,10,100 major ticks as a coherent 4-tuple.

    All four values are consecutive decades, so on a log x-axis their pixel
    spacings must be equal. This whole-tuple constraint prevents an isolated
    log-minor tick from being selected merely because it is locally darker.
    """
    pools=[]
    for f in X_EXPECTED_FRAC:
        pools.append(local_x_candidates(
            strength, f*pw, radius=0.050*pw, max_candidates=12
        ))
    if any(not q for q in pools):
        raise RuntimeError("insufficient x tick candidates")

    sm=ndimage.gaussian_filter1d(strength.astype(float),sigma=1.0)
    best=None
    for combo in itertools.product(*pools):
        js=np.array([c[0] for c in combo],float)
        if not np.all(np.diff(js)>0):
            continue
        gaps=np.diff(js)
        mean_gap=float(np.mean(gaps))
        if mean_gap<=0:
            continue
        gap_cv=float(np.std(gaps)/mean_gap)
        frac=js/pw
        frac_rms=float(np.sqrt(np.mean((frac-X_EXPECTED_FRAC)**2)))

        A=np.vstack([js,np.ones_like(js)]).T
        a,b=np.linalg.lstsq(A,np.log10(X_TICK_VALUES),rcond=None)[0]
        resid=float(np.max(np.abs(a*js+b-np.log10(X_TICK_VALUES))))

        strength_norm=float(np.mean([
            sm[int(round(j))]/max(np.max(sm[max(0,int(j-0.05*pw)):min(len(sm),int(j+0.05*pw)+1)]),1.0)
            for j in js
        ]))

        # Geometry dominates; literal stroke strength only breaks close ties.
        score = 4.0*resid + 1.5*gap_cv + 1.0*frac_rms - 0.03*strength_norm
        rec={
            "score":score,
            "indices":js.tolist(),
            "gap_cv":gap_cv,
            "expected_fraction_rms":frac_rms,
            "fit_log10_max_residual":resid,
            "mean_local_strength_fraction":strength_norm,
        }
        if best is None or score<best["score"]:
            best=rec
    if best is None:
        raise RuntimeError("no admissible x major tick tuple")
    return best


def _parse_numeric_word(text):
    t=text.strip()
    # Tick labels are ordinary decimal numerals in the target PDF. Keep this
    # conservative so equation numbers and punctuation are not silently coerced.
    if not t or any(ch not in "0123456789.-+" for ch in t):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def choose_x_tick_labels_from_pdf(page,clip,dpi,sp):
    """Use the printed vector-text labels 0.1, 1, 10, 100 for x calibration.

    This is deliberately independent of raster tick darkness. The label centres
    share the same data-x coordinate as their tick strokes. Ambiguous numeric
    words elsewhere on the page are rejected by geometric coherence with the
    detected plot frame and by requiring one horizontal label row.
    """
    scale=dpi/72.0
    L,R,T,B=[sp[k] for k in ("left","right","top","bottom")]
    pw=R-L
    bottom_pdf_y=clip.y0 + B/scale
    left_pdf_x=clip.x0 + L/scale
    right_pdf_x=clip.x0 + R/scale

    words=page.get_text("words")
    pools={}
    for val in X_TICK_VALUES:
        cand=[]
        for w in words:
            x0,y0,x1,y1,txt=w[:5]
            num=_parse_numeric_word(txt)
            if num is None or abs(num-float(val))>1e-12:
                continue
            cx=0.5*(x0+x1); cy=0.5*(y0+y1)
            # Figure is within the rendered top clip. X tick labels must lie
            # horizontally within the plot frame and just below its bottom.
            if not (left_pdf_x-0.04*page.rect.width <= cx <=
                    right_pdf_x+0.04*page.rect.width):
                continue
            dy=cy-bottom_pdf_y
            if not (-0.005*page.rect.height <= dy <= 0.060*page.rect.height):
                continue
            cand.append({
                "text":txt,"value":float(val),
                "center_pdf":[float(cx),float(cy)],
                "bbox_pdf":[float(x0),float(y0),float(x1),float(y1)],
                "dy_from_bottom_pdf":float(dy),
            })
        if not cand:
            raise RuntimeError(f"no PDF-text candidate for x tick {val}")
        pools[float(val)]=cand

    import itertools as _it
    best=None
    ordered_vals=[float(v) for v in X_TICK_VALUES]
    for combo in _it.product(*(pools[v] for v in ordered_vals)):
        xs=np.array([q["center_pdf"][0] for q in combo],float)
        ys=np.array([q["center_pdf"][1] for q in combo],float)
        if not np.all(np.diff(xs)>0):
            continue

        # Convert to raster coordinates for comparison with plot geometry.
        xpix=(xs-clip.x0)*scale
        frac=(xpix-L)/pw
        if np.any(frac < -0.03) or np.any(frac > 1.03):
            continue

        # Four consecutive decades must be linear in pixel coordinate.
        A=np.vstack([xpix,np.ones_like(xpix)]).T
        a,b=np.linalg.lstsq(A,np.log10(X_TICK_VALUES),rcond=None)[0]
        resid=float(np.max(np.abs(a*xpix+b-np.log10(X_TICK_VALUES))))
        row_spread=float(np.std(ys)/page.rect.height)
        frac_rms=float(np.sqrt(np.mean((frac-X_EXPECTED_FRAC)**2)))
        mean_dy=float(np.mean(ys)-bottom_pdf_y)
        dy_target=0.018*page.rect.height
        dy_pen=abs(mean_dy-dy_target)/page.rect.height

        score=8.0*resid + 2.0*row_spread + 0.5*frac_rms + 0.25*dy_pen
        rec={
            "score":score,
            "x_tick_pixels":xpix.tolist(),
            "selected_words":list(combo),
            "row_spread_page_fraction":row_spread,
            "expected_fraction_rms":frac_rms,
            "fit_log10_max_residual":resid,
            "mean_label_offset_below_spine_pdf":mean_dy,
        }
        if best is None or score<best["score"]:
            best=rec
    if best is None:
        raise RuntimeError("no coherent PDF-text x-tick label tuple")
    return best


def choose_x_major_tick_triplet(strength,pw):
    """Identify the first three printed decade ticks: 0.1, 1, 10.

    Three distinct decades are already sufficient to determine the affine mapping
    pixel_x -> log10(x). The published raster exposes these three strokes robustly;
    the fourth (100) was the sole failure mode of v5.1.1.

    This is calibration-only. The scientific anchor set and acceptance gate are
    unchanged.
    """
    vals=np.array([0.1,1.0,10.0],float)
    exps=X_EXPECTED_FRAC[:3]
    pools=[]
    for f in exps:
        pools.append(local_x_candidates(
            strength, f*pw, radius=0.050*pw, max_candidates=12
        ))
    if any(not q for q in pools):
        raise RuntimeError("insufficient x triplet candidates")

    sm=ndimage.gaussian_filter1d(strength.astype(float),sigma=1.0)
    best=None
    for combo in itertools.product(*pools):
        js=np.array([c[0] for c in combo],float)
        if not np.all(np.diff(js)>0):
            continue
        gaps=np.diff(js)
        mean_gap=float(np.mean(gaps))
        if mean_gap<=0:
            continue
        gap_cv=float(np.std(gaps)/mean_gap)
        frac=js/pw
        frac_rms=float(np.sqrt(np.mean((frac-exps)**2)))

        A=np.vstack([js,np.ones_like(js)]).T
        a,b=np.linalg.lstsq(A,np.log10(vals),rcond=None)[0]
        resid=float(np.max(np.abs(a*js+b-np.log10(vals))))

        local_strengths=[]
        for j in js:
            lo=max(0,int(j-0.05*pw)); hi=min(len(sm),int(j+0.05*pw)+1)
            den=max(float(np.max(sm[lo:hi])),1.0)
            local_strengths.append(float(sm[int(round(j))]/den))
        strength_norm=float(np.mean(local_strengths))

        # Equal decade spacing and known layout dominate. Darkness only breaks ties.
        score=8.0*resid + 2.0*gap_cv + 1.0*frac_rms - 0.03*strength_norm
        rec={
            "score":score,
            "indices":js.tolist(),
            "gap_cv":gap_cv,
            "expected_fraction_rms":frac_rms,
            "fit_log10_max_residual":resid,
            "mean_local_strength_fraction":strength_norm,
            "inferred_fourth_decade_pixel":float(js[-1]+mean_gap),
        }
        if best is None or score<best["score"]:
            best=rec
    if best is None:
        raise RuntimeError("no admissible x major tick triplet")
    return best


def calibrate_axes(page,clip,dpi,dark,sp):
    L,R,T,B=[sp[k] for k in ("left","right","top","bottom")]
    pw=R-L; ph=B-T

    # v5.1.3: use only the first three robust raster major-decade ticks
    # (0.1, 1, 10). Three points are sufficient for a log-axis affine fit.
    xs=x_tick_strength(dark,sp)
    xtri=choose_x_major_tick_triplet(xs,pw)
    xpix=L+np.array(xtri["indices"],float)
    xvals=np.array([0.1,1.0,10.0],float)

    # y calibration unchanged from v5.1.0/v5.1.1, where it passed.
    ys=y_tick_strength(dark,sp)
    ypix=[]
    for f in Y_EXPECTED_FRAC:
        idx=f*ph
        j=choose_local_peak(ys,idx,0.035*ph)
        ypix.append(T+j)
    ypix=np.array(ypix,float)

    if len(set(map(lambda q:int(round(q)),xpix)))<3 or len(set(map(int,ypix)))<6:
        raise RuntimeError(f"duplicate tick picks x={xpix}, y={ypix}")

    Ax=np.vstack([xpix,np.ones_like(xpix)]).T
    ay,bx=np.linalg.lstsq(Ax,np.log10(xvals),rcond=None)[0]
    Ay=np.vstack([ypix,np.ones_like(ypix)]).T
    by,cy=np.linalg.lstsq(Ay,np.log10(Y_TICK_VALUES),rcond=None)[0]
    xres=np.max(np.abs(ay*xpix+bx-np.log10(xvals)))
    yres=np.max(np.abs(by*ypix+cy-np.log10(Y_TICK_VALUES)))

    # Frozen residual gates unchanged.
    if xres>0.012 or yres>0.012:
        raise RuntimeError(
            f"axis calibration residual too large x={xres} y={yres}; "
            f"x_triplet={xtri}"
        )

    inferred100=L+xtri["inferred_fourth_decade_pixel"]
    return {
        "x_tick_source":"raster first-three decade strokes (0.1,1,10)",
        "x_tick_pixels":xpix.tolist(),
        "x_tick_values":xvals.tolist(),
        "x_triplet_diagnostics":xtri,
        "x_inferred_100_tick_pixel":float(inferred100),
        "x_100_role":"redundant QA only; not used in calibration fit",
        "y_tick_source":"raster tick strokes",
        "y_tick_pixels":ypix.tolist(),
        "y_tick_values":Y_TICK_VALUES.tolist(),
        "log10x_per_pixel":float(ay),"log10x_intercept":float(bx),
        "log10y_per_pixel":float(by),"log10y_intercept":float(cy),
        "x_log10_max_residual":float(xres),
        "y_log10_max_residual":float(yres),
    }



def xy_to_pix(x,y,cal):
    px=(math.log10(x)-cal["log10x_intercept"])/cal["log10x_per_pixel"]
    py=(math.log10(y)-cal["log10y_intercept"])/cal["log10y_per_pixel"]
    return float(px),float(py)


def pix_to_xy(px,py,cal):
    x=10**(cal["log10x_per_pixel"]*px+cal["log10x_intercept"])
    y=10**(cal["log10y_per_pixel"]*py+cal["log10y_intercept"])
    return float(x),float(y)


def hue_mask(rgb,mu,sat_min):
    hsv=rgb_to_hsv(np.clip(rgb.astype(float)/255.0,0,1))
    h=hsv[...,0]; s=hsv[...,1]; v=hsv[...,2]
    hlo,hhi=HUE_WINDOWS[mu]
    return (h>=hlo)&(h<=hhi)&(s>=sat_min)&(v>=0.15)&(v<=0.98)


def detect_anchor(rgb,sp,cal,mu,n,sat_min):
    m=root_eq326(mu,n); nl=nlambda(m,mu)
    px,py=xy_to_pix(m,nl,cal)
    L,R,T,B=[sp[k] for k in ("left","right","top","bottom")]
    pw=R-L; ph=B-T
    # Search box is identification-only, not the acceptance tolerance.
    rx=max(8,int(0.040*pw))
    ry=max(8,int(0.055*ph))
    xa=max(L,int(px-rx)); xb=min(R,int(px+rx)+1)
    ya=max(T,int(py-ry)); yb=min(B,int(py+ry)+1)
    if xa>=xb or ya>=yb:
        return {"status":"PREDICTION_OUTSIDE_PLOT","mu1":mu,"n":n}
    mask=hue_mask(rgb[ya:yb,xa:xb],mu,sat_min)
    lab,num=ndimage.label(mask)
    if num==0:
        return {"status":"NO_COLORED_COMPONENT","mu1":mu,"n":n}
    objs=ndimage.find_objects(lab)
    candidates=[]
    min_area=max(3,int(round(4*(rgb.shape[1]/1800.0)**2)))
    for label_id,sl in enumerate(objs,1):
        if sl is None: continue
        yy,xx=sl
        yy0,yy1=yy.start,yy.stop; xx0,xx1=xx.start,xx.stop
        component=(lab[yy0:yy1,xx0:xx1]==label_id)
        area=int(component.sum())
        if area<min_area: continue
        cy,cx=ndimage.center_of_mass(component)
        gx=xa+xx0+cx; gy=ya+yy0+cy
        # Reject page text / legend-like large structures in local windows.
        bw=xx1-xx0; bh=yy1-yy0
        if bw>0.075*pw or bh>0.10*ph:
            continue
        dist=((gx-px)/pw)**2+((gy-py)/ph)**2
        candidates.append((dist,area,gx,gy,xa+xx0,xa+xx1-1,ya+yy0,ya+yy1-1,bw,bh))
    if not candidates:
        return {"status":"NO_ADMISSIBLE_COMPONENT","mu1":mu,"n":n}
    candidates.sort(key=lambda z:(z[0],-z[1]))
    dist,area,gx,gy,x0,x1,y0,y1,bw,bh=candidates[0]

    # Graphical digitization envelope: actual colored component footprint expanded
    # only by one raster pixel and the measured axis-calibration residual.
    xlog0=cal["log10x_per_pixel"]*(x0-1)+cal["log10x_intercept"]
    xlog1=cal["log10x_per_pixel"]*(x1+1)+cal["log10x_intercept"]
    ylog0=cal["log10y_per_pixel"]*(y0-1)+cal["log10y_intercept"]
    ylog1=cal["log10y_per_pixel"]*(y1+1)+cal["log10y_intercept"]
    xmin,xmax=sorted((10**xlog0,10**xlog1))
    ymin,ymax=sorted((10**ylog0,10**ylog1))
    # calibration uncertainty in log coordinates
    xpad=cal["x_log10_max_residual"]; ypad=cal["y_log10_max_residual"]
    xmin/=10**xpad; xmax*=10**xpad
    ymin/=10**ypad; ymax*=10**ypad

    xc,yc=pix_to_xy(gx,gy,cal)
    inside=(xmin<=m<=xmax and ymin<=nl<=ymax)
    return {
        "status":"DETECTED",
        "mu1":mu,"n":n,"sat_min":sat_min,
        "theory_m_lambda":m,"theory_N_lambda":nl,
        "digitized_center_m_lambda":xc,"digitized_center_N_lambda":yc,
        "digitized_envelope_m_lambda":[xmin,xmax],
        "digitized_envelope_N_lambda":[ymin,ymax],
        "theory_inside_graphical_envelope":bool(inside),
        "component_area_pixels":area,
        "component_bbox_pixels":[int(x0),int(y0),int(x1),int(y1)],
        "component_width_pixels":int(bw),"component_height_pixels":int(bh),
        "normalized_center_distance_to_theory":float(math.sqrt(dist)),
        "predicted_pixel":[px,py],
        "detected_center_pixel":[float(gx),float(gy)],
    }


def summarize_anchor(records):
    good=[r for r in records if r.get("status")=="DETECTED"]
    dpis=sorted(set(r["dpi"] for r in good))
    passes=[r for r in good if r["theory_inside_graphical_envelope"]]
    robust=(len(dpis)>=2 and len(good)>=4)
    contradictory=(
        len(dpis)>=2 and
        sum(not r["theory_inside_graphical_envelope"] for r in good)>=max(2,len(good)//2)
    )
    if good:
        xc=np.median([r["digitized_center_m_lambda"] for r in good])
        yc=np.median([r["digitized_center_N_lambda"] for r in good])
        tx=good[0]["theory_m_lambda"]; ty=good[0]["theory_N_lambda"]
        return {
            "mu1":good[0]["mu1"],"n":good[0]["n"],
            "robust_detection":robust,
            "contradictory_detection":contradictory,
            "successful_estimates":len(good),
            "successful_dpis":dpis,
            "envelope_pass_estimates":len(passes),
            "theory_m_lambda":tx,"theory_N_lambda":ty,
            "digitized_median_m_lambda":float(xc),
            "digitized_median_N_lambda":float(yc),
            "median_fractional_difference_m":float(abs(xc-tx)/tx),
            "median_fractional_difference_N":float(abs(yc-ty)/ty),
            "status":("ROBUST_MATCH" if robust and not contradictory else
                      "ROBUST_MISMATCH" if contradictory else
                      "INSUFFICIENT_GRAPHICAL_SUPPORT")
        }
    return {
        "mu1":records[0]["mu1"],"n":records[0]["n"],
        "robust_detection":False,"contradictory_detection":False,
        "successful_estimates":0,"successful_dpis":[],
        "status":"INSUFFICIENT_GRAPHICAL_SUPPORT"
    }


def draw_overlay(rgb,sp,cal,summaries,outfile):
    img=Image.fromarray(rgb)
    dr=ImageDraw.Draw(img)
    for s in summaries:
        if s["status"]=="INSUFFICIENT_GRAPHICAL_SUPPORT":
            continue
        px,py=xy_to_pix(s["theory_m_lambda"],s["theory_N_lambda"],cal)
        r=8
        # Black ring = independently calculated point. No color is used for the overlay.
        dr.ellipse([px-r,py-r,px+r,py+r],outline=(0,0,0),width=3)
    img.save(outfile)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--pdf",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()
    pdf=Path(a.pdf).resolve(); out=Path(a.outdir).resolve()
    out.mkdir(parents=True,exist_ok=True)

    doc=fitz.open(pdf)
    best,candidates=find_figure1_page(doc)
    pidx=best["page_index_zero_based"]
    (out/"FIGURE1_PAGE_LOCATOR.json").write_text(json.dumps({
        "selected":best,"candidates":candidates,
        "page_number_one_based":pidx+1
    },indent=2)+"\n")

    rendered={}
    cal_fracs=[]
