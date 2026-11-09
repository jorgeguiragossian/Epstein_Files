# Wave 7 photograph integration

The ten dataset 2 PDFs are integrated with native text and scoped photograph-quality notices. The public sample now contains **170 PDFs / 2,208 pages**. Eleven photographic pages have sparse stamp/artifact-only extraction; this does not imply empty images. Source PDFs remain linked to DOJ, with both EFTA00003601 pages preserved in source order.

The EFTA00003726/EFTA00003792 notices explain partial camera overlays omitted from native text: day-number/time fragments do not supply complete calendar dates. No missing month/year, face identity, location, ownership, relationship, image-derived caption or verified duplicate claim is inferred. No OCR was needed for substantial prose in this review.

The explicit `native_image_quality_v1` mode validates pinned quality evidence and source/page hashes without requiring nonexistent OCR results. It rejects image-only dispatch if the quality record says source-assisted OCR review is needed; existing handwritten-log/deposit OCR validation remains required through its existing modes. Prior quality payloads are unchanged.

All ten new primary dates are unreviewed. Totals: **70 dated, 30 uncertain, 70 unreviewed**. Existing primary-date/reporting-period cohorts and frequencies remain unchanged. There are still 194 parser occurrences, 120 scoped candidate reviews, 53 body breakdowns, 36 prepared/source-checked briefs, 34 date-evidence-only documents and six reporting-period PDFs.

Validation: 94 offline tests, 107 static/Python comparisons, real-cache HTTP checks and browser checks of the partial-overlay notice and second-page source link. All 160 prior document payloads, 194 email records/groups and prior analysis entries are exactly preserved. Tests cover image-only quality dispatch without fabricated OCR, unchanged native candidates and refusal to skip required OCR review.

The processing catalog retains 24,447 observed URL pairs and now records 170 acquired/extracted PDFs. The saved expansion plan has **70 acquired/extracted/integrated PDFs and 30 unprocessed**. PDF/native/rendered caches remain ignored; builds require original and seven-wave caches, plus prior local OCR evidence. Do not regenerate the saved selection.

Next: primary-date adjudication of these ten PDFs, retaining uncertainty where capture/issue dates are not established, particularly incomplete overlays. Then acquire the remaining saved dataset 3, 4 and 5 batches.
