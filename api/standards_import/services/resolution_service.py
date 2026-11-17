"""Deciding review items: matching stored rules, and turning a strategy into a value.

This is what replaces `resolve_inconsistencies` in `import_standards/cdisc_staging.py`.
The behaviour is deliberately close to that script's — the catalogue pecking order still
settles most disagreements, and synonyms are still merged rather than chosen between —
but where the script hardcoded those choices, they are now rows that can be read,
changed and attributed.

One difference is intentional. The script logged whatever it could not resolve and
carried on importing; here anything left undecided keeps the release out of MDR. The
disagreements it silently ignored are exactly the ones worth a human glance.
"""

import hashlib
import json
import logging
import re
from typing import Any, NamedTuple

from common.exceptions import ValidationException
from standards_import.models.inconsistencies import (
    FROM_NAMING_RULES,
    MAX_PATTERN_LENGTH,
    TIER_DEPENDENT_TYPES,
    InconsistencyStatus,
    InconsistencyType,
    ResolutionStrategy,
    RuleScope,
    is_informational,
)
from standards_import.services import semantic_matching, sponsor_matching

log = logging.getLogger(__name__)

# ADOPT_CDISC_NAME chooses between exactly two names: the one held and the one proposed.
ADOPT_NAME_CANDIDATE_COUNT = 2

# Rule fields that must agree with the finding whenever the rule sets them. The rule
# calls it `inconsistency_type`; on the finding it is just `type`.
RULE_DISCRIMINATORS = {
    "entity_type": "entity_type",
    "concept_id": "concept_id",
    "related_concept_id": "related_concept_id",
    "property": "property",
    "effective_date": "effective_date",
    "inconsistency_type": "type",
    "match_tier": "match_tier",
}

# What each scope has to pin down to be meaningful, checked when a rule is written so
# that matching itself stays a simple field comparison. Each entry is a set of
# alternatives:
# a CONCEPT rule names either the concept itself or the codelist whose terms it reaches,
# both of which are one concept.
SCOPE_REQUIREMENTS: dict[RuleScope, tuple[tuple[str, ...], ...]] = {
    RuleScope.OCCURRENCE: (("concept_id", "in_codelist_id"),),
    RuleScope.CONCEPT: (("concept_id", "in_codelist_id"),),
    RuleScope.PROPERTY: (("property",),),
    RuleScope.GLOBAL: (),
}

STRATEGIES_NEEDING_VALUE = (
    ResolutionStrategy.PICK_VALUE,
    ResolutionStrategy.CUSTOM_VALUE,
)

# Every other strategy settles a value in staging, and the worst a bad rule can do is
# stage the wrong string until somebody re-analyses. The first three change what MDR
# already holds — they retire a term, take one out of a codelist, or rename one — and a
# standing rule would do that unattended every quarter. `ACKNOWLEDGE` changes nothing in
# MDR, but is banned for the same underlying reason: every finding it settles is a fact
# about *today's* database — a term's current usage, or a duplicate/divergence that
# exists right now — rather than a convention a rule could stand for. A rule saved while
# one happens to look a certain way would wave through a materially different one next
# quarter, unattended. They are all decisions, not conventions.
NEVER_A_STANDING_RULE = {
    ResolutionStrategy.REMOVE_SPONSOR_FROM_CODELIST,
    ResolutionStrategy.RETIRE_SPONSOR_TERM,
    ResolutionStrategy.ADOPT_CDISC_NAME,
    ResolutionStrategy.ACKNOWLEDGE,
}

# Displacing a sponsor term breaks anything pointing at it, and nothing in OSB stops
# that — the main API has no usage check on its own retirement either. So this app makes
# one, deliberately at its most conservative: *any* reference at all refuses both, and
# migrating it through the main API comes first. Renaming is absent because a rename
# breaks nothing; every reference is by uid.
# What `save_as_rule` on a resolution is refused for. The three above, and one more for
# a different reason: a `USE_SUBMISSION_VALUE` rule has to name the codelist it takes the
# value from, and a resolution has no `in_codelist_id` to give it. Such a rule is written
# through `POST /resolution-rules` instead, where it can.
NOT_SAVEABLE_FROM_A_RESOLUTION = NEVER_A_STANDING_RULE | {
    ResolutionStrategy.USE_SUBMISSION_VALUE
}

NEEDS_AN_UNUSED_TERM = {
    ResolutionStrategy.REMOVE_SPONSOR_FROM_CODELIST,
    ResolutionStrategy.RETIRE_SPONSOR_TERM,
}

# Recorded as the author when the pecking order settled something rather than a rule
# or a person, so an audit can tell the three apart.
CATALOGUE_PRIORITY_AUTHOR = "catalogue-priority"

# Only I to V, which is as far as trial phases go. `IV` and `V` are tried before the
# `I{1,3}` run so that "IV" is not read as "I" followed by a stray "V".
ROMAN_NUMERAL_RE = re.compile(r"\b(IV|V|I{1,3})([ab])?\b")
ROMAN_VALUES = {"I": "1", "II": "2", "III": "3", "IV": "4", "V": "5"}

# `Phase 0` is named `Early Phase 1` rather than being converted like the rest.
PHASE_ZERO_RE = re.compile(r"^Phase 0(\s+Trial)?$", re.IGNORECASE)
EARLY_PHASE_1 = "Early Phase 1"

# A compound phase repeats the word: `Phase 1/2` is written `Phase 1/Phase 2`.
COMPOUND_PHASE_RE = re.compile(r"(?<=Phase )(\d[ab]?)((?:/\d[ab]?)+)")
TRAILING_TRIAL_RE = re.compile(r"\s+Trial$")


def candidate_fingerprint(candidates: list[dict[str, Any]]) -> str:
    """Digests the competing values, so a later run can tell whether they changed.

    Catalogue names are part of it: "SDTM says X, ADAM says Y" becoming "SDTM says X,
    ADAM says X, SEND says Y" is a different question, even though X and Y both persist.
    """

    normalised = sorted(
        (json.dumps(c["value"], sort_keys=True), sorted(c["catalogues"]))
        for c in candidates
    )
    return hashlib.sha256(json.dumps(normalised).encode()).hexdigest()


def rule_matches(rule: dict[str, Any], finding: dict[str, Any]) -> bool:
    """Reports whether a stored rule applies to a finding.

    A rule constrains only the fields it sets; everything it leaves unset it does not
    care about. Scope does not participate here — it is validated when the rule is
    written and used only to order matching from narrow to broad.
    """

    if not rule.get("enabled", True):
        return False

    for rule_field, finding_field in RULE_DISCRIMINATORS.items():
        expected = rule.get(rule_field)
        if expected is not None and expected != finding.get(finding_field):
            return False

    # A membership test rather than an equality one: this is how a rule reaches every
    # term of a codelist without having to name each of them.
    in_codelist = rule.get("in_codelist_id")
    if in_codelist is not None and in_codelist not in (
        finding.get("codelist_ids") or []
    ):
        return False

    # A guard on the value itself, so a narrow conditional rule can sit in front of a
    # broader one for the same codelist rather than the two competing.
    guard = rule.get("when")
    return guard is None or _value_matches(guard, finding)


def _value_matches(guard: str, finding: dict[str, Any]) -> bool:
    """Whether any competing value matches the guard.

    Sponsor-name findings carry a single value, which is what the seeded guards were
    written against. Where several catalogues disagree there is no one value to test,
    and "any of them looks like this" is the readable rule — testing whichever happened
    to be listed first is not.
    """

    try:
        return any(
            isinstance(candidate.get("value"), str)
            and re.search(guard, candidate["value"]) is not None
            for candidate in finding.get("candidates") or []
        )
    except re.error:
        log.warning("Rule guard %r is not a valid regular expression", guard)
        return False


def find_matching_rule(
    finding: dict[str, Any], rules: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Returns the narrowest rule that applies, or None.

    `rules` must already be ordered narrowest-first, which the repository does in Cypher.
    """

    for rule in rules:
        if rule_matches(rule, finding):
            return rule
    return None


class Request(NamedTuple):
    """Everything a strategy needs to work out its value."""

    finding: dict[str, Any]
    value: Any = None
    catalogue: str | None = None
    pattern: str | None = None
    in_codelist_id: str | None = None
    steps: tuple[tuple[str, str], ...] = ()

    @property
    def candidates(self) -> list[dict[str, Any]]:
        return self.finding.get("candidates") or []

    def sole_text_value(self, strategy: str) -> str:
        """The one text value this finding is about, or a refusal explaining why not."""

        ValidationException.raise_if(
            len(self.candidates) != 1,
            msg=f"{strategy} rewrites a single value; this finding does not have one.",
        )
        source = self.candidates[0]["value"]
        ValidationException.raise_if_not(
            isinstance(source, str), msg=f"{strategy} only applies to text values."
        )
        return str(source)


def _prefer_catalogue(request: Request) -> Any:
    ValidationException.raise_if_not(
        request.catalogue, msg="PREFER_CATALOGUE needs a catalogue to prefer."
    )
    for candidate in request.candidates:
        if request.catalogue in (candidate.get("catalogues") or []):
            return candidate["value"]
    raise ValidationException(
        msg=f"Catalogue '{request.catalogue}' supplied no value for this finding. "
        f"Available: {sorted(_all_catalogues(request.candidates))}."
    )


def _pick_value(request: Request) -> Any:
    ValidationException.raise_if(
        request.value is None, msg="PICK_VALUE needs the value to pick."
    )
    for candidate in request.candidates:
        if candidate["value"] == request.value:
            return request.value
    raise ValidationException(
        msg="PICK_VALUE must name one of the competing values; "
        "use CUSTOM_VALUE to supply one that no catalogue offered."
    )


def _custom_value(request: Request) -> Any:
    ValidationException.raise_if(
        request.value is None, msg="CUSTOM_VALUE needs a value."
    )
    return request.value


def _union_values(request: Request) -> Any:
    merged: list[str] = []
    for candidate in request.candidates:
        candidate_value = candidate["value"]
        if candidate_value is None:
            continue
        ValidationException.raise_if_not(
            isinstance(candidate_value, list),
            msg="UNION_VALUES only applies where every value is a list.",
        )
        for item in candidate_value:
            if item not in merged:
                merged.append(item)
    return merged


def _comparable(value: Any) -> Any:
    """A hashable stand-in for a property value, so values can be compared in a set.

    Synonyms arrive as lists, and a list cannot be a set element. Order is kept
    significant: two different orderings are two different values here.
    """

    if isinstance(value, list):
        return tuple(_comparable(item) for item in value)
    return value


def _strip_quotes(request: Request) -> Any:
    stripped = {
        _comparable(_strip(candidate["value"])) for candidate in request.candidates
    }
    ValidationException.raise_if(
        len(stripped) > 1,
        msg="Stripping quotes leaves more than one distinct value, so it does not "
        "settle this finding on its own.",
    )
    return _strip(request.candidates[0]["value"]) if request.candidates else None


def _accept_as_is(request: Request) -> Any:
    ValidationException.raise_if_not(
        request.candidates, msg="There is no value to accept."
    )
    ValidationException.raise_if(
        len(request.candidates) > 1,
        msg="More than one value is on offer, so accepting is ambiguous. Choose "
        "between them instead.",
    )
    return request.candidates[0]["value"]


def _regex_replace(request: Request) -> Any:
    ValidationException.raise_if_not(
        request.pattern, msg="REGEX_REPLACE needs a pattern."
    )
    source = request.sole_text_value("REGEX_REPLACE")
    return apply_pattern(request.pattern or "", str(request.value or ""), source)


def _rewrite(request: Request) -> Any:
    """Applies each substitution in turn.

    Several codelists need two or three with different replacements, which one pattern
    cannot express: Dosage Form turns `Dosage Form for Injection` into `For Injection`
    but `Tablet Dosage Form` into `Tablet`.
    """

    ValidationException.raise_if_not(
        request.steps, msg="REWRITE needs at least one step."
    )
    text = request.sole_text_value("REWRITE")
    for pattern, replacement in request.steps:
        text = apply_pattern(pattern, replacement, text)
    return text.strip()


def _trial_phase_name(request: Request) -> Any:
    """Rewrites a CDISC trial phase into the name the sponsor uses.

    Reproduces what the bootstrap script spells out term by term, and covers the ones it
    misses — `Phase V` and the `a`/`b` variants were simply left with their Roman
    numerals and their trailing ` Trial`.
    """

    text = request.sole_text_value("TRIAL_PHASE_NAME").strip()
    if PHASE_ZERO_RE.match(text):
        return EARLY_PHASE_1

    text = TRAILING_TRIAL_RE.sub("", text)
    text = ROMAN_NUMERAL_RE.sub(
        lambda match: ROMAN_VALUES[match.group(1)] + (match.group(2) or ""), text
    )
    return COMPOUND_PHASE_RE.sub(
        lambda match: match.group(1)
        + "".join(f"/Phase {part}" for part in match.group(2).split("/") if part),
        text,
    ).strip()


def _use_submission_value(request: Request) -> Any:
    submission_values = dict(
        zip(
            request.finding.get("codelist_ids") or [],
            request.finding.get("submission_values") or [],
        )
    )
    ValidationException.raise_if_not(
        submission_values,
        msg="This finding carries no submission values, so there is none to use.",
    )
    if request.in_codelist_id:
        ValidationException.raise_if_not(
            request.in_codelist_id in submission_values,
            msg=f"The term has no submission value in codelist "
            f"'{request.in_codelist_id}'. It belongs to {sorted(submission_values)}.",
        )
        return submission_values[request.in_codelist_id]

    distinct = set(submission_values.values())
    ValidationException.raise_if(
        len(distinct) > 1,
        msg="The term carries a different submission value in each of its codelists "
        f"({sorted(submission_values)}); name the codelist to take it from.",
    )
    return distinct.pop()


def _drop_term_from_codelist(request: Request) -> Any:
    """Returns the term to drop from the codelist this finding is about.

    A finding about one term names it, so nothing more is needed. A membership
    disagreement names none — it is about the codelist as a whole — so there the term
    has to be supplied as `value`, which is how the seeded 2017-09-29 rule says it is
    `C48262` that does not belong to Trial Type.

    The value produced is the term id rather than a property value; no property is
    rewritten, the term is left out when memberships are attached.
    """

    term_id = request.finding.get("related_concept_id") or request.value
    ValidationException.raise_if_not(
        term_id,
        msg="DROP_TERM_FROM_CODELIST removes one term from a codelist, and neither "
        "this finding nor the rule names which. Findings about a single term name it; "
        "for a membership disagreement, supply the term's concept id as `value`.",
    )
    return term_id


def _ignore(_request: Request) -> Any:
    """Accepts the data exactly as CDISC supplied it, so there is no value to produce."""

    return None


def _acknowledge(_request: Request) -> Any:
    """Confirms something already true of the database has been considered, so there
    is no value to produce.

    Mechanically identical to `_ignore` — neither writes anything — but kept as its own
    strategy so a reviewer sees "acknowledged" rather than "ignored" for a finding that
    is not a disagreement being waved through: a live reference, a near-duplicate, a
    diverged name. `decide()` gives it a different status for the same reason:
    `ACKNOWLEDGED`, not `IGNORED`.
    """

    return None


def sponsor_uid(value: Any) -> str | None:
    """The sponsor term a candidate names, whichever pass wrote it.

    A string collision leads with its match tier and a semantic one with its confidence;
    both are acted on by the same strategies, so both have to be readable here.
    """

    return sponsor_matching.sponsor_uid_from_candidate(
        value
    ) or sponsor_matching.sponsor_uid_from_candidate(
        value, semantic_matching.CONFIDENCE_NAMES
    )


def _sponsor_term_to_displace(request: Request) -> Any:
    """The sponsor term a collision decision acts on.

    The value produced is a uid rather than a property value, the way
    `DROP_TERM_FROM_CODELIST` produces a term id: nothing is being rewritten, something is
    being taken out of the way.

    One candidate needs no argument. Several do — a CDISC term can collide with more than
    one sponsor term in a codelist, and guessing which of them to retire is not a thing to
    do quietly.
    """

    named = sponsor_uid(request.value) or request.value
    uids = [sponsor_uid(candidate["value"]) for candidate in request.candidates]
    offered = [uid for uid in uids if uid]

    ValidationException.raise_if_not(
        offered,
        msg="This finding names no sponsor term, so there is nothing to act on.",
    )
    if named:
        ValidationException.raise_if_not(
            named in offered,
            msg=f"'{named}' is not one of the sponsor terms this finding collides with "
            f"({sorted(offered)}).",
        )
        return named
    ValidationException.raise_if(
        len(set(offered)) > 1,
        msg="This CDISC term collides with more than one sponsor term "
        f"({sorted(set(offered))}); name the one to act on as `value`.",
    )
    return offered[0]


def _adopt_cdisc_name(request: Request) -> Any:
    """The name the naming rules would give this term today.

    A `SPONSOR_NAME_DIVERGED` finding carries two candidates — what MDR holds and what
    the rules now produce — and each says which it is in its `source`. This takes the
    one from the rules. Taking the held one would be `IGNORE` wearing a different hat,
    except that it would also write a new name version saying nothing had changed.

    Findings raised before candidates carried a source are read by position instead,
    held first; the two are never mixed on one finding.
    """

    ValidationException.raise_if(
        len(request.candidates) != ADOPT_NAME_CANDIDATE_COUNT,
        msg="ADOPT_CDISC_NAME needs a finding offering a held name and a proposed one; this one does not.",
    )
    from_rules = [
        candidate
        for candidate in request.candidates
        if candidate.get("source") == FROM_NAMING_RULES
    ]
    proposed = (from_rules[0] if from_rules else request.candidates[1])["value"]
    ValidationException.raise_if_not(
        isinstance(proposed, str) and proposed,
        msg="The proposed name is not a name.",
    )
    return proposed


STRATEGY_HANDLERS = {
    ResolutionStrategy.PREFER_CATALOGUE: _prefer_catalogue,
    ResolutionStrategy.PICK_VALUE: _pick_value,
    ResolutionStrategy.CUSTOM_VALUE: _custom_value,
    ResolutionStrategy.UNION_VALUES: _union_values,
    ResolutionStrategy.STRIP_QUOTES: _strip_quotes,
    ResolutionStrategy.ACCEPT_AS_IS: _accept_as_is,
    ResolutionStrategy.REGEX_REPLACE: _regex_replace,
    ResolutionStrategy.REWRITE: _rewrite,
    ResolutionStrategy.TRIAL_PHASE_NAME: _trial_phase_name,
    ResolutionStrategy.USE_SUBMISSION_VALUE: _use_submission_value,
    ResolutionStrategy.DROP_TERM_FROM_CODELIST: _drop_term_from_codelist,
    ResolutionStrategy.IGNORE: _ignore,
    ResolutionStrategy.REMOVE_SPONSOR_FROM_CODELIST: _sponsor_term_to_displace,
    ResolutionStrategy.RETIRE_SPONSOR_TERM: _sponsor_term_to_displace,
    ResolutionStrategy.ADOPT_CDISC_NAME: _adopt_cdisc_name,
    ResolutionStrategy.ACKNOWLEDGE: _acknowledge,
}


# Which strategies settle which kind of review item. One table, served by
# `GET /resolution-strategies` and enforced by `guard_strategy_fits_finding`, so the menu a
# reviewer is shown and the menu the endpoint accepts cannot drift apart.
#
# Admissible on type grounds is the first gate, not the last: a strategy listed here can
# still refuse a particular finding — `ACCEPT_AS_IS` on two competing values, `UNION_VALUES`
# on text — and says why. What this table rules out is the combination that could never
# make sense, so that a reviewer learns it from the list rather than from a 400.
#
# Ordered with the usual choice first, which is the only opinion the list carries.
STRATEGIES_BY_TYPE: dict[InconsistencyType, tuple[ResolutionStrategy, ...]] = {
    InconsistencyType.CONFLICTING_VALUES: (
        ResolutionStrategy.PREFER_CATALOGUE,
        ResolutionStrategy.PICK_VALUE,
        ResolutionStrategy.CUSTOM_VALUE,
        ResolutionStrategy.UNION_VALUES,
        # A property can be disputed *and* quoted; where the quotes are the whole
        # disagreement, stripping them settles both.
        ResolutionStrategy.STRIP_QUOTES,
        ResolutionStrategy.IGNORE,
    ),
    InconsistencyType.UNWANTED_QUOTES: (
        ResolutionStrategy.STRIP_QUOTES,
        ResolutionStrategy.ACCEPT_AS_IS,
        ResolutionStrategy.PICK_VALUE,
        ResolutionStrategy.CUSTOM_VALUE,
        ResolutionStrategy.PREFER_CATALOGUE,
        ResolutionStrategy.UNION_VALUES,
        ResolutionStrategy.REGEX_REPLACE,
        ResolutionStrategy.REWRITE,
        ResolutionStrategy.IGNORE,
    ),
    # A membership disagreement is about which terms the codelist contains, not about a
    # property, so there is nowhere for a chosen value to be written. Staging holds the
    # union of every catalogue's terms: IGNORE accepts that, DROP_TERM_FROM_CODELIST
    # narrows it.
    InconsistencyType.INCONSISTENT_TERM_SETS: (
        ResolutionStrategy.IGNORE,
        ResolutionStrategy.DROP_TERM_FROM_CODELIST,
    ),
    InconsistencyType.CONFLICTING_SUBMISSION_VALUES: (
        ResolutionStrategy.PREFER_CATALOGUE,
        ResolutionStrategy.PICK_VALUE,
        ResolutionStrategy.CUSTOM_VALUE,
        ResolutionStrategy.STRIP_QUOTES,
        ResolutionStrategy.DROP_TERM_FROM_CODELIST,
        ResolutionStrategy.IGNORE,
    ),
    InconsistencyType.CODELIST_PAIRING: (
        ResolutionStrategy.ACCEPT_AS_IS,
        ResolutionStrategy.PICK_VALUE,
        ResolutionStrategy.CUSTOM_VALUE,
        ResolutionStrategy.IGNORE,
    ),
    InconsistencyType.SPONSOR_NAME: (
        ResolutionStrategy.ACCEPT_AS_IS,
        ResolutionStrategy.CUSTOM_VALUE,
        ResolutionStrategy.REGEX_REPLACE,
        ResolutionStrategy.REWRITE,
        ResolutionStrategy.TRIAL_PHASE_NAME,
        ResolutionStrategy.USE_SUBMISSION_VALUE,
        ResolutionStrategy.PICK_VALUE,
        ResolutionStrategy.IGNORE,
    ),
    # The sponsor impact kinds are not about a value: the disagreement is between this
    # release and what MDR already holds, so nothing a value-producing strategy could
    # return has anywhere to be written. What each takes is what can actually be done.
    #
    # `ACKNOWLEDGE` rather than `IGNORE`: where the finding is informational it is not a
    # data disagreement being waved through, and the two strategies read differently on
    # purpose. An `EXACT` collision is OPEN and blocks import, so `strategies_for` takes
    # `ACKNOWLEDGE` off its menu: the tier, not the type, decides that.
    InconsistencyType.SPONSOR_TERM_DUPLICATE: (
        ResolutionStrategy.ACKNOWLEDGE,
        ResolutionStrategy.REMOVE_SPONSOR_FROM_CODELIST,
        ResolutionStrategy.RETIRE_SPONSOR_TERM,
    ),
    # The same problem as above, found by a different means, so the same answers apply.
    InconsistencyType.SPONSOR_TERM_SEMANTIC_DUPLICATE: (
        ResolutionStrategy.ACKNOWLEDGE,
        ResolutionStrategy.REMOVE_SPONSOR_FROM_CODELIST,
        ResolutionStrategy.RETIRE_SPONSOR_TERM,
    ),
    # Nothing can be done here through this API: it has no way to retire a codelist, and
    # merging two is a person's job in the main API. Acknowledging it is the whole answer.
    InconsistencyType.SPONSOR_CODELIST_DUPLICATE: (ResolutionStrategy.ACKNOWLEDGE,),
    InconsistencyType.SPONSOR_NAME_DIVERGED: (
        ResolutionStrategy.ACKNOWLEDGE,
        ResolutionStrategy.ADOPT_CDISC_NAME,
    ),
    # A fact about today's database, not a value in dispute: nothing can be done about a
    # CDISC change itself, so acknowledging the reference is the whole menu.
    # `ACKNOWLEDGE` rather than `IGNORE` — this is not a disagreement being waved
    # through, it is a live reference somebody has considered and accepted.
    InconsistencyType.CDISC_TERM_SUBMISSION_VALUE_CHANGED: (
        ResolutionStrategy.ACKNOWLEDGE,
    ),
    InconsistencyType.CDISC_TERM_REMOVED_FROM_CODELIST: (
        ResolutionStrategy.ACKNOWLEDGE,
    ),
}

# What each strategy has to be given, beyond the finding, to produce its value. Served
# alongside the table above so a client knows which inputs to ask for; `validate_rule`
# checks the same things when a rule is written.
STRATEGY_INPUTS: dict[ResolutionStrategy, tuple[str, ...]] = {
    ResolutionStrategy.PREFER_CATALOGUE: ("catalogue",),
    ResolutionStrategy.PICK_VALUE: ("value",),
    ResolutionStrategy.CUSTOM_VALUE: ("value",),
    # `value` is the replacement and is optional: left out, the match is deleted, which
    # is what every seeded "drop the trailing word" rule does.
    ResolutionStrategy.REGEX_REPLACE: ("pattern",),
    ResolutionStrategy.REWRITE: ("steps",),
}

STRATEGY_DESCRIPTIONS: dict[ResolutionStrategy, str] = {
    ResolutionStrategy.PREFER_CATALOGUE: "Takes the value that catalogue supplied.",
    ResolutionStrategy.PICK_VALUE: "Takes one of the competing values, named exactly.",
    ResolutionStrategy.CUSTOM_VALUE: "Takes a value nobody supplied.",
    ResolutionStrategy.UNION_VALUES: (
        "Merges the candidates, dropping duplicates. Lists only."
    ),
    ResolutionStrategy.ACCEPT_AS_IS: (
        "Keeps the single value on offer. Refuses where there is more than one."
    ),
    ResolutionStrategy.STRIP_QUOTES: "Removes the surrounding quotes.",
    ResolutionStrategy.REGEX_REPLACE: (
        "One substitution over the value: `pattern` to find, `value` to put in its place "
        "— left out, the match is deleted."
    ),
    ResolutionStrategy.REWRITE: "Several ordered substitutions, applied in order.",
    ResolutionStrategy.TRIAL_PHASE_NAME: (
        "Rewrites a CDISC trial phase into the sponsor's form."
    ),
    ResolutionStrategy.USE_SUBMISSION_VALUE: (
        "Uses the term's submission value as its name. Unambiguous only where the term "
        "carries the same one in every codelist it belongs to; a rule names the "
        "codelist with `in_codelist_id`."
    ),
    ResolutionStrategy.DROP_TERM_FROM_CODELIST: (
        "Leaves the term out of the codelist this release. Where the finding does not "
        "name a term, `value` does."
    ),
    ResolutionStrategy.IGNORE: "Accepts the data exactly as shipped and changes nothing.",
    ResolutionStrategy.REMOVE_SPONSOR_FROM_CODELIST: (
        "Closes the sponsor term's membership of that codelist. Refused while anything "
        "still refers to the term. Where the CDISC term collides with several, `value` "
        "names which."
    ),
    ResolutionStrategy.RETIRE_SPONSOR_TERM: (
        "Retires the sponsor term, both halves, and closes that membership. Refused "
        "while anything still refers to the term."
    ),
    ResolutionStrategy.ADOPT_CDISC_NAME: (
        "Renames the term to what the naming rules produce today. The one case where "
        "the import writes over a sponsor preferred name it did not create."
    ),
    ResolutionStrategy.ACKNOWLEDGE: (
        "Confirms this has been considered and the release may proceed. Changes "
        "nothing, like IGNORE — the difference is what it means: something already "
        "true of the database has been accepted, not a disagreement waved through."
    ),
}


def strategies_for(
    finding_type: InconsistencyType, match_tier: str | None = None
) -> tuple[ResolutionStrategy, ...]:
    """The menu for one finding: its type's entry, less `ACKNOWLEDGE` where the type
    is tier-dependent and the tier makes the finding OPEN.

    An `EXACT` `SPONSOR_TERM_DUPLICATE` breaks a uniqueness rule and has to be acted on,
    not acknowledged. Other OPEN kinds (the `CDISC_TERM_*` usage findings) are settled
    by `ACKNOWLEDGE` alone, so this is deliberately not "every OPEN finding".
    """

    menu = STRATEGIES_BY_TYPE[finding_type]
    if finding_type.value in TIER_DEPENDENT_TYPES and not is_informational(
        finding_type.value, match_tier
    ):
        return tuple(
            strategy
            for strategy in menu
            if strategy is not ResolutionStrategy.ACKNOWLEDGE
        )
    return menu


def guard_strategy_fits_finding(
    strategy: ResolutionStrategy, finding: dict[str, Any]
) -> None:
    """Refuses a strategy that could never settle a finding of this kind.

    The per-finding refusals — a catalogue that supplied nothing, a value nobody offered —
    stay with the handlers, where the finding's own values decide. This is only the first
    gate, and it names the whole menu so a caller does not have to try each in turn.
    """

    finding_type = finding.get("type")
    try:
        allowed = strategies_for(
            InconsistencyType(str(finding_type)), finding.get("match_tier")
        )
    except ValueError:
        return
    ValidationException.raise_if_not(
        strategy in allowed,
        msg=f"{strategy.value} does not apply to a {finding_type} finding, which takes "
        f"one of {[option.value for option in allowed]}.",
    )


def resolve_value(
    strategy: ResolutionStrategy,
    finding: dict[str, Any],
    value: Any = None,
    catalogue: str | None = None,
    pattern: str | None = None,
    in_codelist_id: str | None = None,
    steps: tuple[tuple[str, str], ...] = (),
    title_case: bool = False,
) -> Any:
    """Turns a strategy into the concrete value analysis should apply.

    Raises ValidationException when the strategy cannot be applied to this finding —
    naming a catalogue that supplied nothing, picking a value nobody offered, or
    merging values that are not lists.
    """

    guard_strategy_fits_finding(strategy, finding)

    handler = STRATEGY_HANDLERS.get(strategy)
    if handler is None:
        return None

    resolved = handler(
        Request(
            finding=finding,
            value=value,
            catalogue=catalogue,
            pattern=pattern,
            in_codelist_id=in_codelist_id,
            steps=steps,
        )
    )
    # Applied centrally so it works for whichever strategy produced the text — in
    # practice the submission values, which CDISC ships in upper case.
    if title_case and isinstance(resolved, str):
        return resolved.title()
    return resolved


def decide(
    finding: dict[str, Any],
    strategy: ResolutionStrategy,
    author_id: str,
    value: Any = None,
    catalogue: str | None = None,
    note: str | None = None,
    rule_uid: str | None = None,
    automatic: bool = False,
    pattern: str | None = None,
    in_codelist_id: str | None = None,
    steps: tuple[tuple[str, str], ...] = (),
    title_case: bool = False,
) -> tuple[InconsistencyStatus, dict[str, Any]]:
    """Builds the decision record for a finding, and the status it puts it in.

    `automatic` distinguishes a decision analysis made for itself from one a person
    made, which is the difference between AUTO_RESOLVED and RESOLVED. It is passed
    explicitly rather than inferred from `rule_uid`, because the catalogue pecking
    order decides automatically without any rule behind it.
    """

    resolved = resolve_value(
        strategy,
        finding,
        value=value,
        catalogue=catalogue,
        pattern=pattern,
        in_codelist_id=in_codelist_id,
        steps=steps,
        title_case=title_case,
    )
    if strategy is ResolutionStrategy.IGNORE:
        status = InconsistencyStatus.IGNORED
    elif strategy is ResolutionStrategy.ACKNOWLEDGE:
        status = InconsistencyStatus.ACKNOWLEDGED
    else:
        status = (
            InconsistencyStatus.AUTO_RESOLVED
            if automatic
            else InconsistencyStatus.RESOLVED
        )
    return status, {
        "strategy": strategy.value,
        "resolved_value": resolved,
        "chosen_catalogue": catalogue,
        "author_id": author_id,
        "note": note,
        "rule_uid": rule_uid,
    }


def auto_resolve(
    finding: dict[str, Any],
    rules: list[dict[str, Any]],
    catalogue_priority: list[str],
) -> tuple[InconsistencyStatus, dict[str, Any]] | None:
    """Settles a finding without asking, or returns None to leave it open.

    A stored rule is tried first. Failing that, and only for a straight disagreement
    over a value, the catalogue pecking order picks a winner — which is what the
    bootstrap script does for every conflict it meets.
    """

    rule = find_matching_rule(finding, rules)
    if rule is not None:
        try:
            return decide(
                finding,
                ResolutionStrategy(rule["strategy"]),
                author_id=rule["author_id"],
                value=rule.get("value"),
                catalogue=rule.get("catalogue"),
                pattern=rule.get("pattern"),
                in_codelist_id=rule.get("in_codelist_id"),
                steps=tuple(
                    (step["pattern"], step["replacement"])
                    for step in rule.get("steps") or []
                ),
                title_case=bool(rule.get("title_case")),
                note=rule.get("note"),
                rule_uid=rule["uid"],
                automatic=True,
            )
        except ValidationException as exc:
            # A rule that cannot apply here is a configuration problem, not a reason to
            # fail the run — but it must be visible rather than swallowed.
            log.warning(
                "Rule %s matched finding %s but could not be applied: %s",
                rule["uid"],
                finding["uid"],
                exc.msg,
            )
        except Exception:  # pylint: disable=broad-except
            # A strategy meeting a value shape it cannot handle is a bug, but analysis
            # walks tens of thousands of findings and one of them must not take the
            # whole run down. Left open, logged with a traceback, and still importable
            # once a person settles it.
            log.exception(
                "Rule %s matched finding %s but failed unexpectedly",
                rule["uid"],
                finding["uid"],
            )

    if finding.get("type") == InconsistencyType.CONFLICTING_VALUES.value:
        winner = preferred_by_catalogue(finding, catalogue_priority)
        if winner is not None:
            return decide(
                finding,
                ResolutionStrategy.PREFER_CATALOGUE,
                author_id=CATALOGUE_PRIORITY_AUTHOR,
                catalogue=winner,
                note=f"Settled by catalogue priority: {winner}.",
                automatic=True,
            )

    return None


def preferred_by_catalogue(
    finding: dict[str, Any], catalogue_priority: list[str]
) -> str | None:
    """Returns the most authoritative catalogue that supplied a value here.

    Catalogue names carry the effective date (`SDTM CT 2025-09-26`) while the pecking
    order is by catalogue (`SDTM CT`), so the comparison is by prefix.
    """

    for preferred in catalogue_priority:
        for candidate in finding.get("candidates") or []:
            for name in candidate.get("catalogues") or []:
                if name == preferred or name.startswith(f"{preferred} "):
                    return name
    return None


def build_rule_uid(rule: dict[str, Any]) -> str:
    """Composes a rule's uid from what it discriminates on.

    Saving the same rule twice then updates it instead of stacking a duplicate that
    would compete with itself during matching.
    """

    parts = [
        "rule",
        str(rule.get("scope") or "GLOBAL"),
        str(rule.get("entity_type") or "-"),
        str(rule.get("concept_id") or "-"),
        str(rule.get("related_concept_id") or "-"),
        str(rule.get("property") or "-"),
        str(rule.get("effective_date") or "-"),
        str(rule.get("inconsistency_type") or "-"),
        str(rule.get("in_codelist_id") or "-"),
    ]
    # Appended only when set, so a rule written before this discriminator existed keeps
    # the uid it already has and is updated rather than duplicated alongside itself.
    if rule.get("match_tier"):
        parts.append(str(rule["match_tier"]))
    return "_".join(parts)


def validate_rule(rule: dict[str, Any]) -> None:
    """Checks a rule pins down what its scope claims to, before it is stored."""

    strategy = ResolutionStrategy(rule["strategy"])
    if strategy is ResolutionStrategy.ACKNOWLEDGE:
        raise ValidationException(
            msg="ACKNOWLEDGE settles a finding about today's database rather than a "
            "standing convention — what it found may look different next quarter. "
            "Settle the item without `save_as_rule`."
        )
    ValidationException.raise_if(
        strategy in NEVER_A_STANDING_RULE,
        msg=f"{strategy.value} changes what the MDR database already holds, so it is "
        "taken one finding at a time and never stands for every release. A rule doing "
        "this would retire sponsor content on its own, quarter after quarter, without "
        "anyone looking. Settle the item without `save_as_rule`.",
    )

    scope = RuleScope(rule["scope"])
    for alternatives in SCOPE_REQUIREMENTS[scope]:
        ValidationException.raise_if_not(
            any(rule.get(field) for field in alternatives),
            msg=f"A {scope.value} rule needs "
            + " or ".join(f"`{field}`" for field in alternatives)
            + ", otherwise it would apply far more widely than its scope claims.",
        )

    for field in ("pattern", "when"):
        if rule.get(field):
            check_regex(rule[field], field)
    for index, step in enumerate(rule.get("steps") or []):
        check_regex(step["pattern"], f"steps[{index}].pattern")

    if strategy in STRATEGIES_NEEDING_VALUE:
        ValidationException.raise_if(
            rule.get("value") in (None, "", []),
            msg=f"A {strategy.value} rule needs `value`, and it cannot be empty.",
        )
    if strategy is ResolutionStrategy.PREFER_CATALOGUE:
        ValidationException.raise_if_not(
            rule.get("catalogue"),
            msg="A PREFER_CATALOGUE rule needs `catalogue`.",
        )
    if strategy is ResolutionStrategy.REGEX_REPLACE:
        ValidationException.raise_if_not(
            rule.get("pattern"), msg="A REGEX_REPLACE rule needs `pattern`."
        )
    if strategy is ResolutionStrategy.REWRITE:
        ValidationException.raise_if_not(
            rule.get("steps"), msg="A REWRITE rule needs at least one step."
        )
    if strategy is ResolutionStrategy.USE_SUBMISSION_VALUE:
        ValidationException.raise_if_not(
            rule.get("in_codelist_id"),
            msg="A USE_SUBMISSION_VALUE rule needs `in_codelist_id`: a term can carry a "
            "different submission value in each codelist it belongs to.",
        )


def check_regex(pattern: str, field: str) -> None:
    """Rejects a regular expression that is too long or does not compile.

    Run when a rule is stored, so a bad one fails the request that supplied it rather
    than every analysis run that later evaluates the rule.
    """

    ValidationException.raise_if(
        len(pattern) > MAX_PATTERN_LENGTH,
        msg=f"`{field}` is longer than {MAX_PATTERN_LENGTH} characters.",
    )
    try:
        re.compile(pattern)
    except re.error as exc:
        raise ValidationException(
            msg=f"`{field}` is not a valid regular expression: {exc}"
        ) from exc


def apply_pattern(pattern: str, replacement: str, text: str) -> str:
    """Runs one regular-expression substitution, with the pattern length capped."""

    ValidationException.raise_if(
        len(pattern) > MAX_PATTERN_LENGTH,
        msg=f"The pattern is longer than {MAX_PATTERN_LENGTH} characters.",
    )
    try:
        return re.sub(pattern, replacement, text).strip()
    except re.error as exc:
        raise ValidationException(
            msg=f"The pattern is not a valid regular expression: {exc}"
        ) from exc


def _strip(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip('"').replace('""', '"')
    if isinstance(value, list):
        return [_strip(item) for item in value]
    return value


def _all_catalogues(candidates: list[dict[str, Any]]) -> set[str]:
    return {
        name for candidate in candidates for name in (candidate.get("catalogues") or [])
    }
