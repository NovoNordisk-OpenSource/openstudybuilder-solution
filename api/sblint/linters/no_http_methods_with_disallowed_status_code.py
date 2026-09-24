import ast
import sys

from rich import print as rptint
from rich.table import Table

from sblint.sblinter import SBLinter


class NoHTTPMethodsWithDisallowedStatusCode(SBLinter):
    ALLOWED_STATUS_CODES = {
        "get": [200],
        "post": [200, 201, 202, 204, 207],
        "patch": [200, 207],
        "put": [200],
        "delete": [200, 204],
    }

    @classmethod
    def validate(cls, code_tree: ast.Module, _file_path: str) -> list[int]:
        """
        Validates the given Python code by checking if it defines any HTTP method calls
        with disallowed status codes.

        Args:
            code_tree (ast.Module): The tree of the Python code to be validated.

        Returns:
            list[int]: A list of line numbers where HTTP method calls have disallowed status codes.
        """
        lines = []

        for node in ast.walk(code_tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and any(
                    keyword
                    for keyword in node.keywords
                    if keyword.arg == "status_code"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value
                    not in cls.ALLOWED_STATUS_CODES[node.func.attr.lower()]
                )
            ):
                lines.append(node.lineno)
        return sorted(lines)

    @classmethod
    def expose_validation(cls, invalid_files: list[str]) -> None:
        """
        Displays a message indicating that HTTP methods should only use allowed status codes.

        Args:
            invalid_files (list[str]): A list of file paths that contain HTTP methods
            with disallowed status codes.
        """
        if invalid_files:
            rptint(
                "Wow, you've outdone yourself! This code is a masterclass in how not to handle HTTP status codes. Bravo, truly inspiring levels of chaos!\n"
            )

            rptint(
                "Fix: Ensure that HTTP methods only use the following allowed status codes:"
            )

            table = Table()

            table.add_column("HTTP Method", style="cyan")
            table.add_column("Allowed Status Codes", style="green")

            for method, codes in cls.ALLOWED_STATUS_CODES.items():
                table.add_row(method.upper(), ", ".join(str(code) for code in codes))

            rptint(table)

            super().expose_validation(invalid_files)


if __name__ == "__main__":
    NoHTTPMethodsWithDisallowedStatusCode.validate_and_report_me(sys.argv[1:])
