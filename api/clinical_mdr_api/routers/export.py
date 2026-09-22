import collections
import csv
import functools
import io
from copy import copy
from typing import Any, Callable

import yaml
from dict2xml import dict2xml
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

from clinical_mdr_api.models import utils
from clinical_mdr_api.models.utils import BaseModel

REGISTERED_EXPORT_FORMATS: dict[str, Callable[..., Any]] = {}


def register_export_format(name: str):
    """Decorator used to register an export function.

    Give a valid MIME type for name.
    """

    def decorator(func):
        REGISTERED_EXPORT_FORMATS[name] = func
        return func

    return decorator


def _convert_headers_to_dict(headers: list[Any]) -> dict[str, Any]:
    """
    Converts a list of headers to a dictionary.

    Args:
        headers (list[Any]): The headers to convert.

    Returns:
        dict[str, Any]: The converted headers as a dictionary.
    """

    dict_headers = collections.OrderedDict()
    for item in headers:
        if "=" in item:
            name, value = item.split("=")
            dict_headers[name] = value
        else:
            dict_headers[item] = item
    return dict_headers


def _extract_values_from_data(data: dict[Any, Any], headers: dict[Any, Any]):
    """
    Extracts required values from data and yields them.

    Args:
        data (dict): The data to extract values from.
        headers (dict): The headers containing the keys to extract.

    Yields:
        dict: The extracted values as a dictionary.
    """
    if isinstance(data, utils.CustomPage | utils.GenericFilteringReturn):
        data = data.items
    if isinstance(data, BaseModel):
        data = [data]
    for item in data:
        result = {}
        if not isinstance(item, dict):
            item = item.model_dump()
        for header, target in headers.items():
            if "." in target:
                value = item
                parts = target.split(".")
                for index, path in enumerate(parts):
                    if isinstance(value, list):
                        items = []
                        for elm in value:
                            subvalue = elm.get(path, "")
                            if isinstance(subvalue, float | int | str):
                                # collection[].key
                                items.append(str(subvalue))
                            elif isinstance(subvalue, dict):
                                # collection[].key1.key2
                                items.append(subvalue[parts[index + 1]])
                        value = ", ".join(items)
                    elif isinstance(value, dict):
                        # Check if path contains [] notation
                        if path.endswith("[]"):
                            # Strip [] and get the list
                            clean_path = path[:-2]
                            value = value.get(clean_path, "")
                        else:
                            value = value.get(path, "")
                    if not value:
                        break
            else:
                value = item.get(target, "")
                if isinstance(value, bool):
                    value = "Yes" if value else "No"
            if value == []:
                value = ""
            result[header] = value
        yield result


def _convert_data_to_rows(data: dict[Any, Any], headers: list[Any]):
    """Generate rows based on given data."""
    # First, convert received headers to a more usable representation
    dict_headers = _convert_headers_to_dict(headers)
    yield list(dict_headers.keys())
    for value in _extract_values_from_data(data, dict_headers):
        rs: list[str | bool | float | int] = []
        for x in value.values():
            if isinstance(x, str):
                rs.append(x.replace("\n", " ").replace("\r", " "))
            elif isinstance(x, bool | float | int):
                rs.append(x)
            elif x is None:
                rs.append("")
            else:
                rs.append(str(x))
        yield rs


def _convert_data_to_list(data: dict[Any, Any], headers: list[Any]) -> list[Any]:
    """Generate a list of dictionaries based on given data."""
    # First, convert received headers to a more usable representation
    dict_headers = _convert_headers_to_dict(headers)
    result = []
    for value in _extract_values_from_data(data, dict_headers):
        result.append(value)
    return result


@register_export_format("text/csv")
def _export_to_csv(data: dict[Any, Any], headers: list[Any]):
    """Export given data to CSV.

    The generated CSV content will only contain items listed in
    headers.
    """
    stream = io.StringIO()
    writer = csv.writer(stream, delimiter=",", quoting=csv.QUOTE_ALL)
    for row in _convert_data_to_rows(data, headers):
        writer.writerow(row)
    return stream.getvalue()


@register_export_format(
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
def _export_to_xslx(data: dict[Any, Any], headers: list[Any]):
    """Export given data to XLSX.

    The generated content will only contain items listed in headers.
    """
    stream = io.BytesIO()
    workbook = Workbook()
    # grab the active worksheet
    worksheet = workbook.active
    for row in _convert_data_to_rows(data, headers):
        worksheet.append(row)
    workbook.save(stream)
    return stream.getvalue()


@register_export_format("text/xml")
def _export_to_xml(data: dict[Any, Any], headers: list[Any]):
    """Export given data to XML.

    The generated content will only contain items listed in headers.
    """
    export_dict = {"item": _convert_data_to_list(data, headers)}
    # If data is a single BaseModel instance we don't won't to wrap the export into <items> tags
    if isinstance(data, BaseModel):
        return dict2xml(export_dict, indent="  ")
    return dict2xml(export_dict, wrap="items", indent="  ")


@register_export_format("application/x-yaml")
# pylint: disable=unused-argument
def _export_to_yaml(data: BaseModel, headers: list[Any]):
    """Export given data to YAML."""
    return yaml.dump(data.model_dump())


def export(
    export_format: str,
    data: dict[Any, Any],
    export_definition: dict[Any, Any],
    *args,
    custom_fields: list[str] | None = None,
    **kwargs,
):
    """Generic export function.

    Use this function when you want to export data to given data. It
    will return a StreamingResponse instance or the given data if
    format is not supported.

    Args:
        export_format: The MIME type of the export format
        data: The data to export
        export_definition: Dictionary containing default fields and format definitions
        custom_fields: Optional list of custom field names to export instead of defaults
    """
    # Use custom fields if provided, otherwise use format-specific or default fields
    if custom_fields:
        headers = custom_fields
    elif export_format in export_definition:
        headers = export_definition[export_format]
    else:
        headers = export_definition["defaults"]

    if export_format in REGISTERED_EXPORT_FORMATS:
        if isinstance(data, utils.CustomPage | utils.GenericFilteringReturn):
            data = data.items

        # Only add extra headers if not using custom fields
        if not custom_fields:
            extra_headers = export_definition.get("include_if_exists")
            headers = copy(headers)
            if extra_headers and data:
                headers += [
                    extra_header
                    for extra_header in extra_headers
                    if extra_header in data[0]
                ]
        else:
            headers = copy(headers)

        result = REGISTERED_EXPORT_FORMATS[export_format](
            data, headers, *args, **kwargs
        )
        response = StreamingResponse(iter([result]), media_type=export_format)
        response.headers["Content-Disposition"] = "attachment; filename=export"
        return response
    return data


_TRUTHY_QUERY_VALUES = frozenset({"true", "1", "yes", "on"})


def _query_param_is_truthy(request, name: str) -> bool:
    if request is None:
        return False
    raw = request.query_params.get(name)
    if raw is None:
        return False
    return raw.lower() in _TRUTHY_QUERY_VALUES


def _resolve_export_definition(
    export_definition: dict[Any, Any], request
) -> dict[Any, Any]:
    variants = export_definition.get("variants")
    if not variants:
        return export_definition
    base = {key: value for key, value in export_definition.items() if key != "variants"}
    for param_name, variant in variants.items():
        if _query_param_is_truthy(request, param_name):
            return {**base, **variant}
    return base


def allow_exports(export_definition: dict[Any, Any]):
    """Decorator used to add export functionality to list type endpoint.

    The export_definition may declare optional ``variants`` mapping a
    query-string parameter name to a partial export definition. When the
    named parameter is present in the request and parses as truthy
    (``true``/``1``/``yes``/``on``, case-insensitive), the variant is
    shallow-merged over the base definition before exporting. Variants
    are evaluated in declaration order; the first match wins.

    Supports custom field selection via the 'export_fields' query parameter.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            accept = None
            custom_fields = None

            if request:
                accept = request.headers.get("accept", "application/json")
                # Extract export_fields query parameter if present
                export_fields_param = request.query_params.get("export_fields")
                if export_fields_param:
                    # Split comma-separated fields and strip whitespace
                    custom_fields = [
                        field.strip()
                        for field in export_fields_param.split(",")
                        if field.strip()
                    ]

            result = func(*args, **kwargs)
            resolved = _resolve_export_definition(export_definition, request)
            formats = list(resolved.get("formats", []))
            formats.extend(resolved.keys())
            if accept and accept in formats:
                result = export(accept, result, resolved, custom_fields=custom_fields)
            return result

        return wrapper

    return decorator
