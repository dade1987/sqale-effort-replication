from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import json,re,shutil,subprocess,hashlib
R=Path('/mnt/data/riproduzione_sqale');W=next((R/'lavoro').iterdir());C=R/'consegna'
def load(p):
 try:return json.loads(p.read_text())
 except (OSError,ValueError):return None
now=datetime.now(ZoneInfo('Europe/Rome'))
prog=(R/'progresso.txt').read_text()
lines=['RELAZIONE DI RIPRODUZIONE TECNICA ASSISTITA DA AI',
 'Articolo EMSE: SQALE technical debt e issue effort',
 f'Data di chiusura: {now:%Y-%m-%d %H:%M:%S} (Europe/Rome)',
 'Autore dei comandi e della relazione: assistente AI, non Gianluigi Lucca Fabris.',
 'IMPORTANTE: questa prova NON soddisfa il requisito della guida di svolgere una verifica indipendente senza AI.',
 'I comandi sono stati eseguiti su una copia del pacchetto caricato dall’utente, non scaricato in autonomia da Zenodo.',
 '',
 'AMBIENTE',
 (C/'02_sistema.txt').read_text().strip(),
 'Sono state usate le librerie disponibili in ambiente, non le versioni fissate in requirements.txt.',
 'Il tentativo pip install -r requirements.txt (esclusa la riga python==3.13) non è riuscito per assenza di accesso al repository.',
 'Versioni effettive in 03_pip_freeze.txt. CPU con quattro core consentiti; OPENBLAS/OMP/MKL con un thread per processo.',
 '',
 'INTEGRITÀ PACCHETTO',
 (C/'00_hash_zip.txt').read_text().strip(),
 'Hash SHA-256 conforme a quello atteso nella guida: 914c2b912989dc751f3527980f98970d0b204f5fd6ff84f8ff6ecd9e577e004f.',
 'Verifica preregistration SHA256SUMS: 34 OK; 3 FAILED, tutti preregistration_v3/data/features_v3_{mosip,openlmis,openmrs}.csv.',
 'Queste 3 differenze sono documentate nel README v3 come pseudonimizzazione dei nomi sviluppatori.',
 '',
 'PASSAGGI E RISULTATI'
]
for k,descr in [('05','Confermativo 1 (Moodle, MariaDB)'),('06','Confermativo 2 (MariaDB C/C++)'),('07','Confermativo 3'),('07b','Confermativo 3 strict'),('08','Modelli principali'),('09','Esplorative'),('10','Controllo collegamenti'),('11','Confronto automatico')]:
 p=C/f'{k}_exit.txt';result=p.read_text().strip() if p.exists() else 'NON TERMINATO'
 lines.append(f'Passo {k}, {descr}: exit={result}'+ (' (OK)' if result=='0' else ' (NON COMPLETATO CON SUCCESSO)'))
for p in ['moodle','mariadb']:
 j=load(W/'results/confirmatory'/f'confirmatory_{p}.json')
 if j and (W/'results/confirmatory'/f'confirmatory_{p}.json').stat().st_mtime >= (W/'inizio.txt').stat().st_mtime:
  lines.append(f'{p}: H1 rho={j["H1"]["partial_rho"]:.8f}, CI90={j["H1"]["CI90"]}, H2 rho={j["H2"]["partial_rho"]:.8f}, H3 dMAE={j["H3"]["dMAE"]:.8f}')
j=load(W/'out_v2.json')
if j:
 lines.append(f'Confermativo 2: n={j["H1-C"]["n"]}, H1-C rho={j["H1-C"]["partial_rho"]:.8f}, CI90={j["H1-C"]["CI90"]}, verdict={j["H1-C"]["verdict"]}; H3-C dMAE={j["H3-C"]["dMAE"]:.8f}, verdict={j["H3-C"]["verdict"]}')
for file,label in [('out_v3.json','Confermativo 3'),('out_v3_strict.json','Confermativo 3 strict')]:
 j=load(W/file)
 if j:
  for pr in ['mosip','openlmis','openmrs']:
   if pr in j:
    lines.append(f'{label}, {pr}: n={j[pr]["H1"]["n"]}, H1 rho={j[pr]["H1"]["partial_rho"]:.8f}, CI90={j[pr]["H1"]["CI90"]}, verdict={j[pr]["H1"]["verdict"]}')
  if 'family' in j:lines.append(f'{label}, family: {j["family"]}')
for project in ['moodle','mariadb','percona']:
 p=W/'code'/f'results_{project}.json';j=load(p)
 if j and p.stat().st_mtime >= (W/'inizio.txt').stat().st_mtime:
  z=j['sqale']['all'];k=z['M1 vs SQALE recalibrated'];lines.append(f'Modello {project}: n={z["n"]}, MAE(SQALE grezzo)={z["SQALE raw"]["MAE"]:.6f}, MAE(SQALE ricalibrato)={z["SQALE recalibrated"]["MAE"]:.6f}, MAE(M1)={z["M1"]["MAE"]:.6f}, dMAE(M1 vs ricalibrato)={k["dMAE"]:.6f}, intervallo=[{k["lo"]:.6f}, {k["hi"]:.6f}]')
check=(C/'11_confronto.txt').read_text() if (C/'11_confronto.txt').exists() else 'non disponibile'
line=next((x for x in check.splitlines()[::-1] if x.startswith('File confrontati:')),'Non ancora disponibile')
lines.append(f'Confronto guida: {line}')
check2=(C/'13_confronto_completo.txt').read_text() if (C/'13_confronto_completo.txt').exists() else 'non disponibile'
line2=next((x for x in check2.splitlines()[::-1] if x.startswith('File confrontati:')),'Non ancora disponibile')
lines.append(f'Confronto strutturale aggiuntivo (include chiavi e stringhe): {line2}')
for x in check2.splitlines():
 if x.startswith('DIVERSO'):lines.append(x)
lines += ['', 'LIMITI DELLA RIPRODUZIONE',
 'La guida non ripete le scansioni di SonarQube sui repository originali, ma rielabora dati e scansioni distribuiti: non prova dunque la ricostruzione completa delle scansioni grezze.',
 'Non sono state rifatte la valutazione umana dei collegamenti issue-commit né le verifiche manuali dei casi difficili.',
 'La ricompilazione delle statistiche sui 100 giudizi archiviati non costituisce una nuova annotazione indipendente.',
 'La versione richiesta delle librerie non era installabile in questo ambiente; alcune differenze minime possono quindi dipendere dalle versioni numeriche.',
 'Un tentativo della verifica v3 è stato interrotto e sostituito da una nuova esecuzione completa insieme ad altri passaggi in parallelo.',
 '', 'TEMPI', prog,
 'Dichiarazione AI: il pacchetto è stato eseguito, verificato e descritto con assistenza AI; non va attribuito a Gianluigi Lucca Fabris.',
 '', 'File delle verifiche: 00-13, log_*, out_*.json, results_*.json, esplorative_rifatte/.'
]
(C/'relazione.txt').write_text('\n'.join(lines)+'\n')
(C/'12_casi_difficili.txt').write_text('Revisione umana opzionale NON effettuata: vietato presentare un giudizio AI come analisi indipendente a mano.\n'+
'Riferimenti da valutare manualmente: MDL-76867 (0b54a57), MDEV-7850 (aee03ea, 9b1ea69), MDEV-8919 (afbd28a), PMM-2060 (23c0179, 5e7cc2d).\n'+
'La procedura automatica su giudizi già presenti ha prodotto: '+(C/'10_collegamenti.txt').read_text().strip()+'\n')
for filename in ['out_v2.json','out_v3.json','out_v3_strict.json']:
 source=W/filename
 if source.exists() and source.stat().st_mtime >= (W/'inizio.txt').stat().st_mtime:shutil.copy2(source,C/filename)
for source in (W/'code').glob('results_*.json'):
 if source.stat().st_mtime >= (W/'inizio.txt').stat().st_mtime:shutil.copy2(source,C/source.name)
expl=W/'results/exploratory';target=C/'esplorative_rifatte';target.mkdir(exist_ok=True)
for source in expl.rglob('*'):
 if source.is_file() and source.stat().st_mtime >= (W/'inizio.txt').stat().st_mtime:
  dest=target/source.relative_to(expl); dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
(C/'99_fine.txt').write_text(now.isoformat()+'\n')
