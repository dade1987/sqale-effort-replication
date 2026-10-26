"""M1 / M0 vs SQALE from the official C/C++ analyser on the MariaDB sample (exploratory).
Official SQALE has no pre-2023 training data, so its recalibration is a 10-fold cross-validated log-linear fit on the
sample itself (favourable to SQALE). sonar-cxx SQALE is recalibrated as in the paper (pre-2023 exploratory issues)."""
import json, glob
import numpy as np, pandas as pd
rng = np.random.default_rng(2026)
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = f"{ROOT}/data"; OUT = f"{ROOT}/results/exploratory"
R = [json.loads(l) for f in sorted(glob.glob(f'{D}/official_cxx/cloud_w*.jsonl')) for l in open(f)]
cloud = pd.DataFrame([{k: v for k, v in r.items() if k != 'per_file'} for r in R]).drop_duplicates('key', keep='last')
cloud = cloud[cloud.get('error').isna() & (cloud.files_measured > 0)] if 'error' in cloud else cloud[cloud.files_measured > 0]
cxx = pd.read_json(f'{D}/confirmatory/holdout_scan_mariadb.jsonl', lines=True).drop_duplicates('key')[['key', 'sqale_min', 'ncloc']]
pred = pd.read_csv(f'{D}/predictions/mariadb_predictions.csv')
m1 = [c for c in pred.columns if c.startswith('M1 after')][0]; m0 = [c for c in pred.columns if c.startswith('M0 at')][0]
d = cloud.merge(cxx, on='key').merge(pred[['key', 'hours', 'assignee', m1, m0]], on='key').reset_index(drop=True)
d['dev'] = d.assignee.fillna('unknown')
y = d.hours.values
# recalibrated official SQALE, 10-fold CV
folds = rng.permutation(len(d)) % 10; rec = np.zeros(len(d))
X = np.c_[np.ones(len(d)), np.log1p(d.sqale_min_official.values)]
for f in range(10):
    tr, te = folds != f, folds == f
    b = np.linalg.lstsq(X[tr], np.log(y[tr]), rcond=None)[0]; rec[te] = np.exp(X[te] @ b)
d['official_recal_cv'] = rec
# sonar-cxx recalibrated the same way (same folds), for a like-for-like comparison
rec2 = np.zeros(len(d)); X2 = np.c_[np.ones(len(d)), np.log1p(d.sqale_min.values)]
for f in range(10):
    tr, te = folds != f, folds == f
    b2 = np.linalg.lstsq(X2[tr], np.log(y[tr]), rcond=None)[0]; rec2[te] = np.exp(X2[te] @ b2)
d['sonarcxx_recal_cv'] = rec2
# sonar-cxx recalibrated as in the paper: fit on pre-2023 exploratory MariaDB issues
s = pd.read_json(f'{D}/sqale/mariadb_sqale.jsonl', lines=True)
f = pd.read_csv(f'{D}/features/mariadb_features.csv', usecols=['key', 'hours', 'fix_date'])
tr = s.merge(f, on='key'); tr = tr[(tr.fix_date < '2023-01-01') & (tr.code_files_at_parent > 0)]
b = np.linalg.lstsq(np.c_[np.ones(len(tr)), np.log1p(tr.sqale_min)], np.log(tr.hours), rcond=None)[0]
d['sonarcxx_recal'] = np.exp(b[0] + b[1] * np.log1p(d.sqale_min.values))
d['official_raw'] = d.sqale_min_official / 60
P = {'official_raw': 'SQALE official, raw', 'official_recal_cv': 'SQALE official, recalibrated (CV)', 'sonarcxx_recal': 'SQALE sonar-cxx, recalibrated', 'sonarcxx_recal_cv': 'SQALE sonar-cxx, recalibrated (CV)',
     m0: 'M0', m1: 'M1'}
mae = {P[c]: round(float(np.mean(np.abs(d[c] - y))), 2) for c in P}
groups = {k: v.index.values for k, v in d.groupby('dev')}; ks = list(groups)
def dmae(a, b, B=5000):
    e = np.abs(d[a].values - y) - np.abs(d[b].values - y); obs = e.mean(); vals = []
    for _ in range(B):
        idx = np.concatenate([groups[k] for k in rng.choice(ks, len(ks))]); vals.append(e[idx].mean())
    vals = np.array(vals); p = min(1.0, 2 * min((vals >= 0).mean(), (vals <= 0).mean()))
    return {'dMAE_h': round(float(obs), 2), 'ci95': [round(float(v), 2) for v in np.percentile(vals, [2.5, 97.5])], 'p_boot': round(float(p), 4),
            'pct_of_baseline_MAE': round(float(obs / np.mean(np.abs(d[b].values - y)) * 100), 1)}
out = {'n': len(d), 'MAE_h': mae, 'median_hours': float(np.median(y)),
       'M1_vs_official_recal_cv': dmae(m1, 'official_recal_cv'), 'M0_vs_official_recal_cv': dmae(m0, 'official_recal_cv'),
       'M1_vs_official_raw': dmae(m1, 'official_raw'), 'M1_vs_sonarcxx_recal': dmae(m1, 'sonarcxx_recal'),
       'official_recal_cv_vs_sonarcxx_recal': dmae('official_recal_cv', 'sonarcxx_recal'),
       'official_recal_cv_vs_sonarcxx_recal_cv': dmae('official_recal_cv', 'sonarcxx_recal_cv'), 'M1_vs_sonarcxx_recal_cv': dmae(m1, 'sonarcxx_recal_cv')}
json.dump(out, open(f'{OUT}/official_cxx_models.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
