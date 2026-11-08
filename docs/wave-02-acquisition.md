# Wave 2: dataset 9 acquisition and quality triage

On November 8, 2026, the ten dataset 9 PDFs from the unchanged expansion selection were downloaded using their official DOJ listing links through normal browser access. Existing adult-eligibility authorization covered the age-verification prompt. Each download was copied into the ignored wave cache after checking the PDF signature, individual and batch size limits, and SHA-256. Browser response headers were not captured; the download manifest does not invent HTTP response metadata.

The batch contains 38 pages and 2,148,585 bytes. All ten native-text extractions succeeded. Metadata lives in `data/pilot/2026-11-08-wave-02/`; source PDFs and raw extractions remain ignored. `selection.json` retains the parent selection's catalog provenance. `downloads.json` records actual byte hashes, acquisition method and listing URLs. `metrics.json` and `metrics.csv` record native extraction measurements.

Codex visually inspected each first PDF page and the only low-text page, EFTA00064578 page 6. That page is a sparse attachment note with both visible sentences and the stamp captured in native text. No OCR remediation is indicated by this inspection. This is a bounded quality check, not review of all 38 source pages or independent authentication. `quality-review.json` records the exact scope, source hashes and inspected native-page text hashes.

The heuristic extraction metric reports 38 email-header candidates; the current email parser produces 41 unreviewed occurrences across six PDFs. These are different detection methods, not established unique messages. Redacted identities, separated header values, damaged labels, nested chains and signature boundaries need further review. No primary dates or new identity associations were assigned.

Next: inspect candidate boundaries and header alignment against the relevant source pages, preserve native text, and label any justified derived header layer. Then integrate this batch into the viewer with regression checks and review primary dates separately. Do not assume the property deed's recording date is its execution date, or use dates in the exhibit list as its assembly date.

The live site remains at 110 PDFs and 1,836 pages. Across the expansion plan, 20 PDFs are now acquired/extracted, ten are integrated, and 80 remain unprocessed. A fresh clone can reconstruct caches using the existing `scripts/pilot.py download` and `analyze` commands with `--out data/pilot/2026-11-08-wave-02`; browser acquisition may be needed if command-line access is blocked. Compare source bytes before accepting reconstructed review evidence.

## First correspondence review pass

Six outer email candidates, one per correspondence-bearing PDF, now have source-assisted editorial reviews in `correspondence-reviews.json`. Ten individual source pages were inspected (first pages of all six PDFs and second pages of the four multi-page chains). Five candidates have lossless native-body partitions separating authored-text candidates, signatures, header metadata and inline or forwarded quotes where supported. All 41 native candidate payloads remain intact; 35 nested/later candidates remain unreviewed. No derived header correction, identity association, primary-date assignment or public integration was made.

EFTA00073640 needs particular care: a phrase visibly in the outer message body appears at native page 1 line 16, after a nested header. A complete authored-body partition would misrepresent this extraction. That candidate remains flagged with a source-order mismatch and has no body partition. Its page 2 also includes a From label without a colon that the parser misses. Other explicit findings include separated subject/date values in EFTA00059374, damaged subject/attachment text in EFTA00064578, and merged From/To rows in EFTA00079911. None is silently repaired.

Revalidate and materialize the reviewed catalog locally with:

```powershell
python scripts/check-wave-correspondence.py --out data/pilot/2026-11-08-wave-02
```

The checker validates PDF/extraction bindings, parser versions, candidate fingerprints, reviewed native-page hashes and exact body reconstruction. It rejects unique-message or contact-count promotion. The local catalog stays under ignored `extractions/`; the summary and evidence metadata are tracked. All 78 offline tests pass, including changed-source, changed-review and native-field preservation checks.

Five initial quality-review page hashes were corrected to use explicit UTF-8 JSON decoding and UTF-8 text hashing rather than Windows default decoding. `quality-review.json` records the affected pages and correction rationale; source PDF and extraction bytes did not change.

Next: review the remaining nested/later candidates and resolve or explicitly retain header-layout issues before public integration. Do not treat the six scoped reviews as whole-chain verification.
