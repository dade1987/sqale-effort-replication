#!/bin/sh
# Checks the per-file hashes of the four preregistrations (run from the package root).
echo "== first";  ( cd preregistration && sha256sum -c SHA256SUMS.txt ) ; sha256sum preregistration/preregistration_files.zip
echo "== second"; ( cd preregistration_v2 && sha256sum -c SHA256SUMS.txt && cd risultati && sha256sum -c SHA256SUMS_risultati.txt )
echo "== third (3 pseudonymised feature tables are expected to fail)"; ( cd preregistration_v3 && sha256sum -c SHA256SUMS.txt )
echo "== fourth"; ( cd preregistration_v4 && sha256sum -c SHA256SUMS.txt && cd results && sha256sum -c SHA256SUMS_results.txt )
