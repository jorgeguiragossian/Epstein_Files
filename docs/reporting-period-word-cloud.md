# Reporting-period word clouds — November 8, 2026

The word-cloud page now offers an explicit **Date basis** choice:

- **Primary document date** is the default. Existing primary-date eligibility, counts and source references are preserved.
- **Reviewed reporting-period overlap** selects documents whose reviewed statement/activity period overlaps the inclusive From/Through bounds. Either bound can remain open; without bounds all reviewed period documents qualify.

Period mode currently covers six of the 130 published PDFs; the other 124 have no qualifying reviewed period. It can include a document with an uncertain primary date. Standalone as-of dates do not qualify. A document is counted once even when multiple reviewed periods match. Dataset scope controls the coverage denominator, and a person filter still selects individual pages with the curated literal-name match.

The cloud counts **all selected PDF pages**, including narrative, signatures, disclosures, headers and repeated summaries. It does not isolate transaction rows occurring inside the chosen dates. Financial table text and OCR errors remain unverified; word counts are not amounts, money-flow analysis, verified themes, unique messages or relationships. Extra-word exclusions and the existing token rules apply in both modes.

For example, November 30, 2015 in reporting-period mode selects EFTA01280951's two pages. A word's evidence list retains its exact per-page token counts and links to the source reader. December 1 alone has no overlapping statement in the reviewed period sample. The coverage paragraph and excluded-document statistic explicitly identify the chosen basis.

The selection persists in the shareable URL, using `date_basis=reporting_period` alongside `date_from`, `date_to`, `dataset`, `person` and `exclude`. These date bounds apply to the selected basis on the word-cloud page. Unknown date bases and invalid/reversed dates are rejected. Timeframe briefs still use primary dates; no reporting-period brief mode was added.

The derived frequency index is now `word-frequency-2`. It retains page frequencies for documents with reviewed periods even when their primary dates are uncertain. Source metadata, native text, primary dates, email records and coverage reviews do not change. The period response adds explicit period eligibility/exclusion metrics; legacy primary-date denominators remain primary-date metrics. The UI uses the appropriate metrics for its selected basis.

Validation passed: 92 offline Python tests, 74 static/Python API comparisons, real-cache HTTP smoke checks and browser checks of period selection, term/source evidence, basis switching and source-page navigation. Tests cover uncertain-primary-date inclusion, inclusive/open bounds, non-overlap, overlapping-period deduplication, person-page filtering, extra exclusions, standalone as-of exclusion and unknown bases. Direct comparison with the prior public bundle confirms unchanged primary-mode frequencies/page evidence and timeframe results (apart from the word-index schema version), and unchanged document/email/review payloads.

The collection remains 130 PDFs / 1,916 pages, with 54 primary-dated, 16 uncertain and 60 unreviewed PDFs. The next acquisition milestone can use the next ten PDFs from the remaining 70 saved selections; no selection regeneration is needed.
