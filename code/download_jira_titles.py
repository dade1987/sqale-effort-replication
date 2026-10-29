# Title (summary) changes from the Jira changelog, used by start_of_work.py to reconstruct the title at the start of work.
# Usage: python3 download_jira_titles.py <base> <api 2|3> <keys.txt> <out.jsonl>
import json, sys, urllib.request, urllib.error, time, os
from concurrent.futures import ThreadPoolExecutor
base, api, kf, out = sys.argv[1:5]
def get(u):
    for i in range(6):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"Accept": "application/json"}), timeout=90))
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(2 ** i)
        except Exception: time.sleep(2 ** i)
    return "ERR"
def one(k):
    hist = []
    if api == "3":
        s = 0
        while True:
            j = get(f"{base}/rest/api/3/issue/{k}/changelog?startAt={s}&maxResults=100")
            if j == "ERR": return {"key": k, "error": 1}
            if not j: break
            hist += j["values"]; s += len(j["values"])
            if not j["values"] or s >= j["total"]: break
    else:
        j = get(f"{base}/rest/api/2/issue/{k}?expand=changelog&fields=summary")
        if j == "ERR": return {"key": k, "error": 1}
        hist = (j or {}).get("changelog", {}).get("histories", [])
    ch = [[h["created"], it.get("fromString"), it.get("toString")] for h in hist for it in h.get("items", []) if (it.get("field") or "").lower() == "summary"]
    return {"key": k, "summary_changes": ch}
keys = open(kf).read().split()
done = {json.loads(l)["key"] for l in open(out) if "error" not in l} if os.path.exists(out) else set()
keys = [k for k in keys if k not in done]
with open(out, "a") as fo, ThreadPoolExecutor(8) as ex:
    for i, r in enumerate(ex.map(one, keys)):
        fo.write(json.dumps(r) + "\n"); fo.flush()
        if i % 1000 == 0: print(i, len(keys), flush=True)
print("DONE", out, flush=True)
