import json
import re
import subprocess

import pytest

from src.scripts.package_diff import site_gen
from src.scripts.package_diff.site_render import IMPACT_PAGES
from src.scripts.package_diff.ct_diff import build_report
from src.scripts.package_diff.ct_diff_grouping import group_report
from src.tests.package_diff.factories import make_codelist, make_package, make_term


def write_packages(tmp_path):
    """Two package files on disk.

    CL1 loses two terms, CL4 loses one, CL3 is new, CL2 is untouched. CL1 and
    CL4 both land in S1, and CL1 outranks CL4 on volume - so a cap of 1 leaves
    CL4 listed on the S1 page with no page of its own, which is the case that
    used to produce dangling links.
    """
    old = make_package(
        "2024-01-01",
        [
            make_codelist(
                "CL1",
                "SUBCL1",
                [
                    make_term("T1", "SUB1"),
                    make_term("T2", "SUB2"),
                    make_term("T5", "SUB5"),
                ],
            ),
            make_codelist("CL2", "SUBCL2", [make_term("T3", "SUB3")]),
            make_codelist(
                "CL4", "SUBCL4", [make_term("T6", "SUB6"), make_term("T7", "SUB7")]
            ),
        ],
    )
    new = make_package(
        "2024-04-01",
        [
            make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")]),
            make_codelist("CL2", "SUBCL2", [make_term("T3", "SUB3")]),
            make_codelist("CL3", "SUBCL3", [make_term("T4", "SUB4")]),
            make_codelist("CL4", "SUBCL4", [make_term("T6", "SUB6")]),
        ],
    )
    paths = []
    for raw in (old, new):
        path = tmp_path / f'sdtmct-{raw["effectiveDate"]}.json'
        path.write_text(json.dumps(raw), encoding="utf-8")
        paths.append(str(path))
    return paths


def model_for(tmp_path):
    files = write_packages(tmp_path)
    return files, site_gen.build_site_model(files)


class Test:
    def test__writes_the_expected_page_tree(self, tmp_path):
        _, (report, grouped, _) = model_for(tmp_path)
        out = tmp_path / "site"

        site_gen.write_site_sources(report, grouped, out)

        docs = out / "docs"
        for name in (
            "index.md",
            "codelists-removed.md",
            "terms-removed-from-catalogue.md",
            "terms-removed-from-codelist.md",
            "submission-values-changed.md",
            "terms-added-to-extensible-codelists.md",
            "terms-moved-between-codelists.md",
            "new-codelists.md",
            "term-attribute-changes.md",
            "full-report.md",
            "full-report.json",
            "codelists/index.md",
        ):
            assert (docs / name).exists(), name
        assert (out / "mkdocs.yml").exists()

    def test__every_impact_band_gets_a_page_the_nav_points_at(self, tmp_path):
        # The nav is hand-written text, so adding a band to IMPACT_PAGES without
        # adding it to the nav would produce a page nobody can reach.
        _, (report, grouped, _) = model_for(tmp_path)
        out = tmp_path / "site"

        site_gen.write_site_sources(report, grouped, out)

        nav = (out / "mkdocs.yml").read_text()
        for page in IMPACT_PAGES.values():
            assert (out / "docs" / page).exists(), page
            assert page in nav, page

    def test__writes_one_page_per_changed_codelist_and_no_others(self, tmp_path):
        _, (report, grouped, _) = model_for(tmp_path)
        out = tmp_path / "site"

        site_gen.write_site_sources(report, grouped, out)

        pages = {p.stem for p in (out / "docs" / "codelists").glob("*.md")}
        assert pages == {"index", "CL1", "CL3", "CL4"}  # CL2 did not change

    def test__cap_limits_pages_but_never_the_full_report(self, tmp_path):
        _, (report, grouped, _) = model_for(tmp_path)
        out = tmp_path / "site"

        site_gen.write_site_sources(report, grouped, out, max_codelist_pages=1)

        pages = {p.stem for p in (out / "docs" / "codelists").glob("*.md")}
        assert pages == {"index", "CL1"}  # worst-first, so CL1 survives the cap
        assert "Output capped" in (out / "docs" / "index.md").read_text()
        # The backstop stays complete.
        full = json.loads((out / "docs" / "full-report.json").read_text())
        assert full["cumulative"]["bands"]

    def test__cap_does_not_leave_links_to_pages_that_were_never_written(self, tmp_path):
        # mkdocs reports these as broken-link warnings; a reviewer gets a 404.
        _, (report, grouped, _) = model_for(tmp_path)
        out = tmp_path / "site"

        site_gen.write_site_sources(report, grouped, out, max_codelist_pages=1)

        docs = out / "docs"
        written = {p.relative_to(docs).as_posix() for p in docs.rglob("*.md")}
        for page in docs.rglob("*.md"):
            base = page.parent.relative_to(docs)
            for target in re.findall(r"\]\(([^)]+\.md)\)", page.read_text()):
                resolved = (base / target).as_posix().replace("codelists/../", "")
                assert resolved in written, f"{page.name} links to missing {target}"

    def test__full_report_is_kept_out_of_the_search_index(self, tmp_path):
        # It restates the per-codelist pages, so indexing it would duplicate
        # every hit and double what the browser downloads.
        _, (report, grouped, _) = model_for(tmp_path)
        out = tmp_path / "site"

        site_gen.write_site_sources(report, grouped, out)

        full = (out / "docs" / "full-report.md").read_text()
        assert full.startswith("---\nsearch:\n  exclude: true\n---")
        # Only that page: the codelist pages are the search surface.
        assert "search:" not in (out / "docs" / "codelists" / "CL1.md").read_text()

    def test__no_cap_banner_when_the_cap_is_not_reached(self, tmp_path):
        _, (report, grouped, _) = model_for(tmp_path)
        out = tmp_path / "site"

        site_gen.write_site_sources(report, grouped, out, max_codelist_pages=50)

        assert "Output capped" not in (out / "docs" / "index.md").read_text()

    def test__main_never_shells_out_without_build_html(self, tmp_path, monkeypatch):
        # The default path must work with nothing installed beyond the stdlib.
        files = write_packages(tmp_path)

        def fail(*args, **kwargs):
            raise AssertionError("subprocess.run must not be called")

        monkeypatch.setattr(subprocess, "run", fail)

        site_gen.main([*files, "--out-dir", str(tmp_path / "site")])

        assert (tmp_path / "site" / "docs" / "index.md").exists()

    def test__missing_mkdocs_binary_is_reported_not_raised(self, tmp_path, caplog):
        # The Markdown is already written by then, so this is a warning about an
        # optional convenience, not a failure.
        out = tmp_path / "site"
        out.mkdir()

        assert site_gen.run_mkdocs(out, "build", mkdocs_bin="no-such-mkdocs") is False
        assert "mkdocs not found" in caplog.text

    def test__mkdocs_failure_is_reported_not_raised(
        self, tmp_path, monkeypatch, caplog
    ):
        def fail(*args, **kwargs):
            raise subprocess.CalledProcessError(1, "mkdocs")

        monkeypatch.setattr(subprocess, "run", fail)

        assert site_gen.run_mkdocs(tmp_path, "build") is False
        assert "failed with exit code 1" in caplog.text

    def test__default_out_dir_names_the_catalogue(self, tmp_path):
        _, (report, _, _) = model_for(tmp_path)

        assert site_gen.default_out_dir(report).startswith("sdtm_ct_diff_site_")

    def test__a_single_file_is_rejected(self, tmp_path, capsys):
        files = write_packages(tmp_path)

        with pytest.raises(SystemExit):
            site_gen.main([files[0], "--out-dir", str(tmp_path / "site")])

        assert "At least 2 package files" in capsys.readouterr().err

    def test__build_site_model_matches_building_the_pieces_separately(self, tmp_path):
        files = write_packages(tmp_path)

        report, grouped, packages = site_gen.build_site_model(files)

        # packages come back already normalized and chronologically sorted.
        expected = group_report(build_report(packages), packages)
        assert grouped["cumulative"]["order"] == expected["cumulative"]["order"]
        assert report["catalogues"] == ["SDTM CT"]
        assert [p["effectiveDate"] for p in packages] == ["2024-01-01", "2024-04-01"]
