# Preregistration: Does SQALE debt predict human-logged issue effort beyond code size? A confirmatory test on unseen issues

Version 1, 24 October 2026. Written before any SQALE measurement of the hold-out samples described below.

## 1 Background and what has already been seen

An exploratory study (manuscript v3) analysed SQALE debt on random samples of issues from Moodle (MDL) and MariaDB Server (MDEV). For each project it used 1,000 issues fixed before 2023 and about 1,000 fixed from 2023, 3,998 issues in total. In those samples:

- SQALE of the touched files added almost nothing to lines of code when predicting logged hours;
- the partial Spearman correlation of hours with SQALE, given lines of code, was 0.00 (Moodle) and 0.11 (MariaDB) on test issues.

These analyses were exploratory. The test period had been used by an earlier version, and the design was revised after seeing results. The present protocol defines a confirmatory test on issues whose SQALE debt has never been measured.

**What is unseen.** For each project we drew 1,000 issues at random (seed 20261024) from the test-period issues (fixed from 1 January 2023) that were not in the earlier SQALE sample. That pool holds 4,457 issues in Moodle and 2,730 in MariaDB. No SonarQube analysis of these issues has been run.

**What is not unseen.** Their logged hours and non-SQALE features were used in the earlier model evaluation (RQ3 of v3). The relationship between their SQALE debt and their hours is unseen.

Key lists:

| File | SHA-256 |
|---|---|
| `holdout_keys_moodle.txt` | 9aface42e8fb6f23aa76344775cadcf26a7e405903dbd49a89d75de102ae3c7a |
| `holdout_keys_mariadb.txt` | 771a0a825494596b2cdffc8748fa096fc85a3dd336b0aa9afeff32a97b27c68e |

Percona is excluded: all its issues were already analysed.

## 2 Construct

Technical debt **interest** is the extra effort that existing debt causes in later work. We cannot observe the counterfactual effort without the debt. We therefore test an observable implication: if SQALE debt measured interest-relevant problems, then among issues touching code of the same size, issues touching more SQALE debt should take more logged hours.

The outcome is the total hours people logged on the issue in Jira. This is team effort across the issue life cycle (development, review, integration, testing), self-reported. The claims are restricted to this outcome.

## 3 Measurements

All measurements use the same setup:

- SonarQube Community Build 26.9.0.129388;
- the "Sonar way" profiles (PHP, JavaScript) for Moodle;
- sonar-cxx 2.4.0-beta1 with cppcheck 2.13 and the profile `td_cxx_profile.xml` for MariaDB.

The scanning script is `sqale_lines.py`. For each issue, let **c1** be the earliest linked fixing commit and **par** its parent.

- **SQALE_files:** the sum of `sqale_index` over all code files touched by the issue's linked commits, at par. This is the same measure as in v3.
- **NCLOC_files:** non-comment lines of code of the same files.
- **SQALE_changed:** the remediation effort of open maintainability issues reported on c1's files at par whose primary line is one of the old-side lines changed by c1. These lines come from `git diff -U0 par c1`, and a pure insertion counts the line it follows.
- **LINES_changed:** the number of such old-side changed lines.
- **NCLOC_c1:** NCLOC of c1's files at par.
- **Removed debt (secondary):** SQALE of c1's files at par minus SQALE of the same files at c1.

## 4 Hypotheses (confirmatory)

Each hypothesis is tested separately in Moodle and in MariaDB. The smallest effect size of interest (SESOI) is a partial Spearman ρ of 0.10, and a change of 2% in mean absolute error.

**H1, debt in the touched files.** The partial Spearman correlation between logged hours and SQALE_files, controlling for NCLOC_files, is positive.

**H2, debt on the changed lines.** The partial Spearman correlation between logged hours and SQALE_changed, controlling for LINES_changed and NCLOC_c1, is positive.

**H3, predictive value.** Two log-linear models of log(hours) are fitted on the earlier sample's issues fixed before 2023: one on log(1+NCLOC_files), one on log(1+NCLOC_files) and log(1+SQALE_files). On the hold-out, the model with SQALE has a lower mean absolute error in hours.

The partial Spearman correlation is the Pearson correlation of the rank residuals, after a linear regression of each variable's ranks on the ranks of the control variables.

## 5 Inference and decision rules

**Uncertainty.** 90% confidence intervals from a bootstrap that resamples developers (5,000 replicates, seed 2026). The developer is the Jira assignee at the first fix commit, or the author of c1 when none is recorded.

**Rules for H1 and H2**, applied to the 90% CI of ρ:

- **Supported, practically relevant:** the lower bound is above 0.10.
- **Positive but of uncertain size:** the lower bound is above 0 and the interval includes 0.10.
- **Practically negligible:** the interval lies inside (−0.10, 0.10). This is an equivalence test by two one-sided tests at α = 0.05.
- **Inconclusive:** anything else.

The one-sided bootstrap p-values for ρ > 0 are corrected with Holm across the four tests (H1 and H2 in two projects).

**Rules for H3**, applied to the 90% CI of ΔMAE (model with SQALE minus model without):

- **SQALE helps:** the upper bound is below −2% of the lines-only MAE.
- **Equivalent:** the interval lies inside ±2%.
- **Inconclusive:** anything else.

**Conclusion of the study.**

- If H1 and H2 are practically negligible and H3 is equivalent in a project, we conclude that in that project SQALE debt does not carry effort-relevant information beyond size.
- If H1 or H2 is supported, we conclude that it does, at the measured size.

The MariaDB results are interpreted with the caveat that its C/C++ analysis does not use SonarSource's own analyser.

## 6 Inclusion and exclusion

- Issues with logged hours > 0.
- **H1 and H3:** at least one code file present at par and NCLOC_files > 0.
- **H2:** at least one of c1's code files present at par, LINES_changed > 0, and NCLOC_c1 > 0.

A SonarQube scan that fails is re-run once. Issues that still fail are reported as missing, with counts.

No other exclusions, transformations or outlier rules are applied.

## 7 Sample size

With about 850 analysable issues per project, the 90% CI half-width of ρ is about 0.06 without clustering, and wider with it. This is enough to tell 0 from 0.10 if the clustering is moderate. We did not choose a larger sample because of scanning time.

## 8 Secondary analyses (not confirmatory)

These are reported, but they do not decide the conclusion:

- removed debt against hours, controlling for LINES_changed;
- SQALE density (SQALE per line) against hours;
- H1–H3 with the hours logged by the assignee only;
- H1–H3 for bugs only;
- intervals from a bootstrap of calendar-month blocks;
- the same measures on the earlier sample of 3,998 issues.

## 9 Analysis code and deviations

The analysis script is `confermativo.py`. The protocol and the script are frozen together, with their SHA-256 hashes recorded at registration. Any deviation from this protocol will be reported, with its reason, in the paper.

## 10 Timeline

1. The protocol is registered (OSF) before the hold-out scans start.
2. The scan logs carry timestamps.
3. Results are computed once with the frozen script.
