# Testing a real CDISC release, step by step

This walks through importing one quarterly release into an OSB database, from the files
on disk to the version history in Neo4j. It assumes nothing beyond a running Neo4j.

Every command is a `curl` you can paste. Substitute `2025-09-26` for whichever release
you are importing.

---

## 0. Before you start

**Two databases.** The service reads and writes a *staging* database and an *MDR*
database. They must be different, and the MDR one is the real OpenStudyBuilder database.

```bash
cd api

OAUTH_ENABLED=false OAUTH_RBAC_ENABLED=false TRACING_ENABLED=false \
  NEO4J_DSN="bolt://neo4j:<password>@localhost:7687/mdrdb" \
  STANDARDS_IMPORT_STAGING_DSN="bolt://neo4j:<password>@localhost:7687/cdisc" \
  pipenv run standards-import-dev
```

`NEO4J_DSN` is the OSB database the release lands in. `STANDARDS_IMPORT_STAGING_DSN` is
the staging one. With OAuth off, everything is attributed to `unknown-user`; that is fine
for a test but means the audit trail is not meaningful.

Swagger is at <http://localhost:8010/docs> if you would rather click than curl.

> **Take a backup of the MDR database first.** The import is append-only and has no undo.
> If anything looks wrong afterwards, restoring is the way back.

**Sanity check** — the service is up and can see both databases:

```bash
curl -s localhost:8010/effective-dates | jq
```

An empty list `[]` is correct on a first run: it lists releases *this service* has staged,
not what the bootstrap script loaded.

---

## 1. Upload the package files

One call per catalogue file, all sharing an effective date. The body is the raw JSON.

**Alternative: let it find the release for you.** If `STANDARDS_IMPORT_CDISC_API_BASE_URL`
is configured, this step can be skipped for SDTM CT — discovery fetches and stages it
automatically. It is a job, same shape as the others:

```bash
curl -s -X POST localhost:8010/packages/discover \
  -H 'Content-Type: application/json' \
  -d '{"api_key": "<your CDISC Library API key>"}' | jq
JOB=<uid>
watch -n2 "curl -s localhost:8010/jobs/$JOB | jq '{status, stats, error}'"
```

`stats` reports `new_release_count`, `skipped_count` and `auto_staged_count` once it
finishes. Other catalogues (`SEND CT`, `ADAM CT`, …) are only *reported*, not fetched —
upload those the usual way, below. Calling this twice in a row reports the same releases
once and then nothing, so it is safe to poll instead of running it again.

```bash
PKG=../import_standards/cdisc_data/packages/cdisc_ct

for f in sdtmct sendct adamct cdashct protocolct define ddfct glossaryct; do
  echo "--- $f ---"
  curl -s -X POST localhost:8010/packages/files \
    --data-binary @$PKG/$f-2025-09-26.json | jq -c '{package_name, codelist_count, term_count}'
done
```

Skip any file that does not exist for that date — not every catalogue ships every quarter.

**Check:** each call returns `201` with the codelist and term counts. Compare them against
the file if you want: `jq '.codelists | length' $PKG/sdtmct-2025-09-26.json`.

**What to watch for:**
- `400` saying the package name disagrees with the effective date — you have mixed up files
  from two releases.
- `replaced_previous_upload: true` — you had already uploaded that catalogue and this
  replaced it. Re-uploading identical bytes is a no-op and returns the existing record.

---

## 2. Upload the paired-codelist workbooks

These say which code codelist each name codelist belongs with. They cannot be derived
from the packages, so without them **new codelists will not be paired**.

```bash
XLS=../import_standards/CDISC_xls

for f in SDTM_paired_view_2025_09_26.xlsx SEND_paired_view_2025_09_26.xlsx; do
  curl -s -X POST "localhost:8010/effective-dates/2025-09-26/pairings?source_file=$f" \
    --data-binary @$XLS/$f | jq -c '{source_file, pairings, skipped: (.skipped | length)}'
done
```

Use the workbooks **for the release you are importing** — the dates in the filenames must
match the release. `CDISC_xls/` also holds earlier ones (`…_2025_03_28.xlsx` and older);
those upload perfectly happily and simply will not contain this release's new codelists,
so the pairings quietly come up short.

**Check:** `pairings` is in the hundreds for SDTM, and `skipped` is small (a handful of
rows with no counterpart is normal). `GET /effective-dates/2025-09-26/pairings` lists what
was stored.

### Optionally, CDISC's own account of what changed

The terminology-changes spreadsheets say in prose what CDISC changed and why. Purely
informational — nothing below depends on them, and uploading one changes nothing about
the release. Note the `.xls`: these are the one legacy binary workbook CDISC still ships.

```bash
for f in sdtmct-2025-09-26.xls sendct-2025-09-26.xls adamct-2025-09-26.xls; do
  curl -s -X POST "localhost:8010/effective-dates/2025-09-26/changelog?source_file=$f" \
    --data-binary @$XLS/$f | jq -c '{catalogue, sheet, entries, collapsed}'
done
```

The package file for a catalogue has to be in first — each entry is stored attached to
the codelist or term it is about — so this belongs after step 1, not before it.

**Check:** SDTM reports well over a thousand `entries`, and a `collapsed` count of around
a hundred. Those hundred are codelist renames, which the sheet repeats once per member
term; they are folded back into the one change they describe.

**Check:** upload a sheet for the **wrong** release and it is refused, naming the row and
the release date it found there. The files do not carry the effective date in a header,
only per row, which is exactly the mistake worth catching.

**Check:** `GET /effective-dates/2025-09-26/changelog` lists them all; add
`?catalogue=SEND%20CT` for one catalogue's. An entry a codelist shares between SDTM and
SEND appears once, with both in `catalogues`.

---

## 3. Analyse

This groups the catalogues together, finds where they disagree, and settles everything
the stored rules cover.

```bash
curl -s -X POST localhost:8010/effective-dates/2025-09-26/analysis | jq
```

This returns `202` immediately with a job (`{"uid": ..., "kind": "ANALYSIS", "status":
"RUNNING", ...}`); the release's status is `ANALYZING` while it runs. Follow it:

```bash
JOB=<uid>
watch -n2 "curl -s localhost:8010/jobs/$JOB | jq '{status, stats, error}'"
```

Expect it to take roughly 20–60 seconds for a multi-catalogue release. Once `status` is
`SUCCEEDED`, read the outcome:

```bash
curl -s localhost:8010/effective-dates/2025-09-26/analysis | jq
```

**Check the response:**

| Field | What it should say |
|---|---|
| `catalogues` | every file you uploaded, and nothing else |
| `status` | `ANALYZED` if nothing is open, `BLOCKED` if something is |
| `grouped_codelist_count` | distinct codelist concepts across all catalogues |
| `inconsistencies[]` | per kind: `total`, `open`, `auto_resolved` |

`auto_resolved` counts are expected to be large — that is the catalogue pecking order and
the seeded rules doing their job. `open` is the only number that holds up the import.

**If `catalogues` is missing one you uploaded**, that file did not land: re-check step 1.
Analysing an incomplete release under-reports disagreements, because there is less to
disagree.

---

## 4. Work the review queue (only if `BLOCKED`)

If a `type` or `strategy` value isn't self-explanatory, `GET /type-descriptions` explains
every one of them — the same text a frontend would show as a tooltip:

```bash
curl -s localhost:8010/type-descriptions | jq '.inconsistency_type.values.SPONSOR_TERM_SEMANTIC_DUPLICATE'
```

**Splitting the queue into "CDISC" and "sponsor impact" without fetching anything.**
`raised_by` on `GET /resolution-strategies` names which step raises each kind — that is a
fixed property of the kind, not of any one finding, so a frontend can partition its UI
into "settle these before you can even assess" and "sponsor impact findings" from this
one static call:

```bash
curl -s localhost:8010/resolution-strategies | jq '.raised_by'
```

```bash
curl -s "localhost:8010/inconsistencies?effective_date=2025-09-26&status=OPEN" | jq -c '.[] |
  {uid, type, concept_id, property, candidates: [.candidates[].value]}'
```

Then look at one in full — this is what shows you *who said what*:

```bash
curl -s localhost:8010/inconsistencies/<uid> | jq '.candidates'
```

Settle it. Pick the strategy that matches the situation:

```bash
# take the value one catalogue gave
# e.g. CONFLICTING_VALUES, CONFLICTING_SUBMISSION_VALUES
curl -s -X POST localhost:8010/inconsistencies/<uid>/resolution \
  -H 'Content-Type: application/json' \
  -d '{"strategy":"PREFER_CATALOGUE","catalogue":"SDTM CT 2025-09-26",
       "note":"SDTM is authoritative here","save_as_rule":true,"rule_scope":"CONCEPT"}' | jq -c '{status, resolution}'

# the values are the same once the stray quotes come off
# e.g. UNWANTED_QUOTES
curl -s -X POST localhost:8010/inconsistencies/<uid>/resolution \
  -H 'Content-Type: application/json' \
  -d '{"strategy":"STRIP_QUOTES","save_as_rule":true,"rule_scope":"OCCURRENCE"}'

# type in a value nobody supplied
curl -s -X POST localhost:8010/inconsistencies/<uid>/resolution \
  -H 'Content-Type: application/json' \
  -d '{"strategy":"CUSTOM_VALUE","value":"Screening"}'

# accept the disagreement and move on
curl -s -X POST localhost:8010/inconsistencies/<uid>/resolution \
  -H 'Content-Type: application/json' -d '{"strategy":"IGNORE"}'
```

**`INCONSISTENT_TERM_SETS` takes only two of them.** The catalogues disagree on which
terms the codelist holds, and that is not a property with a value to write, so anything
that produces one — `PREFER_CATALOGUE`, `PICK_VALUE`, `CUSTOM_VALUE`, `UNION_VALUES` — is
refused with a `400` rather than settling the item without changing anything. Staging
keeps every catalogue's terms, so the two real choices are to accept that union or to
remove a term from it:

```bash
# keep the union of every catalogue's terms
curl -s -X POST localhost:8010/inconsistencies/<uid>/resolution \
  -H 'Content-Type: application/json' -d '{"strategy":"IGNORE"}'

# drop one term from the codelist — `value` names the term, because the finding is
# about the codelist as a whole and names no term of its own
curl -s -X POST localhost:8010/inconsistencies/<uid>/resolution \
  -H 'Content-Type: application/json' \
  -d '{"strategy":"DROP_TERM_FROM_CODELIST","value":"C48262"}'
```

`save_as_rule` is the part worth exercising: it stores the choice so the same disagreement
is settled automatically next quarter. `rule_scope` decides how far it reaches —
`OCCURRENCE` (this concept, this property, this release) up to `GLOBAL` (every finding of
this kind).

Made a mistake? `DELETE /inconsistencies/{uid}/resolution` puts it back in the queue.

**Re-analyse** when the queue is empty. It is safe, and it is what applies your decisions
to the staged values — same job-and-poll shape as before:

```bash
curl -s -X POST localhost:8010/effective-dates/2025-09-26/analysis | jq
JOB=<uid>
watch -n2 "curl -s localhost:8010/jobs/$JOB | jq '{status, stats, error}'"
curl -s localhost:8010/effective-dates/2025-09-26/analysis | jq '{status, open_inconsistency_count}'
```

**Check:** your decisions survived — the same items now show `RESOLVED` rather than `OPEN`:

```bash
curl -s "localhost:8010/inconsistencies?effective_date=2025-09-26&status=RESOLVED" | jq length
```

---

## 5. Preview — the most important check

This writes nothing. It is your last look before anything touches OSB.

```bash
curl -s localhost:8010/effective-dates/2025-09-26/preview | jq
```

**What good looks like** for a quarterly release onto a populated OSB:

```
codelists: new≈25    updated≈5     unchanged≈1150
terms    : new≈600   updated≈180   unchanged≈25000
```

**`unchanged` must dominate.** That is the single most informative number here.

> **If `updated` is in the thousands, stop and do not import.** It means the values being
> computed do not match how the existing data was written, and every concept would be
> given a pointless new version. Nothing has been written yet, so there is no harm done —
> report it instead.

Also check:
- `new_catalogues` is empty unless CDISC genuinely added a catalogue type
- `new_packages` lists one package per file you uploaded

`can_import` will still be `false` at this point, with a blocker saying sponsor impact has
not been assessed. That is the next step; everything else in `blockers` should be gone.

---

## Exploring the release as a whole

Optional, and read-only — nothing here settles a finding, that is still
`POST /inconsistencies/{uid}/resolution`. Useful once a release is large enough that
the flat `/inconsistencies` queue stops being the fastest way to see where you stand.

```bash
# release-wide counts, review items by pass, review progress
curl -s localhost:8010/effective-dates/2025-09-26/dashboard | jq

# one row per codelist worth a look — changed, or carrying a finding
curl -s localhost:8010/effective-dates/2025-09-26/codelists | jq -c '.items[] |
  {codelist_id, change_status, findings, review: .review.status}'

# only what still blocks
curl -s "localhost:8010/effective-dates/2025-09-26/codelists?has_open_findings=true" | jq

# everything on one codelist: its own diff, its terms, every finding scoped to it
curl -s localhost:8010/effective-dates/2025-09-26/codelists/C66781 | jq

# mark it reviewed — refused while anything on it is still OPEN or INFORMATIONAL.
# Review is a wider guarantee than import: an INFORMATIONAL finding never blocks the
# import, but "reviewed" means somebody looked at everything, that included.
curl -s -X POST localhost:8010/effective-dates/2025-09-26/codelists/C66781/review | jq

# take that back
curl -s -X DELETE localhost:8010/effective-dates/2025-09-26/codelists/C66781/review | jq
```

**Check:** a codelist whose only change is a term CDISC dropped shows up with
`membership_change: "ENDED"` on that term and `change_status: null` — null, not
`"UNCHANGED"`, because this release does not define the term at all.

**Check:** if you uploaded the changes spreadsheets, the same call carries CDISC's own
note of why — `.changelog` on the codelist for its own, and on each term row for that
term's:

```bash
curl -s localhost:8010/effective-dates/2025-09-26/codelists/C67154 | jq -c '
  {codelist: [.changelog[].change_summary]},
  (.terms[] | select(.changelog != []) | {concept_id, why: [.changelog[].change_summary]})'
```

**Check:** `?show=all` on either list endpoint returns everything, changed or not —
the default view is deliberately the smaller, "needs a look" one.

**Check:** reviewing a codelist with an open or informational finding fails with a `400`
naming how many. Settle or acknowledge it, review again — this time it succeeds and the
response carries `reviewed_by`/`reviewed_at`.

**Check:** re-run the analysis so it reopens something on an already-reviewed codelist
(or just `DELETE /inconsistencies/{uid}/resolution` on one of its findings), then
`GET` the codelist again — `review.status` reads `REVIEWED_STALE`, and `reviewed_by`/
`reviewed_at` are unchanged from before. Review it again once the new item is settled
and it goes back to plain `REVIEWED`.

---

## 6. Assess what it lands on

The preview covered the CDISC side. This covers what the release would collide with in
the codelists and terms **your organisation** added.

```bash
curl -s -X POST localhost:8010/effective-dates/2025-09-26/sponsor-impact | jq
```

Same shape as analysis: `202` with a job, release status `ASSESSING` while it runs.

```bash
JOB=<uid>
watch -n2 "curl -s localhost:8010/jobs/$JOB | jq '{status, stats, error}'"
```

```json
{
  "status": "SUCCEEDED",
  "stats": {
    "open_finding_count": 2,
    "checked_codelists": 25,
    "checked_memberships": 143,
    "checked_semantically": 0,
    "checked_updated_terms": 180
  }
}
```

**Read `stats.checked_*` before you read the findings, and read them from the job, not
from `GET .../sponsor-impact`.** What a run compared is not stored — it is a property of
that run, not of the release — so the `GET` below reports `status` and the finding counts
but not `checked_*`. A `stats.checked_memberships` of 0 has not given you a clean bill of
health — it means none of the codelists being extended holds a sponsor term, so there was
nothing to compare. That is a different answer from "compared, and nothing collides".

```bash
curl -s localhost:8010/effective-dates/2025-09-26/sponsor-impact | jq
```

```json
{
  "status": "BLOCKED",
  "open_finding_count": 2,
  "by_match_tier": {"CASE_INSENSITIVE": 5, "EXACT": 2, "NORMALIZED": 1}
}
```

If `STANDARDS_IMPORT_SEMANTIC_PROVIDER` is configured, a language model is also asked
about the codelists the strings could not answer for, raising
`SPONSOR_TERM_SEMANTIC_DUPLICATE`. Those never block; they are a suggestion with a
confidence, and `stats.checked_semantically` on the job says how many terms were put to
the model. Unconfigured — the default — that count is zero and nothing else changes.

Anything at the `EXACT` tier stays `OPEN`, and it is the only tier that does. Those are the
collisions that break a uniqueness rule the main API enforces — a CDISC term arriving with
the name of a sponsor term already in that codelist — and this app's Cypher will not stop
them, so somebody has to look. Work them the same way as any other review item:

```bash
curl -s "localhost:8010/inconsistencies?effective_date=2025-09-26&status=OPEN" | jq \
  '.[] | {uid, type, concept_id, related_concept_id, match_tier, candidates}'

# keeping both is a perfectly good answer — it just has to be given
curl -X POST localhost:8010/inconsistencies/<uid>/resolution \
  -H 'Content-Type: application/json' -d '{"strategy":"ACKNOWLEDGE"}'
```

**`?status=INFORMATIONAL` lists the near-matches** — `CASE_INSENSITIVE`, `NORMALIZED`,
and `SPONSOR_TERM_SEMANTIC_DUPLICATE`, `SPONSOR_CODELIST_DUPLICATE` and
`SPONSOR_NAME_DIVERGED` at any tier — none of them block, and none of them are settled by
a rule any more; there is nothing left to disable. `ACKNOWLEDGE` on one of these moves it
to `RESOLVED`, same as above, purely so a person's own review is distinguishable from
"nothing has looked at this yet":

```bash
curl -s "localhost:8010/inconsistencies?effective_date=2025-09-26&status=INFORMATIONAL" | jq
```

Each candidate reads `TIER:sponsor_uid:what matched what`, so the sponsor term to go and
look at in the main API is right there.

Accepting is not the only answer. Where the sponsor term is genuinely superseded:

```bash
# retire it and take it out of the codelist, in one decision
curl -X POST localhost:8010/inconsistencies/<uid>/resolution \
  -H 'Content-Type: application/json' -d '{"strategy":"RETIRE_SPONSOR_TERM"}'

# or just take it out of this codelist, leaving the term alone elsewhere
curl -X POST localhost:8010/inconsistencies/<uid>/resolution \
  -H 'Content-Type: application/json' -d '{"strategy":"REMOVE_SPONSOR_FROM_CODELIST"}'
```

Both are refused with a `400` while **anything still refers to the sponsor term**, and the
message names what does. Move that usage onto the CDISC term through the main API first —
retiring a term out from under a study is something nothing else in OSB will stop you
doing. `usage_count` on each finding tells you in advance which ones are free.

Neither can be saved with `save_as_rule`: a standing rule would retire sponsor content
unattended, quarter after quarter.

Re-run the assessment after settling, and check the preview again: `can_import` should now
be `true`.

> **If you re-analyse after assessing, you have to assess again.** Analysis rebuilds the
> settled values the assessment compared against, so the import refuses an assessment
> older than the last analysis and says so.

### Giving the semantic check something to find

The string comparison catches a CDISC term arriving with a sponsor term's name or
submission value. What it cannot catch is the same concept under a name sharing no words,
which is what the semantic check is for — so to see that check do anything, the collision
has to be invisible to the strings.

Two that work against the **2025-09-26** release, assuming an MDR whose newest package is
`2025-03-28`. Both codelists are extensible and neither is covered by a naming rule, so the
name compared is CDISC's preferred term exactly as shipped.

| Codelist | Sponsor term to create | CDISC term arriving in that release | Why the strings miss it |
|---|---|---|---|
| `C67154` Laboratory Test Name | **Cytolysin** (`CYTLYS`) | `C221544` Perforin-1 Measurement | Perforin-1 is also called cytolysin — no word in common |
| `C65047` Laboratory Test Code | **Animal Starch** (`ANSTRCH`) | `C221431` Glycogen Measurement | Glycogen's historical name — again nothing shared |

Create them through the **main API** (port 8000), not by hand in the database — that way
they are real sponsor terms, versioned and attributed like any other:

```bash
curl -s -X POST localhost:8000/ct/terms -H 'Content-Type: application/json' -d '{
  "library_name": "Sponsor",
  "catalogue_names": ["SDTM CT"],
  "codelists": [{"codelist_uid": "C67154", "submission_value": "CYTLYS"}],
  "sponsor_preferred_name": "Cytolysin",
  "sponsor_preferred_name_sentence_case": "cytolysin",
  "nci_preferred_name": "Cytolysin Measurement",
  "definition": "Measurement of the pore-forming protein released by cytotoxic T lymphocytes and natural killer cells."
}' | jq -c '{term_uid, sponsor_preferred_name}'

curl -s -X POST localhost:8000/ct/terms -H 'Content-Type: application/json' -d '{
  "library_name": "Sponsor",
  "catalogue_names": ["SDTM CT"],
  "codelists": [{"codelist_uid": "C65047", "submission_value": "ANSTRCH"}],
  "sponsor_preferred_name": "Animal Starch",
  "sponsor_preferred_name_sentence_case": "animal starch",
  "nci_preferred_name": "Animal Starch Measurement",
  "definition": "Measurement of the branched glucose polymer stored in liver and muscle tissue."
}' | jq -c '{term_uid, sponsor_preferred_name}'
```

**The definitions deliberately describe the substance without naming the CDISC term.** They
are half of what the model is shown and worth about ten points of recall — but a definition
that says "glycogen" turns the exercise into keyword matching and proves nothing.

`POST /ct/terms` always creates the term in **Draft** — the route has no approve option.
The assessment reads Draft sponsor terms too, deliberately: the main API's own
name-uniqueness rule exempts only *Retired* terms, so a Draft one already blocks a
duplicate name and the collision is real. The check therefore fires either way. Approving
is closer to what a sponsor term normally looks like, and takes two calls per term — the
two halves are approved separately:

```bash
curl -s -X POST localhost:8000/ct/terms/<term_uid>/names/approvals
curl -s -X POST localhost:8000/ct/terms/<term_uid>/attributes/approvals
```

Then assess, with a provider configured:

```bash
curl -s -X POST localhost:8010/effective-dates/2025-09-26/sponsor-impact | jq
curl -s "localhost:8010/inconsistencies?effective_date=2025-09-26\
&inconsistency_type=SPONSOR_TERM_SEMANTIC_DUPLICATE" | jq '.[] | {concept_id, related_concept_id, candidates}'
```

**What good looks like.** `checked_semantically` of 76 — both codelists send all 38 of their
additions, because none of them was string-matched. Two findings, both `INFORMATIONAL`: a
model's suggestion is recorded, never blocking, and settled only by a person through
`ACKNOWLEDGE`. The answer is in the candidate text, reading
`HIGH:<sponsor term uid>:may be the same concept as sponsor term 'Cytolysin' — …`.

Nothing found is a result too, and worth reporting rather than retrying: it says the model
you configured cannot make these two connections, which is the thing you were testing.

Re-assessing costs nothing after the first run — answers are cached on the prompt — so pass
`?refresh=true` while iterating on a model or a prompt.

### CDISC's own changes, where OSB already refers to what changed

A different question from everything above: not a collision with something the sponsor
built, but a CDISC change to a term landing on a reference OSB already has. Same job,
same response — nothing extra to run:

```bash
curl -s "localhost:8010/inconsistencies?effective_date=2025-09-26\
&inconsistency_type=CDISC_TERM_SUBMISSION_VALUE_CHANGED" | jq
curl -s "localhost:8010/inconsistencies?effective_date=2025-09-26\
&inconsistency_type=CDISC_TERM_REMOVED_FROM_CODELIST" | jq
```

**An empty list here is the expected, ordinary outcome — not a sign the check did not
run.** Most CDISC changes land on nothing, and only the referenced ones are worth a
finding at all; `stats.checked_removed_or_changed_terms` on the job says how many
term/codelist pairs were checked, most of them cleanly.

**Giving it something to find**, on a real release where nothing happens to be
referenced: find a term this release changes or removes, then build a reference to it
directly in a **throwaway** MDR database — never a real one, this writes the same shape
`use_term_in_a_study` builds in the integration tests:

```cypher
// find a candidate: a term this release's preview shows as updated, still open in some codelist
MATCH (root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->()-[hv:HAS_VERSION]->(v)
WHERE hv.end_date IS NULL
MATCH (codelist:CTCodelistRoot)-[:HAS_TERM {end_date: NULL}]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(root)
RETURN root.uid, codelist.uid, v.definition LIMIT 5;

// build a reference to it, the same shape any study selection would
MATCH (root:CTTermRoot {uid: '<term_uid>'})
MATCH (codelist:CTCodelistRoot {uid: '<codelist_uid>'})
CREATE (context:CTTermContext)
CREATE (context)-[:HAS_SELECTED_TERM]->(root)
CREATE (context)-[:HAS_SELECTED_CODELIST]->(codelist)
CREATE (:StudyVisit:StudySelection)-[:HAS_VISIT_TYPE]->(context);
```

Then re-assess and look again — the finding for that term now exists, `OPEN`, with
`usage_count` above zero:

```bash
curl -s -X POST localhost:8010/effective-dates/2025-09-26/sponsor-impact | jq
curl -s "localhost:8010/inconsistencies?effective_date=2025-09-26\
&inconsistency_type=CDISC_TERM_REMOVED_FROM_CODELIST&status=OPEN" | jq
```

**Settling it is `ACKNOWLEDGE`, and nothing else** — there is no value to write, only
whether the change has been considered. It settles the item as `RESOLVED`, not
`IGNORED`: this is a live reference somebody has accepted, not a disagreement waved
through, and the two read differently on purpose.

```bash
curl -s -X POST localhost:8010/inconsistencies/<uid>/resolution \
  -H 'Content-Type: application/json' -d '{"strategy":"ACKNOWLEDGE"}' | jq -c '{status}'
```

**Try `IGNORE` on the same finding** and expect a `400` naming the menu — it does not
apply to either of these two kinds:

```bash
curl -s -X POST localhost:8010/inconsistencies/<uid>/resolution \
  -H 'Content-Type: application/json' -d '{"strategy":"IGNORE"}' | jq -r .message
```

`save_as_rule` is refused on `ACKNOWLEDGE` unconditionally — try it, and expect a `400`:

```bash
curl -s -X POST localhost:8010/inconsistencies/<uid>/resolution \
  -H 'Content-Type: application/json' \
  -d '{"strategy":"ACKNOWLEDGE","save_as_rule":true}' | jq -r .message
```

---

## 7. Import

```bash
curl -s -X POST localhost:8010/effective-dates/2025-09-26/import \
  -H 'Content-Type: application/json' \
  -d '{"expected_catalogues":["SDTM CT 2025-09-26","SEND CT 2025-09-26"]}' | jq
```

List every catalogue you uploaded in `expected_catalogues`. It is a guard against
importing a half-uploaded release: the import is append-only, so a catalogue missing now
could never be added afterwards.

It returns `202` immediately with a job. Follow it:

```bash
JOB=<uid>
watch -n5 "curl -s localhost:8010/jobs/$JOB | jq '{status, stats, error}'"
```

Expect 15–60 seconds. `stats` appears when it finishes.

**Check:** `status: SUCCEEDED`, and the `stats` match what the preview predicted.

If it says `FAILED`, the error is on the job and the release goes back to `READY`. Every
step is idempotent, so fixing the cause and re-running is safe.

---

## 8. Verify in the database

```cypher
// the new package is there and chained to its predecessor
MATCH (p:CTPackage {uid: 'SDTM__CT__2025-09-26'})
OPTIONAL MATCH (prior:CTPackage)-[:NEXT_PACKAGE]->(p)
RETURN p.name, toString(p.effective_date), prior.uid;

// a codelist the preview said was updated now has two versions,
// the old one closed on the release date and the new one open
MATCH (:CTCodelistRoot {uid: 'C170524'})-[:HAS_ATTRIBUTES_ROOT]->()-[hv:HAS_VERSION]->(v)
RETURN hv.version, hv.status, toString(hv.start_date), toString(hv.end_date)
ORDER BY hv.start_date;

// an unchanged codelist must still have exactly ONE version — no pointless churn
MATCH (:CTCodelistRoot {uid: 'C66742'})-[:HAS_ATTRIBUTES_ROOT]->()-[hv:HAS_VERSION]->(v)
RETURN count(*) AS versions;

// LATEST and LATEST_FINAL moved to the new version
MATCH (:CTCodelistRoot {uid: 'C170524'})-[:HAS_ATTRIBUTES_ROOT]->(ar)-[p:LATEST|LATEST_FINAL]->(v)
MATCH (ar)-[hv:HAS_VERSION]->(v)
RETURN type(p), hv.version;

// terms that left a codelist are closed, not deleted
MATCH (:CTCodelistRoot)-[ht:HAS_TERM]->()
WHERE ht.end_date IS NOT NULL
RETURN count(*) AS ended_memberships;
```

Then check it through the main API, which is what actually matters to users:

```bash
curl -s "localhost:8000/ct/packages?catalogue_name=SDTM%20CT" | jq -c '.[-2:]'
curl -s "localhost:8000/ct/packages/changes?catalogue_name=SDTM%20CT&old_package_date=2025-03-28&new_package_date=2025-09-26" \
  | jq '{new_codelists: (.new_codelists|length), updated_codelists: (.updated_codelists|length)}'
```

The package-changes numbers should line up with what the preview told you.

---

## Making a release that actually blocks

Real CDISC releases are internally consistent, so a genuine import leaves the review
queue empty and the blocking half of analysis never runs. To exercise it you need package
files that disagree, and there is a command that writes them:

```bash
PKG=../import_standards/cdisc_data/packages/cdisc_ct

pipenv run standards-import-conflicts \
  --primary   $PKG/sdtmct-2025-09-26.json \
  --secondary $PKG/sendct-2025-09-26.json \
  --out /tmp/conflicts \
  --trim 2
```

It **never touches your originals** — doctored copies go to `--out`, and it prints
exactly which concepts it edited.

> Upload the result to a **throwaway staging database**. The copies keep the same package
> names as the originals, so uploading them into a staging database holding a release you
> care about replaces the real files with the doctored ones.

`--secondary` is a second catalogue of the same effective date. Two of the five conflicts
compare one catalogue against another, so without it they are skipped and it says so.
`--trim 2` keeps only the codelists it doctored plus two more, which takes analysis from
about a minute down to a few seconds.

### What it introduces

| Conflict | Review item raised | Needs `--secondary` |
|---|---|---|
| `codelist-quotes` | `UNWANTED_QUOTES` on a codelist definition | no |
| `term-quotes` | `UNWANTED_QUOTES` on a term definition | no |
| `submission-value-quotes` | `UNWANTED_QUOTES` on a term's submission value | no |
| `submission-value-conflict` | `CONFLICTING_SUBMISSION_VALUES` | yes |
| `term-set-conflict` | `INCONSISTENT_TERM_SETS` | yes |

Pass `--include` to pick a subset, for example `--include term-set-conflict`.

The three quoting conflicts go into a codelist the *secondary* file does not define. If
they went into a shared one, quoting a value would also make the two catalogues disagree,
and that disagreement is settled automatically by the catalogue pecking order — which
would muddy what the quote alone was meant to show.

### Using it

```bash
for f in /tmp/conflicts/*.json; do
  curl -s -X POST localhost:8010/packages/files --data-binary @$f | jq -c '{package_name}'
done

curl -s -X POST localhost:8010/effective-dates/2025-09-26/analysis | jq '{status, open_inconsistency_count}'
```

**Check:** `status` is `BLOCKED` with one open item per conflict you asked for, and the
queue names the concepts the command reported:

```bash
curl -s "localhost:8010/inconsistencies?status=OPEN" | jq -c '.[] | {type, concept_id, related_concept_id, property}'
```

The import is then refused with `400` until you settle them, which is the whole point:

```bash
curl -s -X POST localhost:8010/effective-dates/2025-09-26/import \
  -H 'Content-Type: application/json' -d '{}' | jq -r .message
```

### Conflicts that do not block

`CONFLICTING_VALUES` — two catalogues giving different definitions — is settled
automatically by the catalogue pecking order, so it will not hold up an import. To see
one blocked, temporarily point the pecking order at a catalogue the release does not
contain:

```bash
curl -s -X PUT localhost:8010/config/catalogue-priority \
  -H 'Content-Type: application/json' -d '{"catalogues":["GLOSSARY CT"]}'
```

No ranked catalogue then supplies a value, so the conflicts stay open. Put the real order
back afterwards, or every release will raise them from now on.

## Things worth deliberately trying

| Try this | Expected |
|---|---|
| Import the same release twice | `400`, "It has already been imported" |
| Import an *older* release | `400`, refuses to rewrite history |
| Import with a wrong `expected_catalogues` | `400`, lists what is actually staged |
| Import while something is `OPEN` | `400`, names the open count |
| Re-upload a package with changed content | `replaced_previous_upload: true`, release resets to `FILES_STAGED` |
| Re-upload identical bytes | no-op, status unchanged |
| Analyse, resolve, re-analyse | the decision survives |
| Analyse, resolve, change the file, re-analyse | the decision is **discarded** and the item reopens |
| Resolve the last open item, then import **without** re-analysing | `400`, names how many decisions are newer than the analysis |
| Upload a package or workbook to an already `IMPORTED` release | `400`, its files can no longer be changed |
| Upload a new workbook to an `ANALYZED` release | release resets to `FILES_STAGED`; the pairings feed the analysis |
| `PREFER_CATALOGUE` on an `INCONSISTENT_TERM_SETS` item | `400`, no property to write the value to |
| `DROP_TERM_FROM_CODELIST` with no term named anywhere | `400`, neither finding nor rule says which term |
| Import without assessing sponsor impact | `400`, "Sponsor impact has not been assessed" |
| Assess, then re-analyse, then import | `400`, the assessment predates the analysis |
| Assess while an analysis item is still `OPEN` | `400`, the name to compare has not been chosen yet |
| Assess an already `IMPORTED` release | `400`, it is past the point where a decision could apply |
| `PICK_VALUE` on a sponsor impact finding | `400`, there is nowhere to write a value |
| `GET .../sponsor-impact` before assessing | `404`, which is not the same as "nothing found" |
| `RETIRE_SPONSOR_TERM` on a term a study uses | `400`, naming what refers to it |
| Decide to retire, then start using the term, then import | `400` before the run starts, so nothing is half-written |
| `RETIRE_SPONSOR_TERM` with `save_as_rule: true` | `400`, it can never stand for every release |
| `RETIRE_SPONSOR_TERM` where the CDISC term hits two sponsor terms | `400`, name one as `value` |
| Retire, then import, then assess the release after it | the collision is gone — retired terms are exempt |
| Assess with `STANDARDS_IMPORT_SEMANTIC_PROVIDER` pointing at nothing that exists | `400`, asked-for-and-unavailable is not "switched off" |
| `GET .../codelists/{codelist_id}` for a codelist not in the release | `404`, names the codelist |
| `GET .../dashboard` for an effective date never staged | `404`, same as every other release-scoped read |
| `POST .../codelists/{codelist_id}/review` with an `OPEN` finding still on it | `400`, names how many |
| `POST .../codelists/{codelist_id}/review` with only an `INFORMATIONAL` finding on it | `400` too — review waits on informational findings even though import never does |
| `POST .../codelists/{codelist_id}/review` for an unknown codelist | `404` |
| `DELETE .../codelists/{codelist_id}/review` never marked | no-op, `200` with `NOT_REVIEWED` — not an error |
| `DELETE .../codelists/{codelist_id}/review` for an unknown codelist | `404` |
| Review a codelist, then reopen one of its findings, then `GET` it | `review.status` is `REVIEWED_STALE`; `reviewed_by`/`reviewed_at` unchanged |
| Import a release with codelists still `NOT_REVIEWED` | succeeds — review never blocks import |
| Import a release with an unacknowledged `INFORMATIONAL` finding anywhere on it | succeeds — informational never blocks the import, acknowledged or not |
| `IGNORE` on a `SPONSOR_TERM_DUPLICATE`/`SPONSOR_TERM_SEMANTIC_DUPLICATE`/`SPONSOR_CODELIST_DUPLICATE`/`SPONSOR_NAME_DIVERGED` finding | `400`, names the menu — `ACKNOWLEDGE` is what these take |
| `ACKNOWLEDGE` with `save_as_rule: true` on any sponsor-impact finding | `400`, refused unconditionally |
| `DELETE .../inconsistencies/{uid}/resolution` on an acknowledged `INFORMATIONAL` finding | back to `INFORMATIONAL`, not `OPEN` — it never blocked before the decision either |
| Assess with a gateway that times out | that codelist's answer is lost, the string findings are not |
| Assess twice with nothing changed in between | the model is not asked anything the second time |
| Settle a naming item, re-analyse, re-assess | only the codelist that term is in is asked again |
| `POST .../sponsor-impact?refresh=true` | every question is put again |
| Assess, settle a collision, re-analyse | the decision survives — analysis prunes only its own kinds |
| Assess, settle, then rename the sponsor term in the main API, re-assess | the decision is **discarded** and the item is re-judged at its new tier |
| Start an analysis, then start another analysis on the same release before it finishes | `400`, "Another step is already running" |
| Start an analysis, then try to assess or import the same release before it finishes | `400`, names the step already running |
| Start an analysis, then upload a new file to the same release before it finishes | `400`, "Another step is already running" |
| Start a sponsor-impact assessment, then start an analysis on the same release before it finishes | `400`, names the step already running |
| `POST .../analysis` or `.../sponsor-impact` on a release with no job running | `202` with a job; `GET /jobs/{uid}` follows it |
| `GET .../analysis` or `.../sponsor-impact` before one has ever run | `404`, not the same as "found nothing" |
| `POST /packages/discover` a second time while the first is still running | `400`, "A discovery run is already in progress" |
| `POST /packages/discover` with `STANDARDS_IMPORT_CDISC_API_BASE_URL` unset | `400` immediately — no job is created |
| `POST /packages/discover` with no body, or an empty `api_key` | `422` — the key is required on every call |
| `POST /packages/discover` with a key CDISC rejects | `202`, then the job ends `FAILED` with CDISC's `401`/`403` in `error`; the key appears nowhere in the job or the logs |
| Kill the process mid-analysis (or mid-assessment, mid-import, mid-discovery), then restart | startup fails the abandoned job and reverts its release; a release with no live worker is never left stuck |
| Assess a release where CDISC changes/removes a term nothing refers to | no finding at all — not `AUTO_RESOLVED`, absent from the queue entirely |
| Assess a release where CDISC changes/removes a **referenced** term | `CDISC_TERM_SUBMISSION_VALUE_CHANGED` or `CDISC_TERM_REMOVED_FROM_CODELIST`, `OPEN`, `usage_count` above zero |
| `IGNORE` on either of those two kinds | `400`, names the menu — `ACKNOWLEDGE` is the only strategy they take |
| `ACKNOWLEDGE` with `save_as_rule: true` on either of those two kinds | `400`, refused unconditionally — usage is a fact about today, not a standing rule |
| Build a reference to a changed/removed term after a clean assessment, then import | `400` before the run starts, naming the term — the same "deciding and importing are different moments" guard as a sponsor term |
| Build a reference, re-assess (no import) | a fresh `OPEN` finding appears — usage is re-queried every run, never cached from the last one |
| Remove the reference to an already-flagged term, re-assess | the finding is pruned, the same as any disagreement the data no longer supports |

**Change the file, then re-analyse** is the subtle one: a decision made about one set of
competing values is never silently reapplied to a different set.
