# pylint: disable=unused-argument,redefined-outer-name

import logging

import pytest
from _pytest.fixtures import FixtureRequest

from clinical_mdr_api.services.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesService,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def test_data(request: FixtureRequest):
    """Fixture creates, initializes and yields a test database, then destroys it at teardown"""

    log.debug("%s() fixture: creating database", request.fixturename)
    db_name = "services.ctversioning"
    database = inject_and_clear_db(db_name)

    log.debug("%s() fixture: initializing database", request.fixturename)
    inject_base_data()
    log.debug("%s() fixture: setup complete", request.fixturename)
    yield database

    # log.debug("%s() fixture: teardown: deleting database", request.fixturename)
    # database.cypher_query("CREATE OR REPLACE DATABASE $db", {"db": db_name})


def test_version_sequence(test_data):
    # Create a new term as draft
    ct_test_term = TestUtils.create_ct_term(
        sponsor_preferred_name="test_term_1", approve=False
    )
    initial = CTTermAttributesService().get_by_uid(ct_test_term.term_uid)
    assert initial.version == "0.1", "New term is not version 0.1"
    assert initial.status == "Draft", "New term is not in Draft"
    history = CTTermAttributesService().get_version_history(ct_test_term.term_uid)
    assert len(history) == 1
    #
    # Edit the new draft to create a new draft version
    initial.definition = "edited_" + initial.definition
    CTTermAttributesService().edit_draft(ct_test_term.term_uid, initial)
    edited = CTTermAttributesService().get_by_uid(ct_test_term.term_uid)
    assert edited.version == "0.2", "Edited term is not version 0.2"
    assert edited.status == "Draft", "Edited term is not in Draft"
    history = CTTermAttributesService().get_version_history(ct_test_term.term_uid)
    assert len(history) == 2

    # Approve the term to make it Final
    CTTermAttributesService().approve(term_uid=ct_test_term.term_uid)
    approved = CTTermAttributesService().get_by_uid(ct_test_term.term_uid)
    assert approved.version == "1.0", "Approved term is not version 1.0"
    assert approved.status == "Final", "Approved term is not in Final"
    history = CTTermAttributesService().get_version_history(ct_test_term.term_uid)
    assert len(history) == 3

    # Create a new version to go back to Draft
    CTTermAttributesService().create_new_version(ct_test_term.term_uid)
    new_draft = CTTermAttributesService().get_by_uid(ct_test_term.term_uid)
    assert new_draft.version == "1.1", "New version is not version 1.1"
    assert new_draft.status == "Draft", "New version is not in Draft"
    history = CTTermAttributesService().get_version_history(ct_test_term.term_uid)
    assert len(history) == 4

    # Approve the term to make it Final
    CTTermAttributesService().approve(term_uid=ct_test_term.term_uid)
    approved = CTTermAttributesService().get_by_uid(ct_test_term.term_uid)
    assert approved.version == "2.0", "Approved term is not version 2.0"
    assert approved.status == "Final", "Approved term is not in Final"
    history = CTTermAttributesService().get_version_history(ct_test_term.term_uid)
    assert len(history) == 5

    # Inactivate
    CTTermAttributesService().inactivate_final(ct_test_term.term_uid)
    inactivated = CTTermAttributesService().get_by_uid(ct_test_term.term_uid)
    assert inactivated.version == "2.0", "Inactivated version is not version 2.0"
    assert inactivated.status == "Retired", "Inactivated version is not Retired"
    history = CTTermAttributesService().get_version_history(ct_test_term.term_uid)
    assert len(history) == 6

    # Reactivate
    CTTermAttributesService().reactivate_retired(ct_test_term.term_uid)
    reactivated = CTTermAttributesService().get_by_uid(ct_test_term.term_uid)
    assert reactivated.version == "2.0", "Reactivated version is not version 2.0"
    assert reactivated.status == "Final", "Reactivated version is not in Final"
    history = CTTermAttributesService().get_version_history(ct_test_term.term_uid)
    assert len(history) == 7

    # Check that we have the right versions
    expected = [
        ("2.0", "Final"),
        ("2.0", "Retired"),
        ("2.0", "Final"),
        ("1.1", "Draft"),
        ("1.0", "Final"),
        ("0.2", "Draft"),
        ("0.1", "Draft"),
    ]
    for item, (ver, status) in zip(history, expected):
        assert item.version == ver
        assert item.status == status

    # Check that the start and end dates are sequential
    change_date = None
    for item, (ver, status) in zip(history, expected):
        assert (
            item.start_date is not None
        ), f"Version {ver} {status} is missing a start date"
        if change_date is None:
            assert (
                item.end_date is None
            ), f"The latest version {ver} {status} should not have an end date"
        else:
            assert (
                item.end_date is not None
            ), f"Version {ver} {status} is missing an end date"
            assert (
                item.end_date <= change_date
            ), f"Version {ver} {status} has an end date after the start date of the next version"
        change_date = item.start_date
