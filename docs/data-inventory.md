# DOJ dataset inventory

Observation date: November 1, 2026 (America/Los_Angeles). Individual retrieval timestamps are recorded in UTC in the machine-readable inventory.

## Findings

The [DOJ disclosures index](https://www.justice.gov/epstein/doj-disclosures) links to all 12 numbered datasets. This pass read the first listing page of each dataset and attempted the last page advertised by its pagination. It did not download PDFs, audio, video, archives, or document text, and made no document HEAD requests.

We observed **525 dataset/file URL pairs** across the 12 first pages. These are listed URLs, not verified downloads or distinct underlying documents. Datasets 6 and 7 have no pagination links and list 13 and 17 PDFs respectively; their visible listings were fully inventoried. The other ten datasets advertise pagination, but requests to their last-page URLs returned **HTTP 403**. Their exact file totals remain unknown.

| Dataset | Advertised listing pages | File links observed | Visible listing coverage |
| --- | ---: | ---: | --- |
| [1](https://www.justice.gov/epstein/doj-disclosures/data-set-1-files) | 63 | 50 | First page only |
| [2](https://www.justice.gov/epstein/doj-disclosures/data-set-2-files) | 12 | 49 | First page only |
| [3](https://www.justice.gov/epstein/doj-disclosures/data-set-3-files) | 2 | 49 | First page only |
| [4](https://www.justice.gov/epstein/doj-disclosures/data-set-4-files) | 4 | 49 | First page only |
| [5](https://www.justice.gov/epstein/doj-disclosures/data-set-5-files) | 3 | 49 | First page only |
| [6](https://www.justice.gov/epstein/doj-disclosures/data-set-6-files) | 1 | 13 | Entire visible listing |
| [7](https://www.justice.gov/epstein/doj-disclosures/data-set-7-files) | 1 | 17 | Entire visible listing |
| [8](https://www.justice.gov/epstein/doj-disclosures/data-set-8-files) | 221 | 49 | First page only |
| [9](https://www.justice.gov/epstein/doj-disclosures/data-set-9-files) | 10,675 | 50 | First page only |
| [10](https://www.justice.gov/epstein/doj-disclosures/data-set-10-files) | 10,081 | 50 | First page only |
| [11](https://www.justice.gov/epstein/doj-disclosures/data-set-11-files) | 6,634 | 50 | First page only |
| [12](https://www.justice.gov/epstein/doj-disclosures/data-set-12-files) | 4 | 50 | First page only |

There are 27,701 advertised listing pages in total. This is a pagination observation, not a count of PDF pages or documents. The first pages contain either 49 or 50 links for paginated datasets; multiplying pagination by 50 would not establish an exact total. No conclusions about missing or removed records follow from those differences. Numeric gaps in EFTA filenames must not be treated as missing-file counts either.

## What the listings expose

- Dataset number, listing URL, file URL, EFTA filename, and pagination links.
- All 525 observed file links have a `.pdf` extension. File bodies and MIME types were not checked; this does not establish that the full collection contains only PDFs.
- No ZIP archive links were found in the 12 captured dataset listing pages. This does not establish that official bulk downloads are unavailable elsewhere; no archive URLs were guessed or probed.
- The listings do not provide usable per-document dates, people, email headers, byte sizes, PDF page counts, OCR quality, or document checksums. Those fields remain unknown until a document pilot.
- The files are presented as document links rather than a structured analytical dataset. The extracted metadata will need its own documented schema.

## Source context and limits

The [Epstein Library home page](https://www.justice.gov/epstein) displays a last-updated date of September 11, 2026 at observation time and says further documents may be released. That date applies to the home page; it is not a verified release date for each file or dataset.

DOJ says its search can be incomplete or unreliable for some formats, including handwriting. The disclosures page describes redactions and notes that some sensitive personal information may have been inadvertently included. Our processing should preserve redactions and retain a correction/removal path rather than treating a public URL as a reason to automatically republish extracted personal details.

The pages include an age-verification interface. The inventory read HTML returned by ordinary public GET requests; no age-verification cookies were set and no access controls were bypassed. HTTP 403 failures are preserved as failures. Their cause was not established. A future cataloging pass should resolve supported access before scaling requests.

Court Records, FOIA, Prior DOJ Disclosures, and House disclosures are separate sections or sources. They are outside this inventory of the 12 numbered datasets; possible overlap has not been measured.

## Evidence and reproduction

Files under [`data/inventory/2026-11-01/`](../data/inventory/2026-11-01/):

- `datasets.csv`: one summary row per dataset; empty analytical fields mean unknown.
- `observed-files.csv`: 525 observed dataset/file URL pairs with discovery source and retrieval time; not a complete corpus manifest.
- `inventory.json`: dataset summaries, observed links, source snapshots, retrieval timestamps, HTML SHA-256 hashes, and failed requests.
- `listing-*.html`: the 12 accessible first-page HTML responses.
- `context-*.html`: accessible Library home and disclosures index HTML responses.

These hashes authenticate our saved HTML snapshots, not the linked document contents. Server timestamps and file extensions are not substitutes for document dates or content verification. The snapshot may change on later runs.

Run from the repository root in PowerShell 7:

```powershell
./scripts/inventory-doj.ps1 -OutputDirectory ./data/inventory/YYYY-MM-DD
```

Use a new output directory to retain earlier observations. The script makes sequential public listing requests, pauses briefly between dataset requests, records failures, and downloads no linked documents. A failed dataset must remain incomplete; an absent record does not mean a dataset is empty. `pagination_implied_files`, when populated, assumes uniform intermediate pages unless all listing pages were observed. Inspect `count_status` before using it.

## Recommended next milestone

Conduct a bounded **100-document extraction pilot** across all 12 datasets before selecting a web stack or bulk storage approach. One simple allocation is all 30 listed files from datasets 6 and 7, plus seven files from each of the other ten datasets. This is a coverage pilot, not a statistically representative sample. Select across listing positions when supported access is resolved; record any first-page-only selection bias.

For each pilot document measure download availability, actual bytes, content hash, page count, text extraction quality, OCR need, document type, dates with evidence, and whether genuine sender/recipient headers can be extracted. Preserve page references and distinguish a document date from dates merely mentioned in its text. Confirm that the sample contains useful correspondence before promising contact analysis; add a separately labeled targeted email sample if necessary.

Use those measurements to decide storage, processing cost, and the first searchable experience. Current evidence supports committing small manifests, provenance, schemas, and scripts to Git; it does not yet support a total storage estimate or a decision to put every original document in ordinary Git history.
