import datetime
import json
import re
from copy import copy, deepcopy
from types import NoneType, UnionType
from typing import (
    Annotated,
    Any,
    Callable,
    Generic,
    Self,
    Sequence,
    TypeVar,
    cast,
    get_args,
    get_origin,
)

import nh3
from annotated_types import MinLen
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field, ValidationInfo, create_model, field_validator
from pydantic.fields import FieldInfo, PydanticUndefined
from starlette.responses import Response

from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.services.user_info import UserInfoService
from common.config import settings
from common.utils import get_field_type, get_sub_fields

ALLOWED_HTML_TAGS = {
    "abbr",  # abbreviation
    "acronym",  # acronym
    "b",  # bold
    "blockquote",  # block quote
    "br",  # line break
    "code",  # code-styled text
    "em",  # emphasis
    "i",  # italic
    "li",  # list item
    "ol",  # ordered list
    "p",  # paragraph
    "strong",  # strong emphasis
    "sub",  # subscript
    "sup",  # superscript
    "u",  # underline
    "ul",  # unordered list
}

ALLOWED_HTML_ATTRIBUTES: dict[Any, Any] = {}

EXCLUDE_PROPERTY_ATTRIBUTES_FROM_SCHEMA = {
    "remove_from_wildcard",
    "source",
    "exclude_from_model_validate",
    "is_json",
}


def from_duration_object_to_value_and_unit(
    duration: str,
    find_all_study_time_units: Callable[..., tuple[list[UnitDefinitionAR], int]],
):
    duration_code = duration[-1].lower()
    # cut off the first 'P' and last unit letter
    duration_value = int(duration[1:-1])

    all_study_time_units, _ = find_all_study_time_units(
        subset=settings.study_time_unit_subset
    )
    # We are using a callback here and this function returns objects as an item list, hence we need to unwrap i
    found_unit = None
    # find unit extracted from iso duration string (duration_code) and find it in the set of all age units
    for unit in all_study_time_units:
        unit_first_letter = unit.name[0].lower()
        unit_last_letter = unit.name[-1].lower()
        # if duration value which is passed is great than 1 we should find a corresponding unit in the plural version
        if (
            duration_value > 1
            and unit_first_letter == duration_code
            and unit_last_letter == "s"
        ):
            found_unit = unit
            break
        if duration_value <= 1 and unit_first_letter == duration_code:
            found_unit = unit
            break
    return duration_value, found_unit


def get_latest_on_datetime_str():
    return f"LATEST on {datetime.datetime.now(datetime.UTC).isoformat()}"


def _json_schema_extra(schema: dict[str, Any], _: type) -> None:
    """Exclude some custom internal attributes of Fields (properties) from the schema definitions"""
    for prop in schema.get("properties", {}).values():
        for attr in EXCLUDE_PROPERTY_ATTRIBUTES_FROM_SCHEMA:
            prop.pop(attr, None)


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra=_json_schema_extra,
    )

    @classmethod
    def model_validate(cls, obj):
        """
        We override this method to allow flattening on nested models.

        It is now possible to declare a source property on a Field()
        call to specify the location where this method should get a
        field's value from.
        """

        def _extract_part_from_node(node_to_extract, path, extract_from_relationship):
            """
            Traverse specified path in the node_to_extract.
            The possible paths for the traversal are stored in the node _relations dictionary.
            """
            if extract_from_relationship:
                path += "_relationship"
            if not hasattr(node_to_extract, "_relations"):
                return None
            if path not in node_to_extract._relations.keys():
                # it means that the field is Optional and None was set to be a default value
                if field.default is None:
                    return None
                raise RuntimeError(
                    f"{path} is not present in node relations (did you forget to fetch it?)"
                )
            if node_to_extract._relations[path] == []:
                return None

            return node_to_extract._relations[path]

        def _get_value_from_source_field(model_field, db_node, db_field):
            value = getattr(db_node, db_field)

            # In case of author_username model field, we need to lookup the User node using the `source` field value as `User.user_id`
            if model_field == "author_username":
                value = UserInfoService.get_author_username_from_id(value)

            return value

        ret: list[Any] = []
        for name, field in cls.model_fields.items():
            jse = field.json_schema_extra or {}
            source: str | None = jse.get("source", None)  # type: ignore[assignment]
            if jse.get("exclude_from_model_validate"):
                continue
            if not source:
                if issubclass(get_field_type(field.annotation), BaseModel):
                    # get out of recursion
                    if get_field_type(field.annotation) is cls:
                        continue
                    # added copy to not override properties in main obj
                    value = get_field_type(field.annotation).model_validate(copy(obj))
                    # if some value of nested model is initialized then set the whole nested object
                    if isinstance(value, list):
                        if value:
                            setattr(obj, name, value)
                        else:
                            setattr(obj, name, [])
                    else:
                        if any(value.dict().values()):
                            setattr(obj, name, value)
                        # if all values of nested model are None set the whole object to None
                        else:
                            setattr(obj, name, None)
                # Quick fix to provide default None value to fields that allow it
                # Not the best place to do this...
                elif field.default == PydanticUndefined and not hasattr(obj, name):
                    setattr(obj, name, None)
                continue
            if isinstance(source, dict):
                source = source["path"]
            if "." in source or "|" in source:
                orig_source = source
                # split by . that implicates property on node or | that indicates property on the relationship
                parts = re.split(r"[.|]", source)
                source = parts[-1]
                last_traversal = parts[-2]
                node = obj
                parts = parts[:-1]
                for _, part in enumerate(parts):
                    extract_from_relationship = False
                    if part == last_traversal and "|" in orig_source:
                        extract_from_relationship = True
                    # if node is a list of nodes we want to extract property/relationship
                    # from all nodes in list of nodes
                    if isinstance(node, list):
                        return_node = []
                        for item in node:
                            extracted = _extract_part_from_node(
                                node_to_extract=item,
                                path=part,
                                extract_from_relationship=extract_from_relationship,
                            )
                            return_node.extend(extracted)
                        node = return_node
                    else:
                        node = _extract_part_from_node(
                            node_to_extract=node,
                            path=part,
                            extract_from_relationship=extract_from_relationship,
                        )
                    if node is None:
                        break
            else:
                node = obj
            if node is not None:
                # if node is a list we want to
                # extract property from each element of list and return list of property values
                if isinstance(node, list):
                    value = [
                        _get_value_from_source_field(name, n, source) for n in node
                    ]
                else:
                    value = _get_value_from_source_field(name, node, source)

            else:
                value = None
            # if obtained value is a list and field type is not List
            # it means that we are building some list[BaseModel] but its fields are not of list type

            if isinstance(value, list) and not get_sub_fields(field):
                # if ret array is not instantiated
                # it means that the first property out of the whole list [BaseModel] is being instantiated
                if not ret:
                    for val in value:
                        temp_obj = copy(obj)
                        setattr(temp_obj, name, val)
                        ret.append(temp_obj)
                # if ret exists it means that some properties out of whole list [BaseModel] are already instantiated
                else:
                    for val, item in zip(value, ret):
                        setattr(item, name, val)
            else:
                setattr(obj, name, value)
        # Nothing to return and the value returned by the query
        # is an empty list => return an empty list
        if not ret and isinstance(value, list) and not value:
            return []
        # Returning single BaseModel
        if not ret and (
            not isinstance(value, list) or (isinstance(value, list) and value)
        ):
            return super().model_validate(obj)
        # if ret exists it means that the list of BaseModels is being returned
        objs_to_return = []
        for item in ret:
            objs_to_return.append(super().model_validate(item))
        return objs_to_return


class InputModel(BaseModel):

    @field_validator("*", mode="before")
    @classmethod
    def _string_validator(cls, value: Any, validation_info: ValidationInfo):
        """
        Field validator sanitizes HTML, strips prefix-tailing whitespace, and conditionally returns `None` for empty strings.

        Empty strings replaced to `None` for fields that:
        - Are annotated with `str` and `None`.
        - Have `min_length` constraint set.

        This validator is applied to all fields (`*`) in "before" mode, to process the value before other validations.

        Args:
            value (Any): The value of the field being validated.
            validation_info (ValidationInfo): Information about the field being validated, including its name and metadata.

        Returns:
            Any: sanitized value, or `None` if the value is an empty string, and the field meets the specified conditions.
        """

        field_info = (
            cls.model_fields.get(validation_info.field_name)
            if validation_info.field_name
            else None
        )

        # Clear HTML
        if (
            field_info
            and field_info.json_schema_extra
            and field_info.json_schema_extra.get("format", "").lower() == "html"
        ):
            if isinstance(value, str):
                value = sanitize_html(value)

            elif isinstance(value, list):
                value = [sanitize_html(v) if isinstance(v, str) else v for v in value]

        # Strip whitespace from strings, items of lists and values of dicts, unless
        # the field opts out (e.g. an opaque blob that must be stored verbatim).
        preserve_whitespace = bool(
            field_info
            and field_info.json_schema_extra
            and field_info.json_schema_extra.get("preserve_whitespace")
        )
        if not preserve_whitespace:
            value = strip_whitespace(value)

        # Empty strings to none
        if (
            field_info
            and isinstance(field_info.annotation, UnionType)
            and NoneType in field_info.annotation.__args__
            and any(isinstance(i, MinLen) for i in getattr(field_info, "metadata", []))
            and value == ""
        ):
            value = None

        return value


class PostInputModel(InputModel): ...


class PatchInputModel(InputModel): ...


class BatchInputModel(InputModel): ...


class EditInputModel(BaseModel):
    change_description: Annotated[str, Field(min_length=1)]


T = TypeVar("T")


class CustomPage(BaseModel, Generic[T]):
    """
    A generic class used as a return type for paginated queries.

    Attributes:
        items (Sequence[T]): The items returned by the query.
        total (int): The total number of items that match the query.
        page (int): The number of the current page.
        size (int): The maximum number of items per page.
    """

    items: Annotated[Sequence[T], Field()]
    total: Annotated[int, Field(ge=-1)]
    page: Annotated[int, Field(ge=0)]
    size: Annotated[int, Field(ge=0)]

    @classmethod
    def create(cls, items: Sequence[T], total: int, page: int, size: int) -> Self:
        return cls(total=total, items=items, page=page, size=size)


class GenericFilteringReturn(BaseModel, Generic[T]):
    """
    A generic class used as a return type for filtered queries.

    Attributes:
        items (list[T]): The items returned by the query.
        total (int): The total number of items that match the query.
    """

    items: Annotated[list[T], Field()]
    total: Annotated[int, Field(ge=-1)]

    @classmethod
    def create(cls, items: list[T], total: int) -> Self:
        return cls(items=items, total=total)


EmptyGenericFilteringResult: GenericFilteringReturn = GenericFilteringReturn(
    items=[], total=0
)


class PrettyJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(", ", ": "),
        ).encode("utf-8")


def strip_whitespace(value: Any) -> Any:
    """Calls str.strip() to strip whitespace off str value or recursively on items of list, set, tuple or values of dict"""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list | set | tuple):
        return [strip_whitespace(elm) for elm in value]

    if isinstance(value, dict):
        return {k: strip_whitespace(v) for k, v in value.items()}

    return value


def sanitize_html(string: str) -> str:
    """Remove malicious HTML tags and attributes from a string."""
    return nh3.clean(
        string, tags=ALLOWED_HTML_TAGS, attributes=ALLOWED_HTML_ATTRIBUTES
    ).strip()


def _make_field_annotation_optional(field_annotation: Any) -> Any:
    """Wrap annotation with None while preserving Annotated metadata."""
    if get_origin(field_annotation) is Annotated:
        annotation, *metadata = get_args(field_annotation)
        return Annotated[annotation | None, *metadata]

    return field_annotation | None


def make_optional(model_cls: type[PydanticBaseModel]) -> type[PydanticBaseModel]:
    """Class decorator that makes all model fields optional and defaults them to None."""
    optional_fields: dict[str, tuple[Any, FieldInfo]] = {}

    for field_name, field_info in model_cls.model_fields.items():
        optional_field_info = deepcopy(field_info)
        optional_field_info.default = None
        optional_field_info.default_factory = None

        optional_fields[field_name] = (
            _make_field_annotation_optional(field_info.annotation),
            optional_field_info,
        )

    optional_model = create_model(
        model_cls.__name__,
        __base__=model_cls,
        **cast(dict[str, Any], optional_fields),
    )
    optional_model.__module__ = model_cls.__module__
    return optional_model
