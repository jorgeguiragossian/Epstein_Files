# Wave 4 public integration

The ten reviewed dataset 11 PDFs are integrated with native page text, all 13 scoped candidate reviews and nine lossless body breakdowns. The collection now contains **140 PDFs / 1,933 pages**, 176 parser occurrences across 41 PDFs, 102 reviewed candidates across 37 PDFs and 37 body breakdowns. These are detected occurrences, not unique messages or verified contacts.

The source-order mismatch in EFTA02215291 and ambiguous trailing material in EFTA02217241 remain visible and now appear in boundary-issue drilldowns in both Python and static APIs and the coverage dashboard. Two calendar alerts carry explicit notices that event text does not establish person-to-person correspondence or a sent date. Native fields, bodies and damaged extraction are preserved; no identities or relationships are inferred.

All ten new primary dates remain unreviewed. Collection totals are **54 dated, 16 uncertain, 70 unreviewed**. The 54 primary-dated and six reporting-period document cohorts retain their frequencies and source evidence; exclusion denominators increase by ten. There are still 36 prepared/source-checked briefs and 18 date-evidence-only documents.

Comparison with the prior public bundle confirms all 130 prior document payloads, all 163 prior email records and every prior word/timeframe index document entry are exactly preserved. The full index gains ten unreviewed entries. All 93 offline tests, 79 static/Python comparisons and real-cache HTTP smoke checks pass. Browser checks confirm boundary filtering and the calendar-alert notice. Tests cover inclusion of both new boundary statuses while excluding alerts from that issue category.

The explicit native-correspondence batch registry pins source/acquisition, quality, review and processing metadata. The processing catalog retains 24,447 observed URL pairs and now records 140 acquired/extracted PDFs. Source PDFs remain at DOJ and in ignored local caches; the authorized public bundle includes native text and review layers. The saved expansion plan has 40 acquired/extracted/integrated PDFs and 60 unprocessed.

Rebuild with all four expansion caches plus the original cache using `scripts/build-pages.py`, then `scripts/check-pages.py` and `tests/test_static_pages.mjs`. Revalidate this batch with `scripts/check-wave-correspondence.py --out data/pilot/2026-11-08-wave-04`. Source changes require re-review, not automatic evidence renewal.

Next: adjudicate primary dates for these ten documents, distinguishing sent dates, nested quoted timestamps and calendar event dates, while retaining uncertainty where extraction or source context is insufficient.
