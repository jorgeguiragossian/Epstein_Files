# Resume checkpoint — November 8, 2026

Wave 3 is integrated with native text and document-level Source quality review panels. The public viewer now has 130 PDFs / 1,916 pages. There are still 163 email candidate occurrences across 31 PDFs, 89 scoped source-reviewed candidates across 27 PDFs and 28 body breakdowns. See `docs/wave-03-integration.md`.

The ten wave 3 dataset 10 PDFs expose table/layout limitations and 14 distinct date-role observations with exact native quotes and source-page buttons. These observations are separate from primary dates. All ten primary dates remain unreviewed. Overall: 53 dated, 7 uncertain, 70 unreviewed. Date-range analysis still covers 53 PDFs, with 36 existing prepared/source-checked editorial briefs and 17 date-evidence-only documents.

All 42 wave 3 source pages were inspected across acquisition/OCR/layout passes. Financial cells and transaction identities are not independently verified; flattened columns and repeated summaries must not drive ledger totals or relationship inferences. Native extraction is unchanged. Deposit-ticket OCR was inadequate; eight provisional literal readings remain only in the ignored local editorial layer. Neither raw OCR nor those readings is included in the public bundle.

Validation passed: 89 offline tests, 61 static/Python API comparisons, real-cache HTTP smoke checks and browser verification of notices, reporting-period evidence, source-page navigation and handwriting limitations. Comparison with the preceding public bundle confirms all 120 prior document payloads, 163 email records/groups and existing date reviews preserved.

Next useful milestone: adjudicate primary dates where source roles support it and add a separate reporting-period filter for statements. Do not silently substitute a reporting-period endpoint for an issue date. The expansion plan has 30 acquired/extracted/integrated PDFs and 70 selected PDFs unprocessed. Do not regenerate the saved selection.

Original PDFs, raw extractions, local SQLite and OCR/editorial-reading caches remain ignored. Main contains source, measurements and evidence manifests; gh-pages contains the authorized native text and source-review payloads. Builds require original and all three expansion caches. Explicit registries pin review evidence; changed source bytes require re-review rather than automatic hash renewal.
