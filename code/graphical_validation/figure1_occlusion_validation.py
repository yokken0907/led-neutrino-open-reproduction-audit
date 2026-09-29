#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, math
import numpy as np
from scipy import ndimage
from scipy.optimize import brentq
from PIL import Image, ImageDraw

EXPECTED_TARGET_PDF_SHA="2850f1c631b07de992cc72dd2b9c8aab80c10e7bccf51a421d90e80373f627c3"
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
    ap.add_argument('--outdir',required=True)
    a=ap.parse_args()
    run=Path(a.run_dir).resolve(); out=Path(a.outdir).resolve()
    out.mkdir(parents=True,exist_ok=True)

    d30a=json.loads((run/'D30A_RESULT.json').read_text())
    pdfsha=d30a.get('target',{}).get('pdf_sha256')
    if pdfsha!=EXPECTED_TARGET_PDF_SHA:
        raise SystemExit(f'SOURCE_TARGET_PDF_SHA_MISMATCH expected={EXPECTED_TARGET_PDF_SHA} actual={pdfsha}')
    if d30a.get('verdict')!='FAIL_DIRECT_TARGET_OUTPUT_DISAGREEMENT':
        raise SystemExit('SOURCE_D30A_VERDICT_NOT_EXPECTED')
    mismatches=sorted(f"{x['mu1']}|{x['n']}" for x in d30a['anchors'] if x['status']=='ROBUST_MISMATCH')
    if mismatches!=['10.0|10','10.0|5']:
        raise SystemExit(f'SOURCE_D30A_MISMATCH_SET_NOT_EXPECTED {mismatches}')

    measurements=[]
    diagnostics={}
    for dpi in DPIS:
        pil=Image.open(run/f'FIGURE1_DIAGNOSTIC_{dpi}dpi.png').convert('RGB')
        rgb=np.asarray(pil)
        hsv=np.asarray(pil.convert('HSV'))
        caldoc=json.loads((run/f'AXIS_CALIBRATION_{dpi}dpi.json').read_text())
        sp=caldoc['spines']; cal=caldoc
        blue=hue_mask_from_hsv(hsv,BLUE,0.25)
        green=hue_mask_from_hsv(hsv,GREEN,0.25)
        nonpurple_occ=blue|green
        by_sat={}
        for sat in SATS:
            recs={n:detect_purple_component(rgb,hsv,sp,cal,n,sat) for n in (REF_N,*CONTROL_NS,*TARGET_NS)}
            ref=recs[REF_N]
            if ref['status']!='DETECTED':
                raise SystemExit(f'REFERENCE_NOT_DETECTED dpi={dpi} sat={sat}')
            rpx,rpy=ref['predicted_pixel']; rl,rt,rr,rb=ref['bbox']
            offsets={'left':rl-rpx,'top':rt-rpy,'right':rr-rpx,'bottom':rb-rpy}
            for n in (*CONTROL_NS,*TARGET_NS):
                z=recs[n]
                z['dpi']=dpi
                if z['status']!='DETECTED':
                    measurements.append(z); continue
                l,t,r,b=z['bbox']; px,py=z['predicted_pixel']
                recx=r-offsets['right']; recy=t-offsets['top']
                dx=recx-px; dy=recy-py
                resid_raw=math.hypot(dx,dy); resid400=resid_raw*400.0/dpi
                full=[px+offsets['left'],py+offsets['top'],px+offsets['right'],py+offsets['bottom']]
                tol_raw=1.0*dpi/400.0
                subset=(l>=full[0]-tol_raw and t>=full[1]-tol_raw and r<=full[2]+tol_raw and b<=full[3]+tol_raw)
                x0=max(0,int(math.floor(full[0]))); y0=max(0,int(math.floor(full[1])))
                x1=min(rgb.shape[1]-1,int(math.ceil(full[2]))); y1=min(rgb.shape[0]-1,int(math.ceil(full[3])))
                occ=float(nonpurple_occ[y0:y1+1,x0:x1+1].mean()) if x1>=x0 and y1>=y0 else 0.0
                z.update({
                    'reference_bbox':ref['bbox'],
                    'reference_edge_offsets_pixels':offsets,
                    'reconstructed_center_pixel':[float(recx),float(recy)],
                    'edge_residual_pixel':[float(dx),float(dy)],
                    'edge_residual_raw_pixels':float(resid_raw),
                    'edge_residual_400dpi_equiv_pixels':float(resid400),
                    'predicted_full_bbox':[float(q) for q in full],
                    'visible_to_reference_width_ratio':float(z['width_pixels']/ref['width_pixels']),
                    'visible_to_reference_height_ratio':float(z['height_pixels']/ref['height_pixels']),
                    'nonpurple_blue_or_green_fraction_in_full_bbox':occ,
                    'visible_bbox_subset_coherent_1px_scaled':bool(subset),
                })
                measurements.append(z)
            by_sat[str(sat)]={'reference':ref,'records':recs}
        if dpi==800:
            diagnostics[dpi]=(np.array(rgb,copy=True),caldoc)
        del hsv, blue, green, nonpurple_occ, rgb, pil

    control=[r for r in measurements if r.get('n') in CONTROL_NS and r.get('status')=='DETECTED']
    if len(control)<ROBUST_MIN_EST:
        cmax=float('inf')
    else:
        cmax=max(r['edge_residual_400dpi_equiv_pixels'] for r in control)
    control_guard_pass=math.isfinite(cmax) and cmax<=CONTROL_GUARD_400PX
    threshold=(cmax+1.0) if control_guard_pass else None

    for r in measurements:
        if r.get('status')!='DETECTED': continue
        r['registration_threshold_400dpi_equiv_pixels']=threshold
        r['registration_pass']=bool(control_guard_pass and r['edge_residual_400dpi_equiv_pixels']<=threshold)
        r['occlusion_signature_pass']=bool(
            r['visible_to_reference_width_ratio']<=SHRINK_MAX_RATIO and
            r['visible_to_reference_height_ratio']<=SHRINK_MAX_RATIO and
            r['nonpurple_blue_or_green_fraction_in_full_bbox']>=OCCLUDER_MIN_FRAC and
            r['visible_bbox_subset_coherent_1px_scaled']
        )

    summaries={}
    for n in (*CONTROL_NS,*TARGET_NS):
        rr=[r for r in measurements if r.get('n')==n]
        summaries[str(n)]={
          'n':n,
          'detected_estimates':sum(r.get('status')=='DETECTED' for r in rr),
          'registration_pass_estimates':sum(bool(r.get('registration_pass')) for r in rr),
          'registration_pass_dpis':sorted({r['dpi'] for r in rr if r.get('registration_pass')}),
          'robust_registration_pass':robust_pass(rr),
          'robust_registration_fail':robust_fail(rr),
          'max_residual_400dpi_equiv_pixels':max([r['edge_residual_400dpi_equiv_pixels'] for r in rr if r.get('status')=='DETECTED'],default=None),
          'occlusion_signature_estimates':sum(bool(r.get('occlusion_signature_pass')) for r in rr),
          'occlusion_signature_dpis':sorted({r['dpi'] for r in rr if r.get('occlusion_signature_pass')}),
          'robust_occlusion_signature':(
              sum(bool(r.get('occlusion_signature_pass')) for r in rr)>=ROBUST_MIN_EST and
              len({r['dpi'] for r in rr if r.get('occlusion_signature_pass')})>=2
          )
        }

    controls_ok=control_guard_pass and all(summaries[str(n)]['robust_registration_pass'] for n in CONTROL_NS)
    target_pass=[summaries[str(n)]['robust_registration_pass'] for n in TARGET_NS]
    target_fail=[summaries[str(n)]['robust_registration_fail'] for n in TARGET_NS]
    target_occ=[summaries[str(n)]['robust_occlusion_signature'] for n in TARGET_NS]
    if not controls_ok:
        verdict='HOLD_D30B_METHOD_OR_OCCLUSION_SUPPORT'
    elif all(target_pass) and all(target_occ):
        verdict='PASS_D30B_OCCLUSION_ARTIFACT_CONFIRMED'
    elif any(target_fail):
        verdict='FAIL_D30B_D30A_CONTRADICTION_RETAINED'
    else:
        verdict='HOLD_D30B_METHOD_OR_OCCLUSION_SUPPORT'

    result={
      'phase':'D30B_OCCLUSION_AWARE_MARKER_ADJUDICATION',
      'version':'5.2.1',
      'source_run_zip_sha256':None,
      'source_run_mode':'fresh D30A run directory from the public one-command workflow',
      'source_target_pdf_sha256':d30a.get('target',{}).get('pdf_sha256'),
      'source_d30a_verdict':d30a['verdict'],
      'source_d30a_mismatches':mismatches,
      'fixed_reference_anchor':'10.0|0',
      'fixed_positive_controls':['10.0|1','10.0|2'],
      'fixed_targets':['10.0|5','10.0|10'],
      'control_max_residual_400dpi_equiv_pixels':cmax,
      'control_guard_max_allowed_400dpi_equiv_pixels':CONTROL_GUARD_400PX,
      'control_guard_pass':control_guard_pass,
      'target_registration_threshold_400dpi_equiv_pixels':threshold,
      'threshold_construction':'positive-control maximum + exactly 1.0 400-dpi pixel; targets excluded',
      'summary_by_n':summaries,
      'verdict':verdict,
      'scientific_interpretation':(
        'The two D30A v5.1.4 contradictory anchors are supported as overplot/occlusion artifacts, not direct Figure-1 disagreements.'
        if verdict=='PASS_D30B_OCCLUSION_ARTIFACT_CONFIRMED' else
        'D30B does not establish that both D30A contradictions are occlusion artifacts.'
      ),
      'claim_boundary':{
        'original_d30a_result_mutated':False,
        'retroactive_d30a_pass_claimed':False,
        'target_author_code_reproduced':False,
        'new_physics_claimed':False,
        'role':'technical adjudication of deterministic published-figure marker overlap'
      }
    }
    (out/'D30B_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'D30B_ALL_ESTIMATES.json').write_text(json.dumps(measurements,indent=2)+'\n')

    # 800-dpi diagnostics: raw crop + theoretical full-marker rectangle + visible bbox.
    dpi=800; rgb,_=diagnostics[dpi]
    for n in (0,1,2,5,10):
        if n==0:
            # obtain n0 from fresh detection at middle saturation for display
            caldoc=json.loads((run/f'AXIS_CALIBRATION_{dpi}dpi.json').read_text()); sp=caldoc['spines']; hsv=np.asarray(Image.fromarray(rgb).convert('HSV'))
            rr=detect_purple_component(rgb,hsv,sp,caldoc,0,0.35)
            px,py=rr['predicted_pixel']; l,t,r,b=rr['bbox']; full=[l,t,r,b]
        else:
            cand=[r for r in measurements if r.get('n')==n and r.get('dpi')==dpi and abs(r.get('sat_min',0)-0.35)<1e-9 and r.get('status')=='DETECTED']
            if not cand: continue
            rr=cand[0]; px,py=rr['predicted_pixel']; l,t,r,b=rr['bbox']; full=rr['predicted_full_bbox']
        margin=40
        xa=max(0,int(min(l,full[0],px)-margin)); xb=min(rgb.shape[1],int(max(r,full[2],px)+margin)+1)
        ya=max(0,int(min(t,full[1],py)-margin)); yb=min(rgb.shape[0],int(max(b,full[3],py)+margin)+1)
        im=Image.fromarray(rgb[ya:yb,xa:xb]).resize(((xb-xa)*3,(yb-ya)*3),Image.Resampling.NEAREST)
        dr=ImageDraw.Draw(im)
        def tr(x,y): return ((x-xa)*3,(y-ya)*3)
        # black cross = theoretical center
        cx,cy=tr(px,py); q=10
        dr.line((cx-q,cy,cx+q,cy),fill=(0,0,0),width=3); dr.line((cx,cy-q,cx,cy+q),fill=(0,0,0),width=3)
        # black rectangle = translated full marker bbox; white rectangle = visible purple bbox
        X0,Y0=tr(full[0],full[1]); X1,Y1=tr(full[2],full[3]); dr.rectangle((X0,Y0,X1,Y1),outline=(0,0,0),width=3)
        V0,W0=tr(l,t); V1,W1=tr(r,b); dr.rectangle((V0,W0,V1,W1),outline=(255,255,255),width=3)
        im.save(out/f'D30B_800dpi_n{n}_edge_registration.png')

    print(json.dumps({
      'verdict':verdict,
      'control_max_400px':cmax,
      'target_threshold_400px':threshold,
      'summary_by_n':summaries
    },indent=2))
    print('D30B_EXECUTION_COMPLETE')

if __name__=='__main__': main()