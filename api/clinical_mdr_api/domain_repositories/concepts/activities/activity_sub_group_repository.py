from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivitySubGroupRoot,
    ActivitySubGroupValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
    ActivitySubGroupVO,
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
from common.utils import convert_to_datetime


class ActivitySubGroupRepository(ConceptGenericRepository[ActivitySubGroupAR]):
    root_class = ActivitySubGroupRoot
    value_class = ActivitySubGroupValue
    return_model = ActivitySubGroup

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> ActivitySubGroupAR:
        major, minor = input_dict["version"].split(".")
        activity_subgroup_ar = ActivitySubGroupAR.from_repository_values(
            uid=input_dict["uid"],
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=input_dict["name"],
                name_sentence_case=input_dict["name_sentence_case"],
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                nci_concept_id=input_dict.get("nci_concept_id"),
                nci_concept_name=input_dict.get("nci_concept_name"),
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
        return activity_subgroup_ar

    def _create_ar(
        self,
        root: VersionRoot,
        library: Library,
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
                nci_concept_id=value.nci_concept_id,
                nci_concept_name=value.nci_concept_name,
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
    ) -> ActivitySubGroupAR:

        return ActivitySubGroupAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                definition=value.definition,
                abbreviation=value.abbreviation,
                nci_concept_id=value.nci_concept_id,
                nci_concept_name=value.nci_concept_name,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def specific_alias_clause(self, **kwargs) -> str:
        # concept_value property comes from the main part of the query
        # which is specified in the activity_generic_repository_impl
        return ""

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict[Any, Any]]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library, **kwargs)
        filter_parameters = []
        if kwargs.get("activity_group_uid") is not None:
            activity_group_uid = kwargs.get("activity_group_uid")
            filter_by_activity_group_uid = """
            $activity_group_uid IN
            [(concept_value)<-[:HAS_SELECTED_SUBGROUP]-(:ActivityGrouping)-[:HAS_SELECTED_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root)
                | activity_group_root.uid]"""
            filter_parameters.append(filter_by_activity_group_uid)
            filter_query_parameters["activity_group_uid"] = activity_group_uid
        if kwargs.get("activity_group_names") is not None:
            activity_group_names = kwargs.get("activity_group_names")
            filter_by_activity_group_names = """
            size([(concept_value)<-[:HAS_SELECTED_SUBGROUP]-(:ActivityGrouping)-[:HAS_SELECTED_GROUP]->(v:ActivityGroupValue) 
            WHERE v.name IN $activity_group_names | v.name]) > 0"""
            filter_parameters.append(filter_by_activity_group_names)
            filter_query_parameters["activity_group_names"] = activity_group_names
        if kwargs.get("activity_names") is not None:
            activity_names = kwargs.get("activity_names")
            filter_by_activity_names = """
            size([(concept_value)<-[:HAS_SELECTED_SUBGROUP]-(:ActivityGrouping)<-[:HAS_GROUPING]-(v:ActivityValue) 
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
    ) -> list[dict[Any, Any]]:
        """
        Get UIDs of activity groups linked to a specific activity subgroup.

        Args:
            subgroup_uid: The UID of the activity subgroup
            version: Optional specific version to get linked activity groups for

        Returns:
            A list of activity group UIDs directly linked to this subgroup
        """
        query = """
        // 1. Find a specific activity subgroup version
        MATCH (sgr:ActivitySubGroupRoot {uid: $uid})
        """

        params = {"uid": subgroup_uid}

        if version:
            query += "-[sgv_rel:HAS_VERSION {version: $version}]->(sgv:ActivitySubGroupValue)"
            params["version"] = version
        else:
            query += "-[:LATEST]->(sgv:ActivitySubGroupValue)"
            # For the LATEST case, we need to find the actual version relationship
            query += """
            MATCH (sgr)-[sgv_rel:HAS_VERSION]->(sgv)
            """

        query += """
        // 2. Find when this version's validity ends (either its end_date or the start of the next version)
        OPTIONAL MATCH (sgr)-[next_rel:HAS_VERSION]->(next_sgv:ActivitySubGroupValue)
        WHERE toFloat(next_rel.version) > toFloat(sgv_rel.version)
        WITH sgv, sgr, sgv_rel,
             CASE WHEN sgv_rel.end_date IS NULL
                  THEN min(next_rel.start_date)
                  ELSE sgv_rel.end_date
             END as version_end_date
        // 3. Find all activity groups connected to this subgroup version via ActivityGrouping nodes
        MATCH (sgv)<-[:HAS_SELECTED_SUBGROUP]-(:ActivityGrouping)-[:HAS_SELECTED_GROUP]->(agv:ActivityGroupValue)
        MATCH (agr:ActivityGroupRoot)-[ag_rel:HAS_VERSION]->(agv)
        // 4. Filter activity group versions created before the subgroup's next version/end date
        // Include all activity groups regardless of status (per user requirement)
        WITH sgv, sgr, sgv_rel, version_end_date, agr, agv, ag_rel
        WHERE ag_rel.start_date <= COALESCE(version_end_date, datetime())
        // 5. Group by activity group for processing
        WITH
            sgr.uid as subgroup_uid,
            sgv_rel.version as subgroup_version,
            agr.uid as group_uid,
            agv.name as group_name,
            agv.definition as group_definition,
            ag_rel.version as group_version,
            ag_rel.status as group_status,
            toInteger(SPLIT(ag_rel.version, '.')[0]) as ag_major_version,
            toInteger(SPLIT(ag_rel.version, '.')[1]) as ag_minor_version
        // 6. Collect all versions by group
        WITH
            group_uid,
            collect({
                ag_major: ag_major_version,
                ag_minor: ag_minor_version,
                group_version: group_version,
                group_name: group_name,
                group_definition: group_definition,
                group_status: group_status
            }) as versions
        // 7. Find highest major version
        WITH
            group_uid,
            versions,
            reduce(max_ag_major = 0, v IN versions |
                CASE WHEN v.ag_major > max_ag_major THEN v.ag_major ELSE max_ag_major END
            ) as max_ag_major
        // 8. Filter to only include versions with the maximum major version
        WITH
            group_uid,
            [v in versions WHERE v.ag_major = max_ag_major] as ag_max_major_versions,
            max_ag_major
        // 9. Find highest minor version
        WITH
            group_uid,
            max_ag_major,
            reduce(max_ag_minor = -1, v IN ag_max_major_versions |
                CASE WHEN v.ag_minor > max_ag_minor THEN v.ag_minor ELSE max_ag_minor END
            ) as max_ag_minor,
            ag_max_major_versions
        // 10. Extract the specific version information
        WITH
            group_uid,
            max_ag_major,
            max_ag_minor,
            [v in ag_max_major_versions WHERE v.ag_minor = max_ag_minor][0] as ag_version_info
        // 11. Return data in the required format
        RETURN
            group_uid as uid,
            ag_version_info.group_name as name,
            ag_version_info.group_version as version,
            ag_version_info.group_status as status
        ORDER BY name
        """

        result, _ = db.cypher_query(query=query, params=params)

        # Return formatted results
        return [
            {
                "uid": row[0],
                "name": row[1],
                "version": row[2],
                "status": row[3],
                "definition": row[4] if len(row) > 4 else None,
            }
            for row in result
            if row[0] is not None
        ]

    def get_linked_activity_uids(
        self,
        subgroup_uid: str,
        version: str | None = None,
        search_string: str = "",
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
    ) -> dict[str, Any]:
        """
        Get UIDs and versions of activities linked to a specific activity subgroup version.
        This ensures we only get activity versions that existed at the time the subgroup version was active.

        Args:
            subgroup_uid: The UID of the activity subgroup
            version: Optional specific version to get linked activities for
            search_string: Optional search string to filter activities by name or other fields
            page_number: The page number for pagination (starting from 1)
            page_size: The number of items per page (0 for all items)
            total_count: Whether to return the total count of records

        Returns:
            A dict with activities and optionally total count
        """
        query = """
        // 1. Find a specific activity subgroup version
        MATCH (sgr:ActivitySubGroupRoot {uid: $uid})
        """

        params = {"uid": subgroup_uid}

        if version:
            query += "-[sgv_rel:HAS_VERSION {version: $version}]->(sgv:ActivitySubGroupValue)"
            params["version"] = version
        else:
            query += "-[:LATEST]->(sgv:ActivitySubGroupValue)"
            # For the LATEST case, we need to find the actual version relationship
            query += """
            MATCH (sgr)-[sgv_rel:HAS_VERSION]->(sgv)
            """

        query += """
        // 2. Find when this version's validity ends (either its end_date or the start of the next version)
        OPTIONAL MATCH (sgr)-[next_rel:HAS_VERSION]->(next_sgv:ActivitySubGroupValue)
        WHERE toFloat(next_rel.version) > toFloat(sgv_rel.version)
        WITH sgv, sgr, sgv_rel, 
             CASE WHEN sgv_rel.end_date IS NULL 
                  THEN min(next_rel.start_date) 
                  ELSE sgv_rel.end_date 
             END as version_end_date
            
        // 3. Find all activities linked to this subgroup version through activity groups
        MATCH (sgv)<-[:HAS_SELECTED_SUBGROUP]-(ag:ActivityGrouping)<-[:HAS_GROUPING]-(av:ActivityValue)<-[a_rel:HAS_VERSION]-(ar:ActivityRoot)
        WHERE NOT EXISTS ((av)<--(:DeletedActivityRoot))
        
        // 4. Filter activity versions - find those existing at the time this subgroup version was active
        WITH sgv, sgr, sgv_rel, version_end_date, ar, av, a_rel
        WHERE a_rel.start_date <= COALESCE(version_end_date, datetime())
        AND a_rel.status = "Final"
        
        // 5. For each activity, find the version that existed at the time this subgroup version was active
        WITH ar.uid as activity_uid, ar, a_rel, sgv_rel.start_date as subgroup_start_date, version_end_date
        
        // 6. Find versions of this activity that existed at the same time as the subgroup version
        MATCH (ar)-[versions:HAS_VERSION]->(activity_values)
        WHERE versions.start_date <= COALESCE(version_end_date, datetime())
        AND (versions.end_date IS NULL OR versions.end_date >= subgroup_start_date)
        AND versions.status = "Final"
        
        // 7. Convert version strings to numbers for sorting
        WITH activity_uid, versions.version as version, 
             toInteger(SPLIT(versions.version, '.')[0]) as major_version,
             toInteger(SPLIT(versions.version, '.')[1]) as minor_version,
             activity_values
        ORDER BY activity_uid, major_version DESC, minor_version DESC
        
        // 8. Collect by activity_uid and take the first (highest) version for each activity
        // Since we already sorted by major and minor version in descending order
        WITH activity_uid, collect({version: version, major: major_version, minor: minor_version, values: activity_values})[0] as highest_version
        """

        # Add search filtering if search_string is provided
        if search_string:
            query += """
        // Apply search filtering on the highest version activity values
        WHERE toLower(highest_version.values.name) CONTAINS toLower($search_string)
           OR toLower(highest_version.values.definition) CONTAINS toLower($search_string)
           OR toLower(highest_version.values.abbreviation) CONTAINS toLower($search_string)
           OR toLower(highest_version.values.nci_concept_id) CONTAINS toLower($search_string)
        """
            params["search_string"] = search_string

        query += """
        WITH activity_uid, highest_version
        """

        # Add COUNT query for total if needed
        if total_count:
            count_query = query + """
            // 9. Return the count of activities for pagination
            RETURN count(activity_uid) as total
            """
            count_result, _ = db.cypher_query(query=count_query, params=params)
            total = count_result[0][0] if count_result else 0
        else:
            total = 0

        query += """
        RETURN activity_uid, highest_version.version as version
        """

        if page_size > 0:
            skip = (page_number - 1) * page_size
            query += f" SKIP {skip} LIMIT {page_size}"

        result, _ = db.cypher_query(query=query, params=params)
        activities = [{"uid": row[0], "version": row[1]} for row in result]

        # Return both the activities and total count
        return {"activities": activities, "total": total}

    def get_cosmos_subgroup_overview(self, subgroup_uid: str) -> dict[str, Any]:
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
            apoc.coll.toSet([(subgroup_value)<-[:HAS_SELECTED_SUBGROUP]-(activity_grouping:ActivityGrouping)-[:HAS_SELECTED_GROUP]->
                (activity_group_value:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
                | {
                    uid: activity_group_root.uid,
                    name: activity_group_value.name
                }]) AS activity_groups,
            apoc.coll.toSet(
                [(subgroup_value)<-[:HAS_SELECTED_SUBGROUP]-
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
            {
                uid: subgroup_root.uid,
                name: subgroup_value.name,
                name_sentence_case: subgroup_value.name_sentence_case,
                definition: subgroup_value.definition,
                abbreviation: subgroup_value.abbreviation
            } AS subgroup_value,
            subgroup_library_name,
            activity_groups,
            linked_activities,
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
        return value_node

    def _has_data_changed(
        self, ar: ActivitySubGroupAR, value: ActivitySubGroupValue
    ) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        return are_concept_properties_changed

    def generic_match_clause_all_versions(self):
        return """
            MATCH (concept_root:ActivitySubGroupRoot)-[version:HAS_VERSION]->(concept_value:ActivitySubGroupValue)
            """

    def get_linked_upgradable_activities(
        self, uid: str, version: str | None = None
    ) -> dict[Any, Any] | None:
        # Get "upgradable" linked activities.
        # These are the activity values that have no end date,
        # meaning that the linked value is the latest version of the activity.
        params = {"uid": uid}
        if version:
            params["version"] = version
            match = """
                MATCH (activity_subgroup_root:ActivitySubGroupRoot {uid:$uid})-[hv:HAS_VERSION {version:$version}]->(activity_subgroup_value:ActivitySubGroupValue)
                WITH DISTINCT activity_subgroup_root, activity_subgroup_value
                """
        else:
            match = """
                MATCH (activity_subgroup_root:ActivitySubGroupRoot {uid:$uid})-[:LATEST]->(activity_subgroup_value:ActivitySubGroupValue)
                """

        query = match + """
        // Find all activities linked to this subgroup value
        MATCH (activity_root:ActivityRoot)-[aihv:HAS_VERSION]->(activity_value:ActivityValue)-[:HAS_GROUPING]->
          (:ActivityGrouping)-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value)
        // For each activity, find all its groupings
        MATCH (activity_value)-[:HAS_GROUPING]->(activity_grouping:ActivityGrouping)-[:HAS_SELECTED_SUBGROUP]->
          (:ActivitySubGroupValue)<-[:HAS_VERSION]-(all_subgroup_root:ActivitySubGroupRoot)
        MATCH (activity_grouping)-[:HAS_SELECTED_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
        WITH DISTINCT activity_root, activity_value, aihv, COLLECT(DISTINCT {
            activity_group_uid: activity_group_root.uid,
            activity_subgroup_uid: all_subgroup_root.uid
        }) AS activity_groupings
        WHERE aihv.end_date IS NULL AND NOT EXISTS ((activity_value)<--(:DeletedActivityRoot))
        WITH *,
            {
                library_name: head([(library)-[:CONTAINS_CONCEPT]->(activity_root) | library.name]),
                uid: activity_root.uid,
                version: 
                    {
                        major_version: toInteger(split(aihv.version,'.')[0]),
                        minor_version: toInteger(split(aihv.version,'.')[1]),
                        status:aihv.status
                    },
                name: activity_value.name,
                name_sentence_case: activity_value.name_sentence_case,
                definition: activity_value.definition,
                abbreviation: activity_value.abbreviation,
                nci_concept_id: activity_value.nci_concept_id,
                nci_concept_name: activity_value.nci_concept_name,
                synonyms: activity_value.synonyms,
                request_rationale: activity_value.request_rationale,
                is_request_final: activity_value.is_request_final,
                is_data_collected: activity_value.is_data_collected,
                is_multiple_selection_allowed: activity_value.is_multiple_selection_allowed,
                activity_groupings: activity_groupings
            } AS activity ORDER BY activity.uid, activity.name
        RETURN
            collect(activity) as activities
        """
        result_array, attribute_names = db.cypher_query(query=query, params=params)
        if len(result_array) == 0:
            return None
        BusinessLogicException.raise_if(
            len(result_array) > 1,
            msg=f"The linked activities query returned broken data: {result_array}",
        )
        instances = result_array[0]
        instances_dict = {}
        for instances_prop, attribute_name in zip(instances, attribute_names):
            instances_dict[attribute_name] = instances_prop
        return instances_dict
