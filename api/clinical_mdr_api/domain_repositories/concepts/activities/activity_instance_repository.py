import datetime
from typing import Any

from neomodel import DoesNotExist, NodeClassNotDefined, db

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.models._utils import ListDistinct
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGrouping,
    ActivityInstanceGroupingRoot,
    ActivityInstanceGroupingValue,
    ActivityInstanceRoot,
    ActivityInstanceValue,
    ActivityItem,
    ActivityRoot,
)
from clinical_mdr_api.domain_repositories.models.biomedical_concepts import (
    ActivityInstanceClassRoot,
    ActivityItemClassRoot,
)
from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains.concepts.activities.activity_instance import (
    ActivityInstanceAR,
    ActivityInstanceAttributesAR,
    ActivityInstanceAttributesVO,
    ActivityInstanceGroupingsAR,
    ActivityInstanceGroupingsVO,
    ActivityInstanceGroupingVO,
    ActivityInstanceVO,
)
from clinical_mdr_api.domains.concepts.activities.activity_item import (
    ActivityItemVO,
    CTCodelistItem,
    CTTermItem,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
    ActivityInstanceAttributes,
    ActivityInstanceGroupings,
)
from clinical_mdr_api.models.concepts.activities.activity_item import (
    CompactUnitDefinition,
)
from clinical_mdr_api.services.user_info import UserInfoService
from common.config import settings
from common.exceptions import BusinessLogicException, NotFoundException
from common.utils import convert_to_datetime, version_string_to_tuple


class ActivityInstanceRepository(ConceptGenericRepository[ActivityInstanceAR]):
    root_class = ActivityInstanceRoot
    value_class = ActivityInstanceValue
    aggregate_class = ActivityInstanceAR
    value_object_class = ActivityInstanceVO
    return_model = ActivityInstance

    def _create_new_value_node(self, ar: ActivityInstanceAR) -> ActivityInstanceValue:
        value_node: ActivityInstanceValue = super()._create_new_value_node(ar=ar)
        attrs = ar.concept_vo.activity_instance_attributes
        value_node.is_research_lab = attrs.is_research_lab
        if attrs.molecular_weight:
            value_node.molecular_weight = attrs.molecular_weight
        if attrs.topic_code:
            value_node.topic_code = attrs.topic_code
        if attrs.adam_param_code:
            value_node.adam_param_code = attrs.adam_param_code
        value_node.is_required_for_activity = attrs.is_required_for_activity
        value_node.is_default_selected_for_activity = (
            attrs.is_default_selected_for_activity
        )
        value_node.is_data_sharing = attrs.is_data_sharing
        value_node.is_legacy_usage = attrs.is_legacy_usage
        value_node.is_derived = attrs.is_derived
        if attrs.legacy_description:
            value_node.legacy_description = attrs.legacy_description

        value_node.save()

        activity_uids = {ag.activity_uid for ag in ar.concept_vo.activity_groupings}
        BusinessLogicException.raise_if(
            len(activity_uids) > 1,
            msg="Instances are not allowed to link to several different activities",
        )
        requested = ActivityRoot.nodes.filter(
            uid=next(iter(activity_uids)),
            has_library__name=settings.requested_library_name,
        )
        BusinessLogicException.raise_if(
            len(requested) > 0,
            msg="Activity instances are not allowed to link to activity requests or placeholders",
        )

        # Set up the GroupingRoot and GroupingValue nodes
        # This method is only called when creating a new ActivityInstanceRoot & Value
        # node pair, so we need to create the GroupingRoot and GroupingValue nodes here.
        # Get the root node
        root_node = ActivityInstanceRoot.nodes.get(uid=ar.uid)
        grouping_root_node = ActivityInstanceGroupingRoot()
        grouping_root_node.save()
        root_node.has_grouping_root.connect(grouping_root_node)

        # Create a new grouping value node
        grouping_value_node = ActivityInstanceGroupingValue()
        grouping_value_node.save()
        grouping_root_node.has_latest_value.connect(grouping_value_node)
        grouping_root_node.latest_draft.connect(grouping_value_node)
        version_properties = {
            "start_date": datetime.datetime.now(datetime.timezone.utc),
            "status": "Draft",
            "author_id": self.author_id,
            "version": "0.1",
            "change_description": "Initial draft",
        }
        grouping_root_node.has_version.connect(
            grouping_value_node, properties=version_properties
        )

        for activity_grouping in ar.concept_vo.activity_groupings:
            # find related ActivityGrouping node
            activity_grouping_node = ListDistinct(
                ActivityGrouping.nodes.filter(
                    has_selected_group__has_version__uid=activity_grouping.activity_group_uid,
                    has_selected_subgroup__has_version__uid=activity_grouping.activity_subgroup_uid,
                    has_grouping__latest_final__uid=activity_grouping.activity_uid,
                ).resolve_subgraph()
            ).distinct()
            BusinessLogicException.raise_if(
                len(activity_grouping_node) == 0,
                msg=f"The ActivityGrouping node wasn't found for Activity Subgroup with UID '{activity_grouping.activity_subgroup_uid}'"
                f" and Activity Group with UID '{activity_grouping.activity_group_uid}'.",
            )
            activity_grouping_node = activity_grouping_node[0]
            # Must not link to archived group
            BusinessLogicException.raise_if(
                activity_grouping_node.has_selected_group.single()
                .has_latest_value.single()
                .has_library.single()
                .name
                == settings.archived_library_name,
                msg=f"Cannot link to archived ActivityGroup with UID '{activity_grouping.activity_uid}'.",
            )
            # Must not link to archived subgroup
            BusinessLogicException.raise_if(
                activity_grouping_node.has_selected_subgroup.single()
                .has_latest_value.single()
                .has_library.single()
                .name
                == settings.archived_library_name,
                msg=f"Cannot link to archived ActivitySubGroup with UID '{activity_grouping.activity_subgroup_uid}'.",
            )
            # link ActivityInstanceValue with ActivityGrouping node
            grouping_value_node.has_activity.connect(activity_grouping_node)

        activity_instance_class = ActivityInstanceClassRoot.nodes.get(
            uid=attrs.activity_instance_class_uid
        )
        value_node.activity_instance_class.connect(activity_instance_class)

        for item in attrs.activity_items:
            activity_item_class = ActivityItemClassRoot.nodes.get_or_none(
                uid=item.activity_item_class_uid
            )
            is_adam_param_specific = (
                item.is_adam_param_specific
                if getattr(
                    activity_item_class.has_activity_instance_class.relationship(
                        activity_instance_class
                    ),
                    "is_adam_param_specific_enabled",
                    False,
                )
                else False
            )
            activity_item_node = ActivityItem(
                is_adam_param_specific=is_adam_param_specific,
                is_activity_instance_id_specific=item.is_activity_instance_id_specific,
                text_value=item.text_value,
            )
            activity_item_node.save()
            activity_item_node.has_activity_item_class.connect(activity_item_class)

            for term in item.ct_terms:
                ct_term_root = CTTermRoot.nodes.get_or_none(uid=term.uid)
                selected_term_node = (
                    CTCodelistAttributesRepository().get_or_create_selected_term(
                        ct_term_root,
                        codelist_uid=term.codelist_uid,
                    )
                )
                activity_item_node.has_ct_term.connect(selected_term_node)

            if item.ct_codelist:
                codelist = CTCodelistRoot.nodes.get_or_none(uid=item.ct_codelist.uid)
                activity_item_node.has_codelist.connect(codelist)

            for unit in item.unit_definitions:
                unit_definition = UnitDefinitionRoot.nodes.get_or_none(uid=unit.uid)
                activity_item_node.has_unit_definition.connect(unit_definition)

            value_node.contains_activity_item.connect(activity_item_node)
        return value_node

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> ActivityInstanceAR:
        major, minor = input_dict["version"].split(".")
        activity_instance_ar = self.aggregate_class.from_repository_values(
            uid=input_dict["uid"],
            concept_vo=self.value_object_class.from_repository_values(
                nci_concept_id=input_dict.get("nci_concept_id"),
                nci_concept_name=input_dict.get("nci_concept_name"),
                name=input_dict["name"],
                name_sentence_case=input_dict["name_sentence_case"],
                activity_instance_class_uid=input_dict.get(
                    "activity_instance_class"
                ).get("uid"),
                activity_instance_class_name=input_dict.get(
                    "activity_instance_class"
                ).get("name"),
                definition=input_dict["definition"],
                abbreviation=input_dict.get("abbreviation"),
                is_research_lab=input_dict.get("is_research_lab", False),
                molecular_weight=input_dict.get("molecular_weight"),
                topic_code=input_dict["topic_code"],
                adam_param_code=input_dict.get("adam_param_code"),
                is_required_for_activity=input_dict.get(
                    "is_required_for_activity", False
                ),
                is_default_selected_for_activity=input_dict.get(
                    "is_default_selected_for_activity", False
                ),
                is_data_sharing=input_dict.get("is_data_sharing", False),
                is_legacy_usage=input_dict.get("is_legacy_usage", False),
                is_derived=input_dict.get("is_derived", False),
                legacy_description=input_dict.get("legacy_description"),
                activity_groupings=[
                    ActivityInstanceGroupingVO(
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
                        activity_uid=activity_grouping.get("activity").get("uid"),
                        activity_name=activity_grouping.get("activity").get("name"),
                        activity_version=f"{activity_grouping.get('activity').get('major_version')}.{activity_grouping.get('activity').get('minor_version')}",
                    )
                    for activity_grouping in input_dict.get("activity_groupings")
                ],
                activity_items=[
                    ActivityItemVO.from_repository_values(
                        is_adam_param_specific=activity_item.get(
                            "is_adam_param_specific"
                        ),
                        activity_item_class_uid=activity_item.get(
                            "activity_item_class_uid"
                        ),
                        activity_item_class_name=activity_item.get(
                            "activity_item_class_name"
                        ),
                        ct_codelist=(
                            CTCodelistItem(
                                uid=activity_item.get("ct_codelist")["uid"],
                                name=activity_item.get("ct_codelist")["name"],
                            )
                            if activity_item.get("ct_codelist")
                            else None
                        ),
                        ct_terms=[
                            CTTermItem(
                                uid=term["uid"],
                                name=term["name"],
                                codelist_uid=term["codelist_uid"],
                            )
                            for term in activity_item.get("ct_terms")
                        ],
                        unit_definitions=[
                            CompactUnitDefinition(
                                uid=unit["uid"],
                                name=unit["name"],
                                dimension_name=unit["dimension_name"],
                            )
                            for unit in activity_item.get("unit_definitions")
                        ],
                        text_value=activity_item.get("text_value"),
                        is_activity_instance_id_specific=activity_item.get(
                            "is_activity_instance_id_specific"
                        ),
                    )
                    for activity_item in input_dict.get("activity_items", [])
                ],
                activity_name=input_dict.get("activity_name"),
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
            groupings_item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("groupings_version", {}).get(
                    "change_description"
                ),
                status=LibraryItemStatus(
                    input_dict.get("groupings_version", {}).get("status")
                ),
                author_id=input_dict.get("groupings_version", {}).get("author_id"),
                author_username=UserInfoService.get_author_username_from_id(
                    input_dict.get("groupings_version", {}).get("author_id", "")
                ),
                start_date=convert_to_datetime(
                    value=input_dict.get("groupings_version", {}).get("start_date")
                ),
                end_date=convert_to_datetime(
                    value=input_dict.get("groupings_version", {}).get("end_date")
                ),
                major_version=int(
                    input_dict.get("groupings_version", {}).get("major_version", "0")
                ),
                minor_version=int(
                    input_dict.get("groupings_version", {}).get("minor_version", "0")
                ),
            ),
        )
        return activity_instance_ar

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ActivityInstanceRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ActivityInstanceValue,
        **_kwargs,
    ) -> ActivityInstanceAR:
        activity_instance_class = value.activity_instance_class.get()
        activity_items = value.contains_activity_item.all()
        activity_item_vos = []
        for activity_item in activity_items:
            activity_item_class_root = (
                activity_item.has_activity_item_class.get_or_none()
            )
            ct_terms = []
            unit_definitions = []
            for unit in activity_item.has_unit_definition.all():
                if (
                    ct_dimension := unit.has_version.single()
                    .has_ct_dimension.single()
                    .has_selected_term.single()
                ):
                    dimension_name = (
                        ct_dimension.has_name_root.single()
                        .has_latest_value.single()
                        .name
                    )
                else:
                    dimension_name = None

                unit_definitions.append(
                    CompactUnitDefinition(
                        uid=unit.uid,
                        name=unit.has_version.single().name,
                        dimension_name=dimension_name,
                    )
                )
            for term_context in activity_item.has_ct_term.all():
                term_root = term_context.has_selected_term.single()
                ct_terms.append(
                    CTTermItem(
                        uid=term_root.uid,
                        name=term_root.has_name_root.single().has_version.single().name,
                        codelist_uid=term_context.has_selected_codelist.single().uid,
                    )
                )
            if codelist := activity_item.has_codelist.get_or_none():
                name_root = codelist.has_name_root.get()
                name_value = name_root.has_latest_value.get()
                ct_codelist = CTCodelistItem(uid=codelist.uid, name=name_value.name)
            else:
                ct_codelist = None

            activity_item_vos.append(
                ActivityItemVO.from_repository_values(
                    is_adam_param_specific=activity_item.is_adam_param_specific,
                    activity_item_class_uid=activity_item_class_root.uid,
                    activity_item_class_name=activity_item_class_root.has_latest_value.get_or_none().name,
                    ct_codelist=ct_codelist,
                    ct_terms=ct_terms,
                    unit_definitions=unit_definitions,
                    text_value=activity_item.text_value,
                    is_activity_instance_id_specific=activity_item.is_activity_instance_id_specific,
                )
            )
        groupings_root = root.has_grouping_root.single()
        groupings_value = groupings_root.has_latest_value.single()
        activity_groupings_nodes = groupings_value.has_activity.all()
        groupings_relationships = groupings_value.has_version.all_relationships(
            groupings_root
        )

        groupings_relationship = max(
            groupings_relationships,
            key=lambda r: r.start_date,
        )
        activity_groupings = []
        activity_name = None
        for activity_grouping in activity_groupings_nodes:
            activity_value_node = activity_grouping.has_grouping.get()
            # ActivityInstance can only link to a single Activity node then it's safe to take a activity_name
            # from the random ActivityValue node related to any ActivityGroupings node linked to ActivityInstance
            activity_name = activity_value_node.name
            # Prefer the Final version of each linked entity. If no Final version exists, fall back to the highest version.
            # The sort key (is_final, version_tuple) ensures Final always ranks above Draft/Retired,
            # and within the same status the highest version number wins.
            # Activity
            activity_root = activity_value_node.has_version.single()
            all_activity_rels = activity_value_node.has_version.all_relationships(
                activity_root
            )
            latest_activity = max(
                all_activity_rels,
                key=lambda r: (
                    r.status == LibraryItemStatus.FINAL.value,
                    version_string_to_tuple(r.version),
                ),
            )
            # ActivityGroup
            activity_group_value = activity_grouping.has_selected_group.get()
            activity_group_root = activity_group_value.has_version.single()
            all_group_rels = activity_group_value.has_version.all_relationships(
                activity_group_root
            )
            latest_group = max(
                all_group_rels,
                key=lambda r: (
                    r.status == LibraryItemStatus.FINAL.value,
                    version_string_to_tuple(r.version),
                ),
            )
            # ActivitySubGroup
            activity_subgroup_value = activity_grouping.has_selected_subgroup.get()
            activity_subgroup_root = activity_subgroup_value.has_version.single()
            all_subgroup_rels = activity_subgroup_value.has_version.all_relationships(
                activity_subgroup_root
            )
            latest_subgroup = max(
                all_subgroup_rels,
                key=lambda r: (
                    r.status == LibraryItemStatus.FINAL.value,
                    version_string_to_tuple(r.version),
                ),
            )

            activity_groupings.append(
                ActivityInstanceGroupingVO(
                    activity_group_uid=activity_group_root.uid,
                    activity_group_version=latest_group.version,
                    activity_subgroup_uid=activity_subgroup_root.uid,
                    activity_subgroup_version=latest_subgroup.version,
                    activity_uid=activity_root.uid,
                    activity_version=latest_activity.version,
                )
            )

        return self.aggregate_class.from_repository_values(
            uid=root.uid,
            concept_vo=self.value_object_class.from_repository_values(
                nci_concept_id=value.nci_concept_id,
                nci_concept_name=value.nci_concept_name,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                activity_instance_class_uid=activity_instance_class.uid,
                activity_instance_class_name=activity_instance_class.has_latest_value.get().name,
                definition=value.definition,
                abbreviation=value.abbreviation,
                is_research_lab=(
                    value.is_research_lab if value.is_research_lab else False
                ),
                molecular_weight=value.molecular_weight,
                topic_code=value.topic_code,
                adam_param_code=value.adam_param_code,
                is_required_for_activity=(
                    value.is_required_for_activity
                    if value.is_required_for_activity
                    else False
                ),
                is_default_selected_for_activity=(
                    value.is_default_selected_for_activity
                    if value.is_default_selected_for_activity
                    else False
                ),
                is_data_sharing=(
                    value.is_data_sharing if value.is_data_sharing else False
                ),
                is_legacy_usage=(
                    value.is_legacy_usage if value.is_legacy_usage else False
                ),
                is_derived=value.is_derived if value.is_derived else False,
                legacy_description=value.legacy_description,
                activity_groupings=activity_groupings,
                activity_items=activity_item_vos,
                activity_name=activity_name,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            groupings_item_metadata=self._library_item_metadata_vo_from_relation(
                groupings_relationship
            ),
        )

    def specific_alias_clause(self, **kwargs) -> str:
        return """
        WITH *,
            concept_value.nci_concept_name AS nci_concept_name,
            concept_value.molecular_weight AS molecular_weight,
            concept_value.topic_code AS topic_code,
            concept_value.adam_param_code AS adam_param_code,
            coalesce(concept_value.is_research_lab, false) AS is_research_lab,
            coalesce(concept_value.is_required_for_activity, false) AS is_required_for_activity,
            coalesce(concept_value.is_default_selected_for_activity, false) AS is_default_selected_for_activity,
            coalesce(concept_value.is_data_sharing, false) AS is_data_sharing,
            coalesce(concept_value.is_legacy_usage, false) AS is_legacy_usage,
            coalesce(concept_value.is_derived, false) AS is_derived,
            concept_value.legacy_description AS legacy_description,
            
            head([(concept_value)-[:ACTIVITY_INSTANCE_CLASS]->
            (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue)
                | {uid:activity_instance_class_root.uid, name:activity_instance_class_value.name}]) AS activity_instance_class,
            [(concept_value)-[:CONTAINS_ACTIVITY_ITEM]->(activity_item:ActivityItem)
            <-[:HAS_ACTIVITY_ITEM]-(activity_item_class_root:ActivityItemClassRoot)-[:LATEST]->
            (activity_item_class_value:ActivityItemClassValue)
                | {
                    activity_item_class_uid: activity_item_class_root.uid,
                    activity_item_class_name: activity_item_class_value.name,
                    ct_terms: COLLECT {
                        MATCH (activity_item)-[:HAS_CT_TERM]->(ct_term_context:CTTermContext)
                        -[:HAS_SELECTED_TERM]->(term_root:CTTermRoot)
                        -[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)
                        -[:LATEST]->(term_name_value:CTTermNameValue)
                        MATCH (ct_term_context)-[:HAS_SELECTED_CODELIST]->(codelist_root:CTCodelistRoot)
                        MATCH (ct_codelist_term:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root)
                        RETURN {uid: term_root.uid, name: term_name_value.name, codelist_uid: codelist_root.uid, submission_value: ct_codelist_term.submission_value}
                    },
                    ct_codelist: head([(activity_item)-[:HAS_CODELIST]->(ccr:CTCodelistRoot)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST]-(ccnv:CTCodelistNameValue) | {uid: ccr.uid, name: ccnv.name}]),
                    unit_definitions: [(activity_item)-[:HAS_UNIT_DEFINITION]->(unit_definition_root:UnitDefinitionRoot)-[:LATEST]->(unit_definition_value:UnitDefinitionValue)-[:HAS_CT_DIMENSION]-(:CTTermRoot)-[:HAS_NAME_ROOT]->(CTTermNamesRoot)-[:LATEST]->(dimension_value:CTTermNameValue) | {uid: unit_definition_root.uid, name: unit_definition_value.name, dimension_name: dimension_value.name}],
                    is_adam_param_specific: activity_item.is_adam_param_specific,
                    is_activity_instance_id_specific: activity_item.is_activity_instance_id_specific,
                    text_value: activity_item.text_value
                }] AS activity_items,
            head([(concept_root)-[:HAS_GROUPING_ROOT]-(groupings_root:ActivityInstanceGroupingRoot)-[:LATEST]->(groupings_value:ActivityInstanceGroupingValue)-[:HAS_ACTIVITY]->(activity_grouping:ActivityGrouping)<-[:HAS_GROUPING]-(activity_value) | activity_value.name]) as activity_name,
            apoc.coll.toSet([(concept_root)-[:HAS_GROUPING_ROOT]-(groupings_root:ActivityInstanceGroupingRoot)-[:LATEST]->(groupings_value:ActivityInstanceGroupingValue)-[:HAS_ACTIVITY]->(activity_grouping:ActivityGrouping)
            | {
                activity: head(apoc.coll.sortMulti([(activity_grouping)<-[:HAS_GROUPING]-(activity_value:ActivityValue)<-[has_version:HAS_VERSION]-
                    (activity_root:ActivityRoot) | 
                    {
                        uid: activity_root.uid,
                        name: activity_value.name,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1])
                    }], ['major_version', 'minor_version'])),
                activity_subgroup: head(apoc.coll.sortMulti([(activity_grouping)-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)<-[has_version:HAS_VERSION]-
                    (activity_subgroup_root:ActivitySubGroupRoot) | 
                    {
                        uid: activity_subgroup_root.uid,
                        name: activity_subgroup_value.name,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1])
                    }], ['major_version', 'minor_version'])), 
                activity_group: head(apoc.coll.sortMulti([(activity_grouping)-[:HAS_SELECTED_GROUP]->(activity_group_value:ActivityGroupValue)<-[has_version:HAS_VERSION]-
                    (activity_group_root:ActivityGroupRoot) | 
                    {
                        uid: activity_group_root.uid,
                        name: activity_group_value.name,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1])
                    }], ['major_version', 'minor_version']))
            }]) AS activity_groupings,
            head(
                apoc.coll.sortMulti([
                    (concept_root)-[:HAS_GROUPING_ROOT]-(groupings_root:ActivityInstanceGroupingRoot)-[groupings_has_version:HAS_VERSION]->
                    (groupings_value:ActivityInstanceGroupingValue) WHERE (groupings_root)-[:LATEST]->(groupings_value)
                    | {
                        status: groupings_has_version.status,
                        author_id: groupings_has_version.author_id,
                        version: groupings_has_version.version,
                        major_version: toInteger(split(groupings_has_version.version,'.')[0]),
                        minor_version: toInteger(split(groupings_has_version.version,'.')[1]),
                        change_description: groupings_has_version.change_description,
                        start_date: groupings_has_version.start_date,
                        end_date: groupings_has_version.end_date
                    }
                ], ['major_version', 'minor_version', 'start_date'])
            ) AS groupings_version
        """

    def minimal_count_query(
        self,
        filter_by: dict[str, dict[str, Any]] | None,
        return_all_versions: bool,
        **kwargs,
    ) -> tuple[str | None, dict[str, Any]]:
        """Provide a fast count path for status query param on activity instances.

        The endpoint-level `status` query parameter should match either the activity
        instance status or the latest groupings status.
        """
        status = kwargs.get("status")
        if status is None:
            return super().minimal_count_query(
                filter_by=filter_by,
                return_all_versions=return_all_versions,
                **kwargs,
            )

        # Keep generic path for non-latest queries and for additional filters that
        # this fast count query does not include.
        if kwargs.get("version", None) is not None or return_all_versions:
            return None, {}
        if filter_by and len(filter_by) > 0:
            return None, {}
        if any(
            kwargs.get(filter_name) is not None
            for filter_name in (
                "activity_instance_names",
                "activity_names",
                "activity_subgroup_names",
                "activity_group_names",
                "activity_instance_class_names",
            )
        ):
            return None, {}

        concept_label = self.root_class.__label__
        concept_value_label = self.value_class.__label__

        where_clauses = [
            "hv.end_date IS NULL",
            """
            (
                hv.status = $status
                OR EXISTS {
                    MATCH (concept_root)-[:HAS_GROUPING_ROOT]->(groupings_root:ActivityInstanceGroupingRoot)
                          -[groupings_has_version:HAS_VERSION]->(groupings_value:ActivityInstanceGroupingValue)
                    WHERE (groupings_root)-[:LATEST]->(groupings_value)
                      AND groupings_has_version.end_date IS NULL
                      AND groupings_has_version.status = $status
                }
            )
            """,
        ]
        params: dict[str, Any] = {"status": status}

        library_name = self.filter_query_parameters.get("library_name")
        if library_name is not None:
            where_clauses.append(
                "EXISTS { MATCH (:Library {name: $library_name})-[:CONTAINS_CONCEPT]->(concept_root) }"
            )
            params["library_name"] = library_name

        uids = self.filter_query_parameters.get("uids")
        if uids is not None:
            where_clauses.append("concept_root.uid IN $uids")
            params["uids"] = uids

        query = f"""
            MATCH (concept_root:{concept_label})-[hv:HAS_VERSION]->(concept_value:{concept_value_label})
            WHERE {' AND '.join(where_clauses)}
            RETURN count(DISTINCT concept_root) AS count
        """
        return query, params

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict[Any, Any]]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library, **kwargs)
        filter_parameters = []
        if kwargs.get("activity_instance_names") is not None:
            activity_instance_names = kwargs.get("activity_instance_names")
            filter_by_activity_instance_names = (
                "concept_value.name IN $activity_instance_names"
            )
            filter_parameters.append(filter_by_activity_instance_names)
            filter_query_parameters["activity_instance_names"] = activity_instance_names
        if kwargs.get("activity_names") is not None:
            activity_names = kwargs.get("activity_names")
            filter_by_activity_names = (
                "size([(concept_root)-[:HAS_GROUPING_ROOT]->(:ActivityInstanceGroupingRoot)"
                "-[:LATEST]->(:ActivityInstanceGroupingValue)-[:HAS_ACTIVITY]->(:ActivityGrouping)"
                "<-[:HAS_GROUPING]-(activity_value:ActivityValue) "
                "WHERE activity_value.name IN $activity_names | activity_value.name]) > 0"
            )
            filter_parameters.append(filter_by_activity_names)
            filter_query_parameters["activity_names"] = activity_names
        if kwargs.get("activity_subgroup_names") is not None:
            activity_subgroup_names = kwargs.get("activity_subgroup_names")
            filter_by_activity_subgroup_names = (
                "size([(concept_root)-[:HAS_GROUPING_ROOT]->(:ActivityInstanceGroupingRoot)"
                "-[:LATEST]->(:ActivityInstanceGroupingValue)-[:HAS_ACTIVITY]->(:ActivityGrouping)"
                "-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue) "
                "WHERE activity_subgroup_value.name IN $activity_subgroup_names | activity_subgroup_value.name]) > 0"
            )
            filter_parameters.append(filter_by_activity_subgroup_names)
            filter_query_parameters["activity_subgroup_names"] = activity_subgroup_names
        if kwargs.get("activity_group_names") is not None:
            activity_group_names = kwargs.get("activity_group_names")
            filter_by_activity_group_names = (
                "size([(concept_root)-[:HAS_GROUPING_ROOT]->(:ActivityInstanceGroupingRoot)"
                "-[:LATEST]->(:ActivityInstanceGroupingValue)-[:HAS_ACTIVITY]->(:ActivityGrouping)"
                "-[:HAS_SELECTED_GROUP]->(activity_group_value:ActivityGroupValue) "
                "WHERE activity_group_value.name IN $activity_group_names | activity_group_value.name]) > 0"
            )
            filter_parameters.append(filter_by_activity_group_names)
            filter_query_parameters["activity_group_names"] = activity_group_names
        if kwargs.get("activity_instance_class_names") is not None:
            instance_class_names = kwargs.get("activity_instance_class_names")
            filter_by_instance_classes = (
                "size([(concept_value)-[:ACTIVITY_INSTANCE_CLASS]->(:ActivityInstanceClassRoot)"
                "-[:LATEST]->(instance_class_value:ActivityInstanceClassValue)"
                "WHERE instance_class_value.name IN $activity_instance_class_names | instance_class_value.name]) > 0"
            )
            filter_parameters.append(filter_by_instance_classes)
            filter_query_parameters["activity_instance_class_names"] = (
                instance_class_names
            )
        if kwargs.get("status") is not None:
            status = kwargs.get("status")
            filter_by_status_or_groupings_status = (
                "("
                "size([(concept_root)-[concept_has_version:HAS_VERSION]->(concept_value) "
                "WHERE concept_has_version.end_date IS NULL "
                "AND concept_has_version.status = $status | concept_has_version]) > 0 "
                "OR "
                "size([(concept_root)-[:HAS_GROUPING_ROOT]->(groupings_root:ActivityInstanceGroupingRoot)"
                "-[groupings_has_version:HAS_VERSION]->(groupings_value:ActivityInstanceGroupingValue) "
                "WHERE (groupings_root)-[:LATEST]->(groupings_value) "
                "AND groupings_has_version.end_date IS NULL "
                "AND groupings_has_version.status = $status | groupings_has_version]) > 0"
                ")"
            )
            filter_parameters.append(filter_by_status_or_groupings_status)
            filter_query_parameters["status"] = status
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

    @classmethod
    def format_filter_sort_keys(cls, key: str) -> str:
        """Map API keys to Cypher aliases used by the activity instance list query."""
        groupings_version_key_map = {
            "groupings_status": "groupings_version.status",
            "groupings_version": "groupings_version.version",
            "groupings_author_username": "groupings_version.author_id",
            "groupings_author_id": "groupings_version.author_id",
            "groupings_major_version": "groupings_version.major_version",
            "groupings_minor_version": "groupings_version.minor_version",
            "groupings_change_description": "groupings_version.change_description",
            "groupings_start_date": "groupings_version.start_date",
            "groupings_end_date": "groupings_version.end_date",
        }
        return groupings_version_key_map.get(key, key)

    def get_activity_instance_overview(
        self, uid: str, version: str | None = None
    ) -> dict[str, Any]:
        if version:
            params = {"uid": uid, "version": version}
            match = """
                    MATCH (activity_instance_root:ActivityInstanceRoot {uid:$uid})
                    CALL (activity_instance_root) {
                        MATCH (activity_instance_root)-[hv:HAS_VERSION {version:$version}]->(aiv:ActivityInstanceValue)
                        WITH hv, aiv
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs, collect (aiv) as aivs
                        RETURN last(hvs) as has_version, last(aivs) as activity_instance_value
                    }
                    """
        else:
            params = {"uid": uid}
            match = """
                    MATCH (activity_instance_root:ActivityInstanceRoot {uid:$uid})-[:LATEST]->(activity_instance_value:ActivityInstanceValue)
                    CALL (activity_instance_root, activity_instance_value) {
                        MATCH (activity_instance_root)-[hv:HAS_VERSION]-(activity_instance_value)
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
        WITH activity_instance_root,activity_instance_value, has_version,
            head([(library)-[:CONTAINS_CONCEPT]->(activity_instance_root) | library.name]) AS instance_library_name,
            head([(activity_instance_value)-[:ACTIVITY_INSTANCE_CLASS]->
            (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue) 
            | activity_instance_class_value]) AS activity_instance_class,
            [(activity_instance_root)-[versions:HAS_VERSION]->(:ActivityInstanceValue) | versions.version] as all_versions
        CALL (activity_instance_root, has_version) {
            MATCH (activity_instance_root)-[:HAS_GROUPING_ROOT]->(:ActivityInstanceGroupingRoot)-[groupings_has_version:HAS_VERSION]->(:ActivityInstanceGroupingValue)
            WHERE (groupings_has_version.start_date < coalesce(has_version.end_date, datetime()) 
                AND has_version.start_date < coalesce(groupings_has_version.end_date, datetime()))
            WITH groupings_has_version
            ORDER BY
                    toInteger(split(groupings_has_version.version, '.')[0]) DESC,
                    toInteger(split(groupings_has_version.version, '.')[1]) DESC,
                    groupings_has_version.start_date DESC
            WITH collect(DISTINCT groupings_has_version.version) as groupings_versions
            RETURN groupings_versions
        }
        WITH *,
            apoc.coll.toSet([(activity_instance_value)-[:CONTAINS_ACTIVITY_ITEM]->(activity_item)
            <-[HAS_ACTIVITY_ITEM]-(activity_item_class_root)-[:LATEST]->(activity_item_class_value) | 
            {
                activity_item_class_uid: activity_item_class_root.uid,
                activity_item_class: activity_item_class_value,
                activity_item_class_role: head([(activity_item_class_value)-[:HAS_ROLE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(role_value) | role_value.name]),
                activity_item_class_data_type: head([(activity_item_class_value)-[:HAS_DATA_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(data_type_value) | data_type_value.name]),
                activity_item: activity_item,
                ct_terms: COLLECT {
                    MATCH (activity_item)-[:HAS_CT_TERM]->(ct_term_context:CTTermContext)
                    -[:HAS_SELECTED_TERM]->(term_root:CTTermRoot)
                    -[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)
                    -[:LATEST]->(term_name_value:CTTermNameValue)
                    MATCH (ct_term_context)-[:HAS_SELECTED_CODELIST]->(codelist_root:CTCodelistRoot)
                    MATCH (ct_codelist_term:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root)
                    RETURN {uid: term_root.uid, name: term_name_value.name, codelist_uid: codelist_root.uid, submission_value: ct_codelist_term.submission_value}
                },
                ct_codelist: head([(activity_item)-[:HAS_CODELIST]->(ccr:CTCodelistRoot)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST]->(ccnv:CTCodelistNameValue) | {uid: ccr.uid, name: ccnv.name}]),
                unit_definitions: [
                    (activity_item)-[:HAS_UNIT_DEFINITION]->(unit_definition_root:UnitDefinitionRoot)-[:LATEST]->(unit_definition_value:UnitDefinitionValue)
                    -[:HAS_CT_DIMENSION]-(:CTTermContext)-[:HAS_SELECTED_TERM]-(:CTTermRoot)-[:HAS_NAME_ROOT]->(CTTermNamesRoot)-[:LATEST]->(dimension_value:CTTermNameValue)
                    | {uid: unit_definition_root.uid, name: unit_definition_value.name, dimension_name: dimension_value.name}
                ],
                is_adam_param_specific: activity_item.is_adam_param_specific,
                is_activity_instance_id_specific: activity_item.is_activity_instance_id_specific,
                text_value: activity_item.text_value
            }
            ]) AS activity_items
        CALL (has_version) {
            OPTIONAL MATCH (author:User)
            WHERE author.user_id = has_version.author_id
            RETURN author
        }
        WITH DISTINCT
            activity_instance_root,
            activity_instance_value,
            instance_library_name,
            activity_instance_class,
            groupings_versions,
            activity_items,
            has_version {
                .*,
                author_username: coalesce(author.username, has_version.author_id)
            } AS has_version,
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
        RETURN *
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

    def get_cosmos_activity_instance_overview(self, uid: str) -> dict[str, Any]:
        query = """
        MATCH (activity_instance_root:ActivityInstanceRoot {uid:$uid})-[:LATEST]->(activity_instance_value:ActivityInstanceValue)
        MATCH (activity_instance_root)-[:HAS_GROUPING_ROOT]->(:ActivityInstanceGroupingRoot)-[:LATEST]->(activity_instance_groupings_value:ActivityInstanceGroupingValue)
        WITH activity_instance_root,activity_instance_value, activity_instance_groupings_value,
            head([(library)-[:CONTAINS_CONCEPT]->(activity_instance_root) | library.name]) AS instance_library_name,
            head([(activity_instance_value)-[:ACTIVITY_INSTANCE_CLASS]->
            (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue) 
            | activity_instance_class_value.name]) AS activity_instance_class_name
        WITH *,
            [(activity_instance_groupings_value)-[:HAS_ACTIVITY]->(:ActivityGrouping)-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value.name] AS activity_subgroups,
            apoc.coll.toSet([(activity_instance_value)-[:CONTAINS_ACTIVITY_ITEM]->(activity_item)
            <-[HAS_ACTIVITY_ITEM]-(activity_item_class_root)-[:LATEST]->(activity_item_class_value) | 
            {
                nci_concept_id: activity_item_class_value.nci_concept_id,
                name: activity_item_class_value.name,
                type: head([(activity_item_class_value)-[:HAS_DATA_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(data_type_value) | data_type_value.name]),
                example_set: [(activity_item)-[:HAS_CT_TERM]->(term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue) | {uid: term_root.uid, name: term_name_value.name}] + [(activity_item)-[:HAS_UNIT_DEFINITION]->(unit_definition_root:UnitDefinitionRoot)-[:LATEST]->(unit_definition_value:UnitDefinitionValue) | {uid: unit_definition_root.uid, name: unit_definition_value.name}]
            }
            ]) AS activity_items
        WITH DISTINCT
            {
                uid: activity_instance_root.uid,
                name: activity_instance_value.name,
                name_sentence_case: activity_instance_value.name_sentence_case,
                definition: activity_instance_value.definition,
                abbreviation: activity_instance_value.abbreviation,
                nci_concept_id: activity_instance_value.nci_concept_id,
                is_required_for_activity: activity_instance_value.is_required_for_activity,
                is_defaulted_for_activity: activity_instance_value.is_defaulted_for_activity
            } AS activity_instance_value,
            activity_instance_class_name,
            activity_subgroups,
            activity_items
        RETURN *
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
            MATCH (concept_root:ActivityInstanceRoot)-[version:HAS_VERSION]->(concept_value:ActivityInstanceValue)
        """

    def get_all_activity_instances_for_activity_grouping(
        self,
        activity_uid: str,
        activity_subgroup_uid: str,
        activity_group_uid: str,
        filter_by_boolean_flags: bool = False,
    ) -> list[tuple[ActivityInstanceRoot, ActivityInstanceValue]]:
        query = """
            MATCH (:ActivityRoot {uid:$activity_uid})-[:LATEST_FINAL]->(:ActivityValue)-[:HAS_GROUPING]->(activity_grouping:ActivityGrouping)
            MATCH (activity_grouping)-[:HAS_SELECTED_SUBGROUP]->(:ActivitySubGroupValue)<-[:HAS_VERSION]-(:ActivitySubGroupRoot {uid:$activity_subgroup_uid})
            MATCH (activity_grouping)-[:HAS_SELECTED_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(:ActivityGroupRoot {uid:$activity_group_uid})
            MATCH (activity_grouping)<-[:HAS_ACTIVITY]-(activity_instance_groupings_value:ActivityInstanceGroupingValue)<-[:LATEST_FINAL]-(activity_instance_groupings_root:ActivityInstanceGroupingRoot)
            MATCH (activity_instance_groupings_root)<-[:HAS_GROUPING_ROOT]-(activity_instance_root:ActivityInstanceRoot)-[:LATEST]->(activity_instance_value:ActivityInstanceValue)
            MATCH (activity_instance_root)-[:LATEST_FINAL]->(activity_instance_value)
            OPTIONAL MATCH (activity_instance_root)-[retired:HAS_VERSION {status: "Retired"}]->(activity_instance_value) WHERE retired.end_date IS NULL
            WITH activity_instance_root, activity_instance_value WHERE retired IS NULL
            WITH DISTINCT activity_instance_root, activity_instance_value
            ORDER BY activity_instance_value.is_required_for_activity DESC, activity_instance_value.is_defaulted_for_activity DESC
            RETURN activity_instance_root as root, activity_instance_value as value
        """
        nodes, _ = db.cypher_query(
            query,
            params={
                "activity_uid": activity_uid,
                "activity_subgroup_uid": activity_subgroup_uid,
                "activity_group_uid": activity_group_uid,
            },
            resolve_objects=True,
        )
        required_instances = []
        defaulted_instances: list[Any] = []
        other_instances: list[Any] = []
        all_instances = []
        for activity_instance in nodes:
            root: ActivityInstanceRoot = activity_instance[0]
            value: ActivityInstanceValue = activity_instance[1]
            all_instances.append((root, value))
            if value.is_required_for_activity:
                required_instances.append((root, value))
            elif (
                value.is_default_selected_for_activity and len(defaulted_instances) == 0
            ):
                defaulted_instances.append((root, value))
            elif len(other_instances) == 0:
                other_instances.append((root, value))
        if filter_by_boolean_flags:
            if required_instances:
                return required_instances
            if defaulted_instances:
                return defaulted_instances
            return other_instances
        return all_instances

    def specific_header_match_clause_lite(self, field_name: str) -> str | None:
        """This is a lightweight version of the header match clause.
        It should fetch only the required field, without supporting wildcard filtering.
        """

        if field_name in [
            "groupings_status",
            "groupings_version",
            "groupings_author_username",
            "groupings_start_date",
            "groupings_end_date",
        ]:
            groupings_value_alias = {
                "groupings_status": "latest_groupings_version.status",
                "groupings_version": "latest_groupings_version.version",
                "groupings_author_username": "coalesce(author.username, latest_groupings_version.author_id)",
                "groupings_start_date": "latest_groupings_version.start_date",
                "groupings_end_date": "latest_groupings_version.end_date",
            }[field_name]
            return f"""
                CALL (concept_root) {{
                    MATCH (concept_root)-[:HAS_GROUPING_ROOT]->(groupings_root:ActivityInstanceGroupingRoot)-[groupings_has_version:HAS_VERSION]->(:ActivityInstanceGroupingValue)
                    WHERE (groupings_root)-[:LATEST]->(:ActivityInstanceGroupingValue)
                    WITH groupings_has_version
                    ORDER BY
                        toInteger(split(groupings_has_version.version, '.')[0]) DESC,
                        toInteger(split(groupings_has_version.version, '.')[1]) DESC,
                        groupings_has_version.start_date DESC
                    RETURN head(collect(groupings_has_version)) AS latest_groupings_version
                }}
                OPTIONAL MATCH (author:User)
                WHERE author.user_id = latest_groupings_version.author_id
                WITH concept_root, concept_value, {groupings_value_alias} AS {field_name}
                """

        if field_name == "activity_name":
            return """
                WITH concept_root, concept_value,
                     head([(concept_root)-[:HAS_GROUPING_ROOT]->(:ActivityInstanceGroupingRoot)-[:LATEST]->(:ActivityInstanceGroupingValue)-[:HAS_ACTIVITY]->(activity_grouping)<-[:HAS_GROUPING]-(activity_value) | activity_value.name]) as activity_name
                """

        if field_name == "activity_instance_class.name":
            return """
                WITH concept_value,
                     head([(concept_value)-[:ACTIVITY_INSTANCE_CLASS]->
                            (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue)
                            | activity_instance_class_value.name]) AS activity_instance_class_name
                """

        return None


class ActivityInstanceAttributesRepository(
    ConceptGenericRepository[ActivityInstanceAttributesAR]
):
    root_class = ActivityInstanceRoot
    value_class = ActivityInstanceValue
    aggregate_class = ActivityInstanceAttributesAR
    value_object_class = ActivityInstanceAttributesVO
    return_model = ActivityInstanceAttributes

    def _create_new_value_node(
        self, ar: ActivityInstanceAttributesAR
    ) -> ActivityInstanceValue:
        value_node: ActivityInstanceValue = super()._create_new_value_node(ar=ar)
        value_node.is_research_lab = ar.concept_vo.is_research_lab
        if ar.concept_vo.molecular_weight:
            value_node.molecular_weight = ar.concept_vo.molecular_weight
        if ar.concept_vo.topic_code:
            value_node.topic_code = ar.concept_vo.topic_code
        if ar.concept_vo.adam_param_code:
            value_node.adam_param_code = ar.concept_vo.adam_param_code
        value_node.is_required_for_activity = ar.concept_vo.is_required_for_activity
        value_node.is_default_selected_for_activity = (
            ar.concept_vo.is_default_selected_for_activity
        )
        value_node.is_data_sharing = ar.concept_vo.is_data_sharing
        value_node.is_legacy_usage = ar.concept_vo.is_legacy_usage
        value_node.is_derived = ar.concept_vo.is_derived
        if ar.concept_vo.legacy_description:
            value_node.legacy_description = ar.concept_vo.legacy_description

        value_node.save()

        activity_instance_class = ActivityInstanceClassRoot.nodes.get(
            uid=ar.concept_vo.activity_instance_class_uid
        )
        value_node.activity_instance_class.connect(activity_instance_class)

        for item in ar.concept_vo.activity_items:
            activity_item_class = ActivityItemClassRoot.nodes.get_or_none(
                uid=item.activity_item_class_uid
            )
            is_adam_param_specific = (
                item.is_adam_param_specific
                if getattr(
                    activity_item_class.has_activity_instance_class.relationship(
                        activity_instance_class
                    ),
                    "is_adam_param_specific_enabled",
                    False,
                )
                else False
            )
            activity_item_node = ActivityItem(
                is_adam_param_specific=is_adam_param_specific,
                is_activity_instance_id_specific=item.is_activity_instance_id_specific,
                text_value=item.text_value,
            )
            activity_item_node.save()
            activity_item_node.has_activity_item_class.connect(activity_item_class)

            for term in item.ct_terms:
                ct_term_root = CTTermRoot.nodes.get_or_none(uid=term.uid)
                selected_term_node = (
                    CTCodelistAttributesRepository().get_or_create_selected_term(
                        ct_term_root,
                        codelist_uid=term.codelist_uid,
                    )
                )
                activity_item_node.has_ct_term.connect(selected_term_node)

            if item.ct_codelist:
                codelist = CTCodelistRoot.nodes.get_or_none(uid=item.ct_codelist.uid)
                activity_item_node.has_codelist.connect(codelist)

            for unit in item.unit_definitions:
                unit_definition = UnitDefinitionRoot.nodes.get_or_none(uid=unit.uid)
                activity_item_node.has_unit_definition.connect(unit_definition)

            value_node.contains_activity_item.connect(activity_item_node)
        return value_node

    def _has_item_data_changed(self, ar_items, value_item_nodes):
        ar_activity_items = []
        for item in ar_items:
            ar_activity_items.append(
                {
                    "is_adam_param_specific": item.is_adam_param_specific,
                    "is_activity_instance_id_specific": item.is_activity_instance_id_specific,
                    "class": item.activity_item_class_uid,
                    "units": {unit.uid for unit in item.unit_definitions},
                    "terms": {(term.uid, term.codelist_uid) for term in item.ct_terms},
                    "text_value": item.text_value,
                    "ct_codelist": item.ct_codelist.uid if item.ct_codelist else None,
                }
            )

        value_activity_items = []
        for activity_item_node in value_item_nodes:
            item_class_uid = activity_item_node.has_activity_item_class.get().uid
            unit_nodes = activity_item_node.has_unit_definition.all()
            ct_terms = [
                {
                    "uid": term_context.has_selected_term.single().uid,
                    "codelist_uid": term_context.has_selected_codelist.single().uid,
                }
                for term_context in activity_item_node.has_ct_term.all()
            ]
            codelist_node = activity_item_node.has_codelist.get_or_none()

            value_activity_items.append(
                {
                    "is_adam_param_specific": activity_item_node.is_adam_param_specific,
                    "is_activity_instance_id_specific": activity_item_node.is_activity_instance_id_specific,
                    "class": item_class_uid,
                    "units": {unit_node.uid for unit_node in unit_nodes},
                    "terms": {
                        (ct_term["uid"], ct_term["codelist_uid"])
                        for ct_term in ct_terms
                    },
                    "text_value": activity_item_node.text_value,
                    "ct_codelist": codelist_node.uid if codelist_node else None,
                }
            )
        for item in ar_activity_items:
            if item not in value_activity_items:
                return True
        for item in value_activity_items:
            if item not in ar_activity_items:
                return True
        return False

    def _has_data_changed(
        self, ar: ActivityInstanceAttributesAR, value: ActivityInstanceValue
    ) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)
        are_props_changed = (
            ar.concept_vo.molecular_weight != value.molecular_weight
            or ar.concept_vo.topic_code != value.topic_code
            or ar.concept_vo.adam_param_code != value.adam_param_code
            or bool(ar.concept_vo.is_research_lab) != bool(value.is_research_lab)
            or bool(ar.concept_vo.is_required_for_activity)
            != bool(value.is_required_for_activity)
            or bool(ar.concept_vo.is_default_selected_for_activity)
            != bool(value.is_default_selected_for_activity)
            or bool(ar.concept_vo.is_data_sharing) != bool(value.is_data_sharing)
            or bool(ar.concept_vo.is_legacy_usage) != bool(value.is_legacy_usage)
            or bool(ar.concept_vo.is_derived) != bool(value.is_derived)
            or ar.concept_vo.legacy_description != value.legacy_description
        )

        item_data_changed = self._has_item_data_changed(
            ar.concept_vo.activity_items, value.contains_activity_item.all()
        )

        are_rels_changed = (
            ar.concept_vo.activity_instance_class_uid
            != value.activity_instance_class.get().uid
            or item_data_changed
        )
        return are_concept_properties_changed or are_props_changed or are_rels_changed

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> ActivityInstanceAttributesAR:
        major, minor = input_dict["version"].split(".")
        activity_instance_ar = self.aggregate_class.from_repository_values(
            uid=input_dict["uid"],
            concept_vo=self.value_object_class.from_repository_values(
                nci_concept_id=input_dict.get("nci_concept_id"),
                nci_concept_name=input_dict.get("nci_concept_name"),
                name=input_dict["name"],
                name_sentence_case=input_dict["name_sentence_case"],
                activity_instance_class_uid=input_dict.get(
                    "activity_instance_class"
                ).get("uid"),
                activity_instance_class_name=input_dict.get(
                    "activity_instance_class"
                ).get("name"),
                definition=input_dict["definition"],
                abbreviation=input_dict.get("abbreviation"),
                is_research_lab=input_dict.get("is_research_lab", False),
                molecular_weight=input_dict.get("molecular_weight"),
                topic_code=input_dict["topic_code"],
                adam_param_code=input_dict.get("adam_param_code"),
                is_required_for_activity=input_dict.get(
                    "is_required_for_activity", False
                ),
                is_default_selected_for_activity=input_dict.get(
                    "is_default_selected_for_activity", False
                ),
                is_data_sharing=input_dict.get("is_data_sharing", False),
                is_legacy_usage=input_dict.get("is_legacy_usage", False),
                is_derived=input_dict.get("is_derived", False),
                legacy_description=input_dict.get("legacy_description"),
                activity_items=[
                    ActivityItemVO.from_repository_values(
                        is_adam_param_specific=activity_item.get(
                            "is_adam_param_specific"
                        ),
                        activity_item_class_uid=activity_item.get(
                            "activity_item_class_uid"
                        ),
                        activity_item_class_name=activity_item.get(
                            "activity_item_class_name"
                        ),
                        ct_terms=[
                            CTTermItem(
                                uid=term["uid"],
                                name=term["name"],
                                codelist_uid=term["codelist_uid"],
                            )
                            for term in activity_item.get("ct_terms")
                        ],
                        ct_codelist=(
                            CTCodelistItem(
                                uid=activity_item.get("ct_codelist", {}).get("uid"),
                                name=activity_item.get("ct_codelist", {}).get("name"),
                            )
                            if activity_item.get("ct_codelist")
                            else None
                        ),
                        unit_definitions=[
                            CompactUnitDefinition(
                                uid=unit["uid"],
                                name=unit["name"],
                                dimension_name=unit["dimension_name"],
                            )
                            for unit in activity_item.get("unit_definitions")
                        ],
                        is_activity_instance_id_specific=activity_item.get(
                            "is_activity_instance_id_specific"
                        ),
                    )
                    for activity_item in input_dict.get("activity_items", [])
                ],
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
        return activity_instance_ar

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ActivityInstanceRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ActivityInstanceValue,
        **_kwargs,
    ) -> ActivityInstanceAttributesAR:
        activity_instance_class = value.activity_instance_class.get()
        activity_items = value.contains_activity_item.all()
        activity_item_vos = []
        for activity_item in activity_items:
            activity_item_class_root = (
                activity_item.has_activity_item_class.get_or_none()
            )
            ct_terms = []
            unit_definitions = []
            for unit in activity_item.has_unit_definition.all():
                if (
                    ct_dimension := unit.has_version.single()
                    .has_ct_dimension.single()
                    .has_selected_term.single()
                ):
                    dimension_name = (
                        ct_dimension.has_name_root.single()
                        .has_latest_value.single()
                        .name
                    )
                else:
                    dimension_name = None

                unit_definitions.append(
                    CompactUnitDefinition(
                        uid=unit.uid,
                        name=unit.has_version.single().name,
                        dimension_name=dimension_name,
                    )
                )
            for term_context in activity_item.has_ct_term.all():
                term_root = term_context.has_selected_term.single()
                ct_terms.append(
                    CTTermItem(
                        uid=term_root.uid,
                        name=term_root.has_name_root.single().has_version.single().name,
                        codelist_uid=term_context.has_selected_codelist.single().uid,
                    )
                )
            if codelist := activity_item.has_codelist.get_or_none():
                name_root = codelist.has_name_root.get()
                name_value = name_root.has_latest_value.get()
                ct_codelist = CTCodelistItem(uid=codelist.uid, name=name_value.name)
            else:
                ct_codelist = None
            activity_item_vos.append(
                ActivityItemVO.from_repository_values(
                    is_adam_param_specific=activity_item.is_adam_param_specific,
                    activity_item_class_uid=activity_item_class_root.uid,
                    activity_item_class_name=activity_item_class_root.has_latest_value.get_or_none().name,
                    ct_terms=ct_terms,
                    ct_codelist=ct_codelist,
                    unit_definitions=unit_definitions,
                    is_activity_instance_id_specific=activity_item.is_activity_instance_id_specific,
                )
            )

        return self.aggregate_class.from_repository_values(
            uid=root.uid,
            concept_vo=self.value_object_class.from_repository_values(
                nci_concept_id=value.nci_concept_id,
                nci_concept_name=value.nci_concept_name,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                activity_instance_class_uid=activity_instance_class.uid,
                activity_instance_class_name=activity_instance_class.has_latest_value.get().name,
                definition=value.definition,
                abbreviation=value.abbreviation,
                is_research_lab=(
                    value.is_research_lab if value.is_research_lab else False
                ),
                molecular_weight=value.molecular_weight,
                topic_code=value.topic_code,
                adam_param_code=value.adam_param_code,
                is_required_for_activity=(
                    value.is_required_for_activity
                    if value.is_required_for_activity
                    else False
                ),
                is_default_selected_for_activity=(
                    value.is_default_selected_for_activity
                    if value.is_default_selected_for_activity
                    else False
                ),
                is_data_sharing=(
                    value.is_data_sharing if value.is_data_sharing else False
                ),
                is_legacy_usage=(
                    value.is_legacy_usage if value.is_legacy_usage else False
                ),
                is_derived=value.is_derived if value.is_derived else False,
                legacy_description=value.legacy_description,
                activity_items=activity_item_vos,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_ar(
        self,
        root: ActivityInstanceRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ActivityInstanceValue,
        **_kwargs,
    ) -> ActivityInstanceAttributesAR:
        activity_instance_objects = _kwargs["activity_instance_root"]
        activity_instance_class = activity_instance_objects["activity_instance_class"]
        activity_item_vos = []
        for activity_item in activity_instance_objects["activity_items"]:
            ct_terms = []
            unit_definitions = []
            for unit in activity_item["unit_definitions"]:
                unit_definitions.append(
                    CompactUnitDefinition(
                        uid=unit["uid"],
                        name=unit["name"],
                    )
                )
            for term in activity_item["ct_terms"]:
                ct_terms.append(
                    CTTermItem(
                        uid=term["uid"],
                        name=term["name"],
                        codelist_uid=term["codelist_uid"],
                    )
                )
            if codelist := activity_item.has_codelist.get_or_none():
                name_root = codelist.has_name_root.get()
                name_value = name_root.has_latest_value.get()
                ct_codelist = CTCodelistItem(uid=codelist.uid, name=name_value.name)
            else:
                ct_codelist = None
            activity_item_vos.append(
                ActivityItemVO.from_repository_values(
                    is_adam_param_specific=activity_item["is_adam_param_specific"],
                    activity_item_class_uid=activity_item["activity_item_class_uid"],
                    activity_item_class_name=activity_item["activity_item_class_name"],
                    ct_terms=ct_terms,
                    ct_codelist=ct_codelist,
                    unit_definitions=unit_definitions,
                    is_activity_instance_id_specific=activity_item.get(
                        "is_activity_instance_id_specific"
                    ),
                )
            )

        return self.aggregate_class.from_repository_values(
            uid=root.uid,
            concept_vo=self.value_object_class.from_repository_values(
                nci_concept_id=value.nci_concept_id,
                nci_concept_name=value.nci_concept_name,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                activity_instance_class_uid=activity_instance_class[
                    "activity_instance_class_uid"
                ],
                activity_instance_class_name=activity_instance_class[
                    "activity_instance_class_name"
                ],
                definition=value.definition,
                abbreviation=value.abbreviation,
                is_research_lab=(
                    value.is_research_lab if value.is_research_lab else False
                ),
                molecular_weight=value.molecular_weight,
                topic_code=value.topic_code,
                adam_param_code=value.adam_param_code,
                is_required_for_activity=(
                    value.is_required_for_activity
                    if value.is_required_for_activity
                    else False
                ),
                is_default_selected_for_activity=(
                    value.is_default_selected_for_activity
                    if value.is_default_selected_for_activity
                    else False
                ),
                is_data_sharing=(
                    value.is_data_sharing if value.is_data_sharing else False
                ),
                is_legacy_usage=(
                    value.is_legacy_usage if value.is_legacy_usage else False
                ),
                is_derived=value.is_derived if value.is_derived else False,
                legacy_description=value.legacy_description,
                activity_items=activity_item_vos,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def specific_alias_clause(self, **kwargs) -> str:
        return """
        WITH *,
            concept_value.nci_concept_name AS nci_concept_name,
            concept_value.molecular_weight AS molecular_weight,
            concept_value.topic_code AS topic_code,
            concept_value.adam_param_code AS adam_param_code,
            coalesce(concept_value.is_research_lab, false) AS is_research_lab,
            coalesce(concept_value.is_required_for_activity, false) AS is_required_for_activity,
            coalesce(concept_value.is_default_selected_for_activity, false) AS is_default_selected_for_activity,
            coalesce(concept_value.is_data_sharing, false) AS is_data_sharing,
            coalesce(concept_value.is_legacy_usage, false) AS is_legacy_usage,
            coalesce(concept_value.is_derived, false) AS is_derived,
            concept_value.legacy_description AS legacy_description,
            
            head([(concept_value)-[:ACTIVITY_INSTANCE_CLASS]->
            (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue)
                | {uid:activity_instance_class_root.uid, name:activity_instance_class_value.name}]) AS activity_instance_class,
            [(concept_value)-[:CONTAINS_ACTIVITY_ITEM]->(activity_item:ActivityItem)
            <-[:HAS_ACTIVITY_ITEM]-(activity_item_class_root:ActivityItemClassRoot)-[:LATEST]->
            (activity_item_class_value:ActivityItemClassValue)
                | {
                    activity_item_class_uid: activity_item_class_root.uid,
                    activity_item_class_name: activity_item_class_value.name,
                    ct_terms: COLLECT {
                        MATCH (activity_item)-[:HAS_CT_TERM]->(ct_term_context:CTTermContext)
                        -[:HAS_SELECTED_TERM]->(term_root:CTTermRoot)
                        -[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)
                        -[:LATEST]->(term_name_value:CTTermNameValue)
                        MATCH (ct_term_context)-[:HAS_SELECTED_CODELIST]->(codelist_root:CTCodelistRoot)
                        MATCH (ct_codelist_term:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root)
                        RETURN {uid: term_root.uid, name: term_name_value.name, codelist_uid: codelist_root.uid, submission_value: ct_codelist_term.submission_value}
                    },
                    unit_definitions: [(activity_item)-[:HAS_UNIT_DEFINITION]->(unit_definition_root:UnitDefinitionRoot)-[:LATEST]->(unit_definition_value:UnitDefinitionValue)-[:HAS_CT_DIMENSION]-(:CTTermRoot)-[:HAS_NAME_ROOT]->(CTTermNamesRoot)-[:LATEST]->(dimension_value:CTTermNameValue) | {uid: unit_definition_root.uid, name: unit_definition_value.name, dimension_name: dimension_value.name}],
                    is_adam_param_specific: activity_item.is_adam_param_specific,
                    is_activity_instance_id_specific: activity_item.is_activity_instance_id_specific
                }] AS activity_items
        """

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict[Any, Any]]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library, **kwargs)
        filter_parameters = []
        if kwargs.get("activity_instance_names") is not None:
            activity_instance_names = kwargs.get("activity_instance_names")
            filter_by_activity_instance_names = (
                "concept_value.name IN $activity_instance_names"
            )
            filter_parameters.append(filter_by_activity_instance_names)
            filter_query_parameters["activity_instance_names"] = activity_instance_names

        if kwargs.get("activity_instance_class_names") is not None:
            instance_class_names = kwargs.get("activity_instance_class_names")
            filter_by_instance_classes = (
                "size([(concept_value)-[:ACTIVITY_INSTANCE_CLASS]->(:ActivityInstanceClassRoot)"
                "-[:LATEST]->(instance_class_value:ActivityInstanceClassValue)"
                "WHERE instance_class_value.name IN $activity_instance_class_names | instance_class_value.name]) > 0"
            )
            filter_parameters.append(filter_by_instance_classes)
            filter_query_parameters["activity_instance_class_names"] = (
                instance_class_names
            )
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

    def generic_match_clause_all_versions(self):
        return """
            MATCH (concept_root:ActivityInstanceRoot)-[version:HAS_VERSION]->(concept_value:ActivityInstanceValue)
        """


class ActivityInstanceGroupingsRepository(
    ConceptGenericRepository[ActivityInstanceGroupingsAR]
):
    root_class = ActivityInstanceGroupingRoot
    parent_root_class = ActivityInstanceRoot
    parent_root_relationship = "has_grouping_root"
    value_class = ActivityInstanceGroupingValue
    aggregate_class = ActivityInstanceGroupingsAR
    value_object_class = ActivityInstanceGroupingsVO
    return_model = ActivityInstanceGroupings

    def _has_uid_and_library_on_parent_root(self) -> bool:
        return True

    def _lock_object(self, uid: str) -> None:
        itm = self.parent_root_class.nodes.get_or_none(uid=uid)
        if itm is not None:
            itm.__WRITE_LOCK__ = None
            itm.save()

    def copy_activity_instance_groupings_and_recreate(
        self,
        activity_instance_groupings: ActivityInstanceGroupingsAR,
        author_id: str,
    ) -> None:
        """
        Creates a new ActivityInstanceGroupingValue node by cloning the current one,
        updates the versioning relationships, and links the new value node to the
        correct ActivityGrouping nodes.

        This is used during cascade edits to persist new groupings versions
        without requiring repository_closure_data (which ActivityInstanceGroupingsAR
        does not have).
        """
        status = activity_instance_groupings.item_metadata.status.value
        query = """
            MATCH (parent_root:ActivityInstanceRoot {uid: $activity_instance_uid})
                -[:HAS_GROUPING_ROOT]->(concept_root:ActivityInstanceGroupingRoot)
                -[status_relationship:LATEST]->(concept_value:ActivityInstanceGroupingValue)
            CALL apoc.refactor.cloneNodes([concept_value])
            YIELD input, output, error

            WITH parent_root, concept_root, concept_value, output, status_relationship

            MATCH (concept_root)-[latest_has_version:HAS_VERSION]->(concept_value)
            WHERE latest_has_version.end_date IS NULL
        """
        query += f"""
            MATCH (concept_root)-[latest_status_relationship:LATEST_{status.upper()}]->(:{self.value_class.__label__})
            WITH parent_root, concept_root, concept_value, output, status_relationship,
                 latest_has_version, latest_status_relationship

            MERGE (concept_root)-[:LATEST]->(output)
            MERGE (concept_root)-[:LATEST_{status.upper()}]->(output)
            MERGE (concept_root)-[new_has_version:HAS_VERSION]->(output)

            SET new_has_version.start_date = $start_date
            SET new_has_version.end_date = null
            SET new_has_version.change_description = $change_description
            SET new_has_version.version = $new_version
            SET new_has_version.status = $new_status
            SET new_has_version.author_id = $author_id
            SET latest_has_version.end_date = $start_date

            WITH parent_root, concept_root, concept_value, output, status_relationship, latest_status_relationship
            DELETE status_relationship, latest_status_relationship

            WITH parent_root, concept_root, concept_value, output

            // Remove cloned HAS_ACTIVITY relationships from the new value node
            // (they were copied by cloneNodes but point to old ActivityGrouping nodes)
            OPTIONAL MATCH (output)-[old_rel:HAS_ACTIVITY]->()
            DELETE old_rel

            WITH parent_root, concept_root, output

            // Link new value node to the correct ActivityGrouping nodes
            UNWIND range(0, size($activity_uids)-1) AS idx
            MATCH (activity_grouping:ActivityGrouping)<-[:HAS_GROUPING]-(:ActivityValue)<-[:LATEST_FINAL]-(:ActivityRoot {{uid: $activity_uids[idx]}})
            MATCH (activity_grouping)-[:HAS_SELECTED_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(:ActivityGroupRoot {{uid: $activity_group_uids[idx]}})
            MATCH (activity_grouping)-[:HAS_SELECTED_SUBGROUP]->(:ActivitySubGroupValue)<-[:HAS_VERSION]-(:ActivitySubGroupRoot {{uid: $activity_subgroup_uids[idx]}})
            WITH output, activity_grouping
            MERGE (output)-[:HAS_ACTIVITY]->(activity_grouping)
            RETURN output
        """

        db.cypher_query(
            query,
            params={
                "activity_instance_uid": activity_instance_groupings.uid,
                "new_status": status,
                "new_version": activity_instance_groupings.item_metadata.version,
                "start_date": datetime.datetime.now(datetime.timezone.utc),
                "change_description": "Cascade edit: updating activity instance groupings",
                "author_id": author_id,
                "activity_uids": [
                    grouping.activity_uid
                    for grouping in activity_instance_groupings.concept_vo.activity_groupings
                ],
                "activity_subgroup_uids": [
                    grouping.activity_subgroup_uid
                    for grouping in activity_instance_groupings.concept_vo.activity_groupings
                ],
                "activity_group_uids": [
                    grouping.activity_group_uid
                    for grouping in activity_instance_groupings.concept_vo.activity_groupings
                ],
            },
        )

    def generic_match_clause(self, **kwargs):
        concept_label = self.root_class.__label__
        parent_root_label = self.parent_root_class.__label__
        concept_value_label = self.value_class.__label__

        version = kwargs.get("version", None)
        rel = (
            "hv:HAS_VERSION WHERE hv.version = $requested_version"
            if version is not None
            else ":LATEST"
        )

        return f"""CYPHER runtime=slotted MATCH (parent_root:{parent_root_label})-[:HAS_GROUPING_ROOT]->(concept_root:{concept_label})-[{rel}]->(concept_value:{concept_value_label})"""

    def generic_alias_clause(self, **kwargs):
        version = kwargs.get("version", None)
        where_version = (
            "WHERE hv.version = $requested_version" if version is not None else ""
        )

        return f"""
            DISTINCT parent_root, concept_root, concept_value,
            head([(library)-[:CONTAINS_CONCEPT]->(parent_root) | library]) AS library
            CALL (concept_root, concept_value) {{
                MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
                {where_version}
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS version_rel
            }}
            WITH
                parent_root,
                concept_root,
                parent_root.uid AS uid,
                concept_value as concept_value,
                library,
                version_rel
                CALL (version_rel) {{
                    OPTIONAL MATCH (author: User)
                    WHERE author.user_id = version_rel.author_id
                    RETURN author
                }}
            WITH
                uid,
                parent_root,
                concept_root,
                library,
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

    def generic_alias_clause_all_versions(self):
        return """
            DISTINCT parent_root, concept_root, concept_value,
            head([(library)-[:CONTAINS_CONCEPT]->(parent_root) | library]) AS library
            CALL (parent_root, concept_root, concept_value) {
                MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                RETURN hv AS version_rel
            }
            WITH
                parent_root,
                concept_root,
                parent_root.uid AS uid,
                concept_value as concept_value,
                library.name AS library_name,
                library.is_editable AS is_library_editable,
                version_rel
                CALL (version_rel) {
                    OPTIONAL MATCH (author: User)
                    WHERE author.user_id = version_rel.author_id
                    RETURN author
                }
            WITH
                uid,
                parent_root,
                concept_root,
                library_name,
                is_library_editable,
                version_rel.start_date AS start_date,
                version_rel.end_date AS end_date,
                version_rel.status AS status,
                version_rel.version AS version,
                version_rel.change_description AS change_description,
                version_rel.author_id AS author_id,
                coalesce(author.username, version_rel.author_id) AS author_username,
                concept_value
        """

    def _get_root_and_library(
        self, uid: str
    ) -> tuple[VersionRoot | None, Library | None]:
        try:
            parent_root = self.parent_root_class.nodes.get(uid=uid)
            root: VersionRoot | None = parent_root.has_grouping_root.get()
        except DoesNotExist as exc:
            raise NotFoundException(
                "ActivityInstance",
                uid,
            ) from exc
        except NodeClassNotDefined as exc:
            raise NotFoundException(
                msg="Resource doesn't exist - it was likely deleted in a concurrent transaction."
            ) from exc
        if parent_root is None:
            return None, None
        library: Library | None
        if self.has_library:
            library = parent_root.has_library.get()
        else:
            library = None
        return root, library

    def _maintain_parameters(
        self,
        versioned_object,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        # No parameters to maintain for ActivityInstanceGroupings
        pass

    def _create_new_value_node(
        self, ar: ActivityInstanceGroupingsAR
    ) -> ActivityInstanceGroupingValue:
        value_node = ActivityInstanceGroupingValue()
        value_node.save()

        activity_uids = {ag.activity_uid for ag in ar.concept_vo.activity_groupings}
        BusinessLogicException.raise_if(
            len(activity_uids) > 1,
            msg="Instances are not allowed to link to several different activities",
        )
        requested = ActivityRoot.nodes.filter(
            uid=next(iter(activity_uids)),
            has_library__name=settings.requested_library_name,
        )
        BusinessLogicException.raise_if(
            len(requested) > 0,
            msg="Activity instances are not allowed to link to activity requests or placeholders",
        )

        for activity_grouping in ar.concept_vo.activity_groupings:
            # find related ActivityGrouping node
            activity_grouping_node = ListDistinct(
                ActivityGrouping.nodes.filter(
                    has_selected_group__has_version__uid=activity_grouping.activity_group_uid,
                    has_selected_subgroup__has_version__uid=activity_grouping.activity_subgroup_uid,
                    has_grouping__latest_final__uid=activity_grouping.activity_uid,
                ).resolve_subgraph()
            ).distinct()
            BusinessLogicException.raise_if(
                len(activity_grouping_node) == 0,
                msg=f"The ActivityGrouping node wasn't found for Activity Subgroup with UID '{activity_grouping.activity_subgroup_uid}'"
                f" and Activity Group with UID '{activity_grouping.activity_group_uid}'.",
            )
            activity_grouping_node = activity_grouping_node[0]
            # Must not link to archived group
            BusinessLogicException.raise_if(
                activity_grouping_node.has_selected_group.single()
                .has_latest_value.single()
                .has_library.single()
                .name
                == settings.archived_library_name,
                msg=f"Cannot link to archived ActivityGroup with UID '{activity_grouping.activity_uid}'.",
            )
            # Must not link to archived subgroup
            BusinessLogicException.raise_if(
                activity_grouping_node.has_selected_subgroup.single()
                .has_latest_value.single()
                .has_library.single()
                .name
                == settings.archived_library_name,
                msg=f"Cannot link to archived ActivitySubGroup with UID '{activity_grouping.activity_subgroup_uid}'.",
            )
            # link ActivityInstanceValue with ActivityGrouping node
            value_node.has_activity.connect(activity_grouping_node)

        return value_node

    def _has_grouping_data_changed(self, ar_groupings, activity_instance_value):
        value_group_pairs = []
        for activity_grouping_node in activity_instance_value.has_activity.all():
            if not activity_grouping_node.has_grouping.get().has_latest_value.single():
                # The linked ActivityValue is not the latest.
                # We need to return True, so that the ActivityInstanceValue
                # gets updated to use the new ActivityValue.
                return True
            value_group_pairs.append(
                (
                    activity_grouping_node.has_grouping.get().has_version.single().uid,
                    activity_grouping_node.has_selected_group.get()
                    .has_version.single()
                    .uid,
                    activity_grouping_node.has_selected_subgroup.get()
                    .has_version.single()
                    .uid,
                )
            )

        ar_group_pairs = [
            (
                grouping.activity_uid,
                grouping.activity_subgroup_uid,
                grouping.activity_group_uid,
            )
            for grouping in ar_groupings
        ]
        for pair in ar_group_pairs:
            if pair not in value_group_pairs:
                return True
        for pair in value_group_pairs:
            if pair not in ar_group_pairs:
                return True
        return False

    def _has_data_changed(
        self, ar: ActivityInstanceGroupingsAR, value: ActivityInstanceGroupingValue
    ) -> bool:
        # are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        # Is this a final version? If yes, we skip the grouping data check
        # to avoid creating new values nodes when just creating a new draft.
        root_for_final_value = value.has_version.match(
            status__in=[LibraryItemStatus.FINAL.value, LibraryItemStatus.RETIRED.value],
            end_date__isnull=True,
        )

        if not root_for_final_value:
            grouping_data_changed = self._has_grouping_data_changed(
                ar.concept_vo.activity_groupings, value
            )
        else:
            grouping_data_changed = False

        return grouping_data_changed

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> ActivityInstanceGroupingsAR:
        major, minor = input_dict["version"].split(".")
        activity_instance_ar = self.aggregate_class.from_repository_values(
            uid=input_dict["uid"],
            library=LibraryVO.from_input_values_2(
                library_name=input_dict["library_name"],
                is_library_editable_callback=lambda _: input_dict[
                    "is_library_editable"
                ],
            ),
            concept_vo=self.value_object_class.from_repository_values(
                activity_groupings=[
                    ActivityInstanceGroupingVO(
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
                        activity_uid=activity_grouping.get("activity").get("uid"),
                        activity_name=activity_grouping.get("activity").get("name"),
                        activity_version=f"{activity_grouping.get('activity').get('major_version')}.{activity_grouping.get('activity').get('minor_version')}",
                    )
                    for activity_grouping in input_dict.get("activity_groupings")
                ],
                activity_name=input_dict.get("activity_name"),
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
        return activity_instance_ar

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ActivityInstanceGroupingRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ActivityInstanceGroupingValue,
        **_kwargs,
    ) -> ActivityInstanceGroupingsAR:

        parent_root = root.has_grouping_root.single()
        activity_groupings_nodes = value.has_activity.all()

        activity_groupings = []
        activity_name = None
        for activity_grouping in activity_groupings_nodes:
            activity_value_node = activity_grouping.has_grouping.get()
            # ActivityInstance can only link to a single Activity node then it's safe to take a activity_name
            # from the random ActivityValue node related to any ActivityGroupings node linked to ActivityInstance
            activity_name = activity_value_node.name
            # Prefer the Final version of each linked entity. If no Final version exists, fall back to the highest version.
            # The sort key (is_final, version_tuple) ensures Final always ranks above Draft/Retired,
            # and within the same status the highest version number wins.
            # Activity
            activity_root = activity_value_node.has_version.single()
            all_activity_rels = activity_value_node.has_version.all_relationships(
                activity_root
            )
            latest_activity = max(
                all_activity_rels,
                key=lambda r: (
                    r.status == LibraryItemStatus.FINAL.value,
                    version_string_to_tuple(r.version),
                ),
            )
            # ActivityGroup
            activity_group_value = activity_grouping.has_selected_group.get()
            activity_group_root = activity_group_value.has_version.single()
            all_group_rels = activity_group_value.has_version.all_relationships(
                activity_group_root
            )
            latest_group = max(
                all_group_rels,
                key=lambda r: (
                    r.status == LibraryItemStatus.FINAL.value,
                    version_string_to_tuple(r.version),
                ),
            )
            # ActivitySubGroup
            activity_subgroup_value = activity_grouping.has_selected_subgroup.get()
            activity_subgroup_root = activity_subgroup_value.has_version.single()
            all_subgroup_rels = activity_subgroup_value.has_version.all_relationships(
                activity_subgroup_root
            )
            latest_subgroup = max(
                all_subgroup_rels,
                key=lambda r: (
                    r.status == LibraryItemStatus.FINAL.value,
                    version_string_to_tuple(r.version),
                ),
            )

            activity_groupings.append(
                ActivityInstanceGroupingVO(
                    activity_group_uid=activity_group_root.uid,
                    activity_group_version=latest_group.version,
                    activity_subgroup_uid=activity_subgroup_root.uid,
                    activity_subgroup_version=latest_subgroup.version,
                    activity_uid=activity_root.uid,
                    activity_version=latest_activity.version,
                )
            )

        return self.aggregate_class.from_repository_values(
            uid=parent_root.uid,
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            concept_vo=self.value_object_class.from_repository_values(
                activity_groupings=activity_groupings,
                activity_name=activity_name,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def specific_alias_clause(self, **kwargs) -> str:
        return """
        WITH *,
            head([(concept_root)-[:LATEST]->(groupings_value:ActivityInstanceGroupingValue)-[:HAS_ACTIVITY]->(activity_grouping:ActivityGrouping)<-[:HAS_GROUPING]-(activity_value) | activity_value.name]) as activity_name,
            apoc.coll.toSet([(concept_root)-[:LATEST]->(groupings_value:ActivityInstanceGroupingValue)-[:HAS_ACTIVITY]->(activity_grouping:ActivityGrouping)
            | {
                activity: head(apoc.coll.sortMulti([(activity_grouping)<-[:HAS_GROUPING]-(activity_value:ActivityValue)<-[has_version:HAS_VERSION]-
                    (activity_root:ActivityRoot) | 
                    {
                        uid: activity_root.uid,
                        name: activity_value.name,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1])
                    }], ['major_version', 'minor_version'])),
                activity_subgroup: head(apoc.coll.sortMulti([(activity_grouping)-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)<-[has_version:HAS_VERSION]-
                    (activity_subgroup_root:ActivitySubGroupRoot) | 
                    {
                        uid: activity_subgroup_root.uid,
                        name: activity_subgroup_value.name,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1])
                    }], ['major_version', 'minor_version'])), 
                activity_group: head(apoc.coll.sortMulti([(activity_grouping)-[:HAS_SELECTED_GROUP]->(activity_group_value:ActivityGroupValue)<-[has_version:HAS_VERSION]-
                    (activity_group_root:ActivityGroupRoot) | 
                    {
                        uid: activity_group_root.uid,
                        name: activity_group_value.name,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1])
                    }], ['major_version', 'minor_version']))
            }]) AS activity_groupings
        """

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict[Any, Any]]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library, **kwargs)
        filter_parameters = []
        if kwargs.get("activity_instance_names") is not None:
            activity_instance_names = kwargs.get("activity_instance_names")
            filter_by_activity_instance_names = (
                "concept_value.name IN $activity_instance_names"
            )
            filter_parameters.append(filter_by_activity_instance_names)
            filter_query_parameters["activity_instance_names"] = activity_instance_names
        if kwargs.get("activity_names") is not None:
            activity_names = kwargs.get("activity_names")
            filter_by_activity_names = (
                "size([(concept_root)-[:HAS_GROUPING_ROOT]->(:ActivityInstanceGroupingRoot)"
                "-[:LATEST]->(:ActivityInstanceGroupingValue)-[:HAS_ACTIVITY]->(:ActivityGrouping)"
                "<-[:HAS_GROUPING]-(activity_value:ActivityValue) "
                "WHERE activity_value.name IN $activity_names | activity_value.name]) > 0"
            )
            filter_parameters.append(filter_by_activity_names)
            filter_query_parameters["activity_names"] = activity_names
        if kwargs.get("activity_subgroup_names") is not None:
            activity_subgroup_names = kwargs.get("activity_subgroup_names")
            filter_by_activity_subgroup_names = (
                "size([(concept_root)-[:HAS_GROUPING_ROOT]->(:ActivityInstanceGroupingRoot)"
                "-[:LATEST]->(:ActivityInstanceGroupingValue)-[:HAS_ACTIVITY]->(:ActivityGrouping)"
                "-[:HAS_SELECTED_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue) "
                "WHERE activity_subgroup_value.name IN $activity_subgroup_names | activity_subgroup_value.name]) > 0"
            )
            filter_parameters.append(filter_by_activity_subgroup_names)
            filter_query_parameters["activity_subgroup_names"] = activity_subgroup_names
        if kwargs.get("activity_group_names") is not None:
            activity_group_names = kwargs.get("activity_group_names")
            filter_by_activity_group_names = (
                "size([(concept_root)-[:HAS_GROUPING_ROOT]->(:ActivityInstanceGroupingRoot)"
                "-[:LATEST]->(:ActivityInstanceGroupingValue)-[:HAS_ACTIVITY]->(:ActivityGrouping)"
                "-[:HAS_SELECTED_GROUP]->(activity_group_value:ActivityGroupValue) "
                "WHERE activity_group_value.name IN $activity_group_names | activity_group_value.name]) > 0"
            )
            filter_parameters.append(filter_by_activity_group_names)
            filter_query_parameters["activity_group_names"] = activity_group_names
        if kwargs.get("activity_instance_class_names") is not None:
            instance_class_names = kwargs.get("activity_instance_class_names")
            filter_by_instance_classes = (
                "size([(concept_value)-[:ACTIVITY_INSTANCE_CLASS]->(:ActivityInstanceClassRoot)"
                "-[:LATEST]->(instance_class_value:ActivityInstanceClassValue)"
                "WHERE instance_class_value.name IN $activity_instance_class_names | instance_class_value.name]) > 0"
            )
            filter_parameters.append(filter_by_instance_classes)
            filter_query_parameters["activity_instance_class_names"] = (
                instance_class_names
            )
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

    def generic_match_clause_all_versions(self):
        return """
            MATCH (concept_root:ActivityInstanceRoot)-[:HAS_GROUPING_ROOT]->(groupings_root:ActivityInstanceGroupingRoot)-[version:HAS_VERSION]->(concept_value:ActivityInstanceGroupingValue)
        """
