import inspect
import json

import pytest

from common.exceptions import ValidationException
from standards_import.repositories import staging_repository
from standards_import.services.staging_service import (
    flatten_links,
    parse_package,
    validate_flat_properties,
)


def package_document(**overrides):
    document = {
        "name": "SDTM CT 2024-09-27",
        "effectiveDate": "2024-09-27",
        "label": "SDTM Controlled Terminology Package 50",
        "registrationStatus": "Final",
        "source": "CDISC",
        "version": "2024-09-27",
        "_links": {
            "self": {
                "href": "/mdr/ct/packages/sdtmct-2024-09-27",
                "type": "Terminology",
            },
            "priorVersion": {"href": "/mdr/ct/packages/sdtmct-2024-06-28"},
        },
        "codelists": [
            {
                "conceptId": "C66742",
                "name": "No Yes Response",
                "definition": "A response.",
                "preferredTerm": "No Yes Response",
                "submissionValue": "NY",
                "extensible": "false",
                "synonyms": ["NY"],
                "terms": [
                    {
                        "conceptId": "C49488",
                        "definition": "Yes.",
                        "preferredTerm": "Yes",
                        "submissionValue": "Y",
                    }
                ],
            }
        ],
    }
    document.update(overrides)
    return json.dumps(document).encode()


def test_parse_package_derives_catalogue_and_uid():
    package = parse_package(package_document())

    assert package["package_name"] == "SDTM CT 2024-09-27"
    assert package["catalogue"] == "SDTM CT"
    assert package["effective_date"] == "2024-09-27"
    assert package["uid"] == "SDTM__CT__2024-09-27"


def test_parse_package_upper_cases_inconsistently_cased_names():
    package = parse_package(
        package_document(
            name="ADaM CT 2020-06-26",
            effectiveDate="2020-06-26",
            version="2020-06-26",
        )
    )

    assert package["package_name"] == "ADAM CT 2020-06-26"
    assert package["catalogue"] == "ADAM CT"


def test_parse_package_flattens_links_onto_the_catalogue():
    package = parse_package(package_document())

    assert (
        package["package_props"]["_links.self.href"]
        == "/mdr/ct/packages/sdtmct-2024-09-27"
    )
    assert (
        package["package_props"]["_links.priorVersion.href"]
        == "/mdr/ct/packages/sdtmct-2024-06-28"
    )
    assert "_links" not in package["package_props"]


def test_parse_package_separates_terms_from_their_codelist():
    package = parse_package(package_document())

    assert "terms" not in package["codelists"][0]
    assert package["term_rows"] == [
        {
            "codelist_id": "C66742",
            "term": {
                "conceptId": "C49488",
                "definition": "Yes.",
                "preferredTerm": "Yes",
                "submissionValue": "Y",
            },
        }
    ]


def test_parse_package_keeps_codelists_without_terms():
    document = json.loads(package_document())
    del document["codelists"][0]["terms"]

    package = parse_package(json.dumps(document).encode())

    assert len(package["codelists"]) == 1
    assert not package["term_rows"]


def test_parse_package_rejects_a_name_that_disagrees_with_the_effective_date():
    with pytest.raises(ValidationException, match="disagrees with the effective date"):
        parse_package(package_document(effectiveDate="2024-06-28"))


def test_parse_package_rejects_a_name_without_a_trailing_date():
    with pytest.raises(
        ValidationException, match="does not end with its effective date"
    ):
        parse_package(package_document(name="SDTM CT"))


def test_parse_package_rejects_an_unparseable_effective_date():
    with pytest.raises(ValidationException, match="not a YYYY-MM-DD date"):
        parse_package(
            package_document(name="SDTM CT 2024-13-45", effectiveDate="2024-13-45")
        )


@pytest.mark.parametrize("missing", ["name", "effectiveDate", "codelists"])
def test_parse_package_rejects_a_document_missing_a_required_key(missing):
    document = json.loads(package_document())
    del document[missing]

    with pytest.raises(ValidationException, match=f"has no `{missing}`"):
        parse_package(json.dumps(document).encode())


def test_parse_package_rejects_invalid_json():
    with pytest.raises(ValidationException, match="not valid JSON"):
        parse_package(b"{not json")


def test_parse_package_rejects_a_top_level_list():
    with pytest.raises(ValidationException, match="package object at the top level"):
        parse_package(b"[]")


def test_parse_package_rejects_a_codelist_without_a_concept_id():
    document = json.loads(package_document())
    del document["codelists"][0]["conceptId"]

    with pytest.raises(ValidationException, match="has no `conceptId`"):
        parse_package(json.dumps(document).encode())


def test_parse_package_rejects_a_nested_codelist_property():
    document = json.loads(package_document())
    document["codelists"][0]["_links"] = {"self": {"href": "/x"}}

    with pytest.raises(ValidationException, match="is a nested value"):
        parse_package(json.dumps(document).encode())


def test_flatten_links_tolerates_a_document_without_links():
    document = {"name": "SDTM CT 2024-09-27"}

    flatten_links(document)

    assert document == {"name": "SDTM CT 2024-09-27"}


def test_validate_flat_properties_accepts_scalars_lists_and_nulls():
    validate_flat_properties(
        {"a": "text", "b": 1, "c": 1.5, "d": True, "e": None, "f": ["x", "y"]},
        "term C1",
    )


def test_validate_flat_properties_rejects_a_list_of_objects():
    with pytest.raises(ValidationException, match="`f` of term C1 is a nested value"):
        validate_flat_properties({"f": [{"x": 1}]}, "term C1")


def test_the_release_summary_counts_workbooks_not_pairing_rows():
    """`pairing_files` is documented as workbooks uploaded.

    Counting `StagedPairing` nodes reports the rows inside them instead — three
    workbooks read as ~700. Both the list and the single-release query feed the same
    summary, so both have to count distinct source files.
    """

    for query in (
        inspect.getsource(staging_repository.get_effective_dates),
        inspect.getsource(staging_repository.find_effective_date),
    ):
        assert "RETURN DISTINCT p.source_file" in query
        assert "AS pairing_files" in query
        assert ":StagedPairing) } AS" not in query
