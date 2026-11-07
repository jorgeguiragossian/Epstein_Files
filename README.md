# Epstein_Files
A repo to explore and analyze the Epstein files

## Public pilot website

[Open the GitHub Pages pilot](https://jorgeguiragossian.github.io/Epstein_Files/). The public static build contains the pilot's extracted text and parsed email data, with original PDF links pointing to DOJ. See [publication scope and deployment instructions](docs/github-pages.md).

Start with the [DOJ dataset inventory](docs/data-inventory.md), observed November 1, 2026.

The [inventory data](data/inventory/2026-11-01/) contains source listing snapshots and metadata, not the document collection. The [PowerShell inventory script](scripts/inventory-doj.ps1) reads public listing pages without downloading linked documents.

The [100-document pilot findings](docs/pilot-findings.md) cover downloads and text extraction across all 12 datasets. See the [pilot manifests and measurements](data/pilot/2026-11-01/); original PDFs and unreviewed extracted text stay in ignored local caches during this phase.

## Local document explorer

Run `python viewer/server.py` and open **http://127.0.0.1:8765** to search the pilot, filter datasets, inspect page text and quality flags, and open original PDFs. See [setup and usage](docs/viewer.md), including cache reconstruction after a fresh clone.

The [date-review milestone](docs/date-review.md) adds primary-date ranges and separate uncertain/undated/unreviewed filters, with page evidence for 40 reviewed pilot documents (36 dated and four uncertain; see [expanded review](docs/date-review-batch-2.md)). Restart a running viewer after code or annotation changes, then reload its browser tab.

The [person-name filter](docs/person-filter.md) now includes 22 curated, source-cited name phrases and highlights their matching pages. Reproducible coverage counts and deferred spelling/initial variants are saved with the pilot metadata. These are text mentions, not verified identities or relationships.

The [email review workspace](docs/email-review.md), available at `/emails`, adds page-cited header/body candidates and conservative visible-copy grouping. Incomplete participants and dates remain flagged; contact rankings are not yet enabled.

The [timeframe briefs](docs/timeframe-briefs.md) view selects 36 prepared AI-assisted, page-scoped drafts with citations. All 36 have recorded Codex editorial source checks; these are not independent or human verification. All 36 dated pilot PDFs now have a limited-page brief. This static view does not generate live AI summaries.

## Collection catalog

The [resumable listing catalog](docs/catalog.md) records 6,462 observed dataset/file URL pairs across all 12 datasets, including download and extraction metadata for the 100 pilot PDFs. Normal browser capture has now traversed every advertised listing page in datasets 1–7 and 12. Datasets 8–11 have eleven observed listing pages each and remain partial. URL extensions include PDF, AVI and MP4; these are file-listing observations, not MIME verification. The full current file total remains unknown. Catalog entries outside the pilot are discovery records, not searchable document text.
