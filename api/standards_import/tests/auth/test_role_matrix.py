"""What each role is allowed to do, checked against the dependency itself."""

import pytest

from common.auth.dependencies import dummy_user
from common.exceptions import ForbiddenException
from standards_import.tests.auth.routes import IMPORT, READ, WRITE

# Every role OSB grants elsewhere. None of them opens this app, in either direction.
# `Admin.Read` is on the list rather than singled out: it used to admit the read routes,
# and it is the one most likely to be assumed to still work.
OTHER_ROLES = [
    "Admin.Read",
    "Admin.Write",
    "Library.Read",
    "Library.Write",
    "Study.Read",
    "Study.Write",
]


def allowed(roles: set[str], required: set[str]) -> bool:
    """Whether a user holding exactly `roles` gets past `RequiresAnyRole(required)`.

    `dummy_user(roles=None)` is not a role-less user — it falls back to every role OSB
    grants, `Library.Import` included — so the set is always assigned explicitly here.
    """

    user = dummy_user(roles={"placeholder"})
    user.roles = set(roles)
    try:
        user.authorize(*required)
    except ForbiddenException:
        return False
    return True


# --- one role gates everything ---------------------------------------------------


def test_the_import_role_can_both_read_and_write():
    assert allowed({IMPORT}, READ) is True
    assert allowed({IMPORT}, WRITE) is True


@pytest.mark.parametrize("role", OTHER_ROLES)
@pytest.mark.parametrize("required", [READ, WRITE], ids=["read", "write"])
def test_roles_from_elsewhere_in_osb_open_nothing_here(role, required):
    """Including the reads.

    Reading here is not the broad read `Admin.Read` grants across OSB: it is the review
    queue and the staged contents of a release nobody has imported yet, which is of use
    to whoever is running the import and to nobody else.
    """

    assert allowed({role}, required) is False


def test_every_standard_osb_role_at_once_opens_nothing():
    """Nobody acquires `Library.Import` by accumulating the ordinary roles."""

    assert allowed(set(OTHER_ROLES), READ) is False
    assert allowed(set(OTHER_ROLES), WRITE) is False


@pytest.mark.parametrize("required", [READ, WRITE], ids=["read", "write"])
def test_a_token_with_no_roles_is_refused(required):
    assert allowed(set(), required) is False


@pytest.mark.parametrize("required", [READ, WRITE], ids=["read", "write"])
def test_unknown_roles_are_refused(required):
    assert allowed({"Some.Fake.Role", ""}, required) is False


# --- combinations -----------------------------------------------------------------


def test_holding_the_import_role_alongside_others_still_grants_access():
    """Any one of the required roles is enough; extra roles are not disqualifying."""

    assert allowed({IMPORT, "Library.Read", "Study.Write"}, WRITE) is True


def test_the_error_says_which_role_was_needed():
    """A 403 that does not say what is missing is not much use to a caller."""

    outsider = dummy_user(roles={"Admin.Read"})

    with pytest.raises(ForbiddenException) as caught:
        outsider.authorize(*READ)

    assert IMPORT in str(caught.value.msg)
