import ast
import sys

from rich import print as rptint

from sblint.sblinter import SBLinter


class NoFieldsAsDefaultValueWithoutRequiredArgs(SBLinter):
    REQUIRED_ARGS = {"alias", "default", "default_factory"}

    @classmethod
    def validate(cls, code_tree: ast.Module, _file_path: str) -> list[int]:
        """
        Validates the given Python code by checking if it contains any
        `pydantic.Field` that is assigned as default value while not providing
        one of the arguments defined in `cls.REQUIRED_ARGS`.

        Args:
            code_tree (ast.Module): The tree of the Python code to be validated.

        Returns:
            list[int]: A list of line numbers where `pydantic.Field` is assigned
            as a default value without the required arguments.
        """
        lines = []

        for node in ast.walk(code_tree):
            if isinstance(node, ast.ClassDef):
                for body_item in node.body:
                    if (
                        isinstance(body_item, ast.AnnAssign)
                        and isinstance(body_item.value, ast.Call)
                        and isinstance(body_item.value.func, ast.Name)
                        and body_item.value.func.id == "Field"
                        and not cls.REQUIRED_ARGS.intersection(
                            kw.arg for kw in body_item.value.keywords
                        )
                    ):
                        lines.append(body_item.lineno)
        return sorted(lines)

    @classmethod
    def expose_validation(cls, invalid_files: list[str]):
        """
        Displays a message indicating that improper use of `pydantic.Field`
        as a default value should be refactored.

        Args:
            invalid_files (list[str]): A list of file paths that contain improper use of
            `pydantic.Field` as a default value.
        """
        if invalid_files:
            rptint(
                "Well done! You've managed to use [b]pydantic.Field[/b] in the most spectacularly wrong way possible! Required arguments? Who cares, right? "
                "Fix it before your code joins the Hall of Shame.\n"
            )
            args = ", ".join(f"[b]{arg}[/b]" for arg in cls.REQUIRED_ARGS)
            rptint(
                "Fix: Either pass [b]pydantic.Field[/b] to [b]typing.Annotated[/b] "
                f"or pass one of the following required arguments to [b]pydantic.Field[/b]: {args}."
            )

            super().expose_validation(invalid_files)


if __name__ == "__main__":
    NoFieldsAsDefaultValueWithoutRequiredArgs.validate_and_report_me(sys.argv[1:])
