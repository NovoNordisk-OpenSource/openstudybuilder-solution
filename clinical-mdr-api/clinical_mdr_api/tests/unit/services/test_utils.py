import unittest
import uuid
from unittest import mock

from parameterized import parameterized

from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.repositories._utils import ComparisonOperator, FilterOperator
from clinical_mdr_api.services import _utils


class BaseTestObject(BaseModel):
    uid: str = str(uuid.uuid4())
    k1: str = ""
    k2: str = ""
    k3: list[str] = []

    def __eq__(self, other):
        return self.k1 == other.k1 and self.k2 == other.k2 and self.k3 == other.k3

    @staticmethod
    def get_all_items() -> list["BaseTestObject"]:
        return [
            BaseTestObject(
                k1=f"k1.row{index}", k2=f"k2.row{index}", uid=str(uuid.uuid4())
            )
            for index in range(100)
        ]


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
        # pylint: disable=unused-argument
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
