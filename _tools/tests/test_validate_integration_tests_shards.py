"""Filesystem-only tests for integration shard validation."""

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

from _tools import validate_integration_tests_shards as validator


class TestIntegrationShards(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.api = self.root / "api"
        self.integration = self.api / "clinical_mdr_api/tests/integration"
        self.prefix = "clinical_mdr_api/tests/integration"
        self.workflow = self.root / ".github/workflows/api-build.yml"
        self.workflow.parent.mkdir(parents=True)
        for path in (
            "api/study/test_one.py",
            "api/study_selections/test_two.py",
            "services/test_three.py",
            "test_four.py",
            "api/study/helper.py",
            "api/study/conftest.py",
        ):
            self.write_file(path)
        (self.api / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\n", encoding="utf-8"
        )
        self.shards = [
            {"shard": "study", "paths": f"{self.prefix}/api/study"},
            {
                "shard": "api-rest",
                "paths": f"--ignore={self.prefix}/api/study {self.prefix}/api",
            },
            {
                "shard": "non-api",
                "paths": f"--ignore={self.prefix}/api {self.prefix}",
            },
        ]

    def write_file(self, relative):
        path = self.integration / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "raise RuntimeError('Do not import test modules')\n", encoding="utf-8"
        )

    def validate(self):
        document = {
            "jobs": {
                "test-integration": {"strategy": {"matrix": {"include": self.shards}}}
            }
        }
        self.workflow.write_text(yaml.safe_dump(document), encoding="utf-8")
        return validator.validate_shards(self.root)

    def test_partition_and_directory_boundaries(self):
        self.assertEqual(self.validate(), {"study": 1, "api-rest": 1, "non-api": 2})

    def test_new_directory_is_covered_by_catch_all(self):
        self.write_file("new_feature/test_new.py")
        self.assertEqual(self.validate()["non-api"], 3)

    def test_file_exclusion_and_future_file_catch_all(self):
        self.shards[0]["paths"] += "/test_one.py"
        self.shards.append(
            {
                "shard": "study-rest",
                "paths": f"--ignore={self.prefix}/api/study/test_one.py {self.prefix}/api/study",
            }
        )
        self.write_file("api/study/test_new.py")
        self.assertEqual(self.validate()["study-rest"], 1)

    def test_all_unassigned_files_are_reported(self):
        self.shards.pop()
        with self.assertRaises(ValueError) as caught:
            self.validate()
        self.assertIn(
            "Unassigned: clinical_mdr_api/tests/integration/services/test_three.py",
            str(caught.exception),
        )
        self.assertIn(
            "Unassigned: clinical_mdr_api/tests/integration/test_four.py",
            str(caught.exception),
        )

    def test_multiple_owners_are_reported_with_shard_names(self):
        self.shards[1]["paths"] = f"{self.prefix}/api"
        with self.assertRaisesRegex(
            ValueError, "Multiple owners: .*test_one.py: study, api-rest"
        ):
            self.validate()

    def test_empty_shard_is_rejected(self):
        self.shards.append(
            {"shard": "empty", "paths": f"{self.prefix}/api/study/helper.py"}
        )
        with self.assertRaisesRegex(ValueError, "empty: selects no test files"):
            self.validate()

    def test_duplicate_shard_names_are_rejected(self):
        self.shards[1]["shard"] = "study"
        with self.assertRaisesRegex(ValueError, "Duplicate shard name"):
            self.validate()

    def test_malformed_entries_are_rejected(self):
        for entry in (
            None,
            {},
            {"shard": "bad", "paths": []},
            {"shard": "", "paths": ""},
        ):
            with self.subTest(entry=entry):
                self.shards = [entry]
                with self.assertRaises(ValueError):
                    self.validate()

    def test_unsupported_selectors_are_rejected(self):
        for selector in (
            "-k something",
            f"{self.prefix}/api/study/test_one.py::test_example",
            f"{self.prefix}/api/*",
            f"{self.prefix}/$DIRECTORY",
            "--ignore-glob=*.py",
        ):
            with self.subTest(selector=selector):
                self.shards[0]["paths"] = selector
                with self.assertRaisesRegex(ValueError, "Unsupported selector"):
                    self.validate()

    def test_missing_include_and_exclusion_paths_are_rejected(self):
        for selector in (
            f"{self.prefix}/missing",
            f"--ignore={self.prefix}/missing {self.prefix}/api/study",
        ):
            with self.subTest(selector=selector):
                self.shards[0]["paths"] = selector
                with self.assertRaisesRegex(ValueError, "Selector does not exist"):
                    self.validate()

    def test_paths_outside_integration_are_rejected(self):
        self.shards[0]["paths"] = "."
        with self.assertRaisesRegex(ValueError, "outside the integration root"):
            self.validate()

    def test_overlapping_include_paths_are_rejected(self):
        self.shards[0]["paths"] += f" {self.prefix}/api/study/test_one.py"
        with self.assertRaisesRegex(ValueError, "overlapping include paths"):
            self.validate()

    def test_configured_filename_patterns(self):
        for patterns in ('["check_*.py"]', '"check_*.py"'):
            with self.subTest(patterns=patterns):
                (self.api / "pyproject.toml").write_text(
                    f"[tool.pytest.ini_options]\npython_files = {patterns}\n",
                    encoding="utf-8",
                )
                for path in (
                    "api/study/check_one.py",
                    "api/study_selections/check_two.py",
                    "check_three.py",
                ):
                    self.write_file(path)
                self.assertEqual(
                    self.validate(), {"study": 1, "api-rest": 1, "non-api": 1}
                )

    def test_cli_returns_failure_and_diagnostics(self):
        output = io.StringIO()
        with patch.object(
            validator,
            "validate_shards",
            side_effect=ValueError("Unassigned: test_missing.py"),
        ):
            with redirect_stderr(output):
                self.assertEqual(validator.main(), 1)
        self.assertIn("Unassigned: test_missing.py", output.getvalue())

    def test_cli_returns_success_and_counts(self):
        output = io.StringIO()
        with patch.object(validator, "validate_shards", return_value={"example": 2}):
            with redirect_stdout(output):
                self.assertEqual(validator.main(), 0)
        self.assertIn("2 test files in 1 shards, exactly once", output.getvalue())


if __name__ == "__main__":
    unittest.main()
