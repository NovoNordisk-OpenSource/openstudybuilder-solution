# System codelists — which CT codelists StudyBuilder needs to function

StudyBuilder does not treat all controlled terminology equally. Some codelists
are *content* — clinical vocabulary that grows over time, and an empty one is
merely an empty picklist. Others are **system codelists**: the application
resolves them by name or submission value in order to build a form, populate a
runtime enum, or validate a mandatory field. When one of those is missing or
empty, a feature does not degrade — it stops working. The most-cited example:
with no terms in `VisitType`, **no study visit can be created at all**, because
visit type is a required field on the visit form.

This document lists the system codelists and says briefly what each is needed
for.

> **Scope.** This is about *which codelists must exist and be populated*. It is
> not a data-entry guide, and it does not say which *terms* belong in each
> codelist — except in the "Verbatim term names" section, where the application
> depends on specific spellings.

---

## The five ways a codelist dependency breaks

Distinguishing these matters, because they need different fixes and produce
very different symptoms.

| # | Failure | Symptom |
|---|---|---|
| 1 | **Codelist absent** — never created | Split behaviour. Loading a form is **silent** (empty dropdown, `200` with `items: []`); saving raises a **400** naming the submission value. See [Absence surfaces on save, not on load](#absence-surfaces-on-save-not-on-load) |
| 2 | **Codelist exists but has zero terms** | Empty dropdown. If the field is *required*, the form cannot be submitted — the feature is unusable but gives no explanatory error |
| 3 | **Codelist populated, but a term was renamed** | Parts of the UI look up terms by literal name with no null-check and throw a `TypeError`. See [Verbatim term names](#verbatim-term-names--the-quiet-landmine) |
| 4 | **Term recreated as a sponsor term instead of loaded from CDISC** | Worst of the five, because it is **silent**. Code that joins on `concept_id` finds nothing (sponsor terms have none) and returns zero rows rather than erroring. See [Criteria Type](#criteria-type-requires-two-specific-cdisc-terms) |
| 5 | **Codelist exists but was never approved** (no `LATEST_FINAL`) | Identical to mode 1 on save — the codelist is visible in the Library UI while the API reports it "not found". See [The Draft trap](#the-draft-trap) |

Mode 2 is the common one in practice, and the one this document is mostly
about. Mode 3 surprises people. Mode 4 is the one to fear, because nothing
anywhere reports it — the system looks healthy and quietly omits data. Mode 5
wastes the most time, because the evidence appears to contradict itself.

For the epoch and visit paths the API is well-behaved about mode 2: terms are
bulk-fetched into per-uid dicts, so an empty codelist yields an empty dict and
then a clean `ValidationException` ("Visit type with UID '…' is not valid"),
not a crash. The unhelpful part is upstream — the form offers nothing to pick,
and the user sees a required field they cannot satisfy and no explanation.

### Absence surfaces on save, not on load

A missing codelist produces a named error — but only when you save something
that references it. Reading it, to populate a dropdown, is silent. The split is
worth knowing, because a user meets the two halves as apparently unrelated
problems: first an empty dropdown with no explanation, later an error naming a
submission value.

**Reading is silent.** All 65 entries in the frontend's `knownCodelists` map
(`src/api/controlledTerminology/terms.js`) are fetched through one endpoint,
`GET /ct/codelists/terms`, whose service performs **no existence check** — the
identifier goes straight into a filter query, and a filter matching nothing
returns `200 OK` with `items: []`. Absent, empty and misspelled-in-the-map are
indistinguishable. (The identifier is a submission value for 43 of the 65
entries; 21 pass `codelist_uid` and one, `role`, passes `codelist_name`. All
three are unchecked, so the behaviour is the same either way.) (`GET /ct/terms` *does* check and
returns 404, but the frontend does not use it for this.) So **do not read "no
error on page load" as evidence that CT loaded** — query the database instead,
see [Verifying an environment](#verifying-an-environment). Unit subsets behave
the same way: the `subset` filter is a plain membership test with no check that
the name exists.

**Saving is loud, and names the codelist.** The write-path guard is
`CTCodelistGenericRepository.get_or_create_selected_term`, used at 66 sites
covering 42 codelists — every `*_cl_submval` that gets attached to a saved
object. It raises a 400 that reaches the user verbatim:

> The codelist identified by submission value `REPEATING_VISIT_FREQUENCY` was not found.

The visit save path alone routes `TIMELB`, `VISCNTMD` and — when a repeating
frequency is set — `REPEATING_VISIT_FREQUENCY` through that guard, so the message
appears with any of the three. **This is the most useful diagnostic in the
system**, because it names the submission value: grep it against
[`sponsor_codelist_definitions.csv`](datafiles/sponsor_library/sponsor_codelist_definitions.csv)
and you have the missing row. Treat it as a provisioning failure, not a bug.

#### The Draft trap

The resolver behind that message matches through **`LATEST_FINAL`**. A codelist
that exists but was never approved has no `LATEST_FINAL`, resolves to `None`, and
produces the *identical* "was not found" message — so it sits plainly visible in
the Library UI while the API insists it does not exist. That reads as an API bug
and is not one. Check the codelist's status before concluding anything is
missing.

### Three pages crash rather than degrade

Most call sites tolerate an empty array. Three index into it on mount to pick a
default tab, and throw `TypeError: Cannot read properties of undefined` before
the page renders: `views/studies/StudyCriteria.vue` and
`views/library/CriteriaInstances.vue` (Criteria Type), and
`views/library/FootnoteTemplates.vue` (Footnote Type). Both codelists are
Tier 1. This fires on **empty as well as absent**, and the traceback names
neither the codelist nor the cause — easy to misread as a frontend bug.

### "Required" depends on which layer you ask

The frontend and the API disagree about mandatoriness more often than you would
expect, and the *stricter* layer is what users actually hit. `Element Sub Type`
and `Arm Type` are both optional in the API but enforced by the UI. Treat the
union of both layers as the practical requirement, and don't conclude a
codelist is safe to leave empty just because the API tolerates it.

Two things carry **no** CT-codelist dependency at all, despite looking like
they should: **study branch arms** and **study design cells**. Both hold only
uid links to arms, epochs and elements. Likewise `VisitClass` and
`VisitSubclass` are CT-shaped in name only — they are plain Python enums in
`common/utils.py`, so they cannot be extended by adding terms.

---

## Where the truth lives

There is no single hand-written list in the codebase; the requirement is spread
across three places. In order of authority:

1. **`api/common/config.py`** — the block of `*_cl_submval` constants under the
   comment `# Codelist submission values`. This is the closest thing to a
   definitive registry: if the API references a codelist by submission value, it
   is here. The same file pins `study_time_unit_subset = "Study Time"` and the
   two criteria-type concept ids. Grep for the comment rather than a line
   number — the block grows.
2. **[`datafiles/sponsor_library/sponsor_codelist_definitions.csv`](datafiles/sponsor_library/sponsor_codelist_definitions.csv)**
   — the 76 Sponsor-library codelists that `codelistterms1` *creates*. Anything
   not in this file and not in CDISC CT will not exist.
3. **`_STATIC_FIELD_CONFIG`** in
   `api/clinical_mdr_api/domains/study_definition_aggregates/study_configuration.py`
   — the study-field configuration, binding study-level metadata fields to
   codelists by uid. A hardcoded Python list; `FieldConfiguration
   .default_field_config()` simply returns a copy of it.

A CDISC-sourced codelist is *not* created by this repo — it arrives with the
CDISC CT load in `import_standards/`. The distinction matters for
troubleshooting: a missing Sponsor codelist means the sponsor import didn't run
or the CSV row is absent; a missing CDISC codelist means the CT package wasn't
loaded.

---

## Tier 1 — Blocking. A feature is unusable without terms in these

Every row here backs a **required** field, or is dereferenced without a
null-check. `Lib` is CDISC or Sponsor.

| Codelist | Submval | Lib | Needed for — and what breaks |
|---|---|---|---|
| **VisitType** | `TIMELB` | Sponsor | Visit type on the study visit form. **No visit can be created without it.** The canonical example |
| **Visit Contact Mode** | `VISCNTMD` | Sponsor | How the visit happens (on-site / phone / virtual). Required on the visit form — blocks visit creation |
| **Time Point Reference** | `TIMEREF` | Sponsor | What a visit's timing is measured *from*. **Conditionally** required: the API enforces it only once a visit carries a time value ("Time reference UID is required for creating a timepoint"), but that covers every scheduled visit, and the visit form marks it required for most visit classes |
| **Unit Subset** | `UNITSUBS` | Sponsor | Holds **seven subset names**, each gating a different unit picker — `Study Time` is the load-bearing one, covering visit timing, element duration and the study population age fields. See [Unit subsets](#unit-subsets--seven-names-that-gate-unit-pickers). A unit missing from the relevant subset is **silently dropped**, leaving a bare unitless number |
| **Unit Dimension** | `UNITDIM` | Sponsor | Classifies unit definitions; consumed when building units |
| **Unit** | `UNIT` | CDISC | Backs `UnitDefinition.ct_units`. Without unit definitions, all timing and dosing fields are unusable |
| **Epoch Type** | `EPOCHTP` | Sponsor | Required on the epoch form. Epochs are a prerequisite for visits, so this blocks visits transitively |
| **Epoch Sub Type** | `EPOCHSTP` | Sponsor | Required on the epoch form; the sub type is what the user actually picks. Must be imported *after* Epoch Type (parent dependency) |
| **Epoch** | `EPOCH` (`C99079`) | CDISC | Terms here are auto-created/reused per epoch subtype, and it backs the visit form's period list plus auto-creation of a `Basic` epoch for Unscheduled / Non-visit classes. If a subtype term is absent from the Epoch codelist, epoch creation raises an **uncaught `IndexError` (HTTP 500)**, not a validation error — the term lookup returns empty and `_get_or_create_epoch_in_specific_subtype` indexes `epoch_terms_result[0]` with no emptiness check (`services/studies/study_epoch.py`). So a broken codelist looks like a server bug. Note `_get_epoch_type_object` in the same file *is* guarded and raises a clean `ValidationException` — don't confuse the two when tracing a 500 |
| **Element Sub Type** | `ELEMSTP` | Sponsor | **UI-required, API-optional.** The study element form marks it required, so element creation is blocked in practice; the API validates it only when supplied. Import after Element Type |
| **Flowchart Group** | `FLWCRTGRP` | Sponsor | The SoA row grouping. Required to place an activity in the Schedule of Activities; the API rejects an unresolvable term with "There is no approved Flowchart Group Term…" |
| **Criteria Type** | `CRITRTP` | Sponsor | Inclusion/exclusion criteria. `type_uid` is mandatory on criteria templates, **and** the Study Criteria page crashes outright on an empty list (indexes `[0]` of an empty array). Additionally requires **two specific CDISC terms** — see [Criteria Type](#criteria-type-requires-two-specific-cdisc-terms) |
| **Footnote Type** | `FTNTTP` | Sponsor | `type_uid` is mandatory on footnote templates — no SoA footnote can be created. The Footnote Templates page also **crashes outright** on an empty list (indexes `[0]` of an empty array) |
| **Disease Milestone Type** | `MIDSTYPE` | Sponsor | Required to create a disease milestone — `BusinessLogicException("Invalid value for study Disease Milestone type")`. The domain holds a module-level dict rebuilt per service instantiation; a membership check runs *before* the raw dict lookup, so an empty codelist gives a clean error rather than a `KeyError` — but only because of that ordering |
| **Reason For Lock** | `RSNFL` | Sponsor | Required to **lock** a study. Blocks the study lifecycle |
| **Reason For Unlock** | `RSNFUL` | Sponsor | Required to **unlock / release** a study. Blocks the study lifecycle |
| **Null Flavor** | `NULLFLVR` | Sponsor | Must contain the term whose **submission value is `NA`**. Five components (study population, intervention type, registry identifiers, study define) resolve it via `TERM_NOT_APPLICABLE_SUBMVAL` in `constants/study.js` and dereference `.term_uid` without a null-check, so absence crashes the "Not Applicable" checkboxes. Matched on submission value, not name — **renaming the display name is safe**, removing the term is not |

## Tier 2 — Referenced by a real feature, but the field is optional

Missing *terms* here leave an empty picklist and the user moves on. Worth
populating; not worth an incident.

**"Optional" describes the field, not the codelist.** Every codelist in this
table is named in the frontend's `knownCodelists` map and requested
unconditionally, usually on component mount. The API accepts a study or concept
without the *value*; that says nothing about the codelist being skippable. Read
this tier as "a user can finish their task without choosing a value" — **all of
them are still expected to exist.**

| Codelist | Submval | Lib | Needed for |
|---|---|---|---|
| Arm Type | `ARMTTP` | Sponsor | Study arm classification. **Caveat:** optional in the API, but the cohorts UI requires it and misbehaves on untyped arms — treat as closer to Tier 1 than the schema suggests |
| Element Type | `ELEMTP` | Sponsor | Parent of Element Sub Type; optional as a form field but needed to import sub types |
| Epoch Allocation | `EPCHALLC` | Sponsor | Optional field, but the visit form's auto-set logic looks up `Previous Visit` / `Current Visit` / `Date Current Visit` by name unguarded |
| Repeating Visit Frequency | `REPEATING_VISIT_FREQUENCY` | Sponsor | Frequency for repeating visits |
| Visit Sub Label | `VISSUBLB` | Sponsor | Sibling-letter visits (V2a / V2b / V2c) |
| Objective Level | `OBJTLEVL` | Sponsor | Primary / secondary objective ranking |
| Endpoint Level / Sub Level | `ENDPLEVL` / `ENDPSBLV` | Sponsor | Endpoint ranking |
| Type of Treatment | `TPOFTRT` | Sponsor | Compound / treatment classification |
| Delivery Device | `DLVRDVC` | Sponsor | Medicinal product delivery device |
| Compound Dispensed In | `COMPDISP` | Sponsor | Compound dispensing container |
| Operator | `OPERATOR` | Sponsor | Comparison operators in syntax templates |
| Therapeutic area | `THERAREA` | Sponsor | Study therapeutic area |
| Role | `ROLE` | Sponsor | SDTM variable role |
| Data Supplier Type | `DATA_SUPPLIER_TYPE` | Sponsor | Data supplier metadata |
| Data type | `DATATYPE` | Sponsor | CRF / ODM item data types |
| Route of Administration | `ROUTE` | CDISC | Compound administration route |
| Dosage Form | `FRM` | CDISC | Compound dosage form (sponsor names patched on top) |
| Frequency | `FREQ` | CDISC | Dosing frequency (sponsor terms added on top) |
| SDTM Domain Abbreviation | `DOMAIN` | CDISC | Sponsor domain definitions |
| Origin Type / Origin Source | `ORIGINT` / `ORIGINS` | CDISC | CRF item origin |

## Tier 3 — Content and indexing codelists

Not system codelists. Categorisation and vocabulary; an empty one costs you a
filter, not a feature. Listed for completeness because they make up the bulk of
the 76.

- Indexing on library templates: Objective Category, Endpoint Category /
  Sub Category, Criteria Category / Sub Category.
- Activity categorisation: Finding / Event / Intervention Category Definition
  and their Subcategory Definitions.
- SDTM per-domain category families: the `Category for …` codelists (Clinical
  Events, Medical History, Vital Signs, Exposure, ECG, Ophthalmic,
  Reproductive System, Substance Use, Procedure Agents, Concomitant
  Medications, Healthcare Encounters), plus `Name of Treatment - EC/EX`,
  the adjudication and pharmacokinetic test name/code pairs, and the hepatic
  event response list.
- Miscellaneous: Language, Registry Identifier, Development Stage,
  Confirmatory / Non-confirmatory Purpose, Data Collection Mode.
- DDF / ODM data-type family: HL7 FHIR, CDISC ODM, ODM v1.3, ODM v2.0, Simple
  and Semantic Data Type. `CODMDT` is read (not written) when importing CRFs.

## Unit subsets — seven names that gate unit pickers

`Unit Subset` (`UNITSUBS`) deserves separate treatment, because it does not
behave like a normal codelist. Its terms are not values a user picks — they are
**named filters**. Every unit picker in the application asks
`/unit-definitions?subset=<name>` and offers only the units tagged into that
subset. If a subset term is missing, or a unit was never tagged into it, the
picker comes back empty and the unit is silently dropped from whatever was
being saved.

All seven, and what each one gates:

| Subset name | Term uid | Gates |
|---|---|---|
| `Study Time` | `CTTerm_000057` | Visit timing and visit windows, element duration, **and the study population age fields**. The most load-bearing by a wide margin |
| `Study Preferred Time Unit` | `CTTerm_000060` | **SoA rendering** — the visit table, protocol flowchart and SoA settings all resolve the display time unit through this |
| `Age Unit` | `C50400` | Template parameter — appears in criteria templates ("age ≥ [x] [Age Unit]"). **Does not gate the study population age fields**, contrary to what the name suggests: those go through `DurationField`, which reads `studiesGeneralStore.units`, populated from `getBySubset('Study Time')`. If an age picker is empty, check `Study Time`, not this subset |
| `Dose Unit` | `CTTerm_000056` | Medicinal product dosing |
| `Strength Unit` | `CTTerm_000059` | Product formulation strength |
| `Time Unit` | `CTTerm_000058` | Formulation timing fields |
| `Endpoint Unit` | `CTTerm_000061` | Units attached to endpoints |

Two notes worth having:

- **Only two of the seven are named by a constant.** The frontend defines
  `Study Time` and `Study Preferred Time Unit` in `src/constants/units.js`;
  `Dose Unit`, `Strength Unit` and `Time Unit` are passed as **bare string
  literals** in component templates. The API pins only `Study Time`
  (`study_time_unit_subset`) and cites `Age Unit` as the example in its own router
  documentation. So most of these names cannot be found by grepping for a
  constant — which makes them easier to break and harder to audit than the rest
  of this document's dependencies.
- `Age Unit` is a **CDISC-uid term (`C50400`) sitting inside a Sponsor
  codelist**, unlike its six siblings which carry `CTTerm_0000NN` uids. Not a
  problem, but it will look anomalous in any audit that assumes sponsor
  codelists contain only sponsor terms.

The `Age Unit` *subset* is a different thing from the CDISC **Age Unit
codelist** `C66781`, which the frontend declares as `ageUnits`. Both exist, but
`ageUnits` has **no call sites** — it is dead code in `terms.js`. Don't assume a
finding about one applies to the other, and don't take the presence of an
`ageUnits` entry as evidence that anything consumes it.

## Study-level metadata fields

Nine study fields bind to a codelist, declared inline in
`_STATIC_FIELD_CONFIG` as `codelist_uid="C99077"` and so on. All nine point at
**CDISC** codelists, not Sponsor ones:

| Study field | Codelist |
|---|---|
| `study_type_code` | Study Type Response (`C99077`) |
| `trial_phase_code` | Trial Phase Response (`C66737`) |
| `trial_type_codes` | Trial Type Response (`C66739`) |
| `trial_intent_types_codes` | Trial Intent Type Response (`C66736`) |
| `control_type_code` | Control Type Response (`C66785`) |
| `intervention_model_code` | Intervention Model Response (`C99076`) |
| `intervention_type_code` | Intervention Type Response (`C99078`) |
| `trial_blinding_schema_code` | Trial Blinding Schema Response (`C66735`) |
| `sex_of_participants_code` | Sex of Participants Response (`C66732`) |

**None of these is mandatory.** Only `study_number` and `study_title` are
required to lock a study, so every codelist-backed study field can remain null.
They are Tier 2 by function. There is no configuration state to provision
either — the bindings are compiled into the API, so the only requirement is
that the nine CDISC codelists exist.

Three further study fields (`therapeutic_area_codes`,
`diagnosis_group_codes`, `disease_condition_or_indication_codes`) resolve
through dictionary terms (SNOMED etc.), not CT codelists, and are out of scope
here.

---

## Verbatim term names — the quiet landmine

Several places look a term up **by its literal name** and immediately
dereference the result. There is no null-check, so a *rename* — not just a
deletion — throws a `TypeError` and breaks the form. A codelist can be present,
populated and approved and still break the UI if a spelling drifts.

Known name-sensitive terms:

| Term name | Codelist | Used by |
|---|---|---|
| `Study Time`, `Study Preferred Time Unit`, `Age Unit`, `Dose Unit`, `Strength Unit`, `Time Unit`, `Endpoint Unit` | Unit Subset | All seven are passed to `/unit-definitions?subset=` **by name**; five of them as bare literals with no constant. See [Unit subsets](#unit-subsets--seven-names-that-gate-unit-pickers) |
| `Unscheduled`, `Non-visit` | VisitType | Special visit-class handling |
| `Global anchor visit`, `Anchor visit in visit group` | Time Point Reference | Anchor visit logic |
| `Virtual Visit` | Visit Contact Mode | Visit-class auto-set |
| `Basic`, `Treatment`, `Treatment 1` | Epoch | Auto-created epoch for Unscheduled / Non-visit |
| `Previous Visit`, `Current Visit`, `Date Current Visit` | Epoch Allocation | Visit form auto-set |
| `Operator` | (template parameter name) | Syntax template parameters |
| `days`, `weeks` | Unit | Study Epoch **lag time**. `LAG_TIME_UNIT_NAMES` narrows the `Study Time` subset to exactly these two — the subset also carries `day`, `week`, `year`, `years`, which are valid visit timings but not lag times. Declared twice, in `frontend/src/constants/units.js` and `api/clinical_mdr_api/domains/study_selections/study_epoch.py`; the two stacks share no code, so a rename must be applied in both. A closed set (MMA recorded only days and weeks), so unlike the subsets it will not grow |

**Treat these as an API contract.** Renaming one is a breaking change, and the
failure appears far from the edit. If a rename is genuinely needed, grep the
frontend constants and `api/common/config.py` first.

---

## Criteria Type requires two specific CDISC terms

`Criteria Type` is worth calling out because it is a **mixed codelist** — a
Sponsor codelist whose six terms come from two libraries — and because two of
them are pinned by the application.

| Term | Uid | `concept_id` | Library | Ordinal |
|---|---|---|---|---|
| Inclusion Criteria | `C25532` | `C25532` | **CDISC** | 1 |
| Exclusion Criteria | `C25370` | `C25370` | **CDISC** | 2 |
| Run-in Criteria | `CTTerm_000001` | *(null)* | Sponsor | 3 |
| Randomisation Criteria | `CTTerm_000002` | *(null)* | Sponsor | 4 |
| Dosing Criteria | `CTTerm_000004` | *(null)* | Sponsor | 5 |
| Withdrawal Criteria | `CTTerm_000003` | *(null)* | Sponsor | 6 |

Three independent code paths require `C25532` and `C25370` specifically, all
matching on the term's **`concept_id`** attribute:

- `common/config.py` — `ct_concept_id_criteria_type_inclusion` /
  `_exclusion`, passed as query parameters at five call sites in
  `consumer_api/v1/db.py` — this is how the **Consumer API** separates inclusion
  from exclusion criteria.
- `clinical_mdr_api/listings/query_service.py` — a **hardcoded literal** in
  a Cypher `WHERE atv.concept_id = 'C25532' or atv.concept_id = 'C25370'`, not
  read from config. CDISC listings output.
- `clinical_mdr_api/services/ddf/usdm_mapper.py`
  (`DDF_ELIGIBILITY_CATEGORY_INCLUSION` / `_EXCLUSION`) — its own module-level
  constants. USDM / DDF export eligibility criteria.

**Matching on `concept_id` is rename-safe**, which makes this a better pattern
than the by-name lookups in the previous section — you can freely rename
"Inclusion Criteria" without breaking anything. What it is *not* is
**recreation-safe**. `concept_id` is populated only on the two CDISC terms and
is `null` on all four sponsor ones, so if the CDISC CT load is missing and
someone recreates an "Inclusion Criteria" term as a sponsor term, it gets no
`concept_id`, and all three consumers **silently return zero rows**: the
Consumer API reports no criteria, listings come back empty, and USDM export
drops eligibility criteria entirely. No error is raised anywhere.

The other four terms are sponsor-defined and not pinned by any code — they are
safe to rename, reorder or extend. Two smaller ordering notes: the Study
Criteria page defaults to the *first* term by ordinal, so `Inclusion Criteria`
being ordinal 1 is what makes it the default tab; and criteria type names are
used as route parameters, so renaming one changes bookmarkable URLs.

## Load order

Codelists cannot be loaded in isolation; the chain is a hard prerequisite, not
a convention.

```
db/  →  import_standards/  →  api/  →  import_sponsor_data/
        (CDISC CT)            (running)   (sponsor codelists + terms)
```

Within `import_sponsor_data`:

1. **`codelistterms1`** creates the codelist *definitions* from
   `sponsor_codelist_definitions.csv`, then approves names and attributes. It
   also flags certain existing CDISC codelists as template parameters via
   `datafiles/codelist_parameter_set.csv`. Paired code/name codelists
   (`ZATEST`/`ZATESTCD`, `PCTEST`/`PCTESTCD`) are topologically sorted so the
   code list is created first.
2. **`codelistterms2`** imports the *terms*. Must run after step 1, and after
   the CDISC load, because sponsor terms need to resolve which codelist to
   attach to. Internal ordering: Epoch Type before Epoch Sub Type, Element Type
   before Element Sub Type, and a final pass sets explicit ordinals on Epoch.
3. **`unitdefinitions`** runs after terms exist, and builds `UnitDefinition`
   concepts by looking up `UNIT`, `UNITDIM` and `UNITSUBS`.
4. `codelistfinish` patches sponsor-preferred names onto pre-existing CDISC
   Dosage Form terms. Creates nothing.

Seven codelists are **assumed to already exist** from CDISC CT and only receive
added or patched terms here — if the CT package wasn't loaded, these steps fail
to resolve a UID: `Frequency` (`C71113`), `Trial Type`, `Trial Blinding
Schema`, `SDTM Domain Abbreviation`, `Dosage Form`, `Epoch`, `Unit`.

## Template parameters

Thirteen codelists are marked as template parameters, meaning their terms can
be substituted into syntax templates. Eleven come from the
`template_parameter=Y` column in `sponsor_codelist_definitions.csv`:
`VisitType`, `Time Point Reference`, `Repeating Visit Frequency`, `Therapeutic
area`, `Type of Treatment`, `Operator`, `Language`, `Data type`, `Data
Collection Mode`, `Confirmatory Purpose`, `Non-confirmatory Purpose`. Two more
are CDISC codelists flagged retroactively via `codelist_parameter_set.csv`:
`Dosage Form` (`C66726`) and `Frequency` (`C71113`).

Implementation note: the flag is stored as an extra `:TemplateParameter`
**label** on the codelist's `CTCodelistNameValue` node — not as a property. A
query looking for a `template_parameter` field finds nothing and will wrongly
conclude the column is inert.

---

## Verifying an environment

Find codelists that exist but have no terms — the Tier 1 rows in this result
are the actionable ones:

```cypher
// substitute the actual (dated) database name
MATCH (lib:Library)-[:CONTAINS_CODELIST]->(cl:CTCodelistRoot)
      -[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST]->(nv:CTCodelistNameValue)
OPTIONAL MATCH (cl)-[:HAS_TERM]->(t)
WITH lib.name AS library, nv.name AS name, cl.uid AS uid, count(t) AS terms
WHERE terms = 0
RETURN library, name, uid ORDER BY library, name
```

List the unit subsets, and check all seven expected names are present:

```cypher
MATCH (cl:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
      -[:LATEST]->(:CTCodelistAttributesValue {submission_value: 'UNITSUBS'})
MATCH (cl)-[:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr:CTTermRoot)
MATCH (tr)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(nv:CTTermNameValue)
RETURN tr.uid AS termUid, nv.name AS subsetName ORDER BY subsetName
```

> Note the property is **`nv.name`**, not `sponsor_preferred_name` — on the
> `CTTermNameValue` path the latter does not exist and a query using it returns
> a column of nulls rather than an error. Easy to misread as "the subsets are
> missing" when they are all present.

Finding a subset name is not sufficient, though: a subset can exist with no
units tagged into it, which produces the same empty picker. To check the
population of a specific subset, hit the API the way the app does —
`GET /unit-definitions?subset=Age Unit` — and confirm it returns a non-empty
list.

---

## Known gaps

Recorded so they aren't rediscovered as bugs.

- **Two Sponsor codelists are defined but never populated**, with no importer
  reference and no `.env.import` entry: `Study Milestone` (`STUDYMS`) and `Name
  of Treatment - EX` (`EXTRT`). Both are Tier 3, so nothing is blocked. Note
  that `MDR_MIGRATION_DISEASE_MILESTONE` exists but is a different codelist
  (`MIDSTYPE`) — it is not STUDYMS.
  `Pharmacokinetic Test Name` (`PCTEST`) and `Event Adjudication Test Name`
  (`ZATEST`) **are** wired and populated, via
  `MDR_MIGRATION_PHARMACOKINETIC_TEST_NAME` and
  `MDR_MIGRATION_EVENT_ADJUDICATION_TEST_NAME` in
  `run_import_standardcodelistterms2.py`. If one of those looks empty, that is a
  real provisioning failure — not a known gap to shrug at.
- **`MDR_MIGRATION_EPOCH` in `.env.import` is orphaned** — no importer reads
  it, though the README table still lists it. Stale documentation, not a bug.
- **The DDF / ODM data-type codelists have unclear provenance.** No importer in
  this repo populates them, yet they carry terms in a live database. Something
  else loads them; worth pinning down before relying on them.
- **No automated check** asserts that Tier 1 codelists are non-empty. A
  smoke test over the first Cypher query above would catch a bad environment
  before a user hits an unsubmittable form.

---

## Appendix — provenance

Assembled from `api/common/config.py` (the `*_cl_submval` registry), all 76 rows
of `sponsor_codelist_definitions.csv` plus the importer wiring, a frontend
required-field audit over `knownCodelists` and the study forms, and a live Neo4j
instance for term counts. Where sources disagreed, the disagreement is recorded
above rather than resolved silently.

**Snapshot caveat.** Term counts and the empty-codelist list come from one local
development database, not production. The *structure* — which codelists exist,
which fields are mandatory — is from source and is stable; the counts are
indicative.
