from src.scripts.utils import *


class Test:
    def test__are_lists_equal_true(self):
        # given, when, then
        assert are_lists_equal([], []) is True
        assert are_lists_equal(["1", "2"], ["2", "1"]) is True
        assert are_lists_equal(["", "test", "test"], ["test", ""]) is True
        assert are_lists_equal(["", "TEST", "test"], ["tesT", ""]) is True
        assert are_lists_equal([None], []) is True

    def test__are_lists_equal_false(self):
        # given, when, then
        assert are_lists_equal(["a"], ["a "]) is False
        assert are_lists_equal(["2"], ["2", ""]) is False
        assert are_lists_equal([""], ["2", ""]) is False
        assert are_lists_equal([None], ["None"]) is False

    def test__string_to_boolean(self):
        # given, when, then
        assert string_to_boolean("TRUE") is True
        assert string_to_boolean("true") is True
        assert string_to_boolean("y") is True
        assert string_to_boolean("Y") is True
        assert string_to_boolean("yes") is True
        assert string_to_boolean("yEs") is True
        assert string_to_boolean("yEs") is True
        assert string_to_boolean("1") is True
        assert string_to_boolean("") is False
        assert string_to_boolean("No") is False
        assert string_to_boolean("no") is False
        assert string_to_boolean("null") is False
        assert string_to_boolean("f") is False
        assert string_to_boolean("0") is False
        assert string_to_boolean("false") is False
        assert string_to_boolean("False") is False
        assert string_to_boolean("-") is False

    def test__get_sentence_case_string(self):
        # given, when, then

        # one word
        assert get_sentence_case_string("Unknown") == "unknown"
        # multiple words without more than one capital letter
        assert (
            get_sentence_case_string("Secondary Outcome Measure")
            == "secondary outcome measure"
        )
        # multiple words including acronyms (all uppercase letters) in the middle
        assert (
            get_sentence_case_string("Prolonged ST Segment by ECG Finding")
            == "prolonged ST segment by ECG finding"
        )
        # multiple words with acronym (all uppercase letters) at the beginning
        # and including an acronym (only first two letters + last uppercase)
        assert (
            get_sentence_case_string("CDISC ADaM Analysis Reason Terminology")
            == "CDISC ADaM analysis reason terminology"
        )

        assert (
            get_sentence_case_string("6MWT - Distance at 6 Minutes")
            == "6MWT - distance at 6 minutes"
        )
        assert get_sentence_case_string("aBcD Test") == "aBcD test"
        assert get_sentence_case_string("A ") == "a "
        assert get_sentence_case_string("A b") == "a b"
        assert get_sentence_case_string("") == ""
        assert get_sentence_case_string(None) is None

    def test__is_newer_than(self):
        assert is_newer_than("2020-01-01", "2021-01-01") is False
        assert is_newer_than("2021-01-01", "2021-01-02") is False
        assert is_newer_than("2021-02-01", "2021-02-02") is False
        assert is_newer_than("2021-01-01", "2021-01-01") is False
        assert is_newer_than("2021-01-01", "2020-01-01") is True
        assert is_newer_than("2021-01-01", "2020") is True
        assert is_newer_than("2021-01-01", "2019-10-29") is True
