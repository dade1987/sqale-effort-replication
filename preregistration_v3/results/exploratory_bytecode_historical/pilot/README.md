# Pilot: compiling the historical snapshots (5 Nov 2026, exploratory, not preregistered)

10 random analysed Java issues per project (seed 20261105) from the third test. For each issue the parent of the earliest linked
commit is exported, the modules holding the touched Java files are built (Maven: `package -DskipTests` + `dependency:build-classpath`;
Gradle 3.5.1 / 4.10.3 / 6.9.4 or the wrapper: `compileJava compileTestJava`), JDK 8, 11 (and 21 for Maven) in turn. The touched Java
files are then measured with SonarQube 26.9 without bytecode (as registered) and with the compiled classes and the dependency jars.

Build fixes (all logged per issue): Maven Central through Google's mirror (direct Central returned HTTP 429), http repositories
rewritten to https (OpenMRS: mavenrepo.openmrs.org/public), OpenLMIS `-SNAPSHOT` libraries (service-util) rebuilt from their own
repository at the last commit before the parent's date, MOSIP `io.mosip` libraries rebuilt from the same repository when the
needed version is found in its history (one level only).

| Project (eligible issues) | Compiled | Main reasons for failure |
|---|---|---|
| OpenMRS (1,264) | 9/10 | Android client (needs the Android SDK) |
| OpenLMIS (804) | 5/10 | JasperReports artifacts only on jaspersoft.artifactoryonline.com (blocked by this environment's network policy); old Gradle plugins |
| MOSIP (2,197) | 1/10 | 2019 `io.mosip` kernel libraries (0.8-0.11) are not public; rebuilding them needs further old MOSIP libraries in a chain |

Without bytecode, 26 of 30 issues reproduce the registered SQALE exactly (all 30 NCLOC); the other 4 differ slightly, probably
because the registered scans analysed several issues in one project, which changes Java type resolution.
With bytecode, debt rose in 13 of the 15 compiled issues (sum 3,166 to 11,473 minutes, 3.6 times).
