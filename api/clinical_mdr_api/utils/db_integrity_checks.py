"""
Database integrity checks utility library.

Provides functions to execute database integrity checks for specific studies,
supporting both strict mode (raises exceptions) and warning mode (returns warnings).
"""

import logging
from dataclasses import dataclass

from neomodel import db  # type: ignore

from clinical_mdr_api.domains.enums import ValidationMode
from common.exceptions import BusinessLogicException

log = logging.getLogger(__name__)


def build_root_summary_return_statement(root_alias, extra_return=None):
    if extra_return is None:
        extra_return_stmts = ""
        with_vars = root_alias
    else:
        # Parse extra_return items: if tuple (expression, alias), use expression in WITH and alias in RETURN
        # If not tuple, use directly in both
        parsed_return_items = []
        with_expressions = []

        for item in extra_return:
            if isinstance(item, tuple) and len(item) == 2:
                # Tuple: (expression, alias)
                expression, alias = item
                # Add to WITH clause: expression AS alias
                with_expressions.append(f"{expression} AS {alias}")
                # Add alias to RETURN clause
                parsed_return_items.append(alias)
            else:
                with_expressions.append(item)
                # Not a tuple, use directly in both WITH and RETURN
                parsed_return_items.append(item)

        # Build extra_return_stmts for RETURN clause
        extra_return_stmts = f"{', '.join(parsed_return_items)},"

        # Build WITH clause variables
        if with_expressions:
            with_vars = f"{root_alias}, {', '.join(with_expressions)}"
        else:
            with_vars = root_alias

    return f"""
        OPTIONAL MATCH ({root_alias})<-[:AFTER]-(saction:StudyAction)
            WHERE NOT "StudyRoot" in labels({root_alias})
        WITH {with_vars}, CASE
                WHEN
                    {root_alias} IS NOT NULL
                    AND "StudyRoot" in labels({root_alias})
                THEN {root_alias}.uid
                WHEN
                    saction is not null
                    and {root_alias} IS NOT NULL
                    AND "StudySelection" in labels({root_alias})
                THEN [{root_alias}.uid,saction.date]
                WHEN
                    saction is null
                    and {root_alias} IS NOT NULL
                    AND "StudySelection" in labels({root_alias})
                THEN {root_alias}.uid
                WHEN
                    "StudyAction" in labels({root_alias})
                THEN [{root_alias}.date,{root_alias}.author_id]
                WHEN
                    {root_alias}.uid IS NOT NULL
                THEN {root_alias}.uid
                WHEN
                    {root_alias}.name IS NOT NULL
                THEN {root_alias}.name
                WHEN
                    {root_alias}.submission_value IS NOT NULL
                THEN {root_alias}.submission_value
                WHEN
                    {root_alias}.user_id IS NOT NULL
                THEN {root_alias}.user_id
                WHEN
                    {root_alias}.concept_id IS NOT NULL
                THEN {root_alias}.concept_id
                WHEN
                    {root_alias}.external_id IS NOT NULL
                THEN {root_alias}.external_id
            ELSE elementId({root_alias})
            end as noncompliant_node_id
        RETURN
            COUNT({root_alias}) as noncompliant_entity_cnt,
            {extra_return_stmts}
            COLLECT(distinct(labels({root_alias}))) as noncompliant_labels,
            COLLECT(distinct noncompliant_node_id) as noncompliant_node_ids
        """


# list of all queries with their descriptions
QUERIES: list[tuple[str, str, str]] = [
    # test_db_study_versioning.py
    (
        "only_latest_study_version_lacks_end_date",
        "Only last version relationship should be without an end date for each root node",
        """
        MATCH (root:StudyRoot {uid: $study_uid})-[v:HAS_VERSION]->(value)
        WITH root, v
        ORDER BY 
            root,
            v.end_date DESC,
            v.start_date DESC 
        WITH root, collect(v) as versions
        WITH root, [v IN tail(versions) WHERE v.end_date IS NULL] as bad
        WITH root WHERE size(bad) > 0
        """ + build_root_summary_return_statement("root"),
    ),
    (
        "only_one_latest_for_study_root",
        "No more than one of each of LATEST|LATEST_DRAFT|LATEST_RETIRED|LATEST_FINAL relationship can exist for a study root node",
        """
        MATCH (root:StudyRoot {uid: $study_uid})-[v:LATEST|LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED]->()
        WITH root, collect(type(v)) as types
        WHERE size(apoc.coll.duplicates(types)) > 0
        """ + build_root_summary_return_statement("root"),
    ),
    (
        "test_no_duplicated_study_version_by_status_and_dates",
        "No duplicate HAS_VERSION relationship with same status by start or end date for each study root node",
        """
        MATCH (root:StudyRoot {uid: $study_uid})-[v:HAS_VERSION]->()
        WITH root, collect(v.status) as statuses, v
        WITH root, statuses, collect(v.start_date) as starts, collect(v.end_date) as ends
        WHERE (size(apoc.coll.duplicates(starts)) > 0 OR size(apoc.coll.duplicates(ends)) > 0)
        """ + build_root_summary_return_statement("root"),
    ),
    (
        "no_study_version_has_negative_duration",
        "No HAS_VERSION relationship ends before it starts",
        """
        MATCH (root:StudyRoot {uid: $study_uid})-[v:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_LOCKED|LATEST_RETIRED|LATEST_RELEASED]->()
        WHERE v.end_date IS NOT NULL AND v.end_date < v.start_date
        """ + build_root_summary_return_statement("root"),
    ),
    (
        "no_study_version_lacks_start_date",
        "No HAS_VERSION lacks a start date",
        """
        MATCH (root:StudyRoot {uid: $study_uid})-[v:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_LOCKED|LATEST_RETIRED|LATEST_RELEASED]->()
        WHERE v.start_date IS NULL
        """ + build_root_summary_return_statement("root"),
    ),
    (
        "no_study_version_lacks_end_date",
        "No HAS_VERSION lacks an end date unless it is the latest version",
        """
        MATCH (root:StudyRoot {uid: $study_uid})-[v:HAS_VERSION]->(sv)
        WHERE v.end_date IS NULL AND NOT (root)-[:LATEST]->(sv)
        """ + build_root_summary_return_statement("root"),
    ),
    (
        "study_versions_in_chronologic_order",
        "Study versions must have chronological start and end date for each root node without overlaps or gaps",
        """
        MATCH (root:StudyRoot {uid: $study_uid})-[v:HAS_VERSION]->(value)
        WITH root, value, v.start_date as start_date,
        CASE
            WHEN v.end_date IS NULL
            THEN datetime()
            ELSE v.end_date
        END AS end_date
        ORDER BY root, datetime.truncate('second', start_date), datetime.truncate('second', end_date)
        WITH root, collect(start_date) as sds, collect(end_date) as eds
        WHERE size(sds)>1
        WITH root, sds, eds, [n IN range(1,size(sds)-1) WHERE datetime.truncate('second', eds[n-1]) <> datetime.truncate('second', sds[n]) ] AS bad
        WITH root, bad, sds, eds WHERE size(bad)>0
        """
        + build_root_summary_return_statement(
            "root", extra_return=[("COLLECT(root.uid)", "root_uids")]
        ),
    ),
    (
        "latest_points_at_latest_study_version",
        "LATEST relationship should point at same value as the latest HAS_VERSION",
        """
        MATCH (root:StudyRoot {uid: $study_uid})-[:LATEST]->(latest)
        MATCH (root)-[v:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_LOCKED|LATEST_RETIRED|LATEST_RELEASED]->(value)
        WITH root, latest, value
        ORDER BY 
            root,
            v.end_date ASC,
            v.start_date ASC 
        WITH root, latest, collect(value) as values
        WITH root, latest, last(values) as latest_by_date
        WITH root WHERE latest <> latest_by_date
        """ + build_root_summary_return_statement("root"),
    ),
    (
        "no_latest_without_has_version",
        "All LATEST_DRAFT, LATEST_FINAL, LATEST_LOCKED, LATEST_RETIRED, LATEST_RELEASED relationships have a matching HAS_VERSION",
        """
        MATCH (root:StudyRoot {uid: $study_uid})-[lat:LATEST_DRAFT|LATEST_FINAL|LATEST_LOCKED|LATEST_RETIRED|LATEST_RELEASED]->(value)
        WHERE lat.version IS NOT NULL AND lat.status IS NOT NULL
            AND NOT (root)-[:HAS_VERSION {version: lat.version, status: lat.status}]->(value)
        """ + build_root_summary_return_statement("root"),
    ),
    (
        "no_released_without_locked",
        "All HAS_VERSION relationships with status LOCKED have a matching HAS_VERSION with status RELEASED",
        """
        MATCH (root:StudyRoot {uid: $study_uid})-[hvl:HAS_VERSION {status: "LOCKED"}]->(value)
        WHERE NOT (root)-[:HAS_VERSION {status: "RELEASED"}]->(value)
        """ + build_root_summary_return_statement("root"),
    ),
    (
        "unique_study_selection_on_each_study_value",
        "StudyValue nodes should be connected to a single version of each StudySelection node",
        """
        MATCH (sr:StudyRoot {uid: $study_uid})-[sr_sv]-(sv:StudyValue)-[sv_ss]-(ss:StudySelection) 
            WHERE NOT TYPE(sv_ss) <> "HAS_PROTOCOL_SOA_CELL" AND TYPE(sv_ss) <> "HAS_PROTOCOL_SOA_FOOTNOTE"
        WITH DISTINCT ss, sv
        WITH ss.uid as ss_uid, sv,  count(ss.uid) as ss_uid_count
        WHERE ss_uid_count>=2
        MATCH (sv)--(n)
        WHERE n.uid = ss_uid
        """ + build_root_summary_return_statement("n"),
    ),
    # test_study_selection_audit_trail.py
    (
        "study_selection_after_relation",
        "Each StudySelection node should have an incoming AFTER relationship",
        """
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(all_sa:StudyAction)-->(ss:StudySelection)
        WHERE NOT (:StudyAction)-[:AFTER]->(ss) AND NOT (:UpdateSoASnapshot)-[:AFTER]->(ss)
        """ + build_root_summary_return_statement("ss"),
    ),
    (
        "study_action_after_relation",
        "Each StudyAction node should have an outgoing AFTER relationship",
        """
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(sa:StudyAction)
            WHERE 
                NOT (sa)-[:AFTER]->()
                AND NOT sa:UpdateSoASnapshot //TODO: will change to StudyActionLog
                AND NOT (sa)-[:BEFORE]->(:StudyValue)
        """ + build_root_summary_return_statement("sa"),
    ),
    (
        "study_selection_labels",
        "Each audit-trailed node that has a uid should have a StudySelection label",
        """
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:AFTER]->(ss)
        WHERE NOT ss:StudySelection AND
            NOT ss.uid is NULL
        WITH ss
        """ + build_root_summary_return_statement("ss"),
    ),
    (
        "time_coherence_on_each_study_selection_required_relationship",
        "Each Study Selection must NOT be connected to another Study Selection with a required relationship outside of the intersection of their alive time",
        """
        MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)--(ss1:StudySelection)<-[:AFTER]-(ss1_after_saction:StudyAction)
        OPTIONAL MATCH (ss1)<-[:BEFORE]-(ss1_before_saction:StudyAction)
        WITH ss1, ss1_after_saction,
        CASE 
            WHEN 
                ss1_before_saction IS NULL
                AND NOT ss1_after_saction:Delete
            then 
                datetime({epochMillis: apoc.date.currentTimestamp()})
            WHEN 
                ss1_before_saction IS NULL
                AND ss1_after_saction:Delete
            then ss1_after_saction.date
            ELSE ss1_before_saction.date
        END AS ss1_before_date
        MATCH (ss1)-[ss1_ss2]-(ss2:StudySelection)
                <-[:AFTER]-(ss2_saction:StudyAction)
                -[:BEFORE]->(ss2_old_version:StudySelection)
            WHERE 
                NOT EXISTS((ss2_old_version)--(ss1))
                AND (
                    ss2_saction.date<ss1_before_date
                    AND ss2_saction.date>ss1_after_saction.date
                )
        WITH ss1, ss1_ss2, ss2, ss2_saction, ss2_old_version
        WHERE 
        TYPE(ss1_ss2) IN [
            "STUDY_VISIT_HAS_SCHEDULE",
            "STUDY_EPOCH_HAS_DESIGN_CELL",
            "STUDY_ACTIVITY_HAS_INSTRUCTION",
            "STUDY_ELEMENT_HAS_DESIGN_CELL",
            "STUDY_ARM_HAS_BRANCH_ARM"
        ]
        OPTIONAL MATCH (ss2_old_version)-[ss2_ss3]-(ss3:StudySelection)
            WHERE TYPE(ss2_ss3)=TYPE(ss1_ss2)
                AND ss3.uid<>ss1.uid
        WITH ss1, ss1_ss2, ss2, ss2_saction, ss2_old_version
            WHERE ss3 IS NULL
        """ + build_root_summary_return_statement("ss1"),
    ),
    (
        "study_actions_are_in_chronological_order",
        "Each StudyAction must follow directly after the previous in time",
        """
        MATCH (sr:StudyRoot {uid: $study_uid})-[at:AUDIT_TRAIL]->(cr:Create)-[after:AFTER]->(ss:StudySelection)
        CALL (ss) {
            MATCH (ss)((:StudySelection)<-[b:BEFORE]-(ac:StudyAction)-[a:AFTER]->(nss:StudySelection)){1,10000}(last_ver:StudySelection) WHERE NOT (last_ver)<-[:BEFORE]-(:StudyAction)
            UNWIND ac AS acs
            WITH collect(acs.date) as dates
            RETURN ALL(i IN RANGE(1, SIZE(dates)-1) WHERE dates[i-1] <= dates[i]) AS inOrder
        }
        WITH sr, ss WHERE NOT inOrder
        """ + build_root_summary_return_statement("ss"),
    ),
    # test_study_selection.py
    (
        "study_selection_after_relation_activity",
        "Each initial StudyActivity node must be linked to an ActivityValue node that was active and in state Final at the time of the StudyAction creating the StudyActivity",
        """
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(sa:Create)-[:AFTER]->(sact:StudyActivity)-[:HAS_SELECTED_ACTIVITY]-(av:ActivityValue)
        OPTIONAL MATCH (av)<-[ahv:HAS_VERSION]-(ar:ActivityRoot) 
        WHERE ahv.start_date < sa.date AND (ahv.end_date IS NULL OR ahv.end_date > sa.date) AND ahv.status = "Final"
        WITH sa, sact, av WHERE ar IS NULL
        """ + build_root_summary_return_statement("sact"),
    ),
    # testing study versions and study definition documents
    (
        "only_one_study_definition_document_per_study_version",
        "Each StudyDefinitionDocument node must reflect only one StudyVersion node",
        """
        MATCH (study_root:StudyRoot {uid: $study_uid})-[:HAS_VERSION]->(study_value:StudyValue)
        OPTIONAL MATCH (study_value)-[:HAS_STUDY_DEFINITION_DOCUMENT]->(study_definition_document:StudyDefinitionDocument)
        OPTIONAL MATCH (study_value)-[:HAS_STUDY_VERSION]->(study_version:StudyVersion)
        WITH study_version, collect(DISTINCT study_definition_document) as study_definition_documents
        WHERE size(study_definition_documents) > 1
        """ + build_root_summary_return_statement("study_version"),
    ),
    (
        "study_version_exists_if_has_protocol_soa_cell_and_study_definition_document_exists",
        "StudyVersion node must exists if there is a HAS_PROTOCOL_SOA_CELL relationship and a StudyDefinitionDocument node for a StudyValue node",
        """
        MATCH (study_root:StudyRoot {uid: $study_uid})-[:HAS_VERSION {status: 'RELEASED'}]->(study_value:StudyValue)-[:HAS_PROTOCOL_SOA_CELL]->(soa_cell:StudySelection)
        MATCH (study_value)-[:HAS_STUDY_DEFINITION_DOCUMENT]->(study_definition_document:StudyDefinitionDocument)
        WHERE NOT (study_value)-[:HAS_STUDY_VERSION]->(:StudyVersion)
        """ + build_root_summary_return_statement("study_definition_document"),
    ),
    (
        "study_version_exists_if_study_definition_document_exists",
        "StudyVersion node must exists if there is a StudyDefinitionDocument node for a StudyValue node",
        """
        MATCH (study_root:StudyRoot {uid: $study_uid})-[:HAS_VERSION]->(study_value:StudyValue)-[:HAS_STUDY_DEFINITION_DOCUMENT]->(study_definition_document:StudyDefinitionDocument)
        WHERE study_definition_document IS NOT NULL AND NOT (study_value)-[:HAS_STUDY_VERSION]->(:StudyVersion)
        """ + build_root_summary_return_statement("study_definition_document"),
    ),
    (
        "FINAL_or_RELEASED_study_version_exisits_if_study_version_node_exists",
        "If StudyVersion node exists for a StudyValue node, there must be a corresponding HAS_VERSION relationship with status FINAL or RELEASED",
        """
        MATCH (study_root:StudyRoot {uid: $study_uid})-[has_version:HAS_VERSION]->(study_value:StudyValue)-[:HAS_STUDY_VERSION]->(study_version:StudyVersion)
        WHERE has_version.status IN ["FINAL", "RELEASED"]
        WITH study_version, collect(has_version) as final_or_released_versions
        WHERE size(final_or_released_versions) = 0
        """ + build_root_summary_return_statement("study_version"),
    ),
]


@dataclass
class CheckResult:
    """Result of a database integrity check."""

    check_id: str
    description: str
    passed: bool
    noncompliant_count: int
    noncompliant_labels: list[list[str]]
    noncompliant_node_ids: list[int]
    root_uids: list[str] | None = None
    error: str | None = None


def execute_check_for_study(
    check_id: str,
    description: str,
    query: str,
    study_uid: str,
) -> CheckResult:
    """
    Execute a single integrity check for a specific study.

    Args:
        check_id: Identifier for the check
        description: Human-readable description of the check
        query: Cypher query to execute
        study_uid: UID of the study to check

    Returns:
        CheckResult with pass/fail status and details
    """
    try:
        # Execute the query (study_uid filter is already in the query)
        result = db.cypher_query(query=query, params={"study_uid": study_uid})

        # Parse results
        rows, columns = result

        if not rows:
            return CheckResult(
                check_id=check_id,
                description=description,
                passed=True,
                noncompliant_count=0,
                noncompliant_labels=[],
                noncompliant_node_ids=[],
            )

        # Get first row (should only be one due to aggregation)
        row = rows[0]
        result_dict = {}
        for idx, col in enumerate(columns):
            result_dict[col] = row[idx] if idx < len(row) else None

        noncompliant_count_raw = result_dict.get("noncompliant_entity_cnt", 0)
        noncompliant_count = (
            int(noncompliant_count_raw) if noncompliant_count_raw is not None else 0
        )
        noncompliant_labels = result_dict.get("noncompliant_labels", [])
        noncompliant_node_ids = result_dict.get("noncompliant_node_ids", [])
        root_uids = result_dict.get("root_uids")

        return CheckResult(
            check_id=check_id,
            description=description,
            passed=noncompliant_count == 0,
            noncompliant_count=noncompliant_count,
            noncompliant_labels=noncompliant_labels if noncompliant_labels else [],
            noncompliant_node_ids=(
                noncompliant_node_ids if noncompliant_node_ids else []
            ),
            root_uids=root_uids,
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        log.error("Error executing check %s: %s", check_id, e, exc_info=True)
        return CheckResult(
            check_id=check_id,
            description=description,
            passed=False,
            noncompliant_count=0,
            noncompliant_labels=[],
            noncompliant_node_ids=[],
            error=str(e),
        )


def execute_all_checks_for_study(
    study_uid: str,
    mode: ValidationMode = ValidationMode.STRICT,
) -> list[CheckResult]:
    """
    Execute all integrity checks for a specific study.

    Args:
        study_uid: UID of the study to check
        mode: ValidationMode.STRICT raises exceptions on failure,
              ValidationMode.WARNING returns warnings

    Returns:
        list of CheckResult objects

    Raises:
        BusinessLogicException: In strict mode, if any checks fail
    """
    results = []
    failed_checks = []

    for check_id, description, query in QUERIES:
        result = execute_check_for_study(check_id, description, query, study_uid)
        results.append(result)

        if not result.passed:
            failed_checks.append(result)
            log.warning(
                "Check failed: %s - %s. Noncompliant count: %s",
                check_id,
                description,
                result.noncompliant_count,
            )

    if failed_checks and mode == ValidationMode.STRICT:
        error_messages = []
        for check in failed_checks:
            msg = f"{check.check_id}: {check.description} (found {check.noncompliant_count} noncompliant entities)"
            if check.error:
                msg += f" - Error: {check.error}"
            error_messages.append(msg)

        raise BusinessLogicException(
            msg=f"Study integrity checks failed for study {study_uid}:\n"
            + "\n".join(error_messages)
        )

    return results
