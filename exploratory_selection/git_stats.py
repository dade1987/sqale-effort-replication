# Per-issue Git stats with the paper's STRICT linking rule (subject starts with exactly one key; no merges; --all; --no-renames).
# Usage: python3 git_stats.py <bare repo> <key regex> <out.jsonl>
import re,subprocess,sys,json,collections
repo,pat,out=sys.argv[1:4]; rx=re.compile(pat)
p=subprocess.Popen(["git","-C",repo,"log","--all","--no-merges","--no-renames","--numstat","--summary","--format=%x1e%H%x09%aI%x09%s"],stdout=subprocess.PIPE,text=True,errors="replace")
I=collections.defaultdict(lambda:{"commits":set(),"files":set(),"new":set(),"add":0,"del":0,"first":None})
cur=None
def flush(c):
    if not c: return
    h,date,subj,files,new,a,d=c
    allk=rx.findall(subj); m=rx.match(subj.strip())
    if not (m and len(set(allk))==1) or not files: return
    r=I[allk[0]]
    if h in r["commits"]: return
    r["commits"].add(h); r["files"]|=files; r["new"]|=new; r["add"]+=a; r["del"]+=d
    r["first"]=min(r["first"] or date,date)
for line in p.stdout:
    line=line.rstrip("\n")
    if line.startswith("\x1e"):
        flush(cur); h,date,subj=(line[1:].split("\t",2)+["",""])[:3]; cur=[h,date,subj,set(),set(),0,0]; continue
    if not line or cur is None: continue
    t=line.split("\t")
    if len(t)==3:
        a,d,f=t; cur[3].add(f)
        if a!="-": cur[5]+=int(a); cur[6]+=int(d)
    elif line.startswith(" create mode"):
        cur[4].add(line.split(" ",4)[-1])
flush(cur)
with open(out,"w") as fo:
    for k,r in I.items():
        fo.write(json.dumps({"key":k,"n_commits":len(r["commits"]),"n_files":len(r["files"]),"n_new_files":len(r["new"]&r["files"]),"lines_added":r["add"],"lines_deleted":r["del"],"first_commit":r["first"]})+"\n")
print(out,len(I))
