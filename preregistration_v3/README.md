# Third preregistration: three new projects (MOSIP, OpenLMIS, OpenMRS)

Registered on OSF on 3 November 2026 at 13:06:54 UTC, before any SonarQube analysis of the sample
(view-only link: https://osf.io/q39g8/overview?view_only=fcee5ffc6919429a8c1adcca2466f175).
The registration holds one archive, `preregistrazione_nuovi_progetti_osf.zip`, SHA-256
`04fb8ca0b2cc7f20685f622ea59b5b09b7d3bd4be4bce6c8b71c367088b4e830` (248,970 bytes). Its files are the ones in this folder.
Every file except the three feature tables is identical to the registered one and matches `SHA256SUMS.txt` (`sha256sum -c SHA256SUMS.txt`).

**Personal data.** In the registered feature tables the `dev` column holds Jira account ids or hashed commit emails.
In `data/features_v3_<project>.csv` it is replaced by pseudonyms (`dev_` + 10 hex digits, salted hash; salt not distributed).
That is why those three files do not match their registered hashes.
The mapping is one to one and keeps the order of first appearance, so the frozen script gives the same output: we re-ran it on these files and `results/results_v3.json` came out identical.

## Contents

| Path | What it holds |
|---|---|
| `protocol_confirmatory_v3_new_projects.md` | The registered protocol |
| `code/` | Frozen scripts: linking (`link_multi.py`), data checks, features, scan (`scan_v3.py`), analysis (`confermativo_v3.py`) |
| `data/` | Keys of the sample, feature tables (pseudonymised), issue-commit links with changed files (`<project>_links.jsonl.gz`) |
| `pilot/` | Pipeline test on 36 commits not linked to sample issues (before registration) |
| `test_simulated/` | Test of the frozen script on simulated data (no effect / strong effect) |
| `scan/` | SQALE and NCLOC per issue (SonarQube Community Build 26.9, SonarSource Java/JS/TS analysers, default profiles) |
| `results/` | `results_v3.json` (single run of the frozen script) and `README.md` with the verdicts; `sensitivity_strict_rerun_rule/` (449 re-run MOSIP issues treated as missing); `exploratory_without_test_files/` (not preregistered) |
| `link_check/` | The human rater's verdicts on 90 random links (30 per project) |
| `incidents/` | First-10 quality check; the MOSIP lots that failed because of SonarQube's disk watermark |

## Reproduce

```
python3 code/confermativo_v3.py out.json \
  mosip:data/features_v3_mosip.csv:scan/scan_mosip.jsonl \
  openlmis:data/features_v3_openlmis.csv:scan/scan_openlmis.jsonl \
  openmrs:data/features_v3_openmrs.csv:scan/scan_openmrs.jsonl
```

Re-scanning needs the repositories of the three GitHub organisations and a local SonarQube 26.9:
`code/scan_v3.py <repos_dir> <repo_prefix> data/<project>_links.jsonl data/keys_v3_<project>.txt <lot> <n_lots> <out.jsonl>`, with lots of 50 issues
(57 for MOSIP, 37 for OpenLMIS and 38 for OpenMRS).
`results/exploratory_without_test_files/refetch_without_tests.py` reads per-file measures from those stored analyses.
