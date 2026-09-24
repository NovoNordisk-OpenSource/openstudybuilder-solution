import ast
import sys

from rich import print as rptint
from rich.table import Table

from sblint.sblinter import SBLinter


class NoUnnecessaryImports(SBLinter):
    UNNECESSARY_IMPORTS = [
        ("typing", "Optional", "x | None"),
        ("typing", "Union", "x | y"),
        ("typing", "List", "list"),
        ("typing", "Set", "set"),
        ("typing", "Dict", "dict"),
        ("typing", "Tuple", "tuple"),
        ("typing", "Type", "type"),
    ]

    @classmethod
    def validate(cls, code_tree: ast.Module, _file_path: str) -> list[int]:
        """
        Validates the given Python code by checking if it contains any
        imports that are deemed unnecessary based on the `cls.UNNECESSARY_IMPORTS`
        The `UNNECESSARY_IMPORTS` attribute is expected to be a collection of tuples
        where each tuple contains, in order, a module name, an import name and an alternative.

        Args:
            code_tree (ast.Module): The tree of the Python code to be validated.

        Returns:
            list[int]: A list of line numbers where unnecessary imports are found.
        """
        MODULES = {x[0] for x in cls.UNNECESSARY_IMPORTS}
        IMPORTS = {x[1] for x in cls.UNNECESSARY_IMPORTS}

        lines = []

        for node in ast.walk(code_tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module in MODULES
                and any(alias.name in IMPORTS for alias in node.names)
            ) or (
                isinstance(node, ast.Import)
                and any(alias.name in IMPORTS for alias in node.names)
            ):
                lines.append(node.lineno)
        return sorted(lines)

    @classmethod
    def expose_validation(cls, invalid_files: list[str]) -> None:
        """
        Displays a message indicating that unnecessary imports should be removed
        from the specified files and suggests alternatives. It also displays a
        formatted table of modules, unnecessary imports, and their alternatives.

        Args:
            invalid_files (list[str]): A list of file paths that contain unnecessary imports.
        """
        if invalid_files:
            print(
                "Awesome! You've transformed your code into a museum of outdated unnecessary imports. A masterpiece of inefficiency that future developers will study as a cautionary tale.\n"
            )

            print("Fix: Remove unnecessary imports and use their alternatives:")

            table = Table()

            table.add_column("Module", style="cyan")
            table.add_column("Import", style="red")
            table.add_column("Alternative", style="green")

            for module, unnecessary, alternative in cls.UNNECESSARY_IMPORTS:
                table.add_row(
                    module, f":x: {unnecessary}", f":white_check_mark: {alternative}"
                )

            rptint(table)

            super().expose_validation(invalid_files)


if __name__ == "__main__":
    NoUnnecessaryImports.validate_and_report_me(sys.argv[1:])
