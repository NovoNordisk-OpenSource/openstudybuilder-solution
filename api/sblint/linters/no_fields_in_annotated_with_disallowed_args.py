import ast
import sys

from rich import print as rptint

from sblint.sblinter import SBLinter


class NoFieldsInAnnotatedWithDisallowedArgs(SBLinter):
    DISALLOWED_ARGS = {"alias", "default", "default_factory"}

    @classmethod
    def validate(cls, code_tree: ast.Module, _file_path: str) -> list[int]:
        """
        Validates the given Python code by checking if it contains any
        `pydantic.Field` that is passed to `typing.Annotated` while also
        providing one of the arguments defined in `cls.DISALLOWED_ARGS`.

        Args:
            code_tree (ast.Module): The tree of the Python code to be validated.

        Returns:
            list[int]: A list of line numbers where `pydantic.Field` is passed to
            `typing.Annotated` with disallowed arguments.
        """
        lines = []

        for node in ast.walk(code_tree):
            if isinstance(node, ast.ClassDef):
                for body_item in node.body:
                    if (
                        isinstance(body_item, ast.AnnAssign)
                        and isinstance(body_item.annotation, ast.Subscript)
                        and isinstance(body_item.annotation.slice, ast.Tuple)
                    ):
                        for elts in body_item.annotation.slice.elts:
                            if (
                                isinstance(elts, ast.Call)
                                and isinstance(elts.func, ast.Name)
                                and elts.func.id == "Field"
                                and cls.DISALLOWED_ARGS.intersection(
                                    kw.arg for kw in elts.keywords
                                )
                            ):
                                lines.append(elts.lineno)
        return sorted(lines)

    @classmethod
    def expose_validation(cls, invalid_files: list[str]) -> None:
        """
        Displays a message indicating that improper use of `pydantic.Field`
        within `typing.Annotated` should be refactored.

        Args:
            invalid_files (list[str]): A list of file paths that contain improper use of
            `pydantic.Field` within `typing.Annotated`.
        """
        if invalid_files:

            rptint(
                "Impressive work! You've achieved the rare feat of turning [b]pydantic.Field[/b] in [b]typing.Annotated[/b] into a masterpiece of poor design choices."
                "This level of disregard for coding standards is almost an art form.\n"
            )

            args = ", ".join(f"[b]{arg}[/b]" for arg in cls.DISALLOWED_ARGS)
            rptint(
                "Fix: Either assign [b]pydantic.Field[/b] as the default value "
                f"or remove all of the following disallowed arguments from [b]pydantic.Field[/b]: {args}."
            )

            super().expose_validation(invalid_files)


if __name__ == "__main__":
    NoFieldsInAnnotatedWithDisallowedArgs.validate_and_report_me(sys.argv[1:])
