# RESTful API endpoints used by consumers that want to extract data from OpenStudyBuilder
# This file is a placeholder for version 2 of the consumer api,
# and should be replaced by the real v2 code once that needs to be implemented.

# from fastapi import APIRouter, Query, Request

# from consumer_api.auth import rbac
# from consumer_api.shared import config
# from consumer_api.shared.responses import PaginatedResponse
# from consumer_api.v2 import db as DB
# from consumer_api.v2 import models

# router = APIRouter()

# Example v2 endpoint.
# GET endpoint to retrieve a list of studies.
# An endpoint with the same path also exists in v1.
# But since no breaking changes can be allowed in the consumer api,
# any change that could break existing consumers requires that
# a new version of the endpoint is created.
# A breaking change is anything that modifies the existing content of the response.
# Only changes that add additional content within the response are considered
# non-breaking.
#
# @router.get(
#     "/studies",
#     dependencies=[security, rbac.STUDY_READ],
# )
# def get_studies(
#     request: Request,
#     sort_by: models.SortByStudies = models.SortByStudies.UID,
#     sort_order: models.SortOrder = models.SortOrder.ASC,
#     page_size: Annotated[int, Query(
#         ge=0,
#         le=settings.max_page_size,
#     )] = settings.default_page_size,
#     page_number: Annotated[int, Query(ge=1)] = 1,
# ) -> PaginatedResponse[models.Study]:
#     """Get a list of studies"""
#     studies = DB.get_studies(
#         sort_by=sort_by,
#         sort_order=sort_order,
#         page_size=page_size,
#         page_number=page_number,
#     )

#     return PaginatedResponse.from_input(
#         request=request,
#         sort_by=sort_by.value,
#         sort_order=sort_order.value,
#         page_size=page_size,
#         page_number=page_number,
#         items=[models.Study.from_input(study) for study in studies],
#     )
