# Review coverage dashboard

The [November 7 brief evaluation](brief-evaluation-2026-11-07.md) adds date/brief coverage alongside the correspondence counts described below. New totals show 36 dated PDFs, 36 prepared page briefs, twenty-eight with recorded editorial source checks and none with date evidence only. Dataset/document rows include these denominators and links to the matching timeframe cards. The default document table now includes PDFs with either email candidates or a usable reviewed date; the checkbox shows all remaining pilot PDFs. A brief's editorial source check is separate from email-candidate review and does not change draft or verification status.

The dashboard at `/coverage` locally and `coverage.html` on GitHub Pages shows candidate-level review totals by dataset and source PDF. It includes all 100 pilot PDFs across 12 datasets; documents with no detected email candidates are hidden from the document table by default and can be shown with a checkbox. A dataset selector narrows the document table while the pilot totals remain fixed. Dataset/table settings persist in the URL.

Counts come from the same source-bound candidate catalog as the Email review page. Reviewed means a Codex source-assisted editorial check, not authentication, uniqueness, or eligibility for contact counting. At this milestone, 45 of 114 candidate occurrences are reviewed; 69 remain unreviewed. At least one candidate is reviewed in each of the 18 PDFs with detected email candidates, but coverage within those PDFs is partial.

Boundary counts describe editorial flags. Parser From/To gaps count missing syntactically detected addresses; separate visually supported header readings do not clear them. Date gaps include missing, unparsed and ambiguous numeric dates. A missing timezone alone is not included in that date-gap count. Categories overlap and must not be summed as distinct problems. Zero candidate detections do not establish that a PDF contains no correspondence.

Nonzero candidate counts link to matching Email review groups. New focuses include unreviewed, parser sender gaps, recipient gaps and date gaps. Groups retain all member source references, so future multi-occurrence groups can produce different group and candidate denominators. Dataset totals aggregate the selected pilot files, not the full DOJ release. Contact rankings remain pending.

`viewer/email_coverage.py` computes the local API response at `/api/coverage`; the Pages builder exports that exact response. Tests cover zero-candidate documents, overlapping categories, dataset/document denominator consistency and preserved source references in drilldowns. Static API comparisons check the public adapter against Python, including all new filters.

The [second November 7 batch](brief-evaluation-batch-2.md) records the next ten source checks and ten additional drafts.

The [third November 7 batch](brief-evaluation-batch-3.md) completes limited-page brief coverage for all 36 dated pilot PDFs. The eight newest drafts await a separate recorded check; counts describe PDF records, not unique testimony or events.
