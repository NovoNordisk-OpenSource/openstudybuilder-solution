import ast
import sys

from rich import print as rptint

from sblint.sblinter import SBLinter


class NoRelativeImports(SBLinter):
    @classmethod
    def validate(cls, code_tree: ast.Module, _file_path: str) -> list[int]:
        """
        Validates the given Python code by checking if it contains any relative imports.

        Args:
            code_tree (ast.Module): The tree of the Python code to be validated.

        Returns:
            list[int]: A list of line numbers where relative imports are found.
        """
        lines = []

        for node in ast.walk(code_tree):
            if isinstance(node, ast.ImportFrom) and node.level != 0:
                lines.append(node.lineno)
        return sorted(lines)

    @classmethod
    def expose_validation(cls, invalid_files: list[str]) -> None:
        """
        Displays a message indicating that relative imports should be removed from the specified files.

        Args:
            invalid_files (list[str]): A list of file paths that contain relative imports.
        """
        if invalid_files:
            rptint(
                "Relative imports? Really? It's like you saw the rules and thought, 'Nah, I'll just make my own chaos.' Bold move, but not the best one.\n"
            )

            rptint("Fix: Use only absolute paths for imports.")

            super().expose_validation(invalid_files)


if __name__ == "__main__":
    NoRelativeImports.validate_and_report_me(sys.argv[1:])
