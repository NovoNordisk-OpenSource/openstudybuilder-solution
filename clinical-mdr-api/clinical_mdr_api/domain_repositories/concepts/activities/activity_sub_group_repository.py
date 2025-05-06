from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivitySubGroupRoot,
    ActivitySubGroupValue,
    ActivityValidGroup,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
    ActivitySubGroupVO,
    SimpleActivityGroupVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
)
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime, version_string_to_tuple


class ActivitySubGroupRepository(ConceptGenericRepository[ActivitySubGroupAR]):
    root_class = ActivitySubGroupRoot
    value_class = ActivitySubGroupValue
    return_model = ActivitySubGroup

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> ActivitySubGroupAR:
        major, minor = input_dict.get("version").split(".")
        return ActivitySubGroupAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("name_sentence_case"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                activity_groups=[
                    SimpleActivityGroupVO(
                        activity_group_uid=activity_group.get("activity_group").get(
                            "uid"
                        ),
                        activity_group_version=f"{activity_group.get('activity_group').get('major_version')}.{activity_group.get('activity_group').get('minor_version')}",
                    )
                    for activity_group in input_dict.get("activity_groups")
                ],
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
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> ActivitySubGroupAR:
        return ActivitySubGroupAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                definition=value.definition,
                abbreviation=value.abbreviation,
                activity_groups=[
                    SimpleActivityGroupVO(
                        activity_group_uid=activity_group.get("uid"),
                        activity_group_version=f"{activity_group.get('major_version')}.{activity_group.get('minor_version')}",
                    )
                    for activity_group in _kwargs["activity_subgroups_root"][
                        "activity_groups"
                    ]
                ],
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
    ) -> ActivitySubGroupAR:
        activity_valid_groups = value.has_group.all()
        activity_groups = []
        for activity_valid_group in activity_valid_groups:
            activity_group_value = activity_valid_group.in_group.get()
            activity_group_root = activity_group_value.has_version.single()
            all_rels = activity_group_value.has_version.all_relationships(
                activity_group_root
            )
            latest = max(all_rels, key=lambda r: version_string_to_tuple(r.version))
            activity_groups.append(
                SimpleActivityGroupVO(
                    activity_group_uid=activity_group_root.uid,
                    activity_group_version=latest.version,
                )
            )

        return ActivitySubGroupAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                definition=value.definition,
                abbreviation=value.abbreviation,
                activity_groups=activity_groups,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def specific_alias_clause(
        self,
        only_specific_status: str = ObjectStatus.LATEST.name,
        **kwargs,
    ) -> str:
        # concept_value property comes from the main part of the query
        # which is specified in the activity_generic_repository_impl
        return """
        WITH *,
            [(concept_value)-[:HAS_GROUP]->(activity_valid_group:ActivityValidGroup) |
            {
                activity_group:head(apoc.coll.sortMulti([(activity_valid_group)-[:IN_GROUP]-(activity_group_value:ActivityGroupValue)
                    <-[has_version:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | 
                    {
                     uid:activity_group_root.uid,
                     name:activity_group_value.name,
                     major_version: toInteger(split(has_version.version,'.')[0]),
                     minor_version: toInteger(split(has_version.version,'.')[1])
                    }], ['major_version', 'minor_version']))
            }] AS activity_groups
        """

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library)
        filter_parameters = []
        if kwargs.get("activity_group_uid") is not None:
            activity_group_uid = kwargs.get("activity_group_uid")
            filter_by_activity_group_uid = """
            $activity_group_uid IN 
            [(concept_value)-[:HAS_GROUP]->(:ActivityValidGroup)-[:IN_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root) 
                | activity_group_root.uid]"""
            filter_parameters.append(filter_by_activity_group_uid)
            filter_query_parameters["activity_group_uid"] = activity_group_uid
        if kwargs.get("activity_group_names") is not None:
            activity_group_names = kwargs.get("activity_group_names")
            filter_by_activity_group_names = """
            size([(concept_value)-[:HAS_GROUP]->(:ActivityValidGroup)-[:IN_GROUP]->(v:ActivityGroupValue) 
            WHERE v.name IN $activity_group_names | v.name]) > 0"""
            filter_parameters.append(filter_by_activity_group_names)
            filter_query_parameters["activity_group_names"] = activity_group_names
        if kwargs.get("activity_names") is not None:
            activity_names = kwargs.get("activity_names")
            filter_by_activity_names = """
            size([(concept_value)-[:HAS_GROUP]-(:ActivityValidGroup)<-[:IN_SUBGROUP]-(:ActivityGrouping)<-[:HAS_GROUPING]-(v:ActivityValue) 
            WHERE v.name IN $activity_names | v.name]) > 0"""
            filter_parameters.append(filter_by_activity_names)
            filter_query_parameters["activity_names"] = activity_names
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

    def get_linked_activity_group_uids(
        self, subgroup_uid: str, version: str | None = None
    ) -> list[dict]:
        """
        Get UIDs of activity groups linked to a specific activity subgroup.

        Args:
            subgroup_uid: The UID of the activity subgroup
            version: Optional specific version to get linked activity groups for

        Returns:
            A list of activity group UIDs directly linked to this subgroup
        """
        match_clause = """
        MATCH (sgr:ActivitySubGroupRoot {uid: $uid})
        """

        params = {"uid": subgroup_uid}

        if version:
            match_clause += (
                "-[:HAS_VERSION {version: $version}]->(sgv:ActivitySubGroupValue)"
            )
            params["version"] = version
        else:
            match_clause += "-[:LATEST]->(sgv:ActivitySubGroupValue)"

        query = f"""
        {match_clause}
        // Find all activity groups directly connected to this subgroup version
        MATCH (sgv)-[:HAS_GROUP]->(avg:ActivityValidGroup)-[:IN_GROUP]->(agv:ActivityGroupValue)
        
        // Get the activity group roots and their Final version relationships
        MATCH (agr:ActivityGroupRoot)-[ag_rel:HAS_VERSION {{status: "Final"}}]-(agv)
        
        // Group by activity group root and collect all version relationships
        WITH DISTINCT agr, agv, collect(ag_rel) as versions
        
        // Sort versions and take the latest one
        WITH agr, agv, versions,
             [v in versions | v.version] as version_strings
        ORDER BY agv.name
        
        // Return the result with all necessary fields
        RETURN
            agr.uid as uid, 
            agv.name as name, 
            head([v in versions | v.version]) as version, 
            head([v in versions | v.status]) as status
        """

        result, _ = db.cypher_query(query=query, params=params)

        # Return formatted results
        return [
            {"uid": row[0], "name": row[1], "version": row[2], "status": row[3]}
            for row in result
            if row[0] is not None
        ]

    def get_linked_activity_uids(
        self, subgroup_uid: str, version: str | None = None
    ) -> list[str]:
        """
        Get UIDs of activities linked to a specific activity subgroup.

        Args:
            subgroup_uid: The UID of the activity subgroup
            version: Optional specific version to get linked activities for

        Returns:
            A list of activity UIDs directly linked to this subgroup
        """
        match_clause = """
        MATCH (subgroup_root:ActivitySubGroupRoot {uid:$uid})
        """

        params = {"uid": subgroup_uid}

        if version:
            match_clause += "-[v:HAS_VERSION {version: $version}]->(subgroup_value:ActivitySubGroupValue)"
            params["version"] = version
        else:
            match_clause += "-[:LATEST]->(subgroup_value:ActivitySubGroupValue)"

        query = f"""
        {match_clause}
        MATCH (subgroup_value)-[:HAS_GROUP]->(avg:ActivityValidGroup)<-[:IN_SUBGROUP]-(ag:ActivityGrouping)<-[:HAS_GROUPING]-(av:ActivityValue)<-[:HAS_VERSION]-(ar:ActivityRoot)
        WHERE NOT EXISTS ((av)<--(:DeletedActivityRoot))
        RETURN DISTINCT ar.uid as uid
        """

        result, _ = db.cypher_query(query=query, params=params)
        return [row[0] for row in result]

    def get_cosmos_subgroup_overview(self, subgroup_uid: str) -> dict:
        """
        Get a COSMoS compatible representation of a specific activity subgroup.
        Similar to get_activity_overview but formatted for COSMoS.

        Args:
            subgroup_uid: The UID of the activity subgroup

        Returns:
            A dictionary representation compatible with COSMoS format
        """
        query = """
        MATCH (subgroup_root:ActivitySubGroupRoot {uid:$uid})-[:LATEST]->(subgroup_value:ActivitySubGroupValue)
        WITH DISTINCT subgroup_root, subgroup_value,
            head([(library)-[:CONTAINS_CONCEPT]->(subgroup_root) | library.name]) AS subgroup_library_name,
            [(subgroup_root)-[versions:HAS_VERSION]->(:ActivitySubGroupValue) | versions.version] as all_versions,
            apoc.coll.toSet([(subgroup_value)-[:HAS_GROUP]->(activity_valid_group:ActivityValidGroup)-[:IN_GROUP]->
                (activity_group_value:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
                | {
                    uid: activity_group_root.uid,
                    name: activity_group_value.name
                }]) AS activity_groups,
            apoc.coll.toSet(
                [(subgroup_value)-[:HAS_GROUP]->(activity_valid_group:ActivityValidGroup)<-[:IN_SUBGROUP]-
                (activity_grouping:ActivityGrouping)<-[:HAS_GROUPING]-(activity_value:ActivityValue)<-[:HAS_VERSION]-
                (activity_root:ActivityRoot)
                WHERE NOT EXISTS ((activity_value)<--(:DeletedActivityRoot))
                | {
                    uid: activity_root.uid,
                    name: activity_value.name,
                    definition: activity_value.definition,
                    nci_concept_id: activity_value.nci_concept_id,
                    status: head([(activity_root)-[hv:HAS_VERSION]->(activity_value) | hv.status]),
                    version: head([(activity_root)-[hv:HAS_VERSION]->(activity_value) | hv.version])
                }]) AS linked_activities
        RETURN
            subgroup_value,
            subgroup_library_name,
            activity_groups,
            linked_activities,
            apoc.coll.dropDuplicateNeighbors(apoc.coll.sort(all_versions)) AS all_versions
        """

        result_array, attribute_names = db.cypher_query(
            query=query, params={"uid": subgroup_uid}
        )
        BusinessLogicException.raise_if(
            len(result_array) != 1,
            msg=f"The overview query returned broken data: {result_array}",
        )

        overview = result_array[0]
        overview_dict = {}
        for overview_prop, attribute_name in zip(overview, attribute_names):
            overview_dict[attribute_name] = overview_prop

        return overview_dict

    def _create_new_value_node(self, ar: ActivitySubGroupAR) -> VersionValue:
        value_node: ActivitySubGroupValue = super()._create_new_value_node(ar=ar)
        value_node.save()
        for activity_group in ar.concept_vo.activity_groups:
            # find related ActivityGroup nodes
            group_root = ActivityGroupRoot.nodes.get_or_none(
                uid=activity_group.activity_group_uid
            )
            group_value = group_root.has_latest_value.get_or_none()

            # Create ActivityValidGroup node
            activity_valid_group = ActivityValidGroup(
                uid=ActivityValidGroup.get_next_free_uid_and_increment_counter()
            )
            activity_valid_group.save()

            # connect ActivityValidGroup and ActivityGroupValue nodes
            activity_valid_group.in_group.connect(group_value)

            # connect ActivitySubGroupValue and ActivityValidGroup nodes
            value_node.has_group.connect(activity_valid_group)

        return value_node

    def _has_data_changed(
        self, ar: ActivitySubGroupAR, value: ActivitySubGroupValue
    ) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        activity_valid_groups = value.has_group.all()
        activity_groups_uid = []
        for activity_valid_group in activity_valid_groups:
            activity_group_uid = (
                activity_valid_group.in_group.get().has_version.single().uid
            )
            activity_groups_uid.append(activity_group_uid)

        # Is this a final or retired version? If yes, we skip the check for updated groups
        # to avoid creating new values nodes when just creating a new draft.
        root_for_final_value = value.has_version.match(
            status__in=[LibraryItemStatus.FINAL.value, LibraryItemStatus.RETIRED.value],
            end_date__isnull=True,
        )
        if not root_for_final_value:
            groups_updated = self._any_group_updated(value)
        else:
            groups_updated = False

        are_rels_changed = sorted(
            [
                activity_group.activity_group_uid
                for activity_group in ar.concept_vo.activity_groups
            ]
        ) != sorted(activity_groups_uid)

        return are_concept_properties_changed or are_rels_changed or groups_updated

    def _any_group_updated(self, subgroup_value):
        for grouping_node in subgroup_value.has_group.all():
            if not grouping_node.in_group.get().has_latest_value.single():
                # The linked group is not the latest.
                # We need to return True, so that the subgroup value
                # gets updated to use the new group value.
                return True
        return False

    def generic_match_clause_all_versions(self):
        return """
            MATCH (concept_root:ActivitySubGroupRoot)-[version:HAS_VERSION]->(concept_value:ActivitySubGroupValue)
                    -[:HAS_GROUP]->(avg:ActivityValidGroup)-[:IN_GROUP]->(agv:ActivityGroupValue)<-[:HAS_VERSION]-(agr:ActivityGroupRoot)
            """
