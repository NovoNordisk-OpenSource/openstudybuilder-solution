"""Assessing what a release would land on in the sponsor half of MDR.

These need real databases because the whole pass is a question put to MDR in
hand-written Cypher — which library a term hangs off, which membership is open, which
name version is retired. None of that is visible to a unit test.

The shape of every test here is the same, and it is the real workflow: import one
release so the CDISC codelists exist, plant sponsor content into one of them the way the
main API would, then bring in a second release that lands on it.
"""

import pytest
from neomodel import db as neomodel_db

from common.exceptions import ValidationException
from standards_import.config import settings as si_settings
from standards_import.models.inconsistencies import (
    FROM_LANGUAGE_MODEL,
    FROM_NAMING_RULES,
    HELD_IN_MDR,
)
from standards_import.repositories import staging_db
from standards_import.services import import_service
from standards_import.tests.integration import fake_semantic_provider
from standards_import.tests.integration.packages import codelist, package, term
from standards_import.tests.integration.sponsor_data import (
    add_sponsor_codelist,
    add_sponsor_term,
    offer_term_as_template_parameter,
    stop_using_term,
    use_term_in_a_study,
    use_term_in_a_syntax_instance,
)

FIRST = "2025-09-26"
SECOND = "2026-03-27"


def mdr(query, **params):
    rows, _ = neomodel_db.cypher_query(query, params)
    return rows


def release_with(effective_date, terms, codelists=(), catalogue="SDTM CT"):
    return package(
        catalogue,
        effective_date,
        [codelist("C1", "Test Codelist", "TESTCL", terms=terms), *codelists],
    )


def import_first(release, terms=(term("T1", "A"),)):
    """One release in MDR, so there is a codelist for the sponsor to have extended."""

    release.upload(release_with(FIRST, list(terms)))
    release.analyse(FIRST)
    release.assess(FIRST)
    job = release.import_now(FIRST)
    assert job.status.value == "SUCCEEDED", job.error


def bring_in(release, terms, codelists=()):
    """Upload and analyse a second release, ready to be assessed."""

    release.upload(release_with(SECOND, list(terms), codelists))
    summary = release.analyse(SECOND)
    assert summary.open_inconsistency_count == 0, "fixture was meant to be uncontested"


def findings_of(release, kind):
    return [item for item in release.findings(SECOND) if item.type.value == kind]


# --- terms ----------------------------------------------------------------------


def test_a_cdisc_term_arriving_with_a_sponsor_terms_name_holds_the_release(release):
    """The collision with teeth. Nothing in this app's Cypher stops two terms sharing a
    name inside one codelist, but the main API's uniqueness rule does — so this imports
    quietly and leaves a codelist the main API then refuses to edit. It has to block."""

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "Term T2", "SPONSORSV")

    bring_in(release, [term("T1", "A"), term("T2", "B")])
    summary = release.assess(SECOND)

    assert summary.by_match_tier == {"EXACT": 1}
    assert summary.open_finding_count == 1

    found = findings_of(release, "SPONSOR_TERM_DUPLICATE")
    assert len(found) == 1
    assert found[0].concept_id == "C1", "the collision belongs to the membership"
    assert found[0].related_concept_id == "T2"
    assert found[0].status.value == "OPEN"
    assert "SPONSOR_1" in found[0].candidates[0].value
    # Zero, never null: "checked, nothing refers to it" and "this finding predates the
    # count" are different answers and a reviewer has to be able to tell them apart.
    assert found[0].usage_count == 0

    with pytest.raises(ValidationException, match="review items are still open"):
        release.import_now(SECOND)


def test_a_name_differing_only_in_case_is_recorded_and_waved_through(release):
    """Two distinct values, so no rule breaks — but somebody may still want to know two
    terms now mean the same thing. Recorded as informational, never blocking, and
    raised directly at that status rather than settled by a rule."""

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "TERM T2", "SPONSORSV")

    bring_in(release, [term("T1", "A"), term("T2", "B")])
    summary = release.assess(SECOND)

    assert summary.by_match_tier == {"CASE_INSENSITIVE": 1}
    assert summary.open_finding_count == 0

    found = findings_of(release, "SPONSOR_TERM_DUPLICATE")
    assert found[0].status.value == "INFORMATIONAL"
    assert found[0].resolution is None

    job = release.import_now(SECOND)
    assert job.status.value == "SUCCEEDED", job.error


def test_acknowledging_an_informational_duplicate_settles_it_as_acknowledged(release):
    """`ACKNOWLEDGE`, not `IGNORE`: this is a near-duplicate a person has considered
    and accepted, not a disagreement being waved through — and it was never blocking
    to begin with, so acknowledging it changes nothing about whether the release can
    import."""

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "TERM T2", "SPONSORSV")
    bring_in(release, [term("T1", "A"), term("T2", "B")])
    release.assess(SECOND)
    finding = findings_of(release, "SPONSOR_TERM_DUPLICATE")[0]
    assert finding.status.value == "INFORMATIONAL"

    release.resolve(finding.uid, strategy="ACKNOWLEDGE")

    assert findings_of(release, "SPONSOR_TERM_DUPLICATE")[0].status.value == (
        "ACKNOWLEDGED"
    )
    assert release.preview(SECOND).can_import is True


def test_ignore_does_not_apply_to_an_informational_duplicate(release):
    """`IGNORE` is not on this kind's menu — `ACKNOWLEDGE` is the only way to settle it,
    worded for what it actually is."""

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "TERM T2", "SPONSORSV")
    bring_in(release, [term("T1", "A"), term("T2", "B")])
    release.assess(SECOND)
    finding = findings_of(release, "SPONSOR_TERM_DUPLICATE")[0]

    with pytest.raises(ValidationException, match="does not apply"):
        release.resolve(finding.uid, strategy="IGNORE")


def test_import_is_not_blocked_by_an_unacknowledged_informational_finding(release):
    """Informational never blocks the import, acknowledged or not — that is the whole
    point of the status."""

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "TERM T2", "SPONSORSV")
    bring_in(release, [term("T1", "A"), term("T2", "B")])
    release.assess(SECOND)
    assert findings_of(release, "SPONSOR_TERM_DUPLICATE")[0].status.value == (
        "INFORMATIONAL"
    )

    assert release.preview(SECOND).can_import is True
    assert release.import_now(SECOND).status.value == "SUCCEEDED"


def test_marking_a_codelist_reviewed_waits_on_an_informational_finding(release):
    """Review is a wider guarantee than import: a person has to have looked at
    everything on the codelist, informational items included, even though none of them
    ever holds up the import itself."""

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "TERM T2", "SPONSORSV")
    bring_in(release, [term("T1", "A"), term("T2", "B")])
    release.assess(SECOND)
    assert findings_of(release, "SPONSOR_TERM_DUPLICATE")[0].status.value == (
        "INFORMATIONAL"
    )

    with pytest.raises(ValidationException, match="open or informational"):
        release.review(SECOND, "C1")

    finding = findings_of(release, "SPONSOR_TERM_DUPLICATE")[0]
    release.resolve(finding.uid, strategy="ACKNOWLEDGE")

    reviewed = release.review(SECOND, "C1")
    assert reviewed.status.value == "REVIEWED"


def test_unresolving_an_informational_finding_returns_it_to_informational_not_open(
    release,
):
    """Taking a decision back must not turn a never-blocking finding into a blocking
    one — it goes back to exactly the status it was raised at."""

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "TERM T2", "SPONSORSV")
    bring_in(release, [term("T1", "A"), term("T2", "B")])
    release.assess(SECOND)
    finding = findings_of(release, "SPONSOR_TERM_DUPLICATE")[0]
    release.resolve(finding.uid, strategy="ACKNOWLEDGE")
    assert findings_of(release, "SPONSOR_TERM_DUPLICATE")[0].status.value == (
        "ACKNOWLEDGED"
    )

    release.unresolve(finding.uid)

    assert findings_of(release, "SPONSOR_TERM_DUPLICATE")[0].status.value == (
        "INFORMATIONAL"
    )
    assert release.preview(SECOND).can_import is True


def test_unresolving_an_exact_collision_returns_it_to_open_not_informational(release):
    """The other direction of the same guard: an EXACT collision was never
    informational, and taking its decision back must not make it look like it was."""

    finding = collide(release)
    assert finding.match_tier.value == "EXACT"
    release.resolve(finding.uid, strategy="RETIRE_SPONSOR_TERM")
    assert findings_of(release, "SPONSOR_TERM_DUPLICATE")[0].status.value != "OPEN"

    release.unresolve(finding.uid)

    assert findings_of(release, "SPONSOR_TERM_DUPLICATE")[0].status.value == "OPEN"


def test_a_shared_submission_value_collides_on_its_own(release):
    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "Something Else Entirely", "B")

    bring_in(release, [term("T1", "A"), term("T2", "B")])
    summary = release.assess(SECOND)

    assert summary.by_match_tier == {"EXACT": 1}
    assert (
        "submission value"
        in findings_of(release, "SPONSOR_TERM_DUPLICATE")[0].candidates[0].value
    )


def test_a_retired_sponsor_term_no_longer_collides(release):
    """Retiring is how the main API's own uniqueness rule is satisfied — it exempts a
    retired term explicitly. Reporting one as a collision would mean an item that can
    never be settled."""

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "Term T2", "SPONSORSV", status="Retired")

    bring_in(release, [term("T1", "A"), term("T2", "B")])
    summary = release.assess(SECOND)

    assert findings_of(release, "SPONSOR_TERM_DUPLICATE") == []
    assert summary.checked_memberships == 0, "nothing left to compare against"


def test_a_sponsor_term_in_a_different_codelist_is_not_a_collision(release):
    """The rule is per codelist, not per catalogue. A term of the same name elsewhere is
    somebody else's business.

    Both codelists here are being extended by this release, so both are asked about and
    the sponsor term really is in front of the matcher — which is what makes this a test
    of the scoping rather than of what was fetched.
    """

    two_codelists = [
        codelist("C1", "Test Codelist", "TESTCL", terms=[term("T1", "A")]),
        codelist("C2", "Other Codelist", "OTHERCL", terms=[term("T8", "Y")]),
    ]
    release.upload(package("SDTM CT", FIRST, two_codelists))
    release.analyse(FIRST)
    release.assess(FIRST)
    assert release.import_now(FIRST).status.value == "SUCCEEDED"

    add_sponsor_term("C2", "SPONSOR_1", "Term T2", "B")

    release.upload(
        package(
            "SDTM CT",
            SECOND,
            [
                codelist(
                    "C1",
                    "Test Codelist",
                    "TESTCL",
                    terms=[term("T1", "A"), term("T2", "B")],
                ),
                codelist(
                    "C2",
                    "Other Codelist",
                    "OTHERCL",
                    terms=[term("T8", "Y"), term("T9", "Z")],
                ),
            ],
        )
    )
    release.analyse(SECOND)
    summary = release.assess(SECOND)

    assert summary.checked_memberships == 1, "C2's sponsor term was in front of it"
    assert findings_of(release, "SPONSOR_TERM_DUPLICATE") == []


def test_the_comparison_uses_the_settled_name_not_the_cdisc_preferred_term(release):
    """The naming rules rewrite what a new term is called, and that rewritten name is
    what reaches MDR. Comparing CDISC's own preferred term would miss this collision
    entirely — the two strings share nothing."""

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "Renamed By A Rule", "SPONSORSV")

    release.upload(release_with(SECOND, [term("T1", "A"), term("T2", "B")]))
    release.analyse(SECOND)
    naming = next(
        item
        for item in release.findings(SECOND)
        if item.type.value == "SPONSOR_NAME" and item.concept_id == "T2"
    )
    release.resolve(naming.uid, strategy="CUSTOM_VALUE", value="Renamed By A Rule")
    release.analyse(SECOND)

    release.assess(SECOND)

    found = findings_of(release, "SPONSOR_TERM_DUPLICATE")
    assert len(found) == 1, "the settled name collides even though 'Term T2' would not"
    assert found[0].match_tier.value == "EXACT"


# --- names that have drifted ----------------------------------------------------


def test_a_cdisc_rename_puts_the_local_name_up_for_review(release):
    """The import owns the attributes half and never touches an existing name, so a term
    CDISC renames keeps whatever MDR called it. Worth knowing about: the reason for that
    name may not survive the rename."""

    import_first(release, terms=[term("T1", "A", preferred_term="Old Name")])
    bring_in(release, [term("T1", "A", preferred_term="New Name")])
    summary = release.assess(SECOND)

    found = findings_of(release, "SPONSOR_NAME_DIVERGED")
    assert [item.concept_id for item in found] == ["T1"]
    # Held first, proposed second.
    assert [candidate.value for candidate in found[0].candidates] == [
        "Old Name",
        "New Name",
    ]
    assert (
        found[0].status.value == "INFORMATIONAL"
    ), "reported, never acted on by itself"
    assert summary.checked_updated_terms == 1


def test_a_name_already_adrift_is_not_reported_when_the_release_leaves_it_alone(
    release,
):
    """The population this must not report.

    On a database the bootstrap script populated, thousands of terms carry a name no rule
    would produce today — every Trial Phase term in a real MDR is called `Phase 0 Trial`
    rather than `Early Phase 1`, for instance. If a name differing from what the rules say
    were enough, every one of those would be reported the moment CDISC touched its
    definition, and the handful of genuine renames would be buried.

    What is reported is a name *this release* moved.
    """

    import_first(release, terms=[term("T1", "A", preferred_term="Steady Name")])
    # Somebody, or an older import, gave it a name the rules would not produce.
    mdr("""MATCH (:CTTermRoot {uid:'T1'})-[:HAS_NAME_ROOT]->()-[:HAS_VERSION]->(v)
           SET v.name = 'A Name Of Our Own'""")

    # CDISC reworded the definition and left the term's name alone.
    bring_in(
        release,
        [
            term(
                "T1", "A", preferred_term="Steady Name", definition="Reworded by CDISC."
            )
        ],
    )
    summary = release.assess(SECOND)

    assert summary.checked_updated_terms == 1, "it was compared"
    assert findings_of(release, "SPONSOR_NAME_DIVERGED") == []


def test_a_rename_is_still_reported_when_the_name_was_already_adrift(release):
    """The other half of the same rule: a local name is exactly the reason a rename
    matters, so a term already carrying one must not become invisible."""

    import_first(release, terms=[term("T1", "A", preferred_term="Old Name")])
    mdr("""MATCH (:CTTermRoot {uid:'T1'})-[:HAS_NAME_ROOT]->()-[:HAS_VERSION]->(v)
           SET v.name = 'A Name Of Our Own'""")

    bring_in(release, [term("T1", "A", preferred_term="New Name")])
    release.assess(SECOND)

    found = findings_of(release, "SPONSOR_NAME_DIVERGED")
    assert [item.concept_id for item in found] == ["T1"]
    # Each candidate says which name it is. A consumer must never have to know that
    # the held one comes first.
    by_source = {candidate.source: candidate for candidate in found[0].candidates}
    assert by_source[HELD_IN_MDR].value == "A Name Of Our Own"
    assert by_source[FROM_NAMING_RULES].value == "New Name"
    # And the rules' name says which CDISC package it was produced from.
    assert by_source[FROM_NAMING_RULES].catalogues == ["SDTM CT 2026-03-27"]
    assert by_source[HELD_IN_MDR].catalogues == []


def test_a_name_a_naming_rule_produced_is_not_reported_as_drift(release):
    """The reason this re-runs the rules instead of comparing against `preferredTerm`.

    `C99077` has a shipped rule stripping a trailing ` Study`, so MDR holds
    `Interventional` where CDISC says `Interventional Study`. Every term of every
    rule-covered codelist looks renamed, and the naive test would report all of them,
    every release, forever.
    """

    study_type = [
        codelist(
            "C99077",
            "Study Type",
            "STYPE",
            terms=[term("T1", "A", preferred_term="Interventional Study")],
        )
    ]
    release.upload(package("SDTM CT", FIRST, study_type))
    release.analyse(FIRST)
    release.assess(FIRST)
    assert release.import_now(FIRST).status.value == "SUCCEEDED"

    held = mdr(
        """MATCH (:CTTermRoot {uid:'T1'})-[:HAS_NAME_ROOT]->()-[:HAS_VERSION]->(v)
           RETURN v.name"""
    )
    assert held == [["Interventional"]], "the rule was meant to have renamed it"

    release.upload(
        package(
            "SDTM CT",
            SECOND,
            [
                codelist(
                    "C99077",
                    "Study Type",
                    "STYPE",
                    terms=[
                        term(
                            "T1",
                            "A",
                            preferred_term="Interventional Study",
                            definition="Reworded by CDISC.",
                        )
                    ],
                )
            ],
        )
    )
    release.analyse(SECOND)
    summary = release.assess(SECOND)

    assert summary.checked_updated_terms == 1, "the term was compared"
    assert findings_of(release, "SPONSOR_NAME_DIVERGED") == []


# --- codelists ------------------------------------------------------------------


def test_a_new_codelist_covering_a_sponsor_one_is_reported_without_blocking(release):
    """There is no way to retire a codelist through the API at all, so this is a report
    for a person to act on rather than something we can offer to fix."""

    import_first(release)
    add_sponsor_codelist("SPONSOR_CL", "Second Codelist", "SECONDCL")

    bring_in(
        release,
        [term("T1", "A")],
        codelists=[
            codelist("C2", "Second Codelist", "SECONDCL", terms=[term("T9", "Z")])
        ],
    )
    summary = release.assess(SECOND)

    found = findings_of(release, "SPONSOR_CODELIST_DUPLICATE")
    assert [item.concept_id for item in found] == ["C2"]
    assert found[0].status.value == "INFORMATIONAL"
    assert summary.open_finding_count == 0
    assert summary.checked_codelists == 1


# --- how it holds together ------------------------------------------------------


def test_analysis_does_not_delete_the_assessments_findings(release):
    """Both passes hang findings off the same release. A prune that matched every kind
    would have analysis quietly destroy the assessment's findings — and the decisions
    attached to them — every time it ran."""

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "TERM T2", "SPONSORSV")

    bring_in(release, [term("T1", "A"), term("T2", "B")])
    release.assess(SECOND)
    found = findings_of(release, "SPONSOR_TERM_DUPLICATE")
    release.resolve(found[0].uid, strategy="ACKNOWLEDGE")

    release.analyse(SECOND)

    survivor = findings_of(release, "SPONSOR_TERM_DUPLICATE")
    assert len(survivor) == 1, "analysis pruned a finding that was not its own"
    assert survivor[0].status.value == "ACKNOWLEDGED"
    assert survivor[0].resolution.author_id == "integration-test"


def test_a_decision_survives_re_assessment_and_reopens_when_the_sponsor_edits(release):
    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "Term T2", "SPONSORSV")

    bring_in(release, [term("T1", "A"), term("T2", "B")])
    release.assess(SECOND)
    uid = findings_of(release, "SPONSOR_TERM_DUPLICATE")[0].uid
    release.resolve(uid, strategy="RETIRE_SPONSOR_TERM")

    release.assess(SECOND)
    assert findings_of(release, "SPONSOR_TERM_DUPLICATE")[0].status.value != "OPEN"

    # The sponsor renames their term, so it now collides less badly than it did. The
    # decision was made about the old collision and must not stand for the new one.
    mdr(
        """MATCH (:CTTermRoot {uid:'SPONSOR_1'})-[:HAS_NAME_ROOT]->()-[:HAS_VERSION]->(v)
           SET v.name = 'TERM T2'"""
    )
    release.assess(SECOND)

    reopened = findings_of(release, "SPONSOR_TERM_DUPLICATE")[0]
    assert reopened.match_tier.value == "CASE_INSENSITIVE"
    assert reopened.status.value == "INFORMATIONAL", (
        "the old decision was about the EXACT collision; the near-match one raised "
        "fresh is informational and settles nothing on its own"
    )
    assert reopened.resolution is None


def test_a_release_stops_colliding_when_the_sponsor_term_goes(release):
    """A finding the data no longer supports is pruned, so an item somebody was about to
    decide does not sit in the queue forever."""

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "Term T2", "SPONSORSV")

    bring_in(release, [term("T1", "A"), term("T2", "B")])
    release.assess(SECOND)
    assert findings_of(release, "SPONSOR_TERM_DUPLICATE")

    mdr("""MATCH (:CTCodelistRoot {uid:'C1'})-[ht:HAS_TERM]->(:CTCodelistTerm)
                 -[:HAS_TERM_ROOT]->(:CTTermRoot {uid:'SPONSOR_1'})
           SET ht.end_date = datetime()""")
    release.assess(SECOND)

    assert findings_of(release, "SPONSOR_TERM_DUPLICATE") == []


def test_an_assessment_made_before_the_last_analysis_is_refused(release):
    """Analysis rebuilds the settled values the assessment compared against."""

    import_first(release)
    bring_in(release, [term("T1", "A"), term("T2", "B")])
    release.assess(SECOND)
    release.analyse(SECOND)

    with pytest.raises(ValidationException, match="analysed since sponsor impact"):
        release.import_now(SECOND)


def test_an_unassessed_release_is_refused(release):
    import_first(release)
    bring_in(release, [term("T1", "A"), term("T2", "B")])

    with pytest.raises(ValidationException, match="has not been assessed"):
        release.import_now(SECOND)

    assert release.preview(SECOND).can_import is False


def test_assessing_before_the_review_queue_is_clear_is_refused(release):
    """What a term collides with depends on the name it will be given, so an open review
    item means that name has not been chosen yet."""

    import_first(release)
    # A membership disagreement, which nothing settles on its own — the catalogue pecking
    # order only speaks to a plain disagreement over a value.
    release.upload(
        release_with(SECOND, [term("T1", "A"), term("T2", "B")]),
        package(
            "SEND CT",
            SECOND,
            [codelist("C1", "Test Codelist", "TESTCL", terms=[term("T1", "A")])],
        ),
    )
    release.analyse(SECOND)
    open_items = [i for i in release.findings(SECOND) if i.status.value == "OPEN"]
    assert open_items, "fixture was meant to leave something open"

    with pytest.raises(ValidationException, match="review items are still open"):
        release.assess(SECOND)


# --- acting on a collision ------------------------------------------------------


def collide(release, sponsor_name="Term T2", **kwargs):
    """One release landing a CDISC term on a sponsor term of the same name."""

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", sponsor_name, "SPONSORSV", **kwargs)
    bring_in(release, [term("T1", "A"), term("T2", "B")])
    release.assess(SECOND)
    return findings_of(release, "SPONSOR_TERM_DUPLICATE")[0]


def name_versions(uid="SPONSOR_1"):
    return mdr(
        """MATCH (:CTTermRoot {uid:$uid})-[:HAS_NAME_ROOT]->()-[hv:HAS_VERSION]->(v)
           RETURN hv.status, hv.version, v.name, hv.end_date IS NULL
           ORDER BY hv.status, hv.version""",
        uid=uid,
    )


def open_membership_of(term_uid="SPONSOR_1", codelist_uid="C1"):
    return mdr(
        """MATCH (:CTCodelistRoot {uid:$codelist_uid})-[ht:HAS_TERM]->(:CTCodelistTerm)
                 -[:HAS_TERM_ROOT]->(:CTTermRoot {uid:$term_uid})
           WHERE ht.end_date IS NULL RETURN count(ht)""",
        term_uid=term_uid,
        codelist_uid=codelist_uid,
    )[0][0]


def test_an_ordinary_import_does_not_evict_a_sponsor_term(release):
    """A release never mentions a sponsor term, so anything working out what to close by
    differencing the release against what a codelist currently holds closes the sponsor
    extensions too — every quarter, silently, as though CDISC had dropped them.

    The only thing that takes a sponsor term out of a codelist is somebody deciding so.
    """

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "Nothing To Do With CDISC", "SPONSORSV")

    bring_in(release, [term("T1", "A"), term("T2", "B")])
    release.assess(SECOND)
    job = release.import_now(SECOND)

    assert job.status.value == "SUCCEEDED", job.error
    assert job.stats["memberships_ended"] == 0, "no CDISC term left C1 in this release"
    assert open_membership_of() == 1


def test_retiring_a_sponsor_term_marks_it_retired_and_takes_it_out_of_the_codelist(
    release,
):
    """Both halves of one decision. Retirement is what satisfies the main API's
    name-uniqueness rule; closing the membership is what actually takes the duplicate out
    of the codelist. Neither alone finishes the job."""

    finding = collide(release)
    release.resolve(finding.uid, strategy="RETIRE_SPONSOR_TERM")

    job = release.import_now(SECOND)
    assert job.status.value == "SUCCEEDED", job.error
    assert job.stats["sponsor_terms_retired"] == 1
    assert job.stats["sponsor_memberships_closed"] == 1

    assert name_versions() == [
        ["Final", "1.0", "Term T2", False],
        ["Retired", "1.0", "Term T2", True],
    ], "the open version is Retired, over the same value and at the same version number"
    assert open_membership_of() == 0

    pointers = mdr(
        """MATCH (:CTTermRoot {uid:'SPONSOR_1'})-[:HAS_NAME_ROOT]->(nr)-[p]->()
           WHERE type(p) STARTS WITH 'LATEST'
           RETURN DISTINCT type(p) ORDER BY type(p)"""
    )
    assert pointers == [
        ["LATEST"],
        ["LATEST_FINAL"],
        ["LATEST_RETIRED"],
    ], "LATEST_FINAL is a historical pointer and must survive a retirement"

    statuses = mdr(
        """MATCH (:CTTermRoot {uid:'SPONSOR_1'})-[:HAS_ATTRIBUTES_ROOT]->()-[hv:HAS_VERSION]->()
           WHERE hv.end_date IS NULL RETURN hv.status"""
    )
    assert statuses == [
        ["Retired"]
    ], "both halves, not Retired in name and Final in attributes"


def test_the_collision_is_gone_when_the_release_after_it_is_assessed(release):
    """The loop closes: a retired sponsor term is exempt from the uniqueness rule, so it
    is no longer something to report."""

    finding = collide(release)
    release.resolve(finding.uid, strategy="RETIRE_SPONSOR_TERM")
    assert release.import_now(SECOND).status.value == "SUCCEEDED"

    third = "2026-09-25"
    release.upload(release_with(third, [term("T1", "A"), term("T2", "B")]))
    release.analyse(third)
    release.assess(third)

    assert [
        item
        for item in release.findings(third)
        if item.type.value == "SPONSOR_TERM_DUPLICATE"
    ] == []


def test_removing_from_the_codelist_leaves_the_term_itself_alone(release):
    """The narrower answer, for a sponsor term that earns its keep elsewhere."""

    finding = collide(release)
    release.resolve(finding.uid, strategy="REMOVE_SPONSOR_FROM_CODELIST")

    job = release.import_now(SECOND)
    assert job.status.value == "SUCCEEDED", job.error
    assert job.stats["sponsor_memberships_closed"] == 1
    assert job.stats["sponsor_terms_retired"] == 0

    assert open_membership_of() == 0
    assert name_versions() == [["Final", "1.0", "Term T2", True]], "still Final"


def test_the_template_parameter_link_goes_with_the_membership(release):
    """The main API's own `remove_term` deletes it. Left behind, the term would still be
    offered as a parameter of a codelist it is no longer in."""

    finding = collide(release)
    offer_term_as_template_parameter("C1", "SPONSOR_1")
    assert mdr("MATCH ()-[p:HAS_PARAMETER_TERM]->() RETURN count(p)")[0][0] == 1

    release.resolve(finding.uid, strategy="REMOVE_SPONSOR_FROM_CODELIST")
    assert release.import_now(SECOND).status.value == "SUCCEEDED"

    assert mdr("MATCH ()-[p:HAS_PARAMETER_TERM]->() RETURN count(p)")[0][0] == 0


def test_a_sponsor_term_something_still_uses_cannot_be_displaced(release):
    """Nothing in OSB stops a term being retired out from under a study — the main API has
    no usage check on its own retirement either. This app makes one."""

    finding = collide(release)
    use_term_in_a_study("C1", "SPONSOR_1")

    for strategy in ("RETIRE_SPONSOR_TERM", "REMOVE_SPONSOR_FROM_CODELIST"):
        with pytest.raises(ValidationException, match="still referred to"):
            release.resolve(finding.uid, strategy=strategy)

    assert (
        findings_of(release, "SPONSOR_TERM_DUPLICATE")[0].status.value == "OPEN"
    ), "a refused resolution settles nothing"


def test_usage_through_the_name_half_counts_too(release):
    """A syntax instance reaches a term through its *name* root, so a check that walked
    `CTTermRoot` would call this term unused and retire it out from under the instance.
    """

    finding = collide(release)
    use_term_in_a_syntax_instance("SPONSOR_1")

    with pytest.raises(ValidationException, match="USES_VALUE"):
        release.resolve(finding.uid, strategy="RETIRE_SPONSOR_TERM")


def test_being_offered_as_a_template_parameter_is_not_usage(release):
    """`HAS_PARAMETER_TERM` says the term is on the codelist's parameter list, and taking
    it out of the codelist is what removes it from that list — the main API's own
    `remove_term` deletes the edge too. Counting it as usage would make every term ever
    offered as a parameter impossible to displace."""

    finding = collide(release)
    offer_term_as_template_parameter("C1", "SPONSOR_1")

    release.resolve(finding.uid, strategy="RETIRE_SPONSOR_TERM")

    assert findings_of(release, "SPONSOR_TERM_DUPLICATE")[0].status.value == "RESOLVED"


def test_a_term_that_falls_into_use_after_the_decision_stops_the_import(release):
    """Deciding and importing are separate moments. Caught before the run starts, so
    nothing is half-written."""

    finding = collide(release)
    release.resolve(finding.uid, strategy="RETIRE_SPONSOR_TERM")

    use_term_in_a_study("C1", "SPONSOR_1")

    assert release.preview(SECOND).can_import is False
    with pytest.raises(ValidationException, match="now referred to by something else"):
        release.import_now(SECOND)


def test_the_assessment_says_how_much_stands_in_the_way(release):
    """The count is what tells a reviewer which collisions are theirs to act on at all."""

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "Term T2", "SPONSORSV")
    use_term_in_a_study("C1", "SPONSOR_1")

    bring_in(release, [term("T1", "A"), term("T2", "B")])
    release.assess(SECOND)

    assert findings_of(release, "SPONSOR_TERM_DUPLICATE")[0].usage_count == 1


def test_retiring_is_not_stacked_a_second_time_by_a_retried_run(release):
    """A run that dies after this step and is repeated must find the work already done,
    not retire an already-retired term all over again."""

    finding = collide(release)
    release.resolve(finding.uid, strategy="RETIRE_SPONSOR_TERM")
    assert release.import_now(SECOND).status.value == "SUCCEEDED"

    with staging_db.staging_session() as session:
        import_service.apply_sponsor_decisions(session, SECOND, "integration-test")

    assert len(name_versions()) == 2, "a second retirement would make it three"
    assert open_membership_of() == 0


# --- names that have drifted, acted on ------------------------------------------


def test_adopting_the_cdisc_name_opens_a_new_version_of_the_name_half(release):
    """The one case where the import writes over a sponsor preferred name it did not
    create. The previous name stays readable at the version that carried it."""

    import_first(release, terms=[term("T1", "A", preferred_term="Old Name")])
    bring_in(release, [term("T1", "A", preferred_term="New Name")])
    release.assess(SECOND)

    finding = findings_of(release, "SPONSOR_NAME_DIVERGED")[0]
    release.resolve(finding.uid, strategy="ADOPT_CDISC_NAME")

    job = release.import_now(SECOND)
    assert job.status.value == "SUCCEEDED", job.error
    assert job.stats["sponsor_names_adopted"] == 1

    assert name_versions("T1") == [
        ["Final", "1.0", "Old Name", False],
        ["Final", "2.0", "New Name", True],
    ]
    assert mdr(
        "MATCH (:CTTermRoot {uid:'T1'})-[:HAS_NAME_ROOT]->()-[:LATEST]->(v) RETURN v.name"
    ) == [["New Name"]]


def test_keeping_a_diverged_name_writes_nothing(release):
    """`ACKNOWLEDGE` has to leave the name half exactly as it was — a no-op that still opened
    a version would be indistinguishable from having adopted the new name."""

    import_first(release, terms=[term("T1", "A", preferred_term="Old Name")])
    bring_in(release, [term("T1", "A", preferred_term="New Name")])
    release.assess(SECOND)
    assert release.import_now(SECOND).status.value == "SUCCEEDED"

    assert name_versions("T1") == [["Final", "1.0", "Old Name", True]]


# --- semantic - what the strings cannot see -------------------------------------


PROVIDER = "standards_import.tests.integration.fake_semantic_provider"

# Names sharing no content word, from the release that motivated the whole check.
CDISC_NAME = "Angiopoietin-Related Protein 3/8 Complex"
SPONSOR_NAME = "Angiopoietin-Like 3/8 Complex"


@pytest.fixture(autouse=True)
def no_semantic_provider(monkeypatch):
    """Off unless a test asks for it, which is also the shipped default."""

    monkeypatch.setattr(si_settings, "semantic_provider", "")
    monkeypatch.setattr(fake_semantic_provider, "FAILING", False)
    fake_semantic_provider.PROMPTS.clear()


def ask_the_model(monkeypatch, answer="pairs_the_first_two"):
    monkeypatch.setattr(si_settings, "semantic_provider", f"{PROVIDER}:{answer}")


def set_up_a_renaming(release):
    """A sponsor term and a CDISC one that mean the same and match on nothing."""

    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", SPONSOR_NAME, "ANGL38")
    bring_in(release, [term("T1", "A"), term("T2", "B", preferred_term=CDISC_NAME)])


def test_a_duplicate_under_a_different_name_is_invisible_to_the_strings(release):
    """The premise. Without the model this release looks clean, and it is not."""

    set_up_a_renaming(release)
    summary = release.assess(SECOND)

    assert findings_of(release, "SPONSOR_TERM_DUPLICATE") == []
    assert summary.checked_semantically == 0, "no provider configured, so nothing asked"


def test_the_model_catches_what_the_strings_could_not(release, monkeypatch):
    ask_the_model(monkeypatch)
    set_up_a_renaming(release)
    summary = release.assess(SECOND)

    found = findings_of(release, "SPONSOR_TERM_SEMANTIC_DUPLICATE")
    assert len(found) == 1
    assert found[0].concept_id == "C1"
    assert found[0].related_concept_id == "T2"
    assert found[0].match_tier is None, "a model's opinion is not a string match"
    assert "HIGH:SPONSOR_1:" in found[0].candidates[0].value
    assert found[0].candidates[0].source.startswith(FROM_LANGUAGE_MODEL)
    assert found[0].candidates[0].catalogues == [], "a model is not a catalogue"
    assert summary.checked_semantically == 1


def test_a_candidate_is_recorded_and_never_blocks(release, monkeypatch):
    """It breaks no rule, and a queue held up by a suggestion teaches people to clear it
    without reading."""

    ask_the_model(monkeypatch)
    set_up_a_renaming(release)
    summary = release.assess(SECOND)

    found = findings_of(release, "SPONSOR_TERM_SEMANTIC_DUPLICATE")[0]
    assert found.status.value == "INFORMATIONAL"
    assert found.resolution is None
    assert summary.open_finding_count == 0
    assert release.import_now(SECOND).status.value == "SUCCEEDED"


def test_the_model_is_not_asked_about_a_collision_the_strings_already_found(
    release, monkeypatch
):
    """Two findings about one pair is noise, and the incremental answer is the point."""

    ask_the_model(monkeypatch)
    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "Term T2", "SPONSORSV")
    bring_in(release, [term("T1", "A"), term("T2", "B")])
    summary = release.assess(SECOND)

    assert findings_of(release, "SPONSOR_TERM_DUPLICATE"), "the strings caught it"
    assert findings_of(release, "SPONSOR_TERM_SEMANTIC_DUPLICATE") == []
    assert summary.checked_semantically == 0
    assert not fake_semantic_provider.PROMPTS, "the codelist was never sent"


def test_a_codelist_with_no_sponsor_terms_is_never_sent(release, monkeypatch):
    """What keeps this affordable: on a real release most codelists have no sponsor
    extension at all, and none of them costs a call."""

    ask_the_model(monkeypatch)
    import_first(release)
    bring_in(release, [term("T1", "A"), term("T2", "B")])
    release.assess(SECOND)

    assert not fake_semantic_provider.PROMPTS


def test_a_gateway_that_fails_costs_its_answer_and_nothing_else(release, monkeypatch):
    """The string comparison is the part with teeth. Losing it because a gateway timed out
    would be a poor trade."""

    ask_the_model(monkeypatch, "fails")
    import_first(release)
    add_sponsor_term("C1", "SPONSOR_1", "Term T2", "SPONSORSV")
    add_sponsor_term("C1", "SPONSOR_2", SPONSOR_NAME, "ANGL38")
    bring_in(
        release,
        [term("T1", "A"), term("T2", "B"), term("T3", "C", preferred_term=CDISC_NAME)],
    )
    summary = release.assess(SECOND)

    assert fake_semantic_provider.PROMPTS, "it was asked"
    assert findings_of(release, "SPONSOR_TERM_SEMANTIC_DUPLICATE") == []
    assert summary.checked_semantically == 0, "asked is not answered"
    assert findings_of(release, "SPONSOR_TERM_DUPLICATE"), "the strings still answered"


def test_a_candidate_can_be_acted_on_like_any_other_collision(release, monkeypatch):
    """It is the same problem, found by a different means, so the same answers apply."""

    ask_the_model(monkeypatch)
    set_up_a_renaming(release)
    release.assess(SECOND)

    finding = findings_of(release, "SPONSOR_TERM_SEMANTIC_DUPLICATE")[0]
    release.resolve(finding.uid, strategy="RETIRE_SPONSOR_TERM")

    job = release.import_now(SECOND)
    assert job.status.value == "SUCCEEDED", job.error
    assert job.stats["sponsor_terms_retired"] == 1


def test_a_provider_that_cannot_be_loaded_stops_the_assessment(release, monkeypatch):
    """Asked for and unavailable is not the same as switched off. Skipping it quietly is
    how a release gets a clean bill of health nobody earned."""

    set_up_a_renaming(release)
    monkeypatch.setattr(si_settings, "semantic_provider", "nowhere.at.all:missing")

    with pytest.raises(ValidationException, match="could not be loaded"):
        release.assess(SECOND)


# --- not paying twice for the same question -------------------------------------


def two_codelists_with_sponsor_terms(release):
    """Two CDISC codelists the sponsor has extended, each gaining a term.

    Two, because the point of the cache is that one codelist moving does not re-ask the
    other — which a single-codelist fixture cannot tell apart from re-asking everything.
    """

    release.upload(
        package(
            "SDTM CT",
            FIRST,
            [
                codelist("C1", "First Codelist", "FIRSTCL", terms=[term("T1", "A")]),
                codelist("C2", "Second Codelist", "SECONDCL", terms=[term("T8", "Y")]),
            ],
        )
    )
    release.analyse(FIRST)
    release.assess(FIRST)
    assert release.import_now(FIRST).status.value == "SUCCEEDED"

    add_sponsor_term("C1", "SPONSOR_1", SPONSOR_NAME, "ANGL38")
    add_sponsor_term("C2", "SPONSOR_2", "Something Sponsorish", "SPON2")

    release.upload(
        package(
            "SDTM CT",
            SECOND,
            [
                codelist(
                    "C1",
                    "First Codelist",
                    "FIRSTCL",
                    terms=[term("T1", "A"), term("T2", "B", preferred_term=CDISC_NAME)],
                ),
                codelist(
                    "C2",
                    "Second Codelist",
                    "SECONDCL",
                    terms=[term("T8", "Y"), term("T9", "Z")],
                ),
            ],
        )
    )
    release.analyse(SECOND)


def naming_item_for(release, term_id):
    return next(
        item
        for item in release.findings(SECOND)
        if item.type.value == "SPONSOR_NAME" and item.concept_id == term_id
    )


def test_assessing_again_with_nothing_changed_asks_nothing(release, monkeypatch):
    """A release is assessed once per analysis run, and analysis is re-run every time a
    review item is settled. Without this, settling one item would mean buying every
    codelist's answer over again."""

    ask_the_model(monkeypatch)
    two_codelists_with_sponsor_terms(release)
    first_pass = release.assess(SECOND)
    assert len(fake_semantic_provider.PROMPTS) == 2
    before = {
        item.uid for item in findings_of(release, "SPONSOR_TERM_SEMANTIC_DUPLICATE")
    }
    assert before, "the fixture was meant to produce candidates"

    fake_semantic_provider.PROMPTS.clear()
    second_pass = release.assess(SECOND)

    assert not fake_semantic_provider.PROMPTS, "the same questions were asked again"
    assert second_pass.checked_semantically == first_pass.checked_semantically
    # Re-parsed from what was filed, so the answer is the same answer.
    assert {
        item.uid for item in findings_of(release, "SPONSOR_TERM_SEMANTIC_DUPLICATE")
    } == before


def test_only_the_codelist_that_moved_is_asked_again(release, monkeypatch):
    """The prompt is the key, so what decides a re-ask is whether the question changed —
    and a term renamed in one codelist leaves every other codelist's question identical.
    """

    ask_the_model(monkeypatch)
    two_codelists_with_sponsor_terms(release)
    release.assess(SECOND)
    fake_semantic_provider.PROMPTS.clear()

    # The settled name is half of what the model is shown, so changing it is a different
    # question about C1 and the same question about C2.
    release.resolve(
        naming_item_for(release, "T2").uid,
        strategy="CUSTOM_VALUE",
        value="An Entirely Different Name",
    )
    release.analyse(SECOND)
    release.assess(SECOND)

    assert len(fake_semantic_provider.PROMPTS) == 1
    asked = fake_semantic_provider.PROMPTS[0]
    assert "First Codelist" in asked and "Second Codelist" not in asked
    assert "An Entirely Different Name" in asked


def test_refresh_puts_every_question_again(release, monkeypatch):
    """For when the answers rather than the inputs are what changed."""

    ask_the_model(monkeypatch)
    two_codelists_with_sponsor_terms(release)
    release.assess(SECOND)
    fake_semantic_provider.PROMPTS.clear()

    release.assess(SECOND, refresh=True)

    assert len(fake_semantic_provider.PROMPTS) == 2


def test_a_different_model_is_a_different_question(release, monkeypatch):
    """An answer is only interchangeable with one from the same model, so the model id is
    part of the key rather than just provenance on the finding."""

    ask_the_model(monkeypatch)
    monkeypatch.setattr(si_settings, "semantic_model", "one-model")
    two_codelists_with_sponsor_terms(release)
    release.assess(SECOND)
    fake_semantic_provider.PROMPTS.clear()

    monkeypatch.setattr(si_settings, "semantic_model", "another-model")
    release.assess(SECOND)

    assert len(fake_semantic_provider.PROMPTS) == 2


def test_a_call_that_failed_is_asked_again_next_time(release, monkeypatch):
    """Nothing is filed for a question the gateway never answered — remembering it as
    unanswerable would make one bad afternoon permanent."""

    ask_the_model(monkeypatch, "flaky")
    monkeypatch.setattr(fake_semantic_provider, "FAILING", True)
    two_codelists_with_sponsor_terms(release)
    release.assess(SECOND)
    assert len(fake_semantic_provider.PROMPTS) == 2

    # Same provider path, so nothing but the filing decides whether it is asked again.
    fake_semantic_provider.PROMPTS.clear()
    monkeypatch.setattr(fake_semantic_provider, "FAILING", False)
    summary = release.assess(SECOND)

    assert len(fake_semantic_provider.PROMPTS) == 2
    assert summary.checked_semantically == 2


# --- CDISC changes that land on downstream usage ---------------------------------
#
# Not a collision with sponsor content: CDISC's own change to a term it owns, reported
# only where the MDR database already refers to the term. A routine change with nothing
# built on it must raise nothing at all — not even an auto-resolved finding — because
# CDISC re-values and drops terms every release, almost always harmlessly.


def test_a_changed_submission_value_on_an_unused_term_raises_nothing(release):
    import_first(release, terms=[term("T1", "A")])
    bring_in(release, [term("T1", "B")])
    release.assess(SECOND)

    assert findings_of(release, "CDISC_TERM_SUBMISSION_VALUE_CHANGED") == []


def test_a_changed_submission_value_on_a_used_term_holds_the_release(release):
    import_first(release, terms=[term("T1", "A")])
    use_term_in_a_study("C1", "T1")

    bring_in(release, [term("T1", "B")])
    release.assess(SECOND)

    findings = findings_of(release, "CDISC_TERM_SUBMISSION_VALUE_CHANGED")
    assert len(findings) == 1
    assert findings[0].status.value == "OPEN"
    assert findings[0].usage_count == 1
    assert findings[0].related_concept_id == "T1"
    assert release.preview(SECOND).can_import is False


def test_a_term_removed_from_a_codelist_that_is_unused_raises_nothing(release):
    import_first(release, terms=[term("T1", "A"), term("T2", "B")])
    bring_in(release, [term("T1", "A")])
    release.assess(SECOND)

    assert findings_of(release, "CDISC_TERM_REMOVED_FROM_CODELIST") == []


def test_a_term_removed_from_a_codelist_that_is_used_holds_the_release(release):
    import_first(release, terms=[term("T1", "A"), term("T2", "B")])
    use_term_in_a_study("C1", "T2")

    bring_in(release, [term("T1", "A")])
    release.assess(SECOND)

    findings = findings_of(release, "CDISC_TERM_REMOVED_FROM_CODELIST")
    assert len(findings) == 1
    assert findings[0].status.value == "OPEN"
    assert findings[0].usage_count == 1
    assert findings[0].related_concept_id == "T2"
    assert release.preview(SECOND).can_import is False


def test_acknowledging_a_used_term_change_lets_the_release_import(release):
    """ACKNOWLEDGE, not IGNORE: this is a live reference somebody has considered and
    accepted, not a disagreement being waved through."""

    import_first(release, terms=[term("T1", "A"), term("T2", "B")])
    use_term_in_a_study("C1", "T2")
    bring_in(release, [term("T1", "A")])
    release.assess(SECOND)
    finding = findings_of(release, "CDISC_TERM_REMOVED_FROM_CODELIST")[0]

    release.resolve(finding.uid, strategy="ACKNOWLEDGE")

    assert findings_of(release, "CDISC_TERM_REMOVED_FROM_CODELIST")[0].status.value == (
        "ACKNOWLEDGED"
    )
    assert release.preview(SECOND).can_import is True
    assert release.import_now(SECOND).status.value == "SUCCEEDED"


def test_ignore_does_not_apply_to_a_usage_finding(release):
    """IGNORE is the wrong strategy here — the menu for these two kinds is ACKNOWLEDGE
    only, and the endpoint says so before storing anything."""

    import_first(release, terms=[term("T1", "A"), term("T2", "B")])
    use_term_in_a_study("C1", "T2")
    bring_in(release, [term("T1", "A")])
    release.assess(SECOND)
    finding = findings_of(release, "CDISC_TERM_REMOVED_FROM_CODELIST")[0]

    with pytest.raises(ValidationException, match="does not apply"):
        release.resolve(finding.uid, strategy="IGNORE")


def test_save_as_rule_is_refused_for_a_usage_finding(release):
    """Usage is a fact about today's database, not a standing convention — a rule saved
    while a term happens to be unused would wave through a much larger count next
    quarter."""

    import_first(release, terms=[term("T1", "A"), term("T2", "B")])
    use_term_in_a_study("C1", "T2")
    bring_in(release, [term("T1", "A")])
    release.assess(SECOND)
    finding = findings_of(release, "CDISC_TERM_REMOVED_FROM_CODELIST")[0]

    with pytest.raises(ValidationException, match="rather than a standing convention"):
        release.resolve(finding.uid, strategy="ACKNOWLEDGE", save_as_rule=True)


def test_usage_appearing_after_assessment_still_blocks_the_import(release):
    """A term that falls into use after a clean assessment has no finding at all for the
    generic "open review items" blocker to catch — this is its own check, made again
    just before the import runs, for the same reason `sponsor_terms_no_longer_free` is.
    """

    import_first(release, terms=[term("T1", "A"), term("T2", "B")])
    bring_in(release, [term("T1", "A")])
    release.assess(SECOND)
    assert findings_of(release, "CDISC_TERM_REMOVED_FROM_CODELIST") == []
    assert release.preview(SECOND).can_import is True

    use_term_in_a_study("C1", "T2")

    assert release.preview(SECOND).can_import is False
    with pytest.raises(ValidationException, match="have not been acknowledged"):
        release.import_now(SECOND)


def test_a_term_that_becomes_used_is_a_fresh_finding_on_reassessment(release):
    """Detection is a pure recompute of a freshly queried usage count every run, so a
    term whose usage moves from zero to nonzero is new to the next run's candidate set
    and gets created like any other finding — nothing is cached from the run before."""

    import_first(release, terms=[term("T1", "A"), term("T2", "B")])
    bring_in(release, [term("T1", "A")])
    release.assess(SECOND)
    assert findings_of(release, "CDISC_TERM_REMOVED_FROM_CODELIST") == []

    use_term_in_a_study("C1", "T2")
    release.assess(SECOND)

    findings = findings_of(release, "CDISC_TERM_REMOVED_FROM_CODELIST")
    assert len(findings) == 1
    assert findings[0].status.value == "OPEN"


def test_usage_going_to_zero_prunes_the_finding(release):
    """A finding the data no longer supports is pruned, the same as any other kind —
    usage dropping back to zero means the term is simply absent from the next run's
    candidate set."""

    import_first(release, terms=[term("T1", "A"), term("T2", "B")])
    use_term_in_a_study("C1", "T2")
    bring_in(release, [term("T1", "A")])
    release.assess(SECOND)
    assert findings_of(release, "CDISC_TERM_REMOVED_FROM_CODELIST")

    stop_using_term("C1", "T2")
    release.assess(SECOND)

    assert findings_of(release, "CDISC_TERM_REMOVED_FROM_CODELIST") == []


def two_codelists_sharing_a_term(release):
    """T2 in both C1 and C2; the second release takes it out of C1 only."""

    other = codelist("C2", "Other Codelist", "OTHERCL", terms=[term("T2", "B")])
    release.upload(release_with(FIRST, [term("T1", "A"), term("T2", "B")], [other]))
    release.analyse(FIRST)
    release.assess(FIRST)
    assert release.import_now(FIRST).status.value == "SUCCEEDED"

    bring_in(release, [term("T1", "A")], [other])


def test_usage_through_another_codelist_is_not_hit_by_a_removal_from_this_one(release):
    """A context that picked T2 through C2 does not notice T2 leaving C1 — counting it
    would hold the release for a reference the change cannot break."""

    two_codelists_sharing_a_term(release)
    use_term_in_a_study("C2", "T2")

    release.assess(SECOND)

    assert findings_of(release, "CDISC_TERM_REMOVED_FROM_CODELIST") == []
    assert release.preview(SECOND).can_import is True


def test_usage_through_this_codelist_is_hit_by_a_removal_from_it(release):
    two_codelists_sharing_a_term(release)
    use_term_in_a_study("C2", "T2")
    use_term_in_a_study("C1", "T2")

    release.assess(SECOND)

    findings = findings_of(release, "CDISC_TERM_REMOVED_FROM_CODELIST")
    assert len(findings) == 1
    assert findings[0].usage_count == 1


def test_usage_by_name_is_not_hit_by_a_removal_from_a_codelist(release):
    """A syntax instance built on the term's name is untouched by the membership
    changing — the name half of the term is not what this release alters."""

    import_first(release, terms=[term("T1", "A"), term("T2", "B")])
    use_term_in_a_syntax_instance("T2")
    bring_in(release, [term("T1", "A")])

    release.assess(SECOND)

    assert findings_of(release, "CDISC_TERM_REMOVED_FROM_CODELIST") == []
