import datetime
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGrouping,
    ActivityGroupRoot,
    ActivityRoot,
    ActivitySubGroupRoot,
    ActivityValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains.concepts.activities.activity import (
    ActivityAR,
    ActivityGroupingVO,
    ActivityVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.activities.activity import Activity
from clinical_mdr_api.models.utils import GenericFilteringReturn
from common.config import settings
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime, version_string_to_tuple


def _get_display_version(versions: list[dict[Any, Any]]) -> dict[Any, Any] | None:
    if len(versions) == 1:
        return versions[0]
    sorted_versions = sorted(
        versions, key=lambda x: version_string_to_tuple(x["version"]), reverse=True
    )
    for status in [
        LibraryItemStatus.FINAL,
        LibraryItemStatus.RETIRED,
        LibraryItemStatus.DRAFT,
    ]:
        latest_ver = next(
            (
                version
                for version in sorted_versions
                if version["status"] == status.value
            ),
            None,
        )
        if latest_ver:
            return latest_ver
    return None


class ActivityRepository(ConceptGenericRepository[ActivityAR]):
    root_class = ActivityRoot
    value_class = ActivityValue
    return_model = Activity
    filter_query_parameters: dict[Any, Any] = {}

    def latest_concept_in_library_exists_by_name(
        self,
        library_name: str,
        concept_name: str,
        activity_groupings: list[ActivityGroupingVO] | None = None,
    ) -> bool:
        if not activity_groupings or library_name != settings.requested_library_name:
            return super().latest_concept_in_library_exists_by_name(
                library_name, concept_name
            )
        # Check if an activity with the same name AND same groupings exists
        grouping_clauses = []
        params: dict[str, Any] = {
            "concept_name": concept_name,
            "library_name": library_name,
        }
        for i, grouping in enumerate(activity_groupings):
            group_uid = (
                grouping.activity_group_uid
                if hasattr(grouping, "activity_group_uid")
                else grouping.get("activity_group_uid")
            )
            subgroup_uid = (
                grouping.activity_subgroup_uid
                if hasattr(grouping, "activity_subgroup_uid")
                else grouping.get("activity_subgroup_uid")
            )
            if group_uid and subgroup_uid:
                grouping_clauses.append(f"""EXISTS {{
                        MATCH (concept_value)-[:HAS_GROUPING]->(ag:ActivityGrouping)
                            -[:HAS_SELECTED_GROUP]->(gv:ActivityGroupValue)
                            <-[:HAS_VERSION]-(gr:ActivityGroupRoot {{uid: $group_uid_{i}}})
                        WHERE EXISTS {{
                            MATCH (ag)-[:HAS_SELECTED_SUBGROUP]->(sv:ActivitySubGroupValue)
                                <-[:HAS_VERSION]-(sr:ActivitySubGroupRoot {{uid: $subgroup_uid_{i}}})
                        }}
                    }}""")
                params[f"group_uid_{i}"] = group_uid
                params[f"subgroup_uid_{i}"] = subgroup_uid

        if not grouping_clauses:
            return super().latest_concept_in_library_exists_by_name(
                library_name, concept_name
            )

        where_clause = " AND ".join(grouping_clauses)
        query = f"""
            MATCH (l:Library {{name: $library_name}})-[:CONTAINS_CONCEPT]->
                    (concept_root:ActivityRoot)-[:LATEST]->
                    (concept_value:ActivityValue{{name: $concept_name}})
            WHERE {where_clause}
            RETURN concept_root
            """
        result, _ = db.cypher_query(query, params)
        return len(result) > 0 and len(result[0]) > 0

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> ActivityAR:
        major, minor = input_dict["version"].split(".")
        activity_ar = ActivityAR.from_repository_values(
            uid=input_dict["uid"],
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=input_dict.get("nci_concept_id"),
                nci_concept_name=input_dict.get("nci_concept_name"),
                name=input_dict["name"],
                name_sentence_case=input_dict["name_sentence_case"],
                synonyms=input_dict.get("synonyms") or [],
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                activity_groupings=[
                    ActivityGroupingVO(
                        activity_group_uid=activity_grouping.get("activity_group").get(
                            "uid"
                        ),
                        activity_group_name=activity_grouping.get("activity_group").get(
                            "name"
                        ),
                        activity_group_version=f"{activity_grouping.get('activity_group').get('major_version')}.{activity_grouping.get('activity_group').get('minor_version')}",
                        activity_subgroup_uid=activity_grouping.get(
                            "activity_subgroup"
                        ).get("uid"),
                        activity_subgroup_name=activity_grouping.get(
                            "activity_subgroup"
                        ).get("name"),
                        activity_subgroup_version=f"{activity_grouping.get('activity_subgroup').get('major_version')}.{activity_grouping.get('activity_subgroup').get('minor_version')}",
                    )
                    for activity_grouping in input_dict.get("activity_groupings")
                ],
                activity_instances=input_dict["activity_instances"],
                request_rationale=input_dict.get("request_rationale"),
                is_request_final=input_dict["is_request_final"],
                used_by_studies=input_dict["used_by_studies"],
                replaced_by_activity=input_dict.get("replaced_by_activity"),
                reason_for_rejecting=input_dict.get("reason_for_rejecting"),
                contact_person=input_dict.get("contact_person"),
                is_request_rejected=input_dict["is_request_rejected"],
                is_data_collected=input_dict["is_data_collected"],
                is_multiple_selection_allowed=input_dict[
                    "is_multiple_selection_allowed"
                ],
                is_finalized=input_dict["is_finalized"],
                is_used_by_legacy_instances=input_dict["is_used_by_legacy_instances"],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict["library_name"],
                is_library_editable_callback=(
                    lambda _: input_dict["is_library_editable"]
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict["change_description"],
                status=LibraryItemStatus(input_dict.get("status")),
                author_id=input_dict["author_id"],
                author_username=input_dict.get("author_username"),
                start_date=convert_to_datetime(value=input_dict["start_date"]),
                end_date=convert_to_datetime(value=input_dict.get("end_date")),
                major_version=int(major),
                minor_version=int(minor),
            ),
        )
        return activity_ar

    def _create_ar(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        study_count: int = 0,
        *,
        activity_root,
        **kwargs,
    ) -> ActivityAR:
        activity_groupings = []
        filter_out_retired_groupings = kwargs.get("filter_out_retired_groupings")
        for activity_grouping in activity_root["activity_groupings"]:
            activity_group = activity_grouping["activity_group"]
            activity_group_status = activity_group.get("status")
            activity_subgroup = activity_grouping["activity_subgroup"]
            activity_subgroup_status = activity_subgroup.get("status")

            # filter_out_retired_groupings removes Activity Group/Subgroup pair if any of these is Retired
            if (
                LibraryItemStatus.RETIRED.value
                in (activity_subgroup_status, activity_group_status)
                and filter_out_retired_groupings
            ):
                continue

            activity_groupings.append(
                ActivityGroupingVO(
                    activity_group_uid=activity_group.get("uid"),
                    activity_group_name=activity_group.get("name"),
                    activity_group_version=f"{activity_group.get('major_version')}.{activity_group.get('minor_version')}",
                    activity_subgroup_uid=activity_subgroup.get("uid"),
                    activity_subgroup_name=activity_subgroup.get("name"),
                    activity_subgroup_version=f"{activity_subgroup.get('major_version')}.{activity_subgroup.get('minor_version')}",
                )
            )

        return ActivityAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=value.nci_concept_id,
                nci_concept_name=value.nci_concept_name,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                synonyms=value.synonyms or [],
                definition=value.definition,
                abbreviation=value.abbreviation,
                activity_groupings=activity_groupings,
                activity_instances=activity_root.get("activity_instances", []),
                request_rationale=value.request_rationale,
                is_request_final=(
                    value.is_request_final if value.is_request_final else False
                ),
                used_by_studies=activity_root["used_by_studies"],
                replaced_by_activity=activity_root["replaced_activity_uid"],
                reason_for_rejecting=value.reason_for_rejecting,
                contact_person=value.contact_person,
                is_request_rejected=(
                    value.is_request_rejected if value.is_request_rejected else False
                ),
                is_data_collected=(
                    value.is_data_collected if value.is_data_collected else False
                ),
                is_multiple_selection_allowed=(
                    value.is_multiple_selection_allowed
                    if value.is_multiple_selection_allowed is not None
                    else True
                ),
                is_finalized=bool(
                    value.is_request_rejected or activity_root["replaced_activity_uid"]
                ),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> ActivityAR:
        replaced_activity = value.replaced_by_activity.get_or_none()
        activity_groupings_nodes = value.has_grouping.all()
        activity_groupings = []
        activity_instances_legacy_codes = {}
        activity_instances = []
        _activity_instance_uids = set()
        for activity_grouping in activity_groupings_nodes:
            for instance_groupings_value in activity_grouping.has_activity.all():
                activity_instance_root = (
                    instance_groupings_value.has_version.single().has_grouping_root.single()
                )
                activity_instance_value = (
                    activity_instance_root.has_latest_value.single()
                )
                has_version = activity_instance_value.has_version
                for activity_instance_root in has_version.all():
                    if activity_instance_root.uid in _activity_instance_uids:
                        continue
                    _activity_instance_uids.add(activity_instance_root.uid)
                    activity_instances.append(
                        {
                            "uid": activity_instance_root.uid,
                            "name": activity_instance_value.name,
                        }
                    )

                    has_version_props = has_version.relationship(activity_instance_root)
                    if (
                        activity_instance_root
                        and has_version_props.status == "Final"
                        and has_version_props.end_date is None
                        and activity_instance_root.uid
                        not in activity_instances_legacy_codes
                    ):
                        activity_instances_legacy_codes[activity_instance_root.uid] = (
                            activity_instance_value.is_legacy_usage
                        )

            # ActivityGroup
            activity_group_value = activity_grouping.has_selected_group.single()
            activity_group_root = activity_group_value.has_version.single()
            all_group_rels = [
                has_version
                for has_version in activity_group_value.has_version.all_relationships(
                    activity_group_root
                )
                if has_version.status in ["Final", "Retired"]
            ]
            latest_group = max(
                all_group_rels, key=lambda r: version_string_to_tuple(r.version)
            )

            # ActivitySubGroup
            activity_subgroup_value = activity_grouping.has_selected_subgroup.single()
            activity_subgroup_root = activity_subgroup_value.has_version.single()
            all_subgroup_rels = [
                has_version
                for has_version in activity_subgroup_value.has_version.all_relationships(
                    activity_subgroup_root
                )
                if has_version.status in ["Final", "Retired"]
            ]
            latest_subgroup = max(
                all_subgroup_rels, key=lambda r: version_string_to_tuple(r.version)
            )

            activity_groupings.append(
                ActivityGroupingVO(
                    activity_group_uid=activity_group_root.uid,
                    activity_group_name=activity_group_value.name,
                    activity_group_version=latest_group.version,
                    activity_subgroup_uid=activity_subgroup_root.uid,
                    activity_subgroup_name=activity_subgroup_value.name,
                    activity_subgroup_version=latest_subgroup.version,
                )
            )
        used_by_studies: list[str] = []
        # We are only interested in the StudyId of the Activity Requests
        if library.name == settings.requested_library_name:
            query = """
                MATCH (ar:ActivityRoot {uid:$uid})-[:HAS_VERSION]->(:ActivityValue)<-[:HAS_SELECTED_ACTIVITY]-(sa:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(sv:StudyValue)
                WHERE NOT (sa)-[:BEFORE]-() AND NOT (sa)--(:Delete)
                WITH CASE sv.study_subpart_acronym
                    WHEN IS NULL THEN COALESCE(sv.study_id_prefix, '') + '-' + COALESCE(sv.study_number, '')
                    ELSE COALESCE(sv.study_id_prefix, '') + '-' + COALESCE(sv.study_number, '') + '-' + sv.study_subpart_acronym
                END AS study_id
                RETURN apoc.coll.toSet(apoc.coll.sort(collect(distinct study_id))) AS used_by_studies
            """
            result, _ = db.cypher_query(query, {"uid": root.uid})
            if result and len(result) > 0 and len(result[0]) > 0:
                used_by_studies = result[0][0] or []

        return ActivityAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=value.nci_concept_id,
                nci_concept_name=value.nci_concept_name,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                synonyms=value.synonyms or [],
                definition=value.definition,
                abbreviation=value.abbreviation,
                activity_groupings=activity_groupings,
                activity_instances=activity_instances,
                request_rationale=value.request_rationale,
                is_request_final=(
                    value.is_request_final if value.is_request_final else False
                ),
                used_by_studies=used_by_studies,
                replaced_by_activity=(
                    replaced_activity.uid if replaced_activity else None
                ),
                reason_for_rejecting=value.reason_for_rejecting,
                contact_person=value.contact_person,
                is_request_rejected=(
                    value.is_request_rejected if value.is_request_rejected else False
                ),
                is_data_collected=(
                    value.is_data_collected if value.is_data_collected else False
                ),
                is_multiple_selection_allowed=(
                    value.is_multiple_selection_allowed
                    if value.is_multiple_selection_allowed is not None
                    else True
                ),
                is_finalized=bool(value.is_request_rejected or replaced_activity),
                is_used_by_legacy_instances=(
                    all(activity_instances_legacy_codes.values())
                    if activity_instances_legacy_codes
                    else False
                ),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict[Any, Any]]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library, **kwargs)
        filter_parameters = []
        activity_subgroup_uid = kwargs.get("activity_subgroup_uid")
        activity_group_uid = kwargs.get("activity_group_uid")
        if kwargs.get("group_by_groupings") is False:
            activity_grouping_query_text = "activity_grouping"
        else:
            activity_grouping_query_text = (
                "concept_value)-[:HAS_GROUPING]->(activity_grouping:ActivityGrouping"
            )
        if activity_subgroup_uid and activity_group_uid:
            filter_by_subgroup_and_group_uid = f"""
            {{activity_subgroup_uid: $activity_subgroup_uid, activity_group_uid: $activity_group_uid}} IN
            [({activity_grouping_query_text}) |
            {{
                activity_subgroup_uid: head([(activity_grouping)-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)
                                            <-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | activity_subgroup_root.uid]),
                activity_group_uid: head([(activity_grouping)-[:HAS_SELECTED_GROUP]->(activity_group_value:ActivityGroupValue)
                                            <-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | activity_group_root.uid])
            }}
            ]"""
            filter_parameters.append(filter_by_subgroup_and_group_uid)
            filter_query_parameters["activity_subgroup_uid"] = activity_subgroup_uid
            filter_query_parameters["activity_group_uid"] = activity_group_uid
        if activity_subgroup_uid is not None and activity_group_uid is None:
            filter_by_activity_subgroup_uid = f"""
            $activity_subgroup_uid IN [({activity_grouping_query_text})-[:HAS_SELECTED_SUBGROUP]->
            (activity_subgroup_value:ActivitySubGroupValue)
            <-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | activity_subgroup_root.uid]"""
            filter_parameters.append(filter_by_activity_subgroup_uid)
            filter_query_parameters["activity_subgroup_uid"] = activity_subgroup_uid
        if activity_group_uid is not None and activity_subgroup_uid is None:
            filter_by_activity_group_uid = f"""
            $activity_group_uid IN [({activity_grouping_query_text})-[:HAS_SELECTED_GROUP]->
            (activity_group_value:ActivityGroupValue)
            <-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | activity_group_root.uid]"""
            filter_parameters.append(filter_by_activity_group_uid)
            filter_query_parameters["activity_group_uid"] = activity_group_uid
        if kwargs.get("activity_names") is not None:
            activity_names = kwargs.get("activity_names")
            filter_by_activity_names = "concept_value.name IN $activity_names"
            filter_parameters.append(filter_by_activity_names)
            filter_query_parameters["activity_names"] = activity_names
        if kwargs.get("activity_subgroup_names") is not None:
            activity_subgroup_names = kwargs.get("activity_subgroup_names")
            filter_by_activity_subgroup_names = f"""
            size([({activity_grouping_query_text})-[:HAS_SELECTED_SUBGROUP]->
            (asgv:ActivitySubGroupValue) WHERE asgv.name IN $activity_subgroup_names | asgv.name]) > 0"""
            filter_parameters.append(filter_by_activity_subgroup_names)
            filter_query_parameters["activity_subgroup_names"] = activity_subgroup_names
        if kwargs.get("activity_group_names") is not None:
            activity_group_names = kwargs.get("activity_group_names")
            filter_by_activity_group_names = f"""
            size([({activity_grouping_query_text})-[:HAS_SELECTED_GROUP]->
            (agv:ActivityGroupValue) WHERE agv.name IN $activity_group_names | agv.name]) > 0"""
            filter_parameters.append(filter_by_activity_group_names)
            filter_query_parameters["activity_group_names"] = activity_group_names
        extended_filter_statements = " AND ".join(filter_parameters)
        if filter_statements_from_concept != "":
            if len(extended_filter_statements) > 0:
                filter_statements_to_return = " AND ".join(
                    [filter_statements_from_concept, extended_filter_statements]
                )
            else:
                filter_statements_to_return = filter_statements_from_concept
        else:
            filter_statements_to_return = (
                "WHERE " + extended_filter_statements
                if len(extended_filter_statements) > 0
                else ""
            )
        return filter_statements_to_return, filter_query_parameters

    def _create_new_value_node(self, ar: ActivityAR) -> ActivityValue:
        value_node: ActivityValue = super()._create_new_value_node(ar=ar)
        value_node.synonyms = ar.concept_vo.synonyms  # type: ignore[assignment]
        if ar.concept_vo.request_rationale:
            value_node.request_rationale = ar.concept_vo.request_rationale
        value_node.is_request_final = ar.concept_vo.is_request_final
        if ar.concept_vo.reason_for_rejecting:
            value_node.reason_for_rejecting = ar.concept_vo.reason_for_rejecting
        if ar.concept_vo.contact_person:
            value_node.contact_person = ar.concept_vo.contact_person
        value_node.is_request_rejected = ar.concept_vo.is_request_rejected
        value_node.is_data_collected = ar.concept_vo.is_data_collected
        value_node.is_multiple_selection_allowed = (
            ar.concept_vo.is_multiple_selection_allowed
        )
        value_node.save()
        for activity_grouping in ar.concept_vo.activity_groupings:
            # create ActivityGrouping node
            activity_grouping_node = ActivityGrouping(
                uid=ActivityGrouping.get_next_free_uid_and_increment_counter()
            )
            activity_grouping_node.save()

            # link ActivityValue and ActivityGrouping nodes
            value_node.has_grouping.connect(activity_grouping_node)

            # link ActivityGrouping with ActivityGroupValue and ActivitySubGroupValue nodes
            group_node = ActivityGroupRoot.nodes.get(
                uid=activity_grouping.activity_group_uid
            ).has_latest_value.single()
            subgroup_node = ActivitySubGroupRoot.nodes.get(
                uid=activity_grouping.activity_subgroup_uid
            ).has_latest_value.single()
            activity_grouping_node.has_selected_subgroup.connect(subgroup_node)
            activity_grouping_node.has_selected_group.connect(group_node)

        return value_node

    def _any_subgroup_updated(self, activity_value):
        for grouping_node in activity_value.has_grouping.all():
            # If the linked subgroup is not the latest.
            # We need to return True, so that the ActivityValue
            # gets updated to use the new group and/or subgroup value.
            if not grouping_node.has_selected_group.get().has_latest_value.single():
                return True
            if not grouping_node.has_selected_subgroup.get().has_latest_value.single():
                return True
        return False

    def _has_data_changed(self, ar: ActivityAR, value: ActivityValue) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)
        are_props_changed = (
            ar.concept_vo.synonyms != value.synonyms
            or ar.concept_vo.request_rationale != value.request_rationale
            or ar.concept_vo.is_request_final != value.is_request_final
            or ar.concept_vo.reason_for_rejecting != value.reason_for_rejecting
            or ar.concept_vo.contact_person != value.contact_person
            or ar.concept_vo.is_request_rejected != value.is_request_rejected
            or ar.concept_vo.is_data_collected != value.is_data_collected
            or ar.concept_vo.is_multiple_selection_allowed
            != value.is_multiple_selection_allowed
        )

        activity_subgroup_uids = []
        activity_group_uids = []
        activity_grouping_nodes = value.has_grouping.all()
        for activity_grouping_node in activity_grouping_nodes:
            activity_group_value = activity_grouping_node.has_selected_group.single()
            activity_subgroup_value = (
                activity_grouping_node.has_selected_subgroup.single()
            )
            activity_subgroup_uids.append(
                activity_subgroup_value.has_version.single().uid
            )
            activity_group_uids.append(activity_group_value.has_version.single().uid)

        # Is this a final or retired version? If yes, we skip the check for updated subgroups
        # to avoid creating new values nodes when just creating a new draft.
        root_for_final_value = value.has_version.match(
            status__in=[LibraryItemStatus.FINAL.value, LibraryItemStatus.RETIRED.value],
            end_date__isnull=True,
        )
        if not root_for_final_value:
            subgroups_updated = self._any_subgroup_updated(value)
        else:
            subgroups_updated = False

        are_rels_changed = sorted(
            [
                activity_grouping.activity_group_uid
                for activity_grouping in ar.concept_vo.activity_groupings
            ]
        ) != sorted(activity_group_uids) or sorted(
            [
                activity_grouping.activity_subgroup_uid
                for activity_grouping in ar.concept_vo.activity_groupings
            ]
        ) != sorted(
            activity_subgroup_uids
        )
        return (
            are_concept_properties_changed
            or are_rels_changed
            or are_props_changed
            or subgroups_updated
        )

    def copy_activity_and_recreate_activity_groupings(
        self, activity: ActivityAR, author_id: str
    ) -> None:
        query = """
            MATCH (concept_root:ActivityRoot {uid:$activity_uid})-[status_relationship:LATEST]->(concept_value:ActivityValue)
            CALL apoc.refactor.cloneNodes([concept_value])
            YIELD input, output, error"""
        merge_query = f"""
            MERGE (concept_root)-[:LATEST]->(output)
            MERGE (concept_root)-[:LATEST_{activity.item_metadata.status.value.upper()}]->(output)
            MERGE (concept_root)-[new_has_version:HAS_VERSION]->(output)"""
        query += self._update_versioning_relationship_query(
            status=activity.item_metadata.status.value, merge_query=merge_query
        )
        query += """

            WITH library, concept_root, concept_value, output
            OPTIONAL MATCH (concept_value)-[:REPLACED_BY_ACTIVITY]->(replaced_by_activity:ActivityRoot)
            WITH library, concept_root, replaced_by_activity, output
            CALL apoc.do.case([
                replaced_by_activity IS NOT NULL,
                'MERGE (output)-[:REPLACED_BY_ACTIVITY]->(replaced_by_activity) RETURN output'
            ],
            '',
            {
                replaced_by_activity: replaced_by_activity,
                output: output
            })
            YIELD value
            UNWIND range(0, size($activity_group_uids)-1) AS idx
            CREATE (activity_grouping:ActivityGrouping)
            WITH library, concept_root, output, activity_grouping, idx
            MATCH (activity_group_value:ActivityGroupValue)<-[:LATEST]-(:ActivityGroupRoot {uid:$activity_group_uids[idx]})
            MATCH (activity_subgroup_value:ActivitySubGroupValue)<-[:LATEST]-(:ActivitySubGroupRoot {uid:$activity_subgroup_uids[idx]})
            WITH library, concept_root, output, activity_grouping, activity_subgroup_value, activity_group_value
            MERGE (activity_grouping)-[:HAS_SELECTED_GROUP]->(activity_group_value)
            MERGE (activity_grouping)-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value)
            MERGE (output)-[:HAS_GROUPING]->(activity_grouping)
            RETURN concept_root, output, library
        """

        _, _ = db.cypher_query(
            query,
            params={
                "activity_uid": activity.uid,
                "new_status": activity.item_metadata.status.value,
                "new_version": activity.item_metadata.version,
                "start_date": datetime.datetime.now(datetime.timezone.utc),
                "change_description": "Copying previous ActivityValue node and updating ActivityGrouping nodes",
                "author_id": author_id,
                "activity_subgroup_uids": [
                    activity.activity_subgroup_uid
                    for activity in activity.concept_vo.activity_groupings
                ],
                "activity_group_uids": [
                    activity.activity_group_uid
                    for activity in activity.concept_vo.activity_groupings
                ],
            },
        )

    @classmethod
    def format_filter_sort_keys(cls, key: str) -> str:
        """
        Maps a fieldname as provided by the API query (equal to output model) to the same fieldname as defined in the database and/or Cypher query

        :param key: Fieldname to map
        :return str:
        """
        if key.startswith("activity_groupings[0]."):
            splitted = key.split(".")
            activity_groupings_part = splitted[0]
            prop = splitted[1]
            if prop == "activity_group_name":
                return f"{activity_groupings_part}.activity_group.name"
            if prop == "activity_subgroup_name":
                return f"{activity_groupings_part}.activity_subgroup.name"
        if key in [
            "activity_group_uid",
            "activity_group_name",
            "activity_subgroup_uid",
            "activity_subgroup_name",
        ]:
            _split = key.rsplit("_", 1)
            return f"{_split[0]}.{_split[1]}"
        return key

    def specific_alias_clause(self, **kwargs) -> str:
        # concept_value property comes from the main part of the query
        # which is specified in the concept_generic_repository

        if kwargs.get("group_by_groupings") is False:
            activity_grouping_query_text = "activity_grouping"
        else:
            activity_grouping_query_text = (
                "concept_value)-[:HAS_GROUPING]->(activity_grouping:ActivityGrouping"
            )

        # check if sorting by activity group/subgroup name is requested
        grouping_sort_clause = ""
        sort_by = self.sort_by or {}
        group_desc = sort_by.get("activity_groupings[0].activity_group_name")
        subgroup_desc = sort_by.get("activity_groupings[0].activity_subgroup_name")
        if subgroup_desc is not None or group_desc is not None:
            orderings = []
            if group_desc is not None:
                if group_desc:
                    orderings.append("group.name DESC")
                else:
                    orderings.append("group.name")
            if subgroup_desc is not None:
                if subgroup_desc:
                    orderings.append("subgroup.name DESC")
                else:
                    orderings.append("subgroup.name")
            grouping_sort_clause = f"ORDER BY {', '.join(orderings)}"

        return f"""
        WITH *,
            concept_value.synonyms AS synonyms,
            concept_value.request_rationale AS request_rationale,
            coalesce(concept_value.is_request_final, false) AS is_request_final,
            coalesce(concept_value.is_request_rejected, false) AS is_request_rejected,
            concept_value.contact_person AS contact_person,
            concept_value.reason_for_rejecting AS reason_for_rejecting,
            CASE
                WHEN library_name='Requested'
                THEN apoc.coll.toSet(apoc.coll.sort(
                [(concept_root)-[:HAS_VERSION]->(:{self.value_class.__label__})<-[:HAS_SELECTED_ACTIVITY]->(sa:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value:StudyValue)
                       WHERE NOT (sa)-[:BEFORE]-() AND NOT (sa)--(:Delete) | COALESCE(study_value.study_id_prefix, '') + "-" + COALESCE(study_value.study_number, '') +
                        CASE WHEN study_value.study_subpart_acronym IS NOT NULL AND study_value.study_subpart_acronym <> '' THEN "-" + study_value.study_subpart_acronym ELSE "" END]))
                ELSE []
            END AS used_by_studies,
            coalesce(concept_value.is_data_collected, False) AS is_data_collected,
            coalesce(concept_value.is_multiple_selection_allowed, True) AS is_multiple_selection_allowed,
            COLLECT {{
                MATCH (concept_value)-[:HAS_GROUPING]->(activity_grouping:ActivityGrouping)
                MATCH (activity_grouping)-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)
                MATCH (activity_grouping)-[:HAS_SELECTED_GROUP]->(activity_group_value:ActivityGroupValue)
                WITH activity_subgroup_value, activity_group_value
                WITH
                    head(apoc.coll.sortMulti([(activity_subgroup_value:ActivitySubGroupValue)
                        <-[has_version:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) WHERE has_version.status='Final'
                            | {{
                                uid:activity_subgroup_root.uid,
                                major_version: toInteger(split(has_version.version,'.')[0]),
                                minor_version: toInteger(split(has_version.version,'.')[1]),
                                name:activity_subgroup_value.name
                        }}], ['major_version', 'minor_version'])) AS subgroup,
                    head(apoc.coll.sortMulti([(activity_group_value)
                        <-[has_version:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) WHERE has_version.status='Final'
                            | {{
                                uid:activity_group_root.uid,
                                major_version: toInteger(split(has_version.version,'.')[0]),
                                minor_version: toInteger(split(has_version.version,'.')[1]),
                                name:activity_group_value.name
                        }}], ['major_version', 'minor_version'])) AS group
                WITH subgroup, group {grouping_sort_clause}
                WITH {{activity_group: group, activity_subgroup: subgroup}} AS grouping
                RETURN grouping
            }} AS activity_groupings,

            apoc.coll.toSet([({activity_grouping_query_text})<-[:HAS_ACTIVITY]-(activity_instance_groupings_value:ActivityInstanceGroupingValue)
                <-[groupings_has_version:HAS_VERSION]-(activity_instance_groupings_root:ActivityInstanceGroupingRoot)
                <-[:HAS_GROUPING_ROOT]-(activity_instance_root:ActivityInstanceRoot)-[:LATEST]->(activity_instance_value:ActivityInstanceValue)
                | {{uid: activity_instance_root.uid, name: activity_instance_value.name}}]) AS activity_instances,

            head([(concept_value)-[:REPLACED_BY_ACTIVITY]->(replacing_activity_root:ActivityRoot) | replacing_activity_root.uid]) AS replaced_by_activity,

            apoc.coll.sortMulti([({activity_grouping_query_text})<-[:HAS_ACTIVITY]-(activity_instance_groupings_value:ActivityInstanceGroupingValue)
                <-[groupings_has_version:HAS_VERSION]-(activity_instance_groupings_root:ActivityInstanceGroupingRoot)
                <-[:HAS_GROUPING_ROOT]-(activity_instance_root:ActivityInstanceRoot)-[instance_version:HAS_VERSION WHERE instance_version.status='Final' and instance_version.end_date IS NULL]->(activity_instance_value:ActivityInstanceValue) |
                {{
                    uid:activity_instance_root.uid,
                    legacy_code:activity_instance_value.is_legacy_usage,
                    major_version: toInteger(split(instance_version.version,'.')[0]),
                    minor_version: toInteger(split(instance_version.version,'.')[1])
                }}], ['^uid', 'major_version', 'minor_version']) AS all_legacy_codes

            WITH *,
                // Sort by uid and instance_version in descending order and leave only latest version of same ActivityInstances
                [
                    i in range(0, size(all_legacy_codes) -1)
                    WHERE i=0 OR all_legacy_codes[i].uid <> all_legacy_codes[i-1].uid | all_legacy_codes[i].legacy_code ] as all_legacy_codes

            WITH *,
                CASE
                WHEN NOT is_request_rejected and replaced_by_activity IS NULL THEN false
                ELSE true
                END as is_finalized,
                CASE WHEN size(all_legacy_codes) > 0
                    THEN all(is_legacy_usage IN all_legacy_codes where is_legacy_usage=true and is_legacy_usage IS NOT NULL)
                    ELSE false
                END as is_used_by_legacy_instances
            """

    def replace_request_with_sponsor_activity(
        self, activity_request_uid: str, sponsor_activity_uid: str
    ) -> None:
        replace_activity_request_with_sponsor_activity_query = """
            MATCH (:ActivityRoot {uid: $activity_request_uid})-[:LATEST]->(activity_request_value:ActivityValue)
            MATCH (replacing_activity_root:ActivityRoot {uid: $sponsor_activity_uid})
            WITH activity_request_value, replacing_activity_root
            MERGE (activity_request_value)-[:REPLACED_BY_ACTIVITY]->(replacing_activity_root)
        """
        db.cypher_query(
            replace_activity_request_with_sponsor_activity_query,
            {
                "activity_request_uid": activity_request_uid,
                "sponsor_activity_uid": sponsor_activity_uid,
            },
        )

    def final_or_replaced_retired_activity_exists(self, uid: str) -> bool:
        query = f"""
            MATCH (concept_root:{self.root_class.__label__} {{uid: $uid}})-[:LATEST_FINAL]->(concept_value)
            RETURN concept_root
            """
        result, _ = db.cypher_query(query, {"uid": uid})
        exists = len(result) > 0 and len(result[0]) > 0
        if not exists:
            query = f"""
                MATCH (concept_root:{self.root_class.__label__} {{uid: $uid}})-[:LATEST_RETIRED]->(concept_value)
                -[:REPLACED_BY_ACTIVITY]->(:ActivityRoot)
                RETURN concept_root
                """
            result, _ = db.cypher_query(query, {"uid": uid})
            exists = len(result) > 0 and len(result[0]) > 0
        return exists

    def get_activity_overview(
        self, uid: str, version: str | None = None
    ) -> dict[str, Any]:
        if version:
            params = {"uid": uid, "version": version}
            match = """
                MATCH (activity_root:ActivityRoot {uid:$uid})
                CALL (activity_root) {
                        MATCH (activity_root)-[hv:HAS_VERSION {version:$version}]->(av:ActivityValue)
                        WITH hv, av
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs, collect (av) as avs
                        RETURN last(hvs) as has_version, last(avs) as activity_value
                    }
                """
        else:
            params = {"uid": uid}
            match = """
                    MATCH (activity_root:ActivityRoot {uid:$uid})-[:LATEST]->(activity_value:ActivityValue)
                    CALL (activity_root, activity_value) {
                        MATCH (activity_root)-[hv:HAS_VERSION]-(activity_value)
                        WITH hv
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs
                        RETURN last(hvs) as has_version
                    }
                    """
        query = match + """
            WITH DISTINCT
                activity_root,activity_value, has_version,
                head([(library)-[:CONTAINS_CONCEPT]->(activity_root) | library.name]) AS activity_library_name,
                [(activity_root)-[versions:HAS_VERSION]->(:ActivityValue) | versions.version] as all_versions,
                apoc.coll.sortMulti([(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-
                    (activity_instance_groupings_value:ActivityInstanceGroupingValue)<-[aighv:HAS_VERSION]-(activity_instance_groupings_root:ActivityInstanceGroupingRoot)-[:HAS_GROUPING_ROOT]-(activity_instance_root:ActivityInstanceRoot)
                    -[aihv:HAS_VERSION]->(activity_instance_value:ActivityInstanceValue)
                    WHERE NOT EXISTS ((activity_instance_value)<--(:DeletedActivityInstanceRoot)) 
                        AND datetime(has_version.start_date) <= datetime(aihv.start_date)
                        AND (has_version.end_date IS NULL OR datetime(has_version.end_date) > datetime(aihv.start_date))
                    | {
                        activity_instance_library_name: head([(library)-[:CONTAINS_CONCEPT]->(activity_instance_root) | library.name]),
                        uid: activity_instance_root.uid,
                        version: 
                            {
                                major_version: toInteger(split(aihv.version,'.')[0]),
                                minor_version: toInteger(split(aihv.version,'.')[1]),
                                status:aihv.status
                            },
                        name:activity_instance_value.name,
                        name_sentence_case:activity_instance_value.name_sentence_case,
                        abbreviation:activity_instance_value.abbreviation,
                        definition:activity_instance_value.definition,
                        adam_param_code:activity_instance_value.adam_param_code,
                        is_required_for_activity:coalesce(activity_instance_value.is_required_for_activity, false),
                        is_default_selected_for_activity:coalesce(activity_instance_value.is_default_selected_for_activity, false),
                        is_data_sharing:coalesce(activity_instance_value.is_data_sharing, false),
                        is_legacy_usage:coalesce(activity_instance_value.is_legacy_usage, false),
                        is_derived:coalesce(activity_instance_value.is_derived, false),
                        topic_code:activity_instance_value.topic_code,
                        activity_instance_class: head([(activity_instance_value)-[:ACTIVITY_INSTANCE_CLASS]->(activity_instance_class_root:ActivityInstanceClassRoot)
                            -[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue) | activity_instance_class_value])
                    }], ['^uid', 'version.major_version', 'version.minor_version']) AS activity_instances,
                apoc.coll.toSet([(activity_value)-[:HAS_GROUPING]->(activity_grouping:ActivityGrouping)
                    | {
                        activity_subgroup_value: head([(activity_grouping)-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)
                            | activity_subgroup_value]),
                        activity_subgroup_uid: head([(activity_grouping)-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)
                            <-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | activity_subgroup_root.uid]),
                        activity_group_value: head([(activity_grouping)-[:HAS_SELECTED_GROUP]->(activity_group_value:ActivityGroupValue)
                            | activity_group_value]),
                        activity_group_uid: head([(activity_grouping)-[:HAS_SELECTED_GROUP]->(activity_group_value:ActivityGroupValue)
                            <-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | activity_group_root.uid])
                    }]) AS hierarchy
            CALL (has_version) {
                OPTIONAL MATCH (author:User)
                WHERE author.user_id = has_version.author_id
                RETURN author
            }
            WITH *,
                has_version {
                    .*,
                    author_username: coalesce(author.username, has_version.author_id)
                } AS has_version
            RETURN
                hierarchy,
                activity_root,
                activity_value,
                activity_library_name,
                apoc.coll.sortMaps(activity_instances, '^name') as activity_instances,
                has_version,
                apoc.coll.dropDuplicateNeighbors(
                  [v in apoc.coll.sortMulti(
                    [v in all_versions | {
                      version: v,
                      major: toInteger(split(v, '.')[0]),
                      minor: toInteger(split(v, '.')[1])
                    }],
                    ['major', 'minor']
                  ) | v.version]
                ) AS all_versions
            """
        result_array, attribute_names = db.cypher_query(query=query, params=params)
        BusinessLogicException.raise_if(
            len(result_array) != 1,
            msg=f"The overview query returned broken data: {result_array}",
        )
        overview = result_array[0]
        overview_dict = {}
        for overview_prop, attribute_name in zip(overview, attribute_names):
            overview_dict[attribute_name] = overview_prop
        return overview_dict

    def get_cosmos_activity_overview(self, uid: str) -> dict[str, Any]:
        query = """
        MATCH (activity_root:ActivityRoot {uid:$uid})-[:LATEST]->(activity_value:ActivityValue)
        WITH DISTINCT activity_root,activity_value,
            apoc.coll.toSet([(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-
            (activity_instance_groupings_value:ActivityInstanceGroupingValue)<-[:HAS_VERSION]-(activity_instance_groupings_root:ActivityInstanceGroupingRoot)
            <-[:HAS_GROUPING_ROOT]-(activity_instance_root:ActivityInstanceRoot)-[:LATEST]->(activity_instance_value:ActivityInstanceValue)
            -[:ACTIVITY_INSTANCE_CLASS]->
            (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue)
            WHERE NOT EXISTS ((activity_instance_value)<--(:DeletedActivityInstanceRoot))
                AND (:ActivityInstanceRoot)-[:HAS_VERSION {end_date: null}]->(activity_instance_value)
            | {
                name:activity_instance_value.name,
                nci_concept_id:activity_instance_value.nci_concept_id,
                abbreviation:activity_instance_value.abbreviation,
                definition:activity_instance_value.definition,
                activity_instance_class_name: activity_instance_class_value.name
            }]) AS activity_instances,
            [(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value.name] AS activity_subgroups
        WITH activity_root, activity_value,
            activity_subgroups,
            apoc.coll.sortMaps(activity_instances, '^name') as activity_instances
        OPTIONAL MATCH (activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-
            (activity_instance_groupings_value:ActivityInstanceGroupingValue)<-[:HAS_VERSION]-(activity_instance_groupings_root:ActivityInstanceGroupingRoot)
            <-[:HAS_GROUPING_ROOT]-(activity_instance_root:ActivityInstanceRoot)-[:LATEST]->(activity_instance_value:ActivityInstanceValue)-[:CONTAINS_ACTIVITY_ITEM]->
            (activity_item:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(activity_item_class_root:ActivityItemClassRoot)-[:LATEST]->
            (activity_item_class_value:ActivityItemClassValue)
        OPTIONAL MATCH (activity_item)-[]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(CTTermAttributesRoot)-[:LATEST]->(activity_item_term_attr_value)
        OPTIONAL MATCH (activity_item)-[:HAS_UNIT_DEFINITION]->(:UnitDefinitionRoot)-[:LATEST]->(unit_def:UnitDefinitionValue)
        WITH activity_root, activity_value,
            activity_item_class_value,
            activity_instances,
            activity_subgroups,
            CASE WHEN size(collect(activity_item)) > 0 THEN
            apoc.map.fromPairs([
                ['nci_concept_id', activity_item_class_value.nci_concept_id],
                ['name', activity_item_class_value.name],
                ['type', head([(activity_item_class_value)-[:HAS_DATA_TYPE]->(ct_term_context:CTTermContext)
                    -[:HAS_SELECTED_TERM]->(data_type_root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(data_type_term_attr_root)-[:LATEST]->(data_type_term_attr_value) | data_type_term_attr_value.preferred_term])],
                ['example_set', collect(distinct(coalesce(activity_item_term_attr_value.submission_value, unit_def.name)))]
            ]) ELSE null
            END
            AS activity_items
        RETURN
            activity_subgroups,
            {
                uid: activity_root.uid,
                name: activity_value.name,
                name_sentence_case: activity_value.name_sentence_case,
                definition: activity_value.definition,
                abbreviation: activity_value.abbreviation,
                nci_concept_id: activity_value.nci_concept_id
            } AS activity_value,
            activity_instances,
            collect(activity_items) AS activity_items
        """
        result_array, attribute_names = db.cypher_query(
            query=query, params={"uid": uid}
        )
        BusinessLogicException.raise_if(
            len(result_array) != 1,
            msg=f"The overview query returned broken data: {result_array}",
        )
        return {
            attribute_name: result_array[0][index]
            for index, attribute_name in enumerate(attribute_names)
        }

    def generic_match_clause(self, **kwargs):
        concept_label = self.root_class.__label__
        concept_value_label = self.value_class.__label__
        query = f"""CYPHER runtime=slotted MATCH (concept_root:{concept_label})-[:LATEST]->(concept_value:{concept_value_label})
        """
        # IF group_by_groupings false THEN add grouping granularity
        if kwargs.get("group_by_groupings") is False:
            # OPTIONAL because not all activities have groupings
            query += """OPTIONAL MATCH (concept_value)-[:HAS_GROUPING]->(activity_grouping:ActivityGrouping)
                MATCH (concept_value)
            """
        return query

    def generic_alias_clause(self, **kwargs):
        return f"""
            DISTINCT concept_root, concept_value, {"activity_grouping," if kwargs.get("group_by_groupings") is False else ""}
            head([(library)-[:CONTAINS_CONCEPT]->(concept_root) | library]) AS library
            CALL (concept_root, concept_value) {{
                MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS version_rel
            }}
            CALL (version_rel) {{
                OPTIONAL MATCH (author: User)
                WHERE author.user_id = version_rel.author_id
                RETURN author
            }}
            WITH
                {"activity_grouping," if kwargs.get("group_by_groupings") is False else ""}
                concept_root.uid AS uid,
                concept_root,
                concept_value.nci_concept_id AS nci_concept_id,
                concept_value.nci_concept_name AS nci_concept_name,
                concept_value.name AS name,
                concept_value.name_sentence_case AS name_sentence_case,
                concept_value.external_id AS external_id,
                concept_value.definition AS definition,
                concept_value.abbreviation AS abbreviation,
                CASE WHEN concept_value:TemplateParameterTermValue THEN true ELSE false END AS template_parameter,
                library.name AS library_name,
                library.is_editable AS is_library_editable,
                version_rel.start_date AS start_date,
                version_rel.end_date AS end_date,
                version_rel.status AS status,
                version_rel.version AS version,
                version_rel.change_description AS change_description,
                version_rel.author_id AS author_id,
                coalesce(author.username, version_rel.author_id) AS author_username,
                concept_value
        """

    def generic_match_clause_all_versions(self):
        return """
            MATCH (concept_root:ActivityRoot)-[version:HAS_VERSION]->(concept_value:ActivityValue)
                    -[:HAS_GROUPING]->(ag:ActivityGrouping)
                    -[:HAS_SELECTED_SUBGROUP]->(subgroup_val:ActivitySubGroupValue)<-[:HAS_VERSION]-(subgroup_root:ActivitySubGroupRoot)
            WITH *
            MATCH (ag)-[:HAS_SELECTED_GROUP]->(group_value:ActivityGroupValue)<-[:HAS_VERSION]-(group_root:ActivityGroupRoot)
        """

    def is_multiple_selection_allowed_for_activity(self, activity_uid: str) -> bool:
        query = """
            MATCH (activity_root:ActivityRoot {uid: $activity_uid})-[:LATEST_FINAL]->(activity_value)
            RETURN coalesce(activity_value.is_multiple_selection_allowed, true)
            """
        result, _ = db.cypher_query(query, {"activity_uid": activity_uid})
        is_multiple_selection_allowed_for_activity = (
            len(result) > 0 and len(result[0]) > 0
        )
        return is_multiple_selection_allowed_for_activity

    def get_linked_upgradable_activity_instances(
        self, uid: str, version: str | None = None
    ) -> dict[Any, Any] | None:
        # Get "upgradable" linked activity instance values.
        # These are the instance values that have no end date,
        # meaning that the linked value is the latest version of the instance.
        params = {"uid": uid}
        if version:
            params["version"] = version
            match = """
                MATCH (activity_root:ActivityRoot {uid:$uid})-[hv:HAS_VERSION {version:$version}]->(activity_value:ActivityValue)
                WITH DISTINCT activity_root, activity_value
                """
        else:
            match = """
                MATCH (activity_root:ActivityRoot {uid:$uid})-[:LATEST]->(activity_value:ActivityValue)
                """

        query = match + """
        MATCH (activity_value)-[:HAS_GROUPING]->(activity_grouping:ActivityGrouping)<-[:HAS_ACTIVITY]-
            (activity_instance_groupings_value:ActivityInstanceGroupingValue)<-[aighv:HAS_VERSION]-(activity_instance_groupings_root:ActivityInstanceGroupingRoot)
            <-[:HAS_GROUPING_ROOT]-(activity_instance_root:ActivityInstanceRoot)
        OPTIONAL MATCH (activity_grouping)-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
        OPTIONAL MATCH (activity_grouping)-[:HAS_SELECTED_GROUP]->(activity_group_value:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
        WITH DISTINCT activity_root, activity_value, activity_instance_root, activity_instance_groupings_root, aighv, COLLECT(DISTINCT {
            activity_uid: activity_root.uid,
            activity_group_uid: activity_group_root.uid,
            activity_subgroup_uid: activity_subgroup_root.uid
        }) AS activity_groupings
        WHERE aighv.end_date IS NULL AND NOT EXISTS ((activity_instance_groupings_root)<--(:DeletedActivityInstanceRoot))
        WITH *,
            {
                activity_instance_library_name: head([(library)-[:CONTAINS_CONCEPT]->(activity_instance_root) | library.name]),
                uid: activity_instance_root.uid,
                version: 
                    {
                        major_version: toInteger(split(aighv.version,'.')[0]),
                        minor_version: toInteger(split(aighv.version,'.')[1]),
                        status:aighv.status
                    },
                activity_groupings: activity_groupings
            } AS activity_instance ORDER BY activity_instance.uid
        RETURN
            collect(activity_instance) as activity_instances
        """
        result_array, attribute_names = db.cypher_query(query=query, params=params)
        if len(result_array) == 0:
            return None
        BusinessLogicException.raise_if(
            len(result_array) > 1,
            msg=f"The linked instances query returned broken data: {result_array}",
        )
        instances = result_array[0]
        instances_dict = {}
        for instances_prop, attribute_name in zip(instances, attribute_names):
            instances_dict[attribute_name] = instances_prop
        return instances_dict

    def get_activity_uids_by_synonyms(self, synonyms: list[str]):
        if not synonyms:
            return {}

        rs = db.cypher_query(
            """
                MATCH (r:ActivityRoot)-[:LATEST]->(v:ActivityValue)
                WHERE NOT (:Library {name: $library_name})-[:CONTAINS_CONCEPT]->(r)
                      AND ANY(value IN $syn WHERE value IN v.synonyms)
                RETURN r.uid, [value IN $syn WHERE value IN v.synonyms] as existingSynonyms
            """,
            params={"syn": synonyms, "library_name": settings.archived_library_name},
        )

        if not rs[0]:
            return {}

        return {item[0]: item[1] for item in rs[0]}

    def get_all_versions_with_instances(
        self,
        activity_uid: str,
    ) -> list[dict[str, Any]]:
        """
        For a given activity, find all ActivityValue nodes and their latest Final
        version number. For each, find all linked instances with minimal info
        (uid, name, topic_code) and their groupings (group/subgroup uid and name).

        Returns:
            A list of dicts, each with 'version' and 'instances' keys,
            ordered by version number descending.
        """
        query = """
            // Find each ActivityValue with its latest Final version number
            MATCH (ar:ActivityRoot {uid: $uid})-[hv:HAS_VERSION]->(av:ActivityValue)
            WHERE hv.status = 'Final'
            WITH av, hv
            ORDER BY toInteger(split(hv.version, '.')[0]) DESC,
                     toInteger(split(hv.version, '.')[1]) DESC
            WITH av, collect(hv.version) AS final_versions
            WITH av, final_versions[0] AS version_number

            // For each activity version, find linked instances with grouping info
            CALL (av) {
                MATCH (av)-[:HAS_GROUPING]->(agrp:ActivityGrouping)
                MATCH (agrp)-[:HAS_SELECTED_GROUP]->(gv:ActivityGroupValue)<-[:HAS_VERSION]-(gr:ActivityGroupRoot)
                MATCH (agrp)-[:HAS_SELECTED_SUBGROUP]->(sgv:ActivitySubGroupValue)<-[:HAS_VERSION]-(sgr:ActivitySubGroupRoot)
                MATCH (agrp)<-[:HAS_ACTIVITY]-(aigv:ActivityInstanceGroupingValue)
                    <-[ghv:HAS_VERSION]-(aigr:ActivityInstanceGroupingRoot)
                    <-[:HAS_GROUPING_ROOT]-(air:ActivityInstanceRoot)
                // Exclude instances whose latest groupings version is Retired
                CALL (aigr) {
                    MATCH (aigr)-[latest_ghv:HAS_VERSION]->()
                    RETURN latest_ghv
                    ORDER BY latest_ghv.start_date DESC
                    LIMIT 1
                }
                WITH air, agrp, aigv, ghv, gr, gv, sgr, sgv
                WHERE latest_ghv.status <> 'Retired'
                // Get the latest valid instance version
                CALL (air, ghv) {
                    MATCH (air)-[aiv_hv:HAS_VERSION]->(aiv:ActivityInstanceValue)
                    WHERE NOT (aiv)<--(:DeletedActivityInstanceRoot)
                    AND (
                        (ghv.end_date IS NULL AND aiv_hv.end_date IS NULL)
                        OR (ghv.end_date IS NOT NULL AND aiv_hv.end_date IS NULL
                            AND datetime(aiv_hv.start_date) < datetime(ghv.end_date))
                        OR (ghv.end_date IS NULL AND aiv_hv.end_date IS NOT NULL
                            AND datetime(aiv_hv.end_date) > datetime(ghv.start_date))
                        OR (ghv.end_date IS NOT NULL AND aiv_hv.end_date IS NOT NULL
                            AND datetime(aiv_hv.start_date) < datetime(ghv.end_date)
                            AND datetime(aiv_hv.end_date) >= datetime(ghv.start_date))
                    )
                    RETURN aiv
                    ORDER BY aiv_hv.start_date DESC
                    LIMIT 1
                }
                // Collect groupings per instance, then instances
                WITH air.uid AS instance_uid, aiv.name AS instance_name, aiv.topic_code AS topic_code,
                     gr.uid AS group_uid, gv.name AS group_name,
                     sgr.uid AS subgroup_uid, sgv.name AS subgroup_name
                WITH instance_uid, instance_name, topic_code,
                     collect(DISTINCT {
                         activity_group_uid: group_uid,
                         activity_group_name: group_name,
                         activity_subgroup_uid: subgroup_uid,
                         activity_subgroup_name: subgroup_name
                     }) AS groupings
                RETURN collect({
                    uid: instance_uid,
                    name: instance_name,
                    topic_code: topic_code,
                    groupings: groupings
                }) AS instances
            }
            RETURN version_number, instances
            ORDER BY toInteger(split(version_number, '.')[0]) DESC,
                     toInteger(split(version_number, '.')[1]) DESC
        """

        results, _ = db.cypher_query(
            query=query,
            params={"uid": activity_uid},
            resolve_objects=False,
        )

        return [{"version": row[0], "instances": row[1]} for row in results]

    def get_specific_activity_version_groupings(
        self,
        uid: str,
        version: str,
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """
        Get activity groupings information for a specific version of an activity, including
        related subgroups, groups, and instances that existed during this version's validity period.
        """
        query = """
            // 1. Find the latest HAS_VERSION relationship for the specific version
            // (Multiple relationships can exist after inactivate/reactivate cycles)
            CALL {
                MATCH (ar:ActivityRoot {uid: $uid})-[av_rel:HAS_VERSION {version: $version}]->(av:ActivityValue)
                RETURN ar, av_rel, av
                ORDER BY av_rel.start_date DESC
                LIMIT 1
            }
MATCH (av)-[:HAS_GROUPING]->(agrp:ActivityGrouping)
CALL (agrp) {
    MATCH (agrp)-[:HAS_SELECTED_GROUP]->(gv:ActivityGroupValue)<-[:HAS_VERSION]-(gr:ActivityGroupRoot)
    MATCH (agrp)-[:HAS_SELECTED_SUBGROUP]->(sgv:ActivitySubGroupValue)<-[:HAS_VERSION]-(sgr:ActivitySubGroupRoot)
    RETURN DISTINCT sgv, sgr, gv, gr
}
CALL (sgv, sgr) {
    MATCH (sgr)-[hv:HAS_VERSION]->(sgv)
    WITH hv
    ORDER BY
        toInteger(split(hv.version, '.')[0]) ASC,
        toInteger(split(hv.version, '.')[1]) ASC,
        hv.end_date ASC,
        hv.start_date ASC
    WITH collect(hv) as hvs
    RETURN last(hvs) AS sg_ver
}
CALL (gv, gr) {
    MATCH (gr)-[hv:HAS_VERSION]->(gv)
    WITH hv
    ORDER BY
        toInteger(split(hv.version, '.')[0]) ASC,
        toInteger(split(hv.version, '.')[1]) ASC,
        hv.end_date ASC,
        hv.start_date ASC
    WITH collect(hv) as hvs
    RETURN last(hvs) AS g_ver
}
CALL (agrp) {
    MATCH (agrp)<-[:HAS_ACTIVITY]-(aigv:ActivityInstanceGroupingValue)
        <-[ghv:HAS_VERSION]-(:ActivityInstanceGroupingRoot)<-[:HAS_GROUPING_ROOT]-(air:ActivityInstanceRoot)-[hv:HAS_VERSION]->(aiv:ActivityInstanceValue)
    WHERE NOT EXISTS((aiv)<--(:DeletedActivityInstanceRoot))
        AND (
            // both versions are the latest: no further checks needed
            (ghv.end_date IS NULL AND hv.end_date IS NULL) 
            // grouping has an end date, instance is latest: instance start date is before grouping end date
            OR (ghv.end_date IS NOT NULL AND hv.end_date IS NULL AND datetime(hv.start_date) < datetime(ghv.end_date))
            // grouping has an end date, instance has an end date: instance start date is before grouping end date and instance end date is after grouping end date
            OR (ghv.end_date IS NOT NULL AND hv.end_date IS NOT NULL AND datetime(hv.start_date) < datetime(ghv.end_date) AND datetime(hv.end_date) >= datetime(ghv.end_date))
        )
    WITH aiv, hv, air
    ORDER BY hv.start_date
    WITH DISTINCT air, collect({aiv: aiv, version: hv.version}) AS aiv_versions
    WITH air, last(aiv_versions) AS last_aiv_version
    WITH DISTINCT last_aiv_version.aiv AS aiv, air, last_aiv_version.version AS instance_version
    WITH {instance_name: aiv.name, instance_uid: air.uid, instance_version: instance_version} AS instance
    RETURN collect(instance) AS activity_instances
}
RETURN
  ar.uid AS activity_uid, 
  av_rel.version AS activity_version, 
  agrp.uid AS valid_group_uid,
  sgr.uid AS subgroup_uid, 
  sgv.name AS subgroup_name, 
  sg_ver.version AS subgroup_version,
  sg_ver.status AS subgroup_status,
  gr.uid AS group_uid, 
  gv.name AS group_name, 
  g_ver.version AS group_version,
  g_ver.status AS group_status,
  activity_instances
            """

        result_array, _ = db.cypher_query(
            query=query, params={"uid": uid, "version": version}
        )

        # Process the result into a list of individual grouping dicts
        activity_groupings = []

        for row in result_array:
            (
                _,  # activity_uid (unused)
                _,  # activity_version (unused)
                valid_group_uid,
                subgroup_uid,
                subgroup_name,
                subgroup_version,
                subgroup_status,
                group_uid,
                group_name,
                group_version,
                group_status,
                activity_instances,
            ) = row

            # Process instances for this grouping
            group_instances = [
                {
                    "uid": instance["instance_uid"],
                    "name": instance["instance_name"],
                    "version": instance.get("instance_version"),
                }
                for instance in activity_instances
            ]

            activity_groupings.append(
                {
                    "valid_group_uid": valid_group_uid,
                    "subgroup": {
                        "uid": subgroup_uid,
                        "name": subgroup_name,
                        "version": subgroup_version,
                        "status": subgroup_status,
                    },
                    "group": {
                        "uid": group_uid,
                        "name": group_name,
                        "version": group_version,
                        "status": group_status,
                    },
                    "activity_instances": group_instances,
                }
            )

        total = len(activity_groupings) if total_count else 0

        # Apply pagination
        if page_size > 0:
            start_idx = (page_number - 1) * page_size
            end_idx = start_idx + page_size
            paginated_groupings = activity_groupings[start_idx:end_idx]
        else:
            paginated_groupings = activity_groupings

        return GenericFilteringReturn(items=paginated_groupings, total=total)

    def get_activity_instances_for_version(
        self,
        activity_uid: str,
        version: str | None,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[dict[Any, Any]], int]:
        """
        Retrieves a paginated list of activity instances that are linked to a specific
        activity version via HAS_ACTIVITY relationships.

        Only returns instance versions that have a direct HAS_ACTIVITY relationship to
        this activity's groupings. If an instance was later moved to a different activity,
        only the versions that were linked to THIS activity are returned.

        For each relevant activity instance, it returns the latest linked version as the
        parent, along with older linked versions as children.

        Args:
            activity_uid (str): The UID of the parent activity.
            version (str): The specific version of the parent activity (e.g., "16.0").
            skip (int): Number of records to skip for pagination (0-based).
            limit (int): Maximum number of records to return.

        Returns:
            tuple[list[dict], int]: A tuple containing the list of activity instance
                                    dictionaries and the total count of unique relevant instances.
        """
        # Ensure skip and limit are non-negative integers
        if not isinstance(skip, int) or skip < 0:
            skip = 0

        if not isinstance(limit, int) or limit < 0:
            # Default to a reasonable value for negative or invalid values
            limit = 10

        # Collect linked instances
        linked_instances_query = """
            MATCH (activity_root:ActivityRoot {uid: $uid})-[:HAS_VERSION {version: $version}]->(activity_value:ActivityValue)
            WITH activity_root, activity_value
            MATCH (activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-(:ActivityInstanceGroupingValue)<-[ghv:HAS_VERSION]-(:ActivityInstanceGroupingRoot)<-[:HAS_GROUPING_ROOT]-(ai_root:ActivityInstanceRoot)
            WITH DISTINCT ai_root, activity_value, collect(ghv) AS ghvs ORDER BY ai_root.uid
            CALL (ai_root, activity_value, ghvs) {
                UNWIND ghvs AS ghv
                MATCH (ai_root)-[hv:HAS_VERSION]->(aiv:ActivityInstanceValue)
                WHERE NOT (aiv)<--(:DeletedActivityInstanceRoot)
                AND (
                  // both versions are the latest: no further checks needed
                  (ghv.end_date IS NULL AND hv.end_date IS NULL) 
                  // grouping has an end date, instance is latest: instance start date is before grouping end date
                  OR (ghv.end_date IS NOT NULL AND hv.end_date IS NULL AND datetime(hv.start_date) < datetime(ghv.end_date))
                  // grouping is the latest, instance has an end date: instance end date is after grouping start date
                  OR (ghv.end_date IS NULL AND hv.end_date IS NOT NULL AND datetime(hv.end_date) > datetime(ghv.start_date))
                  // grouping has an end date, instance has an end date: instance start date is before grouping end date and instance end date is after grouping start date
                  OR (ghv.end_date IS NOT NULL AND hv.end_date IS NOT NULL AND datetime(hv.start_date) < datetime(ghv.end_date) AND datetime(hv.end_date) >= datetime(ghv.start_date))
                )
                OPTIONAL MATCH (aiv)-[:ACTIVITY_INSTANCE_CLASS]->(aic_root:ActivityInstanceClassRoot)-[:LATEST]->(aic_value:ActivityInstanceClassValue)
                WITH {uid: ai_root.uid, name: aiv.name, version: hv.version, activity_instance_class: {uid: aic_root.uid, name: aic_value.name}, status: hv.status, topic_code: aiv.topic_code, adam_param_code: aiv.adam_param_code} AS instance_info
                ORDER BY hv.start_date DESC
                WITH COLLECT(DISTINCT instance_info) AS instance_versions
                WITH instance_versions[0].uid AS uid,
                    instance_versions[0].name AS name,
                    instance_versions[0].version AS version,
                    instance_versions[0].activity_instance_class AS activity_instance_class,
                    instance_versions[0].status AS status,
                    instance_versions[0].topic_code AS topic_code,
                    instance_versions[0].adam_param_code AS adam_param_code,
                    instance_versions[1..] AS children
                RETURN *
            }
        """

        instances_return_query = """
            WITH {
                uid: uid,
                version: version,
                status: status,
                name: name,
                adam_param_code: adam_param_code,
                topic_code: topic_code,
                activity_instance_class: activity_instance_class,
                children: children
            } AS instance
            RETURN instance SKIP $skip LIMIT $limit
        """

        count_return_query = "RETURN count(uid) as total_count"

        count_query = linked_instances_query + count_return_query
        params: dict[str, str | int | None] = {"uid": activity_uid, "version": version}
        try:
            count_result, _ = db.cypher_query(
                query=count_query,
                params=params,
                resolve_objects=False,
            )
            if not count_result or not count_result[0]:
                # This case might mean the activity/version doesn't exist or has no linked instances
                return [], 0
            total_count = count_result[0][0]

            # Handle case where activity/version exists but no instances meet criteria
            if total_count == 0:
                return [], 0

        except IndexError:
            # Handle case where query returns empty results unexpectedly
            return [], 0
        except Exception as e:
            # Log error or raise a more specific exception
            print(f"Error executing count/end_date query: {e}")
            raise  # Re-raise for now, or handle appropriately

        # Query 2: Fetch details for paginated roots

        full_query = linked_instances_query + instances_return_query
        params.update({"skip": skip, "limit": limit})
        try:
            instances_results, _ = db.cypher_query(
                query=full_query, params=params, resolve_objects=False
            )
            instances = [row[0] for row in instances_results]
        except Exception as e:
            # Log error or raise a more specific exception
            print(f"Error executing details query: {e}")
            raise  # Re-raise for now, or handle appropriately

        return instances, total_count

    def get_activity_instances_for_version_deleteme(
        self,
        activity_uid: str,
        version: str | None,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[dict[Any, Any]], int]:
        """
        Retrieves a paginated list of activity instances that are linked to a specific
        activity version via HAS_ACTIVITY relationships.

        Only returns instance versions that have a direct HAS_ACTIVITY relationship to
        this activity's groupings. If an instance was later moved to a different activity,
        only the versions that were linked to THIS activity are returned.

        For each relevant activity instance, it returns the latest linked version as the
        parent, along with older linked versions as children.

        Args:
            activity_uid (str): The UID of the parent activity.
            version (str): The specific version of the parent activity (e.g., "16.0").
            skip (int): Number of records to skip for pagination (0-based).
            limit (int): Maximum number of records to return.

        Returns:
            tuple[list[dict], int]: A tuple containing the list of activity instance
                                    dictionaries and the total count of unique relevant instances.
        """
        # Ensure skip and limit are non-negative integers
        if not isinstance(skip, int) or skip < 0:
            skip = 0

        # Store original limit for pagination logic
        original_page_size = limit

        if not isinstance(limit, int) or limit < 0:
            # Default to a reasonable value for negative or invalid values
            limit = 10

        # Query 1: Calculate version_end_date and count total relevant roots
        count_and_end_date_query = """
            // 1a. Find the specific activity version
            MATCH (activity_root:ActivityRoot {uid: $uid})-[av_rel:HAS_VERSION {version: $version}]->(activity_value:ActivityValue)
            WITH activity_root, av_rel, activity_value

            // 1b. Find the minimum start date of subsequent versions (if any)
            OPTIONAL MATCH (activity_root)-[next_rel:HAS_VERSION]->(:ActivityValue)
            WHERE toInteger(split(next_rel.version, '.')[0]) > toInteger(split($version, '.')[0])
               OR (toInteger(split(next_rel.version, '.')[0]) = toInteger(split($version, '.')[0])
                   AND toInteger(split(next_rel.version, '.')[1]) > toInteger(split($version, '.')[1]))
            WITH activity_value, av_rel, min(next_rel.start_date) as min_next_start_date // Grouping implicitly by activity_value, av_rel

            // 1c. Calculate the final version_end_date
            WITH activity_value, av_rel.end_date as activity_end_date, COALESCE(av_rel.end_date, min_next_start_date, datetime()) as version_end_date

            // 2. Find distinct relevant ActivityInstance Roots and count them
            MATCH (activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-(:ActivityInstanceValue)<-[aihv_check:HAS_VERSION]-(ai_root:ActivityInstanceRoot)
            WHERE aihv_check.start_date <= version_end_date
              AND (activity_end_date IS NOT NULL OR aihv_check.end_date IS NULL)
            RETURN count(DISTINCT ai_root) as total_count, version_end_date, activity_end_date
        """
        params_count = {"uid": activity_uid, "version": version}
        try:
            count_result, _ = db.cypher_query(
                query=count_and_end_date_query,
                params=params_count,
                resolve_objects=False,
            )
            if not count_result or not count_result[0]:
                # This case might mean the activity/version doesn't exist or has no linked instances
                return [], 0
            total_count = count_result[0][0]
            version_end_date = count_result[0][1]  # Get the calculated end date
            activity_end_date = count_result[0][
                2
            ]  # Get activity version end date for filtering

            # Handle case where activity/version exists but no instances meet criteria
            if total_count == 0:
                return [], 0

        except IndexError:
            # Handle case where query returns empty results unexpectedly
            return [], 0
        except Exception as e:
            # Log error or raise a more specific exception
            print(f"Error executing count/end_date query: {e}")
            raise  # Re-raise for now, or handle appropriately

        # Query 2: Fetch details for paginated roots

        # Build pagination clause based on original page size
        pagination_clause = ""
        if original_page_size > 0:
            pagination_clause = f"""
            // 3. Apply Pagination to the distinct relevant roots
            ORDER BY ai_root.uid
            SKIP {skip}
            LIMIT {limit}
            """
        else:
            pagination_clause = """
            // 3. Apply ordering but no pagination (return all items)
            ORDER BY ai_root.uid
            """

        details_query = f"""
            // 1. Find the specific activity version's value node
            MATCH (activity_root:ActivityRoot {{uid: $uid}})-[:HAS_VERSION {{version: $version}}]->(activity_value:ActivityValue)
            WITH activity_value, $version_end_date as version_end_date, $activity_end_date as activity_end_date

            // 2. Find distinct relevant ActivityInstance Roots linked via groupings
            MATCH (activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-(:ActivityInstanceValue)<-[aihv_check:HAS_VERSION]-(ai_root:ActivityInstanceRoot)
            WHERE aihv_check.start_date <= version_end_date
              AND (activity_end_date IS NOT NULL OR aihv_check.end_date IS NULL)
            WITH DISTINCT ai_root, version_end_date, activity_value, activity_end_date
{pagination_clause}
            WITH ai_root, version_end_date, activity_value, activity_end_date

            // --- Instance Detail Fetching ---

            // 4. For each paginated root, find versions LINKED TO THIS ACTIVITY's groupings
            // This ensures we only get versions that have HAS_ACTIVITY relationship to this activity
            MATCH (activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-(ai_val:ActivityInstanceValue)<-[aihv:HAS_VERSION]-(ai_root)

            // 5. Filter versions active within the window & Order them
            WITH ai_root, aihv, ai_val, version_end_date, activity_value, activity_end_date
            WHERE aihv.start_date <= version_end_date
              AND (activity_end_date IS NOT NULL OR aihv.end_date IS NULL)
            WITH ai_root, aihv, ai_val, version_end_date, activity_value
            ORDER BY ai_root.uid, aihv.start_date DESC,
                     toInteger(split(aihv.version, '.')[0]) DESC,
                     toInteger(split(aihv.version, '.')[1]) DESC

            // 6. Collect the ordered versions per root
            WITH ai_root, version_end_date, activity_value, collect({{rel: aihv, val: ai_val}}) as relevant_versions_sorted

            // 7. Identify the specific version to display (the first in the sorted list)
            WITH DISTINCT ai_root, activity_value, relevant_versions_sorted[0] as display_instance_map // Map {{rel:..., val:...}}

            // 8. Get library info for the root
            OPTIONAL MATCH (library)-[:CONTAINS_CONCEPT]->(ai_root)

            // 9. Get ActivityInstanceClass for the display instance version node
            WITH ai_root, display_instance_map, library, activity_value, display_instance_map.val as display_instance_node
            OPTIONAL MATCH (display_instance_node)-[:ACTIVITY_INSTANCE_CLASS]->(:ActivityInstanceClassRoot)-[:LATEST]->(aic_value:ActivityInstanceClassValue)

            // 10. Find all *other* versions (children) that are LINKED TO THIS ACTIVITY
            WITH ai_root, display_instance_map, display_instance_node, library, aic_value, activity_value
            OPTIONAL MATCH (activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-(child_ai_val:ActivityInstanceValue)<-[child_aihv:HAS_VERSION]-(ai_root)
            WHERE child_aihv <> display_instance_map.rel AND
                  (child_aihv.start_date < display_instance_map.rel.start_date
                   OR (child_aihv.start_date = display_instance_map.rel.start_date
                       AND (toInteger(split(child_aihv.version, '.')[0]) < toInteger(split(display_instance_map.rel.version, '.')[0])
                            OR (toInteger(split(child_aihv.version, '.')[0]) = toInteger(split(display_instance_map.rel.version, '.')[0])
                                AND toInteger(split(child_aihv.version, '.')[1]) < toInteger(split(display_instance_map.rel.version, '.')[1])))))

            // 11. Get ActivityInstanceClass for children
            OPTIONAL MATCH (child_ai_val)-[:ACTIVITY_INSTANCE_CLASS]->(:ActivityInstanceClassRoot)-[:LATEST]->(child_aic_value:ActivityInstanceClassValue)

            // 12. Order children (newest first) and collect
            WITH ai_root, display_instance_map, library, aic_value, child_aihv, child_ai_val, child_aic_value
            ORDER BY child_aihv.start_date DESC,
                     toInteger(split(child_aihv.version, '.')[0]) DESC,
                     toInteger(split(child_aihv.version, '.')[1]) DESC
            WITH ai_root, display_instance_map, library, aic_value, collect(
                CASE WHEN child_aihv IS NULL THEN null ELSE {{
                    uid: ai_root.uid, version: child_aihv.version, status: child_aihv.status, name: child_ai_val.name,
                    definition: child_ai_val.definition, abbreviation: child_ai_val.abbreviation,
                    topic_code: child_ai_val.topic_code, adam_param_code: child_ai_val.adam_param_code,
                    activity_instance_class: CASE WHEN child_aic_value IS NULL THEN null ELSE {{ name: child_aic_value.name }} END
                }} END
            ) as children_data_list

            // 13. Format the final output map
            RETURN {{
                activity_instance_library_name: library.name, uid: ai_root.uid, version: display_instance_map.rel.version,
                status: display_instance_map.rel.status, name: display_instance_map.val.name,
                name_sentence_case: display_instance_map.val.name_sentence_case, abbreviation: display_instance_map.val.abbreviation,
                definition: display_instance_map.val.definition, adam_param_code: display_instance_map.val.adam_param_code,
                is_required_for_activity: coalesce(display_instance_map.val.is_required_for_activity, false),
                is_default_selected_for_activity: coalesce(display_instance_map.val.is_default_selected_for_activity, false),
                is_data_sharing: coalesce(display_instance_map.val.is_data_sharing, false),
                is_legacy_usage: coalesce(display_instance_map.val.is_legacy_usage, false),
                is_derived: coalesce(display_instance_map.val.is_derived, false),
                topic_code: display_instance_map.val.topic_code,
                activity_instance_class: CASE WHEN aic_value IS NULL THEN null ELSE {{ name: aic_value.name }} END,
                children: [c IN children_data_list WHERE c IS NOT NULL]
            }} AS instance
        """

        params_details = {
            "uid": activity_uid,
            "version": version,
            "version_end_date": version_end_date,
            "activity_end_date": activity_end_date,
        }

        try:
            instances_results, _ = db.cypher_query(
                query=details_query, params=params_details, resolve_objects=False
            )
            instances = [row[0] for row in instances_results]
        except Exception as e:
            # Log error or raise a more specific exception
            print(f"Error executing details query: {e}")
            raise  # Re-raise for now, or handle appropriately

        return instances, total_count

    def specific_header_match_clause_lite(self, field_name: str) -> str | None:
        """This is a lightweight version of the header match clause.
        It should fetch only the required field, without supporting wildcard filtering.
        """

        header_query: str | None = None
        # activities/activities/headers?field_name=is_used_by_legacy_instances
        if field_name == "is_used_by_legacy_instances":
            header_query = """
                WITH concept_value,
                apoc.coll.toSet([(concept_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-(activity_instance_value:ActivityInstanceValue)
                <-[has_version:HAS_VERSION]-(activity_instance_root:ActivityInstanceRoot) | {uid: activity_instance_root.uid, name: activity_instance_value.name}]) AS activity_instances,
                head([(concept_value)-[:REPLACED_BY_ACTIVITY]->(replacing_activity_root:ActivityRoot) | replacing_activity_root.uid]) AS replaced_by_activity,
                apoc.coll.sortMulti([(concept_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-(activity_instance_value:ActivityInstanceValue)
                    <-[instance_version:HAS_VERSION WHERE instance_version.status='Final' and instance_version.end_date IS NULL]-(activity_instance_root) |
                    {
                        uid:activity_instance_root.uid,
                        legacy_code:activity_instance_value.is_legacy_usage,
                        major_version: toInteger(split(instance_version.version,'.')[0]),
                        minor_version: toInteger(split(instance_version.version,'.')[1])
                    }], ['^uid', 'major_version', 'minor_version']) AS all_legacy_codes
                WITH *,
                    // Sort by uid and instance_version in descending order and leave only latest version of same ActivityInstances
                    [
                        i in range(0, size(all_legacy_codes) -1)
                        WHERE i=0 OR all_legacy_codes[i].uid <> all_legacy_codes[i-1].uid | all_legacy_codes[i].legacy_code ] as all_legacy_codes
                WITH *,
                    CASE WHEN size(all_legacy_codes) > 0
                        THEN all(is_legacy_usage IN all_legacy_codes where is_legacy_usage=true and is_legacy_usage IS NOT NULL)
                        ELSE false
                    END as is_used_by_legacy_instances
            """
        # activities/activities/headers?field_name=used_by_studies
        elif field_name == "used_by_studies":
            header_query = """WITH CASE
                WHEN exists((concept_root)<-[:CONTAINS_CONCEPT]-(:Library {name:'Requested'}))
                THEN apoc.coll.toSet(apoc.coll.sort([(concept_root)-[:HAS_VERSION]->(:ActivityValue)<-[:HAS_SELECTED_ACTIVITY]->(sa:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value:StudyValue)
                WHERE NOT (sa)-[:BEFORE]-() AND NOT (sa)--(:Delete) | COALESCE(study_value.study_id_prefix, '') + "-" + COALESCE(study_value.study_number, '') +
                        CASE WHEN study_value.study_subpart_acronym IS NOT NULL AND study_value.study_subpart_acronym <> '' THEN "-" + study_value.study_subpart_acronym ELSE "" END]))
                ELSE []
            END AS used_by_studies"""
        return header_query
