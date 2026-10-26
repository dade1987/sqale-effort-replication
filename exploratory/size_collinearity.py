"""SQALE vs code size: rank correlation, and partial rho (hours, SQALE | ncloc) with developer-clustered bootstrap CIs.
Exploratory, for the EMSE revision. Writes size_collinearity.json."""
import json, sys
import numpy as np, pandas as pd
from scipy.stats import rankdata, spearmanr
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = f"{ROOT}/data"; OUT = f"{ROOT}/results/exploratory"
TEST = {'moodle': '2023-01-01', 'mariadb': '2023-01-01', 'percona': '2021-01-01'}
rng = np.random.default_rng(2026)

def partial(h, s, n):
    r = [rankdata(x) for x in (h, s, n)]
    X = np.c_[np.ones(len(h)), r[2]]
    res = [y - X @ np.linalg.lstsq(X, y, rcond=None)[0] for y in r[:2]]
    return np.corrcoef(*res)[0, 1]

def boot(df, B=2000):
    groups = {k: g.index.values for k, g in df.groupby('dev')}
    keys = list(groups); vals = []
    for _ in range(B):
        idx = np.concatenate([groups[k] for k in rng.choice(keys, len(keys))])
        d = df.loc[idx]
        vals.append(partial(d.hours.values, d.sqale.values, d.ncloc.values))
    return np.percentile(vals, [2.5, 97.5]).round(3).tolist()

out = {}
for p in TEST:
    s = pd.read_json(f'{D}/sqale/{p}_sqale.jsonl', lines=True)
    f = pd.read_csv(f'{D}/features/{p}_features.csv', usecols=['key', 'hours', 'fix_date', 'assignee', 'fix_author'])
    d = s.merge(f, on='key')
    d = d[(d.code_files_at_parent > 0) & (d.ncloc > 0)].copy()
    d['dev'] = d.assignee.fillna(d.fix_author).fillna('unknown')
    d = d.reset_index(drop=True)
    t = d[d.fix_date >= TEST[p]].reset_index(drop=True)
    out[p] = {
        'n_all': len(d), 'n_test': len(t),
        'rho_sqale_ncloc_all': round(spearmanr(d.sqale_min, d.ncloc)[0], 3),
        'rho_sqale_ncloc_test': round(spearmanr(t.sqale_min, t.ncloc)[0], 3),
        'rho_hours_ncloc_test': round(spearmanr(t.hours, t.ncloc)[0], 3),
        'rho_hours_sqale_test': round(spearmanr(t.hours, t.sqale_min)[0], 3),
        'partial_test': round(partial(t.hours.values, t.sqale_min.values, t.ncloc.values), 3),
        'partial_test_ci95': boot(t.rename(columns={'sqale_min': 'sqale'})),
    }
for p in ['moodle', 'mariadb']:
    h = pd.read_json(f'{D}/confirmatory/holdout_scan_{p}.jsonl', lines=True)
    h = h[(h.code_files_at_parent > 0) & (h.ncloc > 0)]
    out[p]['rho_sqale_ncloc_holdout'] = round(spearmanr(h.sqale_min, h.ncloc)[0], 3)
    out[p]['n_holdout'] = len(h)
json.dump(out, open(f'{OUT}/size_collinearity.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
