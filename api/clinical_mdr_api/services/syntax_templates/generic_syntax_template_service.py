import abc
from typing import TypeVar

from neomodel import db
from neomodel.exceptions import DoesNotExist
from pydantic import BaseModel

from clinical_mdr_api.domain_repositories.syntax_instances.generic_syntax_instance_repository import (
    GenericSyntaxInstanceRepository,
)
from clinical_mdr_api.domains.syntax_templates.template import (
    TemplateAggregateRootBase,
    TemplateVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.repositories._utils import ComparisonOperator
from clinical_mdr_api.services._utils import (
    fill_missing_values_in_base_model_from_reference_base_model,
    is_library_editable,
    process_parameters,
)
from clinical_mdr_api.services.generic_syntax_service import GenericSyntaxService
from common.exceptions import AlreadyExistsException, NotFoundException

_AggregateRootType = TypeVar("_AggregateRootType")


class GenericSyntaxTemplateService(GenericSyntaxService[_AggregateRootType], abc.ABC):
    instance_repository_interface: type
    pre_instance_repository_interface: type | None

    @property
    def instance_repository(self) -> GenericSyntaxInstanceRepository:
        return self.instance_repository_interface()

    @property
    def pre_instance_repository(self) -> GenericSyntaxInstanceRepository | None:
        if self.pre_instance_repository_interface:
            return self.pre_instance_repository_interface()
        return None

    def _create_ar_from_input_values(self, template: BaseModel) -> _AggregateRootType:
        template_vo, library_vo = self._create_template_vo(template)

        # Process item to save
        item = TemplateAggregateRootBase.from_input_values(
            author_id=self.author_id,
            template=template_vo,
            library=library_vo,
            generate_uid_callback=self.repository.generate_uid_callback,
            next_available_sequence_id_callback=self.repository.next_available_sequence_id,
        )

        return item

    def create(self, template: BaseModel) -> BaseModel:
        # This function is not decorated with db.transaction as internal transactions
        # are handled manually by "with" statement.
        self.authorize_user_defined_syntax_write(template.library_name)

        try:
            # Transaction that is performing initial save
            with db.transaction:
                filter_by = {
                    "name": {
                        "v": [template.name],
                        "op": ComparisonOperator.EQUALS.value,
                    },
                    "library.name": {
                        "v": [template.library_name],
                        "op": ComparisonOperator.EQUALS.value,
                    },
                }
                if type_uid := getattr(template, "type_uid", None):
                    filter_by |= {"type.term_uid": {"v": [type_uid]}}

                if existing_template := self.repository.get_all(filter_by=filter_by)[0]:
                    if existing_template[0].library.name == "User Defined":
                        return self._transform_aggregate_root_to_pydantic_model(
                            existing_template[0]
                        )

                    raise AlreadyExistsException(
                        field_value=template.name, field_name="Name"
                    )

                item = self._create_ar_from_input_values(template)

                # Save item
                self.repository.save(item)

            return self._transform_aggregate_root_to_pydantic_model(item)
        except DoesNotExist as exc:
            raise NotFoundException("Library", template.library_name, "Name") from exc

    def _create_template_vo(self, template: BaseModel) -> tuple[TemplateVO, LibraryVO]:
        # Create TemplateVO
        template_vo = TemplateVO.from_input_values_2(
            template_name=template.name,
            guidance_text=getattr(template, "guidance_text", None),
            parameter_name_exists_callback=self._parameter_name_exists,
        )

        # Fetch library
        library_vo = LibraryVO.from_input_values_2(
            library_name=template.library_name,
            is_library_editable_callback=is_library_editable,
        )

        return template_vo, library_vo

    @db.transaction
    def create_new_version(self, uid: str, template: BaseModel) -> BaseModel:
        item = self.repository.find_by_uid(uid=uid, for_update=True)

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=template,
            reference_base_model=self._transform_aggregate_root_to_pydantic_model(item),
        )

        template_vo = TemplateVO.from_input_values_2(
            template_name=template.name,
            guidance_text=getattr(template, "guidance_text", None),
            parameter_name_exists_callback=self._parameter_name_exists,
        )

        item.create_new_version(
            author_id=self.author_id,
            change_description=template.change_description,
            template=template_vo,
        )
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def approve_cascade(self, uid: str) -> BaseModel:
        item = self.repository.find_by_uid(uid, for_update=True)

        self.authorize_user_defined_syntax_write(item.library.name)

        item.approve(author_id=self.author_id)
        self.repository.save(item)

        related_instance_uids = (
            self.instance_repository.find_instance_uids_by_template_uid(uid)
        )
        for related_instance_uid in related_instance_uids:
            related_instance = self.instance_repository.find_by_uid(
                related_instance_uid, for_update=True
            )
            if related_instance:
                related_instance.cascade_update(
                    author_id=self.author_id,
                    date=item.item_metadata.start_date,
                    new_template_name=item.name,
                )
                self.instance_repository.save(related_instance)

        if self.pre_instance_repository:
            related_pre_instance_uids = (
                self.pre_instance_repository.find_pre_instance_uids_by_template_uid(uid)
            )
            for related_pre_instance_uid in related_pre_instance_uids:
                related_pre_instance = self.pre_instance_repository.find_by_uid(
                    related_pre_instance_uid, for_update=True
                )
                if related_pre_instance:
                    related_pre_instance.cascade_update(
                        author_id=self.author_id,
                        date=item.item_metadata.start_date,
                        new_template_name=item.name,
                    )
                    self.pre_instance_repository.save(related_pre_instance)

        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def inactivate_final(self, uid: str) -> BaseModel:
        item = self.repository.find_by_uid(uid, for_update=True)

        item.inactivate(author_id=self.author_id)

        if self.pre_instance_repository:
            related_pre_instance_uids = (
                self.pre_instance_repository.find_pre_instance_uids_by_template_uid(uid)
            )
            for related_pre_instance_uid in related_pre_instance_uids:
                related_pre_instance = self.pre_instance_repository.find_by_uid(
                    related_pre_instance_uid, for_update=True
                )
                if (
                    related_pre_instance
                    and related_pre_instance._item_metadata.status
                    == LibraryItemStatus.DRAFT
                ):
                    related_pre_instance.approve(author_id=self.author_id)
                    self.pre_instance_repository.save(related_pre_instance)

                if (
                    related_pre_instance
                    and related_pre_instance._item_metadata.status
                    == LibraryItemStatus.FINAL
                ):
                    related_pre_instance.inactivate(author_id=self.author_id)
                    self.pre_instance_repository.save(related_pre_instance)

        self.repository.save(item)

        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def reactivate_retired(self, uid: str) -> BaseModel:
        item = self.repository.find_by_uid(uid, for_update=True)

        item.reactivate(author_id=self.author_id)
        self.repository.save(item)

        if self.pre_instance_repository:
            related_pre_instance_uids = (
                self.pre_instance_repository.find_pre_instance_uids_by_template_uid(uid)
            )
            for related_pre_instance_uid in related_pre_instance_uids:
                related_pre_instance = self.pre_instance_repository.find_by_uid(
                    related_pre_instance_uid, for_update=True
                )
                if (
                    related_pre_instance
                    and related_pre_instance._item_metadata.status
                    == LibraryItemStatus.RETIRED
                ):
                    related_pre_instance.reactivate(author_id=self.author_id)
                    self.pre_instance_repository.save(related_pre_instance)

        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def edit_draft(self, uid: str, template: BaseModel) -> BaseModel:
        template_vo = TemplateVO.from_input_values_2(
            template_name=template.name,
            parameter_name_exists_callback=self._parameter_name_exists,
        )

        item = self.repository.find_by_uid(
            uid, for_update=True, return_study_count=True
        )

        self.authorize_user_defined_syntax_write(item.library.name)

        if (
            self.repository.check_exists_by_name_in_library(
                name=template.name, library=item.library.name
            )
            and template.name != item.name
        ):
            raise AlreadyExistsException(field_value=template.name, field_name="Name")

        item.edit_draft(
            author_id=self.author_id,
            change_description=template.change_description,
            template=template_vo,
        )
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def get_parameters(
        self,
        uid: str,
        study_uid: str | None = None,
        include_study_endpoints: bool = False,
    ):
        try:
            parameters = self.repository.get_parameters_including_terms(
                template_uid=uid,
                study_uid=study_uid,
                include_study_endpoints=include_study_endpoints,
            )
            return process_parameters(parameters)
        except DoesNotExist as exc:
            raise NotFoundException(field_value=uid) from exc

    @db.transaction
    def validate_template_syntax(self, template_name_to_validate: str) -> None:
        TemplateVO.from_input_values_2(
            template_name=template_name_to_validate,
            parameter_name_exists_callback=self._parameter_name_exists,
        )
