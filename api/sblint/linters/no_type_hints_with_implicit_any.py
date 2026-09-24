import ast
import sys

from rich import print as rptint

from sblint.sblinter import SBLinter


class NoTypeHintsWithImplicitAny(SBLinter):
    NO_IMPLICIT_ANY_TYPES = ["list", "dict", "set", "tuple"]

    @classmethod
    def validate(cls, code_tree: ast.Module, _file_path: str) -> list[int]:
        """
        Validates the given Python code by checking if it contains type hints with implicit Any.

        Args:
            code_tree (ast.Module): The tree of the Python code to be validated.

        Returns:
            list[int]: A list of line numbers of type hints with implicit Any.
        """

        def bin_op_check(node):
            return isinstance(node, ast.BinOp) and (
                (
                    isinstance(node.left, ast.Name)
                    and node.left.id in cls.NO_IMPLICIT_ANY_TYPES
                )
                or (
                    isinstance(node.right, ast.Name)
                    and node.right.id in cls.NO_IMPLICIT_ANY_TYPES
                )
            )

        lines = []

        for node in ast.walk(code_tree):
            if isinstance(node, ast.Subscript):
                if (
                    isinstance(node.value, ast.Name)
                    and node.value.id in cls.NO_IMPLICIT_ANY_TYPES
                    and isinstance(node.slice, ast.Name)
                    and node.slice.id in cls.NO_IMPLICIT_ANY_TYPES
                ):
                    lines.append(node.lineno)
            elif hasattr(node, "elts") and all(
                isinstance(elt, ast.Name) for elt in node.elts
            ):
                if any(elt.id in cls.NO_IMPLICIT_ANY_TYPES for elt in node.elts):
                    lines.append(node.lineno)
            elif hasattr(node, "annotation") and isinstance(node.annotation, ast.Name):
                if node.annotation.id in cls.NO_IMPLICIT_ANY_TYPES:
                    lines.append(node.lineno)
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if (
                    isinstance(node.returns, ast.Name)
                    and node.returns.id in cls.NO_IMPLICIT_ANY_TYPES
                ):
                    lines.append(node.lineno)
                if node.args and isinstance(node.args, ast.arguments):
                    for arg in node.args.args:
                        if (
                            isinstance(arg.annotation, ast.Name)
                            and arg.annotation.id in cls.NO_IMPLICIT_ANY_TYPES
                        ):
                            lines.append(arg.lineno)
                        if bin_op_check(arg.annotation):
                            lines.append(arg.lineno)
                    for posonlyarg in node.args.posonlyargs:
                        if (
                            isinstance(posonlyarg.annotation, ast.Name)
                            and posonlyarg.annotation.id in cls.NO_IMPLICIT_ANY_TYPES
                        ):
                            lines.append(posonlyarg.lineno)
                        if bin_op_check(posonlyarg.annotation):
                            lines.append(posonlyarg.lineno)
                    for kwonlyarg in node.args.kwonlyargs:
                        if (
                            isinstance(kwonlyarg.annotation, ast.Name)
                            and kwonlyarg.annotation.id in cls.NO_IMPLICIT_ANY_TYPES
                        ):
                            lines.append(kwonlyarg.lineno)
                        if bin_op_check(kwonlyarg.annotation):
                            lines.append(kwonlyarg.lineno)
                if bin_op_check(node.returns):
                    lines.append(node.lineno)

        return sorted(lines)

    @classmethod
    def expose_validation(cls, invalid_files: list[str]) -> None:
        """
        Displays a message indicating that type hints with implicit `typing.Any` should
        be updated to include either a specific type hint or an explicit `typing.Any`.

        Args:
            invalid_files (list[str]): A list of file paths that contain type hints with implicit Any.
        """
        if invalid_files:
            rptint(
                "Looks like these files are as clueless about type hints as you are. Fix them before they drag your reputation down further!\n"
            )
            rptint(
                "Fix: Type hints with implicit [b]typing.Any[/b] should be updated to include either a specific type hint or an explicit [b]typing.Any[/b]."
            )

            super().expose_validation(invalid_files)


if __name__ == "__main__":
    NoTypeHintsWithImplicitAny.validate_and_report_me(sys.argv[1:])
