# Exploratory (not preregistered), 5 Nov 2026, update after 100 MOSIP links were checked (8% wrong, Wilson 95% CI 4-15%; 14% not fully correct): how much could wrong issue-commit links hide an effect in MOSIP?
# Real MOSIP hours, developers and NCLOC (protocol-conforming sample: 449 re-run issues treated as missing).
# A synthetic SQALE with a chosen true partial rho is built; then a fraction f of issues gets the code measures (SQALE, NCLOC)
# of a random other issue, as a wrong link would. The frozen H1 statistic and developer bootstrap are applied.
import sys, json, numpy as np, pandas as pd
sys.argv = ["x", "x"]; sys.path.insert(0, "/mnt/project-files/ricerca2/preregistrazione_nuovi_progetti/code")
exec(open("/mnt/project-files/ricerca2/preregistrazione_nuovi_progetti/code/confermativo_v3.py").read().split("out = {")[0])
P = "/mnt/project-files/ricerca2/preregistrazione_nuovi_progetti"
f = pd.read_csv(P + "/data/features_v3_mosip.csv")
s = pd.DataFrame([json.loads(l) for l in open(P + "/risultati/sensitivity_strict_rerun_rule/scan_mosip_without_lots48_56.jsonl")]).rename(columns={"sqale_min": "sqale"})
a = f.merge(s, on="key"); a = a[(a.files_measured > 0) & (a.ncloc > 0)].reset_index(drop=True)
print("n", len(a), "observed", round(partial(a), 4))
BB, REPS = 400, 200
rng = np.random.default_rng(7)
rh = rank_resid(a, "hours", ["ncloc"]); rh = (rh - rh.mean()) / rh.std()
ln = np.log(a.ncloc.values); ln = (ln - ln.mean()) / ln.std()
def make(c, rng):
    e = c * rh + np.sqrt(1 - c * c) * rng.standard_normal(len(a))
    return np.exp(2 + 1.6 * ln + 0.8 * e)          # rank correlation with NCLOC about 0.85-0.9, as in the data
def boot_ci(d, rng):
    g = pd.factorize(d.dev)[0]; idx = [np.where(g == i)[0] for i in range(g.max() + 1)]
    bs = [partial(d.iloc[np.concatenate([idx[i] for i in rng.integers(0, len(idx), len(idx))])]) for _ in range(BB)]
    return np.percentile(bs, [5, 95])
# calibrate c so that the clean partial rho is about the target
res = {"n": int(len(a)), "observed_partial_rho": partial(a), "B": BB, "reps": REPS, "scenarios": []}
for target in (0.10, 0.15):
    c = target
    for _ in range(6):
        vals = []
        for _r in range(30):
            d = a.copy(); d["sqale"] = make(c, rng); vals.append(partial(d))
        c *= target / np.mean(vals)
    for frac in (0.0, 0.08, 0.15, 0.30):
        obs, neg, sup = [], 0, 0
        for r in range(REPS):
            d = a.copy(); d["sqale"] = make(c, rng)
            k = rng.random(len(d)) < frac; j = rng.integers(0, len(d), k.sum())
            d.loc[k, ["sqale", "ncloc"]] = d[["sqale", "ncloc"]].values[j]
            obs.append(partial(d)); lo, hi = boot_ci(d, rng)
            neg += (lo > -0.1 and hi < 0.1); sup += lo > 0
        sc = {"true_rho": target, "wrong_share": frac, "mean_observed_rho": float(np.mean(obs)), "share_called_negligible": neg / REPS, "share_CI_above_0": sup / REPS}
        print(sc, flush=True); res["scenarios"].append(sc)
json.dump(res, open(P + "/risultati/exploratory_wrong_links/sim100/sim_wrong_links_100.json", "w"), indent=1)
