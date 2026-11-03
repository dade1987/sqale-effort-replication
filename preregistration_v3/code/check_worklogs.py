# Data check on 200 random linked issues per project (seed 20261103): worklog authors, suspicious accounts, granularity,
# single bulk worklogs, worklog author also author of a linked commit (by normalised name). No SQALE involved.
import json, sys, random, requests, collections, subprocess, re, unicodedata
host, links, rdir = sys.argv[1:4]
L = [json.loads(l) for l in open(links)]; random.seed(20261103); S = random.sample(L, min(200, len(L)))
norm = lambda s: re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower())
st = collections.Counter(); auth = collections.Counter(); gran = collections.Counter(); match = 0; nw = []
for d in S:
    w = requests.get(f"https://{host}/rest/api/3/issue/{d['key']}/worklog", params={"maxResults": 5000}, timeout=60).json().get("worklogs", [])
    names = {x["author"].get("displayName", "?") for x in w}; auth.update(names); nw.append(len(w))
    st["with worklog" if w else "no worklog"] += 1
    if any(re.search(r"bot|automation|tempo|service|jira", a, re.I) for a in names): st["suspicious account"] += 1
    if len(w) == 1: st["single worklog"] += 1
    for x in w: gran["multiple of 30 min" if x["timeSpentSeconds"] % 1800 == 0 else "other"] += 1
    ca = set()
    for c in d["commits"][:20]:
        r = subprocess.run(["git", "-C", f"{rdir}/{d['repo']}", "log", "-1", "--format=%an", c], capture_output=True, text=True).stdout.strip(); ca.add(norm(r))
    if any(norm(a) in ca or any(norm(a)[:6] and norm(a)[:6] in x for x in ca) for a in names): match += 1
import statistics
print(json.dumps({"host": host, "sample": len(S), **st, "worklog_author_is_commit_author_share": round(match / len(S), 3), "median_worklogs": statistics.median(nw),
                  "distinct_authors": len(auth), "top_authors_counts": [n for _, n in auth.most_common(10)], "granularity": dict(gran)}))
