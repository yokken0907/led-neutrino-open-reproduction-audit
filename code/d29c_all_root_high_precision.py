#!/usr/bin/env python3
from pathlib import Path
import csv, json, math, argparse
import mpmath as mp

XTOL=1e-14
RTOL=1e-13

def hp_root(mu,n,y0):
    mp.mp.dps=80
    mu_mp=mp.mpf(str(mu)); alpha=mu_mp*mu_mp
    f=lambda y: mp.pi/mp.tan(mp.pi*y)-alpha*y
    eps=mp.mpf('1e-30')
    lo=mp.mpf(n)+eps
    hi=mp.mpf(n)+mp.mpf('0.5')-eps
    # monotone branch: bisection gives an unambiguous high-precision root
    flo=f(lo); fhi=f(hi)
    if not (flo>0 and fhi<0):
        raise RuntimeError(f'branch bracket failed mu={mu} n={n}')
    for _ in range(320):
        mid=(lo+hi)/2
        fm=f(mid)
        if fm>0: lo=mid
        else: hi=mid
    y=(lo+hi)/2
    return y, abs(f(y))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--roots-dir',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    rootdir=Path(a.roots_dir)
    files=[('FIG1_ROOTS_mu1_10.csv',10.0),('FIG1_ROOTS_mu1_1.csv',1.0),('FIG1_ROOTS_mu1_0.1.csv',0.1)]
    rows=[]
    for fn,mu in files:
        with (rootdir/fn).open() as f:
            for r in csv.DictReader(f):
                n=int(r['n'])
                m_text=r['m_lambda']
                m_float=float(m_text)
                mu_mp=mp.mpf(str(mu))
                m_bin=mp.mpf(m_float)
                y_bin=m_bin/mu_mp
                y_hp,resid=hp_root(mu,n,m_text)
                tol_mp=mp.mpf(str(XTOL))+mp.mpf(str(RTOL))*abs(y_bin)
                dy_mp=abs(y_bin-y_hp)
                dm_mp=abs(m_bin-y_hp*mu_mp)
                ratio_mp=dy_mp/tol_mp
                rows.append(dict(mu1=mu,n=n,m_lambda=m_float,solver_coordinate_tolerance_abs_y=float(tol_mp),
                                 binary64_abs_y_difference=float(dy_mp),binary64_difference_over_solver_tolerance=float(ratio_mp),
                                 binary64_abs_m_difference=float(dm_mp),high_precision_equation_residual_abs=float(resid),
                                 high_precision_root_y=mp.nstr(y_hp,82)))
    ratios=sorted(r['binary64_difference_over_solver_tolerance'] for r in rows)
    def qlinear(vals,q):
        pos=(len(vals)-1)*q
        i=int(math.floor(pos)); j=int(math.ceil(pos))
        return vals[i] if i==j else vals[i]+(vals[j]-vals[i])*(pos-i)
    result={
      'phase':'D29C_ALL_ROOT_HIGH_PRECISION_DIRECT_VALIDATION',
      'root_count_checked':len(rows),
      'all_within_inherited_solver_tolerance':all(x<=1.0 for x in ratios),
      'max_difference_over_solver_tolerance':max(ratios),
      'median_difference_over_solver_tolerance':qlinear(ratios,0.5),
      'p99_difference_over_solver_tolerance':qlinear(ratios,0.99),
      'max_abs_m_difference':max(r['binary64_abs_m_difference'] for r in rows),
      'max_high_precision_equation_residual_abs':max(r['high_precision_equation_residual_abs'] for r in rows),
      'verdict':'PASS_D29C_ALL_3552_ROOTS_HIGH_PRECISION_DIRECT_VALIDATION' if len(rows)==3552 and all(x<=1.0 for x in ratios) else 'FAIL_D29C_ALL_ROOT_DIRECT_VALIDATION'
    }
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    assert result['verdict']=='PASS_D29C_ALL_3552_ROOTS_HIGH_PRECISION_DIRECT_VALIDATION'
    print('D29C_ALL_ROOT_HP_PASS')
if __name__=='__main__': main()
