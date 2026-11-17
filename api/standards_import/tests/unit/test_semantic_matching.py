"""The half of the semantic check that does not talk to anything.

The gateway call is one function behind a seam; everything here is what stays the same
whichever LLM backend an organisation points that seam at, so it is all testable offline.
"""

from typing import Any

import pytest

from common.exceptions import ValidationException
from standards_import.config import settings
from standards_import.repositories.semantic_repository import answer_key
from standards_import.services.semantic_matching import (
    build_prompt,
    clean,
    dereference,
    describe_candidate,
    extract_pairs,
    resolve_pairs,
)
from standards_import.services.semantic_provider import load_provider

ADDED: list[dict[str, Any]] = [
    {
        "concept_id": "C1",
        "name": "Angiopoietin-Related Protein 3/8 Complex",
        "submission_value": "ANGPTL38",
        "definition": "A complex.",
    },
    {
        "concept_id": "C2",
        "name": "Something Else",
        "submission_value": "ELSE",
        "definition": None,
    },
]
SPONSORS: list[dict[str, Any]] = [
    {
        "uid": "CTTerm_000042",
        "name": "Angiopoietin-Like 3/8 Complex",
        "submission_value": "ANGL38",
        "definition": "The same complex.",
    }
]


# --- the prompt -------------------------------------------------------------------


def test_the_prompt_carries_both_lists_with_their_definitions():
    """Definitions are worth ten points of recall — they are what lets one generic prompt
    reach the accuracy of a hand-written per-codelist one."""

    prompt = build_prompt("Lab Test Code", ADDED, SPONSORS)

    assert "Lab Test Code" in prompt
    assert "N00: Angiopoietin-Related Protein 3/8 Complex" in prompt
    assert "E00: Angiopoietin-Like 3/8 Complex" in prompt
    assert "def: A complex." in prompt
    assert "def: The same complex." in prompt


def test_the_prompt_is_identical_for_identical_inputs():
    """Re-assessing a release must not quietly produce a different set of candidates."""

    assert build_prompt("X", ADDED, SPONSORS) == build_prompt("X", ADDED, SPONSORS)


def test_the_cdisc_carriage_return_marker_is_stripped():
    assert clean("one_x000D_ two   three") == "one two three"


# --- reading the reply ------------------------------------------------------------


def test_the_pairs_survive_prose_on_both_sides_of_them():
    """The prompt asks for reasoning first and the model often adds a note afterwards, so
    slicing to the last brace spans more than one object and raises."""

    reply = (
        "N00 | angiopoietin 3/8 | none\n"
        '{"pairs": [{"new": "N00", "existing": "E00", "confidence": "high"}]}\n'
        "That is the only one. {not json at all"
    )

    assert extract_pairs(reply) == [
        {"new": "N00", "existing": "E00", "confidence": "high"}
    ]


def test_a_reply_with_no_json_at_all_yields_nothing():
    assert extract_pairs("I could not find any duplicates.") == []
    assert extract_pairs("") == []


def test_the_largest_pairs_array_wins():
    """Models sometimes echo a worked example before the real answer."""

    reply = '{"pairs": []} then really {"pairs": [{"new":"N00","existing":"E00"}]}'

    assert len(extract_pairs(reply)) == 1


def test_an_index_outside_the_list_is_dropped_rather_than_resolved():
    """One bad pair out of a dozen must not cost the whole codelist's answer, and must
    certainly not be resolved to whichever term happens to sit at that position."""

    resolved = resolve_pairs(
        [
            {"new": "N09", "existing": "E00", "confidence": "high"},
            {"new": "N00", "existing": "E00", "confidence": "high", "why": "Same."},
        ],
        ADDED,
        SPONSORS,
    )

    assert list(resolved) == ["C1"]
    assert resolved["C1"][0]["sponsor_uid"] == "CTTerm_000042"


def test_candidates_come_back_most_confident_first():
    resolved = resolve_pairs(
        [
            {"new": "N00", "existing": "E00", "confidence": "low", "why": "Maybe."},
            {"new": "N00", "existing": "E00", "confidence": "high", "why": "Yes."},
        ],
        ADDED,
        SPONSORS,
    )

    assert [c["confidence"] for c in resolved["C1"]] == ["high", "low"]


def test_a_confidence_nobody_recognises_sorts_last_rather_than_raising():
    resolved = resolve_pairs(
        [
            {"new": "N00", "existing": "E00", "confidence": "certain"},
            {"new": "N00", "existing": "E00", "confidence": "medium"},
        ],
        ADDED,
        SPONSORS,
    )

    assert [c["confidence"] for c in resolved["C1"]] == ["medium", "certain"]


# --- the labels the model writes back ---------------------------------------------


def test_labels_in_the_reason_become_the_names_they_stand_for():
    """The reasons come back referring to the labels the prompt handed out, which is
    coherent in the reply and meaningless in a review queue."""

    reason = dereference(
        "E00 measures the fragment, while N00 measures total.", ADDED, SPONSORS
    )

    assert "Angiopoietin-Like 3/8 Complex" in reason
    assert "Angiopoietin-Related Protein 3/8 Complex" in reason
    assert "N00" not in reason and "E00" not in reason


def test_a_label_the_model_invented_is_left_as_written():
    """Better an unresolved label than one resolved to the wrong term."""

    assert "N99" in dereference("N99 is unrelated.", ADDED, SPONSORS)


def test_a_single_digit_label_is_not_read_as_a_reference():
    """`N1` is a plausible term name — nitrogen-1, a visit number — and the labels the
    prompt hands out are always two digits, so one digit is somebody's data.

    Written with an index that *is* in range, because an out-of-range one is left alone
    anyway and would pass whether the pattern were right or not.
    """

    assert len(ADDED) > 1, "the fixture must make N1 resolvable for this to bite"

    assert dereference("The N1 fixation pathway.", ADDED, SPONSORS) == (
        "The N1 fixation pathway."
    )


def test_a_name_the_model_already_wrote_out_is_not_doubled():
    reason = dereference(
        'N00 "Angiopoietin-Related Protein 3/8 Complex" matches.', ADDED, SPONSORS
    )

    assert reason.count("Angiopoietin-Related Protein 3/8 Complex") == 1


# --- how it reads --------------------------------------------------------------


def test_a_candidate_never_borrows_the_vocabulary_of_a_real_collision():
    """`COLLIDES` states a fact about a uniqueness rule. This is a model's opinion, and a
    reviewer has to be able to tell them apart without reading twice."""

    described = describe_candidate(
        {
            "confidence": "high",
            "sponsor_uid": "CTTerm_000042",
            "sponsor_name": "Angiopoietin-Like 3/8 Complex",
            "reason": "Same complex.",
        }
    )

    assert described.startswith("HIGH:CTTerm_000042:")
    assert "may be the same concept" in described
    assert "COLLIDES" not in described


# --- the seam ---------------------------------------------------------------------


def test_no_provider_configured_is_the_check_switched_off(monkeypatch):
    monkeypatch.setattr(settings, "semantic_provider", "")

    assert load_provider() is None


def test_a_provider_is_loaded_by_dotted_path(monkeypatch):
    """Adapting this to another gateway means naming your own module, never editing ours."""

    monkeypatch.setattr(
        settings,
        "semantic_provider",
        "standards_import.tests.integration.fake_semantic_provider:finds_nothing",
    )
    provider = load_provider()

    assert provider is not None
    assert provider("anything") == '{"pairs": []}'


@pytest.mark.parametrize(
    "path,expected",
    [
        ("no.colon.here", "not a `package.module:callable` path"),
        ("standards_import.nope:thing", "could not be loaded"),
        ("standards_import.services.semantic_matching:nope", "could not be loaded"),
        (
            "standards_import.services.semantic_matching:CONFIDENCE_ORDER",
            "not callable",
        ),
    ],
)
def test_a_provider_that_cannot_be_loaded_says_so_rather_than_going_quiet(
    monkeypatch, path, expected
):
    """Silently skipping a check the operator asked for is how a release gets a clean bill
    of health nobody earned."""

    monkeypatch.setattr(settings, "semantic_provider", path)

    with pytest.raises(ValidationException, match=expected):
        load_provider()


# --- what makes an answer reusable ------------------------------------------------


PROMPT = "ask me something"


def test_the_same_question_has_the_same_key():
    assert answer_key("mod:fn", "a-model", PROMPT) == answer_key(
        "mod:fn", "a-model", PROMPT
    )


@pytest.mark.parametrize(
    "provider,model,prompt",
    [
        ("other:fn", "a-model", PROMPT),
        ("mod:fn", "another-model", PROMPT),
        ("mod:fn", "a-model", PROMPT + " else"),
    ],
)
def test_anything_that_changes_the_answer_changes_the_key(provider, model, prompt):
    """All three decide what comes back. An answer from a different model, or from a
    provider pointed somewhere else, is not interchangeable with the one on file."""

    assert answer_key(provider, model, prompt) != answer_key(
        "mod:fn", "a-model", PROMPT
    )


def test_the_key_cannot_be_confused_by_where_the_parts_end():
    """Concatenation without a separator would make ('ab', 'c') and ('a', 'bc') the same
    question, which is the classic way a cache key of joined strings goes wrong."""

    assert answer_key("ab", "c", PROMPT) != answer_key("a", "bc", PROMPT)
