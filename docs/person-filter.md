# Page-based person-name filtering

The curated vocabulary now contains **22 name phrases**, expanded from the original eight, with source evidence from the existing pilot. It does not provide a comprehensive person index, identify unnamed people, resolve identities, or classify involvement in events.

## Reviewed vocabulary

The original entries remain: Bill Gates, Boris Nikolic, Ghislaine Maxwell, Jeffrey Epstein, Leon Black, Prince Andrew, Richard Kahn, and Sigrid McCawley. Fourteen additional source-checked phrases are listed below. These are labels for strings visible in pilot records, not biographical profiles or claims about the people named. Selection was purposive, not an exhaustive name extraction or a ranking of importance or involvement.

| Added name phrase | Source file | PDF page |
| --- | --- | ---: |
| Alan Dershowitz | EFTA00009329 | 14 |
| Alexander Acosta | EFTA00009229 | 1 |
| Audrey Strauss | EFTA00008874 | 18 |
| Barry Krischer | EFTA00009229 | 37 |
| Darren Indyke | EFTA01263156 | 1 |
| Gerald Lefcourt | EFTA00009329 | 14 |
| Guy Lewis | EFTA00009329 | 29 |
| Jay Lefkowitz | EFTA00009016 | 67 |
| Jeanne Christensen | EFTA02731485 | 1 |
| Ken Starr | EFTA00009016 | 34 |
| Larry Cohen | EFTA02730265 | 1 |
| Lilly Ann Sanchez | EFTA00009329 | 23 |
| Reid Weingarten | EFTA00009658 | 5 |
| Roy Black | EFTA00009329 | 14 |

The fourteen additions are supported by twelve distinct cited pages, visually compared with their extracted text. PDF page numbers are file positions, not printed transcript page numbers: for example, the Alan Dershowitz source is PDF page 14 but printed page 114.

[`people.json`](../data/pilot/2026-11-01/people.json) stores each entry's ID, display label, literal matching form, cited file ID, 1-based PDF evidence page, short name-only quote, PDF SHA-256, and review method. The initial source pages were visually reviewed during the date milestone, and the additions were visually reviewed in this expansion. Exact name strings were checked against extraction. Counts elsewhere are automatic lexical matches, not individually reviewed identity assertions.

[`people-coverage.json`](../data/pilot/2026-11-01/people-coverage.json) contains reproducible document, page, and occurrence counts for all 22 entries across the same 100 PDFs / 1,787 pages. It includes hashes of the vocabulary, pilot selection, and pilot metrics. Counts overlap between names and should not be summed as unique documents or people. The live API is checked against this snapshot.

[`name-review-notes.json`](../data/pilot/2026-11-01/name-review-notes.json) records three observed forms deliberately deferred from alias merging: Jeffery Epstein, Lillian Sanchez, and Darren K. Indyke. Each has a source quote, PDF page, source hash, and reason. The notes do not establish that any pair of forms identifies the same person.

## Matching and counts

- The matcher ignores case, permits whitespace or line breaks between name words, and requires whole-name boundaries. It will not match a longer surname simply because it starts with the same letters.
- Only the listed phrase is accepted. Initials such as JE, standalone surnames, email addresses, unlisted nickname mappings, and fuzzy spelling variants are excluded. A source phrase such as Ken Starr remains literal; it is not expanded to another first-name form. A different spelling such as Jeffery instead of Jeffrey is not automatically merged. Namesakes remain possible.
- The filter applies to individual PDF pages. Combining it with search words requires both the name and all search words to appear on the same page, rather than somewhere in the same multi-page file.
- Results group matching pages by document and open the first matching page. The reader highlights the selected phrase and provides links to other matching pages.
- Document and page counts beside the selector describe the complete 100-document pilot. Current filtered result counts are shown separately. Selecting a dataset, quality flag, or reviewed date range narrows results.
- Per-page occurrence counts include repeated headers, quoted threads, and reproduced material. They are not unique people, messages, communication frequency, or relationship counts.

The reader's **Names matched on this page** section lists occurrences and links to the vocabulary's cited source page. No match from this vocabulary does not establish that a page contains no names. Missing results may reflect incomplete vocabulary, OCR errors, redactions, spelling differences, or the limited sample.

## Implementation and validation

The SQLite index stores the vocabulary and derived page matches locally under ignored `data/viewer/`. `/api/people` provides pilot-wide coverage and source metadata. `/api/search?person=ghislaine-maxwell` applies the filter, and the page-detail API includes matched strings with Python Unicode character offsets in that page's extracted text. The UI highlights text by the same whole-name phrase semantics rather than treating those offsets as JavaScript UTF-16 indices.

Name-source hashes and quotes are checked before indexing, alongside existing PDF and extraction hashes. The current schema deliberately permits one literal matching form per vocabulary entry; adding aliases requires a separate evidence design. Unknown filter IDs return HTTP 400 rather than broadening the search.

To reproduce the vocabulary, coverage snapshot, and deferred-form notes from the existing ignored pilot cache, run `python scripts/prepare-people.py`. The script verifies each listed name against its cited extracted page. Add `--render-expansion` to recreate three local QA contact sheets for the twelve expansion evidence pages; this optional step requires pypdfium2 and Pillow. Original PDFs, page images, raw page text, and the derived index remain ignored; only source metadata, names, counts, and review decisions are committed.

Validation includes synthetic tests for whole-name boundaries, case and line breaks, overlapping-form deduplication, distinct document/page/occurrence counts, same-page search semantics, combined dates and datasets, unknown IDs, and source-evidence mismatches. Live API and browser checks cover real pilot results, highlights, page-level evidence, combined dates, empty results, and restored URL filters.

The next data-quality step is evidence-based alias handling and email-message normalization/deduplication before contact rankings. This 22-entry pilot still does not fulfill full-corpus person extraction. No file collection, date annotations, or matching rules changed during this expansion.
