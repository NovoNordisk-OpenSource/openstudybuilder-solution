from fastapi import APIRouter

from common.auth import rbac
from common.auth.dependencies import security
from extensions.hello import db as DB

router = APIRouter(
    tags=["Hello"],
)


# GET endpoint that returns the count of nodes in the database
@router.get(
    "/nodes-count",
    dependencies=[security, rbac.ADMIN_READ],
    status_code=200,
)
def get_nodes_count() -> int:
    """
    Returns the count of nodes in the database.
    """
    count = DB.get_node_count()
    return count
