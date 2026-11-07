# Browser catalog expansion — second batch, November 7, 2026

Used normal in-app browser navigation and the site’s visible Next page links. Captured 112 additional listing pages: dataset 1 pages 2–62, dataset 2 pages 1–11, and datasets 8, 9, 10 and 11 pages 1–10 each. Page indices are zero-based. No document downloads, HEAD requests, alternate endpoints, mirrors or access-control bypasses were used.

Each committed `.dom.html` snapshot contains observed rendered anchor links and their text. Its companion metadata records the actual URL, UTC capture time and SHA-256. Import checks URL/hash correspondence, retains every page observation, deduplicates dataset/URL pairs and rejects identical file sets on different page indices. Browser HTTP status is not inferred; earlier command-line HTTP 403 records remain preserved.

## Coverage

| Dataset | Observed listing pages | Advertised listing pages | Observed unique file URLs | Next unobserved page |
| --- | ---: | ---: | ---: | ---: |
| 1 | 63 | 63 | 3,147 | — |
| 2 | 12 | 12 | 566 | — |
| 3 | 2 | 2 | 76 | — |
| 4 | 4 | 4 | 151 | — |
| 5 | 3 | 3 | 118 | — |
| 6 | 1 | 1 | 13 | — |
| 7 | 1 | 1 | 17 | — |
| 8 | 11 | 221 | 549 | 11 |
| 9 | 11 | 10,675 | 550 | 11 |
| 10 | 11 | 10,081 | 550 | 11 |
| 11 | 11 | 6,634 | 550 | 11 |
| 12 | 4 | 4 | 175 | — |

The catalog grew from 898 to **6,462 dataset/file URL pairs**, adding 5,564. Eight datasets now have all advertised listing pages observed; datasets 8–11 remain partial. The overall current total remains null. Observations taken at different times do not establish a single immutable current release, unique document contents or missing files.

The observed suffixes are 6,460 `.pdf`, one `.avi` and one `.mp4`. The AVI and PDF with stem EFTA00003212 are retained as separate URL records. File IDs alone must not serve as catalog primary keys. Suffixes do not verify file bodies or MIME types. Media processing will require a later, separate pipeline.

Searchable pilot text remains 100 PDFs. All prior pilot data and brief-review records are unchanged. The 6,362 cataloged non-pilot records have not been downloaded or indexed.

## Continue

Start the next bounded browser capture at page 11 for datasets 8–11, using observed pagination links. Dataset 8 has the smallest remaining listing range. Preserve each page’s evidence and export the resumable catalog before ending a batch. For the very large datasets, evaluate a documented official bulk manifest or supported discovery interface before committing to tens of thousands of manual page visits.
