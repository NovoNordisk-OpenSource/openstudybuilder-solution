from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.odms.description_repository import (
    DescriptionRepository,
)
from clinical_mdr_api.domains.concepts.odms.description import (
    OdmDescriptionAR,
    OdmDescriptionVO,
)
from clinical_mdr_api.models.concepts.odms.odm_description import (
    OdmDescription,
    OdmDescriptionBatchInput,
    OdmDescriptionBatchOutput,
    OdmDescriptionPatchInput,
    OdmDescriptionPostInput,
    OdmDescriptionVersion,
)
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.services._utils import ensure_transaction
from clinical_mdr_api.services.concepts.odms.odm_generic_service import (
    OdmGenericService,
)
from common import exceptions


class OdmDescriptionService(OdmGenericService[OdmDescriptionAR]):
    aggregate_class = OdmDescriptionAR
    version_class = OdmDescriptionVersion
    repository_interface = DescriptionRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmDescriptionAR
    ) -> OdmDescription:
        return OdmDescription.from_odm_description_ar(odm_description_ar=item_ar)

    def _create_aggregate_root(
        self, concept_input: OdmDescriptionPostInput, library
    ) -> OdmDescriptionAR:
        return OdmDescriptionAR.from_input_values(
            author_id=self.author_id,
            concept_vo=OdmDescriptionVO.from_repository_values(
                name=concept_input.name,
                language=concept_input.language,
                description=concept_input.description,
                instruction=concept_input.instruction,
                sponsor_instruction=concept_input.sponsor_instruction,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
        )

    def _edit_aggregate(
        self, item: OdmDescriptionAR, concept_edit_input: OdmDescriptionPatchInput
    ) -> OdmDescriptionAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=OdmDescriptionVO.from_repository_values(
                name=concept_edit_input.name,
                language=concept_edit_input.language,
                description=concept_edit_input.description,
                instruction=concept_edit_input.instruction,
                sponsor_instruction=concept_edit_input.sponsor_instruction,
            ),
        )
        return item

    def soft_delete(self, uid: str) -> None:
        exceptions.NotFoundException.raise_if_not(
            self._repos.odm_description_repository.exists_by("uid", uid, True),
            "ODM Description",
            uid,
        )

        exceptions.BusinessLogicException.raise_if(
            self._repos.odm_description_repository.has_active_relationships(
                uid,
                [
                    "has_form",
                    "has_item_group",
                    "has_item",
                    "has_condition",
                    "has_method",
                ],
            ),
            msg="This ODM Description is in use.",
        )

        return super().soft_delete(uid)

    @ensure_transaction(db)
    def handle_batch_operations(
        self, operations: list[OdmDescriptionBatchInput]
    ) -> list[OdmDescriptionBatchOutput]:
        results = []
        for operation in operations:
            result = {}
            item = None

            try:
                if operation.method == "POST":
                    item = self.create(operation.content)
                    response_code = status.HTTP_201_CREATED
                elif operation.method == "PATCH":
                    item = self.edit_draft(operation.content.uid, operation.content)
                    response_code = status.HTTP_200_OK
                else:
                    raise exceptions.MethodNotAllowedException(method=operation.method)
                result["response_code"] = response_code
                if item:
                    result["content"] = item.model_dump()
                results.append(OdmDescriptionBatchOutput(**result))
            except exceptions.MDRApiBaseException as error:
                results.append(
                    OdmDescriptionBatchOutput.model_construct(
                        response_code=error.status_code,
                        content=BatchErrorResponse(message=str(error)),
                    )
                )
        return results

    @db.transaction
    def get_active_relationships(self, uid: str):
        exceptions.NotFoundException.raise_if_not(
            self._repos.odm_description_repository.exists_by("uid", uid, True),
            "ODM Description",
            uid,
        )

        return self._repos.odm_description_repository.get_active_relationships(
            uid,
            ["has_form", "has_item_group", "has_item", "has_condition", "has_method"],
        )
