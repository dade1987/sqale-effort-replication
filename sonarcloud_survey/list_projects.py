import json, urllib.request, urllib.parse, sys, time
R = ["ncloc >= 50000 and ncloc < 70000","ncloc >= 70000 and ncloc < 100000","ncloc >= 100000 and ncloc < 200000","ncloc >= 200000 and ncloc < 500000","ncloc >= 500000"]
seen = {}
for f in R:
    for p in range(1, 21):
        q = urllib.parse.urlencode({"filter": f, "ps": 500, "p": p, "f": "analysisDate"})
        for t in range(4):
            try: d = json.load(urllib.request.urlopen("https://sonarcloud.io/api/components/search_projects?" + q, timeout=60)); break
            except Exception as e: print(e, file=sys.stderr); time.sleep(3)
        for c in d["components"]: seen[c["key"]] = {k: c.get(k) for k in ("organization", "key", "name", "analysisDate")}
        if len(d["components"]) < 500: break
    print(f, len(seen), file=sys.stderr)
with open(sys.argv[1], "w") as o:
    for v in seen.values(): o.write(json.dumps(v) + "\n")
