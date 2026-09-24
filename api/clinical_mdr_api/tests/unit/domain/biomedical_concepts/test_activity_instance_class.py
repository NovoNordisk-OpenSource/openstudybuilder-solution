import unittest

from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
    ActivityInstanceClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str


def create_activity_instance_class_vo(
    name: str | None = None,
    nci_concept_id: str | None = None,
    nci_concept_name: str | None = None,
) -> ActivityInstanceClassVO:
    return ActivityInstanceClassVO.from_repository_values(
        name=name or random_str(),
        order=None,
        definition=random_str(),
        is_domain_specific=False,
        level=None,
        dataset_class_uid=None,
        activity_item_classes=[],
        nci_concept_id=nci_concept_id,
        nci_concept_name=nci_concept_name,
    )


def create_activity_instance_class_ar(
    nci_concept_id: str | None = None,
    nci_concept_name: str | None = None,
) -> ActivityInstanceClassAR:
    return ActivityInstanceClassAR.from_input_values(
        author_id=AUTHOR_ID,
        activity_instance_class_vo=create_activity_instance_class_vo(
            nci_concept_id=nci_concept_id, nci_concept_name=nci_concept_name
        ),
        library=LibraryVO.from_repository_values(
            library_name="Sponsor", is_editable=True
        ),
        activity_instance_class_exists_by_name_callback=lambda _: False,
        dataset_class_exists_by_uid=lambda _: None,
        generate_uid_callback=random_str,
    )


class TestActivityInstanceClass(unittest.TestCase):
    def test__init__ar_created_with_nci_properties(self):
        # when
        activity_instance_class_ar = create_activity_instance_class_ar(
            nci_concept_id="C12345", nci_concept_name="Some NCI Concept"
        )

        # then
        self.assertEqual(activity_instance_class_ar.nci_concept_id, "C12345")
        self.assertEqual(
            activity_instance_class_ar.nci_concept_name, "Some NCI Concept"
        )
        self.assertEqual(
            activity_instance_class_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__init__ar_created_without_nci_properties(self):
        # when
        activity_instance_class_ar = create_activity_instance_class_ar()

        # then
        self.assertIsNone(activity_instance_class_ar.nci_concept_id)
        self.assertIsNone(activity_instance_class_ar.nci_concept_name)

    def test__edit_draft__nci_properties_updated_and_new_version_created(self):
        # given
        activity_instance_class_ar = create_activity_instance_class_ar(
            nci_concept_id="C12345", nci_concept_name="Old NCI Concept"
        )
        activity_instance_class_ar.approve(author_id=AUTHOR_ID)
        activity_instance_class_ar.create_new_version(author_id=AUTHOR_ID)

        edited_vo = create_activity_instance_class_vo(
            nci_concept_id="C67890", nci_concept_name="New NCI Concept"
        )

        # when
        activity_instance_class_ar.edit_draft(
            author_id=AUTHOR_ID,
            change_description="Updated NCI properties",
            activity_instance_class_vo=edited_vo,
            activity_instance_class_exists_by_name_callback=lambda _: False,
            dataset_class_exists_by_uid=lambda _: None,
        )

        # then
        self.assertEqual(activity_instance_class_ar.nci_concept_id, "C67890")
        self.assertEqual(activity_instance_class_ar.nci_concept_name, "New NCI Concept")
        self.assertEqual(activity_instance_class_ar.item_metadata.version, "1.2")
        self.assertEqual(
            activity_instance_class_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__edit_draft__unchanged_nci_properties_do_not_create_new_version(self):
        # given
        activity_instance_class_ar = create_activity_instance_class_ar(
            nci_concept_id="C12345", nci_concept_name="Same NCI Concept"
        )
        original_vo = activity_instance_class_ar.activity_instance_class_vo
        activity_instance_class_ar.approve(author_id=AUTHOR_ID)
        activity_instance_class_ar.create_new_version(author_id=AUTHOR_ID)

        # when: re-submitting an identical VO (same nci_concept_id/name and all other fields)
        activity_instance_class_ar.edit_draft(
            author_id=AUTHOR_ID,
            change_description="No-op edit",
            activity_instance_class_vo=original_vo,
            activity_instance_class_exists_by_name_callback=lambda _: False,
            dataset_class_exists_by_uid=lambda _: None,
        )

        # then: no new version is cut, since the VO (including nci fields) is unchanged
        self.assertEqual(activity_instance_class_ar.item_metadata.version, "1.1")

    def test__nci_concept_id_participates_in_vo_equality(self):
        # given: two VOs identical in every field except nci_concept_id
        common_kwargs = {
            "name": "Some class",
            "order": None,
            "definition": "Some definition",
            "is_domain_specific": False,
            "level": None,
            "dataset_class_uid": None,
            "activity_item_classes": [],
            "nci_concept_name": "Some NCI Concept",
        }
        vo_a = ActivityInstanceClassVO.from_repository_values(
            nci_concept_id="C12345", **common_kwargs
        )
        vo_b = ActivityInstanceClassVO.from_repository_values(
            nci_concept_id="C67890", **common_kwargs
        )

        # then: VOs differing only by nci_concept_id must not compare equal,
        # otherwise `_has_data_changed`/`edit_draft` would silently ignore NCI edits
        self.assertNotEqual(vo_a, vo_b)
