#!/usr/bin/env python3
"""Independent of bundled comparator: structurally and numerically compare regenerated JSON files."""
import json,math,os
from pathlib import Path
R=Path('/mnt/data/riproduzione_sqale'); W=next((R/'lavoro').iterdir()); O=next((R/'originale').iterdir())
C=R/'consegna'; marker=(W/'inizio.txt').stat().st_mtime
extra={
 'code/results_moodle.json':'results/results_moodle.json',
 'code/results_mariadb.json':'results/results_mariadb.json',
 'code/results_percona.json':'results/results_percona.json',
 'code/results_transfer.json':'results/results_transfer.json',
 'code/results_exploratory_moodle.json':'results/results_exploratory_moodle.json',
 'code/results_exploratory_mariadb.json':'results/results_exploratory_mariadb.json',
 'code/results_exploratory_percona.json':'results/results_exploratory_percona.json',
 'out_v2.json':'preregistration_v2/risultati/risultati_confermativo_v2.json',
 'out_v3.json':'preregistration_v3/results/results_v3.json',
 'out_v3_strict.json':'preregistration_v3/results/sensitivity_strict_rerun_rule/results_strict.json',
}
pairs = [(p.relative_to(O).as_posix(),p.relative_to(O).as_posix()) for p in O.rglob('*.json') if (W/p.relative_to(O)).exists()]
pairs += [(a,b) for a,b in extra.items()]
results=[]
def compare(a,b,path,di):
 if isinstance(a,dict) and isinstance(b,dict):
  for k in sorted(a.keys()|b.keys()):
   if k not in a or k not in b: di.append((path+'/'+k,'KEY_MISSING_OR_EXTRA',str(k in a),str(k in b)))
   else: compare(a[k],b[k],path+'/'+k,di)
 elif isinstance(a,list) and isinstance(b,list):
  if len(a)!=len(b): di.append((path,'LIST_SIZE',len(a),len(b)))
  else:
   for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+f'[{i}]',di)
 elif isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):
  if not ((math.isnan(a) and math.isnan(b)) or math.isclose(a,b,rel_tol=1e-6,abs_tol=1e-7)):di.append((path,'NUMBER',a,b))
 elif a!=b:di.append((path,'VALUE_OR_TYPE',a,b))
for wpath,opath in sorted(set(pairs)):
 wp=W/wpath;op=O/opath
 if not wp.exists() or not op.exists():
  results.append({'file':wpath,'reference':opath,'error':'FILE NON DISPONIBILE'})
  continue
 if wp.stat().st_mtime < marker:
  continue
 try:
  a=json.loads(op.read_text()); b=json.loads(wp.read_text())
 except Exception as e:
  results.append({'file':wpath,'reference':opath,'error':repr(e)}); continue
 diffs=[];compare(a,b,'',diffs)
 results.append({'file':wpath,'reference':opath,'match':not diffs,'differences':diffs[:100],'n_differences':len(diffs),'exact':a==b})
(C/'13_confronto_completo.json').write_text(json.dumps(results,ensure_ascii=False,indent=2,default=str))
lines=[]
for x in results:
 lines.append(('UGUALE ' if x.get('match') else 'DIVERSO') + ' ' + x['file'] + (' (differenze solo a precisione macchina)' if x.get('match') and not x.get('exact') else ''))
 for d in x.get('differences',[])[:8]:lines.append('    '+ repr(d))
 if 'error' in x:lines.append('    ERRORE '+x['error'])
lines.append(f"File confrontati: {len(results)}; file con differenze oltre tolleranza: {sum(not x.get('match',False) for x in results)}")
(C/'13_confronto_completo.txt').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
