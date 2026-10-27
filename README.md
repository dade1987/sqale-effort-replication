# Replication package: Does SQALE Debt Explain Issue Effort Beyond Code Size?

This package lets you reproduce every number in the paper. It contains the data, the code and the results for 24,887 resolved Jira issues from Moodle, MariaDB Server and Percona. In these projects people logged their own hours, and each issue is linked to its fixing commits.

It also contains the preregistered confirmatory study (2,000 hold-out issues from Moodle and MariaDB), the exploratory analyses added during review, the survey of public SonarQube Cloud projects, and both validations of the issue–commit links.

## Contents

| Folder | What it holds |
|---|---|
| `data/links/` | Issue → commit links with logged hours, type, resolution date, components and changed files (`<project>_links.jsonl.gz`) |
| `data/features/` | Per-issue features (Table 2 of the paper) |
| `data/history/` | Jira fields reconstructed at creation, assignee at the first fix commit, the start of work and the developer at that moment (`<project>_start_of_work.csv`), expert estimates and assignee hours |
| `data/extra/` | Features for the exploratory analyses (file and component history, text embeddings and their keys) and per-issue worklog timing (`<project>_worklog_timing.csv`) |
| `data/sqale/` | SQALE results per issue (`sqale_min`, `ncloc`, files analysed) and the sampled keys |
| `data/confirmatory/` | SQALE scans of the hold-out (`holdout_scan_<project>.jsonl`) and of the exploratory sample (`exploratory_sample_scan_<project>.jsonl`), as read by the preregistered script |
| `data/official_cxx/` | Official SonarQube Cloud C/C++ analyser results on 200 MariaDB hold-out issues, and the sampled keys |
| `data/predictions/` | Per-issue test predictions of every model and baseline; `dev_at_first_commit/` holds those of the earlier definition (sensitivity analysis) |
| `code/` | Main pipeline: download, linking, features, SQALE scans, models (see below) |
| `preregistration/` | The frozen preregistration files and the script that re-runs them (see below) |
| `exploratory/` | Exploratory analyses of Sections 6 and 8 that are not preregistered |
| `results/` | Result files behind the tables of the paper; `results/confirmatory/` and `results/exploratory/` hold the newer analyses |
| `sonarqube/` | The C/C++ quality profile used with sonar-cxx (`td_cxx_profile.xml`) |
| `sonarcloud_survey/` | Survey of 365 public SonarQube Cloud projects: remediation functions and signs of active use |
| `link_validation/` | The AI-rater validation samples, the blind manual check by the author and the second human rater |
| `docs/` | The maps used to translate the original Italian labels and keys into English |

## Personal data

Developer names, logins and emails are replaced by pseudonyms (`dev_` followed by 10 hex digits). The pseudonyms come from a salted hash, and the salt is not distributed. The same person always gets the same pseudonym, so the developer-history features and the developer-clustered bootstrap reproduce.

Issue keys, titles and commit hashes are public and are kept. The raw Jira change histories and worklogs contain names, so they are not distributed. `code/download_jira_history.py` downloads them again from the public Jira instances. The only worklog information we distribute is derived and anonymous: per issue, the date of the first worklog, the hours logged and the hours logged before the day of the first fix commit (`data/extra/<project>_worklog_timing.csv`).

## Main pipeline (`code/`)

1. `download_jira_issues.py`: downloads the issues with logged time from Jira.
2. `link_issues_commits.py`: links issues to commits. It is run with `ONLY_FIXED=1 STRICT=1`, so the subject must start with exactly one issue key and merges are excluded.
3. `percona_main_repo.py`: assigns each Percona issue to the repository with the most changed files, excluding `vendor/`.
4. `features.py`: computes the per-issue features from each Git repository.
5. `download_jira_history.py` and `history_features.py`: download the change histories and reconstruct the Jira fields at creation.
6. `sample_sqale.py` and `sqale_scan.py`: draw the SQALE samples and analyse the touched files with SonarQube Community Build 26.9. C/C++ files use sonar-cxx 2.4.0-beta1 and cppcheck 2.13.
7. `download_jira_descriptions.py` and `extra_features.py`: compute the features for the exploratory analyses.
8. `start_of_work.py`: finds the start of work S (the earlier of the first worklog day and the first fix commit day) and the developer at S (the assignee at the start of that day, otherwise the author of the first worklog). It reads the raw Jira histories, which contain names, so its pseudonymised output is distributed instead (`data/history/<project>_start_of_work.csv`).
9. `model.py`: the main analysis (RQ1–RQ4). M0 uses the developer and their history at S. `DEV_AT=commit` restores the earlier definition (the assignee at the first fix commit), whose results are in `results/dev_at_first_commit/`. `exploratory.py`: the exploratory models. `transfer.py`: cross-project transfer.
10. `representativeness.py` and `hours_shares.py`: compute the selection profile and the share of hours logged by the assignee.

Step 9 runs from the distributed data alone:

```
cd code && sh run_models.sh
```

The distributed results were produced by this script from the distributed data.

## Preregistered confirmatory study (`preregistration/`)

The protocol was registered on OSF on 24 October 2026 before the hold-out was analysed (view-only link: https://osf.io/ts9n6/overview?view_only=451038ea3c264c6caf16a97fdc2908da).

These files are byte-identical to the registered ones, and `SHA256SUMS.txt` lists their hashes. They are kept in their original form, Italian comments and keys included, so that they can be checked against the registration:

| File | Content |
|---|---|
| `protocol_confirmatory_v1.md` | The protocol (hypotheses H1–H3, SESOI, analysis plan) |
| `confermativo.py` | The frozen analysis script |
| `sqale_lines.py` | The frozen scan script (SQALE on the changed lines); it contains the local paths used at the time |
| `holdout_keys_moodle.txt`, `holdout_keys_mariadb.txt` | The 1,000 + 1,000 hold-out keys (seed 20261024) |
| `preregistration_files.zip` | The archive uploaded to OSF |

To re-run the confirmatory analysis:

```
python3 preregistration/run_confirmatory.py
```

The script runs the frozen `confermativo.py` on `data/confirmatory/`, applies the Holm correction across the four one-sided tests, and writes two copies of the results:

- `preregistration/results/`: `confermativo_<project>.json` and `holm_4test.json`, with the original Italian keys, as the frozen script writes them;
- `results/confirmatory/`: `confirmatory_<project>.json` and `holm_4_tests.json`, with the same numbers and English keys and verdicts (`docs/translation_map_confirmatory.json`).

The distributed copies were produced at the time of the study. Re-running gives identical results, apart from one MariaDB value that differs in the 16th decimal place.

The scan files in `data/confirmatory/` keep the field names read by the frozen script. The Italian ones mean:

| Field | Meaning |
|---|---|
| `sqale_c1_prima`, `ncloc_c1_prima` | SQALE and lines of code of the files changed by the first fix commit, before the commit |
| `sqale_c1_dopo`, `ncloc_c1_dopo` | the same, after the commit |
| `righe_vecchie_modificate` | old lines changed or deleted by the first fix commit |
| `sqale_righe_modificate` | SQALE of the issues located on those lines |
| `smell_su_righe_modificate` | number of code smells on those lines |
| `sqale_c1_da_issues` | SQALE of the changed files, summed from the individual issues |

`exploratory/confirmatory_secondary.py` computes the secondary analyses listed in Section 8 of the protocol (`results/confirmatory/secondary_results.json`).

## Exploratory analyses (`exploratory/`)

None of these analyses is preregistered. All of them run from the distributed data:

```
sh exploratory/run_all.sh
```

| Script | Paper | Output in `results/exploratory/` |
|---|---|---|
| `by_issue_type.py` | Table 11, error by issue type | `by_issue_type.json` |
| `size_collinearity.py` | SQALE vs size, partial ρ in the exploratory data | `size_collinearity.json` |
| `debt_removed.py` | Debt removed by the first fix commit | `debt_removed.json` |
| `other_algorithms.py` | Table 12, random forest, XGBoost, CatBoost and a neural network | `other_algorithms_<project>.json` |
| `official_cxx_compare.py`, `official_cxx_models.py` | Table 13, official C/C++ analyser vs sonar-cxx | `official_cxx_compare.json`, `official_cxx_models.json` |
| `revision_checks.py` | Timing of the logged work, excluded issues, nonlinear size models, uncertainty of Table 10 | `revision_checks.json` |
| `size_classes_cutpoints.py` | Table 10 and the alternative cut-points (2/8 h, 8/40 h) | `size_classes_cutpoints.json` |
| `other_quality_measures.py` | Partial ρ of hours with other quality and history measures given size | `other_quality_measures.json` |
| `figure1_partial_rho.py` | Figure 1 (English and Italian labels) | `fig1_partial_rho_en.png`, `fig1_partial_rho_it.png` |

`common.py` holds the metrics and paired tests shared with `code/model.py`.

All outputs match the analyses reported in the paper. In `revision_checks.py` the developer clusters of the bootstrap are ordered by developer identifier, so the confidence intervals depend on the pseudonyms. The intervals in the paper are the ones computed from this package.

`official_cxx_scan.py` and `official_cxx_run.sh` re-run the official analyser. They need a clone of MariaDB/server (`MARIADB_REPO`), `sonar-scanner` (`SONAR_SCANNER`), a SonarQube Cloud organisation (`SONAR_ORG`) and a token with analysis rights in `SONAR_TOKEN`. They are not part of `run_all.sh`.

## Link validation (`link_validation/`)

**AI raters.** `mariadb_moodle_judgements.csv` and `percona_judgements.csv` hold 50 + 50 sampled issues, their linked commits, and the judgements of two AI raters (correct, partial or wrong):

- Rater 1: Claude (Anthropic).
- Rater 2: ChatGPT (OpenAI, GPT-6 Thinking, extended reasoning).

The raters judged blind to each other, and the author spot-checked the doubtful cases. The second rater's instruction is in `second_rater_prompt.md`, verbatim and in English translation. The second rater wrote its notes in Italian: `rater_chatgpt_note_original_it` keeps them, and `rater_chatgpt_note_en` translates them.

**Manual check by the author** (`manual_check/`). The author checked 100 random links (40 Moodle, 40 MariaDB, 20 Percona) without AI help, on a page that hid every other judgement. For each issue the author judged the linked commits (correct, partial or wrong) and said whether a fix commit was missing.

- `sample_100.csv`: the sample.
- `answers_author.csv`: the answers, with the time per issue.
- `second_rater/`: a second person, not involved in the research and without AI help, checked 30 of the 100 links (seed 20261026; `sample_30_keys.json`, `answers_second_rater.csv`).
- `analyze_manual_check.py` → `results_manual_check.json`: precision 99%, completeness 96%, median 28 s per issue, agreement 30/30 between the two people.

## SonarQube Cloud survey (`sonarcloud_survey/`)

- `list_projects.py` lists the public projects with at least 50,000 lines.
- `sample_projects.py` draws 400 of them (seed 20261023) → `sample.jsonl`.
- `remediation_functions.py` reads their rule remediation times → `remediation_functions.json`.
- `active_use.py` collects public signs of active use (triaged issues, analyses in the last 12 months, pull requests, debt history) → `active_use.jsonl`.

365 of the 400 projects could be read anonymously.

## Software

The analyses were run on Python 3.13 with the libraries listed in `requirements.txt`. Seeds are fixed: 2026 for the models, samples and bootstrap, 20261023 for the SonarQube Cloud survey, 20261024 for the hold-out and 20261026 for the second human rater's subset.

## Licence

Code: MIT. Data derived from public Jira and Git repositories: CC BY 4.0, subject to the terms of the original sources.
