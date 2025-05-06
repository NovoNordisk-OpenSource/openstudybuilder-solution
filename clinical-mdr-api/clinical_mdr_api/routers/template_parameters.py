from typing import Annotated

from fastapi import APIRouter, Path

from clinical_mdr_api.models.syntax_templates.template_parameter import (
    TemplateParameter,
    TemplateParameterTerm,
)
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services import template_parameters as service
from common.auth import rbac

# Prefixed with "/template-parameters"
router = APIRouter()


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all template parameter available with samples of the available values.",
    description="The returned template parameter are ordered by\n0. name ascending",
    response_model=list[TemplateParameter],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_template_parameters():
    return service.get_all()


@router.get(
    "/{name}/terms",
    dependencies=[rbac.LIBRARY_READ],
    summary="Return all terms available for the given template parameter.",
    response_model=list[TemplateParameterTerm],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_template_parameter_terms(
    name: Annotated[str, Path(description="Name of the template parameter")],
):
    return service.get_template_parameter_terms(name)
