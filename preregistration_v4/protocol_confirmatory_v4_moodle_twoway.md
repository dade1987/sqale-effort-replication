# Preregistration 4: Does SQALE debt carry information about human-logged issue effort in Moodle beyond code size, when issues that share developers or code components are treated as related?

Version 4, 24 November 2026, frozen for registration on OSF. Written before any SQALE measurement of the new sample described below. It complements the three earlier registrations (https://osf.io/ts9n6, 24 October 2026; https://osf.io/gb3y9, 31 October 2026; https://osf.io/q39g8, 3 November 2026), which it does not change.

## 1 Why a fourth registration

The first registration tested H1, the partial Spearman correlation of logged hours with the SQALE debt of the touched files given their size, with a 90% interval from a bootstrap that resamples developers. In Moodle the verdict was "practically negligible" (ρ = −0.024, 90% CI −0.095 to 0.026). After that test, as exploratory checks, we found that debt is a property of files and components, so issues that touch the same Jira component are not independent. With a two-way bootstrap that resamples developers and first Jira components, the Moodle interval became −0.15 to 0.08, "inconclusive". The two-way interval is the main limitation reported in the paper. Its width comes mostly from the small number of issues (851) and components (196) of the first hold-out.

This protocol tests H1 again on all Moodle issues of the dataset whose debt has never been measured, about eight times more issues, with the **two-way interval as the primary interval**.

**Why Moodle only.** We first planned the same test for MariaDB with SonarSource's C/C++ analyser. A simulation on the real MariaDB pool (Section 7) showed that, there, a true ρ of 0 would be called "negligible" in only 24% of runs: the MariaDB debt residual is strongly shared within components (intraclass correlation 0.47) and the pool has only 108 developers. A MariaDB test could therefore not reach a conclusion under two-way clustering, and we do not run it. This decision was taken from the simulation, before any new measurement.

**What has been seen.**

- SQALE and hours of the earlier exploratory Moodle sample (2,000 issues) and of the first Moodle hold-out (1,000 issues).
- All results of the three registrations and of the exploratory analyses in the paper, including the two-way and fixed-effect estimates.
- The logged hours and the non-SQALE features (size from Git, developer history, file history, components) of all Moodle issues of the dataset, which were used in the model evaluation (RQ4) and in the simulation of Section 7.
- On the new sample, the positive-control association of Section 5 (commits to the touched files in the previous year) has already been computed while testing the analysis script: partial ρ 0.23 (two-way 90% CI 0.17 to 0.29). It does not use SQALE.

**What is unseen.** The new sample is every Moodle issue of the dataset (`data/links/moodle_links.jsonl.gz`, 11,117 issues) that is not in the earlier SQALE sample (`data/sqale/moodle_sample_keys.txt`), the exploratory scan, or the first hold-out: **8,117 issues**, all with logged hours > 0, 8,105 of them resolved from 2018. No SonarQube analysis, of any analyser, has been run on them. The relationship between their SQALE debt and their hours is unseen. The sample is the whole remaining pool, not a random draw, so no seed is needed.

| File | SHA-256 |
|---|---|
| `newsample_keys_moodle.txt` | 2035497833507c065159daf4d05928a8dcaaaeb4a39bdd9debe0e45115d240ed |
| `confermativo_v4.py` | be85299e8118da95806bc7abd6031ea7a6d02fc6e12450c8e7abacf701479450 |
| `scan/run_v4.py` | 81c5f8d4403dfcd872d742c556bfc0d137eee9e2850f2ed2ed6601c771cbc10b |

## 2 Construct

Unchanged from the first registration. If SQALE debt measured problems that make work slower, then among issues that touch code of the same size, issues that touch more SQALE debt should take more logged hours. The outcome is the total hours people logged on the issue in Jira (team effort, self-reported). Claims are restricted to this outcome.

## 3 Measurements

Unchanged from the first registration: SonarQube Community Build 26.9.0.129388 on a local server, "Sonar way" profiles for PHP and JavaScript, SonarScanner CLI 8.2.0.6438, and the frozen scanning script `preregistration/sqale_lines.py` of the first registration (SHA-256 ba8f20ed277f5a3cea9259f9b302b32ede9821807dbfccd354b52e8f3e46aaeb), run by `scan/run_v4.py` in lots of 50 issues with one new SonarQube project per lot, deleted after reading. For each issue, let c1 be the earliest linked fixing commit and par its parent. **SQALE_files** is the sum of the file-level `sqale_index` over the PHP and JavaScript code files touched by the issue's linked commits, at par; **NCLOC_files** is their non-comment lines from the same analysis. The SonarQube version is recorded in every record.

**Quality check before the full run.** The first 10 issues of the key list are scanned and checked by hand (scan completed, NCLOC consistent with the files at par, no value equal to that of another issue), without looking at hours; the check is logged. Problems found there are fixed and the 10 issues re-run.

## 4 Hypothesis (confirmatory)

Same SESOI as the first registration: a partial Spearman ρ of 0.10.

**H1-2W.** The partial Spearman correlation between logged hours and SQALE_files, controlling for NCLOC_files, is positive.

The partial Spearman correlation is the Pearson correlation of the rank residuals, after a linear regression of each variable's ranks on the ranks of NCLOC_files (as in the first registration).

## 5 Inference and decision rules

**Primary interval.** 90% CI from a two-way cluster (pigeonhole) bootstrap: developers and first Jira components are resampled independently with replacement, and each issue is weighted by the product of its developer's and its component's draw counts (Owen 2007); 5,000 replicates, seed 2026. The developer is defined as in the first registration (the Jira assignee at the first fix commit, or the author of c1 when none is recorded). The component is the first component listed in Jira; issues with none form one group.

**Decision rules** (unchanged, applied to the primary interval):

- supported, practically relevant: lower bound > 0.10;
- positive but of uncertain size: lower bound > 0 and the interval includes 0.10;
- practically negligible: the interval lies inside (−0.10, 0.10); we also report the two one-sided test p-values from the same bootstrap;
- inconclusive: anything else.

One-sided bootstrap p-value for ρ > 0; there is one confirmatory test, so no multiplicity correction.

**Conclusion.** If H1-2W is practically negligible, we conclude that in Moodle the SQALE debt of the touched files carries no effort-relevant information beyond size above the SESOI, also when issues that share developers or components are treated as related. If, in addition, the secondary developer × code-module interval (Section 8) lies inside ±0.10, we describe the result as robust to both kinds of code grouping; otherwise we say that it holds for components but not for code modules. If H1-2W is supported or positive, we conclude that there is an association beyond size, at the measured size. If it is inconclusive, we report that this design cannot decide.

**Positive control (registered).** The same statistic and interval are computed with the number of commits to the touched files in the previous year (`h_commits_1y`) in place of SQALE_files. A lower bound above 0 shows that the design can detect a known association; this was already computed (Section 1) and is reported again from the frozen script.

## 6 Inclusion and exclusion

- Issues of the key list with logged hours > 0 (all of them).
- At least one PHP or JavaScript code file present at par and NCLOC_files > 0.
- Issues whose linked commits touch more than 2,000 files are excluded in advance (5 issues: mass renames and merges; MDL-67733, MDL-76932, MDL-78511, MDL-83424, MDL-89576). This was decided from the file counts in Git, without any SQALE value, because the frozen scanning script cannot pass so many paths to Git.
- A lot that fails is re-run key by key once; issues that still fail are reported as missing, with counts and with their median hours compared with the analysed issues.

No other exclusions, transformations or outlier rules.

## 7 Sample size and verdict probabilities

Of the 8,117 issues, 7,075 touch a code file with lines at par according to Git (no analysis), so we expect about 7,000 analysable issues, with 589 developers and 879 first components.

Before registration we simulated the verdicts on the real pool (`power_sim/power_pool.py`). Each run keeps the real hours, sizes (lines of the touched code files at par, from Git), developers and components of the pool issues; replaces SQALE by a synthetic measure with the size slope and residual spread of the already-scanned Moodle issues, and with a residual partly shared within components (intraclass correlation 0.09, estimated on 2,580 scanned issues); mixes in the hours rank residual to reach a target ρ; and applies the registered two-way bootstrap (1,000 replicates in the simulation) and decision rules. 200 runs per target:

| True ρ | negligible | positive, uncertain size | supported | inconclusive | mean CI width |
|---|---|---|---|---|---|
| 0.00 | 100% | 0% | 0% | 0% | 0.077 |
| 0.05 | 76.5% | 23.5% | 0% | 0% | 0.077 |
| 0.10 | 1.5% | 98% | 0.5% | 0% | 0.077 |

With a higher share of debt shared within components (intraclass correlation 0.25 or 0.47), a true ρ of 0 is still called negligible in 99% and 94% of 100 runs (CI widths 0.091 and 0.107). The same simulation on the MariaDB pool (4,481 issues, 108 developers, intraclass correlation 0.47 with SonarSource's analyser) gives 23.5% for a true ρ of 0 (Section 1).

The simulation assumes that the real debt behaves like the synthetic measure; real debt may be more clustered or skewed, which would widen the interval.

## 8 Secondary analyses (registered, not confirmatory)

- H1 with a two-way developer × code-module bootstrap; the module of an issue is the most frequent of the first two directory levels of its touched code files (ties: alphabetical).
- H1 with the developer-only bootstrap of the first registration.
- H1 with an analytic two-way cluster-robust standard error (Cameron, Gelbach and Miller 2011) on the influence function of the correlation.
- H1 with the hours logged by the assignee only.
- H1 on the issues resolved from 2023 (the period of the first hold-out).
- H2 (debt on the old lines changed by c1, given the number of those lines and the size of c1's files at par) with the two-way bootstrap.
- H3 by 10-fold cross-validation: the mean absolute error of a log-linear model on log(1+NCLOC_files) with and without log(1+SQALE_files), with a two-way bootstrap of the difference and the 2% margin of the first registration.

## 9 Analysis code and deviations

`confermativo_v4.py` was written and tested only on simulated data before registration (with no effect it gives "practically negligible" and "equivalent"; with a strong simulated effect it gives "supported" and "SQALE helps"; folder `test_simulated/`), and is then frozen. The protocol, the key list, the scanning wrapper and the analysis script are registered with their SHA-256 hashes. Any deviation is reported, with its reason, in the paper.

## 10 Timeline

1. The protocol is registered on OSF before any scan of the new sample.
2. The 10-issue quality check, then the full scan; scan records carry UTC timestamps.
3. Results are computed once with the frozen script.

## References

Cameron AC, Gelbach JB, Miller DL (2011) Robust inference with multiway clustering. Journal of Business & Economic Statistics 29(2):238–249.
Owen AB (2007) The pigeonhole bootstrap. The Annals of Applied Statistics 1(2):386–411.
