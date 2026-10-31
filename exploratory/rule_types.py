# SQALE by rule type, size-neutral variant, debt ratio and A-E rating (exploratory, not preregistered; plan in the README).
# The frozen H1 pipeline (preregistration/confermativo.py) applied to per-rule debt of the same hold-out issues (data/rules/, re-scan whose
# per-rule efforts sum exactly to the H1 sqale_min). Usage: python3 rule_types.py <project>   -> results/exploratory/rule_types_<project>.json
import sys, json, re, os, numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)) + "/.."
p = sys.argv[1]
src = open(f"{H}/preregistration/confermativo.py").read()
exec(src[src.index("B, SEED"):src.index("\nst = ")])                     # constants
exec(src[src.index("def rank_resid"):src.index("out = {")])             # rank_resid, partial, boot_groups, verdict_rho, test_rho (frozen code)
meta = json.load(open(f"{H}/data/rules/rule_meta.json"))
SIZE_TAGS = {"duplicate", "redundant", "unused", "unnecessary"}
SIZE_NAME = re.compile(r"lines of code|code lines|too many (methods|functions|fields)|duplicat|identical|unused|never used|commented.out|dead code", re.I)
CONV_NAME = re.compile(r"document|header|todo|fixme|tab", re.I)
def group(r):
    m = meta[r]; tags = set(m["tags"]); name = m["name"] or ""
    if tags & SIZE_TAGS or SIZE_NAME.search(name): return "size_adding"
    if "brain-overload" in tags: return "complexity"
    if tags & {"convention", "bad-practice"} or CONV_NAME.search(name): return "convention"
    return "other"
G = ["size_adding", "complexity", "convention", "other"]
st = pd.read_csv(f"{H}/data/history/{p}_history.csv")[["key", "assignee_T"]]
df = pd.read_csv(f"{H}/data/features/{p}_features.csv").merge(st, on="key", how="left")
df["dev"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace({"git:": "?", "": "?"})
df = df[df.hours > 0]
ho = pd.read_json(f"{H}/data/confirmatory/holdout_scan_{p}.jsonl", lines=True).drop_duplicates("key").merge(df[["key", "hours", "dev"]], on="key")
a1 = ho[(ho.code_files_at_parent > 0) & (ho.ncloc > 0)].copy()
rows = []
for r in map(json.loads, open(f"{H}/data/rules/rules_{p}.jsonl")):
    d = {"key": r["key"], "sqale_rules": r["sqale_min"], "rule_sum": sum(r["effort_by_rule"].values())}
    for g in G: d[g] = sum(v for k, v in r["effort_by_rule"].items() if group(k) == g)
    rows.append(d)
a = a1.merge(pd.DataFrame(rows), on="key", how="left").reset_index(drop=True)
assert a.sqale_rules.notna().all() and (a.sqale_rules == a.sqale_min).all() and (a.rule_sum == a.sqale_min).all()
a["size_neutral"] = a.sqale_min - a.size_adding
a["debt_ratio"] = a.sqale_min / (30 * a.ncloc)
a["rating"] = np.select([a.debt_ratio <= .05, a.debt_ratio <= .10, a.debt_ratio <= .20, a.debt_ratio <= .50], [1, 2, 3, 4], 5)
used = sorted({k for r in map(json.loads, open(f"{H}/data/rules/rules_{p}.jsonl")) for k in r["effort_by_rule"]})
out = {"project": p, "n": int(len(a)),
       "rules_per_group": {g: [k for k in used if group(k) == g] for g in G},
       "effort_share": {g: float(a[g].sum() / a.sqale_min.sum()) for g in G},
       "issues_with_nonzero": {g: int((a[g] > 0).sum()) for g in G},
       "spearman_with_ncloc": {x: float(a[[x, "ncloc"]].corr("spearman").iloc[0, 1]) for x in G + ["size_neutral", "debt_ratio", "rating"]},
       "rating_counts": {"ABCDE"[i - 1]: int((a.rating == i).sum()) for i in range(1, 6)},
       "median_hours_by_rating": {"ABCDE"[i - 1]: float(a.hours[a.rating == i].median()) if (a.rating == i).any() else None for i in range(1, 6)}}
rng = np.random.default_rng(SEED)
tests = {"total_H1": test_rho(a, "sqale_min", ["ncloc"])}
for x in G + ["size_neutral", "debt_ratio", "rating"]: tests[x] = test_rho(a, x, ["ncloc"])
ps = sorted((v["p_unilaterale_rho_gt_0"], k) for k, v in tests.items() if k != "total_H1"); m = len(ps); run = 0
for i, (pv, k) in enumerate(ps):
    run = max(run, min(1.0, (m - i) * pv)); tests[k]["p_holm"] = run
out["tests"] = tests
json.dump(out, open(f"{H}/results/exploratory/rule_types_{p}.json", "w"), indent=1, default=float)
print(json.dumps({k: v for k, v in out.items() if k != "rules_per_group"}, indent=1, default=float))
