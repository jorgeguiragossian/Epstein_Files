# Email parsing and visible-copy review

This pilot adds an **Email review** workspace at `/emails`, linked from the document explorer. It shows extracted sender/recipient headers, raw dates, parsed timestamp candidates, uncertainty flags, detected body segments, and source PDF/page/line references. It does not produce contact rankings.

The repository owner subsequently authorized a [full GitHub Pages export](github-pages.md), including raw parsed email data. The local cache details below describe storage on `main`; the generated export on `gh-pages` is public and downloadable. The static Email review page is `emails.html` under the project URL.

## Pilot results

The final parser pass over 100 PDFs found **114 candidate header occurrences in 18 documents**. These are unverified email-layout candidates, not 114 independently established emails. A limited source-assisted spot check is recorded in [`email-review-notes.json`](../data/pilot/2026-11-01/email-review-notes.json); no corpus-wide precision or recall estimate is available.

Strict visible-text grouping found **zero repeat groups** in this pilot. That means no matches under the current rules; it does not establish that the underlying messages are all unique. OCR differences, partial quotations, attachments, and extraction ordering can conceal duplicates. Positive exact-copy grouping and incomplete-repeat handling are verified with synthetic fixtures rather than invented real matches.

113 candidates have no syntactically extracted To-address, and 103 have no syntactically extracted From-address. These fields may be redacted, missing, or damaged by extraction. A syntactically detected address is not a verified identity. Four numeric dates remain ambiguous, eight candidates lack a labeled date, and 69 date strings could not be parsed. Twenty-five parsed timestamps lack a timezone. Parsed timestamps do not update the separately reviewed document dates or drive the existing document date filter.

The original pilot's 103 strict header-block detections remain unchanged. The new parser uses different candidate rules, so its larger count is not evidence of validated recall improvement or additional unique messages.

## Parsing boundaries

- Recognize From/To layouts in either order, missing recipient/sender labels where enough other headers exist, Date/Sent and Subject labels, selected wrapped fields, and separately extracted Sent values.
- Carry body segments across PDF pages with original 1-based PDF page and extracted-line references. Recognized EFTA/source-stamp lines are excluded from the detected body; original page text stays unchanged in the document explorer.
- Separate later header blocks, including quoted or forwarded candidates. Later blocks are flagged rather than assumed to be independent messages. Not every inline quoted-message style is supported.
- Keep raw header values. Do not reconstruct redacted participants, repair misspelled addresses, infer people from nearby names, or substitute a body date for a missing sent date.
- Parse supported date formats as candidates. Ambiguous day/month numeric dates remain unresolved. Timezones are not invented; damaged date strings are not silently repaired. Parsed timestamps and header classifications still require source review.
- Flag body boundaries as unverified: a detected segment can contain signatures, quotes, or attachment material. Layout recognition is not a guarantee of a clean RFC email record.

## Grouping rules

The key hashes the complete detected header fields, unresolved header fragments, and complete detected body after whitespace collapse. It preserves body/header case and punctuation, reply/forward prefixes, and raw date values. It does not use subject similarity, partial-body prefixes, fuzzy OCR matching, or name/identity aliases.

- **Single source occurrence:** one detected record under this visible-text key. This does not establish uniqueness.
- **Exact visible copies:** identical visible records with a syntactically detected sender address, at least one To-address, a parsed timestamp, a subject, and a substantive body. They remain unverified groups, not proof of one real-world message or confirmed participants.
- **Possible repeat, incomplete headers:** identical visible records with incomplete fields. They are not promoted to an exact-copy or unique-message claim.

Every occurrence remains in the local catalog. Groups retain all source file/page/line references; filtering by one source document does not discard a group's other copy references. There is no fuzzy merge and no deduplicated contact-frequency denominator in this milestone.

## Data and reproduction

- [`email-summary.json`](../data/pilot/2026-11-01/email-summary.json): committed metadata only: aggregate counts, flags, group membership, candidate IDs, source hashes, PDF pages, and extracted-line references. It includes the input metrics hash. No raw subjects, addresses, or message bodies are included.
- Ignored `data/viewer/emails.json`: local raw candidates and detected body segments, generated by the preparation script.
- Ignored SQLite viewer index: raw candidates rebuilt from the validated pilot cache on server startup. No additional preparation command is required to open the email workspace.

```powershell
python scripts/prepare-emails.py
python -m unittest discover -s tests -v
python viewer/server.py
# In another terminal:
python tests/smoke_viewer.py
```

The preparation script verifies PDF hashes and extraction-source hashes before generating metadata. The viewer performs its existing source validations before parsing. The parser uses only Python's standard library; there are no external AI calls or new downloads. The application remains local-only, and the raw email catalog is ignored by Git.

The API `/api/emails` supports `filter=all`, `filter=unresolved`, or `filter=repeats`, optional `document=EFTA...`, and result `page`. The UI preserves these filters in its URL and exposes raw headers/body behind a disclosure. Invalid filter values, malformed document IDs, and invalid page numbers return HTTP 400.

## Before contact rankings

Review more header/body boundaries against PDFs, resolve date formats without guessing, and create source-backed address-to-person mappings. Epstein-specific To/From analysis must distinguish his verified accounts from mentions of his name, later DOJ correspondence, redacted participants, and nested quoted messages. Until those checks exist, the workspace deliberately reports candidate occurrences and visible groups, with `unique_messages: null` and `contact_rankings_ready: false`.

## Source-assisted validation

A subsequent [15-candidate review](email-validation.md) adds source-bound annotations and three observed header associations. Raw parsing and grouping remain unchanged; contact rankings remain pending.

The five flagged boundary cases now include [source-linked body breakdowns](email-boundaries.md), preserving every original detected body and group while separating quoted text for inspection.

A [second 15-candidate batch](email-review-batch-2.md) brings coverage to 30 candidates and 13 source-bound header associations. Ten candidates now need body/quote-boundary attention; these observations remain ineligible for contact rankings.

The subsequent [AM/PM parser correction](email-date-parser.md) fixes nine derived timestamps and leaves one previously parsed damaged date unresolved. All five source-reviewed clocks now match. Raw evidence and grouping remain unchanged.
