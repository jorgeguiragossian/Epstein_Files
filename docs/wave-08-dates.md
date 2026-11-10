# Wave 8 primary-date review — November 9, 2026

EFTA00004231 receives a primary **evidence-received date of July 17, 2020**, explicitly labeled as that role in document results, reader and timeframe cards. The handwritten source field says Date Received with literal `7/17/20`; the normalized 2020 date uses the contemporary US evidence-receipt context. Native extraction is damaged and unchanged. This is evidence handling, not image capture, USB/media creation or independently authenticated chain of custody. Template revision dates remain separate.

The other nine primary dates remain **uncertain**:

- EFTA00003434: photograph has no established full capture/issue date.
- EFTA00003858 and EFTA00003931: package/item-not-scanned records; template revisions/product copyright do not establish a single record issue day.
- EFTA00004012: photo-processing sleeve date field blank; only PDF pages 1/14/27 visually inspected.
- EFTA00004060: covers/promotions provide month/anniversary/weekly references without a complete primary day.
- EFTA00004577 and EFTA00005091: only first/middle/last pages inspected; captions/filenames/index labels do not establish a single assembly or issue day.
- EFTA00005536: redacted publication/image pages lack an established complete primary date.
- EFTA00005586: only PDF pages 1/60/119 inspected; labels/stamps and blacked-out content do not establish a full date or hearing/filing status.

The 28-page visual scope is retained and supporting hashes bind each inspected page. Larger files are not represented as fully source-reviewed. Exact native quotes anchor evidence pages; for uncertain dates some anchors are identifiers or empty-date labels, not positive date evidence. No redactions, names, media contents or image relationships are inferred.

A new supported `evidence_received` date role prevents the receipt from being mislabeled as an email, report issue or photo date. Existing roles and payloads remain unchanged. Earlier OCR assessment findings are historical recognition findings, distinct from this later source-assisted date adjudication; the reader explains that a reviewed date does not correct native text. Raw OCR and provisional literal layers remain local. Only the adjudicated source date reading and rationale are public; no other provisional fields are promoted.

Totals: **71 dated, 49 uncertain, 60 unreviewed**, across 180 PDFs / 2,556 pages. One additional document enters primary-date search/word clouds and date-evidence-only timeframe cards. There are still 36 prepared/source-checked briefs, now with 35 date-evidence-only documents; six reviewed reporting-period PDFs remain unchanged. No new content summaries are prepared.

Validation: 97 offline tests; 121 static/Python comparisons; real-cache HTTP smoke checks. Tests accept the explicit receipt role, exclude template-revision dates and show the receipt as date evidence only. All 194 email records/groups and native/quality document fields are preserved; only ten document date-review payloads change. Public browser checks verify the evidence-received role and source-reading rationale.

Reconstruct via `scripts/prepare-wave-08-dates.py` after source comparison. Exact PDF/native/page evidence must match. Source PDFs, extraction/render/OCR/literal caches stay ignored. Next: acquire the ten saved dataset 4 selections and perform extraction-quality/source review. Eighty expansion PDFs are integrated; twenty dataset 4/5 selections remain unprocessed. Do not regenerate selection.
