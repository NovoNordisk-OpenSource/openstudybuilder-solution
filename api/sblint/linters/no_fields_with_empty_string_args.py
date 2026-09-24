import ast
import sys

from rich import print as rptint

from sblint.sblinter import SBLinter


class NoFieldsWithEmptyStringArgs(SBLinter):
    NON_EMPTY_STRING_ARGS = ["description"]

    @classmethod
    def validate(cls, code_tree: ast.Module, _file_path: str) -> list[int]:
        """
        Validates the given Python code by checking if it contains any
        `pydantic.Field` assignments where fields listed in
        NON_EMPTY_STRING_ARGS have empty string arguments.

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
                and any(
                    keyword.arg in cls.NON_EMPTY_STRING_ARGS
                    for keyword in node.keywords
                    if isinstance(keyword.value, ast.Constant)
                    and keyword.value.value == ""
                )
            ):
                lines.append(node.lineno)
        return sorted(lines)

    @classmethod
    def expose_validation(cls, invalid_files: list[str]) -> None:
        """
        Displays a message indicating that empty strings were passed for specific fields
        listed in NON_EMPTY_STRING_ARGS.

        Args:
            invalid_files (list[str]): A list of file paths that contain invalid `Field` assignments.
        """
        if invalid_files:
            rptint(
                "Awesome, you've managed to pass empty strings to [b]pydantic.Field[/b] arguments that explicitly require non-empty strings. "
                "This is the kind of innovation that keeps bugs alive and thriving. Bravo! Now go fix it before it becomes a monument to bad coding.\n"
            )

            args = ", ".join(f"[b]{arg}[/b]" for arg in cls.NON_EMPTY_STRING_ARGS)
            rptint(
                f"Fix: Either assign a non-empty string to the following arguments or remove them entirely: {args}."
            )

            super().expose_validation(invalid_files)


if __name__ == "__main__":
    NoFieldsWithEmptyStringArgs.validate_and_report_me(sys.argv[1:])
