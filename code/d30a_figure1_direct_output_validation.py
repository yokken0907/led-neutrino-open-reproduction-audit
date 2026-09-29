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


