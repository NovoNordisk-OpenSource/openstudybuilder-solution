# SBLint: Custom Static Code Analysis for Study Builder

SBLint is a powerful static code analysis tool tailored to enforce custom coding standards and identify potential issues in your codebase. It offers a suite of configurable validators to help maintain code quality and ensure long-term maintainability.

## Run the SBLint
To run SBLint and ensure your code adheres to the defined standards, use the following commands:

### Run All SBLinters
Execute all available SBLinters against `clinical_mdr_api`, `consumer_api` and `common`:
```sh
pipenv run sblint
```

Execute all available SBLinters against the specified directories:
```sh
python -m sblint.main dir1 dir2 ...
```

### Run a Specific SBLinter
Execute a specific linter against the specified directories:
```sh
python -m sblint.linters.no_relative_imports dir1 dir2 ...
```

## Create a New SBLinter
Follow these steps to create a new SBLinter:

1. **Create a New Python File in the `linters` dir** - Name the file according to the purpose of the linter (e.g. `no_relative_imports.py`).  
    ```python
    import ast
    import sys

    from sblinter import SBLinter


    # Your SBLinter must inherit sblinter.SBlinter
    class CustomLinter(SBLinter):
        @classmethod
        def validate(cls, tree: ast.Module) -> list[int]:
            # Implement validation logic for your SBLinter.

        @classmethod
        def expose_validation(cls, invalid_files: list[str]) -> None:
            if invalid_files:
                # Implement logic for exposing validation.

                # Always call the parent's `expose_validation` function to list all files that failed validation.
                super().expose_validation(invalid_files)


    # This makes sure that your SBLinter is also runnable independently, i.e. without main.py.
    if __name__ == "__main__":
        CustomLinter.validate_and_report_me(sys.argv[1:])
    ```
1. **Register the SBLinter** - Add your SBLinter to the `sblinter.get_sblinters` function to make it runnable as part of the `main.py`.