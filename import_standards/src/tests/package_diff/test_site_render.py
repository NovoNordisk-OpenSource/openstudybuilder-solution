import re

from src.scripts.package_diff.ct_diff import build_report, normalize_package
from src.scripts.package_diff.ct_diff_grouping import group_report
from src.scripts.package_diff.site_render import (
    build_mkdocs_config,
    codelist_link,
    render_codelist_page,
    render_codelists_index_page,
    render_impact_page,
    render_new_codelists_page,
    render_overview_page,
    render_term_attribute_changes_page,
    slug_for,
)
from src.tests.package_diff.factories import make_codelist, make_package, make_term


def model(old_raw, new_raw):
    """Build the (report, grouped-cumulative, cumulative-pair-diff) trio."""
    packages = [normalize_package(old_raw), normalize_package(new_raw)]
    report = build_report(packages)
    grouped = group_report(report, packages)
    return report, grouped["cumulative"], report["cumulative"]


def simple_model():
    """CL1 loses a term and renames; CL2 is untouched."""
    old = make_package(
        "2024-01-01",
        [
            make_codelist(
                "CL1", "SUBCL1", [make_term("T1", "SUB1"), make_term("T2", "SUB2")]
            ),
            make_codelist("CL2", "SUBCL2", [make_term("T3", "SUB3")]),
        ],
    )
    new = make_package(
        "2024-04-01",
        [
            make_codelist(
                "CL1", "SUBCL1", [make_term("T1", "SUB1")], name="Renamed CL1"
            ),
            make_codelist("CL2", "SUBCL2", [make_term("T3", "SUB3")]),
        ],
    )
    return model(old, new)


class Test:
    def test__slug_is_safe_for_a_path(self):
        # Real conceptIds are alphanumeric; a malformed package must still not
        # be able to write outside the docs directory.
        assert slug_for("C66741") == "C66741"
        assert slug_for("../../etc/passwd") == ".._.._etc_passwd"
        assert "/" not in slug_for("a/b")

    def test__empty_categories_are_omitted_entirely(self):
        # Not rendered as "(none)": on a per-codelist page most categories are
        # empty, and across hundreds of pages that filler would be most of the text.
        _, grouped, pair_diff = simple_model()

        page = render_codelist_page(pair_diff, grouped["codelists"]["CL1"], grouped)

        assert "## Terms removed from the catalogue (1)" in page
        assert "(none)" not in page
        assert "New codelists and terms" not in page

    def test__pages_name_the_change_rather_than_grade_it(self):
        # The whole point of the rename: no S-numbers anywhere a reviewer looks.
        _, grouped, pair_diff = simple_model()

        pages = [
            render_codelist_page(pair_diff, grouped["codelists"]["CL1"], grouped),
            render_codelists_index_page(grouped),
            render_impact_page(pair_diff, grouped, 2),
        ]

        for page in pages:
            assert not re.search(r"\bS\d{1,2}\b", page), page

    def test__codelist_page_does_not_repeat_its_own_name_on_every_line(self):
        old = make_package(
            "2024-01-01", [make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")])]
        )
        new = make_package(
            "2024-04-01", [make_codelist("CL1", "SUBCL1", [make_term("T1", "SUBX")])]
        )
        _, grouped, pair_diff = model(old, new)

        page = render_codelist_page(pair_diff, grouped["codelists"]["CL1"], grouped)

        # The heading already names the codelist, so the column that would hold
        # it on every row is dropped rather than printed.
        assert "| Term | Before | After |" in page
        assert '| `T1` "T1 preferred term" | "SUB1" | "SUBX" |' in page
        assert "CL1" not in page.split("## Submission values changed")[1]

    def test__links_point_only_at_codelists_that_have_a_page(self):
        _, grouped, _ = simple_model()
        link = codelist_link(grouped, prefix="codelists/")

        assert link("CL1") == "codelists/CL1.md"
        # CL2 did not change, so it has no page and must not be linked.
        assert link("CL2") is None

    def test__index_lists_only_changed_codelists_worst_first(self):
        _, grouped, _ = simple_model()

        page = render_codelists_index_page(grouped)

        assert "1 codelist(s) changed" in page
        assert "CL1" in page
        assert "](CL2.md)" not in page

    def test__index_names_the_categories_instead_of_grading_the_codelist(self):
        # A reviewer may not share our view of what is worst, so the row states
        # what changed and leaves the verdict to them.
        _, grouped, _ = simple_model()

        row = [
            ln
            for ln in render_codelists_index_page(grouped).splitlines()
            if "CL1" in ln
        ][0]

        assert "Terms removed from the catalogue" in row
        assert "Codelist names and descriptions updated" in row
        # No severity grade, and no per-category count columns to decode.
        assert "Worst" not in render_codelists_index_page(grouped)

    def test__impact_page_explains_fan_out_when_one_change_spans_codelists(self):
        # A move is a single record naming the codelist it left and the one it
        # entered, so it is listed under both and the bullets outnumber the
        # changes. CL2 is extensible, so the move lands in "terms added to
        # extensible codelists" rather than the plain move category.
        old = make_package(
            "2024-01-01",
            [
                make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")]),
                make_codelist("CL2", "SUBCL2", [], extensible="true"),
            ],
        )
        new = make_package(
            "2024-04-01",
            [
                make_codelist("CL1", "SUBCL1", []),
                make_codelist(
                    "CL2", "SUBCL2", [make_term("T1", "SUB1")], extensible="true"
                ),
            ],
        )
        _, grouped, pair_diff = model(old, new)

        page = render_impact_page(pair_diff, grouped, 5)

        assert "1 change(s) affecting 2 codelist(s)." in page
        assert "Listed 2 times below" in page

    def test__impact_page_does_not_claim_fan_out_for_per_codelist_records(self):
        # A term deleted from two codelists is two membership records, one per
        # codelist - two distinct facts, not one fact listed twice.
        old = make_package(
            "2024-01-01",
            [
                make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")]),
                make_codelist("CL2", "SUBCL2", [make_term("T1", "SUB1")]),
            ],
        )
        new = make_package(
            "2024-04-01",
            [make_codelist("CL1", "SUBCL1", []), make_codelist("CL2", "SUBCL2", [])],
        )
        _, grouped, pair_diff = model(old, new)

        page = render_impact_page(pair_diff, grouped, 2)

        assert "2 change(s) affecting 2 codelist(s)." in page
        assert "times below" not in page

    def test__impact_page_says_so_when_a_category_is_empty(self):
        # simple_model only removes a term and renames a codelist, so nothing
        # lands in "submission values changed".
        _, grouped, pair_diff = simple_model()

        page = render_impact_page(pair_diff, grouped, 4)

        assert "Nothing in this diff" in page
        assert "submission values changed" in page

    def test__term_attribute_page_links_back_to_every_home_codelist(self):
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

        _, grouped, pair_diff = model(packages("Before."), packages("After."))

        page = render_term_attribute_changes_page(pair_diff, grouped)

        assert "1 change(s) to term attributes" in page
        assert "codelists/CL1.md" in page
        assert "codelists/CL2.md" in page

    def test__term_attribute_changes_are_a_table_not_a_bullet_list(self):
        # Uniform changes - one term, one property, before and after - so fixed
        # columns can be scanned down. Prose bullets could not be.
        def packages(definition):
            return make_package(
                "2024-01-01",
                [make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1", definition)])],
            )

        _, grouped, pair_diff = model(packages("Before."), packages("After."))

        page = render_term_attribute_changes_page(pair_diff, grouped)
        row = [ln for ln in page.splitlines() if ln.startswith("| `T1`")][0]

        assert "| Term | Property | Before | After | Codelists |" in page
        assert row.count("|") == 6
        assert "`definition`" in row
        assert '"Before."' in row and '"After."' in row

    def test__a_multi_valued_cell_gets_a_line_per_value(self):
        # Synonym lists run to a dozen entries. Comma-separated inside a table
        # cell they are unreadable at any column width.
        def packages(synonyms):
            term = make_term("T1", "SUB1")
            term["synonyms"] = synonyms
            return make_package("2024-01-01", [make_codelist("CL1", "SUBCL1", [term])])

        _, grouped, pair_diff = model(packages(["B", "A"]), packages(["C", "A", "B"]))

        page = render_term_attribute_changes_page(pair_diff, grouped)
        row = [ln for ln in page.splitlines() if ln.startswith("| `T1`")][0]

        assert '| "A"<br>"B" | "A"<br>"B"<br>"C" |' in row

    def test__a_moved_term_names_the_codelist_whose_page_it_is_on(self):
        # The row lists both sides of the move, so the page's own codelist has
        # to be marked or the reader cannot tell which way the term went.
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
        _, grouped, pair_diff = model(old, new)

        page = render_codelist_page(pair_diff, grouped["codelists"]["CL1"], grouped)
        row = [ln for ln in page.splitlines() if ln.startswith("| `T1`")][0]

        assert "| Term | Left | Entered |" in page
        assert "**this codelist**" in row
        assert "CL2" in row

    def test__a_pipe_in_a_definition_does_not_invent_a_column(self):
        # Definitions are free text out of the package. An unescaped pipe or
        # newline silently breaks the row it lands in.
        def packages(definition):
            return make_package(
                "2024-01-01",
                [make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1", definition)])],
            )

        _, grouped, pair_diff = model(
            packages("a | b"), packages("first line\nsecond line")
        )

        page = render_term_attribute_changes_page(pair_diff, grouped)
        row = [ln for ln in page.splitlines() if ln.startswith("| `T1`")][0]

        assert row.count("|") == 6 + 1  # the escaped pipe is still a character
        assert "a \\| b" in row
        assert "first line<br>second line" in row

    def test__overview_reports_the_changed_share_and_the_categories(self):
        report, grouped, _ = simple_model()

        page = render_overview_page(report, grouped)

        assert "**1** of 2 codelists changed" in page
        assert (
            "| **[Terms removed from the catalogue]"
            "(terms-removed-from-catalogue.md)** | 1 | 1 |" in page
        )

    def test__overview_warns_when_the_page_cap_bites(self):
        # Never truncate silently: the full report stays complete and says so.
        report, grouped, _ = simple_model()

        page = render_overview_page(report, grouped, capped=(10, 96))

        assert "Output capped" in page
        assert "10 of 96 changed codelists" in page
        assert "full-report.md" in page

    def test__overview_has_no_cap_banner_by_default(self):
        report, grouped, _ = simple_model()

        assert "Output capped" not in render_overview_page(report, grouped)

    def test__nav_has_one_codelists_entry_not_one_per_codelist(self):
        # Guards the scale decision: 500+ nav entries would be unusable, and
        # per-codelist pages are reachable by search and the index instead.
        report, _, _ = simple_model()

        config = build_mkdocs_config(report)

        assert config.count("Changed codelists: codelists/index.md") == 1
        assert "CL1.md" not in config

    def test__mkdocs_config_escapes_quotes_in_the_site_name(self):
        report, _, _ = simple_model()

        config = build_mkdocs_config(report, site_name='A "quoted" name')

        assert 'site_name: "A \\"quoted\\" name"' in config

    def test__new_codelists_page_lists_them_with_what_a_reviewer_needs(self):
        old = make_package(
            "2024-01-01", [make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")])]
        )
        new = make_package(
            "2024-04-01",
            [
                make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")]),
                make_codelist(
                    "CL9",
                    "SUBCL9",
                    [make_term("T8", "SUB8"), make_term("T9", "SUB9")],
                    extensible="true",
                ),
            ],
        )
        _, grouped, _ = model(old, new)

        page = render_new_codelists_page(grouped)

        # Only CL9 is new; CL1 is unchanged and has no bucket at all.
        assert "CL9" in page
        assert "CL1" not in page
        # Submission value, extensibility and term count, so the check against
        # sponsor-defined codelists can be made without opening the package.
        assert "| `SUBCL9` | yes | 2 |" in page

    def test__new_codelists_page_says_so_when_there_are_none(self):
        _, grouped, _ = simple_model()

        assert "introduces no new codelists" in render_new_codelists_page(grouped)

    def test__new_codelists_page_does_not_link_a_page_the_cap_cut(self):
        old = make_package("2024-01-01", [make_codelist("CL1", "SUBCL1", [])])
        new = make_package(
            "2024-04-01",
            [
                make_codelist("CL1", "SUBCL1", []),
                make_codelist("CL9", "SUBCL9", [make_term("T9", "SUB9")]),
            ],
        )
        _, grouped, _ = model(old, new)

        page = render_new_codelists_page(grouped, available=set())

        assert "codelists/CL9.md" not in page
        assert "CL9" in page

    def test__extensible_addition_page_tells_the_reviewer_what_to_check(self):
        old = make_package(
            "2024-01-01",
            [
                make_codelist(
                    "CL1", "SUBCL1", [make_term("T1", "SUB1")], extensible="true"
                )
            ],
        )
        new = make_package(
            "2024-04-01",
            [
                make_codelist(
                    "CL1",
                    "SUBCL1",
                    [make_term("T1", "SUB1"), make_term("T2", "SUB2")],
                    extensible="true",
                )
            ],
        )
        _, grouped, pair_diff = model(old, new)

        page = render_impact_page(pair_diff, grouped, 5)

        assert "sponsor-defined" in page
        assert "1 change(s) affecting 1 codelist(s)." in page
        # The catalogue-wide fact survives the record that was dropped.
        assert "new in this package" in page
