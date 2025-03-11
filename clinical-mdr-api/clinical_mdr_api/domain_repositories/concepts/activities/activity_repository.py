from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGrouping,
    ActivityRoot,
    ActivityValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
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
from common.config import REQUESTED_LIBRARY_NAME
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime


def _version_to_number(version: str) -> float:
    major, minor = version.split(".")
    return 1000 * float(major) + float(minor)


def _get_display_version(versions: list[dict]) -> dict | None:
    if len(versions) == 1:
        return versions[0]
    sorted_versions = sorted(
        versions, key=lambda x: _version_to_number(x["version"]), reverse=True
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
    filter_query_parameters = {}

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> ActivityAR:
        major, minor = input_dict.get("version").split(".")
        return ActivityAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=input_dict.get("nci_concept_id"),
                nci_concept_name=input_dict.get("nci_concept_name"),
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("name_sentence_case"),
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
                request_rationale=input_dict.get("request_rationale"),
                is_request_final=input_dict.get("is_request_final"),
                requester_study_id=input_dict.get("requester_study_id"),
                replaced_by_activity=input_dict.get("replaced_by_activity"),
                reason_for_rejecting=input_dict.get("reason_for_rejecting"),
                contact_person=input_dict.get("contact_person"),
                is_request_rejected=input_dict.get("is_request_rejected"),
                is_data_collected=input_dict.get("is_data_collected"),
                is_multiple_selection_allowed=input_dict.get(
                    "is_multiple_selection_allowed"
                ),
                is_finalized=input_dict.get("is_finalized"),
                is_used_by_legacy_instances=input_dict.get(
                    "is_used_by_legacy_instances"
                ),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict.get("library_name"),
                is_library_editable_callback=(
                    lambda _: input_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("change_description"),
                status=LibraryItemStatus(input_dict.get("status")),
                author_id=input_dict.get("author_id"),
                author_username=input_dict.get("author_username"),
                start_date=convert_to_datetime(value=input_dict.get("start_date")),
                end_date=convert_to_datetime(value=input_dict.get("end_date")),
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

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
        for activity_grouping in activity_root["activity_groupings"]:
            activity_group = activity_grouping["activity_group"]
            activity_subgroup = activity_grouping["activity_subgroup"]
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
                request_rationale=value.request_rationale,
                is_request_final=(
                    value.is_request_final if value.is_request_final else False
                ),
                requester_study_id=activity_root["requester_study_id"],
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
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> ActivityAR:
        replaced_activity = value.replaced_by_activity.get_or_none()
        activity_groupings_nodes = value.has_grouping.all()
        activity_groupings = []
        activity_instances_legacy_codes = {}
        for activity_grouping in activity_groupings_nodes:
            for activity_instance_value in activity_grouping.has_activity.all():
                has_version = activity_instance_value.has_version
                for activity_instance_root in has_version.all():
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

            activity_valid_groups = activity_grouping.in_subgroup.all()
            for activity_valid_group in activity_valid_groups:
                # ActivityGroup
                activity_group_value = activity_valid_group.in_group.get()
                activity_group_root = activity_group_value.has_version.single()
                all_group_rels = activity_group_value.has_version.all_relationships(
                    activity_group_root
                )
                latest_group = max(all_group_rels, key=lambda r: float(r.version))
                # ActivitySubGroup
                activity_subgroup_value = activity_valid_group.has_group.get()
                activity_subgroup_root = activity_subgroup_value.has_version.single()
                all_subgroup_rels = (
                    activity_subgroup_value.has_version.all_relationships(
                        activity_subgroup_root
                    )
                )
                latest_subgroup = max(all_subgroup_rels, key=lambda r: float(r.version))

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
        requester_study_id = None
        # We are only interested in the StudyId of the Activity Requests
        if library.name == REQUESTED_LIBRARY_NAME:
            if study_activity := value.has_selected_activity.single():
                if activity := study_activity.has_study_activity.single():
                    requester_study_id = (
                        f"{activity.study_id_prefix}-{activity.study_number}"
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
                request_rationale=value.request_rationale,
                is_request_final=(
                    value.is_request_final if value.is_request_final else False
                ),
                requester_study_id=requester_study_id,
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
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library)
        filter_parameters = []
        if (activity_subgroup_uid := kwargs.get("activity_subgroup_uid")) is not None:
            filter_by_activity_subgroup_uid = """
            $activity_subgroup_uid IN [(concept_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->
            (:ActivityValidGroup)<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue)
            <-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | activity_subgroup_root.uid]"""
            filter_parameters.append(filter_by_activity_subgroup_uid)
            filter_query_parameters["activity_subgroup_uid"] = activity_subgroup_uid
        if (activity_group_uid := kwargs.get("activity_group_uid")) is not None:
            filter_by_activity_group_uid = """
            $activity_group_uid IN [(concept_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->
            (:ActivityValidGroup)-[:IN_GROUP]->(activity_group_value:ActivityGroupValue)
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
            filter_by_activity_subgroup_names = """
            size([(concept_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->
            (:ActivityValidGroup)<-[:HAS_GROUP]-(asgv:ActivitySubGroupValue) WHERE asgv.name IN $activity_subgroup_names | asgv.name]) > 0"""
            filter_parameters.append(filter_by_activity_subgroup_names)
            filter_query_parameters["activity_subgroup_names"] = activity_subgroup_names
        if kwargs.get("activity_group_names") is not None:
            activity_group_names = kwargs.get("activity_group_names")
            filter_by_activity_group_names = """
            size([(concept_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->
            (:ActivityValidGroup)-[:IN_GROUP]->(agv:ActivityGroupValue) WHERE agv.name IN $activity_group_names | agv.name]) > 0"""
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
        value_node.synonyms = ar.concept_vo.synonyms
        value_node.request_rationale = ar.concept_vo.request_rationale
        value_node.is_request_final = ar.concept_vo.is_request_final
        value_node.reason_for_rejecting = ar.concept_vo.reason_for_rejecting
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

            # find related ActivityValidGroup node
            query = """
                MATCH (activity_valid_group:ActivityValidGroup)-[:IN_GROUP]-(agv:ActivityGroupValue)<-[:HAS_VERSION]-(agr:ActivityGroupRoot {uid:$activity_group_uid})
                MATCH (activity_valid_group)-[:HAS_GROUP]-(asgv:ActivitySubGroupValue)<-[:HAS_VERSION]-(asgr:ActivitySubGroupRoot {uid:$activity_subgroup_uid})
                WITH *, 
                    head([(asgv)<-[latest:LATEST]-(asgr) | latest]) AS is_subgroup_latest,
                    head([(agv)<-[latest:LATEST]-(agr) | latest]) AS is_group_latest
                RETURN activity_valid_group
                ORDER BY is_subgroup_latest, is_group_latest
            """
            activity_valid_groups_ret, _ = db.cypher_query(
                query,
                params={
                    "activity_group_uid": activity_grouping.activity_group_uid,
                    "activity_subgroup_uid": activity_grouping.activity_subgroup_uid,
                },
                resolve_objects=True,
            )
            BusinessLogicException.raise_if(
                len(activity_valid_groups_ret) == 0,
                msg=f"The ActivityValidGroup node wasn't found for Activity Subgroup '{activity_grouping.activity_subgroup_uid}' "
                f"and Activity Group '{activity_grouping.activity_group_uid}'.",
            )
            activity_valid_group_node = activity_valid_groups_ret[0][0]
            # link ActivityGrouping and ActivityValidGroup
            activity_grouping_node.in_subgroup.connect(activity_valid_group_node)

        return value_node

    def _any_subgroup_updated(self, activity_value):
        for grouping_node in activity_value.has_grouping.all():
            if (
                not grouping_node.in_subgroup.get()
                .has_group.get()
                .has_latest_value.single()
            ):
                # The linked subgroup is not the latest.
                # We need to return True, so that the ActivityValue
                # gets updated to use the new subgroup value.
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
            activity_valid_group_nodes = activity_grouping_node.in_subgroup.all()
            for activity_valid_group_node in activity_valid_group_nodes:
                activity_subgroup_uids.append(
                    activity_valid_group_node.has_group.get().has_version.single().uid
                )
                activity_group_uids.append(
                    activity_valid_group_node.in_group.get().has_version.single().uid
                )

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
        return key

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name
    ) -> str:
        # concept_value property comes from the main part of the query
        # which is specified in the concept_generic_repository
        activity_subgroup_names = self.filter_query_parameters.get(
            "activity_subgroup_names"
        )
        activity_group_names = self.filter_query_parameters.get("activity_group_names")
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
                THEN head([(concept_root)-[:HAS_VERSION]->(:{self.value_class.__label__})<-[:HAS_SELECTED_ACTIVITY]->(:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value:StudyValue)
                   | coalesce(study_value.study_id_prefix, "") + "-" + toString(study_value.study_number)])
                ELSE NULL
            END AS requester_study_id,
            coalesce(concept_value.is_data_collected, False) AS is_data_collected,
            coalesce(concept_value.is_multiple_selection_allowed, True) AS is_multiple_selection_allowed,
            apoc.coll.toSet([(concept_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)
            {'WHERE size([(activity_valid_group)<-[:HAS_GROUP]-(activity_subgroup_value) WHERE activity_subgroup_value.name in $activity_subgroup_names | activity_subgroup_value.name]) > 0 '
        if activity_subgroup_names
        else ''}
            {'AND' if activity_subgroup_names and activity_group_names else ''}
            {'' if activity_subgroup_names and activity_group_names else 'WHERE' if not activity_subgroup_names and activity_group_names else ''}
            {'size([(activity_valid_group)-[:IN_GROUP]-(activity_group_value) WHERE activity_group_value.name in $activity_group_names | activity_group_value.name]) > 0 '
        if activity_group_names
        else ''}
             | {{
                 activity_subgroup: head(apoc.coll.sortMulti([(activity_valid_group)<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue)
                 <-[has_version:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
                    | {{
                        uid:activity_subgroup_root.uid,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1]),
                        name:activity_subgroup_value.name
                    }}], ['major_version', 'minor_version'])),
                 activity_group: head(apoc.coll.sortMulti([(activity_valid_group)-[:IN_GROUP]-(activity_group_value:ActivityGroupValue)
                 <-[has_version:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
                    | {{
                        uid:activity_group_root.uid,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1]),
                        name:activity_group_value.name
                    }}], ['major_version', 'minor_version']))
             }}]) AS activity_groupings,
            head([(concept_value)-[:REPLACED_BY_ACTIVITY]->(replacing_activity_root:ActivityRoot) | replacing_activity_root.uid]) AS replaced_by_activity,
            apoc.coll.sortMulti([(concept_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-(activity_instance_value:ActivityInstanceValue)
                <-[instance_version:HAS_VERSION WHERE instance_version.status='Final' and instance_version.end_date IS NULL]-(activity_instance_root) |
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

    def get_activity_overview(self, uid: str, version: str | None = None) -> dict:
        if version:
            params = {"uid": uid, "version": version}
            match = """
                MATCH (activity_root:ActivityRoot {uid:$uid})
                CALL {
                        WITH activity_root
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
                    CALL {
                        WITH activity_root, activity_value
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

        query = (
            match
            + """
        WITH DISTINCT activity_root,activity_value, has_version,
            head([(library)-[:CONTAINS_CONCEPT]->(activity_root) | library.name]) AS activity_library_name,
            [(activity_root)-[versions:HAS_VERSION]->(:ActivityValue) | versions.version] as all_versions,
            apoc.coll.sortMulti([(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-
            (activity_instance_value:ActivityInstanceValue)<-[aihv:HAS_VERSION]-(activity_instance_root:ActivityInstanceRoot)
            WHERE NOT EXISTS ((activity_instance_value)<--(:DeletedActivityInstanceRoot))
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
            [(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)
                <-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue) | {
                    activity_subgroup_value: activity_subgroup_value, 
                    activity_group_value: head([(activity_valid_group)-[:IN_GROUP]->(activity_group_value) | activity_group_value])
                }
            ] AS hierarchy
        RETURN
            hierarchy,
            activity_root,
            activity_value,
            activity_library_name,
            apoc.coll.sortMaps(activity_instances, '^name') as activity_instances,
            has_version,
            apoc.coll.dropDuplicateNeighbors(apoc.coll.sort(all_versions)) AS all_versions
        """
        )
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

    def get_cosmos_activity_overview(self, uid: str) -> dict:
        query = """
        MATCH (activity_root:ActivityRoot {uid:$uid})-[:LATEST]->(activity_value:ActivityValue)
        WITH DISTINCT activity_root,activity_value,
            apoc.coll.toSet([(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-
            (activity_instance_value:ActivityInstanceValue)-[:ACTIVITY_INSTANCE_CLASS]->
            (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue)
            WHERE NOT EXISTS ((activity_instance_value)<--(:DeletedActivityInstanceRoot))
            | {
                name:activity_instance_value.name,
                nci_concept_id:activity_instance_value.nci_concept_id,
                abbreviation:activity_instance_value.abbreviation,
                definition:activity_instance_value.definition,
                activity_instance_class_name: activity_instance_class_value.name
            }]) AS activity_instances,
            [(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)
            <-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value.name] AS activity_subgroups
        WITH activity_value,
            activity_subgroups,
            apoc.coll.sortMaps(activity_instances, '^name') as activity_instances
        OPTIONAL MATCH (activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-
            (activity_instance_value)-[:CONTAINS_ACTIVITY_ITEM]->
            (activity_item:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(activity_item_class_root:ActivityItemClassRoot)-[:LATEST]->
            (activity_item_class_value:ActivityItemClassValue)
        OPTIONAL MATCH (activity_item)-[]->(CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(CTTermAttributesRoot)-[:LATEST]->(activity_item_term_attr_value)
        OPTIONAL MATCH (activity_item)-[:HAS_UNIT_DEFINITION]->(:UnitDefinitionRoot)-[:LATEST]->(unit_def:UnitDefinitionValue)
        WITH activity_value,
            activity_item_class_value,
            activity_instances,
            activity_subgroups,
            CASE WHEN size(collect(activity_item)) > 0 THEN
            apoc.map.fromPairs([
                ['nci_concept_id', activity_item_class_value.nci_concept_id],
                ['name', activity_item_class_value.name],
                ['type', head([(activity_item_class_value)-[:HAS_DATA_TYPE]->(data_type_term_root)-[:HAS_ATTRIBUTES_ROOT]->(data_type_term_attr_root)-[:LATEST]->(data_type_term_attr_value) | data_type_term_attr_value.preferred_term])],
                ['example_set', collect(distinct(coalesce(activity_item_term_attr_value.code_submission_value, unit_def.name)))]
            ]) ELSE null
            END
            AS activity_items
        RETURN
            activity_subgroups,
            activity_value,
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

    def generic_match_clause_all_versions(self):
        return """
            MATCH (concept_root:ActivityRoot)-[version:HAS_VERSION]->(concept_value:ActivityValue)
                    -[:HAS_GROUPING]->(ag:ActivityGrouping)
                    -[:IN_SUBGROUP]->(avg:ActivityValidGroup)<-[:HAS_GROUP]-(subgroup_val:ActivitySubGroupValue)<-[:HAS_VERSION]-(subgroup_root:ActivitySubGroupRoot)
            WITH *
            MATCH (avg)-[:IN_GROUP]->(group_value:ActivityGroupValue)<-[:HAS_VERSION]-(group_root:ActivityGroupRoot)
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
    ) -> dict | None:
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

        query = (
            match
            + """
        MATCH (activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-
            (activity_instance_value:ActivityInstanceValue)<-[aihv:HAS_VERSION]-(activity_instance_root:ActivityInstanceRoot)
        WITH DISTINCT activity_root, activity_value, activity_instance_root, activity_instance_value, aihv
        WHERE aihv.end_date IS NULL AND NOT EXISTS ((activity_instance_value)<--(:DeletedActivityInstanceRoot))
        WITH *,
            {
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
            } AS activity_instance ORDER BY activity_instance.uid, activity_instance.name
        RETURN
            collect(activity_instance) as activity_instances
        """
        )
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
MATCH(r:ActivityRoot)-[:LATEST]->(v:ActivityValue)
WHERE ANY(value IN $syn WHERE value IN v.synonyms)
RETURN r.uid, [value IN $syn WHERE value IN v.synonyms] as existingSynonyms
""",
            params={"syn": synonyms},
        )

        if not rs[0]:
            return {}

        return {item[0]: item[1] for item in rs[0]}
