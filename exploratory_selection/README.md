# Included and excluded issues (Section 8, Table 11)

Exploratory and post hoc: added on 23 November 2026, after an external methodological review of the draft, when all main results were known.

It compares two pairs of groups on traits that can be observed for every issue:

- **(a) With vs without logged hours.** Every fixed MDL (Moodle) and MDEV (MariaDB) issue resolved from 1 January 2018, with or without logged time, linked to commits with the paper's rule (subject starts with exactly one key, no merges, all branches, no renames).
- **(b) Existing code vs excluded.** Issues of the SQALE samples (`data/sqale/`; Percona: test period from 2021) that change code present at the parent commit, vs those excluded (`code_files_at_parent = 0`).

Effect sizes are standardised mean differences (SMD, on log(1 + x) for counts) and Cliff's delta. `reweight.py` reweights the analysed SQALE-sample issues by the inverse of their estimated probability of having logged hours (logistic model on the traits of Table 11) and recomputes the partial Spearman ρ of hours with SQALE given NCLOC.

| File | What it does |
|---|---|
| `download_fixed_issues.py` | Downloads all fixed issues from the public Jira (keeps only key, logged seconds, dates, type, priority, number of components and of comments; no names) |
| `git_stats.py` | Per-issue commits, files, new files and changed lines from a clone of the repository |
| `compare.py` | Table 11 (`results/A_*.csv`, `results/B_*.csv`, `results/link_rates.json`) |
| `reweight.py` | The reweighting check (`results/reweight.json`) |
| `data/` | The downloaded issues (`<project>_fixed_2018_all.jsonl.gz`, 23 November 2026 snapshot) and the Git statistics (`<project>_git_stats.jsonl.gz`) |

Run from the repository root (needs only the libraries in `requirements.txt`):

```
python3 exploratory_selection/compare.py
python3 exploratory_selection/reweight.py
```

To rebuild the inputs:

```
python3 exploratory_selection/download_fixed_issues.py https://moodle.atlassian.net 1 'project = MDL AND resolution = Fixed AND resolved >= "2018-01-01" ORDER BY key' moodle_all.jsonl
python3 exploratory_selection/download_fixed_issues.py https://jira.mariadb.org 0 'project = MDEV AND resolution = Fixed AND resolved >= "2018-01-01" ORDER BY key' mariadb_all.jsonl
python3 exploratory_selection/git_stats.py <moodle clone> 'MDL-\d+' moodle_git.jsonl
python3 exploratory_selection/git_stats.py <mariadb clone> 'MDEV-\d+' mariadb_git.jsonl
```

Jira data change over time (new comments, late worklogs), so a new download can differ slightly. The linking reproduces the package: all 11,117 Moodle and 10,529 of 10,531 MariaDB linked issues of `data/links/` are found, with the same number of files for 11,117 and 10,526 of them. Changed lines and commits in (a) count every linked commit on all branches, so Moodle's back-ports to stable branches raise them for issues from before 2019. Percona's issues without hours are not compared, because their linking needs 21 repositories.
