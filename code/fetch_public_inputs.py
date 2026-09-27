#!/usr/bin/env python3
from pathlib import Path
import urllib.request, hashlib, json, sys, tarfile, io

ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"

NETWORK_SOURCES = [
    {"dest":"inputs/d25g/authority_sources/dayabay.jl","url":"https://raw.githubusercontent.com/Newtrinos-org/Newtrinos.jl/4388c2782248c37b08a8749247f49566fd89deac/src/experiments/daya_bay/daya_bay_3158days/dayabay.jl","sha256":"061e01680a18458aaa9df7439ff689c0c918bfc4bd25a459560f66ac9fa0405f"},
    {"dest":"inputs/d25g/authority_sources/test.jl","url":"https://raw.githubusercontent.com/Newtrinos-org/Newtrinos.jl/4388c2782248c37b08a8749247f49566fd89deac/src/experiments/daya_bay/daya_bay_3158days/test.jl","sha256":"4bddcf7032b17037215f3184f3b89caeb9a36a10e908e1fd9f60bafa45361e1b"},
    {"dest":"inputs/d25g/authority_sources/corr.txt","url":"https://raw.githubusercontent.com/Newtrinos-org/Newtrinos.jl/4388c2782248c37b08a8749247f49566fd89deac/src/experiments/daya_bay/daya_bay_3158days/DayaBay_CorrMat_arXiv_1607.05378.txt","sha256":"3e3234a2ada4a873c2ebd6baae4c84edc44c9e874a82afa2faa43daab773b190"},
    {"dest":"inputs/d25g/authority_sources/ibd_eh3.txt","url":"https://raw.githubusercontent.com/Newtrinos-org/Newtrinos.jl/4388c2782248c37b08a8749247f49566fd89deac/src/experiments/daya_bay/daya_bay_3158days/DayaBay_IBDPromptSpectrum_EH3_3158days.txt","sha256":"c1e015b6b41a8da5a30ac3df387482207104963f1de5bd0bcc0a61ab1ba9ad83"},
    {"dest":"inputs/d25g/authority_sources/bkg_eh3.txt","url":"https://raw.githubusercontent.com/Newtrinos-org/Newtrinos.jl/4388c2782248c37b08a8749247f49566fd89deac/src/experiments/daya_bay/daya_bay_3158days/DayaBay_BackgroundSpectrum_EH3_3158days.txt","sha256":"ddb2cb9b3d411140e3201546ca2966c4d61f47fff0fb9ee0fd6a8a703bd979f4"}
]
DAYABAY_DEST = "inputs/d26c1/DayaBay_DeltaChiSq_NO_3158days.txt"
DAYABAY_SHA = "52986e39f7844f157d064ba8c88ca2a692b39e6e915a994c039fb15a9538fa84"
DAYABAY_URLS = [
    "https://authors.library.caltech.edu/records/1g2ty-5pk30/files/DayaBay_DeltaChiSq_NO_3158days.txt?download=1",
    "https://arxiv.org/src/2211.14988v1/anc/DayaBay_DeltaChiSq_NO_3158days.txt",
]
ARXIV_EPRINT = "https://export.arxiv.org/e-print/2211.14988"

def h(b): return hashlib.sha256(b).hexdigest()

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*","Referer":"https://authors.library.caltech.edu/"})
    with urllib.request.urlopen(req,timeout=120) as r: return r.read()

def get_dayabay():
    errors=[]
    for u in DAYABAY_URLS:
        try:
            b=get(u)
            if h(b)==DAYABAY_SHA: return b, u
            errors.append(f"hash mismatch {u}: {h(b)}")
        except Exception as e: errors.append(f"{u}: {type(e).__name__}: {e}")
    try:
        blob=get(ARXIV_EPRINT)
        with tarfile.open(fileobj=io.BytesIO(blob),mode="r:*") as tf:
            for m in tf.getmembers():
                if m.name.endswith("DayaBay_DeltaChiSq_NO_3158days.txt"):
                    b=tf.extractfile(m).read()
                    if h(b)==DAYABAY_SHA: return b, ARXIV_EPRINT+"#"+m.name
                    errors.append(f"arXiv tar hash mismatch: {h(b)}")
    except Exception as e: errors.append(f"{ARXIV_EPRINT}: {type(e).__name__}: {e}")
    raise RuntimeError("Could not acquire official Daya Bay surface. " + " | ".join(errors))

def main():
    ledger=[]
    for s in NETWORK_SOURCES:
        p=ROOT/s["dest"]; p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists() and h(p.read_bytes())==s["sha256"]:
            b=p.read_bytes(); print("OK cached",s["dest"])
        else:
            print("GET",s["url"]); b=get(s["url"])
            got=h(b)
            if got!=s["sha256"]: raise SystemExit(f"HASH MISMATCH {s['dest']}: expected {s['sha256']}, got {got}")
            p.write_bytes(b)
        ledger.append({**s,"bytes":len(b),"acquisition":"network_or_cache"})
    p=ROOT/DAYABAY_DEST; p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists() and h(p.read_bytes())==DAYABAY_SHA:
        b=p.read_bytes(); source="cached_hash_verified"; print("OK cached",DAYABAY_DEST)
    else:
        print("GET official Daya Bay surface with fallback routes")
        b,source=get_dayabay(); p.write_bytes(b)
    ledger.append({"dest":DAYABAY_DEST,"sha256":DAYABAY_SHA,"bytes":len(b),"source":source})
    (ROOT/"inputs/FETCH_LEDGER.json").write_text(json.dumps(ledger,indent=2)+"\n")
    print("All public inputs acquired and hash-verified.")
if __name__=="__main__": main()
