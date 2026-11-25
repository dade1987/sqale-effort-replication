# Fourth preregistration: Moodle with two-way clustering

Registered on OSF on 24 November 2026 at 14:30:59 UTC (https://osf.io/8fdc7, embargo until 1 June 2027; view-only link: https://osf.io/8fdc7/overview?view_only=b450691c631f4bc5b574e56b42ff7980), before any SonarQube analysis of the sample.
The protocol, key list, scan wrapper and analysis script are registered with their SHA-256 hashes; the files here match them (`sha256sum -c SHA256SUMS.txt`).
Paper: Sections 5.7 and 6.3 (Table 5d).

**Question.** H1-2W: is the partial Spearman correlation of logged hours with the SQALE debt of the touched files, given their size, positive,
with a 90% two-way (developer × first Jira component) pigeonhole bootstrap interval as the primary interval?
Sample: the 8,117 Moodle issues of the dataset whose debt had never been measured.

**Result (single run of the frozen script).** 7,080 issues analysed (589 developers, 878 components).
H1-2W ρ = −0.047, 90% CI −0.098 to 0.012: practically negligible (TOST p = 0.041).
Positive control (commits to the touched files in the previous year): 0.236 (0.176 to 0.290).
Secondary: developer × code module (−0.124 to 0.033) inconclusive, so by the registered rule the result holds for components but not for code modules;
H2 negligible; H3 equivalent. Full values in `results/results_v4.json`.

## Contents

| Path | What it holds |
|---|---|
| `protocol_confirmatory_v4_moodle_twoway.md` | The registered protocol |
| `newsample_keys_moodle.txt` | The 8,117 issue keys |
| `confermativo_v4.py` | Frozen analysis script |
| `scan/run_v4.py` | Frozen scan wrapper (runs `preregistration/sqale_lines.py` of the first registration in lots of 50) |
| `power_sim/` | Simulation of the verdict probabilities on the real Moodle and MariaDB pools, run before registration |
| `test_simulated/` | Test of the frozen script on simulated data (no effect / strong effect) |
| `scan_log/` | Hand check of the first 10 issues, before the full scan |
| `results/moodle_scan_v4.jsonl` | SQALE and NCLOC per issue (SonarQube Community Build 26.9.0.129388, Sonar way PHP/JS), with lot, attempt and UTC times |
| `results/scan_progress.log` | Lot-by-lot progress of the scan, including restarts |
| `results/results_v4.json`, `results/run_log.txt` | Output of the single run of the frozen script |

The scan wrapper did not skip the five issues excluded in advance (more than 2,000 files); two of them (MDL-67733, MDL-83424) made their lots fail,
so those lots were re-run issue by issue. The container restarted several times and the scan resumed from the saved issues; every repeated scan
output kept on disk (2,322 issue scans) was identical to the recorded value (paper, Section 6.3, "Deviations from the fourth protocol").

## Reproduce

From the package root:

```
python3 preregistration_v4/confermativo_v4.py . preregistration_v4/results/moodle_scan_v4.jsonl out.json
```

The paths written inside `scan/run_v4.py` and `power_sim/power_pool.py` are those of the machine that ran them; they are kept unchanged because the files are registered by hash.
