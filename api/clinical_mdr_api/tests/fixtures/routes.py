import logging
from collections import defaultdict

import pytest
import starlette.routing

__all__ = ["main_app_all_route_paths"]

log = logging.getLogger(__name__)

# A Mapping type that returns a placeholder for missing keys
PARAMETER_DEFAULTS = defaultdict(
    lambda: "MISSING",
    **{
        "codelist_uid": "98765432101",
        "catalogue_name": "98765432102",
        "study_number": "98765432103",
        "term_uid": "98765432104",
        "uid": "98765432105",
        "study_uid": "98765432106",
        "version": "0.98765432107",
        "field_name": "uid",
        "repeating": "false",
    },
)


@pytest.fixture(scope="session")
def main_app_all_route_paths(main_app) -> tuple[tuple[str, tuple[str]], ...]:
    log.debug("Compiling a list of all route paths")

    paths = []
    for route in main_app.routes:
        if isinstance(route, starlette.routing.Route):
            path = route.path.format_map(PARAMETER_DEFAULTS)
            paths.append((path, tuple(route.methods)))

    return tuple(paths)
