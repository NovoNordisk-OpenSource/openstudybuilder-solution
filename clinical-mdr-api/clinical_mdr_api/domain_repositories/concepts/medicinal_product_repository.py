from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
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
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.concept_base import _AggregateRootType
from clinical_mdr_api.domains.concepts.medicinal_product import (
    MedicinalProductAR,
    MedicinalProductVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.medicinal_product import MedicinalProduct
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

        if ar.concept_vo.dose_frequency_uid is not None:
            value_node.has_dose_frequency.connect(
                CTTermRoot.nodes.get(uid=ar.concept_vo.dose_frequency_uid)
            )

        if ar.concept_vo.delivery_device_uid is not None:
            value_node.has_delivery_device.connect(
                CTTermRoot.nodes.get(uid=ar.concept_vo.delivery_device_uid)
            )

        if ar.concept_vo.dispenser_uid is not None:
            value_node.has_dispenser.connect(
                CTTermRoot.nodes.get(uid=ar.concept_vo.dispenser_uid)
            )

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

        old_dose_freq = value.has_dose_frequency.get_or_none()
        old_dose_freq_uid = old_dose_freq.uid if old_dose_freq else None

        old_delivery_device = value.has_delivery_device.get_or_none()
        old_delivery_device_uid = (
            old_delivery_device.uid if old_delivery_device else None
        )

        old_dispenser = value.has_dispenser.get_or_none()
        old_dispenser_uid = old_dispenser.uid if old_dispenser else None

        are_rels_changed = (
            sorted(ar.concept_vo.dose_value_uids)
            != sorted([val.uid for val in value.has_dose_value.all()])
            or (ar.concept_vo.dose_frequency_uid != old_dose_freq_uid)
            or (ar.concept_vo.delivery_device_uid != old_delivery_device_uid)
            or (ar.concept_vo.dispenser_uid != old_dispenser_uid)
            or sorted(ar.concept_vo.pharmaceutical_product_uids)
            != sorted([val.uid for val in value.has_pharmaceutical_product.all()])
            or (ar.concept_vo.compound_uid != value.is_compound.get().uid)
        )

        return was_parent_data_modified or are_rels_changed

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> MedicinalProductAR:
        major, minor = input_dict.get("version").split(".")
        ar = MedicinalProductAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=MedicinalProductVO.from_repository_values(
                external_id=input_dict.get("external_id"),
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("name_sentence_case"),
                dose_value_uids=list(
                    map(lambda x: x.get("uid"), input_dict.get("dose_values"))
                ),
                dose_frequency_uid=(
                    input_dict.get("dose_frequency")._properties.get("uid")
                    if input_dict.get("dose_frequency")
                    else None
                ),
                delivery_device_uid=(
                    input_dict.get("delivery_device")._properties.get("uid")
                    if input_dict.get("delivery_device")
                    else None
                ),
                dispenser_uid=(
                    input_dict.get("dispenser")._properties.get("uid")
                    if input_dict.get("dispenser")
                    else None
                ),
                pharmaceutical_product_uids=list(
                    map(
                        lambda x: x.get("uid"),
                        input_dict.get("pharmaceutical_products"),
                    )
                ),
                compound_uid=input_dict.get("compound_uid"),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict.get("library_name"),
                is_library_editable_callback=(
                    lambda _: input_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("change_description"),
                status=LibraryItemStatus(input_dict.get("status")),
                author_id=input_dict.get("author_id"),
                author_username=input_dict.get("author_username"),
                start_date=convert_to_datetime(value=input_dict.get("start_date")),
                end_date=convert_to_datetime(value=input_dict.get("end_date")),
                major_version=int(major),
                minor_version=int(minor),
            ),
        )
        return ar

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> MedicinalProductAR:
        dose_frequency = value.has_dose_frequency.get_or_none()
        delivery_device = value.has_delivery_device.get_or_none()
        dispenser = value.has_dispenser.get_or_none()

        ar = MedicinalProductAR.from_repository_values(
            uid=root.uid,
            concept_vo=MedicinalProductVO.from_repository_values(
                external_id=value.external_id,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                compound_uid=value.is_compound.get().uid,
                pharmaceutical_product_uids=[
                    x.uid for x in value.has_pharmaceutical_product.all()
                ],
                dose_value_uids=[x.uid for x in value.has_dose_value.all()],
                dose_frequency_uid=dose_frequency.uid if dose_frequency else None,
                delivery_device_uid=delivery_device.uid if delivery_device else None,
                dispenser_uid=dispenser.uid if dispenser else None,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )
        return ar

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
        return """
            WITH *,
                head([(concept_value)-[:IS_COMPOUND]->(compound:CompoundRoot) | compound.uid]) AS compound_uid,
                [(concept_value)-[:HAS_PHARMACEUTICAL_PRODUCT]->(pp:PharmaceuticalProductRoot) | pp] AS pharmaceutical_products,
                [(concept_value)-[:HAS_DOSE_VALUE]->(dv:NumericValueWithUnitRoot) | dv] AS dose_values,
                head([(concept_value)-[:HAS_DOSE_FREQUENCY]->(df:CTTermRoot) | df]) AS dose_frequency,
                head([(concept_value)-[:HAS_DISPENSER]->(disp:CTTermRoot) | disp]) AS dispenser,
                head([(concept_value)-[:HAS_DELIVERY_DEVICE]->(device:CTTermRoot) | device]) AS delivery_device
                """
