"""Asking a language model which CDISC additions duplicate a sponsor term by meaning.

`sponsor_matching` compares strings, and its own docstring admits what that cannot reach:
a sponsor term can share no strings at all with a CDISC term meaning the same thing. The
gap is measured, not theoretical. In the SDTM 2025-09-26 → 2026-03-27 release CDISC added
`Angiopoietin-Related Protein 3/8 Complex` to C67154 while the sponsor already had
`Angiopoietin-Like 3/8 Complex` — the same complex, with no content word in common. The
sibling codelist C65047 carries the same clash as the code `ANGPTL38`, where it matches
exactly. So the string check reports one and calls the other clean, which is worse than
missing both.

Everything here is pure and offline. The gateway call is the one function in
`semantic_provider`, and it is the only thing an organisation with a different LLM backend
has to replace.

**This is a suggestion, not a verdict, and the wording enforces that.** A string collision
on a name is a fact about a rule the main API enforces. A semantic candidate is a model's
opinion with a confidence attached. So nothing here is ever raised at a `match_tier`,
nothing it produces blocks a release by default, and it says "may be" rather than "is".
The two must not be confusable at a glance.

**Definitions are load-bearing, and this is why `get_sponsor_terms_in_codelists` reads a
field the string matcher never looks at.** Measured on the same benchmark: a generic
prompt with names alone scores 82.5% recall, a hand-tuned per-codelist prompt with names
alone scores 92.5%, and the *generic* prompt with definitions recovers the full 92.5%.
Facing some 1,500 codelists, no tool can carry a hand-written prompt for each; definitions
are how one generic prompt reaches domain-tuned performance.

Change the prompt and those numbers no longer describe what you have. That is also why
every finding records which model answered.
"""

import json
import logging
import re
from typing import Any

log = logging.getLogger(__name__)

# Worst first, matching `sponsor_matching`'s convention. Anything unrecognised sorts last
# rather than raising: a future provider may hand back a word this version never saw.
CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2}

# What `describe_candidate` writes first, and what a decision on one of these
# findings reads back to learn which sponsor term it is about. The same shape as a
# string collision's candidates, deliberately not the same words.
CONFIDENCE_NAMES = frozenset({name.upper() for name in CONFIDENCE_ORDER} | {"UNKNOWN"})

# Concrete renaming classes, named in the prompt. The single biggest lever found during
# tuning: naming them primes the model to attempt a domain lookup on an opaque code rather
# than skip it. The same reasoning scaffold without them scored ten points lower.
RENAMING_CLASSES = (
    "acronyms and abbreviations, gene or protein symbols, historical "
    "or vendor-specific names, trade names and alternative spellings"
)

# An `Nxx`/`Exx` label as the model writes it back inside its prose. Two or three digits
# and a word boundary either side, so a term legitimately called `N2`, or an `E1` inside a
# definition, is not mistaken for a reference to the list.
INDEX_REFERENCE = re.compile(r"\b([NE])(\d{2,3})\b")

# The model often writes a label with the name already beside it — `N01 'Event
# Adjudication Domain'` — which substitution would turn into the same name twice.
DOUBLED_NAME = re.compile(r"\"([^\"]+)\"\s*['\"]\1['\"]")


def clean(text: Any) -> str:
    """Collapses whitespace and strips the literal `_x000D_` CDISC exports carry."""

    return re.sub(r"\s+", " ", (text or "").replace("_x000D_", " ")).strip()


def build_prompt(
    codelist_name: str, added: list[dict[str, Any]], sponsors: list[dict[str, Any]]
) -> str:
    """One request covering a whole codelist. Pure, so it is tested without a gateway.

    Both lists whole, in one call, rather than scoring every added term against every
    sponsor term. The pairwise shape is an N x M blow-up that costs a fortune and answers
    worse, and this is the shape every recall figure above was measured with.

    Deliberately generic — no per-codelist hints. The strictness clause matters as much as
    the matching one: without it the model returns fragment-versus-whole and
    component-versus-complex pairs, which is exactly the noise that teaches a reviewer to
    stop reading the column.
    """

    new_list = "\n".join(
        f'- N{index:02d}: {term["name"]}  [submission: {term["submission_value"]}]'
        f'\n    def: {clean(term.get("definition"))}'
        for index, term in enumerate(added)
    )
    existing_list = "\n".join(
        f'- E{index:02d}: {sponsor.get("name")}  '
        f'[submission: {sponsor.get("submission_value")}]'
        f'\n    def: {clean(sponsor.get("definition"))}'
        for index, sponsor in enumerate(sponsors)
    )
    return f"""You are a controlled-terminology curator reconciling a sponsor's \
"{codelist_name}" codelist against new CDISC additions. Your job is to catch cases where \
importing a new CDISC term would duplicate a concept the sponsor already has \
under a different name.

The sponsor's names are written by domain specialists, so expect \
{RENAMING_CLASSES}. Two names that look nothing alike are frequently the same \
concept.

Each term is followed by its definition. The two sides were written \
independently, so wording will differ even for identical concepts - read for the \
underlying concept, not shared phrasing. Where a definition is uninformative, \
rely on the name.

Work through this for EVERY added term, in order:
1. Expand it to the underlying concept. Resolve acronyms, symbols and \
   historical or vendor-specific names to a canonical form.
2. Note its qualifiers: which variant, subtype, scale or derived form it is.
3. Scan the existing list for anything that resolves to the SAME concept with \
   the SAME qualifiers.

Count as duplicates: pure synonyms, acronym vs expansion, symbol vs full name, \
historical vs modern nomenclature, different word order.
Do NOT count: a part vs the whole, one variant or subtype vs another, a \
component vs a composite containing it, a raw value vs a form derived from it.

Use your domain knowledge. If you recognise an obscure abbreviation, say so - \
do not skip a term because its name is opaque.

TERMS BEING ADDED ({len(added)}):
{new_list}

EXISTING SPONSOR TERMS ({len(sponsors)}):
{existing_list}

First, for each added term, write one line: `Nxx | canonical concept | qualifiers`.
Then output the matches as JSON:
{{"pairs": [{{"new": "Nxx", "existing": "Exx", "confidence": "high|medium|low", \
"why": "one sentence"}}]}}. Empty list if none."""


def extract_pairs(text: str) -> list[dict[str, Any]]:
    """Pulls the pairs array out of a reply, however the model chose to wrap it.

    `raw_decode` from every `{` rather than slicing to the last `}`: the prompt asks for
    per-term reasoning before the JSON and the model often adds prose after it, so a naive
    slice spans more than one object and raises. That was a real failure during the work
    this is ported from, not a hypothetical one.

    Returns the largest well-formed `pairs` array found, or an empty list.
    """

    decoder = json.JSONDecoder()
    best: list[dict[str, Any]] = []
    for match in re.finditer(r"\{", text or ""):
        try:
            found, _ = decoder.raw_decode(text[match.start() :])
        except ValueError:
            continue
        if (
            isinstance(found, dict)
            and isinstance(found.get("pairs"), list)
            and len(found["pairs"]) >= len(best)
        ):
            best = found["pairs"]
    return best


def dereference(
    text: str, added: list[dict[str, Any]], sponsors: list[dict[str, Any]]
) -> str:
    """Replaces the model's `Nxx`/`Exx` labels in prose with the names they stand for.

    The reasons come back referring to the labels the prompt handed out — "E111 measures
    the fragment, while N23 measures total…" — which is coherent in the reply and
    meaningless in a review queue, where no list of labels exists. Observed on a real run
    rather than anticipated.

    Fixed here rather than by asking the model not to do it: the prompt is the one every
    recall figure was measured with, and rewording it to tidy up prose would put those
    numbers back in question for nothing.

    Substituted only where the index is in range, so a label the model invented is left as
    written rather than resolved to the wrong term.
    """

    def replace(match: re.Match) -> str:
        pool = added if match.group(1) == "N" else sponsors
        index = int(match.group(2))
        if index >= len(pool):
            return match.group(0)
        return f'"{pool[index].get("name")}"'

    return DOUBLED_NAME.sub(r'"\1"', INDEX_REFERENCE.sub(replace, text or ""))


def resolve_pairs(
    pairs: list[dict[str, Any]],
    added: list[dict[str, Any]],
    sponsors: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Turns the model's opaque indices into concept ids, keyed by the CDISC term.

    Done on this side of the seam so nothing downstream ever sees an index it has no way
    to validate. A malformed or out-of-range one is dropped with a warning rather than
    raising: one bad pair out of a dozen must not cost the whole codelist's answer.
    """

    by_term: dict[str, list[dict[str, Any]]] = {}
    for pair in pairs:
        new_index = _index(pair.get("new"), len(added))
        existing_index = _index(pair.get("existing"), len(sponsors))
        if new_index is None or existing_index is None:
            log.warning(
                "Ignoring an unusable pair from the model: %r -> %r",
                pair.get("new"),
                pair.get("existing"),
            )
            continue
        term, sponsor = added[new_index], sponsors[existing_index]
        by_term.setdefault(term["concept_id"], []).append(
            {
                "sponsor_uid": sponsor.get("uid"),
                "sponsor_name": sponsor.get("name"),
                "confidence": str(pair.get("confidence") or "unknown").lower(),
                "reason": dereference(clean(pair.get("why")), added, sponsors),
            }
        )
    return {
        concept_id: sorted(
            candidates,
            key=lambda candidate: CONFIDENCE_ORDER.get(candidate["confidence"], 9),
        )
        for concept_id, candidates in by_term.items()
    }


def describe_candidate(candidate: dict[str, Any]) -> str:
    """One candidate as a candidate value, in the shape the collision findings use.

    Confidence and sponsor uid lead, for the same reasons the tier and uid do in
    `sponsor_matching.describe_match` — and the words are deliberately none of that
    function's. `COLLIDES` states a fact about a uniqueness rule; this states a degree of
    belief, and a reviewer has to be able to tell them apart without reading twice.
    """

    return (
        f"{candidate['confidence'].upper()}"
        f":{candidate.get('sponsor_uid') or '-'}"
        f":may be the same concept as sponsor term "
        f"{candidate.get('sponsor_name')!r} — {candidate.get('reason') or 'no reason given'}"
    )


def _index(marker: Any, count: int) -> int | None:
    """`"N03"` -> `3`, or None where it is not a usable index into `count` items."""

    try:
        value = int(str(marker)[1:])
    except ValueError, TypeError:
        return None
    return value if 0 <= value < count else None
