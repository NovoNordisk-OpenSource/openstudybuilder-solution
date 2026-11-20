from typing import Any

from neomodel import Q, db
from neomodel.sync_.match import NodeNameResolver, Path

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.generic_repository import (
    _manage_versioning_with_relations,
)
from clinical_mdr_api.domain_repositories.models._utils import ListDistinct
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
)
from clinical_mdr_api.domain_repositories.models.study_auxiliary_device import (
    StudyAuxiliaryDevice,
)
from clinical_mdr_api.domains.study_selections.study_auxiliary_device import (
    StudyAuxiliaryDeviceVO,
)
from clinical_mdr_api.models.study_selections.study_auxiliary_device import (
    StudyAuxiliaryDeviceOGM,
    StudyAuxiliaryDeviceOGMVer,
)
from clinical_mdr_api.repositories._utils import (
    FilterOperator,
    get_field,
    get_field_path,
    get_order_by_clause,
    merge_q_query_filters,
    transform_filters_into_neomodel,
    validate_filters_and_add_search_string,
)
from common.config import settings
from common.exceptions import NotFoundException, ValidationException
from common.utils import validate_page_number_and_page_size

DEVICE_TERM = "has_auxiliary_device__has_selected_term"
TRAVERSALS = (
    "has_after__audit_trail",
    f"{DEVICE_TERM}__has_name_root__latest_final",
    f"{DEVICE_TERM}__has_attributes_root__latest_final",
    f"{DEVICE_TERM}__has_term_root",
)


class StudyAuxiliaryDeviceRepository:
    def __init__(self, author_id: str):
        self.author_id = author_id

    def _study_filter(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[Q]:
        if study_value_version:
            return [
                Q(study_value__has_version__uid=study_uid),
                Q(**{"study_value__has_version|version": study_value_version}),
            ]
        return [Q(study_value__latest_value__uid=study_uid)]

    def _set_submission_values(self, items: list[StudyAuxiliaryDeviceOGM]) -> None:
        # latest HAS_TERM of the selected codelist, so a changed submission value,
        # other codelists and a removed term all resolve to what the codelist showed last
        rows, _ = db.cypher_query(
            """
            MATCH (:StudyAuxiliaryDevice)-[:HAS_AUXILIARY_DEVICE]->(context:CTTermContext)
                -[:HAS_SELECTED_TERM]->(term_root:CTTermRoot)
            WHERE term_root.uid IN $term_uids
            WITH DISTINCT context, term_root
            MATCH (context)-[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot)-[has_term:HAS_TERM]
                ->(codelist_term:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root)
            WITH term_root, codelist_term ORDER BY has_term.start_date DESC
            RETURN term_root.uid, head(collect(codelist_term.submission_value))
            """,
            {"term_uids": list({item.auxiliary_device_term_uid for item in items})},
        )
        submission_values = dict(rows)
        for item in items:
            item.auxiliary_device_submission_value = submission_values.get(
                item.auxiliary_device_term_uid
            )

    def find_all(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> tuple[list[StudyAuxiliaryDeviceOGM], int]:
        q_filters = transform_filters_into_neomodel(
            filter_by=filter_by, model=StudyAuxiliaryDeviceOGM
        )
        q_filters = merge_q_query_filters(q_filters, filter_operator=filter_operator)
        q_filters += self._study_filter(study_uid, study_value_version)
        sort_paths = get_order_by_clause(sort_by=sort_by, model=StudyAuxiliaryDeviceOGM)
        validate_page_number_and_page_size(page_number=page_number, page_size=page_size)
        start: int = (page_number - 1) * page_size
        end: int = start + page_size
        # a term with several CTCodelistTerm nodes gives one row each, so page after
        # dedup; fine for the few devices a study has, page in Cypher if that grows
        nodes = ListDistinct(
            StudyAuxiliaryDevice.nodes.traverse(*TRAVERSALS)
            .order_by(sort_paths[0] if len(sort_paths) > 0 else "order")
            .filter(*q_filters)
            .resolve_subgraph()
        ).distinct()[start : end or None]
        items = [StudyAuxiliaryDeviceOGM.model_validate(node) for node in nodes]
        self._set_submission_values(items)
        total = len(StudyAuxiliaryDevice.nodes.filter(*q_filters)) if total_count else 0
        return items, total

    def find_all_by_study(self, study_uid: str) -> list[StudyAuxiliaryDeviceOGM]:
        return [
            StudyAuxiliaryDeviceOGM.model_validate(node)
            for node in ListDistinct(
                StudyAuxiliaryDevice.nodes.traverse(*TRAVERSALS)
                .filter(study_value__latest_value__uid=study_uid)
                .order_by("order")
                .resolve_subgraph()
            ).distinct()
        ]

    def find_by_uid(self, study_uid: str, uid: str) -> StudyAuxiliaryDeviceOGM:
        nodes = ListDistinct(
            StudyAuxiliaryDevice.nodes.traverse(*TRAVERSALS)
            .filter(uid=uid, study_value__latest_value__uid=study_uid)
            .resolve_subgraph()
        ).distinct()
        NotFoundException.raise_if(len(nodes) == 0, "Study Auxiliary Device", uid)
        item = StudyAuxiliaryDeviceOGM.model_validate(nodes[0])
        self._set_submission_values([item])
        return item

    def get_all_versions(
        self, study_uid: str, uid: str | None = None
    ) -> list[StudyAuxiliaryDeviceOGMVer]:
        filters: dict[str, Any] = {"has_after__audit_trail__uid": study_uid}
        if uid:
            filters["uid"] = uid
        items = [
            StudyAuxiliaryDeviceOGMVer.model_validate(node)
            for node in ListDistinct(
                StudyAuxiliaryDevice.nodes.traverse(
                    *TRAVERSALS, Path(value="has_before", optional=True)
                )
                .filter(**filters)
                .resolve_subgraph()
            ).distinct()
        ]
        self._set_submission_values(items)
        return sorted(items, key=lambda item: item.start_date, reverse=True)

    def save(self, item: StudyAuxiliaryDeviceVO, delete_flag: bool = False):
        create = item.uid is None
        study_root: StudyRoot = StudyRoot.nodes.get(uid=item.study_uid)
        study_value: StudyValue = study_root.latest_value.get_or_none()
        ValidationException.raise_if(
            study_value is None, msg="Study doesn't have draft version."
        )

        term_root = CTTermRoot.nodes.get_or_none(uid=item.auxiliary_device_term_uid)
        NotFoundException.raise_if(
            term_root is None, "Auxiliary device term", item.auxiliary_device_term_uid
        )
        # reads traverse latest_final, a never-approved term would vanish after create
        ValidationException.raise_if(
            create
            and not (
                term_root.has_name_root.single().latest_final.single()
                and term_root.has_attributes_root.single().latest_final.single()
            ),
            msg=f"Auxiliary device term '{item.auxiliary_device_term_uid}' has no approved version.",
        )
        # raises 400 if the term is not in the DEVICE_DEF codelist
        selected_term_node = (
            CTCodelistAttributesRepository().get_or_create_selected_term(
                term_root,
                codelist_submission_value=settings.auxiliary_device_cl_submval,
                allow_removed_terms=not create,
            )
        )

        new_node = StudyAuxiliaryDevice(
            uid=item.uid,
            accepted_version=item.accepted_version,
            order=item.order,
            status=item.status.value,
        )
        new_node.save()
        item.uid = new_node.uid
        new_node.has_auxiliary_device.connect(selected_term_node)

        if create:
            _manage_versioning_with_relations(
                study_root=study_root,
                action_type=Create,
                before=None,
                after=new_node,
                author_id=self.author_id,
            )
            new_node.study_value.connect(study_value)
            return item

        previous_item = study_value.has_study_auxiliary_device.get(uid=item.uid)
        _manage_versioning_with_relations(
            study_root=study_root,
            action_type=Delete if delete_flag else Edit,
            before=previous_item,
            after=new_node,
            exclude_relationships=[StudyAuxiliaryDevice.has_auxiliary_device],
            author_id=self.author_id,
        )
        if not delete_flag:
            new_node.study_value.connect(study_value)
        return item

    def get_distinct_headers(
        self,
        study_uid: str,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        study_value_version: str | None = None,
    ) -> list[Any]:
        filter_by = validate_filters_and_add_search_string(
            search_string, field_name, filter_by
        )
        q_filters = transform_filters_into_neomodel(
            filter_by=filter_by, model=StudyAuxiliaryDeviceOGM
        )
        q_filters = merge_q_query_filters(q_filters, filter_operator=filter_operator)
        q_filters += self._study_filter(study_uid, study_value_version)
        field = get_field(prop=field_name, model=StudyAuxiliaryDeviceOGM)
        field_path = get_field_path(prop=field_name, field=field)
        nodeset = StudyAuxiliaryDevice.nodes
        if "__" in field_path:
            path, prop = field_path.rsplit("__", 1)
            source = NodeNameResolver(path)
            nodeset = nodeset.traverse(path)
        else:
            source = StudyAuxiliaryDevice.__name__.lower()
            prop = field_path
        return (
            nodeset.filter(*q_filters)[:page_size]
            .intermediate_transform(
                {
                    field_path: {
                        "source": source,
                        "source_prop": prop,
                        "include_in_return": True,
                    }
                },
                distinct=True,
                ordering=[field_path],
            )
            .all()
        )
