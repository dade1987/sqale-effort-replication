# Jira values reconstructed from the changelog: type, priority and components at creation,
# assignee at the first fix commit, first Original Estimate, hours of the assignee only.
# Usage: python3 history_features.py <features.csv> <jira.jsonl> <jira_history.jsonl> <out.csv>
import sys, json, datetime, pandas as pd
featf, jiraf, stf, out = sys.argv[1:5]
P = lambda s: datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S") if s else None
jira = {}
for l in open(jiraf):
    d = json.loads(l); jira[d["key"]] = d
st = {}
for l in open(stf):
    d = json.loads(l); st[d["key"]] = d
fe = pd.read_csv(featf, usecols=["key", "fix_date", "type", "components"])
rows = []
for k, fix, typ, comps in fe.itertuples(index=False):
    j = jira.get(k, {}); s = st.get(k)
    T = datetime.datetime.strptime(fix, "%Y-%m-%d")          # day of the first fix commit (start of day)
    cur_type = typ; cur_prio = (j.get("priority") or {}).get("name")
    cur_comp = set(c for c in str(comps).split("|") if c and c != "nan")
    cur_ass = (j.get("assignee") or {}).get("displayName")
    est_cur = j.get("timeoriginalestimate")
    r = {"key": k, "summary": j.get("summary") or ""}
    if not s:
        r.update(type_open=cur_type, priority_open=cur_prio, components_open="|".join(sorted(cur_comp)), assignee_T=cur_ass,
                 est_first_h=(est_cur or 0) / 3600 or None, storia=0); rows.append(r); continue
    ch = sorted(s["changes"], key=lambda c: c[0], reverse=True)   # from newest to oldest
    created = P(s["created"])
    typ_o, prio_o, comp_o, ass_T = cur_type, cur_prio, set(cur_comp), cur_ass
    est_vals = []
    for when, field, fr, frs, to, tos in ch:
        w = P(when)
        f = (field or "").lower()
        if f == "issuetype": typ_o = frs              # undo changes back to creation
        elif f == "priority": prio_o = frs
        elif f == "component":
            if tos and not frs: comp_o.discard(tos)
            elif frs and not tos: comp_o.add(frs)
        elif f == "assignee" and w >= T: ass_T = frs   # assignee at the start of the day of the first commit
        elif f == "timeoriginalestimate": est_vals.append((w, fr, to))
    # first original estimate: the initial value of the first change, or the first value set
    est_first = None; est_date = None
    if est_vals:
        w, fr, to = sorted(est_vals)[0]
        est_first = float(fr) if fr else (float(to) if to else None)
        est_date = created if fr else w        # already present at the first change = set at creation
    elif est_cur: est_first = float(est_cur); est_date = created
    wl_start = min((P(w[3]) for w in s["worklogs"] if w[3]), default=None)
    # hours logged by the assignee (at the first commit) and number of worklog authors
    wl = s["worklogs"]; tot = sum(w[2] for w in wl) or 0
    mine = sum(w[2] for w in wl if w[1] == ass_T)
    authors = {w[1] for w in wl}
    r.update(type_open=typ_o, priority_open=prio_o, components_open="|".join(sorted(comp_o)), assignee_T=ass_T,
             est_first_h=(est_first or 0) / 3600 or None, est_changed=int(len(est_vals) > 1 or (len(est_vals) == 1 and est_vals[0][1] is not None)),
             est_first_date=est_date.strftime("%Y-%m-%d") if est_date else None, first_worklog=wl_start.strftime("%Y-%m-%d") if wl_start else None, hours_assignee=mine / 3600, hours_wl_total=tot / 3600, n_wl_authors=len(authors),
             type_changed=int(typ_o != cur_type), prio_changed=int(prio_o != cur_prio), ass_changed=int(ass_T != cur_ass), storia=1)
    rows.append(r)
d = pd.DataFrame(rows); d.to_csv(out, index=False)
print(out, len(d), d[["type_changed", "prio_changed", "ass_changed", "est_changed"]].mean().round(3).to_dict(), "assegnatario mancante", d.assignee_T.isna().mean().round(3), file=sys.stderr)
