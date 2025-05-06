import json

from neomodel import NodeSet, db
from neomodel.sync_.match import (
    Collect,
    Last,
    NodeNameResolver,
    Optional,
    RawCypher,
    RelationNameResolver,
)

from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.models.biomedical_concepts import (
    ActivityInstanceClassRoot,
    ActivityItemClassRoot,
    ActivityItemClassValue,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    VariableClass,
)
from clinical_mdr_api.domain_repositories.neomodel_ext_item_repository import (
    NeomodelExtBaseRepository,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_item_class import (
    ActivityInstanceClassActivityItemClassRelVO,
    ActivityItemClassAR,
    ActivityItemClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityItemClass,
)


class ActivityItemClassRepository(
    NeomodelExtBaseRepository, LibraryItemRepositoryImplBase[_AggregateRootType]
):
    root_class = ActivityItemClassRoot
    value_class = ActivityItemClassValue
    return_model = ActivityItemClass

    def get_neomodel_extension_query(self) -> NodeSet:
        return (
            ActivityItemClassRoot.nodes.fetch_relations(
                "has_latest_value",
                "has_library",
                "has_latest_value__has_role__has_name_root__has_latest_value",
                "has_latest_value__has_data_type__has_name_root__has_latest_value",
                Optional("has_activity_instance_class"),
                Optional("has_activity_instance_class__has_latest_value"),
                Optional("maps_variable_class"),
                Optional("related_codelist"),
                Optional("related_codelist__has_attributes_root"),
                Optional("related_codelist__has_attributes_root__has_latest_value"),
            )
            .unique_variables("has_latest_value", "has_activity_instance_class")
            .subquery(
                ActivityItemClassRoot.nodes.fetch_relations("has_version")
                .intermediate_transform(
                    {"rel": {"source": RelationNameResolver("has_version")}},
                    ordering=[
                        RawCypher("toInteger(split(rel.version, '.')[0])"),
                        RawCypher("toInteger(split(rel.version, '.')[1])"),
                        "rel.end_date",
                        "rel.start_date",
                    ],
                )
                .annotate(latest_version=Last(Collect("rel"))),
                ["latest_version"],
                initial_context=[NodeNameResolver("self")],
            )
            .annotate(
                Collect(NodeNameResolver("has_activity_instance_class"), distinct=True),
                Collect(
                    RelationNameResolver("has_activity_instance_class"), distinct=True
                ),
                Collect(
                    NodeNameResolver("has_activity_instance_class__has_latest_value"),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver(
                        "has_activity_instance_class__has_latest_value"
                    ),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver("related_codelist__has_attributes_root"),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver("related_codelist__has_attributes_root"),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver(
                        "related_codelist__has_attributes_root__has_latest_value"
                    ),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver(
                        "related_codelist__has_attributes_root__has_latest_value"
                    ),
                    distinct=True,
                ),
                Collect(NodeNameResolver("maps_variable_class"), distinct=True),
                Collect(RelationNameResolver("maps_variable_class"), distinct=True),
            )
        )

    def _has_data_changed(
        self, ar: ActivityItemClassAR, value: ActivityItemClassValue
    ) -> bool:
        existing_activity_instance_classes = []
        root = value.has_version.single()
        for node in root.has_activity_instance_class.all():
            rel = root.has_activity_instance_class.relationship(node)
            existing_activity_instance_classes.append(
                {
                    "uid": node.uid,
                    "mandatory": rel.mandatory,
                    "is_adam_param_specific_enabled": rel.is_adam_param_specific_enabled,
                }
            )
        existing_activity_instance_classes.sort(key=json.dumps)

        new_activity_instance_classes = sorted(
            [
                item.__dict__
                for item in ar.activity_item_class_vo.activity_instance_classes
            ],
            key=json.dumps,
        )

        codelist_uids = []
        for codelist in root.related_codelist.all():
            codelist_uids.append(codelist.uid)

        return (
            ar.activity_item_class_vo.name != value.name
            or ar.activity_item_class_vo.definition != value.definition
            or ar.activity_item_class_vo.nci_concept_id != value.nci_concept_id
            or ar.activity_item_class_vo.order != value.order
            or new_activity_instance_classes != existing_activity_instance_classes
            or ar.activity_item_class_vo.role_uid != value.has_role.get().uid
            or ar.activity_item_class_vo.data_type_uid != value.has_data_type.get().uid
            or ar.activity_item_class_vo.codelist_uids != codelist_uids
        )

    def _get_or_create_value(
        self, root: ActivityItemClassRoot, ar: ActivityItemClassAR
    ) -> ActivityItemClassValue:
        for itm in root.has_version.all():
            if not self._has_data_changed(ar, itm):
                return itm
        new_value = ActivityItemClassValue(
            name=ar.activity_item_class_vo.name,
            order=ar.activity_item_class_vo.order,
            definition=ar.activity_item_class_vo.definition,
            nci_concept_id=ar.activity_item_class_vo.nci_concept_id,
        )
        self._db_save_node(new_value)
        for (
            activity_instance_class_uid
        ) in ar.activity_item_class_vo.activity_instance_classes:
            activity_instance_class = ActivityInstanceClassRoot.nodes.get_or_none(
                uid=activity_instance_class_uid.uid
            )
            rel = root.has_activity_instance_class.relationship(activity_instance_class)
            if rel:
                rel.mandatory = activity_instance_class_uid.mandatory
                rel.is_adam_param_specific_enabled = (
                    activity_instance_class_uid.is_adam_param_specific_enabled
                )
                rel.save()
            else:
                root.has_activity_instance_class.connect(
                    activity_instance_class,
                    {
                        "mandatory": activity_instance_class_uid.mandatory,
                        "is_adam_param_specific_enabled": activity_instance_class_uid.is_adam_param_specific_enabled,
                    },
                )
        new_value.has_data_type.connect(
            CTTermRoot.nodes.get(uid=ar.activity_item_class_vo.data_type_uid)
        )
        new_value.has_role.connect(
            CTTermRoot.nodes.get(uid=ar.activity_item_class_vo.role_uid)
        )

        root.related_codelist.disconnect_all()
        for codelist_uid in ar.activity_item_class_vo.codelist_uids or []:
            codelist_uid = CTCodelistRoot.nodes.get_or_none(uid=codelist_uid)
            root.related_codelist.connect(codelist_uid)

        return new_value

    def generate_uid(self) -> str:
        return ActivityItemClassRoot.get_next_free_uid_and_increment_counter()

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ActivityItemClassRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ActivityItemClassValue,
        **_kwargs,
    ) -> ActivityItemClassAR:
        activity_instance_classes = root.has_activity_instance_class.all()
        codelists = root.related_codelist.all()
        role_term = value.has_role.get()
        data_type_term = value.has_data_type.get()
        variable_class_uids = [node.uid for node in root.maps_variable_class.all()]
        return ActivityItemClassAR.from_repository_values(
            uid=root.uid,
            activity_item_class_vo=ActivityItemClassVO.from_repository_values(
                name=value.name,
                definition=value.definition,
                nci_concept_id=value.nci_concept_id,
                order=value.order,
                activity_instance_classes=[
                    ActivityInstanceClassActivityItemClassRelVO(
                        uid=activity_instance_class.uid,
                        mandatory=activity_instance_class.has_activity_item_class.relationship(
                            root
                        ).mandatory,
                        is_adam_param_specific_enabled=activity_instance_class.has_activity_item_class.relationship(
                            root
                        ).is_adam_param_specific_enabled,
                    )
                    for activity_instance_class in activity_instance_classes
                ],
                role_uid=role_term.uid,
                role_name=role_term.has_name_root.get().has_latest_value.get().name,
                data_type_uid=data_type_term.uid,
                data_type_name=data_type_term.has_name_root.get()
                .has_latest_value.get()
                .name,
                variable_class_uids=variable_class_uids,
                codelist_uids=[codelist.uid for codelist in codelists],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def patch_mappings(self, uid: str, variable_class_uids: list[str]) -> None:
        root = ActivityItemClassRoot.nodes.get(uid=uid)
        root.maps_variable_class.disconnect_all()
        for variable_class in variable_class_uids:
            variable_class = VariableClass.nodes.get(uid=variable_class)
            root.maps_variable_class.connect(variable_class)

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: ActivityItemClassRoot,
        value: ActivityItemClassValue,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass

    def get_related_codelist_uid(
        self, activity_item_class_uid: str
    ) -> list[str] | None:
        rs = db.cypher_query(
            """
MATCH (:ActivityItemClassRoot {uid: $activity_item_class_uid})-[:RELATED_CODELIST]->(codelist:CTCodelistRoot)
RETURN DISTINCT codelist.uid
""",
            params={"activity_item_class_uid": activity_item_class_uid},
        )

        if rs[0]:
            return [item[0] for item in rs[0]]

        return None
