"""Helpers shared across the standards import API."""

import os
from typing import Any

from common.models.error import ErrorResponse


def get_api_version() -> str:
    version_path = os.path.join("./standards_import", "apiVersion")
    with open(version_path, encoding="utf-8") as file:
        return file.read().strip()


# Declaring these registers ErrorResponse in the generated schema. Without at least
# one route referring to the model, the `400` that the OpenAPI customisation adds to
# every operation would point at a component that is never defined.
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Bad Request"},
    403: {"model": ErrorResponse, "description": "Forbidden"},
}

NOT_FOUND_RESPONSES: dict[int | str, dict[str, Any]] = {
    **ERROR_RESPONSES,
    404: {"model": ErrorResponse, "description": "Not Found"},
}
