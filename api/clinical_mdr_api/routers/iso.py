from typing import TypedDict

from fastapi import APIRouter

from clinical_mdr_api.domains.iso_languages import (
    LANGUAGES_BY_NAME_AND_639_1_AND_639_2T,
)
from common.auth import rbac
from common.auth.dependencies import security

# Prefixed with "/iso"
router = APIRouter()


ISOLanguageModel = TypedDict("ISOLanguageModel", {"name": str, "_1": str, "_2T": str})


@router.get(
    "/639",
    dependencies=[security, rbac.LIBRARY_READ_OR_STUDY_READ],
    summary="Get ISO 639 Languages",
    description="""
Get a list of ISO 639 languages with their codes.\n
The list includes the language name, ISO 639-1 code and ISO 639-2T code.
""",
)
def get_iso_languages() -> list[ISOLanguageModel]:
    return [
        {"name": name, "_1": x, "_2T": y}
        for name, (x, y) in LANGUAGES_BY_NAME_AND_639_1_AND_639_2T.items()
    ]
