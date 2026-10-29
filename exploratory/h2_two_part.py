# H2 split in two parts (not preregistered): does the first fix commit touch any debt at all on the changed lines,
# and, where it does, does the amount of debt go with the hours? Same sample, covariates, bootstrap and verdicts as H2.
# Usage: python3 h2_two_part.py <project>
import sys, json, numpy as np, pandas as pd, os
H = os.path.dirname(os.path.abspath(__file__)) + "/.."
p = sys.argv[1]
src = open(f"{H}/preregistration/confermativo.py").read()
exec(src[src.index("B, SEED"):src.index("\nst = ")]); exec(src[src.index("def rank_resid"):src.index("out = {")])
st = pd.read_csv(f"{H}/data/history/{p}_history.csv")[["key", "assignee_T"]]
df = pd.read_csv(f"{H}/data/features/{p}_features.csv").merge(st, on="key", how="left")
df["dev"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace({"git:": "?", "": "?"})
df = df[df.hours > 0]
ho = pd.read_json(f"{H}/data/confirmatory/holdout_scan_{p}.jsonl", lines=True).drop_duplicates("key").merge(df[["key", "hours", "dev"]], on="key")
a2 = ho[(ho.c1_files_at_parent > 0) & (ho.righe_vecchie_modificate > 0) & (ho.ncloc_c1_prima > 0)].copy()
rng = np.random.default_rng(SEED)
COV = ["righe_vecchie_modificate", "ncloc_c1_prima"]
a2["any_debt"] = (a2.sqale_righe_modificate > 0).astype(float)
pos = a2[a2.sqale_righe_modificate > 0].copy()
out = {"project": p, "n": int(len(a2)), "share_zero_debt_on_changed_lines": float((a2.sqale_righe_modificate == 0).mean()),
       "median_hours_zero": float(a2[a2.any_debt == 0].hours.median()), "median_hours_positive": float(pos.hours.median()),
       "median_changed_lines_zero": float(a2[a2.any_debt == 0].righe_vecchie_modificate.median()), "median_changed_lines_positive": float(pos.righe_vecchie_modificate.median()),
       "H2_frozen": test_rho(a2, "sqale_righe_modificate", COV),
       "part1_any_debt": test_rho(a2, "any_debt", COV),
       "part2_amount_if_positive": test_rho(pos, "sqale_righe_modificate", COV)}
json.dump(out, open(f"{H}/results/exploratory/h2_two_part_{p}.json", "w"), indent=1)
for k, v in out.items():
    print(k, [round(v["rho_parziale"], 3), [round(c, 3) for c in v["IC90"]], v["n"], v["esito"]] if isinstance(v, dict) else v)
