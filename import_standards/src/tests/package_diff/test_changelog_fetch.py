from src.scripts.package_diff.changelog_fetch import (
    CATALOGUES,
    archive_url,
    current_url,
    is_excel,
    local_catalogues,
    package_dates,
    summarize,
)


class Test:
    def test__archive_url_follows_the_plain_pattern(self):
        assert archive_url("sdtmct", "2025-03-28") == (
            "https://evs.nci.nih.gov/ftp1/CDISC/SDTM/Archive/"
            "SDTM Terminology Changes 2025-03-28.xls"
        )

    def test__current_url_is_undated_at_the_catalogue_root(self):
        # The newest release is published here rather than in Archive/.
        assert current_url("sdtmct") == (
            "https://evs.nci.nih.gov/ftp1/CDISC/SDTM/SDTM Terminology Changes.xls"
        )

    def test__cdash_lives_in_the_sdtm_directory(self):
        # Directory is not derivable from the catalogue name.
        assert "/CDISC/SDTM/Archive/CDASH Terminology Changes 2025-03-28.xls" in (
            archive_url("cdashct", "2025-03-28")
        )

    def test__glossary_and_mrct_deviate_from_the_stem_pattern(self):
        # Glossary prefixes "CDISC"; MRCT drops "Terminology" altogether.
        assert current_url("glossaryct").endswith(
            "/Glossary/CDISC Glossary Terminology Changes.xls"
        )
        assert current_url("mrctct").endswith(
            "/MRCT Center Clinical Research Glossary/"
            "CDISC MRCT Center Clinical Research Glossary Changes.xls"
        )

    def test__is_excel_rejects_the_spa_shell(self):
        # The server answers 200 with HTML for missing files, so this check -
        # not the status code - is what decides whether a file exists.
        assert is_excel("application/vnd.ms-excel") is True
        assert is_excel("application/vnd.ms-excel; charset=utf-8") is True
        assert is_excel("text/html") is False
        assert is_excel(None) is False

    def test__package_dates_matches_only_its_own_catalogue(self, tmp_path):
        for name in (
            "sdtmct-2024-03-29.json",
            "sdtmct-2025-03-28.json",
            "qs-ftct-2014-09-26.json",
            "define-xmlct-2024-03-29.json",
            "notapackage.json",
            "sdtmct-2024-03-29.txt",
        ):
            (tmp_path / name).write_text("{}", encoding="utf-8")

        # Hyphenated catalogue names must not be mistaken for each other.
        assert package_dates(str(tmp_path), "sdtmct") == ["2024-03-29", "2025-03-28"]
        assert package_dates(str(tmp_path), "qs-ftct") == ["2014-09-26"]
        assert package_dates(str(tmp_path), "define-xmlct") == ["2024-03-29"]
        assert package_dates(str(tmp_path), "adamct") == []

    def test__local_catalogues_lists_prefixes(self, tmp_path):
        for name in ("sdtmct-2024-03-29.json", "adamct-2024-03-29.json", "junk.json"):
            (tmp_path / name).write_text("{}", encoding="utf-8")

        assert local_catalogues(str(tmp_path)) == ["adamct", "sdtmct"]

    def test__every_known_catalogue_has_a_directory_and_stem(self):
        for catalogue, (directory, stem) in CATALOGUES.items():
            assert directory and stem, catalogue

    def test__summarize_names_the_dates_without_a_change_log(self):
        text = summarize(
            {
                "sdtmct": [
                    {"date": "2024-03-29", "status": "downloaded"},
                    {"date": "2025-03-28", "status": "present"},
                ],
                "protocolct": [{"date": "2017-09-29", "status": "missing"}],
            }
        )

        assert "sdtmct: 1 downloaded, 1 present" in text
        assert "no change log for: 2017-09-29" in text
