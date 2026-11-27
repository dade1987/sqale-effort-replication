# Point 5: calibration of the two-way bootstrap TOST on the observed dependence structure (fourth registration sample).
import sys, json, numpy as np, pandas as pd
from scipy.stats import norm, rankdata
from common_v4 import load, REG
rho, s0, s1, out = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
g = load(REG); a = g["a"].copy(); BS = 2000; g["B"] = BS; S = 0.10
e2 = g["rank_resid"](a, "sqale", ["ncloc"]); u = norm.ppf(rankdata(e2) / (len(e2) + 1))
e1 = g["rank_resid"](a, "hours", ["ncloc"]); e1 = (e1 - e1.mean()) / e1.std()
def share(gr):   # method-of-moments share of variance between groups
    s = pd.Series(e1).groupby(gr.values); m, n = s.mean(), s.size()
    k = len(n); N = n.sum(); msb = (n * (m - 0) ** 2).sum() / (k - 1); msw = ((s.var(ddof=1) * (n - 1)).sum()) / (N - k)
    n0 = (N - (n ** 2).sum() / N) / (k - 1); sb = max((msb - msw) / n0, 0); return sb / (sb + msw)
sd, sc = share(a.dev), share(a.comp)
r = 2 * np.sin(np.pi * rho / 6)   # Pearson correlation of the Gaussian copula giving Spearman rho
gd, gc = pd.factorize(a.dev)[0], pd.factorize(a.comp)[0]
import os
res = json.load(open(out))["sims"] if os.path.exists(out) else []
done = {r["seed"] for r in res}
for seed in range(s0, s1):
    if seed in done: continue
    rng = np.random.default_rng(seed)
    noise = np.sqrt(sd) * rng.standard_normal(gd.max() + 1)[gd] + np.sqrt(sc) * rng.standard_normal(gc.max() + 1)[gc] + np.sqrt(max(1 - sd - sc, 0)) * rng.standard_normal(len(a))
    noise /= np.sqrt(sd + sc + max(1 - sd - sc, 0))
    a["hours"] = r * u + np.sqrt(1 - r ** 2) * noise
    est = g["partial"](a, "sqale")
    bs = np.array([g["partial"](a.iloc[i], "sqale") for i in g["boot_twoway"](a, np.random.default_rng(10 ** 6 + seed))])
    lo, hi = np.nanpercentile(bs, [5, 95])
    res.append({"seed": seed, "est": est, "lo": float(lo), "hi": float(hi), "nan": int((~np.isfinite(bs)).sum()),
                "p_tost": float(max(np.mean(bs <= -S) + 1 / BS, np.mean(bs >= S) + 1 / BS)), "verdict": g["verdict"](lo, hi)})
    json.dump({"rho": rho, "r_latent": r, "share_dev": sd, "share_comp": sc, "B": BS, "sims": res}, open(out, "w"))
