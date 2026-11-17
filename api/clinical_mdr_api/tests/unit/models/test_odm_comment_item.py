import pytest
from pydantic import ValidationError

from clinical_mdr_api.models.odms.item import OdmItemPatchInput, OdmItemPostInput

PATCH_DEFAULTS = {
    "change_description": "change",
    "name": "item",
    "oid": "I.1",
    "datatype_uid": None,
    "prompt": None,
    "length": None,
    "significant_digits": None,
    "sas_field_name": None,
    "sds_var_name": None,
    "origin": None,
    "comment": None,
    "external_question": None,
    "codelist": None,
    "terms": [],
    "vendor_elements": [],
    "vendor_element_attributes": [],
    "vendor_attributes": [],
}


def post_input(**properties):
    return OdmItemPostInput(name="item", oid="I.1", **properties)


def patch_input(**properties):
    return OdmItemPatchInput(**{**PATCH_DEFAULTS, **properties})


@pytest.mark.parametrize("build", [post_input, patch_input])
def test_comment_item_without_other_properties_is_accepted(build):
    build()


@pytest.mark.parametrize("build", [post_input, patch_input])
def test_comment_item_may_have_translated_texts_aliases_and_vendor_extensions(build):
    build(
        translated_texts=[
            {"text_type": "Description", "language": "eng", "text": "text"}
        ],
        aliases=[{"context": "context", "name": "alias"}],
        vendor_elements=[],
    )


@pytest.mark.parametrize("build", [post_input, patch_input])
def test_item_with_data_type_may_have_any_properties(build):
    build(datatype_uid="string_uid", prompt="prompt", length=0, origin="origin")


@pytest.mark.parametrize("build", [post_input, patch_input])
@pytest.mark.parametrize(
    "property_name, property_value",
    [
        ("prompt", "prompt"),
        ("length", 0),
        ("sas_field_name", "sas"),
        ("comment", "comment"),
        ("origin", "origin"),
    ],
)
def test_comment_item_with_other_properties_is_rejected(
    build, property_name, property_value
):
    with pytest.raises(ValidationError) as exc_info:
        build(**{property_name: property_value})

    assert f"Remove: {property_name}." in str(exc_info.value)


def test_error_message_lists_all_offending_properties():
    with pytest.raises(ValidationError) as exc_info:
        post_input(prompt="prompt", length=5)

    msg = str(exc_info.value)
    assert "no data type" in msg
    assert (
        "only 'oid', 'name', translations, aliases and vendor extensions can be set"
        in msg
    )
    assert "Remove: prompt, length." in msg
