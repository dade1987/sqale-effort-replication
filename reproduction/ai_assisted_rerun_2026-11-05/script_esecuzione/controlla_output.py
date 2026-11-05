from pathlib import Path
R=Path('/mnt/data/riproduzione_sqale');W=next((R/'lavoro').iterdir());C=R/'consegna';mark=(W/'inizio.txt').stat().st_mtime
expected=[f'code/results_{p}.json' for p in ('moodle','mariadb','percona','transfer','exploratory_moodle','exploratory_mariadb','exploratory_percona')]
expected += ['out_v2.json','out_v3.json','out_v3_strict.json']
expected += [f'results/confirmatory/confirmatory_{p}.json' for p in ('moodle','mariadb')]
res=[]
for n in expected:
 p=W/n;status='NON DISPONIBILE' if not p.exists() else 'RIGENERATO' if p.stat().st_mtime>=mark else 'PRESENTE MA NON RIGENERATO'
 res.append(f'{status}: {n}')
for p in sorted((W/'code').glob('log_*.txt')):
 s=p.read_text(errors='replace'); status='ERRORI/TRACEBACK' if 'Traceback' in s or 'Error:' in s or 'Segmentation fault' in s else 'NON SONO EMERSI ERRORI NEL LOG'
 res.append(f'{status}: code/{p.name}, {len(s)} caratteri')
res.append(f"Esplorative rigenerate: {sum(p.stat().st_mtime>=mark for p in (W/'results/exploratory').rglob('*') if p.is_file())} file")
(C/'14_controllo_output.txt').write_text('\n'.join(res)+'\n')
print('\n'.join(res))
