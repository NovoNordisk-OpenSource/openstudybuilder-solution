# Introduction 
As part of the Clinical MDR project, this repository takes care of the import of
* the controlled terminology (CT) from CDISC.

Later on, other imports like UNII, SNOMED, etc. might be added.

**Data model notes (for anyone reading the Cypher):**
- Every staging node carries `:CDISCStaging` as a second label (e.g.
  `:RawPackage:CDISCStaging`, `:GroupedCodelist:CDISCStaging`) so the MDR role's DENY
  filter and the `verifications/` drift check can enforce isolation.
- Several relationship types and one node label were renamed in the merge to avoid
  collisions with MDR's own rel-types:
  - `HAS_TERM` → `HAS_GROUPED_TERM_MEMBER` (staging grouped/versioned membership edge)
  - `HAS_VERSION` → `HAS_STAGED_VERSION` (staging `VersionedCodelist`/`VersionedTerm` →
    `CodelistVersion`/`TermVersion`)
  - `CONTAINS` → `DM_CONTAINS` (data-models staging containment graph)
  - `Version` node label → `DataModelStagingVersion`
- The staging indexes and constraints previously created by `create_indexes_if_not_existent()`
  inside these scripts have moved to `db/db_schema.py` (`STAGING_INDEXES`,
  `STAGING_CONSTRAINTS`, `STAGING_COMPOSITE_INDEXES`, `STAGING_COMPOSITE_CONSTRAINTS`)
  and are now created by `db/init_neo4j.py` as part of the standard database init. The
  scripts no longer create them themselves.

# Local Setup

## Setup python virtual environment

* Python 3.14 and Pipenv are prerequisites — see the [root README](../README.md#prerequisites).
* Run `uv sync --group dev`
---
## Setup environment variables

Create `.env` file (in the root of the repository) as a copy of `.env.example`

---

## Neo4j database setup

### CDISC DB

The CDISC DB will be created automatically including the index configuration. Nothing to do here.

### MDR DB

The MDR DB needs to be present and have the correct index configuration. See [`db/README.md`](../db/README.md) — the database is ready once the `Initiate neo4j database` step has been run.

## CDISC Data

* Download CT Packages from the CDISC REST API by running:
```shell
uv run poe download_ct_json_data_from_cdisc_api 'your-sub-directory'
```

  This syncs against the JSON files already on disc: every package the API
  offers that has no file yet is downloaded, so a gap in one catalogue is
  filled even when another catalogue already has newer packages. Pass an
  effective date as a second argument to ignore everything older than it
  (use `''` for the directory to keep the default):
```shell
uv run poe download_ct_json_data_from_cdisc_api '' '2025-01-01'
```

  The downloader writes each package on a single line. Re-indent them with:
```shell
uv run poe format_jsons
```

* Download Data Model Versions from the CDISC REST API by running:
```shell
uv run poe download_data_models_json_data_from_cdisc_api 'your-sub-directory'
```

**Note:** These steps can be skipped as the JSON package files is now placed in the repository and will be downloaded when you clone the repository.
This is to avoid high usage of the CDISC API, as there is a rate-limit in place.
---

## Importing Entrypoints - Available for pipelines

### Import data models to both CDISC and MDR databases
The following command will:
* trigger the import of data models into the CDISC DB
* trigger the import into the MDR DB

```shell
uv run poe bulk_import_data_models 'TEST' '' # Second argument is to specify a different data directory
# You can append the name of a catalogue to import, excluding the others, for example 'SDTM' or 'FBDE'
# Both model and IG will be imported, for example SDTM and SDTMIG
```


### Import all CT data to CDISC staging database

The following command will:
* trigger the import of CT into the CDISC staging DB

```shell
uv run poe import_cdisc_ct_into_cdisc_db
```

### Import all CT data from the CDISC staging database into the MDR database

The following command will:
* trigger the import of all staged CT into the MDR DB

```shell
uv run poe import_ct_from_cdisc_db_into_mdr
```

### Import Data Models data to CDISC database only

The following command will:
* trigger the import of Data Models into the CDISC DB

```shell
uv run poe import_cdisc_data_models_into_cdisc_db 'TEST' ''  # Second argument is to specify a different data directory
# You can append the name of a catalogue to import, excluding the others, for example 'SDTM' or 'FBDE'
# Both model and IG will be imported, for example SDTM and SDTMIG
```

---

## Evaluating package changes before an import

Diff several CT packages of the **same catalogue** to see what an import would
bring in. Reads the raw package JSON files directly — no Neo4j, no API, no
network — and writes a Markdown report.

```shell
pipenv run diff_cdisc_ct_packages sdtmct-2024-03-29.json sdtmct-2024-09-27.json sdtmct-2025-03-28.json
```

Files are sorted by `effectiveDate` and diffed as a chain — one section per
consecutive release, plus a cumulative oldest-to-newest rollup. Bare filenames
are resolved against `CDISC_JSON_DIR` from your `.env`, so no path is needed;
pass `--json-dir` to point somewhere else, or give full paths instead. At least
two files are required.

| Option | Purpose |
|---|---|
| `--out PATH` | Report path. Defaults to a timestamped file in the current directory. |
| `--json-out PATH` | Also write the structured diff as JSON, for downstream tooling. |
| `--changelog-dir DIR` | Annotate changes with CDISC's own rationale. Defaults to `<CDISC_XLS_DIR>/changelogs`. Pass `""` to skip. |
| `--stdout` | Also print the report. |

Every change is rendered as a table row, in the flat report and on every page of
the review site alike. A release is thousands of near-identical facts, and the
one thing a reviewer does with them — read a single column, which term, which
property, what the value became, straight down the list — needs fixed columns.
Columns that are blank for every row of a table are dropped rather than printed
empty, and a cell holding several values (synonyms, codelists, change-log
requests) gets one per line.

Changes are grouped into categories, ordered so a reviewer can stop reading once
it stops mattering. The order carries the judgement; the names only describe
what happened, so nothing tells a reviewer what to conclude:

| Category | Contains |
|---|---|
| Codelists removed | a codelist is gone from the package |
| Terms removed from the catalogue | a term no longer exists anywhere |
| Terms removed from a codelist | a term left this codelist but still exists elsewhere |
| Submission values changed | a term's submission value in a codelist changed |
| Terms added to existing extensible codelists | a term added to, or moved into, a codelist that already existed and was **already extensible** |
| Terms moved between codelists | a term left one codelist and entered another, neither extensible |
| Terms added to existing non-extensible codelists | a term added to a codelist that already existed but nobody could extend |
| New codelists | a codelist this package introduces |
| Terms added to new codelists | a term arriving in one of those new codelists |
| New terms in the catalogue | a conceptId that did not exist in the older package |
| Codelist names and descriptions updated | a codelist's `name`, `preferredTerm`, `definition`, `synonyms` or `extensible` |
| Term names and descriptions updated | a term's `preferredTerm`, `definition` or `synonyms` |

The two removal categories are split because they are very different facts. A
term gone from the catalogue resolves against nothing, anywhere; a term that
merely left one codelist is still there, just not where it was.

Additions are cut four ways because they are the bulk of any CDISC release and
lumping them together hides the only part that needs a human. Two independent
questions decide which category applies — did the codelist already exist, and
could the sponsor already have extended it?

| | already extensible | not extensible |
|---|---|---|
| **existing codelist** | terms added to existing extensible codelists | terms added to existing non-extensible codelists |
| **new codelist** | terms added to new codelists | terms added to new codelists |

Only the top-left cell can collide with a sponsor-defined term. If a codelist
was extensible, the sponsor may already have coined a term of their own in it,
and a CDISC term arriving there can clash by name or submission value.
Extensibility is read from the **older** package — the state the sponsor could
actually have extended — so a codelist that has since been closed is still
flagged. A codelist nobody could extend holds no sponsor terms, and one this
package introduces did not exist to be extended, which is why the bottom row
collapses.

"New terms in the catalogue" counts conceptIds rather than placements, so it
overlaps the three membership categories by design: a genuinely new term is
counted once there and once where it landed.

Codelists and terms are both identified by their `conceptId`. A term's submission
value depends on which codelist it sits in, so term attributes and
term-to-codelist relationships are diffed separately — a submission value change
is reported against the relationship, not against the term.

### Change-log enrichment

The diff says what changed; CDISC's per-release change logs say why. Where a
change can be matched to a change-log row, the report carries that row's request
code and change summary in a `Change log` column:

| Codelist | Submission value | Change log |
|---|---|---|
| `C85495` "Microbiology Susceptibility Testing Result Category" | `MSRESCAT` | CDISC-6596: Retire codelist |

A change citing several requests gets one per line in the cell. Repeated
request codes are collapsed: CDISC files a change-log row per affected
codelist, so a term edited across five of them matches five identical rows.

The JSON output carries the whole matched row, including CDISC's free-text
implementation instructions, which are too long for the report but are the part
that usually says what an importer has to do.

This reads `.xls` files already on disk and never goes to the network — fetch
them first with [`fetch_cdisc_changelogs`](#fetching-the-cdisc-change-logs).
Enrichment is strictly optional and cannot fail a diff: a missing directory, a
release CDISC published no change log for, or a file that will not parse each
log a warning and leave those changes unannotated. The change logs are not
reliably complete, so they annotate the diff and never gate it — an unmatched
change is a change you still have to review.

Both `diff_cdisc_ct_packages` and `generate_cdisc_ct_diff_site` take
`--changelog-dir`, defaulting to `<CDISC_XLS_DIR>/changelogs`.

### What this diff cannot tell you

It compares CDISC against CDISC, from files on disk. What it cannot see is **your**
database — so it cannot say whether a term CDISC is adding lands on one your organisation
already coined, which is the question that decides whether an import is safe here.

That question is answered by the **standards import API** (`api/standards_import/`), as its
sponsor impact assessment: it reads the sponsor half of the MDR database directly, raises a
review item for each collision, and refuses the import until the ones that break a
uniqueness rule have been settled. It also asks a language model about duplicates that
share no words at all, which no string comparison can catch.

This tool used to attempt a version of that over an authenticated API call, against a
snapshot of the sponsor side. That has moved: doing it where the import runs means reading
the database rather than sampling it, comparing the names terms will *actually* be given
rather than the ones CDISC ships, and — most of the point — being able to act on the answer
instead of printing it.

So use this to understand what a release contains, and the standards import API to find out
what it means for your database.

### Generating a review site

The flat report is complete but hard to review: one quarter of SDTM CT is ~1,800
changes in a single document, and 3.5 years is ~22,800. The same diff can be
written as a browsable tree of small pages instead — an overview, a page per
category that can invalidate already-imported data, and one page per changed
codelist.

```shell
pipenv run generate_cdisc_ct_diff_site sdtmct-2021-03-26.json sdtmct-2021-06-25.json
```

Same file-resolution rules as `diff_cdisc_ct_packages`. Output is a timestamped
directory containing `docs/` (Markdown) and `mkdocs.yml`.

| Option | Purpose |
|---|---|
| `--out-dir DIR` | Output directory. Defaults to a timestamped directory in the current directory. |
| `--json-dir DIR` | Directory to resolve bare filenames against. Defaults to `CDISC_JSON_DIR`. |
| `--changelog-dir DIR` | Annotate changes with CDISC's own rationale. Defaults to `<CDISC_XLS_DIR>/changelogs`. Pass `""` to skip. |
| `--max-codelist-pages N` | Cap how many codelist pages are written. The diff itself is never capped. |
| `--build-html` | Render to HTML with `mkdocs build` afterwards. |
| `--serve` | Run `mkdocs serve` for local review. |

**Only changes are rendered.** A codelist nothing happened to gets no page, no
index row and no nav entry, and an empty category is omitted rather than printed
as a heading with "(none)" underneath.

The Markdown is the deliverable — nothing in the package imports mkdocs, and the
default run needs nothing beyond the standard library. `--build-html` and
`--serve` are an optional convenience that shell out to mkdocs, which lives in
`[dev-packages]`; run `pipenv sync --dev` first, or they will tell you they could
not find it and leave the Markdown in place.

`full-report.md` and `full-report.json` are written alongside as the completeness
backstop. They are never capped, and never trimmed to only-changed anything.

### Fetching the CDISC change logs

CDISC publishes a per-release change log as Excel. They are not reliably
complete, so they can only ever annotate a computed diff — but they often carry
the *rationale* for a change, which the JSON packages do not.

```shell
pipenv run fetch_cdisc_changelogs --dry-run     # probe what exists, download nothing
pipenv run fetch_cdisc_changelogs               # fetch everything we hold packages for
pipenv run fetch_cdisc_changelogs --catalogue sdtmct --date 2025-03-28
```

Releases to fetch are read from the package filenames in `CDISC_JSON_DIR`, and
files land in `<CDISC_XLS_DIR>/changelogs` as `<catalogue>-<date>.xls`. Files
already on disk are skipped before any request is made — the server is slow, so
re-runs are cheap. Use `--force` to re-download.

| Option | Purpose |
|---|---|
| `--dry-run` | Report which change logs exist without downloading. |
| `--catalogue PREFIX` | Limit to one catalogue, e.g. `sdtmct`. Repeatable. |
| `--date YYYY-MM-DD` | Limit to one release. Repeatable. |
| `--force` | Re-download files already present. |
| `--out-dir PATH` | Override the destination. |

Two things about the NCI EVS server that are easy to get wrong:

- **A missing file returns HTTP 200**, serving an HTML page, because the site is
  a single-page app. Existence is decided on the response *content type*, never
  the status code — a status-code check reports every guessed URL as a hit.
- **There is no directory listing**, so URLs cannot be discovered; they are
  built from a measured table of per-catalogue directory and file names. Neither
  is derivable from the catalogue name: CDASH, COA, QRS and QS-FT live under
  `SDTM/`, Glossary's files are prefixed `CDISC`, and MRCT omits "Terminology"
  from the filename. A catalogue with no known location is reported and skipped.

The newest release is published undated at the catalogue root rather than under
`Archive/`; the fetcher falls back to it for the newest date and warns, since
that file is whatever CDISC published most recently and may not be the release
you asked for.

Note these are legacy `.xls` (BIFF) files — `openpyxl`, used elsewhere in this
component, cannot read them, which is why `xlrd` is a dependency. Once fetched,
they are read by [change-log enrichment](#change-log-enrichment).

---

## Verify setup is complete
* Open Neo4j browser in your web browser at the address: http://localhost:5074/ (or http://NEO4J_MDR_HOST:NEO4J_MDR_BOLT_PORT), log in with username and password stated in .env file in neo4j_database repository (the value of `NEO4J_MDR_AUTH_PASSWORD` from your `.env`).
* Switch to database cdisc, run command:
```
MATCH (cat:RawCatalogue)-[:HAS_RAW_CODELIST]->(c:RawCodelist) WHERE cat.effectiveDate="2015-12-18"
WITH cat.name as name, count(c) AS count
RETURN name, count
```
* The output should be:
```
name	                count
"SDTM CT 2015-12-18"	480
"SEND CT 2015-12-18"	92
"ADAM CT 2015-12-18"	7
```
* Switch to database neo4j, run command:
```
MATCH (c:CTPackage)-[:CONTAINS_CODELIST]->(cc:CTPackageCodelist) WHERE c.effective_date=datetime("2015-12-18")
WITH c.name as name, count(cc) AS count
RETURN name, count
```
* The output should be the same as before:
```
name	                count
"SDTM CT 2015-12-18"	480
"SEND CT 2015-12-18"	92
"ADAM CT 2015-12-18"	7
```

---

# More information on CDISC Import

For more information on pipeline configuration, see the `*.yml` files in the root of the repository.

For more information on the overall setup, see the section `CDISC CT Integration` in the documentation portal.

For more information on script definitions, see `[tool.poe.tasks]` in [pyproject.toml](./pyproject.toml).

---

## Further Development Commands

- drops the *intermediate* CDISC DB
```cypher
DROP DATABASE `cdisc` IF EXISTS
```

- deletes everything in the currently selected DB
```cypher
:auto MATCH ()-[r]-() CALL { WITH r DELETE r } IN TRANSACTIONS OF 50000 ROWS;
:auto MATCH (n) CALL { WITH n DELETE n } IN TRANSACTIONS OF 50000 ROWS;
```