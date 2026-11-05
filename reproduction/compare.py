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
