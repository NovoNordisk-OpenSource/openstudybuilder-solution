"""Review items raised by analysis, and the decisions that settle them.

Findings and decisions are deliberately different things. A finding is derived: every
analysis run re-derives it from the staged files and throws away what it replaced. A
decision is an input: somebody chose it, it is attributed and timestamped, and it has
to outlive the run that prompted it.

That only works because a finding's uid is deterministic — the same disagreement over
the same concept and property at the same effective date always produces the same uid,
so re-analysis reattaches the decision that was already made. What a decision must not
survive is the underlying values changing; `candidate_fingerprint` is what detects that.
"""

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    StrictBool,
    StrictInt,
    StringConstraints,
)


def _parse_iso_date(value: object) -> object:
    """Accepts `YYYY-MM-DD` or a date; pydantic's lax mode would also take 0 as 1970-01-01."""
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d").date()
    if value is None or isinstance(value, date):
        return value
    raise ValueError("Input should be a valid date in YYYY-MM-DD format")


IsoDate = Annotated[date, BeforeValidator(_parse_iso_date)]


class EntityType(StrEnum):
    CODELIST = "CODELIST"
    TERM = "TERM"


class ReviewPass(StrEnum):
    """Which step raises a kind of review item.

    A finding's kind is fixed at the moment it exists, so this is really a property of
    `InconsistencyType` rather than of any one finding — every `SPONSOR_NAME` is
    `ANALYSIS`, every `SPONSOR_NAME_DIVERGED` is `SPONSOR_IMPACT`, with no exceptions.
    `ANALYSIS` types must be settled, and the release re-analysed, before
    `POST /effective-dates/{date}/sponsor-impact` can run at all — see
    `guard_assessable` and "What it compares" in the README.
    """

    ANALYSIS = "ANALYSIS"
    """Raised by `POST /effective-dates/{date}/analysis`. Must be settled — and the
    release re-analysed — before sponsor impact can be assessed."""

    SPONSOR_IMPACT = "SPONSOR_IMPACT"
    """Raised by `POST /effective-dates/{date}/sponsor-impact`, which only runs once
    every `ANALYSIS` item is settled and applied."""


class InconsistencyType(StrEnum):
    """The kinds of review item that analysis can raise."""

    CONFLICTING_VALUES = "CONFLICTING_VALUES"
    """Catalogues of the same release disagree on a property of the same concept."""

    UNWANTED_QUOTES = "UNWANTED_QUOTES"
    """A value arrives wrapped in double quotes."""

    INCONSISTENT_TERM_SETS = "INCONSISTENT_TERM_SETS"
    """Catalogues disagree on which terms a codelist contains."""

    CONFLICTING_SUBMISSION_VALUES = "CONFLICTING_SUBMISSION_VALUES"
    """A term has more than one submission value within the same codelist."""

    CODELIST_PAIRING = "CODELIST_PAIRING"
    """Which code codelist a name codelist pairs with."""

    SPONSOR_NAME = "SPONSOR_NAME"
    """What a term new to the MDR database should be called."""

    SPONSOR_TERM_DUPLICATE = "SPONSOR_TERM_DUPLICATE"
    """A term this release adds to a codelist means the same as a sponsor-defined term
    already in it. A term submission value depends on the codelist, so this collision
    belongs to the membership, not to the term."""

    SPONSOR_CODELIST_DUPLICATE = "SPONSOR_CODELIST_DUPLICATE"
    """A codelist this release introduces covers the same ground as a sponsor-defined
    one. Informational: the API has no way to retire a codelist, so the remedy is a
    person merging the two."""

    SPONSOR_TERM_SEMANTIC_DUPLICATE = "SPONSOR_TERM_SEMANTIC_DUPLICATE"
    """A language model estimates a term this release adds means the same as a sponsor term
    already in the codelist, under a different submission value. An opinion with a confidence
    level, not a fact about a uniqueness rule — it does not block the release. Raised only
    where the string comparison found nothing, so it is always an incremental answer rather
    than a second opinion on one already given."""

    SPONSOR_NAME_DIVERGED = "SPONSOR_NAME_DIVERGED"
    """CDISC has changed a term whose sponsor name in MDR is not what the naming rules
    would produce today — so the reason it was named that way may no longer hold."""

    CDISC_TERM_SUBMISSION_VALUE_CHANGED = "CDISC_TERM_SUBMISSION_VALUE_CHANGED"
    """CDISC has given a term a different submission value in a codelist it already
    belongs to, and something in the MDR database still refers to the term. This is not
    a data error — a routine CDISC change — but raised only where the term is actually
    referred to, because a reference keyed on the old value can silently stop matching
    what it meant to.
    Codelist as `concept_id`, term as `related_concept_id`: the fact belongs to the
    membership, not to the term alone."""

    CDISC_TERM_REMOVED_FROM_CODELIST = "CDISC_TERM_REMOVED_FROM_CODELIST"
    """CDISC has taken a term out of a codelist it used to belong to, and something in
    the MDR database still refers to the term. Not a data error — a routine CDISC
    change — but raised only where the term is actually referred to, because losing the
    membership can leave that reference pointing at a term no longer offered here.
    Codelist as `concept_id`, term as `related_concept_id`: the fact belongs to the
    membership, not to the term alone.."""


SPONSOR_IMPACT_TYPES = frozenset(
    {
        InconsistencyType.SPONSOR_TERM_DUPLICATE.value,
        InconsistencyType.SPONSOR_TERM_SEMANTIC_DUPLICATE.value,
        InconsistencyType.SPONSOR_CODELIST_DUPLICATE.value,
        InconsistencyType.SPONSOR_NAME_DIVERGED.value,
        InconsistencyType.CDISC_TERM_SUBMISSION_VALUE_CHANGED.value,
        InconsistencyType.CDISC_TERM_REMOVED_FROM_CODELIST.value,
    }
)
"""The kinds raised by the sponsor impact assessment rather than by analysis."""

# Derived rather than listed, so a new kind cannot be added to the enum and quietly left
# out of both passes. The two sets partition the enum, and each pass prunes only its own
# — otherwise analysis would delete the assessment's findings, decisions and all.
ANALYSIS_TYPES = frozenset(member.value for member in InconsistencyType) - (
    SPONSOR_IMPACT_TYPES
)


def review_pass_of(inconsistency_type: InconsistencyType) -> ReviewPass:
    """Which step raises this kind — `ANALYSIS_TYPES`/`SPONSOR_IMPACT_TYPES` restated
    as the enum a client actually wants, rather than two frozensets it would have to
    know about."""

    return (
        ReviewPass.SPONSOR_IMPACT
        if inconsistency_type.value in SPONSOR_IMPACT_TYPES
        else ReviewPass.ANALYSIS
    )


# The four kinds that are informational rather than blocking, at least some of the
# time — settled only by ACKNOWLEDGE, never auto-resolved. NOT a clean "these types are
# always informational" set: SPONSOR_TERM_DUPLICATE is informational only away from the
# EXACT match tier — an EXACT collision breaks a uniqueness rule the main API enforces
# and stays OPEN. Use `is_informational` rather than membership here when a tier is
# known.
INFORMATIONAL_TYPES = frozenset(
    {
        InconsistencyType.SPONSOR_TERM_DUPLICATE.value,
        InconsistencyType.SPONSOR_TERM_SEMANTIC_DUPLICATE.value,
        InconsistencyType.SPONSOR_CODELIST_DUPLICATE.value,
        InconsistencyType.SPONSOR_NAME_DIVERGED.value,
    }
)

# Of INFORMATIONAL_TYPES, the one kind whose status depends on match_tier rather than
# holding for every instance. SPONSOR_TERM_SEMANTIC_DUPLICATE carries no EXACT tier at
# all (a model's opinion is never a fact about a broken rule) and SPONSOR_CODELIST_
# DUPLICATE/SPONSOR_NAME_DIVERGED are informational regardless of whatever tier they
# carry — only SPONSOR_TERM_DUPLICATE genuinely switches on it.
TIER_DEPENDENT_TYPES = frozenset({InconsistencyType.SPONSOR_TERM_DUPLICATE.value})

BLOCKING_TIER = "EXACT"


def is_informational(finding_type: str, match_tier: str | None) -> bool:
    """Whether a finding of this kind and tier is raised as INFORMATIONAL, not OPEN.

    The single definition of the rule. `clear_decision`'s Cypher cannot call it and
    restates it (a missing tier counts as `EXACT` there too); keep the two in step.
    """

    if finding_type not in INFORMATIONAL_TYPES:
        return False
    if finding_type in TIER_DEPENDENT_TYPES:
        return (match_tier or BLOCKING_TIER) != BLOCKING_TIER
    return True


class MatchTier(StrEnum):
    """How closely a CDISC value and a sponsor-defined one agree.

    The tiers are not degrees of tidiness; they separate a broken invariant from a
    judgement call. Only `EXACT` breaks something the main API enforces — a term's name
    must be unique among the terms of the codelists it belongs to, and a codelist's name
    and submission value are unique outright. Nothing in this app's Cypher stops an exact
    collision, so it imports silently and leaves MDR in a state the main API then refuses
    to edit. The other two break nothing at all: they mean two things end up meaning the
    same under different spellings, which is for a person to weigh.
    """

    EXACT = "EXACT"
    """The values are identical. Importing this would break the uniqueness rule."""

    CASE_INSENSITIVE = "CASE_INSENSITIVE"
    """They differ only in case."""

    NORMALIZED = "NORMALIZED"
    """They differ only in spacing or punctuation."""


class InconsistencyStatus(StrEnum):
    """How a review item currently stands — still open, or settled and by whom."""

    OPEN = "OPEN"
    """Nobody has decided yet. Blocks import of the release."""

    AUTO_RESOLVED = "AUTO_RESOLVED"
    """Settled by a stored rule rather than by a person."""

    RESOLVED = "RESOLVED"
    """Settled by a person, who changed a value."""

    IGNORED = "IGNORED"
    """Accepted as-is; the values are left exactly as CDISC supplied them."""

    INFORMATIONAL = "INFORMATIONAL"
    """Not blocking, and cannot be made to — a fact worth noting rather than a decision
    holding up the release. Raised directly at this status, never through a rule; the
    only way forward is `ACKNOWLEDGE`, which settles it as `ACKNOWLEDGED`."""

    ACKNOWLEDGED = "ACKNOWLEDGED"
    """Settled by a person, who considered a fact about today's database and changed
    nothing. Kept apart from `RESOLVED` so counts can tell "a value was chosen" from
    "nothing needed choosing" — see `ResolutionStrategy.ACKNOWLEDGE`."""


class ResolutionStrategy(StrEnum):
    """How a review item is settled, and what value that produces."""

    PREFER_CATALOGUE = "PREFER_CATALOGUE"
    """Take the value supplied by a named catalogue."""

    PICK_VALUE = "PICK_VALUE"
    """Take one of the competing values."""

    CUSTOM_VALUE = "CUSTOM_VALUE"
    """Use a value that none of the catalogues supplied."""

    UNION_VALUES = "UNION_VALUES"
    """Merge every competing list into one, de-duplicated. For list properties."""

    STRIP_QUOTES = "STRIP_QUOTES"
    """Remove the surrounding double quotes."""

    DROP_TERM_FROM_CODELIST = "DROP_TERM_FROM_CODELIST"
    """Leaves the CDISC term out of the codelist this release."""

    IGNORE = "IGNORE"
    """Accept the disagreement and change nothing."""

    ACCEPT_AS_IS = "ACCEPT_AS_IS"
    """Take the single value on offer. Refuses when there is more than one, which is
    what turns an ambiguous pairing into something a person has to look at."""

    REGEX_REPLACE = "REGEX_REPLACE"
    """Derive the value by rewriting the one on offer. Needs `pattern`; `value` is the
    replacement. This is what makes the naming transforms expressible as data."""

    TRIAL_PHASE_NAME = "TRIAL_PHASE_NAME"
    """Name a trial phase the way the sponsor writes it: drop the trailing ` Trial`,
    turn Roman numerals into digits keeping any `a`/`b` suffix, and spell out each part
    of a compound — `Phase I/II/III Trial` becomes `Phase 1/Phase 2/Phase 3`. Plain
    substitution cannot do this: it is a lookup over however many numerals the value
    holds. `Phase 0` is the one exception and becomes `Early Phase 1`."""

    REWRITE = "REWRITE"
    """Apply an ordered list of substitutions. Some codelists need two or three with
    different replacements — `Dosage Form for Injection` becomes `For Injection`, while
    `Tablet Dosage Form` becomes `Tablet` — and a single pattern cannot express that."""

    REMOVE_SPONSOR_FROM_CODELIST = "REMOVE_SPONSOR_FROM_CODELIST"
    """Close the sponsor term's membership of the codelist the CDISC term is joining, so
    the two no longer sit in it together. The sponsor term itself is left alone — it stays
    in its library and in any other codelist it belongs to."""

    RETIRE_SPONSOR_TERM = "RETIRE_SPONSOR_TERM"
    """Retire the sponsor term outright and close that membership. The stronger form of
    the above, and the only one that helps when the sponsor term sits in several
    codelists: the main API's name-uniqueness rule exempts retired terms, so this is what
    it recognises as the collision being resolved. Refused while anything still uses the
    term."""

    ADOPT_CDISC_NAME = "ADOPT_CDISC_NAME"
    """Give the term the name the naming rules would produce for it today. The one case
    where the import writes over a sponsor preferred name it did not create, and only ever
    because somebody asked for it."""

    USE_SUBMISSION_VALUE = "USE_SUBMISSION_VALUE"
    """Name a term after its submission value rather than its CDISC preferred term.
    Which submission value is decided by the rule's `in_codelist_id`, because a term
    can carry a different one in each codelist it belongs to."""

    ACKNOWLEDGE = "ACKNOWLEDGE"
    """Confirms this has been looked at; the release may proceed regardless. Changes
    nothing, the same as `IGNORE` — the difference is only in what it means to a
    reviewer: `IGNORE` says a disagreement is fine as shipped, `ACKNOWLEDGE` says
    something already true of the database — a live reference, a near-duplicate, a
    diverged name — has been considered and accepted rather than overlooked."""


class RuleScope(StrEnum):
    """How widely a rule applies. Narrower scopes win when several rules match."""

    OCCURRENCE = "OCCURRENCE"
    """One concept, one property, one effective date."""

    CONCEPT = "CONCEPT"
    """One concept."""

    PROPERTY = "PROPERTY"
    """One property, across all concepts."""

    GLOBAL = "GLOBAL"
    """Everything not matched more narrowly."""


PropertyValue = str | list[str] | None

# A regular expression supplied through the API is compiled and run server-side, so it
# is length-capped. The endpoint is already behind the import role; this guards against
# a careless pattern rather than a hostile one.
MAX_PATTERN_LENGTH = 200
MAX_IDENTIFIER_LENGTH = 255
MAX_TEXT_LENGTH = 2000
MAX_PRIORITY = 10_000

RuleValue = (
    Annotated[str, StringConstraints(max_length=MAX_TEXT_LENGTH)]
    | Annotated[
        list[Annotated[str, StringConstraints(max_length=MAX_TEXT_LENGTH)]],
        Field(max_length=100),
    ]
    | None
)

Identifier = Annotated[str, StringConstraints(max_length=MAX_IDENTIFIER_LENGTH)]
Text = Annotated[str, StringConstraints(max_length=MAX_TEXT_LENGTH)]
Regex = Annotated[str, StringConstraints(max_length=MAX_PATTERN_LENGTH)]
RulePriority = Annotated[
    StrictInt,
    Field(
        description="Order among equally scoped rules; lower is tried first",
        ge=0,
        le=MAX_PRIORITY,
    ),
]

# What a candidate's `source` says where the value came from somewhere other than a CDISC
# catalogue. These are the words a reviewer reads to tell the two names on a diverged-name
# finding apart, so they are spelled out rather than left to the order the candidates
# happen to be listed in — and they are what a strategy reads back to pick one.
HELD_IN_MDR = "sponsor preferred name currently held in MDR"
FROM_NAMING_RULES = "naming rules applied to the CDISC preferred term"
FROM_LANGUAGE_MODEL = "language model"
FROM_MDR_HEAD = "value currently held in MDR"
FROM_THIS_RELEASE = "value this release ships"


class RewriteStep(BaseModel):
    """One substitution in a `REWRITE`, applied in the order listed."""

    pattern: Annotated[
        str,
        Field(
            description="Regular expression to replace",
            min_length=1,
            max_length=MAX_PATTERN_LENGTH,
        ),
    ]
    replacement: Annotated[
        str,
        Field(description="What to put in its place", max_length=MAX_TEXT_LENGTH),
    ] = ""


class CandidateValue(BaseModel):
    """One of the competing values, and where it came from.

    `catalogues` is the provenance for values CDISC shipped. `source` is for the ones it
    did not: a finding about what a release lands on in MDR holds a value from the
    database, or from the naming rules, or from a language model, and a reviewer has to
    be able to tell which is which without counting positions.
    """

    value: PropertyValue
    catalogues: list[str]
    source: Annotated[
        str | None,
        Field(
            description="Where this value comes from, where that is not a CDISC catalogue: "
            "the sponsor name held in MDR, the naming rules, or the language model that "
            "proposed it. Unset for values the catalogues supplied"
        ),
    ] = None
    sponsor_term_uid: Annotated[
        str | None,
        Field(
            description="The sponsor term this candidate collides with, read from "
            "`value` on SPONSOR_TERM_DUPLICATE and SPONSOR_TERM_SEMANTIC_DUPLICATE. It "
            "is what REMOVE_SPONSOR_FROM_CODELIST and RETIRE_SPONSOR_TERM take as "
            "`value` where a finding collides with more than one. Unset otherwise"
        ),
    ] = None


class ResolutionDecision(BaseModel):
    """The decision that settled a review item."""

    strategy: ResolutionStrategy
    resolved_value: Annotated[
        PropertyValue,
        Field(description="The value that analysis will apply to the grouped concept"),
    ] = None
    chosen_catalogue: str | None = None
    author_id: str
    decided_at: datetime
    note: str | None = None
    rule_uid: Annotated[
        str | None,
        Field(
            description="Set when a stored rule made this decision rather than a person"
        ),
    ] = None


class Inconsistency(BaseModel):
    """One thing a reviewer may need to decide about a release."""

    uid: Annotated[
        str,
        Field(
            description="Deterministic: the same disagreement always gets the same uid, "
            "so a decision survives re-analysis"
        ),
    ]
    effective_date: date
    type: InconsistencyType
    entity_type: EntityType
    concept_id: Annotated[str, Field(description="Concept the finding is about")]
    related_concept_id: Annotated[
        str | None,
        Field(
            description="The term involved, for findings about a term within a codelist"
        ),
    ] = None
    property: Annotated[
        str | None, Field(description="Property in disagreement, where one applies")
    ] = None
    match_tier: Annotated[
        MatchTier | None,
        Field(
            description="How closely the colliding values agree, for findings raised by "
            "comparing this release against sponsor-defined content. The strongest tier "
            "of any candidate: `EXACT` is the one that breaks a uniqueness rule the main "
            "API enforces, and is why such a finding blocks until somebody settles it"
        ),
    ] = None
    usage_count: Annotated[
        int | None,
        Field(
            description="How many things in the MDR database refer to the term this "
            "finding is about; null on every other kind. On SPONSOR_TERM_DUPLICATE it "
            "counts references to the sponsor term the CDISC term collides with — zero "
            "means checked and free, above zero means it cannot be retired or taken "
            "out of the codelist until that usage is migrated through the main API. On "
            "CDISC_TERM_SUBMISSION_VALUE_CHANGED and CDISC_TERM_REMOVED_FROM_CODELIST "
            "it counts references to the CDISC term (`related_concept_id`) through the "
            "codelist the change is in, and is always above zero — those kinds are "
            "raised only when the term is actually referred to"
        ),
    ] = None
    status: InconsistencyStatus
    detected_at: datetime
    candidates: Annotated[
        list[CandidateValue],
        Field(
            description="The competing values, each with the catalogues that supplied it"
        ),
    ] = []
    codelist_ids: Annotated[
        list[str],
        Field(
            description="Codelists this term belongs to, where the finding is about a term. "
            "A rule's `in_codelist_id` is matched against these."
        ),
    ] = []
    submission_values: Annotated[
        dict[str, str],
        Field(
            description="The term's submission value in each of those codelists. More than "
            "half of all terms carry a different one per codelist, which is why "
            "USE_SUBMISSION_VALUE has to be told which codelist it means."
        ),
    ] = {}
    resolution: ResolutionDecision | None = None


class ResolutionInput(BaseModel):
    """A reviewer settling one review item."""

    strategy: ResolutionStrategy
    value: Annotated[
        PropertyValue,
        Field(description="Required by PICK_VALUE and CUSTOM_VALUE"),
    ] = None
    catalogue: Annotated[
        str | None, Field(description="Required by PREFER_CATALOGUE")
    ] = None
    pattern: Annotated[str | None, Field(description="Required by REGEX_REPLACE")] = (
        None
    )
    steps: Annotated[list[RewriteStep], Field(description="Required by REWRITE")] = []
    title_case: StrictBool = False
    note: str | None = None
    save_as_rule: Annotated[
        StrictBool,
        Field(
            description="Also store this as a rule, so the same disagreement is settled "
            "automatically next time instead of coming back"
        ),
    ] = False
    rule_scope: Annotated[
        RuleScope,
        Field(description="How widely the saved rule should apply"),
    ] = RuleScope.OCCURRENCE


class ResolutionRule(BaseModel):
    """A standing decision, applied by analysis without asking."""

    uid: str
    scope: RuleScope
    strategy: ResolutionStrategy
    entity_type: EntityType | None = None
    concept_id: str | None = None
    property: str | None = None
    effective_date: Annotated[
        date | None,
        Field(description="Limits the rule to one release; unset means every release"),
    ] = None
    inconsistency_type: InconsistencyType | None = None
    match_tier: Annotated[
        MatchTier | None,
        Field(
            description="Matches only findings whose colliding values agree this "
            "closely. This is how a rule can wave through near-matches while leaving "
            "exact ones for a person, since only those break a uniqueness rule"
        ),
    ] = None
    related_concept_id: Annotated[
        str | None,
        Field(
            description="Matches only the finding about this term. Needed where the "
            "term is not the concept: a submission value belongs to the membership, so "
            "those findings carry the codelist as `concept_id` and the term here"
        ),
    ] = None
    in_codelist_id: Annotated[
        str | None,
        Field(
            description="Matches a term that belongs to this codelist. Unlike the other "
            "discriminators this is a membership test, which is how a rule reaches every "
            "term of a codelist without naming them"
        ),
    ] = None
    value: PropertyValue = None
    pattern: Annotated[
        str | None, Field(description="Regular expression, for REGEX_REPLACE")
    ] = None
    steps: Annotated[
        list[RewriteStep],
        Field(description="The ordered substitutions a REWRITE applies"),
    ] = []
    when: Annotated[
        str | None,
        Field(
            description="Regular expression the value must match for this rule to apply. "
            "Lets a narrow conditional rule sit in front of a broader one for the same "
            "codelist, which is how `Administration via …` is treated differently from "
            "the rest of its codelist."
        ),
    ] = None
    title_case: Annotated[
        bool,
        Field(
            description="Title-case the result, for values taken from a submission value"
        ),
    ] = False
    priority: Annotated[
        int,
        Field(description="Order among equally scoped rules; lower is tried first"),
    ] = 100
    catalogue: str | None = None
    enabled: bool = True
    author_id: str
    created_at: datetime
    note: str | None = None


class ResolutionRuleInput(BaseModel):
    """A new standing decision."""

    scope: RuleScope
    strategy: ResolutionStrategy
    entity_type: EntityType | None = None
    concept_id: Identifier | None = None
    property: Identifier | None = None
    effective_date: IsoDate | None = None
    inconsistency_type: InconsistencyType | None = None
    match_tier: Annotated[
        MatchTier | None,
        Field(
            description="Matches only findings whose colliding values agree this closely"
        ),
    ] = None
    related_concept_id: Identifier | None = None
    in_codelist_id: Identifier | None = None
    value: RuleValue = None
    pattern: Annotated[
        Regex | None, Field(description="Regular expression, for REGEX_REPLACE")
    ] = None
    steps: Annotated[
        list[RewriteStep],
        Field(description="The ordered substitutions a REWRITE applies"),
    ] = []
    when: Annotated[
        Regex | None,
        Field(
            description="Regular expression the value must match for this rule to apply. "
            "Lets a narrow conditional rule sit in front of a broader one for the same "
            "codelist, which is how `Administration via …` is treated differently from "
            "the rest of its codelist."
        ),
    ] = None
    title_case: Annotated[
        StrictBool,
        Field(
            description="Title-case the result, for values taken from a submission value"
        ),
    ] = False
    priority: RulePriority = 100
    catalogue: Identifier | None = None
    enabled: StrictBool = True
    note: Text | None = None


class ResolutionRuleUpdate(BaseModel):
    """Changes to a stored rule.

    Only what the rule *does* can change. What it matches on composes its uid, so
    altering that would make it a different rule.
    """

    strategy: ResolutionStrategy | None = None
    value: RuleValue = None
    pattern: str | None = None
    steps: list[RewriteStep] | None = None
    when: str | None = None
    title_case: StrictBool | None = None
    priority: StrictInt | None = None
    catalogue: str | None = None
    enabled: StrictBool | None = None
    note: str | None = None


class StrategyDescription(BaseModel):
    """One way of settling a review item, and what it has to be given."""

    strategy: ResolutionStrategy
    description: str
    needs: Annotated[
        list[str],
        Field(
            description="Fields of the resolution this strategy cannot do without — "
            "`value`, `catalogue`, `pattern` or `steps`. Anything else it takes is "
            "optional and the description says what it is for"
        ),
    ] = []
    can_save_as_rule: Annotated[
        bool,
        Field(
            description="Whether a resolution using it accepts `save_as_rule`. False for "
            "the ones that change what the MDR database already holds, which are never "
            "standing rules, and for `USE_SUBMISSION_VALUE`, whose rule has to name a "
            "codelist a resolution cannot — write that one through `/resolution-rules`"
        ),
    ] = True


class ResolutionOptions(BaseModel):
    """Which strategies settle which kind of review item.

    The same table `POST /inconsistencies/{uid}/resolution` enforces, so what a client
    offers and what the endpoint accepts cannot drift. Admissible on kind is the first
    gate, not the last: a listed strategy can still refuse a particular finding — one
    value to accept where there are two, a catalogue that supplied nothing — and says so.
    """

    strategies: Annotated[
        list[StrategyDescription],
        Field(description="Every strategy, with what it needs and what it does"),
    ]
    by_type: Annotated[
        dict[InconsistencyType, list[ResolutionStrategy]],
        Field(
            description="For each kind of review item, the strategies that can settle "
            "it, the usual choice first. Where the menu depends on `match_tier` this is "
            "the one for a finding with no tier or an `EXACT` one — the most "
            "restrictive; `by_type_and_tier` has the rest"
        ),
    ]
    by_type_and_tier: Annotated[
        dict[InconsistencyType, dict[MatchTier, list[ResolutionStrategy]]],
        Field(
            description="For the kinds whose menu depends on `match_tier`, the menu at "
            "each tier. A kind absent here has one menu at every tier. `ACKNOWLEDGE` is "
            "only offered where the finding does not block import"
        ),
    ]
    raised_by: Annotated[
        dict[InconsistencyType, ReviewPass],
        Field(
            description="For each kind of review item, which step raises it — "
            "`ANALYSIS` (`POST /effective-dates/{date}/analysis`) or `SPONSOR_IMPACT` "
            "(`POST /effective-dates/{date}/sponsor-impact`). Every `ANALYSIS` kind "
            "must be settled, and the release re-analysed, before sponsor impact can "
            "run at all — this is a fixed property of the kind, not of any one finding"
        ),
    ]


class CataloguePriorityEntry(BaseModel):
    """Where a catalogue sits in the default pecking order, and its standing flags."""

    catalogue_name: str
    priority: Annotated[int, Field(description="Lower wins", ge=0)]
    mandatory: Annotated[
        bool,
        Field(description="Must be present in a release before analysis can run"),
    ] = False
    expects_workbook: Annotated[
        bool,
        Field(
            description="Usually ships a paired-view workbook alongside the package "
            "files. Informational only — never a gate"
        ),
    ] = False


class CataloguePriorityInput(BaseModel):
    """The default pecking order, in full."""

    catalogues: Annotated[
        list[str],
        Field(
            description="Catalogue names, most authoritative first",
            min_length=1,
        ),
    ]


class MandatoryCataloguesInput(BaseModel):
    """The catalogues a release must hold before it can be analysed, in full."""

    catalogues: Annotated[
        list[str],
        Field(
            description="Catalogue names that must all be present before analysis "
            "can run. Replaces the set wholesale — a catalogue left out is no "
            "longer mandatory"
        ),
    ]


class ExpectedWorkbooksInput(BaseModel):
    """The catalogues that usually ship a paired-view workbook, in full."""

    catalogues: Annotated[
        list[str],
        Field(
            description="Catalogue names that usually ship a paired-view workbook. "
            "Informational only — never a gate. Replaces the set wholesale"
        ),
    ]


class ImportEnabled(BaseModel):
    """Whether promoting a release from staging into OSB is allowed."""

    enabled: Annotated[
        StrictBool,
        Field(
            description="When false, review and analysis still work but the final "
            "import into the OSB database is refused. Disabled by default"
        ),
    ]


def build_inconsistency_uid(
    effective_date: str,
    entity_type: EntityType,
    concept_id: str,
    inconsistency_type: InconsistencyType,
    property_name: str | None = None,
    related_concept_id: str | None = None,
) -> str:
    """Composes the deterministic uid of a review item.

    Readable rather than hashed: a uid that says what it refers to is worth far more
    when reading a review queue or a log line than one that is merely short.
    """

    parts = [
        effective_date,
        entity_type.value,
        concept_id,
        inconsistency_type.value,
        property_name or "-",
        related_concept_id or "-",
    ]
    return "_".join(parts)
