# pylint: disable=invalid-name
# pylint: disable=redefined-builtin
from datetime import datetime, timezone
from typing import Any

from common import queries as common_queries
from common.config import settings
from common.exceptions import NotFoundException, ValidationException
from common.utils import validate_page_number_and_page_size
from consumer_api.shared.common import (
    SortByType,
    db_pagination_clause,
    db_sort_clause,
    query,
)
from consumer_api.v1 import models


def get_base_query_for_study_root_and_value(study_version_number: str | None) -> str:
    if study_version_number:
        return """
        MATCH (study_root:StudyRoot {uid: $study_uid})-[hv:HAS_VERSION {version: $study_version_number}]->(study_value:StudyValue)
        WITH study_root, study_value, hv ORDER BY hv.end_date DESC LIMIT 1
        """

    return """
    MATCH (study_root:StudyRoot {uid: $study_uid})-[latest:LATEST]->(study_value:StudyValue)
    MATCH (study_root)-[hv:HAS_VERSION]->(study_value)
    WITH study_root, study_value, hv ORDER BY hv.end_date DESC LIMIT 1
    """


def get_base_query_for_study_root_and_value_with_study_id(
    study_version_number: str | None, subpart: str | None
) -> str:
    base_query = "MATCH (study_root:StudyRoot)-[rel"
    if study_version_number:
        base_query += (
            ":HAS_VERSION {version: $study_version_number, status: 'RELEASED'}"
        )
    else:
        base_query += ":LATEST_RELEASED"
    if subpart:
        base_query += "]->(study_value:StudyValue {study_id_prefix: $project, study_number: $study_number, study_subpart_acronym: $subpart})"
    else:
        base_query += "]->(study_value:StudyValue {study_id_prefix: $project, study_number: $study_number})"
    base_query += "WITH study_root, study_value, rel ORDER BY rel.end_date DESC LIMIT 1"
    return base_query


def get_latest_version_from_datetime(
    project: str, study_number: str, date_time: str, subpart: str | None
) -> str:
    params = {
        "project": project,
        "study_number": study_number,
        "datetime": date_time,
        "subpart": subpart,
    }
    full_query = "MATCH (study_root:StudyRoot)-[hv:HAS_VERSION {status:'RELEASED'}]->"
    if subpart:
        full_query += "(study_value:StudyValue {study_id_prefix: $project, study_number: $study_number, study_subpart_acronym: $subpart})"
    else:
        full_query += "(study_value:StudyValue {study_id_prefix: $project, study_number: $study_number})"
    full_query += """
        where datetime(hv.end_date) <= datetime($datetime)
        with hv ORDER BY hv.end_date DESC LIMIT 1
        return hv.version AS version
        """

    res = query(full_query, params)

    NotFoundException.raise_if_not(
        res,
        msg=f"Study has no RELEASED version before {date_time}.",
    )

    return res[0]["version"]


def get_studies(
    sort_by: models.SortByStudies = models.SortByStudies.UID,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: int = 10,
    page_number: int = 1,
    id: str | None = None,
) -> list[dict[Any, Any]]:
    validate_page_number_and_page_size(page_number, page_size)

    params = {}
    filter_clause = ""

    if id is not None:
        params["id"] = id.strip()
        filter_clause = "WHERE toUpper(id) CONTAINS toUpper($id)"

    base_query = f"""
        MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)
        OPTIONAL MATCH (study_root)-[hv:HAS_VERSION|LATEST_DRAFT]->(:StudyValue)
        OPTIONAL MATCH (study_root)-[hv_ld:LATEST_DRAFT]->(:StudyValue)
        OPTIONAL MATCH (author:User) WHERE author.user_id = hv.author_id
        WITH *,
            COLLECT ({{
                user_id: author.user_id,
                username: author.username
            }}) AS authors
        ORDER BY hv.start_date DESC
        WITH
            study_root,
            study_value,
            study_root.uid as uid,
            study_value.study_acronym as acronym,
            study_value.study_id_prefix as id_prefix,
            study_value.study_number as number,
            CASE study_value.study_subpart_acronym
                WHEN IS NULL THEN COALESCE(study_value.study_id_prefix, '') + "-" + COALESCE(study_value.study_number, '')
                ELSE COALESCE(study_value.study_id_prefix, '') + "-" + COALESCE(study_value.study_number, '') + "-" + study_value.study_subpart_acronym
            END AS id,
            hv_ld as version_latest_draft,
            COLLECT(DISTINCT {{
                version_status: hv.status,
                version_number: hv.version,
                version_started_at: hv.start_date,
                version_ended_at: hv.end_date,
                version_author_id: hv.author_id,
                all_authors: authors,
                version_description: hv.change_description
            }}) as versions_all

        {filter_clause}

        WITH *,
            [v IN versions_all 
                WHERE v.version_status IN ['RELEASED', 'LOCKED']
                OR (v.version_started_at = version_latest_draft.start_date AND v.version_ended_at is null)] as versions

        OPTIONAL MATCH (study_value)-[hsds:HAS_STUDY_DATA_SUPPLIER]->(sds:StudyDataSupplier)
        OPTIONAL MATCH (sds)-[hds:HAS_DATA_SUPPLIER]->(dsv:DataSupplierValue)
        OPTIONAL MATCH (sds)-[:HAS_STUDY_DATA_SUPPLIER_TYPE]->(ctc:CTTermContext)
        OPTIONAL MATCH (ctc)-[:HAS_SELECTED_TERM]->(ctr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(ctnv:CTTermNameValue)
        OPTIONAL MATCH (ctr)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm)<-[:HAS_TERM]-(ccr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->
        (:CTCodelistAttributesRoot)-[:LATEST]->(:CTCodelistAttributesValue {{submission_value: "DATA_SUPPLIER_TYPE"}})

        RETURN uid,
            acronym,
            id_prefix,
            number,
            id,
            versions,
            [(study_root)-[:HAS_COMPLETENESS_TAG]->(t:DataCompletenessTag) | t.name] as data_completeness_tags,
            [ds IN COLLECT(DISTINCT {{
                uid: sds.uid,
                name: dsv.name,
                type_uid: ctr.uid,
                type_codelist_uid: ccr.uid,
                order: sds.order
            }}) WHERE ds.uid IS NOT NULL] AS study_data_suppliers
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause(sort_by.value, sort_order.value),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query, params)


def get_study_version(
    study_uid: str, study_version_number: str | None
) -> dict[str, Any]:
    params = {"study_uid": study_uid, "study_version_number": study_version_number}

    base_query = get_base_query_for_study_root_and_value(study_version_number)
    full_query = f"""
        {base_query}
        RETURN  hv.version AS version_number,
                hv.status AS version_status,
                hv.start_date AS version_started_at,
                hv.end_date AS version_ended_at,
                hv.change_description AS version_description,
                hv.author_id AS version_author_id
        """

    res = query(full_query, params)

    NotFoundException.raise_if_not(
        res,
        msg=(
            f"Study version {study_version_number} does not exist."
            if study_version_number
            else f"Study {study_uid} does not exist."
        ),
    )
    return res[0]


def get_study_visits(
    study_uid: str,
    sort_by: models.SortByStudyVisits = models.SortByStudyVisits.UID,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: int = 10,
    page_number: int = 1,
    study_version_number: str | None = None,
) -> list[dict[Any, Any]]:
    validate_page_number_and_page_size(page_number, page_size)

    params = {"study_uid": study_uid, "study_version_number": study_version_number}
    base_query = get_base_query_for_study_root_and_value(study_version_number)

    base_query += """
        MATCH (study_value)-[:HAS_STUDY_VISIT]-(study_visit:StudyVisit)
        OPTIONAL MATCH (study_visit)-[:HAS_VISIT_NAME]->(:VisitNameRoot)-[:LATEST]->(visit_name_value:VisitNameValue)
        OPTIONAL MATCH (study_visit)-[:HAS_VISIT_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(visit_type_ct_term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(visit_type_ct_term_name_value:CTTermNameValue)
        OPTIONAL MATCH (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
        OPTIONAL MATCH (study_epoch)-[:HAS_EPOCH]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(epoch_ct_term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(epoch_term:CTTermNameValue)
        OPTIONAL MATCH (study_visit)-[:HAS_TIMEPOINT]->(:TimePointRoot)-[:LATEST]->(:TimePointValue)-[:HAS_UNIT_DEFINITION]->(time_unit_unit_definition_root:UnitDefinitionRoot)-[:LATEST]->(time_unit_unit_definition_value:UnitDefinitionValue)
        OPTIONAL MATCH (study_visit)-[:HAS_TIMEPOINT]->(:TimePointRoot)-[:LATEST]->(:TimePointValue)-[:HAS_VALUE]->(time_value_root:NumericValueRoot)-[:LATEST]->(time_value_value:NumericValue)
        OPTIONAL MATCH (study_visit)-[:HAS_TIMEPOINT]->(:TimePointRoot)-[:LATEST]->(:TimePointValue)-[:HAS_TIME_REFERENCE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(time_ref_ct_root:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(time_ref_ct_term_name_value:CTTermNameValue)
        OPTIONAL MATCH (study_visit)-[:HAS_WINDOW_UNIT]->(window_unit_unit_definition_root:UnitDefinitionRoot)-[:LATEST]->(window_unit_unit_definition_value:UnitDefinitionValue)

        WITH
            study_root.uid AS study_uid,
            study_visit.uid AS uid,
            study_visit.unique_visit_number AS unique_visit_number,
            study_visit.visit_number AS visit_number,
            study_visit.short_visit_label AS visit_short_name,
            study_visit.visit_window_min AS visit_window_min,
            study_visit.visit_window_max AS visit_window_max,
            study_visit.is_global_anchor_visit AS is_global_anchor_visit,
            study_visit.visit_class AS visit_class,
            study_visit.visit_subclass AS visit_subclass,
            study_visit.visit_sublabel_reference AS anchor_visit_uid,
            visit_name_value.name AS visit_name,
            visit_type_ct_term_root.uid AS visit_type_uid,
            visit_type_ct_term_name_value.name AS visit_type_name,
            window_unit_unit_definition_root.uid AS visit_window_unit_uid,
            window_unit_unit_definition_value.name AS visit_window_unit_name,
            study_epoch.uid AS study_epoch_uid,
            epoch_term.name AS study_epoch_name,
            time_unit_unit_definition_root.uid AS time_unit_uid,
            time_unit_unit_definition_value.name AS time_unit_name,
            time_unit_unit_definition_value.conversion_factor_to_master AS time_unit_conversion_factor_to_master,
            time_value_root.uid AS time_value_uid,
            time_value_value.value AS time_value_value,
            time_ref_ct_term_name_value.name AS time_reference_name
        RETURN *
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause(
                sort_by.value,
                sort_order.value,
                sort_by_type=(
                    SortByType.NUMBER
                    if sort_by == models.SortByStudyVisits.UNIQUE_VISIT_NUMBER
                    else SortByType.STRING
                ),
            ),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query, params)


def get_study_activities(
    study_uid: str,
    sort_by: models.SortByStudyActivities = models.SortByStudyActivities.UID,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: int = 10,
    page_number: int = 1,
    study_version_number: str | None = None,
) -> list[dict[Any, Any]]:
    validate_page_number_and_page_size(page_number, page_size)

    params = {"study_uid": study_uid, "study_version_number": study_version_number}
    base_query = get_base_query_for_study_root_and_value(study_version_number)

    base_query += """
        WITH study_root, study_value, hv
        MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(sa:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)<-[:HAS_VERSION]-(ar:ActivityRoot)
        MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(soa_group_term:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(soa_group_term_value:CTTermNameValue)
        MATCH (ar)<-[:CONTAINS_CONCEPT]-(lib:Library)

        WITH DISTINCT *
        CALL {
            WITH ar, av
            MATCH (ar)-[hv:HAS_VERSION]-(av)
            WHERE hv.status in ['Final', 'Retired']
            WITH hv
            ORDER BY
                toInteger(split(hv.version, '.')[0]) ASC,
                toInteger(split(hv.version, '.')[1]) ASC,
                hv.end_date ASC,
                hv.start_date ASC
            WITH collect(hv) as hvs
            RETURN last(hvs) as hv_ver
        }

        WITH DISTINCT *
        ORDER BY sa.order ASC
        MATCH (sa)<-[:AFTER]-(:StudyAction)
        RETURN DISTINCT
            study_root.uid AS study_uid,
            sa.uid AS uid,
            head([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_selection)
            -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | 
                {
                    selection_uid: study_activity_subgroup_selection.uid, 
                    activity_subgroup_uid:activity_subgroup_root.uid,
                    activity_subgroup_name:activity_subgroup_value.name
                }]) AS study_activity_subgroup,
            head([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_selection)
                -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | 
                {
                    selection_uid: study_activity_group_selection.uid, 
                    activity_group_uid: activity_group_root.uid,
                    activity_group_name:activity_group_value.name
                }]) AS study_activity_group,
            {
                study_soa_group_uid: soa_group.uid,
                soa_group_term_uid: soa_group_term.uid,
                soa_group_name: soa_group_term_value.name
            } AS soa_group,
            ar.uid AS activity_uid,
            av.name AS activity_name,
            av.nci_concept_id AS nci_concept_id,
            av.nci_concept_name AS nci_concept_name,
            coalesce(av.is_data_collected, False) AS is_data_collected
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause(sort_by.value, sort_order.value),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query, params)


def get_study_activity_instances(
    study_uid: str,
    sort_by: models.SortByStudyActivityInstances = models.SortByStudyActivityInstances.UID,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: int = 10,
    page_number: int = 1,
    study_version_number: str | None = None,
) -> list[dict[Any, Any]]:
    validate_page_number_and_page_size(page_number, page_size)

    params = {"study_uid": study_uid, "study_version_number": study_version_number}
    base_query = get_base_query_for_study_root_and_value(study_version_number)

    base_query += """
        MATCH (study_value)-[:HAS_STUDY_ACTIVITY_INSTANCE]->(sa:StudyActivityInstance)
            <-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]-(study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value)

        WITH DISTINCT *
        MATCH (sa)<-[:AFTER]-(sac:StudyAction)

        RETURN DISTINCT
            study_root.uid AS study_uid,
            sa.uid AS uid,
            study_activity.uid AS study_activity_uid,
            head(apoc.coll.sortMulti([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue)<-[has_version:HAS_VERSION]
            -(activity_root:ActivityRoot) WHERE has_version.status IN ['Final', 'Retired'] | 
                {
                    uid: activity_root.uid,
                    name: activity_value.name,
                    nci_concept_id: activity_value.nci_concept_id,
                    nci_concept_name: activity_value.nci_concept_name,
                    version: has_version.version,
                    major_version: toInteger(split(has_version.version,'.')[0]),
                    minor_version: toInteger(split(has_version.version,'.')[1]),
                    order: study_activity.order
                }], ['major_version', 'minor_version'])) AS activity,
            head(apoc.coll.sortMulti([(sa)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(activity_instance_val:ActivityInstanceValue)<-[has_version:HAS_VERSION]
            -(activity_instance_root:ActivityInstanceRoot) WHERE has_version.status IN ['Final', 'Retired'] |  
                { 
                    uid: activity_instance_root.uid, 
                    name: activity_instance_val.name,
                    nci_concept_id: activity_instance_val.nci_concept_id,
                    nci_concept_name: activity_instance_val.nci_concept_name,
                    param_code: activity_instance_val.adam_param_code,
                    topic_code: activity_instance_val.topic_code,
                    version: has_version.version,
                    major_version: toInteger(split(has_version.version,'.')[0]),
                    minor_version: toInteger(split(has_version.version,'.')[1]),
                    order: sa.order
                }], ['major_version', 'minor_version'])) AS activity_instance,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_selection)
                -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
                WHERE (study_value)-[:HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_selection) | 
                {
                    selection_uid: study_activity_subgroup_selection.uid, 
                    uid:activity_subgroup_root.uid,
                    name: activity_subgroup_value.name,
                    order: study_activity_subgroup_selection.order
                }]) AS study_activity_subgroup,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_selection)
                -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
                 WHERE (study_value)-[:HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_selection) | 
                {
                    selection_uid: study_activity_group_selection.uid, 
                    uid: activity_group_root.uid,
                    name: activity_group_value.name,
                    order: study_activity_group_selection.order
                }]) AS study_activity_group,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group_selection)
                -[:HAS_FLOWCHART_GROUP]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(ct_term_root:CTTermRoot)-[:HAS_NAME_ROOT]-(:CTTermNameRoot)-[:LATEST]->(flowchart_value:CTTermNameValue)
                WHERE (study_value)-[:HAS_STUDY_SOA_GROUP]->(study_soa_group_selection) | 
                {
                    selection_uid: study_soa_group_selection.uid, 
                    uid: ct_term_root.uid,
                    name: flowchart_value.name,
                    order: study_soa_group_selection.order
                }]) AS study_soa_group
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause(sort_by.value, sort_order.value),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query, params)


def get_study_detailed_soa(
    study_uid: str,
    sort_by: models.SortByStudyDetailedSoA = models.SortByStudyDetailedSoA.ACTIVITY_NAME,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: int = 10,
    page_number: int = 1,
    study_version_number: str | None = None,
    include_unscheduled_activities: bool = False,
) -> list[dict[Any, Any]]:
    validate_page_number_and_page_size(page_number, page_size)

    params = {"study_uid": study_uid, "study_version_number": study_version_number}
    base_query = get_base_query_for_study_root_and_value(study_version_number)

    if include_unscheduled_activities:
        base_query += """
        MATCH (study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value)
        WHERE NOT (study_activity)-[:BEFORE]-()
        OPTIONAL MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value),
            (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value)
        OPTIONAL MATCH (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
        """
    else:
        base_query += """
        MATCH (study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value)
        MATCH (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value)
        OPTIONAL MATCH (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
        MATCH (study_activity_schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value)
        WHERE NOT (study_activity)<-[:BEFORE]-()
        """

    base_query += """
        WITH
            hv,
            study_root,
            study_value,
            study_activity_schedule,
            study_visit,
            study_epoch,
            study_activity,
            head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue)<-[:HAS_VERSION]-(activity_root:ActivityRoot) | {value: activity_value, uid: activity_root.uid}]) AS activity,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | {value: activity_subgroup_value, uid: activity_subgroup_root.uid}]) AS activity_subgroup,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(:StudyActivityGroup)-[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | {value: activity_group_value, uid: activity_group_root.uid}]) AS activity_group,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue) | term_name_value]) AS term_name_value,
            head([(study_epoch)-[:HAS_EPOCH]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]-(epoch_term:CTTermNameValue) | epoch_term.name]) AS epoch_name

        RETURN DISTINCT
            study_root.uid AS study_uid,
            study_visit.uid AS visit_uid,
            study_visit.short_visit_label AS visit_short_name,
            study_activity.uid AS study_activity_uid,
            epoch_name AS epoch_name,
            activity.uid AS activity_uid,
            activity.value.name AS activity_name,
            activity.value.nci_concept_id AS activity_nci_concept_id,
            activity.value.nci_concept_name AS activity_nci_concept_name,
            activity_subgroup.value.name AS activity_subgroup_name,
            activity_subgroup.uid AS activity_subgroup_uid,
            activity_group.value.name AS activity_group_name,
            activity_group.uid AS activity_group_uid,
            term_name_value.name AS soa_group_name,
            coalesce(activity.value.is_data_collected, False) AS is_data_collected
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause(
                sort_by.value,
                sort_order.value,
                secondary_sort_fields="visit_uid, soa_group_name, activity_group_uid, activity_subgroup_uid, activity_uid, study_activity_uid",
            ),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query, params)


def get_study_operational_soa(
    study_uid: str,
    sort_by: models.SortByStudyOperationalSoA = models.SortByStudyOperationalSoA.ACTIVITY_NAME,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: int = 10,
    page_number: int = 1,
    study_version_number: str | None = None,
    include_unscheduled_activities: bool = False,
) -> list[dict[Any, Any]]:
    validate_page_number_and_page_size(page_number, page_size)

    params = {"study_uid": study_uid, "study_version_number": study_version_number}
    base_query = get_base_query_for_study_root_and_value(study_version_number)

    if include_unscheduled_activities:
        base_query += """
        MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->(study_activity_instance:StudyActivityInstance)<-[:HAS_STUDY_ACTIVITY_INSTANCE]-(study_value)
        MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity)
        WHERE NOT (study_activity)<-[:BEFORE]-() AND (study_activity_instance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]-()
        OPTIONAL MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value),
            (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value)
        OPTIONAL MATCH (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
        """
    else:
        base_query += """
        MATCH (study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value)
        MATCH (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value)
        OPTIONAL MATCH (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
        MATCH (study_activity_schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->(study_activity_instance:StudyActivityInstance)<-[:HAS_STUDY_ACTIVITY_INSTANCE]-(study_value)
        WHERE NOT (study_activity)<-[:BEFORE]-() AND (study_activity_instance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]-()
        """

    base_query += """
        WITH
            hv,
            study_root,
            study_value,
            study_visit,
            head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue)<-[:HAS_VERSION]-(activity_root:ActivityRoot) | { uid: activity_root.uid, study_activity_uid: study_activity.uid, name: activity_value.name, nci_concept_id: activity_value.nci_concept_id, nci_concept_name: activity_value.nci_concept_name }]) as activity,
            head([(study_activity_instance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(activity_instance_value:ActivityInstanceValue)<-[:HAS_VERSION]-(activity_instance_root:ActivityInstanceRoot) | { uid: activity_instance_root.uid, name: activity_instance_value.name, topic_code: activity_instance_value.topic_code, adam_param_code: activity_instance_value.adam_param_code, nci_concept_id: activity_instance_value.nci_concept_id, nci_concept_name: activity_instance_value.nci_concept_name }]) as activity_instance,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)<-[:LATEST]-(activity_subgroup_root:ActivitySubGroupRoot) | { uid: activity_subgroup_root.uid, name: activity_subgroup_value.name }]) as activity_subgroup,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(:StudyActivityGroup)-[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)<-[:LATEST]-(activity_group_root:ActivityGroupRoot) | { uid: activity_group_root.uid, name: activity_group_value.name }]) as activity_group,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue) | term_name_value]) as term_name_value,
            head([(study_epoch)-[:HAS_EPOCH]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]-(epoch_term:CTTermNameValue) | epoch_term.name]) as epoch_name

        RETURN DISTINCT
            study_root.uid AS study_uid,
            CASE study_value.study_subpart_acronym
                WHEN IS NULL THEN toUpper(COALESCE(study_value.study_id_prefix, '') + "-" + COALESCE(study_value.study_number, ''))
                ELSE toUpper(COALESCE(study_value.study_id_prefix, '') + "-" + COALESCE(study_value.study_number, '')) + "-" + study_value.study_subpart_acronym
            END AS study_id,
            study_visit.uid AS visit_uid,
            study_visit.short_visit_label AS visit_short_name,
            epoch_name AS epoch_name,
            activity.name AS activity_name,
            activity.nci_concept_id AS activity_nci_concept_id,
            activity.nci_concept_name AS activity_nci_concept_name,
            activity.uid AS activity_uid,
            activity.study_activity_uid AS study_activity_uid,
            activity_instance.name AS activity_instance_name,
            activity_instance.nci_concept_id AS activity_instance_nci_concept_id,
            activity_instance.nci_concept_name AS activity_instance_nci_concept_name,
            activity_instance.uid AS activity_instance_uid,
            activity_instance.topic_code AS topic_code,
            activity_instance.adam_param_code AS param_code,
            activity_subgroup.name AS activity_subgroup_name,
            activity_subgroup.uid AS activity_subgroup_uid,
            activity_group.name AS activity_group_name,
            activity_group.uid AS activity_group_uid,
            term_name_value.name as soa_group_name
    """
    full_query = " ".join(
        [
            base_query,
            db_sort_clause(
                sort_by.value,
                sort_order.value,
                secondary_sort_fields="visit_uid, soa_group_name, activity_group_uid, activity_subgroup_uid, activity_uid, study_activity_uid, activity_instance_uid",
            ),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query, params)


def get_library_activities(
    sort_by: models.SortByLibraryItem = models.SortByLibraryItem.NAME,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: int = 10,
    page_number: int = 1,
    library: models.Library | None = None,
    status: models.LibraryItemStatus | None = None,
) -> list[dict[Any, Any]]:
    validate_page_number_and_page_size(page_number, page_size)

    params = {
        "status": status.value if status else None,
        "library": library.value if library else None,
    }
    status_filter = "WHERE last_version_rel.status = $status " if status else ""

    base_query = (
        """
            MATCH (lib:Library {name: $library})-[:CONTAINS_CONCEPT]->(act_root:ActivityRoot)
        """
        if library
        else """
            MATCH (lib:Library)-[:CONTAINS_CONCEPT]->(act_root:ActivityRoot)
        """
    )

    base_query += f"""
        -[ver:LATEST]->(act_val:ActivityValue)
        WITH lib, act_root, act_val
        CALL {{
                WITH act_root, act_val
                MATCH (act_root)-[hv:HAS_VERSION]-(act_val)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS last_version_rel
            }}
        WITH lib, act_root, act_val, last_version_rel

        {status_filter}

        WITH lib, act_root, act_val, last_version_rel,
            apoc.coll.toSet([(act_val)-[:HAS_GROUPING]->(activity_grouping:ActivityGrouping)
             | {{
                 activity_subgroup: head(apoc.coll.sortMulti([(activity_grouping)-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)
                 <-[has_version:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
                    | {{
                        uid:activity_subgroup_root.uid,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1]),
                        name:activity_subgroup_value.name
                    }}], ['major_version', 'minor_version'])),
                    activity_group: head(apoc.coll.sortMulti([(activity_grouping)-[:HAS_SELECTED_GROUP]->(activity_group_value:ActivityGroupValue)
                    <-[has_version:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
                    | {{
                        uid:activity_group_root.uid,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1]),
                        name:activity_group_value.name
                    }}], ['major_version', 'minor_version']))
                }}]) AS groupings

        RETURN DISTINCT
            lib.name AS library,
            act_root.uid AS uid,
            act_val.name AS name,
            groupings,
            act_val.definition AS definition,
            act_val.nci_concept_id AS nci_concept_id,
            act_val.nci_concept_name AS nci_concept_name,
            coalesce(act_val.is_data_collected, False) AS is_data_collected,
            last_version_rel.version AS version,
            last_version_rel.status AS status
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause(sort_by.value, sort_order.value),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query, params)


def get_library_activity_instances(
    sort_by: models.SortByLibraryItem = models.SortByLibraryItem.NAME,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: int = 10,
    page_number: int = 1,
    library: models.Library | None = None,
    status: models.LibraryItemStatus | None = None,
    activity_uid: str | None = None,
) -> list[dict[Any, Any]]:
    validate_page_number_and_page_size(page_number, page_size)

    params = {
        "status": status.value if status else None,
        "library": library.value if library else None,
        "activity_uid": activity_uid.strip() if activity_uid else None,
    }
    status_filter = "WHERE last_version_rel.status = $status " if status else ""
    activity_uid_filter = (
        "WHERE $activity_uid IN [activity_grouping IN activity_groupings | activity_grouping.activity.uid] "
        if activity_uid
        else ""
    )

    base_query = (
        """
            MATCH (library:Library {name: $library})-[:CONTAINS_CONCEPT]->(concept_root:ActivityInstanceRoot)-[:LATEST]->(concept_value:ActivityInstanceValue)
        """
        if library
        else """
            MATCH (library:Library)-[:CONTAINS_CONCEPT]->(concept_root:ActivityInstanceRoot)-[:LATEST]->(concept_value:ActivityInstanceValue)
        """
    )
    base_query += """
        MATCH (concept_root)-[:HAS_GROUPING_ROOT]->(grouping_root:ActivityInstanceGroupingRoot)-[:LATEST]->(grouping_value:ActivityInstanceGroupingValue)
    """

    base_query += f"""
        WITH 
            DISTINCT concept_root, concept_value, grouping_root, grouping_value, library
            CALL {{
                WITH concept_root, concept_value
                MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS last_version_rel
            }}
            CALL {{
                WITH grouping_root, grouping_value
                MATCH (grouping_root)-[hv:HAS_VERSION]-(grouping_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS last_grouping_version_rel
            }}
            WITH concept_root, concept_value, grouping_root, grouping_value, last_version_rel, last_grouping_version_rel, library

            {status_filter}

            WITH
                concept_root.uid AS uid,
                library.name AS library_name,
                last_version_rel,
                last_grouping_version_rel,
                concept_value.nci_concept_id AS nci_concept_id,
                concept_value.nci_concept_name AS nci_concept_name,
                concept_value.name AS name,
                concept_value.definition AS definition,
                last_version_rel.status AS status,
                last_version_rel.version AS version,
                last_grouping_version_rel.status AS groupings_status,
                last_grouping_version_rel.version AS groupings_version,
                concept_value.topic_code AS topic_code,
                concept_value.adam_param_code AS param_code,
                head([(concept_value)-[:ACTIVITY_INSTANCE_CLASS]->(aic_root:ActivityInstanceClassRoot) | aic_root.uid]) AS activity_instance_class_uid,
                head([(concept_value)-[:ACTIVITY_INSTANCE_CLASS]->(:ActivityInstanceClassRoot)-[:LATEST]->(aic_val:ActivityInstanceClassValue) | aic_val.name]) AS activity_instance_class_name,
                apoc.coll.toSet([(grouping_value)-[:HAS_ACTIVITY]->(activity_grouping:ActivityGrouping)
                | {{
                    activity: head(apoc.coll.sortMulti([(activity_grouping)<-[:HAS_GROUPING]-(activity_value:ActivityValue)<-[has_version:HAS_VERSION]-
                        (activity_root:ActivityRoot) |
                        {{
                            uid: activity_root.uid,
                            name: activity_value.name,
                            major_version: toInteger(split(has_version.version,'.')[0]),
                            minor_version: toInteger(split(has_version.version,'.')[1])
                        }}], ['major_version', 'minor_version'])),
                    activity_subgroup: head(apoc.coll.sortMulti([(activity_grouping)-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)<-[has_version:HAS_VERSION]-
                        (activity_subgroup_root:ActivitySubGroupRoot) |
                        {{
                            uid: activity_subgroup_root.uid,
                            name: activity_subgroup_value.name,
                            major_version: toInteger(split(has_version.version,'.')[0]),
                            minor_version: toInteger(split(has_version.version,'.')[1])
                        }}], ['major_version', 'minor_version'])),
                    activity_group: head(apoc.coll.sortMulti([(activity_grouping)-[:HAS_SELECTED_GROUP]->(activity_group_value:ActivityGroupValue)<-[has_version:HAS_VERSION]-
                        (activity_group_root:ActivityGroupRoot) |
                        {{
                            uid: activity_group_root.uid,
                            name: activity_group_value.name,
                            major_version: toInteger(split(has_version.version,'.')[0]),
                            minor_version: toInteger(split(has_version.version,'.')[1])
                        }}], ['major_version', 'minor_version']))
                }}]) AS activity_groupings,
                [(concept_value)-[:CONTAINS_ACTIVITY_ITEM]->(ai)
                    <-[:HAS_ACTIVITY_ITEM]-(aic_root)-[:LATEST]->(aic_val) | {{
                    activity_item_class_uid: aic_root.uid,
                    activity_item_class_name: aic_val.name,
                    data_type: head([(aic_val)-[:HAS_DATA_TYPE]->(:CTTermContext)
                        -[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->
                        (:CTTermNameRoot)-[:LATEST]->(dtv:CTTermNameValue) | dtv.name]),
                    ct_codelist: head([(ai)-[:HAS_CODELIST]->(clr:CTCodelistRoot)
                        -[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
                        -[:LATEST]->(clav:CTCodelistAttributesValue)
                        | {{uid: clr.uid, submission_value: clav.submission_value}}]),
                    ct_terms: [(ai)-[:HAS_CT_TERM]->(:CTTermContext)-[:HAS_SELECTED_TERM]->
                        (tr:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm)
                        <-[:HAS_TERM]-(clr:CTCodelistRoot)
                        | {{uid: tr.uid, codelist_uid: clr.uid}}],
                    unit_definitions: [(ai)-[:HAS_UNIT_DEFINITION]->(udr:UnitDefinitionRoot)
                        | {{uid: udr.uid}}],
                    text_value: ai.text_value,
                    is_adam_param_specific: ai.is_adam_param_specific,
                    is_activity_instance_id_specific: ai.is_activity_instance_id_specific
                }}] AS activity_items

                {activity_uid_filter}

                RETURN  uid,
                        library_name,
                        name,
                        definition,
                        nci_concept_id,
                        nci_concept_name,
                        topic_code,
                        param_code,
                        activity_instance_class_uid,
                        activity_instance_class_name,
                        activity_groupings,
                        activity_items,
                        status,
                        version,
                        groupings_status,
                        groupings_version
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause(sort_by.value, sort_order.value),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query, params)


def get_papillons_soa(
    project: str,
    study_number: str,
    subpart: str | None = None,
    date_time: str | None = None,
    study_version_number: str | None = None,
) -> dict[str, Any]:
    """
    Papillons SoA for a study. If ``date_time`` is set, ``study_version_number``
    is resolved from it. If both ``date_time`` and ``study_version_number`` are
    omitted, the latest released study value is used.
    """
    if date_time:
        study_version_number = get_latest_version_from_datetime(
            project=project,
            study_number=study_number,
            date_time=date_time,
            subpart=subpart,
        )
    api_version = "v1"
    params = {
        "project": project,
        "study_number": study_number,
        "subpart": subpart,
        "study_version_number": study_version_number,
        "api_version": api_version,
        "specified_dt": date_time,
    }
    full_query = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_version_number, subpart=subpart
    )
    full_query += """
        MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)
        MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->(study_activity_instance:StudyActivityInstance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(activity_instance_value:ActivityInstanceValue)
        MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(cttc:CTTermContext)-[:HAS_SELECTED_TERM]->(soa_group_term:CTTermRoot)-[:HAS_NAME_ROOT]->(cttnr:CTTermNameRoot)-[:LATEST_FINAL]->(soa_group_term_value:CTTermNameValue)
        MATCH (study_value)-[:HAS_STUDY_ACTIVITY_INSTANCE]->(study_activity_instance)
        OPTIONAL MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value)
        OPTIONAL MATCH (study_value)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)-[:STUDY_VISIT_HAS_SCHEDULE]->(study_activity_schedule)
        OPTIONAL MATCH (study_activity_instance)-[:HAS_BASELINE]->(baseline_visit:StudyVisit)
        WITH
            study_value, rel, study_activity_instance, activity_instance_value, study_visit, study_activity, study_activity_schedule, soa_group_term_value, baseline_visit
            order by toInteger(study_visit.unique_visit_number), toInteger(baseline_visit.unique_visit_number)

        WHERE NOT (study_visit)--(:Delete) AND NOT (baseline_visit)--(:Delete) AND NOT (study_activity_schedule)--(:Delete)
        AND NOT (study_activity)--(:Delete) AND NOT (study_activity_instance)--(:Delete)
        AND NOT (soa_group)-[:BEFORE]-(:StudyAction)
        WITH
            study_value, rel, study_activity_instance, activity_instance_value, soa_group_term_value,
            {topic_cd: activity_instance_value.topic_code,
            soa_grp: collect(DISTINCT soa_group_term_value.name),
            important: study_activity_instance.is_important,
            baseline_visits: collect(DISTINCT baseline_visit.unique_visit_number),
            visits: collect(DISTINCT study_visit.unique_visit_number)} AS activities

        RETURN 
        study_value.study_id_prefix             AS project,
        study_value.study_number                AS study_number,
        study_value.study_subpart_acronym       AS subpart,
        COALESCE(study_value.study_id_prefix,"") + '-' + COALESCE(study_value.study_number ,"") + COALESCE(study_value.study_subpart_acronym ,"") AS full_study_id,
        $api_version                            AS api_version,
        rel.version                             AS study_version,
        $specified_dt                           AS specified_dt,
        toString(datetime())                    AS fetch_dt,
        collect(activities)                     AS soa
        """
    res = query(full_query, params)

    NotFoundException.raise_if(
        len(res) == 0,
        msg="Study SoA not found, please ensure the study has at least one released version.",
    )
    ValidationException.raise_if(len(res) > 1, msg="Too many results.")
    return res[0]


def _get_study_arms_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> list[dict[str, Any]]:
    """
    Return study arms for the given study value.
    """
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
        "criteria_type_inclusion_concept_id": settings.ct_concept_id_criteria_type_inclusion,
        "criteria_type_exclusion_concept_id": settings.ct_concept_id_criteria_type_exclusion,
    }
    full_query = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query += common_queries.study_standard_version_ct_terms_datetime
    full_query += """
        MATCH (study_value)-[:HAS_STUDY_ARM]->(sar:StudyArm)
        OPTIONAL MATCH (sar)-[:HAS_ARM_TYPE]->(arm_type_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->
            (elr:CTTermRoot)
    """
    full_query += _build_ct_term_with_codelist_cypher(
        root="elr", value="arm_type", context="arm_type_ctx"
    )
    full_query += """
        WITH sar, arm_type
        ORDER BY sar.order
        RETURN
            sar.uid AS uid,
            sar.name AS name,
            sar.short_name AS short_name,
            sar.arm_code AS code,
            sar.number_of_subjects AS no_subject,
            sar.description AS desc,
            sar.order AS order,
            sar.randomization_group AS rand_grp,
            CASE WHEN arm_type.term_uid IS NULL OR arm_type.term_uid = '' THEN null ELSE arm_type END AS type
    """
    res = query(full_query, params)
    arms = []
    for row in res:
        arms.append(
            {
                "uid": row.get("uid") or "",
                "name": row.get("name") or "",
                "short_name": row.get("short_name") or "",
                "code": row.get("code") or "",
                "no_subject": row.get("no_subject"),
                "desc": row.get("desc") or "",
                "order": row.get("order") if row.get("order") is not None else 0,
                "rand_grp": row.get("rand_grp") or "",
                "type": row.get("type"),
            }
        )
    return arms


def _get_study_branch_arms_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> list[dict[str, Any]]:
    """
    Return study branch arms for the given study value.
    """
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
        "criteria_type_inclusion_concept_id": settings.ct_concept_id_criteria_type_inclusion,
        "criteria_type_exclusion_concept_id": settings.ct_concept_id_criteria_type_exclusion,
    }
    full_query = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query += """
        MATCH (study_value)-[:HAS_STUDY_BRANCH_ARM]->(sba:StudyBranchArm)
        OPTIONAL MATCH (sba)<-[:STUDY_ARM_HAS_BRANCH_ARM]-(ar:StudyArm)<-[:HAS_STUDY_ARM]-(study_value)
        WITH sba, ar
        RETURN
            sba.uid AS uid,
            sba.name AS name,
            sba.short_name AS short_name,
            sba.branch_arm_code AS code,
            sba.number_of_subjects AS no_subject,
            sba.description AS desc,
            sba.order AS order,
            ar.uid AS arm_uid,
            sba.randomization_group AS rand_grp,
            ar.order AS _arm_order
        ORDER BY _arm_order, order
    """
    res = query(full_query, params)
    branches = []
    for row in res:
        branches.append(
            {
                "uid": row.get("uid") or "",
                "name": row.get("name") or "",
                "short_name": row.get("short_name") or "",
                "code": row.get("code") or "",
                "no_subject": row.get("no_subject"),
                "desc": row.get("desc") or "",
                "order": row.get("order") if row.get("order") is not None else 0,
                "arm_uid": row.get("arm_uid") or "",
                "rand_grp": row.get("rand_grp") or "",
            }
        )
    return branches


def _get_study_cohorts_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> list[dict[str, Any]]:
    """
    Return study cohorts for the given study value.
    """
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
        "criteria_type_inclusion_concept_id": settings.ct_concept_id_criteria_type_inclusion,
        "criteria_type_exclusion_concept_id": settings.ct_concept_id_criteria_type_exclusion,
    }
    full_query = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query += """
        MATCH (study_value)-[:HAS_STUDY_COHORT]->(sc:StudyCohort)
        OPTIONAL MATCH (sc)<-[:STUDY_ARM_HAS_COHORT]-(ar:StudyArm)<-[:HAS_STUDY_ARM]-(study_value)
        WITH sc, collect(DISTINCT ar.uid) AS arm_uids_raw
        OPTIONAL MATCH (sc)<-[:STUDY_BRANCH_ARM_HAS_COHORT]-(sba:StudyBranchArm)
        WITH sc, arm_uids_raw, collect(DISTINCT sba.uid) AS branch_uids_raw
        WITH sc,
            [x IN arm_uids_raw WHERE x IS NOT NULL] AS arm_uid,
            [x IN branch_uids_raw WHERE x IS NOT NULL] AS branch_uid
        RETURN
            sc.uid AS uid,
            sc.name AS name,
            sc.short_name AS short_name,
            sc.cohort_code AS code,
            sc.number_of_subjects AS no_subject,
            sc.description AS desc,
            arm_uid AS arm_uid,
            branch_uid AS branch_uid
        ORDER BY sc.order
    """
    res = query(full_query, params)
    cohorts = []
    for row in res:
        arm_uid = row.get("arm_uid")
        branch_uid = row.get("branch_uid")
        cohorts.append(
            {
                "uid": row.get("uid") or "",
                "name": row.get("name") or "",
                "short_name": row.get("short_name") or "",
                "code": row.get("code") or "",
                "no_subject": row.get("no_subject"),
                "desc": row.get("desc") or "",
                "arm_uid": list(arm_uid) if arm_uid else [],
                "branch_uid": list(branch_uid) if branch_uid else [],
            }
        )
    return cohorts


def _get_study_epochs_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> list[dict[str, Any]]:
    """
    Return study epochs for the given study value.
    """
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
        "criteria_type_inclusion_concept_id": settings.ct_concept_id_criteria_type_inclusion,
        "criteria_type_exclusion_concept_id": settings.ct_concept_id_criteria_type_exclusion,
    }
    full_query = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query += common_queries.study_standard_version_ct_terms_datetime
    full_query += """
        MATCH (study_value)-[:HAS_STUDY_EPOCH]->(se:StudyEpoch)
        OPTIONAL MATCH (se)-[:HAS_EPOCH]->(epoch_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->
            (epoch_root:CTTermRoot)
        OPTIONAL MATCH (se)-[:HAS_EPOCH_TYPE]->(epoch_type_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->
            (type_root:CTTermRoot)
        OPTIONAL MATCH (se)-[:HAS_EPOCH_SUB_TYPE]->(epoch_subtype_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->
            (subtype_root:CTTermRoot)
    """
    full_query += common_queries.ct_term_name_at_datetime.format(
        root="epoch_root", value="epoch_name"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="type_root", value="epoch_type", context="epoch_type_ctx"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="subtype_root", value="epoch_subtype", context="epoch_subtype_ctx"
    )
    full_query += """
        WITH se, epoch_name, epoch_type, epoch_subtype,
            head([(se)-[:HAS_AE_LAG_TIME_UNIT]->(ae_unit_root:UnitDefinitionRoot)-[:LATEST]->
                (ae_unit_value:UnitDefinitionValue) |
                {uid: ae_unit_root.uid, name: ae_unit_value.name}]) AS ae_lag_time_unit,
            head([(se)-[:HAS_HYPO_LAG_TIME_UNIT]->(hypo_unit_root:UnitDefinitionRoot)-[:LATEST]->
                (hypo_unit_value:UnitDefinitionValue) |
                {uid: hypo_unit_root.uid, name: hypo_unit_value.name}]) AS hypo_lag_time_unit,
            head([(se)-[:HAS_CE_LAG_TIME_UNIT]->(ce_unit_root:UnitDefinitionRoot)-[:LATEST]->
                (ce_unit_value:UnitDefinitionValue) |
                {uid: ce_unit_root.uid, name: ce_unit_value.name}]) AS ce_lag_time_unit
        RETURN
            se.uid AS uid,
            se.order AS order,
            COALESCE(epoch_name.sponsor_preferred_name, se.name, '') AS name,
            CASE WHEN epoch_type.term_uid IS NULL OR epoch_type.term_uid = '' THEN null ELSE epoch_type END AS type,
            CASE WHEN epoch_subtype.term_uid IS NULL OR epoch_subtype.term_uid = '' THEN null ELSE epoch_subtype END AS subtype,
            COALESCE(se.start_rule, '') AS start_rule,
            COALESCE(se.end_rule, '') AS end_rule,
            COALESCE(se.description, '') AS description,
            se.ae_lag_time AS ae_lag_time,
            ae_lag_time_unit.uid AS ae_lag_time_unit_uid,
            ae_lag_time_unit.name AS ae_lag_time_unit_name,
            se.hypo_lag_time AS hypo_lag_time,
            hypo_lag_time_unit.uid AS hypo_lag_time_unit_uid,
            hypo_lag_time_unit.name AS hypo_lag_time_unit_name,
            se.ce_lag_time AS ce_lag_time,
            ce_lag_time_unit.uid AS ce_lag_time_unit_uid,
            ce_lag_time_unit.name AS ce_lag_time_unit_name
        ORDER BY se.order
    """
    res = query(full_query, params)
    epochs = []
    for row in res:
        order_val = row.get("order")
        epochs.append(
            {
                "uid": row.get("uid") or "",
                "order": order_val if order_val is not None else None,
                "name": row.get("name") or "",
                "type": row.get("type"),
                "subtype": row.get("subtype"),
                "start_rule": row.get("start_rule") or "",
                "end_rule": row.get("end_rule") or "",
                "description": row.get("description") or "",
                # `or ""` would turn a genuine 0 into a blank, so pass these through as-is
                "ae_lag_time": row.get("ae_lag_time"),
                "ae_lag_time_unit_uid": row.get("ae_lag_time_unit_uid"),
                "ae_lag_time_unit_name": row.get("ae_lag_time_unit_name"),
                "hypo_lag_time": row.get("hypo_lag_time"),
                "hypo_lag_time_unit_uid": row.get("hypo_lag_time_unit_uid"),
                "hypo_lag_time_unit_name": row.get("hypo_lag_time_unit_name"),
                "ce_lag_time": row.get("ce_lag_time"),
                "ce_lag_time_unit_uid": row.get("ce_lag_time_unit_uid"),
                "ce_lag_time_unit_name": row.get("ce_lag_time_unit_name"),
            }
        )
    return epochs


def _get_study_visits_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> list[dict[str, Any]]:
    """
    Return study visits for the given study value.
    """
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
    }
    full_query = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query += common_queries.study_standard_version_ct_terms_datetime
    full_query += """
        MATCH (study_value)-[:HAS_STUDY_VISIT]->(sv:StudyVisit)
        OPTIONAL MATCH (sv)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(se:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
        OPTIONAL MATCH (se)-[:HAS_EPOCH]->(visit_epoch_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->
            (epoch_root:CTTermRoot)
        OPTIONAL MATCH (sv)-[:HAS_VISIT_TYPE]->(visit_type_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->
            (vt_root:CTTermRoot)
        OPTIONAL MATCH (sv)-[:HAS_VISIT_CONTACT_MODE]->(contact_mode_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->
            (vcm_root:CTTermRoot)
        OPTIONAL MATCH (sv)-[:HAS_EPOCH_ALLOCATION]->(epoch_alloc_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->
            (ea_root:CTTermRoot)
        OPTIONAL MATCH (sv)-[:HAS_WINDOW_UNIT]->(wu_root:UnitDefinitionRoot)-[:LATEST]->
            (wu_val:UnitDefinitionValue)
        OPTIONAL MATCH (sv)-[:HAS_VISIT_NAME]->(vn_root:VisitNameRoot)-[:LATEST]->
            (vn_val:VisitNameValue)
        OPTIONAL MATCH (sv)-[:HAS_STUDY_DAY]->(sd_root:StudyDayRoot)-[:LATEST]->
            (sd_val:StudyDayValue)
    """
    full_query += common_queries.ct_term_name_at_datetime.format(
        root="epoch_root", value="epoch_name"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="vt_root", value="visit_type", context="visit_type_ctx"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="vcm_root", value="contact_mode", context="contact_mode_ctx"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ea_root", value="epoch_alloc", context="epoch_alloc_ctx"
    )
    full_query += """
        RETURN
            se.uid AS epoch_uid,
            COALESCE(epoch_name.sponsor_preferred_name, '') AS epoch_name,
            CASE WHEN visit_type.term_uid IS NULL OR visit_type.term_uid = '' THEN null ELSE visit_type END AS visit_type,
            CASE WHEN contact_mode.term_uid IS NULL OR contact_mode.term_uid = '' THEN null ELSE contact_mode END AS contact_model,
            COALESCE(sv.unique_visit_number, '') AS visit_no,
            COALESCE(vn_val.name, sv.visit_name_label, '') AS name,
            COALESCE(sv.short_visit_label, '') AS short_name,
            sd_val.value AS study_day,
            sv.visit_window_min AS window_min,
            sv.visit_window_max AS window_max,
            COALESCE(wu_val.name, '') AS window_unit,
            COALESCE(sv.description, '') AS desc,
            CASE WHEN epoch_alloc.term_uid IS NULL OR epoch_alloc.term_uid = '' THEN null ELSE epoch_alloc END AS epoch_alloc,
            COALESCE(sv.start_rule, '') AS start_rule,
            COALESCE(sv.end_rule, '') AS end_rule
        ORDER BY toInteger(sv.unique_visit_number)
    """
    res = query(full_query, params)
    visits = []
    for row in res:
        study_day = row.get("study_day")
        if study_day is not None and not isinstance(study_day, int):
            try:
                study_day = int(study_day)
            except TypeError, ValueError:
                study_day = None
        visits.append(
            {
                "epoch_uid": row.get("epoch_uid") or "",
                "epoch_name": row.get("epoch_name") or "",
                "visit_type": row.get("visit_type"),
                "contact_model": row.get("contact_model"),
                "visit_no": str(row.get("visit_no") or ""),
                "name": row.get("name") or "",
                "short_name": row.get("short_name") or "",
                "study_day": study_day,
                "window_min": row.get("window_min"),
                "window_max": row.get("window_max"),
                "window_unit": row.get("window_unit") or "",
                "desc": row.get("desc") or "",
                "epoch_alloc": row.get("epoch_alloc"),
                "start_rule": row.get("start_rule") or "",
                "end_rule": row.get("end_rule") or "",
            }
        )
    return visits


def _get_study_elements_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> list[dict[str, Any]]:
    """
    Return study elements for the given study value.
    """
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
    }
    full_query = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query += common_queries.study_standard_version_ct_terms_datetime
    full_query += """
        MATCH (study_value)-[:HAS_STUDY_ELEMENT]->(se:StudyElement)
        OPTIONAL MATCH (se)-[:HAS_ELEMENT_SUBTYPE]->(element_subtype_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->
            (subtype_root:CTTermRoot)
        OPTIONAL MATCH (type_tr:CTTermRoot {uid: se.element_code})
    """
    full_query += _build_ct_term_with_codelist_cypher(
        root="subtype_root", value="element_subtype", context="element_subtype_ctx"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="type_tr", value="element_type"
    )
    full_query += """
        WITH se, element_type, element_subtype
        ORDER BY se.order
        RETURN
            se.uid AS uid,
            COALESCE(se.order, 0) AS order,
            COALESCE(se.name, '') AS name,
            COALESCE(se.short_name, '') AS short_name,
            CASE WHEN element_type.term_uid IS NULL OR element_type.term_uid = '' THEN null ELSE element_type END AS type,
            CASE WHEN element_subtype.term_uid IS NULL OR element_subtype.term_uid = '' THEN null ELSE element_subtype END AS subtype,
            COALESCE(se.start_rule, '') AS start_rule,
            COALESCE(se.end_rule, '') AS end_rule,
            COALESCE(se.planned_duration, '') AS dur,
            COALESCE(se.description, '') AS desc
    """
    res = query(full_query, params)
    elements = []
    for row in res:
        order = row.get("order")
        if order is not None and not isinstance(order, int):
            try:
                order = int(order)
            except TypeError, ValueError:
                order = 0
        elements.append(
            {
                "uid": row.get("uid") or "",
                "order": order,
                "name": row.get("name") or "",
                "short_name": row.get("short_name") or "",
                "type": row.get("type"),
                "subtype": row.get("subtype"),
                "start_rule": row.get("start_rule") or "",
                "end_rule": row.get("end_rule") or "",
                "dur": row.get("dur") or "",
                "desc": row.get("desc") or "",
            }
        )
    return elements


def _get_study_design_cells_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> list[dict[str, Any]]:
    """
    Return study design cells (design matrix) for the given study value (same
    contract as StudyDesignMatrixListingModel, including transition_rule).
    """
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
    }
    full_query = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query += """
        MATCH (study_value)-[:HAS_STUDY_DESIGN_CELL]->(sdc:StudyDesignCell)
        MATCH (sdc)<-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(sep:StudyEpoch)
        MATCH (sdc)<-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sel:StudyElement)
        OPTIONAL MATCH (sdc)<-[:STUDY_ARM_HAS_DESIGN_CELL]-(sarm:StudyArm)
        OPTIONAL MATCH (sdc)<-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL]-(sbarm:StudyBranchArm)
        WITH sarm, sbarm, sep, sel, sdc
        ORDER BY sdc.order
        RETURN
            COALESCE(sarm.uid, '') AS arm_uid,
            COALESCE(sbarm.uid, '') AS branch_uid,
            sep.uid AS epoch_uid,
            COALESCE(sel.uid, '') AS element_uid,
            COALESCE(sdc.transition_rule, '') AS transition_rule
    """
    res = query(full_query, params)
    design_cells = []
    for row in res:
        design_cells.append(
            {
                "arm_uid": row.get("arm_uid") or "",
                "branch_uid": row.get("branch_uid") or "",
                "epoch_uid": row.get("epoch_uid") or "",
                "element_uid": row.get("element_uid") or "",
                "transition_rule": row.get("transition_rule") or "",
            }
        )
    return design_cells


def _get_study_endpoints_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> list[dict[str, Any]]:
    """
    Return study endpoints for the given study value: uid, type, subtype, text,
    objective_uid, timeframe, endpoint_unit.
    """
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
    }
    full_query = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query += common_queries.study_standard_version_ct_terms_datetime
    full_query += """
        MATCH (study_value)-[:HAS_STUDY_ENDPOINT]->(se:StudyEndpoint)
        OPTIONAL MATCH (se)-[:HAS_SELECTED_ENDPOINT]->(ev:EndpointValue)
        OPTIONAL MATCH (se)-[:HAS_SELECTED_ENDPOINT_TEMPLATE]->(etv:EndpointTemplateValue)
        OPTIONAL MATCH (se)-[:HAS_ENDPOINT_LEVEL]->(endpoint_level_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->
            (level_root:CTTermRoot)
        OPTIONAL MATCH (se)-[:HAS_ENDPOINT_SUB_LEVEL]->(endpoint_sub_level_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->
            (sub_root:CTTermRoot)
        OPTIONAL MATCH (se)-[:STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE]->(so:StudyObjective)
        OPTIONAL MATCH (se)-[:HAS_SELECTED_TIMEFRAME]->(tv:TimeframeValue)
        CALL {
            WITH se
            OPTIONAL MATCH (se)-[rel:HAS_UNIT]->(un:UnitDefinitionRoot)-[:LATEST_FINAL]->
                (unv:UnitDefinitionValue)
            WITH se, rel, unv.name AS unit_name ORDER BY rel.index
            WITH se, collect(unit_name) AS unit_names
            OPTIONAL MATCH (se)-[:HAS_CONJUNCTION]->(co:Conjunction)
            RETURN unit_names, co.string AS unit_separator
        }
    """
    full_query += _build_ct_term_with_codelist_cypher(
        root="level_root", value="endpoint_type", context="endpoint_level_ctx"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="sub_root", value="endpoint_subtype", context="endpoint_sub_level_ctx"
    )
    full_query += """
        WITH se,
            COALESCE(ev.name_plain, etv.name_plain, se.text, '') AS text,
            CASE WHEN endpoint_type.term_uid IS NULL OR endpoint_type.term_uid = '' THEN null ELSE endpoint_type END AS type,
            CASE WHEN endpoint_subtype.term_uid IS NULL OR endpoint_subtype.term_uid = '' THEN null ELSE endpoint_subtype END AS subtype,
            COALESCE(so.uid, '') AS objective_uid,
            COALESCE(tv.name_plain, '') AS timeframe,
            unit_names,
            unit_separator
        ORDER BY se.order
        RETURN
            se.uid AS uid,
            type,
            subtype,
            text,
            objective_uid,
            timeframe,
            unit_names,
            unit_separator
    """
    res = query(full_query, params)
    endpoints = []
    for row in res:
        unit_names = row.get("unit_names") or []
        unit_sep = row.get("unit_separator")
        if unit_sep is None:
            unit_sep = " "
        if unit_names and len(unit_names) == 1:
            endpoint_unit = unit_names[0] or ""
        elif unit_names:
            endpoint_unit = (unit_sep or " ").join(u or "" for u in unit_names)
        else:
            endpoint_unit = ""
        endpoints.append(
            {
                "uid": row.get("uid") or "",
                "type": row.get("type"),
                "subtype": row.get("subtype"),
                "text": row.get("text") or "",
                "objective_uid": row.get("objective_uid") or "",
                "timeframe": row.get("timeframe") or "",
                "endpoint_unit": endpoint_unit,
            }
        )
    return endpoints


def _get_study_objectives_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> list[dict[str, Any]]:
    """
    Return study objectives for the given study value: uid, type, text.
    """
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
    }
    full_query = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query += common_queries.study_standard_version_ct_terms_datetime
    full_query += """
        MATCH (study_value)-[:HAS_STUDY_OBJECTIVE]->(so:StudyObjective)
        OPTIONAL MATCH (so)-[:HAS_SELECTED_OBJECTIVE]->(ov:ObjectiveValue)
        OPTIONAL MATCH (so)-[:HAS_SELECTED_OBJECTIVE_TEMPLATE]->(otv:ObjectiveTemplateValue)
        OPTIONAL MATCH (so)-[:HAS_OBJECTIVE_LEVEL]->(objective_level_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->
            (level_root:CTTermRoot)
    """
    full_query += _build_ct_term_with_codelist_cypher(
        root="level_root", value="objective_type", context="objective_level_ctx"
    )
    full_query += """
        WITH so, objective_type,
            COALESCE(ov.name_plain, otv.name_plain, '') AS text,
            CASE WHEN objective_type.term_uid IS NULL OR objective_type.term_uid = '' THEN null ELSE objective_type END AS type
        ORDER BY so.order
        RETURN
            so.uid AS uid,
            type,
            text
    """
    res = query(full_query, params)
    objectives = []
    for row in res:
        objectives.append(
            {
                "uid": row.get("uid") or "",
                "type": row.get("type"),
                "text": row.get("text") or "",
            }
        )
    return objectives


def _get_study_criteria_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> list[dict[str, Any]]:
    """
    Return study criteria (inclusion and exclusion only) for the given study value: uid, type,
    text. Only criteria with HAS_SELECTED_CRITERIA (instance) are included,
    not template-only.
    """
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
        "criteria_type_inclusion_concept_id": settings.ct_concept_id_criteria_type_inclusion,
        "criteria_type_exclusion_concept_id": settings.ct_concept_id_criteria_type_exclusion,
    }
    full_query = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query += common_queries.study_standard_version_ct_terms_datetime
    full_query += """
        MATCH (study_value)-[:HAS_STUDY_CRITERIA]->(sc:StudyCriteria)
        MATCH (sc)-[:HAS_SELECTED_CRITERIA]->(cv:CriteriaValue)
        MATCH (cv)<-[:LATEST]-(cr:CriteriaRoot)<-[:HAS_CRITERIA]-
            (ctr:CriteriaTemplateRoot)-[:HAS_TYPE]->(criteria_type_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->
            (type_root:CTTermRoot)
    """
    full_query += _build_ct_term_with_codelist_cypher(
        root="type_root", value="criteria_type", context="criteria_type_ctx"
    )
    full_query += """
        WITH sc, cv, criteria_type
        WHERE criteria_type.term_uid = $criteria_type_inclusion_concept_id
            OR criteria_type.term_uid = $criteria_type_exclusion_concept_id
        WITH sc,
            criteria_type AS type,
            COALESCE(cv.name_plain, '') AS text
        ORDER BY sc.order
        WITH sc.uid AS uid,
            sc.order AS ord,
            head(collect(DISTINCT type)) AS type,
            head(collect(DISTINCT text)) AS text
        RETURN uid, type, text
        ORDER BY ord
    """
    res = query(full_query, params)
    criteria = []
    for row in res:
        criteria.append(
            {
                "uid": row.get("uid") or "",
                "type": row.get("type"),
                "text": row.get("text") or "",
            }
        )
    return criteria


# Registry identifier DB field_name -> listing key (RegistryIdentifiersListingModel).
_REGISTRY_ID_FIELD_TO_KEY = {
    "ct_gov_id": "ct_gov",
    "eudract_id": "eudract",
    "universal_trial_number_utn": "utn",
    "japanese_trial_registry_id_japic": "japic",
    "investigational_new_drug_application_number_ind": "ind",
    "eu_trial_number": "eutn",
    "civ_id_sin_number": "civ",
    "national_clinical_trial_number": "nctn",
    "japanese_trial_registry_number_jrct": "jrct",
    "national_medical_products_administration_nmpa_number": "nmpa",
    "eudamed_srn_number": "esn",
    "investigational_device_exemption_ide_number": "ide",
    "eu_pas_number": "eupn",
}


def _get_study_registry_identifiers_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> dict[str, str]:
    """
    Return registry identifiers for the given study value: ct_gov, eudract, utn,
    japic, ind, eutn, civ, nctn, jrct, nmpa, esn, ide, eupn. Values come from
    StudyTextField nodes linked via HAS_TEXT_FIELD; missing fields are "".
    """
    field_names = list(_REGISTRY_ID_FIELD_TO_KEY.keys())
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
        "field_names": field_names,
    }
    full_query = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_TEXT_FIELD]->(stf:StudyTextField)
        WHERE stf.field_name IN $field_names
        WITH study_value, collect({fn: stf.field_name, val: stf.value}) AS pairs
        UNWIND pairs AS p
        WITH p WHERE p.fn IS NOT NULL
        RETURN p.fn AS field_name, p.val AS value
    """
    res = query(full_query, params)
    # Build listing key -> value; default "" for all keys.
    reg_id = {key: "" for key in _REGISTRY_ID_FIELD_TO_KEY.values()}
    for row in res:
        fn = row.get("field_name")
        if fn and fn in _REGISTRY_ID_FIELD_TO_KEY:
            key = _REGISTRY_ID_FIELD_TO_KEY[fn]
            reg_id[key] = (row.get("value") or "").strip()
    return reg_id


def _build_ct_term_with_codelist_cypher(
    *, root: str, value: str, context: str | None = None
) -> str:
    """Format Cypher to resolve CT term with codelist metadata at ct_terms_datetime."""
    if context is not None:
        return common_queries.ct_term_with_codelist_at_datetime.format(
            root=root, value=value, context_var=context
        )
    return common_queries.ct_term_with_codelist_at_datetime_no_context.format(
        root=root, value=value
    )


def _ct_term_dict_from_query_result(ct_term: Any) -> dict[str, Any]:
    """Map enriched CT term query result to listing response dict."""
    if isinstance(ct_term, dict) and ct_term.get("term_uid"):
        return {
            "term_uid": ct_term.get("term_uid") or "",
            "sponsor_preferred_name": ct_term.get("sponsor_preferred_name"),
            "submission_value": ct_term.get("submission_value"),
            "concept_id": ct_term.get("concept_id"),
            "codelist_uid": ct_term.get("codelist_uid"),
            "codelist_name": ct_term.get("codelist_name"),
            "codelist_submission_value": ct_term.get("codelist_submission_value"),
            "queried_effective_date": ct_term.get("queried_effective_date"),
            "date_conflict": ct_term.get("date_conflict"),
        }
    return {
        "term_uid": "",
        "sponsor_preferred_name": None,
        "submission_value": None,
        "concept_id": None,
        "codelist_uid": None,
        "codelist_name": None,
        "codelist_submission_value": None,
        "queried_effective_date": None,
        "date_conflict": None,
    }


def _resolve_ct_term_name_root(
    study_value_var: str, field_name: str, result_var: str
) -> tuple[str, str]:
    """Build Cypher to resolve StudyTextField to CTTermRoot for ct_term_name query.

    Returns (cypher_fragment, field_alias). Pass field_alias straight into
    _resolve_ct_null_flavor_root's bound_field_var instead of retyping the
    "stf_{result_var}" convention by hand at the call site.
    """
    field_alias = f"stf_{result_var}"
    cypher = f"""
        OPTIONAL MATCH ({study_value_var})-[:HAS_TEXT_FIELD]->({field_alias}:StudyTextField {{field_name: '{field_name}'}})
        OPTIONAL MATCH
            ({field_alias})-[:HAS_TYPE]->
            (ctx_{result_var}:CTTermContext)-[:HAS_SELECTED_TERM]->
            (ct_root_{result_var}:CTTermRoot)
    """
    return cypher, field_alias


def _resolve_ct_null_flavor_root(
    study_value_var: str,
    rel: str,
    label: str,
    parent_field_name: str,
    result_var: str,
    *,
    bound_field_var: str | None = None,
) -> str:
    """Build Cypher to resolve null flavor CT term from parent StudyField.

    When ``bound_field_var`` is set (already OPTIONAL MATCHed), skip rematching
    the parent field and only follow HAS_REASON_FOR_NULL_VALUE from that node.
    """
    if bound_field_var:
        return f"""
        OPTIONAL MATCH
            ({bound_field_var})-[:HAS_REASON_FOR_NULL_VALUE]->
            (ctx_{result_var}:CTTermContext)-[:HAS_SELECTED_TERM]->
            (ct_root_{result_var}:CTTermRoot)
    """
    return f"""
        OPTIONAL MATCH ({study_value_var})-[:{rel}]->(sf_{result_var}:{label} {{field_name: '{parent_field_name}'}})
        OPTIONAL MATCH
            (sf_{result_var})-[:HAS_REASON_FOR_NULL_VALUE]->
            (ctx_{result_var}:CTTermContext)-[:HAS_SELECTED_TERM]->
            (ct_root_{result_var}:CTTermRoot)
    """


def _get_study_type_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> dict[str, Any] | None:
    """
    Return study type (high-level study design) for the given study value.
    Returns None if no study value; otherwise a dict with stype, stype_nf,
    trial_type, trial_type_nf, phase, phase_nf, extension, extension_nf,
    adaptive, adaptive_nf, stop_rule, stop_rule_nf, confirmed_res_min_dur,
    confirmed_res_min_dur_nf, post_auth, post_auth_nf.
    """
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
    }
    base = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    # Resolve CT text fields as conflict-aware objects; get boolean/time/text values
    full_query = base
    full_query += common_queries.study_standard_version_ct_terms_datetime
    stype_cypher, stype_alias = _resolve_ct_term_name_root(
        "study_value", "study_type_code", "stype"
    )
    full_query += stype_cypher
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TEXT_FIELD",
        "StudyTextField",
        "study_type_code",
        "stype_nf",
        bound_field_var=stype_alias,
    )
    phase_cypher, phase_alias = _resolve_ct_term_name_root(
        "study_value", "trial_phase_code", "phase"
    )
    full_query += phase_cypher
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TEXT_FIELD",
        "StudyTextField",
        "trial_phase_code",
        "phase_nf",
        bound_field_var=phase_alias,
    )
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_ARRAY_FIELD",
        "StudyArrayField",
        "trial_type_codes",
        "trial_type_nf",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_TEXT_FIELD]->(stf_stop:StudyTextField {field_name: 'study_stop_rules'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TEXT_FIELD",
        "StudyTextField",
        "study_stop_rules",
        "stop_rule_nf",
        bound_field_var="stf_stop",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_BOOLEAN_FIELD]->(sbf_ext:StudyBooleanField {field_name: 'is_extension_trial'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_BOOLEAN_FIELD",
        "StudyBooleanField",
        "is_extension_trial",
        "extension_nf",
        bound_field_var="sbf_ext",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_BOOLEAN_FIELD]->(sbf_adapt:StudyBooleanField {field_name: 'is_adaptive_design'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_BOOLEAN_FIELD",
        "StudyBooleanField",
        "is_adaptive_design",
        "adaptive_nf",
        bound_field_var="sbf_adapt",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_TIME_FIELD]->(stf_crd:StudyTimeField {field_name: 'confirmed_response_minimum_duration'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TIME_FIELD",
        "StudyTimeField",
        "confirmed_response_minimum_duration",
        "confirmed_res_min_dur_nf",
        bound_field_var="stf_crd",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_BOOLEAN_FIELD]->(sbf_pa:StudyBooleanField {field_name: 'post_auth_indicator'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_BOOLEAN_FIELD",
        "StudyBooleanField",
        "post_auth_indicator",
        "post_auth_nf",
        bound_field_var="sbf_pa",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_stype", value="ct_stype", context="ctx_stype"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_stype_nf", value="ct_stype_nf", context="ctx_stype_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_phase", value="ct_phase", context="ctx_phase"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_phase_nf", value="ct_phase_nf", context="ctx_phase_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_trial_type_nf",
        value="ct_trial_type_nf",
        context="ctx_trial_type_nf",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_stop_rule_nf", value="ct_stop_rule_nf", context="ctx_stop_rule_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_extension_nf", value="ct_extension_nf", context="ctx_extension_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_adaptive_nf", value="ct_adaptive_nf", context="ctx_adaptive_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_confirmed_res_min_dur_nf",
        value="ct_confirmed_res_min_dur_nf",
        context="ctx_confirmed_res_min_dur_nf",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_post_auth_nf", value="ct_post_auth_nf", context="ctx_post_auth_nf"
    )
    full_query += """
        WITH study_value,
            CASE WHEN ct_stype.term_uid IS NULL OR ct_stype.term_uid = '' THEN null ELSE ct_stype END AS stype,
            CASE WHEN ct_stype_nf.term_uid IS NULL OR ct_stype_nf.term_uid = '' THEN null ELSE ct_stype_nf END AS stype_nf,
            CASE WHEN ct_phase.term_uid IS NULL OR ct_phase.term_uid = '' THEN null ELSE ct_phase END AS phase,
            CASE WHEN ct_phase_nf.term_uid IS NULL OR ct_phase_nf.term_uid = '' THEN null ELSE ct_phase_nf END AS phase_nf,
            CASE WHEN ct_trial_type_nf.term_uid IS NULL OR ct_trial_type_nf.term_uid = '' THEN null ELSE ct_trial_type_nf END AS trial_type_nf,
            CASE WHEN ct_stop_rule_nf.term_uid IS NULL OR ct_stop_rule_nf.term_uid = '' THEN null ELSE ct_stop_rule_nf END AS stop_rule_nf,
            CASE WHEN ct_extension_nf.term_uid IS NULL OR ct_extension_nf.term_uid = '' THEN null ELSE ct_extension_nf END AS extension_nf,
            CASE WHEN ct_adaptive_nf.term_uid IS NULL OR ct_adaptive_nf.term_uid = '' THEN null ELSE ct_adaptive_nf END AS adaptive_nf,
            CASE WHEN ct_confirmed_res_min_dur_nf.term_uid IS NULL OR ct_confirmed_res_min_dur_nf.term_uid = '' THEN null ELSE ct_confirmed_res_min_dur_nf END AS confirmed_res_min_dur_nf,
            CASE WHEN ct_post_auth_nf.term_uid IS NULL OR ct_post_auth_nf.term_uid = '' THEN null ELSE ct_post_auth_nf END AS post_auth_nf,
            COALESCE(stf_stop.value, '') AS stop_rule,
            COALESCE(stf_crd.value, '') AS confirmed_res_min_dur,
            CASE WHEN sbf_ext.value = true THEN 'Y' WHEN sbf_ext.value = false THEN 'N' ELSE '' END AS extension,
            CASE WHEN sbf_adapt.value = true THEN 'Y' WHEN sbf_adapt.value = false THEN 'N' ELSE '' END AS adaptive,
            CASE WHEN sbf_pa.value = true THEN 'Y' WHEN sbf_pa.value = false THEN 'N' ELSE '' END AS post_auth
        RETURN stype, stype_nf, phase, phase_nf, trial_type_nf, extension, extension_nf,
            adaptive, adaptive_nf, stop_rule, stop_rule_nf, confirmed_res_min_dur,
            confirmed_res_min_dur_nf, post_auth, post_auth_nf
    """
    res = query(full_query, params)
    if not res:
        return None
    row = res[0]
    # Build trial_type list from array field + CT resolution
    trial_type = _get_trial_type_list_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=study_value_version,
    )
    return {
        "stype": row.get("stype"),
        "stype_nf": row.get("stype_nf"),
        "trial_type": trial_type,
        "trial_type_nf": row.get("trial_type_nf"),
        "phase": row.get("phase"),
        "phase_nf": row.get("phase_nf"),
        "extension": (row.get("extension") or "").strip(),
        "extension_nf": row.get("extension_nf"),
        "adaptive": (row.get("adaptive") or "").strip(),
        "adaptive_nf": row.get("adaptive_nf"),
        "stop_rule": (row.get("stop_rule") or "").strip(),
        "stop_rule_nf": row.get("stop_rule_nf"),
        "confirmed_res_min_dur": (row.get("confirmed_res_min_dur") or "").strip(),
        "confirmed_res_min_dur_nf": row.get("confirmed_res_min_dur_nf"),
        "post_auth": (row.get("post_auth") or "").strip(),
        "post_auth_nf": row.get("post_auth_nf"),
    }


def _get_trial_type_list_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> list[dict[str, Any]]:
    """Resolve trial_type_codes array to list of CTTermWithCodelistAndConflictFlag-like dicts."""
    return _get_multiselect_ct_list_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=study_value_version,
        field_name="trial_type_codes",
    )


def _get_study_intent_list_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> list[dict[str, Any]]:
    """Resolve trial_intent_types_codes array to list of CTTermWithCodelistAndConflictFlag-like dicts."""
    return _get_multiselect_ct_list_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=study_value_version,
        field_name="trial_intent_types_codes",
    )


def _get_multiselect_ct_list_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
    field_name: str,
) -> list[dict[str, Any]]:
    """Resolve a study array field (multiselect) to conflict-aware CT term dicts per row."""
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
        "field_name": field_name,
    }
    full_query = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query += common_queries.study_standard_version_ct_terms_datetime
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_ARRAY_FIELD]->(saf:StudyArrayField {field_name: $field_name})
        WITH study_value, ct_terms_datetime,
            CASE WHEN saf.value IS NOT NULL THEN saf.value ELSE [] END AS uids
        UNWIND uids AS term_uid
        OPTIONAL MATCH (root:CTTermRoot {uid: term_uid})
    """
    full_query += _build_ct_term_with_codelist_cypher(root="root", value="name_at_dt")
    full_query += """
        OPTIONAL MATCH (droot:DictionaryTermRoot {uid: term_uid})-[:LATEST]->(dval:DictionaryTermValue)
        RETURN term_uid AS uid,
            name_at_dt AS ct_term,
            dval.name AS dictionary_name,
            dval.dictionary_id AS dictionary_id
    """
    res = query(full_query, params)
    out: list[dict[str, Any]] = []
    for r in res:
        uid = r.get("uid")
        if uid is None:
            continue
        ct_term = r.get("ct_term")
        if isinstance(ct_term, dict) and ct_term.get("term_uid"):
            out.append(_ct_term_dict_from_query_result(ct_term))
            continue
        dict_name = r.get("dictionary_name")
        dict_id = r.get("dictionary_id")
        if dict_name is not None or dict_id is not None:
            out.append(
                {
                    "term_uid": uid or (dict_id or ""),
                    "sponsor_preferred_name": dict_name,
                    "submission_value": None,
                    "concept_id": None,
                    "codelist_uid": None,
                    "codelist_name": None,
                    "codelist_submission_value": None,
                    "queried_effective_date": None,
                    "date_conflict": None,
                }
            )
            continue
        out.append(
            {
                "term_uid": uid,
                "sponsor_preferred_name": None,
                "submission_value": None,
                "concept_id": None,
                "codelist_uid": None,
                "codelist_name": None,
                "codelist_submission_value": None,
                "queried_effective_date": None,
                "date_conflict": None,
            }
        )
    return out


def _get_study_attributes_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> dict[str, Any] | None:
    """
    Return study attributes (study intervention) for the given study value.
    Returns None if no study value.
    """
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
    }
    base = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query = base
    full_query += common_queries.study_standard_version_ct_terms_datetime
    intv_type_cypher, intv_type_alias = _resolve_ct_term_name_root(
        "study_value", "intervention_type_code", "intv_type"
    )
    full_query += intv_type_cypher
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TEXT_FIELD",
        "StudyTextField",
        "intervention_type_code",
        "intv_type_nf",
        bound_field_var=intv_type_alias,
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_BOOLEAN_FIELD]->(sbf_addon:StudyBooleanField {field_name: 'add_on_to_existing_treatments'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_BOOLEAN_FIELD",
        "StudyBooleanField",
        "add_on_to_existing_treatments",
        "add_on_nf",
        bound_field_var="sbf_addon",
    )
    control_type_cypher, control_type_alias = _resolve_ct_term_name_root(
        "study_value", "control_type_code", "control_type"
    )
    full_query += control_type_cypher
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TEXT_FIELD",
        "StudyTextField",
        "control_type_code",
        "control_type_nf",
        bound_field_var=control_type_alias,
    )
    intv_model_cypher, intv_model_alias = _resolve_ct_term_name_root(
        "study_value", "intervention_model_code", "intv_model"
    )
    full_query += intv_model_cypher
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TEXT_FIELD",
        "StudyTextField",
        "intervention_model_code",
        "intv_model_nf",
        bound_field_var=intv_model_alias,
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_BOOLEAN_FIELD]->(sbf_rand:StudyBooleanField {field_name: 'is_trial_randomised'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_BOOLEAN_FIELD",
        "StudyBooleanField",
        "is_trial_randomised",
        "randomised_nf",
        bound_field_var="sbf_rand",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_TEXT_FIELD]->(stf_strata:StudyTextField {field_name: 'stratification_factor'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TEXT_FIELD",
        "StudyTextField",
        "stratification_factor",
        "strata_nf",
        bound_field_var="stf_strata",
    )
    blinding_cypher, blinding_alias = _resolve_ct_term_name_root(
        "study_value", "trial_blinding_schema_code", "blinding"
    )
    full_query += blinding_cypher
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TEXT_FIELD",
        "StudyTextField",
        "trial_blinding_schema_code",
        "blinding_nf",
        bound_field_var=blinding_alias,
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_TIME_FIELD]->(stf_pl:StudyTimeField {field_name: 'planned_study_length'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TIME_FIELD",
        "StudyTimeField",
        "planned_study_length",
        "planned_length_nf",
        bound_field_var="stf_pl",
    )
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_ARRAY_FIELD",
        "StudyArrayField",
        "trial_intent_types_codes",
        "study_intent_nf",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_intv_type", value="ct_intv_type", context="ctx_intv_type"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_intv_type_nf", value="ct_intv_type_nf", context="ctx_intv_type_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_add_on_nf", value="ct_add_on_nf", context="ctx_add_on_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_control_type", value="ct_control_type", context="ctx_control_type"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_control_type_nf",
        value="ct_control_type_nf",
        context="ctx_control_type_nf",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_intv_model", value="ct_intv_model", context="ctx_intv_model"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_intv_model_nf",
        value="ct_intv_model_nf",
        context="ctx_intv_model_nf",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_randomised_nf",
        value="ct_randomised_nf",
        context="ctx_randomised_nf",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_strata_nf", value="ct_strata_nf", context="ctx_strata_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_blinding", value="ct_blinding", context="ctx_blinding"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_blinding_nf", value="ct_blinding_nf", context="ctx_blinding_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_planned_length_nf",
        value="ct_planned_length_nf",
        context="ctx_planned_length_nf",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_study_intent_nf",
        value="ct_study_intent_nf",
        context="ctx_study_intent_nf",
    )
    full_query += """
        WITH study_value,
            CASE WHEN ct_intv_type.term_uid IS NULL OR ct_intv_type.term_uid = '' THEN null ELSE ct_intv_type END AS intv_type,
            CASE WHEN ct_intv_type_nf.term_uid IS NULL OR ct_intv_type_nf.term_uid = '' THEN null ELSE ct_intv_type_nf END AS intv_type_nf,
            CASE WHEN ct_add_on_nf.term_uid IS NULL OR ct_add_on_nf.term_uid = '' THEN null ELSE ct_add_on_nf END AS add_on_nf,
            CASE WHEN ct_control_type.term_uid IS NULL OR ct_control_type.term_uid = '' THEN null ELSE ct_control_type END AS control_type,
            CASE WHEN ct_control_type_nf.term_uid IS NULL OR ct_control_type_nf.term_uid = '' THEN null ELSE ct_control_type_nf END AS control_type_nf,
            CASE WHEN ct_intv_model.term_uid IS NULL OR ct_intv_model.term_uid = '' THEN null ELSE ct_intv_model END AS intv_model,
            CASE WHEN ct_intv_model_nf.term_uid IS NULL OR ct_intv_model_nf.term_uid = '' THEN null ELSE ct_intv_model_nf END AS intv_model_nf,
            CASE WHEN ct_randomised_nf.term_uid IS NULL OR ct_randomised_nf.term_uid = '' THEN null ELSE ct_randomised_nf END AS randomised_nf,
            CASE WHEN ct_strata_nf.term_uid IS NULL OR ct_strata_nf.term_uid = '' THEN null ELSE ct_strata_nf END AS strata_nf,
            CASE WHEN ct_blinding.term_uid IS NULL OR ct_blinding.term_uid = '' THEN null ELSE ct_blinding END AS blinding,
            CASE WHEN ct_blinding_nf.term_uid IS NULL OR ct_blinding_nf.term_uid = '' THEN null ELSE ct_blinding_nf END AS blinding_nf,
            CASE WHEN ct_planned_length_nf.term_uid IS NULL OR ct_planned_length_nf.term_uid = '' THEN null ELSE ct_planned_length_nf END AS planned_length_nf,
            CASE WHEN ct_study_intent_nf.term_uid IS NULL OR ct_study_intent_nf.term_uid = '' THEN null ELSE ct_study_intent_nf END AS study_intent_nf,
            COALESCE(stf_strata.value, '') AS strata,
            COALESCE(stf_pl.value, '') AS planned_length,
            CASE WHEN sbf_addon.value = true THEN 'Y' WHEN sbf_addon.value = false THEN 'N' ELSE '' END AS add_on,
            CASE WHEN sbf_rand.value = true THEN 'Y' WHEN sbf_rand.value = false THEN 'N' ELSE '' END AS randomised
        RETURN intv_type, intv_type_nf, add_on, add_on_nf, control_type, control_type_nf,
            intv_model, intv_model_nf, randomised, randomised_nf, strata, strata_nf,
            blinding, blinding_nf, planned_length, planned_length_nf, study_intent_nf
    """
    res = query(full_query, params)
    if not res:
        return None
    row = res[0]
    study_intent = _get_study_intent_list_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=study_value_version,
    )
    return {
        "intv_type": row.get("intv_type"),
        "intv_type_nf": row.get("intv_type_nf"),
        "add_on": (row.get("add_on") or "").strip(),
        "add_on_nf": row.get("add_on_nf"),
        "control_type": row.get("control_type"),
        "control_type_nf": row.get("control_type_nf"),
        "intv_model": row.get("intv_model"),
        "intv_model_nf": row.get("intv_model_nf"),
        "randomised": (row.get("randomised") or "").strip(),
        "randomised_nf": row.get("randomised_nf"),
        "strata": (row.get("strata") or "").strip(),
        "strata_nf": row.get("strata_nf"),
        "blinding": row.get("blinding"),
        "blinding_nf": row.get("blinding_nf"),
        "planned_length": (row.get("planned_length") or "").strip(),
        "planned_length_nf": row.get("planned_length_nf"),
        "study_intent": study_intent,
        "study_intent_nf": row.get("study_intent_nf"),
    }


def _get_study_population_for_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None,
    study_value_version: str,
) -> dict[str, Any] | None:
    """
    Return study population for the given study value. Returns None if no study value.
    """
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
    }
    base = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query = base
    full_query += common_queries.study_standard_version_ct_terms_datetime
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_ARRAY_FIELD",
        "StudyArrayField",
        "therapeutic_area_codes",
        "therapy_area_nf",
    )
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_ARRAY_FIELD",
        "StudyArrayField",
        "disease_condition_or_indication_codes",
        "indication_nf",
    )
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_ARRAY_FIELD",
        "StudyArrayField",
        "diagnosis_group_codes",
        "diag_grp_nf",
    )
    sex_cypher, sex_alias = _resolve_ct_term_name_root(
        "study_value", "sex_of_participants_code", "sex"
    )
    full_query += sex_cypher
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TEXT_FIELD",
        "StudyTextField",
        "sex_of_participants_code",
        "sex_nf",
        bound_field_var=sex_alias,
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_BOOLEAN_FIELD]->(sbf_rare:StudyBooleanField {field_name: 'rare_disease_indicator'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_BOOLEAN_FIELD",
        "StudyBooleanField",
        "rare_disease_indicator",
        "rare_dis_nf",
        bound_field_var="sbf_rare",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_BOOLEAN_FIELD]->(sbf_healthy:StudyBooleanField {field_name: 'healthy_subject_indicator'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_BOOLEAN_FIELD",
        "StudyBooleanField",
        "healthy_subject_indicator",
        "healthy_subj_nf",
        bound_field_var="sbf_healthy",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_TIME_FIELD]->(stf_min:StudyTimeField {field_name: 'planned_minimum_age_of_subjects'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TIME_FIELD",
        "StudyTimeField",
        "planned_minimum_age_of_subjects",
        "min_age_nf",
        bound_field_var="stf_min",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_TIME_FIELD]->(stf_max:StudyTimeField {field_name: 'planned_maximum_age_of_subjects'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TIME_FIELD",
        "StudyTimeField",
        "planned_maximum_age_of_subjects",
        "max_age_nf",
        bound_field_var="stf_max",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_TIME_FIELD]->(stf_stable:StudyTimeField {field_name: 'stable_disease_minimum_duration'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TIME_FIELD",
        "StudyTimeField",
        "stable_disease_minimum_duration",
        "stable_dis_min_dur_nf",
        bound_field_var="stf_stable",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_BOOLEAN_FIELD]->(sbf_ped:StudyBooleanField {field_name: 'pediatric_study_indicator'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_BOOLEAN_FIELD",
        "StudyBooleanField",
        "pediatric_study_indicator",
        "pediatric_nf",
        bound_field_var="sbf_ped",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_BOOLEAN_FIELD]->(sbf_ped_post:StudyBooleanField {field_name: 'pediatric_postmarket_study_indicator'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_BOOLEAN_FIELD",
        "StudyBooleanField",
        "pediatric_postmarket_study_indicator",
        "pediatric_postmarket_nf",
        bound_field_var="sbf_ped_post",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_BOOLEAN_FIELD]->(sbf_ped_inv:StudyBooleanField {field_name: 'pediatric_investigation_plan_indicator'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_BOOLEAN_FIELD",
        "StudyBooleanField",
        "pediatric_investigation_plan_indicator",
        "pediatric_inv_nf",
        bound_field_var="sbf_ped_inv",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_TEXT_FIELD]->(stf_relapse:StudyTextField {field_name: 'relapse_criteria'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_TEXT_FIELD",
        "StudyTextField",
        "relapse_criteria",
        "relapse_criteria_nf",
        bound_field_var="stf_relapse",
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_INT_FIELD]->(sif_plan:StudyIntField {field_name: 'number_of_expected_subjects'})
    """
    full_query += _resolve_ct_null_flavor_root(
        "study_value",
        "HAS_INT_FIELD",
        "StudyIntField",
        "number_of_expected_subjects",
        "plan_no_subject_nf",
        bound_field_var="sif_plan",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_therapy_area_nf",
        value="ct_therapy_area_nf",
        context="ctx_therapy_area_nf",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_indication_nf",
        value="ct_indication_nf",
        context="ctx_indication_nf",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_diag_grp_nf", value="ct_diag_grp_nf", context="ctx_diag_grp_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_sex", value="ct_sex", context="ctx_sex"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_sex_nf", value="ct_sex_nf", context="ctx_sex_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_rare_dis_nf", value="ct_rare_dis_nf", context="ctx_rare_dis_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_healthy_subj_nf",
        value="ct_healthy_subj_nf",
        context="ctx_healthy_subj_nf",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_min_age_nf", value="ct_min_age_nf", context="ctx_min_age_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_max_age_nf", value="ct_max_age_nf", context="ctx_max_age_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_stable_dis_min_dur_nf",
        value="ct_stable_dis_min_dur_nf",
        context="ctx_stable_dis_min_dur_nf",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_pediatric_nf", value="ct_pediatric_nf", context="ctx_pediatric_nf"
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_pediatric_postmarket_nf",
        value="ct_pediatric_postmarket_nf",
        context="ctx_pediatric_postmarket_nf",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_pediatric_inv_nf",
        value="ct_pediatric_inv_nf",
        context="ctx_pediatric_inv_nf",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_relapse_criteria_nf",
        value="ct_relapse_criteria_nf",
        context="ctx_relapse_criteria_nf",
    )
    full_query += _build_ct_term_with_codelist_cypher(
        root="ct_root_plan_no_subject_nf",
        value="ct_plan_no_subject_nf",
        context="ctx_plan_no_subject_nf",
    )
    full_query += """
        WITH study_value,
            CASE WHEN ct_therapy_area_nf.term_uid IS NULL OR ct_therapy_area_nf.term_uid = '' THEN null ELSE ct_therapy_area_nf END AS therapy_area_nf,
            CASE WHEN ct_indication_nf.term_uid IS NULL OR ct_indication_nf.term_uid = '' THEN null ELSE ct_indication_nf END AS indication_nf,
            CASE WHEN ct_diag_grp_nf.term_uid IS NULL OR ct_diag_grp_nf.term_uid = '' THEN null ELSE ct_diag_grp_nf END AS diag_grp_nf,
            CASE WHEN ct_sex.term_uid IS NULL OR ct_sex.term_uid = '' THEN null ELSE ct_sex END AS sex,
            CASE WHEN ct_sex_nf.term_uid IS NULL OR ct_sex_nf.term_uid = '' THEN null ELSE ct_sex_nf END AS sex_nf,
            CASE WHEN ct_rare_dis_nf.term_uid IS NULL OR ct_rare_dis_nf.term_uid = '' THEN null ELSE ct_rare_dis_nf END AS rare_dis_nf,
            CASE WHEN ct_healthy_subj_nf.term_uid IS NULL OR ct_healthy_subj_nf.term_uid = '' THEN null ELSE ct_healthy_subj_nf END AS healthy_subj_nf,
            CASE WHEN ct_min_age_nf.term_uid IS NULL OR ct_min_age_nf.term_uid = '' THEN null ELSE ct_min_age_nf END AS min_age_nf,
            CASE WHEN ct_max_age_nf.term_uid IS NULL OR ct_max_age_nf.term_uid = '' THEN null ELSE ct_max_age_nf END AS max_age_nf,
            CASE WHEN ct_stable_dis_min_dur_nf.term_uid IS NULL OR ct_stable_dis_min_dur_nf.term_uid = '' THEN null ELSE ct_stable_dis_min_dur_nf END AS stable_dis_min_dur_nf,
            CASE WHEN ct_pediatric_nf.term_uid IS NULL OR ct_pediatric_nf.term_uid = '' THEN null ELSE ct_pediatric_nf END AS pediatric_nf,
            CASE WHEN ct_pediatric_postmarket_nf.term_uid IS NULL OR ct_pediatric_postmarket_nf.term_uid = '' THEN null ELSE ct_pediatric_postmarket_nf END AS pediatric_postmarket_nf,
            CASE WHEN ct_pediatric_inv_nf.term_uid IS NULL OR ct_pediatric_inv_nf.term_uid = '' THEN null ELSE ct_pediatric_inv_nf END AS pediatric_inv_nf,
            CASE WHEN ct_relapse_criteria_nf.term_uid IS NULL OR ct_relapse_criteria_nf.term_uid = '' THEN null ELSE ct_relapse_criteria_nf END AS relapse_criteria_nf,
            CASE WHEN ct_plan_no_subject_nf.term_uid IS NULL OR ct_plan_no_subject_nf.term_uid = '' THEN null ELSE ct_plan_no_subject_nf END AS plan_no_subject_nf,
            COALESCE(stf_relapse.value, '') AS relapse_criteria,
            COALESCE(stf_min.value, '') AS min_age,
            COALESCE(stf_max.value, '') AS max_age,
            COALESCE(stf_stable.value, '') AS stable_dis_min_dur,
            CASE WHEN sbf_rare.value = true THEN 'Y' WHEN sbf_rare.value = false THEN 'N' ELSE '' END AS rare_dis,
            CASE WHEN sbf_healthy.value = true THEN 'Y' WHEN sbf_healthy.value = false THEN 'N' ELSE '' END AS healthy_subj,
            CASE WHEN sbf_ped.value = true THEN 'Y' WHEN sbf_ped.value = false THEN 'N' ELSE '' END AS pediatric,
            CASE WHEN sbf_ped_post.value = true THEN 'Y' WHEN sbf_ped_post.value = false THEN 'N' ELSE '' END AS pediatric_postmarket,
            CASE WHEN sbf_ped_inv.value = true THEN 'Y' WHEN sbf_ped_inv.value = false THEN 'N' ELSE '' END AS pediatric_inv,
            sif_plan.value AS plan_no_subject
        RETURN therapy_area_nf, indication_nf, diag_grp_nf, sex, sex_nf, rare_dis, rare_dis_nf,
            healthy_subj, healthy_subj_nf, min_age, min_age_nf, max_age, max_age_nf,
            stable_dis_min_dur, stable_dis_min_dur_nf, pediatric, pediatric_nf,
            pediatric_postmarket, pediatric_postmarket_nf, pediatric_inv, pediatric_inv_nf,
            relapse_criteria, relapse_criteria_nf, plan_no_subject, plan_no_subject_nf
    """
    res = query(full_query, params)
    if not res:
        return None
    row = res[0]
    therapy_area = _get_multiselect_ct_list_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=study_value_version,
        field_name="therapeutic_area_codes",
    )
    indication = _get_multiselect_ct_list_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=study_value_version,
        field_name="disease_condition_or_indication_codes",
    )
    diag_grp = _get_multiselect_ct_list_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=study_value_version,
        field_name="diagnosis_group_codes",
    )
    plan_val = row.get("plan_no_subject")
    if plan_val is not None and isinstance(plan_val, (str, float)):
        try:
            plan_val = int(plan_val)
        except TypeError, ValueError:
            plan_val = None
    return {
        "therapy_area": therapy_area,
        "therapy_area_nf": row.get("therapy_area_nf"),
        "indication": indication,
        "indication_nf": row.get("indication_nf"),
        "diag_grp": diag_grp,
        "diag_grp_nf": row.get("diag_grp_nf"),
        "sex": row.get("sex"),
        "sex_nf": row.get("sex_nf"),
        "rare_dis": (row.get("rare_dis") or "").strip(),
        "rare_dis_nf": row.get("rare_dis_nf"),
        "healthy_subj": (row.get("healthy_subj") or "").strip(),
        "healthy_subj_nf": row.get("healthy_subj_nf"),
        "min_age": (row.get("min_age") or "").strip(),
        "min_age_nf": row.get("min_age_nf"),
        "max_age": (row.get("max_age") or "").strip(),
        "max_age_nf": row.get("max_age_nf"),
        "stable_dis_min_dur": (row.get("stable_dis_min_dur") or "").strip(),
        "stable_dis_min_dur_nf": row.get("stable_dis_min_dur_nf"),
        "pediatric": (row.get("pediatric") or "").strip(),
        "pediatric_nf": row.get("pediatric_nf"),
        "pediatric_postmarket": (row.get("pediatric_postmarket") or "").strip(),
        "pediatric_postmarket_nf": row.get("pediatric_postmarket_nf"),
        "pediatric_inv": (row.get("pediatric_inv") or "").strip(),
        "pediatric_inv_nf": row.get("pediatric_inv_nf"),
        "relapse_criteria": (row.get("relapse_criteria") or "").strip(),
        "relapse_criteria_nf": row.get("relapse_criteria_nf"),
        "plan_no_subject": plan_val,
        "plan_no_subject_nf": row.get("plan_no_subject_nf"),
    }


def get_study_metadata_listing(
    project_id: str,
    study_number: str,
    subpart_acronym: str | None = None,
    study_value_version: str | None = None,
    datetime_value: str | None = None,
) -> models.StudyMetadataListingModel:
    """
    Return study metadata listing via direct Cypher.

    If ``datetime_value`` is set, ``study_value_version`` is resolved from it.
    If both ``study_value_version`` and ``datetime_value`` are omitted, the
    latest released study value is used (see ``get_base_query_for_study_root_and_value_with_study_id``).
    """
    if datetime_value:
        study_value_version = get_latest_version_from_datetime(
            project=project_id,
            study_number=study_number,
            date_time=datetime_value,
            subpart=subpart_acronym,
        )
    request_dt = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    specified_dt = datetime_value if datetime_value else ""
    api_version = "v1"
    params = {
        "project": project_id,
        "study_number": study_number,
        "subpart": subpart_acronym,
        "study_version_number": study_value_version,
        "specified_dt": specified_dt,
        "request_dt": request_dt,
        "api_version": api_version,
    }
    full_query = get_base_query_for_study_root_and_value_with_study_id(
        study_version_number=study_value_version, subpart=subpart_acronym
    )
    full_query += """
        OPTIONAL MATCH (study_value)-[:HAS_TEXT_FIELD]->(stf:StudyTextField {field_name: 'study_title'})
        RETURN
            study_value.study_id_prefix AS project,
            study_value.study_number AS study_number,
            study_value.study_subpart_acronym AS subpart,
            COALESCE(study_value.study_id_prefix, '') + '-'
            + COALESCE(toString(study_value.study_number), '')
            + COALESCE(study_value.study_subpart_acronym, '') AS study_id,
            COALESCE(study_value.study_id_prefix, '') + '-'
            + COALESCE(toString(study_value.study_number), '')
            + COALESCE(study_value.study_subpart_acronym, '') AS full_study_id,
            rel.version AS study_ver,
            $specified_dt AS specified_dt,
            $request_dt AS request_dt,
            $api_version AS api_version,
            toString(datetime()) AS fetch_dt,
            stf.value AS title
    """
    res = query(full_query, params)
    NotFoundException.raise_if(
        len(res) == 0,
        msg=f"Study id {project_id}-{study_number}{subpart_acronym or ''} not found.",
    )
    ValidationException.raise_if(len(res) > 1, msg="Too many results.")
    row = res[0]
    selected_study_value_version = row.get("study_ver")
    ValidationException.raise_if(
        selected_study_value_version is None,
        msg="Unable to resolve released study version.",
    )
    selected_study_value_version = str(selected_study_value_version)
    study_ver = row["study_ver"]
    if study_ver is not None and not isinstance(study_ver, (int, float)):
        study_ver = float(study_ver)
    arms = _get_study_arms_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=selected_study_value_version,
    )
    branches = _get_study_branch_arms_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=selected_study_value_version,
    )
    cohorts = _get_study_cohorts_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=selected_study_value_version,
    )
    epochs = _get_study_epochs_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=selected_study_value_version,
    )
    visits = _get_study_visits_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=selected_study_value_version,
    )
    elements = _get_study_elements_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=selected_study_value_version,
    )
    design_matrix = _get_study_design_cells_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=selected_study_value_version,
    )
    endpoints = _get_study_endpoints_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=selected_study_value_version,
    )
    objectives = _get_study_objectives_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=selected_study_value_version,
    )
    criteria = _get_study_criteria_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=selected_study_value_version,
    )
    reg_id = _get_study_registry_identifiers_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=selected_study_value_version,
    )
    study_type = _get_study_type_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=selected_study_value_version,
    )
    study_attributes = _get_study_attributes_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=selected_study_value_version,
    )
    study_population = _get_study_population_for_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=selected_study_value_version,
    )
    payload = {
        "project": row.get("project") or "",
        "study_number": row.get("study_number") or "",
        "subpart": row.get("subpart"),
        "study": row.get("full_study_id") or "",
        "api_version": row["api_version"],
        "study_version": str(study_ver),
        "fetch_dt": row.get("fetch_dt") or "",
        "specified_dt": row["specified_dt"] or "",
        "title": row.get("title"),
        "reg_id": reg_id,
        "study_type": study_type,
        "study_attributes": study_attributes,
        "study_population": study_population,
        "arms": arms,
        "branches": branches,
        "cohorts": cohorts,
        "epochs": epochs,
        "elements": elements,
        "design_matrix": design_matrix,
        "visits": visits,
        "criteria": criteria,
        "objectives": objectives,
        "endpoints": endpoints,
    }
    return models.StudyMetadataListingModel(**payload)


def get_studies_audit_trail(
    from_ts: datetime,
    to_ts: datetime,
    study_id: str | None,
    entity_type: models.StudyAuditTrailEntity | None = None,
    exclude_study_ids: list[str] | None = None,
    page_number: int = 1,
) -> list[dict[Any, Any]]:
    validate_page_number_and_page_size(
        page_number, settings.consumer_api_audit_trail_max_rows
    )
    params = {"from_ts": from_ts.isoformat(), "to_ts": to_ts.isoformat()}

    filters = []
    if study_id:
        params["study_id"] = study_id.upper().strip()
        filters.append("toUpper(study_id) CONTAINS $study_id")

    if entity_type:
        params["entity_type"] = entity_type.value.strip()
        entity_type_filter = "$entity_type IN entity_labels"
    else:
        entity_type_filter = ""

    if exclude_study_ids:
        for idx, sid in enumerate(exclude_study_ids):
            if sid.upper().strip():
                params[f"exclude_study_ids_{idx}"] = sid.upper().strip()
                filters.append(f"NOT study_id CONTAINS $exclude_study_ids_{idx}")

    base_query = f"""
        MATCH 
            (sr:StudyRoot)-[:LATEST]->
            (sv:StudyValue)<-[:AFTER]-
            (study_sa:StudyAction)
        
        WITH DISTINCT
            sr,
            sv,
            sr.uid AS study_uid,
            CASE sv.subpart_id
                WHEN IS NULL 
                    THEN 
                        toUpper(
                            COALESCE(sv.study_id_prefix, '') 
                            + "-" 
                            + COALESCE(sv.study_number, '')
                        )
                ELSE toUpper(
                        COALESCE(sv.study_id_prefix, '') 
                        + "-" 
                        + COALESCE(sv.study_number, '')
                    ) 
                    + "-" 
                    + sv.subpart_id
            END AS study_id
            
        { 'WHERE ' + ' AND '.join(filters) if filters else ''}

        WITH distinct sr, sv, study_uid, study_id

        MATCH 
            (obj_after)<-[:AFTER]-
            (sa:StudyAction)<-[:AUDIT_TRAIL]- 
            (sr)-[:LATEST]->
            (sv)
            WHERE 
                sa.date >= datetime($from_ts) 
                AND 
                sa.date < datetime($to_ts)

        OPTIONAL MATCH 
            (sa)-[:BEFORE]->
            (obj_before)

        WITH DISTINCT
            sa.date AS ts,
            study_uid,
            study_id,
            [
                label IN labels(sa) 
                    WHERE label <> 'StudyAction'
            ][0] as action,
            obj_after.uid as entity_uid,
            labels(obj_after) as entity_labels,
            [
                key IN keys(obj_after) 
                    WHERE obj_after[key] <> obj_before[key]
            ] AS changed_properties,
            CASE WHEN sa.author_id IS NOT NULL AND sa.author_id <> ''
                THEN apoc.util.md5([sa.author_id])
                ELSE ''
            END AS author
            { 'WHERE ' + entity_type_filter if entity_type_filter else ''}

        RETURN DISTINCT
            ts,
            study_uid,
            study_id,
            action,
            entity_uid,
            apoc.text.join(entity_labels, '|') AS entity_type,
            changed_properties,
            author
        ORDER BY ts ASC
        """

    full_query = " ".join(
        [
            base_query,
            db_pagination_clause(
                settings.consumer_api_audit_trail_max_rows, page_number
            ),
        ]
    )
    return query(full_query, params)


def get_projects(
    page_size: int = 10,
    page_number: int = 1,
) -> list[dict[Any, Any]]:
    validate_page_number_and_page_size(page_number, page_size)

    # Projects and clinical programmes are plain unversioned nodes, so there
    # is no Root/Value traversal and no status filtering here.
    # The node property is `project_number`; the Consumer API exposes it as
    # `project_id`, which is the name the other endpoints already use.
    base_query = """
        MATCH (clinical_programme:ClinicalProgramme)-[:HOLDS_PROJECT]->(project:Project)

        WITH
        project.uid AS uid,
        project.project_number AS project_id,
        project.name AS name,
        project.description AS description,
        clinical_programme.uid AS clinical_programme_uid,
        clinical_programme.name AS clinical_programme_name

        RETURN *
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause("project_id", "ASC"),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query)


def project_id_exists(project_id: str) -> bool:
    """Returns True if a Project node with the given project ID exists.

    Matches the exact, case-sensitive lookup done by the main API's
    `ProjectRepository.project_number_exists`, so a project that passes this
    check also passes the domain layer's own check.
    """
    result = query(
        """
        MATCH (project:Project {project_number: $project_id})
        RETURN count(project) > 0 AS exists
        """,
        params={"project_id": project_id},
    )
    return bool(result and result[0]["exists"])


def get_codelists(
    page_size: int = 10,
    page_number: int = 1,
    name_status: models.LibraryItemStatus | None = None,
    attributes_status: models.LibraryItemStatus | None = None,
) -> list[dict[Any, Any]]:
    validate_page_number_and_page_size(page_number, page_size)

    attributes_status_filter = (
        "last_version_rel_attributes.status = $status_attributes "
        if attributes_status
        else ""
    )

    name_status_filter = (
        "last_version_rel_name.status = $status_name " if name_status else ""
    )

    status_filter = ""

    if attributes_status_filter and name_status_filter:
        status_filter = f"WHERE {attributes_status_filter} AND {name_status_filter}"
    elif attributes_status_filter:
        status_filter = f"WHERE {attributes_status_filter}"
    elif name_status_filter:
        status_filter = f"WHERE {name_status_filter}"

    params = {
        "status_attributes": attributes_status.value if attributes_status else None,
        "status_name": name_status.value if name_status else None,
    }

    base_query = f"""
        MATCH (codelist_root:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->
        (codelist_attributes_root:CTCodelistAttributesRoot)-[:LATEST]->(codelist_attributes_value:CTCodelistAttributesValue)

        MATCH (codelist_root)-[:HAS_NAME_ROOT]->(codelist_name_root:CTCodelistNameRoot)-[:LATEST]->(codelist_name_value:CTCodelistNameValue)

        WITH
        DISTINCT codelist_root, codelist_attributes_root, codelist_attributes_value, codelist_name_root, codelist_name_value,
        head([(library:Library)-[:CONTAINS_CODELIST]->(codelist_root) | library]) AS library

        CALL {{
                WITH codelist_attributes_root, codelist_attributes_value
                MATCH (codelist_attributes_root)-[hv:HAS_VERSION]-(codelist_attributes_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS last_version_rel_attributes
            }}
        CALL {{
                WITH codelist_name_root, codelist_name_value
                MATCH (codelist_name_root)-[hv:HAS_VERSION]-(codelist_name_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS last_version_rel_name
            }}

        WITH codelist_root, codelist_attributes_value, codelist_name_value, library,
             last_version_rel_attributes, last_version_rel_name

        {status_filter}

        WITH
        codelist_root.uid AS uid,
        codelist_attributes_value.name AS name,
        codelist_attributes_value.submission_value AS submission_value,
        codelist_attributes_value.preferred_term AS nci_preferred_name,
        codelist_attributes_value.definition AS definition,
        codelist_attributes_value.extensible AS is_extensible,
        codelist_name_value.name AS sponsor_preferred_name,
        library.name AS library_name,
        last_version_rel_attributes.version AS attributes_version,
        last_version_rel_attributes.status AS attributes_status,
        last_version_rel_name.version AS name_version,
        last_version_rel_name.status AS name_status

        RETURN *
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause("name", "ASC"),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query, params=params)


def get_codelist_terms(
    codelist_submission_value: str | None = None,
    codelist_uid: str | None = None,
    page_size: int = 10,
    page_number: int = 1,
    name_status: models.LibraryItemStatus | None = None,
    attributes_status: models.LibraryItemStatus | None = None,
) -> list[dict[Any, Any]]:
    validate_page_number_and_page_size(page_number, page_size)

    attributes_status_filter = (
        "last_version_rel_attributes.status = $status_attributes "
        if attributes_status
        else ""
    )

    name_status_filter = (
        "last_version_rel_name.status = $status_name " if name_status else ""
    )

    status_filter = ""

    if attributes_status_filter and name_status_filter:
        status_filter = f"WHERE {attributes_status_filter} AND {name_status_filter}"
    elif attributes_status_filter:
        status_filter = f"WHERE {attributes_status_filter}"
    elif name_status_filter:
        status_filter = f"WHERE {name_status_filter}"

    params: dict[str, Any] = {
        "status_attributes": attributes_status.value if attributes_status else None,
        "status_name": name_status.value if name_status else None,
    }

    # Build the codelist match clause depending on which filters are provided
    codelist_match_lines = [
        "MATCH (codelist_root:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(clav:CTCodelistAttributesValue)"
    ]
    codelist_where_parts = []

    if codelist_submission_value is not None:
        codelist_where_parts.append(
            "clav.submission_value = $codelist_submission_value"
        )
        params["codelist_submission_value"] = codelist_submission_value

    if codelist_uid is not None:
        codelist_where_parts.append("codelist_root.uid = $codelist_uid")
        params["codelist_uid"] = codelist_uid

    if codelist_where_parts:
        codelist_match_lines.append("WHERE " + " AND ".join(codelist_where_parts))

    codelist_match = "\n        ".join(codelist_match_lines)

    base_query = f"""
        {codelist_match}
                            
        MATCH (codelist_root)-[ht:HAS_TERM]->(ct_cl_term:CTCodelistTerm)-[:HAS_TERM_ROOT]->(ct_term_root:CTTermRoot)<-[:CONTAINS_TERM]-(library:Library)
        WHERE ht.end_date IS NULL
        MATCH (ct_term_root)-[:HAS_NAME_ROOT]->(tnr:CTTermNameRoot)-[:LATEST]->(tnv:CTTermNameValue)
        MATCH (ct_term_root)-[:HAS_ATTRIBUTES_ROOT]->(tar:CTTermAttributesRoot)-[:LATEST]->(tav:CTTermAttributesValue)
        
        WITH 
        DISTINCT codelist_root, ht, ct_cl_term, ct_term_root, tnr, tnv, tar, tav, library

        CALL {{
                WITH tar, tav
                MATCH (tar)-[hv:HAS_VERSION]-(tav)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS last_version_rel_attributes
            }}
        CALL {{
                WITH tnr, tnv
                MATCH (tnr)-[hv:HAS_VERSION]-(tnv)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS last_version_rel_name
            }}

        WITH codelist_root, ct_term_root, ct_cl_term, ht, tnv, tav, library,
             last_version_rel_attributes, last_version_rel_name

        {status_filter}

        WITH
        codelist_root.uid as codelist_uid,
        ct_term_root.uid AS term_uid,
        codelist_root.uid + '_' + ct_term_root.uid AS sort_field,
        ht.order AS order,
        ht.ordinal AS ordinal,
        ct_cl_term.submission_value AS submission_value,
        tav.concept_id AS concept_id,
        tav.preferred_term AS nci_preferred_name,
        tnv.name AS sponsor_preferred_name,
        library.name AS library_name,
        last_version_rel_attributes.version AS attributes_version,
        last_version_rel_attributes.status AS attributes_status,
        last_version_rel_name.version AS name_version,
        last_version_rel_name.status AS name_status

        RETURN *
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause("sort_field", "ASC", secondary_sort_fields="sort_field"),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query, params=params)


def get_unit_definitions(
    page_size: int = 10,
    page_number: int = 1,
    subset: str | None = None,
    status: models.LibraryItemStatus | None = None,
) -> list[dict[Any, Any]]:
    validate_page_number_and_page_size(page_number, page_size)

    params: dict[str, Any] = {
        "status": status.value if status else None,
        "unit_dimension_cl_submval": settings.unit_dimension_cl_submval,
        "unit_subset_cl_submval": settings.unit_subset_cl_submval,
    }

    subset_filter = ""
    if subset:
        params["subset"] = subset
        subset_filter = """WHERE $subset IN [(concept_value)-[:HAS_UNIT_SUBSET]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->
        (:CTTermNameRoot)-[:LATEST]->(term_name_value) | term_name_value.name]"""

    status_filter = "WHERE last_version_rel.status = $status " if status else ""

    base_query = f"""
        MATCH (concept_root:UnitDefinitionRoot)-[:LATEST]->(concept_value:UnitDefinitionValue)
        {subset_filter}

        WITH 
            DISTINCT concept_root, concept_value,
            head([(library)-[:CONTAINS_CONCEPT]->(concept_root) | library]) AS library

        CALL {{
                WITH concept_root, concept_value
                MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS last_version_rel
            }}

        WITH concept_root, concept_value, library, last_version_rel

        {status_filter}

        CALL {{
            WITH concept_value
            OPTIONAL MATCH (concept_value)-[:HAS_UNIT_SUBSET]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(sub_tr:CTTermRoot)
            OPTIONAL MATCH (sub_tr)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(sub_tnv:CTTermNameValue)
            OPTIONAL MATCH (sub_tr)<-[:HAS_TERM_ROOT]-(sub_cl_term:CTCodelistTerm)<-[:HAS_TERM]-(sub_cl_root:CTCodelistRoot)
                -[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(sub_cl_attrs:CTCodelistAttributesValue {{submission_value: $unit_subset_cl_submval}})
            WITH sub_tr, sub_tnv, sub_cl_term, sub_cl_root, sub_cl_attrs
            WHERE sub_tr IS NOT NULL
            RETURN COLLECT({{
                term_uid: sub_tr.uid,
                term_name: sub_tnv.name,
                term_submission_value: sub_cl_term.submission_value,
                codelist_uid: sub_cl_root.uid,
                codelist_name: sub_cl_attrs.name,
                codelist_submission_value: sub_cl_attrs.submission_value
            }}) AS subsets
        }}

        OPTIONAL MATCH (concept_value)-[:HAS_CT_DIMENSION]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(dim_tr:CTTermRoot)
        OPTIONAL MATCH (dim_tr)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(dim_tnv:CTTermNameValue)
        OPTIONAL MATCH (dim_tr)<-[:HAS_TERM_ROOT]-(dim_cl_term:CTCodelistTerm)<-[:HAS_TERM]-(dim_cl_root:CTCodelistRoot)
            -[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(dim_cl_attrs:CTCodelistAttributesValue {{submission_value: $unit_dimension_cl_submval}})
        OPTIONAL MATCH (concept_value)-[:HAS_UCUM_TERM]->(ucum_root)-[:LATEST]->(ucum_val)

        WITH
            concept_root.uid AS uid,
            concept_value.nci_concept_id AS nci_concept_id,
            concept_value.nci_concept_name AS nci_concept_name,
            concept_value.name AS name,
            library.name AS library_name,
            last_version_rel.status AS status,
            last_version_rel.version AS version,
            subsets,
            concept_value.convertible_unit AS is_convertible_unit,
            concept_value.master_unit AS is_master_unit,
            concept_value.si_unit AS is_si_unit,
            concept_value.display_unit AS is_display_unit,
            concept_value.us_conventional_unit AS is_us_conventional_unit,
            concept_value.use_complex_unit_conversion AS use_complex_unit_conversion,
            concept_value.use_molecular_weight AS use_molecular_weight,
            ucum_val.name AS ucum_unit_name,
            CASE WHEN dim_tr IS NOT NULL THEN {{
                term_uid: dim_tr.uid,
                term_name: dim_tnv.name,
                term_submission_value: dim_cl_term.submission_value,
                codelist_uid: dim_cl_root.uid,
                codelist_name: dim_cl_attrs.name,
                codelist_submission_value: dim_cl_attrs.submission_value
            }} ELSE null END AS unit_dimension,
            concept_value.legacy_code AS legacy_code,
            concept_value.conversion_factor_to_master AS conversion_factor_to_master

        RETURN *
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause("name", "ASC"),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query, params)


def get_library_activity_item_classes(
    sort_by: models.SortByLibraryActivityItemClass = models.SortByLibraryActivityItemClass.NAME,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: int = 10,
    page_number: int = 1,
    library: models.Library | None = None,
    status: models.LibraryItemStatus | None = None,
    is_nsv: bool | None = None,
) -> list[dict[Any, Any]]:
    """
    Return a paginated list of Activity Item Classes (regular ones and/or NSVs).

    Filtering:
      - ``library``: when provided, restrict to a single library (e.g. *Sponsor*).
      - ``status``: when provided, restrict to a specific version status
        (Final/Draft/Retired) of the latest version of each Activity Item Class.
      - ``is_nsv``:
          * ``True``  -> return only Non-Standard Variables (value node carries
            the ``NonStandardVariableValue`` label).
          * ``False`` -> return only regular Activity Item Classes (value node
            does NOT carry the ``NonStandardVariableValue`` label).
          * ``None``  -> return both.
    """
    validate_page_number_and_page_size(page_number, page_size)

    params: dict[str, Any] = {
        "status": status.value if status else None,
        "library": library.value if library else None,
    }

    status_filter = "AND last_version_rel.status = $status " if status else ""

    # NSV is a label on the *value* node (NonStandardVariableValue is a subclass
    # of ActivityItemClassValue in the neomodel layer).
    if is_nsv is True:
        nsv_filter = "AND concept_value:NonStandardVariableValue "
    elif is_nsv is False:
        nsv_filter = "AND NOT concept_value:NonStandardVariableValue "
    else:
        nsv_filter = ""

    base_query = (
        """
            MATCH (lib:Library {name: $library})-[:CONTAINS]->(concept_root:ActivityItemClassRoot)
        """
        if library
        else """
            MATCH (lib:Library)-[:CONTAINS]->(concept_root:ActivityItemClassRoot)
        """
    )

    base_query += f"""
        -[:LATEST]->(concept_value:ActivityItemClassValue)
        WITH lib, concept_root, concept_value
        CALL {{
                WITH concept_root, concept_value
                MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS last_version_rel
            }}

        WITH lib, concept_root, concept_value, last_version_rel
        WHERE 1 = 1 {status_filter} {nsv_filter}

        WITH lib, concept_root, concept_value, last_version_rel,
            head([
                (concept_value)-[:HAS_DATA_TYPE]->(dt_ctx:CTTermContext)
                -[:HAS_SELECTED_TERM]->(dt_root:CTTermRoot)-[:HAS_NAME_ROOT]->
                (:CTTermNameRoot)-[:LATEST]->(dt_name_value:CTTermNameValue)
                | {{
                    uid: dt_root.uid,
                    name: dt_name_value.name,
                    codelist_uid: head([
                        (dt_ctx)-[:HAS_SELECTED_CODELIST]->(dt_codelist:CTCodelistRoot)
                        | dt_codelist.uid
                    ])
                }}
            ]) AS data_type,
            head([
                (concept_value)-[:HAS_ROLE]->(role_ctx:CTTermContext)
                -[:HAS_SELECTED_TERM]->(role_root:CTTermRoot)-[:HAS_NAME_ROOT]->
                (:CTTermNameRoot)-[:LATEST]->(role_name_value:CTTermNameValue)
                | {{
                    uid: role_root.uid,
                    name: role_name_value.name,
                    codelist_uid: head([
                        (role_ctx)-[:HAS_SELECTED_CODELIST]->(role_codelist:CTCodelistRoot)
                        | role_codelist.uid
                    ])
                }}
            ]) AS role,
            [
                (concept_root)<-[rel:HAS_ITEM_CLASS]-(aic_root:ActivityInstanceClassRoot)
                -[:LATEST]->(aic_value:ActivityInstanceClassValue) | {{
                    uid: aic_root.uid,
                    name: aic_value.name,
                    mandatory: rel.mandatory,
                    is_adam_param_specific_enabled: rel.is_adam_param_specific_enabled,
                    is_additional_optional: rel.is_additional_optional,
                    is_default_linked: rel.is_default_linked
                }}
            ] AS activity_instance_classes,
            [
                (concept_root)-[:HAS_VALID_CODELIST_FOR_ITEMS]->(valid_cl:CTCodelistRoot)
                | {{
                    uid: valid_cl.uid,
                    submission_value: head([
                        (valid_cl)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
                        -[:LATEST]->(valid_cl_attrs:CTCodelistAttributesValue)
                        | valid_cl_attrs.submission_value
                    ])
                }}
            ] AS valid_codelists,
            CASE WHEN concept_value:NonStandardVariableValue THEN {{
                code: concept_value.code,
                is_multiple: concept_value.is_multiple,
                length: concept_value.length,
                algorithm: concept_value.algorithm,
                is_cdisc_defined: concept_value.is_cdisc_defined,
                derivation_rule: concept_value.derivation_rule,
                origin_type: head([
                    (concept_value)-[:DEFAULT_ORIGIN_TYPE]->(ot_ctx:CTTermContext)
                    -[:HAS_SELECTED_TERM]->(ot_term:CTTermRoot)
                    -[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(ot_name:CTTermNameValue)
                    | {{
                        uid: ot_term.uid,
                        name: ot_name.name,
                        codelist_uid: head([(ot_ctx)-[:HAS_SELECTED_CODELIST]->(ot_cl:CTCodelistRoot) | ot_cl.uid])
                    }}
                ]),
                origin_source: head([
                    (concept_value)-[:DEFAULT_ORIGIN_SOURCE]->(os_ctx:CTTermContext)
                    -[:HAS_SELECTED_TERM]->(os_term:CTTermRoot)
                    -[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(os_name:CTTermNameValue)
                    | {{
                        uid: os_term.uid,
                        name: os_name.name,
                        codelist_uid: head([(os_ctx)-[:HAS_SELECTED_CODELIST]->(os_cl:CTCodelistRoot) | os_cl.uid])
                    }}
                ])
            }} ELSE null END AS non_standard_variable

        RETURN DISTINCT
            concept_root.uid AS uid,
            concept_value.name AS name,
            lib.name AS library_name,
            concept_value.definition AS definition,
            concept_value.nci_concept_id AS nci_concept_id,
            concept_value.nci_concept_name AS nci_concept_name,
            concept_value.display_name AS display_name,
            concept_value.order AS order,
            last_version_rel.status AS status,
            last_version_rel.version AS version,
            data_type,
            role,
            activity_instance_classes,
            valid_codelists,
            CASE WHEN concept_value:NonStandardVariableValue THEN true ELSE false END AS is_nsv,
            non_standard_variable
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause(sort_by.value, sort_order.value),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query, params)


# Walks IS_SPECIALIZATION_OF up from a bound `dt_root` (0 hops = the term
# itself) to the nearest ancestor that belongs to NSVXMLDT (NSV XML Data
# Type), returning that ancestor's NSVXMLDT submission value as
# `nsv_xml_data_type`. The submission value lives on the CTCodelistTerm join
# node (per-codelist), not on CTTermAttributesValue. Shared between the
# Papillons NSV export query and the standalone single-term lookup below so
# the two can't drift apart.
_NSV_XML_DT_ANCESTOR_TRAVERSAL_CYPHER = """
        CALL {
            WITH dt_root
            MATCH path = (dt_root)-[:IS_SPECIALIZATION_OF*0..]->(ancestor:CTTermRoot)
            MATCH (nsvxmldt_cl:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->
                (:CTCodelistAttributesRoot)-[:LATEST]->
                (:CTCodelistAttributesValue {submission_value: 'NSVXMLDT'})
            MATCH (nsvxmldt_cl)-[nsvxmldt_ht:HAS_TERM]->
                (nsvxmldt_cl_term:CTCodelistTerm)-[:HAS_TERM_ROOT]->(ancestor)
            WHERE nsvxmldt_ht.end_date IS NULL
            WITH nsvxmldt_cl_term, length(path) AS dist
            ORDER BY dist ASC
            LIMIT 1
            RETURN nsvxmldt_cl_term.submission_value AS nsv_xml_data_type
        }
"""


def get_nsv_xml_data_type_for_semtcdt_term(term_submission_value: str) -> str | None:
    """
    Resolve a single SEMTCDT (Semantic Data Type) term to its NSVXMLDT
    (NSV XML Data Type) equivalent, by submission value (e.g. ``"code"``,
    ``"ctTerm"``, ``"unii"``), walking the same IS_SPECIALIZATION_OF chain
    used by ``get_papillons_non_standard_variables``.

    Returns ``None`` if no such SEMTCDT term exists, or it has no NSVXMLDT
    ancestor (inclusive of itself).
    """
    query_str = (
        """
        MATCH (semtcdt_cl:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->
            (:CTCodelistAttributesRoot)-[:LATEST]->
            (:CTCodelistAttributesValue {submission_value: 'SEMTCDT'})
        MATCH (semtcdt_cl)-[semtcdt_ht:HAS_TERM]->
            (semtcdt_cl_term:CTCodelistTerm {submission_value: $term_submission_value})
            -[:HAS_TERM_ROOT]->(dt_root:CTTermRoot)
        WHERE semtcdt_ht.end_date IS NULL
        """
        + _NSV_XML_DT_ANCESTOR_TRAVERSAL_CYPHER
        + """
        RETURN nsv_xml_data_type
        """
    )
    rows = query(query_str, {"term_submission_value": term_submission_value})
    return rows[0]["nsv_xml_data_type"] if rows else None


def get_papillons_non_standard_variables() -> list[dict[Any, Any]]:
    """
    Return every Final Non-Standard Variable whose data type belongs to the
    SEMTCDT (Semantic Data Type) codelist, shaped for the Papillons SDTM_QNAM
    export.

    The data type is translated to its NSVXMLDT (NSV XML Data Type)
    equivalent by walking the real IS_SPECIALIZATION_OF chain up from the
    SEMTCDT term to the nearest ancestor (inclusive of the term itself) that
    belongs to the NSVXMLDT codelist - not a hardcoded table, so this stays
    correct if the term hierarchy in datatype.csv is ever revised.
    """
    query_str = (
        """
        MATCH (lib:Library)-[:CONTAINS]->(concept_root:ActivityItemClassRoot)
        -[:LATEST]->(concept_value:ActivityItemClassValue:NonStandardVariableValue)
        WITH lib, concept_root, concept_value
        CALL {
                WITH concept_root, concept_value
                MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS last_version_rel
            }
        WITH lib, concept_root, concept_value, last_version_rel
        WHERE last_version_rel.status = 'Final'

        MATCH (concept_value)-[:HAS_DATA_TYPE]->(:CTTermContext)
        -[:HAS_SELECTED_TERM]->(dt_root:CTTermRoot)

        // Restrict to data types that belong to the SEMTCDT codelist.
        MATCH (semtcdt_cl:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->
            (:CTCodelistAttributesRoot)-[:LATEST]->
            (:CTCodelistAttributesValue {submission_value: 'SEMTCDT'})
        MATCH (semtcdt_cl)-[semtcdt_ht:HAS_TERM]->
            (:CTCodelistTerm)-[:HAS_TERM_ROOT]->(dt_root)
        WHERE semtcdt_ht.end_date IS NULL
        """
        + _NSV_XML_DT_ANCESTOR_TRAVERSAL_CYPHER
        + """
        RETURN
            concept_value.code AS variable_name,
            concept_value.display_name AS label,
            concept_value.definition AS definition,
            nsv_xml_data_type,
            concept_value.length AS length,
            head([
                (concept_root)-[:HAS_VALID_CODELIST_FOR_ITEMS]->(valid_cl:CTCodelistRoot)
                -[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
                -[:LATEST]->(valid_cl_attrs:CTCodelistAttributesValue)
                | valid_cl_attrs.submission_value
            ]) AS codelist_submission_value,
            concept_value.algorithm AS algorithm,
            concept_value.is_multiple AS is_multiple,
            concept_value.is_cdisc_defined AS is_cdisc_defined,
            head([
                (concept_value)-[:DEFAULT_ORIGIN_TYPE]->(:CTTermContext)
                -[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->
                (:CTTermNameRoot)-[:LATEST]->(ot_name:CTTermNameValue)
                | ot_name.name
            ]) AS origin_type_name,
            head([
                (concept_value)-[:DEFAULT_ORIGIN_SOURCE]->(:CTTermContext)
                -[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->
                (:CTTermNameRoot)-[:LATEST]->(os_name:CTTermNameValue)
                | os_name.name
            ]) AS origin_source_name

        ORDER BY variable_name ASC
        """
    )
    return query(query_str)
