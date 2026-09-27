#!/usr/bin/env python3
"""Finite-KK Dirac-bulk neutrino kernel following de Giorgi, Pasari & Turner (2026).

Scenario:
- flat S1/Z2 extra dimension
- bulk Majorana mass MJ = 0
- bulk Dirac mass MD != 0
- brane Dirac Yukawa mass mD solved so that the lightest singular value equals
  the requested physical neutrino mass.

This is a preflight implementation. No experimental limit is encoded here.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.optimize import brentq
from scipy.constants import value as scipy_value

HBARC_EV_UM=0.1973269804
SURPROB_ARG_CONVERSION=math.pi*2e-3*scipy_value("electron volt-inverse meter relationship")

def sin2theta_from_sin22theta(x):
    return 0.5*(1.0-math.sqrt(1.0-float(x)))

def physical_masses(m0,dm21,dm3abs,nmo,leading="dm32"):
    m0=float(m0);dm21=float(dm21);dm3=abs(float(dm3abs))
    if nmo>=0:
        m1=m0;m2=math.sqrt(max(0,m1*m1+dm21))
        m3=math.sqrt(max(0,m2*m2+dm3)) if leading=="dm32" else math.sqrt(max(0,m1*m1+dm3))
        return np.array([m1,m2,m3])
    m3=m0
    if leading=="dm32":
        m2=math.sqrt(max(0,m3*m3+dm3));m1=math.sqrt(max(0,m2*m2-dm21))
    else:
        m1=math.sqrt(max(0,m3*m3+dm3));m2=math.sqrt(max(0,m1*m1+dm21))
    return np.array([m1,m2,m3])

def wavefunction_factors(radius_um,MD_eV,nkk):
    R=float(radius_um)/HBARC_EV_UM
    x=R*float(MD_eV)
    if abs(x)<1e-10:
        chi0=1.0
    else:
        chi0=math.sqrt((2.0*math.pi*x)/math.expm1(2.0*math.pi*x))
    mu=np.arange(1,nkk+1,dtype=float)/R
    chin=np.sqrt(2.0)*mu/np.sqrt(mu*mu+MD_eV*MD_eV)
    return chi0,chin,mu

def tower(brane_mD_eV,radius_um,bulk_MD_eV,nkk):
    chi0,chin,mu=wavefunction_factors(radius_um,bulk_MD_eV,nkk)
    diag=np.sqrt(mu*mu+bulk_MD_eV*bulk_MD_eV)
    M=np.zeros((nkk+1,nkk+1),dtype=float)
    M[0,0]=chi0*brane_mD_eV
    M[0,1:]=chin*brane_mD_eV
    idx=np.arange(1,nkk+1)
    M[idx,idx]=diag
    vals,vecs=np.linalg.eigh(M@M.T)
    masses=np.sqrt(np.clip(vals,0,None))
    active_weights=np.abs(vecs[0,:])**2
    return masses,active_weights

def solve_brane_mD(mphys_eV,radius_um,bulk_MD_eV,nkk):
    mphys=float(mphys_eV)
    if mphys==0:return 0.0
    def f(x):
        return tower(x,radius_um,bulk_MD_eV,nkk)[0][0]-mphys
    hi=max(0.1,2*mphys)
    fv=f(hi)
    for _ in range(100):
        if fv>=0:break
        hi*=2;fv=f(hi)
    if fv<0:
        raise RuntimeError(f"no bracketing solution: mphys={mphys}, radius={radius_um}, MD={bulk_MD_eV}, N={nkk}")
    return float(brentq(f,0,hi,xtol=1e-14,rtol=1e-13,maxiter=500))

def electron_weights(sin22theta12,sin22theta13):
    s12=sin2theta_from_sin22theta(sin22theta12)
    s13=sin2theta_from_sin22theta(sin22theta13)
    return np.array([(1-s12)*(1-s13),s12*(1-s13),s13])

def pee_array(E_MeV,L_m,radius_um,m0_eV,bulk_ratio,
              sin22theta12,sin22theta13,dm21_eV2,dm3abs_eV2,nmo,
              leading="dm32",nkk=48,
              surprob_arg_conversion=SURPROB_ARG_CONVERSION):
    E=np.asarray(E_MeV,dtype=float)
    ue2=electron_weights(sin22theta12,sin22theta13)
    phys=physical_masses(m0_eV,dm21_eV2,dm3abs_eV2,nmo,leading)
    mu1=HBARC_EV_UM/float(radius_um)
    MD=float(bulk_ratio)*mu1
    phase_pref=float(surprob_arg_conversion)*float(L_m)*0.5e-3
    amp=np.zeros(E.shape,dtype=np.complex128)
    solved=[]
    for u2,mphys in zip(ue2,phys):
        md=solve_brane_mD(mphys,radius_um,MD,nkk)
        masses,w=tower(md,radius_um,MD,nkk)
        amp += u2*(np.exp(-1j*np.outer(1.0/E,masses*masses)*phase_pref)@w)
        solved.append(md)
    return np.abs(amp)**2,np.array(solved)
