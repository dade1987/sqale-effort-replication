# Issue -> commit links over several repositories, same rule as code/link_issues_commits.py with ONLY_FIXED=1 STRICT=1
# (resolution Fixed or Done; merges excluded; the subject starts with exactly one issue key), with one adaptation fixed
# before any SQALE measurement: the key may be wrapped in [] or () at the start ("[MOS-123] ...", "(MOS-123) ...").
# Files are prefixed with the repository name; each issue keeps its main repository (most touched files), as for Percona.
# usage: link_multi.py <issues.jsonl> <key_regex> <repos_dir> <out.jsonl>
import json, re, subprocess, sys, os, collections
iss_f, pat, rdir, out = sys.argv[1:5]
iss = {}
for l in open(iss_f):
    d = json.loads(l)
    if (d.get("resolution") or {}).get("name") in ("Fixed", "Done"): iss[d["key"]] = d
rx = re.compile(pat); lead = re.compile(r"^[\[(]?(" + pat + r")[\])]?(?![0-9])")
links = collections.defaultdict(lambda: {"commits": set(), "files": collections.Counter(), "dates": []})
stat = collections.Counter()
for repo in sorted(os.listdir(rdir)):
    d = os.path.join(rdir, repo)
    p = subprocess.run(["git", "-C", d, "log", "--all", "--no-merges", "--no-renames", "--name-only", "--format=%x1e%H%x09%aI%x09%ae%x09%s%n%b%n%x1d"],
                       capture_output=True, text=True, errors="replace").stdout
    for block in p.split("\x1e")[1:]:
        head, _, files = block.partition("\x1d"); parts = head.split("\t", 3)
        if len(parts) < 4: continue
        h, date = parts[0], parts[1]; subj = parts[3].split("\n", 1)[0].strip(); stat["commits"] += 1
        allk = set(rx.findall(subj)); m = lead.match(subj)
        if not (m and len(allk) == 1): continue
        k = m.group(1)
        if k not in iss: continue
        fl = [f for f in files.strip().splitlines() if f]
        if not fl: continue
        L = links[k]; L["commits"].add(f"{repo}:{h}"); L["dates"].append(date); L["files"].update(f"{repo}/{f}" for f in fl)
with open(out, "w") as f:
    n = 0
    for k, L in links.items():
        c = collections.Counter(); [c.update({x.split("/", 1)[0]: 1}) for x in L["files"]]
        main = c.most_common(1)[0][0]; i = iss[k]
        f.write(json.dumps({"key": k, "hours": i["timespent"] / 3600, "type": (i.get("issuetype") or {}).get("name"), "resolved": i.get("resolutiondate"),
                            "created": i.get("created"), "components": [x["name"] for x in i.get("components") or []], "repo": main, "n_repos": len(c),
                            "commits": sorted(x.split(":", 1)[1] for x in L["commits"] if x.startswith(main + ":")),
                            "files": sorted(x.split("/", 1)[1] for x in L["files"] if x.startswith(main + "/")),
                            "first_commit_date": min(L["dates"])}) + "\n"); n += 1
print(iss_f, "fixed/done", len(iss), "commits", stat["commits"], "linked", n)
