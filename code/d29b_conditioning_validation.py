#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse,csv,json,math
import numpy as np
import mpmath as mp

XTOL=1e-14
RTOL=1e-13

def f_and_fp(y,mu):
    alpha=mu*mu
    f=math.pi/math.tan(math.pi*y)-alpha*y
    fp=-math.pi**2/(math.sin(math.pi*y)**2)-alpha
    return f,fp

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--d29a-result',required=True)
    ap.add_argument('--roots-dir',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    d29a=json.loads(Path(a.d29a_result).read_text())
    roots=Path(a.roots_dir)
    rows=[]
    for fn,mu in [('FIG1_ROOTS_mu1_0.1.csv',0.1),('FIG1_ROOTS_mu1_1.csv',1.0),('FIG1_ROOTS_mu1_10.csv',10.0)]:
        with (roots/fn).open() as f:
            for r in csv.DictReader(f):
                n=int(r['n']); m=float(r['m_lambda']); y=m/mu
                fv,fp=f_and_fp(y,mu)
                dy=abs(fv/fp); tol=XTOL+RTOL*abs(y)
                rows.append({'mu1':mu,'n':n,'m_lambda':m,'raw_abs_residual':abs(fv),
                             'newton_backward_error_abs_y':dy,'solver_coordinate_tolerance_abs_y':tol,
                             'backward_error_over_solver_tolerance':dy/tol})
    worst_raw=max(rows,key=lambda r:r['raw_abs_residual'])
    worst_ratio=max(rows,key=lambda r:r['backward_error_over_solver_tolerance'])
    mp.mp.dps=80
    hp=[]
    for label,rec in [('worst_raw_residual',worst_raw),('worst_normalized_backward_error',worst_ratio)]:
        mu=mp.mpf(str(rec['mu1'])); mf=mp.mpf(str(rec['m_lambda'])); y0=mf/mu; alpha=mu*mu
        f=lambda y: mp.pi/mp.tan(mp.pi*y)-alpha*y
        yh=mp.findroot(f,(y0-mp.mpf('1e-8'),y0+mp.mpf('1e-8')),solver='secant',tol=mp.mpf('1e-60'),verify=False)
        hp.append({'case':label,'mu1':rec['mu1'],'n':rec['n'],'abs_m_difference':float(abs(mf-yh*mu)),
                   'difference_over_solver_tolerance':float(abs(y0-yh)/mp.mpf(str(rec['solver_coordinate_tolerance_abs_y']))),
                   'high_precision_equation_residual_abs':float(abs(f(yh)))})
    substantive=(all(x['pass'] for x in d29a['triangulation']) and
                 all(v['sum_Nlambda2']>0.99 for v in d29a['unitarity'].values()) and
                 d29a['qualitative_text_checks']['lightest_overlap_orders_as_mu_decreases'])
    within=all(r['backward_error_over_solver_tolerance']<=1 for r in rows)
    result={'phase':'D29B_CONDITIONING_AWARE_ROOT_VALIDATION','root_count_checked':len(rows),
            'max_backward_error_over_solver_tolerance':max(r['backward_error_over_solver_tolerance'] for r in rows),
            'median_backward_error_over_solver_tolerance':float(np.median([r['backward_error_over_solver_tolerance'] for r in rows])),
            'p99_backward_error_over_solver_tolerance':float(np.quantile([r['backward_error_over_solver_tolerance'] for r in rows],0.99)),
            'all_within_requested_solver_tolerance':within,'high_precision_checks':hp,
            'substantive_d29a_gates_pass':substantive,
            'verdict':'PASS_FIGURE1_COMPUTATIONAL_CORE_INDEPENDENT_REPLICATION_AFTER_CONDITIONING_AUDIT' if within and substantive else 'FAIL_FIGURE1_REPLICATION_AFTER_CONDITIONING_AUDIT'}
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
