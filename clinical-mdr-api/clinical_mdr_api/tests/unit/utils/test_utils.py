import unittest

from parameterized import parameterized
from pydantic import BaseModel

import common.utils
from clinical_mdr_api import utils


class TestServiceUtils(unittest.TestCase):
    def test_to_dict(self):
        class ClassB:
            z: str

            def __init__(self, z) -> None:
                self.z = z

        class ClassA:
            x: str
            y: ClassB

            def __init__(self, x, y) -> None:
                self.x = x
                self.y = y

        assert utils.to_dict(ClassA(x="a", y=ClassB(z="b"))) == {
            "y": {"z": "b"},
            "x": "a",
        }

    @parameterized.expand(
        [
            ("", None),
            ("   ", None),
            ("x", "x"),
            (" x ", "x"),
        ]
    )
    def test_normalize_string(self, string, expected):
        assert utils.normalize_string(string) == expected

    @parameterized.expand(
        [
            (True, "yes", "yes"),
            (False, "yes", "no"),
            (1, "yes", "yes"),
            (0, "yes", "no"),
            (1, "y", "y"),
            (0, "y", "n"),
            (1, "Y", "Y"),
            (0, "Y", "N"),
            (1, "t", "t"),
            (0, "t", "f"),
            (1, "true", "true"),
            (0, "true", "false"),
            (1, "on", "on"),
            (0, "on", "off"),
            (1, "1", "1"),
            (0, "1", "0"),
        ]
    )
    def test_booltostr(self, boolean, true_format, expected):
        assert common.utils.booltostr(boolean, true_format) == expected

    def test_booltostr_raises_exception(self):
        self.assertRaises(
            ValueError, common.utils.booltostr, 1, "NonExistingTrueFormat"
        )

    @parameterized.expand(
        [
            ("snake_case_input", "snakeCaseInput"),
            ("snake_32_case_input_", "snake32CaseInput"),
            ("..._snake_____case_input____", "...SnakeCaseInput"),
            ("zzz_snake_____case_input____", "zzzSnakeCaseInput"),
        ]
    )
    def test_snake_to_camel(self, input_data, expected):
        assert utils.snake_to_camel(input_data) == expected

    @parameterized.expand(
        [
            ("camelCaseInput", "camel_case_input"),
            ("camel32CaseInput_", "camel32_case_input_"),
            ("...Camel____CaseInput____", "..._camel_____case_input____"),
            ("zzzCamel____CaseInput____", "zzz_camel_____case_input____"),
        ]
    )
    def test_camel_to_snake(self, input_data, expected):
        assert utils.camel_to_snake(input_data) == expected

    @parameterized.expand(
        [
            (
                {
                    "camelCaseInput": "x",
                    "camel32CaseInput_": "y",
                },
                False,
                {
                    "camel_case_input": "x",
                    "camel32_case_input_": "y",
                },
            ),
            (
                {
                    "camelCaseInput": "x",
                    "camel32CaseInput_": "y",
                },
                True,
                {
                    "_camel_case_input": "x",
                    "_camel32_case_input_": "y",
                },
            ),
        ]
    )
    def test_snake_case_data(self, input_data, privates, expected):
        assert utils.snake_case_data(input_data, privates) == expected

    @parameterized.expand(
        [
            (
                {
                    "camel_case_input": "x",
                    "camel32_case_input_": "y",
                    "_camel32_case_input_": "y",
                },
                # pylint: disable=duplicate-key
                {
                    "camelCaseInput": "x",
                    "camel32CaseInput": "y",
                },
            )
        ]
    )
    def test_camel_case_data(self, input_data, expected):
        assert utils.camel_case_data(input_data) == expected

    def test_is_attribute_in_model(self):
        class _model(BaseModel):
            z: str = "something"
            x: int = 123

        assert utils.is_attribute_in_model("x", _model)
        assert not utils.is_attribute_in_model("y", _model)

    @parameterized.expand(
        [
            ("0", 0),
            ("1", 1),
            ("yes", 1),
            ("No", 0),
            ("YES", 1),
            ("yEs", 1),
            ("no", 0),
            ("tRue", 1),
            ("False", 0),
            ("false", 0),
            ("Off", 0),
            ("on", 1),
            ("OFF", 0),
            ("oN", 1),
        ],
    )
    def test_strtobool(self, value, result):
        assert common.utils.strtobool(value) == result

    @parameterized.expand(
        [
            (True, AttributeError),
            (False, AttributeError),
            (None, AttributeError),
            (0, AttributeError),
            (1, AttributeError),
            (-1, AttributeError),
            (0.1, AttributeError),
            ({}, AttributeError),
            ([1, 2], AttributeError),
            ("foo", ValueError),
            ("BAR", ValueError),
            ("Nein", ValueError),
            ("ni", ValueError),
            ("null", ValueError),
            ("NULL", ValueError),
            ("", ValueError),
            (" ", ValueError),
        ],
    )
    def test_strtobool_raises_exception(self, value, exception_type):
        with self.assertRaises(exception_type):
            common.utils.strtobool(value)
