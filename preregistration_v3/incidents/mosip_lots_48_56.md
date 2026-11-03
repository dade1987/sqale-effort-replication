# MOSIP lots 48-56: technical failure on the first pass (3 Nov 2026)

From 14:43 UTC onward, every SonarQube analysis of the MOSIP lots 48-56 failed in the server
step that saves results (Compute Engine). The cause: SonarQube's built-in Elasticsearch
locked its indexes because it reads the disk as 95% full ("flood-stage watermark"). The
real disk still had 13 GB free; the percentage is computed against the container's
nominal size.
No measurement was written for these lots, so no output files exist for them.

The fix (15:03 UTC) changes only that Elasticsearch disk safety threshold:
cluster.routing.allocation.disk.threshold_enabled=false, and the read-only block removed.
It does not change the analysis rules, the profiles, the scanner or the code under analysis.

run.sh was then started again with the same arguments; lots already finished were skipped.
The first 10 issues of lot 48 were checked by hand: plausible values, distinct between issues.
The logs of the failed pass are kept in this folder.
