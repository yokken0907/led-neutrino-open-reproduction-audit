#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,math,platform,sys,time
from pathlib import Path
import mpmath as mp

DPS=80
XTOL=mp.mpf('1e-14')
RTOL=mp.mpf('1e-13')
HP_BRANCH_EPS=mp.mpf('1e-60')
HP_WIDTH_TARGET=mp.mpf('1e-60')
HP_RESIDUAL_TECHNICAL_MAX=mp.mpf('1e-50')
EXPECTED_COUNTS={'10':32,'1':320,'0.1':3200}
FILES=[('10','FIG1_ROOTS_mu1_10.csv'),('1','FIG1_ROOTS_mu1_1.csv'),('0.1','FIG1_ROOTS_mu1_0.1.csv')]

def f_fp(y, mu):
    alpha=mu*mu
    f=mp.pi/mp.tan(mp.pi*y)-alpha*y
    fp=-mp.pi**2/(mp.sin(mp.pi*y)**2)-alpha
    return f,fp

def solve_unique_root(mu_s: str, n: int, seed_m_s: str):
    mu=mp.mpf(mu_s)
    lo=mp.mpf(n)+HP_BRANCH_EPS
    hi=mp.mpf(n)+mp.mpf('0.5')-HP_BRANCH_EPS
    flo,_=f_fp(lo,mu); fhi,_=f_fp(hi,mu)
    if not (flo>0 and fhi<0):
        raise RuntimeError(f'branch does not bracket unique root: mu={mu_s} n={n}')
    x=mp.mpf(seed_m_s)/mu
    if not (lo < x < hi): x=(lo+hi)/2
    for _ in range(40):
        fx,fp=f_fp(x,mu)
        if fx>0: lo=x
        else: hi=x
        xn=x-fx/fp
        if not (lo < xn < hi): xn=(lo+hi)/2
        if abs(xn-x) < mp.mpf('1e-65'):
            x=xn
            break
        x=xn
    for _ in range(240):
        if hi-lo <= HP_WIDTH_TARGET: break
        mid=(lo+hi)/2
        fm,_=f_fp(mid,mu)
        if fm>0: lo=mid
        else: hi=mid
    y=(lo+hi)/2
    res=abs(f_fp(y,mu)[0])
    return y,res,hi-lo

def qlinear(vals,q):
    vals=sorted(vals)
    pos=(len(vals)-1)*q
    i=int(math.floor(pos)); j=int(math.ceil(pos))
    return vals[i] if i==j else vals[i]+(vals[j]-vals[i])*(pos-i)

def summarize(rows, key_ratio, key_dm):
    vals=[r[key_ratio] for r in rows]
    return {'count':len(rows),'max_ratio':max(vals),'median_ratio':qlinear(vals,0.5),'p99_ratio':qlinear(vals,0.99),'max_abs_m_difference':max(r[key_dm] for r in rows),'all_within_solver_tolerance':all(v<=1.0 for v in vals)}

def self_test():
    mp.mp.dps=DPS
    frozen=[('10',30,'300.0033332950758','300.00333329507870459315892018442212639187351214669'),('0.1',1089,'108.90893931175367','108.90893931175094357153565661387382801276279376982')]
    for mu,n,seed,expected in frozen:
        y,res,width=solve_unique_root(mu,n,seed)
        m=y*mp.mpf(mu)
        if abs(m-mp.mpf(expected)) > mp.mpf('1e-45'):
            raise AssertionError((mu,n,mp.nstr(m,70),expected))
        if res > HP_RESIDUAL_TECHNICAL_MAX or width > HP_WIDTH_TARGET*2:
            raise AssertionError((mu,n,res,width))
    print('D29C_STATIC_SELF_TEST_PASS')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input-dir',required=True); ap.add_argument('--outdir',required=True); ap.add_argument('--self-test',action='store_true')
    args=ap.parse_args()
    if args.self_test: self_test(); return
    mp.mp.dps=DPS
    inp=Path(args.input_dir); out=Path(args.outdir); out.mkdir(parents=True,exist_ok=True)
    d29a=json.loads((inp/'D29A_RESULT.json').read_text()); d29b=json.loads((inp/'D29B_RESULT.json').read_text())
    started=time.time(); rows=[]
    for mu_s,fn in FILES:
        with (inp/fn).open(newline='') as f: rr=list(csv.DictReader(f))
        if len(rr)!=EXPECTED_COUNTS[mu_s]: raise RuntimeError(f'count mismatch {mu_s}: {len(rr)} != {EXPECTED_COUNTS[mu_s]}')
        seen=[int(r['n']) for r in rr]
        if seen != list(range(EXPECTED_COUNTS[mu_s])): raise RuntimeError(f'non-contiguous modes for mu={mu_s}')
        mu=mp.mpf(mu_s)
        for r in rr:
            n=int(r['n']); m_text=r['m_lambda']; m_float=float(m_text)
            y_hp,hp_res,hp_width=solve_unique_root(mu_s,n,m_text); m_hp=y_hp*mu
            m_bin=mp.mpf(m_float); y_bin=m_bin/mu; tol_bin=XTOL+RTOL*abs(y_bin); dy_bin=abs(y_bin-y_hp); dm_bin=abs(m_bin-m_hp); ratio_bin=dy_bin/tol_bin
            m_dec=mp.mpf(m_text); y_dec=m_dec/mu; tol_dec=XTOL+RTOL*abs(y_dec); dy_dec=abs(y_dec-y_hp); dm_dec=abs(m_dec-m_hp); ratio_dec=dy_dec/tol_dec
            branch_ok=(mp.mpf(n)<y_hp<mp.mpf(n)+mp.mpf('0.5'))
            rows.append({'mu1':float(mu_s),'n':n,'m_lambda_csv':m_text,'m_lambda_high_precision':mp.nstr(m_hp,75),'y_high_precision':mp.nstr(y_hp,75),'hp_equation_residual_abs':float(hp_res),'hp_final_bracket_width_y':float(hp_width),'hp_branch_ok':branch_ok,'binary64_abs_y_difference':float(dy_bin),'binary64_abs_m_difference':float(dm_bin),'binary64_solver_tolerance_y':float(tol_bin),'binary64_difference_over_solver_tolerance':float(ratio_bin),'serialized_decimal_abs_y_difference':float(dy_dec),'serialized_decimal_abs_m_difference':float(dm_dec),'serialized_decimal_solver_tolerance_y':float(tol_dec),'serialized_decimal_difference_over_solver_tolerance':float(ratio_dec)})
    if len(rows)!=3552: raise RuntimeError(f'total root count {len(rows)} != 3552')
    with (out/'D29C_ALL_ROOT_DIRECT_ERRORS.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    by_mu={}
    for mu in [10.0,1.0,0.1]:
        sub=[r for r in rows if r['mu1']==mu]
        by_mu[str(mu)]={'binary64':summarize(sub,'binary64_difference_over_solver_tolerance','binary64_abs_m_difference'),'serialized_decimal':summarize(sub,'serialized_decimal_difference_over_solver_tolerance','serialized_decimal_abs_m_difference'),'max_hp_equation_residual_abs':max(r['hp_equation_residual_abs'] for r in sub)}
    primary=summarize(rows,'binary64_difference_over_solver_tolerance','binary64_abs_m_difference'); legacy=summarize(rows,'serialized_decimal_difference_over_solver_tolerance','serialized_decimal_abs_m_difference')
    hp_integrity=(all(r['hp_branch_ok'] for r in rows) and max(r['hp_equation_residual_abs'] for r in rows) <= float(HP_RESIDUAL_TECHNICAL_MAX))
    pass_all=(primary['all_within_solver_tolerance'] and legacy['all_within_solver_tolerance'] and hp_integrity)
    worst_bin=max(rows,key=lambda r:r['binary64_difference_over_solver_tolerance']); worst_dec=max(rows,key=lambda r:r['serialized_decimal_difference_over_solver_tolerance'])
    result={'phase':'D29C_ALL_ROOT_80DIGIT_DIRECT_VALIDATION','version':'5.0.2','source_d29a_verdict':d29a.get('verdict'),'source_d29b_verdict':d29b.get('verdict'),'root_count_checked':len(rows),'published_parameter_values_interpreted_exactly':['10','1','0.1'],'high_precision_dps':DPS,'equation':'F(y)=pi*cot(pi*y)-mu1^2*y=0, y=m_lambda/mu1, mD=1','uniqueness_basis':"F'(y)=-pi^2*csc^2(pi*y)-mu1^2 < 0 on each n<y<n+1/2 branch",'solver':'safeguarded Newton followed by bracket refinement to <=1e-60 in y','comparison_tolerance':'xtol + rtol*|y|','solver_xtol':1e-14,'solver_rtol':1e-13,'primary_comparison':'exact binary64 value recovered by float(CSV_text), compared with 80-digit root','lineage_compatibility_comparison':'CSV decimal serialization interpreted exactly, matching the D29B spot-check convention','primary_binary64_statistics':primary,'serialized_decimal_statistics':legacy,'statistics_by_mu1':by_mu,'worst_binary64_root':worst_bin,'worst_serialized_decimal_root':worst_dec,'high_precision_solver_integrity':{'all_roots_on_expected_unique_branch':all(r['hp_branch_ok'] for r in rows),'max_equation_residual_abs':max(r['hp_equation_residual_abs'] for r in rows),'technical_residual_ceiling':float(HP_RESIDUAL_TECHNICAL_MAX),'all_pass':hp_integrity},'verdict':('PASS_D29C_ALL_3552_ROOTS_HIGH_PRECISION_DIRECT_VALIDATION' if pass_all else 'FAIL_D29C_ALL_ROOT_HIGH_PRECISION_DIRECT_VALIDATION'),'manuscript_consequence':('Replace backward-error wording with Newton-correction terminology and cite all-root direct high-precision validation as the primary root-accuracy evidence.' if pass_all else 'Do not claim all-root direct high-precision validation.'),'claim_control':{'D29A_original_automatic_FAIL_preserved':True,'D29B_corrective_PASS_preserved':True,'D29B_F_over_Fprime_relabelled_as_strict_backward_error':False,'Figure1_replication_scope_expanded':False,'Figure5_replication_claimed':False,'new_physics_claimed':False},'runtime_seconds':time.time()-started,'python':sys.version.split()[0],'mpmath':mp.__version__,'platform':platform.platform()}
    (out/'D29C_RESULT.json').write_text(json.dumps(result,indent=2)+chr(10))
    print(json.dumps({'verdict':result['verdict'],'root_count_checked':len(rows),'binary64_max_ratio':primary['max_ratio'],'binary64_max_abs_m_difference':primary['max_abs_m_difference'],'serialized_decimal_max_ratio':legacy['max_ratio'],'serialized_decimal_max_abs_m_difference':legacy['max_abs_m_difference'],'max_hp_equation_residual_abs':result['high_precision_solver_integrity']['max_equation_residual_abs'],'runtime_seconds':result['runtime_seconds']},indent=2))
    print('D29C_EXECUTION_COMPLETE')
    if not pass_all: raise SystemExit(2)

if __name__=='__main__': main()
