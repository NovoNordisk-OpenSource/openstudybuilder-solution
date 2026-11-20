"""Standing decisions: resolution rules and the default catalogue pecking order.

These are the durable inputs to analysis. In `import_standards/cdisc_staging.py` the
equivalents are Python constants — a catalogue priority list and a handful of
date-specific special cases — which means every decision ever taken about CDISC data
is invisible to anyone not reading that source file, and unchangeable without a
release. Here they are rows, editable through the API and attributable to whoever
made them.
"""

import logging
from typing import Any

from standards_import.repositories.staging_db import StagingSession, run_query

log = logging.getLogger(__name__)

_seeded: set[str] = set()

RULE_RETURN = """
    rule.uid AS uid, rule.scope AS scope, rule.strategy AS strategy,
    rule.entity_type AS entity_type, rule.concept_id AS concept_id,
    rule.property AS property, rule.effective_date AS effective_date,
    rule.inconsistency_type AS inconsistency_type, rule.match_tier AS match_tier,
    rule.value AS value,
    rule.related_concept_id AS related_concept_id,
    rule.in_codelist_id AS in_codelist_id, rule.pattern AS pattern,
    rule.step_patterns AS step_patterns, rule.step_replacements AS step_replacements,
    rule.when_value AS when_value, rule.title_case AS title_case, rule.priority AS priority,
    rule.catalogue AS catalogue, rule.enabled AS enabled,
    rule.author_id AS author_id, rule.created_at AS created_at, rule.note AS note
"""

# The order the bootstrap script hardcodes. SDTM is the most authoritative source of a
# shared definition, glossary the least.
DEFAULT_CATALOGUE_PRIORITY = [
    "SDTM CT",
    "ADAM CT",
    "SEND CT",
    "PROTOCOL CT",
    "DEFINE-XML CT",
    "CDASH CT",
    "COA CT",
    "QS-FT CT",
    "QRS CT",
    "DDF CT",
    "TMF CT",
    "MRCT CT",
    "GLOSSARY CT",
]

# A release must hold every one of these before it can be analysed.
DEFAULT_MANDATORY_CATALOGUES = {"SDTM CT", "ADAM CT"}

# Whether the final step, promoting a reviewed release from staging into OSB, may run.
# Off until an administrator turns it on; review and analysis work either way.
DEFAULT_IMPORT_ENABLED = False

# Catalogues that usually ship a paired-view workbook alongside the package files.
# Informational only — never a gate.
DEFAULT_EXPECTED_WORKBOOK_CATALOGUES = {"SDTM CT", "ADAM CT"}

# The bootstrap script's special cases, restated as data. The two dated ones are
# historical — this service only imports releases newer than what is already in MDR —
# but seeding them keeps re-analysis of an old release reproducible, and records why
# those values look the way they do.
# Update here to add your home rules.
SEED_RULES: list[dict[str, Any]] = [
    {
        "uid": "seed_synonyms_union",
        "scope": "PROPERTY",
        "strategy": "UNION_VALUES",
        "property": "synonyms",
        "note": "Synonyms are never chosen between: every catalogue's synonyms are kept.",
    },
    {
        "uid": "seed_send-ct-2018-12-21_strip_quotes",
        "scope": "GLOBAL",
        "strategy": "STRIP_QUOTES",
        "effective_date": "2018-12-21",
        "inconsistency_type": "UNWANTED_QUOTES",
        "note": "SEND CT 2018-12-21 shipped quoted values throughout.",
    },
    {
        "uid": "seed_pairing_from_submission_values",
        "scope": "GLOBAL",
        "strategy": "ACCEPT_AS_IS",
        "inconsistency_type": "CODELIST_PAIRING",
        "note": "Where the submission values imply exactly one code codelist, pair with "
        "it. Where they imply several, ACCEPT_AS_IS refuses and a person decides.",
    },
    {
        "uid": "seed_sponsor_name_from_preferred_term",
        "scope": "GLOBAL",
        "strategy": "ACCEPT_AS_IS",
        "inconsistency_type": "SPONSOR_NAME",
        "note": "A term new to MDR is called what CDISC calls it, unless a narrower rule "
        "says otherwise. Disable this to review every new term by hand instead.",
    },
    {
        "uid": "seed_sponsor_name_C48262_screening",
        "scope": "CONCEPT",
        "strategy": "CUSTOM_VALUE",
        "entity_type": "TERM",
        "concept_id": "C48262",
        "inconsistency_type": "SPONSOR_NAME",
        "value": "Screening",
        "note": "Sponsor name for Trial Screening, from the bootstrap script's cascade.",
    },
    {
        "uid": "seed_sponsor_name_C99158_follow_up",
        "scope": "CONCEPT",
        "strategy": "CUSTOM_VALUE",
        "entity_type": "TERM",
        "concept_id": "C99158",
        "inconsistency_type": "SPONSOR_NAME",
        "value": "Follow-up",
        "note": "Sponsor name for Follow-Up, from the bootstrap script's cascade.",
    },
    {
        "uid": "seed_sponsor_name_C66737_trial_phase",
        "scope": "CONCEPT",
        "strategy": "TRIAL_PHASE_NAME",
        "entity_type": "TERM",
        "in_codelist_id": "C66737",
        "inconsistency_type": "SPONSOR_NAME",
        "note": "Trial Phase terms drop the trailing ' Trial' and use digits: "
        "'Phase I/II/III Trial' becomes 'Phase 1/Phase 2/Phase 3'. 'Phase 0' becomes "
        "'Early Phase 1'.",
    },
    {
        "uid": "seed_sponsor_name_C99077_drop_study",
        "scope": "CONCEPT",
        "strategy": "REGEX_REPLACE",
        "entity_type": "TERM",
        "in_codelist_id": "C99077",
        "inconsistency_type": "SPONSOR_NAME",
        "pattern": r"\s+Study$",
        "value": "",
        "note": "Study Type terms drop the trailing ' Study': "
        "'Interventional Study' becomes 'Interventional'.",
    },
    {
        "uid": "seed_sponsor_name_C99079_epoch",
        "scope": "CONCEPT",
        "strategy": "REGEX_REPLACE",
        "entity_type": "TERM",
        "in_codelist_id": "C99079",
        "inconsistency_type": "SPONSOR_NAME",
        "pattern": r"^Investigational | (Epoch|Period|Study Epoch)$",
        "value": "",
        "note": "Epoch terms drop a leading 'Investigational' and a trailing 'Epoch', "
        "'Period' or 'Study Epoch'. One alternation does both ends at once.",
    },
    {
        "uid": "seed_sponsor_name_C66736_trial_type",
        "scope": "CONCEPT",
        "strategy": "REGEX_REPLACE",
        "entity_type": "TERM",
        "in_codelist_id": "C66736",
        "inconsistency_type": "SPONSOR_NAME",
        "pattern": r" (Study|Trial)$",
        "value": "",
        "note": "Trial Type terms drop a trailing ' Study' or ' Trial'.",
    },
    {
        "uid": "seed_sponsor_name_C66785_control_type",
        "scope": "CONCEPT",
        "strategy": "REGEX_REPLACE",
        "entity_type": "TERM",
        "in_codelist_id": "C66785",
        "inconsistency_type": "SPONSOR_NAME",
        "pattern": r" Control$",
        "value": "",
        "note": "Control Type terms drop a trailing ' Control'.",
    },
    {
        "uid": "seed_sponsor_name_C66735_blinding_schema",
        "scope": "CONCEPT",
        "strategy": "REGEX_REPLACE",
        "entity_type": "TERM",
        "in_codelist_id": "C66735",
        "inconsistency_type": "SPONSOR_NAME",
        "pattern": r" Study$",
        "value": "",
        "note": "Trial Blinding Schema terms drop a trailing ' Study'.",
    },
    {
        "uid": "seed_sponsor_name_C99076_intervention_model",
        "scope": "CONCEPT",
        "strategy": "REGEX_REPLACE",
        "entity_type": "TERM",
        "in_codelist_id": "C99076",
        "inconsistency_type": "SPONSOR_NAME",
        "pattern": r" Study$",
        "value": "",
        "note": "Intervention Model terms drop a trailing ' Study'.",
    },
    {
        "uid": "seed_sponsor_name_C188725_objective_level",
        "scope": "CONCEPT",
        "strategy": "REGEX_REPLACE",
        "entity_type": "TERM",
        "in_codelist_id": "C188725",
        "inconsistency_type": "SPONSOR_NAME",
        "pattern": r"^Trial ",
        "value": "",
        "note": "Objective Level terms drop a leading 'Trial '.",
    },
    {
        "uid": "seed_2017-09-29_drop_C48262_from_C66736",
        "scope": "OCCURRENCE",
        "strategy": "DROP_TERM_FROM_CODELIST",
        "effective_date": "2017-09-29",
        "entity_type": "CODELIST",
        "concept_id": "C66736",
        # The membership disagreement names no term, so the rule says which to drop.
        "value": "C48262",
        # Without this the rule would also match the other kinds of finding raised
        # against C66736 at this date, and settle them by dropping the term they name.
        "inconsistency_type": "INCONSISTENT_TERM_SETS",
        "note": "Trial Screening (C48262) does not belong to Trial Type (C66736).",
    },
]

# The Unit codelist and every subset of it. Their terms are named by submission value
# rather than by preferred term, so each needs its own rule: `in_codelist_id` holds one
# codelist, which is also what tells USE_SUBMISSION_VALUE which value it means.
UNIT_CODELIST_IDS = [
    "C71620",
    "C78417",
    "C78422",
    "C78428",
    "C78427",
    "C78429",
    "C78421",
    "C78423",
    "C78430",
    "C66770",
    "C66781",
    "C85494",
    "C128685",
    "C128686",
    "C128684",
    "C128683",
]

SEED_RULES += [
    {
        "uid": f"seed_sponsor_name_{codelist_id}_unit_submission_value",
        "scope": "CONCEPT",
        "strategy": "USE_SUBMISSION_VALUE",
        "entity_type": "TERM",
        "in_codelist_id": codelist_id,
        "inconsistency_type": "SPONSOR_NAME",
        "note": "Unit terms are called by their submission value, not their CDISC "
        "preferred term.",
    }
    for codelist_id in UNIT_CODELIST_IDS
]

# The three codelist families whose naming needs more than one substitution, or a
# different treatment for part of the codelist. Each is the main codelist plus its
# subsets, and each subset needs its own rule because `in_codelist_id` holds one.
ROUTE_OF_ADMINISTRATION_IDS = ["C66729", "C78420", "C78425"]
DOSAGE_FORM_IDS = ["C66726", "C78418", "C78426"]
FREQUENCY_IDS = ["C71113", "C78419", "C78745"]

SEED_RULES += (
    [
        rule
        for codelist_id in ROUTE_OF_ADMINISTRATION_IDS
        for rule in (
            {
                # Tried first: these few terms are named after the submission value instead.
                "uid": f"seed_sponsor_name_{codelist_id}_route_via",
                "scope": "CONCEPT",
                "strategy": "USE_SUBMISSION_VALUE",
                "entity_type": "TERM",
                "in_codelist_id": codelist_id,
                "inconsistency_type": "SPONSOR_NAME",
                "when": "^Administration via",
                "title_case": True,
                "priority": 10,
                "note": "'Administration via Hemodialysis' is called by its submission "
                "value, title-cased: 'Hemodialysis'.",
            },
            {
                "uid": f"seed_sponsor_name_{codelist_id}_route_strip",
                "scope": "CONCEPT",
                "strategy": "REWRITE",
                "entity_type": "TERM",
                "in_codelist_id": codelist_id,
                "inconsistency_type": "SPONSOR_NAME",
                "priority": 20,
                "steps": [
                    {
                        "pattern": r"((\s|-)Route of Administration$|^Route of Administration )",
                        "replacement": "",
                    }
                ],
                "note": "Route of Administration terms drop that phrase from either end; "
                "at the end it may follow a space or a dash.",
            },
        )
    ]
    + [
        {
            "uid": f"seed_sponsor_name_{codelist_id}_dosage_form",
            "scope": "CONCEPT",
            "strategy": "REWRITE",
            "entity_type": "TERM",
            "in_codelist_id": codelist_id,
            "inconsistency_type": "SPONSOR_NAME",
            "steps": [
                {"pattern": r"^Dosage Form for", "replacement": "For"},
                {
                    "pattern": r"(\sDosage Form($|(?=\s))|^Dosage Form\s)",
                    "replacement": "",
                },
            ],
            "note": "Dosage Form is dropped from the start, middle or end — but a leading "
            "'Dosage Form for' becomes 'For', so the two substitutions differ.",
        }
        for codelist_id in DOSAGE_FORM_IDS
    ]
    + [
        {
            "uid": f"seed_sponsor_name_{codelist_id}_frequency",
            "scope": "CONCEPT",
            "strategy": "REWRITE",
            "entity_type": "TERM",
            "in_codelist_id": codelist_id,
            "inconsistency_type": "SPONSOR_NAME",
            "steps": [
                {"pattern": r"^\.+|\.+$", "replacement": ""},
                {"pattern": r" Per Day$", "replacement": " Daily"},
                {"pattern": r" Per Month$", "replacement": " Monthly"},
            ],
            "note": "Frequency terms lose a stray full stop and read 'Daily'/'Monthly' "
            "rather than 'Per Day'/'Per Month'.",
        }
        for codelist_id in FREQUENCY_IDS
    ]
    + [
        {
            "uid": "seed_sponsor_name_C64954_occasional",
            "scope": "CONCEPT",
            "strategy": "CUSTOM_VALUE",
            "entity_type": "TERM",
            "concept_id": "C64954",
            "inconsistency_type": "SPONSOR_NAME",
            "value": "Occasional",
            "note": "'Infrequent' is called by its synonym. Named on the term, so it beats "
            "the rule covering the rest of the Frequency codelist.",
        },
        {
            "uid": "seed_sponsor_name_C64596_every_day",
            "scope": "CONCEPT",
            "strategy": "CUSTOM_VALUE",
            "entity_type": "TERM",
            "concept_id": "C64596",
            "inconsistency_type": "SPONSOR_NAME",
            "value": "Every Day",
            "note": "C64596 was 'Every Evening' before 2019-06-28 and became 'QPM', which "
            "is really its submission value; the sponsor name stays 'Every Day'.",
        },
    ]
    # Nothing seeds SPONSOR_TERM_DUPLICATE (outside EXACT), SPONSOR_TERM_SEMANTIC_DUPLICATE,
    # SPONSOR_CODELIST_DUPLICATE or SPONSOR_NAME_DIVERGED. Those four are raised directly
    # at INFORMATIONAL status by the collectors in sponsor_impact_service.py — never OPEN,
    # never a candidate for auto_resolve() — so a rule here would never have anything to
    # match. Settling one is ACKNOWLEDGE, by a person, every time; see README "Sponsor
    # impact assessment" for why these never auto-resolve. An EXACT SPONSOR_TERM_DUPLICATE
    # stays OPEN and unseeded for the older reason: it breaks the main API's uniqueness
    # rule, and somebody has to say what to do about it, even if what they say is "keep
    # both".
)

SEED_AUTHOR = "system-seed"


def ensure_seed_data(session: StagingSession) -> None:
    """Writes the default pecking order and the inherited rules, once per database.

    Idempotent by uid, so an operator's later edits to a seeded rule are not undone
    on the next restart — `ON CREATE` guards everything the operator can change.
    """

    database = session._config.database or ""  # pylint: disable=protected-access

    if database in _seeded:
        return

    run_query(
        session,
        """
        UNWIND range(0, size($catalogues) - 1) AS index
        MERGE (cat:CataloguePriority:CDISCStaging {catalogue_name: $catalogues[index]})
        ON CREATE SET cat.priority = index,
                      cat.mandatory = $catalogues[index] IN $mandatory,
                      cat.expects_workbook = $catalogues[index] IN $expects_workbook
        """,
        parameters={
            "catalogues": DEFAULT_CATALOGUE_PRIORITY,
            "mandatory": sorted(DEFAULT_MANDATORY_CATALOGUES),
            "expects_workbook": sorted(DEFAULT_EXPECTED_WORKBOOK_CATALOGUES),
        },
    )
    run_query(
        session,
        """
        UNWIND $rules AS rule_data
        MERGE (rule:ResolutionRule:CDISCStaging {uid: rule_data.uid})
        ON CREATE SET rule += rule_data,
                      rule.enabled = true,
                      rule.author_id = $author_id,
                      rule.created_at = datetime()
        """,
        parameters={
            "rules": [normalise(rule) for rule in SEED_RULES],
            "author_id": SEED_AUTHOR,
        },
    )

    _seeded.add(database)
    log.info(
        "Resolution rules and catalogue priority seeded for database '%s'", database
    )


CATALOGUE_PRIORITY_RETURN = """
    cat.catalogue_name AS catalogue_name, cat.priority AS priority,
    coalesce(cat.mandatory, false) AS mandatory,
    coalesce(cat.expects_workbook, false) AS expects_workbook
"""


def get_catalogue_priority(session: StagingSession) -> list[dict[str, Any]]:
    return run_query(
        session,
        f"""
        MATCH (cat:CataloguePriority)
        RETURN {CATALOGUE_PRIORITY_RETURN}
        ORDER BY cat.priority
        """,
    )


def set_catalogue_priority(
    session: StagingSession, catalogues: list[str]
) -> list[dict[str, Any]]:
    """Replaces the pecking order entirely, so removals actually take effect.

    A catalogue's `mandatory`/`expects_workbook` flags do not survive being removed and
    re-added this way — those are set separately, through `set_mandatory_catalogues`/
    `set_expected_workbook_catalogues`, and are lost if a catalogue drops out of the
    pecking order and comes back.
    """

    run_query(session, "MATCH (cat:CataloguePriority) DETACH DELETE cat")
    return run_query(
        session,
        f"""
        UNWIND range(0, size($catalogues) - 1) AS index
        CREATE (cat:CataloguePriority:CDISCStaging {{catalogue_name: $catalogues[index], priority: index}})
        RETURN {CATALOGUE_PRIORITY_RETURN}
        ORDER BY cat.priority
        """,
        parameters={"catalogues": catalogues},
    )


def set_mandatory_catalogues(
    session: StagingSession, catalogue_names: list[str]
) -> list[dict[str, Any]]:
    """Marks exactly these catalogues mandatory; clears the flag on every other one."""

    return run_query(
        session,
        f"""
        MATCH (cat:CataloguePriority)
        SET cat.mandatory = cat.catalogue_name IN $names
        RETURN {CATALOGUE_PRIORITY_RETURN}
        ORDER BY cat.priority
        """,
        parameters={"names": catalogue_names},
    )


def set_expected_workbook_catalogues(
    session: StagingSession, catalogue_names: list[str]
) -> list[dict[str, Any]]:
    """Marks exactly these catalogues as expecting a workbook; clears every other one."""

    return run_query(
        session,
        f"""
        MATCH (cat:CataloguePriority)
        SET cat.expects_workbook = cat.catalogue_name IN $names
        RETURN {CATALOGUE_PRIORITY_RETURN}
        ORDER BY cat.priority
        """,
        parameters={"names": catalogue_names},
    )


def get_mandatory_catalogues(session: StagingSession) -> list[str]:
    records = run_query(
        session,
        """
        MATCH (cat:CataloguePriority)
        WHERE cat.mandatory
        RETURN cat.catalogue_name AS catalogue_name
        """,
    )
    return [record["catalogue_name"] for record in records]


def get_import_enabled(session: StagingSession) -> bool:
    records = run_query(
        session,
        "MATCH (settings:ImportSettings) RETURN settings.import_enabled AS import_enabled",
    )
    if records and records[0]["import_enabled"] is not None:
        return bool(records[0]["import_enabled"])
    return DEFAULT_IMPORT_ENABLED


def set_import_enabled(session: StagingSession, enabled: bool) -> bool:
    run_query(
        session,
        """
        MERGE (settings:ImportSettings:CDISCStaging {key: 'import'})
        SET settings.import_enabled = $enabled
        """,
        parameters={"enabled": enabled},
    )
    return enabled


def with_steps(record: dict[str, Any]) -> dict[str, Any]:
    """Rebuilds a rule's ordered steps from the two lists Neo4j can actually hold.

    A list of maps is not a valid node property, so the patterns and their replacements
    are stored side by side and zipped back together here.
    """

    rule = dict(record)
    rule["steps"] = [
        {"pattern": pattern, "replacement": replacement}
        for pattern, replacement in zip(
            record.get("step_patterns") or [], record.get("step_replacements") or []
        )
    ]
    rule["when"] = record.get("when_value")
    return rule


def get_rules(
    session: StagingSession, enabled_only: bool = False
) -> list[dict[str, Any]]:
    """Returns rules most specific first, which is the order they must be matched in."""

    filter_clause = "WHERE rule.enabled" if enabled_only else ""
    records = run_query(
        session,
        f"""
        MATCH (rule:ResolutionRule)
        {filter_clause}
        RETURN {RULE_RETURN}
        ORDER BY CASE rule.scope
                     WHEN 'OCCURRENCE' THEN 0
                     WHEN 'CONCEPT' THEN 1
                     WHEN 'PROPERTY' THEN 2
                     ELSE 3
                 END,
                 // A rule naming one term is narrower than one naming its whole
                 // codelist, so it is tried first.
                 CASE WHEN rule.concept_id IS NULL THEN 1 ELSE 0 END,
                 // Likewise for the findings where the term is not the concept: one
                 // naming the term beats one that only names the codelist it is in.
                 CASE WHEN rule.related_concept_id IS NULL THEN 1 ELSE 0 END,
                 COALESCE(rule.priority, 100),
                 CASE WHEN rule.effective_date IS NULL THEN 1 ELSE 0 END,
                 rule.uid
        """,
    )
    return [with_steps(record) for record in records]


def find_rule(session: StagingSession, uid: str) -> dict[str, Any] | None:
    records = run_query(
        session,
        f"""
        MATCH (rule:ResolutionRule {{uid: $uid}})
        RETURN {RULE_RETURN}
        """,
        parameters={"uid": uid},
    )
    return with_steps(records[0]) if records else None


def upsert_rule(session: StagingSession, rule: dict[str, Any]) -> dict[str, Any]:
    """Creates or updates a rule.

    Keyed on a uid composed from what the rule discriminates on, so saving the same
    rule twice updates it rather than quietly stacking a duplicate that would then
    compete with itself during matching.
    """

    records = run_query(
        session,
        f"""
        MERGE (rule:ResolutionRule:CDISCStaging {{uid: $rule.uid}})
        ON CREATE SET rule.created_at = datetime()
        SET rule.scope = $rule.scope,
            rule.strategy = $rule.strategy,
            rule.entity_type = $rule.entity_type,
            rule.concept_id = $rule.concept_id,
            rule.property = $rule.property,
            rule.effective_date = $rule.effective_date,
            rule.inconsistency_type = $rule.inconsistency_type,
            rule.match_tier = $rule.match_tier,
            rule.related_concept_id = $rule.related_concept_id,
            rule.in_codelist_id = $rule.in_codelist_id,
            rule.pattern = $rule.pattern,
            rule.step_patterns = $rule.step_patterns,
            rule.step_replacements = $rule.step_replacements,
            rule.when_value = $rule.when_value,
            rule.title_case = $rule.title_case,
            rule.priority = $rule.priority,
            rule.value = $rule.value,
            rule.catalogue = $rule.catalogue,
            rule.enabled = $rule.enabled,
            rule.author_id = $rule.author_id,
            rule.note = $rule.note
        RETURN {RULE_RETURN}
        """,
        parameters={"rule": normalise(rule)},
    )
    return with_steps(records[0])


def normalise(rule: dict[str, Any]) -> dict[str, Any]:
    """Flattens a rule into properties Neo4j will accept.

    `steps` is a list of maps, which is not a valid node property, so it becomes two
    aligned lists. `when` is renamed because it is a Cypher keyword.
    """

    steps = rule.get("steps") or []
    flattened = {
        key: value for key, value in rule.items() if key not in ("steps", "when")
    }
    flattened.update(
        step_patterns=[step["pattern"] for step in steps],
        step_replacements=[step.get("replacement", "") for step in steps],
        when_value=rule.get("when"),
        title_case=bool(rule.get("title_case")),
        priority=rule.get("priority") if rule.get("priority") is not None else 100,
    )
    return flattened


def delete_rule(session: StagingSession, uid: str) -> None:
    run_query(
        session,
        "MATCH (rule:ResolutionRule {uid: $uid}) DETACH DELETE rule",
        parameters={"uid": uid},
    )
