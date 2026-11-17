import contextvars

from starlette_context import request_cycle_context

from common.auth.dependencies import dummy_access_token_claims, dummy_auth_object
from common.auth.user import transaction_metadata


def test_transaction_metadata_identifies_user():
    auth_info = dummy_auth_object(dummy_access_token_claims(user_id="some-user"))

    with request_cycle_context({"auth": auth_info}):
        assert transaction_metadata() == {"user_id": "some-user"}


def test_transaction_metadata_identifies_client_application():
    claims = dummy_access_token_claims().model_copy(
        update={"oid": None, "azp": "some-app", "preferred_username": None}
    )

    with request_cycle_context({"auth": dummy_auth_object(claims)}):
        assert transaction_metadata() == {"user_id": "some-app"}


def test_transaction_metadata_before_authentication():
    with request_cycle_context({}):
        assert transaction_metadata() == {}


def test_transaction_metadata_outside_request():
    assert contextvars.Context().run(transaction_metadata) == {}
