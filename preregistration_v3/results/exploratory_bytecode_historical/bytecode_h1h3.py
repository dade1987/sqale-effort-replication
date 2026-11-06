# Exploratory (not preregistered): H1/H3 of the third test on the issues whose historical snapshot compiled,
# with the registered measure and with Java measured with bytecode (same files, same issues).
# Usage: python3 bytecode_h1h3.py <outdir>
import json, os, sys, subprocess, pandas as pd
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
B = "/mnt/project-files/ricerca2/preregistrazione_nuovi_progetti"
CONF = B + "/code/confermativo_v3.py"
summary = {}
specs = {v: [] for v in ("registered", "with_bytecode", "java_only_without", "java_only_with")}
for p in ("openmrs", "openlmis"):
    recs = {json.loads(l)["key"]: json.loads(l) for l in open(f"/home/user/hb/full_{p}.jsonl")}
    reg = {json.loads(l)["key"]: json.loads(l) for l in open(f"{B}/risultati/scan_{p}.jsonl")}
    f = pd.read_csv(f"/home/user/np/v3/features_v3_{p}.csv")
    ok = [k for k, r in recs.items() if r.get("bin") and "error" not in r["bin"] and "error" not in r["nobin"]]
    summary[p] = {"attempted": len(recs), "compiled_and_measured": len(ok),
                  "sqale_sum_nobin_java": sum(recs[k]["nobin"]["sqale_min"] for k in ok), "sqale_sum_bin_java": sum(recs[k]["bin"]["sqale_min"] for k in ok),
                  "issues_all_code_java": sum(1 for k in ok if reg[k]["code_files_at_parent"] == recs[k]["java_files_at_parent"]), "of_which_nobin_equals_registered": sum(1 for k in ok if reg[k]["code_files_at_parent"] == recs[k]["java_files_at_parent"] and abs(recs[k]["nobin"]["sqale_min"] - reg[k]["sqale_min"]) < 1e-9), "issues_in_registered_analysis": int(f[f.key.isin([k for k in reg if reg[k].get("files_measured", 0) > 0 and reg[k].get("ncloc", 0) > 0])].shape[0]), "attempted_build_ok": sum(1 for r in recs.values() if r["build_ok"])}
    f[f.key.isin(ok)].to_csv(f"{out}/features_{p}.csv", index=False)
    rows = {v: [] for v in specs}
    for k in ok:
        r0 = dict(reg[k]); n, b = recs[k]["nobin"], recs[k]["bin"]
        rows["registered"].append(r0)
        r1 = dict(r0); r1["sqale_min"] = r0["sqale_min"] - n["sqale_min"] + b["sqale_min"]; rows["with_bytecode"].append(r1)
        for v, m in (("java_only_without", n), ("java_only_with", b)):
            r2 = dict(r0); r2.update(sqale_min=m["sqale_min"], ncloc=m["ncloc"], files_measured=m["files_measured"]); rows[v].append(r2)
    for v in specs:
        with open(f"{out}/scan_{v}_{p}.jsonl", "w") as fh:
            for r in rows[v]: fh.write(json.dumps(r) + "\n")
        specs[v].append(f"{p}:{out}/features_{p}.csv:{out}/scan_{v}_{p}.jsonl")
for v, sp in specs.items():
    subprocess.run(["python3", CONF, f"{out}/results_{v}.json"] + sp, check=True, capture_output=True)
    R = json.load(open(f"{out}/results_{v}.json"))
    summary[v] = {p: {"n": R[p]["H1"]["n"], "H1": [round(R[p]["H1"]["partial_rho"], 3)] + [round(x, 3) for x in R[p]["H1"]["CI90"]],
                      "H1_twoway": [round(x, 3) for x in R[p]["H1_twoway_dev_module"]["CI90"]], "H1_verdict": R[p]["H1"]["verdict"],
                      "H3_pct": [round(x, 2) for x in R[p]["H3"]["CI90_pct_MAE"]], "H3_verdict": R[p]["H3"]["verdict"]} for p in ("openmrs", "openlmis")}
json.dump(summary, open(f"{out}/summary.json", "w"), indent=1); print(json.dumps(summary, indent=1))
