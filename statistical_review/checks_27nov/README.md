# Checks after the AI-assisted statistical review of 27 November 2026 (exploratory)

`review_27nov_ai_assisted_it.pdf` is the review (Italian). `analysis_plan.md` fixed every check below before it was run; its SHA-256 and time are in `analysis_plan.sha256`. Registered files and results are not modified. Details and tables: Online Appendix F.11.

| Point | Script | Output |
|---|---|---|
| 4. H1-2W of the fourth registration with B = 100,000 (registered and one-issue-per-project scans) | `scripts/p4_big.py` | `results/p4_*.json` |
| 6. Non-finite bootstrap replicates in the frozen scripts of registrations 2–4 | `scripts/p6_nan.py` (runs a frozen script unchanged) | `results/p6_*.json` |
| 3. Cluster concentration and leave-one-cluster-out | `scripts/p3_clusters.py` | `results/p3_clusters.json` |
| 5. Calibration simulation (type I error, power, coverage) | `scripts/p5_sim.py` | `results/p5_*.json` |
| 9. Relative MAE margin with resampled denominator | `scripts/p9_ratio_variant_v1..v4.py` (frozen scripts with only the H3 bootstrap statistic changed) | `results/p9_summary.json` |
| 8. Corrected independent reimplementation | `../../preregistration_v4/independent_checks/independent_v4_corrected.py` | `results/p8_*.json` |
| 7. Analytic two-way variance components | `scripts/p7_cgm.py` | `results/p7_cgm.json` |
| 2. Hashes against OSF | (OSF API, view-only links) | `results/p2_hashes.json` |

`scripts/common_v4.py` executes the data preparation of the frozen `preregistration_v4/confermativo_v4.py` itself, so samples and exclusions are identical. Run the scripts from `scripts/` with the package at `/home/user/sqale-effort-replication` or edit `R` in `common_v4.py`.
