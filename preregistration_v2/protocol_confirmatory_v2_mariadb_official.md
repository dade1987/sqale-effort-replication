# Preregistration 2: Does SQALE debt from SonarSource's C/C++ analyser predict human-logged issue effort in MariaDB beyond code size?

Version 2, frozen on 31 October 2026 for registration on OSF, approved by the author. Written before any SQALE measurement of the new sample described below. It complements the first registration (https://osf.io/ts9n6, 24 October 2026), which it does not change.

## 1 Why a second registration

The first registration tested MariaDB with the open-source sonar-cxx analyser, and its verdict was "practically negligible". Practitioners mostly use SonarSource's own C/C++ analyser (CFamily). After the first test, as an exploratory check, we measured the same 862 MariaDB hold-out issues with CFamily on SonarQube Cloud. On the 821 measured issues, the partial Spearman ρ of hours with SQALE given lines of code was 0.09 (90% CI 0.01–0.18): positive, of uncertain size. That check was not preregistered, and its result is known. This protocol defines a confirmatory test with CFamily on MariaDB issues whose CFamily debt has never been measured.

**What has been seen.**

- CFamily SQALE and hours on the 862 issues of the first MariaDB hold-out (`holdout_keys_mariadb.txt`) and on the 200 issues analysed earlier (a subset of them).
- sonar-cxx SQALE on the earlier exploratory MariaDB sample (about 2,000 issues) and on the first hold-out.
- The logged hours and the non-SQALE features of all test-period issues, which were used in the model evaluation (RQ4).

**What is unseen.** The pool of the first registration held 2,730 MariaDB issues fixed from 1 January 2023 and not in the earlier SQALE sample. 1,000 of them formed the first hold-out. The remaining 1,730 issues form the new sample (all with logged hours > 0). The first hold-out is reproduced exactly from the pool with the first registration's seed, so the split can be checked. No SonarQube analysis, of any analyser, has been run on them. The relationship between their SQALE debt and their hours is unseen.

| File | SHA-256 |
|---|---|
| `newsample_keys_mariadb.txt` | cf92bddd8c2065826eec5d7eeedbf419e9fe46cee58c82555b1fd6cc49e892c7 |
| `confermativo_v2.py` | f07c8435b2d5f24736734793f109ce00352388d8b7699260b495b9df06f48a4b |

The new sample is the whole remaining pool, not a random draw, so no seed is needed.

## 2 Construct

Unchanged from the first registration. If SQALE debt measured interest-relevant problems, then among issues touching code of the same size, issues touching more SQALE debt should take more logged hours. The outcome is the total hours people logged on the issue in Jira (team effort, self-reported). Claims are restricted to this outcome.

## 3 Measurements

- SonarQube Cloud, SonarSource C/C++ analyser (CFamily), default "Sonar way" profile, SonarScanner CLI 8.2.0.6438, with the configuration of the exploratory check (`cloudcxx/cloud_cxx_fresh.py`): CMake run at par to produce the compilation database, large plugins and unit tests off, system SSL (bundled as fallback), generated headers built, headers analysed through a translation unit that includes them; analysis cache, duplication detection and SCM data off.
- **One new SonarQube Cloud project per issue**, because reusing a project carried values over from the previous issue (Section 6.5 of the paper).
- For each issue, let **c1** be the earliest linked fixing commit and **par** its parent. **SQALE_files** is the sum of the file-level `sqale_index` over all C/C++ code files touched by the issue's linked commits, at par; **NCLOC_files** is the non-comment lines of the same files, as reported by the same analysis.
- The scanner version and the date of each analysis are logged. SonarQube Cloud updates its analysers without notice; we record the CFamily version reported by each analysis and report any change during the run. (The version was not recorded in the exploratory check, so we cannot say whether it differs.)

## 4 Hypotheses (confirmatory)

Same SESOI as the first registration: a partial Spearman ρ of 0.10, and a change of 2% in mean absolute error.

**H1-C.** The partial Spearman correlation between logged hours and SQALE_files, controlling for NCLOC_files, is positive.

**H3-C.** Two log-linear models of log(hours) are fitted on the 821 measured issues of the first hold-out (the only CFamily measurements available for training): one on log(1+NCLOC_files), one on log(1+NCLOC_files) and log(1+SQALE_files). On the new sample, the model with SQALE has a lower mean absolute error in hours.

The partial Spearman correlation is the Pearson correlation of the rank residuals, after a linear regression of each variable's ranks on the ranks of the control variable. H2 (debt on the changed lines) is not tested here.

## 5 Inference and decision rules

Unchanged from the first registration:

- 90% CIs from a bootstrap that resamples developers (5,000 replicates, seed 2026); the developer is the Jira assignee at the first fix commit, or the author of c1 when none is recorded.
- **H1-C:** supported, practically relevant (lower bound > 0.10); positive but of uncertain size (lower bound > 0 and interval includes 0.10); practically negligible (interval inside (−0.10, 0.10)); inconclusive (anything else). One-sided bootstrap p-value for ρ > 0, no multiplicity correction (one test).
- **H3-C:** SQALE helps (upper bound of ΔMAE below −2% of the lines-only MAE); equivalent (inside ±2%); inconclusive (anything else).

**Conclusion.** If H1-C is negligible and H3-C equivalent, we conclude that with SonarSource's analyser, too, MariaDB's SQALE debt carries no effort-relevant information beyond size. If H1-C is supported, we conclude that it does, at the measured size. If H1-C is positive but of uncertain size, we report that the association is above zero but that the study cannot tell whether it reaches 0.10.

## 6 Inclusion and exclusion

- Issues with logged hours > 0.
- At least one C/C++ code file present at par and NCLOC_files > 0.
- A scan that fails is re-run once in a new project. Issues that still fail, or for which the analyser measures none of the touched files, are reported as missing, with counts and with their median hours compared with the analysed issues.
- **Quality check before the full run:** the first 10 analysed issues are inspected by hand (project freshly created, NCLOC consistent with the files at par, no value equal to the previous issue's). Problems found there are fixed and the 10 issues re-run; the check and any fix are logged. Hours are not looked at during this check.

No other exclusions, transformations or outlier rules.

## 7 Sample size

Of the 1,730 issues, 1,475 touch a C/C++ file present at par (from git alone, without any analysis); with the 95% success rate of the exploratory check we expect about 1,400 analysable issues. With that number, the 90% CI half-width of ρ is about 0.04 without clustering, and wider with it. Honest limit: if the true ρ is close to 0.10, as the exploratory estimate suggests is possible, the result may be "positive but of uncertain size" even with this sample. No larger sample exists: this is all remaining MariaDB issues of the period.

## 8 Secondary analyses (not confirmatory)

- H1-C and H3-C on the new sample pooled with the 821 issues of the exploratory check (reported as partly seen); for the pooled H3-C, which has no separate training set, the error is estimated by 10-fold cross-validation.
- H1-C with intervals clustered by developer and by the first Jira component (two-way).
- H1-C restricted to issues with every touched file measured.
- H1-C with the hours logged by the assignee only.

## 9 Analysis code and deviations

The analysis script `confermativo_v2.py` was written and tested only on simulated data before registration (with no effect it gives "negligible" and "equivalent"; with a strong simulated effect it gives "supported" and "SQALE helps"; folder `test_simulated/`), and is then frozen; the protocol, the key list and the script are registered with their SHA-256 hashes. Any deviation is reported, with its reason, in the paper.

## 10 Timeline

1. The protocol is registered on OSF before any scan of the new sample.
2. The scan logs carry timestamps.
3. Results are computed once with the frozen script.
