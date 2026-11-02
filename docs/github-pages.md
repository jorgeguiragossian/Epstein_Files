# GitHub Pages publication

The repository owner explicitly approved publication of the **full pilot viewer, including extracted text and parsed email data**. The static site targets:

https://jorgeguiragossian.github.io/Epstein_Files/

GitHub Pages serves HTML/CSS/JavaScript and cannot run the local Python/SQLite API. `scripts/build-pages.py` validates the existing pilot cache, exports a public JSON bundle, and installs a browser API adapter. The original local application remains available with `python viewer/server.py`.

## Public scope

The published pilot includes all 100 PDFs' extracted page text (1,787 pages), date annotations, 22-name vocabulary and page matches, source metadata, and raw parsed email candidate headers/body segments. The public JSON file can be downloaded directly; it is not protected by the UI. This is the full pilot, not the full collection of all 12 DOJ datasets.

The original PDF binaries are not duplicated on Pages. PDF links go to the official DOJ source at the selected page and may prompt for DOJ's age verification. Original content restrictions, redactions, OCR limitations, uncertain dates, incomplete identity evidence, and conservative email-grouping labels still apply.

There are no private API credentials, local filesystem paths from the application configuration, or paid AI calls in the build. Cached originals and extraction files stay ignored on `main`. The authorized public text/email export is published as a generated artifact on the **`gh-pages` branch**; it is therefore public in both that branch and the website. The earlier local-only cache policy does not imply that this export is private.

## Build and validate

With the pilot PDF/extraction cache available locally:

```powershell
python scripts/build-pages.py
python scripts/check-pages.py
node tests/test_static_pages.mjs
python -m unittest discover -s tests -v
```

The default output is ignored `site-dist/`, and the base path is `/Epstein_Files/`. `build-info.json` records the source revision and coverage. The data bundle is approximately 2.7 MB before HTTP compression. The browser searches downloaded text locally and preserves the document/date/person/email review behavior; no Python server or external database is needed by visitors.

The adapter tests compare 13 static responses with the existing Python catalog, checking search result IDs and page sets, combined dates/person filters, source detail, email review, invalid inputs, DOJ links, and project-subpath URLs. Case-insensitive word matching uses browser Unicode tokenization with accent folding; it does not add fuzzy matching or entity resolution.

## Publish and update

Commit and push source changes to `main`, then rebuild so the manifest identifies that revision. Publish only the contents of `site-dist/` at the root of `gh-pages` (including `.nojekyll`). Pages is configured to build from that branch's root. No ignored cache folders or original PDFs should be added to the deployment branch.

`scripts/github-pages.py status`, `enable`, and `build-status` use the existing Git credential manager to call GitHub's Pages API. Credentials stay in process memory and are never printed, written to an artifact, or included in the client. `enable` creates Pages with the `gh-pages` source if none exists and declines to switch a different existing source silently.

Future deployments must rebuild from available source caches and repeat validation. This publication does not introduce an unattended re-ingestion or automatic deployment workflow. Repository branch protection, if configured later, may require changing the publication process.
