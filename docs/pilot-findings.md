# 100-document extraction pilot

Sample selected November 1, 2026 (America/Los_Angeles). Individual download and processing times are recorded in UTC. This is a feasibility pilot, not a representative analysis of the full DOJ collection.

## Results

All **100 selected PDFs across all 12 datasets** downloaded successfully after the user confirmed eligibility for DOJ's standard age verification. All **1,787 PDF pages** were processed with pypdf 6.10.0 using their existing text layers. No new OCR or AI calls were performed.

| Measurement | Result |
| --- | ---: |
| PDF download bytes | 284,273,900 (271.1 MiB) |
| Smallest / largest PDF | 12,090 / 39,755,125 bytes |
| Pages processed | 1,787 of 1,787 |
| Low-text pages flagged for review | 249 (13.9%) |
| Documents with at least one low-text page | 52 |
| Documents with only low-text pages | 25 |
| Date-string occurrences / documents containing them | 1,200 / 62 |
| Candidate email header blocks / documents containing them | 103 / 12 |
| Exact duplicate content-hash groups | 0 |

The sample consists of all 13 visible files in dataset 6 and all 17 in dataset 7, plus seven evenly spaced filename positions from the accessible first-page pool of each other dataset. Full-corpus pagination access remains unresolved. Selection is deterministic and biased toward those first pages; these percentages and sizes must not be projected onto the full collection.

| Dataset | Documents | PDF pages | Low-text pages | Candidate email blocks |
| --- | ---: | ---: | ---: | ---: |
| 1 | 7 | 7 | 7 | 0 |
| 2 | 7 | 7 | 7 | 0 |
| 3 | 7 | 161 | 116 | 0 |
| 4 | 7 | 67 | 45 | 0 |
| 5 | 7 | 7 | 5 | 0 |
| 6 | 13 | 487 | 31 | 0 |
| 7 | 17 | 660 | 11 | 0 |
| 8 | 7 | 51 | 2 | 17 |
| 9 | 7 | 153 | 1 | 5 |
| 10 | 7 | 62 | 0 | 76 |
| 11 | 7 | 12 | 2 | 1 |
| 12 | 7 | 113 | 22 | 4 |

## What this means for the website

**Search is feasible, but coverage must be visible.** Every file yielded some text, yet an EFTA stamp alone can produce a misleading extraction success. We flag pages with fewer than 80 alphanumeric characters after removing EFTA stamps. This is a screening heuristic, not a readability score or confirmed OCR requirement. A visual spot check found a redacted photograph among the sparse pages; OCR would not turn it into a normal text document. Another reviewed page had recognition artifacts despite substantial extracted text.

**Time filters need date roles and an undated category.** The 1,200 date matches include repeated references, possible regex false positives, and dates mentioned inside documents. Automated `document_date` remains null for every file. The four-page visual spot check confirms that a reporting form can separately label a report date and contact date, and a transcript cover can contain multiple dates. A small set of reviewed date-role examples is recorded in `manual-review.json`; it does not validate the full set of matches. Date filters must distinguish sent dates, document dates, event dates, unknown dates, and uncertain readings.

**Contact analysis needs message parsing and identity evidence.** The 103 header blocks are unverified candidates, not unique messages, contacts, or messages sent by Epstein. One 41-page PDF accounts for 76 blocks. Quoted threads and repeated productions must be grouped before counts are meaningful. A reviewed email has redacted To/From values, To before From, and an inline date; our strict From-then-To-plus-Date-or-Sent detector misses it. Its measured count is zero despite its visible email layout. Parser recall is therefore known to be incomplete. Redacted participants should remain unknown; they must not be inferred from nearby names or message topics. Epstein's own accounts and aliases also require evidence before classifying a message as to/from him.

**Word clouds need document-type filters and text cleanup.** Extracted material includes transcript line numbers, repeated headers, EFTA stamps, quoted email chains, and recognition errors. The local extraction contains basic word counts, but these are raw English-regex counts, not a publication-ready word cloud. Comparing periods will require deduplication and a documented stopword/boilerplate policy.

**Summaries can retain page-level sources.** Every extracted page has a 1-based PDF page number and text. This gives us a foundation for cited summaries, but date assignment, coverage, redaction review, and summary validation still need work. No AI summary or person index was generated in this pilot. We did not assess named-person extraction accuracy.

## Storage and openness

The small manifests, measurements, source URLs, hashes, code, and review notes are in the repository. PDFs (`cache/`), raw extracted text/contact values (`extractions/`), and QA images (`tmp/`) remain local and are ignored by Git while we review quality and redactions. Publishing the source and manifests does not publish those local caches.

Keep provenance and processing code in ordinary Git. Defer the full original-document storage decision until we have complete corpus sizes and a publication policy; this biased 271 MiB pilot cannot establish total storage or processing cost. We also have not measured full OCR expense, AI expense, or a hosting budget.

## Evidence and verification

See [`data/pilot/2026-11-01/`](../data/pilot/2026-11-01/):

- `selection.json`: all 100 official source URLs, dataset numbers, selection positions, and inventory hash.
- `downloads.json`: observed HTTP results, final URLs, bytes, SHA-256 hashes, and retrieval timestamps.
- `metrics.csv` / `metrics.json`: per-document measurements; JSON also includes page measurements and unvalidated date references.
- `summary.json` / `dataset-summary.csv`: aggregate measurements.
- `manual-review.json`: four-page visual spot check and known failure cases.

Verification checked all 100 cached PDF sizes and hashes, page-text counts and numbering, evidence references, and manifest/metric agreement. Offline tests exercise the exact sample allocation, EFTA-stamp-only pages, page-based date evidence, and rejection of a standalone To/Date heading as an email. The visual review is limited to four pages and does not establish corpus-wide text or redaction accuracy.

## Reproduce

Use Python 3.12 with `pip install -r requirements-pilot.txt`. In a fresh clone, reuse the committed selection and run:

```powershell
python scripts/pilot.py download --age-confirmed
python scripts/pilot.py analyze
python scripts/summarize-pilot.py
python -m unittest discover -s tests -v
```

Only pass `--age-confirmed` after confirming adult eligibility for DOJ's gate. The downloader uses DOJ's standard verification cookie, sequential requests, a 64 MiB per-file cap, a 512 MiB total cap, and no automatic retries. It verifies a PDF signature and records errors or gate redirects rather than treating HTML as a PDF. Existing valid cached downloads are reused; missing files in a fresh clone are downloaded again. Changed or missing extraction caches are rebuilt. Extraction is isolated per file with a 120-second timeout. Limits may leave a future run incomplete; inspect status fields rather than assuming all downloads succeeded. Use a separate output directory and `pilot.py select --out ...` when creating a new selection; summary and optional visual-review helpers currently target this dated pilot.

Optional visual QA: `python scripts/render-pilot-review.py` requires pypdfium2 and Pillow and writes an ignored contact sheet. These optional packages are available in the bundled desktop runtime but are not part of the core extraction requirements.

## Recommended next step

Build a small **local pilot document viewer** with full-text search, dataset filtering, direct PDF/page links, and visible extraction-quality flags. Include a review interface for date roles and redacted/ambiguous email headers before enabling timeline summaries or contact rankings. This gives us a way to validate the data with real documents while keeping the scope small.
