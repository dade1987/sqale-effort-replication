"""[Version 2, 27 Nov 2026: decision order and +1/B aligned with the registered script after a statistical review; version 1 kept as independent_v4.py.]
Independent re-implementation of the fourth preregistration (H1-2W and registered secondary analyses).
Written from the text of protocol_confirmatory_v4_moodle_twoway.md only, without reusing confermativo_v4.py.
Differences by design: own weighted-rank implementation (replicate = data expanded by draw counts), numpy RNG
with a different seed, and several seeds / a larger number of replicates to measure Monte Carlo error.
Usage: python3 independent_v4.py <package_root> <scan.jsonl> <out.json> [B] [seed ...]
"""
import sys, json, gzip, collections, numpy as np, pandas as pd

R, SCAN, OUT = sys.argv[1:4]
B = int(sys.argv[4]) if len(sys.argv) > 4 else 5000
SEEDS = [int(s) for s in sys.argv[5:]] or [11, 22, 33]
CODE_EXT = (".php", ".js")

keys = open(f"{R}/preregistration_v4/newsample_keys_moodle.txt").read().split()
K = set(keys)
feat = pd.read_csv(f"{R}/data/features/moodle_features.csv")
hist = pd.read_csv(f"{R}/data/history/moodle_history.csv")
d = feat[feat.key.isin(K)].merge(hist[["key", "assignee_T", "hours_assignee"]], on="key", how="left")
links = {}
for line in gzip.open(f"{R}/data/links/moodle_links.jsonl.gz", "rt"):
    x = json.loads(line)
    if x["key"] in K: links[x["key"]] = x["files"]
scan = {}
for line in open(SCAN):
    x = json.loads(line); scan[x["key"]] = x

# developer: assignee at first fix commit, else author of c1; component: first Jira component, none -> one group
d["dev"] = d.assignee_T.where(d.assignee_T.notna() & (d.assignee_T.astype(str) != ""), "git:" + d.fix_author.astype(str))
d["comp"] = d.components.apply(lambda c: str(c).split(";")[0] if isinstance(c, str) and c else "<none>")
def module(files):
    c = collections.Counter()
    for f in files:
        if f.lower().endswith(CODE_EXT):
            parts = f.split("/")
            c["/".join(parts[:2]) if len(parts) > 2 else parts[0]] += 1
    if not c: return "<none>"
    top = max(c.values()); return sorted(k for k, v in c.items() if v == top)[0]
d["module"] = d.key.map(lambda k: module(links.get(k, [])))
d["nfiles"] = d.key.map(lambda k: len(links.get(k, [])))

counts = {"keys": len(keys), "hours_gt_0": int((d.hours > 0).sum())}
d = d[d.hours > 0]
counts["excluded_over_2000_files"] = int((d.nfiles > 2000).sum())
d = d[d.nfiles <= 2000]
for c in ["sqale_min", "ncloc", "code_files_at_parent", "sqale_righe_modificate", "righe_vecchie_modificate", "ncloc_c1_prima"]:
    d[c] = d.key.map(lambda k: scan.get(k, {}).get(c))
d["err"] = d.key.map(lambda k: "error" in scan.get(k, {"error": 1}))
counts["touch_code_at_parent_or_failed"] = int(((d.code_files_at_parent.fillna(0) > 0) | d.err).sum())
a = d[(~d.err) & (d.ncloc.fillna(0) > 0) & d.sqale_min.notna()].reset_index(drop=True)
counts["analysed"] = len(a)

def wrank(x, w):
    """mid-ranks of x in the data set where row i appears w[i] times (w=0 rows get NaN)."""
    o = np.argsort(x, kind="mergesort"); xs, ws = x[o], w[o]
    r = np.empty(len(x)); i = 0; cum = 0.0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[j + 1] == xs[i]: j += 1
        W = ws[i:j + 1].sum(); r[o[i:j + 1]] = cum + (W + 1) / 2; cum += W; i = j + 1
    return r
def pcor(y, x, Z, w=None):
    """partial Spearman: Pearson corr of residuals of ranks(y), ranks(x) on ranks(Z), all weighted by w."""
    w = np.ones(len(y)) if w is None else w
    m = w > 0; y, x, Z, w = y[m], x[m], Z[m], w[m]
    ry, rx = wrank(y, w), wrank(x, w)
    RZ = np.column_stack([np.ones(len(y))] + [wrank(z, w) for z in Z.T])
    sw = np.sqrt(w)
    def res(v): b = np.linalg.lstsq(RZ * sw[:, None], v * sw, rcond=None)[0]; return v - RZ @ b
    ey, ex = res(ry), res(rx)
    ey -= np.average(ey, weights=w); ex -= np.average(ex, weights=w)
    return float(np.sum(w * ey * ex) / np.sqrt(np.sum(w * ey ** 2) * np.sum(w * ex ** 2)))

def boot(df, ycol, xcol, zcols, g1, g2, seed, B=B):
    y, x, Z = df[ycol].values.astype(float), df[xcol].values.astype(float), df[zcols].values.astype(float)
    est = pcor(y, x, Z)
    rng = np.random.default_rng(seed)
    c1 = pd.factorize(df[g1])[0]; n1 = c1.max() + 1
    if g2: c2 = pd.factorize(df[g2])[0]; n2 = c2.max() + 1
    reps = np.empty(B)
    for b in range(B):
        w = np.bincount(rng.integers(0, n1, n1), minlength=n1)[c1].astype(float)
        if g2: w = w * np.bincount(rng.integers(0, n2, n2), minlength=n2)[c2]
        reps[b] = pcor(y, x, Z, w)
    lo, hi = np.percentile(reps, [5, 95])
    # corrected (27 Nov 2026): same order as the registered rule (equivalence checked before "positive")
    verdict = ("supported" if lo > 0.10 else "practically negligible" if (lo > -0.10 and hi < 0.10) else
               "positive, uncertain size" if lo > 0 else "inconclusive")
    return {"n": len(df), "estimate": est, "CI90": [float(lo), float(hi)], "verdict": verdict,
            "p_one_sided_rho_gt_0": float(min(1, np.mean(reps <= 0) + 1 / B)),   # corrected: +1/B as in the registered script
            "p_tost": float(max(min(1, np.mean(reps <= -0.10) + 1 / B), min(1, np.mean(reps >= 0.10) + 1 / B))), "seed": seed, "B": B}

out = {"counts": counts, "n_dev": int(a.dev.nunique()), "n_comp": int(a.comp.nunique()), "n_module": int(a.module.nunique())}
out["H1-2W"] = [boot(a, "hours", "sqale_min", ["ncloc"], "dev", "comp", s) for s in SEEDS]
out["positive_control"] = boot(a, "hours", "h_commits_1y", ["ncloc"], "dev", "comp", SEEDS[0])
out["H1_dev_x_module"] = boot(a, "hours", "sqale_min", ["ncloc"], "dev", "module", SEEDS[0])
out["H1_dev_only"] = boot(a, "hours", "sqale_min", ["ncloc"], "dev", None, SEEDS[0])
aa = a[a.hours_assignee.fillna(0) > 0]
out["H1_assignee_hours"] = boot(aa, "hours_assignee", "sqale_min", ["ncloc"], "dev", "comp", SEEDS[0])
a23 = a[pd.to_datetime(a.resolved, errors="coerce") >= "2023-01-01"]
out["H1_from_2023"] = boot(a23, "hours", "sqale_min", ["ncloc"], "dev", "comp", SEEDS[0])
h2 = a[(a.righe_vecchie_modificate.fillna(0) > 0) & a.sqale_righe_modificate.notna() & a.ncloc_c1_prima.notna()]
out["H2_2W"] = boot(h2, "hours", "sqale_righe_modificate", ["righe_vecchie_modificate", "ncloc_c1_prima"], "dev", "comp", SEEDS[0])
json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(out, indent=1))
