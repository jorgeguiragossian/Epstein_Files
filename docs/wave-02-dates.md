# Wave 2 primary-date review — November 8, 2026

Eight of the ten dataset 9 expansion PDFs now have primary dates; two remain uncertain. Reviews are editorial source readings by Codex, not independent authentication. Exact native-text quotes and source PDF SHA-256 values bind the assignments. PDF page numbers refer to file order.

| Document | Primary date | Role | Evidence page |
|---|---|---|---|
| EFTA00059374 | 2019-08-10 | Outer email sent date | 1 |
| EFTA00064578 | 2022-03-10 | Outer email sent date | 1 |
| EFTA00067452 | 2008-06-18 | Outer email sent date | 1 |
| EFTA00070036 | 2019-08-12 | Letter issue date | 1 |
| EFTA00073640 | 2021-12-01 | Outer email sent date | 1 |
| EFTA00075976 | 2021-07-30 | Court order date | 3 |
| EFTA00079911 | 2019-08-23 | Outer email sent date | 1 |
| EFTA00082128 | 2019-08-14 | Outer email sent date | 1 |
| EFTA00039153 | Uncertain | Exhibit-list assembly date not established | 1–3 inspected |
| EFTA00078194 | Uncertain | Primary execution date not established | 1–2 inspected |

The exhibit list has blank footer DATE fields on all three pages. Its many dates refer to exhibits, policies or cited records and are not promoted to a containing-document date.

The deed shows recording on October 23, 2020 and acknowledgment on March 9, 2019. Its March 2019 made/execution-day text is obscured by the watermark and absent from native extraction. The review keeps the primary date uncertain, preserving both roles. The explorer provides separate source buttons for the recording evidence and acknowledgment evidence, with exact quote and native-page hash validation for the supporting page. No legal-effect or authenticity determination is made.

Email dates use the day displayed in the outer header, including December 1 at +0000 for EFTA00073640. Quoted November 30 local-clock messages are separate. No unspecified timezone is inferred. Other excluded date roles include the subpoena date in EFTA00079911's subject, proposed meeting dates, signature-graphic years and the letter's referenced incident dates. The court order uses its final-page Dated line, consistent with the filing stamp.

Collection totals are now 53 dated, 7 uncertain and 60 unreviewed PDFs. All 120 PDFs remain searchable; 53 participate in date-range analysis. Timeframes retain the same 36 prepared/source-checked editorial briefs and now have 17 date-evidence-only documents. There are no new content briefs. All native document fields, 163 email records and earlier date reviews remain unchanged.

Reproduce the review manifest with `python scripts/prepare-wave-02-dates.py`, then rebuild with `python scripts/build-pages.py`. The explicit batch registry pins `date-reviews.json`; indexing validates source bindings and cited quotes. The added supporting-evidence validation rejects changed page hashes, missing quotes and invalid page references.

Validation passed: 80 offline tests, 55 static/Python API comparisons, real-cache HTTP smoke checks, browser checks of the deed's supporting-page navigation and the December 1 date-evidence-only timeframe card. Exclusion checks confirm that the uncertain deed is not placed on its recording date, and the outer December 1 email is not placed on November 30. Comparison with the preceding public bundle confirms only these ten date-review payloads changed within the document records; native fields and email records are intact.

Next: the next bounded acquisition batch from the remaining 80 selected PDFs, or a separately scoped content-brief review for these newly dated documents. Do not imply that date-evidence-only cards summarize their contents.
