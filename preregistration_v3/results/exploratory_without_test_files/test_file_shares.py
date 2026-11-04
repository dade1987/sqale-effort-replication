# Exploratory: share of measured lines (NCLOC) and of SQALE debt that comes from test-like files, per project
# (protocol-conforming MOSIP sample). Run from preregistration_v3/results/.
import json, pandas as pd
strict = {json.loads(l)["key"] for l in open("sensitivity_strict_rerun_rule/scan_mosip_without_lots48_56.jsonl")}
for p in ["mosip", "openlmis", "openmrs"]:
    f = pd.read_csv("../data/features_v3_%s.csv" % p)
    a = {json.loads(l)["key"]: json.loads(l) for l in open("../scan/scan_%s.jsonl" % p)}
    b = {json.loads(l)["key"]: json.loads(l) for l in open("exploratory_without_test_files/scan_%s_no_tests.jsonl" % p)}
    ks = [k for k in f.key if k in a and a[k]["files_measured"] > 0 and a[k]["ncloc"] > 0 and (p != "mosip" or k in strict)]
    nc = sum(a[k]["ncloc"] for k in ks); ncp = sum(b[k]["ncloc"] for k in ks); sq = sum(a[k]["sqale_min"] for k in ks); sqp = sum(b[k]["sqale_min"] for k in ks)
    print(p, len(ks), "test share of NCLOC %.0f%%, of debt %.0f%%; debt per kNCLOC production %.1f, tests %.1f min" % (100 * (nc - ncp) / nc, 100 * (sq - sqp) / sq, 1000 * sqp / ncp, 1000 * (sq - sqp) / (nc - ncp)))
