# Exploratory (5 Nov 2026): MOSIP (protocol-conforming sample) without every link judged wrong OR partly correct
# among the 100 MOSIP links checked by the rater (30 registered + 70 extra). Run from preregistration_v3/.
import csv, json, subprocess
v = {r["issue"]: r["commits_concern_issue"] for r in csv.DictReader(open("link_check/human_rater_verdicts.csv")) if r["project"] == "mosip"}
v.update({r["issue"]: r["commits_concern_issue"] for r in csv.DictReader(open("link_check/mosip_extra70/human_rater_verdicts_mosip70.csv"))})
bad = {k for k, x in v.items() if x != "correct"}
D = "results/exploratory_wrong_links/real100_no_partial"
L = open("results/sensitivity_strict_rerun_rule/scan_mosip_without_lots48_56.jsonl").readlines()
open(D + "/scan.jsonl", "w").writelines(l for l in L if json.loads(l)["key"] not in bad)
subprocess.run(["python3", "code/confermativo_v3.py", D + "/results.json", f"mosip:data/features_v3_mosip.csv:{D}/scan.jsonl"], check=True)
