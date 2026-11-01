# Epstein_Files
A repo to explore and analyze the Epstein files

Start with the [DOJ dataset inventory](docs/data-inventory.md), observed November 1, 2026.

The [inventory data](data/inventory/2026-11-01/) contains source listing snapshots and metadata, not the document collection. The [PowerShell inventory script](scripts/inventory-doj.ps1) reads public listing pages without downloading linked documents.

The [100-document pilot findings](docs/pilot-findings.md) cover downloads and text extraction across all 12 datasets. See the [pilot manifests and measurements](data/pilot/2026-11-01/); original PDFs and unreviewed extracted text stay in ignored local caches during this phase.

## Local document explorer

Run `python viewer/server.py` and open **http://127.0.0.1:8765** to search the pilot, filter datasets, inspect page text and quality flags, and open original PDFs. See [setup and usage](docs/viewer.md), including cache reconstruction after a fresh clone.

The [date-review milestone](docs/date-review.md) adds primary-date ranges and separate uncertain/undated/unreviewed filters, with page evidence for 20 reviewed pilot documents. Restart a running viewer after code or annotation changes, then reload its browser tab.

The [person-name filter](docs/person-filter.md) adds eight curated, source-cited name phrases and highlights their matching pages. These are text mentions, not verified identities or relationships.
