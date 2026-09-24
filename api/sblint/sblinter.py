import ast
import os
import sys
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable, final

from rich import console
from rich import print as rptint


class SBLinter(ABC):
    """
    Abstract base class for validators.
    """

    @classmethod
    @final
    def get_sblinters(cls) -> list[type["SBLinter"]]:
        """
        Returns a list of SBLinter classes to be used for static code analysis.

        The returned linters are responsible for enforcing specific coding standards
        and detecting potential issues in the codebase. Each linter class implements
        its own set of rules and checks.
        """
        from sblint.linters.no_api_models_with_duplicated_names import (
            NoDuplicatedApiModelNames,
        )
        from sblint.linters.no_fields_as_default_value_without_required_args import (
            NoFieldsAsDefaultValueWithoutRequiredArgs,
        )
        from sblint.linters.no_fields_in_annotated_with_disallowed_args import (
            NoFieldsInAnnotatedWithDisallowedArgs,
        )
        from sblint.linters.no_fields_with_disallowed_args import (
            NoFieldsWithDisallowedArgs,
        )
        from sblint.linters.no_fields_with_empty_string_args import (
            NoFieldsWithEmptyStringArgs,
        )
        from sblint.linters.no_http_methods_with_disallowed_status_code import (
            NoHTTPMethodsWithDisallowedStatusCode,
        )
        from sblint.linters.no_relative_imports import NoRelativeImports
        from sblint.linters.no_type_hints_with_implicit_any import (
            NoTypeHintsWithImplicitAny,
        )
        from sblint.linters.no_unnecessary_imports import NoUnnecessaryImports

        return [
            NoFieldsAsDefaultValueWithoutRequiredArgs,
            NoFieldsInAnnotatedWithDisallowedArgs,
            NoFieldsWithDisallowedArgs,
            NoFieldsWithEmptyStringArgs,
            NoTypeHintsWithImplicitAny,
            NoHTTPMethodsWithDisallowedStatusCode,
            NoRelativeImports,
            NoUnnecessaryImports,
            NoDuplicatedApiModelNames,
        ]

    @classmethod
    @abstractmethod
    def validate(cls, code_tree: ast.Module, _file_path: str) -> list[int]:
        """
        Validates the given Python code.

        This abstract method must be implemented by subclasses to define the validation logic for the provided code.

        Args:
            code_tree (ast.Module): The tree of the Python code to be validated.

        Returns:
            list[int]: A list of line numbers where validation issues were found.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @classmethod
    def postprocess_validation(cls) -> list[tuple[str, list[int]]] | None:
        """
        Optional post-processing step after validation.

        This allows validators to perform additional checks that span multiple files
        or require aggregation of results after the initial validation phase.

        This method can be overridden by subclasses to perform any additional
        processing or reporting after the validation has been completed.
        Returns:
            list[tuple[str, list[int]]] | None: A list of tuples containing file names
            and their corresponding line numbers with issues, or None if no post-processing is needed.
        """

    @classmethod
    def expose_validation(cls, invalid_files: list[str]) -> None:
        """
        Displays a list of invalid files in a formatted manner.

        This method prints each invalid file name in a dark cyan color to the terminal for better visibility.
        It is intended to be used for exposing validation results to the user.

        Args:
            invalid_files (list[str]): A list of file names that failed validation.
        """
        print("\n")
        for invalid_file in invalid_files:
            rptint(f":-1: [b][blue]{invalid_file}[/blue][b]")
        print("\n")

    @classmethod
    @final
    def code_crawler(
        cls,
        directories: list[str],
        validators: list[Callable[[ast.Module, str], list[int]]],
        extension: str = ".py",
    ) -> dict[str, list]:
        """
        Crawls through the specified directories to validate Python files using the provided validators.

        Args:
            directories (list[str]): A list of directory paths to search for Python files.
            validators (list[Callable[[str], bool]]): A list of validation functions.
            Each function takes the content of a Python file as input and returns a boolean indicating whether the file passes its validation.
            extension (str): The file extension to filter files. Defaults to `.py`.

        Returns:
            dict[str, list]: A dictionary where the keys are the validator functions (as strings) and the values are sets of file paths that failed the corresponding validation.
        """
        invalid_files: dict[str, list] = defaultdict(list)

        for directory in directories:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith(extension):
                        file_path = os.path.join(root, file)
                        with open(file_path, "r", encoding="utf-8") as f:
                            if content := f.read():
                                tree = ast.parse(content)
                                for validate in validators:
                                    if lines := validate(tree, file_path):
                                        for line in lines:
                                            invalid_files[validate.__qualname__].append(
                                                f"{file_path}:{line}"
                                            )

        return invalid_files

    @classmethod
    @final
    def validate_and_report(
        cls, directories_to_crawl: list[str], validators: list[type["SBLinter"]]
    ):
        """
        Validates the specified directories using the provided validators and reports any issues.

        Args:
            directories_to_crawl (list[str]): A list of directory paths to be validated.
            validators (list[SBLinter]): A list of SBLinter validator instances that implement the `validate` and `expose_validation` methods.

        Raises:
            SystemExit: Exits with status code 1 if no directories are provided or if validation fails.

        Behavior:
            - If no directories are provided, prints usage instruction and exits.
            - Crawls the specified directories and applies the `validate` method of each validator.
            - Reports validation issues for each validator using the `expose_validation` method.
        """
        if not directories_to_crawl:
            print(f"Usage: {sys.argv[0]} <directory1> <directory2> ...")
            sys.exit(1)

        failed_validators = cls.code_crawler(
            directories_to_crawl, [validator.validate for validator in validators]
        )

        # Post-process validations
        for validator in validators:
            if postprocess := validator.postprocess_validation():
                for file_name, line_numbers in postprocess:
                    for line in line_numbers:
                        failed_validators[validator.validate.__qualname__].append(
                            f"{file_name}:{line}"
                        )

        if failed_validators:
            terminal = console.Console()
            terminal.rule("[b]SBLint Failed[/b]", characters="=", style="bold")
            rptint("[b][red]SBLint detected issues in the following areas:[/red][/b]\n")
            for validator in validators:
                if validator.validate.__qualname__ in failed_validators:
                    rptint(f"[b][red]- {validator.__name__}[/red][/b]")
            print("\n")

            for validator in validators:
                if invalid_files := failed_validators.get(
                    validator.validate.__qualname__
                ):
                    terminal.rule(
                        f"[b][red]{validator.__name__}[/red][/b]",
                        characters="-",
                        style="bold red",
                    )
                    validator.expose_validation(invalid_files)

            sys.exit(1)

        rptint(
            "[b][green]You got away this time... but remember, SBLint never sleeps. "
            "I'll be lurking, waiting for your next mistake![/green][/b]"
        )

    @classmethod
    @final
    def validate_and_report_me(cls, directories_to_crawl: list[str]):
        cls.validate_and_report(directories_to_crawl, [cls])
