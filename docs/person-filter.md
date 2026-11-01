# Page-based person-name filtering

This milestone adds a small curated vocabulary of **eight name phrases**, with source evidence from the existing pilot. It does not provide a comprehensive person index, identify unnamed people, resolve identities, or classify involvement in events.

## Initial vocabulary

Bill Gates, Boris Nikolic, Ghislaine Maxwell, Jeffrey Epstein, Leon Black, Prince Andrew, Richard Kahn, and Sigrid McCawley. These are labels for strings visible in pilot records, not biographical profiles or claims about the people named. The choice is a bounded feature demonstration, not a ranking of importance or involvement.

[`people.json`](../data/pilot/2026-11-01/people.json) stores each entry's ID, display label, literal matching form, cited file ID, 1-based PDF evidence page, short name-only quote, PDF SHA-256, and review method. The source pages were visually reviewed during the date milestone and the exact name strings were checked against their extraction. Counts elsewhere are automatic lexical matches, not individually reviewed identity assertions.

## Matching and counts

- The matcher ignores case, permits whitespace or line breaks between name words, and requires whole-name boundaries. It will not match a longer surname simply because it starts with the same letters.
- Only the listed phrase is accepted. Initials such as JE, standalone surnames, email addresses, nicknames, and fuzzy spelling variants are excluded. A misspelling such as Jeffery instead of Jeffrey is not automatically merged. Namesakes remain possible.
- The filter applies to individual PDF pages. Combining it with search words requires both the name and all search words to appear on the same page, rather than somewhere in the same multi-page file.
- Results group matching pages by document and open the first matching page. The reader highlights the selected phrase and provides links to other matching pages.
- Document and page counts beside the selector describe the complete 100-document pilot. Current filtered result counts are shown separately. Selecting a dataset, quality flag, or reviewed date range narrows results.
- Per-page occurrence counts include repeated headers, quoted threads, and reproduced material. They are not unique people, messages, communication frequency, or relationship counts.

The reader's **Names matched on this page** section lists occurrences and links to the vocabulary's cited source page. No match from this vocabulary does not establish that a page contains no names. Missing results may reflect incomplete vocabulary, OCR errors, redactions, spelling differences, or the limited sample.

## Implementation and validation

The SQLite index stores the vocabulary and derived page matches locally under ignored `data/viewer/`. `/api/people` provides pilot-wide coverage and source metadata. `/api/search?person=ghislaine-maxwell` applies the filter, and the page-detail API includes matched strings with Python Unicode character offsets in that page's extracted text. The UI highlights text by the same whole-name phrase semantics rather than treating those offsets as JavaScript UTF-16 indices.

Name-source hashes and quotes are checked before indexing, alongside existing PDF and extraction hashes. The current schema deliberately permits one literal matching form per vocabulary entry; adding aliases requires a separate evidence design. Unknown filter IDs return HTTP 400 rather than broadening the search.

To reproduce the vocabulary from the existing ignored pilot cache, run `python scripts/prepare-people.py`. The script verifies each listed name against its cited extracted page. Original PDFs, page images, raw page text, and the derived index remain ignored; only source metadata and names are committed.

Validation includes synthetic tests for whole-name boundaries, case and line breaks, overlapping-form deduplication, distinct document/page/occurrence counts, same-page search semantics, combined dates and datasets, unknown IDs, and source-evidence mismatches. Live API and browser checks cover real pilot results, highlights, page-level evidence, combined dates, empty results, and restored URL filters.

The next data-quality step is to expand the reviewed vocabulary and build evidence-based alias handling, before attempting a communication or relationship network. The eight-entry pilot does not fulfill full-corpus person extraction.
