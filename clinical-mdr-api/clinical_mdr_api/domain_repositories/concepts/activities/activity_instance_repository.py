from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.activities.activity_repository import (
    _get_display_version,
)
from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models._utils import ListDistinct
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGrouping,
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
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.odm import OdmItemRoot
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.activities.activity_instance import (
    ActivityInstanceAR,
    ActivityInstanceGroupingVO,
    ActivityInstanceVO,
)
from clinical_mdr_api.domains.concepts.activities.activity_item import (
    ActivityItemVO,
    LibraryItem,
)
from clinical_mdr_api.domains.concepts.concept_base import _AggregateRootType
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
    CompactOdmItem,
)
from clinical_mdr_api.models.concepts.activities.activity_item import (
    CompactUnitDefinition,
)
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionSimpleModel,
)
from common.config import REQUESTED_LIBRARY_NAME
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime, version_string_to_tuple


class ActivityInstanceRepository(ConceptGenericRepository[ActivityInstanceAR]):
    root_class = ActivityInstanceRoot
    value_class = ActivityInstanceValue
    aggregate_class = ActivityInstanceAR
    value_object_class = ActivityInstanceVO
    return_model = ActivityInstance

    def _create_new_value_node(self, ar: _AggregateRootType) -> ActivityInstanceValue:
        value_node: ActivityInstanceValue = super()._create_new_value_node(ar=ar)
        value_node.is_research_lab = ar.concept_vo.is_research_lab
        value_node.molecular_weight = ar.concept_vo.molecular_weight
        value_node.topic_code = ar.concept_vo.topic_code
        value_node.adam_param_code = ar.concept_vo.adam_param_code
        value_node.is_required_for_activity = ar.concept_vo.is_required_for_activity
        value_node.is_default_selected_for_activity = (
            ar.concept_vo.is_default_selected_for_activity
        )
        value_node.is_data_sharing = ar.concept_vo.is_data_sharing
        value_node.is_legacy_usage = ar.concept_vo.is_legacy_usage
        value_node.is_derived = ar.concept_vo.is_derived
        value_node.legacy_description = ar.concept_vo.legacy_description

        value_node.save()

        activity_uids = set(ag.activity_uid for ag in ar.concept_vo.activity_groupings)
        BusinessLogicException.raise_if(
            len(activity_uids) > 1,
            msg="Instances are not allowed to link to several different activities",
        )
        for activity_uid in activity_uids:
            requested = ActivityRoot.nodes.filter(
                uid=activity_uid, has_library__name=REQUESTED_LIBRARY_NAME
            )
            BusinessLogicException.raise_if(
                len(requested) > 0,
                msg="Activity instances are not allowed to link to activity requests or placeholders",
            )

        for activity_grouping in ar.concept_vo.activity_groupings:
            # find related ActivityGrouping node
            activity_grouping_node = ListDistinct(
                ActivityGrouping.nodes.filter(
                    in_subgroup__in_group__has_version__uid=activity_grouping.activity_group_uid,
                    in_subgroup__has_group__has_version__uid=activity_grouping.activity_subgroup_uid,
                    has_grouping__latest_final__uid=activity_grouping.activity_uid,
                ).resolve_subgraph()
            ).distinct()
            BusinessLogicException.raise_if(
                len(activity_grouping_node) == 0,
                msg=f"The ActivityValidGroup node wasn't found for Activity Subgroup with UID '{activity_grouping.activity_subgroup_uid}'"
                f" and Activity Group with UID '{activity_grouping.activity_group_uid}'.",
            )
            activity_grouping_node = activity_grouping_node[0]
            # link ActivityInstanceValue with ActivityGrouping node
            value_node.has_activity.connect(activity_grouping_node)

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
                is_adam_param_specific=is_adam_param_specific
            )
            activity_item_node.save()
            activity_item_node.has_activity_item_class.connect(activity_item_class)

            for term in item.ct_terms:
                ct_term_root = CTTermRoot.nodes.get_or_none(uid=term.uid)
                activity_item_node.has_ct_term.connect(ct_term_root)

            for unit in item.unit_definitions:
                unit_definition = UnitDefinitionRoot.nodes.get_or_none(uid=unit.uid)
                activity_item_node.has_unit_definition.connect(unit_definition)

            for odm_item in item.odm_items:
                odm_item = OdmItemRoot.nodes.get_or_none(uid=odm_item.uid)
                activity_item_node.has_odm_item.connect(odm_item)

            value_node.contains_activity_item.connect(activity_item_node)
        return value_node

    def _has_item_data_changed(self, ar_items, value_item_nodes):
        ar_activity_items = []
        for item in ar_items:
            ar_activity_items.append(
                {
                    "is_adam_param_specific": item.is_adam_param_specific,
                    "class": item.activity_item_class_uid,
                    "units": set(unit.uid for unit in item.unit_definitions),
                    "terms": set(term.uid for term in item.ct_terms),
                    "odm_items": set(odm_item.uid for odm_item in item.odm_items),
                }
            )

        value_activity_items = []
        for activity_item_node in value_item_nodes:
            item_class_uid = activity_item_node.has_activity_item_class.get().uid
            unit_nodes = activity_item_node.has_unit_definition.all()
            ct_term_nodes = activity_item_node.has_ct_term.all()
            odm_item_nodes = activity_item_node.has_odm_item.all()
            value_activity_items.append(
                {
                    "is_adam_param_specific": activity_item_node.is_adam_param_specific,
                    "class": item_class_uid,
                    "units": set(unit_node.uid for unit_node in unit_nodes),
                    "terms": set(ct_term_node.uid for ct_term_node in ct_term_nodes),
                    "odm_items": set(
                        odm_item_node.uid for odm_item_node in odm_item_nodes
                    ),
                }
            )
        for item in ar_activity_items:
            if item not in value_activity_items:
                return True
        for item in value_activity_items:
            if item not in ar_activity_items:
                return True
        return False

    def _has_grouping_data_changed(self, ar_groupings, activity_instance_value):
        value_group_pairs = []
        for activity_grouping_node in activity_instance_value.has_activity.all():
            if not activity_grouping_node.has_grouping.get().has_latest_value.single():
                # The linked ActivityValue is not the latest.
                # We need to return True, so that the ActivityInstanceValue
                # gets updated to use the new ActivityValue.
                return True
            activity_valid_group_nodes = activity_grouping_node.in_subgroup.all()
            for activity_valid_group_node in activity_valid_group_nodes:
                value_group_pairs.append(
                    (
                        activity_grouping_node.has_grouping.get()
                        .has_version.single()
                        .uid,
                        activity_valid_group_node.has_group.get()
                        .has_version.single()
                        .uid,
                        activity_valid_group_node.in_group.get()
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
        self, ar: ActivityInstanceAR, value: ActivityInstanceValue
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

        are_rels_changed = (
            ar.concept_vo.activity_instance_class_uid
            != value.activity_instance_class.get().uid
            or grouping_data_changed
            or item_data_changed
        )
        return are_concept_properties_changed or are_props_changed or are_rels_changed

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> ActivityInstanceAR:
        major, minor = input_dict.get("version").split(".")
        return self.aggregate_class.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=self.value_object_class.from_repository_values(
                nci_concept_id=input_dict.get("nci_concept_id"),
                nci_concept_name=input_dict.get("nci_concept_name"),
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("name_sentence_case"),
                activity_instance_class_uid=input_dict.get(
                    "activity_instance_class"
                ).get("uid"),
                activity_instance_class_name=input_dict.get(
                    "activity_instance_class"
                ).get("name"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                is_research_lab=input_dict.get("is_research_lab", False),
                molecular_weight=input_dict.get("molecular_weight"),
                topic_code=input_dict.get("topic_code"),
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
                        activity_group_version=f"{activity_grouping.get('activity_group').get('major_version')}.{activity_grouping.get('activity_group').get('minor_version')}",
                        activity_subgroup_uid=activity_grouping.get(
                            "activity_subgroup"
                        ).get("uid"),
                        activity_subgroup_version=f"{activity_grouping.get('activity_subgroup').get('major_version')}.{activity_grouping.get('activity_subgroup').get('minor_version')}",
                        activity_uid=activity_grouping.get("activity").get("uid"),
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
                        ct_terms=[
                            LibraryItem(uid=term["uid"], name=term["name"])
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
                        odm_items=[
                            CompactOdmItem(
                                uid=odm_item["uid"],
                                oid=odm_item["oid"],
                                name=odm_item["name"],
                            )
                            for odm_item in activity_item.get("odm_items")
                        ],
                    )
                    for activity_item in input_dict.get("activity_items", [])
                ],
                activity_name=input_dict.get("activity_name"),
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

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ActivityInstanceRoot,
        library: Library | None,
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
            odm_items = []
            for unit in activity_item.has_unit_definition.all():
                if ct_dimension := unit.has_version.single().has_ct_dimension.single():
                    dimension_name = (
                        ct_dimension.has_name_root.single()
                        .has_latest_value.single()
                        .name
                    )
                else:
                    dimension_name = None

                unit_definitions.append(
                    UnitDefinitionSimpleModel(
                        uid=unit.uid,
                        name=unit.has_version.single().name,
                        dimension_name=dimension_name,
                    )
                )
            for term in activity_item.has_ct_term.all():
                ct_terms.append(
                    LibraryItem(
                        uid=term.uid,
                        name=term.has_name_root.single().has_version.single().name,
                    )
                )
            for odm_item in activity_item.has_odm_item.all():
                odm_item_value = odm_item.has_latest_value.single()
                odm_items.append(
                    CompactOdmItem(
                        uid=odm_item.uid,
                        oid=odm_item_value.oid,
                        name=odm_item_value.name,
                    )
                )
            activity_item_vos.append(
                ActivityItemVO.from_repository_values(
                    is_adam_param_specific=activity_item.is_adam_param_specific,
                    activity_item_class_uid=activity_item_class_root.uid,
                    activity_item_class_name=activity_item_class_root.has_latest_value.get_or_none().name,
                    ct_terms=ct_terms,
                    unit_definitions=unit_definitions,
                    odm_items=odm_items,
                )
            )
        activity_groupings_nodes = value.has_activity.all()
        activity_groupings = []
        activity_name = None
        for activity_grouping in activity_groupings_nodes:
            activity_value_node = activity_grouping.has_grouping.get()
            # ActivityInstance can only link to a single Activity node then it's safe to take a activity_name
            # from the random ActivityValue node related to any ActivityGroupings node linked to ActivityInstance
            activity_name = activity_value_node.name
            # Activity
            activity_root = activity_value_node.has_version.single()
            all_activity_rels = activity_value_node.has_version.all_relationships(
                activity_root
            )
            latest_activity = max(
                all_activity_rels, key=lambda r: version_string_to_tuple(r.version)
            )

            activity_valid_groups = activity_grouping.in_subgroup.all()
            for activity_valid_group in activity_valid_groups:
                # ActivityGroup
                activity_group_value = activity_valid_group.in_group.get()
                activity_group_root = activity_group_value.has_version.single()
                all_group_rels = activity_group_value.has_version.all_relationships(
                    activity_group_root
                )
                latest_group = max(
                    all_group_rels, key=lambda r: version_string_to_tuple(r.version)
                )
                # ActivitySubGroup
                activity_subgroup_value = activity_valid_group.has_group.get()
                activity_subgroup_root = activity_subgroup_value.has_version.single()
                all_subgroup_rels = (
                    activity_subgroup_value.has_version.all_relationships(
                        activity_subgroup_root
                    )
                )
                latest_subgroup = max(
                    all_subgroup_rels, key=lambda r: version_string_to_tuple(r.version)
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
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_ar(
        self,
        root: ActivityInstanceRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: ActivityInstanceValue,
        **_kwargs,
    ) -> ActivityInstanceAR:
        activity_instance_objects = _kwargs["activity_instance_root"]
        activity_instance_class = activity_instance_objects["activity_instance_class"]
        activity_item_vos = []
        for activity_item in activity_instance_objects["activity_items"]:
            ct_terms = []
            unit_definitions = []
            odm_items = []
            for unit in activity_item["unit_definitions"]:
                unit_definitions.append(
                    UnitDefinitionSimpleModel(
                        uid=unit["uid"],
                        name=unit["name"],
                    )
                )
            for term in activity_item["ct_terms"]:
                ct_terms.append(
                    LibraryItem(
                        uid=term["uid"],
                        name=term["name"],
                    )
                )
            for odm_item in activity_item["odm_items"]:
                odm_items.append(
                    CompactOdmItem(
                        uid=odm_item["uid"], oid=odm_item["oid"], name=odm_item["name"]
                    )
                )
            activity_item_vos.append(
                ActivityItemVO.from_repository_values(
                    is_adam_param_specific=activity_item["is_adam_param_specific"],
                    activity_item_class_uid=activity_item["activity_item_class_uid"],
                    activity_item_class_name=activity_item["activity_item_class_name"],
                    ct_terms=ct_terms,
                    unit_definitions=unit_definitions,
                    odm_items=odm_items,
                )
            )
        activity_groupings = []
        for activity_grouping in activity_instance_objects[
            "activity_instance_groupings"
        ]:
            activity_groupings.append(
                ActivityInstanceGroupingVO(
                    activity_group_uid=activity_grouping.get("activity_group").get(
                        "uid"
                    ),
                    activity_group_version=f"{activity_grouping.get('activity_group').get('major_version')}.{activity_grouping.get('activity_group').get('minor_version')}",
                    activity_subgroup_uid=activity_grouping.get(
                        "activity_subgroup"
                    ).get("uid"),
                    activity_subgroup_version=f"{activity_grouping.get('activity_subgroup').get('major_version')}.{activity_grouping.get('activity_subgroup').get('minor_version')}",
                    activity_uid=activity_grouping.get("activity").get("uid"),
                    activity_version=f"{activity_grouping.get('activity').get('major_version')}.{activity_grouping.get('activity').get('minor_version')}",
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
                activity_groupings=activity_groupings,
                activity_items=activity_item_vos,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
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
                    ct_terms: [(activity_item)-[:HAS_CT_TERM]->(term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue) | {uid: term_root.uid, name: term_name_value.name}],
                    unit_definitions: [(activity_item)-[:HAS_UNIT_DEFINITION]->(unit_definition_root:UnitDefinitionRoot)-[:LATEST]->(unit_definition_value:UnitDefinitionValue)-[:HAS_CT_DIMENSION]-(:CTTermRoot)-[:HAS_NAME_ROOT]->(CTTermNamesRoot)-[:LATEST]->(dimension_value:CTTermNameValue) | {uid: unit_definition_root.uid, name: unit_definition_value.name, dimension_name: dimension_value.name}],
                    is_adam_param_specific: activity_item.is_adam_param_specific,
                    odm_items: [(activity_item)-[:HAS_ODM_ITEM]->(odm_item_root:OdmItemRoot)-[:LATEST]->(odm_item_value:OdmItemValue) | {uid: odm_item_root.uid, oid: odm_item_value.oid, name: odm_item_value.name}]
                }] AS activity_items,
            head([(concept_value)-[:HAS_ACTIVITY]->(activity_grouping)<-[:HAS_GROUPING]-(activity_value) | activity_value.name]) as activity_name,
            apoc.coll.toSet([(concept_value)-[:HAS_ACTIVITY]->(activity_grouping:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)
            <-[:HAS_GROUP]-(activity_subgroup_value)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
             | {
                activity: head(apoc.coll.sortMulti([(activity_grouping)<-[:HAS_GROUPING]-(:ActivityValue)<-[has_version:HAS_VERSION]-
                    (activity_root:ActivityRoot) | 
                    {
                        uid:activity_root.uid,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1])
                    }], ['major_version', 'minor_version'])),
                activity_subgroup: head(apoc.coll.sortMulti([(activity_valid_group)<-[:HAS_GROUP]-(:ActivitySubGroupValue)<-[has_version:HAS_VERSION]-
                    (activity_subgroup_root:ActivitySubGroupRoot) | 
                    {
                        uid:activity_subgroup_root.uid,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1])
                    }], ['major_version', 'minor_version'])), 
                activity_group: head(apoc.coll.sortMulti([(activity_valid_group)-[:IN_GROUP]-(:ActivityGroupValue)<-[has_version:HAS_VERSION]-
                    (activity_group_root:ActivityGroupRoot) | 
                    {
                        uid:activity_group_root.uid,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1])
                    }], ['major_version', 'minor_version']))
             }]) AS activity_groupings
        """

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library)
        filter_parameters = []
        if kwargs.get("activity_names") is not None:
            activity_names = kwargs.get("activity_names")
            filter_by_activity_names = (
                "size([(concept_value)-[:HAS_ACTIVITY]->(:ActivityGrouping)<-[:HAS_GROUPING]-(activity_hierarchy_value) "
                "WHERE activity_hierarchy_value.name IN $activity_names | activity_hierarchy_value.name]) > 0"
            )
            filter_parameters.append(filter_by_activity_names)
            filter_query_parameters["activity_names"] = activity_names
        if kwargs.get("activity_subgroup_names") is not None:
            activity_subgroup_names = kwargs.get("activity_subgroup_names")
            filter_by_activity_subgroup_names = (
                "size([(concept_value)-[:HAS_ACTIVITY]->(:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)"
                "<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue) "
                "WHERE activity_subgroup_value.name IN $activity_subgroup_names | activity_subgroup_value.name]) > 0"
            )
            filter_parameters.append(filter_by_activity_subgroup_names)
            filter_query_parameters["activity_subgroup_names"] = activity_subgroup_names
        if kwargs.get("activity_group_names") is not None:
            activity_group_names = kwargs.get("activity_group_names")
            filter_by_activity_group_names = (
                "size([(concept_value)-[:HAS_ACTIVITY]->(:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)"
                "-[:IN_GROUP]->(activity_group_value:ActivityGroupValue) "
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

    def get_activity_instance_overview(
        self, uid: str, version: str | None = None
    ) -> dict:
        if version:
            params = {"uid": uid, "version": version}
            match = """
                    MATCH (activity_instance_root:ActivityInstanceRoot {uid:$uid})
                    CALL {
                        WITH activity_instance_root
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
                    CALL {
                        WITH activity_instance_root, activity_instance_value
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
        query = (
            match
            + """
        WITH activity_instance_root,activity_instance_value, has_version,
            head([(library)-[:CONTAINS_CONCEPT]->(activity_instance_root) | library.name]) AS instance_library_name,
            head([(activity_instance_value)-[:ACTIVITY_INSTANCE_CLASS]->
            (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue) 
            | activity_instance_class_value]) AS activity_instance_class,
            [(activity_instance_root)-[versions:HAS_VERSION]->(:ActivityInstanceValue) | versions.version] as all_versions
        WITH *,
            [(activity_instance_value)-[:HAS_ACTIVITY]->(activity_grouping:ActivityGrouping)<-[:HAS_GROUPING]-(activity_value:ActivityValue) | 
                {
                    uid: head([(activity_value)<-[:HAS_VERSION]-(activity_root) | activity_root.uid]),
                    activity_value: activity_value,
                    activity_versions: [(activity_value)<-[hav:HAS_VERSION]-(activity_root:ActivityRoot) | hav { .version, .status, .start_date, .end_date}],
                    activity_library_name: head([(activity_value:ActivityValue)<-[:HAS_VERSION]-(activity_root:ActivityRoot)<-[:CONTAINS_CONCEPT]-(library) 
                    | library.name]),
                    activity_subgroup_value: head([(activity_grouping:ActivityGrouping)-[:IN_SUBGROUP]->
                    (activity_valid_group:ActivityValidGroup)<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue) 
                        | activity_subgroup_value]),
                    activity_subgroup_uid: head([(activity_grouping:ActivityGrouping)-[:IN_SUBGROUP]->
                    (activity_valid_group:ActivityValidGroup)<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) 
                        | activity_subgroup_root.uid]),
                    activity_group_value: head([(activity_grouping:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group)-[:IN_GROUP]->(activity_group_value) 
                        | activity_group_value]),
                    activity_group_uid: head([(activity_grouping:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group)-[:IN_GROUP]->(activity_group_value)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) 
                        | activity_group_root.uid])
                }
            ] AS hierarchy,
            apoc.coll.toSet([(activity_instance_value)-[:CONTAINS_ACTIVITY_ITEM]->(activity_item)
            <-[HAS_ACTIVITY_ITEM]-(activity_item_class_root)-[:LATEST]->(activity_item_class_value) | 
            {
                activity_item_class: activity_item_class_value,
                activity_item_class_role: head([(activity_item_class_value)-[:HAS_ROLE]->()-[:HAS_NAME_ROOT]->()-[:LATEST]->(role_value) | role_value.name]),
                activity_item_class_data_type: head([(activity_item_class_value)-[:HAS_DATA_TYPE]->()-[:HAS_NAME_ROOT]->()-[:LATEST]->(data_type_value) | data_type_value.name]),
                activity_item: activity_item,
                ct_terms: [(activity_item)-[:HAS_CT_TERM]->(term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue) | {uid: term_root.uid, name: term_name_value.name}],
                unit_definitions: [
                    (activity_item)-[:HAS_UNIT_DEFINITION]->(unit_definition_root:UnitDefinitionRoot)-[:LATEST]->(unit_definition_value:UnitDefinitionValue)
                    -[:HAS_CT_DIMENSION]-(:CTTermRoot)-[:HAS_NAME_ROOT]->(CTTermNamesRoot)-[:LATEST]->(dimension_value:CTTermNameValue)
                    | {uid: unit_definition_root.uid, name: unit_definition_value.name, dimension_name: dimension_value.name}
                ],
                is_adam_param_specific: activity_item.is_adam_param_specific,
                odm_items: [(activity_item)-[:HAS_ODM_ITEM]->(odm_item_root:OdmItemRoot)-[:LATEST]->(odm_item_value:OdmItemValue) | {uid: odm_item_root.uid, oid: odm_item_value.oid, name: odm_item_value.name}]
            }
            ]) AS activity_items
        WITH DISTINCT 
            activity_instance_root,
            activity_instance_value,
            instance_library_name,
            activity_instance_class,
            hierarchy,
            activity_items,
            has_version,
            apoc.coll.dropDuplicateNeighbors(apoc.coll.sort(all_versions)) AS all_versions
        RETURN *
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
        for item in overview_dict["hierarchy"]:
            item["version"] = _get_display_version(item["activity_versions"])
        return overview_dict

    def get_cosmos_activity_instance_overview(self, uid: str) -> dict:
        query = """
        MATCH (activity_instance_root:ActivityInstanceRoot {uid:$uid})-[:LATEST]->(activity_instance_value:ActivityInstanceValue)
        WITH activity_instance_root,activity_instance_value,
            head([(library)-[:CONTAINS_CONCEPT]->(activity_instance_root) | library.name]) AS instance_library_name,
            head([(activity_instance_value)-[:ACTIVITY_INSTANCE_CLASS]->
            (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue) 
            | activity_instance_class_value.name]) AS activity_instance_class_name
        WITH *,
            [(activity_instance_value)-[:HAS_ACTIVITY]->(:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)
            <-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value.name] AS activity_subgroups,
            apoc.coll.toSet([(activity_instance_value)-[:CONTAINS_ACTIVITY_ITEM]->(activity_item)
            <-[HAS_ACTIVITY_ITEM]-(activity_item_class_root)-[:LATEST]->(activity_item_class_value) | 
            {
                nci_concept_id: activity_item_class_value.nci_concept_id,
                name: activity_item_class_value.name,
                type: head([(activity_item_class_value)-[:HAS_DATA_TYPE]->()-[:HAS_NAME_ROOT]->()-[:LATEST]->(data_type_value) | data_type_value.name]),
                example_set: [(activity_item)-[:HAS_CT_TERM]->(term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue) | {uid: term_root.uid, name: term_name_value.name}] + [(activity_item)-[:HAS_UNIT_DEFINITION]->(unit_definition_root:UnitDefinitionRoot)-[:LATEST]->(unit_definition_value:UnitDefinitionValue) | {uid: unit_definition_root.uid, name: unit_definition_value.name}]
            }
            ]) AS activity_items
        WITH DISTINCT
            activity_instance_value,
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
            -[:HAS_ACTIVITY]->(activity_grouping:ActivityGrouping)<-[:HAS_GROUPING]-(activity_value:ActivityValue)
        """

    def get_all_activity_instances_for_activity_grouping(
        self,
        activity_uid: str,
        activity_subgroup_uid: str,
        activity_group_uid: str,
        filter_by_boolean_flags: bool = False,
    ) -> list[ActivityInstanceRoot]:
        query = """
            MATCH (activity_instance_root:ActivityInstanceRoot)-[:LATEST]->(activity_instance_value:ActivityInstanceValue)
            MATCH (activity_instance_root)-[:LATEST_FINAL]->(activity_instance_value)
            OPTIONAL MATCH (activity_instance_root)-[retired:HAS_VERSION {status: "Retired"}]->(activity_instance_value) WHERE retired.end_date IS NULL
            WITH activity_instance_root, activity_instance_value WHERE retired IS NULL
            MATCH (activity_instance_value)-[:HAS_ACTIVITY]->(activity_grouping:ActivityGrouping)<-[:HAS_GROUPING]-(:ActivityValue)<-[:HAS_VERSION]-(:ActivityRoot {uid:$activity_uid})
            MATCH (activity_grouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)<-[:HAS_GROUP]-(:ActivitySubGroupValue)<-[:HAS_VERSION]-(:ActivitySubGroupRoot {uid:$activity_subgroup_uid})
            MATCH (activity_valid_group)-[:IN_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(:ActivityGroupRoot {uid:$activity_group_uid})
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
        defaulted_instances = []
        other_instances = []
        all_instances = []
        for activity_instance in nodes:
            root: ActivityInstanceRoot = activity_instance[0]
            all_instances.append(root)
            value: ActivityInstanceValue = activity_instance[1]
            if value.is_required_for_activity:
                required_instances.append(root)
            elif (
                value.is_default_selected_for_activity and len(defaulted_instances) == 0
            ):
                defaulted_instances.append(root)
            elif len(other_instances) == 0:
                other_instances.append(root)
        if filter_by_boolean_flags:
            if required_instances:
                return required_instances
            if defaulted_instances:
                return defaulted_instances
            return other_instances
        return all_instances
