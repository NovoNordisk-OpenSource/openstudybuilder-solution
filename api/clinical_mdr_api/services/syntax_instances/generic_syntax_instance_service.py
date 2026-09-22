import abc
from typing import Callable, TypeVar

from neomodel import db
from neomodel.exceptions import DoesNotExist
from neomodel.sync_.node import NodeMeta
from pydantic import BaseModel

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    GenericRepository,
)
from clinical_mdr_api.domain_repositories.models.syntax import SyntaxTemplateRoot
from clinical_mdr_api.domains.libraries.object import ParametrizedTemplateVO
from clinical_mdr_api.domains.libraries.parameter_term import (
    ParameterTermEntryVO,
    SimpleParameterTermVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyComponentEnum,
)
from clinical_mdr_api.domains.syntax_templates.template import TemplateVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.syntax_templates.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.services._utils import is_library_editable, process_parameters
from clinical_mdr_api.services.generic_syntax_service import GenericSyntaxService
from clinical_mdr_api.services.studies.study import StudyService
from common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)

_AggregateRootType = TypeVar("_AggregateRootType")


class GenericSyntaxInstanceService(GenericSyntaxService[_AggregateRootType], abc.ABC):
    """
    This class is generic library object service. It can provide services for any type
    of object derived from templates. Supports generic versioning proces with exception that
    it not allows to create new version after it is approved.

    Configuration options:
    aggregate_class - a class of Aggregate root that supports selected object
    repository_interface - repository interface for selected object
    template_repository_interface - repository for template object that selected object is created from
    template_uid_property - name of template uid property from pydantic models supporting selected object
    """

    aggregate_class: type
    repository_interface: type
    template_repository_interface: type
    template_uid_property: str
    parametrized_template_vo_class: type = ParametrizedTemplateVO
    _allowed_parameters = None

    @property
    def template_repository(self) -> GenericRepository:
        """
        gets template object repository based on interface
        """
        return self.template_repository_interface()

    def _get_parameter_term(self, uid: str) -> tuple[str, list[str]]:
        """
        Return parameter term based on uid
        """
        params = []
        for allowed_parameter in self._allowed_parameters:
            params.extend(allowed_parameter["terms"])
        params_dict = {item["uid"]: item for item in params}
        return params_dict.get(uid, {}).get("name"), params_dict.get(uid, {}).get(
            "labels"
        )

    def create_ar_from_input_values(
        self,
        template,
        next_available_sequence_id_callback: Callable[..., str] = lambda _: "",
        generate_uid_callback=None,
        study_uid: str | None = None,
        template_uid: str | None = None,
        include_study_endpoints: bool = False,
    ) -> _AggregateRootType:
        parameter_terms = self._create_parameter_entries(
            template,
            template_uid=template_uid,
            study_uid=study_uid,
            include_study_endpoints=include_study_endpoints,
        )

        template_uid = template_uid or getattr(template, self.template_uid_property)
        template_root = SyntaxTemplateRoot.nodes.get_or_none(uid=template_uid)

        template_vo = self.parametrized_template_vo_class.from_input_values_2(
            template_uid=template_uid,
            template_sequence_id=getattr(template_root, "sequence_id", None),
            parameter_terms=parameter_terms,
            get_final_template_vo_by_template_uid_callback=self._get_template_vo_by_template_uid,
            library_name=template.library_name,
        )

        library_vo = LibraryVO.from_input_values_2(
            library_name=template.library_name,
            is_library_editable_callback=is_library_editable,
        )

        item = self.aggregate_class.from_input_values(
            author_id=self.author_id,
            template=template_vo,
            library=library_vo,
            generate_uid_callback=(
                self.repository.generate_uid_callback
                if generate_uid_callback is None
                else generate_uid_callback
            ),
            next_available_sequence_id_callback=next_available_sequence_id_callback,
        )
        return item

    def create(
        self, template: BaseModel, preview=False, template_uid: str | None = None
    ) -> BaseModel:
        """
        Supports create object action.
        When the preview parameter is set to true, don't create the object, just preview it.
        """
        self.authorize_user_defined_syntax_write(template.library_name)

        item = None
        try:
            # Transaction that is performing initial save
            with db.transaction:
                item = self.create_ar_from_input_values(
                    template, template_uid=template_uid
                )

                if not preview:
                    AlreadyExistsException.raise_if(
                        self.repository.check_exists_by_name(item.name),
                        field_value=item.name,
                        field_name="Name",
                    )

                    self.repository.save(item)

            return self._transform_aggregate_root_to_pydantic_model(item_ar=item)
        except DoesNotExist as exc:
            raise NotFoundException("Library", template.library_name, "Name") from exc

    def _get_template_vo_by_template_uid(self, template_uid: str) -> TemplateVO | None:
        """
        Helper function getting template for given template uid.
        """
        template_ar = self.template_repository.find_by_uid(
            template_uid, status=LibraryItemStatus.FINAL
        )
        return template_ar.template_value if template_ar is not None else None

    @db.transaction
    def find_by(self, name: str):
        item = self.repository.find_by(name=name)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def edit_draft(self, uid, template: BaseModel):
        """
        Supports edit draft action
        """
        item = self.repository.find_by_uid(uid, for_update=True)
        parameter_terms = self._create_parameter_entries(
            template, template_uid=item.template_uid
        )

        template_vo = self.parametrized_template_vo_class.from_input_values_2(
            template_uid=item.template_uid,
            template_sequence_id=item.template_sequence_id,
            parameter_terms=parameter_terms,
            get_final_template_vo_by_template_uid_callback=self._get_template_vo_by_template_uid,
            library_name=item.template_library_name,
        )
        item.edit_draft(
            author_id=self.author_id,
            change_description=template.change_description,
            template=template_vo,
        )
        self.repository.save(item)

        return self._transform_aggregate_root_to_pydantic_model(item)

    def create_new_version(self, uid: str, template: BaseModel) -> BaseModel:
        """
        Create new version is not allowed for objects derived from templates.
        Only cascading update can do that
        """
        raise NotImplementedError("You cannot create new version")

    @db.transaction
    def get_parameters(
        self,
        uid: str,
        study_uid: str | None = None,
        include_study_endpoints: bool = False,
    ):
        try:
            item = self.repository.find_by_uid(uid)
            parameters = self.template_repository.get_parameters_including_terms(
                item.template_uid,
                study_uid=study_uid,
                include_study_endpoints=include_study_endpoints,
            )
            return process_parameters(parameters)
        except DoesNotExist as exc:
            raise NotFoundException(field_value=uid) from exc

    def _create_parameter_entries(
        self,
        template,
        template_uid: str | None = None,
        study_uid: str | None = None,
        include_study_endpoints: bool = False,
    ) -> list[ParameterTermEntryVO]:
        """
        Creates list of Parameter Term Entries that is used in aggregate. These contain:
        parameter name, conjunctions, uids, and terms of parameters
        """
        if template_uid is None:
            template_uid = getattr(template, self.template_uid_property)

        if template.parameter_terms is None:
            template.parameter_terms = []
        template_parameter_terms = [
            term.uid
            for parameter in template.parameter_terms
            for term in parameter.terms
        ]

        parameter_terms = []
        self._allowed_parameters = (
            self.template_repository.get_parameters_including_terms(
                template_uid,
                study_uid=study_uid,
                include_study_endpoints=include_study_endpoints,
                parameter_term_uids_to_fetch=template_parameter_terms,
            )
        )
        ValidationException.raise_if(
            not template.parameter_terms and self._allowed_parameters,
            msg="parameter_terms must be provided.",
        )

        parameter: TemplateParameterMultiSelectInput
        idx = 0
        for _, allowed_parameter in enumerate(self._allowed_parameters):
            if not template.parameter_terms:
                continue

            parameter = template.parameter_terms[idx]
            uids: list[SimpleParameterTermVO] = []

            if len(parameter.terms or []) == 0:
                # If we have an empty parameter value selection, send an empty list with default type fro the allowed parameters.
                pve = ParameterTermEntryVO.from_input_values(
                    parameter_exists_callback=self._repos.parameter_repository.parameter_name_exists,
                    conjunction_exists_callback=lambda _: True,  # TODO: provide proper callback here
                    parameter_term_uid_exists_for_parameter_callback=(
                        lambda p_name, v_uid, _: (
                            self._repos.parameter_repository.is_parameter_term_uid_valid_for_parameter_name(
                                parameter_term_uid=v_uid,
                                parameter_name=p_name,
                            )
                        )
                    ),
                    parameter_name=allowed_parameter[
                        "name"
                    ],  # Item is used out of context of the for-loop
                    conjunction=parameter.conjunction,  # type: ignore[arg-type]
                    labels=parameter.labels or [],
                    parameters=uids,
                )
                parameter_terms.append(pve)
                idx += 1
            else:
                # Else, iterate over the provided values, store them and their type dynamically.
                for item in parameter.terms:
                    parameter_term_vo = SimpleParameterTermVO.from_input_values(
                        parameter_term_by_uid_lookup_callback=self._get_parameter_term,
                        uid=item.uid,
                    )
                    uids.append(parameter_term_vo)
                pve = ParameterTermEntryVO.from_input_values(
                    parameter_exists_callback=self._repos.parameter_repository.parameter_name_exists,
                    conjunction_exists_callback=lambda _: True,  # TODO: provide proper callback here
                    parameter_term_uid_exists_for_parameter_callback=(
                        lambda p_name, v_uid, _: (
                            self._repos.parameter_repository.is_parameter_term_uid_valid_for_parameter_name(
                                parameter_term_uid=v_uid,
                                parameter_name=p_name,
                            )
                        )
                    ),
                    # pylint: disable=undefined-loop-variable
                    parameter_name=item.type,  # type: ignore[arg-type]
                    conjunction=parameter.conjunction,  # type: ignore[arg-type]
                    labels=parameter.labels or [],
                    parameters=uids,
                )
                parameter_terms.append(pve)
                idx += 1
        return parameter_terms

    @db.transaction
    def get_referencing_studies(
        self,
        uid: str,
        node_type: NodeMeta,
        include_sections: list[StudyComponentEnum] | None = None,
        exclude_sections: list[StudyComponentEnum] | None = None,
    ) -> list[Study]:
        studies = self.study_repository.find_all_by_library_item_uid(
            uid=uid, library_item_type=node_type, sort_by={"uid": True}
        ).items

        study_service = StudyService()
        return_items = [
            study_service._models_study_from_study_definition_ar(
                study_definition_ar=item,
                find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                find_study_parent_part_by_uid=self._repos.study_definition_repository.find_by_uid,
                include_sections=include_sections,
                exclude_sections=exclude_sections,
            )
            for item in studies
        ]
        return return_items
