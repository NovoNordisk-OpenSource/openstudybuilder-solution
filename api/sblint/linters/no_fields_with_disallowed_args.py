import ast
import sys

from rich import print as rptint

from sblint.sblinter import SBLinter


class NoFieldsWithDisallowedArgs(SBLinter):
    DISALLOWED_ARGS = ["title"]

    @classmethod
    def validate(cls, code_tree: ast.Module, _file_path: str) -> list[int]:
        """
        Validates the given Python code by checking if it contains any
        `pydantic.Field` assignments where fields listed in
        DISALLOWED_ARGS have are passed as arguments.

        Args:
            code_tree (ast.Module): The tree of the Python code to be validated.

        Returns:
            list[int]: A list of line numbers of assignments with implicit Any.
        """
        lines = []

        for node in ast.walk(code_tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "Field"
                and any(keyword.arg in cls.DISALLOWED_ARGS for keyword in node.keywords)
            ):
                lines.append(node.lineno)
        return sorted(lines)

    @classmethod
    def expose_validation(cls, invalid_files: list[str]) -> None:
        """
        Displays a message indicating that disallowed arguments should be removed from the `pydantic.Field`.

        Args:
            invalid_files (list[str]): A list of file paths that contain assignments without type hints.
        """
        if invalid_files:
            rptint(
                "Wow, incredible work! You've used disallowed arguments in [b]pydantic.Field[/b]. A true testament to your commitment to making life harder for everyone else!\n"
            )

            args = ", ".join(f"[b]{arg}[/b]" for arg in cls.DISALLOWED_ARGS)
            rptint(
                f"Fix: Remove the following disallowed arguments from [b]pydantic.Field[/b]: {args}"
            )
            super().expose_validation(invalid_files)


if __name__ == "__main__":
    NoFieldsWithDisallowedArgs.validate_and_report_me(sys.argv[1:])
