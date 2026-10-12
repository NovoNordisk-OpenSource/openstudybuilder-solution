import unittest
import uuid
from unittest import mock

from parameterized import parameterized
from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.repositories._utils import ComparisonOperator, FilterOperator
from clinical_mdr_api.services import _utils
from common.exceptions import ValidationException


class BaseTestObject(BaseModel):
    uid: str = str(uuid.uuid4())
    k1: str = ""
    k2: str = ""
    k3: list[str] = Field(default_factory=list)

    def __eq__(self, other):
        return self.k1 == other.k1 and self.k2 == other.k2 and self.k3 == other.k3

    def __hash__(self):
        return hash((self.k1, self.k2, tuple(self.k3)))

    @staticmethod
    def get_all_items() -> list[BaseTestObject]:
        return [
            BaseTestObject(
                k1=f"k1.row{index}", k2=f"k2.row{index}", uid=str(uuid.uuid4())
            )
            for index in range(100)
        ]


class NestedChild(BaseModel):
    # Nullable, mirroring SimpleTermModel.name.
    name: str | None = ""


class ListHolder(BaseModel):
    """Mirrors a model holding a collection of named sub-models.

    Shaped after MedicinalProduct.dose_frequencies, a list[SimpleTermModel].
    """

    children: list[NestedChild] = Field(default_factory=list)


class ListRow(BaseModel):
    collection: ListHolder | None = None


class NestedHolder(BaseModel):
    """Mirrors a selection that carries an optional and a required sub-model.

    Shaped after StudySelectionActivityInstance, where ``activity_instance`` is
    nullable (a placeholder) while ``activity`` is always populated.
    """

    optional_child: NestedChild | None = None
    required_child: NestedChild = NestedChild()


class NestedRow(BaseModel):
    nested: NestedHolder | None = None


class TestServiceUtils(unittest.TestCase):
    @parameterized.expand(
        [
            ("x", "Y", "An Element of Something", ".", "x"),
            (None, "Y", "An Element of Something", ".", "YAEoS.1234567890"),
            (None, "", "An Element of Something", ".", "AEoS.1234567890"),
            (None, "Y", "Something", ".", "YSMTIG.1234567890"),
            (None, "Y", "s", ".", "YS.1234567890"),
            (None, "Y", "Something", "#", "YSMTIG#1234567890"),
            (None, "Y", "Something", "", "YSMTIG1234567890"),
            (None, "Y", "", ".", "Y.1234567890"),
        ]
    )
    @mock.patch("clinical_mdr_api.services._utils.time", return_value=1234567890)
    def test_get_input_or_new_value(
        self, input_field, prefix, output_field, sep, expected, mock_class
    ):

        assert (
            _utils.get_input_or_new_value(input_field, prefix, output_field, sep)
            == expected
        )

    def test_get_input_or_new_value_raises_exception(self):
        self.assertRaises(ValueError, _utils.get_input_or_new_value, None, "Y", None)

    @parameterized.expand(
        [
            ({"x": 1, "y": 2}, {"x": 1, "y": 3}, ["y"]),
            ({"x": 1, "y": 2}, {"x": 1, "y": 2}, []),
            ({"x": 1, "y": 2}, None, []),
        ]
    )
    def test_object_diff(self, obj1, obj2, expected):
        assert _utils.object_diff(obj1, obj2) == expected

    @parameterized.expand(
        [
            (
                BaseTestObject.get_all_items(),
                {"k1": {"v": ["k1.row10"], "op": "co"}},
                FilterOperator.AND,
                {},
                True,
                1,
                0,
                [BaseTestObject(k1="k1.row10", k2="k2.row10")],
            ),
            (
                BaseTestObject.get_all_items(),
                {"*": {"v": ["row20"], "op": "co"}},
                FilterOperator.AND,
                {},
                True,
                1,
                0,
                [
                    BaseTestObject(k1="k1.row20", k2="k2.row20"),
                ],
            ),
            (
                BaseTestObject.get_all_items(),
                {"k1": {"v": ["k1.row10", "k1.row20"], "op": "co"}},
                FilterOperator.OR,
                {},
                True,
                1,
                0,
                [
                    BaseTestObject(k1="k1.row10", k2="k2.row10"),
                    BaseTestObject(k1="k1.row20", k2="k2.row20"),
                ],
            ),
            (
                BaseTestObject.get_all_items(),
                {
                    "k1": {"v": ["k1.row10"], "op": "co"},
                    "k2": {"v": ["k2.row30"], "op": "co"},
                },
                FilterOperator.OR,
                {},
                True,
                1,
                0,
                [
                    BaseTestObject(k1="k1.row10", k2="k2.row10"),
                    BaseTestObject(k1="k1.row30", k2="k2.row30"),
                ],
            ),
            (
                BaseTestObject.get_all_items(),
                {
                    "k1": {"v": ["k1.row10"], "op": "co"},
                    "k2": {"v": ["k2.row30"], "op": "co"},
                },
                FilterOperator.AND,
                {},
                True,
                1,
                0,
                [],
            ),
            (
                BaseTestObject.get_all_items(),
                {
                    "k1": {"v": ["k1.row10"], "op": "co"},
                    "k2": {"v": ["k2.row10"], "op": "co"},
                },
                FilterOperator.AND,
                {},
                True,
                1,
                0,
                [
                    BaseTestObject(k1="k1.row10", k2="k2.row10"),
                ],
            ),
        ]
    )
    def test_service_level_generic_filtering(
        self,
        items,
        filter_by,
        filter_operator,
        sort_by,
        total_count,
        page_number,
        page_size,
        expected,
    ):
        out = _utils.service_level_generic_filtering(
            items,
            filter_by,
            filter_operator,
            sort_by,
            total_count,
            page_number,
            page_size,
        )
        assert out.items == expected
        assert out.total == len(expected)

    @parameterized.expand(
        [
            (
                BaseTestObject.get_all_items(),
                "k1",
                FilterOperator.AND,
                "k1.row10",
                {"k1": {"v": ["k1.row10", "k1.row20"], "op": "co"}},
                5,
                ["k1.row10"],
            ),
            (
                BaseTestObject.get_all_items(),
                "k1",
                FilterOperator.OR,
                "k1.row1",
                {
                    "k1": {"v": ["k1.row10", "k1.row20"], "op": "co"},
                },
                5,
                ["k1.row1", "k1.row10", "k1.row11", "k1.row12", "k1.row13"],
            ),
        ]
    )
    def test_service_level_generic_header_filtering(
        self,
        items,
        field_name,
        filter_operator,
        search_string,
        filter_by,
        page_size,
        expected,
    ):
        out = _utils.service_level_generic_header_filtering(
            items,
            field_name,
            filter_operator,
            search_string,
            filter_by,
            page_size,
        )
        assert sorted(out) == sorted(expected)

    @parameterized.expand(
        [
            ("valueA", ComparisonOperator.EQUALS, ["valueA"], True),
            ("valueA", ComparisonOperator.EQUALS, ["VALUEA"], False),
            ("valueA", ComparisonOperator.CONTAINS, ["valuea"], True),
            ("valueA", ComparisonOperator.CONTAINS, ["val"], True),
            ("valueA", ComparisonOperator.CONTAINS, ["UE"], True),
            ("valueA", ComparisonOperator.CONTAINS, ["x", "y", "z"], False),
            ("valueA", ComparisonOperator.GREATER_THAN, ["valueA"], False),
            ("valueA", ComparisonOperator.GREATER_THAN, ["aaa"], True),
            ("valueA", ComparisonOperator.GREATER_THAN_OR_EQUAL_TO, ["valueA"], True),
            ("valueA", ComparisonOperator.GREATER_THAN_OR_EQUAL_TO, ["zzz"], False),
            ("valueA", ComparisonOperator.LESS_THAN, ["valuea"], True),
            ("valueA", ComparisonOperator.LESS_THAN_OR_EQUAL_TO, ["valuea"], True),
            ("valueA", ComparisonOperator.BETWEEN, ["abc", "ddd"], False),
            ("valueA", ComparisonOperator.BETWEEN, ["aaa", "zzz"], True),
            ("valueA", ComparisonOperator.BETWEEN, ["valueA", "valueB"], True),
            ("valueA", ComparisonOperator.EQUALS, [], False),
            (None, ComparisonOperator.EQUALS, [], True),
        ]
    )
    def test_apply_filter_operator(self, value, operator, filter_values, expected):
        out = _utils.apply_filter_operator(value, operator, filter_values)
        assert out == expected

    def test_service_level_generic_filtering_or_dedup_without_uid_attr(self):
        """OR-filtering should dedupe items matching multiple keys even when
        items have no `uid` attribute (e.g. StudySelectionActivity uses
        `study_activity_uid`). Previously raised AttributeError, surfacing as 500.
        """

        class NoUidModel(BaseModel):
            # Deliberately no `uid` field; only a differently-named id.
            study_activity_uid: str
            k1: str = ""
            k2: str = ""

        items = [
            NoUidModel(study_activity_uid="a", k1="match", k2="match"),
            NoUidModel(study_activity_uid="b", k1="other", k2="other"),
        ]

        out = _utils.service_level_generic_filtering(
            items=items,
            # Both filter keys match the same first item; OR must not duplicate it.
            filter_by={
                "k1": {"v": ["match"], "op": "co"},
                "k2": {"v": ["match"], "op": "co"},
            },
            filter_operator=FilterOperator.OR,
            sort_by={},
            total_count=True,
            page_number=1,
            page_size=0,
        )

        assert [item.study_activity_uid for item in out.items] == ["a"]
        assert out.total == 1

    @parameterized.expand(
        [
            (BaseTestObject(k1="k1.value1", k2="k2.value2"), "k1", "val", "co", True),
            (BaseTestObject(k1="k1.value1", k2="k2.value2"), "k1", "xyz", "co", False),
            (
                BaseTestObject(k3=["value1", "value2"], k2="k2.aaa"),
                "k3",
                "valu",
                "co",
                True,
            ),
            (
                BaseTestObject(k3=["value1", "value2"], k2="k2.aaa"),
                "k3",
                "xyz",
                "co",
                False,
            ),
        ]
    )
    def test_filter_aggregated_items(
        self, item, filter_key, filter_values, filter_operator, expected
    ):
        out = _utils.filter_aggregated_items(
            item, filter_key, filter_values, filter_operator
        )
        assert out == expected

    def test_rgetattr_type_resolves_through_nullable_nested_model(self):
        """A path through a null nested model must still yield the declared type.

        Resolving a dotted path hands each step the *type* of the previous
        segment. Before this was handled, the walk fell off at the first model
        class and returned NoneType, which made sorting pick an int sentinel for
        rows whose nested model is null and compare it against str values.
        """
        placeholder = NestedRow(
            nested=NestedHolder(
                optional_child=None, required_child=NestedChild(name="B")
            )
        )
        assert _utils.rgetattr_type(placeholder, "nested.optional_child.name") is str
        # The populated case was already correct and must stay so.
        populated = NestedRow(
            nested=NestedHolder(
                optional_child=NestedChild(name="A"),
                required_child=NestedChild(name="B"),
            )
        )
        assert _utils.rgetattr_type(populated, "nested.optional_child.name") is str

    @parameterized.expand(
        [
            # (label, term names per row, expected ascending order of resolved values)
            ("two populated", [["QD"], ["BID"]], [["BID"], ["QD"]]),
            ("empty collection", [["QD"], []], [[], ["QD"]]),
            # A row whose whole path resolves to nothing needs a list-shaped
            # sentinel, otherwise "-1" is compared against a list.
            ("absent parent", [["QD"], None], [None, ["QD"]]),
            # A null term name inside the list must not break the comparison.
            ("null term name", [["QD"], [None]], [[None], ["QD"]]),
        ]
    )
    def test_sorting_on_list_valued_path(self, _label, rows_spec, expected_ascending):
        """A key resolving to a list (a path through a collection) must sort.

        This previously raised TypeError for any page containing a row with an
        absent parent or an unnamed term.
        """
        key = "collection.children.name"
        rows = [
            (
                ListRow(collection=None)
                if names is None
                else ListRow(
                    collection=ListHolder(
                        children=[NestedChild(name=name) for name in names]
                    )
                )
            )
            for names in rows_spec
        ]

        ascending = _utils.generic_item_filtering(items=list(rows), sort_by={key: True})
        descending = _utils.generic_item_filtering(
            items=list(rows), sort_by={key: False}
        )

        assert [_utils.rgetattr(item, key) for item in ascending] == expected_ascending
        assert [_utils.rgetattr(item, key) for item in descending] == list(
            reversed(expected_ascending)
        )

    @parameterized.expand(
        [
            # The first declared key is primary, whichever directions are mixed.
            (
                "first asc, second desc",
                {"k1": True, "k2": False},
                [("x", "b"), ("x", "a"), ("y", "c")],
            ),
            (
                "first desc, second asc",
                {"k1": False, "k2": True},
                [("y", "c"), ("x", "a"), ("x", "b")],
            ),
            (
                "second key declared first",
                {"k2": False, "k1": True},
                [("y", "c"), ("x", "b"), ("x", "a")],
            ),
            # Same-direction keys go down the other branch; included so both
            # branches are pinned to the same declaration-order precedence.
            (
                "both asc",
                {"k1": True, "k2": True},
                [("x", "a"), ("x", "b"), ("y", "c")],
            ),
        ]
    )
    def test_multi_key_sort_uses_declaration_order_precedence(
        self, _label, sort_by, expected
    ):
        """`{"field_1": ..., "field_2": ...}` must sort by field_1 first.

        The mixed-direction branch sorts once per key, and a stable sort lets the
        LAST applied sort win — so iterating in declaration order made the last
        declared key primary, contradicting the documented behaviour and the
        same-direction branch.
        """
        rows = [
            BaseTestObject(k1="x", k2="b"),
            BaseTestObject(k1="x", k2="a"),
            BaseTestObject(k1="y", k2="c"),
        ]

        out = _utils.generic_item_filtering(items=list(rows), sort_by=sort_by)

        assert [(item.k1, item.k2) for item in out] == expected

    def test_sorting_by_nested_model_raises_validation_error_not_type_error(self):
        """A sort key naming a whole sub-model is bad input, so answer 400.

        Two such objects cannot be ordered, and letting the TypeError escape
        surfaced as a 500 for a request a client can plausibly make.
        """
        rows = [
            NestedRow(nested=NestedHolder(required_child=NestedChild(name="A"))),
            NestedRow(nested=NestedHolder(required_child=NestedChild(name="B"))),
        ]

        with self.assertRaises(ValidationException) as ctx:
            _utils.generic_item_filtering(items=rows, sort_by={"nested": True})

        assert ctx.exception.status_code == 400
        # The message has to name the offending key and point at the way out.
        assert "nested" in ctx.exception.msg
        assert "scalar sub-field" in ctx.exception.msg

    def test_sorting_on_nullable_nested_path_does_not_raise(self):
        """Sorting a column whose nested model is null on some rows must work.

        Nulls cluster at the head of an ascending sort rather than being ordered
        by any fallback value — that is accepted behaviour, not an oversight.
        """
        key = "nested.optional_child.name"
        populated = NestedRow(
            nested=NestedHolder(
                optional_child=NestedChild(name="Zebra"),
                required_child=NestedChild(name="ignored"),
            )
        )
        placeholder = NestedRow(
            nested=NestedHolder(
                optional_child=None, required_child=NestedChild(name="Body Temp")
            )
        )

        out = _utils.generic_item_filtering(
            items=[populated, placeholder], sort_by={key: True}
        )

        assert [_utils.rgetattr(item, key) for item in out] == [None, "Zebra"]
