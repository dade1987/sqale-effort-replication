import os,subprocess,datetime,time
from pathlib import Path
R=Path('/mnt/data/riproduzione_sqale');W=next((R/'lavoro').iterdir());C=R/'consegna'; prog=R/'progresso.txt'
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
def log(s):
 with open(prog,'a') as f:f.write(s+'\n')
 print(s,flush=True)
args7=['python3.13','-u','code/confermativo_v3.py','../out_v3.json','mosip:data/features_v3_mosip.csv:scan/scan_mosip.jsonl','openlmis:data/features_v3_openlmis.csv:scan/scan_openlmis.jsonl','openmrs:data/features_v3_openmrs.csv:scan/scan_openmrs.jsonl']
args7b=['python3.13','-u','code/confermativo_v3.py','../out_v3_strict.json','mosip:data/features_v3_mosip.csv:results/sensitivity_strict_rerun_rule/scan_mosip_without_lots48_56.jsonl','openlmis:data/features_v3_openlmis.csv:scan/scan_openlmis.jsonl','openmrs:data/features_v3_openmrs.csv:scan/scan_openmrs.jsonl']
steps=[('07','07_test3',W/'preregistration_v3',args7),('07b','07_test3_mosip_regola_protocollo',W/'preregistration_v3',args7b),('08','08_modelli',W,['sh','-c','cd code && sh run_models.sh']),('09','09_esplorative',W,['sh','exploratory/run_all.sh']),('10','10_collegamenti',W,['python3.13','-u','link_validation/manual_check/analyze_manual_check.py'])]
procs=[]
for id,name,cwd,args in steps:
 f=open(C/f'{name}.txt','w')
 log(f"INIZIO {id} {datetime.datetime.now(datetime.timezone.utc).isoformat()} {name}")
 p=subprocess.Popen(args,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
 procs.append((id,name,p,f,time.monotonic()))
for id,name,p,f,t in procs:
 try:code=p.wait(timeout=1800)
 except subprocess.TimeoutExpired:
  p.kill();code=124
 f.close()
 (C/f'{id}_exit.txt').write_text(str(code)+'\n')
 log(f"FINE {id} {datetime.datetime.now(datetime.timezone.utc).isoformat()} EXIT={code} DURATA={time.monotonic()-t:.1f}s")
if (W/'code').exists():
 import shutil
 for p in (W/'code').glob('log_*.txt'):shutil.copyfile(p,C/p.name)
args=['python3.13',str(R/'confronta.py'),str(next((R/'originale').iterdir())),'.',
 'code/results_moodle.json=results/results_moodle.json','code/results_mariadb.json=results/results_mariadb.json','code/results_percona.json=results/results_percona.json','code/results_transfer.json=results/results_transfer.json',
 'code/results_exploratory_moodle.json=results/results_exploratory_moodle.json','code/results_exploratory_mariadb.json=results/results_exploratory_mariadb.json','code/results_exploratory_percona.json=results/results_exploratory_percona.json',
 'out_v2.json=preregistration_v2/risultati/risultati_confermativo_v2.json','out_v3.json=preregistration_v3/results/results_v3.json','out_v3_strict.json=preregistration_v3/results/sensitivity_strict_rerun_rule/results_strict.json']
with open(C/'11_confronto.txt','w') as f:
 r=subprocess.run(args,env=env,cwd=W,stdout=f,stderr=subprocess.STDOUT,timeout=100)
(C/'11_exit.txt').write_text(str(r.returncode)+'\n')
with open(C/'13_analisi_verifica.txt','w') as f:
 r=subprocess.run(['python3.13',str(R/'verifica_risultati.py')],env=env,cwd=W,stdout=f,stderr=subprocess.STDOUT,timeout=100)
log('PROCEDURA_TERMINATA')
