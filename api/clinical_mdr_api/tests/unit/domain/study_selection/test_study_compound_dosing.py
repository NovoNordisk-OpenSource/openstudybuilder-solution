import datetime
import unittest

from clinical_mdr_api.domains.concepts.medicinal_product import (
    MedicinalProductAR,
    MedicinalProductVO,
)
from clinical_mdr_api.domains.study_selections.study_compound_dosing import (
    StudyCompoundDosingVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import (
    AUTHOR_ID,
    AUTHOR_USERNAME,
    random_str,
)
from common import exceptions

MEDICINAL_PRODUCT_UID = "MedicinalProduct_000001"
DOSE_VALUE_UID = "dose_value_uid1"
DOSE_FREQUENCY_UID_1 = "dose_frequency_uid1"
DOSE_FREQUENCY_UID_2 = "dose_frequency_uid2"


def create_medicinal_product_ar(
    dose_frequency_uids: list[str] | None = None,
    dose_value_uids: list[str] | None = None,
) -> MedicinalProductAR:
    return MedicinalProductAR.from_repository_values(
        uid=MEDICINAL_PRODUCT_UID,
        concept_vo=MedicinalProductVO.from_repository_values(
            name="medicinal product name",
            name_sentence_case="medicinal product name",
            external_id=None,
            compound_uid="compound_uid1",
            pharmaceutical_product_uids=[],
            delivery_device_uid=None,
            dispenser_uid=None,
            dose_value_uids=(
                dose_value_uids if dose_value_uids is not None else [DOSE_VALUE_UID]
            ),
            dose_frequency_uids=dose_frequency_uids,
        ),
        library=LibraryVO.from_repository_values(
            library_name="Sponsor", is_editable=True
        ),
        item_metadata=LibraryItemMetadataVO.from_repository_values(
            change_description="Initial version",
            status=LibraryItemStatus.FINAL,
            author_id=AUTHOR_ID,
            author_username=AUTHOR_USERNAME,
            start_date=datetime.datetime.now(datetime.timezone.utc),
            end_date=None,
            major_version=1,
            minor_version=0,
        ),
    )


def create_study_compound_dosing_vo(
    dose_frequency_uid: str | None = None,
    dose_value_uid: str | None = DOSE_VALUE_UID,
) -> StudyCompoundDosingVO:
    return StudyCompoundDosingVO.from_input_values(
        study_uid="Study_000001",
        study_selection_uid=random_str(),
        study_compound_uid="StudyCompound_000001",
        study_element_uid="StudyElement_000001",
        medicinal_product_uid=MEDICINAL_PRODUCT_UID,
        dose_value_uid=dose_value_uid,
        dose_frequency_uid=dose_frequency_uid,
        author_id=AUTHOR_ID,
        start_date=datetime.datetime.now(datetime.timezone.utc),
    )


class TestStudyCompoundDosingVOValidate(unittest.TestCase):
    def _validate(
        self,
        compound_dosing_vo: StudyCompoundDosingVO,
        medicinal_product_ar: MedicinalProductAR,
    ) -> None:
        compound_dosing_vo.validate(
            selection_uid_by_compound_dose_and_frequency_callback=lambda _: None,
            medicinal_product_callback=lambda _: medicinal_product_ar,
        )

    def test__validate__dose_frequency_defined_on_medicinal_product__success(self):
        medicinal_product_ar = create_medicinal_product_ar(
            dose_frequency_uids=[DOSE_FREQUENCY_UID_1, DOSE_FREQUENCY_UID_2]
        )
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_2
        )

        self._validate(compound_dosing_vo, medicinal_product_ar)

    def test__validate__no_dose_frequency_selected__success(self):
        medicinal_product_ar = create_medicinal_product_ar(
            dose_frequency_uids=[DOSE_FREQUENCY_UID_1]
        )
        compound_dosing_vo = create_study_compound_dosing_vo(dose_frequency_uid=None)

        self._validate(compound_dosing_vo, medicinal_product_ar)

    def test__validate__medicinal_product_not_found__success(self):
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_1
        )

        compound_dosing_vo.validate(
            selection_uid_by_compound_dose_and_frequency_callback=lambda _: None,
            medicinal_product_callback=lambda _: None,
        )

    def test__validate__dose_frequency_not_defined_on_medicinal_product__failure(self):
        medicinal_product_ar = create_medicinal_product_ar(
            dose_frequency_uids=[DOSE_FREQUENCY_UID_1]
        )
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_2
        )

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            self._validate(compound_dosing_vo, medicinal_product_ar)

        self.assertIn("dose frequency", context.exception.msg)

    def test__validate__medicinal_product_without_dose_frequencies__failure(self):
        medicinal_product_ar = create_medicinal_product_ar(dose_frequency_uids=[])
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_1
        )

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            self._validate(compound_dosing_vo, medicinal_product_ar)

        self.assertIn("dose frequency", context.exception.msg)

    def test__validate__dose_value_not_defined_on_medicinal_product__failure(self):
        medicinal_product_ar = create_medicinal_product_ar(
            dose_frequency_uids=[DOSE_FREQUENCY_UID_1], dose_value_uids=[]
        )
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_1
        )

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            self._validate(compound_dosing_vo, medicinal_product_ar)

        self.assertIn("dose value", context.exception.msg)
