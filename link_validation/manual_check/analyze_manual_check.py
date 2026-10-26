"""Blind manual check of issue-commit links (Section 3.2 of the paper).
Precision: share of issues whose linked commits were judged correct (partial counted both ways), with Wilson 95% CIs.
Completeness: share of issues with no missing fix commit. Agreement with the second human rater on 30 of the 100 issues.
Usage (from this folder): python3 analyze_manual_check.py   -> results_manual_check.json"""
import csv, json, math, os, statistics
from collections import Counter
D = os.path.dirname(os.path.abspath(__file__))
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [(c - h) / d, (c + h) / d]
read = lambda f: {r["key"]: r for r in csv.DictReader(open(os.path.join(D, f)))}
A = read("answers_author.csv"); B = read("second_rater/answers_second_rater.csv")
res = {"n_sample": len(A)}
for name, keys in [("all", list(A))] + [(p, [k for k in A if A[k]["project"] == p]) for p in ["moodle", "mariadb", "percona"]]:
    n = len(keys); g = Counter(A[k]["judgement"] for k in keys); m = Counter(A[k]["missing_commit"] for k in keys)
    strict, loose = g["correct"], g["correct"] + g["partial"]
    res[name] = {"n": n, "judgement": dict(g), "missing_commit": dict(m),
                 "precision_strict": strict / n, "precision_strict_CI95": wilson(strict, n),
                 "precision_incl_partial": loose / n, "precision_incl_partial_CI95": wilson(loose, n),
                 "no_missing_commit": m["no"] / n, "no_missing_commit_CI95": wilson(m["no"], n),
                 "missing_commits_reported": {k: A[k]["missing_commit_hashes"] for k in keys if A[k]["missing_commit"] == "yes"},
                 "median_seconds_per_issue": statistics.median(int(A[k]["seconds"]) for k in keys)}
def agree(field, cats):
    keys = sorted(B); a = [A[k][field] for k in keys]; b = [B[k][field] for k in keys]; n = len(keys)
    po = sum(x == y for x, y in zip(a, b)) / n; pa, pb = Counter(a), Counter(b)
    pe_k = sum(pa[c] / n * pb[c] / n for c in cats); pi = {c: (pa[c] + pb[c]) / (2 * n) for c in cats}
    pe_g = sum(p * (1 - p) for p in pi.values()) / (len(cats) - 1)
    return {"n": n, "percent_agreement": po, "cohen_kappa": (po - pe_k) / (1 - pe_k) if pe_k < 1 else None, "gwet_ac1": (po - pe_g) / (1 - pe_g),
            "author": dict(pa), "second_rater": dict(pb), "disagreements": [k for k, x, y in zip(keys, a, b) if x != y]}
res["second_rater"] = {"judgement": agree("judgement", ["correct", "partial", "wrong"]), "missing_commit": agree("missing_commit", ["no", "yes", "dont_know"]),
                       "median_seconds_second_rater": statistics.median(int(B[k]["seconds"]) for k in B),
                       "median_seconds_author_same_30": statistics.median(int(A[k]["seconds"]) for k in B)}
json.dump(res, open(os.path.join(D, "results_manual_check.json"), "w"), indent=1)
print(json.dumps({k: res["all"][k] for k in ["precision_strict", "no_missing_commit", "median_seconds_per_issue"]}), json.dumps(res["second_rater"]["judgement"]["gwet_ac1"]))
