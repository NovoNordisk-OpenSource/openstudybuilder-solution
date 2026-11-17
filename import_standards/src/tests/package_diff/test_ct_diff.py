import json

import pytest

from src.scripts.package_diff.ct_diff import (
    band_changes,
    derive_moves,
    diff_fields,
    diff_memberships,
    diff_package_pair,
    diff_terms,
    extensible_codelists,
    normalize_package,
    render_report,
    severity_of,
    CODELIST_FIELDS,
    TERM_FIELDS,
)
from src.tests.package_diff.factories import make_codelist, make_package, make_term

# A move out of CL9 into CL8, for severity checks that need a shaped record.
MOVE = {"conceptId": "T1", "left": ["CL9"], "entered": ["CL8"]}


class Test:
    def test__normalize_package_coerces_extensible_and_synonyms(self):
        raw = make_package(
            "2024-01-01",
            [
                make_codelist(
                    "CL1", "SUBCL1", [make_term("T1", "SUB1")], extensible="true"
                ),
                make_codelist(
                    "CL2", "SUBCL2", [make_term("T2", "SUB2", synonyms=["a"])]
                ),
            ],
        )

        package = normalize_package(raw)

        assert package["codelists"]["CL1"]["extensible"] is True
        assert package["codelists"]["CL2"]["extensible"] is False
        # synonyms absent on T1 -> empty frozenset, not None
        assert package["terms"]["T1"]["synonyms"] == frozenset()
        assert package["terms"]["T2"]["synonyms"] == frozenset(["a"])

    def test__normalize_package_splits_terms_from_memberships(self):
        # The same term in two codelists with two different submission values.
        raw = make_package(
            "2024-01-01",
            [
                make_codelist("CL1", "SUBCL1", [make_term("T1", "CODE")]),
                make_codelist("CL2", "SUBCL2", [make_term("T1", "Long name")]),
            ],
        )

        package = normalize_package(raw)

        # One term, two memberships
        assert list(package["terms"]) == ["T1"]
        assert package["memberships"] == {
            ("CL1", "T1"): "CODE",
            ("CL2", "T1"): "Long name",
        }
        # submissionValue must not leak onto the term itself
        assert "submissionValue" not in package["terms"]["T1"]

    def test__normalize_package_warns_on_conflicting_term_attributes(self, caplog):
        raw = make_package(
            "2024-01-01",
            [
                make_codelist(
                    "CL1", "SUBCL1", [make_term("T1", "SUB1", definition="One.")]
                ),
                make_codelist(
                    "CL2", "SUBCL2", [make_term("T1", "SUB2", definition="Two.")]
                ),
            ],
        )

        normalize_package(raw)

        assert "T1" in caplog.text
        assert "definition" in caplog.text
        assert "CL1" in caplog.text and "CL2" in caplog.text

    def test__diff_fields(self):
        old = {"name": "A", "definition": "D", "synonyms": frozenset(["x", "y"])}
        new = {"name": "B", "definition": "D", "synonyms": frozenset(["y", "x"])}

        changes = diff_fields(old, new, ("name", "definition", "synonyms"))

        # synonyms compare order-insensitively, definition is unchanged
        assert changes == [("name", "A", "B")]

    def test__diff_fields_no_changes(self):
        entity = {"name": "A", "definition": "D"}

        assert diff_fields(entity, dict(entity), CODELIST_FIELDS) == []

    def test__submission_value_change_is_a_membership_change_only(self):
        old = normalize_package(
            make_package(
                "2024-01-01", [make_codelist("CL1", "SUBCL1", [make_term("T1", "OLD")])]
            )
        )
        new = normalize_package(
            make_package(
                "2024-06-01", [make_codelist("CL1", "SUBCL1", [make_term("T1", "NEW")])]
            )
        )

        _, _, term_changed = diff_terms(old["terms"], new["terms"])
        _, _, membership_changed = diff_memberships(
            old["memberships"], new["memberships"]
        )

        assert term_changed == []
        assert membership_changed == [
            {"key": ("CL1", "T1"), "old": "OLD", "new": "NEW"}
        ]

    def test__term_attribute_change_is_a_term_change_only(self):
        old = normalize_package(
            make_package(
                "2024-01-01",
                [
                    make_codelist(
                        "CL1", "SUBCL1", [make_term("T1", "SUB", definition="Old.")]
                    )
                ],
            )
        )
        new = normalize_package(
            make_package(
                "2024-06-01",
                [
                    make_codelist(
                        "CL1", "SUBCL1", [make_term("T1", "SUB", definition="New.")]
                    )
                ],
            )
        )

        _, _, term_changed = diff_terms(old["terms"], new["terms"])
        _, _, membership_changed = diff_memberships(
            old["memberships"], new["memberships"]
        )

        assert membership_changed == []
        assert term_changed[0]["field_changes"] == [("definition", "Old.", "New.")]

    def test__derive_moves_left_and_entered(self):
        moves, added, removed = derive_moves(
            added=[("CL2", "T1")], removed=[("CL1", "T1")]
        )

        assert moves == [{"conceptId": "T1", "left": ["CL1"], "entered": ["CL2"]}]
        # the add and the remove are absorbed into the move
        assert added == []
        assert removed == []

    def test__derive_moves_ignores_plain_addition(self):
        moves, added, removed = derive_moves(
            added=[("CL2", "T1")], removed=[("CL1", "T2")]
        )

        assert moves == []
        assert added == [("CL2", "T1")]
        assert removed == [("CL1", "T2")]

    def test__severity_of_each_category(self):
        assert severity_of({"kind": "codelist_removed"}) == 1
        assert severity_of({"kind": "term_removed"}) == 2
        # Without the removed-terms set this is the milder of the two removals.
        assert severity_of({"kind": "membership_removed", "key": ("CL1", "T1")}) == 3
        assert severity_of({"kind": "membership_changed"}) == 4
        assert (
            severity_of({"kind": "codelist_changed", "field": "submissionValue"}) == 4
        )
        assert severity_of({"kind": "term_moved", "move": MOVE}) == 6
        # Without the added-codelists set every addition reads as landing in a
        # codelist that already existed.
        assert severity_of({"kind": "membership_added", "key": ("CL1", "T1")}) == 7
        assert severity_of({"kind": "codelist_added"}) == 8
        assert severity_of({"kind": "term_added"}) == 10
        # Property updates are split by what was edited, not by which field.
        for field in ("name", "preferredTerm", "definition", "synonyms", "extensible"):
            assert severity_of({"kind": "codelist_changed", "field": field}) == 11
            assert severity_of({"kind": "term_changed", "field": field}) == 12

    def test__additions_are_cut_by_codelist_age_and_extensibility(self):
        # The four-way split of "something was added", which is the bulk of any
        # CDISC release. Only one of these can collide with a sponsor term.
        extensible = frozenset({"CL_EXT"})
        new = frozenset({"CL_NEW", "CL_NEW_EXT"})

        def band(cl_cid):
            return severity_of(
                {"kind": "membership_added", "key": (cl_cid, "T1")},
                extensible,
                added_codelists=new,
            )

        assert band("CL_EXT") == 5  # existing, was extensible -> collision risk
        assert band("CL_PLAIN") == 7  # existing, nobody could extend it
        assert band("CL_NEW") == 9  # codelist is new in this package
        # A new codelist collapses the extensibility question: there was nothing
        # to extend, so an extensible new codelist bands with the other new ones.
        assert band("CL_NEW_EXT") == 9

    def test__term_gone_from_the_catalogue_outranks_leaving_one_codelist(self):
        # Same record kind, two very different facts: T1 no longer exists at all,
        # T2 just moved out of this codelist and is still resolvable elsewhere.
        gone = frozenset({"T1"})

        removal = {"kind": "membership_removed", "key": ("CL1", "T1")}
        assert severity_of(removal, removed_terms=gone) == 2
        assert severity_of({**removal, "key": ("CL1", "T2")}, removed_terms=gone) == 3

    def test__additions_to_an_already_extensible_codelist_are_flagged(self):
        # The sponsor could already have coined a term of their own in CL1, so a
        # CDISC term arriving there may collide by name or submission value.
        # CL2 was never extensible, so nothing of the sponsor's can be in it.
        extensible = frozenset({"CL1"})

        added = {"kind": "membership_added", "key": ("CL1", "T1")}
        assert severity_of(added, extensible) == 5
        assert severity_of({**added, "key": ("CL2", "T1")}, extensible) == 7

        # derive_moves strips a moved membership out of "added", so the move
        # record is the only place the risk can be seen.
        into_cl1 = {"kind": "term_moved", "move": {**MOVE, "entered": ["CL1"]}}
        assert severity_of(into_cl1, extensible) == 5
        # A move that lands nowhere extensible is just a move.
        assert severity_of({"kind": "term_moved", "move": MOVE}, extensible) == 6

        # A brand new codelist has no sponsor terms to collide with, and a new
        # term is only risky through the codelist it lands in.
        assert severity_of({"kind": "codelist_added"}, extensible) == 8
        assert severity_of({"kind": "term_added"}, extensible) == 10

    def test__extensible_codelists_reads_the_normalized_boolean(self):
        # CDISC ships extensible as the string "true"/"false"; normalize_package
        # coerces it. Guard that here, because banding now depends on it and a
        # regression would silently promote every codelist to S3.
        package = normalize_package(
            make_package(
                "2024-01-01",
                [
                    make_codelist("CL1", "SUBCL1", [], extensible="true"),
                    make_codelist("CL2", "SUBCL2", [], extensible="false"),
                    make_codelist("CL3", "SUBCL3", []),
                ],
            )
        )

        assert extensible_codelists(package) == frozenset({"CL1"})

    def test__diff_package_pair_bands_end_to_end(self):
        old = normalize_package(
            make_package(
                "2024-01-01",
                [
                    make_codelist(
                        "CL1",
                        "SUBCL1",
                        [
                            make_term("T1", "SUB1"),
                            make_term("T2", "SUB2", definition="Old."),
                        ],
                    ),
                    make_codelist("CL2", "SUBCL2", [make_term("T3", "SUB3")]),
                ],
            )
        )
        new = normalize_package(
            make_package(
                "2024-06-01",
                [
                    make_codelist(
                        "CL1",
                        "SUBCL1",
                        [
                            # T1 submission value changed  -> 4
                            make_term("T1", "SUB1-NEW"),
                            # T2 definition changed        -> 8
                            make_term("T2", "SUB2", definition="New."),
                            # T4 is brand new -> 10 (catalogue) + 7 (membership;
                            # CL1 already existed and was never extensible)
                            make_term("T4", "SUB4"),
                        ],
                    ),
                    # CL2 removed, taking T3 with it -> 1 (codelist) + 2 (term
                    # gone from the catalogue, and the membership that held it)
                    # CL3 added -> 8 (codelist) + 9 (its term's membership)
                    # + 10 (T5 is new catalogue-wide)
                    make_codelist("CL3", "SUBCL3", [make_term("T5", "SUB5")]),
                ],
            )
        )

        pair = diff_package_pair(old, new)
        bands = band_changes(pair)
        kinds = {
            level: sorted(c["kind"] for c in changes)
            for level, changes in bands.items()
        }

        assert kinds[1] == ["codelist_removed"]
        # T3 is gone catalogue-wide, so its membership removal is banded with it
        # rather than as a term merely leaving a codelist.
        assert kinds[2] == ["membership_removed", "term_removed"]
        assert kinds[3] == []
        assert kinds[4] == ["membership_changed"]
        assert kinds[5] == []
        assert kinds[6] == []
        # T4 joins CL1, which already existed and nobody could extend.
        assert kinds[7] == ["membership_added"]
        assert kinds[8] == ["codelist_added"]
        # T5 joins CL3, which this package introduces.
        assert kinds[9] == ["membership_added"]
        assert kinds[10] == ["term_added", "term_added"]
        assert kinds[11] == []
        assert kinds[12] == ["term_changed"]

    def test__band_changes_promotes_additions_into_extensible_codelists(self):
        # Same shape as the end-to-end test above, but CL1 was extensible - so
        # the term arriving in it is a collision risk, not a plain addition.
        def package(date, terms, extensible):
            return normalize_package(
                make_package(
                    date, [make_codelist("CL1", "SUBCL1", terms, extensible=extensible)]
                )
            )

        old = package("2024-01-01", [make_term("T1", "SUB1")], "true")
        new = package(
            "2024-06-01", [make_term("T1", "SUB1"), make_term("T2", "SUB2")], "true"
        )

        pair = diff_package_pair(old, new)
        promoted = band_changes(pair, extensible_codelists(old))
        plain = band_changes(pair)

        assert [c["kind"] for c in promoted[5]] == ["membership_added"]
        # The catalogue-wide term_added is not codelist-specific, so it stays put.
        assert [c["kind"] for c in promoted[10]] == ["term_added"]
        # Without the extensible set nothing is promoted at all.
        assert plain[5] == []
        assert [c["kind"] for c in plain[7]] == ["membership_added"]

    def test__render_report_runs_and_marks_mixed_catalogues(self):
        from src.scripts.package_diff.ct_diff import build_report

        sdtm = normalize_package(
            make_package(
                "2024-01-01", [make_codelist("CL1", "S1", [make_term("T1", "A")])]
            ),
            source="sdtmct-2024-01-01.json",
        )
        adam = normalize_package(
            make_package(
                "2024-06-01",
                [make_codelist("CL1", "S1", [make_term("T1", "A")])],
                name="ADaM CT",
            ),
            source="adamct-2024-06-01.json",
        )

        text = render_report(build_report([sdtm, adam]))

        assert "WARNING" in text
        assert "SDTM CT" in text and "ADaM CT" in text
        # identical content across the two files -> no changes to report
        assert "(no changes)" in text

    def test__diff_package_files_is_callable_from_another_script(self, tmp_path):
        # The seam a multi-catalogue wrapper depends on: load, diff and write
        # without going through argparse or sys.argv.
        from src.scripts.package_diff import diff_package_files, write_report

        for date, definition in (("2024-01-01", "Old."), ("2024-06-01", "New.")):
            path = tmp_path / f"sdtmct-{date}.json"
            path.write_text(
                json.dumps(
                    make_package(
                        date,
                        [
                            make_codelist(
                                "CL1",
                                "SUBCL1",
                                [make_term("T1", "SUB", definition=definition)],
                            )
                        ],
                    )
                ),
                encoding="utf-8",
            )

        # Bare filenames resolved against json_dir, as the CLI does.
        report = diff_package_files(
            ["sdtmct-2024-01-01.json", "sdtmct-2024-06-01.json"],
            json_dir=str(tmp_path),
        )
        out_path, text = write_report(report, out_path=str(tmp_path / "report.md"))

        assert report["catalogues"] == ["SDTM CT"]
        assert (tmp_path / "report.md").read_text(encoding="utf-8") == text
        assert out_path == str(tmp_path / "report.md")

    def test__diff_package_files_enriches_when_given_a_changelog_dir(
        self, tmp_path, monkeypatch
    ):
        # The CLI annotates and this seam did not, which is how the api's port came
        # to have no enrichment at all. A caller passing a changelog dir must get
        # what main() produces, without having to know to call annotate_report
        # itself, in the right place, to get it.
        from src.scripts.package_diff import diff_package_files

        for date, definition in (("2024-01-01", "Old."), ("2024-06-01", "New.")):
            path = tmp_path / f"sdtmct-{date}.json"
            path.write_text(
                json.dumps(
                    make_package(
                        date,
                        [
                            make_codelist(
                                "CL1",
                                "SUBCL1",
                                [make_term("T1", "SUB", definition=definition)],
                            )
                        ],
                    )
                ),
                encoding="utf-8",
            )

        monkeypatch.setattr(
            "src.scripts.package_diff.changelog_annotate.read_changelog_rows",
            lambda _path: [
                {
                    "release_date": "2024-06-01",
                    "request_code": "CDISC-1",
                    "change_type": "Update",
                    "nci_code": "T1",
                    "term_type": "CDISC Definition",
                    "codelist_short_name": "SUBCL1",
                    "codelist_long_name": None,
                    "change_summary": "Update CDISC Definition",
                    "original": "Old.",
                    "new": "New.",
                    "instructions": None,
                }
            ],
        )
        (tmp_path / "sdtmct-2024-06-01.xls").write_bytes(b"stub")

        files = ["sdtmct-2024-01-01.json", "sdtmct-2024-06-01.json"]

        def annotated(report):
            return [
                change
                for step in report["steps"]
                for band in (step.get("bands") or {}).values()
                for change in band
                if change.get("changelog")
            ]

        enriched = diff_package_files(
            files, json_dir=str(tmp_path), changelog_dir=str(tmp_path)
        )
        assert annotated(enriched)

        # Still opt-in: the default stays unenriched, so no existing caller
        # silently starts reading the filesystem.
        assert not annotated(diff_package_files(files, json_dir=str(tmp_path)))

    def test__diff_package_files_raises_instead_of_exiting(self, tmp_path):
        # A wrapper must be able to skip a bad catalogue and carry on, so these
        # are exceptions rather than parser.error()/SystemExit.
        from src.scripts.package_diff import diff_package_files

        with pytest.raises(ValueError):
            diff_package_files(["only-one.json"])

        with pytest.raises(FileNotFoundError):
            diff_package_files(
                ["missing-a.json", "missing-b.json"], json_dir=str(tmp_path)
            )

    def test__term_fields_exclude_submission_value(self):
        # Guards the core modelling decision: submission value is codelist-scoped.
        assert "submissionValue" not in TERM_FIELDS
        assert "submissionValue" in CODELIST_FIELDS
