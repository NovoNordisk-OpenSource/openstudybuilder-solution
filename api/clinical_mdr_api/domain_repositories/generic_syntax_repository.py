import abc
from datetime import datetime
from typing import Any, Generic, Literal, TypeVar, overload

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivityRoot,
    ActivitySubGroupRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    SyntaxTemplateRoot,
    SyntaxTemplateValue,
)
from clinical_mdr_api.domains.libraries.parameter_term import (
    ParameterTermEntryVO,
    SimpleParameterTermVO,
)
from clinical_mdr_api.domains.syntax_templates.template import (
    InstantiationCountsVO,
    TemplateAggregateRootBase,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemStatus,
)
from clinical_mdr_api.repositories._utils import FilterOperator, sb_clear_cache
from common.config import settings
from common.exceptions import NotFoundException

_AggregateRootType = TypeVar("_AggregateRootType", bound=LibraryItemAggregateRootBase)


class GenericSyntaxRepository(
    LibraryItemRepositoryImplBase[_AggregateRootType],
    Generic[_AggregateRootType],
    abc.ABC,
):

    def find_by_uid_2(
        self,
        uid: str,
        *,
        version: str | None = None,
        status: LibraryItemStatus | None = None,
        at_specific_date: datetime | None = None,
        for_update: bool = False,
        return_study_count: bool = False,
        return_instantiation_counts: bool = False,
    ):
        "Use find_by_uid instead"

    def find_all(
        self,
        *,
        status: LibraryItemStatus | None = None,
        library_name: str | None = None,
        return_study_count: bool = False,
    ):
        "Use get_all instead"

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        study_count: int = 0,
        counts: InstantiationCountsVO | None = None,
    ):
        "Use _create_ar instead"

    @abc.abstractmethod
    def _create_ar(
        self,
        root: SyntaxTemplateRoot,
        library: Library,
        relationship: VersionRelationship,
        value: SyntaxTemplateValue,
        study_count: int = 0,
        **kwargs,
    ) -> TemplateAggregateRootBase:
        raise NotImplementedError

    @overload
    def find_by_uid(
        self,
        uid: str | None,
        for_update=False,
        *,
        library_name: str | None = None,
        status: LibraryItemStatus | None = None,
        version: str | None = None,
        return_study_count: bool = False,
        for_audit_trail: Literal[False] = False,
    ) -> _AggregateRootType: ...
    @overload
    def find_by_uid(
        self,
        uid: str | None,
        for_update=False,
        *,
        library_name: str | None = None,
        status: LibraryItemStatus | None = None,
        version: str | None = None,
        return_study_count: bool = False,
        for_audit_trail: Literal[True] = True,
    ) -> list[_AggregateRootType]: ...
    def find_by_uid(
        self,
        uid: str | None,
        for_update=False,
        *,
        library_name: str | None = None,
        status: LibraryItemStatus | None = None,
        version: str | None = None,
        return_study_count: bool = False,
        for_audit_trail: bool = False,
    ) -> _AggregateRootType | list[_AggregateRootType]:
        return self.find_by_uid_optimized(  # type: ignore[call-overload]
            uid=uid,
            for_update=for_update,
            library_name=library_name,
            status=status,
            version=version,
            return_study_count=return_study_count,
            for_audit_trail=for_audit_trail,
        )

    def get_all(
        self,
        *,
        status: LibraryItemStatus | None = None,
        library_name: str | None = None,
        return_study_count: bool = False,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        for_audit_trail: bool = False,
    ) -> tuple[list[Any], int]:
        return self.get_all_optimized(
            status=status,
            library_name=library_name,
            return_study_count=return_study_count,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=filter_by,
            filter_operator=filter_operator,
            total_count=total_count,
            for_audit_trail=for_audit_trail,
        )

    def get_headers(
        self,
        *,
        field_name: str,
        status: LibraryItemStatus | None = None,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ):
        return self.get_headers_optimized(
            field_name=field_name,
            status=status,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )

    def _parse_parameter_terms(
        self, instance_parameters
    ) -> dict[int, list[ParameterTermEntryVO]]:
        # Note that this method is used both by templates for default values and instances for values
        # Hence the checks we have to make on the existence of the set_number property
        parameter_strings = []
        # First, parse results from the database
        for position_parameters in instance_parameters:
            position, param_name, param_terms, _ = position_parameters
            if len(param_terms) == 0:
                # If we find an empty (NA) parameter term, temporary save a none object that will be replaced later
                parameter_strings.append(
                    {
                        "set_number": 0,
                        "position": position,
                        "index": None,
                        "definition": None,
                        "template": None,
                        "parameter_uid": None,
                        "parameter_term": None,
                        "parameter_name": param_name,
                        "labels": [],
                    }
                )

            for parameter in param_terms:
                parameter_strings.append(
                    {
                        "set_number": (
                            parameter["set_number"] if "set_number" in parameter else 0
                        ),
                        "position": parameter["position"],
                        "index": parameter["index"],
                        "parameter_name": parameter["parameter_name"],
                        "parameter_term": parameter["parameter_term"],
                        "parameter_uid": parameter["parameter_uid"],
                        "definition": parameter["definition"],
                        "template": parameter["template"],
                        "labels": parameter["labels"],
                    }
                )

        # Then, start building the nested dictionary to group parameter terms in a list
        data_dict: dict[Any, Any] = {}
        # Create the first two levels, like
        # set_number
        # --> position
        for param in parameter_strings:
            if param["set_number"] not in data_dict:
                data_dict[param["set_number"]] = {}
            data_dict[param["set_number"]][param["position"]] = {
                "parameter_name": param["parameter_name"],
                "definition": param["definition"],
                "template": param["template"],
                "parameter_uids": [],
                "conjunction": next(
                    x
                    for x in instance_parameters
                    if x[0] == param["position"]  # type: ignore[arg-type,misc]
                    and (
                        len(x[2]) == 0
                        or (
                            "set_number" in x[2][0]
                            and x[2][0]["set_number"] == param["set_number"]
                        )
                    )
                )[3],
                "labels": param["labels"],
            }

        # Then, unwind to create the third level, like:
        # set_number
        # --> position
        # -----> [parameter_uids]
        for param in parameter_strings:
            data_dict[param["set_number"]][param["position"]]["parameter_uids"].append(
                {
                    "index": param["index"],
                    "parameter_uid": param["parameter_uid"],
                    "parameter_name": param["parameter_name"],
                    "parameter_term": param["parameter_term"],
                    "labels": param["labels"],
                }
            )

        # Finally, convert the nested dictionary to a list of ParameterTermEntryVO objects, grouped by value set
        return_dict = {}
        for set_number, term_set in data_dict.items():
            term_set = [x[1] for x in sorted(term_set.items(), key=lambda x: x[0])]
            parameter_list: list[ParameterTermEntryVO] = []
            for item in term_set:
                term_list = []
                for value in sorted(
                    item["parameter_uids"],
                    key=lambda x: x["index"] or 0,
                ):
                    if value["parameter_uid"]:
                        simple_parameter_term_vo = (
                            self._parameter_from_repository_values(value)
                        )
                        term_list.append(simple_parameter_term_vo)
                pve = ParameterTermEntryVO.from_repository_values(
                    parameters=term_list,
                    parameter_name=item["parameter_name"],
                    conjunction=item.get("conjunction", ""),
                    labels=item.get("labels", []),
                )
                parameter_list.append(pve)
            return_dict[set_number] = parameter_list
        return return_dict

    def _parameter_from_repository_values(self, value):
        simple_parameter_term_vo = SimpleParameterTermVO.from_repository_values(
            uid=value["parameter_uid"],
            value=value["parameter_term"],
            labels=value["labels"],
        )
        return simple_parameter_term_vo

    def get_template_type_uid(self, syntax_node: SyntaxTemplateRoot) -> str:
        """
        Get the UID of the type associated with a given Syntax Template.

        Args:
            syntax_node (SyntaxTemplateRoot): Syntax Template Root to get the type for.

        Returns:
            str: The UID of the type associated with the given Syntax Template.

        Raises:
            NotFoundException: If a Syntax Template doesn't exist.
        """

        NotFoundException.raise_if_not(
            syntax_node, msg="The requested Syntax Template doesn't exist."
        )

        ct_term = syntax_node.has_type.get_or_none()

        if ct_term:
            ct_term = ct_term.has_selected_term.get_or_none()

        return ct_term.uid if ct_term else None

    def _get_indication(self, uid: str) -> DictionaryTermRoot:
        # Finds indication in database based on root node uid
        return DictionaryTermRoot.nodes.get(uid=uid)

    def _get_category(self, uid: str) -> CTTermRoot:
        # Finds category in database based on root node uid
        return CTTermRoot.nodes.get(uid=uid)

    def _get_activity(self, uid: str) -> ActivityRoot:
        # Finds activity in database based on root node uid
        return ActivityRoot.nodes.get(uid=uid)

    def _get_activity_group(self, uid: str) -> ActivityGroupRoot:
        # Finds activity group in database based on root node uid
        return ActivityGroupRoot.nodes.get(uid=uid)

    def _get_activity_subgroup(self, uid: str) -> ActivitySubGroupRoot:
        # Finds activity sub group in database based on root node uid
        return ActivitySubGroupRoot.nodes.get(uid=uid)

    def _get_template_type(self, uid: str) -> CTTermRoot:
        # Finds template type in database based on root node uid
        return CTTermRoot.nodes.get(uid=uid)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def patch_indications(self, uid: str, indication_uids: list[str] | None) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_indication.disconnect_all()
        for indication in indication_uids or []:
            indication = self._get_indication(indication)
            root.has_indication.connect(indication)

    def _get_mapped_codelist_submission_value(self):
        mapping = {
            "Endpoint": (
                settings.syntax_endpoint_category_cl_submval,
                settings.syntax_endpoint_sub_category_cl_submval,
            ),
            "Criteria": (
                settings.syntax_criteria_category_cl_submval,
                settings.syntax_criteria_sub_category_cl_submval,
            ),
            "Objective": (settings.syntax_objective_category_cl_submval, None),
        }

        target = getattr(self, "template_class", None) or self.root_class
        target = (
            target.__label__.removesuffix("Root")
            .removesuffix("Template")
            .removesuffix("PreInstance")
        )

        return mapping.get(target)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def patch_categories(self, uid: str, category_uids: list[str] | None) -> None:
        cl_submval = self._get_mapped_codelist_submission_value()

        root = self.root_class.nodes.get(uid=uid)
        root.has_category.disconnect_all()
        for category_uid in category_uids or []:
            if category := self._get_category(category_uid):
                selected_term_node = (
                    CTCodelistAttributesRepository().get_or_create_selected_term(
                        category,
                        codelist_submission_value=cl_submval[0],
                        catalogue_name=settings.sdtm_ct_catalogue_name,
                    )
                )
                root.has_category.connect(selected_term_node)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def patch_subcategories(
        self, uid: str, sub_category_uids: list[str] | None
    ) -> None:
        cl_submval = self._get_mapped_codelist_submission_value()

        root = self.root_class.nodes.get(uid=uid)
        root.has_subcategory.disconnect_all()
        for sub_category_uid in sub_category_uids or []:
            if sub_category := self._get_category(sub_category_uid):
                selected_term_node = (
                    CTCodelistAttributesRepository().get_or_create_selected_term(
                        sub_category,
                        codelist_submission_value=cl_submval[1],
                        catalogue_name=settings.sdtm_ct_catalogue_name,
                    )
                )
                root.has_subcategory.connect(selected_term_node)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def patch_activities(self, uid: str, activity_uids: list[str] | None) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_activity.disconnect_all()
        for activity in activity_uids or []:
            activity = self._get_activity(activity)
            root.has_activity.connect(activity)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def patch_activity_groups(
        self, uid: str, activity_group_uids: list[str] | None
    ) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_activity_group.disconnect_all()
        for group in activity_group_uids or []:
            group = self._get_activity_group(group)
            root.has_activity_group.connect(group)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def patch_activity_subgroups(
        self, uid: str, activity_subgroup_uids: list[str] | None
    ) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_activity_subgroup.disconnect_all()
        for group in activity_subgroup_uids or []:
            sub_group = self._get_activity_subgroup(group)
            root.has_activity_subgroup.connect(sub_group)

    def patch_is_confirmatory_testing(
        self, uid: str, is_confirmatory_testing: bool
    ) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.is_confirmatory_testing = is_confirmatory_testing
        self._db_save_node(root)

    def _create(self, item: _AggregateRootType):
        item = super()._create(item)
        root = None
        if item.uid:
            root = self.root_class.nodes.get(uid=item.uid)
            root.sequence_id = item.sequence_id
            self._db_save_node(root)

        return root, item

    def _are_changes_possible(
        self,
        versioned_object: _AggregateRootType,
        previous_versioned_object: _AggregateRootType,
    ) -> bool:
        new_status = versioned_object.item_metadata.status
        prev_status = previous_versioned_object.item_metadata.status
        possible_states = (LibraryItemStatus.DRAFT, LibraryItemStatus.FINAL)
        return prev_status in possible_states and new_status in possible_states
