# Source-linked body breakdowns

Five previously flagged email candidates now have explicit editorial body partitions. Codex assigned exact extracted-line ranges on the four previously visually inspected PDF pages; no general quote-detection heuristic is introduced. The tracked [boundary annotations](../data/pilot/2026-11-01/email-boundaries.json) retain parent candidate IDs, PDF hashes, visible fingerprints, source ranges, exact text and text hashes. Run `scripts/prepare-email-boundaries.py` against the existing email cache to reproduce the curated annotations, then `scripts/prepare-emails.py` to validate and attach them.

Four quote spans are distinguished from authored-text candidates, signatures and uncertain header continuation text. One span is a quoted header with no established body. One candidate contains only a forwarding wrapper; its following quoted message was already indexed. Two annotations link to following existing quoted/forwarded candidates. These links describe source layout, not inferred real-world reply relationships.

All spans in each breakdown must reconstruct the entire original detected body exactly, in source order. Overlapping ranges, changed text/hashes, stale parent fingerprints, missing source review and invalid child references are rejected. The original 114 candidates, raw headers, bodies, flags and copy-group fingerprints remain unchanged. No newly verified messages or contact-ranking denominator are created. The existing five-case boundary filter remains available for inspection; the new breakdowns do not remove uncertainty flags.

The site shows each span separately with links to its PDF page and extracted-line range. Line numbers refer to native extraction, not printed PDF line numbers. Raw detected bodies remain available below the breakdown. This small editorial sample does not establish corpus-wide quote separation or parser accuracy.

Next: review a larger correspondence sample, including sender/recipient fields and message dates, before calculating contact frequencies. Automated quote separation should be measured against a broader reviewed set before changing canonical candidate boundaries or copy groups.
