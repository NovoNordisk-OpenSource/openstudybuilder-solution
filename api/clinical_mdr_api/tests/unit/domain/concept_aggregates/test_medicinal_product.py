import unittest

from clinical_mdr_api.domains.concepts.medicinal_product import MedicinalProductVO
from clinical_mdr_api.tests.unit.domain.utils import random_str
from common import exceptions

EXISTING_CT_TERM_UIDS = ["dose_frequency_uid1", "dose_frequency_uid2"]
EXISTING_NUMERIC_VALUE_UIDS = ["dose_value_uid1"]
EXISTING_COMPOUND_UIDS = ["compound_uid1"]
EXISTING_PHARMACEUTICAL_PRODUCT_UIDS = ["pharmaceutical_product_uid1"]


def _ct_term_exists_callback(uid: str) -> bool:
    return uid in EXISTING_CT_TERM_UIDS


def _numeric_value_exists_callback(uid: str) -> bool:
    return uid in EXISTING_NUMERIC_VALUE_UIDS


def _compound_exists_callback(uid: str) -> bool:
    return uid in EXISTING_COMPOUND_UIDS


def _pharmaceutical_product_exists_callback(uid: str) -> bool:
    return uid in EXISTING_PHARMACEUTICAL_PRODUCT_UIDS


def create_medicinal_product_vo(
    dose_frequency_uids: list[str] | None = None,
) -> MedicinalProductVO:
    return MedicinalProductVO.from_repository_values(
        name=random_str(),
        name_sentence_case=random_str(),
        external_id=None,
        compound_uid=EXISTING_COMPOUND_UIDS[0],
        pharmaceutical_product_uids=list(EXISTING_PHARMACEUTICAL_PRODUCT_UIDS),
        delivery_device_uid=None,
        dispenser_uid=None,
        dose_value_uids=list(EXISTING_NUMERIC_VALUE_UIDS),
        dose_frequency_uids=dose_frequency_uids,
    )


class TestMedicinalProductVO(unittest.TestCase):
    def _validate(self, medicinal_product_vo: MedicinalProductVO) -> None:
        medicinal_product_vo.validate(
            uid=random_str(),
            medicinal_product_uid_by_property_value_callback=lambda _x, _y: None,
            ct_term_exists_callback=_ct_term_exists_callback,
            numeric_value_exists_callback=_numeric_value_exists_callback,
            compound_exists_callback=_compound_exists_callback,
            pharmaceutical_product_exists_callback=_pharmaceutical_product_exists_callback,
        )

    def test__from_repository_values__no_dose_frequencies__defaults_to_empty_list(self):
        medicinal_product_vo = create_medicinal_product_vo(dose_frequency_uids=None)

        self.assertEqual(medicinal_product_vo.dose_frequency_uids, [])
        self.assertEqual(medicinal_product_vo.dose_frequencies, [])
        self._validate(medicinal_product_vo)

    def test__validate__no_dose_frequencies__success(self):
        medicinal_product_vo = create_medicinal_product_vo(dose_frequency_uids=[])

        self._validate(medicinal_product_vo)

    def test__validate__single_existing_dose_frequency__success(self):
        medicinal_product_vo = create_medicinal_product_vo(
            dose_frequency_uids=["dose_frequency_uid1"]
        )

        self._validate(medicinal_product_vo)

    def test__validate__multiple_existing_dose_frequencies__success(self):
        medicinal_product_vo = create_medicinal_product_vo(
            dose_frequency_uids=["dose_frequency_uid1", "dose_frequency_uid2"]
        )

        self._validate(medicinal_product_vo)

    def test__validate__non_existent_dose_frequency__failure(self):
        medicinal_product_vo = create_medicinal_product_vo(
            dose_frequency_uids=["dose_frequency_uid1", "non-existent-uid"]
        )

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            self._validate(medicinal_product_vo)

        self.assertIn("non-existent-uid", context.exception.msg)
        self.assertIn("Dose Frequency", context.exception.msg)
