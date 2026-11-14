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

## Restore/build test and working-cache policy

On November 14, restored all 582 manifest files into an isolated tracked-source
checkout with no ignored evidence caches. The complete 190-document/2,826-page
site build passed all 131 Python/static API comparisons. Its public pilot JSON
was byte-identical to the current artifact, and every original inventory hash
was checked afterward. See `data/archive/restore-build-2026-11-14.json`.
The first restore stopped; a repeat verified all files before building. No
success was recorded until the complete hash validation and build passed.

Restore through the saved-credential wrapper:

```powershell
& scripts/run-r2-archive.ps1 -PythonPath '<bundled-python.exe>' -Action restore -Batch '2026-11-09-wave-09'
```

Omit `-Batch` to restore the complete verified snapshot. The destination defaults
to the project root. `-Destination` may name an isolated directory under project
`tmp` for recovery testing. Retrieval is explicit, not an automatic network call
inside the viewer/build. The command skips matching local files, rejects changed
ones, downloads missing evidence, validates size/SHA-256 before atomic install,
and checks the restored selection again. It rejects changed inventory manifests,
wrong object keys, escaped destinations and unrecognized batch selectors.

The restore tool enforces a 2 GiB evidence-cache ceiling per destination and
leaves at least 1 GiB free disk space. This is a restore guard, not an OS quota
or a limit yet enforced by the separate DOJ acquisition tool. Future ingestion
must respect this policy or add its own guard. No automatic eviction is enabled.
Before eviction, require a matching verified archive snapshot, retain tracked
metadata, and evict only reproducible PDF/native/OCR cache files. Restore all
required batches before a full build; currently every registered batch is needed.
Do not delete credential configuration, unarchived/new evidence, or alter source
hashes to work around a mismatch. The isolated recovery workspace is disposable
and removed after its result is recorded; original caches remain intact.

Validation: 101 offline tests, including restoration, overwrite refusal, manifest
pinning, source changes, path restrictions and cache/free-space budgets.

## Local cache release - November 14, 2026

Released 407 exact manifest-listed ignored cache/extraction files (456,190,489
logical bytes), including 180 older PDFs, after matching archive receipt and
recovery-build proof and rehashing each source immediately before removal.
Latest dataset 4 wave 9 remains active locally, with all its manifest hashes
verified. Tracked metadata, source code, credentials, unverified/changed files,
Downloads and the live website were untouched. The retained pilot files total
54,612,409 logical bytes. OneDrive disk allocation and synchronization can differ
from these logical sizes. Removal inside OneDrive may synchronize there; the
separately verified private R2 archive remains the recovery source.

`data/archive/cache-release-2026-11-14.json` records every released relative path.
Before a complete viewer rebuild or local PDF access to older batches, run the
saved-credential wrapper with `-Action restore` (omit `-Batch` for all evidence).
That temporarily rehydrates the complete roughly 511 MB snapshot; the 2 GiB
restore cap still applies. Restore one batch with `-Batch` for narrower source
work. Do not run a fresh inventory expecting evicted evidence to be local; the
immutable manifest and archive receipt remain authoritative for released files.
No automatic build-time retrieval or automatic eviction is enabled.
