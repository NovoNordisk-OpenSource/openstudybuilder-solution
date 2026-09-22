from dataclasses import dataclass
from typing import Callable, Self

from deepdiff import DeepDiff

from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domains.controlled_terminologies.utils import CtTermInfo
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.exceptions import BusinessLogicException


@dataclass(frozen=True)
class MedicinalProductVO(ConceptVO):
    """
    The MedicinalProductVO acts as the single value object for MedicinalProductAR aggregate.
    """

    class CompoundInfo:
        def __init__(self, uid: str, name: str | None):
            self.uid = uid
            self.name = name

    class PharmaceuticalProductInfo:
        def __init__(self, uid: str, external_id: str | None):
            self.uid = uid
            self.external_id = external_id

    class DoseValueInfo:
        def __init__(
            self, uid: str, value: float, unit_definition_uid: str, unit_label: str
        ):
            self.uid = uid
            self.value = value
            self.unit_definition_uid = unit_definition_uid
            self.unit_label = unit_label

    compound_uid: str
    external_id: str | None
    pharmaceutical_product_uids: list[str] | None = None
    pharmaceutical_products: list[PharmaceuticalProductInfo] | None = None
    delivery_device_uid: str | None = None
    delivery_device: CtTermInfo | None = None
    dispenser_uid: str | None = None
    dispenser: CtTermInfo | None = None
    dose_value_uids: list[str] | None = None
    dose_values: list[DoseValueInfo] | None = None
    dose_frequency_uids: list[str] | None = None
    dose_frequencies: list[CtTermInfo] | None = None
    compound: CompoundInfo | None = None

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: str | None,
        external_id: str | None,
        compound_uid: str,
        pharmaceutical_product_uids: list[str] | None,
        delivery_device_uid: str | None,
        dispenser_uid: str | None,
        dose_value_uids: list[str] | None,
        dose_frequency_uids: list[str] | None,
        pharmaceutical_products: list[PharmaceuticalProductInfo] | None = None,
        delivery_device: CtTermInfo | None = None,
        dispenser: CtTermInfo | None = None,
        dose_values: list[DoseValueInfo] | None = None,
        dose_frequencies: list[CtTermInfo] | None = None,
        compound: CompoundInfo | None = None,
    ) -> Self:
        if not dose_frequency_uids:
            dose_frequency_uids = []
        if not pharmaceutical_products:
            pharmaceutical_products = []
        if not dose_values:
            dose_values = []
        if not dose_frequencies:
            dose_frequencies = []

        medicinal_product_vo = cls(
            external_id=external_id,
            compound_uid=compound_uid,
            pharmaceutical_product_uids=pharmaceutical_product_uids,
            delivery_device_uid=delivery_device_uid,
            dispenser_uid=dispenser_uid,
            dose_value_uids=dose_value_uids,
            dose_frequency_uids=dose_frequency_uids,
            name=name,
            name_sentence_case=name_sentence_case,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
            pharmaceutical_products=pharmaceutical_products,
            delivery_device=delivery_device,
            dispenser=dispenser,
            dose_values=dose_values,
            dose_frequencies=dose_frequencies,
            compound=compound,
        )

        return medicinal_product_vo

    def validate(
        self,
        uid: str,
        medicinal_product_uid_by_property_value_callback: Callable[
            [str, str], str | None
        ],
        ct_term_exists_callback: Callable[[str], bool],
        numeric_value_exists_callback: Callable[[str], bool],
        compound_exists_callback: Callable[[str], bool],
        pharmaceutical_product_exists_callback: Callable[[str], bool],
    ):
        if self.external_id is not None:
            self.validate_uniqueness(
                lookup_callback=medicinal_product_uid_by_property_value_callback,
                uid=uid,
                property_name="external_id",
                value=self.external_id,
                error_message=f"MedicinalProduct with external_id '{self.external_id}' already exists.",
            )
        BusinessLogicException.raise_if_not(
            compound_exists_callback(self.compound_uid),
            msg=f"{type(self).__name__} tried to connect to non-existent Compound with UID '{self.compound_uid}'.",
        )
        for p_uid in self.pharmaceutical_product_uids:
            BusinessLogicException.raise_if_not(
                pharmaceutical_product_exists_callback(p_uid),
                msg=f"{type(self).__name__} tried to connect to non-existent Pharmaceutical Product with UID '{p_uid}'.",
            )

        BusinessLogicException.raise_if(
            self.delivery_device_uid
            and not ct_term_exists_callback(self.delivery_device_uid),
            msg=f"{type(self).__name__} tried to connect to non-existent Delivery Device with UID '{self.delivery_device_uid}'.",
        )

        BusinessLogicException.raise_if(
            self.dispenser_uid and not ct_term_exists_callback(self.dispenser_uid),
            msg=f"{type(self).__name__} tried to connect to non-existent Dispenser with UID '{self.dispenser_uid}'.",
        )
        for dose_value_uid in self.dose_value_uids:
            BusinessLogicException.raise_if_not(
                numeric_value_exists_callback(dose_value_uid),
                msg=f"{type(self).__name__} tried to connect to non-existent Dose Value with UID '{dose_value_uid}'.",
            )
        for dose_frequency_uid in self.dose_frequency_uids:
            BusinessLogicException.raise_if_not(
                ct_term_exists_callback(dose_frequency_uid),
                msg=f"{type(self).__name__} tried to connect to non-existent Dose Frequency with UID '{dose_frequency_uid}'.",
            )


class MedicinalProductAR(ConceptARBase):
    _external_id: str | None
    _concept_vo: MedicinalProductVO

    @property
    def concept_vo(self) -> MedicinalProductVO:
        return self._concept_vo

    @concept_vo.setter
    def concept_vo(self, value: MedicinalProductVO) -> None:
        self._concept_vo = value

    @property
    def name(self) -> str:
        return self.concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author_id: str,
        concept_vo: MedicinalProductVO,
        library: LibraryVO,
        medicinal_product_uid_by_property_value_callback: Callable[
            [str, str], str | None
        ],
        ct_term_exists_callback: Callable[[str], bool],
        numeric_value_exists_callback: Callable[[str], bool],
        compound_exists_callback: Callable[[str], bool],
        pharmaceutical_product_exists_callback: Callable[[str], bool],
        generate_uid_callback: Callable[[], str],
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )
        uid = generate_uid_callback()

        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )

        concept_vo.validate(
            uid=uid,
            medicinal_product_uid_by_property_value_callback=medicinal_product_uid_by_property_value_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            numeric_value_exists_callback=numeric_value_exists_callback,
            compound_exists_callback=compound_exists_callback,
            pharmaceutical_product_exists_callback=pharmaceutical_product_exists_callback,
        )

        medicinal_product_ar = cls(
            _uid=uid,
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return medicinal_product_ar

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        concept_vo: MedicinalProductVO,
        concept_exists_by_callback: Callable[
            [str, str], str | None
        ] = lambda x, y: None,
        ct_term_exists_callback: Callable[[str], bool] = lambda _: False,
        numeric_value_exists_callback: Callable[[str], bool] = lambda _: False,
        compound_exists_callback: Callable[[str], bool] = lambda _: False,
        pharmaceutical_product_exists_callback: Callable[[str], bool] = lambda _: False,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            self.uid,
            medicinal_product_uid_by_property_value_callback=concept_exists_by_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            numeric_value_exists_callback=numeric_value_exists_callback,
            compound_exists_callback=compound_exists_callback,
            pharmaceutical_product_exists_callback=pharmaceutical_product_exists_callback,
        )

        exclude_paths = [
            "root.dose_values",
            "root.pharmaceutical_products",
            "root.delivery_device",
            "root.dispenser",
            "root.dose_frequencies",
            "root.compound",
        ]

        if DeepDiff(
            self._concept_vo, concept_vo, ignore_order=True, exclude_paths=exclude_paths
        ):
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._concept_vo = concept_vo
