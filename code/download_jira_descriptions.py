# Downloads the current issue descriptions (wiki text), in blocks of 100 keys.
# Usage: python3 download_jira_descriptions.py <base_url> <cloud 0|1> <keys.txt> <out.jsonl>
import sys, json, urllib.request, urllib.parse, time
from concurrent.futures import ThreadPoolExecutor
base, cloud, kf, out = sys.argv[1], sys.argv[2] == "1", sys.argv[3], sys.argv[4]
keys = open(kf).read().split()
chunks = [keys[i:i + 100] for i in range(0, len(keys), 100)]
def get(ch):
    path = "/rest/api/2/search/jql" if cloud else "/rest/api/2/search"
    u = base + path + "?" + urllib.parse.urlencode({"jql": "key in (" + ",".join(ch) + ")", "fields": "description", "maxResults": 100})
    for t in range(5):
        try: return [{"key": i["key"], "description": i["fields"].get("description") or ""} for i in json.load(urllib.request.urlopen(u, timeout=120))["issues"]]
        except Exception as e: err = e; time.sleep(2 ** t)
    print("error", ch[0], err, file=sys.stderr); return []
with open(out, "w") as f, ThreadPoolExecutor(4) as ex:
    for i, rs in enumerate(ex.map(get, chunks)):
        for r in rs: f.write(json.dumps(r) + "\n")
        if i % 20 == 0: print(i, len(chunks), file=sys.stderr, flush=True)
