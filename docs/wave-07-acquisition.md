# Wave 7: dataset 2 acquisition and quality triage

All ten dataset 2 PDFs from the unchanged saved expansion selection were downloaded through official DOJ listing links using normal browser access. Existing adult-eligibility authorization covered the age prompt. PDF signatures, source SHA-256 hashes and 64 MiB individual / 512 MiB batch limits were checked. Response headers were not captured or invented.

All native extractions succeeded: **11 pages / 8,687,811 bytes**. Codex visually compared every page with native UTF-8 text. All pages are photographic content; all eleven are flagged low-text and mostly yield only source stamps or incidental extraction artifacts. Sparse text is not an empty image. No substantial prose requiring OCR was observed in this pass, and no OCR was performed.

EFTA00003601 has two pages containing visually similar image presentations with different quality/redaction framing. Both remain preserved in source order; this is not an exact-image duplicate finding. EFTA00003726 and EFTA00003792 have partial camera overlays with day-number/time fragments but no complete calendar date in the inspected image. Native text omits those overlays. Missing month/year must not be inferred, and no primary date was assigned.

The heuristic and current email parser detect zero candidates. No identities, face associations, locations, ownership, relationships, image-derived search text, primary dates or content summaries were assigned. Source redactions remain intact. This is scoped quality review, not independent authentication.

Tracked metadata lives in `data/pilot/2026-11-08-wave-07/selection.json`, `downloads.json`, `metrics.json`, `metrics.csv` and `quality-review.json`. Selection statuses describe planning time; downloads/metrics record actual results. PDF/native/rendered/parser caches remain ignored. Reconstruct using existing pilot download/analyze commands with this output directory, using normal browser acquisition when required. Exact source bytes must match before accepting existing reviews.

The live viewer remains unchanged at **160 PDFs / 2,197 pages**, 70 dated, 30 uncertain and 60 unreviewed PDFs. Across the expansion plan, **70 PDFs are acquired/extracted, 60 integrated and 30 unprocessed**. Do not regenerate the saved selection.

Next: integrate this native photograph batch with explicit sparse-text/camera-overlay quality notices and prior-public-data checks, then primary-date adjudication. No OCR or manual captioning is necessary merely to populate search text.
