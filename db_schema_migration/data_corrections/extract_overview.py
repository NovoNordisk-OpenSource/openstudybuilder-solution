import importlib
import inspect
import sys


def extract_overview(module_name: str) -> str:
    imported_module = importlib.import_module(f"data_corrections.{module_name}")

    module_docstring = inspect.getdoc(imported_module)

    # find all functions defined in the module
    functions = inspect.getmembers(imported_module, inspect.isfunction)

    # create an overview of the module
    overview = f"## Data corrections: overview of {imported_module.__name__}\n\n"
    overview += f"{module_docstring}\n\n"

    idx = 1
    for func_name, func in functions:
        # only include functions defined in this module
        if func.__module__ != imported_module.__name__ or func_name == "main":
            print(
                f"Skipping imported function: {func_name} from module: {func.__module__}"
            )
            continue
        func_docstring = inspect.getdoc(func)
        if not func_docstring:
            print(f"Function {func_name} has no docstring, skipping.")
            continue
        # increase the heading level for function docstrings by one level
        if func_docstring:
            func_docstring = func_docstring.replace("## ", "### ")
        overview += f"\n\n## {idx}. Correction: {func_name}\n\n"
        overview += f"{func_docstring}\n"
        idx += 1

    return overview


if __name__ == "__main__":
    correction_module_name = sys.argv[1]
    correction_overview = extract_overview(correction_module_name)
    with open(
        f"data_corrections/{correction_module_name}_overview.md", "w", encoding="utf-8"
    ) as f:
        f.write(correction_overview)
