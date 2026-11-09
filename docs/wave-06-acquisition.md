# Wave 6: dataset 1 acquisition and quality triage

All ten dataset 1 PDFs from the unchanged expansion selection were acquired through their official DOJ listing links using normal browser downloads. Existing adult-eligibility authorization covered the age prompt. PDF signatures, exact SHA-256 hashes and 64 MiB individual / 512 MiB batch limits were checked. Response headers were not captured or invented.

All ten native extractions succeeded: **10 pages / 4,639,698 bytes**. Codex visually compared every source page with native UTF-8 text. Nine PDFs are photographs of building/interior/outdoor scenes or equipment; native extraction yields the source stamp only. Small incidental signs/labels are not comprehensively transcribed, so text search does not cover everything visible in these images. Sparse extraction does not mean an empty source page.

**EFTA00003158 needs source-assisted OCR/transcription review.** It photographs a handwritten log/form with substantial visible entries that native extraction captures poorly. It passes the automatic text-density threshold, illustrating that density alone does not establish extraction accuracy. Handwritten fields, row alignment and possible references to other photographs are not validated. No handwritten date/location/description is silently substituted into native text. No OCR was run in this acquisition milestone.

The simple header heuristic and current email parser detect zero candidates. This observation does not authenticate the files or establish facts beyond the inspected scope. No primary dates, identities, locations, ownership claims, photograph-to-log associations or content summaries were assigned. Source redactions are preserved.

Tracked metadata lives in `data/pilot/2026-11-08-wave-06/selection.json`, `downloads.json`, `metrics.json`, `metrics.csv` and `quality-review.json`. Planning-time statuses are retained in selection; downloads/metrics record actual results. PDFs, raw native text, parser caches and rendered images remain ignored. Reconstruct through existing pilot download/analyze commands with this output directory, using browser acquisition when needed; compare exact source bytes before accepting prior reviews.

The live site remains unchanged at **150 PDFs / 2,187 pages**, with 70 dated, 20 uncertain and 60 unreviewed PDFs. Across the expansion plan, **60 PDFs are acquired/extracted, 50 integrated and 40 unprocessed**. Do not regenerate the saved selection.

Next: locally assess OCR/transcription of EFTA00003158 against its source, retaining native text and explicit handwriting uncertainty, then integrate this photograph-heavy batch with source-quality notices. Primary-date review remains separate; do not infer dates or locations from neighboring files or image appearance.
