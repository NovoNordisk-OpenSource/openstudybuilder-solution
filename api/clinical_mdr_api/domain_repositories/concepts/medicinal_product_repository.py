from typing import Any

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.models.compounds import CompoundRoot
from clinical_mdr_api.domain_repositories.models.concepts import (
    NumericValueWithUnitRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.medicinal_product import (
    MedicinalProductRoot,
    MedicinalProductValue,
)
from clinical_mdr_api.domain_repositories.models.pharmaceutical_product import (
    PharmaceuticalProductRoot,
)
from clinical_mdr_api.domains.concepts.concept_base import _AggregateRootType
from clinical_mdr_api.domains.concepts.medicinal_product import (
    MedicinalProductAR,
    MedicinalProductVO,
)
from clinical_mdr_api.domains.controlled_terminologies.utils import CtTermInfo
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.medicinal_product import MedicinalProduct
from common.config import settings
from common.utils import convert_to_datetime


class MedicinalProductRepository(ConceptGenericRepository):
    root_class = MedicinalProductRoot
    value_class = MedicinalProductValue
    return_model = MedicinalProduct

    def _create_new_value_node(self, ar: _AggregateRootType) -> VersionValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.save()

        for uid in ar.concept_vo.dose_value_uids:
            value_node.has_dose_value.connect(
                NumericValueWithUnitRoot.nodes.get(uid=uid)
            )

        for uid in ar.concept_vo.dose_frequency_uids:
            dose_frequency_node = CTTermRoot.nodes.get(uid=uid)
            selected_term_node = (
                CTCodelistAttributesRepository().get_or_create_selected_term(
                    dose_frequency_node,
                    codelist_submission_value=settings.dose_frequency_cl_submval,
                    catalogue_name=settings.sdtm_ct_catalogue_name,
                )
            )
            value_node.has_dose_frequency.connect(selected_term_node)

        if ar.concept_vo.delivery_device_uid is not None:
            delivery_device_node = CTTermRoot.nodes.get(
                uid=ar.concept_vo.delivery_device_uid
            )
            selected_term_node = (
                CTCodelistAttributesRepository().get_or_create_selected_term(
                    delivery_device_node,
                    codelist_submission_value=settings.delivery_device_cl_submval,
                    catalogue_name=settings.sdtm_ct_catalogue_name,
                )
            )
            value_node.has_delivery_device.connect(selected_term_node)

        if ar.concept_vo.dispenser_uid is not None:
            dispenser_node = CTTermRoot.nodes.get(uid=ar.concept_vo.dispenser_uid)
            selected_term_node = (
                CTCodelistAttributesRepository().get_or_create_selected_term(
                    dispenser_node,
                    codelist_submission_value=settings.compound_dispensed_in_cl_submval,
                    catalogue_name=settings.sdtm_ct_catalogue_name,
                )
            )
            value_node.has_dispenser.connect(selected_term_node)

        for uid in ar.concept_vo.pharmaceutical_product_uids:
            value_node.has_pharmaceutical_product.connect(
                PharmaceuticalProductRoot.nodes.get(uid=uid)
            )

        value_node.is_compound.connect(
            CompoundRoot.nodes.get(uid=ar.concept_vo.compound_uid)
        )

        return value_node

    def _has_data_changed(self, ar: _AggregateRootType, value: VersionValue) -> bool:
        was_parent_data_modified = super()._has_data_changed(ar=ar, value=value)

        old_dose_freq_nodes = [
            node.has_selected_term.get() for node in value.has_dose_frequency.all()
        ]

        old_delivery_device = value.has_delivery_device.get_or_none()
        if old_delivery_device is not None:
            old_delivery_device = old_delivery_device.has_selected_term.get_or_none()
        old_delivery_device_uid = (
            old_delivery_device.uid if old_delivery_device else None
        )

        old_dispenser = value.has_dispenser.get_or_none()
        if old_dispenser is not None:
            old_dispenser = old_dispenser.has_selected_term.get_or_none()
        old_dispenser_uid = old_dispenser.uid if old_dispenser else None

        are_rels_changed = (
            sorted(ar.concept_vo.dose_value_uids)
            != sorted([val.uid for val in value.has_dose_value.all()])
            or sorted(ar.concept_vo.dose_frequency_uids)
            != sorted([val.uid for val in old_dose_freq_nodes])
            or (ar.concept_vo.delivery_device_uid != old_delivery_device_uid)
            or (ar.concept_vo.dispenser_uid != old_dispenser_uid)
            or sorted(ar.concept_vo.pharmaceutical_product_uids)
            != sorted([val.uid for val in value.has_pharmaceutical_product.all()])
            or (ar.concept_vo.compound_uid != value.is_compound.get().uid)
        )

        return was_parent_data_modified or are_rels_changed

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> MedicinalProductAR:
        major, minor = input_dict["version"].split(".")
        ar = MedicinalProductAR.from_repository_values(
            uid=input_dict["uid"],
            concept_vo=MedicinalProductVO.from_repository_values(
                external_id=input_dict.get("external_id"),
                name=input_dict["name"],
                name_sentence_case=input_dict.get("name_sentence_case"),
                dose_value_uids=[
                    dose_value.get("uid")
                    for dose_value in input_dict.get("dose_values")
                ],
                dose_frequency_uids=[
                    dose_frequency.get("uid")
                    for dose_frequency in input_dict.get("dose_frequencies")
                ],
                delivery_device_uid=(
                    input_dict.get("delivery_device").get("uid")
                    if input_dict.get("delivery_device")
                    else None
                ),
                dispenser_uid=(
                    input_dict.get("dispenser").get("uid")
                    if input_dict.get("dispenser")
                    else None
                ),
                pharmaceutical_product_uids=[
                    pharmaceutical_product.get("uid")
                    for pharmaceutical_product in input_dict.get(
                        "pharmaceutical_products"
                    )
                ],
                compound_uid=input_dict.get("compound").get("uid"),
                pharmaceutical_products=[
                    MedicinalProductVO.PharmaceuticalProductInfo(
                        uid=pharmaceutical_product.get("uid"),
                        external_id=pharmaceutical_product.get("external_id"),
                    )
                    for pharmaceutical_product in input_dict.get(
                        "pharmaceutical_products"
                    )
                ],
                delivery_device=(
                    CtTermInfo(
                        term_uid=input_dict.get("delivery_device").get("uid"),
                        name=input_dict.get("delivery_device").get("name"),
                    )
                    if input_dict.get("delivery_device")
                    else None
                ),
                dispenser=(
                    CtTermInfo(
                        term_uid=input_dict.get("dispenser").get("uid"),
                        name=input_dict.get("dispenser").get("name"),
                    )
                    if input_dict.get("dispenser")
                    else None
                ),
                dose_values=[
                    MedicinalProductVO.DoseValueInfo(
                        uid=dose_value.get("uid"),
                        value=dose_value.get("value"),
                        unit_definition_uid=dose_value.get("unit_definition_uid"),
                        unit_label=dose_value.get("unit_label"),
                    )
                    for dose_value in input_dict.get("dose_values")
                ],
                dose_frequencies=[
                    CtTermInfo(
                        term_uid=dose_frequency.get("uid"),
                        name=dose_frequency.get("name"),
                    )
                    for dose_frequency in input_dict.get("dose_frequencies")
                ],
                compound=MedicinalProductVO.CompoundInfo(
                    uid=input_dict.get("compound").get("uid"),
                    name=input_dict.get("compound").get("name"),
                ),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict["library_name"],
                is_library_editable_callback=(
                    lambda _: input_dict["is_library_editable"]
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict["change_description"],
                status=LibraryItemStatus(input_dict.get("status")),
                author_id=input_dict["author_id"],
                author_username=input_dict.get("author_username"),
                start_date=convert_to_datetime(value=input_dict["start_date"]),
                end_date=convert_to_datetime(value=input_dict.get("end_date")),
                major_version=int(major),
                minor_version=int(minor),
            ),
        )
        return ar

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> MedicinalProductAR:
        pharmaceutical_products = [
            MedicinalProductVO.PharmaceuticalProductInfo(
                uid=pp.uid,
                external_id=pp.has_latest_value.get().external_id,
            )
            for pp in value.has_pharmaceutical_product.all()
        ]

        dose_values = [
            MedicinalProductVO.DoseValueInfo(
                uid=dv.uid,
                value=dv_val.value,
                unit_definition_uid=unit.uid,
                unit_label=unit_val.name,
            )
            for dv in value.has_dose_value.all()
            if (dv_val := dv.has_latest_value.get_or_none()) is not None
            and (unit := dv_val.has_unit_definition.get_or_none()) is not None
            and (unit_val := unit.has_latest_value.get_or_none()) is not None
        ]

        dose_frequencies = [
            dose_frequency
            for ct_term_context in value.has_dose_frequency.all()
            if (
                dose_frequency := CtTermInfo.extract_ct_term_info(
                    ct_term_context=ct_term_context
                )
            )
            is not None
        ]

        delivery_device = CtTermInfo.extract_ct_term_info(
            ct_term_context=value.has_delivery_device.get_or_none()
        )
        dispenser = CtTermInfo.extract_ct_term_info(
            ct_term_context=value.has_dispenser.get_or_none()
        )

        compound = MedicinalProductVO.CompoundInfo(
            uid=value.is_compound.get().uid,
            name=value.is_compound.get().has_latest_value.get().name,
        )

        ar = MedicinalProductAR.from_repository_values(
            uid=root.uid,
            concept_vo=MedicinalProductVO.from_repository_values(
                external_id=value.external_id,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                compound_uid=compound.uid,
                pharmaceutical_product_uids=[x.uid for x in pharmaceutical_products],
                dose_value_uids=[x.uid for x in dose_values],
                dose_frequency_uids=[
                    x.term_uid for x in dose_frequencies if x.term_uid is not None
                ],
                delivery_device_uid=(
                    delivery_device.term_uid if delivery_device else None
                ),
                dispenser_uid=dispenser.term_uid if dispenser else None,
                dose_frequencies=dose_frequencies,
                delivery_device=delivery_device,
                dispenser=dispenser,
                pharmaceutical_products=pharmaceutical_products,
                dose_values=dose_values,
                compound=compound,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )
        return ar

    def specific_alias_clause(self, **kwargs) -> str:
        return """
            WITH *,
                head([(concept_value)-[:IS_COMPOUND]->(compound:CompoundRoot)-[:LATEST]->(compound_val:CompoundValue) | {uid: compound.uid, name: compound_val.name}]) AS compound,
                [(concept_value)-[:HAS_PHARMACEUTICAL_PRODUCT]->(pp:PharmaceuticalProductRoot)-[:LATEST]->(pp_val:PharmaceuticalProductValue) 
                    | {uid: pp.uid, external_id: pp_val.external_id, version: pp_val.version}] AS pharmaceutical_products,
                [(concept_value)-[:HAS_DOSE_VALUE]->(dv:NumericValueWithUnitRoot)-[:LATEST]->(dv_val:NumericValueWithUnitValue)-[:HAS_UNIT_DEFINITION]->(unit:UnitDefinitionRoot)-[:LATEST]->(unit_val:UnitDefinitionValue)
                    | {uid: dv.uid, value: dv_val.value, unit_definition_uid: unit.uid, unit_label: unit_val.name}] AS dose_values,
                [(concept_value)-[:HAS_DOSE_FREQUENCY]->(df_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(df:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(df_name_val:CTTermNameValue)
                    | {uid: df.uid, name: df_name_val.name}] AS dose_frequencies,
                head([(concept_value)-[:HAS_DISPENSER]->(disp_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(disp:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(disp_name_val:CTTermNameValue)
                    | {uid: disp.uid, name: disp_name_val.name}]) AS dispenser,
                head([(concept_value)-[:HAS_DELIVERY_DEVICE]->(dev_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(device:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(device_name_val:CTTermNameValue)
                    | {uid: device.uid, name: device_name_val.name}]) AS delivery_device
                """
