#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument("--d25g",required=True)
p.add_argument("--d26c1",required=True)
p.add_argument("--out",required=True)
a=p.parse_args()
n25=json.loads(Path(a.d25g).read_text()); o25=json.loads((ROOT/"expected/D25G_R2_RESULT.json").read_text())
n26=json.loads(Path(a.d26c1).read_text()); o26=json.loads((ROOT/"expected/D26C1_RESULT.json").read_text())
c25={
 "verdict_equal":n25.get("verdict")==o25.get("verdict"),
 "N192_crossings_equal":n25.get("N192",{}).get("crossing_count")==o25.get("N192",{}).get("crossing_count"),
 "N384_crossings_equal":n25.get("N384",{}).get("crossing_count")==o25.get("N384",{}).get("crossing_count"),
 "N192_sequence_equal":n25.get("N192",{}).get("crossing_sequence")==o25.get("N192",{}).get("crossing_sequence"),
 "N384_sequence_equal":n25.get("N384",{}).get("crossing_sequence")==o25.get("N384",{}).get("crossing_sequence"),
}
c25["pass"]=all(c25.values())
keys=["profiled_public_best_abs_chi2_difference","spearman_rho","median_abs_delta_difference","p90_abs_delta_difference"]
tol={"profiled_public_best_abs_chi2_difference":.05,"spearman_rho":.005,"median_abs_delta_difference":.05,"p90_abs_delta_difference":.10}
c26={
 "verdict_equal":n26.get("verdict")==o26.get("verdict"),
 "gates_equal":n26.get("gates")==o26.get("gates"),
}
c26["metric_deltas"]={k:abs(n26["metrics"][k]-o26["metrics"][k]) for k in keys}
c26["metrics_within_frozen_D27_tolerance"]=all(c26["metric_deltas"][k]<=tol[k] for k in keys)
c26["pass"]=c26["verdict_equal"] and c26["gates_equal"] and c26["metrics_within_frozen_D27_tolerance"]
rep={"phase":"D27B_PUBLIC_REPOSITORY_REPRODUCTION","checks":{"D25G_R2":c25,"D26C1":c26}}
rep["overall_pass"]=c25["pass"] and c26["pass"]
Path(a.out).write_text(json.dumps(rep,indent=2)+"\n")
print(json.dumps(rep,indent=2))
sys.exit(0 if rep["overall_pass"] else 3)
