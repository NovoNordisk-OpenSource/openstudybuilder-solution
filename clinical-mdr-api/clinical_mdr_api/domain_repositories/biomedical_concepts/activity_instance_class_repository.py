from neomodel import NodeSet
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
    ActivityInstanceClassValue,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.standard_data_model import DatasetClass
from clinical_mdr_api.domain_repositories.neomodel_ext_item_repository import (
    NeomodelExtBaseRepository,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassActivityItemClassRelVO,
    ActivityInstanceClassAR,
    ActivityInstanceClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
)


class ActivityInstanceClassRepository(
    NeomodelExtBaseRepository, LibraryItemRepositoryImplBase[_AggregateRootType]
):
    root_class = ActivityInstanceClassRoot
    value_class = ActivityInstanceClassValue
    return_model = ActivityInstanceClass

    def get_neomodel_extension_query(self) -> NodeSet:
        return (
            ActivityInstanceClassRoot.nodes.fetch_relations(
                "has_latest_value",
                "has_library",
                Optional("parent_class"),
                Optional("parent_class__has_latest_value"),
                Optional("maps_dataset_class__has_instance"),
                Optional("has_activity_item_class__has_latest_value"),
                Optional("parent_class__has_activity_item_class__has_latest_value"),
                Optional("has_data_domain"),
                Optional("has_data_domain__has_name_root__has_latest_value"),
                Optional("has_data_domain__has_attributes_root__has_latest_value"),
                Optional("parent_class__has_data_domain"),
                Optional(
                    "parent_class__has_data_domain__has_name_root__has_latest_value"
                ),
                Optional(
                    "parent_class__has_data_domain__has_attributes_root__has_latest_value"
                ),
            )
            .unique_variables(
                "parent_class", "has_data_domain", "parent_class__has_data_domain"
            )
            .subquery(
                ActivityInstanceClassRoot.nodes.traverse_relations(
                    latest_version="has_version"
                )
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
                Collect(NodeNameResolver("has_activity_item_class"), distinct=True),
                Collect(RelationNameResolver("has_activity_item_class"), distinct=True),
                Collect(
                    NodeNameResolver("has_activity_item_class__has_latest_value"),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver("has_activity_item_class__has_latest_value"),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver("parent_class__has_activity_item_class"),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver("parent_class__has_activity_item_class"),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver(
                        "parent_class__has_activity_item_class__has_latest_value"
                    ),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver(
                        "parent_class__has_activity_item_class__has_latest_value"
                    ),
                    distinct=True,
                ),
                Collect(NodeNameResolver("has_data_domain"), distinct=True),
                Collect(RelationNameResolver("has_data_domain"), distinct=True),
                Collect(
                    NodeNameResolver("has_data_domain__has_name_root"), distinct=True
                ),
                Collect(
                    RelationNameResolver("has_data_domain__has_name_root"),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver(
                        "has_data_domain__has_name_root__has_latest_value"
                    ),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver(
                        "has_data_domain__has_name_root__has_latest_value"
                    ),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver("has_data_domain__has_attributes_root"),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver("has_data_domain__has_attributes_root"),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver(
                        "has_data_domain__has_attributes_root__has_latest_value"
                    ),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver(
                        "has_data_domain__has_attributes_root__has_latest_value"
                    ),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver("parent_class__has_data_domain"),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver("parent_class__has_data_domain"),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver("parent_class__has_data_domain__has_name_root"),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver(
                        "parent_class__has_data_domain__has_name_root"
                    ),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver(
                        "parent_class__has_data_domain__has_name_root__has_latest_value"
                    ),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver(
                        "parent_class__has_data_domain__has_name_root__has_latest_value"
                    ),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver(
                        "parent_class__has_data_domain__has_attributes_root"
                    ),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver(
                        "parent_class__has_data_domain__has_attributes_root"
                    ),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver(
                        "parent_class__has_data_domain__has_attributes_root__has_latest_value"
                    ),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver(
                        "parent_class__has_data_domain__has_attributes_root__has_latest_value"
                    ),
                    distinct=True,
                ),
            )
        )

    def _has_data_changed(
        self, ar: ActivityInstanceClassAR, value: ActivityInstanceClassValue
    ) -> bool:
        if parent := value.has_latest_value.get_or_none():
            parent = parent.parent_class.get_or_none()
        if dataset_class := value.has_latest_value.get_or_none():
            dataset_class = dataset_class.maps_dataset_class.get_or_none()
        if data_domains := value.has_latest_value.get_or_none():
            data_domains = data_domains.has_data_domain.all()
        else:
            data_domains = []

        return (
            ar.activity_instance_class_vo.name != value.name
            or ar.activity_instance_class_vo.order != value.order
            or ar.activity_instance_class_vo.definition != value.definition
            or ar.activity_instance_class_vo.is_domain_specific
            != value.is_domain_specific
            or ar.activity_instance_class_vo.level != value.level
            or (
                ar.activity_instance_class_vo.data_domain_uids
                != [data_domain.uid for data_domain in data_domains]
            )
            or (
                ar.activity_instance_class_vo.parent_uid != parent.uid
                if parent
                else None
            )
            or (
                ar.activity_instance_class_vo.dataset_class_uid != dataset_class.uid
                if dataset_class
                else None
            )
        )

    def _get_or_create_value(
        self, root: ActivityInstanceClassRoot, ar: ActivityInstanceClassAR
    ) -> ActivityInstanceClassValue:
        for itm in root.has_version.all():
            if not self._has_data_changed(ar, itm):
                return itm
        latest_draft = root.latest_draft.get_or_none()
        if latest_draft and not self._has_data_changed(ar, latest_draft):
            return latest_draft
        latest_final = root.latest_final.get_or_none()
        if latest_final and not self._has_data_changed(ar, latest_final):
            return latest_final
        latest_retired = root.latest_retired.get_or_none()
        if latest_retired and not self._has_data_changed(ar, latest_retired):
            return latest_retired
        new_value = ActivityInstanceClassValue(
            name=ar.activity_instance_class_vo.name,
            order=ar.activity_instance_class_vo.order,
            definition=ar.activity_instance_class_vo.definition,
            is_domain_specific=ar.activity_instance_class_vo.is_domain_specific,
            level=ar.activity_instance_class_vo.level,
        )

        self._db_save_node(new_value)

        if ar.activity_instance_class_vo.parent_uid:
            parent = ActivityInstanceClassRoot.nodes.get_or_none(
                uid=ar.activity_instance_class_vo.parent_uid
            )
            root.parent_class.connect(parent)
        if ar.activity_instance_class_vo.dataset_class_uid:
            dataset = DatasetClass.nodes.get_or_none(
                uid=ar.activity_instance_class_vo.dataset_class_uid
            )
            root.maps_dataset_class.connect(dataset)
        for data_domain_uid in ar.activity_instance_class_vo.data_domain_uids or []:
            data_domain = CTTermRoot.nodes.get_or_none(uid=data_domain_uid)
            root.has_data_domain.connect(data_domain)

        return new_value

    def generate_uid(self) -> str:
        return ActivityInstanceClassRoot.get_next_free_uid_and_increment_counter()

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ActivityInstanceClassRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ActivityInstanceClassValue,
        **_kwargs,
    ) -> ActivityInstanceClassAR:
        parent_class = root.parent_class.get_or_none()
        dataset_class = root.maps_dataset_class.get_or_none()
        activity_item_classes = root.has_activity_item_class.all()
        data_domains = root.has_data_domain.all()

        return ActivityInstanceClassAR.from_repository_values(
            uid=root.uid,
            activity_instance_class_vo=ActivityInstanceClassVO.from_repository_values(
                name=value.name,
                order=value.order,
                definition=value.definition,
                is_domain_specific=value.is_domain_specific,
                level=value.level,
                parent_uid=parent_class.uid if parent_class else None,
                dataset_class_uid=dataset_class.uid if dataset_class else None,
                activity_item_classes=[
                    ActivityInstanceClassActivityItemClassRelVO(
                        uid=activity_item_class.uid,
                        mandatory=activity_item_class.has_activity_instance_class.relationship(
                            root
                        ).mandatory,
                        is_adam_param_specific_enabled=activity_item_class.has_activity_instance_class.relationship(
                            root
                        ).is_adam_param_specific_enabled,
                    )
                    for activity_item_class in activity_item_classes
                ],
                data_domain_uids=[data_domain.uid for data_domain in data_domains],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: ActivityInstanceClassRoot,
        value: ActivityInstanceClassValue,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass
