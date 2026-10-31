# Variant of v4_null_verdict_sim.py: probability of each H1 verdict by true partial rho, with the bootstrap clustered by developer (as registered)
# or two-way (developer x first Jira component, as in v4_checks.py c), optionally at a larger n by resampling the hold-out issues with replacement
# (expected n of the second MariaDB test). Exploratory. Usage: python3 v4_null_verdict_sim_twoway.py <project> <n_sim> <B> <dev|twoway> [n] [targets]
# Writes results/exploratory/v4_null_verdict_sim_<twoway|dev>_<project>[_n<n>].json
import sys, json, os, numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)) + "/.."
p, NSIM, BB, mode = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
N = int(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] != "-" else None
T = [float(t) for t in sys.argv[6].split(",")] if len(sys.argv) > 6 else [0.0, 0.05, 0.10]
src = open(f"{H}/preregistration/confermativo.py").read()
exec(src[src.index("B, SEED"):src.index("\nst = ")]); exec(src[src.index("def rank_resid"):src.index("out = {")])
B = BB
st = pd.read_csv(f"{H}/data/history/{p}_history.csv")[["key", "assignee_T"]]
df = pd.read_csv(f"{H}/data/features/{p}_features.csv").merge(st, on="key", how="left")
df["dev"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace({"git:": "?", "": "?"})
df["comp"] = df.components.fillna("?").astype(str).str.split(";").str[0].replace({"": "?"})
df = df[df.hours > 0]
ho = pd.read_json(f"{H}/data/confirmatory/holdout_scan_{p}.jsonl", lines=True).drop_duplicates("key").merge(df[["key", "hours", "dev", "comp"]], on="key")
a0 = ho[(ho.code_files_at_parent > 0) & (ho.ncloc > 0)].copy().reset_index(drop=True)
rng = np.random.default_rng(SEED); sim_rng = np.random.default_rng(20261031)
def boot_twoway(a):
    gd, gc = pd.factorize(a.dev)[0], pd.factorize(a.comp)[0]
    for _ in range(B):
        wd = np.bincount(rng.integers(0, gd.max() + 1, gd.max() + 1), minlength=gd.max() + 1)
        wc = np.bincount(rng.integers(0, gc.max() + 1, gc.max() + 1), minlength=gc.max() + 1)
        yield np.repeat(np.arange(len(a)), wd[gd] * wc[gc])
boot = boot_groups if mode == "dev" else boot_twoway
def test(a):
    est = partial(a, "x", ["ncloc"]); bs = np.array([partial(a.iloc[i], "x", ["ncloc"]) for i in boot(a)])
    lo, hi = np.nanpercentile(bs, [5, 95]); return est, verdict_rho(est, lo, hi)
out = {"project": p, "bootstrap": mode, "n_holdout": int(len(a0)), "n": N or int(len(a0)), "n_sim": NSIM, "B": B, "runs": {}}
for target in T:
    counts, rhos = {}, []
    for k in range(NSIM):
        a = a0.iloc[sim_rng.integers(0, len(a0), N)].reset_index(drop=True) if N else a0.copy()
        l = np.log1p(a.ncloc.values); s = np.log1p(a.sqale_min.values); X = np.column_stack([np.ones(len(l)), l])
        fit = X @ np.linalg.lstsq(X, s, rcond=None)[0]; res = s - fit; sd = res.std()
        eh = rank_resid(a, "hours", ["ncloc"]); eh = (eh - eh.mean()) / eh.std()
        z = sim_rng.permutation(res) / sd
        z = target * eh + np.sqrt(1 - target ** 2) * (z - z.mean()) / z.std() if target else z
        a["x"] = fit + sd * z
        est, v = test(a); counts[v] = counts.get(v, 0) + 1; rhos.append(est)
        if k == 9: print(f"{p} {mode} n={out['n']} target {target}: first 10 runs", counts, "mean rho", round(float(np.mean(rhos)), 3), flush=True)
    out["runs"][str(target)] = {"verdict_share": {v: c / NSIM for v, c in counts.items()}, "mean_rho": float(np.mean(rhos)), "sd_rho": float(np.std(rhos))}
name = f"v4_null_verdict_sim_{mode}_{p}" + (f"_n{N}" if N else "")
json.dump(out, open(f"{H}/results/exploratory/{name}.json", "w"), indent=1)
print(json.dumps(out, indent=1))
