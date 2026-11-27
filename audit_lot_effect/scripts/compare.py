import json, glob, csv, sys, os
from scipy.stats import spearmanr
import numpy as np
C="/home/user/sqale-effort-replication/data/confirmatory/"; V3="/home/user/sqale-effort-replication/preregistration_v3/scan/"
def load(p):
    d={}
    for l in open(p):
        r=json.loads(l)
        if "error" not in r: d[r["key"]]=r
    return d
def iso(pattern):
    d={}
    for p in glob.glob(pattern): d.update(load(p))
    return d
groups={}
for proj,D in (("moodle","moodle1"),("mariadb","mariadb1")):
    s=iso(f"/home/user/audit/{D}/single_w*.jsonl")
    groups[f"{proj}_holdout"]=(load(C+f"holdout_scan_{proj}.jsonl"),s,"sqale_min","ncloc")
    groups[f"{proj}_exploratory"]=(load(C+f"exploratory_sample_scan_{proj}.jsonl"),s,"sqale_min","ncloc")
for p in ("mosip","openlmis","openmrs"):
    groups[p]=(load(V3+f"scan_{p}.jsonl"),iso(f"/home/user/audit/v3/{p}/single_w*.jsonl"),"sqale_min","ncloc")
out=sys.argv[1] if len(sys.argv)>1 else "/home/user/audit/compare/out"; os.makedirs(out,exist_ok=True)
summ={}
for g,(o,s,fs,fn) in groups.items():
    ks=[k for k in o if k in s]
    if not ks: continue
    rows=[]
    for k in ks:
        a,b=float(o[k].get(fs,0)),float(s[k].get(fs,0)); na,nb=float(o[k].get(fn,0)),float(s[k].get(fn,0))
        rows.append(dict(issue_key=k,sqale_original=a,sqale_isolated=b,diff_percent=(100*(b-a)/a if a else (0.0 if b==0 else float("inf"))),ncloc_original=na,ncloc_isolated=nb,
                         sqale_lines_original=o[k].get("sqale_righe_modificate"),sqale_lines_isolated=s[k].get("sqale_righe_modificate")))
    with open(f"{out}/{g}.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    A=np.array([r["sqale_original"] for r in rows]); B=np.array([r["sqale_isolated"] for r in rows])
    dp=np.array([r["diff_percent"] for r in rows if r["sqale_original"]>0])
    summ[g]=dict(n=len(rows),identical=int((A==B).sum()),pct_identical=round(100*(A==B).mean(),1),lower=int((B<A).sum()),higher=int((B>A).sum()),
                 ncloc_identical=int(sum(r["ncloc_original"]==r["ncloc_isolated"] for r in rows)),
                 spearman=round(spearmanr(A,B)[0],4) if len(rows)>2 else None,
                 diff_pct_p5_p50_p95=[round(float(x),2) for x in np.percentile(dp,[5,50,95])] if len(dp) else None,
                 max_abs_diff_pct=round(float(np.abs(dp).max()),2) if len(dp) else None)
json.dump(summ,open(f"{out}/summary.json","w"),indent=1); print(json.dumps(summ,indent=1))
