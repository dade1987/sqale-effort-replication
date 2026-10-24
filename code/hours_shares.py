# Who logs the hours, and when the expert estimate is first set.
#  - share of hours logged by the assignee at the first commit (weighted by hours, and per issue)
#  - time of the first Original Estimate relative to the first commit (T)
# Usage: python3 hours_shares.py <data_dir> <jira_history_dir>   -> hours_shares.json
# Needs the raw Jira change histories (download_jira_history.py), which contain personal names and are not distributed.
import json, pandas as pd, numpy as np
import sys
M, S = sys.argv[1], sys.argv[2]
P = {"moodle": (M + "features/moodle_features.csv", "st_moodle.jsonl"), "mariadb": (M + "features/mariadb_features.csv", "st_mariadb.jsonl"),
     "percona": (M + "features/percona_features.csv", "st_percona.jsonl")}
out = {}
for p, (f, st) in P.items():
    d = pd.read_csv(M + f"history/{p}_history.csv").merge(pd.read_csv(f)[["key", "hours", "fix_date"]], on="key")
    a = d[d.assignee_T.notna() & (d.hours_wl_total > 0)]
    T = dict(zip(d.key, d.fix_date))
    first_est = {}
    for l in open(S + st):
        j = json.loads(l)
        ch = [c for c in j["changes"] if c[1] == "timeoriginalestimate" and c[4]]
        if ch: first_est[j["key"]] = min(c[0] for c in ch)[:10]
    fe = pd.Series(first_est)
    before = [fe[k] <= T[k] for k in fe.index if k in T]
    out[p] = {"issue_con_assegnatario_e_worklog": int(len(a)),
              "quota_ore_assegnatario_pesata": float(a.hours_assignee.sum() / a.hours_wl_total.sum()),
              "quota_issue_ore_solo_assegnatario": float((a.hours_assignee == a.hours_wl_total).mean()),
              "quota_issue_zero_ore_assegnatario": float((a.hours_assignee == 0).mean()),
              "mediana_autori_worklog": float(a.n_wl_authors.median()),
              "issue_con_prima_stima_nella_storia": int(len(before)),
              "quota_prima_stima_entro_T": float(np.mean(before)) if before else None}
json.dump(out, open("hours_shares.json", "w"), indent=1)
print(json.dumps(out, indent=1))
