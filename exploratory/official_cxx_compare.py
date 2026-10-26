"""Official SonarQube Cloud C/C++ analyser (CFamily, real build configuration) vs sonar-cxx + cppcheck,
on a random sample of 200 MariaDB hold-out issues. Exploratory, not preregistered. Writes compare_official.json."""
import json, glob
import numpy as np, pandas as pd
from scipy.stats import rankdata, spearmanr
rng = np.random.default_rng(2026)
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = f"{ROOT}/data"; OUT = f"{ROOT}/results/exploratory"
R = [json.loads(l) for f in sorted(glob.glob(f'{D}/official_cxx/cloud_w*.jsonl')) for l in open(f)]
cloud = pd.DataFrame([{k: v for k, v in r.items() if k != 'per_file'} for r in R]).drop_duplicates('key', keep='last')
cxx = pd.read_json(f'{D}/confirmatory/holdout_scan_mariadb.jsonl', lines=True).drop_duplicates('key')[['key', 'sqale_min', 'ncloc', 'code_files_at_parent']]
feat = pd.read_csv(f'{D}/features/mariadb_features.csv', usecols=['key', 'hours', 'assignee', 'fix_author'])
d = cloud.merge(cxx, on='key').merge(feat, on='key')
d['dev'] = d.assignee.fillna(d.fix_author).fillna('unknown')
n_sample = len(cloud)
ok = d[d.get('error').isna() & (d.files_measured > 0)].copy() if 'error' in d else d[d.files_measured > 0].copy()
full = ok[ok.files_measured == ok.files_at_parent].copy()
def partial(h, s, n):
    r = [rankdata(x) for x in (h, s, n)]
    X = np.c_[np.ones(len(h)), r[2]]
    res = [y - X @ np.linalg.lstsq(X, y, rcond=None)[0] for y in r[:2]]
    return float(np.corrcoef(*res)[0, 1])
def boot(df, col, level=90, B=2000):
    g = {k: v.index.values for k, v in df.groupby('dev')}; ks = list(g); vals = []
    for _ in range(B):
        x = df.loc[np.concatenate([g[k] for k in rng.choice(ks, len(ks))])]
        vals.append(partial(x.hours.values, x[col].values, x.ncloc.values))
    a = (100 - level) / 2
    return [round(float(v), 3) for v in np.percentile(vals, [a, 100 - a])]
def block(x):
    x = x.reset_index(drop=True)
    ratio = (x.sqale_min_official + 1) / (x.sqale_min + 1)
    return {
        'n': len(x),
        'spearman_official_vs_sonarcxx': round(spearmanr(x.sqale_min_official, x.sqale_min)[0], 3),
        'median_sqale_h_official': round(x.sqale_min_official.median() / 60, 2), 'median_sqale_h_sonarcxx': round(x.sqale_min.median() / 60, 2),
        'median_ratio_official_over_sonarcxx': round(float(ratio.median()), 3), 'ratio_p10_p90': [round(float(v), 3) for v in ratio.quantile([.1, .9])],
        'median_hours_logged': round(x.hours.median(), 2),
        'spearman_official_vs_ncloc': round(spearmanr(x.sqale_min_official, x.ncloc)[0], 3),
        'spearman_sonarcxx_vs_ncloc': round(spearmanr(x.sqale_min, x.ncloc)[0], 3),
        'mae_raw_h_official': round(float(np.mean(np.abs(x.sqale_min_official / 60 - x.hours))), 2),
        'mae_raw_h_sonarcxx': round(float(np.mean(np.abs(x.sqale_min / 60 - x.hours))), 2),
        'partial_rho_official': round(partial(x.hours.values, x.sqale_min_official.values, x.ncloc.values), 3), 'partial_rho_official_ci90': boot(x, 'sqale_min_official'),
        'partial_rho_sonarcxx_same_issues': round(partial(x.hours.values, x.sqale_min.values, x.ncloc.values), 3), 'partial_rho_sonarcxx_ci90': boot(x, 'sqale_min'),
    }
out = {'n_sample': n_sample, 'n_cmake_or_scan_error': int(d.get('error').notna().sum()) if 'error' in d else 0,
       'n_with_measures': len(ok), 'n_all_files_measured': len(full),
       'median_stmt_parsed_pct': float(ok.stmt_parsed_pct.median()),
       'all_issues_with_measures': block(ok), 'issues_all_files_measured': block(full)}
json.dump(out, open(f'{OUT}/official_cxx_compare.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
