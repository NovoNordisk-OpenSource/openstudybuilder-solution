import collections
import csv
import functools
import io
from copy import copy
from typing import Any

import yaml
from dict2xml import dict2xml
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

from clinical_mdr_api.models import utils
from clinical_mdr_api.models.utils import BaseModel

REGISTERED_EXPORT_FORMATS = {}


def register_export_format(name: str):
    """Decorator used to register an export function.

    Give a valid MIME type for name.
    """

    def decorator(func):
        REGISTERED_EXPORT_FORMATS[name] = func
        return func

    return decorator


def _convert_headers_to_dict(headers: list[Any]) -> dict:
    """
    Converts a list of headers to a dictionary.

    Args:
        headers (list[Any]): The headers to convert.

    Returns:
        dict: The converted headers as a dictionary.
    """

    dict_headers = collections.OrderedDict()
    for item in headers:
        if "=" in item:
            name, value = item.split("=")
            dict_headers[name] = value
        else:
            dict_headers[item] = item
    return dict_headers


def _extract_values_from_data(data: dict, headers: dict):
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
            item = item.dict()
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


def _convert_data_to_rows(data: dict, headers: list[Any]):
    """Generate rows based on given data."""
    # First, convert received headers to a more usable representation
    dict_headers = _convert_headers_to_dict(headers)
    yield list(dict_headers.keys())
    for value in _extract_values_from_data(data, dict_headers):
        rs = []
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


def _convert_data_to_list(data: dict, headers: list[Any]) -> list[Any]:
    """Generate a list of dictionaries based on given data."""
    # First, convert received headers to a more usable representation
    dict_headers = _convert_headers_to_dict(headers)
    result = []
    for value in _extract_values_from_data(data, dict_headers):
        result.append(value)
    return result


@register_export_format("text/csv")
def _export_to_csv(data: dict, headers: list[Any]):
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
def _export_to_xslx(data: dict, headers: list[Any]):
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
def _export_to_xml(data: dict, headers: list[Any]):
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


def export(export_format: str, data: dict, export_definition: dict, *args, **kwargs):
    """Generic export function.

    Use this function when you want to export data to given data. It
    will return a StreamingResponse instance or the given data if
    format is not supported.
    """
    if export_format in export_definition:
        headers = export_definition[export_format]
    else:
        headers = export_definition["defaults"]
    if export_format in REGISTERED_EXPORT_FORMATS:
        if isinstance(data, utils.CustomPage | utils.GenericFilteringReturn):
            data = data.items
        extra_headers = export_definition.get("include_if_exists")
        headers = copy(headers)
        if extra_headers and data:
            headers += [
                extra_header
                for extra_header in extra_headers
                if extra_header in data[0]
            ]

        result = REGISTERED_EXPORT_FORMATS[export_format](
            data, headers, *args, **kwargs
        )
        response = StreamingResponse(iter([result]), media_type=export_format)
        response.headers["Content-Disposition"] = "attachment; filename=export"
        return response
    return data


def allow_exports(export_definition: dict):
    """Decorator used to add export functionality to list type endpoint."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            accept = None
            if request:
                accept = request.headers.get("accept", "application/json")
            result = func(*args, **kwargs)
            formats = export_definition.get("formats", [])
            formats.extend(export_definition.keys())
            if accept and accept in formats:
                result = export(accept, result, export_definition)
            return result

        return wrapper

    return decorator
