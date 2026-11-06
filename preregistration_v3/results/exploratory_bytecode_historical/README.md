# Java with compiled classes on the historical snapshots (5-6 Nov 2026, exploratory, not preregistered)

For every analysed Java issue of OpenMRS (1,264) and OpenLMIS (804) of the third test, the parent of the earliest linked commit
was exported and the modules holding the touched Java files were built (`hist_bytecode_pilot.py`; Maven `package -DskipTests`
+ `dependency:build-classpath`, or Gradle 3.5.1 / 4.10.3 / 6.9.4 / wrapper `compileJava compileTestJava`; JDK 8, then 11, then 21).
The touched Java files were measured with SonarQube 26.9 (Sonar way) twice: without bytecode, as registered, and with the
compiled classes and dependency jars. MOSIP was left out after a 10-issue pilot (1/10 built: its 2019 io.mosip libraries are
not public; `pilot_mosip_10.jsonl`).

Build fixes: Maven Central via Google's mirror; http repositories rewritten to https; OpenLMIS -SNAPSHOT libraries
(service-util) rebuilt from their repository at the last commit before the parent's date. Third-party -SNAPSHOT dependencies
resolve to today's snapshots (a limitation). Some OpenLMIS builds need jaspersoft.artifactoryonline.com, blocked here.

| | OpenMRS | OpenLMIS |
|---|---|---|
| Attempted / compiled and measured | 1,264 / 805 (64%) | 804 / 492 (61%) |
| Share of the registered analysed issues | 805 / 1,582 | 492 / 1,344 |
| Java debt with / without bytecode | 2.29x (debt rose in 707) | 3.57x (rose in 456) |
| Spearman per issue, without vs with | 0.89 | 0.81 |
| Spearman debt-NCLOC, without / with | 0.89 / 0.92 | 0.77 / 0.84 |
| H1, registered measure, same issues | -0.107 (-0.182 to -0.023) | 0.041 (-0.028 to 0.130) |
| H1, Java measured with bytecode | -0.136 (-0.217 to -0.046) | 0.127 (0.032 to 0.217) |
| H1 with bytecode, developer x module | (-0.265 to 0.021) | (-0.005 to 0.261) |
| H3 with bytecode, dMAE % of MAE | +0.40 to +1.39 (equivalent) | +0.46 to +2.05 (inconclusive; SQALE makes the error worse) |

`bytecode_h1h3.py` runs the frozen `confermativo_v3.py` on the compiled issues with four measures (registered; registered
with the Java part replaced by the bytecode measure; Java only without; Java only with). Results in `results/`.

Checks: without bytecode, 709 of 791 (OpenMRS) and 378 of 483 (OpenLMIS) all-Java issues reproduce the registered SQALE
exactly; the others differ, probably because the registered scans analysed many issues in one SonarQube project, which changes
Java type resolution. Re-running 3 issues after the SonarQube database was reset (disk space) gave identical values without
bytecode and in 2 of 3 with bytecode (`recheck_3_after_db_reset.jsonl`); the third rose by 17%, probably because a -SNAPSHOT
dependency changed.
