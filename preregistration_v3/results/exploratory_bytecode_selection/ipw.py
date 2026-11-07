# Exploratory selection sensitivity (not preregistered): inverse-probability weighting of the compiled issues so that they
# resemble all attempted issues on year, hours, NCLOC, files, issue type and repository. Weighted partial Spearman
# (weighted ranks, weighted least squares, weighted correlation), developer-clustered bootstrap B=5000, seed 2026, weights fixed.
# Validation: the weighted registered-measure estimate on the compiled issues should move toward the all-attempted estimate.
import json, sys, numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
B, SEED = 5000, 2026; out = sys.argv[1]; F = "/home/user/hb/ana/final"
def wrank(x, w):
    o = np.argsort(x, kind="mergesort"); xs, ws = x[o], w[o]; cw = np.cumsum(ws); r = np.empty(len(x)); i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and xs[j + 1] == xs[i]: j += 1
        r[o[i:j + 1]] = (cw[j] + (cw[i - 1] if i else 0)) / 2; i = j + 1
    return r
def wresid(y, z, w):
    X = np.column_stack([np.ones(len(y)), z]); sw = np.sqrt(w); b = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)[0]; return y - X @ b
def wpartial(h, s, n, w):
    rh, rs, rn = wrank(h, w), wrank(s, w), wrank(n, w); a, b = wresid(rh, rn, w), wresid(rs, rn, w)
    a, b = a - np.average(a, weights=w), b - np.average(b, weights=w)
    return float(np.sum(w * a * b) / np.sqrt(np.sum(w * a * a) * np.sum(w * b * b)))
res = {}
for p in ("openmrs", "openlmis"):
    d = pd.read_csv(f"{out}/issues_{p}.csv")
    X = pd.DataFrame({"lh": np.log1p(d.hours), "ln": np.log1p(d.ncloc), "lf": np.log1p(d.files)})
    yr = d.year.clip(d.year.quantile(.05), d.year.quantile(.95)).astype(int).astype(str)
    rp = d.repo.where(d.repo.map(d.repo.value_counts()) >= 20, "other"); ty = d.type.where(d.type.map(d.type.value_counts()) >= 20, "other")
    X = pd.concat([X, pd.get_dummies(yr, prefix="y", drop_first=True), pd.get_dummies(rp, prefix="r", drop_first=True), pd.get_dummies(ty, prefix="t", drop_first=True)], axis=1).astype(float)
    m = LogisticRegression(C=1.0, max_iter=5000).fit((X - X.mean()) / X.std().replace(0, 1), d.compiled)
    ps = m.predict_proba((X - X.mean()) / X.std().replace(0, 1))[:, 1]; d["ps"] = ps
    c = d[d.compiled].copy(); w = 1 / c.ps.values; w = np.minimum(w, np.quantile(w, .99)); c["w"] = w
    ess = float(w.sum() ** 2 / (w ** 2).sum())
    bal = {}
    for v in ("year", "hours", "ncloc", "files"):
        t = np.log1p(d[v]) if v != "year" else d[v]; tc = np.log1p(c[v]) if v != "year" else c[v]
        sd = t.std(); bal[v] = {"smd_unweighted_vs_all": round(float((tc.mean() - t.mean()) / sd), 3), "smd_weighted_vs_all": round(float((np.average(tc, weights=c.w) - t.mean()) / sd), 3)}
    reg = {json.loads(l)["key"]: json.loads(l) for l in open(f"{F}/scan_registered_{p}.jsonl")}
    byt = {json.loads(l)["key"]: json.loads(l) for l in open(f"{F}/scan_with_bytecode_{p}.jsonl")}
    c["s_reg"] = c.key.map(lambda k: reg[k]["sqale_min"]); c["s_bin"] = c.key.map(lambda k: byt[k]["sqale_min"])
    g = pd.factorize(c.dev)[0]; idx = [np.where(g == i)[0] for i in range(g.max() + 1)]; R = {"ess": round(ess, 1), "n": len(c), "balance": bal}
    for lab, col in (("registered", "s_reg"), ("with_bytecode", "s_bin")):
        for wl, ww in (("unweighted", np.ones(len(c))), ("ipw", c.w.values)):
            h, s, n = c.hours.values, c[col].values.astype(float), c.ncloc.values.astype(float)
            est = wpartial(h, s, n, ww); rng = np.random.default_rng(SEED); bs = []
            for _ in range(B):
                ii = np.concatenate([idx[i] for i in rng.integers(0, len(idx), len(idx))]); bs.append(wpartial(h[ii], s[ii], n[ii], ww[ii]))
            R[f"{lab}_{wl}"] = {"rho": round(est, 3), "CI90_dev": [round(float(x), 3) for x in np.percentile(bs, [5, 95])]}
    res[p] = R; print(p, json.dumps(R), flush=True)
json.dump(res, open(f"{out}/summary_ipw.json", "w"), indent=1)
