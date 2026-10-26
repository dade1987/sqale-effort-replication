import json,re,subprocess,sys,collections,os,statistics as st
repo,issues,pat,out=sys.argv[1:5]
iss={}
for l in open(issues):
    d=json.loads(l)
    if os.environ.get("ONLY_FIXED") and (d.get("resolution") or {}).get("name") not in ("Fixed","Done"): continue
    iss[d["key"]]=d
rx=re.compile(pat)
# one record per commit: hash, date, subject+body keys, files
p=subprocess.run(["git","-C",repo,"log","--all","--no-merges","--no-renames","--name-only","--format=%x1e%H%x09%aI%x09%ae%x09%s%n%b%n%x1d"],capture_output=True,text=True,errors="replace").stdout
links=collections.defaultdict(lambda:{"commits":set(),"files":set()})
ncommit=nkey=0
for block in p.split("\x1e")[1:]:
    head,_,files=block.partition("\x1d")
    parts=head.split("\t",3)
    if len(parts)<3: continue
    h,date,mail=parts[:3]
    ncommit+=1
    subj=head.split("\n",1)[0].split("\t",3)[-1]
    keys=set(rx.findall(subj if os.environ.get("SUBJECT_ONLY") else head))
    if os.environ.get("STRICT"):
        # exactly one key in the subject, at its start (e.g. "MDEV-123 ..." or "MDEV-123: ...")
        allk=rx.findall(subj)
        m=rx.match(subj.strip())
        keys=set(allk) if (m and len(set(allk))==1) else set()
    if keys: nkey+=1
    fl=[f for f in files.strip().splitlines() if f]
    for k in keys:
        if k in iss:
            links[k]["commits"].add(h); links[k]["files"].update(fl)
linked=[k for k in iss if k in links and links[k]["files"]]
print("commit",ncommit,"with key",nkey,"issues with hours",len(iss),"linked",len(linked))
h=[iss[k]["timespent"]/3600 for k in linked]
print("hours of linked issues: total",round(sum(h)),"median",round(st.median(h),2))
nf=[len(links[k]["files"]) for k in linked]; print("median files per issue",st.median(nf))
fc=collections.Counter(f for k in linked for f in links[k]["files"])
print("file distinti",len(fc),"file con >=5 issue",sum(v>=5 for v in fc.values()),">=20",sum(v>=20 for v in fc.values()))
comp=collections.Counter(c["name"] for k in linked for c in (iss[k].get("components") or []))
print("componenti",len(comp),"con >=50 issues",sum(v>=50 for v in comp.values()))
yr=collections.Counter((iss[k].get("resolutiondate") or "????")[:4] for k in linked); print(sorted(yr.items()))
small=[k for k in linked if len(links[k]["files"])<=5 and iss[k]["timespent"]<=8*3600 and (iss[k].get("issuetype") or {}).get("name") in ("Bug","Task","Improvement")]
print("candidate per agenti AI (<=5 file, <=8h, bug/task/improvement)",len(small))
with open(out,"w") as f:
    for k in linked: f.write(json.dumps({"key":k,"hours":iss[k]["timespent"]/3600,"type":(iss[k].get("issuetype") or {}).get("name"),"resolved":iss[k].get("resolutiondate"),"components":[c["name"] for c in iss[k].get("components") or []],"commits":sorted(links[k]["commits"]),"files":sorted(links[k]["files"])})+"\n")
