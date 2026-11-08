# Wave 3 acquisition and quality triage — November 8, 2026

The ten dataset 10 PDFs from the unchanged expansion selection were acquired through their official DOJ listing links using normal browser downloads. The prior adult-eligibility authorization covered the age prompt. PDF signatures, source SHA-256 and the existing individual/batch byte limits were checked before caching. Actual response headers were not captured; the acquisition manifest does not invent them.

All ten native extractions succeeded: **42 pages and 3,125,888 bytes**. The batch includes a legal application, a property/tax record, a preliminary settlement statement, a deposit ticket and account/portfolio statements. Neither the simple header heuristic nor the current email parser detected email occurrences. This does not establish that no correspondence could exist in source material beyond the inspected scope.

The quality pass visually inspected 14 PDF pages: all ten first pages, EFTA01281641 page 2, and EFTA01283668 pages 2, 3 and 14. Native extraction covers all 42 pages. `data/pilot/2026-11-08-wave-03/quality-review.json` records source hashes, inspected-page text hashes, findings and scope. This is not whole-document review, independent authentication or verification of financial data.

The main extraction issue is EFTA01281641, a deposit ticket. Handwritten content on page 1 is poorly captured despite passing the text-density threshold. Page 2 has rotated handwritten content largely missing from extraction and is the only automatically flagged low-text page. Both need source-assisted OCR/transcription review; neither has been silently corrected. No OCR was run during acquisition.

EFTA01283668 pages 2 and 14 visibly say they were intentionally left blank. Branding and source notices supply some extracted text, so the density heuristic does not flag them. These are expected sparse pages, not observed text-loss failures. Page 3 contains side-by-side financial tables. The statement, tax and settlement records also need column/row checks before any structured amount, transaction or entity analysis. Search text alone does not establish financial relationships or wrongdoing.

No primary dates were assigned. Reporting periods, settlement/disbursement dates, preliminary-print timestamps and cited-event dates need distinct treatment in the subsequent date review. No source PDF, extraction text or financial values are added to ordinary Git history; caches remain ignored. The live viewer remains at 120 PDFs / 1,874 pages with its existing 53 dated, 7 uncertain and 60 unreviewed records.

Acquisition metadata and measurements are saved in `selection.json`, `downloads.json`, `metrics.json` and `metrics.csv`. Selection status describes planning time; downloads and metrics describe actual outcomes. Reconstruct with the existing pilot download/analyze commands using `--out data/pilot/2026-11-08-wave-03`, with browser acquisition if command-line access is blocked. Compare actual source bytes before accepting existing review evidence.

Next: review the two deposit-ticket pages using local OCR and source comparison, retaining native text and explicit uncertainty for handwriting. Then inspect financial table extraction and date roles before integrating this batch. Across the expansion plan, 30 PDFs are acquired/extracted, 20 are integrated, and 70 remain unprocessed.
