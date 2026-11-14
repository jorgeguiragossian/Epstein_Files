# Private R2 archive setup

Bucket: `epstein-files-archive`, Standard storage, public access disabled.
Use an R2 Object Read & Write key scoped only to this bucket. Do not commit
credentials or paste them into chat. Source archive migration is now the next
milestone, ahead of dataset 5 ingestion.

`scripts/setup-r2-local.ps1` prompts locally for the S3 account endpoint and
hidden access/secret keys. It encrypts the complete configuration using Windows
DPAPI for the current user, saving it under
`%LOCALAPPDATA%/EpsteinFilesArchive/r2-credentials.dpapi`, outside OneDrive and
the repository. It passes decrypted credentials only to the child process
environment and clears those variables afterward. Re-running uses the saved
configuration. Windows account/machine recovery and credential rotation need
separate handling; this file is not a portable credential backup.

Install `requirements-r2.txt` into ignored `tmp/r2-deps`, then run the setup
helper with `-PythonPath` pointing at the bundled Python interpreter. The helper
uses the S3-compatible boto3 API documented by Cloudflare:
https://developers.cloudflare.com/r2/examples/aws/boto3/

The initial test uploads exactly four explicitly selected evidence files
(264,099 bytes total): one PDF, its native extraction, one OCR crop and its OCR
result. Keys are content-addressed under `archive-smoke/sha256/`. Conditional
creation prevents overwriting an existing object. Existing objects are read
back and verified rather than overwritten. The helper never deletes objects,
changes bucket permissions or removes source files.

Each sample is downloaded, checked for exact byte count and SHA-256, and stored
in a new ignored `tmp/r2-smoke/<run>/` directory. A successful `receipt.json`
records local paths, object keys and verified digests without credentials.
Four samples are only a connectivity/restore test, not a full archive backup.
Do not clear project caches after this smoke test. Full migration still needs
a complete evidence inventory, verified upload/restore, and build-cache retrieval.

Offline checks passed for four-file transfer/restore, corrupted-download
rejection, source preservation and PowerShell parsing. No live transfer has
been verified until a successful local receipt exists.
