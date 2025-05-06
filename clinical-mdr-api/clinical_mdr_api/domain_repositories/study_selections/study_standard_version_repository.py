import datetime
from typing import Sequence, TypeVar

from neomodel import Q
from neomodel.sync_.match import Optional

from clinical_mdr_api.domain_repositories.generic_repository import (
    manage_previous_connected_study_selection_relationships,
)
from clinical_mdr_api.domain_repositories.models._utils import ListDistinct
from clinical_mdr_api.domain_repositories.models.controlled_terminology import CTPackage
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
)
from clinical_mdr_api.domain_repositories.models.study_standard_version import (
    StudyStandardVersion,
)
from clinical_mdr_api.domains.study_selections.study_selection_standard_version import (
    StudyStandardVersionVO,
)
from clinical_mdr_api.models.study_selections.study_standard_version import (
    StudyStandardVersionOGM,
    StudyStandardVersionOGMVer,
)
from clinical_mdr_api.repositories._utils import (
    FilterOperator,
    get_order_by_clause,
    merge_q_query_filters,
    transform_filters_into_neomodel,
)
from common.exceptions import ValidationException
from common.utils import validate_page_number_and_page_size

# pylint: disable=invalid-name
_StandardsReturnType = TypeVar("_StandardsReturnType")


class StudyStandardVersionRepository:
    def __init__(self, author_id: str):
        self.author_id = author_id

    def find_all_standard_version(
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
    ) -> tuple[list[StudyStandardVersionOGM], int]:
        q_filters = self.create_query_filter_statement_neomodel(
            study_uid=study_uid,
            study_value_version=study_value_version,
            filter_by=filter_by,
            **kwargs,
        )
        q_filters = merge_q_query_filters(q_filters, filter_operator=filter_operator)
        sort_paths = get_order_by_clause(sort_by=sort_by, model=StudyStandardVersionOGM)
        validate_page_number_and_page_size(page_number=page_number, page_size=page_size)
        start: int = (page_number - 1) * page_size
        end: int = start + page_size
        nodes = ListDistinct(
            StudyStandardVersion.nodes.fetch_relations(
                "has_after__audit_trail",
                "has_ct_package",
            )
            .order_by(sort_paths[0] if len(sort_paths) > 0 else "uid")
            .filter(*q_filters)[start:end]
            .resolve_subgraph()
        ).distinct()
        all_standard_versions = [
            StudyStandardVersionOGM.model_validate(standard_version_node)
            for standard_version_node in nodes
        ]
        all_nodes = 0
        if total_count:
            len_query = StudyStandardVersion.nodes.filter(*q_filters)
            all_nodes = len(len_query)
        return all_standard_versions, all_nodes if total_count else 0

    def create_query_filter_statement_neomodel(
        self,
        study_uid: str | None = None,
        study_value_version: str | None = None,
        filter_by: dict | None = None,
    ) -> tuple[dict, list[Q]]:
        q_filters = transform_filters_into_neomodel(
            filter_by=filter_by, model=StudyStandardVersionOGM
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

    def find_standard_versions_in_study(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> Sequence[StudyStandardVersionOGM] | None:
        if study_value_version:
            filters = {
                "study_value__has_version|version": study_value_version,
                "study_value__has_version__uid": study_uid,
            }
        else:
            filters = {
                "study_value__latest_value__uid": study_uid,
            }
        standard_versions = [
            StudyStandardVersionOGM.model_validate(sas_node)
            for sas_node in ListDistinct(
                StudyStandardVersion.nodes.fetch_relations(
                    "has_after__audit_trail",
                    "has_ct_package",
                )
                .filter(**filters)
                .order_by("uid")
                .resolve_subgraph()
            ).distinct()
        ]
        return standard_versions

    def find_by_uid(
        self,
        study_uid: str,
        study_standard_version_uid: str,
        study_value_version: str | None = None,
    ) -> StudyStandardVersionVO:
        if study_value_version:
            filters = {
                "study_value__has_version|version": study_value_version,
                "study_value__has_version__uid": study_uid,
                "uid": study_standard_version_uid,
            }
        else:
            filters = {
                "study_value__latest_value__uid": study_uid,
                "uid": study_standard_version_uid,
            }
        standard_version_node = ListDistinct(
            StudyStandardVersion.nodes.fetch_relations(
                "has_after__audit_trail",
                "has_ct_package",
            )
            .filter(**filters)
            .resolve_subgraph()
        ).distinct()

        ValidationException.raise_if(
            len(standard_version_node) > 1,
            msg=f"Found more than one StudyStandardVersion node with UID '{study_standard_version_uid}'.",
        )
        ValidationException.raise_if(
            len(standard_version_node) == 0,
            msg=f"The StudyStandardVersion with UID '{study_standard_version_uid}' doesn't exist.",
        )

        return StudyStandardVersionOGM.model_validate(standard_version_node[0])

    def get_all_versions(self, uid: str, study_uid):
        return sorted(
            [
                StudyStandardVersionOGMVer.model_validate(se_node)
                for se_node in StudyStandardVersion.nodes.fetch_relations(
                    "has_after__audit_trail", "has_ct_package", Optional("has_before")
                )
                .filter(uid=uid, has_after__audit_trail__uid=study_uid)
                .resolve_subgraph()
            ],
            key=lambda item: item.start_date,
            reverse=True,
        )

    def get_all_study_version_versions(self, study_uid: str):
        return sorted(
            [
                StudyStandardVersionOGMVer.model_validate(se_node)
                for se_node in StudyStandardVersion.nodes.fetch_relations(
                    "has_after__audit_trail", "has_ct_package", Optional("has_before")
                )
                .filter(has_after__audit_trail__uid=study_uid)
                .order_by("has_after__audit_trail.date")
                .resolve_subgraph()
            ],
            key=lambda item: item.start_date,
            reverse=False,
        )

    def save(self, study_standard_version: StudyStandardVersionVO, delete_flag=False):
        # if exists
        if study_standard_version.uid is not None:
            # if has to be deleted
            if delete_flag:
                self._update(study_standard_version, create=False, delete=True)
            # if has to be modified
            else:
                return self._update(study_standard_version, create=False)
        # if has to be created
        else:
            return self._update(study_standard_version, create=True)
        return None

    def _update(self, item: StudyStandardVersionVO, create: bool = False, delete=False):
        study_root: StudyRoot = StudyRoot.nodes.get(uid=item.study_uid)
        study_value: StudyValue = study_root.latest_value.get_or_none()
        previous_item = None
        ValidationException.raise_if(
            study_value is None, "Study doesn't have draft version."
        )
        if not create:
            previous_item = study_value.has_study_standard_version.get(uid=item.uid)
        new_study_standard_version = StudyStandardVersion(
            uid=item.uid,
            status=item.study_status.value,
            description=item.description,
            automatically_created=item.automatically_created,
        )
        if item.uid is not None:
            new_study_standard_version.uid = item.uid
        new_study_standard_version.save()
        if item.uid is None:
            item.uid = new_study_standard_version.uid
        ct_package = CTPackage.nodes.get(uid=item.ct_package_uid)
        new_study_standard_version.has_ct_package.connect(ct_package)

        if create:
            self.manage_versioning_create(
                study_root=study_root, item=item, new_item=new_study_standard_version
            )
            new_study_standard_version.study_value.connect(study_value)
        else:
            if delete is False:
                # update
                self.manage_versioning_update(
                    study_root=study_root,
                    item=item,
                    previous_item=previous_item,
                    new_item=new_study_standard_version,
                )
                new_study_standard_version.study_value.connect(study_value)
            else:
                # delete
                self.manage_versioning_delete(
                    study_root=study_root,
                    item=item,
                    previous_item=previous_item,
                    new_item=new_study_standard_version,
                )
            manage_previous_connected_study_selection_relationships(
                previous_item=previous_item,
                study_value_node=study_value,
                new_item=new_study_standard_version,
            )
        return item

    def manage_versioning_create(
        self,
        study_root: StudyRoot,
        item: StudyStandardVersionVO,
        new_item: StudyStandardVersion,
    ):
        action = Create(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=item.study_status.value,
            author_id=item.author_id,
        )
        action.save()
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def manage_versioning_update(
        self,
        study_root: StudyRoot,
        item: StudyStandardVersionVO,
        previous_item: StudyStandardVersion,
        new_item: StudyStandardVersion,
    ):
        action = Edit(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=item.study_status.value,
            author_id=item.author_id,
        )
        action.save()
        action.has_before.connect(previous_item)
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def manage_versioning_delete(
        self,
        study_root: StudyRoot,
        item: StudyStandardVersionVO,
        previous_item: StudyStandardVersion,
        new_item: StudyStandardVersion,
    ):
        action = Delete(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=item.study_status.value,
            author_id=item.author_id,
        )
        action.save()
        action.has_before.connect(previous_item)
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)
