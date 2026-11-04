# Link check of preregistration 3: rater Gianluigi Lucca Fabris (answers received 3 Nov 2026, 20:50 UTC)

Verdicts: human_rater_verdicts.csv (90/90 rows answered). The rater worked from a spreadsheet with the English originals, without translations, and was instructed not to use AI tools.
Question 1, "do the commits concern this issue?":

| Project | correct | partial | wrong | Precision (correct), Wilson 95% CI | At least partly correct |
|---|---|---|---|---|---|
| MOSIP | 26 | 0 | 4 | 86.7% (70.3-94.7) | 86.7% |
| OpenLMIS | 27 | 3 | 0 | 90.0% (74.4-96.5) | 100% (88.6-100) |
| OpenMRS | 30 | 0 | 0 | 100% (88.6-100) | 100% |
| All | 83 | 3 | 4 | 92.2% (84.8-96.2) | 95.6% (89.1-98.3) |

The wrong MOSIP links: MOS-25757, MOS-22738, MOS-13174, MOS-28823. The partial OpenLMIS links: OLMIS-1267, OLMIS-1156, OLMIS-933.
Question 2 (missing commits): "don't know" for all 90 rows, so completeness was not measured.

## Extra MOSIP check (exploratory, not in the protocol)

Because MOSIP had the lowest precision, the same rater checked 70 further MOSIP links (answers received 4 Nov 2026), drawn at random (seed 20261104) from the protocol-conforming analysed MOSIP sample, excluding the 30 already checked; same spreadsheet format and instructions. Script: mosip_extra70/build_sample70.py (paths refer to the authors' workspace); keys: mosip_extra70/sample70_keys.json; verdicts: mosip_extra70/human_rater_verdicts_mosip70.csv.

| MOSIP | correct | partial | wrong | Precision (correct), Wilson 95% CI |
|---|---|---|---|---|
| Extra 70 | 60 | 6 | 4 | 85.7% (75.7-92.1) |
| All 100 | 86 | 6 | 8 | 86.0% (77.9-91.5) |

Wrong in the extra 70: MOS-29377, MOS-24367, MOS-24325, MOS-29421. Question 2: "don't know" for all 70.
Seven of the eight wrong links are in the analysed MOSIP sample; without them MOSIP gives -0.015 (90% CI -0.068 to 0.036; n = 1,996), negligible; H3 equivalent (results/exploratory_wrong_links/real100/).
