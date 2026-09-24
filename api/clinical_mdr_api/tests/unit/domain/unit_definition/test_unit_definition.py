from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Self

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis.strategies import (
    booleans,
    composite,
    datetimes,
    floats,
    integers,
    just,
    lists,
    none,
    one_of,
    sampled_from,
    tuples,
)

from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    CONCENTRATION_UNIT_DIMENSION_VALUE,
    CTTerm,
    UnitDefinitionAR,
    UnitDefinitionValueVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import (
    AUTHOR_ID,
    AUTHOR_USERNAME,
    random_str,
)
from clinical_mdr_api.tests.utils.common_strategies import (
    strings_with_at_least_one_non_space_char,
    stripped_non_empty_strings,
)

# noinspection PyProtectedMember
from clinical_mdr_api.utils import normalize_string
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    ValidationException,
)


@composite
def item_metadata(draw):
    _item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
        author_id=AUTHOR_ID,
    ).new_draft_version(
        author_id=draw(strings_with_at_least_one_non_space_char()),
        change_description=draw(strings_with_at_least_one_non_space_char()),
    )

    status = draw(sampled_from(LibraryItemStatus))
    author_id = _item_metadata.author_id
    author_username = AUTHOR_USERNAME
    change_description = _item_metadata.change_description
    major_version, minor_version = draw(
        tuples(integers(min_value=0), integers(min_value=0)).filter(
            lambda t: t[0] > 0 or t[1] > 0
        )
    )
    start_date, end_date = draw(
        tuples(
            datetimes(max_value=datetime.now()),
            one_of(none(), datetimes(max_value=datetime.now())),
        )
        .map(lambda t: (t[1], t[0]) if t[1] is not None and t[1] < t[0] else t)
        .filter(lambda t: t[0] != t[1])
    )

    return LibraryItemMetadataVO.from_repository_values(
        status=status,
        author_id=author_id,
        author_username=author_username,
        change_description=change_description,
        major_version=major_version,
        minor_version=minor_version,
        start_date=start_date,
        end_date=end_date,
    )


@dataclass
class VO:
    name: str


class CTTermNameAR:
    _uid: str
    _term_vo: VO

    def __init__(self, name):
        self._uid = name
        self._term_vo = VO(name=name)

    @property
    def uid(self):
        return self._uid

    @property
    def name(self):
        return self.ct_term_vo.name

    @property
    def ct_term_vo(self):
        return self._term_vo


@dataclass(frozen=True)
class CTSimpleCodelistTermVO:
    """
    The CTSimpleCodelistTermVO acts as the value object for a single CT simple codelist term
    """

    term_uid: str
    term_name: str
    submission_value: str
    order: int | None
    codelist_uid: str | None
    codelist_name: str | None
    codelist_submission_value: str | None


@dataclass
class CTSimpleCodelistTermAR:
    _ct_simple_codelist_term_vo: CTSimpleCodelistTermVO

    @property
    def ct_simple_codelist_term_vo(self) -> CTSimpleCodelistTermVO:
        return self._ct_simple_codelist_term_vo

    @classmethod
    def from_repository_values(
        cls,
        ct_simple_codelist_term_vo: CTSimpleCodelistTermVO,
    ) -> Self:
        ct_simple_codelist_term_ar = cls(
            _ct_simple_codelist_term_vo=ct_simple_codelist_term_vo,
        )
        return ct_simple_codelist_term_ar


def get_mock_ct_item(name):
    return CTTermNameAR(name=name)


class DictionaryTermAR:
    _uid: str
    _dictionary_term_vo: VO

    def __init__(self, name):
        self._uid = name
        self._dictionary_term_vo = VO(name=name)

    @property
    def uid(self):
        return self._uid

    @property
    def name(self):
        return self.dictionary_term_vo.name

    @property
    def dictionary_term_vo(self):
        return self._dictionary_term_vo


def get_mock_dictionary_item(name):
    return DictionaryTermAR(name=name)


@composite
def unit_definition_values(draw, valid_unit_ct_uid_set: list[str] | None = None):
    master_unit = draw(booleans())
    conversion_factor_to_master = (
        draw(one_of(none(), floats(allow_nan=False))) if not master_unit else 1.0
    )
    unit_dimension = draw(
        one_of(
            none(),
            just(CONCENTRATION_UNIT_DIMENSION_VALUE),
            stripped_non_empty_strings(),
        )
    )
    ct_units = draw(
        lists(
            stripped_non_empty_strings()
            if valid_unit_ct_uid_set is None
            else sampled_from(valid_unit_ct_uid_set)
        )
    )
    unit_subsets = draw(lists(stripped_non_empty_strings()))
    return UnitDefinitionValueVO.from_input_values(
        name=random_str(),
        ct_units=ct_units,
        unit_subsets=unit_subsets,
        convertible_unit=draw(booleans()),
        display_unit=draw(booleans()),
        master_unit=master_unit,
        si_unit=draw(booleans()),
        us_conventional_unit=draw(booleans()),
        use_complex_unit_conversion=draw(booleans()),
        legacy_code=draw(one_of(none(), stripped_non_empty_strings())),
        use_molecular_weight=False,
        conversion_factor_to_master=conversion_factor_to_master,
        unit_ct_uid_exists_callback=lambda _: True,
        unit_dimension_uid=unit_dimension,
        ucum_uid=draw(one_of(none(), stripped_non_empty_strings())),
        order=draw(integers(1, 20)),
        comment=draw(one_of(none(), stripped_non_empty_strings())),
        definition=draw(one_of(none(), stripped_non_empty_strings())),
        ucum_uid_exists_callback=lambda _: True,
        find_term_by_uid=lambda _: get_mock_ct_item(unit_dimension),
        is_template_parameter=False,
    )


@composite
def libraries(
    draw,
    *,
    valid_library_names_set: list[str] | None = None,
    editable: bool | None = None,
):
    return LibraryVO.from_input_values_2(
        library_name=(
            draw(strings_with_at_least_one_non_space_char())
            if valid_library_names_set is None
            else sampled_from(valid_library_names_set)
        ),
        is_library_editable_callback=(
            lambda _: draw(booleans()) if editable is None else editable
        ),
    )


@composite
def draft_unit_definitions(
    draw,
    *,
    valid_unit_ct_uid_set: list[str] | None = None,
    valid_library_names_set: list[str] | None = None,
):
    result = UnitDefinitionAR.from_input_values(
        unit_definition_value=draw(
            unit_definition_values(valid_unit_ct_uid_set=valid_unit_ct_uid_set)
        ),
        library=draw(
            libraries(editable=True, valid_library_names_set=valid_library_names_set)
        ),
        author_id=draw(strings_with_at_least_one_non_space_char()),
        uid_supplier=lambda: draw(stripped_non_empty_strings()),
        concept_exists_by_callback=lambda x, y, z: False,
        master_unit_exists_for_dimension_predicate=lambda _: False,
        unit_definition_exists_by_legacy_code=lambda _: False,
    )
    return result


@composite
def final_unit_definitions(
    draw,
    *,
    valid_unit_ct_uid_set: list[str] | None = None,
    valid_library_names_set: list[str] | None = None,
):
    result: UnitDefinitionAR = draw(
        draft_unit_definitions(
            valid_unit_ct_uid_set=valid_unit_ct_uid_set,
            valid_library_names_set=valid_library_names_set,
        )
    )
    result.approve(
        author_id=draw(stripped_non_empty_strings()),
        change_description=draw(stripped_non_empty_strings()),
    )
    return result


@composite
def retired_unit_definitions(
    draw,
    *,
    valid_unit_ct_uid_set: list[str] | None = None,
    valid_library_names_set: list[str] | None = None,
):
    result: UnitDefinitionAR = draw(
        final_unit_definitions(
            valid_unit_ct_uid_set=valid_unit_ct_uid_set,
            valid_library_names_set=valid_library_names_set,
        )
    )
    result.inactivate(
        author_id=draw(stripped_non_empty_strings()),
        change_description=draw(stripped_non_empty_strings()),
    )
    return result


@composite
def unit_definitions(
    draw,
    *,
    valid_unit_ct_uid_set: list[str] | None = None,
    valid_library_names_set: list[str] | None = None,
):
    return draw(
        one_of(
            draft_unit_definitions(
                valid_unit_ct_uid_set=valid_unit_ct_uid_set,
                valid_library_names_set=valid_library_names_set,
            ),
            final_unit_definitions(
                valid_unit_ct_uid_set=valid_unit_ct_uid_set,
                valid_library_names_set=valid_library_names_set,
            ),
            retired_unit_definitions(
                valid_unit_ct_uid_set=valid_unit_ct_uid_set,
                valid_library_names_set=valid_library_names_set,
            ),
        )
    )


@given(
    name=stripped_non_empty_strings(),
    ct_units=lists(stripped_non_empty_strings()),
    unit_subsets=lists(stripped_non_empty_strings()),
    convertible_unit=booleans(),
    display_unit=booleans(),
    master_unit=booleans(),
    si_unit=booleans(),
    us_conventional_unit=booleans(),
    use_complex_unit_conversion=booleans(),
    legacy_code=one_of(none(), stripped_non_empty_strings()),
    unit_dimension=one_of(none(), stripped_non_empty_strings()),
    use_molecular_weight=booleans(),
    conversion_factor_to_master=one_of(none(), floats(allow_nan=False)),
    ucum_uid=one_of(none(), stripped_non_empty_strings()),
    definition=one_of(none(), stripped_non_empty_strings()),
    order=integers(0, 20),
    comment=one_of(none(), stripped_non_empty_strings()),
)
def test__unit_definition_value_vo__from_repository__existing_unit_ct_id__success(
    name: str,
    ct_units: list[Any],
    unit_subsets: list[Any],
    convertible_unit: bool,
    display_unit: bool,
    master_unit: bool,
    si_unit: bool,
    us_conventional_unit: bool,
    use_complex_unit_conversion: bool,
    unit_dimension: str | None,
    legacy_code: str | None,
    use_molecular_weight: bool | None,
    conversion_factor_to_master: float | None,
    ucum_uid: str | None,
    definition: str | None,
    order: int,
    comment: str | None,
):
    # when
    unit_definition_value = UnitDefinitionValueVO.from_repository_values(
        name=name,
        si_unit=si_unit,
        ct_units=ct_units,
        unit_subsets=unit_subsets,
        display_unit=display_unit,
        master_unit=master_unit,
        conversion_factor_to_master=conversion_factor_to_master,
        us_conventional_unit=us_conventional_unit,
        use_complex_unit_conversion=use_complex_unit_conversion,
        legacy_code=legacy_code,
        use_molecular_weight=use_molecular_weight,
        convertible_unit=convertible_unit,
        unit_dimension_uid=unit_dimension,
        ucum_uid=ucum_uid,
        definition=definition,
        comment=comment,
        order=order,
        ucum_name=None,
        unit_dimension_name=None,
        is_template_parameter=False,
    )

    # then
    assert unit_definition_value.si_unit == si_unit
    assert unit_definition_value.ct_units == ct_units
    assert unit_definition_value.unit_subsets == unit_subsets
    assert unit_definition_value.display_unit == display_unit
    assert unit_definition_value.legacy_code == legacy_code
    assert unit_definition_value.name == name
    assert unit_definition_value.convertible_unit == convertible_unit
    assert unit_definition_value.use_molecular_weight == use_molecular_weight
    assert unit_definition_value.us_conventional_unit == us_conventional_unit
    assert (
        unit_definition_value.use_complex_unit_conversion == use_complex_unit_conversion
    )
    assert (
        unit_definition_value.conversion_factor_to_master == conversion_factor_to_master
    )
    assert unit_definition_value.master_unit == master_unit
    assert unit_definition_value.unit_dimension_uid == unit_dimension
    assert unit_definition_value.ucum_uid == ucum_uid
    assert unit_definition_value.definition == definition
    assert unit_definition_value.comment == comment
    assert unit_definition_value.order == order


@given(
    name=strings_with_at_least_one_non_space_char(),
    ct_units=lists(stripped_non_empty_strings()),
    unit_subsets=lists(stripped_non_empty_strings()),
    convertible_unit=booleans(),
    display_unit=booleans(),
    master_unit=booleans(),
    si_unit=booleans(),
    us_conventional_unit=booleans(),
    use_complex_unit_conversion=booleans(),
    legacy_code=one_of(none(), stripped_non_empty_strings()),
    unit_dimension=one_of(none(), stripped_non_empty_strings()),
    use_molecular_weight=booleans(),
    conversion_factor_to_master=one_of(none(), floats(allow_nan=False)),
    ucum_uid=one_of(none(), stripped_non_empty_strings()),
    definition=one_of(none(), stripped_non_empty_strings()),
    order=integers(0, 20),
    comment=one_of(none(), stripped_non_empty_strings()),
)
def test__unit_definition_value_vo__from_input__existing_unit_ct_id__success(
    name: str,
    ct_units: list[Any],
    unit_subsets: list[Any],
    convertible_unit: bool,
    display_unit: bool,
    master_unit: bool,
    si_unit: bool,
    us_conventional_unit: bool,
    use_complex_unit_conversion: bool,
    unit_dimension: str | None,
    legacy_code: str | None,
    use_molecular_weight: bool | None,
    conversion_factor_to_master: float | None,
    ucum_uid: str | None,
    definition: str | None,
    order: int,
    comment: str | None,
):
    # assumptions
    conversion_factor_to_master = (
        conversion_factor_to_master if not master_unit else 1.0
    )
    # when
    unit_definition_value = UnitDefinitionValueVO.from_input_values(
        name=name,
        si_unit=si_unit,
        ct_units=ct_units,
        unit_subsets=unit_subsets,
        display_unit=display_unit,
        master_unit=master_unit,
        conversion_factor_to_master=conversion_factor_to_master,
        us_conventional_unit=us_conventional_unit,
        use_complex_unit_conversion=use_complex_unit_conversion,
        legacy_code=legacy_code,
        use_molecular_weight=use_molecular_weight,
        unit_dimension_uid=unit_dimension,
        convertible_unit=convertible_unit,
        unit_ct_uid_exists_callback=lambda _: True,
        ucum_uid=ucum_uid,
        definition=definition,
        order=order,
        comment=comment,
        ucum_uid_exists_callback=lambda _: True,
        find_term_by_uid=lambda _: get_mock_ct_item(unit_dimension),
        is_template_parameter=False,
    )

    # then
    assert unit_definition_value == UnitDefinitionValueVO.from_repository_values(
        name=name.strip(),
        si_unit=si_unit,
        ct_units=[CTTerm(uid=ct_unit, name=None) for ct_unit in ct_units],
        unit_subsets=[
            CTTerm(uid=unit_subset, name=None) for unit_subset in unit_subsets
        ],
        display_unit=display_unit,
        master_unit=master_unit,
        conversion_factor_to_master=conversion_factor_to_master,
        us_conventional_unit=us_conventional_unit,
        use_complex_unit_conversion=use_complex_unit_conversion,
        legacy_code=normalize_string(legacy_code),
        use_molecular_weight=use_molecular_weight,
        convertible_unit=convertible_unit,
        unit_dimension_uid=normalize_string(unit_dimension),
        ucum_uid=ucum_uid,
        definition=definition,
        order=order,
        comment=comment,
        ucum_name=None,
        unit_dimension_name=None,
        is_template_parameter=False,
    )


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    name=strings_with_at_least_one_non_space_char(),
    ct_units=lists(stripped_non_empty_strings(), min_size=1),
    unit_subsets=lists(stripped_non_empty_strings()),
    convertible_unit=booleans(),
    display_unit=booleans(),
    master_unit=booleans(),
    si_unit=booleans(),
    us_conventional_unit=booleans(),
    use_complex_unit_conversion=booleans(),
    legacy_code=one_of(none(), stripped_non_empty_strings()),
    unit_dimension=one_of(none(), stripped_non_empty_strings()),
    use_molecular_weight=booleans(),
    conversion_factor_to_master=one_of(none(), floats(allow_nan=False)),
    ucum_uid=one_of(none(), stripped_non_empty_strings()),
    definition=one_of(none(), stripped_non_empty_strings()),
    order=integers(0, 20),
    comment=one_of(none(), stripped_non_empty_strings()),
)
def test__unit_definition_value_vo__from_input__non_existent_unit_ct_id__failure(
    name: str,
    ct_units: list[Any],
    unit_subsets: list[Any],
    convertible_unit: bool,
    display_unit: bool,
    master_unit: bool,
    si_unit: bool,
    us_conventional_unit: bool,
    use_complex_unit_conversion: bool,
    unit_dimension: str | None,
    legacy_code: str | None,
    use_molecular_weight: bool | None,
    conversion_factor_to_master: float | None,
    ucum_uid: str | None,
    definition: str | None,
    order: int,
    comment: str | None,
):
    # then
    with pytest.raises(ValidationException):
        # when
        UnitDefinitionValueVO.from_input_values(
            name=name,
            si_unit=si_unit,
            ct_units=ct_units,
            unit_subsets=unit_subsets,
            display_unit=display_unit,
            master_unit=master_unit,
            conversion_factor_to_master=conversion_factor_to_master,
            us_conventional_unit=us_conventional_unit,
            use_complex_unit_conversion=use_complex_unit_conversion,
            legacy_code=legacy_code,
            use_molecular_weight=use_molecular_weight,
            unit_dimension_uid=unit_dimension,
            convertible_unit=convertible_unit,
            unit_ct_uid_exists_callback=lambda _: False,
            ucum_uid=ucum_uid,
            definition=definition,
            order=order,
            comment=comment,
            ucum_uid_exists_callback=lambda _: True,
            find_term_by_uid=lambda _: get_mock_ct_item(unit_dimension),
            is_template_parameter=False,
        )


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    unit_definition_value=unit_definition_values(),
    library=libraries().filter(lambda _: _.is_editable),
    author_id=strings_with_at_least_one_non_space_char(),
    uid=one_of(
        none(), strings_with_at_least_one_non_space_char().map(lambda _: _.strip())
    ),
    master_unit_uid=one_of(none(), stripped_non_empty_strings()),
)
def test__unit_definition_ar__from_input_values__success(
    unit_definition_value: UnitDefinitionValueVO,
    library: LibraryVO,
    author_id: str,
    uid: str,
    master_unit_uid: str | None,
):
    # given
    if unit_definition_value.master_unit:
        master_unit_uid = None

    assume(master_unit_uid is None or master_unit_uid != uid)

    # pylint: disable=unreachable
    # when
    unit_definition_ar = UnitDefinitionAR.from_input_values(
        library=library,
        author_id=author_id,
        uid_supplier=lambda: uid,
        unit_definition_value=unit_definition_value,
        concept_exists_by_callback=lambda x, y, z: y != unit_definition_value.name,
        master_unit_exists_for_dimension_predicate=lambda _: _
        != unit_definition_value.unit_dimension_uid,
        unit_definition_exists_by_legacy_code=lambda _: _
        != unit_definition_value.legacy_code,
    )

    # then
    assert unit_definition_ar.uid == uid
    assert unit_definition_ar.name == unit_definition_value.name
    assert unit_definition_ar.library == library
    assert unit_definition_ar.concept_vo == unit_definition_value
    assert unit_definition_ar.item_metadata.author_id == author_id


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    unit_definition_value=unit_definition_values().filter(
        lambda _: _.master_unit and _.unit_dimension_uid is not None
    ),
    library=libraries().filter(lambda _: _.is_editable),
    author_id=strings_with_at_least_one_non_space_char(),
    uid=one_of(
        none(), strings_with_at_least_one_non_space_char().map(lambda _: _.strip())
    ),
)
def test__unit_definition_ar__from_input_values_another_master_unit__failure(
    unit_definition_value: UnitDefinitionValueVO,
    library: LibraryVO,
    author_id: str,
    uid: str,
):
    # then
    with pytest.raises(BusinessLogicException):
        # when
        UnitDefinitionAR.from_input_values(
            library=library,
            author_id=author_id,
            uid_supplier=lambda: uid,
            unit_definition_value=unit_definition_value,
            concept_exists_by_callback=lambda x, y, z: False,
            master_unit_exists_for_dimension_predicate=lambda _: _
            == unit_definition_value.unit_dimension_uid,
            unit_definition_exists_by_legacy_code=lambda _: False,
        )


@settings(suppress_health_check=(HealthCheck.too_slow,))
@given(
    unit_definition_value=unit_definition_values(),
    library=libraries(),  # no matter, either editable or not this should fail
    author_id=strings_with_at_least_one_non_space_char(),
    uid=one_of(none(), stripped_non_empty_strings()),
)
def test__unit_definition_ar__from_input_values__non_unique_name__failure(
    unit_definition_value: UnitDefinitionValueVO,
    library: LibraryVO,
    author_id: str,
    uid: str,
):
    # then
    with pytest.raises(AlreadyExistsException):
        # when
        UnitDefinitionAR.from_input_values(
            library=library,
            author_id=author_id,
            uid_supplier=lambda: uid,
            unit_definition_value=unit_definition_value,
            concept_exists_by_callback=lambda x, y, z: y == unit_definition_value.name,
            master_unit_exists_for_dimension_predicate=lambda _: False,
            unit_definition_exists_by_legacy_code=lambda _: False,
        )


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    unit_definition_value=unit_definition_values(),
    library=libraries(),  # no matter, either editable or not this should fail
    author_id=strings_with_at_least_one_non_space_char(),
    uid=one_of(none(), stripped_non_empty_strings()),
)
def test__unit_definition_ar__from_input_values__non_unique_legacy_code__failure(
    unit_definition_value: UnitDefinitionValueVO,
    library: LibraryVO,
    author_id: str,
    uid: str,
):
    assume(unit_definition_value.legacy_code is not None)
    # then
    with pytest.raises(AlreadyExistsException):  # pylint: disable=unreachable
        # when
        UnitDefinitionAR.from_input_values(
            library=library,
            author_id=author_id,
            uid_supplier=lambda: uid,
            unit_definition_value=unit_definition_value,
            concept_exists_by_callback=lambda x, y, z: False,
            master_unit_exists_for_dimension_predicate=lambda _: False,
            unit_definition_exists_by_legacy_code=lambda _: _
            == unit_definition_value.legacy_code,
        )


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    unit_definition_value=unit_definition_values(),
)
def test__unit_definition_ar__from_input_values__non_unique_unit_ct_uid__failure(
    unit_definition_value: UnitDefinitionValueVO,
):
    for unit_ct_uid in unit_definition_value.ct_units:
        assume(unit_ct_uid is not None)


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    unit_definition_value=unit_definition_values(),
    library=libraries().filter(lambda _: not _.is_editable),
    author_id=strings_with_at_least_one_non_space_char(),
    uid=one_of(none(), stripped_non_empty_strings()),
)
def test__unit_definition_ar__from_input_values__non_editable_library__failure(
    unit_definition_value: UnitDefinitionValueVO,
    library: LibraryVO,
    author_id: str,
    uid: str,
):
    # then
    with pytest.raises(BusinessLogicException):
        # when
        UnitDefinitionAR.from_input_values(
            library=library,
            author_id=author_id,
            uid_supplier=lambda: uid,
            unit_definition_value=unit_definition_value,
            concept_exists_by_callback=lambda x, y, z: False,
            master_unit_exists_for_dimension_predicate=lambda _: False,
            unit_definition_exists_by_legacy_code=lambda _: False,
        )


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    unit_definition_value=unit_definition_values(),
    library=libraries(),
    uid=stripped_non_empty_strings(),
    an_item_metadata=item_metadata(),
)
def test__unit_definition_ar__from_repository_values__result(
    unit_definition_value: UnitDefinitionValueVO,
    library: LibraryVO,
    uid: str,
    an_item_metadata: LibraryItemMetadataVO,
):
    # when
    unit_definition_ar = UnitDefinitionAR.from_repository_values(
        unit_definition_value=unit_definition_value,
        library=library,
        uid=uid,
        item_metadata=an_item_metadata,
    )

    # then
    assert unit_definition_ar.concept_vo == unit_definition_value
    assert unit_definition_ar.name == unit_definition_value.name
    assert unit_definition_ar.uid == uid
    assert unit_definition_ar.item_metadata == an_item_metadata
    assert unit_definition_ar.library == library


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    unit_definition_ar=draft_unit_definitions(),
    new_unit_definition_value=unit_definition_values(),
    change_description=stripped_non_empty_strings(),
    author_id=stripped_non_empty_strings(),
)
def test__unit_definition_ar__edit_draft__result(
    unit_definition_ar: UnitDefinitionAR,
    new_unit_definition_value: UnitDefinitionValueVO,
    change_description: str,
    author_id: str,
):
    new_unit_definition_value = UnitDefinitionValueVO.from_repository_values(
        name=new_unit_definition_value.name,
        # we cannot change unit_ct_uid if it's already assigned in existing aggregate (logic forbids that)
        ct_units=(
            unit_definition_ar.concept_vo.ct_units
            if unit_definition_ar.concept_vo.ct_units is not None
            else new_unit_definition_value.ct_units
        ),
        unit_subsets=new_unit_definition_value.unit_subsets,
        convertible_unit=new_unit_definition_value.convertible_unit,
        display_unit=new_unit_definition_value.display_unit,
        master_unit=new_unit_definition_value.master_unit,
        si_unit=new_unit_definition_value.si_unit,
        us_conventional_unit=new_unit_definition_value.us_conventional_unit,
        use_complex_unit_conversion=new_unit_definition_value.use_complex_unit_conversion,
        unit_dimension_uid=new_unit_definition_value.unit_dimension_uid,
        legacy_code=new_unit_definition_value.legacy_code,
        use_molecular_weight=new_unit_definition_value.use_molecular_weight,
        conversion_factor_to_master=new_unit_definition_value.conversion_factor_to_master,
        ucum_uid=new_unit_definition_value.ucum_uid,
        definition=new_unit_definition_value.definition,
        order=new_unit_definition_value.order,
        comment=new_unit_definition_value.comment,
        ucum_name=None,
        unit_dimension_name=None,
        is_template_parameter=False,
    )

    # when
    library = unit_definition_ar.library
    datetime_before = datetime.now(timezone.utc)

    unit_definition_ar.edit_draft(
        new_unit_definition_value=new_unit_definition_value,
        change_description=change_description,
        author_id=author_id,
        concept_exists_by_callback=lambda x, y, z: y != new_unit_definition_value.name
        or y == unit_definition_ar.name,
        master_unit_exists_for_dimension_predicate=(
            lambda _: (
                True
                if (
                    unit_definition_ar.concept_vo.master_unit
                    and unit_definition_ar.concept_vo.unit_dimension_uid
                    == new_unit_definition_value.unit_dimension_uid
                )
                else _ != new_unit_definition_value.unit_dimension_uid
            )
        ),
        unit_definition_exists_by_legacy_code=lambda _: _
        == unit_definition_ar.concept_vo.legacy_code
        or _ != new_unit_definition_value.legacy_code,
    )

    datetime_after = datetime.now(timezone.utc)

    # then
    assert unit_definition_ar.concept_vo == new_unit_definition_value
    assert unit_definition_ar.item_metadata.status == LibraryItemStatus.DRAFT
    assert unit_definition_ar.item_metadata.start_date >= datetime_before
    assert unit_definition_ar.item_metadata.start_date <= datetime_after
    assert unit_definition_ar.item_metadata.end_date is None
    assert unit_definition_ar.item_metadata.author_id == author_id
    assert unit_definition_ar.item_metadata.change_description == change_description
    assert unit_definition_ar.library == library


@settings(
    max_examples=int(max(10, settings.default.max_examples / 10)),
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
@given(
    unit_definition_ar=draft_unit_definitions().filter(
        lambda x: x.concept_vo.legacy_code is not None
    ),
    new_unit_definition_value=unit_definition_values().filter(
        lambda x: x.legacy_code is not None
    ),
    change_description=stripped_non_empty_strings(),
    author_id=stripped_non_empty_strings(),
)
def test__unit_definition_ar__edit_draft_without_legacy_code_change__result(
    unit_definition_ar: UnitDefinitionAR,
    new_unit_definition_value: UnitDefinitionValueVO,
    change_description: str,
    author_id: str,
):
    # given
    new_unit_definition_value = UnitDefinitionValueVO.from_repository_values(
        name=new_unit_definition_value.name,
        ct_units=(
            unit_definition_ar.concept_vo.ct_units
            if unit_definition_ar.concept_vo.ct_units is not None
            else new_unit_definition_value.ct_units
        ),
        unit_subsets=new_unit_definition_value.unit_subsets,
        convertible_unit=new_unit_definition_value.convertible_unit,
        display_unit=new_unit_definition_value.display_unit,
        master_unit=new_unit_definition_value.master_unit,
        si_unit=new_unit_definition_value.si_unit,
        us_conventional_unit=new_unit_definition_value.us_conventional_unit,
        use_complex_unit_conversion=new_unit_definition_value.use_complex_unit_conversion,
        unit_dimension_uid=new_unit_definition_value.unit_dimension_uid,
        legacy_code=unit_definition_ar.concept_vo.legacy_code,  # i.e. not changing this one
        use_molecular_weight=new_unit_definition_value.use_molecular_weight,
        conversion_factor_to_master=new_unit_definition_value.conversion_factor_to_master,
        ucum_uid=new_unit_definition_value.ucum_uid,
        definition=new_unit_definition_value.definition,
        order=new_unit_definition_value.order,
        comment=new_unit_definition_value.comment,
        ucum_name=None,
        unit_dimension_name=None,
        is_template_parameter=False,
    )

    # when
    library = unit_definition_ar.library
    datetime_before = datetime.now(timezone.utc)
    unit_definition_ar.edit_draft(
        new_unit_definition_value=new_unit_definition_value,
        change_description=change_description,
        author_id=author_id,
        concept_exists_by_callback=lambda x, y, z: y == unit_definition_ar.name
        or y != new_unit_definition_value.name,
        master_unit_exists_for_dimension_predicate=(
            lambda _: (
                True
                if (
                    unit_definition_ar.concept_vo.master_unit
                    and unit_definition_ar.concept_vo.unit_dimension_uid
                    == new_unit_definition_value.unit_dimension_uid
                )
                else _ != new_unit_definition_value.unit_dimension_uid
            )
        ),
        unit_definition_exists_by_legacy_code=lambda _: True,
    )
    datetime_after = datetime.now(timezone.utc)

    # then
    assert unit_definition_ar.concept_vo == new_unit_definition_value
    assert unit_definition_ar.item_metadata.status == LibraryItemStatus.DRAFT
    assert unit_definition_ar.item_metadata.start_date >= datetime_before
    assert unit_definition_ar.item_metadata.start_date <= datetime_after
    assert unit_definition_ar.item_metadata.end_date is None
    assert unit_definition_ar.item_metadata.author_id == author_id
    assert unit_definition_ar.item_metadata.change_description == change_description
    assert unit_definition_ar.library == library


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    unit_definition_ar=draft_unit_definitions(),
    new_unit_definition_value=unit_definition_values(),
    change_description=stripped_non_empty_strings(),
    author_id=stripped_non_empty_strings(),
)
def test__unit_definition_ar__edit_draft_without_unit_ct_uid_change__result(
    unit_definition_ar: UnitDefinitionAR,
    new_unit_definition_value: UnitDefinitionValueVO,
    change_description: str,
    author_id: str,
):
    # given
    new_unit_definition_value = UnitDefinitionValueVO.from_repository_values(
        name=new_unit_definition_value.name,
        ct_units=unit_definition_ar.concept_vo.ct_units,  # i.e. not changing this
        unit_subsets=unit_definition_ar.concept_vo.unit_subsets,
        convertible_unit=new_unit_definition_value.convertible_unit,
        display_unit=new_unit_definition_value.display_unit,
        master_unit=new_unit_definition_value.master_unit,
        si_unit=new_unit_definition_value.si_unit,
        us_conventional_unit=new_unit_definition_value.us_conventional_unit,
        use_complex_unit_conversion=new_unit_definition_value.use_complex_unit_conversion,
        unit_dimension_uid=new_unit_definition_value.unit_dimension_uid,
        legacy_code=new_unit_definition_value.legacy_code,
        use_molecular_weight=new_unit_definition_value.use_molecular_weight,
        conversion_factor_to_master=new_unit_definition_value.conversion_factor_to_master,
        ucum_uid=new_unit_definition_value.ucum_uid,
        definition=new_unit_definition_value.definition,
        order=new_unit_definition_value.order,
        comment=new_unit_definition_value.comment,
        ucum_name=None,
        unit_dimension_name=None,
        is_template_parameter=False,
    )

    # when
    library = unit_definition_ar.library
    datetime_before = datetime.now(timezone.utc)
    unit_definition_ar.edit_draft(
        new_unit_definition_value=new_unit_definition_value,
        change_description=change_description,
        author_id=author_id,
        concept_exists_by_callback=lambda x, y, z: y == unit_definition_ar.name
        or y != new_unit_definition_value.name,
        master_unit_exists_for_dimension_predicate=(
            lambda _: (
                True
                if (
                    unit_definition_ar.concept_vo.master_unit
                    and unit_definition_ar.concept_vo.unit_dimension_uid
                    == new_unit_definition_value.unit_dimension_uid
                )
                else _ != new_unit_definition_value.unit_dimension_uid
            )
        ),
        unit_definition_exists_by_legacy_code=(
            lambda _: _ == unit_definition_ar.concept_vo.legacy_code
            or _ != new_unit_definition_value.legacy_code
        ),
    )
    datetime_after = datetime.now(timezone.utc)

    # then
    assert unit_definition_ar.concept_vo == new_unit_definition_value
    assert unit_definition_ar.item_metadata.status == LibraryItemStatus.DRAFT
    assert unit_definition_ar.item_metadata.start_date >= datetime_before
    assert unit_definition_ar.item_metadata.start_date <= datetime_after
    assert unit_definition_ar.item_metadata.end_date is None
    assert unit_definition_ar.item_metadata.author_id == author_id
    assert unit_definition_ar.item_metadata.change_description == change_description
    assert unit_definition_ar.library == library


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    unit_definition_ar=draft_unit_definitions(),
    new_unit_definition_value=unit_definition_values(),
    change_description=stripped_non_empty_strings(),
    author_id=stripped_non_empty_strings(),
)
def test__unit_definition_ar__edit_draft_without_name_change__result(
    unit_definition_ar: UnitDefinitionAR,
    new_unit_definition_value: UnitDefinitionValueVO,
    change_description: str,
    author_id: str,
):
    # given
    new_unit_definition_value = UnitDefinitionValueVO.from_repository_values(
        name=unit_definition_ar.name,
        ct_units=(
            unit_definition_ar.concept_vo.ct_units
            if unit_definition_ar.concept_vo.ct_units is not None
            else new_unit_definition_value.ct_units
        ),
        unit_subsets=unit_definition_ar.concept_vo.unit_subsets,
        convertible_unit=new_unit_definition_value.convertible_unit,
        display_unit=new_unit_definition_value.display_unit,
        master_unit=new_unit_definition_value.master_unit,
        si_unit=new_unit_definition_value.si_unit,
        us_conventional_unit=new_unit_definition_value.us_conventional_unit,
        use_complex_unit_conversion=new_unit_definition_value.use_complex_unit_conversion,
        unit_dimension_uid=new_unit_definition_value.unit_dimension_uid,
        legacy_code=new_unit_definition_value.legacy_code,
        use_molecular_weight=new_unit_definition_value.use_molecular_weight,
        conversion_factor_to_master=new_unit_definition_value.conversion_factor_to_master,
        ucum_uid=new_unit_definition_value.ucum_uid,
        definition=new_unit_definition_value.definition,
        order=new_unit_definition_value.order,
        comment=new_unit_definition_value.comment,
        ucum_name=None,
        unit_dimension_name=None,
        is_template_parameter=False,
    )
    unit_def_value_before_edit = unit_definition_ar.concept_vo

    # when
    library = unit_definition_ar.library
    datetime_before = datetime.now(timezone.utc)
    unit_definition_ar.edit_draft(
        new_unit_definition_value=new_unit_definition_value,
        change_description=change_description,
        author_id=author_id,
        concept_exists_by_callback=lambda x, y, z: True,
        master_unit_exists_for_dimension_predicate=(
            lambda _: (
                True
                if (
                    unit_definition_ar.concept_vo.master_unit
                    and unit_definition_ar.concept_vo.unit_dimension_uid
                    == new_unit_definition_value.unit_dimension_uid
                )
                else _ != new_unit_definition_value.unit_dimension_uid
            )
        ),
        unit_definition_exists_by_legacy_code=lambda _: _
        == unit_definition_ar.concept_vo.legacy_code
        or _ != new_unit_definition_value.legacy_code,
    )
    datetime_after = datetime.now(timezone.utc)

    # then
    if unit_def_value_before_edit != new_unit_definition_value:
        assert unit_definition_ar.concept_vo == new_unit_definition_value
        assert unit_definition_ar.item_metadata.status == LibraryItemStatus.DRAFT
        assert unit_definition_ar.item_metadata.start_date >= datetime_before
        assert unit_definition_ar.item_metadata.start_date <= datetime_after
        assert unit_definition_ar.item_metadata.end_date is None
        assert unit_definition_ar.item_metadata.author_id == author_id
        assert unit_definition_ar.item_metadata.change_description == change_description
        assert unit_definition_ar.library == library


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    unit_definition_ar=draft_unit_definitions(),
    new_unit_definition_value=unit_definition_values(),
    change_description=stripped_non_empty_strings(),
    author_id=stripped_non_empty_strings(),
)
def test__unit_definition_ar__edit_draft_with_non_unique_name__failure(
    unit_definition_ar: UnitDefinitionAR,
    new_unit_definition_value: UnitDefinitionValueVO,
    change_description: str,
    author_id: str,
):
    assume(new_unit_definition_value.name != unit_definition_ar.name)
    # then
    with pytest.raises(AlreadyExistsException):  # pylint: disable=unreachable
        # when
        unit_definition_ar.edit_draft(
            author_id=author_id,
            change_description=change_description,
            new_unit_definition_value=new_unit_definition_value,
            concept_exists_by_callback=lambda x, y, z: y
            == new_unit_definition_value.name,
            master_unit_exists_for_dimension_predicate=lambda _: False,
            unit_definition_exists_by_legacy_code=lambda _: False,
        )


@settings(
    max_examples=int(max(10, settings.default.max_examples / 10)),
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
@given(
    unit_definition_ar=draft_unit_definitions(),
    new_unit_definition_value=unit_definition_values().filter(
        lambda x: x.legacy_code is not None
    ),
    change_description=stripped_non_empty_strings(),
    author_id=stripped_non_empty_strings(),
)
def test__unit_definition_ar__edit_draft_with_non_unique_legacy_code__failure(
    unit_definition_ar: UnitDefinitionAR,
    new_unit_definition_value: UnitDefinitionValueVO,
    change_description: str,
    author_id: str,
):
    assume(
        new_unit_definition_value.legacy_code
        != unit_definition_ar.concept_vo.legacy_code
    )
    # then
    with pytest.raises(BusinessLogicException):  # pylint: disable=unreachable
        # when
        unit_definition_ar.edit_draft(
            author_id=author_id,
            change_description=change_description,
            new_unit_definition_value=new_unit_definition_value,
            concept_exists_by_callback=lambda x, y, z: False,
            master_unit_exists_for_dimension_predicate=lambda _: False,
            unit_definition_exists_by_legacy_code=lambda _: _
            == new_unit_definition_value.legacy_code,
        )


@settings(
    max_examples=int(max(10, settings.default.max_examples / 10)),
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    deadline=None,
)
@given(
    unit_definition_ar=draft_unit_definitions(),
    new_unit_definition_value=unit_definition_values(),
    change_description=stripped_non_empty_strings(),
    author_id=stripped_non_empty_strings(),
)
def test__unit_definition_ar__edit_draft_making_another_master_unit__failure(
    unit_definition_ar: UnitDefinitionAR,
    new_unit_definition_value: UnitDefinitionValueVO,
    change_description: str,
    author_id: str,
):
    # given
    assume(new_unit_definition_value.unit_dimension_uid is not None)
    assume(new_unit_definition_value.master_unit)  # pylint: disable=unreachable
    assume(  # pylint: disable=unreachable
        not unit_definition_ar.concept_vo.master_unit
        or new_unit_definition_value.unit_dimension_uid
        != unit_definition_ar.concept_vo.unit_dimension_uid
    )

    # then
    with pytest.raises(BusinessLogicException):  # pylint: disable=unreachable
        # when
        unit_definition_ar.edit_draft(
            author_id=author_id,
            change_description=change_description,
            new_unit_definition_value=new_unit_definition_value,
            concept_exists_by_callback=lambda x, y, z: False,
            master_unit_exists_for_dimension_predicate=lambda _: _
            == new_unit_definition_value.unit_dimension_uid,
            unit_definition_exists_by_legacy_code=lambda _: False,
        )


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    unit_definition_ar=one_of(final_unit_definitions(), retired_unit_definitions()),
    new_unit_definition_value=unit_definition_values(),
    change_description=stripped_non_empty_strings(),
    author_id=stripped_non_empty_strings(),
)
def test__unit_definition_ar__edit_draft__incorrect_status__failure(
    unit_definition_ar: UnitDefinitionAR,
    new_unit_definition_value: UnitDefinitionValueVO,
    change_description: str,
    author_id: str,
):
    # then
    with pytest.raises(BusinessLogicException):
        # when
        unit_definition_ar.edit_draft(
            author_id=author_id,
            change_description=change_description,
            new_unit_definition_value=new_unit_definition_value,
            concept_exists_by_callback=lambda x, y, z: False,
            master_unit_exists_for_dimension_predicate=lambda _: False,
            unit_definition_exists_by_legacy_code=lambda _: False,
        )


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    unit_definition_value=unit_definition_values(),
    non_1_conversion_factor=floats(allow_nan=False).filter(lambda _: _ != 1.0),
)
def test__unit_definition_value_vo__from_input_values__non_1_conversion_factor_for_master_unit__failure(
    unit_definition_value: UnitDefinitionValueVO, non_1_conversion_factor: float
):
    # then
    with pytest.raises(ValidationException):
        # when
        UnitDefinitionValueVO.from_input_values(
            name=unit_definition_value.name,
            ct_units=unit_definition_value.ct_units,
            unit_subsets=unit_definition_value.unit_subsets,
            convertible_unit=unit_definition_value.convertible_unit,
            display_unit=unit_definition_value.display_unit,
            master_unit=True,
            si_unit=unit_definition_value.si_unit,
            us_conventional_unit=unit_definition_value.us_conventional_unit,
            use_complex_unit_conversion=unit_definition_value.use_complex_unit_conversion,
            legacy_code=unit_definition_value.legacy_code,
            use_molecular_weight=unit_definition_value.use_molecular_weight,
            conversion_factor_to_master=non_1_conversion_factor,
            unit_ct_uid_exists_callback=lambda _: True,
            unit_dimension_uid=unit_definition_value.unit_dimension_uid,
            ucum_uid=unit_definition_value.ucum_uid,
            definition=unit_definition_value.definition,
            order=unit_definition_value.order,
            comment=unit_definition_value.comment,
            ucum_uid_exists_callback=lambda _: True,
            find_term_by_uid=lambda _: get_mock_ct_item(
                unit_definition_value.unit_dimension_uid
            ),
            is_template_parameter=False,
        )


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(unit_definition_value=unit_definition_values())
def test__unit_definition_value_vo__from_input_values__molecular_weight_conv_expon_not_provided_for_concentration__failure(
    unit_definition_value: UnitDefinitionValueVO,
):
    # then
    with pytest.raises(ValidationException):
        # when
        UnitDefinitionValueVO.from_input_values(
            name=unit_definition_value.name,
            ct_units=unit_definition_value.ct_units,
            unit_subsets=unit_definition_value.unit_subsets,
            convertible_unit=unit_definition_value.convertible_unit,
            display_unit=unit_definition_value.display_unit,
            master_unit=unit_definition_value.master_unit,
            si_unit=unit_definition_value.si_unit,
            us_conventional_unit=unit_definition_value.us_conventional_unit,
            use_complex_unit_conversion=unit_definition_value.use_complex_unit_conversion,
            legacy_code=unit_definition_value.legacy_code,
            use_molecular_weight=None,
            conversion_factor_to_master=unit_definition_value.conversion_factor_to_master,
            unit_ct_uid_exists_callback=lambda _: True,
            unit_dimension_uid=CONCENTRATION_UNIT_DIMENSION_VALUE,
            ucum_uid=unit_definition_value.ucum_uid,
            definition=unit_definition_value.definition,
            order=unit_definition_value.order,
            comment=unit_definition_value.comment,
            ucum_uid_exists_callback=lambda _: True,
            find_term_by_uid=lambda _: get_mock_ct_item(
                CONCENTRATION_UNIT_DIMENSION_VALUE
            ),
            is_template_parameter=False,
        )
