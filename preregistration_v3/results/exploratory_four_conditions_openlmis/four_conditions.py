# Exploratory (not preregistered), checklist v7 point 1: OpenLMIS, the same issues under four measurement conditions
#   A no bytecode, test files included  (= registered preregistered measure)
#   B no bytecode, test files excluded
#   C bytecode,    test files included
#   D bytecode,    test files excluded
# Family 1 ("registered-based"): A = registered scan; B = registered scan recomputed without test files (5 Nov);
#   C = A - Java(no bytecode) + Java(bytecode); D = B - non-test Java(no bytecode) + non-test Java(bytecode).
# Family 2 ("Java-only, same scan"): the four cells from the per-file rerun of 7 Nov only (touched Java files, one project per issue).
# Issues kept only if valid (files_measured > 0 and NCLOC > 0) in all four cells of the family -> identical issue set per family.
# Frozen script confermativo_v3.py (developer and developer x module bootstrap, B=5000, seed 2026, H3 split by resolution date).
# Usage: python3 four_conditions.py <perfile.jsonl> <outdir>
import json, os, re, sys, subprocess, pandas as pd
pf, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
B = "/mnt/project-files/ricerca2/preregistrazione_nuovi_progetti"; CONF = B + "/code/confermativo_v3.py"
TEST = re.compile(r"(^|/)(test|tests|__tests__|spec|e2e|it)/|[._-](spec|test|tests)\.[a-z]+$|Tests?\.java$|IT\.java$", re.I)  # same rule as 5 Nov
reg = {json.loads(l)["key"]: json.loads(l) for l in open(f"{B}/risultati/scan_openlmis.jsonl")}
nt = {json.loads(l)["key"]: json.loads(l) for l in open(f"{B}/risultati/exploratory_without_test_files/scan_openlmis_no_tests.jsonl")}
pr = [json.loads(l) for l in open(pf)]; pr = [r for r in pr if r.get("bin") and "files" in r["bin"] and "files" in r["nobin"]]
def agg(files, keep):
    fs = [f for f in files if keep(f["path"])]; return sum(f["sqale_min"] for f in fs), sum(f["ncloc"] for f in fs), len(fs)
ALL, NOTEST = (lambda p: True), (lambda p: not TEST.search(p))
fam = {"registered_based": {c: [] for c in "ABCD"}, "java_only": {c: [] for c in "ABCD"}}; info = []
for r in pr:
    k = r["key"]; a, b = reg[k], nt[k]
    jn_all, jb_all, jn_nt, jb_nt = agg(r["nobin"]["files"], ALL), agg(r["bin"]["files"], ALL), agg(r["nobin"]["files"], NOTEST), agg(r["bin"]["files"], NOTEST)
    mk = lambda base, s, n, f: dict(base, sqale_min=s, ncloc=n, files_measured=f)
    cells = {"A": dict(a), "B": dict(b),
             "C": mk(a, a["sqale_min"] - jn_all[0] + jb_all[0], a["ncloc"], a["files_measured"]),
             "D": mk(b, b["sqale_min"] - jn_nt[0] + jb_nt[0], b["ncloc"], b["files_measured"])}
    cj = {"A": mk(a, *jn_all), "B": mk(a, *jn_nt), "C": mk(a, *jb_all), "D": mk(a, *jb_nt)}
    for fname, cs in (("registered_based", cells), ("java_only", cj)):
        if all(c["files_measured"] > 0 and c["ncloc"] > 0 for c in cs.values()):
            for c in "ABCD": fam[fname][c].append(cs[c])
    info.append({"key": k, "java_test_files": r["nobin"]["files_measured"] - jn_nt[2], "sqale": {"A": cells["A"]["sqale_min"], "B": cells["B"]["sqale_min"], "C": cells["C"]["sqale_min"], "D": cells["D"]["sqale_min"]}})
f = pd.read_csv("/home/user/np/v3/features_v3_openlmis.csv")
summary = {"issues_with_per_file_data": len(pr)}
for fname, cs in fam.items():
    keys = [c["key"] for c in cs["A"]]; assert all([c["key"] for c in cs[x]] == keys for x in "BCD")
    f[f.key.isin(keys)].to_csv(f"{out}/features_{fname}.csv", index=False)
    summary[fname] = {"n_same_issues": len(keys)}
    for c in "ABCD":
        sf = f"{out}/scan_{fname}_{c}.jsonl"; open(sf, "w").write("".join(json.dumps(x) + "\n" for x in cs[c]))
        rf = f"{out}/results_{fname}_{c}.json"
        subprocess.run(["python3", CONF, rf, f"openlmis:{out}/features_{fname}.csv:{sf}"], check=True, capture_output=True)
        R = json.load(open(rf))["openlmis"]
        summary[fname][c] = {"n": R["H1"]["n"], "sum_sqale_min": sum(x["sqale_min"] for x in cs[c]), "sum_ncloc": sum(x["ncloc"] for x in cs[c]),
            "median_sqale_min": float(pd.Series([x["sqale_min"] for x in cs[c]]).median()), "median_ncloc": float(pd.Series([x["ncloc"] for x in cs[c]]).median()),
            "spearman_sqale_ncloc": float(pd.DataFrame(cs[c])[["sqale_min", "ncloc"]].corr("spearman").iloc[0, 1]),
            "H1_rho": round(R["H1"]["partial_rho"], 3), "H1_CI90_dev": [round(x, 3) for x in R["H1"]["CI90"]], "H1_verdict_dev": R["H1"]["verdict"],
            "H1_CI90_dev_module": [round(x, 3) for x in R["H1_twoway_dev_module"]["CI90"]], "H1_verdict_dev_module": R["H1_twoway_dev_module"]["verdict"],
            "H3_dMAE_h": round(R["H3"]["dMAE"], 3), "H3_CI90_pct_MAE": [round(x, 2) for x in R["H3"]["CI90_pct_MAE"]], "H3_verdict": R["H3"]["verdict"]}
    s = summary[fname]
    s["effects_on_H1_rho"] = {"bytecode_with_tests (C-A)": round(s["C"]["H1_rho"] - s["A"]["H1_rho"], 3), "bytecode_without_tests (D-B)": round(s["D"]["H1_rho"] - s["B"]["H1_rho"], 3),
                              "tests_out_without_bytecode (B-A)": round(s["B"]["H1_rho"] - s["A"]["H1_rho"], 3), "tests_out_with_bytecode (D-C)": round(s["D"]["H1_rho"] - s["C"]["H1_rho"], 3),
                              "interaction (D-C)-(B-A)": round(s["D"]["H1_rho"] - s["C"]["H1_rho"] - s["B"]["H1_rho"] + s["A"]["H1_rho"], 3)}
open(f"{out}/per_issue.jsonl", "w").write("".join(json.dumps(x) + "\n" for x in info))
json.dump(summary, open(f"{out}/summary_four_conditions.json", "w"), indent=1); print(json.dumps(summary, indent=1))
