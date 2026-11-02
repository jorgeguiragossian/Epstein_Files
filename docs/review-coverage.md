# Review coverage dashboard

The dashboard at `/coverage` locally and `coverage.html` on GitHub Pages shows candidate-level review totals by dataset and source PDF. It includes all 100 pilot PDFs across 12 datasets; documents with no detected email candidates are hidden from the document table by default and can be shown with a checkbox. A dataset selector narrows the document table while the pilot totals remain fixed. Dataset/table settings persist in the URL.

Counts come from the same source-bound candidate catalog as the Email review page. Reviewed means a Codex source-assisted editorial check, not authentication, uniqueness, or eligibility for contact counting. At this milestone, 45 of 114 candidate occurrences are reviewed; 69 remain unreviewed. At least one candidate is reviewed in each of the 18 PDFs with detected email candidates, but coverage within those PDFs is partial.

Boundary counts describe editorial flags. Parser From/To gaps count missing syntactically detected addresses; separate visually supported header readings do not clear them. Date gaps include missing, unparsed and ambiguous numeric dates. A missing timezone alone is not included in that date-gap count. Categories overlap and must not be summed as distinct problems. Zero candidate detections do not establish that a PDF contains no correspondence.

Nonzero candidate counts link to matching Email review groups. New focuses include unreviewed, parser sender gaps, recipient gaps and date gaps. Groups retain all member source references, so future multi-occurrence groups can produce different group and candidate denominators. Dataset totals aggregate the selected pilot files, not the full DOJ release. Contact rankings remain pending.

`viewer/email_coverage.py` computes the local API response at `/api/coverage`; the Pages builder exports that exact response. Tests cover zero-candidate documents, overlapping categories, dataset/document denominator consistency and preserved source references in drilldowns. Static API comparisons check the public adapter against Python, including all new filters.
