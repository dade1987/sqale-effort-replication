import json,urllib.request,urllib.parse,sys,time
base,cloud,jql,out=sys.argv[1],sys.argv[2]=="1",sys.argv[3],sys.argv[4]
F="timespent,timeoriginalestimate,created,resolutiondate,issuetype,status,resolution,components,project,summary,priority,assignee,fixVersions"
def req(u):
    for i in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"Accept":"application/json"}),timeout=120))
        except Exception as e: time.sleep(2**i); err=e
    raise err
rows=[];tok=None;start=0
while True:
    if cloud:
        q={"jql":jql,"maxResults":100,"fields":F}
        if tok: q["nextPageToken"]=tok
        r=req(base+"/rest/api/3/search/jql?"+urllib.parse.urlencode(q)); rows+=r["issues"]; tok=r.get("nextPageToken")
        if not tok or r.get("isLast"): break
    else:
        r=req(base+"/rest/api/2/search?"+urllib.parse.urlencode({"jql":jql,"maxResults":1000,"startAt":start,"fields":F})); rows+=r["issues"]; start+=len(r["issues"])
        if not r["issues"] or start>=r["total"]: break
    print(len(rows),file=sys.stderr,flush=True)
with open(out,"w") as f:
    for i in rows: f.write(json.dumps({"key":i["key"],**i["fields"]})+"\n")
print(out,len(rows))
