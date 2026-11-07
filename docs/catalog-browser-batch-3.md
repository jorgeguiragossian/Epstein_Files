# Dataset 8 listing completion — November 7, 2026

Used normal in-app browser navigation and visible Next page links to capture dataset 8 pages 11–220 inclusive (210 additional zero-based pages). URL and heading checks guarded each capture; each saved snapshot has a companion actual-URL, UTC timestamp and SHA-256 record. The final advertised page exposed 35 file links. No linked document, spreadsheet, audio or video bodies were downloaded or opened.

Dataset 8 now has **221 of 221 advertised listing pages observed**, yielding **11,034 unique dataset/file URL pairs**. The new pages add **10,485 unique URLs**, raising the overall catalog from 6,462 to **16,947**. Captures were imported at intermediate checkpoints and after the final page. Every snapshot URL and hash was checked on import, and the exporter retained all discovery provenance.

## Collection checkpoint

Datasets **1–8 and 12** have all advertised listing pages observed. Datasets **9, 10 and 11** remain at eleven observed pages each (0–10), with next unobserved page **11**. Their advertised listing ranges remain 10,675, 10,081 and 6,634 pages respectively. These are listing-page observations, not an exact full-release file total.

| Observed URL extension | Catalog records |
| --- | ---: |
| .pdf | 16,507 |
| .mp4 | 419 |
| .xlsx | 10 |
| .csv | 4 |
| .m4a | 3 |
| .xls | 2 |
| .mp3 | 1 |
| .avi | 1 |

Formats describe URL suffixes only; bodies and MIME types were not verified. Different formats with the same EFTA stem remain separate URL records. Later ingestion must support spreadsheets, CSV, audio and video as well as PDFs; no non-PDF processing or transcription was performed in this pass.

Searchable text remains the 100-PDF pilot. The 16,847 cataloged non-pilot records remain unprocessed. All pilot source text, dates, email records and editorial brief checks are unchanged.

## Validation and continuation

Audit the exact page range 0–220, all snapshot hashes and metadata URLs, uniqueness of dataset/URL pairs, unchanged prior file metadata and pilot records, extension totals, and an exact restore of the committed CSV/JSON manifests into a fresh working database. No page gaps or guessed EFTA filenames should be introduced.

Continue from page 11 in datasets 9–11 in bounded browser batches. With roughly 27,000 listing pages still unobserved across those three datasets, a documented official bulk manifest or supported discovery interface would be worth investigating before scaling manual pagination further. No third-party mirror, paid service or alternate API was used here.
