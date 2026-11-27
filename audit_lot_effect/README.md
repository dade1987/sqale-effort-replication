# Lot-effect audit of the first and third preregistrations (exploratory sensitivity analysis)

Run 26–27 November 2026, after all registered results were known. It does **not** replace the registered results; the registered files were not modified.

## What was done

- Every issue scanned by the frozen scripts of the first registration (Moodle, MariaDB: hold-out **and** the exploratory sample used to train H3) and of the third registration (MOSIP, OpenLMIS, OpenMRS) was rescanned **alone, in its own SonarQube project**, with the same parent commit, the same SonarQube Community Build 26.9.0.129388, the same analysers and profiles (MariaDB: sonar-cxx 2.4.0-beta1 built from tag `cxx-2.4.0-beta.1`, cppcheck 2.13, profile TD-CXX; third registration: Java without bytecode, as registered), and the frozen scan scripts changed only in working folder and project key (`scripts/`).
- Pilot first: MariaDB 10/10 issues identical to the recorded values before the full run; 4 OpenLMIS issues rescanned alone twice gave identical values (isolated scans are deterministic).
- Isolated scan files were built by replacing each rescanned record in a copy of the registered file (`isolated_scans/`); the registered analysis scripts (`preregistration/confermativo.py`, `preregistration_v3/code/confermativo_v3.py`) were run unchanged on the original files (they reproduce the registered numbers exactly) and on the isolated files, with the same samples, exclusions, seeds, SESOI and decision rules.
- The second registration is excluded: it already used one SonarQube Cloud project per issue.

## Measurement agreement (`per_issue_comparison/`, one file per group)

| Group | Issues rescanned | Debt identical | Isolated lower / higher | Spearman | NCLOC identical | Changed-line debt identical |
|---|---|---|---|---|---|---|
| Moodle, 1st, hold-out | 859 | 93.8% | 52 / 1 | 0.999 | 100% | 99.7% |
| Moodle, 1st, H3 training sample | 1,735 | 90.1% | 170 / 2 | 0.999 | 100% | 98.8% |
| MariaDB, 1st, hold-out | 880 | 100% | 0 / 0 | 1.000 | 100% | 100% |
| MariaDB, 1st, H3 training sample | 1,719 | 100% | 0 / 0 | 1.000 | 100% | – |
| MOSIP, 3rd | 2,384 | 89.3% | 54 / 200 | 0.9996 | 100% | – |
| OpenLMIS, 3rd | 1,448 | 86.8% | 77 / 114 | 0.986 | 100% | – |
| OpenMRS, 3rd | 1,582 | 91.7% | 17 / 115 | 0.999 | 100% | – |

## Single table: registered vs isolated (90% CIs; verdicts by the registered rules)

| Group | Test | n | Registered | Isolated | Verdict registered → isolated |
|---|---|---|---|---|---|
| Moodle (1st) | H1 partial ρ | 851 | −0.024 (−0.095 to 0.026) | −0.018 (−0.089 to 0.034) | negligible → negligible |
| Moodle (1st) | H2 partial ρ | 822 | −0.004 (−0.066 to 0.063) | −0.008 (−0.071 to 0.059) | negligible → negligible |
| Moodle (1st) | H3 ΔMAE, % of MAE | 851 | (−0.02% to +0.04%) | (−0.03% to +0.06%) | equivalent → equivalent |
| MariaDB (1st) | H1 partial ρ | 862 | 0.023 (−0.038 to 0.084) | identical | negligible → negligible |
| MariaDB (1st) | H2 partial ρ | | −0.008 (−0.085 to 0.053) | identical | negligible → negligible |
| MariaDB (1st) | H3 ΔMAE, % of MAE | | (−0.36% to +0.10%) | identical | equivalent → equivalent |
| MOSIP (3rd) | H1, protocol-conforming sample (primary, Table 5c) | 2,003 | −0.016 (−0.067 to 0.035), TOST p 0.004 | −0.015 (−0.067 to 0.035), TOST p 0.004 | negligible → negligible |
| MOSIP (3rd) | H1, developer × module | 2,003 | (−0.094 to 0.067) | (−0.094 to 0.066) | negligible → negligible |
| MOSIP (3rd) | H3 ΔMAE, % of MAE | 1,002 | (−0.04% to +0.76%) | (−0.03% to +0.75%) | equivalent → equivalent |
| MOSIP (3rd) | sensitivity: H1 with the 449 re-run issues | 2,380 | −0.018 (−0.063 to 0.026), TOST p 0.002 | −0.017 (−0.062 to 0.028), TOST p 0.002 | negligible → negligible |
| OpenLMIS (3rd) | H1 partial ρ, developer bootstrap | 1,344 | 0.041 (−0.046 to 0.133), TOST p 0.140 | 0.033 (−0.051 to 0.118), TOST p 0.097 | inconclusive → inconclusive |
| OpenLMIS (3rd) | H1, developer × module | 1,344 | (−0.079 to 0.159), TOST p 0.197 | (−0.083 to 0.146), TOST p 0.159 | inconclusive → inconclusive |
| OpenLMIS (3rd) | H3 ΔMAE, % of MAE | 672 | +0.30 h (+0.29% to +3.50%) | +0.24 h (+0.07% to +3.00%) | inconclusive → inconclusive |
| OpenMRS (3rd) | H1 partial ρ, developer bootstrap | 1,582 | −0.081 (−0.139 to −0.015), TOST p 0.291 | −0.080 (−0.138 to −0.014), TOST p 0.281 | inconclusive → inconclusive |
| OpenMRS (3rd) | H1, developer × module | 1,582 | (−0.174 to 0.018), TOST p 0.363 | (−0.172 to 0.019), TOST p 0.357 | inconclusive → inconclusive |
| OpenMRS (3rd) | H3 ΔMAE, % of MAE | 791 | (−1.56% to +0.23%) | (−1.52% to +0.22%) | equivalent → equivalent |
| 3rd, family | Holm-adjusted TOST p (MOSIP / OpenLMIS / OpenMRS) | | 0.011 / 0.279 / 0.291 (primary MOSIP sample) | 0.011 / 0.193 / 0.281 | not all equivalent → not all equivalent |
| 3rd, pooled (secondary) | random-effects ρ | | −0.026 (−0.076 to 0.025) | −0.026 (−0.074 to 0.022) | – |
| 1st, family | Holm over 4 one-sided p (ρ > 0) | | all 1 | all 1 | no H1/H2 rejected → none rejected |

MOSIP is reported on the protocol-conforming sample (without the 449 issues of the nine batches run a third time; `results_strict.json`, scan file built from `preregistration_v3/results/sensitivity_strict_rerun_rule/scan_mosip_without_lots48_56.jsonl`) as primary, and with them (`results_v3.json`) as sensitivity, as in the article.

Secondary analyses of the third registration: every verdict unchanged except OpenLMIS "bugs only" (n small), inconclusive → negligible.

## Conclusion

The lot effect is real for the PHP (Moodle) and Java/JavaScript (third registration) analysers, absent for sonar-cxx/cppcheck on MariaDB, never affects size, and changes 6–13% of debt values, mostly by small amounts. It moves the estimates by at most 0.008 in ρ and changes no primary verdict, no Holm decision and no familywise conclusion in either registration.

Files: `per_issue_comparison/` (one CSV per group with issue_key, sqale_original, sqale_isolated, diff_percent, ncloc_original, ncloc_isolated and changed-line debt; `summary.json`), `results/` (outputs of the registered analysis scripts on the registered files, `*_registered`, and on the isolated files, `*_isolated`), `isolated_scans/` (isolated scan files in the registered format, and the raw per-issue records `raw_*.jsonl`), `scripts/` (scan workers, comparison and file-building scripts; they contain the absolute paths of the machine where they ran and read the SonarQube token from a local file, which is not included).

To rerun the analyses on the isolated values: `python3 preregistration/confermativo.py data/features/<p>_features.csv data/history/<p>_history.csv <p> audit_lot_effect/isolated_scans/first/holdout_scan_<p>.jsonl audit_lot_effect/isolated_scans/first/exploratory_sample_scan_<p>.jsonl` (first registration) and, from `preregistration_v3/`, `python3 code/confermativo_v3.py out.json mosip:data/features_v3_mosip.csv:../audit_lot_effect/isolated_scans/third/scan_mosip_without_lots48_56.jsonl openlmis:data/features_v3_openlmis.csv:../audit_lot_effect/isolated_scans/third/scan_openlmis.jsonl openmrs:data/features_v3_openmrs.csv:../audit_lot_effect/isolated_scans/third/scan_openmrs.jsonl` (third registration, primary MOSIP sample; use `scan_mosip.jsonl` for the sensitivity sample).
