import pytest

from clinical_mdr_api.domains.libraries.object import ParametrizedTemplateVO
from clinical_mdr_api.domains.libraries.parameter_term import (
    ParameterTermEntryVO,
    SimpleParameterTermVO,
)
from clinical_mdr_api.domains.syntax_templates.template import TemplateVO
from clinical_mdr_api.domains.syntax_templates.timeframe_template import (
    TimeframeTemplateAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.services.user_info import UserInfoService
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID
from common.exceptions import BusinessLogicException


def _parameter_term(parameter_name: str, *values: str) -> ParameterTermEntryVO:
    return ParameterTermEntryVO(
        parameters=[
            SimpleParameterTermVO(uid=f"uid-{value}", value=value, labels=[])
            for value in values
        ],
        conjunction="and",
        parameter_name=parameter_name,
        labels=[],
    )


def _parametrized_template(
    template_name: str,
    parameter_terms: list[ParameterTermEntryVO],
    template_parameter_names: list[str] | None = None,
) -> ParametrizedTemplateVO:
    return ParametrizedTemplateVO(
        template_name=template_name,
        template_uid="template-uid",
        template_sequence_id=None,
        guidance_text=None,
        parameter_terms=parameter_terms,
        library_name="Sponsor",
        template_parameter_names=template_parameter_names,
    )


@pytest.mark.parametrize(
    "template_name, parameter_terms, expected_name, expected_name_plain",
    [
        pytest.param(
            "<p>Assess [Activity] [see note]</p>",
            [_parameter_term("Activity", "aspirin")],
            "<p>Assess [aspirin] &#91;see note&#93;</p>",
            "Assess aspirin [see note]",
            id="literal text is escaped",
        ),
        pytest.param(
            "<p>[a [Activity] b]</p>",
            [_parameter_term("Activity", "aspirin")],
            "<p>&#91;a [aspirin] b&#93;</p>",
            "[a aspirin b]",
            id="literal around a placeholder",
        ),
        pytest.param(
            "<p>[Activity] then [Activity]</p>",
            [
                _parameter_term("Activity", "aspirin"),
                _parameter_term("Activity", "placebo"),
            ],
            "<p>[Aspirin] then [placebo]</p>",
            "Aspirin then placebo",
            id="duplicate placeholders are filled in order",
        ),
        pytest.param(
            "<p>Take [Activity]</p>",
            [_parameter_term("Activity", "dose [mg]")],
            "<p>Take [dose &#91;mg&#93;]</p>",
            "Take dose [mg]",
            id="brackets in values are escaped",
        ),
        pytest.param(
            "<p>Take [Activity] and [Activity]</p>",
            [
                _parameter_term("Activity", "Activity"),
                _parameter_term("Activity", "placebo"),
            ],
            "<p>Take [Activity] and [placebo]</p>",
            "Take Activity and placebo",
            id="value equal to a parameter name",
        ),
    ],
)
def test__parametrized_template__name(
    template_name: str,
    parameter_terms: list[ParameterTermEntryVO],
    expected_name: str,
    expected_name_plain: str,
):
    template = _parametrized_template(template_name, parameter_terms)

    assert template.expanded_template_value == expected_name
    assert template.expanded_plain_template_value == expected_name_plain


def test__parametrized_template__literal_first__not_capitalized():
    template = _parametrized_template(
        "[optional] take [Activity]", [_parameter_term("Activity", "aspirin")]
    )

    assert template.expanded_template_value == "&#91;optional&#93; take [aspirin]"


def test__parametrized_template__uses_template_parameter_names():
    # Parameter terms created from input may carry the name of a child parameter.
    template = _parametrized_template(
        "Take [Intervention] [see note]",
        [_parameter_term("Compound", "aspirin")],
        template_parameter_names=["Intervention"],
    )

    assert template.expanded_template_value == "Take [aspirin] &#91;see note&#93;"


@pytest.fixture(autouse=True)
def _no_author_lookup(monkeypatch):
    # Item metadata resolves the author's username from the database
    monkeypatch.setattr(
        UserInfoService, "get_author_username_from_id", lambda author_id: author_id
    )


def _approved_template(template_name: str, parameter_names: list[str]):
    ar = TimeframeTemplateAR.from_repository_values(
        template=TemplateVO.from_repository_values(
            template_name=template_name,
            template_name_plain=template_name,
            linked_parameter_names=parameter_names,
        ),
        uid="some-uid",
        sequence_id="some-sequence_id",
        library=LibraryVO.from_repository_values(
            library_name="Library", is_editable=True
        ),
        item_metadata=LibraryItemMetadataVO.get_initial_item_metadata(
            author_id="who ever"
        ),
    )
    ar.approve(author_id=AUTHOR_ID)
    return ar


def _new_template(template_name: str, existing_parameter_names: set[str]):
    return TemplateVO.from_input_values_2(
        template_name=template_name,
        parameter_name_exists_callback=existing_parameter_names.__contains__,
    )


@pytest.mark.parametrize(
    "new_template_name",
    [
        pytest.param("[Activity] see [Note]", id="unchanged name"),
        pytest.param("[Activity], see [Note]", id="reworded"),
    ],
)
def test__create_new_version__literal_matching_new_parameter__stays_literal(
    new_template_name: str,
):
    # [Note] was stored as literal text; a Note parameter has been created since
    ar = _approved_template("[Activity] see [Note]", ["Activity"])

    ar.create_new_version(
        author_id=AUTHOR_ID,
        change_description="New version",
        template=_new_template(new_template_name, {"Activity", "Note"}),
    )

    assert ar.template_value.parameter_names == ["Activity"]
    assert ar.name == new_template_name


def test__edit_draft__literal_matching_new_parameter__stays_literal():
    ar = _approved_template("[Activity] see [Note]", ["Activity"])
    ar.create_new_version(
        author_id=AUTHOR_ID,
        change_description="New version",
        template=_new_template("[Activity] see [Note]", {"Activity", "Note"}),
    )

    ar.edit_draft(
        author_id=AUTHOR_ID,
        change_description="Fix typo",
        template=_new_template("[Activity], see [Note]", {"Activity", "Note"}),
    )

    assert ar.template_value.parameter_names == ["Activity"]
    assert ar.name == "[Activity], see [Note]"


def test__edit_draft__unapproved__literal_matching_new_parameter__becomes_parameter():
    # Before approval there are no instances, so the text is resolved afresh
    ar = TimeframeTemplateAR.from_repository_values(
        template=TemplateVO.from_repository_values(
            template_name="[Activity] see [Note]",
            template_name_plain="[Activity] see [Note]",
            linked_parameter_names=["Activity"],
        ),
        uid="some-uid",
        sequence_id="some-sequence_id",
        library=LibraryVO.from_repository_values(
            library_name="Library", is_editable=True
        ),
        item_metadata=LibraryItemMetadataVO.get_initial_item_metadata(
            author_id="who ever"
        ),
    )

    ar.edit_draft(
        author_id=AUTHOR_ID,
        change_description="Fix typo",
        template=_new_template("[Activity], see [Note]", {"Activity", "Note"}),
    )

    assert ar.template_value.parameter_names == ["Activity", "Note"]


@pytest.mark.parametrize(
    "new_template_name",
    [
        pytest.param("[Activity] see note [Visit]", id="added parameter"),
        pytest.param("see note", id="removed parameter"),
        pytest.param("[Visit] see note", id="replaced parameter"),
    ],
)
def test__create_new_version__changed_parameters__failure(new_template_name: str):
    ar = _approved_template("[Activity] see note", ["Activity"])

    with pytest.raises(
        BusinessLogicException, match="template parameters cannot be modified"
    ):
        ar.create_new_version(
            author_id=AUTHOR_ID,
            change_description="New version",
            template=_new_template(new_template_name, {"Activity", "Visit"}),
        )


def test__edit_draft__approved__added_parameter__failure():
    ar = _approved_template("[Activity] see note", ["Activity"])
    ar.create_new_version(
        author_id=AUTHOR_ID,
        change_description="New version",
        template=_new_template("[Activity] see note", {"Activity", "Note"}),
    )

    with pytest.raises(
        BusinessLogicException, match="template parameters cannot be modified"
    ):
        ar.edit_draft(
            author_id=AUTHOR_ID,
            change_description="Add parameter",
            template=_new_template("[Activity] see [Note]", {"Activity", "Note"}),
        )


def test__create_new_version__literal_kept__success():
    ar = _approved_template("[Activity] see [note]", ["Activity"])

    ar.create_new_version(
        author_id=AUTHOR_ID,
        change_description="Fix typo",
        template=_new_template("[Activity], see [note]", {"Activity"}),
    )

    assert ar.template_value.parameter_names == ["Activity"]
    assert ar.name == "[Activity], see [note]"
