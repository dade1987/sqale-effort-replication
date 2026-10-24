# Replication package: Does SQALE Debt Explain Issue Effort Beyond Code Size?

This package lets you reproduce every number in the paper. It contains the data, the code and the results for 24,887 resolved Jira issues from Moodle, MariaDB Server and Percona. In these projects people logged their own hours, and each issue is linked to its fixing commits.

## Contents

| Folder | What it holds |
|---|---|
| `data/links/` | Issue → commit links with logged hours, type, resolution date, components and changed files (`<project>_links.jsonl.gz`) |
| `data/features/` | Per-issue features (Table 2 of the paper) |
| `data/history/` | Jira fields reconstructed at creation, assignee at the first fix commit, expert estimates and assignee hours |
| `data/extra/` | Features for the exploratory analyses: file and component history, text embeddings and their keys |
| `data/sqale/` | SQALE results per issue (`sqale_min`, `ncloc`, files analysed) and the sampled keys |
| `data/predictions/` | Per-issue test predictions of every model and baseline |
| `results/` | Result files behind the tables of the paper |
| `code/` | All scripts (see below) |
| `sonarqube/` | The C/C++ quality profile used with sonar-cxx (`td_cxx_profile.xml`) |
| `sonarcloud_survey/` | Scripts and data of the survey of 365 public SonarQube Cloud projects |
| `link_validation/` | The two validation samples with both raters' judgements, and the second rater's instruction |

## Personal data

Developer names, logins and emails are replaced by pseudonyms (`dev_` followed by 10 hex digits). The pseudonyms come from a salted hash, and the salt is not distributed. The same person always gets the same pseudonym, so the developer-history features and the developer-clustered bootstrap reproduce exactly.

Issue keys, titles and commit hashes are public and are kept. The raw Jira change histories and worklogs contain names, so they are not distributed. `code/download_jira_history.py` downloads them again from the public Jira instances.

## Pipeline

1. `download_jira_issues.py`: downloads the issues with logged time from Jira.
2. `link_issues_commits.py`: links issues to commits. It is run with `ONLY_FIXED=1 STRICT=1`, so the subject must start with exactly one issue key and merges are excluded.
3. `percona_main_repo.py`: assigns each Percona issue to the repository with the most changed files, excluding `vendor/`.
4. `features.py`: computes the per-issue features from each Git repository.
5. `download_jira_history.py` and `history_features.py`: download the change histories and reconstruct the Jira fields at creation.
6. `sample_sqale.py` and `sqale_scan.py`: draw the SQALE samples and analyse the touched files with SonarQube Community Build 26.9. C/C++ files use sonar-cxx 2.4.0-beta1 and cppcheck 2.13.
7. `download_jira_descriptions.py` and `extra_features.py`: compute the features for the exploratory analyses.
8. `model.py`: the main analysis (RQ1–RQ3). `exploratory.py`: the exploratory analyses. `transfer.py`: cross-project transfer.
9. `representativeness.py` and `hours_shares.py`: compute the selection profile and the share of hours logged by the assignee.

You can re-run steps 8 from the distributed data alone:

```
cd code && sh run_models.sh
```

We re-ran `model.py` on the distributed Percona data and got the published results. One difference appeared, in the ATLM baseline, at the 15th decimal place.

## Software

The analyses were run on Python 3.13 with the libraries listed in `requirements.txt`. Seeds are fixed: 2026 for the models, samples and bootstrap, and 20261023 for the SonarQube Cloud survey.

## Link validation

`link_validation/` contains `mariadb_moodle_judgements.csv` and `percona_judgements.csv`. Each file has the sampled issues, their linked commits, and the judgements of both raters: correct, partial or wrong.

- **Rater 1:** Claude (Anthropic).
- **Rater 2:** ChatGPT (OpenAI, GPT-6 Thinking, extended reasoning).

The raters judged blind to each other, and the authors spot-checked doubtful cases. The second rater's instruction is in `second_rater_prompt.md`, verbatim and in English translation. The raters worked in Italian, so their notes are in Italian.

## Glossary of result keys

Some keys in the result files and labels in the code are in Italian. This glossary translates them.

| Key | Meaning |
|---|---|
| `test`, `confronti` | test-set metrics; paired comparisons (`dMAE`, `lo`, `hi`, `p_boot`, `p_holm`, `A12_appaiato` = paired A12) |
| `B0 mediana`, `B1 mediana per tipo` | median baseline, median per type |
| `B2 log-lineare n. file`, `B3 testo del titolo` | log-linear on number of files, title text |
| `B5 analogia k-NN` | analogy |
| `M0 all'apertura`, `M1 dopo la localizzazione dei file`, `M2 ex post (+ patch)` | M0 at assignment, M1 after file localisation, M2 ex post |
| `senza sviluppatore`, `senza testo`, `senza statiche`, `senza cronologia` | ablations: without developer, text, static, history features |
| `esperto (prima stima)`, `(prima stima prima del lavoro)`, `(stima finale)` | expert: first estimate, first estimate before work, final estimate |
| `non_inferiore`, `margine_h`, `IC90` | non-inferior, margin in hours, 90% CI |
| `sqale` → `tutte`, `refactoring e pulizia` | SQALE on all analysable issues; refactoring and cleanup subset |
| `SQALE grezzo`, `SQALE ricalibrato` | raw SQALE, recalibrated SQALE |
| `oltre_la_dimensione` | beyond size (RQ2): `solo righe` = lines only, `righe + SQALE` = lines + SQALE, `spearman_parziale_*` = partial Spearman |
| `sensibilita` | sensitivity: `solo ore dell'assegnatario` = assignee hours only, `senza estremi` = without extremes |
| `analisi_errori`, `casi_peggiori`, `importanza_*`, `origine_mobile_SA` | error analysis, worst cases, feature importance, rolling-origin SA |
| `scelta_in_validazione`, `classi`, `pulizia R1` | variants chosen on validation, size classes, cleaning rule R1 |
| `classe piu' frequente`, `accuratezza`, `kappa_pesata`, `errore_di_due_classi` | most frequent class, accuracy, weighted κ, two-class error |
| history: `type_open`, `priority_open`, `components_open`, `assignee_T`, `est_first_h`, `hours_assignee` | values at creation, assignee at T, first estimate, assignee hours |

## Licence

Code: MIT. Data derived from public Jira and Git repositories: CC BY 4.0, subject to the terms of the original sources.
