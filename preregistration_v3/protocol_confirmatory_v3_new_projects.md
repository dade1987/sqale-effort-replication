# Preregistration 3: Does SQALE debt predict human-logged issue effort beyond code size in three new projects (MOSIP, OpenLMIS, OpenMRS)?

Version 3, written on 3 November 2026 for registration on OSF, before any SQALE measurement of the issues described below. It complements the first registration (https://osf.io/ts9n6, 24 October 2026, Moodle and MariaDB) and the second (https://osf.io/gb3y9, 31 October 2026, MariaDB with SonarSource's C/C++ analyser), which it does not change.

## 1 Why a third registration

The first two registrations tested two projects (Moodle, MariaDB) whose data had also been used for exploration, and whose issues share most of their code. Reviewers asked for a confirmation on independent code, from other organisations, with SonarSource's own analysers and with a design that handles dependence between issues. This protocol tests the same question on three projects never used before in this study.

**What has been seen.** For the three projects: the Jira issues with logged time (keys, hours, dates, assignee, components, worklog authors of 200 random linked issues per project), the issue-commit links and the files changed by the linked commits. 36 random commits that are not linked to any sample issue (12 per project) were scanned once to test the scanning pipeline (`pilot/`); they are not part of the sample. A random sample of 90 links (30 per project) is being checked by a human rater (Section 6).

**What is unseen.** No SonarQube analysis of any sample issue has been run. The relationship between SQALE debt and hours is unseen in all three projects.

## 2 Projects and data

| Project | Domain | Jira (public) | Code (GitHub) | Linked issues with hours > 0 |
|---|---|---|---|---|
| MOSIP | digital identity platform | mosip.atlassian.net | github.com/mosip (40 repositories) | 2,849 |
| OpenLMIS | health supply-chain system | openlmis.atlassian.net | github.com/OpenLMIS (25 repositories) | 1,811 |
| OpenMRS | medical record system | openmrs.atlassian.net | github.com/openmrs (57 repositories) | 1,867 |

The three projects are developed by different organisations from Moodle, MariaDB and Percona. OpenLMIS and OpenMRS have had at least one contractor in common; we report this and analyse each project separately.

**Linking** (`code/link_multi.py`): the same rule as the paper (resolution Fixed or Done; merge commits excluded; the commit subject starts with exactly one issue key), with one adaptation fixed before any measurement: the key may be wrapped in [] or () at the start, as in MOSIP's convention "[MOS-123] ...". Commits are searched in all listed repositories; each issue keeps its main repository (the one with most touched files), as for Percona in the paper. The repository lists were compiled from the Jira project names, because the GitHub organisation listing was not available to us; repositories not listed are not searched.

**Data checks done** (`code/check_worklogs.py`, 200 random linked issues per project, seed 20261103): all had worklogs; no bot or automation account; 65% (OpenMRS), 72% (MOSIP) and 83% (OpenLMIS) of the issues had at least one worklog by an author of a linked commit (name match).

**Features fixed before measurement** (`code/prepare_features_v3.py` → `features_v3_<project>.csv`, hashed below): hours (Jira time spent), resolution date, developer (the Jira assignee; if none, the author of the earliest linked commit), module (main repository plus the most frequent of the first two directory levels of the touched files, after dropping layout and namespace segments), first Jira component, issue type.

## 3 Construct

Unchanged from the first registration. If SQALE debt measured interest-relevant problems, then among issues touching code of the same size, issues touching more SQALE debt should take more logged hours. The outcome is the total hours people logged on the issue in Jira (team effort, self-reported). Claims are restricted to this outcome.

## 4 Measurements

- SonarQube Community Build 26.9.0.129388 (local), SonarScanner CLI 8.2.0.6438, default "Sonar way" profiles of SonarSource's Java, JavaScript and TypeScript analysers (the versions bundled with that build).
- Code files: .java, .js, .jsx, .mjs, .ts, .tsx, except minified or bundled files and files under node_modules/, vendor/, bower_components/, dist/, build/ and target/.
- For each issue, let **c1** be the earliest linked fixing commit in the main repository and **par** its parent. **SQALE_files** is the sum of the file-level `sqale_index` over the code files touched by the issue's linked commits in the main repository that exist at par; **NCLOC_files** is the non-comment lines of the same files, from the same analysis. Files that SonarQube classifies as test files are not measured (as in the paper's scans).
- Java is analysed without compiled classes (`sonar.java.binaries` set to an empty folder), because building thousands of historical versions is not feasible. Rules that need bytecode or resolved types may therefore fire less often; this applies equally to all issues and is a limitation of the measurement, not of the comparison.
- One SonarQube project per lot of issues (each issue a separate folder), as in the paper (`code/scan_v3.py`). Duplication detection and SCM data off.

## 5 Hypotheses (confirmatory)

Same SESOI as the first registration: a partial Spearman ρ of 0.10, and a change of 2% in mean absolute error. Each project is tested separately.

**H1-p** (p = MOSIP, OpenLMIS, OpenMRS). The partial Spearman correlation between logged hours and SQALE_files, controlling for NCLOC_files, is positive.

**H3-p.** Within each project, issues are ordered by resolution date; two log-linear models of log(hours) are fitted on the first half: one on log(1+NCLOC_files), one on log(1+NCLOC_files) and log(1+SQALE_files). On the second half, the model with SQALE has a lower mean absolute error in hours.

H2 (debt on the changed lines) is not tested.

## 6 Inference and decision rules

- **Primary intervals:** 90% CIs from a bootstrap that resamples developers (5,000 replicates, seed 2026), as in the first two registrations.
- **H1-p verdicts:** supported, practically relevant (lower bound > 0.10); positive but of uncertain size (lower bound > 0 and interval includes 0.10); practically negligible (interval inside (−0.10, 0.10)); inconclusive (anything else). One-sided bootstrap p-value for ρ > 0 per project, Holm-corrected across the three projects.
- **Familywise equivalence:** the two one-sided test (TOST) p-value of each H1-p is the larger of P*(ρ ≤ −0.10) and P*(ρ ≥ 0.10) (+1/B) in the developer bootstrap; the three are Holm-corrected. We claim that SQALE adds no practically relevant information in all three projects only if all three Holm-adjusted TOST p-values are below 0.05.
- **Dependence through code:** each H1-p is also estimated with a two-way bootstrap that resamples developers and modules independently (pigeonhole bootstrap). We describe the equivalence as robust to dependence through code only if all three two-way intervals also lie inside ±0.10; otherwise we report that the equivalence holds only under developer clustering.
- **H3-p:** SQALE helps (upper bound of ΔMAE below −2% of the lines-only MAE); equivalent (inside ±2%); inconclusive (anything else). 90% CI from the developer bootstrap on the test half.

**Conclusions.** If all three H1-p are negligible with familywise equivalence and all H3-p are equivalent, we conclude that in these three projects SQALE debt carries no practically relevant effort information beyond size, and we say whether this holds under the two-way dependence check. If any H1-p is supported, we conclude that SQALE adds information in that project, at the measured size. Positive but uncertain or inconclusive results are reported as such, per project.

## 7 Inclusion and exclusion

- Linked issues with logged hours > 0 (keys in `keys_v3_<project>.txt`, hashed below).
- At least one code file present at par and NCLOC_files > 0 from the analysis.
- A lot whose analysis fails is re-run once. Issues that still fail, or with no measured file, are reported as missing, with counts and with their median hours compared with the analysed issues.
- **Quality check before the full run:** the first 10 analysed issues of each project are inspected by hand (files at par present, NCLOC consistent with the files, values not copied between issues). Problems found there are fixed and the 10 issues re-run; the check and any fix are logged. Hours are not looked at during this check.
- **Link check:** the human rater's verdicts on the 90 sampled links are reported per project (precision with Wilson 95% CI, missing commits). They do not change the sample.

No other exclusions, transformations or outlier rules.

## 8 Sample size

About 90–95% of the linked issues are expected to touch a code file present at par. With about 1,600–2,600 analysable issues per project, the unclustered 90% CI half-width of ρ is about 0.03–0.04; clustering widens it. With 66 developers (OpenLMIS), developer clustering may widen it more. In simulations with the real hours and developers and no effect, the script gives "negligible" in all three projects; with a strong simulated effect it gives "supported" and "SQALE helps" (`test_simulated/`). Honest limit: under the two-way bootstrap the intervals are wider, and a null result may not reach the dependence-robust reading.

## 9 Secondary analyses (not confirmatory)

- A random-effects pooled estimate of ρ across the three projects (Fisher z, bootstrap standard errors, DerSimonian-Laird).
- H1-p on bugs only; H1-p on issues with every touched code file measured.
- The positive control of the paper (commits to the touched files in the previous year, same model), if it can be computed from git alone.

## 10 Analysis code and deviations

`code/confermativo_v3.py` was written and tested only on simulated data before registration and is then frozen. The protocol, key lists, feature files and scripts are registered with their SHA-256 hashes (`SHA256SUMS.txt`). Any deviation is reported, with its reason, in the paper.

## 11 Timeline

1. The protocol is registered on OSF before any scan of the sample.
2. The scan logs carry timestamps.
3. Results are computed once with the frozen script.
