import sys, json, numpy as np
from common_v4 import load, REG, ISO
which = sys.argv[1]; g = load(REG if which == "registered" else ISO); a = g["a"]
B, BL, SEED, S = 100000, 5000, 20261127, 0.10
g["B"] = B; rng = np.random.default_rng(SEED)
bs = np.array([g["partial"](a.iloc[i], "sqale") for i in g["boot_twoway"](a, rng)])
nan = int((~np.isfinite(bs)).sum())
lo, hi = np.nanpercentile(bs, [5, 95])
p_lo = min(1, np.mean(bs <= -S) + 1 / B); p_hi = min(1, np.mean(bs >= S) + 1 / B)
blocks = bs.reshape(20, BL)
blo = np.nanpercentile(blocks, 5, axis=1); bp = np.array([max(np.mean(b <= -S), np.mean(b >= S)) for b in blocks])
# order-statistic 95% CI for the 5th percentile
srt = np.sort(bs[np.isfinite(bs)]); n = len(srt); k = 0.05 * n; sd = np.sqrt(n * 0.05 * 0.95)
os_ci = [float(srt[int(np.floor(k - 1.96 * sd))]), float(srt[int(np.ceil(k + 1.96 * sd))])]
out = {"scan": which, "n": len(a), "B": B, "seed": SEED, "nan_replicates": nan, "estimate": g["partial"](a, "sqale"),
       "CI90": [float(lo), float(hi)], "p_tost": float(max(p_lo, p_hi)), "p_tost_lower": float(p_lo), "p_tost_upper": float(p_hi),
       "verdict": g["verdict"](lo, hi),
       "mc_se_lower_bound_batch": float(blo.std(ddof=1) / np.sqrt(20)), "lower_bound_blocks_range": [float(blo.min()), float(blo.max())],
       "mc_se_p_tost_batch": float(bp.std(ddof=1) / np.sqrt(20)), "lower_bound_order_stat_95ci": os_ci,
       "blocks_negligible": int(sum(1 for b in blocks if np.nanpercentile(b, 5) > -S and np.nanpercentile(b, 95) < S))}
json.dump(out, open(f"/home/user/stat27/p4_{which}.json", "w"), indent=1); print(json.dumps(out, indent=1))
