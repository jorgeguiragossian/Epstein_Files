# Targeted wave header and body reviews — November 7, 2026

Completed the three targeted source-assisted header/body reviews before public integration. Individually inspected EFTA00014597 page 1, EFTA00021826 pages 1–3, and EFTA00032045 pages 1–2. This is Codex editorial review of displayed layout and native text, not independent verification, identity resolution or message authentication.

## Fragmented header

EFTA00014597 has a redacted header and a surviving native fragment located between To and Cc in text extraction. Its visual placement is in the header, but it cannot reliably be assigned to a particular participant field. The explicit `reviewed_header_fragments_v1` layer removes that line only from the parser scan, retains its exact native content as unresolved-fragment metadata, and preserves the original extraction. It supplies no names or addresses.

Checks require the source PDF hash, page-text hash, exact fragment line and surrounding To/Cc labels. The body and remaining source lines keep their original order and line references. The existing parser then recognizes one candidate with the source URL as its body; the URL is neither followed nor corrected. All participant addresses remain unresolved.

## Lossless quote partitions

For EFTA00021826, six spans distinguish an uncertain header-continuation line, the short top-level reply, and the quoted chain and reproduced release extending through pages 2–3. For EFTA00032045, four spans distinguish the top-level reply, signature and quoted chain across two pages. Text classified as quoted is not attributed to the top-level sender and is not promoted to additional message candidates.

The ten spans retain every character of the parser’s detected body when rejoined with its original newline convention. This is losslessness relative to the normalized parser body, not a claim that native extraction captures every visual character or that PDF footers are body text. Source ranges exclude the EFTA page stamps already excluded by the parser. Page, line range, text hash, source PDF hash, candidate fingerprint and derived-layer hash bind each annotation to the reviewed evidence.

The existing body-boundary validator checks the materialized spans, ordering, overlap, source text and full-body reconstruction. Parent candidate bodies are unchanged. All source-reviewed candidates retain `unique_message_verified: false` and `contact_count_eligible: false`.

## Counts and remaining scope

The richer native viewer parser detects five occurrences in the ten PDFs. The earlier two label layers raised this to seven; the new fragment layer raises it to **eight occurrences across seven PDFs**. Three candidates now have targeted header/body source reviews, and two of those have ten lossless body spans. The other five occurrences remain unreviewed. These counts differ from the simple pilot heuristic’s six blocks and must not be combined or treated as unique messages.

Only metadata is committed: `header-fragment-reviews.json`, `candidate-boundary-reviews.json`, `boundary-review-summary.json`, and updated parser/processing assessments. Raw fragment text is limited to the unassigned header artifact; complete derived extraction and body-span text remain in ignored local caches. Original native text, the old pilot’s parser and reviews, source PDFs, and public website data remain unchanged.

## Rebuild locally

With the cached wave extractions:

```powershell
python scripts/prepare-header-layers.py --out data/pilot/2026-11-07-wave-01
python scripts/prepare-wave-boundaries.py --out data/pilot/2026-11-07-wave-01
```

The second command materializes and validates the reviewed candidates and partitions under `extractions/header-reviewed/reviewed-catalog.json`. It fails when candidate fingerprints, source-layer hashes, source text or body reconstruction differ from the recorded review. It never publishes text or enables contact rankings.

## Next milestone

Prepare integration of the ten acquired PDFs with explicit native/derived layer labels, unreviewed date states, source PDF links and reconciled processing metadata. The targeted quality blockers are addressed, but this does not imply a whole-document review or reviewed status for every candidate. Public search remains the 100-PDF pilot until that integration is implemented and checked.

## Published expansion

The [wave 1 integration](wave-01-integration.md) adds ten dataset 8 PDFs to the searchable sample (110 PDFs, 1,836 pages). Dates remain unreviewed; the email workspace labels derived header layers and preserves native source text. Earlier counts and local-only status above describe their original milestone.
