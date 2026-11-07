# Dataset 8 extraction wave 1 — November 7, 2026

Downloaded and natively extracted all **ten selected PDFs**, totaling **7,964,305 bytes (7.60 MiB)** and **49 PDF pages**. There were no download or extraction failures. Source size/hash, extraction-source binding, page ordering, character counts and candidate metadata were verified. No exact source-hash duplicates were found within this wave or against the original 100-PDF pilot; this does not establish unique underlying messages or events.

| Source PDF | Pages | Low-text pages | Simple header candidate blocks |
| --- | ---: | ---: | ---: |
| EFTA00009713 | 34 | 1 | 0 |
| EFTA00014597 | 1 | 0 | 1 |
| EFTA00018844 | 1 | 0 | 0 |
| EFTA00021826 | 3 | 0 | 0 |
| EFTA00026433 | 1 | 0 | 1 |
| EFTA00029421 | 1 | 0 | 2 |
| EFTA00032045 | 2 | 0 | 0 |
| EFTA00034623 | 3 | 0 | 0 |
| EFTA00037008 | 1 | 0 | 1 |
| EFTA00039023 | 2 | 1 | 1 |

The native extractor reported **six header blocks across five PDFs** and **49 unvalidated date mentions**. Blocks are detection candidates, not unique emails, verified correspondence or contacts. Dates remain unreviewed; no primary dates or content briefs were assigned.

## Correction and current follow-up

The [targeted quality follow-up](wave-01-quality-followup.md) retracts the original OCR-target finding: EFTA00039023 PDF page 2 is blank except for its stamp. The email body shown in the contact sheet was on page 1. Local OCR and an individual page render confirm the correction. Two explicit source-reviewed header-label layers are now prepared; they do not change native extraction or public parser behavior.

## Visual quality findings

Compared rendered PDFs with native text for **13 of 49 pages**: every first page, both low-text pages, and roster page 2. This is a same-assistant editorial quality inspection, not independent or whole-document verification. Findings are source-hash and page-text-hash bound in `quality-review.json`.

- **EFTA00009713, page 8:** genuinely sparse date/signature page. Its low-text flag does not justify OCR by itself.
- **EFTA00039023, page 2:** the original email-body finding was incorrect and has been retracted. An individual render shows only the EFTA stamp, consistent with native extraction and the later local OCR check.
- **EFTA00021826 and EFTA00032045, page 1:** visibly email-like pages missed by the strict pilot header heuristic. Native labels lose a colon or read Front. Investigate the richer viewer parser before changing detection; do not silently repair evidence or infer redacted senders/recipients.
- **EFTA00009713, pages 1–2:** roster tables lose layout and contain character-recognition artifacts in flattened extraction. Raw word/line order is unsuitable for inferring staff assignments.

OCR was not run in the initial acquisition pass. A later one-page check is recorded in the follow-up. A future OCR pass should retain the native layer separately, cite the PDF page and preserve existing redactions. The remaining 36 pages were not visually inspected in this quality pass. Other recognition errors can remain even on pages exceeding the low-text threshold.

## Saved evidence

Under [data/pilot/2026-11-07-wave-01](../data/pilot/2026-11-07-wave-01/): `downloads.json`, `metrics.json`, `metrics.csv`, `summary.json`, `quality-review.json` and `processing-status.json`. Original PDFs, native page text and rendered review images remain in ignored local caches. The committed metrics contain processing measurements and unvalidated date candidates, not the full extracted page text.

The immutable `selection.json` retains its planning-time status. `downloads.json` status and `metrics.json` status are the authoritative later acquisition/extraction outcomes; inherited catalog status fields in the download rows describe the selection snapshot, not the current processing state. `processing-status.json` makes the current wave outcome explicit. The parent expansion’s `progress.json` records ten processed files and 90 still unprocessed.

The existing catalog export remains the discovery/processing snapshot from before this acquisition, recording the original pilot’s processing metadata. New processing evidence is in the wave manifest; a later integration milestone should reconcile catalog processing status across batches. Discovery totals remain 24,447 URL pairs and the public website still searches **100 PDFs**, not 110. No new raw text, email candidates, dates or summaries were published to the website.

## Reproduce measurements

With cached PDFs and extractions present:

```powershell
python scripts/measure-batch.py --out data/pilot/2026-11-07-wave-01
```

To reconstruct missing local caches, reuse the committed selection with the previously authorized download and analyze commands in [the expansion plan](bulk-discovery-and-expansion.md). The download step verifies cached source hashes before skipping a previously downloaded file.

## Next milestone

The [targeted follow-up](wave-01-quality-followup.md) completes the stamp-only OCR check and prepares reviewed label layers for the two initially missed headers. Before integration, inspect quoted-body boundaries and the additional fragmented header in EFTA00014597, then reconcile document keys, date states, source links and batch processing metadata. New raw text remains local and unreviewed at the document level. The remaining 90 selected files remain unprocessed.

## Published expansion

The [wave 1 integration](wave-01-integration.md) adds ten dataset 8 PDFs to the searchable sample (110 PDFs, 1,836 pages). Dates remain unreviewed; the email workspace labels derived header layers and preserves native source text. Earlier counts and local-only status above describe their original milestone.
