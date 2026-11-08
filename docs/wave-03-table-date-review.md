# Wave 3 layout and date-role review — November 8, 2026

All ten PDFs now have source-based layout/date-role assessments. Twenty-eight additional pages were visually inspected in this pass; combined with acquisition and deposit-ticket review, all 42 pages were inspected. This is an editorial assessment of layout and date roles, not cell-by-cell verification, independent authentication or a transaction ledger.

`data/pilot/2026-11-08-wave-03/table-date-role-reviews.json` binds every source PDF and every native page by SHA-256. It records exact native text anchors, concrete extraction issues and 14 date-role observations. Normalized day/period readings are separate source-assisted observations; no record is promoted to a primary document date.

| Document | Source/date-role finding | Layout finding |
|---|---|---|
| EFTA01262784 | Application signature on page 4 and order signature on page 7: June 27, 2019. Repeated 2017.02.06 footer is a form/version marker. | Narrative application followed by order; no financial table. |
| EFTA01268630 | Tax heading supplies 1980 only, without a day date. | Native row numbers/headings separate from rows; name and digit errors remain. |
| EFTA01280083 | Preliminary print: December 9, 2014. Planned settlement/proration/disbursement fields: December 10. Blank signatures do not establish completion. | Borrower/seller columns flatten; GFE/HUD-1 comparison sections repeat line items. |
| EFTA01280951 | Statement period: November 1–30, 2015. Analysis period is a separate role. | Three side-by-side Date/Amount pairs on page 2 lose header order in native text. |
| EFTA01281641 | Handwritten date remains a local literal with unresolved format/century. | OCR is inadequate; provisional source-assisted readings are separate. |
| EFTA01283668 | Portfolio as of June 30, 2018; activity period June 1–30. Trade and settlement dates are distinct. | Parallel tables, currencies, current-period/year-to-date measures and repeated summaries must remain separate. |
| EFTA01285058 | Reporting period: August 1–31, 2014. | Activity continues on page 2; check/other-debit summaries repeat detailed entries. |
| EFTA01286095 | Reporting period: April 1–30, 2016. | Summary digits/words contain recognition errors; text alone does not verify balances or absence of activity. |
| EFTA01287122 | Reporting period: October 1–31, 2017. | Continued activity and repeated check/other-debit summaries are not additional transfers. |
| EFTA01288151 | Reporting period: December 1–31, 2018. | Balance, fee, interest, period and year-to-date fields have different roles. |

The native text remains usable for source-linked searching, with explicit limitations. It should not drive automatic debit/credit totals, counterparties, ownership claims or relationship graphs. In particular, do not sum local-currency values with their USD equivalents or treat repeated summaries as new events. Disclosures, explanatory notices and intentionally blank pages are classified by source context rather than by text density alone.

No source PDFs, raw native text, OCR images/results or literal financial readings were added to ordinary Git history. No primary dates, structured financial values or new public documents were published in this review. The public viewer remains at 120 PDFs / 1,874 pages.

Validate the evidence chain with:

```powershell
python scripts/check-table-date-review.py --out data/pilot/2026-11-08-wave-03
```

The validator checks complete document/page coverage, PDF/extraction/page bindings, exact source anchors, recognized date roles and valid ordered reporting periods. It rejects promotion of these observations into a primary date, verified ledger or identity inference. All 88 offline tests pass, including changed bytes, missing pages, wrong quotes, unsupported roles and reversed periods. Native extraction remains unchanged.

Next: integrate wave 3 with document-level layout/date-role notices and source links. Keep reporting-period observations separate from the existing primary-date filter. The deposit-ticket editorial layer needs an explicit source-assisted label if later exposed; it must not silently replace native extraction.
