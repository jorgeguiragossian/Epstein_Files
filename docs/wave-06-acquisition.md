# Wave 6: dataset 1 acquisition and quality triage

All ten dataset 1 PDFs from the unchanged expansion selection were acquired through their official DOJ listing links using normal browser downloads. Existing adult-eligibility authorization covered the age prompt. PDF signatures, exact SHA-256 hashes and 64 MiB individual / 512 MiB batch limits were checked. Response headers were not captured or invented.

All ten native extractions succeeded: **10 pages / 4,639,698 bytes**. Codex visually compared every source page with native UTF-8 text. Nine PDFs are photographs of building/interior/outdoor scenes or equipment; native extraction yields the source stamp only. Small incidental signs/labels are not comprehensively transcribed, so text search does not cover everything visible in these images. Sparse extraction does not mean an empty source page.

**EFTA00003158 needs source-assisted OCR/transcription review.** It photographs a handwritten log/form with substantial visible entries that native extraction captures poorly. It passes the automatic text-density threshold, illustrating that density alone does not establish extraction accuracy. Handwritten fields, row alignment and possible references to other photographs are not validated. No handwritten date/location/description is silently substituted into native text. No OCR was run in this acquisition milestone.

The simple header heuristic and current email parser detect zero candidates. This observation does not authenticate the files or establish facts beyond the inspected scope. No primary dates, identities, locations, ownership claims, photograph-to-log associations or content summaries were assigned. Source redactions are preserved.

Tracked metadata lives in `data/pilot/2026-11-08-wave-06/selection.json`, `downloads.json`, `metrics.json`, `metrics.csv` and `quality-review.json`. Planning-time statuses are retained in selection; downloads/metrics record actual results. PDFs, raw native text, parser caches and rendered images remain ignored. Reconstruct through existing pilot download/analyze commands with this output directory, using browser acquisition when needed; compare exact source bytes before accepting prior reviews.

The live site remains unchanged at **150 PDFs / 2,187 pages**, with 70 dated, 20 uncertain and 60 unreviewed PDFs. Across the expansion plan, **60 PDFs are acquired/extracted, 50 integrated and 40 unprocessed**. Do not regenerate the saved selection.

Next: locally assess OCR/transcription of EFTA00003158 against its source, retaining native text and explicit handwriting uncertainty, then integrate this photograph-heavy batch with source-quality notices. Primary-date review remains separate; do not infer dates or locations from neighboring files or image appearance.

## Handwritten-log OCR assessment completed

EFTA00003158 PDF page 1 was rendered locally with PDFium at scale 3 (1,785 by 2,649 pixels). The existing Windows.Media.Ocr en-US helper ran on the full page and two focused crops: header `[240,400,1700,710]`, rows `[240,710,1690,1600]`. Full-page OCR returned eight lines / 139 characters; header crop three lines / 44 characters; row crop two lines / 63 characters. These are output volumes, not recognition-accuracy measurements.

Source comparison confirms the engine mostly reads printed labels and misses the handwritten table. **No OCR improvement is accepted for native-text replacement.** Codex separately saved two clear sample row literals in an ignored provisional editorial layer. They are not independently verified, do not constitute a complete log transcription and do not establish links between log photo numbers and EFTA PDF identifiers. The handwritten date, normalized primary day, complete row alignment and ambiguous numerals remain unadjudicated. Redacted preparer information is not reconstructed.

`ocr-transcription-review.json` records exact PDF/native/image/result/literal hashes, source regions, scope and disabled eligibility flags. Full-page/crop images, raw OCR word boxes and provisional literal readings remain under ignored `extractions/ocr-review/`. They are not public and do not change native text, primary dates, identity/location findings or photo associations.

The existing checker validates all bindings, source regions and unchanged native extraction:

```powershell
python scripts/check-ocr-review.py --out data/pilot/2026-11-08-wave-06
```

All 94 offline tests pass. Repeat OCR only with explicit source re-review; new results/timestamps must not automatically renew prior evidence. Next: integrate the ten native PDFs with notices distinguishing image-only sparse text from the handwritten log's inadequate extraction. Keep provisional OCR/editorial caches local. Primary-date adjudication remains separate.
