# Epstein_Files
A repo to explore and analyze the Epstein files

Start with the [DOJ dataset inventory](docs/data-inventory.md), observed November 1, 2026.

The [inventory data](data/inventory/2026-11-01/) contains source listing snapshots and metadata, not the document collection. The [PowerShell inventory script](scripts/inventory-doj.ps1) reads public listing pages without downloading linked documents.

The [100-document pilot findings](docs/pilot-findings.md) cover downloads and text extraction across all 12 datasets. See the [pilot manifests and measurements](data/pilot/2026-11-01/); original PDFs and unreviewed extracted text stay in ignored local caches during this phase.
