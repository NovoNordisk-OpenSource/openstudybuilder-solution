"""MS Graph API integrations router"""

from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import StringConstraints

from clinical_mdr_api.models.integrations import msgraph as msgraph_model
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.integrations import msgraph
from common.auth import rbac

# Prefixed with "/integrations/ms-graph"
router = APIRouter()


@router.get(
    "/users",
    dependencies=[rbac.ANY],
    summary="List users of the relevant AD groups",
    description="Lists all users whose name, initials or email match the optional `search` parameter (regex)"
    " and who are members of relevant AD groups.",
    status_code=200,
    response_model=list[msgraph_model.GraphUser],
    response_model_by_alias=False,
    response_model_exclude_none=True,
    responses={
        403: _generic_descriptions.ERROR_403,
    },
)
async def get_users(
    search: Annotated[
        str | None,
        StringConstraints(strip_whitespace=True, min_length=2, max_length=255),
        Query(title="Filter users by name or initials"),
    ] = None
):
    if msgraph.service:
        return await msgraph.service.search_all_group_direct_member_users(search)
    return []
