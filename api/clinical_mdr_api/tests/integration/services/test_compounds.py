import unittest

from neomodel import db
from parameterized import parameterized

from clinical_mdr_api.models.concepts.compound import Compound, CompoundEditInput
from clinical_mdr_api.models.concepts.compound_alias import (
    CompoundAlias,
    CompoundAliasEditInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.services.concepts.compound_alias_service import (
    CompoundAliasService,
)
from clinical_mdr_api.services.concepts.compound_service import CompoundService
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_INSTANCES,
    STARTUP_ACTIVITY_INSTANCES_CT_INIT,
    STARTUP_ACTIVITY_SUB_GROUPS,
    STARTUP_NUMERIC_VALUES_WITH_UNITS,
    STARTUP_PROJECTS_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from common import exceptions


class TestCompoundsService(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("compounds.service")

        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)
        db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
        db.cypher_query(STARTUP_PROJECTS_CYPHER)

        super().setUp()

    @parameterized.expand(
        [
            ({"*": {"v": ["aaa"]}}, "name", "name-AAA-"),
            ({"*": {"v": ["bBb"]}}, "name", "name-BBB-"),
            (
                {"*": {"v": ["unknown-user"], "op": "co"}},
                "author_username",
                "unknown-user@example.com",
            ),
            ({"*": {"v": ["Draft"]}}, "status", "Draft"),
            ({"*": {"v": ["0.1"]}}, "version", "0.1"),
            ({"*": {"v": ["ccc"]}}, None, None),
        ]
    )
    def test_filtering_wildcard(
        self, filter_by, expected_matched_field, expected_result_prefix
    ):
        for index in range(5):
            TestUtils.create_compound(name="name-AAA-" + str(index))
            TestUtils.create_compound(name="name-BBB-" + str(index))
            TestUtils.create_compound(definition="def-XXX-" + str(index))
            TestUtils.create_compound(definition="def-YYY-" + str(index))

        service = CompoundService()
        results: GenericFilteringReturn = service.get_all_concepts(
            library="Sponsor", filter_by=filter_by
        )

        if expected_result_prefix:
            assert len(results.items) > 0
            # Each returned row has a field that starts with the specified filter value
            for row in results.items:
                assert (
                    getattr(row, expected_matched_field).startswith(
                        expected_result_prefix
                    )
                    is True
                )
        else:
            assert len(results.items) == 0

    @parameterized.expand(
        [
            ({"name": {"v": ["name-AAA"]}}, "name", "name-AAA"),
            ({"name": {"v": ["name-BBB"]}}, "name", "name-BBB"),
            ({"name": {"v": ["cc"]}}, None, None),
            ({"definition": {"v": ["def-XXX"]}}, "definition", "def-XXX"),
            ({"definition": {"v": ["def-YYY"]}}, "definition", "def-YYY"),
            ({"definition": {"v": ["cc"]}}, None, None),
        ]
    )
    def test_filtering_exact(self, filter_by, expected_matched_field, expected_result):
        TestUtils.create_compound(name="name-AAA")
        TestUtils.create_compound(name="name-BBB")
        TestUtils.create_compound(definition="def-XXX")
        TestUtils.create_compound(definition="def-YYY")

        service = CompoundService()
        results: GenericFilteringReturn = service.get_all_concepts(
            library="Sponsor", filter_by=filter_by
        )

        if expected_result:
            assert len(results.items) > 0
            # Each returned row has a field whose value is equal to the specified filter value
            for row in results.items:
                assert getattr(row, expected_matched_field) == expected_result
        else:
            assert len(results.items) == 0

    def test_delete_compound(self):
        # Create a compound with two aliases
        compound: Compound = TestUtils.create_compound(name="name-AAA")
        compound_alias1 = TestUtils.create_compound_alias(
            name=f"Alias1 for {compound.name}", compound_uid=compound.uid
        )
        compound_alias2 = TestUtils.create_compound_alias(
            name=f"Alias2 for {compound.name}", compound_uid=compound.uid
        )

        CompoundService().soft_delete(compound.uid)

        # Assert that both the compound and two aliases are deleted
        with self.assertRaises(exceptions.NotFoundException):
            CompoundService().get_by_uid(compound.uid)

        with self.assertRaises(exceptions.NotFoundException):
            CompoundAliasService().get_by_uid(compound_alias1.uid)

        with self.assertRaises(exceptions.NotFoundException):
            CompoundAliasService().get_by_uid(compound_alias2.uid)

        results: GenericFilteringReturn = CompoundAliasService().get_all_concepts(
            library="Sponsor", filter_by={"compound_uid": {"v": [compound.uid]}}
        )
        assert len(results.items) == 0

    def test_caching(self):
        # Create a compound with an alias
        compound_name = "name-AAA"
        compound: Compound = TestUtils.create_compound(name=compound_name)
        compound_alias1: CompoundAlias = TestUtils.create_compound_alias(
            name=f"Alias1 for {compound.name}", compound_uid=compound.uid
        )

        # Update compound, then fetch it and assert that the updated name is returned
        CompoundService().edit_draft(
            uid=compound.uid,
            concept_edit_input=CompoundEditInput(
                name=f"{compound_name}-UPDATED",
                change_description="Update name",
            ),
        )
        compound = CompoundService().get_by_uid(compound.uid)
        assert compound.name == f"{compound_name}-UPDATED"

        # Update compound alias, then fetch it and assert that the updated name is returned
        CompoundAliasService().edit_draft(
            uid=compound_alias1.uid,
            concept_edit_input=CompoundAliasEditInput(
                name=f"{compound_name}-UPDATED",
                compound_uid=compound.uid,
                change_description="Update name",
            ),
        )
        compound_alias = CompoundAliasService().get_by_uid(compound_alias1.uid)
        assert compound_alias.name == f"{compound_name}-UPDATED"
