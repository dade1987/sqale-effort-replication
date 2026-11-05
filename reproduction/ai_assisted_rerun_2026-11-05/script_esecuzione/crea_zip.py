from pathlib import Path
import hashlib,zipfile,shutil,os
R=Path('/mnt/data/riproduzione_sqale');C=R/'consegna'
S=C/'script_esecuzione';S.mkdir(exist_ok=True)
for f in ['parallel_runner.py','run_replicazione.sh','verifica_risultati.py','confronta.py','controlla_output.py','crea_relazione.py','crea_zip.py','requirements_installabili.txt']:
 src=R/f
 if src.is_file(): shutil.copy2(src,S/f)
shutil.copy2('/mnt/data/guida_riproduzione_it(3).md',C/'guida_originale.md')
(C/'LEGGERE_PRIMA_DI_CONDIVIDERE.txt').write_text('Questo archivio contiene una riproduzione assistita da AI, NON una verifica umana indipendente.\nNon e stato creato o validato da Gianluigi Lucca Fabris.\nSono state usate versioni diverse delle dipendenze a causa dell’assenza di accesso al repository pip.\nLeggere relazione.txt e i due confronti prima di citare i risultati.\n')
filenames=sorted(p for p in C.rglob('*') if p.is_file() and p.name!='manifest_sha256.txt')
manifest='\n'.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(C)}' for p in filenames)+'\n'
(C/'manifest_sha256.txt').write_text(manifest)
z=Path('/mnt/data/riproduzione_assistita_AI.zip')
with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as out:
 for file in sorted(p for p in C.rglob('*') if p.is_file()):out.write(file,arcname='consegna/'+str(file.relative_to(C)))
with zipfile.ZipFile(z) as zp:
 bad=zp.testzip()
 if bad:raise RuntimeError('Corrupted entry: '+bad)
 print('ZIP',z,'files',len(zp.namelist()),'bytes',z.stat().st_size,'sha256',hashlib.sha256(z.read_bytes()).hexdigest())
