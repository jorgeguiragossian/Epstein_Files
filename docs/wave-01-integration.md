# Ten-file dataset 8 integration — November 7, 2026

The viewer and static publication now include **110 PDFs, 1,836 pages and 122 email-layout candidate occurrences**. The original 100 document records and 114 email records are preserved. The ten new PDFs add 49 native-text pages and eight candidate occurrences across seven documents.

## Date and review scope

All ten added document dates are **unreviewed**, with no primary date. Parsed email timestamps remain candidates and do not substitute for a document-date review. Date-filtered word clouds and timeframe briefs therefore retain the same 36 eligible dated documents; 74 PDFs now lack a usable reviewed date (70 unreviewed and four uncertain). All 36 prepared page briefs and their recorded editorial checks remain unchanged.

The combined email workspace has 48 source-reviewed candidates in 21 documents, nine source-linked body breakdowns, three adjacent-page checks and 14 observed header name/address associations. Only three of the eight new candidates received the targeted header/body review. The other five remain unreviewed. No unique-message claims, account ownership or contact rankings are enabled.

## Native and derived text

Document search, page text, literal-name mentions and exports use **native extraction**. The explorer never replaces Front with From or silently assigns the unresolved header fragment.

Three email candidates have explicit source-reviewed derived header layers. The email card identifies the layer, explains the limited label/fragment handling, links to native page text, and retains the exact native header lines. The unassigned fragment remains visible as unresolved metadata. Source-linked body partitions distinguish top-level text from quoted material without changing parent bodies or counting nested quotes as new messages.

## Reproducible batches

`data/pilot/viewer-batches.json` explicitly registers the ten-file expansion and pins its selection, download, metrics and review evidence hashes. Build validates source PDF/extraction bindings, checks identifier collisions before indexing, rebuilds derived layers from native data, and revalidates candidate fingerprints and lossless body partitions. A changed evidence file requires an explicit registry update and appropriate review; cached derived JSON is not accepted as the sole review authority.

The original pilot folder remains intact. A fresh clone needs both original and wave PDF/native-text caches. Reconstruct the wave with:

```powershell
python scripts/pilot.py download --out data/pilot/2026-11-07-wave-01 --age-confirmed
python scripts/pilot.py analyze --out data/pilot/2026-11-07-wave-01
python scripts/build-pages.py
```

Historical download metadata can change during reconstruction; compare actual bytes and evidence before updating pinned manifests. Do not automatically renew editorial checks for changed sources.

The static bundle exposes the newly integrated native text, candidate bodies and labeled derived header metadata. Source PDFs remain on DOJ; no PDFs or credentials are copied into the publication. Local caches remain ignored on main. The repository owner authorized continuing the published viewer with this integration.

## Processing catalog

`data/catalog/processing-batches.json` registers the expansion for catalog processing-status exports. Its ten URL rows now record acquired bytes, source hashes and PDF page counts as expansion records. The 24,447 discovered URLs and listing provenance do not change. Metadata is joined by complete URL rather than EFTA stem, preserving different formats under the same stem.

## Validation

Regression checks cover evidence-hash rejection, duplicate document/candidate identifiers, preserved prior records, unreviewed new dates, native versus derived headers, complete body reconstruction, existing date/name search, static/Python API parity and source PDF links. Browser checks cover the fragment card, quote breakdown and native-text link. This milestone expands publication coverage, not full-release or whole-document review coverage.

The remaining 90 selected expansion PDFs remain unprocessed. The next useful milestone is primary-date review for these ten new documents, followed by a further bounded acquisition batch.


## Primary-date review completed November 7

The separate wave `date-reviews.json` assigns nine primary dates: seven containing-email sent dates, one court-order date and one memorandum issue date. The multi-day roster EFTA00009713 remains uncertain; its July 22, August 9 and August 10 pages do not establish one assembly date. EFTA00034623 is assigned July 24, 2019, the memorandum issue date, rather than its July 23 activity period.

Each assignment binds the PDF SHA-256 and an exact native-text quote on PDF page 1. Codex visually compared the source pages; these are editorial assignments, not independent authentication. The roster's additional date-bearing pages 18 and 25 were also inspected. The registry pins this review file, and indexing rejects unknown, duplicate, stale or unsupported date assignments before rebuilding the database. Reproduce the curated manifest with `python scripts/prepare-wave-dates.py`.

Published totals are now 45 dated, 5 uncertain and 60 unreviewed PDFs. Date filters and word clouds include the nine new dated documents. Timeframes show nine date-evidence-only documents alongside the unchanged 36 prepared and source-checked briefs. Native page text and all 122 email candidate records remain unchanged. The next milestone is a further bounded acquisition batch from the remaining 90 selected PDFs.
