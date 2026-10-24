# Representativeness: how many resolved issues have logged hours, per resolution year and type.
# Counts from the public Jira search APIs (no personal data). Output: representativeness.csv
import json, urllib.request, urllib.parse, itertools, pandas as pd
from concurrent.futures import ThreadPoolExecutor
PERC = "project in (PMM,PS,PXC,PXB,K8SPXC,PBM,PSMDB,K8SPSMDB,PSQLADM,PT) AND resolution = Done"
SRC = {"moodle": ("https://moodle.atlassian.net", 3, "project = MDL AND resolution = Fixed"),
       "mariadb": ("https://jira.mariadb.org", 2, "project = MDEV AND resolution = Fixed"),
       "percona": ("https://perconadev.atlassian.net", 3, PERC)}
TYPES = ["Bug", "Improvement", "New Feature", "Task"]
def count(base, api, jql):
    if api == 2:
        u = base + "/rest/api/2/search?" + urllib.parse.urlencode({"jql": jql, "maxResults": 0})
        return json.load(urllib.request.urlopen(u, timeout=120))["total"]
    q = urllib.request.Request(base + "/rest/api/3/search/approximate-count", json.dumps({"jql": jql}).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(q, timeout=120))["count"]
jobs = []
for p, (base, api, j0) in SRC.items():
    for y, t, h in itertools.product(range(2013, 2027), TYPES + ["tutti"], [True, False]):
        jql = f'{j0} AND resolved >= "{y}-01-01" AND resolved < "{y + 1}-01-01"' + ("" if t == "tutti" else f' AND issuetype = "{t}"') + (" AND timespent > 0" if h else "")
        jobs.append((p, y, t, h, base, api, jql))
def run(j):
    for _ in range(4):
        try: return (*j[:4], count(*j[4:]))
        except Exception as e: err = e
    return (*j[:4], None)
with ThreadPoolExecutor(6) as ex: rows = list(ex.map(run, jobs))
d = pd.DataFrame(rows, columns=["progetto", "anno", "tipo", "con_ore", "n"])
d = d.pivot_table(index=["progetto", "anno", "tipo"], columns="con_ore", values="n").rename(columns={True: "con_ore", False: "tutte"}).reset_index()
d["quota_con_ore"] = d.con_ore / d.tutte
d.to_csv("representativeness.csv", index=False)
print(d[d.tipo == "tutti"].to_string())
