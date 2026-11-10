# Wave 8: dataset 3 acquisition and bounded quality triage

The ten dataset 3 PDFs from the unchanged saved expansion selection were acquired through official DOJ listing links via normal browser downloads. Existing adult-eligibility authorization covered the age prompt. All PDF signatures, source SHA-256 hashes and 64 MiB individual / 512 MiB batch limits were checked. Response headers were not captured or invented.

All native extractions succeeded: **348 pages / 91,006,129 bytes**, with **213 low-text pages**. Codex visually compared **28 pages** with native UTF-8 text: all pages of six files of up to four pages, and first/middle/last pages of four larger files. Extraction covers every page; source-content review does not. No OCR was performed.

The inspected material includes photographs, redacted album/contact sheets and captions, product/publication covers, disc/USB item images, item-not-scanned placeholders and a handwritten evidence receipt. A placeholder is source content describing an item, not a failed PDF download. Its template revision date is not automatically an item/document issue date. Redactions are preserved and not reconstructed.

Three files need targeted extraction follow-up before integration:

- EFTA00003858: visible printed product-package text is largely absent from extraction; all four pages inspected.
- EFTA00004060: visible cover text is incompletely extracted, especially PDF page 3; all four pages inspected.
- EFTA00004231: evidence receipt handwriting/date/description needs field-level source/OCR assessment; all three pages inspected. A receipt date is separate from capture/media-creation dates. The USB photograph/placeholder does not supply its contents.

EFTA00004012 (27 pages), EFTA00004577 (86), EFTA00005091 (100) and EFTA00005586 (119) each have only three visually inspected pages. Captions, filenames and disc/index labels do not independently establish identities, location, relationships, file contents or capture dates. The three sampled pages of EFTA00005586 show blacked-out content with a Grand Jury-NY label; do not generalize visual review to every page or infer hidden content. All scope and exact native page hashes are recorded in `quality-review.json`.

No email candidates were detected by either the simple heuristic or current parser. No primary dates, identities, associations, content summaries or corrected search layers were assigned. Native text remains unchanged and no source PDF is published.

Tracked metadata: `data/pilot/2026-11-08-wave-08/selection.json`, `downloads.json`, `metrics.json`, `metrics.csv` and `quality-review.json`. Selection statuses describe planning time; downloads/metrics describe actual results. Source PDFs/native/rendered/parser caches remain ignored. Reconstruct through existing pilot download/analyze commands with this output directory and normal browser acquisition where required; compare exact source bytes before accepting prior review evidence.

The live viewer remains unchanged at **170 PDFs / 2,208 pages**, 70 dated, 40 uncertain and 60 unreviewed PDFs. The unchanged expansion plan has **80 acquired/extracted PDFs, 70 integrated and 20 unprocessed**. Do not regenerate it.

Next: targeted local source/OCR assessment of the two printed-cover files and handwritten receipt, retaining native text and explicit field/date uncertainty. Then integrate with bounded album/redaction/placeholder notices, prior-data preservation checks and separate primary-date adjudication.

## Targeted OCR/source assessment — November 9, 2026

Five source pages were re-rendered at PDFium scale 3 and visually compared with seven local Windows.Media.Ocr en-US runs:

| Source | Scope | OCR output characters |
| --- | --- | --- |
| EFTA00003858 | PDF pages 3 and 4, full page | 28 / 547 |
| EFTA00004060 | PDF pages 1 and 3, full page | 633 / 46 |
| EFTA00004231 | PDF page 1, full/header/description | 497 / 179 / 48 |

Character counts measure output volume, not accuracy. OCR recovers some printed package/advertisement prose but misses prominent stylized headings and introduces character, label and barcode errors. Receipt OCR misses the handwritten received date and damages most description text, including in focused crops. **No OCR output is accepted as native-text replacement or corrected public search text.**

Codex separately retained four provisional sample literals in ignored local editorial layers: one package heading, one advertisement heading and two receipt-field fragments. This is not full-page transcription, independent identity/ownership verification or an authenticated custody chain. The receipt field is explicitly Date Received, distinct from photo capture/media creation. No normalized primary date is assigned. Redacted contributor/agent content is not reconstructed, and the USB photograph does not supply USB contents.

Three tracked metadata files (`ocr-review-EFTA00003858.json`, `ocr-review-EFTA00004060.json`, `ocr-review-EFTA00004231.json`) and `ocr-review-index.json` bind PDF/native/image/result/literal hashes, page scope, crop coordinates, sample regions and disabled promotion flags. All raw OCR text/word boxes, render images and literal readings remain ignored under `extractions/ocr-review/`. Native extraction bytes are unchanged. No new source PDFs, dates, summaries or review layers are deployed in this milestone.

The checker now accepts a named metadata file through `--review`, preserving its default behavior for earlier batches and rejecting paths outside the batch. Revalidate each named review, for example:

```powershell
python scripts/check-ocr-review.py --out data/pilot/2026-11-08-wave-08 --review ocr-review-EFTA00004231.json
```

All three source/OCR/literal evidence chains validate and all **95 offline tests** pass, including named-manifest stale-field and path-containment checks. The five inspected OCR pages do not expand the previous 28-page visual scope because all were already inspected. The remaining album/redaction scope limits still apply.

Next: integrate wave 8 native text with explicit bounded album/redaction/placeholder notices and OCR-assessment findings. Preserve all provisional literals locally and compare prior public payloads. Primary-date adjudication follows separately; template revisions, product labels and receipt roles must remain distinct.
