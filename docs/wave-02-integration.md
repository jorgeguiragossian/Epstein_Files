# Wave 2 public integration — November 8, 2026

The ten dataset 9 PDFs from `data/pilot/2026-11-08-wave-02/` are integrated with their native extracted text and scoped correspondence reviews. The published sample grows from 110 PDFs / 1,836 pages to **120 PDFs / 1,874 pages**. The original 110 document payloads and 122 email candidate records are unchanged.

The email workspace adds 41 occurrences across six PDFs, for 163 occurrences across 31 PDFs overall. All 41 new occurrences have scoped source-assisted editorial reviews. The collection now has 89 reviewed candidates across 27 PDFs and 28 source-linked body breakdowns. Nineteen of the new candidates retain unseparated-quote findings; header problems and incomplete quoted-message enumeration remain explicit. These are not independently verified or unique messages, and contact rankings remain disabled.

Each review card shows its header finding, review notes and links to the inspected native PDF pages. The workspace explains that review completion does not resolve all issues. Native fields and text remain intact; no source-order, timestamp or header repair was silently applied. The last page of EFTA00064578 remains a correctly captured sparse note. Original PDFs stay at DOJ and are not copied into GitHub Pages.

All ten new document dates remain unreviewed. Date totals are 45 dated, 5 uncertain and 70 unreviewed. The eligible date-range collection remains 45 PDFs, with 36 existing briefs and nine date-evidence-only documents. New files are searchable by text, dataset and existing literal-name vocabulary, but are excluded from date-range word clouds and timeframe briefs until primary-date review.

`data/pilot/viewer-batches.json` pins source measurements, acquisition metadata and editorial evidence, selecting the `native_correspondence_v1` loader for this batch. The loader revalidates native bytes and candidate/page/body bindings and supports multiple reviewed occurrences per document. The legacy derived-header layer for wave 1 is preserved. The processing catalog now marks 120 acquired/extracted PDFs while retaining the same 24,447 observed dataset/file URL pairs.

Validation: 80 offline Python tests; 50 static/Python API comparisons; real-cache HTTP smoke checks; browser checks of unresolved findings, reviewed-page links, raw evidence, all eight EFTA00082128 body breakdowns and the sparse-page reader. Comparison with the prior public bundle confirms all prior document payloads, email records and date reviews are unchanged. Tests cover dispatch of multiple candidates from one native review batch, changed source/review rejection, exact body reconstruction and exclusion of unreviewed dates.

Rebuild with both original and expansion caches present:

```powershell
python scripts/build-pages.py
python scripts/check-pages.py
node tests/test_static_pages.mjs
```

Source PDFs and extraction caches remain ignored; public page text and review payloads are in the authorized gh-pages bundle. The next milestone is primary-date review of these ten new PDFs. Eighty selected expansion PDFs remain unprocessed.

The subsequent [primary-date review](wave-02-dates.md) assigns eight dates and retains two uncertain records. Collection date totals are now 53 dated, 7 uncertain and 60 unreviewed; the integration counts above describe the earlier milestone.
