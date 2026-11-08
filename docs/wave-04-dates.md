# Wave 4 primary-date review

All ten dataset 11 PDFs now have source-bound primary-date reviews. Codex compared each first PDF page with native UTF-8 extraction. Eight outer sent dates were assigned; the two calendar alerts remain uncertain because their displayed event dates do not establish separate sent/issue dates. This is editorial source comparison, not independent authentication.

| Document | Primary date | Basis |
| --- | --- | --- |
| EFTA02212883 | 2017-05-30 | Outer Sent row; native slash damaged |
| EFTA02213471 | 2017-05-19 | Outer Sent row; native date incomplete |
| EFTA02213987 | Uncertain | Calendar event date only |
| EFTA02214639 | 2017-06-09 | Outer Sent value displaced in native text |
| EFTA02215291 | 2017-06-12 | Outer Sent row; June 15 schedule is separate |
| EFTA02215926 | 2017-06-14 | Outer Sent row; June 8 quoted chain is separate |
| EFTA02216544 | Uncertain | Calendar event/reminder timestamp only |
| EFTA02217241 | 2017-06-16 | Outer Sent value displaced in native text |
| EFTA02217799 | 2017-07-12 | Outer Sent row; appointment time is separate |
| EFTA02218280 | 2017-07-31 | Outer Sent row; relative future meeting requests separate |

The two damaged native dates retain exact native quotes and explicit source readings in the review rationale. Every record binds PDF bytes, exact native page-text hash and evidence quote. Native email fields are unchanged; known body-order/header issues are not silently corrected. Displayed calendar days are used without inferred timezone conversion.

Collection totals are **62 dated, 18 uncertain and 60 unreviewed PDFs** out of 140 PDFs / 1,933 pages. The eight newly dated documents enter primary-date search, word clouds and timeframe date-evidence cards. No new content briefs were prepared: 36 briefs retain their editorial checks, with 26 additional date-evidence-only documents. Six reporting-period PDFs and their evidence remain unchanged. Calendar alerts remain excluded from primary-date analysis.

Validation: all 93 offline tests; 84 static/Python API comparisons; HTTP smoke checks for calendar-alert exclusion, corrected source-day selection and separation from future schedule dates; browser check of the date-evidence-only card/rationale/source link. All 176 email payloads and groups and all native document fields are unchanged; only the ten intended document date-review payloads change.

Reconstruct with `scripts/prepare-wave-04-dates.py` only after source comparison. The helper rejects changed PDF/native quality bindings and pins date reviews in the explicit batch registry. Builds still require ignored original/four-wave PDF and extraction caches. No PDF copies or OCR layers are published.

Next: acquire the ten saved dataset 12 selections from the unchanged expansion plan, then repeat extraction-quality and source review. Forty selected expansion PDFs are integrated; sixty remain unprocessed.
