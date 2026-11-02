# Source-assisted email review

This page records the first batch. See the [third batch](email-review-batch-3.md) for current combined coverage: 45 reviewed candidates, 14 needing boundary attention, and 14 observed header associations.

Fifteen purposively selected candidates were compared by Codex with ten rendered source PDF pages and enlarged header crops. This editorial review is not human verification, document authentication, or a representative accuracy estimate.

Ten detected segments were supported by the visible layout. Four contain inline or forwarded quotations that need separation; one is a forwarding wrapper. All 114 original candidate occurrences and their raw headers, bodies, uncertainty flags, and visible-copy groups remain intact. Unique-message counts and contact rankings remain pending.

Three source-bound name/address associations are recorded in [email-validation.json](../data/pilot/2026-11-01/email-validation.json). Two require a separate visual reading because native extraction damaged the address. These are observed header pairs, not verified account ownership or global person aliases. The viewer displays source readings separately from raw extraction. Source-specific date readings likewise do not replace parsed timestamps or reviewed document dates.

Each review pins the PDF SHA-256, candidate fingerprint, PDF page, extracted line, and exact anchor. Changes invalidate the overlay rather than silently carrying it forward. The preparation script records the bounded editorial findings; it does not automatically infer new reviews. Synthetic checks cover stale evidence, preserved raw fields and grouping, and prohibited identity/count promotions.

The Email review page now offers source-reviewed and quoted-message boundary filters. The next analysis milestone should separate the flagged quotations with explicit parent/child source references, then review a larger correspondence sample before computing contact frequencies.
