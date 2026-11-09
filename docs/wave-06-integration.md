# Wave 6 photograph/log integration

The ten dataset 1 PDFs are integrated with native extracted text and source-quality notices. The public sample is **160 PDFs / 2,197 pages**. Nine photographs retain stamp-only extraction; the photographed handwritten log retains its original damaged form text. Image-only content is not represented as searchable prose. No OCR, provisional sample literals or source-image copies are included in the public bundle.

The log notice explicitly records that all three local OCR passes were inadequate for handwriting and no replacement was accepted. Dates, full-table transcription and log-number/PDF-ID associations remain unresolved. The other notices explain image/small-label limitations without inferring identities, locations, ownership or dates. Source PDFs remain linked to DOJ.

The explicit `native_quality_v1` registry mode validates acquisition/extraction and pinned quality/OCR-review metadata, revalidates local OCR evidence, and attaches only scoped public quality notices. The shared quality validator now supports batches without compound-file assessments; prior compound review behavior and payloads are preserved. Builds require the original and six expansion PDF/native caches plus local OCR evidence for the two OCR-assessed records. Raw OCR results/images/literals remain ignored.

No correspondence candidates are added: **194 occurrences, 120 scoped reviewed candidates and 53 body breakdowns** remain. All ten new primary dates are unreviewed. Overall dates: **70 dated, 20 uncertain, 70 unreviewed**; existing date-based frequencies/evidence remain unchanged. There are 36 prepared/source-checked briefs, 34 date-evidence-only documents and six reviewed reporting-period PDFs.

Validation: 94 offline tests, 99 static/Python comparisons, real-cache HTTP smoke checks and browser verification of the log notice. The test suite covers quality layers without components and rejects stale source/page evidence; HTTP checks ensure no provisional literal layer appears in public log payloads. All 150 prior document payloads, 194 email records/groups and existing analysis entries are exactly preserved.

The catalog retains 24,447 observed URL pairs and now records 160 acquired/extracted PDFs. The unchanged expansion plan has **60 acquired/extracted/integrated PDFs and 40 unprocessed**. Next: primary-date adjudication for the photographs/log, without assigning image dates from neighboring files, appearance or unverified handwritten fields; then resume remaining selections.
