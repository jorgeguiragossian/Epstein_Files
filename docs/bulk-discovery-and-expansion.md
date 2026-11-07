# Official discovery check and next extraction batch — November 7, 2026

## Finding

**No documented Epstein-specific bulk manifest, archive download, or public file-enumeration API was found in the official sources checked.** This is a bounded investigation, not proof that no bulk route exists. The working fallback remains normal browser cataloging. The catalog stays at 24,447 observed file URLs, with datasets 9–11 resuming at zero-based page 61.

| Official source | Check and result |
| --- | --- |
| [DOJ disclosures](https://www.justice.gov/epstein/doj-disclosures) | Expanded the Transparency Act section in the normal browser. Twelve dataset links were exposed; no archive, bulk-download or manifest candidate matched the saved anchor-link check. |
| [Library search](https://www.justice.gov/epstein/search) | Queried the known filename EFTA00039826 and received its dataset 9 PDF link. No bulk/export link observed. This establishes a useful targeted lookup, not enumeration completeness. DOJ states that some formats can be unsearchable or unreliable. |
| [API documentation](https://www.justice.gov/developer/api-documentation/api_v1) and [developer resources](https://www.justice.gov/developer) | The documented API resources include blog entries and press releases. They do not document an Epstein file-enumeration resource. General news API pagination is not evidence that those parameters work for the Epstein Library. |
| [Open Data](https://www.justice.gov/open/open-data) and its linked [Public Data List](https://www.justice.gov/data.json) | Retrieved the JSON successfully: 10,455,182 bytes and 3,267 dataset records. A case-insensitive scan for Epstein anywhere in each serialized record returned zero matches. This checks the public inventory metadata only. |

Evidence is committed under [data/discovery/2026-11-07](../data/discovery/2026-11-07/). The Public Data List check records retrieval time, byte count and SHA-256; its 10 MiB source body is retained only in the ignored local cache `tmp/doj-public-data-list.json`. Browser evidence contains rendered anchor metadata, not raw response bytes or hidden form values. Search evidence contains the query and result link, not document text. Link-candidate rules check archive/JSON/CSV suffixes and bulk/download-all/manifest anchor text. A zero-candidate result does not rule out other published methods.

No guessed ZIP URLs, undocumented endpoints, mirrors, authentication bypasses, messages to DOJ, paid services or corpus downloads were used. Official-domain search results were used to locate relevant public documentation, not to infer a complete corpus.

## Ready-to-run selection

Prepared [100 new PDF URLs](../data/pilot/2026-11-07-expansion/selection.json), plus a [ten-PDF first wave from dataset 8](../data/pilot/2026-11-07-wave-01/selection.json). These manifests are **planned, not downloaded or extracted**. They do not change search coverage.

The deterministic selection uses ten evenly spaced positions in each remaining observed PDF pool for datasets 1–5 and 8–12. Datasets 6 and 7 have no remaining eligible catalog PDFs because all their listed PDFs are already in the pilot. Exclusions remove prior pilot URLs, processed catalog records, non-PDF suffixes and URLs outside the matching official dataset path. Each selected URL carries its observed pool position and matching listing provenance, bound to catalog/provenance hashes and the source Git revision. Later catalog changes do not silently redefine the saved pool.

This is a non-random coverage sample. Dataset 9–11 pools cover only the cataloged first 61 pages; no claim of representative sampling, correspondence content or dates follows from filename position. A URL suffix does not establish valid PDF bytes; the existing downloader checks the response and PDF signature.

Start with the ten dataset 8 files. Their selection spans the completed observed listing and avoids the original seven dataset 8 pilot files. Before processing the remaining 90, measure actual bytes, page counts, native-text yield, OCR needs, extraction failures and correspondence candidates. Preserve ambiguous dates and identities for later source review.

Limits inherited from the existing pilot processor: 64 MiB per file, 512 MiB total cached PDFs per output directory, 60-second download timeout, sequential requests with a pause, and 120-second native-extraction subprocess timeout per file. No OCR, model calls or media processing is enabled. File sizes and page counts remain unknown until acquisition. A byte-limit failure does not mean the file is absent. The native extractor has no total-page cap; inspect first-wave metrics before expanding processing.

## Reproduction and next action

Recreate the plan only into new output directories, retaining the committed selection:

```powershell
python scripts/plan-expansion.py --out data/pilot/NEW-expansion --wave-out data/pilot/NEW-wave-01
```

The next acquisition and measurement milestone can use the existing processor:

```powershell
python scripts/pilot.py download --out data/pilot/2026-11-07-wave-01 --age-confirmed
python scripts/pilot.py analyze --out data/pilot/2026-11-07-wave-01
```

The adult eligibility was confirmed in this project; the flag records that prerequisite. These commands were **not run in this milestone**. Original PDFs and raw extraction text stay in ignored local caches. New text is not automatically added to the public site: first inspect extraction quality and source context, reconcile document identifiers and duplicate hashes, and integrate only with visible coverage/date-review states. Do not inherit date reviews or editorial checks from the old pilot.

The public website remains the 100-document pilot with 36 reviewed-date page briefs. The catalog and its existing continuation points are unchanged. Continue catalog discovery alongside this bounded acquisition work while leaving the bulk-route finding open to new official documentation.
