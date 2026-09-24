from datetime import datetime
from typing import Annotated, Literal
from urllib.parse import quote

from fastapi import APIRouter, File, Path, Query, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import StringConstraints

from clinical_mdr_api.domains.odms.utils import ExporterType, TargetType
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.odms.clinspark_import import (
    OdmClinicalXmlImporterService,
)
from clinical_mdr_api.services.odms.csv_exporter import OdmCsvExporterService
from clinical_mdr_api.services.odms.data_extractor import OdmDataExtractor
from clinical_mdr_api.services.odms.metadata import (
    get_odm_aliases,
    get_odm_formal_expressions,
    get_odm_translated_texts,
)
from clinical_mdr_api.services.odms.xml_exporter import OdmXmlExporterService
from clinical_mdr_api.services.odms.xml_importer import OdmXmlImporterService
from clinical_mdr_api.services.odms.xml_stylesheets import (
    STYLESHEET_NAME_PATTERN,
    OdmXmlStylesheetService,
)
from common import templating
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.exceptions import ValidationException

# Prefixed with "/odms/metadata"
router = APIRouter()

OP_ANNOTATION = Annotated[
    Literal["co", "eq"],
    Query(
        description="Operator to use for filtering. `co` for contains, `eq` for equals. Default is `co`."
    ),
]


@router.get(
    "/aliases",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Listing of ODM Aliases",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
    },
)
def get_aliases(
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    sort_by: Annotated[
        str,
        StringConstraints(strip_whitespace=True),
        Query(
            description="""Comma separated list of fields to sort by. Available fields are: `name`, `context`. Prefix with `-` for descending order.
            E.g. `-name,context` sorts by name in descending order and then by context in ascending order.""",
        ),
    ] = "",
    search: Annotated[
        str | None,
        Query(description="Search by name or context. Search is case insensitive."),
    ] = None,
    op: OP_ANNOTATION = "co",
) -> CustomPage:
    aliases, total = get_odm_aliases(
        page_number=page_number,
        page_size=page_size,
        sort_by=sort_by,
        search=search,
        op=op,
    )
    return CustomPage(items=aliases, size=page_size, page=page_number, total=total)


@router.get(
    "/translated-texts",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Listing of ODM Translated Texts",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
    },
)
def get_translated_texts(
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    sort_by: Annotated[
        str,
        StringConstraints(strip_whitespace=True),
        Query(
            description="""Comma separated list of fields to sort by. Available fields are: `text_type`, `language` and `text`. Prefix with `-` for descending order.
            E.g. `-language,text_type` sorts by language in descending order and then by text_type in ascending order.""",
        ),
    ] = "",
    search: Annotated[
        str | None,
        Query(
            description="Search by text_type, language or text. Search is case insensitive."
        ),
    ] = None,
    op: OP_ANNOTATION = "co",
) -> CustomPage:
    translated_texts, total = get_odm_translated_texts(
        page_number=page_number,
        page_size=page_size,
        sort_by=sort_by,
        search=search,
        op=op,
    )

    return CustomPage(
        items=translated_texts, size=page_size, page=page_number, total=total
    )


@router.get(
    "/formal-expressions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Listing of ODM Formal Expressions",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
    },
)
def get_formal_expressions(
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    sort_by: Annotated[
        str,
        StringConstraints(strip_whitespace=True),
        Query(
            description="""Comma separated list of fields to sort by. Available fields are: `context` and `expression`. Prefix with `-` for descending order.
            E.g. `-context,expression` sorts by context in descending order and then by expression in ascending order.""",
        ),
    ] = "",
    search: Annotated[
        str | None,
        Query(
            description="Search by context or expression. Search is case insensitive."
        ),
    ] = None,
    op: OP_ANNOTATION = "co",
) -> CustomPage:
    formal_expressions, total = get_odm_formal_expressions(
        page_number=page_number,
        page_size=page_size,
        sort_by=sort_by,
        search=search,
        op=op,
    )

    return CustomPage(
        items=formal_expressions, size=page_size, page=page_number, total=total
    )


@router.post(
    "/report",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Export ODM Report",
    status_code=200,
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/html": {}},
        },
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
    response_class=Response,
)
def get_odm_report(
    request: Request,
    target_type: TargetType,
    targets: Annotated[
        list[str],
        Query(
            description="List of UIDs and (optionally) versions separated by comma. E.g. `uid1,v1` or `uid1` for latest version.",
        ),
    ],
):
    odm_data_extractor = OdmDataExtractor(target_type, targets)

    return templating.templates.TemplateResponse(
        request,
        "odm/crf.html",
        {
            "request": request,
            "data": {
                "odm_forms": odm_data_extractor.odm_forms,
                "odm_item_groups": odm_data_extractor.odm_item_groups,
                "odm_items": odm_data_extractor.odm_items,
            },
        },
        headers={
            "Content-Disposition": f'attachment; filename="{datetime.now().strftime('odm_report_%Y%m%d_%H%M%S.html')}"',
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'",
        },
    )


MAPPER_DESCRIPTION = """
Optional CSV file providing mapping rules between a legacy vendor extension and its OpenStudyBuilder equivalent.\n\n
Only CSV format is supported.\n\n
Following headers must exist: `type`, `parent`, `from_name`, `to_name`, `to_alias`, `from_alias` and `alias_context`\n\n
Allowed values for `type` are: `attribute` and `element`\n\n
Allowed values for `to_alias` and `from_alias` are: `true` and `false`. Anything other than `true` is considered `false`\n\n
If `to_alias` is true `type` must be `attribute`\n\n
If `to_alias` is true `to_name` is ignored\n\n
If `from_alias` is true `alias_context` must be provided\n\n
If `parent` is empty or `*` is given then the mapping will apply to all occurrences in the entire XML file"""


@router.post(
    "/xmls/export",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Export ODM XML",
    status_code=200,
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/xml": {}, "application/pdf": {}},
        },
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
    response_class=Response,
)
def get_odm_document(
    target_type: TargetType,
    targets: Annotated[
        list[str],
        Query(
            description="List of UIDs and (optionally) versions separated by comma. E.g. `uid1,v1` or `uid1` for latest version.",
        ),
    ],
    allowed_namespaces: Annotated[
        list[str] | None,
        Query(
            description="Names of the Vendor Namespaces to export or `*` to export all available Vendor Namespaces. If not specified, no Vendor Namespaces will be exported."
        ),
    ] = None,
    pdf: Annotated[
        bool, Query(description="Whether or not to export the ODM as a PDF.")
    ] = False,
    stylesheet: Annotated[
        str | None,
        Query(description="Name of the ODM XML Stylesheet.", pattern="^[a-zA-Z0-9-]+$"),
    ] = None,
    mapper_file: Annotated[
        UploadFile | None, File(description=MAPPER_DESCRIPTION)
    ] = None,
):
    if allowed_namespaces is None:
        allowed_namespaces = []

    odm_xml_export_service = OdmXmlExporterService(
        target_type, targets, allowed_namespaces, pdf, stylesheet, mapper_file
    )

    content = odm_xml_export_service.get_odm_document()

    if pdf:
        return Response(
            content,
            headers={
                "Content-Disposition": f'attachment; filename="{datetime.now().strftime('CRF %Y%m%d %H%M%S.pdf')}"',
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "default-src 'none'",
            },
            media_type="application/pdf",
        )

    return Response(
        content=content,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="{datetime.now().strftime('odm_export_%Y%m%d_%H%M%S.xml')}"',
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'",
        },
    )


@router.post(
    "/csvs/export",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Export ODM CSV",
    status_code=200,
    responses={
        200: {"description": "Successful Response", "content": {"text/csv": {}}},
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
    response_class=StreamingResponse,
)
def get_odm_csv(target_uid: str, target_type: TargetType):
    odm_csv_exporter_service = OdmCsvExporterService(target_uid, target_type)
    csv_data = odm_csv_exporter_service.get_odm_csv()

    return StreamingResponse(
        iter(csv_data),
        200,
        {"Content-Disposition": "attachment; filename=odm_metadata.csv"},
        "text/csv",
    )


@router.post(
    "/xmls/import",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Import ODM XML",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def store_odm_xml(
    xml_file: Annotated[
        UploadFile, File(description="The ODM XML file to upload. Supports ODM V1.")
    ],
    exporter: Annotated[
        ExporterType,
        Query(
            description="The system that exported this ODM XML file.",
        ),
    ] = ExporterType.OSB,
    mapper_file: Annotated[
        UploadFile | None, File(description=MAPPER_DESCRIPTION)
    ] = None,
    library_name: Annotated[
        str | None,
        Query(
            description="The name of the library to import into. Defaults to the configured sponsor library.",
        ),
    ] = None,
):
    kwargs = {"library_name": library_name} if library_name else {}
    if exporter == ExporterType.OSB:
        odm_xml_importer_service = OdmXmlImporterService(
            xml_file, mapper_file, **kwargs
        )
    else:
        odm_xml_importer_service = OdmClinicalXmlImporterService(
            xml_file, mapper_file, **kwargs
        )

    return odm_xml_importer_service.store_odm_xml()


@router.get(
    "/xmls/stylesheets",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Listing of all available ODM XML Stylesheet names",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_available_stylesheet_names() -> list[str]:
    return OdmXmlStylesheetService.get_available_stylesheet_names()


@router.get(
    "/xmls/stylesheets/{stylesheet}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get a specific ODM XML Stylesheet",
    status_code=200,
    responses={
        200: {"description": "Successful Response", "content": {"application/xml": {}}},
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
    response_class=Response,
)
def get_specific_stylesheet(
    stylesheet: Annotated[str, Path(description="Name of the ODM XML Stylesheet.")],
):
    if not STYLESHEET_NAME_PATTERN.fullmatch(stylesheet):
        raise ValidationException(
            msg="Stylesheet name must only contain letters, numbers and hyphens."
        )

    rs = OdmXmlStylesheetService.get_specific_stylesheet(stylesheet)

    # URL-encode the filename for safe inclusion in header
    safe_filename = quote(f"{stylesheet}.xsl", safe="")

    return Response(
        content=rs,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'",
        },
    )
