# 70 more random MOSIP links (protocol-conforming analysed sample, excluding the 30 already checked), seed 20261104.
import json, random, subprocess, urllib.request, os
P = "/mnt/project-files/ricerca2/preregistrazione_nuovi_progetti"
old = {x["k"] for x in json.load(open(P + "/link_check/sample90.json")) if x["p"] == "mosip"}
an = [json.loads(l) for l in open(P + "/risultati/sensitivity_strict_rerun_rule/scan_mosip_without_lots48_56.jsonl")]
an = sorted(d["key"] for d in an if d["files_measured"] > 0 and d["ncloc"] > 0 and d["key"] not in old)
keys = random.Random(20261104).sample(an, 70)
L = {json.loads(l)["key"]: json.loads(l) for l in open("/home/user/np/data/mosip_links.jsonl")}
out = []
for n, k in enumerate(keys, 1):
    d = L[k]; repo = d["repo"]; rd = "/home/user/repos/cand/mosip/" + repo
    cs = []
    for h in d["commits"]:
        s = subprocess.run(["git", "-C", rd, "show", "-s", "--format=%s", h], capture_output=True, text=True).stdout.strip()
        cs.append([h[:10], s])
    try:
        j = json.load(urllib.request.urlopen(f"https://mosip.atlassian.net/rest/api/2/issue/{k}?fields=summary,description", timeout=30))
        t, desc = j["fields"]["summary"], (j["fields"].get("description") or "")
    except Exception as e:
        t, desc = "", f"(descrizione non scaricata: {e})"
    out.append({"n": n, "p": "mosip", "k": k, "u": f"https://mosip.atlassian.net/browse/{k}", "t": t, "d": desc[:3000],
                "repo": f"https://github.com/mosip/{repo}", "c": cs, "nc": len(cs)})
json.dump(out, open(P + "/link_check/mosip70/sample70.json", "w"), ensure_ascii=False, indent=1)
print(len(out), sum(1 for x in out if x["t"]), keys[:3])
