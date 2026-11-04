# Results of preregistration 3 (OSF https://osf.io/q39g8, registered 3 Nov 2026 13:06 UTC)

The frozen script `code/confermativo_v3.py` (sha256 5ef65525…) was run once, on 3 Nov 2026 at about 15:20 UTC:
`results_v3.json` (console output in `run_output.txt`). Scans: `scan_<project>.jsonl` (SonarQube 26.9, in `../scan/`).

## Confirmatory results (90% developer-clustered CI)

| Project | Analysed / eligible | H1 partial rho (CI) | Verdict | Two-way dev x module CI | H3 dMAE h (CI as % of MAE) | H3 verdict |
|---|---|---|---|---|---|---|
| MOSIP | 2,380 / 2,384 | -0.018 (-0.063, 0.026) | negligible | (-0.089, 0.055) | +0.03 (-0.12%, +0.50%) | equivalent |
| OpenLMIS | 1,344 / 1,448 | 0.041 (-0.046, 0.133) | inconclusive | (-0.079, 0.159) | +0.30 (+0.29%, +3.50%) | inconclusive (SQALE slightly worse) |
| OpenMRS | 1,582 / 1,582 | -0.080 (-0.139, -0.015) | inconclusive (below zero) | (-0.174, 0.018) | -0.06 (-1.56%, +0.23%) | equivalent |

- Holm one-sided p for rho > 0: OpenLMIS 0.74, MOSIP 1, OpenMRS 1. No H1 is supported.
- Holm TOST: MOSIP 0.006, OpenLMIS 0.28, OpenMRS 0.29. Familywise equivalence is **not** reached.
- Pooled (secondary): rho = -0.026 (90% CI -0.075 to 0.022), tau^2 = 0.0012.
- Secondary analyses: bugs only, MOSIP -0.108 (-0.169, -0.041), OpenLMIS -0.002 (-0.087, 0.101), OpenMRS -0.071 (-0.163, 0.030), all inconclusive. With every touched file measured, the values are practically the same.
- Missing: MOSIP 4 (median 10.5 h against 9.5 h), OpenLMIS 104 (7.0 h against 14.5 h), OpenMRS 0.
- The positive control was not computed (it is listed as "if it can be computed").

Registered conclusion: the condition "all three negligible with familywise equivalence, and all H3 equivalent" is NOT met.
No project supports a positive association. MOSIP is negligible and equivalent. OpenMRS has a negative estimate whose
interval reaches below -0.10. OpenLMIS is inconclusive, and adding SQALE makes the error slightly worse (by up to 3.5%).

## Deviations and incidents (all reported)

1. 13:09 UTC: the first quality-check attempt failed because SonarQube was down after a container restart. No issue
   was measured. Logs: (not distributed: no measurement was made).
2. MOSIP lots 48-56 (449 issues) failed twice on the first pass. The cause was SonarQube's Elasticsearch disk
   watermark, a server problem rather than a problem with the code. After the fix the lots were run a third time,
   while the protocol allows one re-run only. Logs and the fix: `../incidents/mosip_lots_48_56.md`.
   Sensitivity with those 449 issues treated as missing, as the protocol rule would require: `sensitivity_strict_rerun_rule/`.
   MOSIP rho -0.016 (-0.067, 0.035), negligible; H3 equivalent; same conclusions.
3. Test files: the protocol says that files SonarQube classifies as tests are not measured. As in the paper's scans,
   no `sonar.tests` was set, so SonarQube classifies no file as a test, and test files are measured as code.
   Exploratory, not preregistered: with test-like paths left out (`exploratory_without_test_files/`):
   MOSIP -0.073 (-0.121, -0.020); OpenLMIS 0.127 (0.039, 0.177), positive of uncertain size, two-way CI (-0.011, 0.221);
   OpenMRS -0.103 (-0.167, -0.034). H3 equivalent in all three. Pooled -0.018 (-0.127, 0.091), tau^2 0.012.
4. Link check (90 links, rater Gianluigi Lucca Fabris): see `../link_check/README.md`.

## Further exploratory checks (3 Nov 2026, after a simulated review; not preregistered)

- `exploratory_wrong_links/`: simulation on the protocol-conforming MOSIP sample. A synthetic debt measure with a known
  partial rho (0.10 or 0.15) is built; 13% or 30% of the issues get the code measures of a random other issue; then the frozen
  H1 analysis is applied (200 runs, B = 400). True rho 0.10: mean estimate 0.101 / 0.088 / 0.068 with 0% / 13% / 30% wrong
  links, and the CI is above 0 in 100% / 98% / 93% of the runs. True rho 0.15: CI above 0 in every run.
- `exploratory_completeness/`: commits in the main repository that mention the issue key anywhere but are not linked by the
  strict rule. Issues with at least one such commit: MOSIP 14%, OpenLMIS 9%, OpenMRS 11% (upper bound).
- `exploratory_without_test_files/results_no_tests_strict_mosip.json`: test-like files left out, on the protocol-conforming
  MOSIP sample: -0.070 (-0.122 to -0.014), n = 1,787.
- In the paper, Table 5c reports MOSIP under the protocol's single re-run rule (`sensitivity_strict_rerun_rule/`), with the
  449 re-run issues counted as missing, as primary. `results_v3.json` keeps the single run that includes them.
- `exploratory_wrong_links/real/`: protocol-conforming MOSIP sample without the 3 analysed issues the rater judged wrong: -0.015 (-0.066 to 0.035), negligible.
- `exploratory_without_test_files/test_file_shares.py`: share of lines and of debt in test-like files (OpenLMIS: 62% of lines, 45% of debt).
