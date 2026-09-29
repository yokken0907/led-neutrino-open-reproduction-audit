#!/usr/bin/env python3
from pathlib import Path
import csv, argparse, json

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--anchors',required=True)
    ap.add_argument('--occlusion',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    anchors=list(csv.DictReader(open(a.anchors)))
    occ={int(r['n']):r for r in csv.DictReader(open(a.occlusion))}
    direct={}
    unresolved=[]
    for r in anchors:
        mu=float(r['mu1']); n=int(r['n']); st=r['status']
        direct.setdefault(mu,0)
        if st=='ROBUST_MATCH': direct[mu]+=1
        elif st=='INSUFFICIENT_GRAPHICAL_SUPPORT': unresolved.append(f'{mu}|{n}')
    assert len(anchors)==15
    assert direct=={10.0:3,1.0:5,0.1:4}, direct
    for n in (5,10):
        r=occ[n]
        assert int(r['registration_pass_estimates'])==9
        assert int(r['occlusion_signature_estimates'])==9
        assert r['registration_pass_dpis']=='400,600,800'
        assert r['occlusion_signature_dpis']=='400,600,800'
    combined={10.0:direct[10.0]+2,1.0:direct[1.0],0.1:direct[0.1]}
    coverage={str(k):v>=4 for k,v in combined.items()}
    result={
      'phase':'D30C_FIGURE1_DIRECT_OUTPUT_EVIDENCE_CHECK',
      'direct_robust_matches':sum(1 for r in anchors if r['status']=='ROBUST_MATCH'),
      'occlusion_adjudicated_targets':['10.0|5','10.0|10'],
      'unresolved':unresolved,
      'combined_supported_by_mu1':{str(k):v for k,v in combined.items()},
      'coverage_rule':'at least 4 of 5 anchors per mu1',
      'coverage_pass':coverage,
      'verdict':'PASS_D30C_FROZEN_DIRECT_OUTPUT_EVIDENCE' if all(coverage.values()) else 'FAIL_D30C_FROZEN_DIRECT_OUTPUT_EVIDENCE',
      'boundary':'This CI rechecks the frozen D30A/D30B evidence tables; it does not rerasterize the publisher PDF.'
    }
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    assert result['verdict']=='PASS_D30C_FROZEN_DIRECT_OUTPUT_EVIDENCE'
    print('D30C_EVIDENCE_CHECK_PASS')
if __name__=='__main__': main()
