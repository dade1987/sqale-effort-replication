# Exploratory: re-weights the analysed issues to the population of ALL linked fixed issues (with and without hours)
# by inverse probability of having logged hours, then recomputes the partial Spearman rho of hours with SQALE given NCLOC.
import numpy as np,pandas as pd,json
from sklearn.linear_model import LogisticRegression
import os
H=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(H,"..","data"); rng=np.random.default_rng(2026)
def X(df):
    x=pd.DataFrame({"ll":np.log1p(df.lines_changed),"lf":np.log1p(df.n_files),"lc":np.log1p(df.n_commits),"lm":np.log1p(df.n_comments.fillna(0)),"yr":df.year-2018})
    for t in ["Bug","Task","New Feature","Improvement"]: x["t_"+t]=(df.type==t).astype(float)
    for p in ["Blocker","Critical","Major","Minor"]: x["p_"+p]=(df.priority==p).astype(float)
    return x.values
def wpartial(h,s,n,w):
    r=lambda v: pd.Series(v).rank().values
    H,S,N=r(h),r(s),r(n); W=w/w.sum()
    def res(y):
        A=np.c_[np.ones_like(N),N]; b=np.linalg.lstsq(A*np.sqrt(W)[:,None],y*np.sqrt(W),rcond=None)[0]; return y-A@b
    a,b=res(H),res(S); return float((W*a*b).sum()/np.sqrt((W*a*a).sum()*(W*b*b).sum()))
out={}
for p in ["moodle","mariadb"]:
    a=pd.read_json(f"{H}/data/{p}_fixed_2018_all.jsonl.gz",lines=True); g=pd.read_json(f"{H}/data/{p}_git_stats.jsonl.gz",lines=True)
    g["lines_changed"]=g.lines_added+g.lines_deleted; a["year"]=pd.to_datetime(a.resolved,utc=True).dt.year
    m=a.merge(g,on="key"); m["hh"]=(m.timespent.fillna(0)>0).astype(int)
    lr=LogisticRegression(max_iter=2000,C=1.0).fit(X(m),m.hh); m["ps"]=lr.predict_proba(X(m))[:,1]
    sq=pd.read_json(f"{D}/sqale/{p}_sqale.jsonl",lines=True).drop_duplicates("key"); f=pd.read_csv(f"{D}/features/{p}_features.csv")[["key","hours"]]
    d=sq[sq.code_files_at_parent>0].merge(f,on="key").merge(m[["key","ps"]],on="key")
    w=1/np.clip(d.ps.values,0.05,1)
    est=lambda idx,ww: wpartial(d.hours.values[idx],d.sqale_min.values[idx],d.ncloc.values[idx],ww[idx])
    i0=np.arange(len(d)); u=est(i0,np.ones(len(d))); wv=est(i0,w)
    bs=[est(ix,w)-est(ix,np.ones(len(d))) for ix in (rng.integers(0,len(d),len(d)) for _ in range(1000))]
    out[p]=dict(n=len(d),rho_unweighted=u,rho_weighted=wv,diff_ci90=[float(np.percentile(bs,5)),float(np.percentile(bs,95))],
                weight_max=float(w.max()),ess=float(w.sum()**2/(w**2).sum()),auc=float(__import__("sklearn.metrics",fromlist=["x"]).roc_auc_score(m.hh,m.ps)))
    print(p,out[p])
json.dump(out,open(f"{H}/results/reweight.json","w"),indent=1)
