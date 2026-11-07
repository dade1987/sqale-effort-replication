# Selection bias of the compilable historical Java snapshots (exploratory, not preregistered)

Date: 7 November 2026. Inputs: `../exploratory_bytecode_historical/full_{openmrs,openlmis}.jsonl` (all attempted issues),
registered scans `../scan_*.jsonl`, issue features `features_v3_*.csv`. Scripts: `selection.py` (comparison and frozen
H1/H3 script on subsets), `ipw.py` (reweighting), `diag_failures.py` (failure reasons). Outputs in `out/`.
"Compiled" = build succeeded and both scans (without and with bytecode) succeeded; no issue built without being measured.

## Coverage
* OpenMRS: 805 of 1,264 attempted Java issues (64%). The 459 failures: 243 Android client (needs the Android SDK; 0/243),
  41 dependency or parent POM not resolvable, 13 compilation errors, 162 other Maven errors. Without the Android client: 805/1,021 (79%).
* OpenLMIS: 492 of 804 (61%). Failure reasons were not kept by the main run; a random re-run of 20 failed issues
  (`diag_openlmis.jsonl`, seed 20261107) shows 13/20 old Spring dependency-management Gradle plugin (2016 to early 2017
  snapshots, no Gradle version we have works), 5/20 JasperReports libraries only on `jaspersoft.artifactoryonline.com`
  (blocked by the environment's network policy), 2/20 other libraries missing from Maven Central.

## Compiled vs not compiled (`out/summary_selection.json`)
| | OpenMRS compiled / not | OpenLMIS compiled / not |
|---|---|---|
| n | 805 / 459 | 492 / 312 |
| median year of the parent commit | 2015 / 2016 (SMD -0.23) | 2018 / 2017 (SMD +0.43) |
| median hours | 4.5 / 6.0 (SMD log -0.18) | 12.0 / 19.5 (SMD log -0.46) |
| median NCLOC (registered) | 515 / 422 (SMD log +0.07) | 998 / 882 (SMD log +0.20) |
| median SQALE min (registered) | 114 / 64 (SMD log +0.32) | 25 / 30 (SMD log -0.03) |
| median files measured | 2 / 3 (SMD log -0.24) | 6 / 6 (SMD log +0.10) |
| issue type differs (chi-square p) | < 0.001 | < 0.001 |
| developers (compiled / not / all) | 203 / 78 / 244 | 32 / 30 / 44 |
| modules (compiled / not / all) | 138 / 73 / 182 | 64 / 59 / 96 |

Compile rate by year and repository is in the JSON. OpenLMIS: 2016 37/174, 2017 196/276, 2018 177/200; repository
`requisition` 124/304, `stockmanagement` 5/61. OpenMRS: `openmrs-core` 383/389, Android client 0/243.
The compiled OpenLMIS issues are therefore later, smaller in hours and partly from different repositories.

## Does selection change the registered association? (frozen script, registered measure, developer bootstrap)
| | all attempted | compiled | not compiled |
|---|---|---|---|
| OpenMRS H1 rho (CI90) | -0.108 (-0.168; -0.045) | -0.107 (-0.182; -0.023) | -0.014 (-0.104; 0.068) |
| OpenLMIS H1 rho (CI90) | 0.077 (0.020; 0.154) | 0.041 (-0.028; 0.130) | 0.043 (-0.038; 0.148) |

## Reweighting sensitivity (`out/summary_ipw.json`)
Logistic model of "compiled" on year, log hours, log NCLOC, log files, issue type and repository; weights 1/p trimmed at the
99th percentile; weighted partial Spearman; developer bootstrap with weights fixed.
* OpenMRS (effective n 672): balance improves on all four variables. Check on the registered measure: weighted -0.110,
  all attempted -0.108 (it works). With bytecode: unweighted -0.136 (-0.215; -0.044), weighted -0.153 (-0.229; -0.062).
* OpenLMIS (effective n 291): the check fails. Year balance gets worse (SMD 0.17 to 0.33) and the weighted registered
  estimate (0.186, CI -0.009; 0.393) moves away from the all-attempted value (0.077). The reweighting is not defensible here;
  we report it only to show that it was tried. With bytecode: unweighted 0.127 (0.034; 0.219), weighted 0.161 (-0.025; 0.325).

## Reading
* OpenMRS: selection is mostly by repository (no Android client) and slightly by year and size; reweighting recovers the
  all-attempted registered value, and the bytecode association stays negative after reweighting. The bytecode result
  can be read as applying to OpenMRS server-side issues, not to the Android client.
* OpenLMIS: the compiled issues differ clearly (later, fewer hours, few `requisition` 2016-17 and `stockmanagement`
  issues), and no defensible reweighting exists with these data. The 0.13 with bytecode must not be generalised to all
  OpenLMIS issues. The registered association is similar in compiled and not compiled issues (0.04 and 0.04), and both are
  lower than in all attempted issues (0.08), which shows that subsets of this project can move the estimate by about 0.04
  for reasons unrelated to bytecode.

Note: script paths refer to the authors machine; issue features (developers, modules) are in the pseudonymised `data/features_v3_*.csv`, so the per-issue CSV files with original identifiers are not included.
