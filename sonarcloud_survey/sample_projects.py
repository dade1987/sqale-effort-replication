import json, urllib.request, urllib.parse, sys, time, random
from concurrent.futures import ThreadPoolExecutor
B = "https://sonarcloud.io/api/"
def get(path, **q):
    for t in range(4):
        try: return json.load(urllib.request.urlopen(B + path + "?" + urllib.parse.urlencode(q), timeout=60))
        except urllib.error.HTTPError as e:
            return {"_err": e.code}
        except Exception: time.sleep(2 + t * 2)
    return {"_err": "net"}
allp = [json.loads(l) for l in open("tutti.jsonl")]
random.seed(20261023)
S = random.sample(allp, 400)
def one(p):
    k, o = p["key"], p["organization"]
    m = get("measures/component", component=k, metricKeys="ncloc,ncloc_language_distribution,sqale_index")
    meas = {x["metric"]: x.get("value") for x in m.get("component", {}).get("measures", [])}
    langs = {}
    for part in (meas.get("ncloc_language_distribution") or "").split(";"):
        if "=" in part: a, b = part.split("="); langs[a] = int(b)
    qp = get("qualityprofiles/search", project=k, organization=o)
    prof = {x["language"]: {"name": x["name"], "builtin": x["isBuiltIn"], "parent": x.get("parentKey") is not None} for x in qp.get("profiles", [])}
    st = get("settings/values", component=k, keys="sonar.technicalDebt.developmentCost,sonar.technicalDebt.ratingGrid")
    sets = {x["key"]: {"value": x.get("value"), "inherited": x.get("inherited"), "origin": x.get("parentOrigin")} for x in st.get("settings", [])}
    qg = get("qualitygates/get_by_project", project=k, organization=o)
    return dict(p, ncloc=meas.get("ncloc"), sqale_index=meas.get("sqale_index"), langs=langs, profiles=prof, settings=sets,
                qg=qg.get("qualityGate"), errs=[x.get("_err") for x in (m, qp, st, qg) if "_err" in x])
with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, S))
with open("sample.jsonl", "w") as f:
    for r in res: f.write(json.dumps(r) + "\n")
print("ok", len(res))
