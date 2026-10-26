import json, urllib.request, urllib.parse, time
from concurrent.futures import ThreadPoolExecutor
R=[json.loads(l) for l in open("sample.jsonl")]
ok=[r for r in R if r["langs"] and r["profiles"]]
def get(q):
    for t in range(4):
        try: return json.load(urllib.request.urlopen("https://sonarcloud.io/api/rules/search?"+urllib.parse.urlencode(q), timeout=60))
        except Exception: time.sleep(2+2*t)
    return None
def one(r):
    o=r["organization"]; langs=",".join(sorted(r["langs"], key=r["langs"].get, reverse=True)[:3])
    n=0; ov=[]; p=1
    while True:
        d=get({"organization":o,"languages":langs,"ps":500,"p":p,"f":"remFn,defaultRemFn"})
        if d is None: return {"key":r["key"],"err":True}
        for x in d["rules"]:
            n+=1
            if (x.get("remFnType"),x.get("remFnBaseEffort"),x.get("remFnGapMultiplier"))!=(x.get("defaultRemFnType"),x.get("defaultRemFnBaseEffort"),x.get("defaultRemFnGapMultiplier")): ov.append(x["key"])
        if p*500>=d["total"]: break
        p+=1
    return {"key":r["key"],"org":o,"langs":langs,"rules":n,"overridden":ov}
with ThreadPoolExecutor(6) as ex: res=list(ex.map(one, ok))
json.dump(res, open("remfn.json","w"))
orgs={}
for x in res: orgs.setdefault(x.get("org"),x)
print("progetti",len(res),"errori",sum(1 for x in res if x.get("err")),"con override",sum(1 for x in res if x.get("overridden")))
print("regole controllate (media)", sum(x.get("rules",0) for x in res)/len(res))
print([ (x["key"],len(x["overridden"])) for x in res if x.get("overridden")])
