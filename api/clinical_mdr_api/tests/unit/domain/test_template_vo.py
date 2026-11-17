import pytest
from hypothesis import given
from hypothesis.strategies import composite, from_regex, lists

from clinical_mdr_api.domains.syntax_templates.template import TemplateVO


@composite
def valid_template_with_list_of_parameter_names(draw):
    parameter_list = draw(lists(from_regex(r"\A[\w\s]+\Z"), min_size=1))
    static_fragments_list = draw(
        lists(
            from_regex(r"\A[^][]*\Z"),
            min_size=1 + len(parameter_list),
            max_size=1 + len(parameter_list),
        )
    )
    template_string = ""
    for param_pos, param in enumerate(parameter_list):
        template_string += static_fragments_list[param_pos] + "[" + param + "]"
    template_string += static_fragments_list[len(parameter_list)]
    return template_string, parameter_list


@composite
def template_string_with_valid_syntax(draw):
    return draw(valid_template_with_list_of_parameter_names())[0]


@given(template_and_parameter_list=valid_template_with_list_of_parameter_names())
def test__template_vo_from_input_values__success(
    template_and_parameter_list: tuple[str, list[str]],
):
    # event(f"template_string={template_string}")
    template_string = template_and_parameter_list[0]
    parameter_list = template_and_parameter_list[1]
    # when
    template_vo = TemplateVO.from_input_values_2(
        template_name=template_string, parameter_name_exists_callback=lambda _: True
    )

    # then
    assert template_vo.name == template_string
    assert tuple(template_vo.parameter_names) == tuple(parameter_list)


@given(template_string=template_string_with_valid_syntax())
def test__template_vo_from_input_values__unknown_parameters__literal_text(
    template_string: str,
):
    # when
    template_vo = TemplateVO.from_input_values_2(
        template_name=template_string,
        parameter_name_exists_callback=lambda _: False,
    )

    # then
    assert template_vo.name == template_string
    assert not template_vo.parameter_names


@pytest.mark.parametrize(
    "template_name, expected_parameter_names",
    [
        pytest.param("See [note] for [Activity]", ["Activity"], id="literal text"),
        pytest.param("[a [Activity] b]", ["Activity"], id="nested literal"),
        pytest.param("x ] [Activity] [", ["Activity"], id="unbalanced literal"),
        pytest.param("x [] [Activity]", ["Activity"], id="empty literal"),
        pytest.param(
            "[Activity] and [Activity]", ["Activity", "Activity"], id="duplicates"
        ),
    ],
)
def test__template_vo_from_input_values__literal_brackets(
    template_name: str, expected_parameter_names: list[str]
):
    # when
    template_vo = TemplateVO.from_input_values_2(
        template_name=template_name,
        parameter_name_exists_callback={"Activity"}.__contains__,
    )

    # then
    assert template_vo.parameter_names == expected_parameter_names


def test__template_vo_from_repository_values__resolves_against_linked_parameters():
    # when
    template_vo = TemplateVO.from_repository_values(
        template_name="[Activity] [Note]",
        template_name_plain="[Activity] [Note]",
        linked_parameter_names=["Activity"],
    )

    # then
    assert template_vo.parameter_names == ["Activity"]
