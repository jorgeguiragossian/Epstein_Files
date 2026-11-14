# Private evidence archive

The migration inventory is `data/archive/manifest-2026-11-14.json`: all 582 files
under `data/pilot`, totaling 510,802,898 bytes. This includes 190 source PDFs,
native extractions, retained OCR images/results, provisional editorial layers,
review manifests and pilot metadata. Two files have identical content, giving
580 unique evidence objects.

The bucket is `epstein-files-archive`. Objects use content-addressed keys under
`evidence/sha256/`; the complete relative-path manifest is also uploaded under
`manifests/sha256/`. No bucket settings, public access or lifecycle rules are
changed by the migration. Credentials remain Windows-user encrypted outside
OneDrive and Git. Newline trimming is required when loading the encrypted file.

`scripts/r2-archive.py inventory` creates a bounded inventory and refuses to
overwrite an existing manifest. `scripts/run-r2-archive.ps1 -PythonPath ...`
loads saved credentials in memory and runs the upload without interactive key
entry. It checks local file hashes and exact inventory coverage before and
after transfer. Uploads use conditional object creation; existing content is
downloaded and checked, never silently overwritten. Four concurrent workers
restore every unique object to a temporary disk file, check size and SHA-256,
then discard only that temporary restored copy. Original evidence is retained.
Failed transfers can be re-run; existing objects are verified again.

Successful completion requires a receipt in ignored `tmp/r2-archive/` recording
all verified objects and the remote manifest digest. A compact copy of the
verification receipt can be tracked under `data/archive`. No success is inferred
from object listings or stored metadata alone.

The archive excludes Downloads duplicates, temporary QA sheets under `tmp`,
Python dependencies, Git internals and credentials. Temporary QA sheets are
derivable presentation aids; the pinned OCR evidence they illustrate is covered
under `data/pilot`. Source code and other tracked project records remain in
GitHub. Archive storage is private and separate from the public website.

No local cache is cleared by these tools. Builds still require local source
and evidence files. Before reducing the working cache, implement a manifest-bound
restore command with path containment and hash checks, then test a complete
batch restore and build. The current inventory is a snapshot; future evidence
requires a new immutable manifest and verification receipt.

Validation includes restore round-trip, rejection of corrupt/oversize remote
objects, no overwrite of existing objects, local source preservation, path
containment, complete manifest coverage and changed-source detection. The full
offline suite contains 99 passing tests.

## Verified migration result

Completed November 14, 2026: all 580 unique objects representing 582 files /
510,802,898 bytes were uploaded or found existing, restored and SHA-256 verified.
All 190 PDFs and retained native/OCR evidence are covered. The remote inventory
manifest was restored byte-for-byte and all local source hashes/coverage were
rechecked afterward. `data/archive/verification-2026-11-14.json` records the
verified objects and manifest digest. All local originals remain in place.
This verifies restoration of this snapshot; it is not an independent second
provider backup or permission to clear build caches.
