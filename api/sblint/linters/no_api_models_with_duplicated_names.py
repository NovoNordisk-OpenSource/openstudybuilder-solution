import ast
import builtins
import sys

from rich import print as rptint

from sblint.sblinter import SBLinter

BUILTINS = dir(builtins)
BUILTINS.extend(["Enum", "ABC", "TestCase"])


class ClassDef:
    def __init__(self, name: str, lineno: int, bases: list[str], file_path: str):
        self.name = name
        self.lineno = lineno
        self.bases = bases
        self.file_path = file_path
        self.inherits_from_base_model: bool | None = None


class Imported:
    def __init__(self, name: str, module: str):
        self.name = name
        self.module = module


class NoDuplicatedApiModelNames(SBLinter):

    all_class_defs: dict[str, dict[str, ClassDef]] = {}
    all_imports: dict[str, dict[str, Imported]] = {}

    visited_model_names: dict[str, dict[str, list[tuple[str, int]]]] = {}

    @classmethod
    def _get_api_name(cls, file_path: str) -> str:
        if file_path.startswith("consumer_api"):
            version = file_path.split("/")[1]
            return f"consumer_api/{version}"
        if "/" in file_path:
            return file_path.split("/")[0]
        return "other"

    @classmethod
    def _append_model_name(cls, file_path: str, model_name: str, lineno: int) -> None:
        api = cls._get_api_name(file_path)
        cls.visited_model_names.setdefault(api, {}).setdefault(model_name, []).append(
            (file_path, lineno)
        )

    @classmethod
    def _check_class_name(cls, file_path, class_name: str, lineno: int) -> bool:
        result = False
        api = cls._get_api_name(file_path)
        if class_name in cls.visited_model_names.get(api, {}):
            result = True
        cls._append_model_name(file_path, class_name, lineno)
        return result

    @classmethod
    def _find_class_def_by_name_and_path(
        cls, name: str, module: str
    ) -> ClassDef | None:
        """Finds a class definition by its name across all files."""
        # first try to find it using the module
        file_path = f"{module.replace('.', '/')}.py"
        if file_path in cls.all_class_defs:
            if name in cls.all_class_defs[file_path]:
                return cls.all_class_defs[file_path][name]
        for file_class_defs in cls.all_class_defs.values():
            if name in file_class_defs:
                return file_class_defs[name]
        return None

    @classmethod
    def _check_class_inherits_base_model(cls, name: str, file_path: str) -> bool:
        """Checks if the given class name inherits from BaseModel either directly or indirectly."""

        if name == "BaseModel":
            return True
        local_class_def = cls.all_class_defs.get(file_path, {}).get(name)
        if local_class_def is not None:
            # already checked?
            if local_class_def.inherits_from_base_model is not None:
                return local_class_def.inherits_from_base_model
            for base_class_name in local_class_def.bases:
                if cls._check_class_inherits_base_model(base_class_name, file_path):
                    local_class_def.inherits_from_base_model = True
                    return True
            # all bases checked, none inherits from BaseModel
            local_class_def.inherits_from_base_model = False
            return False

        # we need to check imports
        local_imported = cls.all_imports.get(file_path, {}).get(name)
        if local_imported is not None:
            imported_module = local_imported.module
            imported_name = local_imported.name
            # try to find the class def among all definitions
            imported_class_def = cls._find_class_def_by_name_and_path(
                imported_name, imported_module
            )
            if imported_class_def is not None:
                if cls._check_class_inherits_base_model(
                    imported_class_def.name, imported_class_def.file_path
                ):
                    imported_class_def.inherits_from_base_model = True
                    return True
        return False

    @classmethod
    def validate(cls, code_tree: ast.Module, file_path: str) -> list[int]:
        """
        Validates the given Python code by checking if it contains any
        classes inheriting from `BaseModel` that have already been seen
        with the same name anywhere within the same API.

        Duplicated names are problematic as the generated OpenAPI schema
        will only include one of the models, leading to confusing or conflicting
        information in tools such as the Swagger UI.

        This validator performs a two-pass approach. The validation first
        collects all class definitions and their inheritance relationships.
        This is performed by the `validate` method.
        In the second pass, performed by the `postprocess_validation` method,
        it checks each class to see if it inherits from `BaseModel` (directly
        or indirectly) and if its name has already been used for another
        class inheriting from `BaseModel`. If both conditions are met, the
        line number of the class definition is recorded as a violation.

        Args:
            code_tree (ast.Module): The tree of the Python code to be validated.

        Returns:
            list[int]: An empty list. This validator returns the results in the
            `postprocess_validation` step.
        """

        class_defs: dict[str, ClassDef] = {}
        all_imports: dict[str, Imported] = {}

        for node in ast.walk(code_tree):
            # Pass 1: Find all class definitions that inherit from some superclass
            # skipping those that do not have any bases or whose bases are builtins
            if isinstance(node, ast.ClassDef):
                parent_names: list[str] = []
                if node.bases:
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id not in BUILTINS:
                            parent_names.append(base.id)
                if parent_names:
                    class_defs[node.name] = ClassDef(
                        node.name, node.lineno, parent_names, file_path
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module if node.module else ""
                alias = node.names[0]
                all_imports[alias.name] = Imported(alias.name, module)

        # store imports that are used as parent class of any collected class def
        for name, imported in all_imports.items():
            if any(name in class_def.bases for class_def in class_defs.values()):
                cls.all_imports.setdefault(file_path, {})[name] = imported

        cls.all_class_defs.setdefault(file_path, {}).update(class_defs)

        return []

    @classmethod
    def postprocess_validation(cls) -> list[tuple[str, list[int]]] | None:
        """
        Post-processes the validation results to identify files with duplicated
        request/response model class names.

        Returns:
            list[tuple[str, list[int]]] | None: A list of tuples containing file names
            and their corresponding line numbers with duplicated request/response model class names.
        """
        class_defs_to_check = []

        # Step 1: find all classes that inherit directly from BaseModel
        for file_path, file_class_defs in cls.all_class_defs.items():
            for class_def in file_class_defs.values():
                if cls._check_class_inherits_base_model(class_def.name, file_path):
                    class_defs_to_check.append(class_def)

        results = []
        results_per_file: dict[str, list[int]] = {}
        # Step 3: check for duplicated class names among those that inherit from BaseModel
        for class_def in class_defs_to_check:
            if cls._check_class_name(
                class_def.file_path, class_def.name, class_def.lineno
            ):
                results_per_file.setdefault(class_def.file_path, []).append(
                    class_def.lineno
                )

        for file_path, line_numbers in results_per_file.items():
            results.append((file_path, sorted(line_numbers)))

        return results

    @classmethod
    def expose_validation(cls, invalid_files: list[str]) -> None:
        """
        Displays a message indicating that duplicated class names were found.

        Args:
            invalid_files (list[str]): A list of file paths that contain duplicated class names.
        """
        if invalid_files:
            rptint(
                "Apparently you loved that request/response model class name so much you decided it should be used more than once. "
                "How cute, now enjoy the ensuing confusion and chaos.\n"
            )

            rptint(
                "Fix: Rename the duplicated request/response model classes in the following files:"
            )
            for api, findings in cls.visited_model_names.items():
                for model_name, occurrences in findings.items():
                    if len(occurrences) > 1:
                        rptint(
                            f":-1: [blue]Duplicated model name [red][b]{model_name}[/b][/red] found in the following locations of {api}[/blue]:"
                        )
                        for file_path, lineno in occurrences:
                            rptint(f" - {file_path}, line {lineno}")


if __name__ == "__main__":
    NoDuplicatedApiModelNames.validate_and_report_me(sys.argv[1:])
