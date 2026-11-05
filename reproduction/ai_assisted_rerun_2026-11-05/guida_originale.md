# Guida per la riproduzione indipendente (articolo EMSE su SQALE)

Versione del 4 novembre 2026, seconda edizione: questa volta si rifà **tutto** e si **salva tutto**.

Per: Gianluigi Lucca Fabris, con un computer Linux o Mac e Python 3.13.
Tempo: circa 1 ora (su un computer con 4 processori i calcoli più lunghi durano circa 5 e 10 minuti).
Regole: non usare strumenti di AI per eseguire i comandi o controllare i risultati; non chiedere aiuto all'autore durante i passaggi; annotare ogni differenza. Se poi usi un'AI per scrivere il testo della relazione, dichiaralo.

**Importante:** non cancellare niente fino alla fine. Alla fine si manda a Davide **un solo file zip** (passo 11).

## 1. Preparare le cartelle
```
mkdir -p ~/riproduzione_sqale && cd ~/riproduzione_sqale
mkdir originale lavoro consegna
```
- `originale`: il pacchetto intatto, solo per il confronto. Non si tocca.
- `lavoro`: qui si fanno girare i comandi.
- `consegna`: qui finisce tutto quello da mandare.

## 2. Scaricare il pacchetto (versione 1.7)
```
cd ~/riproduzione_sqale
curl -L -o pacchetto_v1.7.zip "https://zenodo.org/records/23942119/files/dade1987/sqale-effort-replication-v1.7.zip?download=1"
sha256sum pacchetto_v1.7.zip | tee consegna/00_hash_zip.txt
unzip -q pacchetto_v1.7.zip -d originale
unzip -q pacchetto_v1.7.zip -d lavoro
```
L'hash atteso è `914c2b912989dc751f3527980f98970d0b204f5fd6ff84f8ff6ecd9e577e004f`.
Crea anche il piccolo programma di confronto `confronta.py`, che serve al passo 10 (copia e incolla tutto il blocco nel terminale):
```
cat > ~/riproduzione_sqale/confronta.py <<'FINE'
# Confronta i numeri dei file JSON di due cartelle (pacchetto originale vs cartella di lavoro).
# Uso: python3 confronta.py <cartella_originale> <cartella_lavoro> [file_extra_lavoro=file_originale ...]
import json, sys, os, math
A, B = sys.argv[1], sys.argv[2]
pairs = []
for root, _, files in os.walk(A):
    for f in files:
        if f.endswith(".json"):
            a = os.path.join(root, f); b = os.path.join(B, os.path.relpath(a, A))
            if os.path.exists(b): pairs.append((a, b))
for x in sys.argv[3:]:
    b, a = x.split("="); pairs.append((os.path.join(A, a), os.path.join(B, b)))
def walk(x, y, path, out):
    if isinstance(x, dict) and isinstance(y, dict):
        for k in x:
            if k in y: walk(x[k], y[k], path + "/" + str(k), out)
            else: out.append((path + "/" + str(k), "manca"))
    elif isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
        for i, (u, v) in enumerate(zip(x, y)): walk(u, v, f"{path}[{i}]", out)
    elif isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
        if not (math.isclose(x, y, rel_tol=1e-6, abs_tol=1e-7) or (math.isnan(x) and math.isnan(y))): out.append((path, f"{x} -> {y}"))
    elif x != y and not isinstance(x, str): out.append((path, f"{x} -> {y}"))
tot = diff = 0
mark = os.path.join(B, 'inizio.txt'); t0 = os.path.getmtime(mark) if os.path.exists(mark) else 0
for a, b in sorted(pairs):
    try: x, y = json.load(open(a)), json.load(open(b))
    except Exception as e: print("NON LEGGIBILE", b, e); continue
    if os.path.getmtime(b) < t0: continue  # file non rifatto in questa esecuzione
    out = []; walk(x, y, "", out); tot += 1
    if out:
        diff += 1; print(f"DIVERSO {os.path.relpath(b, B)}: {len(out)} valori"); [print("   ", p, v) for p, v in out[:10]]
    else: print(f"UGUALE  {os.path.relpath(b, B)}")
print(f"\nFile confrontati: {tot}; con differenze: {diff}")
FINE
```

Da qui in poi i comandi partono dalla cartella del pacchetto di lavoro:
```
cd ~/riproduzione_sqale/lavoro/dade1987-sqale-effort-replication-*
export C=~/riproduzione_sqale/consegna
```
Se apri un terminale nuovo, rifai questi due comandi e riattiva Python (`. ~/riproduzione_sqale/venv/bin/activate`).

## 3. Preparare Python e salvare le versioni
```
python3.13 -m venv ~/riproduzione_sqale/venv && . ~/riproduzione_sqale/venv/bin/activate
pip install -r requirements.txt 2>&1 | tee $C/01_pip_install.txt   # se la riga python==3.13 dà errore, toglila
uname -a > $C/02_sistema.txt; python --version >> $C/02_sistema.txt
pip freeze > $C/03_pip_freeze.txt
date > inizio.txt
```
Il file `inizio.txt` serve a `confronta.py` per sapere quali file sono stati rifatti.

## 4. Controllare gli hash dei file preregistrati
```
( cd preregistration && sha256sum -c SHA256SUMS.txt
  cd ../preregistration_v2 && sha256sum -c SHA256SUMS.txt
  cd risultati && sha256sum -c SHA256SUMS_risultati.txt
  cd ../../preregistration_v3 && sha256sum -c SHA256SUMS.txt ) 2>&1 | tee $C/04_hash_file.txt
```
Tutti OK, tranne 3 file in preregistration_v3: le tabelle `data/features_v3_*.csv`, dove i nomi degli sviluppatori sono stati sostituiti da codici. È normale e lo spiega il README della cartella.

## 5. Test preregistrato 1 (Moodle e MariaDB)
```
python3 preregistration/run_confirmatory.py 2>&1 | tee $C/05_test1.txt
```
Atteso (IC 90%): Moodle H1 −0,024 (−0,095; 0,026), MariaDB H1 0,023 (−0,038; 0,084); H2 Moodle −0,004, MariaDB −0,008.

## 6. Test preregistrato 2 (MariaDB, analizzatore C/C++ ufficiale)
```
python3 preregistration_v2/confermativo_v2.py data/features/mariadb_features.csv data/history/mariadb_history.csv \
  preregistration_v2/newsample_keys_mariadb.txt preregistration_v2/risultati/new_scan_mariadb_v2.jsonl \
  preregistration_v2/risultati/train_scan_mariadb_fresh.jsonl out_v2.json 2>&1 | tee $C/06_test2.txt
```
Atteso: 1.385 issue; H1-C 0,079 (−0,005; 0,156); H3-C equivalente.

## 7. Test preregistrato 3 (MOSIP, OpenLMIS, OpenMRS)
```
cd preregistration_v3
python3 code/confermativo_v3.py ../out_v3.json \
  mosip:data/features_v3_mosip.csv:scan/scan_mosip.jsonl \
  openlmis:data/features_v3_openlmis.csv:scan/scan_openlmis.jsonl \
  openmrs:data/features_v3_openmrs.csv:scan/scan_openmrs.jsonl 2>&1 | tee $C/07_test3.txt
python3 code/confermativo_v3.py ../out_v3_strict.json \
  mosip:data/features_v3_mosip.csv:results/sensitivity_strict_rerun_rule/scan_mosip_without_lots48_56.jsonl \
  openlmis:data/features_v3_openlmis.csv:scan/scan_openlmis.jsonl \
  openmrs:data/features_v3_openmrs.csv:scan/scan_openmrs.jsonl 2>&1 | tee $C/07_test3_mosip_regola_protocollo.txt
cd ..
```
Atteso, H1: MOSIP −0,018 (con le 449 issue rifatte, 2.380 issue) e −0,016 (regola del protocollo, 2.003 issue); OpenLMIS 0,041; OpenMRS −0,080.

## 8. Modelli principali (Tabelle 7-9 e Appendice A): il passo più lungo
```
( cd code && sh run_models.sh ) 2>&1 | tee $C/08_modelli.txt
cp code/log_*.txt $C/
```
Il comando non scrive quasi niente a schermo: è normale. Aspetta che torni il cursore.
Valori chiave (Tabella 8, M1 contro SQALE ricalibrato): circa −0,9 h (Moodle), −2,0 h (MariaDB), −3,4 h (Percona).

## 9. Analisi esplorative
```
sh exploratory/run_all.sh 2>&1 | tee $C/09_esplorative.txt
```

## 10. Collegamenti issue-commit e confronto automatico
```
python3 link_validation/manual_check/analyze_manual_check.py 2>&1 | tee $C/10_collegamenti.txt
python3 ~/riproduzione_sqale/confronta.py ~/riproduzione_sqale/originale/dade1987-sqale-effort-replication-* . \
  code/results_moodle.json=results/results_moodle.json \
  code/results_mariadb.json=results/results_mariadb.json \
  code/results_percona.json=results/results_percona.json \
  code/results_transfer.json=results/results_transfer.json \
  code/results_exploratory_moodle.json=results/results_exploratory_moodle.json \
  code/results_exploratory_mariadb.json=results/results_exploratory_mariadb.json \
  code/results_exploratory_percona.json=results/results_exploratory_percona.json \
  out_v2.json=preregistration_v2/risultati/risultati_confermativo_v2.json \
  out_v3.json=preregistration_v3/results/results_v3.json \
  out_v3_strict.json=preregistration_v3/results/sensitivity_strict_rerun_rule/results_strict.json \
  2>&1 | tee $C/11_confronto.txt
```
L'ultima riga dice quanti file sono stati confrontati e quanti hanno differenze. Nella prova fatta prima di mandarti la guida: 31 file confrontati, uno solo diverso (`results_transfer.json`, alla quinta cifra decimale, per un piccolo effetto casuale della libreria LightGBM). Piccole differenze come questa vanno solo annotate.

Facoltativo, a mano e senza AI: guarda i 5 casi difficili dei collegamenti, cioè MDL-76867 (giudicato parziale; commit mancante 0b54a57), MDEV-7850 (mancano aee03ea e 9b1ea69), MDEV-8919 (manca afbd28a) e PMM-2060 (mancano 23c0179 e 5e7cc2d). Per ognuno scrivi in `$C/12_casi_difficili.txt` se sei d'accordo che il commit appartiene alla correzione e perché.

## 11. Preparare il file da mandare
```
cp out_v2.json out_v3.json out_v3_strict.json code/results_*.json $C/
cp -r results/exploratory $C/esplorative_rifatte
date > $C/99_fine.txt
cd ~/riproduzione_sqale && zip -r riproduzione_gianluigi.zip consegna
```
Scrivi anche una breve relazione (`consegna/relazione.txt`, poi rifai lo zip) con: date, sistema, esito di ogni passo (uguale / diverso, con i valori), tempo impiegato, casi difficili, e se hai usato un'AI per scrivere il testo.
Manda a Davide **riproduzione_gianluigi.zip**.
