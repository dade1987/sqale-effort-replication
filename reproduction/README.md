# Re-runs of the replication package

- `guide_it.md`: the written guide (Italian) given to the re-runner; `compare.py`: the comparison script it embeds.
- `ai_assisted_rerun_2026-11-05/`: outputs of a re-run of version 1.7 organised by a person who is not an author (the rater of the new projects' links), with an AI assistant (ChatGPT) executing the commands in its own Linux environment. It is a computational check, not an independent manual verification (see `LEGGERE_PRIMA_DI_CONDIVIDERE.txt` and `relazione.txt`). The pinned library versions could not be installed, so older ones were used (`03_pip_freeze.txt`).
  - Package hash: identical to the Zenodo v1.7 file.
  - All three preregistered tests and the main comparison of Table 8 reproduce the stored values.
  - 10 of 31 result files differ in secondary values (`11_confronto.txt`, `13_confronto_completo.txt`), consistent with the different library versions.
  - With the pinned versions, the authors' own re-run from a clean download matched 30 of 31 files (the other, `results_transfer.json`, in the fifth decimal).
