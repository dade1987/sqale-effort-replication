# Public signs of active SonarQube Cloud use in the sampled projects (same sample as sample_projects.py).
# Usage: python3 active_use.py sample.jsonl active_use.jsonl
import json, urllib.request, urllib.parse, time, sys
from concurrent.futures import ThreadPoolExecutor
B = "https://sonarcloud.io/api/"
def get(path, **q):
    for t in range(4):
        try: return json.load(urllib.request.urlopen(B + path + "?" + urllib.parse.urlencode(q), timeout=60))
        except urllib.error.HTTPError as e: return {"_err": e.code}
        except Exception: time.sleep(2 + t * 2)
    return {"_err": "net"}
S = [json.loads(l) for l in open(sys.argv[1])]
S = [p for p in S if p.get("ncloc")]
def one(p):
    k = p["key"]
    tri = get("issues/search", componentKeys=k, issueStatuses="FALSE_POSITIVE,ACCEPTED", ps=1)
    an = get("project_analyses/search", project=k, ps=500, **{"from": "2025-10-24"})
    hist = get("measures/search_history", component=k, metrics="sqale_index,ncloc", ps=1000)
    pr = get("project_pull_requests/list", project=k)
    h = {m["metric"]: [(x["date"], x.get("value")) for x in m["history"] if x.get("value") is not None] for m in hist.get("measures", [])}
    return {"key": k, "organization": p["organization"], "ncloc": p["ncloc"], "qg": (p.get("qg") or {}).get("name"),
            "triaged": tri.get("paging", {}).get("total") if "_err" not in tri else None,
            "analyses_12m": an.get("paging", {}).get("total") if "_err" not in an else None,
            "n_pr": len(pr.get("pullRequests", [])) if "_err" not in pr else None,
            "sqale_hist": h.get("sqale_index", []), "ncloc_hist": h.get("ncloc", []),
            "errs": [x.get("_err") for x in (tri, an, hist, pr) if "_err" in x]}
with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, S))
with open(sys.argv[2], "w") as f:
    for r in res: f.write(json.dumps(r) + "\n")
print("ok", len(res))
