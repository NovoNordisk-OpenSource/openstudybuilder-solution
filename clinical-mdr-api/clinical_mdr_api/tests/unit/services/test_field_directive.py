import pytest
from pydantic import BaseModel

from clinical_mdr_api.services._utils import (
    FieldsDirective,
    filter_base_model_using_fields_directive,
)


@pytest.mark.parametrize(
    "query_param, field_path, expected_should_include",
    [
        ("", "whatever_field", True),
        ("", "whatever.nested.field", True),
        (None, "whatever_field", True),
        (None, "whatever.nested.field", True),
        ("f1, +f2", "f1", True),
        ("f1, +f2", "f2", True),
        ("f1, +f2", "f3", False),
        ("f1, +f2", "f1.any.nested.field", True),
        ("f1, +f2", "f2.any.nested.field", True),
        ("f1, +f2", "f3.any.nested.field", False),
        ("f1, +f2, -f2.excluded_nested", "f2.any.nested.field", True),
        ("f1, +f2, -f2.excluded_nested", "f2.excluded_nested", False),
        ("f1, +f2, -f2.nested.excluded", "f2.nested.non_excluded", True),
        ("f1, +f2, -f2.nested.excluded", "f2.nested.excluded", False),
        (
            "very.specific.deeply.nested.field, another.very.specific.deeply.nested.field",
            "something.else",
            False,
        ),
        (
            "very.specific.deeply.nested.field, another.very.specific.deeply.nested.field",
            "very.specific.deeply.nested.field",
            True,
        ),
        (
            "very.specific.deeply.nested.field, another.very.specific.deeply.nested.field",
            "another.very.specific.deeply.nested.field",
            True,
        ),
    ],
)
def test__field_directive__is_field_included__results(
    query_param: str | None, field_path: str, expected_should_include: bool
):
    # given
    field_directive: FieldsDirective = FieldsDirective.from_fields_query_parameter(
        query_param
    )

    # when
    should_include = field_directive.is_field_included(field_path)

    # then
    assert should_include == expected_should_include


@pytest.mark.parametrize("query_param", ["f1, f2", "f1, -f1.nested", "f3.nested", None])
@pytest.mark.parametrize("before_dot_part", ["f1", "f2", "f3", "f5678"])
@pytest.mark.parametrize("after_dot_part", ["f1", "f2", "f3", "f5678", "nested"])
def test__field_directive__is_field_included_and_get_fields_directive_for_children_of_field__consistent_results(
    query_param: str | None, before_dot_part: str, after_dot_part: str
):
    # given
    field_directive: FieldsDirective = FieldsDirective.from_fields_query_parameter(
        query_param
    )
    nested_field_path = f"{before_dot_part}.{after_dot_part}"

    # when
    should_include_result = field_directive.is_field_included(nested_field_path)
    should_include_by_nesting_result = field_directive.is_field_included(
        before_dot_part
    ) and (
        field_directive.get_fields_directive_for_children_of_field(
            before_dot_part
        ).is_field_included(after_dot_part)
    )

    # then
    assert should_include_by_nesting_result == should_include_result


class ChildBaseModel(BaseModel):
    child_field: str | None = None


class ParentBaseModel(BaseModel):
    parent_field: str | None = None
    child: ChildBaseModel | None = None


@pytest.mark.parametrize(
    "given_parent_field, given_child_field, query_fields_param",
    [
        ("parent Field Value", "child Field Value", None),
        ("parent Field Value", "child Field Value", "parent_field"),
        ("parent Field Value", "child Field Value", "child"),
        ("parent Field Value", "child Field Value", "child, -child.child_field"),
        ("parent Field Value", "child Field Value", "-child"),
    ],
)
def test__filter_base_model_using_fields_directive__consistency_with_directive(
    given_parent_field: str | None,
    given_child_field: str | None,
    query_fields_param: str | None,
):
    # given
    field_directive: FieldsDirective = FieldsDirective.from_fields_query_parameter(
        query_fields_param
    )
    given_base_model = ParentBaseModel(
        parent_field=given_parent_field,
        child=ChildBaseModel(child_field=given_child_field),
    )

    # when
    resulting_base_model = filter_base_model_using_fields_directive(
        given_base_model, field_directive
    )

    # then
    if field_directive.is_field_included("parent_field"):
        assert vars(resulting_base_model).get("parent_field") is not None
    else:
        assert vars(resulting_base_model).get("parent_field") is None

    if field_directive.is_field_included("child"):
        assert vars(resulting_base_model).get("child") is not None
        assert field_directive.is_field_included("child.child_field") == (
            "child_field" in resulting_base_model.child.model_fields_set
        )
    else:
        assert vars(resulting_base_model).get("child") is None
