"""Exploratory: size classes with the a-priori cut-points (4/16 h) and two alternatives (2/8 h, 8/40 h), on the SQALE test issues.
Accuracy and quadratic weighted kappa of the most frequent class, recalibrated SQALE, M0 and M1. Output: results/exploratory/size_classes_cutpoints.json"""
import json, numpy as np, pandas as pd
from pathlib import Path
from sklearn.metrics import accuracy_score, cohen_kappa_score
ROOT = Path(__file__).resolve().parents[1]; D = f"{ROOT}/data"; OUT = f"{ROOT}/results/exploratory"
T0 = {"moodle": "2023-01-01", "mariadb": "2023-01-01", "percona": "2021-01-01"}
res = {}
for p in T0:
    df = pd.read_csv(f"{D}/features/{p}_features.csv"); df = df[df.hours > 0]; df["y"] = np.log(df.hours)
    ytr = df[df.fix_date < T0[p]].hours.values
    pr = pd.read_csv(f"{D}/predictions/{p}_predictions.csv").set_index("key")
    M0 = [c for c in pr.columns if c.startswith("M0 at")][0]; M1 = [c for c in pr.columns if c.startswith("M1 after")][0]
    sq = pd.read_json(f"{D}/sqale/{p}_sqale.jsonl", lines=True).drop_duplicates("key").set_index("key")
    d2 = df.join(sq[["sqale_min", "code_files_at_parent"]], on="key", how="inner"); d2 = d2[d2.code_files_at_parent > 0]
    s_tr, s_te = d2[d2.fix_date < T0[p]], d2[d2.fix_date >= T0[p]].copy()
    c = np.polyfit(np.log1p(s_tr.sqale_min), s_tr.y, 1); s_te["cal"] = np.exp(np.polyval(c, np.log1p(s_te.sqale_min)))
    s_te = s_te[s_te.key.isin(pr.index)]; s_te["m0"] = pr.loc[s_te.key, M0].values; s_te["m1"] = pr.loc[s_te.key, M1].values
    r = {"n": int(len(s_te))}
    for cuts in [(4, 16), (2, 8), (8, 40)]:
        cl = lambda h: np.digitize(h, list(cuts), right=True)
        ct = cl(s_te.hours.values); maj = np.bincount(cl(ytr)).argmax(); q = {}
        for k, v in [("most frequent class", np.full(len(ct), maj)), ("SQALE recalibrated", cl(s_te.cal.values)), ("M0", cl(s_te.m0.values)), ("M1", cl(s_te.m1.values))]:
            q[k] = dict(accuracy=float(accuracy_score(ct, v)), weighted_kappa=float(cohen_kappa_score(ct, v, weights="quadratic")) if len(set(v)) > 1 else 0.0)
        r[f"{cuts[0]}/{cuts[1]} h"] = q
    res[p] = r
json.dump(res, open(f"{OUT}/size_classes_cutpoints.json", "w"), indent=1)
for p, r in res.items():
    for k, q in r.items():
        if k != "n": print(p, k, {m: (round(v["accuracy"], 3), round(v["weighted_kappa"], 2)) for m, v in q.items()})
