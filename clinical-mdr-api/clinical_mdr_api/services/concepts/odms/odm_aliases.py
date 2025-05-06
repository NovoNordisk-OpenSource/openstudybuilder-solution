from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.odms.alias_repository import (
    AliasRepository,
)
from clinical_mdr_api.domains.concepts.odms.alias import OdmAliasAR, OdmAliasVO
from clinical_mdr_api.models.concepts.odms.odm_alias import (
    OdmAlias,
    OdmAliasBatchInput,
    OdmAliasBatchOutput,
    OdmAliasPatchInput,
    OdmAliasPostInput,
    OdmAliasVersion,
)
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.services._utils import ensure_transaction
from clinical_mdr_api.services.concepts.odms.odm_generic_service import (
    OdmGenericService,
)
from common import exceptions


class OdmAliasService(OdmGenericService[OdmAliasAR]):
    aggregate_class = OdmAliasAR
    version_class = OdmAliasVersion
    repository_interface = AliasRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmAliasAR
    ) -> OdmAlias:
        return OdmAlias.from_odm_alias_ar(odm_alias_ar=item_ar)

    def _create_aggregate_root(
        self, concept_input: OdmAliasPostInput, library
    ) -> OdmAliasAR:
        return OdmAliasAR.from_input_values(
            author_id=self.author_id,
            concept_vo=OdmAliasVO.from_repository_values(
                name=concept_input.name,
                context=concept_input.context,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            odm_object_exists_callback=self._repos.odm_alias_repository.odm_object_exists,
        )

    def _edit_aggregate(
        self, item: OdmAliasAR, concept_edit_input: OdmAliasPatchInput
    ) -> OdmAliasAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=OdmAliasVO.from_repository_values(
                name=concept_edit_input.name,
                context=concept_edit_input.context,
            ),
            odm_object_exists_callback=self._repos.odm_alias_repository.odm_object_exists,
        )
        return item

    def soft_delete(self, uid: str) -> None:
        exceptions.NotFoundException.raise_if_not(
            self._repos.odm_alias_repository.exists_by("uid", uid, True),
            "ODM Alias",
            uid,
        )

        exceptions.BusinessLogicException.raise_if(
            self._repos.odm_alias_repository.has_active_relationships(
                uid,
                [
                    "has_form",
                    "has_item_group",
                    "has_item",
                    "has_condition",
                    "has_method",
                ],
            ),
            msg="This ODM Alias is in use.",
        )

        return super().soft_delete(uid)

    @ensure_transaction(db)
    def handle_batch_operations(
        self, operations: list[OdmAliasBatchInput]
    ) -> list[OdmAliasBatchOutput]:
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
                results.append(OdmAliasBatchOutput(**result))
            except exceptions.MDRApiBaseException as error:
                results.append(
                    OdmAliasBatchOutput.model_construct(
                        response_code=error.status_code,
                        content=BatchErrorResponse(message=str(error)),
                    )
                )
        return results

    @db.transaction
    def get_active_relationships(self, uid: str):
        exceptions.NotFoundException.raise_if_not(
            self._repos.odm_alias_repository.exists_by("uid", uid, True),
            "ODM Alias",
            uid,
        )

        return self._repos.odm_alias_repository.get_active_relationships(
            uid,
            ["has_form", "has_item_group", "has_item", "has_condition", "has_method"],
        )
