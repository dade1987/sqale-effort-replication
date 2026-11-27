import json, glob
V3 = "/home/user/sqale-effort-replication/preregistration_v3/scan/"
for p in ("mosip", "openlmis", "openmrs"):
    iso = {}
    for f in glob.glob(f"/home/user/audit/v3/{p}/single_w*.jsonl"):
        for l in open(f):
            r = json.loads(l)
            if "error" not in r: iso[r["key"]] = r
    n = rep = 0
    with open(f"/home/user/audit/recalc/v3/iso/scan_{p}.jsonl", "w") as out:
        for l in open(V3 + f"scan_{p}.jsonl"):
            r = json.loads(l); n += 1
            if r["key"] in iso:
                s = {k: v for k, v in iso[r["key"]].items() if k not in ("utc", "attempt")}; r = s; rep += 1
            out.write(json.dumps(r) + "\n")
    print(p, n, "replaced", rep)
