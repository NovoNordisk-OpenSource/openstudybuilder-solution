from clinical_mdr_api.repositories import libraries as libraries_repository
from common.exceptions import AlreadyExistsException


def get_libraries(is_editable: bool | None):
    return libraries_repository.find_all(is_editable)


def create(name: str, is_editable: bool):
    AlreadyExistsException.raise_if(
        libraries_repository.find_by_name(name), "Library", name, "Name"
    )

    return libraries_repository.create(name, is_editable)
