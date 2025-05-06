# pylint: disable=invalid-name
# pylint: disable=redefined-builtin
from common.utils import validate_page_number_and_page_size
from consumer_api.shared.common import db_pagination_clause, db_sort_clause, query
from consumer_api.v1 import models


def get_studies(
    sort_by: models.SortByStudies = models.SortByStudies.UID,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: int = 10,
    page_number: int = 1,
    id: str = None,
) -> list[dict]:
    validate_page_number_and_page_size(page_number, page_size)

    params = {}
    filter_clause = ""

    if id is not None:
        params["id"] = id.strip()
        filter_clause = "WHERE id CONTAINS toUpper($id)"

    base_query = f"""
        MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)
        OPTIONAL MATCH (study_root)-[hv:HAS_VERSION]->(:StudyValue)
        OPTIONAL MATCH (author:User) WHERE author.user_id = hv.author_id
        WITH *,
            COLLECT ({{
                user_id: author.user_id,
                username: author.username
            }}) AS authors
        ORDER BY hv.start_date DESC
        WITH
            study_root.uid as uid,
            study_value.study_acronym as acronym,
            study_value.study_id_prefix as id_prefix,
            study_value.study_number as number,
            toUpper(COALESCE(study_value.study_id_prefix, '') + "-" + COALESCE(study_value.study_number, '')) as id,
            COLLECT({{
                version_status: hv.status,
                version_number: hv.version,
                version_started_at: hv.start_date,
                version_ended_at: hv.end_date,
                version_author_id: hv.author_id,
                all_authors: authors,
                version_description: hv.change_description
            }}) as versions

        {filter_clause}

        RETURN *
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause(sort_by.value, sort_order.value),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query, params)


def get_study_visits(
    study_uid: str,
    sort_by: models.SortByStudyVisits = models.SortByStudyVisits.UID,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: int = 10,
    page_number: int = 1,
    study_version_number: str | None = None,
) -> list[dict]:
    validate_page_number_and_page_size(page_number, page_size)

    params = {"study_uid": study_uid}

    if not study_version_number:
        base_query = "MATCH (study_root:StudyRoot {uid: $study_uid})-[hv:LATEST]->(study_value:StudyValue)"
    else:
        base_query = """MATCH (study_root:StudyRoot {uid: $study_uid})-[hv:HAS_VERSION {version: $study_version_number}]->(study_value:StudyValue)
        WITH study_root, study_value, hv ORDER BY hv.end_date DESC LIMIT 1
        """
        params["study_version_number"] = study_version_number

    base_query += """
        MATCH (study_value)-[:HAS_STUDY_VISIT]-(study_visit:StudyVisit)
        OPTIONAL MATCH (study_visit)-[:HAS_VISIT_NAME]->(:VisitNameRoot)-[:LATEST]->(visit_name_value:VisitNameValue)
        OPTIONAL MATCH (study_visit)-[:HAS_VISIT_TYPE]->(visit_type_ct_term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(visit_type_ct_term_name_value:CTTermNameValue)
        OPTIONAL MATCH (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)-[:HAS_EPOCH]->(epoch_ct_term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(epoch_term:CTTermNameValue)
        OPTIONAL MATCH (study_visit)-[:HAS_TIMEPOINT]->(:TimePointRoot)-[:LATEST]->(:TimePointValue)-[:HAS_UNIT_DEFINITION]->(time_unit_unit_definition_root:UnitDefinitionRoot)-[:LATEST]->(time_unit_unit_definition_value:UnitDefinitionValue)
        OPTIONAL MATCH (study_visit)-[:HAS_TIMEPOINT]->(:TimePointRoot)-[:LATEST]->(:TimePointValue)-[:HAS_VALUE]->(time_value_root:NumericValueRoot)-[:LATEST]->(time_value_value:NumericValue)
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
            visit_name_value.name AS visit_name,
            visit_type_ct_term_root.uid AS visit_type_uid,
            visit_type_ct_term_name_value.name AS visit_type_name,
            window_unit_unit_definition_root.uid AS visit_window_unit_uid,
            window_unit_unit_definition_value.name AS visit_window_unit_name,
            study_epoch.uid AS study_epoch_uid,
            epoch_term.name AS study_epoch_name,
            time_unit_unit_definition_root.uid AS time_unit_uid,
            time_unit_unit_definition_value.name AS time_unit_name,
            time_value_root.uid AS time_value_uid,
            time_value_value.value AS time_value_value,
            CASE
                WHEN hv.status IN ["LOCKED", "RELEASED"]
                THEN hv.version
                ELSE "LATEST on " + apoc.temporal.format(datetime(), 'yyyy-MM-dd HH:mm:ss zzz')
            END as study_version_number

        RETURN *
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause(sort_by.value, sort_order.value),
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
) -> list[dict]:
    validate_page_number_and_page_size(page_number, page_size)

    params = {"study_uid": study_uid}

    if not study_version_number:
        base_query = "MATCH (study_root:StudyRoot {uid: $study_uid})-[hv:LATEST]->(study_value:StudyValue)"
    else:
        base_query = """MATCH (study_root:StudyRoot {uid: $study_uid})-[hv:HAS_VERSION {version: $study_version_number}]->(study_value:StudyValue)
        WITH study_root, study_value, hv ORDER BY hv.end_date DESC LIMIT 1
        """
        params["study_version_number"] = study_version_number

    base_query += """
        WITH study_root, study_value, hv
        MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(sa:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)<-[:HAS_VERSION]-(ar:ActivityRoot)
        MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(soa_group_term:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(soa_group_term_value:CTTermNameValue)
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
            coalesce(av.is_data_collected, False) AS is_data_collected,
            CASE
                WHEN hv.status IN ["LOCKED", "RELEASED"]
                THEN hv.version
                ELSE "LATEST on " + apoc.temporal.format(datetime(), 'yyyy-MM-dd HH:mm:ss zzz')
            END AS study_version_number
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
    sort_by: models.SortByStudyActivities = models.SortByStudyActivities.UID,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: int = 10,
    page_number: int = 1,
    study_version_number: str | None = None,
) -> list[dict]:
    validate_page_number_and_page_size(page_number, page_size)

    params = {"study_uid": study_uid}

    if not study_version_number:
        base_query = "MATCH (study_root:StudyRoot {uid: $study_uid})-[hv:LATEST]->(study_value:StudyValue)"
    else:
        base_query = """MATCH (study_root:StudyRoot {uid: $study_uid})-[hv:HAS_VERSION {version: $study_version_number}]->(study_value:StudyValue)
        WITH study_root, study_value, hv ORDER BY hv.end_date DESC LIMIT 1
        """
        params["study_version_number"] = study_version_number

    base_query += """
        MATCH (study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value)
        MATCH (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value)
        MATCH (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
        MATCH (study_activity_schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value)

        WITH
            hv,
            study_root,
            study_value,
            study_activity_schedule,
            study_visit,
            study_epoch,
            study_activity,
            head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue) | activity_value]) AS activity,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value]) AS activity_subgroup,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(:StudyActivityGroup)-[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue) | activity_group_value]) AS activity_group,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue) | term_name_value]) AS term_name_value,
            head([(study_epoch)-[:HAS_EPOCH]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]-(epoch_term:CTTermNameValue) | epoch_term.name]) AS epoch_name
        ORDER BY study_activity.order, study_visit.visit_number

        RETURN DISTINCT
            study_root.uid AS study_uid,
            study_visit.short_visit_label AS visit_name,
            epoch_name AS epoch_name,
            activity.name AS activity_name,
            activity_subgroup.name AS activity_subgroup_name,
            activity_group.name AS activity_group_name,
            term_name_value.name AS soa_group_name,
            coalesce(activity.is_data_collected, False) AS is_data_collected,
            CASE
                WHEN hv.status IN ["LOCKED", "RELEASED"]
                THEN hv.version
                ELSE "LATEST on " + apoc.temporal.format(datetime(), 'yyyy-MM-dd HH:mm:ss zzz')
            END AS study_version_number
        """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause(sort_by.value, sort_order.value),
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
) -> list[dict]:
    validate_page_number_and_page_size(page_number, page_size)

    params = {"study_uid": study_uid}

    if not study_version_number:
        base_query = "MATCH (study_root:StudyRoot {uid: $study_uid})-[hv:LATEST]->(study_value:StudyValue)"
    else:
        base_query = """MATCH (study_root:StudyRoot {uid: $study_uid})-[hv:HAS_VERSION {version: $study_version_number}]->(study_value:StudyValue)
        WITH study_root, study_value, hv ORDER BY hv.end_date DESC LIMIT 1
        """
        params["study_version_number"] = study_version_number

    base_query += """
        MATCH (study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value)
        MATCH (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value)
        MATCH (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
        MATCH (study_activity_schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->(study_activity_instance:StudyActivityInstance)<-[:HAS_STUDY_ACTIVITY_INSTANCE]-(study_value)

        WITH
            hv,
            study_root,
            study_value,
            study_visit,
            head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue)<-[:LATEST]-(activity_root:ActivityRoot) | { uid: activity_root.uid, name: activity_value.name }]) as activity,
            head([(study_activity_instance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(activity_instance_value:ActivityInstanceValue)<-[:LATEST]-(activity_instance_root:ActivityInstanceRoot) | { uid: activity_instance_root.uid, name: activity_instance_value.name, topic_code: activity_instance_value.topic_code, adam_param_code: activity_instance_value.adam_param_code }]) as activity_instance,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)<-[:LATEST]-(activity_subgroup_root:ActivitySubGroupRoot) | { uid: activity_subgroup_root.uid, name: activity_subgroup_value.name }]) as activity_subgroup,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(:StudyActivityGroup)-[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)<-[:LATEST]-(activity_group_root:ActivityGroupRoot) | { uid: activity_group_root.uid, name: activity_group_value.name }]) as activity_group,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue) | term_name_value]) as term_name_value,
            head([(study_epoch)-[:HAS_EPOCH]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]-(epoch_term:CTTermNameValue) | epoch_term.name]) as epoch_name
        ORDER BY study_activity.order, study_visit.visit_number

        RETURN DISTINCT
            study_root.uid AS study_uid,
            toUpper(COALESCE(study_value.study_id_prefix, '') + "-" + COALESCE(study_value.study_number, '')) as study_id,
            study_visit.uid AS visit_uid,
            study_visit.short_visit_label AS visit_short_name,
            epoch_name AS epoch_name,
            activity.name AS activity_name,
            activity.uid AS activity_uid,
            activity_instance.name AS activity_instance_name,
            activity_instance.uid AS activity_instance_uid,
            activity_instance.topic_code AS topic_code,
            activity_instance.adam_param_code AS param_code,
            activity_subgroup.name AS activity_subgroup_name,
            activity_subgroup.uid AS activity_subgroup_uid,
            activity_group.name AS activity_group_name,
            activity_group.uid AS activity_group_uid,
            term_name_value.name as soa_group_name,
            CASE
                WHEN hv.status IN ["LOCKED", "RELEASED"]
                THEN hv.version
                ELSE "LATEST on " + apoc.temporal.format(datetime(), 'yyyy-MM-dd HH:mm:ss zzz')
            END as study_version_number
    """

    full_query = " ".join(
        [
            base_query,
            db_sort_clause(sort_by.value, sort_order.value),
            db_pagination_clause(page_size, page_number),
        ]
    )
    return query(full_query, params)
