# Wave 9: bounded local OCR assessment

Reviewed November 9, 2026, by Codex using installed Windows.Media.Ocr en-US and PDFium scale-3 renders. No external OCR service. All eight acquisition-flagged files are covered by 14 attempts across 13 source pages; this is bounded same-assistant source comparison, not independent authentication or complete review of the 270-page batch.

| File | PDF pages assessed | Attempts | Finding |
| --- | --- | --- | --- |
| EFTA00005910 | 1 | 1 | Folder handwriting remains garbled. |
| EFTA00006085 | 1, 2, 3 | 3 | Folder heading, certification handwriting and inventory not reliably recovered. |
| EFTA00007501 | 1 | 2 | Full OCR omits date; focused OCR repeats incorrect year 2006 for visible 2005. |
| EFTA00007606 | 1, 3 | 2 | Folder identifier partly recovered; shipping fields and date remain unreliable. |
| EFTA00007684 | 1 | 1 | Reflective/faint invoice body and dates largely omitted. |
| EFTA00007763 | 4, 5 | 2 | Evidence handwriting and placeholder description unreliable. |
| EFTA00007968 | 1, 2 | 2 | Evidence date/description misread; template revision is a different date role. |
| EFTA00008320 | 89 | 1 | Handwritten marking omitted; redactions preserved. |

One provisional source-assisted literal (the statement-heading date) is pinned to a local image region and retained only in the ignored editorial layer. No complete replacement layer was accepted. Native extraction is unchanged. No primary dates, validated transactions, subscriber identities, contact rankings or media contents were promoted. Other pages/components remain outside this OCR scope.

Eight named manifests and `ocr-review-index.json` record PDF, native extraction, page-text, rendered-image, OCR-result and local-literal hashes. Existing `check-ocr-review.py` validates every evidence chain, exact eight-file flag coverage and disabled eligibility. During validation, acquisition review page fingerprints were corrected to hash UTF-8-decoded text consistently; source PDF and extraction bytes were unchanged. Raw OCR, images and the provisional literal remain ignored and are excluded from publication.

## Next milestone

Register the ten documents through the existing indexed OCR-quality batch mode, publish explicit scoped findings/source links, and verify preservation of prior data before deployment. Adjudicate document dates separately. Live site remains 180 PDFs / 2,556 pages, 71 dated / 49 uncertain / 60 unreviewed. Expansion remains 90 acquired/extracted, 80 integrated, 10 unprocessed (dataset 5).
