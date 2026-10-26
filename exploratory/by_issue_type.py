# EXPLORATORY table (not preregistered): error by issue type (type at creation) on the test issues with SQALE (Table 11).
# Same distributed predictions and same SQALE recalibration as model.py (log hours ~ log1p SQALE minutes, fitted on issues before TEST_START).
import sys, json, numpy as np, pandas as pd
from common import metrics, compare, holm
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = f"{ROOT}/data"; OUT = f"{ROOT}/results/exploratory"
M0, M1 = "M0 at assignment", "M1 after file localisation"
out = {}
for p in ["moodle", "mariadb", "percona"]:
    T0 = "2021-01-01" if p == "percona" else "2023-01-01"
    df = pd.read_csv(f"{D}/features/{p}_features.csv").merge(pd.read_csv(f"{D}/history/{p}_history.csv"), on="key", how="left")
    df = df[df.hours > 0].copy(); df["type"] = df.type_open.fillna(df.type); df["y"] = np.log(df.hours)
    ytr = df[df.fix_date < T0].hours.values
    sq = pd.read_json(f"{D}/sqale/{p}_sqale.jsonl", lines=True).drop_duplicates("key").set_index("key")
    d2 = df.join(sq[["sqale_min", "code_files_at_parent"]], on="key", how="inner"); d2 = d2[d2.code_files_at_parent > 0]
    s_tr, s_te = d2[d2.fix_date < T0], d2[d2.fix_date >= T0]
    c = np.polyfit(np.log1p(s_tr.sqale_min), s_tr.y, 1)
    pr = pd.read_csv(f"{D}/predictions/{p}_predictions.csv").set_index("key")
    s_te = s_te[s_te.key.isin(pr.index)]
    s_te["tipo"] = s_te.type.where(s_te.type.isin(["Bug", "Improvement", "Task", "New Feature"]), "altro")
    R = {}
    for t in ["all"] + sorted(s_te.tipo.unique()):
        st = s_te if t == "all" else s_te[s_te.tipo == t]
        if len(st) < 20: R[t] = {"n": int(len(st))}; continue
        ys = st.hours.values; g = pr.loc[st.key, "assignee"].fillna("?").replace("", "?").values
        P = {"SQALE raw": np.maximum(st.sqale_min.values / 60, 1 / 60), "SQALE recalibrated": np.exp(np.polyval(c, np.log1p(st.sqale_min.values))),
             "M0": pr.loc[st.key, M0].values, "M1": pr.loc[st.key, M1].values}
        r = {"n": int(len(st))}; r.update({k: metrics(ys, v, ytr) for k, v in P.items()})
        cmp_ = {"M0 vs SQALE recalibrated": compare(ys, P["M0"], P["SQALE recalibrated"], g), "M1 vs SQALE recalibrated": compare(ys, P["M1"], P["SQALE recalibrated"], g)}
        holm(cmp_); r.update(cmp_); R[t] = r
    out[p] = R
json.dump(out, open(f"{OUT}/by_issue_type.json", "w"), indent=1, default=float)
for p, R in out.items():
    print("==", p)
    for t, r in R.items():
        if "M1" not in r: print(f"  {t}: n={r['n']} (troppo poche)"); continue
        f = lambda k: f"{r[k]['MAE']:.2f}/{r[k]['MdAE']:.2f}/{100*r[k]['within2x']:.0f}%"
        c1 = r["M1 vs SQALE recalibrated"]
        print(f"  {t:12s} n={r['n']:4d} raw {f('SQALE raw')} | recal {f('SQALE recalibrated')} | M0 {f('M0')} | M1 {f('M1')} | dMAE M1-recal {c1['dMAE']:+.2f} p_boot {c1['p_boot']:.4f} p_wil {c1['p_wilcoxon']:.4f}")
