# Wave 11 acquisition — November 15, 2026

Five dataset 9 PDFs from the frozen first wave of phase 02 were downloaded by the user through normal browser access, copied into the ignored project cache and checked for PDF signatures and SHA-256 identity. No response-header capture is claimed. The selection and official DOJ URLs remain unchanged.

The batch contains 4,733,705 source bytes and 65 pages. Native extraction succeeded for all five files. There are ten native header candidates and eleven parser occurrences, not established unique messages. One sparse page is an exhibit cover. No dates, correspondence candidates or identities were promoted by this acquisition pass.

| Document | Pages | Visually inspected pages | Parser occurrences |
|---|---:|---|---:|
| EFTA00039156 | 34 | 1, 17, 34 | 0 |
| EFTA00065579 | 2 | 1–2 | 0 |
| EFTA00072576 | 1 | 1 | 1 |
| EFTA00077515 | 24 | 1, 3, 12, 24 | 2 |
| EFTA00082124 | 4 | 1–4 | 8 |

The bounded visual comparison covers 14 of 65 pages. The policy document's table has flattened reading order. The exhibit letter needs source-assisted OCR assessment for native date/heading errors. Email review must preserve redactions, distinguish quoted messages from current bodies and separate news-clipping attachments, signatures and repeated disclaimers. Longer policy and clipping documents have not received complete content review. Exact scope and UTF-8 page fingerprints are recorded in `quality-review.json`.

Private R2 snapshot `data/archive/manifest-2026-11-15-wave-11.json` covers all 16 batch files, including original PDFs, native extraction, parser candidates and acquisition metadata: 5,186,584 bytes. Every object was restored temporarily and SHA-256 checked; the remote manifest matched byte-for-byte and the local inventory was revalidated. The pinned receipt is `data/archive/verification-2026-11-15-wave-11.json`. Originals and Downloads were retained. Credentials remain encrypted outside Git.

The public viewer is unchanged at 200 PDFs / 2,836 pages. Total acquired documents are now 205; phase 02 has five acquired and twenty pending, with none of its new documents integrated yet. Next: scoped source/header/body-boundary review of the eleven parser occurrences and a bounded OCR assessment of the letter before integration; primary date review follows separately.
