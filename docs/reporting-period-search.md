# Primary dates and reporting-period search — November 8, 2026

Document search now has a separate **Filter by reviewed reporting period** section. From/Through bounds select documents whose reviewed reporting period overlaps the requested range, including both endpoints. Either bound can be left open. Clearing both bounds removes the period constraint. Text, dataset, person, quality, primary-date and date-status filters still apply together.

The filter uses only source-reviewed `statement_reporting_period` and `transaction_reporting_period` observations. It currently covers six PDFs: EFTA01280951, EFTA01283668, EFTA01285058, EFTA01286095, EFTA01287122 and EFTA01288151. Standalone as-of dates, transaction dates, form markers and planned settlement dates do not qualify. Documents without a reviewed period are excluded when a period bound is active. This is partial reviewed coverage, not a complete statement inventory.

For example, November 1–30, 2015 finds EFTA01280951 even though its primary issue date remains uncertain. November 30 alone also matches; December 1 alone does not. Period overlap means the document reports on some part of the selected interval, not that every transaction in the document occurred within it. The reader's source-quality panel supplies the period quote and source-page reference.

Shareable URLs use `period_from` and `period_to`, independently of primary-date parameters `date_from` and `date_to`. The server and GitHub Pages adapter enforce the same calendar-date and range validation. One example:

```text
?period_from=2015-11-01&period_to=2015-11-30&date_status=uncertain
```

This milestone applies reporting-period selection to **document search only**. Word clouds and timeframe briefs continue to use reviewed primary dates. Do not interpret period-search results as a verified ledger, filter individual transaction rows by the document bounds, or silently use period endpoints as issue dates.

## Wave 3 primary-date adjudication

The legal application/order bundle EFTA01262784 receives a primary court-order date of June 27, 2019, cited to PDF page 7 and supported by the application signature on page 4. Its repeated 2017 footer is a form/version marker. The other nine wave 3 PDFs remain uncertain as primary-day assignments: their visible roles are reporting/as-of periods, a year-only heading, preliminary print versus planned settlement dates, or unresolved handwriting. No day is invented from a year or forced from a reporting interval.

The explicit registry pins `data/pilot/2026-11-08-wave-03/date-reviews.json`. Reproduce it with `python scripts/prepare-wave-03-dates.py`; indexing checks source bindings and cited evidence. These editorial assignments are not independent authentication.

Collection totals are **54 dated, 16 uncertain, 60 unreviewed PDFs**, out of 130 PDFs / 1,916 pages. Date-range analysis covers 54 PDFs; 76 lack a usable primary date. Timeframes retain 36 existing prepared/source-checked briefs and now have 18 date-evidence-only documents. No new content brief, financial value or account association was created.

Validation: 91 offline tests, 68 static/Python API comparisons and real-cache HTTP smoke checks. Tests cover inclusive/open bounds, non-overlap, invalid/reversed dates, standalone as-of exclusion and combinations with primary dates, status, text and dataset. Browser checks cover period controls, uncertain-date results, source reading, URL persistence and clear/reset behavior. All native document fields, source-quality metadata and 163 email records remain unchanged; only the ten new primary-date reviews changed in document payloads.


The subsequent [reporting-period word-cloud milestone](reporting-period-word-cloud.md) adds an explicit date-basis choice to word analysis. Reviewed reporting periods can select PDFs with uncertain primary dates; primary-date mode remains the default. Counts cover whole selected pages with exact source references. Timeframe briefs continue to use primary dates.
