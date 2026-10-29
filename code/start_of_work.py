# Start of work for each issue, and the developer known at that moment (used for "M0 at start of work").
# S = the earlier of the first worklog day and the day of the first fix commit.
# Developer at S: the Jira assignee at the start of day S (changelog undone back to S); if nobody was assigned,
# the author of the first worklog, but only if that worklog is on day S (otherwise unknown). assignee_S_lenient keeps the
# first-worklog author whatever its date (the earlier definition). No information from the fix commits is used.
# Title at S: every title change made on or after day S is undone (summary_changes.jsonl from the Jira changelog, optional).
# Usage: python3 start_of_work.py <features.csv> <history.csv from history_features.py> <jira_history.jsonl> <out.csv> [summary_changes.jsonl]
import sys, json, datetime, pandas as pd
featf, histf, stf, out = sys.argv[1:5]
sch = {d["key"]: d.get("summary_changes") or [] for d in map(json.loads, open(sys.argv[5]))} if len(sys.argv) > 5 else {}
P = lambda s: datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
st = {}
for l in open(stf):
    d = json.loads(l); st[d["key"]] = d
fe = pd.read_csv(featf, usecols=["key", "fix_date"]).merge(pd.read_csv(histf, usecols=["key", "assignee_T", "first_worklog", "summary"]), on="key", how="left")[["key", "fix_date", "assignee_T", "first_worklog", "summary"]]
rows = []
for k, fix, ass_T, fw, title in fe.itertuples(index=False):
    S = min(fix, fw) if isinstance(fw, str) else fix
    T0, S0 = datetime.datetime.strptime(fix, "%Y-%m-%d"), datetime.datetime.strptime(S, "%Y-%m-%d")
    s = st.get(k); ass = ass_T if isinstance(ass_T, str) else None; src = "assignee"; lenient = None
    if s:
        for when, field, fr, frs, to, tos in sorted(s["changes"], key=lambda c: c[0], reverse=True):
            if (field or "").lower() == "assignee" and S0 <= P(when) < T0: ass = frs   # undo changes made between S and T
        if not ass:
            wl = sorted((w[3], w[1]) for w in s["worklogs"] if w[3])
            if wl:
                lenient = wl[0][1]
                if wl[0][0][:10] == S: ass, src = wl[0][1], "first_worklog_author (same day as S)"
                else: src = "none (first worklog after S)"
    if not ass and src == "assignee": src = "none"
    t = title if isinstance(title, str) else ""
    for when, fr, to in sorted(sch.get(k, []), key=lambda c: c[0], reverse=True):
        if when[:10] >= S and fr is not None: t = fr
    rows.append({"key": k, "start_date": S, "assignee_S": ass, "assignee_S_source": src, "assignee_S_lenient": ass or lenient,
                 "days_start_to_fix": (T0 - S0).days, "title_at_start": t, "title_changed_after_S": int(t != (title if isinstance(title, str) else ""))})
d = pd.DataFrame(rows); d.to_csv(out, index=False)
print(out, len(d), d.assignee_S_source.value_counts().to_dict(), "median days", d.days_start_to_fix.median(), file=sys.stderr)
