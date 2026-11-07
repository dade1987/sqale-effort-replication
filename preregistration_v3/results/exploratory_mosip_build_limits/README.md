# MOSIP: why the Java measures could not be repeated with compiled classes (exploratory, not preregistered)

Date: 7 November 2026. Same procedure as `../exploratory_bytecode_historical/` (parent of the earliest linked commit,
Maven with JDK 8/11/21, public Maven Central through the Google mirror; for `io.mosip` artifacts missing from Central,
the library is rebuilt from the same MOSIP repository at a commit where that exact version is declared, one level only).
No dependency version was ever replaced by a different one: a build either resolves the declared versions or fails.

## Two random samples of 10 issues

* **2019 pilot** (5 Nov, seed 20261105, random among the 2,197 eligible MOSIP issues; 1,819 of them were resolved in 2019):
  `pilot_2019_random10.jsonl`, log `pilot_2019_random10.log`. **1/10 compiled.**
* **2020+ check** (7 Nov, seed 20261107, random among the eligible issues resolved from 1 Jan 2020, about 300 issues):
  `check_2020plus_random10.jsonl`, log `check_2020plus_random10.log`, script `hist_bytecode_perfile.py`
  (`HB_MIN_RESOLVED=2020-01-01 python3 hist_bytecode_perfile.py mosip 10 20261107 out.jsonl`). **2/10 compiled.**

Per-issue reasons: `failures_table.md` (first missing or failing item copied from the Maven log stored in each record).

## What blocks the builds

1. **2019 snapshots (83% of the eligible issues):** the `io.mosip` libraries of that time (versions 0.8-0.11) were never
   published on Maven Central; Central starts at 1.0.5 (checked on 7 Nov 2026 through `maven-metadata.xml` of
   `kernel-core`, `kernel-parent`, `kernel-logger-logback`, `kernel-dataaccess-hibernate`, `kernel-cbeffutil-api`).
   Rebuilding them from history needs further unpublished libraries in a chain (e.g. kernel-parent), and one rebuild
   failed in its own tests. One module also needs `snuggletex` 1.2.2, which is on no public repository we can reach.
2. **2020+ snapshots:** most of them depend on `-SNAPSHOT` versions of other MOSIP libraries (e.g. `kernel-core:1.2.0-SNAPSHOT`,
   `kernel-idobjectvalidator:1.2.1-SNAPSHOT`, `kernel-authcodeflowproxy-api:1.3.0-SNAPSHOT`). Snapshots are not kept on
   Maven Central, and the state of a snapshot on a given day cannot be recovered from a version number.

## Decision

A buildable historical subsample is not obtainable without inventing dependencies (replacing the declared versions with
other ones) or without long, fragile rebuild chains of unpublished libraries. With 3/20 builds the compiled subset would
also be tiny and highly selected. MOSIP is therefore excluded from the bytecode analyses; for MOSIP the Java measures
remain those of the registered scans (Java analysed without compiled classes), and results with compiled classes must not
be generalised to MOSIP. The sensitivity to wrong or partial issue-commit links in MOSIP (8/100 wrong in the human check,
`../exploratory_wrong_links/`) is unchanged and kept.
