# Resumable collection catalog

The collection catalog is the discovery layer for eventual coverage of all twelve numbered DOJ datasets. It is separate from the 100-document searchable pilot. Records outside the pilot have not been downloaded or text-indexed.

## Current checkpoint

The [second browser batch](catalog-browser-batch-2.md) expands the catalog to **6,462 dataset/file URL pairs**: 6,460 `.pdf`, one `.avi` and one `.mp4` URL. These are observed extensions, not verified MIME types. Every advertised listing page has been observed for datasets **1–7 and 12**. Datasets **8–11** each have pages 0–10 observed; each resumes at zero-based page **11**. The full collection total remains unknown and searchable text still covers only the 100 pilot PDFs.

## Initial November 7 observations

Ordinary public GET requests refreshed the first listing page of each of the twelve datasets. They yielded the same 525 dataset/file URL pairs observed November 1. The next batch requested dataset 1 listing page 1 and received HTTP 403; the crawler recorded the failure and stopped without automatic retries. The cause of the denial is unknown. No access controls were bypassed, file URLs guessed, document bodies downloaded, HEAD requests made, mirrors used or paid services provisioned.

The listings advertise 27,701 pages in total. This is listing pagination, not PDF pages or an exact document total. Datasets 6 and 7 each have one advertised page, so their visible listings are covered. The initial refresh alone left ten datasets partial; the browser pass described below expanded that coverage. Historical and current observations are both retained; previously seen URLs are never silently labeled current, removed or missing. The full current file total stays null, even when all advertised pages have been seen at different times.

A normal browser visit to the same page succeeded. Using the previously authorized adult verification, a bounded pass captured link DOM snapshots for dataset 1 page 1, dataset 3 page 1, dataset 4 pages 1–3, dataset 5 pages 1–2, and dataset 12 pages 1–3. The ten browser snapshots add 373 unique dataset/file URL pairs, yielding **898 observed pairs**. Browser access did not modify the command-line failure record or use a bypass.

Every advertised listing page has now been observed for datasets **3, 4, 5, 6, 7 and 12**. Their observed unique URL counts are 76, 151, 118, 13, 17 and 175 respectively. Dataset 3 repeats a URL across listing pages, illustrating why displayed link counts must not simply be summed. Six other datasets remain partial. These are URL counts, not distinct document-content counts.

## Open manifests

Under [data/catalog/2026-11-07](../data/catalog/2026-11-07/):

- `files.csv`: 6,462 unique dataset/URL pairs, discovery timestamps, observed page indices, and pilot download/extraction metadata where available. Empty size, hash and page fields mean unknown. `pilot_download_record` is a historical processing record, not a fresh download or a guarantee a fresh clone has the cached PDF.
- `provenance.csv`: each URLâ€™s listing page, observation timestamp and exact HTML hash. Repeated observations are retained here without duplicating file rows.
- `catalog.json`: dataset coverage, all successful listing observations, twelve fresh successful request records, the fresh 403, and ten historical pagination failures. Dataset rows include the next unobserved listing page; the top-level extension counts describe URL suffixes. Browser observations are separately identified with `representation: browser_link_dom`; their HTTP status is not inferred. `current_total_files` is null; discovery counts must not be described as the full release.

HTML snapshot hashes authenticate locally saved listing bytes, not linked PDFs. Original November 1 snapshots are tracked in the inventory directory. Fresh HTTP listing HTML and the working SQLite database are local caches ignored by Git. Browser link snapshots and their capture metadata are committed under `browser-snapshots/`; they contain observed anchor links and text, not raw HTTP response bytes or hidden form values. Their hashes authenticate those saved DOM representations. The committed CSV/JSON exports preserve the discovery/provenance records and can reconstruct the database after a clone. External public archival storage for raw snapshots and the full document collection remains a later infrastructure decision.

## Reproduce and resume

Python uses only its standard library. From the repository root:

```powershell
python scripts/catalog.py restore --out data/catalog/2026-11-07
python scripts/catalog.py export --out data/catalog/2026-11-07
```

For a new catalog initialized from the hash-checked original inventory:

```powershell
python scripts/catalog.py seed
```

To explicitly run a new bounded request batch:

```powershell
python scripts/catalog.py crawl --refresh-first --max-pages 12
python scripts/catalog.py crawl --max-pages 12
```

The first command refreshes first pages. The second schedules unobserved page indices from advertised pagination, in page-index/dataset order. Each invocation allows 1â€“100 listing requests, with at least 0.5 seconds between requests, a 25-second timeout and a 4 MiB response limit. A failed request stops the whole batch. Re-running `crawl` explicitly attempts the earliest unobserved page again; there is no automatic background retry. Resolve supported pagination access before scheduling larger ingestion work.

Each successful listing is committed transactionally to local SQLite before the next request. Repeated file URLs are deduplicated within datasets while every observation retains provenance. Identical file sets on different pages are rejected for review, preventing a server that repeats page zero from falsely completing pagination. Failed pages remain incomplete; no numeric EFTA gaps are used to infer files.

Browser snapshots can be imported with `python scripts/catalog.py import-browser --dataset 3 --page 1 --snapshot data/catalog/2026-11-07/browser-snapshots/dataset-3-page-1.dom.html`. The companion `.dom.json` must record the matching actual page URL, UTC capture time and SHA-256. Import checks both URL and hash before recording an observation. Snapshots are captured from the normal browser’s rendered anchors; this command itself makes no network requests.

## Next step

Normal browser pagination works for this bounded pass; command-line pagination still fails with 403. Use supported browser capture in bounded batches, or obtain a documented official bulk manifest suitable for large-scale discovery. Then resume cataloging in bounded batches, preserving failures and provenance. Once discovery coverage is measurable, choose the next extraction batch and evaluate public storage/search requirements. This milestone does not yet claim a complete catalog or add the 6,362 non-pilot records to full-text search.
