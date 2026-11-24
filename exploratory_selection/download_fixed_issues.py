# Downloads ALL fixed issues (with and without logged time) resolved since 2018, keeping comment COUNT only.
import json,urllib.request,urllib.parse,sys,time
base,cloud,jql,out=sys.argv[1],sys.argv[2]=="1",sys.argv[3],sys.argv[4]
F="timespent,created,resolutiondate,issuetype,priority,components,comment,resolution,status"
def req(u):
    for i in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"Accept":"application/json"}),timeout=180))
        except Exception as e: time.sleep(2**i); err=e
    raise err
def slim(i):
    f=i["fields"]; c=f.get("comment") or {}
    return {"key":i["key"],"timespent":f.get("timespent"),"created":f.get("created"),"resolved":f.get("resolutiondate"),
            "type":(f.get("issuetype") or {}).get("name"),"priority":(f.get("priority") or {}).get("name"),
            "n_components":len(f.get("components") or []),"n_comments":c.get("total",len(c.get("comments",[]))),
            "resolution":(f.get("resolution") or {}).get("name")}
n=0;tok=None;start=0
with open(out,"w") as fo:
  while True:
    if cloud:
        q={"jql":jql,"maxResults":100,"fields":F}
        if tok: q["nextPageToken"]=tok
        r=req(base+"/rest/api/3/search/jql?"+urllib.parse.urlencode(q)); iss=r["issues"]; tok=r.get("nextPageToken")
    else:
        r=req(base+"/rest/api/2/search?"+urllib.parse.urlencode({"jql":jql,"maxResults":200,"startAt":start,"fields":F})); iss=r["issues"]; start+=len(iss)
    for i in iss: fo.write(json.dumps(slim(i))+"\n")
    n+=len(iss); print(n,file=sys.stderr,flush=True)
    if cloud and (not tok or r.get("isLast")): break
    if not cloud and (not iss or start>=r["total"]): break
print(out,n)
