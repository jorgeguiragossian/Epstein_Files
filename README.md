# Epstein_Files
A repo to explore and analyze the Epstein files

The [published sample](https://jorgeguiragossian.github.io/Epstein_Files/) now contains **110 PDFs and 1,836 pages**, including the [ten-file dataset 8 integration](docs/wave-01-integration.md). Its ten document dates remain unreviewed. The 36 dated page briefs are unchanged; eight new email-layout occurrences bring that workspace to 122, with derived header readings explicitly labeled.


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

The [resumable listing catalog](docs/catalog.md) records 24,447 observed dataset/file URL pairs across all 12 datasets, including download and extraction records for the original 100 PDFs and the ten-file expansion. Normal browser capture has now traversed every advertised listing page in datasets 1–8 and 12. Datasets 9–11 have 61 observed listing pages each and remain partial. URL extensions include PDF, spreadsheets, CSV, audio and video; these are file-listing observations, not MIME verification. The full current file total remains unknown. Catalog entries outside the pilot are discovery records, not searchable document text.

The [official bulk-discovery check and next extraction plan](docs/bulk-discovery-and-expansion.md) found no documented bulk route in the official sources checked. A source-bound 100-PDF expansion is prepared. The [ten-file dataset 8 first wave](docs/expansion-wave-01.md) has been downloaded and natively extracted (49 pages); the [quality follow-up](docs/wave-01-quality-followup.md) retracted an incorrect OCR target and prepared source-reviewed label layers for two header misses. The [targeted boundary follow-up](docs/wave-01-boundary-followup.md) now records the additional fragment and lossless quote partitions; public integration remains pending. The ten PDFs are now included in public search with unreviewed dates; the remaining 90 selected files are unprocessed.
