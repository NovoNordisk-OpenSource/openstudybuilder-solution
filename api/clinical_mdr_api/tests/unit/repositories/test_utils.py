from typing import Any

from clinical_mdr_api.domain_repositories.biomedical_concepts.activity_item_class_repository import (
    ActivityItemClassRepository,
)
from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityItemClass,
)
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
)
from clinical_mdr_api.repositories._utils import CypherQueryBuilder, FilterDict


def _build_filter_clause(
    filter_key: str,
    return_model: Any = ActivityItemClass,
    value: Any = "some value",
) -> str:
    builder = CypherQueryBuilder(
        match_clause="MATCH (concept_root)",
        alias_clause="concept_root AS concept_root",
        return_model=return_model,
        filter_by=FilterDict(elements={filter_key: {"v": [value], "op": "eq"}}),
    )
    return builder.filter_clause


def _build_wildcard_filter_clause(
    wildcard_properties_list: list[str], value: str = "some value"
) -> str:
    builder = CypherQueryBuilder(
        match_clause="MATCH (concept_root)",
        alias_clause="concept_root AS concept_root",
        wildcard_properties_list=wildcard_properties_list,
        filter_by=FilterDict(elements={"*": {"v": [value], "op": "co"}}),
    )
    return builder.filter_clause


def _build_filter_clause_multi(elements: dict[str, Any]) -> str:
    builder = CypherQueryBuilder(
        match_clause="MATCH (concept_root)",
        alias_clause="concept_root AS concept_root",
        return_model=ActivityItemClass,
        filter_by=FilterDict(elements=elements),
    )
    return builder.filter_clause


class TestHandleNestedBaseModelFiltering:
    """Regression coverage for the path-prefix bug in
    CypherQueryBuilder._handle_nested_base_model_filtering: a filter/sort key
    with 3+ dot-segments (e.g. non_standard_variable.origin_type.name) used to
    lose every intermediate segment but the last, producing `origin_type.name`
    instead of `non_standard_variable.origin_type.name` in the Cypher predicate.
    """

    def test_two_level_nested_key_keeps_its_path(self):
        filter_clause = _build_filter_clause("role.name")
        assert "toLower(role.name)=$role_name_0" in filter_clause

    def test_three_level_nested_key_keeps_its_full_path(self):
        filter_clause = _build_filter_clause("non_standard_variable.origin_type.name")
        assert (
            "toLower(non_standard_variable.origin_type.name)"
            "=$non_standard_variable_origin_type_name_0" in filter_clause
        )
        # the regression produced a predicate rooted at the wrong alias:
        assert "toLower(origin_type.name)" not in filter_clause


class TestBetweenOperatorGrouping:
    """Regression coverage: a BETWEEN filter on a date-like field appends an
    ungrouped `OR <datetime-cast predicate>` to its own comparison. Joined with
    a sibling filter key via the default AND operator, that stray OR takes over
    operator precedence and the sibling filter is effectively dropped for any
    row matching the datetime-cast half alone.
    """

    def test_between_date_predicate_is_grouped_before_joining_with_other_keys(self):
        filter_clause = _build_filter_clause_multi(
            {
                "status": {"v": ["Final"], "op": "eq"},
                "start_date": {"v": ["2020-01-01", "2030-01-01"], "op": "bw"},
            }
        )
        # the OR introduced by the datetime cast must be parenthesized so it
        # binds to the BETWEEN comparison alone, not to the whole AND-joined clause
        assert (
            "AND ($start_date_0<=start_date<=$start_date_1"
            " OR datetime($start_date_0)<=start_date<=datetime($start_date_1))"
            in filter_clause
        )


class TestNestedFilteringOnUnresolvableProperty:
    """Regression coverage for nested filter keys whose last segment does not exist
    on the return model. The unit definitions alias clause exposes its CT term maps
    keyed `name`, while SimpleCodelistTermModel names that field `term_name`, so
    `unit_subsets.name` / `unit_dimension.name` resolve to None on the model. That
    used to select the non-string branch and drop toLower(), while the query
    parameter was still lowercased — so filtering the Units table on any value that
    was not already lowercase returned an empty list.
    """

    def test_unresolvable_property_on_list_field_is_lowercased(self):
        filter_clause = _build_filter_clause(
            "unit_subsets.name", return_model=UnitDefinitionModel
        )
        assert (
            "any(attr in unit_subsets WHERE toLower(attr.name) = $unit_subsets_name_0)"
            in filter_clause
        )

    def test_unresolvable_property_on_single_field_is_lowercased(self):
        filter_clause = _build_filter_clause(
            "unit_dimension.name", return_model=UnitDefinitionModel
        )
        assert "toLower(unit_dimension.name)=$unit_dimension_name_0" in filter_clause

    def test_unresolvable_property_with_non_string_value_is_not_lowercased(self):
        # toLower() on a boolean is a Cypher type error, and a boolean value is never
        # lowercased when bound, so an unresolvable property must follow the value.
        filter_clause = _build_filter_clause(
            "unit_dimension.name", return_model=UnitDefinitionModel, value=True
        )
        assert "unit_dimension.name=$unit_dimension_name_0" in filter_clause
        assert "toLower" not in filter_clause

    def test_resolvable_non_string_property_is_not_lowercased(self):
        filter_clause = _build_filter_clause(
            "unit_subsets.order", return_model=UnitDefinitionModel
        )
        assert (
            "any(attr in unit_subsets WHERE attr.order = $unit_subsets_order_0)"
            in filter_clause
        )
        assert "toLower" not in filter_clause


class TestWildcardFilteringOnManualPropertyList:
    """Regression coverage: the manual `wildcard_properties_list` loop used to emit
    `toLower(db_property)` unconditionally. For a non-string property (e.g. the NSV
    table's `non_standard_variable.length`, an int) that is a Cypher type error, since
    toLower() only accepts a string. Wrapping in toString() first fixes the numeric
    case and is a no-op for the already-string properties in every other repository's
    wildcard_properties_list.
    """

    def test_string_property_is_still_lowercased_via_tostring(self):
        filter_clause = _build_wildcard_filter_clause(["name"])
        assert "toLower(toString(name)) CONTAINS $wildcard_0" in filter_clause

    def test_numeric_property_is_wrapped_in_tostring_before_lowering(self):
        filter_clause = _build_wildcard_filter_clause(["non_standard_variable.length"])
        assert (
            "toLower(toString(non_standard_variable.length)) CONTAINS $wildcard_0"
            in filter_clause
        )

    def test_activity_item_class_wildcard_list_covers_the_five_nsv_columns(self):
        # The bug report: origin_type, algorithm, length, origin_source, and
        # derivation_rule were missing from general (wildcard) search on the NSV table.
        wildcard_list = ActivityItemClassRepository.wildcard_properties_list
        assert "non_standard_variable.origin_type.name" in wildcard_list
        assert "non_standard_variable.algorithm" in wildcard_list
        assert "non_standard_variable.length" in wildcard_list
        assert "non_standard_variable.origin_source.name" in wildcard_list
        assert "non_standard_variable.derivation_rule" in wildcard_list
