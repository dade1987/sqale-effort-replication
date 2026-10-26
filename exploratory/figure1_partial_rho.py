"""Figure 1: partial Spearman rho (hours, SQALE | size) across projects and phases, with the SESOI band."""
import json, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
lang = sys.argv[1] if len(sys.argv) > 1 else 'en'
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = f"{ROOT}/data"; OUT = f"{ROOT}/results/exploratory"
ex = json.load(open(f'{OUT}/size_collinearity.json'))
conf = {p: json.load(open(f'{ROOT}/results/confirmatory/confirmatory_{p}.json')) for p in ['moodle', 'mariadb']}
L = {'en': ('Exploratory, touched files (95% CI)', 'Confirmatory H1, touched files (90% CI)', 'Confirmatory H2, changed lines (90% CI)', 'Partial Spearman ρ (hours, SQALE | size)', 'SESOI ±0.10', 'Official C/C++ analyser, touched files (90% CI)'),
     'it': ('Esplorativo, file toccati (IC 95%)', 'Confermativo H1, file toccati (IC 90%)', 'Confermativo H2, righe modificate (IC 90%)', 'ρ parziale di Spearman (ore, SQALE | dimensione)', 'SESOI ±0,10', 'Analizzatore C/C++ ufficiale, file toccati (IC 90%)')}[lang]
rows = []
for p, name in [('moodle', 'Moodle'), ('mariadb', 'MariaDB'), ('percona', 'Percona')]:
    lo, hi = ex[p]['partial_test_ci95']; rows.append((f'{name} — {L[0]}', ex[p]['partial_test'], lo, hi, 'o'))
for h, lab, mk in [('H1', L[1], 's'), ('H2', L[2], 'D')]:
    for p, name in [('moodle', 'Moodle'), ('mariadb', 'MariaDB')]:
        r = conf[p][h]; rows.append((f'{name} — {lab}', r['partial_rho'], r['CI90'][0], r['CI90'][1], mk))
off = json.load(open(f'{OUT}/official_cxx_compare.json'))['all_issues_with_measures']
rows.append((f'MariaDB — {L[5]}', off['partial_rho_official'], off['partial_rho_official_ci90'][0], off['partial_rho_official_ci90'][1], '^'))
fig, ax = plt.subplots(figsize=(7.2, 3.7))
ax.axvspan(-0.10, 0.10, color='#dfe8f3', label=L[4]); ax.axvline(0, color='#555', lw=0.8)
for i, (lab, v, lo, hi, mk) in enumerate(rows[::-1]):
    ax.plot([lo, hi], [i, i], color='#1f3b63', lw=1.6); ax.plot(v, i, mk, color='#1f3b63', ms=6)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=8)
ax.set_xlabel(L[3], fontsize=9); ax.set_xlim(-0.2, 0.45); ax.legend(loc='lower right', fontsize=8, frameon=False)
for s in ['top', 'right']: ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(f'{OUT}/fig1_partial_rho_{lang}.png', dpi=200)
