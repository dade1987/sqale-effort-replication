# Analysis plan: checks requested by the statistical review of 27 November 2026

Written on 27 November 2026, before any of the computations below was run. All analyses are exploratory and post hoc; the registered results and files are kept unchanged. The SHA-256 of this file is recorded in the results folder before the runs start.

## Point 4. Fourth registration, H1-2W with a large number of replicates

- Statistic, sample, exclusions, interval type (two-way developer × first component pigeonhole bootstrap, 90% percentile interval), SESOI (±0.10) and decision rule exactly as in `preregistration_v4/confermativo_v4.py`; the data preparation is executed from the frozen script itself.
- B = 100,000 replicates, seed 20261127, generated as 20 consecutive blocks of 5,000 from that one generator.
- Run on (a) the registered scan file and (b) the one-issue-per-project scan file (`independent_checks/one_issue_per_project/single_all.jsonl`).
- Reported: lower and upper 90% bounds, TOST p (with the +1/B term of the frozen script), verdict; Monte Carlo standard error of the lower bound and of the TOST p from the 20 block estimates (batch means) and, for the bound, also from the binomial order-statistic interval.
- Both results are reported whatever the verdicts. No other seed and no other B is run for this point.

## Point 6. Invalid bootstrap replicates

- For every bootstrap test of the second, third and fourth registrations (primary and secondary), re-run with the registered seed and B and count replicates whose statistic is NaN or infinite. If any exist, the p-values are recomputed with valid replicates only in the denominator and reported next to the registered ones.

## Point 3. Cluster concentration and influence

- Fourth registration, H1-2W: share of issues and of hours in the largest 1, 5 and 10 developers and components; effective number of clusters (1/Σp²).
- Leave-one-cluster-out: H1-2W re-estimated without each of the 5 largest developers and each of the 5 largest components in turn (B = 5,000, seed 2026, as registered).

## Point 5. Calibration by simulation on the observed dependence structure

- Fourth registration sample (7,080 issues, same developers, components and NCLOC). Hours are replaced by simulated outcomes whose rank residual (given NCLOC) has partial correlation ρ with the observed SQALE rank residual, plus developer and component random effects with the variance shares estimated from the observed hour residuals (ANOVA-type estimates), and noise.
- True ρ ∈ {−0.10, 0, +0.10}; 500 simulated data sets per value (seeds 1–500, 501–1000, 1001–1500); B = 2,000 replicates per data set.
- Reported: proportion of "practically negligible" verdicts (type I error at the two boundaries, nominal ≤ 5%; power at 0), coverage of the 90% interval for the realised partial ρ of each simulated data set, with binomial 95% intervals.
- Alternative margins: for every primary test of the four registrations, the verdict under SESOI 0.05 and 0.15 from the registered intervals (no new computation).

## Point 9. Relative MAE margin with the denominator resampled

- For each H3 analysis (first registration Moodle and MariaDB, second, third ×3, fourth), the same registered bootstrap is run on the ratio mean(d)/MAE_lines-only recomputed in each replicate; the 90% interval of the ratio is compared with ±2%. Same seed and B as registered. Model retraining inside the bootstrap is not done.

## Point 8. Independent reimplementation

- `independent_checks/independent_v4.py` is corrected to apply the decision rules in the registered order (equivalence before "positive") and to add the +1/B term to tail frequencies; it is re-run with its original seeds on both scan files. The original version is kept.

## Point 7. Analytic two-way interval

- The CGM secondary analysis is re-run reporting the three variance components and a flag if the combined variance is negative (truncated to zero). Text only otherwise.

## Point 2. Hashes

- The SHA-256 of every frozen script and protocol in the package is compared with the hashes listed in the OSF registrations (and the registered SHA256SUMS files), in one table. The wording on test files in the third registration is changed to "not fully conforming to the protocol text".
