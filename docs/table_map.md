# Where each table and figure of the paper comes from

| Paper | Script | Result file | Keys |
|---|---|---|---|
| Table 1, dataset | `code/link_issues_commits.py`, `code/representativeness.py` | `data/links/<project>_links.jsonl.gz`, `results/representativeness.csv` | issue and hour counts per project |
| §3.3, hours logged by the assignee | `code/hours_shares.py` | `results/hours_shares.json` | `<project>` |
| Table 2, features of M1 | `code/features.py` | `data/features/<project>_features.csv` | columns |
| Table 3, SQALE on the exploratory samples | `code/model.py` | `results/results_<project>.json` | `sqale.all` (`SQALE raw`, `SQALE recalibrated`), `sqale.spearman_*`, `sqale.median_*` |
| Table 4, SQALE beyond lines of code | `code/model.py`, `exploratory/size_collinearity.py` | `results/results_<project>.json`, `results/exploratory/size_collinearity.json` | `sqale.beyond_size` |
| Table 5, preregistered tests | `preregistration/run_confirmatory.py` | `results/confirmatory/confirmatory_<project>.json`, `holm_4_tests.json` | H1–H3 |
| Table 6, secondary analyses | `exploratory/confirmatory_secondary.py`, `exploratory/debt_removed.py` | `results/confirmatory/secondary_results.json`, `results/exploratory/debt_removed.json` | |
| Figure 1, partial ρ | `exploratory/figure1_partial_rho.py` | `results/exploratory/fig1_partial_rho_{en,it}.png` | |
| Table 7 (and 7b, MdAE and within 2×), models on the full test sets | `code/model.py` | `results/results_<project>.json`, `data/predictions/<project>_predictions.csv` | `test` (MAE, MdAE, SA, within2x, spearman), `comparisons` |
| Table 8, models against recalibrated SQALE | `code/model.py` | `results/results_<project>.json` | `sqale.all` (`M1`, `M0`, `M1 without developer`, `… vs SQALE recalibrated`) |
| Table 9, learned models against experts | `code/model.py` | `results/results_mariadb.json`, `results/results_moodle.json` | `expert (first estimate)`, `expert (first estimate before work)`, `expert (final estimate)` |
| Online appendix A (errors, rolling origin, importance, sensitivity, transfer) | `code/model.py`, `code/transfer.py` | `results/results_<project>.json`, `results/results_transfer.json` | `error_analysis`, `rolling_origin_SA`, `importance_M0`, `importance_M1`, `sensitivity` |
| Online appendix B, model variants E1–E6 | `code/exploratory.py` | `results/results_exploratory_<project>.json` | `test`, `test_comparisons` |
| Online appendix Table B1, size classes | `exploratory/size_classes_cutpoints.py`, `exploratory/revision_checks.py` (intervals) | `results/exploratory/size_classes_cutpoints.json`, `results/exploratory/revision_checks.json` | |
| Online appendix Table B2, by issue type | `exploratory/by_issue_type.py` | `results/exploratory/by_issue_type.json` | |
| §6.5, nonlinear size models, timing of logged work, excluded issues | `exploratory/revision_checks.py` | `results/exploratory/revision_checks.json` | |
| §6.5, other quality and history measures | `exploratory/other_quality_measures.py` | `results/exploratory/other_quality_measures.json` | |
| Online appendix Table B3, other algorithms | `exploratory/other_algorithms.py` | `results/exploratory/other_algorithms_<project>.json` | `test`, `vs_lightgbm` |
| Table 10, official C/C++ analyser on the 187 measured issues of the first 200 (re-measured in fresh SonarQube Cloud projects) | `exploratory/official_cxx_compare.py`, `exploratory/official_cxx_models.py` | `results/exploratory/official_cxx_compare.json`, `official_cxx_models.json` | |
| §6.5 and Figure 1, official C/C++ analyser on all 862 MariaDB hold-out issues (821 measured) | `exploratory/official_cxx_full.py` | `results/exploratory/official_cxx_full.json` | `primary`, `carryover_fix`, `h3_style` |
| Online appendix Table C1, SQALE by rule type, size-neutral variant, debt ratio and A–E rating | `exploratory/sqale_rules_scan.py` (per-rule scan), `exploratory/rule_types.py` | `data/rules/`, `results/exploratory/rule_types_<project>.json` | `tests`, `effort_share`, `rating_counts` |
| §8, sensitivity: lenient developer rule and current titles | `code/model.py` with `DEV_AT=start_lenient` | `results/dev_at_start_current_titles/`, `data/predictions/dev_at_start_current_titles/` | |
| §8, sensitivity: developer at the first fix commit | `code/model.py` with `DEV_AT=commit` | `results/dev_at_first_commit/` | |
| §6.3, H2 in two parts | `exploratory/h2_two_part.py` | `results/exploratory/h2_two_part_<project>.json` | |
| §6.3 or §8, positive control for H1 and minimum detectable effect | `exploratory/positive_control_h1.py` | `results/exploratory/positive_control_h1_<project>.json` | |
| §3.2, link validation | `link_validation/manual_check/analyze_manual_check.py` | `link_validation/manual_check/results_manual_check.json` | |
| §2 and §8, SonarQube Cloud survey | `sonarcloud_survey/*.py` | `sonarcloud_survey/remediation_functions.json`, `active_use.jsonl` | |
