# Exploratory: Java analysed with and without compiled classes (5 Nov 2026, not preregistered)

The third registration analyses Java without bytecode. The historical snapshots of the sample could not be rebuilt
(for example, MOSIP admin-services at an issue's parent commit needs io.mosip.kernel 0.8.0 artifacts that are not in any public repository,
and Lombok versions of 2019 do not run on current JDKs). We therefore built a current version of two repositories and analysed the same
Java files twice with SonarQube Community Build 26.9 (Sonar way): without bytecode, as registered, and with the compiled classes and the
dependency jars (`bytecode_compare.py`). Test files are analysed as code, as in the registered scans.

| Repository (commit) | Files | Debt with / without bytecode | Spearman per file, with vs without | Spearman debt-NCLOC, without / with | Rules that grow most |
|---|---|---|---|---|---|
| MOSIP admin-services (7d33a8d0f3, Aug 2026) | 1,504 | 2.62x | 0.75 | 0.49 / 0.68 | S3252, S6813, S1128 |
| OpenMRS core (a5374b63a, Oct 2026; modules api, web, test) | 1,452 | 2.91x | 0.70 | 0.57 / 0.71 | S100, S112, S3457 |

Proxy H1 (`proxy_h1.py`): for the analysed issues of each repository, the current measures of the touched Java files that still exist
(matched by package path) are summed, without and with bytecode, and the frozen H1 script is applied. This proxy is not the registered
measure (it uses today's files), but it compares the two analyser settings on the same files and issues:

| | Issues | Without bytecode | With bytecode |
|---|---|---|---|
| MOSIP admin-services | 291 | -0.047 (-0.149 to 0.071) | -0.180 (-0.267 to -0.069) |
| OpenMRS core | 348 | -0.012 (-0.099 to 0.079) | -0.019 (-0.103 to 0.080) |

OpenLMIS (Gradle 4.10 build of requisition) could not be built here: dependency downloads were refused (HTTP 429).
