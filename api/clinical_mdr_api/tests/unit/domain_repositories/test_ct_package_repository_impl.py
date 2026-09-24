import datetime
import unittest
from typing import Collection
from unittest.mock import Mock, patch

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_package_repository import (
    CTPackageRepository,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import CTPackage
from clinical_mdr_api.domains.controlled_terminologies.ct_package import CTPackageAR
from clinical_mdr_api.tests.unit.domain.utils import random_str


class MockLibrary:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name


def create_random_ct_package_node(catalogue_name: str) -> CTPackage:
    mock = Mock()
    mocked_catalogue_node = MockLibrary(catalogue_name)
    mock.single = lambda: mocked_catalogue_node
    random_ct_package = CTPackage(
        uid=random_str(),
        name=random_str(),
        label=random_str(),
        description=random_str(),
        href=random_str(),
        registration_status=random_str(),
        source=random_str(),
        import_date=datetime.datetime.now(datetime.timezone.utc),
        effective_date=datetime.date(year=2020, month=6, day=26),
        author_id=random_str(),
        contains_package=mock,
    )
    return random_ct_package


class TestCTPackageRepositoryImpl(unittest.TestCase):
    @patch(CTPackageRepository.__module__ + ".db")
    def test__find_all_mocked_ct_package_exist(self, ct_package_mock):
        # given
        repo = CTPackageRepository()
        ct_packages: list[list[CTPackage]] = [
            [create_random_ct_package_node(random_str()), "some-id", "some-author"]
            for _ in range(10)
        ]
        ct_package_mock.cypher_query.return_value = ct_packages, ()
        # when
        ct_packages_ars: Collection[CTPackageAR] = repo.find_all(catalogue_name=None)
        # then
        self.assertTrue(len(ct_packages_ars) > 0)
        for ct_package, ct_package_ar in zip(ct_packages, ct_packages_ars):
            with self.subTest():
                self.assertEqual(ct_package[0].uid, ct_package_ar.uid)
                self.assertEqual(
                    ct_package[0].contains_package.single().name,
                    ct_package_ar.catalogue_name,
                )
                self.assertEqual(ct_package[0].name, ct_package_ar.name)
                self.assertEqual(ct_package[0].label, ct_package_ar.label)
                self.assertEqual(ct_package[0].description, ct_package_ar.description)
                self.assertEqual(ct_package[0].href, ct_package_ar.href)
                self.assertEqual(
                    ct_package[0].registration_status, ct_package_ar.registration_status
                )
                self.assertEqual(ct_package[0].source, ct_package_ar.source)
                self.assertEqual(ct_package[0].import_date, ct_package_ar.import_date)
                self.assertEqual(
                    ct_package[0].effective_date, ct_package_ar.effective_date
                )
                self.assertEqual(ct_package[0].author_id, ct_package_ar.author_id)

    @patch(CTPackageRepository.__module__ + ".db")
    def test__find_all_mocked_ct_package_not_exist(self, ct_package_mock):
        # given
        repo = CTPackageRepository()
        ct_packages: list[list[CTPackage]] = []
        ct_package_mock.cypher_query.return_value = ct_packages, ()

        # when
        ct_packages_ars: Collection[CTPackageAR] = repo.find_all(catalogue_name=None)

        # then
        self.assertTrue(len(ct_packages_ars) == 0)

    @patch(CTPackageRepository.__module__ + ".db")
    def test__find_all_mocked_ct_package_exist_valid_catalogue_passed(
        self, ct_package_mock
    ):
        # given
        repo = CTPackageRepository()
        valid_catalogue_name: str = random_str()
        invalid_catalogue_name: str = random_str()
        ct_packages_valid_catalogue = [
            [
                create_random_ct_package_node(valid_catalogue_name),
                "some-id",
                "some-author",
            ]
            for _ in range(6)
        ]
        ct_packages_invalid_catalogue = [
            [
                create_random_ct_package_node(invalid_catalogue_name),
                "some-id",
                "some-author",
            ]
            for _ in range(4)
        ]
        ct_package_mock.cypher_query.return_value = ct_packages_valid_catalogue, ()

        # when
        ct_packages_ars: Collection[CTPackageAR] = repo.find_all(
            catalogue_name=valid_catalogue_name
        )

        # then
        # check if CTPackages with specified catalogue name were only fetched
        self.assertTrue(len(ct_packages_ars) == len(ct_packages_valid_catalogue))

        for ct_package, ct_package_ar in zip(
            ct_packages_valid_catalogue, ct_packages_ars
        ):
            with self.subTest():
                self.assertEqual(ct_package[0].uid, ct_package_ar.uid)
                self.assertEqual(
                    ct_package[0].contains_package.single().name,
                    ct_package_ar.catalogue_name,
                )
                self.assertEqual(ct_package[0].name, ct_package_ar.name)
                self.assertEqual(ct_package[0].label, ct_package_ar.label)
                self.assertEqual(ct_package[0].description, ct_package_ar.description)
                self.assertEqual(ct_package[0].href, ct_package_ar.href)
                self.assertEqual(
                    ct_package[0].registration_status, ct_package_ar.registration_status
                )
                self.assertEqual(ct_package[0].source, ct_package_ar.source)
                self.assertEqual(ct_package[0].import_date, ct_package_ar.import_date)
                self.assertEqual(
                    ct_package[0].effective_date, ct_package_ar.effective_date
                )
                self.assertEqual(ct_package[0].author_id, ct_package_ar.author_id)

        # check if CTPackages with not specified catalogue name were not fetched
        invalid_catalogue_ct_package_uids = [
            ct_package[0].uid for ct_package in ct_packages_invalid_catalogue
        ]
        ct_packages_uid = [ct_package.uid for ct_package in ct_packages_ars]
        for invalid_catalogue_ct_package_uid in invalid_catalogue_ct_package_uids:
            with self.subTest():
                self.assertNotIn(invalid_catalogue_ct_package_uid, ct_packages_uid)
