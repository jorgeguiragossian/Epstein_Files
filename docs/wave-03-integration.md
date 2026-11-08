# Wave 3 native-source integration — November 8, 2026

The ten dataset 10 PDFs are integrated as native searchable source text. The viewer grows to **130 PDFs / 1,916 pages**. All 120 prior document payloads, 163 email records, visible-copy groups and existing date reviews are unchanged. No new email occurrences were detected in this wave; the email workspace still has 163 occurrences across 31 source PDFs.

The reader now supports an optional document-level **Source quality review** panel. For these ten PDFs it shows the recorded layout limitations and a collapsible list of date-role observations. Each observation includes its role, source-assisted day/period/year reading where available, the exact native quote and a button opening the cited PDF page. Reporting periods, portfolio as-of dates, preliminary print/planned settlement dates, form/version markers and signature dates remain distinct.

The new source-quality metadata is stored separately from primary-date reviews in the local index and static bundle. No date-role observation automatically enters a primary-date filter. All ten wave 3 primary dates remain unreviewed: collection totals are **53 dated, 7 uncertain, 70 unreviewed**. Date-range analysis still covers 53 PDFs, with 36 prepared/source-checked editorial briefs and 17 date-evidence-only documents. Seventy-seven PDFs have no usable reviewed primary date.

Financial table text remains unverified as structured data. The quality panels identify flattened columns, repeated summary entries, mixed-currency/current-period/year-to-date measures and handwriting limitations. The native extraction is unchanged. The deposit-ticket raw OCR and eight provisional literal readings remain local in ignored extraction caches; they are not included in the public bundle. Its public notice explains the unresolved handwriting/date issue. Source PDFs remain linked at DOJ.

`data/pilot/viewer-batches.json` registers the `native_layout_review_v1` mode and pins acquisition, measurement and review manifests. Loading revalidates source bytes and complete page/quote bindings before indexing the quality payloads. The original header-layer and correspondence-review modes are preserved. Source-quality payloads are optional, so prior documents retain the same API records. The processing catalog still has 24,447 observed dataset/file URL pairs, now with 130 acquired/extracted records.

Validation passed: 89 offline Python tests, 61 static/Python API comparisons and real-cache HTTP smoke checks. Browser checks covered the source-quality panel, reporting-period evidence, the legal order's page-7 link and deposit-ticket limitations. The HTTP test also checks that a statement period does not make an unreviewed PDF appear in primary-date search. Comparison against the prior public bundle confirms preservation of previous document/email data and absence of the local editorial-reading layer.

Build with original and all three expansion caches available:

```powershell
python scripts/build-pages.py
python scripts/check-pages.py
node tests/test_static_pages.mjs
```

The expansion plan now has 30 acquired/extracted/integrated PDFs and 70 selected PDFs still unprocessed. Next useful work is a separate primary-date adjudication and reporting-period filtering milestone; do not silently equate a reporting-period endpoint with an issue date.
