from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivityGroupValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.activities.activity_group import (
    ActivityGroupAR,
    ActivityGroupVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.activities.activity_group import ActivityGroup
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime


class ActivityGroupRepository(ConceptGenericRepository[ActivityGroupAR]):
    root_class = ActivityGroupRoot
    value_class = ActivityGroupValue
    return_model = ActivityGroup

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> ActivityGroupAR:
        major, minor = input_dict.get("version").split(".")
        return ActivityGroupAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=ActivityGroupVO.from_repository_values(
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("name_sentence_case"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
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
    ) -> ActivityGroupAR:
        return ActivityGroupAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActivityGroupVO.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                definition=value.definition,
                abbreviation=value.abbreviation,
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
    ) -> ActivityGroupAR:
        return self._create_ar(
            root=root, library=library, relationship=relationship, value=value
        )

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library)
        filter_parameters = []
        if kwargs.get("activity_subgroup_names") is not None:
            activity_subgroup_names = kwargs.get("activity_subgroup_names")
            filter_by_activity_subgroup_names = """
            size([(concept_value)<-[:IN_GROUP]-(:ActivityValidGroup)<-[:HAS_GROUP]-(v:ActivitySubGroupValue) 
            WHERE v.name IN $activity_subgroup_names | v.name]) > 0"""
            filter_parameters.append(filter_by_activity_subgroup_names)
            filter_query_parameters["activity_subgroup_names"] = activity_subgroup_names
        if kwargs.get("activity_names") is not None:
            activity_names = kwargs.get("activity_names")
            filter_by_activity_names = """
            size([(concept_value)<-[:IN_GROUP]-(:ActivityValidGroup)<-[:IN_SUBGROUP]-(:ActivityGrouping)<-[:HAS_GROUPING]-(v:ActivityValue) 
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

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
        # concept_value property comes from the main part of the query
        # which is specified in the activity_generic_repository_impl
        return """
        WITH *,
            head([(concept_value)<-[:IN_GROUP]-(:ActivityValidGroup)<-[:HAS_GROUP]-(activity_sub_group_value:ActivitySubGroupValue)<-[:HAS_VERSION]-
            (activity_sub_group_root:ActivitySubGroupRoot) | {uid:activity_sub_group_root.uid, name:activity_sub_group_value.name}]) AS activity_subgroup,
            head([(concept_value)<-[:IN_GROUP]-(:ActivityValidGroup)<-[:IN_SUBGROUP]-(:ActivityGrouping)<-[:HAS_GROUPING]-(activity_value:ActivityValue)
            <-[:HAS_VERSION]-(activity_root:ActivityRoot) | {uid:activity_root.uid, name:activity_value.name}]) AS activity
        """

    def _create_new_value_node(self, ar: ActivityGroupAR) -> ActivityGroupValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.save()
        return value_node

    def generic_match_clause_all_versions(self):
        return """
            MATCH (concept_root:ActivityGroupRoot)-[version:HAS_VERSION]->(concept_value:ActivityGroupValue)
        """

    def get_cosmos_group_overview(self, group_uid: str) -> dict:
        """
        Get a COSMoS compatible representation of a specific activity group.
        Similar to get_group_overview but formatted for COSMoS.

        Args:
            group_uid: The UID of the activity group

        Returns:
            A dictionary representation compatible with COSMoS format
        """

        query = """
        MATCH (group_root:ActivityGroupRoot {uid:$uid})-[:LATEST]->(group_value:ActivityGroupValue)
        WITH DISTINCT group_root, group_value,
            head([(library)-[:CONTAINS_CONCEPT]->(group_root) | library.name]) AS group_library_name,
            [(group_root)-[versions:HAS_VERSION]->(:ActivityGroupValue) | versions.version] as all_versions,
            apoc.coll.toSet([(sgv:ActivitySubGroupValue)-[:HAS_GROUP]->(avg:ActivityValidGroup)-[:IN_GROUP]->(group_value)
                | {
                    uid: head([(sgr:ActivitySubGroupRoot)-[:HAS_VERSION]->(sgv) | sgr.uid]),
                    name: sgv.name,
                    definition: sgv.definition,
                    status: head([(sgr:ActivitySubGroupRoot)-[hv:HAS_VERSION]->(sgv) | hv.status]),
                    version: head([(sgr:ActivitySubGroupRoot)-[hv:HAS_VERSION]->(sgv) | hv.version])
                }]) AS linked_subgroups,
            apoc.coll.toSet(
                [(group_value)<-[:IN_GROUP]-(activity_valid_group:ActivityValidGroup)<-[:IN_SUBGROUP]-
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
            group_value,
            group_library_name,
            linked_subgroups,
            linked_activities,
            apoc.coll.dropDuplicateNeighbors(apoc.coll.sort(all_versions)) AS all_versions
        """

        result_array, attribute_names = db.cypher_query(
            query=query, params={"uid": group_uid}
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

    def get_linked_activity_subgroup_uids(
        self, group_uid: str, version: str
    ) -> list[dict[str, str]]:
        """
        Get the UIDs of all activity subgroups linked to a specific activity group version.
        Will return the latest version of each subgroup connected to this activity group version.

        Args:
            group_uid: The UID of the activity group
            version: The version of the activity group

        Returns:
            A list of dictionaries containing the subgroup uid, name, status and version
        """
        # Find all subgroups connected to this specific group version and collect all their versions
        query = """
        // 1. Find the specific activity group version
        MATCH (agr:ActivityGroupRoot {uid: $group_uid})-[:HAS_VERSION {version: $version}]-(gv:ActivityGroupValue)
        
        // 2. Find subgroups directly connected to this group version through the valid relationship path
        MATCH (gv)-[:IN_GROUP]-(avg:ActivityValidGroup)-[:HAS_GROUP]-(sgv:ActivitySubGroupValue)
        
        // 3. Get the subgroup roots and their Final version relationships
        MATCH (sgr:ActivitySubGroupRoot)-[sgv_rel:HAS_VERSION {status: "Final"}]-(sgv)
        
        // 4. Group by subgroup root and collect all version relationships
        WITH DISTINCT agr, gv, sgr, sgv, collect(sgv_rel) as versions
        
        // 5. Sort results by subgroup name
        ORDER BY sgv.name
        
        // 6. Return the result with all necessary fields
        RETURN {
            uid: sgr.uid,
            name: sgv.name,
            version: head([v in versions | v.version]),
            status: head([v in versions | v.status]),
            definition: sgv.definition
        } as result
        """

        results, _ = db.cypher_query(
            query,
            {
                "group_uid": group_uid,
                "version": version,
            },
        )
        if not results:
            return []
        return [dict(result[0]) for result in results]
