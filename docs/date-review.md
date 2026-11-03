# Primary-date review and timeframe filters

This page records the original milestone. The [second batch](date-review-batch-2.md) expands current coverage to 36 dated documents, four uncertain and 60 unreviewed. The preparation script now regenerates all 40 reviewed records.

Review date: November 1, 2026 (America/Los_Angeles).

Twenty pilot documents were selected purposively to cover transcript covers, a reporting form, email threads, an exhibit containing forwarded correspondence, and compilations with unclear dates. Each cited PDF page was rendered and visually compared with its extracted text. This is a Codex editorial review, not human verification, authentication of the underlying document, or a representative sample.

## Results

| Status | Documents | Meaning |
| --- | ---: | --- |
| Reviewed date | 17 | A primary day and date role are supported by the cited source context |
| Uncertain | 3 | Date evidence exists but no single primary document date was established |
| Reviewed, undated | 0 | Reserved for reviewed material where no usable date can be established; none assigned in this pass |
| Not yet reviewed | 80 | No date-review conclusion; these must not be called undated |

The 17 assignments comprise 5 transcript session dates, 1 report date, and 11 email sent dates. Date strings elsewhere in a file remain page-level mentions; they are not automatically promoted to primary dates.

## Evidence and interpretation

[`date-reviews.json`](../data/pilot/2026-11-01/date-reviews.json) records each reviewed file ID, original PDF SHA-256, status, primary ISO day if supported, date type, day precision, 1-based PDF evidence page, exact extracted date evidence, review method, timezone policy, and rationale. The date quotes contain date evidence rather than message bodies or participant details. No raw PDF or page image is committed.

- Transcript dates use the session date below the courthouse address. Earlier dates marking a grand-jury designation are not selected simply because they appear first on the cover.
- Report dates use an explicit report-date label. A contact or event date can be a separate role even if it has the same day.
- Email dates use the top-level Date or Sent header. Quoted messages, attachment filenames, and dates of events discussed in the body remain separate.
- The email reproduced on PDF page 2 of `EFTA00039806` is dated February 24, 2019. This dates the reproduced outermost message; it does not establish when the exhibit was assembled. Its quoted 2016 thread is not used as the primary day.
- `EFTA02212905` has an inline May 18, 2017 date in the body without a clear sent-date label. It remains uncertain rather than assuming the inline date is the sent date.
- `EFTA00005740` and `EFTA00005967` are compilations with date-bearing material but no single established compilation date. The latter includes a shipment delivery event; that event does not automatically date the complete file.

Calendar days use the date as displayed in the source header or label. No timezone is inferred, and there is no UTC conversion of a date with unspecified timezone. Review annotations are separate from the original pilot measurements and can be corrected without changing the extracted evidence.

## Viewer behavior

Use **Date status**, **From**, and **Through** above the document index. Both range endpoints are inclusive; either endpoint may be omitted. A range returns only documents with a reviewed primary date. It does not search all dates mentioned on their pages. Search words, dataset, text-quality filters, date status, and the date range combine.

Choose **Uncertain date**, **Reviewed · undated**, or **Not yet reviewed** to inspect those categories separately. Selecting one clears and disables range inputs, because those categories do not have a reviewed primary date. API clients receive HTTP 400 if they combine such a status with a range. Invalid calendar dates and reversed ranges also return HTTP 400.

Each result displays the assigned date and role or its review status. The reader shows the rationale and a **View date evidence** button that opens the cited PDF page. Date details persist when navigating pages, while the list of unverified date mentions changes with the currently open page. Filter settings and reader page are retained in the view URL.

The viewer validates each annotation against the current PDF hash, cited page, and exact extracted evidence before building its index. Duplicate or unknown review IDs, stale source hashes, impossible dates, and primary dates assigned to uncertain/undated records are rejected at startup.

## Reproduce and validate

`python scripts/prepare-date-review.py` regenerates the curated review file from documented assignments and checks that its evidence quotes exist in the extracted cache. This is not an automated date classifier. `--render` additionally writes five ignored local QA contact sheets; rendering requires the optional pypdfium2 and Pillow packages.

```powershell
python -m unittest discover -s tests -v
python viewer/server.py
# In another terminal:
python tests/smoke_viewer.py
```

Tests cover inclusive and open-ended ranges, invalid/reversed dates, combined filters, distinct date statuses, missing reviews, source-hash/evidence mismatches, and exclusion of an agreement's body date from the containing email's primary-date range. A different test port can be used with `smoke_viewer.py --base-url http://127.0.0.1:8766`.

This milestone establishes a reviewable schema and a working filter for 17 dated pilot documents. Reviewing more documents and measuring an automatic date parser against these examples are subsequent steps; the 80 unreviewed documents are not timeframe-ready yet.
