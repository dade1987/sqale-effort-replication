# Start of work for each issue, and the developer known at that moment (used for "M0 at start of work").
# S = the earlier of the first worklog day and the day of the first fix commit.
# Developer at S: the Jira assignee at the start of day S (changelog undone back to S); if nobody was assigned,
# the author of the first worklog. No information from the fix commits is used.
# Usage: python3 start_of_work.py <features.csv> <history.csv from history_features.py> <jira_history.jsonl> <out.csv>
import sys, json, datetime, pandas as pd
featf, histf, stf, out = sys.argv[1:5]
P = lambda s: datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
st = {}
for l in open(stf):
    d = json.loads(l); st[d["key"]] = d
fe = pd.read_csv(featf, usecols=["key", "fix_date"]).merge(pd.read_csv(histf, usecols=["key", "assignee_T", "first_worklog"]), on="key", how="left")
rows = []
for k, fix, ass_T, fw in fe.itertuples(index=False):
    S = min(fix, fw) if isinstance(fw, str) else fix
    T0, S0 = datetime.datetime.strptime(fix, "%Y-%m-%d"), datetime.datetime.strptime(S, "%Y-%m-%d")
    s = st.get(k); ass = ass_T if isinstance(ass_T, str) else None; src = "assignee"
    if s:
        for when, field, fr, frs, to, tos in sorted(s["changes"], key=lambda c: c[0], reverse=True):
            if (field or "").lower() == "assignee" and S0 <= P(when) < T0: ass = frs   # undo changes made between S and T
        if not ass:
            wl = sorted((w[3], w[1]) for w in s["worklogs"] if w[3])
            if wl: ass, src = wl[0][1], "first_worklog_author"
    if not ass: src = "none"
    rows.append({"key": k, "start_date": S, "assignee_S": ass, "assignee_S_source": src, "days_start_to_fix": (T0 - S0).days})
d = pd.DataFrame(rows); d.to_csv(out, index=False)
print(out, len(d), d.assignee_S_source.value_counts().to_dict(), "median days", d.days_start_to_fix.median(), file=sys.stderr)
