import datetime
from typing import Any, TypeVar

from neomodel import Q, db
from neomodel.sync_.match import NodeNameResolver, Optional

from clinical_mdr_api.domain_repositories.generic_repository import (
    manage_previous_connected_study_selection_relationships,
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
from clinical_mdr_api.domain_repositories.models.study_disease_milestone import (
    StudyDiseaseMilestone,
)
from clinical_mdr_api.domains.study_selections.study_disease_milestone import (
    StudyDiseaseMilestoneVO,
)
from clinical_mdr_api.models.study_selections.study_disease_milestone import (
    StudyDiseaseMilestoneOGM,
    StudyDiseaseMilestoneOGMVer,
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
from common.exceptions import ValidationException
from common.utils import validate_page_number_and_page_size

# pylint: disable=invalid-name
_StandardsReturnType = TypeVar("_StandardsReturnType")


def get_ctlist_terms_by_name_and_definition(code_list_name: str):
    cypher_query = """
        MATCH (:CTCodelistNameValue {name: $code_list_name})<-[:LATEST_FINAL]-(:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-
        (:CTCodelistRoot)-[:HAS_TERM]->
        (tr:CTTermRoot)-[:HAS_NAME_ROOT]->
        (:CTTermNameRoot)-[:LATEST_FINAL]->
        (ctnv:CTTermNameValue)
        MATCH (tr)-[HAS_ATTRIBUTES_ROOT]->(CTTermAttributesRoot)-[LATEST]->(ctav:CTTermAttributesValue)
        return tr.uid, ctnv.name, ctav.definition
        """
    items, _ = db.cypher_query(cypher_query, {"code_list_name": code_list_name})
    return {a[0]: {"name": a[1], "definition": a[2]} for a in items}


class StudyDiseaseMilestoneRepository:
    def __init__(self, author_id: str):
        self.author_id = author_id

    def create_ctlist_definition(self, code_list_name: str):
        return get_ctlist_terms_by_name_and_definition(code_list_name)

    def find_all_disease_milestone(
        self,
        study_uid: str | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
        **kwargs,
    ) -> tuple[list[StudyDiseaseMilestoneOGM], int]:
        q_filters = self.create_query_filter_statement_neomodel(
            study_uid=study_uid,
            study_value_version=study_value_version,
            filter_by=filter_by,
            **kwargs,
        )
        q_filters = merge_q_query_filters(q_filters, filter_operator=filter_operator)
        sort_paths = get_order_by_clause(
            sort_by=sort_by, model=StudyDiseaseMilestoneOGM
        )
        validate_page_number_and_page_size(page_number=page_number, page_size=page_size)
        start: int = (page_number - 1) * page_size
        end: int = start + page_size
        nodes = ListDistinct(
            StudyDiseaseMilestone.nodes.fetch_relations(
                "has_after__audit_trail",
                "has_disease_milestone_type__has_name_root__latest_final",
                "has_disease_milestone_type__has_attributes_root__latest_final",
            )
            .order_by(sort_paths[0] if len(sort_paths) > 0 else "uid")
            .filter(*q_filters)[start:end]
            .resolve_subgraph()
        ).distinct()
        all_activities = [
            StudyDiseaseMilestoneOGM.model_validate(activity_node)
            for activity_node in nodes
        ]
        if total_count:
            len_query = StudyDiseaseMilestone.nodes.filter(*q_filters)
            all_nodes = len(len_query)

        # pylint: disable=possibly-used-before-assignment
        return all_activities, all_nodes if total_count else 0

    def create_query_filter_statement_neomodel(
        self,
        study_uid: str | None = None,
        study_value_version: str | None = None,
        filter_by: dict | None = None,
    ) -> tuple[dict, list[Q]]:
        q_filters = transform_filters_into_neomodel(
            filter_by=filter_by, model=StudyDiseaseMilestoneOGM
        )
        if study_uid:
            if study_value_version:
                q_filters.append(Q(study_value__has_version__uid=study_uid))
                q_filters.append(
                    Q(**{"study_value__has_version|version": study_value_version})
                )
            else:
                q_filters.append(Q(study_value__latest_value__uid=study_uid))
        return q_filters

    def find_all_disease_milestones_by_study(
        self, study_uid: str
    ) -> _StandardsReturnType | None:
        all_disease_milestones = [
            StudyDiseaseMilestoneOGM.model_validate(sas_node)
            for sas_node in ListDistinct(
                StudyDiseaseMilestone.nodes.fetch_relations(
                    "has_after__audit_trail",
                    "has_disease_milestone_type__has_name_root__latest_final",
                    "has_disease_milestone_type__has_attributes_root__latest_final",
                )
                .filter(study_value__latest_value__uid=study_uid)
                .order_by("order")
                .resolve_subgraph()
            ).distinct()
        ]
        return all_disease_milestones

    def find_by_uid(self, uid: str) -> StudyDiseaseMilestoneVO:
        disease_milestone_node = ListDistinct(
            StudyDiseaseMilestone.nodes.fetch_relations(
                "has_after__audit_trail",
                "study_value__latest_value",
                "has_disease_milestone_type__has_name_root__latest_final",
                "has_disease_milestone_type__has_attributes_root__latest_final",
            )
            .filter(uid=uid)
            .resolve_subgraph()
        ).distinct()

        ValidationException.raise_if(
            len(disease_milestone_node) > 1,
            msg=f"Found more than one StudyDiseaseMilestone node with UID '{uid}'.",
        )
        ValidationException.raise_if(
            len(disease_milestone_node) == 0,
            msg=f"Study Disease Milestone with UID '{uid}' doesn't exist.",
        )

        return StudyDiseaseMilestoneOGM.model_validate(disease_milestone_node[0])

    def get_all_versions(self, uid: str, study_uid):
        return sorted(
            [
                StudyDiseaseMilestoneOGMVer.model_validate(se_node)
                for se_node in ListDistinct(
                    StudyDiseaseMilestone.nodes.fetch_relations(
                        "has_after__audit_trail",
                        "has_disease_milestone_type__has_name_root__latest_final",
                        "has_disease_milestone_type__has_attributes_root__latest_final",
                        Optional("has_before"),
                    )
                    .filter(uid=uid, has_after__audit_trail__uid=study_uid)
                    .resolve_subgraph()
                )
            ],
            key=lambda item: item.start_date,
            reverse=True,
        )

    def get_all_disease_milestone_versions(self, study_uid: str):
        return sorted(
            [
                StudyDiseaseMilestoneOGMVer.model_validate(se_node)
                for se_node in (
                    StudyDiseaseMilestone.nodes.fetch_relations(
                        "has_after__audit_trail",
                        "has_disease_milestone_type__has_name_root__latest_final",
                        "has_disease_milestone_type__has_attributes_root__latest_final",
                        Optional("has_before"),
                    )
                    .filter(has_after__audit_trail__uid=study_uid)
                    .order_by("order")
                    .resolve_subgraph()
                )
            ],
            key=lambda item: item.start_date,
            reverse=True,
        )

    def save(self, disease_milestone: StudyDiseaseMilestoneVO, delete_flag=False):
        # if exists
        if disease_milestone.uid is not None:
            # if has to be deleted
            if delete_flag:
                self._update(disease_milestone, create=False, delete=True)
            # if has to be modified
            else:
                return self._update(disease_milestone, create=False)
        # if has to be created
        else:
            return self._update(disease_milestone, create=True)
        return None

    def _update(
        self, item: StudyDiseaseMilestoneVO, create: bool = False, delete=False
    ):
        study_root: StudyRoot = StudyRoot.nodes.get(uid=item.study_uid)
        study_value: StudyValue = study_root.latest_value.get_or_none()

        ValidationException.raise_if(
            study_value is None, msg="Study doesn't have draft version."
        )

        if not create:
            previous_item = study_value.has_study_disease_milestone.get(uid=item.uid)
        new_study_disease_milestone = StudyDiseaseMilestone(
            uid=item.uid,
            accepted_version=item.accepted_version,
            order=item.order,
            status=item.status.value,
            repetition_indicator=item.repetition_indicator,
        )
        if item.uid is not None:
            new_study_disease_milestone.uid = item.uid
        new_study_disease_milestone.save()
        if item.uid is None:
            item.uid = new_study_disease_milestone.uid
        ct_disease_milestone_type = CTTermRoot.nodes.get(uid=item.dm_type.name)
        new_study_disease_milestone.has_disease_milestone_type.connect(
            ct_disease_milestone_type
        )

        if create:
            self.manage_versioning_create(
                study_root=study_root, item=item, new_item=new_study_disease_milestone
            )
            new_study_disease_milestone.study_value.connect(study_value)
        else:
            if delete is False:
                # update
                self.manage_versioning_update(
                    study_root=study_root,
                    item=item,
                    # pylint: disable=possibly-used-before-assignment
                    previous_item=previous_item,
                    new_item=new_study_disease_milestone,
                )
                new_study_disease_milestone.study_value.connect(study_value)
            else:
                # delete
                self.manage_versioning_delete(
                    study_root=study_root,
                    item=item,
                    previous_item=previous_item,
                    new_item=new_study_disease_milestone,
                )
            manage_previous_connected_study_selection_relationships(
                previous_item=previous_item,
                study_value_node=study_value,
                new_item=new_study_disease_milestone,
            )
        return item

    def manage_versioning_create(
        self,
        study_root: StudyRoot,
        item: StudyDiseaseMilestoneVO,
        new_item: StudyDiseaseMilestone,
    ):
        action = Create(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=item.status.value,
            author_id=item.author_id,
        )
        action.save()
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def manage_versioning_update(
        self,
        study_root: StudyRoot,
        item: StudyDiseaseMilestoneVO,
        previous_item: StudyDiseaseMilestone,
        new_item: StudyDiseaseMilestone,
    ):
        action = Edit(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=item.status.value,
            author_id=item.author_id,
        )
        action.save()
        action.has_before.connect(previous_item)
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def manage_versioning_delete(
        self,
        study_root: StudyRoot,
        item: StudyDiseaseMilestoneVO,
        previous_item: StudyDiseaseMilestone,
        new_item: StudyDiseaseMilestone,
    ):
        action = Delete(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=item.status.value,
            author_id=item.author_id,
        )
        action.save()
        action.has_before.connect(previous_item)
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def get_distinct_headers(
        self,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        page_size: int = 10,
    ) -> list[Any]:
        """
        Method runs a cypher query to fetch possible values for a given field_name, with a limit of page_size.
        It uses generic filtering capability, on top of filtering the field_name with provided search_string.

        :param field_name: Field name for which to return possible values
        :param search_string
        :param filter_by:
        :param filter_operator: Same as for generic filtering
        :param page_size: Max number of values to return. Default 10
        :return list[Any]:
        """

        # Add header field name to filter_by, to filter with a CONTAINS pattern
        filter_by = validate_filters_and_add_search_string(
            search_string, field_name, filter_by
        )
        q_filters = transform_filters_into_neomodel(
            filter_by=filter_by, model=StudyDiseaseMilestoneOGM
        )
        q_filters = merge_q_query_filters(q_filters, filter_operator=filter_operator)
        field = get_field(prop=field_name, model=StudyDiseaseMilestoneOGM)
        field_path = get_field_path(prop=field_name, field=field)
        nodeset = StudyDiseaseMilestone.nodes
        if "__" in field_path:
            path, prop = field_path.rsplit("__", 1)
            source = NodeNameResolver(path)
            nodeset = nodeset.fetch_relations(path)
        else:
            # FIXME: we need a proper way to resolve the variable name (NodeNameResolver
            # does not support 'self'...)
            source = StudyDiseaseMilestone.__name__.lower()
            prop = field_path
        values = (
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
            )
            .all()
        )
        return values
