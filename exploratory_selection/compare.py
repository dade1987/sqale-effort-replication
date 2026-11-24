# Exploratory, post hoc: compares (A) fixed issues with vs without logged hours (resolved 2018+, linked with the paper's rule)
# and (B) sampled issues that change existing code vs those excluded from the SQALE analyses (new files only, build, docs).
# Effect sizes: standardised mean difference (SMD, on log1p for counts) and Cliff's delta; |SMD| >= 0.1 = imbalance (Austin 2009).
import json,gzip,sys,numpy as np,pandas as pd
import os
H=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(H,"..","data")
def smd(a,b):
    a,b=np.asarray(a,float),np.asarray(b,float); s=np.sqrt((a.var(ddof=1)+b.var(ddof=1))/2); return (a.mean()-b.mean())/s if s>0 else 0.0
def smd_p(p1,p0):
    s=np.sqrt((p1*(1-p1)+p0*(1-p0))/2); return (p1-p0)/s if s>0 else 0.0
def cliff(a,b):
    a=np.sort(np.asarray(a,float)); b=np.sort(np.asarray(b,float))
    gt=np.searchsorted(b,a,side="left").sum(); lt=(len(b)-np.searchsorted(b,a,side="right")).sum()
    return (gt-lt)/(len(a)*len(b))
def table(df,g,num,cat):
    A=df[df[g]];B=df[~df[g]];rows=[]
    for c in num:
        a=A[c].dropna();b=B[c].dropna()
        rows.append(dict(trait=c,grp1=f"{a.median():.4g}",grp0=f"{b.median():.4g}",SMD=smd(np.log1p(a),np.log1p(b)),cliff=cliff(a,b)))
    for c,lev in cat:
        for v in lev:
            p1=(A[c]==v).mean();p0=(B[c]==v).mean()
            rows.append(dict(trait=f"{c}={v}",grp1=f"{100*p1:.1f}%",grp0=f"{100*p0:.1f}%",SMD=smd_p(p1,p0),cliff=np.nan))
    t=pd.DataFrame(rows); t["n1"]=len(A); t["n0"]=len(B); return t
def jira(p):
    a=pd.read_json(f"{H}/data/{p}_fixed_2018_all.jsonl.gz",lines=True)
    a["created"]=pd.to_datetime(a.created,utc=True); a["resolved"]=pd.to_datetime(a.resolved,utc=True)
    a["days_open"]=(a.resolved-a.created).dt.total_seconds()/86400; a["year"]=a.resolved.dt.year
    a["prio"]=a.priority.map(lambda x: "Blocker/Critical" if x in ("Blocker","Critical") else ("Major" if x=="Major" else "Minor/Trivial" if x in ("Minor","Trivial") else "other"))
    a["typ"]=a.type.map(lambda x: x if x in ("Bug","Improvement","New Feature","Task") else "other")
    return a
NUM=["lines_changed","n_files","n_commits","days_open","n_comments","year"]
CAT=[("typ",["Bug","Improvement","New Feature","Task"]),("prio",["Blocker/Critical","Major","Minor/Trivial"])]
out={}
for p in ["moodle","mariadb"]:
    a=jira(p); g=pd.read_json(f"{H}/data/{p}_git_stats.jsonl.gz",lines=True); g["lines_changed"]=g.lines_added+g.lines_deleted
    a["has_hours"]=a.timespent.fillna(0)>0; a["linked"]=a.key.isin(set(g.key))
    out[f"{p}_link_rate"]={"with":[int(a[a.has_hours].linked.sum()),int(a.has_hours.sum())],"without":[int(a[~a.has_hours].linked.sum()),int((~a.has_hours).sum())]}
    m=a[a.linked].merge(g,on="key")
    for lab,sub in [("all2018",m),("test2023",m[m.year>=2023])]:
        t=table(sub,"has_hours",NUM,CAT); t.to_csv(f"{H}/results/A_{p}_{lab}.csv",index=False); print("\nA",p,lab); print(t.round(3).to_string())
    # also share with hours by year, without linking
    print(a.groupby("year").has_hours.mean().round(3).to_dict())
# B: change existing code vs excluded (code_files_at_parent==0), on the SQALE samples (Percona: test period 2021+)
for p in ["moodle","mariadb","percona"]:
    f=pd.read_csv(f"{D}/features/{p}_features.csv"); sq=pd.read_json(f"{D}/sqale/{p}_sqale.jsonl",lines=True).drop_duplicates("key")
    d=f.merge(sq[["key","code_files_at_parent"]],on="key")
    if p=="percona": d=d[d.fix_date>="2021-01-01"]
    d["analysed"]=d.code_files_at_parent>0; d["lines_changed"]=d.p_added+d.p_deleted; d["n_commits"]=d.p_commits
    d["days_open"]=(pd.to_datetime(d.resolved)-pd.to_datetime(d.created)).dt.days; d["year"]=pd.to_datetime(d.resolved).dt.year
    d["prio"]=d.priority.map(lambda x: "Blocker/Critical" if x in ("Blocker","Critical","High","Highest","Urgent") else ("Major" if x in("Major","Medium") else "Minor/Trivial" if x in ("Minor","Trivial","Low","Lowest") else "other"))
    d["typ"]=d.type.map(lambda x: x if x in ("Bug","Improvement","New Feature","Task") else "other")
    if p!="percona":
        c=jira(p)[["key","n_comments"]]; d=d.merge(c,on="key",how="left")
    else: d["n_comments"]=np.nan
    t=table(d,"analysed",["hours"]+NUM,CAT); t.to_csv(f"{H}/results/B_{p}.csv",index=False); print("\nB",p); print(t.round(3).to_string())
    print(" priorities:",d.priority.value_counts().to_dict(), "new-file share among excluded:", (d[~d.analysed].n_new/d[~d.analysed].n_files).median())
json.dump(out,open(f"{H}/results/link_rates.json","w"),indent=1); print(out)
