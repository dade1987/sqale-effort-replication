# Exploratory (not preregistered): per-issue SQALE and NCLOC recomputed from the stored SonarQube analyses,
# leaving out files whose path looks like a test (no sonar.tests was set, so SonarQube measured tests as code).
import json, sys, re, urllib.request, base64, collections
proj, nlot, scanf, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
TOK = json.load(open("/home/user/sonar/token.json"))["token"]
TEST = re.compile(r"(^|/)(test|tests|__tests__|spec|e2e|it)/|[._-](spec|test|tests)\.[a-z]+$|Tests?\.java$|IT\.java$", re.I)
def api(p):
    q = urllib.request.Request("http://localhost:9000" + p, headers={"Authorization": "Basic " + base64.b64encode((TOK + ":").encode()).decode()})
    return json.load(urllib.request.urlopen(q))
per = collections.defaultdict(lambda: {"sqale_min": 0, "smells": 0, "ncloc": 0, "files_measured": 0}); ntest = collections.Counter()
for lot in range(nlot):
    pk = f"full{proj}_lot{lot}"; p = 1
    while True:
        j = api(f"/api/measures/component_tree?component={pk}&qualifiers=FIL&metricKeys=sqale_index,code_smells,ncloc&ps=500&p={p}")
        for c in j["components"]:
            k, rest = c["path"].split("/", 1)
            if TEST.search(rest): ntest[k] += 1; continue
            m = {x["metric"]: float(x["value"]) for x in c["measures"]}
            per[k]["sqale_min"] += m.get("sqale_index", 0); per[k]["smells"] += m.get("code_smells", 0); per[k]["ncloc"] += m.get("ncloc", 0); per[k]["files_measured"] += 1
        if p * 500 >= j["paging"]["total"]: break
        p += 1
n = 0
with open(out, "w") as f:
    for l in open(scanf):
        d = json.loads(l); d.update(per.get(d["key"], {"sqale_min": 0, "smells": 0, "ncloc": 0, "files_measured": 0})); d["test_files_left_out"] = ntest[d["key"]]
        f.write(json.dumps(d) + "\n"); n += d["test_files_left_out"] > 0
print(proj, "issues with test files left out:", n, "test files:", sum(ntest.values()), file=sys.stderr)
