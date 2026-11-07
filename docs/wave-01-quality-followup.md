# Wave 1 quality follow-up — November 7, 2026

## Corrected OCR finding

**The earlier OCR target for EFTA00039023 PDF page 2 was incorrect.** The email chain seen on the contact sheet belongs to PDF page 1. Reopening the individual page 2 render shows a blank page except for stamp EFTA00039024, consistent with the native text. This corrects an editorial page-attribution error, not a source-file or extraction change.

Ran the installed local Windows.Media.Ocr engine (en-US) on the individual page 2 render: one line and 12 characters, exactly EFTA00039024. No missing email body was recovered or substituted. The source PDF, native page text, rendered image and local engine output are hash-bound in `ocr-check.json`. The raw engine output remains in the ignored extraction cache. The original native extraction metrics and summary remain unchanged; their `ocr_performed: false` describes that native-only extraction, while `quality-review.json` records the later one-page OCR check separately.

Both initially flagged low-text pages are now explained by visible sparse content: a date/signature page in EFTA00009713 and the stamp-only page in EFTA00039023. This does not establish that every other wave page has complete text: only the recorded quality-review pages have been inspected.

## Reviewed label layers

Individually compared the first pages of EFTA00021826 and EFTA00032045 with native text. Four explicit label-only readings are recorded in `header-label-reviews.json`: their top-level From and To labels. Native From/To text has missing colons, and one From label reads Front. The source shows the labels next to redacted participant fields.

The opt-in helper `viewer/source_layers.py` checks the PDF hash, native page-text hash and exact line before creating a separate derived extraction. It can normalize only reviewed label-only From/To readings; it cannot supply a participant, address, identity or body text. Native files, all other lines, source page/line positions and the existing public email parser remain unchanged. Stale source or text references fail validation.

The existing richer viewer parser detects zero candidates in each original document, and one top-level candidate in each derived layer. Both have unresolved sender/recipient addresses and unseparated quoted material. They are not verified messages or contact-count records. Candidate output remains local under `extractions/header-reviewed/` and is explicitly marked with its derived text layer and pending quote-boundary flag.

## Broader parser check

Across the ten native wave PDFs, the richer viewer parser produces five candidate occurrences. Applying the two reviewed label layers raises that to seven occurrences across six PDFs. These counts differ from the simple pilot heuristic’s six header blocks across five PDFs; the algorithms and denominators must not be conflated.

A further visible email-like first page, **EFTA00014597**, still produces zero richer-parser candidates because of fragmented header text. This case remains open and is not silently reconstructed. The wave is not yet ready for automatic integration or contact analysis.

## Reproduce

For the local OCR check, with the saved individual render:

```powershell
powershell.exe -NoProfile -File scripts/ocr-image-windows.ps1 -ImagePath "ABSOLUTE_PATH_TO_EFTA00039023-p2.png" -OutputPath "ABSOLUTE_PATH_TO_LOCAL_OCR_JSON"
```

The helper uses Windows PowerShell 5.1 and the installed en-US Windows OCR language. It records engine, OS version, image dimensions/hash, text, lines and word boxes; no external OCR service is called. It checks the engine’s maximum image size. The source PDF can be rendered again locally with pypdfium2; the measured check used scale 2, producing a 1224 by 1620 pixel image.

To rebuild the local reviewed-label outputs from committed source readings and cached native extractions:

```powershell
python scripts/prepare-header-layers.py --out data/pilot/2026-11-07-wave-01
```

This also writes the metadata-only `header-parser-assessment.json`. It does not write raw text into the public site, change candidate validation status or alter the original 100-document pilot.

## Next step

Review the remaining fragmented header and quoted-body boundaries, then prepare integration of the ten additional PDFs with explicit source-layer display, unreviewed date states and reconciled processing metadata. The public website remains at 100 PDFs; the remaining 90 planned expansion files are still unprocessed.

## Subsequent targeted review

The [boundary follow-up](wave-01-boundary-followup.md) now handles the remaining fragment through an explicit unassigned-fragment layer and records lossless body partitions for the two quote chains. It raises the opt-in wave total to eight candidate occurrences; the original native parser output and public site remain unchanged.
