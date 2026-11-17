"""Whether a CDISC concept collides with a sponsor-defined one already in MDR.

Pure: it is handed the sponsor entities somebody else read out of MDR and the values this
release would write, and it says which of them mean the same thing.

Three things to note.

**It compares names, not preferred terms.** For CDISC terms, the name that actually reaches
MDR is what the `SPONSOR_NAME` review item settled — the seeded rules turn `Interventional Study`
into `Interventional` across many codelists — so matching the raw preferred term both
misses real collisions and invents ones that will never happen. Callers pass settled
values, and the field names are the same on both sides because by then they mean the
same thing.

**A collision is reported once per sponsor field, not once per CDISC field.** Where a
concept's name and its submission value both land on the same sponsor *name*, that is one
problem stated twice; where they land on the sponsor's name and its submission value
respectively, it is genuinely two.

**A match carries both field names.** Knowing that the name you are adding is already
somebody's *submission value* is different from it being their name, and collapsing the
two loses the half a reviewer needs to act.
"""

from typing import Any

from standards_import.models.inconsistencies import MatchTier

# Compared on both sides. A sponsor term's name is its `CTTermNameValue.name` and its
# submission value belongs to the membership (`CTCodelistTerm.submission_value`); a
# sponsor codelist carries both on its attributes.
MATCH_FIELDS = ("name", "submission_value")

# A candidate is written `<leading word>:<sponsor uid>:<value>`.
CANDIDATE_PARTS = 3

FIELD_LABELS = {"name": "name", "submission_value": "submission value"}

# Worst first: an exact collision breaks a uniqueness rule the main API enforces, the
# other two are for a person to weigh. See MatchTier.
TIER_ORDER = {
    MatchTier.EXACT: 0,
    MatchTier.CASE_INSENSITIVE: 1,
    MatchTier.NORMALIZED: 2,
}

# What `describe_match` writes first and `sponsor_uid_from_candidate` reads back, so a
# value from some other kind of finding is not mistaken for one of ours.
TIER_NAMES = frozenset(tier.value for tier in MatchTier)

SponsorEntity = dict[str, Any]
SponsorIndex = dict[str, list[tuple[SponsorEntity, str]]]
Match = dict[str, Any]


def normalize_key(value: Any) -> str:
    """Casefolds and drops every non-alphanumeric character.

    `AE Severity`, `ae_severity` and `AESEVERITY` all collapse to `aeseverity`, which is
    the point: the same concept reaches the database under all three spellings depending
    on who typed it.

    `str.isalnum` rather than an ASCII pattern, so an accented letter survives instead of
    being silently dropped. `None`, and anything made entirely of punctuation, yields the
    empty string — which never matches, because otherwise every value without a letter in
    it would collide with every other one.
    """

    if value is None:
        return ""
    return "".join(char for char in str(value).casefold() if char.isalnum())


def match_tier(cdisc_value: Any, sponsor_value: Any) -> MatchTier:
    """How closely two values that already share a normalized key agree.

    Only ever called for values `normalize_key` has put in the same bucket, so there is no
    "no match" answer to give.
    """

    left = "" if cdisc_value is None else str(cdisc_value)
    right = "" if sponsor_value is None else str(sponsor_value)
    if left == right:
        return MatchTier.EXACT
    if left.casefold() == right.casefold():
        return MatchTier.CASE_INSENSITIVE
    return MatchTier.NORMALIZED


def build_index(entities: list[SponsorEntity] | None) -> SponsorIndex:
    """Files sponsor entities under the normalized form of each field they can collide on.

    Entries keep the field they were filed under, not just the entity. A lookup has to be
    able to say *which* sponsor value it landed on, and an index that merged name and
    submission value into one bucket could not.
    """

    index: SponsorIndex = {}
    for entity in entities or ():
        for field in MATCH_FIELDS:
            key = normalize_key(entity.get(field))
            # The one guard that keeps values with no alphanumeric content apart. An
            # unset submission value and a name of `---` both normalize to the empty
            # string, and filing those would report every one of them as colliding with
            # every other. Looking up an empty key then simply finds nothing.
            if key:
                index.setdefault(key, []).append((entity, field))
    return index


def find_matches(
    index: SponsorIndex,
    name: Any = None,
    submission_value: Any = None,
) -> list[Match]:
    """Sponsor entities that one CDISC concept would collide with, worst first.

    Scope is the caller's: an index built from one codelist's sponsor terms answers only
    for that codelist, which is what a term collision means. A sponsor term of the same
    name in a *different* codelist is not a collision — the main API's uniqueness rule is
    per codelist, not per catalogue.
    """

    best: dict[tuple[str, str], Match] = {}

    for cdisc_field, cdisc_value in (
        ("name", name),
        ("submission_value", submission_value),
    ):
        for entity, sponsor_field in index.get(normalize_key(cdisc_value), ()):
            sponsor_value = entity.get(sponsor_field)
            match = {
                "field": cdisc_field,
                "sponsor_field": sponsor_field,
                "tier": match_tier(cdisc_value, sponsor_value),
                "cdisc_value": cdisc_value,
                "sponsor_uid": entity.get("uid"),
                "sponsor_value": sponsor_value,
            }
            # Identity falls back to the object where a sponsor entity somehow arrives
            # without a uid, so two of them cannot silently collapse into one match.
            marker = entity.get("uid") or f"anonymous-{id(entity)}"
            slot = (str(marker), sponsor_field)
            held = best.get(slot)
            if held is None or _preference(match) < _preference(held):
                best[slot] = match

    return sorted(best.values(), key=_ordering)


def strongest_tier(matches: list[Match]) -> MatchTier | None:
    """The tier that decides how a finding is treated, or None where nothing matched.

    Taken from the matches rather than from `matches[0]`, so it stays right if a caller
    ever reorders them.
    """

    if not matches:
        return None
    return min((match["tier"] for match in matches), key=lambda tier: TIER_ORDER[tier])


def describe_match(match: Match) -> str:
    """One collision written as a candidate value.

    A candidate holds one value, and this has to carry three things: what settles the
    finding, how badly it collides, and enough for a person to recognise it. So the tier
    and the sponsor uid lead — neither can contain a colon — and everything after the
    second one is prose, which `split(":", 2)` recovers however the sponsor's own value
    is punctuated. Compound candidate values have precedent here: a term-set finding's
    candidates are `conceptId:submissionValue` for the same reason.

    The whole string is what the fingerprint digests, which is what makes a decision
    reopen rather than quietly stand when the sponsor edits the value it was about.
    """

    return (
        f"{match['tier'].value}"
        f":{match['sponsor_uid'] or '-'}"
        f":this release introduces a CDISC-Sponsor duplicate "
        f"on {FIELD_LABELS[match['sponsor_field']]} {match['cdisc_value']!r}"
    )


def sponsor_uid_from_candidate(
    value: Any, prefixes: frozenset[str] = TIER_NAMES
) -> str | None:
    """The sponsor entity a candidate written by `describe_match` names, or None.

    The other half of that function's contract, and the reason the uid sits where it does:
    a decision has to be able to say *which* sponsor term it is about, and the only thing
    it has to go on is the candidate value it was made against.

    `prefixes` is the vocabulary the leading word must come from. Two passes write
    candidates in this shape — this one leads with a match tier, the semantic one with a
    confidence — and both are acted on by the same strategies, so the format is shared and
    only the words differ. Naming the vocabulary is what keeps a plain value from some
    other kind of finding from being read as though it named a sponsor term.

    `None` rather than a raise for anything that is not one of those, so a caller can
    refuse with a message about the finding instead of a parse error.
    """

    if not isinstance(value, str):
        return None
    parts = value.split(":", CANDIDATE_PARTS - 1)
    if len(parts) != CANDIDATE_PARTS or parts[0] not in prefixes or not parts[1]:
        return None
    return parts[1]


def _preference(match: Match) -> tuple[int, bool]:
    """Which of two matches on the same sponsor field to keep. Lower wins.

    The tier decides, because that is what says whether an invariant breaks. Where two
    pairings agree on it, the one whose fields have the same name is kept: `name` against
    `name` is what a reviewer expects to read, and `submission value` against `name` is
    the surprising one worth stating only when it is all there is.
    """

    return (TIER_ORDER[match["tier"]], match["field"] != match["sponsor_field"])


def _ordering(match: Match) -> tuple[int, str, str]:
    """Worst first, then a total order so the same inputs always produce the same list."""

    return (
        TIER_ORDER[match["tier"]],
        str(match.get("sponsor_uid") or ""),
        match["sponsor_field"],
    )
