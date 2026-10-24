# Jira changelog and worklogs for each issue of the dataset, to reconstruct values at creation.
# Usage: python3 download_jira_history.py <base_url> <api 2|3> <keys.txt> <out.jsonl>
import json, sys, urllib.request, time, os
from concurrent.futures import ThreadPoolExecutor
base, api, kf, out = sys.argv[1:5]
F = {"issuetype", "priority", "component", "assignee", "timeoriginalestimate", "timeestimate", "status", "resolution"}
def get(u):
    for i in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"Accept": "application/json"}), timeout=90))
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(2 ** i)
        except Exception: time.sleep(2 ** i)
    return None
def one(k):
    hist = []
    if api == "3":
        s = 0
        while True:
            j = get(f"{base}/rest/api/3/issue/{k}/changelog?startAt={s}&maxResults=100")
            if not j: break
            hist += j["values"]; s += len(j["values"])
            if not j["values"] or s >= j["total"]: break
        meta = get(f"{base}/rest/api/3/issue/{k}?fields=created,assignee,reporter")
    else:
        j = get(f"{base}/rest/api/2/issue/{k}?expand=changelog&fields=created,assignee,reporter")
        meta = j; hist = (j or {}).get("changelog", {}).get("histories", [])
    ch = []
    for h in hist:
        for it in h.get("items", []):
            fl = (it.get("fieldId") or it.get("field") or "").lower()
            if fl in F or it.get("field") in ("Component", "assignee", "priority", "issuetype"):
                ch.append([h["created"], it.get("field"), it.get("from"), it.get("fromString"), it.get("to"), it.get("toString")])
    wl = []; s = 0
    while True:
        j = get(f"{base}/rest/api/{api}/issue/{k}/worklog?startAt={s}&maxResults=1000")
        if not j: break
        for w in j["worklogs"]:
            a = w.get("author") or {}
            wl.append([a.get("accountId") or a.get("name") or a.get("key"), a.get("displayName"), w["timeSpentSeconds"], w.get("started")])
        s += len(j["worklogs"])
        if not j["worklogs"] or s >= j.get("total", 0): break
    f = (meta or {}).get("fields", {})
    return {"key": k, "created": f.get("created"), "reporter": ((f.get("reporter") or {}).get("accountId") or (f.get("reporter") or {}).get("name")), "changes": ch, "worklogs": wl}
keys = open(kf).read().split()
done = set()
if os.path.exists(out): done = {json.loads(l)["key"] for l in open(out)}
keys = [k for k in keys if k not in done]
with open(out, "a") as fo, ThreadPoolExecutor(8) as ex:
    for i, r in enumerate(ex.map(one, keys)):
        fo.write(json.dumps(r) + "\n")
        if i % 500 == 0: print(i, len(keys), flush=True)
print("FINE", out)
