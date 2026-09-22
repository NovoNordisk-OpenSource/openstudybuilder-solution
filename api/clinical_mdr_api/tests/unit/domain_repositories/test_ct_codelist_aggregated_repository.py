"""
Unit tests for CT Codelist Aggregated Repository utility functions
"""

import pytest

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_get_all_query_utils import (
    format_codelist_filter_sort_keys,
    format_codelist_term_filter_sort_keys,
)
from clinical_mdr_api.repositories._utils import escape_lucene_special_chars
from common.exceptions import ValidationException


class TestEscapeLuceneSpecialChars:
    """Tests for the escape_lucene_special_chars utility function"""

    def test_escape_square_brackets(self):
        """Test that square brackets are escaped"""
        assert escape_lucene_special_chars("[test]") == "\\[test\\]"
        assert escape_lucene_special_chars("a[b]c") == "a\\[b\\]c"

    def test_escape_curly_braces(self):
        """Test that curly braces are escaped"""
        assert escape_lucene_special_chars("{test}") == "\\{test\\}"
        assert escape_lucene_special_chars("a{b}c") == "a\\{b\\}c"

    def test_escape_parentheses(self):
        """Test that parentheses are escaped"""
        assert escape_lucene_special_chars("(test)") == "\\(test\\)"
        assert escape_lucene_special_chars("a(b)c") == "a\\(b\\)c"

    def test_escape_plus_minus(self):
        """Test that plus and minus signs are escaped"""
        assert escape_lucene_special_chars("+test") == "\\+test"
        assert escape_lucene_special_chars("-test") == "\\-test"
        assert escape_lucene_special_chars("a+b-c") == "a\\+b\\-c"

    def test_escape_exclamation(self):
        """Test that exclamation marks are escaped"""
        assert escape_lucene_special_chars("!test") == "\\!test"

    def test_escape_colon(self):
        """Test that colons are escaped"""
        assert escape_lucene_special_chars("field:value") == "field\\:value"

    def test_escape_tilde(self):
        """Test that tildes are escaped"""
        assert escape_lucene_special_chars("test~2") == "test\\~2"

    def test_escape_caret(self):
        """Test that carets are escaped"""
        assert escape_lucene_special_chars("test^2") == "test\\^2"

    def test_escape_quotes(self):
        """Test that double quotes are escaped"""
        assert escape_lucene_special_chars('"exact phrase"') == '\\"exact phrase\\"'

    def test_escape_asterisk_question(self):
        """Test that wildcards are escaped"""
        assert escape_lucene_special_chars("test*") == "test\\*"
        assert escape_lucene_special_chars("test?") == "test\\?"

    def test_escape_backslash(self):
        """Test that backslashes are escaped"""
        assert escape_lucene_special_chars("test\\value") == "test\\\\value"

    def test_escape_slash(self):
        """Test that forward slashes are escaped"""
        assert escape_lucene_special_chars("test/value") == "test\\/value"

    def test_escape_ampersand(self):
        """Test that ampersands are escaped (for && operator)"""
        assert escape_lucene_special_chars("a&b") == "a\\&b"
        assert escape_lucene_special_chars("a&&b") == "a\\&\\&b"

    def test_escape_pipe(self):
        """Test that pipes are escaped (for || operator)"""
        assert escape_lucene_special_chars("a|b") == "a\\|b"
        assert escape_lucene_special_chars("a||b") == "a\\|\\|b"

    def test_escape_multiple_special_chars(self):
        """Test escaping multiple special characters in one string"""
        input_str = "[test]{value}(group)+required-prohibited"
        expected = "\\[test\\]\\{value\\}\\(group\\)\\+required\\-prohibited"
        assert escape_lucene_special_chars(input_str) == expected

    def test_escape_empty_string(self):
        """Test that empty strings are handled"""
        assert escape_lucene_special_chars("") == ""

    def test_escape_no_special_chars(self):
        """Test that strings without special chars are unchanged"""
        assert escape_lucene_special_chars("simple text") == "simple text"
        assert escape_lucene_special_chars("ABC123") == "ABC123"

    def test_escape_preserves_normal_chars(self):
        """Test that normal characters are preserved"""
        assert escape_lucene_special_chars("Test Value 123") == "Test Value 123"
        assert (
            escape_lucene_special_chars("alpha-numeric_text") == "alpha\\-numeric_text"
        )

    def test_realistic_search_strings(self):
        """Test realistic search strings that might contain special chars"""
        # Email-like pattern
        assert escape_lucene_special_chars("user@domain.com") == "user@domain.com"

        # Version string
        assert escape_lucene_special_chars("v1.2.3") == "v1.2.3"

        # Chemical formula (often contains brackets and plus/minus)
        assert escape_lucene_special_chars("Ca[2+]") == "Ca\\[2\\+\\]"

        # Query with range brackets
        assert escape_lucene_special_chars("[A TO Z]") == "\\[A TO Z\\]"


class TestFormatCodelistFilterSortKeysPairedCodelist:
    """
    Tests for the paired_codelist.* branch of format_codelist_filter_sort_keys.

    Regression tests for the bug where sorting/filtering the CT Codelists table by
    its "Paired with" column (key `paired_codelist.name`) raised an error, because
    the key had no mapping to the `paired_codelist_name`/`paired_codelist_uid`
    Cypher aliases exposed by CTCodelistAggregatedRepository.generic_final_alias_clause.
    """

    def test_paired_codelist_uid_maps_to_flat_alias(self):
        assert (
            format_codelist_filter_sort_keys("paired_codelist.uid")
            == "paired_codelist_uid"
        )

    def test_paired_codelist_name_maps_to_flat_alias(self):
        assert (
            format_codelist_filter_sort_keys("paired_codelist.name")
            == "paired_codelist_name"
        )

    def test_paired_codelist_invalid_suffix_raises(self):
        with pytest.raises(ValidationException):
            format_codelist_filter_sort_keys("paired_codelist.unknown")


class TestFormatCodelistTermFilterSortKeys:
    """
    GET /ct/codelists/{uid}/terms aliases columns 1:1 with the response model
    and has no `value_node` variable. Regression for the 500 (Neo4j "Variable
    `value_node` not defined") caused by mapping `submission_value` through
    format_codelist_filter_sort_keys.
    """

    def test_submission_value_stays_as_alias(self):
        assert (
            format_codelist_term_filter_sort_keys("submission_value")
            == "submission_value"
        )

    def test_does_not_use_value_node(self):
        for key in (
            "submission_value",
            "definition",
            "nci_preferred_name",
            "sponsor_preferred_name",
            "start_date",
        ):
            mapped = format_codelist_term_filter_sort_keys(key)
            assert "value_node" not in mapped, key
            assert mapped == key

    @pytest.mark.parametrize(
        "key",
        [
            "term_uid",
            "submission_value",
            "definition",
            "concept_id",
            "nci_preferred_name",
            "sponsor_preferred_name",
            "library_name",
            "order",
            "name_status",
            "attributes_status",
        ],
    )
    def test_simple_keys_stay_flat_aliases(self, key):
        """
        Every simple filter/sort key exposed by GET /ct/codelists/{uid}/terms
        must round-trip unchanged: the query aliases columns 1:1 with the
        response model and does not expose `value_node` or `rel_data`
        Cypher variables.
        """
        mapped = format_codelist_term_filter_sort_keys(key)
        assert mapped == key
        assert "value_node" not in mapped
        assert "rel_data" not in mapped

    def test_nested_ts_fields_map_to_flat_aliases(self):
        assert (
            format_codelist_term_filter_sort_keys("semantic_data_type.uid")
            == "semantic_data_type_uid"
        )
        assert (
            format_codelist_term_filter_sort_keys(
                "response_codelist.sponsor_preferred_name"
            )
            == "response_codelist_name"
        )

    def test_invalid_key_raises(self):
        with pytest.raises(ValidationException):
            format_codelist_term_filter_sort_keys("not a valid key!")


class TestFormatCodelistFilterSortKeysSimple:
    """
    GET /ct/codelists projects `value_node_name` / `value_node_attributes` /
    `rel_data_name` (not a bare `value_node`), so filter/sort keys on the
    aggregated listing must map onto those nested aliases rather than the
    flat aliases used by the terms listing.
    """

    @pytest.mark.parametrize("key", ["codelist_uid", "library_name"])
    def test_root_level_keys_stay_aliases(self, key):
        assert format_codelist_filter_sort_keys(key) == key

    @pytest.mark.parametrize(
        "key,expected",
        [
            ("submission_value", "value_node.submission_value"),
            ("definition", "value_node.definition"),
            ("name", "value_node.name"),
        ],
    )
    def test_unprefixed_value_node_keys(self, key, expected):
        assert format_codelist_filter_sort_keys(key) == expected

    def test_nci_preferred_name_maps_to_preferred_term(self):
        assert (
            format_codelist_filter_sort_keys("nci_preferred_name")
            == "value_node.preferred_term"
        )

    @pytest.mark.parametrize(
        "key,expected",
        [
            ("name.name", "value_node_name.name"),
            ("name.status", "rel_data_name.status"),
            ("attributes.submission_value", "value_node_attributes.submission_value"),
            ("attributes.definition", "value_node_attributes.definition"),
            (
                "attributes.nci_preferred_name",
                "value_node_attributes.preferred_term",
            ),
        ],
    )
    def test_nested_name_and_attributes_keys(self, key, expected):
        assert format_codelist_filter_sort_keys(key) == expected
