# Preregistration manifest

How each OSF registration maps to the files of this package, and how to check it (`sh docs/verify_preregistrations.sh`, run from the package root).

| | First | Second | Third |
|---|---|---|---|
| OSF registration | https://osf.io/ts9n6 | https://osf.io/gb3y9 | https://osf.io/q39g8 |
| Registered (UTC) | 24 Oct 2026, 06:26:50 | 31 Oct 2026, about 21:30 | 3 Nov 2026, 13:06:54 |
| Embargo | until 1 Jun 2027 (view-only links in the paper) | same | same |
| Folder here | `preregistration/` | `preregistration_v2/` | `preregistration_v3/` |
| Registered archive | `preregistration_files.zip` (SHA-256 `24baf467…08837`) | none usable: the files attached on OSF are empty (0 bytes, an upload problem); the SHA-256 hashes of the protocol, key list and script are written in the registration's description and in the protocol (table "File / SHA-256") | `preregistrazione_nuovi_progetti_osf.zip` on OSF, SHA-256 `04fb8ca0…4e830` (248,970 bytes), stated in the registration's description |
| Per-file hashes | `SHA256SUMS.txt` | `SHA256SUMS.txt` (same values as the registration's description) | `SHA256SUMS.txt` |
| Files that differ from the registered ones | none | none | the three feature tables `data/features_v3_<project>.csv`: developer identifiers pseudonymised (salted hash, salt not distributed); the frozen script gives identical output on them (see `preregistration_v3/README.md`) |
| Results | `preregistration/results/` | `preregistration_v2/risultati/` (`SHA256SUMS_risultati.txt`) | `preregistration_v3/results/` |

Scans started only after each registration: first registration, hold-out scans launched at 06:29 UTC on 24 Oct; second, the 1,475 new CFamily scans after 21:30 UTC on 31 Oct; third, the first SonarQube analysis of the sample after 13:06 UTC on 3 Nov (`preregistration_v3/incidents/`).

The Zenodo record cited in the paper archives this repository at a tagged release; `README.md` and `docs/table_map.md` map each table to its script and result file.
