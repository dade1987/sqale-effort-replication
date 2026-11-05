# Exploratory (5 Nov 2026): split the 1,344 analysed OpenLMIS issues into those that touch only test-like files
# (no production NCLOC once test paths are removed) and those that touch production code; then run the frozen
# script on each part with the REGISTERED measure (test files counted). Run from preregistration_v3/.
import json, subprocess, pandas as pd
R = "results/exploratory_without_test_files"
nt = {json.loads(l)["key"]: json.loads(l) for l in open(R + "/scan_openlmis_no_tests.jsonl")}
f = pd.read_csv("data/features_v3_openlmis.csv"); keys = set(f.key)
an = [json.loads(l) for l in open("scan/scan_openlmis.jsonl")]
an = [d for d in an if d["files_measured"] > 0 and d["ncloc"] > 0 and d["key"] in keys]
parts = {"test_only": [d for d in an if nt.get(d["key"], {}).get("ncloc", 0) == 0],
         "with_production": [d for d in an if nt.get(d["key"], {}).get("ncloc", 0) > 0]}
for name, s in parts.items():
    p = f"{R}/openlmis_399/scan_registered_{name}.jsonl"
    open(p, "w").writelines(json.dumps(d) + "\n" for d in s)
    subprocess.run(["python3", "code/confermativo_v3.py", f"{R}/openlmis_399/res_{name}.json", f"openlmis:data/features_v3_openlmis.csv:{p}"], check=True)
    print(name, len(s), "zero-debt share", round(sum(d["sqale_min"] == 0 for d in s) / len(s), 2))
