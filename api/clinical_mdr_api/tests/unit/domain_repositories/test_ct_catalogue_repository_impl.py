import unittest
from typing import Collection
from unittest.mock import Mock, patch

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_catalogue_repository import (
    CTCatalogueRepository,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCatalogue,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_catalogue import CTCatalogueAR
from clinical_mdr_api.tests.unit.domain.utils import random_str


class MockLibrary:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name


def create_random_ct_catalogue_node(library_name: str | None) -> CTCatalogue:
    mock = Mock()
    mocked_library_node = MockLibrary(library_name)
    mock.single = lambda: mocked_library_node
    random_ct_catalogue = CTCatalogue(name=random_str(), contains_catalogue=mock)
    return random_ct_catalogue


class TestCTCatalogueRepositoryImpl(unittest.TestCase):
    @patch(CTCatalogueRepository.__module__ + ".CTCatalogue")
    def test__find_all_mocked_ct_catalogue_exist(self, ct_catalogue_mock):
        # given
        repo = CTCatalogueRepository()
        ct_catalogues: list[CTCatalogue] = [
            create_random_ct_catalogue_node(random_str()) for _ in range(10)
        ]
        ct_catalogue_mock.nodes.order_by("name").all.return_value = ct_catalogues

        # when
        ct_catalogue_ars: Collection[CTCatalogueAR] = repo.find_all(library_name=None)

        # then
        self.assertTrue(len(ct_catalogue_ars) > 0)
        for ct_catalogue, ct_catalogue_ar in zip(ct_catalogues, ct_catalogue_ars):
            with self.subTest():
                self.assertEqual(ct_catalogue.name, ct_catalogue_ar.name)
                self.assertEqual(
                    ct_catalogue.contains_catalogue.single().name,
                    ct_catalogue_ar.library_name,
                )

    @patch(CTCatalogueRepository.__module__ + ".CTCatalogue")
    def test__find_all_mocked_ct_catalogue_not_exist(self, ct_catalogue_mock):
        # given
        repo = CTCatalogueRepository()
        ct_catalogues: list[CTCatalogue] = []
        ct_catalogue_mock.nodes.order_by("name").all.return_value = ct_catalogues

        # when
        ct_catalogue_ars: Collection[CTCatalogueAR] = repo.find_all(library_name=None)

        # then
        self.assertTrue(len(ct_catalogue_ars) == 0)

    @patch(CTCatalogueRepository.__module__ + ".CTCatalogue")
    def test__find_all_mocked_ct_catalogue_exist_valid_library_passed(
        self, ct_catalogue_mock
    ):
        # given
        repo = CTCatalogueRepository()
        valid_library_name: str = random_str()
        invalid_library_name: str = random_str()
        ct_catalogues_valid_library = [
            create_random_ct_catalogue_node(valid_library_name) for _ in range(6)
        ]
        ct_catalogues_invalid_library = [
            create_random_ct_catalogue_node(invalid_library_name) for _ in range(4)
        ]
        ct_catalogues: list[CTCatalogue] = (
            ct_catalogues_valid_library + ct_catalogues_invalid_library
        )
        ct_catalogue_mock.nodes.order_by("name").all.return_value = ct_catalogues

        # when
        ct_catalogue_ars: Collection[CTCatalogueAR] = repo.find_all(
            library_name=valid_library_name
        )

        # then
        # check if CTCatalogues with specified library name were only fetched
        self.assertTrue(len(ct_catalogue_ars) == len(ct_catalogues_valid_library))

        for ct_catalogue, ct_catalogue_ar in zip(
            ct_catalogues_valid_library, ct_catalogue_ars
        ):
            with self.subTest():
                self.assertEqual(ct_catalogue.name, ct_catalogue_ar.name)
                self.assertEqual(
                    ct_catalogue.contains_catalogue.single().name,
                    ct_catalogue_ar.library_name,
                )

        # check if CTCatalogues with not specified library name were not fetched
        invalid_library_ct_catalogues_names = [
            ct_catalogue.name for ct_catalogue in ct_catalogues_invalid_library
        ]
        ct_catalogues_names = [ct_catalogue.name for ct_catalogue in ct_catalogue_ars]
        for invalid_library_ct_catalogues_name in invalid_library_ct_catalogues_names:
            with self.subTest():
                self.assertNotIn(
                    invalid_library_ct_catalogues_name, ct_catalogues_names
                )
