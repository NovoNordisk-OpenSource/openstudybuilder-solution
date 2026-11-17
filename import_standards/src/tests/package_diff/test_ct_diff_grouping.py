import pytest

from src.scripts.package_diff.ct_diff import (
    band_changes,
    build_report,
    diff_package_pair,
    normalize_package,
)
from src.scripts.package_diff.ct_diff_grouping import (
    codelists_for_change,
    group_by_codelist,
    group_report,
    index_memberships_by_term,
)
from src.tests.package_diff.factories import make_codelist, make_package, make_term


def grouped_pair(old_raw, new_raw):
    """Normalize, diff and group two raw packages. Returns (grouped, pair_diff)."""
    old = normalize_package(old_raw)
    new = normalize_package(new_raw)
    pair_diff = diff_package_pair(old, new)
    # build_report does this for every pair; grouping consumes bands, not the
    # raw sub-dicts, so a bare diff_package_pair result is not enough.
    pair_diff["bands"] = band_changes(pair_diff)
    return group_by_codelist(pair_diff, old, new), pair_diff


def kinds_in(bucket, level):
    return [change["kind"] for change in bucket["bands"][level]]


class Test:
    def test__index_memberships_by_term_lists_every_home(self):
        package = normalize_package(
            make_package(
                "2024-01-01",
                [
                    make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")]),
                    make_codelist(
                        "CL2",
                        "SUBCL2",
                        [make_term("T1", "SUB1"), make_term("T2", "SUB2")],
                    ),
                ],
            )
        )

        homes = index_memberships_by_term(package)

        assert homes["T1"] == {"CL1", "CL2"}
        assert homes["T2"] == {"CL2"}

    def test__codelists_for_change_rejects_unknown_kind(self):
        # Better a loud failure than silently dropping a change from every page.
        with pytest.raises(ValueError, match="Unknown change kind"):
            codelists_for_change({"kind": "invented"}, {}, {})

    def test__codelist_field_change_lands_under_its_own_codelist(self):
        old = make_package(
            "2024-01-01", [make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")])]
        )
        new = make_package(
            "2024-04-01",
            [make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")], name="Renamed")],
        )

        grouped, _ = grouped_pair(old, new)

        assert grouped["order"] == ["CL1"]
        assert kinds_in(grouped["codelists"]["CL1"], 11) == ["codelist_changed"]

    def test__term_attribute_change_fans_out_to_every_home_codelist(self):
        # Terms are deduplicated catalogue-wide, so one definition edit is a
        # change to every codelist holding that term.
        def packages(definition):
            return make_package(
                "2024-01-01",
                [
                    make_codelist(
                        "CL1", "SUBCL1", [make_term("T1", "SUB1", definition)]
                    ),
                    make_codelist(
                        "CL2", "SUBCL2", [make_term("T1", "SUB1", definition)]
                    ),
                ],
            )

        grouped, _ = grouped_pair(packages("Before."), packages("After."))

        assert kinds_in(grouped["codelists"]["CL1"], 12) == ["term_changed"]
        assert kinds_in(grouped["codelists"]["CL2"], 12) == ["term_changed"]
        # ...and once, de-duplicated, on the consolidated page.
        assert len(grouped["term_attribute_changes"]) == 1
        assert grouped["term_attribute_changes"][0]["codelists"] == ["CL1", "CL2"]

    def test__move_is_tagged_with_the_side_it_applies_to(self):
        old = make_package(
            "2024-01-01",
            [
                make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")]),
                make_codelist("CL2", "SUBCL2", []),
            ],
        )
        new = make_package(
            "2024-04-01",
            [
                make_codelist("CL1", "SUBCL1", []),
                make_codelist("CL2", "SUBCL2", [make_term("T1", "SUB1")]),
            ],
        )

        grouped, _ = grouped_pair(old, new)

        moves = {
            cid: [c for band in b["bands"].values() for c in band]
            for cid, b in grouped["codelists"].items()
        }
        assert [c["kind"] for c in moves["CL1"]] == ["term_moved"]
        assert moves["CL1"][0]["role"] == "left"
        assert moves["CL2"][0]["role"] == "entered"

    def test__deleted_term_is_not_listed_twice_on_one_codelist_page(self):
        # ct_diff emits both a catalogue-level term_removed and a per-codelist
        # membership_removed. On a codelist page they state the same fact, so the
        # membership record survives and carries the catalogue-wide fact as a flag.
        old = make_package(
            "2024-01-01",
            [
                make_codelist(
                    "CL1", "SUBCL1", [make_term("T1", "SUB1"), make_term("T2", "SUB2")]
                )
            ],
        )
        new = make_package(
            "2024-04-01", [make_codelist("CL1", "SUBCL1", [make_term("T2", "SUB2")])]
        )

        grouped, pair_diff = grouped_pair(old, new)

        assert kinds_in(grouped["codelists"]["CL1"], 2) == ["membership_removed"]
        # The flat report still carries both records; only the grouping drops one.
        assert len(pair_diff["bands"][2]) == 2
        assert grouped["distinct_counts"][2] == 1

    def test__surviving_membership_record_carries_the_catalogue_wide_fact(self):
        # Dropping term_removed must not lose "and it is gone from the catalogue
        # entirely", which is a bigger deal than leaving one codelist.
        old = make_package(
            "2024-01-01",
            [
                make_codelist(
                    "CL1", "SUBCL1", [make_term("T1", "SUB1"), make_term("T2", "SUB2")]
                ),
                make_codelist("CL2", "SUBCL2", [make_term("T2", "SUB2")]),
            ],
        )
        new = make_package(
            "2024-04-01",
            [
                make_codelist("CL1", "SUBCL1", [make_term("T2", "SUB2")]),
                make_codelist("CL2", "SUBCL2", [make_term("T2", "SUB2")]),
            ],
        )

        grouped, _ = grouped_pair(old, new)

        (change,) = grouped["codelists"]["CL1"]["bands"][2]
        assert change["catalogue_gone"] is True

    def test__membership_removal_is_kept_when_the_term_survives_elsewhere(self):
        # The term still exists, it just left this codelist - so there is no
        # catalogue-level record to fold in and no flag to set.
        old = make_package(
            "2024-01-01",
            [
                make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")]),
                make_codelist("CL2", "SUBCL2", [make_term("T1", "SUB1")]),
            ],
        )
        new = make_package(
            "2024-04-01",
            [
                make_codelist("CL1", "SUBCL1", []),
                make_codelist("CL2", "SUBCL2", [make_term("T1", "SUB1")]),
            ],
        )

        grouped, _ = grouped_pair(old, new)

        (change,) = grouped["codelists"]["CL1"]["bands"][3]
        assert change["kind"] == "membership_removed"
        assert "catalogue_gone" not in change

    def test__entity_status_marks_added_and_removed_codelists(self):
        old = make_package(
            "2024-01-01", [make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")])]
        )
        new = make_package(
            "2024-04-01", [make_codelist("CL2", "SUBCL2", [make_term("T2", "SUB2")])]
        )

        grouped, _ = grouped_pair(old, new)

        assert grouped["codelists"]["CL1"]["entity_status"] == "removed"
        assert grouped["codelists"]["CL2"]["entity_status"] == "added"

    def test__order_puts_the_most_disruptive_category_first(self):
        old = make_package(
            "2024-01-01",
            [
                # CL1 only gains a term, and was never extensible (category 7);
                # CL2 loses one outright (category 2).
                make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")]),
                make_codelist(
                    "CL2", "SUBCL2", [make_term("T2", "SUB2"), make_term("T3", "SUB3")]
                ),
            ],
        )
        new = make_package(
            "2024-04-01",
            [
                make_codelist(
                    "CL1", "SUBCL1", [make_term("T1", "SUB1"), make_term("T4", "SUB4")]
                ),
                make_codelist("CL2", "SUBCL2", [make_term("T2", "SUB2")]),
            ],
        )

        grouped, _ = grouped_pair(old, new)

        assert grouped["order"] == ["CL2", "CL1"]
        assert grouped["codelists"]["CL2"]["min_severity"] == 2
        assert grouped["codelists"]["CL1"]["min_severity"] == 7

    def test__unchanged_codelist_gets_no_bucket(self):
        # The governing principle: the site renders changes and nothing else.
        old = make_package(
            "2024-01-01",
            [
                make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")]),
                make_codelist("CL2", "SUBCL2", [make_term("T2", "SUB2")]),
            ],
        )
        new = make_package(
            "2024-04-01",
            [
                make_codelist(
                    "CL1", "SUBCL1", [make_term("T1", "SUB1")], name="Renamed"
                ),
                make_codelist("CL2", "SUBCL2", [make_term("T2", "SUB2")]),
            ],
        )

        grouped, _ = grouped_pair(old, new)

        assert list(grouped["codelists"]) == ["CL1"]

    def test__every_change_is_attributed_to_some_codelist(self):
        old = make_package(
            "2024-01-01",
            [
                make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")]),
                make_codelist("CL2", "SUBCL2", [make_term("T2", "SUB2")]),
            ],
        )
        new = make_package(
            "2024-04-01",
            [
                make_codelist("CL1", "SUBCL1", [make_term("T1", "SUBX")]),
                make_codelist("CL3", "SUBCL3", [make_term("T3", "SUB3")]),
            ],
        )

        grouped, _ = grouped_pair(old, new)

        assert not any(grouped["unscoped"].values())

    def test__group_report_covers_cumulative_and_every_step(self):
        packages = [
            normalize_package(
                make_package(
                    date, [make_codelist("CL1", "SUBCL1", [make_term("T1", value)])]
                )
            )
            for date, value in (
                ("2024-01-01", "SUB1"),
                ("2024-04-01", "SUB2"),
                ("2024-07-01", "SUB3"),
            )
        ]
        report = build_report(packages)

        grouped = group_report(report, packages)

        assert len(grouped["steps"]) == 2
        assert grouped["cumulative"]["order"] == ["CL1"]
        # Cumulative collapses SUB1 -> SUB3; the steps show both hops.
        assert grouped["cumulative"]["distinct_counts"][4] == 1
        assert [s["distinct_counts"][4] for s in grouped["steps"]] == [1, 1]
