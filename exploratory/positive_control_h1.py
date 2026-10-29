# Positive control for H1 (not preregistered): the frozen H1 pipeline (preregistration/confermativo.py) applied to change-history
# measures of the touched files instead of SQALE, on the same hold-out issues, plus a simulation of the smallest effect H1 can detect.
# Usage: python3 positive_control_h1.py <project> [n_sim]
import sys, json, numpy as np, pandas as pd, os
H = os.path.dirname(os.path.abspath(__file__)) + "/.."
p = sys.argv[1]; NSIM = int(sys.argv[2]) if len(sys.argv) > 2 else 200
src = open(f"{H}/preregistration/confermativo.py").read()
exec(src[src.index("B, SEED"):src.index("\nst = ")])                     # constants
exec(src[src.index("def rank_resid"):src.index("out = {")])             # rank_resid, partial, boot_groups, verdict_rho, test_rho (frozen code)
st = pd.read_csv(f"{H}/data/history/{p}_history.csv")[["key", "assignee_T"]]
df = pd.read_csv(f"{H}/data/features/{p}_features.csv").merge(st, on="key", how="left")
df["dev"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace({"git:": "?", "": "?"})
df = df[df.hours > 0]
ho = pd.read_json(f"{H}/data/confirmatory/holdout_scan_{p}.jsonl", lines=True).drop_duplicates("key").merge(
    df[["key", "hours", "dev", "fix_date", "h_commits_1y", "h_churn_1y", "h_commits_sum", "st_ccn_sum"]], on="key")
a1 = ho[(ho.code_files_at_parent > 0) & (ho.ncloc > 0)].copy()
out = {"project": p, "n": int(len(a1)), "note": "Same sample, covariate, bootstrap (B=5000, seed 2026, developer clusters) and verdict rules as H1; only the measure differs. History measures are over all files touched by the fix (features.py)."}
rng = np.random.default_rng(SEED)
for x in ["sqale_min", "h_commits_1y", "h_churn_1y", "h_commits_sum", "st_ccn_sum"]:
    out[x] = test_rho(a1, x, ["ncloc"])
# Power simulation: inject a known effect of SQALE beyond size into the real hours and rerun the H1 test.
# hours* = hours * exp(beta * z), z = standardised residual of log1p(SQALE) on log1p(ncloc); each run resamples developers.
z0 = np.log1p(a1.sqale_min.values); l = np.log1p(a1.ncloc.values)
Xl = np.column_stack([np.ones(len(l)), l]); zr = z0 - Xl @ np.linalg.lstsq(Xl, z0, rcond=None)[0]; a1["z"] = zr / zr.std()
B = 1000
sim = {}
for beta in [0.0, 0.05, 0.08, 0.1, 0.12, 0.15, 0.2]:
    rhos, gt0, gt_sesoi = [], 0, 0
    for s in range(NSIM):
        g = pd.factorize(a1.dev)[0]; idx = [np.where(g == i)[0] for i in range(g.max() + 1)]
        pick = rng.integers(0, len(idx), len(idx)); b = a1.iloc[np.concatenate([idx[i] for i in pick])].copy().reset_index(drop=True)
        b["hours"] = b.hours * np.exp(beta * b.z)
        r = test_rho(b, "sqale_min", ["ncloc"])
        rhos.append(r["rho_parziale"]); gt0 += r["IC90"][0] > 0; gt_sesoi += r["IC90"][0] > SESOI_RHO
    sim[str(beta)] = {"mean_partial_rho": float(np.mean(rhos)), "power_lower90_above_0": gt0 / NSIM, "power_lower90_above_SESOI": gt_sesoi / NSIM,
                      "hours_ratio_per_sd": float(np.exp(beta))}
out["power_simulation"] = {"n_sim": NSIM, "B_per_test": B, "by_beta": sim}
os.makedirs(f"{H}/results/exploratory", exist_ok=True)
json.dump(out, open(f"{H}/results/exploratory/positive_control_h1_{p}.json", "w"), indent=1)
print(json.dumps({k: (v if not isinstance(v, dict) or "rho_parziale" not in v else [round(v["rho_parziale"], 3), [round(c, 3) for c in v["IC90"]], v["esito"]]) for k, v in out.items()}, indent=1))
