from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Self

from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.odms.ar_base import OdmARBase
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmTranslatedTextModel,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from common.exceptions import AlreadyExistsException, BusinessLogicException
from common.utils import booltostr

if TYPE_CHECKING:
    from clinical_mdr_api.models.odms.item import OdmItemCodelist, OdmItemParentGroup


@dataclass(frozen=True)
class CTTermItem:
    uid: str
    name: str | None = None
    version: str | None = None
    codelist_uid: str | None = None
    submission_value: str | None = None


@dataclass(frozen=True)
class OdmItemVO:
    name: str | None
    oid: str | None
    prompt: str | None
    datatype: CTTermItem | None
    length: int | None
    significant_digits: int | None
    sas_field_name: str | None
    sds_var_name: str | None
    origin: str | None
    comment: str | None
    odm_item_group: "OdmItemParentGroup | None"
    translated_texts: list[OdmTranslatedTextModel]
    aliases: list[OdmAliasModel]
    unit_definition_uids: list[str]
    external_question: CTTermItem | None
    codelist: "OdmItemCodelist | None"
    term_uids: list[str]
    vendor_attribute_uids: list[str]
    vendor_element_uids: list[str]
    vendor_element_attribute_uids: list[str]
    activity_instances: list[dict[str, Any]]

    @classmethod
    def from_repository_values(
        cls,
        oid: str | None,
        name: str,
        prompt: str | None,
        datatype: CTTermItem | None,
        length: int | None,
        significant_digits: int | None,
        sas_field_name: str | None,
        sds_var_name: str | None,
        origin: str | None,
        comment: str | None,
        odm_item_group: "OdmItemParentGroup | None",
        translated_texts: list[OdmTranslatedTextModel],
        aliases: list[OdmAliasModel],
        unit_definition_uids: list[str],
        external_question: CTTermItem | None,
        codelist: "OdmItemCodelist | None",
        term_uids: list[str],
        vendor_element_uids: list[str],
        vendor_attribute_uids: list[str],
        vendor_element_attribute_uids: list[str],
        activity_instances: list[dict[str, Any]],
    ) -> Self:
        return cls(
            oid=oid,
            name=name,
            prompt=prompt,
            datatype=datatype,
            length=length,
            significant_digits=significant_digits,
            sas_field_name=sas_field_name,
            sds_var_name=sds_var_name,
            origin=origin,
            comment=comment,
            odm_item_group=odm_item_group,
            translated_texts=translated_texts,
            aliases=aliases,
            unit_definition_uids=unit_definition_uids,
            external_question=external_question,
            codelist=codelist,
            term_uids=term_uids,
            vendor_element_uids=vendor_element_uids,
            vendor_attribute_uids=vendor_attribute_uids,
            vendor_element_attribute_uids=vendor_element_attribute_uids,
            activity_instances=activity_instances,
        )

    def validate(
        self,
        odm_object_exists_callback: Callable,
        unit_definition_exists_by_callback: Callable[[str, str, bool], bool],
        find_codelist_attribute_callback: Callable[
            [str], CTCodelistAttributesAR | None
        ],
        find_all_terms_callback: Callable[
            [str], GenericFilteringReturn[CTTermNameAR] | None
        ],
        term_exists_by_uid_callback: Callable[[str], bool] = lambda _: True,
        find_activity_instance_callback: Callable[[str], Any] = lambda _: None,
        odm_uid: str | None = None,
        library_name: str | None = None,
    ) -> None:
        if uids := odm_object_exists_callback(library_name=library_name, oid=self.oid):

            if uids[0] != odm_uid:
                raise AlreadyExistsException(
                    msg=f"ODM Item with OID '{self.oid}' already exists in library '{library_name}' with UID ({uids[0]})"
                )

        if self.external_question is not None:
            BusinessLogicException.raise_if_not(
                term_exists_by_uid_callback(self.external_question.uid),
                msg=f"ODM Item tried to connect to non-existent or non-final CT Term with UID '{self.external_question.uid}'.",
            )

        if self.datatype is not None:
            BusinessLogicException.raise_if_not(
                term_exists_by_uid_callback(self.datatype.uid),
                msg=f"ODM Item tried to connect to non-existent or non-final CT Term with UID '{self.datatype.uid}'.",
            )

            # Validate length and significant_digits based on datatype submission_value
            if self.datatype.submission_value:
                datatype_submval = self.datatype.submission_value.casefold()

                if self.length is not None and datatype_submval not in [
                    "text",
                    "string",
                    "integer",
                    "float",
                ]:
                    raise BusinessLogicException(
                        msg="When datatype is not 'text', 'string', 'integer' or 'float', length must be null."
                    )
                if self.length is None and datatype_submval in ["text", "string"]:
                    raise BusinessLogicException(
                        msg="When datatype is 'text' or 'string', length must be provided."
                    )

                if datatype_submval == "float" and (
                    bool(self.length is not None)
                    ^ bool(self.significant_digits is not None)
                ):
                    raise BusinessLogicException(
                        msg="When datatype is 'float', both length and significant_digits must be provided together, or both must be null."
                    )

        for unit_definition_uid in self.unit_definition_uids:
            if not unit_definition_exists_by_callback("uid", unit_definition_uid, True):
                raise BusinessLogicException(
                    msg=f"ODM Item tried to connect to non-existent Unit Definition with UID '{unit_definition_uid}'.",
                )

        if self.codelist is not None and not find_codelist_attribute_callback(
            self.codelist.uid
        ):
            raise BusinessLogicException(
                msg=f"ODM Item tried to connect to non-existent Codelist with UID '{self.codelist.uid}'.",
            )

        if self.term_uids:
            if self.codelist is None:
                raise BusinessLogicException(
                    msg="To add terms you need to specify a codelist."
                )

            codelist_term_uids = [
                term.uid for term in find_all_terms_callback(self.codelist.uid).items
            ]
            for term_uid in self.term_uids:
                BusinessLogicException.raise_if(
                    term_uid not in codelist_term_uids,
                    msg=f"Term with UID '{term_uid}' doesn't belong to the specified Codelist with UID '{self.codelist.uid}'.",
                )

        if self.activity_instances:
            for activity_instance in self.activity_instances:
                db_activity_instance = find_activity_instance_callback(
                    activity_instance["activity_instance_uid"]
                )

                if not db_activity_instance:
                    raise BusinessLogicException(
                        msg=f"ODM Item tried to connect to non-existent Activity Instance with UID '{activity_instance["activity_instance_uid"]}'."
                    )

                if activity_instance["activity_item_class_uid"] not in [
                    activity_item.activity_item_class_uid
                    for activity_item in db_activity_instance.concept_vo.activity_instance_attributes.activity_items
                ]:
                    raise BusinessLogicException(
                        msg=(
                            f"Activity Item Class with UID '{activity_instance["activity_item_class_uid"]}' isn't present in Activity Instance with UID '{activity_instance["activity_instance_uid"]}'"
                        )
                    )


@dataclass
class OdmItemAR(OdmARBase):
    _odm_vo: OdmItemVO

    @property
    def name(self) -> str:
        return self._odm_vo.name

    @property
    def odm_vo(self) -> OdmItemVO:
        return self._odm_vo

    @odm_vo.setter
    def odm_vo(self, value: OdmItemVO) -> None:
        self._odm_vo = value

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        odm_vo: OdmItemVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        return cls(
            _uid=uid,
            _odm_vo=odm_vo,
            _library=library,
            _item_metadata=item_metadata,
        )

    @classmethod
    def from_input_values(
        cls,
        author_id: str,
        odm_vo: OdmItemVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str] = lambda: "",
        odm_object_exists_callback: Callable = lambda _: True,
        unit_definition_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        find_codelist_attribute_callback: Callable[
            [str], CTCodelistAttributesAR | None
        ] = lambda _: None,
        find_all_terms_callback: Callable[
            [str], GenericFilteringReturn[CTTermNameAR] | None
        ] = lambda _: None,
        term_exists_by_uid_callback: Callable[[str], bool] = lambda _: True,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        odm_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback,
            unit_definition_exists_by_callback=unit_definition_exists_by_callback,
            find_codelist_attribute_callback=find_codelist_attribute_callback,
            find_all_terms_callback=find_all_terms_callback,
            term_exists_by_uid_callback=term_exists_by_uid_callback,
            library_name=library.name,
        )

        return cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _odm_vo=odm_vo,
        )

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        odm_vo: OdmItemVO,
        odm_object_exists_callback: Callable = lambda _: True,
        unit_definition_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        find_codelist_attribute_callback: Callable[
            ..., CTCodelistAttributesAR | None
        ] = lambda _: None,
        find_all_terms_callback: Callable[
            [str], GenericFilteringReturn[CTTermNameAR] | None
        ] = lambda _: None,
        term_exists_by_uid_callback: Callable[[str], bool] = lambda _: True,
        find_activity_instance_callback: Callable[[str], Any] = lambda _: None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        odm_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback,
            unit_definition_exists_by_callback=unit_definition_exists_by_callback,
            find_codelist_attribute_callback=find_codelist_attribute_callback,
            find_all_terms_callback=find_all_terms_callback,
            term_exists_by_uid_callback=term_exists_by_uid_callback,
            find_activity_instance_callback=find_activity_instance_callback,
            odm_uid=self.uid,
            library_name=self._library.name,
        )

        if self._odm_vo != odm_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._odm_vo = odm_vo


@dataclass(frozen=True)
class OdmItemRefVO:
    uid: str
    oid: str
    name: str
    version: str
    item_group_uid: str
    order_number: int
    mandatory: str
    key_sequence: str
    method_oid: str
    imputation_method_oid: str
    role: str
    role_codelist_oid: str
    collection_exception_condition_oid: str | None
    vendor: dict[Any, Any]

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        oid: str,
        name: str,
        version: str,
        item_group_uid: str,
        order_number: int,
        mandatory: bool,
        key_sequence: str,
        method_oid: str,
        imputation_method_oid: str,
        role: str,
        role_codelist_oid: str,
        vendor: dict[Any, Any],
        collection_exception_condition_oid: str | None = None,
    ) -> Self:
        return cls(
            uid=uid,
            oid=oid,
            name=name,
            version=version,
            item_group_uid=item_group_uid,
            order_number=order_number,
            mandatory=booltostr(mandatory),
            key_sequence=key_sequence,
            method_oid=method_oid,
            imputation_method_oid=imputation_method_oid,
            role=role,
            role_codelist_oid=role_codelist_oid,
            collection_exception_condition_oid=collection_exception_condition_oid,
            vendor=vendor,
        )


@dataclass(frozen=True)
class OdmItemTermVO:
    uid: str
    name: str
    mandatory: bool
    order: int
    display_text: str
    version: str
    submission_value: str

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        name: str,
        mandatory: bool,
        order: int,
        display_text: str,
        version: str,
        submission_value: str,
    ) -> Self:
        return cls(
            uid=uid,
            name=name,
            mandatory=mandatory,
            order=order,
            display_text=display_text,
            version=version,
            submission_value=submission_value,
        )


@dataclass(frozen=True)
class OdmItemUnitDefinitionVO:
    uid: str
    name: str
    mandatory: bool
    order: int

    @classmethod
    def from_repository_values(
        cls, uid: str, name: str, mandatory: bool, order: int
    ) -> Self:
        return cls(uid=uid, name=name, mandatory=mandatory, order=order)
