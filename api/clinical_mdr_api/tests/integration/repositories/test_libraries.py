import unittest

from clinical_mdr_api.repositories.libraries import (
    create,
    does_library_exist,
    find_all,
    find_by_name,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db


class TestLibrary(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("libraryrepo")

    def test_create(self):
        data_e = create("Test editable", True)
        data_ne = create("Test not editable", False)

        self.assertEqual(data_e["name"], "Test editable")
        self.assertEqual(data_ne["name"], "Test not editable")

        result = does_library_exist("Not test")
        self.assertEqual(len(result), 0)

        result = does_library_exist("Test editable")
        self.assertEqual(len(result), 1)

        result = find_all(None)
        self.assertEqual(len(result), 2)

        result = find_all(True)
        self.assertEqual(len(result), 1)

        result = find_all(False)
        self.assertEqual(len(result), 1)

        result = find_by_name("Test editable")
        self.assertEqual(len(result), 1)
