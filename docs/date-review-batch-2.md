# Expanded primary-date review

On November 2, 2026, Codex visually compared cited PDF pages with native extraction for 20 previously unreviewed pilot documents. Selection favored explicit cover/session, report, letter or outer email dates across datasets 6, 7, 9, 10, 11 and 12. This is an editorial, purposive sample, not authentication or an accuracy estimate for the full release.

Nineteen documents receive supported primary dates. One reminder (`EFTA02212924`) remains uncertain: its May 23, 2017 event time is not a labeled sent or creation date. The combined review now covers 40 pilot PDFs: **36 dated, four uncertain, and 60 unreviewed**. No records are classified as reviewed-undated. The original twenty decisions remain unchanged.

The additions include ten transcript/interview session dates, five outer email sent dates, two letter dates, one report date and one presentation date. `letter` and `presentation` are explicit supported date roles rather than overloading report/session roles. Jury designations, template-effective dates, historical events, quoted message dates, and delivery/meeting dates are not substituted for document dates.

Two date readings rely on a clear PDF header despite damaged native extraction: `EFTA01263156` visibly reads October 10, 2018, and `EFTA02212961` visibly reads May 16, 2017. Their exact damaged extracted evidence and source hashes remain pinned alongside notes explaining the visual readings. No OCR text is repaired, participant identity inferred, timezone invented or document claims authenticated.

The regenerated [date review file](../data/pilot/2026-11-01/date-reviews.json) records ISO dates, roles, source PDF hashes, evidence pages, exact extracted evidence and rationales. Reproduce with `scripts/prepare-date-review.py`; `--render` produces local QA sheets for all 40 reviewed records. Only annotation metadata is committed; source PDFs and rendered pages remain in ignored caches.

The explorer and word cloud now admit 36 dated PDFs and exclude 64 uncertain/unreviewed PDFs from date ranges. A primary date dates the containing document, not each event or quoted email within it. Frequency changes reflect additional source coverage, not newly established message/contact counts. Existing email parsing, source text, person matches and correspondence reviews remain unchanged.
