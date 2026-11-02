# Local pilot document explorer

The first viewer searches the 100-document pilot, not the full DOJ collection. It runs on your computer and uses the PDFs and page text already downloaded during the pilot.

A [GitHub Pages version](github-pages.md) also publishes the full authorized pilot text/email export for browser-only use. The instructions below describe the original local Python application; raw caches remain ignored on `main`, while the generated public export lives on `gh-pages`.

## Run

From the repository root:

```powershell
python viewer/server.py
```

Open **http://127.0.0.1:8765**. Stop with Ctrl+C. An alternative port can be supplied with `--port 8766`. Python 3.12 with SQLite FTS5 is sufficient to run the viewer; there is no frontend build, package install, external font request, API key, or AI service.

If your Python installation does not have SQLite FTS5, use an installation that includes it. In the Codex desktop workspace, the bundled Python runtime works.

### Fresh clone

The repository contains the source, selection, measurements, and evidence manifests. PDFs, unreviewed text, and the search index are ignored. Recreate the pilot cache first (see [pilot findings](pilot-findings.md)):

```powershell
python -m pip install -r requirements-pilot.txt
python scripts/pilot.py download --age-confirmed
python scripts/pilot.py analyze
python viewer/server.py
```

Pass `--age-confirmed` only after confirming eligibility for DOJ's age gate. The viewer checks that original file hashes and extraction source hashes agree before indexing. Missing or changed caches produce a startup error rather than silently showing an incomplete collection. The SQLite index is rebuilt at startup and stays under ignored `data/viewer/`.

## What works

- Search all words within the same extracted PDF page. Results group matching pages by document and show the first matching page. Search is case-insensitive and uses SQLite's Unicode tokenizer. It does not do fuzzy matching, stemming, entity resolution, or boolean query syntax.
- Find an exact EFTA document ID, such as `EFTA00008529`.
- Filter by one of 22 curated person-name phrases and inspect matching PDF pages and highlighted text. See [person-name matching and limits](person-filter.md), including source review, deferred variants, and a reproducible coverage snapshot. These are lexical mentions, not verified identity or relationship assertions.
- Filter by dataset and by whether a document includes low-text pages or has at least one page with substantial text. These quality filters apply to the document; an individual matching page may have different quality.
- Read extracted page text, highlighted search terms, matching-page links, and previous/next or direct page navigation.
- Open the local original PDF at the selected file page or follow the official DOJ source link. A browser PDF viewer may vary in whether it honors `#page=`. DOJ may require its own age verification.
- Filter by reviewed primary date with inclusive From/Through bounds; browse uncertain, reviewed-undated, and unreviewed documents separately. See [date review and filter semantics](date-review.md). The current pilot has 17 reviewed dates, 3 uncertain records, and 80 unreviewed records.
- Inspect page date-string candidates, extraction coverage, email-header candidate counts, source SHA-256, and primary-date evidence/rationale. Primary dates come from separate source-based editorial reviews, not automatic promotion of every date mention.
- Reopen the current view using its URL, including search/filter values, document ID, and PDF page.
- Open **Email review** in the header to inspect parsed email candidates, unresolved fields, detected body segments, and visible-copy groups with source-page links. See [parsing, grouping, and limits](email-review.md). This is a review workspace, not a contact-ranking feature.

Search results are ordered by dataset, document ID, and PDF page, rather than by relevance. Person filtering currently uses a small curated name vocabulary and does not verify identities, wrongdoing, or relationships. OCR errors, redactions, and missing text affect matches. No new OCR, AI summaries, contact rankings, or public hosting is included in this step.

## Local scope

The server binds only to `127.0.0.1`. It serves a small explicit set of UI/API routes and known pilot PDFs, rather than exposing the repository as a file directory. Search uses parameterized SQL and literal word queries. Text is rendered as text nodes, not interpreted as HTML. The server does not log search strings, load analytics, or send document text to an external service. Search terms can still be visible in local browser history because views have URLs.

This is a development application, not a public deployment configuration. Keep the raw cache and derived index out of public hosting until we review content handling and design the production data layer.

## Validation

```powershell
python -m unittest discover -s tests -v
```

The viewer's offline tests use synthetic documents so a fresh clone can test page grouping, literal queries, filters, input errors, page references, and PDF byte ranges without having the ignored source cache. The existing pilot tests also run. Browser QA covers search, dataset/quality filters, the reader, page navigation, source links, empty results, and a narrow viewport.

With the viewer running on its default port, `python tests/smoke_viewer.py` checks the real pilot over HTTP, including page text, expected search counts, invalid inputs, restricted file routes, and partial PDF responses.

## Git milestones

Commit and push at small, verified milestones: inventory and extraction pilot; working local viewer; reliable dates/person/message parsing; then each larger analysis feature. Keep originals and unreviewed text out of ordinary Git history during the pilot. The application source and reproducible data manifests stay in this repository.
