from fastapi import APIRouter

router = APIRouter(
    tags=["System"],
)


@router.get(
    "/healthcheck",
    summary="Returns 200 OK status if the system is ready to serve requests",
    status_code=200,
)
async def healthcheck() -> str:
    return "OK"
