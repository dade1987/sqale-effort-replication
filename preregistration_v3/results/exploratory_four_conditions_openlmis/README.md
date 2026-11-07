# OpenLMIS: the same issues under four measurement conditions (exploratory, not preregistered)

Date: 7 November 2026 (checklist v7, point 1). The registered measure (A) stays the primary analysis.

* `hist_bytecode_perfile.py` / `run_perfile.sh`: second build of the 492 OpenLMIS issues that compiled on 6 Nov
  (`../exploratory_bytecode_historical/`), same procedure, now keeping the debt and NCLOC of every touched Java file
  (`perfile_openlmis.jsonl`, log `perfile_openlmis.log`). `reproducibility_check.txt`: 492/492 issues identical to the first build.
* `four_conditions.py`: builds the four cells and runs the frozen `confermativo_v3.py` on each
  (`python3 four_conditions.py perfile_openlmis.jsonl results`). Test files: the same path rule used on 5 Nov
  (`../exploratory_without_test_files/refetch_without_tests.py`).
  * Family "registered_based" (reported in the article, Table 5d): A = registered scan; B = registered scan without test files;
    C = A − Java debt without bytecode + Java debt with bytecode; D = B − non-test Java debt without bytecode + non-test Java debt with bytecode.
  * Family "java_only" (check): all four cells from the touched Java files of the second build only.
  * An issue is kept only if all four cells have measured files and NCLOC > 0, so each family uses one identical set (476 issues;
    16 issues touch only test files).
* `results/summary_four_conditions.json`: per cell n, total and median debt, ρ(SQALE, NCLOC), H1 with developer and
  developer × module CI, H3; plus the bytecode and test-file effects and their interaction. `results/results_*.json`: full outputs.

| Cell | Bytecode | Test files | H1 (developer CI) | developer × module CI | H3 % MAE |
|---|---|---|---|---|---|
| A | no | counted | 0.048 (−0.022; 0.139) | (−0.073; 0.198) | −0.71; 0.78 equivalent |
| B | no | left out | 0.074 (−0.016; 0.149) | (−0.057; 0.210) | −0.66; 0.99 equivalent |
| C | yes | counted | 0.131 (0.034; 0.230) | (−0.006; 0.269) | 0.30; 2.15 inconclusive |
| D | yes | left out | 0.063 (−0.033; 0.133) | (−0.096; 0.194) | −0.48; 0.94 equivalent |

Reading: bytecode raises ρ only when test files are counted (+0.08; −0.01 without them). The 0.13 with bytecode and the
0.13 on production code only (all 945 production issues, 5 Nov) are different findings. No cell improves prediction.

Note: script paths refer to the authors machine; issue features (developers, modules) are in the pseudonymised `data/features_v3_*.csv`, so the per-issue CSV files with original identifiers are not included.
