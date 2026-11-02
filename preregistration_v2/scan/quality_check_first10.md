# Quality check of the first 10 analysed issues (protocol 2, §6) — 31 October 2026, 22:15 UTC

Done by Claude on the scan records only; hours were not read. sha256sum -c of the frozen files OK before the scan (21:31 UTC).
Issues: MDEV-10653, -10862, -12008, -12305, -12404, -12668, -13594, -13915, -14432, -14959 (first 10 keys of the new sample with a C/C++ file at the parent).

| Check | Result |
|---|---|
| Project freshly created (one per issue) | 10/10 projects dade1987_mdb_v2_<KEY>, each with exactly 1 analysis (api/project_analyses) |
| Scan succeeded, files measured | 10/10 without errors; files measured = files at parent in 9/10 (MDEV-14959: 13 of 14, one file not in the build) |
| Statements parsed | 100% in 10/10 |
| NCLOC consistent with the files at the parent | ncloc / raw lines (git show at parent) = 0.60–0.73 in 10/10 |
| No value equal to the previous issue's | 10/10 (SQALE and NCLOC differ from the previous record) |
| Zero debt on large files | only headers (sp_instr.h, ha_partition.h, handler.h, item_subselect.h, mysqld.h, sp_head.h) and sql/unireg.cc, which was also 0 in every fresh project of the exploratory check; no carry-over possible (new project, single analysis) |
| CFamily version recorded | 10/10: 6.85.0.102562; SonarScanner CLI 8.2.0.6438 |

No problem found, no fix, no re-run. The full run of the remaining issues starts now (run_v2.sh rest, 3 workers).
