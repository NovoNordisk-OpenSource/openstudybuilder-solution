import functools
from collections.abc import Hashable
from dataclasses import dataclass
from enum import Enum
from time import time
from typing import AbstractSet, Any, Callable, Mapping, MutableMapping, Self, TypeVar

import neomodel.sync_.core
from pydantic import BaseModel

from clinical_mdr_api.domain_repositories.libraries.library_repository import (
    LibraryRepository,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.models.syntax_templates.template_parameter import (
    ComplexTemplateParameter,
    TemplateParameter,
    TemplateParameterTerm,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    ComparisonOperator,
    FilterDict,
    FilterOperator,
)
from clinical_mdr_api.utils import extract_parameters
from common.exceptions import ValidationException
from common.telemetry import trace_calls
from common.utils import get_field_type


def is_library_editable(name: str) -> bool:
    """
    Checks if a library with the given name is editable.

    Args:
        name (str): The name of the library to check.

    Returns:
        bool: True if the library is editable, False if it is not editable.

    Raises:
        NotFoundException: If the library doesn't exist.

    Example:
        >>> is_library_editable("Sponsor")
        True
    """
    return LibraryRepository().find_by_name(name).is_editable


def get_term_uid_or_none(field):
    return field.term_uid if field else None


def get_unit_def_uid_or_none(field):
    return field.uid if field else None


def get_name_or_none(field):
    return field.name if field else None


def get_input_or_new_value(
    input_field: str | None, prefix: str, output_field: str, sep: str = "."
):
    """
    Returns the `input_field` if it has a value, otherwise generates a new value using the `prefix`,
    initials of the `output_field` and a timestamp.

    Args:
        input_field (str | None): The value to return if it has a value.
        prefix (str): The prefix to use when generating a new value.
        output_field (str): The output field to use when generating a new value.
        sep (str, optional): The separator to use when joining the initials with the timestamp. Defaults to ".".

    Returns:
        str: The `input_field` if it has a value, otherwise a new value generated using the `prefix`, initials of the `output_field` and a timestamp.

    Raises:
        ValueError: If `output_field` is not a string.

    Example:
        >>> get_input_or_new_value("1234", "ID", "Name")
        "1234"

        >>> get_input_or_new_value(None, "ID", "First Last")
        "IDFL.1639527992"

        >>> get_input_or_new_value(None, "ID", "First Last", "@")
        "IDFL@1639527992"
    """
    if input_field:
        return input_field

    if not isinstance(output_field, str):
        raise ValueError(f"Expected type str but found {type(output_field)}")

    splitted = output_field.split()
    if len(splitted) > 1:
        initials = "".join([s[0] for s in splitted])
    else:
        initials = output_field[::2].upper()

    return f"{prefix}{initials}{sep}{int(time())}"


def object_diff(objt1, objt2=None) -> list[str]:
    """
    Calculate difference table between pydantic objects and return only those fields in the payload that have changed
    """
    if objt2 is None:
        return []

    return [name for name in objt1.keys() if objt1[name] != objt2[name]]


def get_otv(version_object_class, object1, object2=None):
    """
    Creates object of the version_object_class extending object object1
    with the differences with object object2
    """

    changes = object_diff(object1, object2) if object2 is not None else []
    return version_object_class(changes=changes, **object1)


def calculate_diffs(result_list, version_object_class):
    """
    Calculates differences in a list of results and push the comparison results
    to a version_object_class object.
    Returns list of version_class_objects
    """

    if len(result_list) == 0:
        return []
    otv = get_otv(version_object_class, result_list[-1])
    return_list = [otv]
    for i in reversed(range(len(result_list) - 1)):
        item = result_list[i]
        otv = get_otv(version_object_class, item, result_list[i + 1])
        return_list.append(otv)

    return list(reversed(return_list))


def fill_missing_values_in_base_model_from_reference_base_model(
    base_model_with_missing_values: BaseModel, reference_base_model: BaseModel
) -> None:
    """
    Fills missing values in the PATCH payload when only a partial payload is sent by the client.
    It takes the values from the model object based on the domain object.

    Args:
        base_model_with_missing_values (BaseModel): The base model with missing values.
        reference_base_model (BaseModel): The reference base model.

    Returns:
        None
    """
    for field_name in base_model_with_missing_values.model_fields_set:
        if isinstance(
            getattr(base_model_with_missing_values, field_name), BaseModel
        ) and isinstance(getattr(reference_base_model, field_name), BaseModel):
            fill_missing_values_in_base_model_from_reference_base_model(
                getattr(base_model_with_missing_values, field_name),
                getattr(reference_base_model, field_name),
            )

    fields_to_assign_with_none = []
    fields_to_assign_with_previous_value = []
    # The following for loop iterates over all fields that are not present in the partial payload but are available
    # in the reference model and are available in the model that contains missing values
    for field_name in (
        reference_base_model.model_fields_set
        - base_model_with_missing_values.model_fields_set
    ).intersection(base_model_with_missing_values.model_fields):
        if field_name.endswith("Code") and not field_name.endswith("NullValueCode"):
            # both value field and null value code field not exists in the base (coming) set
            if (
                field_name.replace("Code", "") + "NullValueCode"
                not in base_model_with_missing_values.model_fields_set
            ):
                fields_to_assign_with_previous_value.append(field_name)
            # value field doesn't exist and null value field exist in the base (coming) set
            elif (
                field_name.replace("Code", "") + "NullValueCode"
                in base_model_with_missing_values.model_fields_set
            ):
                fields_to_assign_with_none.append(field_name)
        # value field doesn't exist and null value code exist in the base (coming) set but value is not code field
        elif (
            field_name + "NullValueCode"
            in base_model_with_missing_values.model_fields_set
        ):
            fields_to_assign_with_none.append(field_name)
        else:
            fields_to_assign_with_previous_value.append(field_name)
    for field_name in fields_to_assign_with_none:
        setattr(base_model_with_missing_values, field_name, None)
    for field_name in fields_to_assign_with_previous_value:
        setattr(
            base_model_with_missing_values,
            field_name,
            getattr(reference_base_model, field_name),
        )


@dataclass(frozen=True)
class FieldsDirective:
    _included_fields: AbstractSet[str]
    _excluded_fields: AbstractSet[str]
    _nested_fields_directives: Mapping[str, "FieldsDirective"]

    @classmethod
    def _from_include_and_exclude_spec_sets(
        cls, include_spec_set: AbstractSet[str], exclude_spec_set: AbstractSet[str]
    ) -> Self:
        _included_fields: set[str] = set()
        _excluded_fields: set[str] = set()
        _nested_include_specs: MutableMapping[str, set[str]] = {}
        _nested_exclude_specs: MutableMapping[str, set[str]] = {}

        for field_spec in include_spec_set - exclude_spec_set:
            dot_position_in_field_spec = field_spec.find(".")
            if dot_position_in_field_spec < 0:
                _included_fields.add(field_spec)
            else:
                spec_before_dot = field_spec[0:dot_position_in_field_spec]
                spec_after_dot = field_spec[dot_position_in_field_spec + 1 :]
                _included_fields.add(
                    spec_before_dot
                )  # directive to include subfields implicitly includes containing field as well
                if spec_before_dot not in _nested_include_specs:
                    _nested_include_specs[spec_before_dot] = set()
                _nested_include_specs[spec_before_dot].add(spec_after_dot)

        for field_spec in exclude_spec_set:
            dot_position_in_field_spec = field_spec.find(".")
            if dot_position_in_field_spec < 0:
                _excluded_fields.add(field_spec)
            else:
                spec_before_dot = field_spec[0:dot_position_in_field_spec]
                spec_after_dot = field_spec[dot_position_in_field_spec + 1 :]
                if spec_before_dot not in _nested_exclude_specs:
                    _nested_exclude_specs[spec_before_dot] = set()
                _nested_exclude_specs[spec_before_dot].add(spec_after_dot)

        _nested_fields_directives: MutableMapping[str, FieldsDirective] = {}
        for nested_field in _nested_include_specs.keys() | _nested_exclude_specs.keys():
            _nested_fields_directives[nested_field] = (
                cls._from_include_and_exclude_spec_sets(
                    include_spec_set=(
                        _nested_include_specs[nested_field]
                        if nested_field in _nested_include_specs
                        else set()
                    ),
                    exclude_spec_set=(
                        _nested_exclude_specs[nested_field]
                        if nested_field in _nested_exclude_specs
                        else set()
                    ),
                )
            )

        return cls(
            _excluded_fields=_excluded_fields,
            _included_fields=_included_fields,
            _nested_fields_directives=_nested_fields_directives,
        )

    @classmethod
    def from_fields_query_parameter(cls, fields_query_parameter: str | None) -> Self:
        if fields_query_parameter is None:
            fields_query_parameter = ""
        fields_query_parameter = "".join(
            fields_query_parameter.split()
        )  # easy way to remove all white space

        include_specs_set: set[str] = set()
        exclude_specs_set: set[str] = set()

        for field_spec in fields_query_parameter.split(","):
            if len(field_spec) < 1:
                continue
            exclude_spec = False
            if field_spec[0] == "-":
                exclude_spec = True
            if field_spec[0] == "-" or field_spec[0] == "+":
                field_spec = field_spec[1:]
            if len(field_spec) < 1:
                continue
            if exclude_spec:
                exclude_specs_set.add(field_spec)
            else:
                include_specs_set.add(field_spec)

        return cls._from_include_and_exclude_spec_sets(
            include_spec_set=include_specs_set, exclude_spec_set=exclude_specs_set
        )

    def is_field_included(self, field_path: str) -> bool:
        dot_position_in_field_path = field_path.find(".")
        if dot_position_in_field_path > 0:
            # in case of checking on child we recurse to nested field directive
            path_before_dot = field_path[0:dot_position_in_field_path]
            path_after_dot = field_path[dot_position_in_field_path + 1 :]
            if not self.is_field_included(path_before_dot):
                # if parent not included, anything below is also not included
                return False
            return self.get_fields_directive_for_children_of_field(
                path_before_dot
            ).is_field_included(path_after_dot)

        if field_path in self._excluded_fields:  # excludes takes precedence
            return False
        if len(self._included_fields) == 0:
            return (
                True  # when lacking any include spec we assume everything is included
            )
        return field_path in self._included_fields

    def get_fields_directive_for_children_of_field(self, field_path: str) -> Self:
        dot_position_in_field_path = field_path.find(".")
        if dot_position_in_field_path > 0:
            path_before_dot = field_path[0:dot_position_in_field_path]
            path_after_dot = field_path[dot_position_in_field_path + 1 :]

            ValidationException.raise_if_not(
                self.is_field_included(path_before_dot),
                msg="Cannot get fields directive for children of the field which is not included",
            )

            if path_before_dot not in self._nested_fields_directives:
                # if there's no specific we return "anything goes" directive
                return _ANYTHING_GOES_FIELDS_DIRECTIVE
            # other wise we recurse for specific directive
            return self._nested_fields_directives[
                path_before_dot
            ].get_fields_directive_for_children_of_field(path_after_dot)

        ValidationException.raise_if_not(
            self.is_field_included(field_path),
            msg="Cannot get fields directive for children of the field which is not included",
        )

        if field_path not in self._nested_fields_directives:
            # if there's no specific we return "anything goes" directive
            return _ANYTHING_GOES_FIELDS_DIRECTIVE
        # other wise we recurse for specific directive
        return self._nested_fields_directives[field_path]


_ANYTHING_GOES_FIELDS_DIRECTIVE = FieldsDirective.from_fields_query_parameter(None)

_SomeBaseModelSubtype = TypeVar("_SomeBaseModelSubtype", bound=BaseModel)


def filter_base_model_using_fields_directive(
    input_base_model: _SomeBaseModelSubtype, fields_directive: FieldsDirective
) -> _SomeBaseModelSubtype:
    args_dict_for_result_object = {}
    for field_name in input_base_model.model_fields_set:
        if fields_directive.is_field_included(field_name):
            field_value = getattr(input_base_model, field_name)
            if isinstance(field_value, BaseModel):
                field_value = filter_base_model_using_fields_directive(
                    input_base_model=field_value,
                    fields_directive=fields_directive.get_fields_directive_for_children_of_field(
                        field_name
                    ),
                )
            args_dict_for_result_object[field_name] = field_value
    return input_base_model.__class__(**args_dict_for_result_object)


def create_duration_object_from_api_input(
    value: int,
    unit: str,
    find_duration_name_by_code: Callable[[str], UnitDefinitionAR | None],
) -> str | None:
    """
    Transforms the API duration input to the ISO duration format.

    Args:
        value (int): The duration value.
        unit (str): The duration unit.
        find_duration_name_by_code (Callable[[str], UnitDefinitionAR | None]): A function that finds the duration name
            by its code.

    Returns:
        str | None: The ISO duration format, or None if the duration unit is not valid.

    Example:
        >>> create_duration_object_from_api_input(5, "Hour", find_duration_name_by_code)
        "P5H"
    """
    unit_definition_ar = find_duration_name_by_code(unit) if unit is not None else None
    if unit_definition_ar is not None:
        duration_unit = unit_definition_ar.name
        duration = f"P{str(value)}{duration_unit[0].upper()}"
        return duration
    return None


@trace_calls
def service_level_generic_filtering(
    items: list[Any],
    filter_by: dict | None = None,
    filter_operator: FilterOperator = FilterOperator.AND,
    sort_by: dict | None = None,
    total_count: bool = False,
    page_number: int = 1,
    page_size: int = 0,
) -> GenericFilteringReturn:
    """
    Filters and sorts a list of items based on the provided filter and sort criteria.

    Args:
        items (list[Any]): The list of items to filter and sort.
        filter_by (dict | None, optional): A dictionary of filter criteria.
        filter_operator (FilterOperator, optional): The operator to use when filtering elements.
        sort_by (dict | None, optional): A dictionary of sort criteria.
        total_count (bool, optional): If True, returns the total count of items.
        page_number (int, optional): The page number to retrieve.
        page_size (int, optional): The number of items to retrieve per page.

    Returns:
        GenericFilteringReturn: A named tuple containing the filtered and sorted items and the total count (if applicable).

    Example:
        >>> class Obj:
            name: str
            age: int
            def __init__(self, name: str, age: int):
                self.name = name
                self.age = age
        >>> service_level_generic_filtering(
                items=[
                    Obj(name="John", age=30),
                    Obj(name="Jane", age=25),
                    Obj(name="Doe", age=27),
                ],
                filter_by={"age": {"op": "gt", "v": ["27"]}},
                sort_by={"name": True},
                total_count=True,
            )
        GenericFilteringReturn(items=[<__main__.Obj object at 0x7f58cfc4b310>], total=1)
    """
    filtered_items = generic_item_filtering(
        items=items,
        filter_by=filter_by,
        filter_operator=filter_operator,
        sort_by=sort_by,
    )
    # Do count
    count = len(filtered_items) if total_count else 0
    # Do pagination
    filtered_items = generic_pagination(
        items=filtered_items,
        page_number=page_number,
        page_size=page_size,
    )
    return GenericFilteringReturn.create(items=filtered_items, total=count)


def generic_item_filtering(
    items: list[Any],
    filter_by: dict | None = None,
    filter_operator: FilterOperator = FilterOperator.AND,
    sort_by: dict | None = None,
) -> list[Any]:
    """
    Filters and sorts a list of items based on the provided filter and sort criteria.

    Args:
        items (list[Any]): The list of items to filter and sort.
        filter_by (dict | None, optional): A dictionary of filter criteria.
        filter_operator (FilterOperator, optional): The operator to use when filtering elements.
        sort_by (dict | None, optional): A dictionary of sort criteria.

    Returns:
        list[Any]: A list containing the filtered and sorted items.

    Example:
        >>> class Obj:
            name: str
            age: int
            def __init__(self, name: str, age: int):
                self.name = name
                self.age = age
        >>> generic_item_filtering(
                items=[
                    Obj(name="John", age=30),
                    Obj(name="Jane", age=25),
                    Obj(name="Doe", age=27),
                ],
                filter_by={"age": {"op": "gt", "v": ["27"]}},
                sort_by={"name": True},
                total_count=True,
            )
        [<__main__.Obj object at 0x7f58cfc4b310>]
    """
    if sort_by is None:
        sort_by = {}
    if filter_by is None:
        filter_by = {}
    validate_is_dict("sort_by", sort_by)
    validate_is_dict("filter_by", filter_by)

    filters = FilterDict(elements=filter_by)
    if filter_operator == FilterOperator.AND:
        # Start from full list, then only keep items that match filter elements, one by one
        filtered_items = items
        # The list will decrease after each step (aka filtering out)
        for key in filters.elements:
            _values = filters.elements[key].v
            _operator = filters.elements[key].op
            filtered_items = list(
                filter(
                    lambda x, k=key, v=_values, o=_operator: filter_aggregated_items(
                        x, k, v, o
                    ),
                    filtered_items,
                )
            )
    elif filter_operator == FilterOperator.OR:
        # Start from empty list then add element one by one
        _filtered_items = []
        # The list will increase after each step
        for key in filters.elements:
            _values = filters.elements[key].v
            _operator = filters.elements[key].op
            matching_items = list(
                filter(
                    lambda x, k=key, v=_values, o=_operator: filter_aggregated_items(
                        x, k, v, o
                    ),
                    items,
                )
            )
            _filtered_items += matching_items
        # if passed filter dict is empty we should return all elements without any filtering
        if not filters.elements:
            filtered_items = items
        else:
            # Finally, deduplicate list
            uids = set()
            filtered_items = []
            for item in _filtered_items:
                if item.uid not in uids:
                    filtered_items.append(item)
                    uids.add(item.uid)
    else:
        raise ValidationException(msg=f"Invalid filter_operator: {filter_operator}")

    # Do sorting
    distinct_sort_orders = set(list(sort_by.values()))
    # If all orders for SortKeys are the same we can order the list in a single sort function call
    if len(distinct_sort_orders) == 1:
        filtered_items.sort(
            key=lambda x: [
                (
                    elm
                    if (elm := extract_nested_key_value(x, sort_key)) is not None
                    else (
                        "-1"
                        if issubclass(extract_nested_key_type(x, sort_key), str)
                        else -1
                    )
                )
                for sort_key in sort_by.keys()
            ],
            reverse=not distinct_sort_orders.pop(),
        )
    # If orders for SortKeys are different we have to order list calling sort function a few times, once per each SortKey
    elif len(distinct_sort_orders) > 1:
        for sort_key, sort_order in sort_by.items():
            filtered_items.sort(
                key=lambda x, s=sort_key: (
                    elm
                    if (elm := extract_nested_key_value(x, s)) is not None
                    else (
                        "-1" if issubclass(extract_nested_key_type(x, s), str) else -1
                    )
                ),
                reverse=not sort_order,
            )
    return filtered_items


def generic_pagination(
    items: list[Any],
    page_number: int = 1,
    page_size: int = 0,
) -> list[Any]:
    """
    Applies pagination to a list of sorted and filtered items.

    Args:
        items (list[Any]): The list of items to filter and sort.
        page_number (int, optional): The page number to retrieve, where the first page is number 1.
        page_size (int, optional): The number of items to retrieve per page.

    Returns:
        list[Any]: A list containing the selected page of items.

    Example:
        >>> class Obj:
            name: str
            age: int
            def __init__(self, name: str, age: int):
                self.name = name
                self.age = age
        >>> generic_pagination(
                items=[
                    Obj(name="John", age=30),
                    Obj(name="Jane", age=25),
                    Obj(name="Joe", age=27),
                    Obj(name="Doe", age=23),
                ],
                page_number=2,
                page_size=2,
            )
        -> a list containing the "Joe" and "Doe" objects.
    """
    # Do pagination
    paged_items = items
    if page_size > 0:
        paged_items = paged_items[
            (page_number - 1) * page_size : page_number * page_size
        ]
    return paged_items


@trace_calls
def service_level_generic_header_filtering(
    items: list[Any],
    field_name: str,
    filter_operator: FilterOperator = FilterOperator.AND,
    search_string: str = "",
    filter_by: dict | None = None,
    page_size: int = 10,
) -> list[Any]:
    """
    Filters and returns a list of values for a specific field in a list of dictionaries.

    Args:
        items (list[Any]): The list of dictionaries to filter.
        field_name (str): The name of the field to extract values from.
        filter_operator (FilterOperator, optional): The filter operator to use (AND or OR).
        search_string (str, optional): A search string to filter by. Defaults to "".
        filter_by (dict | None, optional): A dictionary of filter elements to apply. Defaults to None.
        page_size (int, optional): The maximum number of results to return. Defaults to 10.

    Returns:
        list[Hashable]: A list of unique values extracted from the specified field.

    Raises:
        ValueError: If the filter_by parameter is not a dictionary.

    Example:
        >>> class Obj:
        ... name: str
        ... age: int
        ... def __init__(self, name: str, age: int):
        ...     self.name = name
        ...     self.age = age
        >>> service_level_generic_header_filtering(
        ...     items=[
        ...         Obj(name="John", age=30),
        ...         Obj(name="Jane", age=25),
        ...         Obj(name="Doe", age=27),
        ...     ],
        ...     field_name="name",
        ...     filter_by={"age": {"op": "gt", "v": ["26"]}},
        ... )
        ["John", "Doe"]
    """
    if filter_by is None:
        filter_by = {}
    validate_is_dict("filter_by", filter_by)

    # Add header field name to filter_by, to filter with a CONTAINS pattern
    if search_string != "":
        filter_by[field_name] = {
            "v": [search_string],
            "op": ComparisonOperator.CONTAINS,
        }
    filters = FilterDict(elements=filter_by)
    if filter_operator == FilterOperator.AND:
        # Start from full list, then only keep items that match filter elements, one by one
        filtered_items = items
        # The list will decrease after each step (aka filtering out)
        for key in filters.elements:
            _values = filters.elements[key].v
            _operator = filters.elements[key].op
            filtered_items = list(
                filter(
                    lambda x, k=key, v=_values, o=_operator: filter_aggregated_items(
                        x, k, v, o
                    ),
                    filtered_items,
                )
            )
    else:
        # Start from full list, then add items that match filter elements, one by one
        _filtered_items = []
        # The list will increase after each step
        for key in filters.elements:
            _values = filters.elements[key].v
            _operator = filters.elements[key].op
            matching_items = list(
                filter(
                    lambda x, k=key, v=_values, o=_operator: filter_aggregated_items(
                        x, k, v, o
                    ),
                    items,
                )
            )
            _filtered_items += matching_items
        filtered_items = _filtered_items

    # Return values for field_name
    extracted_values = []
    for item in filtered_items:
        extracted_value = extract_nested_key_value(item, field_name)
        # The extracted value can be
        # * A list when the property associated with key is a list of objects
        # ** (e.g. categories.name.sponsor_preferred_name for an Objective Template)
        if isinstance(extracted_value, list):
            # Merge lists
            extracted_values = extracted_values + extracted_value
        # * A single value when the property associated with key is a simple property
        # Skip if None
        elif extracted_value is not None:
            # Append element to list
            extracted_values.append(extracted_value)

    return_values = []
    # Transform into a set in order to remove duplicates, then cast back to list
    is_hashable = bool(extracted_values and isinstance(extracted_values[0], Hashable))
    for extracted_value in extracted_values:
        if is_hashable:
            value_to_return = extracted_value
        else:
            value_to_return = extracted_value.name

        if value_to_return not in return_values:
            return_values.append(value_to_return)

    # Limit results returned
    return_values = return_values[:page_size]
    return return_values


def extract_nested_key_value(term, key):
    return rgetattr(term, key)


def extract_nested_key_type(term, key):
    return rgetattr_type(term, key)


def extract_properties_for_wildcard(item, prefix: str = ""):
    output = []
    if prefix:
        prefix += "."
    # item can be None - ignore if it is
    if item:
        # We only want to extract the property keys from one of the items in the list
        if isinstance(item, list | tuple) and len(item) > 0:
            return extract_properties_for_wildcard(item[0], prefix[:-1])
        # Otherwise, let's iterate over all the attributes of the single item we have
        for attribute, attr_desc in item.model_fields.items():
            # if we have marked a field to be removed from wildcard filtering we have to continue to next row
            jse = attr_desc.json_schema_extra or {}
            if jse.get("remove_from_wildcard", False):
                continue
            # The attribute might be a non-class dictionary
            # In that case, we extract the first value and make a recursive call on it
            if (
                isinstance(getattr(item, attribute), dict)
                and len(getattr(item, attribute)) > 0
            ):
                output = output + extract_properties_for_wildcard(
                    list(getattr(item, attribute).values())[0], attribute
                )
            # An attribute can be a nested class, which will inherit from Pydantic's BaseModel
            # In that case, we do a recursive call and add the attribute key of the class as a prefix, like "nested_class."
            # Checking for isinstance of type will make sure that the attribute is a class before checking if it is a subclass
            elif isinstance(get_field_type(attr_desc.annotation), type) and issubclass(
                get_field_type(attr_desc.annotation), BaseModel
            ):
                output = output + extract_properties_for_wildcard(
                    getattr(item, attribute), prefix=prefix + attribute
                )
            # Or a "plain" attribute
            else:
                output.append(prefix + attribute)
    return output


def filter_aggregated_items(item, filter_key, filter_values, filter_operator):
    if filter_key == "*":
        # Only accept requests with default operator (set to equal by FilterDict class) or specified contains operator
        ValidationException.raise_if(
            ComparisonOperator(filter_operator) != ComparisonOperator.EQUALS
            and ComparisonOperator(filter_operator) != ComparisonOperator.CONTAINS,
            msg="Only the default 'contains' operator is supported for wildcard filtering.",
        )

        property_list = extract_properties_for_wildcard(item)
        property_list_filter_match = [
            filter_aggregated_items(
                item, _key, filter_values, ComparisonOperator.CONTAINS
            )
            for _key in property_list
        ]

        return True in property_list_filter_match

    _item_value_for_key = extract_nested_key_value(item, filter_key)

    # The property associated with the filter key can be inside a list
    # e.g., categories.name.sponsor_preferred_name for Objective Templates
    # In these cases, a list of values will be returned here
    # Filtering then becomes "if any of the values matches with the operator"
    if isinstance(_item_value_for_key, list):
        if not filter_values:
            return not _item_value_for_key
        for _val in _item_value_for_key:
            # Return true as soon as any value matches with the operator
            if apply_filter_operator(_val, filter_operator, filter_values):
                return True
        return False
    if isinstance(_item_value_for_key, Enum):
        return apply_filter_operator(
            _item_value_for_key.value, filter_operator, filter_values
        )
    return apply_filter_operator(_item_value_for_key, filter_operator, filter_values)


def apply_filter_operator(
    value, operator: ComparisonOperator, filter_values: list[Any]
) -> bool:
    """
    Applies the specified comparison operator to the given value and filter values.

    Args:
        value: The value to compare.
        operator (ComparisonOperator): The comparison operator to apply.
        filter_values (list[Any]): The filter values to compare against.

    Returns:
        bool: True if the comparison is successful, False otherwise.

    Raises:
        ValidationException: If filtering on a null value is attempted with an operator other than `equal`.
    """

    if len(filter_values) > 0:
        if ComparisonOperator(operator) == ComparisonOperator.EQUALS:
            return value in filter_values
        if ComparisonOperator(operator) == ComparisonOperator.NOT_EQUALS:
            return value not in filter_values
        if ComparisonOperator(operator) == ComparisonOperator.CONTAINS:
            return any(str(_v).lower() in str(value).lower() for _v in filter_values)
        if ComparisonOperator(operator) == ComparisonOperator.GREATER_THAN:
            return str(value) > filter_values[0]
        if ComparisonOperator(operator) == ComparisonOperator.GREATER_THAN_OR_EQUAL_TO:
            return str(value) >= filter_values[0]
        if ComparisonOperator(operator) == ComparisonOperator.LESS_THAN:
            return str(value) < filter_values[0]
        if ComparisonOperator(operator) == ComparisonOperator.LESS_THAN_OR_EQUAL_TO:
            return str(value) <= filter_values[0]
        if ComparisonOperator(operator) == ComparisonOperator.BETWEEN:
            filter_values.sort()
            return (
                filter_values[0].lower()
                <= str(value).lower()
                <= filter_values[1].lower()
            )

    ValidationException.raise_if(
        ComparisonOperator(operator) != ComparisonOperator.EQUALS,
        msg="Filtering on a null value can only be used with the 'equal' operator.",
    )
    # An empty filter_values list means that the returned item's property value should be null
    return value is None


# Recursive getattr to access properties in nested objects
def rgetattr(obj, attr):
    """
    Recursively gets an attribute of an object based on a string representation of the attribute.

    Args:
        obj: The object to get the attribute from.
        attr: The attribute to get, represented as a string.
        *args: Optional additional arguments to pass to the getattr function.

    Returns:
        list | Any | None: The value of the attribute, or None if the attribute doesn't exist.
    """

    def _getattr(obj, attr):
        if isinstance(obj, list):
            return [_getattr(element, attr) for element in obj]
        if isinstance(obj, dict):
            return [_getattr(element, attr) for element in obj.values()]
        return getattr(obj, attr, None)

    return functools.reduce(_getattr, attr.split("."), obj)


def rgetattr_type(obj, attr):
    """
    Recursively gets an attribute of an object based on a string representation of the attribute.
    When the last attribute is found it returns a type of the most inner attribute.

    Args:
        obj: The object to get the attribute from.
        attr: The attribute to get, represented as a string.
        *args: Optional additional arguments to pass to the getattr function.

    Returns:
        Type | None: The type of the attribute, or None if the attribute doesn't exist.
    """

    def _getattr(obj, attr):
        if isinstance(obj, list):
            return [_getattr(element, attr) for element in obj]
        if isinstance(obj, dict):
            return [_getattr(element, attr) for element in obj.values()]
        inner_obj = getattr(obj, attr, None)
        if not isinstance(inner_obj, BaseModel):
            prop = obj.model_fields.get(attr)
            if prop:
                return get_field_type(prop.annotation)
            ValidationException.raise_if(
                True,
                msg=f"Cannot resolve a model field for attribute {attr}",
            )
        return inner_obj

    return functools.reduce(_getattr, attr.split("."), obj)


@trace_calls
def process_complex_parameters(parameters, parameter_repository):
    return_parameters = []
    for _, item in enumerate(parameters):
        item_terms = []
        if item["definition"] is not None:
            param_names = extract_parameters(item["template"])
            params = []
            for param_name in param_names:
                param_term_list = []
                if param_name != "NumericValue":
                    param = parameter_repository.get_parameter_including_terms(
                        param_name
                    )
                    if param is not None:
                        for val in param["terms"]:
                            if val["uid"] is not None:
                                tpt = TemplateParameterTerm(
                                    name=val["name"], uid=val["uid"], type=val["type"]
                                )
                                param_term_list.append(tpt)
                template_parameter = TemplateParameter(
                    name=param_name, terms=param_term_list
                )
                params.append(template_parameter)
            return_parameters.append(
                ComplexTemplateParameter(
                    name=item["name"], format=item["template"], parameters=params
                )
            )
        else:
            for term in item["terms"]:
                if term["uid"] is not None:
                    tpt = TemplateParameterTerm(
                        name=term["name"], uid=term["uid"], type=term["type"]
                    )
                    item_terms.append(tpt)
            return_parameters.append(
                TemplateParameter(name=item["name"], terms=item_terms)
            )
    return return_parameters


@trace_calls
def calculate_diffs_history(
    get_all_object_versions: Callable,
    transform_all_to_history_model: Callable,
    study_uid: str,
    version_object_class,
):
    selection_history = get_all_object_versions(study_uid=study_uid)
    unique_list_uids = list({x.uid for x in selection_history})
    unique_list_uids.sort(reverse=True)
    # list of all study_elements
    data = []
    ith_selection_history = []
    for i_unique in unique_list_uids:
        ith_selection_history = []
        # gather the selection history of the i_unique Uid
        for selection in selection_history:
            if selection.uid == i_unique:
                ith_selection_history.append(selection)
        ith_selection_history.sort(
            key=lambda ith_selection: ith_selection.start_date,
            reverse=True,
        )

        versions = []
        for item in ith_selection_history:
            _study_visit_count = {}
            if hasattr(item, "study_visit_count"):
                _study_visit_count = {"study_visit_count": item.study_visit_count}
            versions.append(
                transform_all_to_history_model(item, **_study_visit_count).dict()
            )

        if not data:
            data = calculate_diffs(versions, version_object_class)
        else:
            data.extend(calculate_diffs(versions, version_object_class))
    return data


def validate_is_dict(object_label, value):
    ValidationException.raise_if_not(
        isinstance(value, dict),
        msg=f"`{object_label}: {value}` is not a valid dictionary",
    )


def extract_filtering_values(filters, parameter_name, single_value=False):
    """
    If the parameter_name is in the filters, with the default "eq" operator,
    extract the value(s) and remove the parameter from the filters.
    If single_value is True, check that there is only one value, and return it.
    """
    if filters:
        ValidationException.raise_if_not(
            isinstance(filters, dict), msg="Invalid filters, must be a dict"
        )
        if parameter_name in filters:
            operator = filters[parameter_name].get(
                "op", ComparisonOperator.EQUALS.value
            )
            if operator == ComparisonOperator.EQUALS.value:
                values = filters[parameter_name]["v"]
                if single_value and len(values) > 1:
                    return None
                if values:
                    values = values[0]
                del filters[parameter_name]
                return values
    return None


def build_simple_filters(
    _vo_to_ar_filter_map: dict, filter_by: dict | None, sort_by: dict | None
) -> dict | None:
    if (
        filter_by is None
        or all(key in _vo_to_ar_filter_map.keys() for key in filter_by.keys())
    ) and (
        sort_by is None
        or all(key in _vo_to_ar_filter_map.keys() for key in sort_by.keys())
    ):
        if filter_by is not None:
            simple_filter_by = {
                _vo_to_ar_filter_map[key]: value for key, value in filter_by.items()
            }
        else:
            simple_filter_by = None
        if sort_by is not None:
            simple_sort_by = {
                _vo_to_ar_filter_map[key]: value for key, value in sort_by.items()
            }
        else:
            simple_sort_by = None
        return {"filter_by": simple_filter_by, "sort_by": simple_sort_by}
    return None


class AggregatedTransactionProxy(neomodel.sync_.core.TransactionProxy):
    """context manager to manage database transaction if there is no active transaction in progress, else do nothing"""

    __manage_transaction = None

    def __enter__(self):
        self.__manage_transaction = (
            getattr(self.db, "_active_transaction", None) is None
        )
        if self.__manage_transaction:
            return super().__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.__manage_transaction:
            super().__exit__(exc_type, exc_value, traceback)


def ensure_transaction(db: neomodel.sync_.core.Database) -> Callable:
    """decorator to ensure a database transaction: starts a new transaction if not already in an active transaction"""
    return AggregatedTransactionProxy(db)
