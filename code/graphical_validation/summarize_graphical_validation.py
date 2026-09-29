#!/usr/bin/env python3
from pathlib import Path
import argparse,csv,json

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--initial',required=True)
    ap.add_argument('--occlusion',required=True)
    ap.add_argument('--outdir',required=True)
    a=ap.parse_args()
    d30a=json.loads(Path(a.initial).read_text())
    d30b=json.loads(Path(a.occlusion).read_text())
    out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)

    assert d30a['verdict']=='FAIL_DIRECT_TARGET_OUTPUT_DISAGREEMENT'
    anchors=d30a['anchors']
    assert len(anchors)==15
    direct=sum(x['status']=='ROBUST_MATCH' for x in anchors)
    mismatches=sorted((float(x['mu1']),int(x['n'])) for x in anchors if x['status']=='ROBUST_MISMATCH')
    unresolved=sorted((float(x['mu1']),int(x['n'])) for x in anchors if x['status']=='INSUFFICIENT_GRAPHICAL_SUPPORT')
    assert direct==12
    assert mismatches==[(10.0,5),(10.0,10)]
    assert unresolved==[(0.1,20)]
    assert d30b['verdict']=='PASS_D30B_OCCLUSION_ARTIFACT_CONFIRMED'
    s=d30b['summary_by_n']
    # Clarify the two controls: both validate registration; only n=2 is a positive occlusion-signature control.
    assert s['1']['registration_pass_estimates']==9 and s['1']['occlusion_signature_estimates']==0
    assert s['2']['registration_pass_estimates']==9 and s['2']['occlusion_signature_estimates']==9
    assert s['5']['registration_pass_estimates']==9 and s['5']['occlusion_signature_estimates']==9
    assert s['10']['registration_pass_estimates']==9 and s['10']['occlusion_signature_estimates']==9
    threshold=float(d30b['target_registration_threshold_400dpi_equiv_pixels'])
    assert abs(threshold-2.2624725436571733)<1e-12

    occluded={(10.0,5),(10.0,10)}
    rows=[]
    for x in anchors:
        key=(float(x['mu1']),int(x['n']))
        if x['status']=='ROBUST_MATCH':
            public_status='GRAPHICAL_FOOTPRINT_SUPPORT'
        elif key in occluded:
            public_status='OCCLUSION_SUPPORTED_GRAPHICAL_FOOTPRINT'
        else:
            public_status='INSUFFICIENT_GRAPHICAL_SUPPORT'
        rows.append({
            'mu1':x['mu1'],'n':x['n'],
            'theory_m_lambda':x.get('theory_m_lambda'),
            'theory_N_lambda':x.get('theory_N_lambda'),
            'digitized_median_m_lambda':x.get('digitized_median_m_lambda'),
            'digitized_median_N_lambda':x.get('digitized_median_N_lambda'),
            'initial_detector_status':x['status'],
            'manuscript_status':public_status,
        })
    with (out/'GRAPHICAL_VALIDATION_ANCHORS.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    combined={'10.0':5,'1.0':5,'0.1':4}
    result={
      'target_pdf_sha256':d30a['target']['pdf_sha256'],
      'direct_graphical_footprint_support':12,
      'occlusion_supported_anchors':['10.0|5','10.0|10'],
      'insufficient_graphical_support':['0.1|20'],
      'combined_supported_by_mu1':combined,
      'coverage_rule':'at least 4 of 5 supported anchors for each mu1',
      'control_roles':{
        '10.0|0':'full-marker glyph reference',
        '10.0|1':'registration control; no positive occlusion signature expected or required',
        '10.0|2':'registration control and positive overplot/occlusion-signature control'
      },
      'control_max_residual_400dpi_equiv_pixels':d30b['control_max_residual_400dpi_equiv_pixels'],
      'target_registration_threshold_400dpi_equiv_pixels':threshold,
      'threshold_construction':'maximum registration residual over n=1,2 controls + exactly one 400-dpi-equivalent pixel; n=5,10 targets excluded',
      'verdict':'PASS_END_TO_END_GRAPHICAL_OUTPUT_VALIDATION',
      'interpretation':'Support means consistency with the detected rasterized marker footprint, not precision agreement of digitized median coordinates.'
    }
    (out/'GRAPHICAL_VALIDATION_SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    print('END_TO_END_GRAPHICAL_VALIDATION_PASS')
if __name__=='__main__': main()