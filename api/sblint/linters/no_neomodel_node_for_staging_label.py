"""Detects neomodel node classes in `clinical_mdr_api` that claim a staging label.

The staging graph and the MDR graph share one Neo4j database, kept apart by the
`:CDISCStaging` marker label. A neomodel class labelled `RawPackage` (or any other
staging label) inside `clinical_mdr_api` would create, match and constrain nodes of that
label from the MDR side, without the marker, defeating the isolation the `mdr` role's
DENY relies on. Staging labels belong to `standards_import`, which talks to the staging
graph with the raw driver, never through neomodel.

A neomodel label is the class name unless `__label__` overrides it, so both are checked.
Base classes are resolved by name across all crawled files, because the neomodel base is
usually inherited indirectly (e.g. `Job` -> `ClinicalMdrNodeWithUID` -> `StructuredNode`).
"""

import ast
import sys
from pathlib import PurePath
from typing import ClassVar

from rich import print as rptint

from sblint.linters.no_staging_label_without_cdisc_staging_marker import (
    STAGING_LABELS,
)
from sblint.sblinter import SBLinter

NEOMODEL_NODE_BASES = frozenset({"StructuredNode", "AsyncStructuredNode"})
GUARDED_DIRECTORY = "clinical_mdr_api"


class NoNeomodelNodeForStagingLabel(SBLinter):
    # class name -> names of all its bases, merged across every crawled file
    bases_by_class_name: ClassVar[dict[str, set[str]]] = {}
    # (file_path, line, effective label, class name) of classes in the guarded directory
    candidates: ClassVar[list[tuple[str, int, str, str]]] = []

    @staticmethod
    def _base_name(base: ast.expr) -> str | None:
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            return base.attr
        return None

    @staticmethod
    def _label_override(class_def: ast.ClassDef) -> str | None:
        for statement in class_def.body:
            if (
                isinstance(statement, ast.Assign)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
                and any(
                    isinstance(target, ast.Name) and target.id == "__label__"
                    for target in statement.targets
                )
            ):
                return statement.value.value
        return None

    @classmethod
    def _is_neomodel_node(cls, class_name: str, visiting: frozenset[str]) -> bool:
        if class_name in NEOMODEL_NODE_BASES:
            return True
        if class_name in visiting:
            return False
        return any(
            cls._is_neomodel_node(base, visiting | {class_name})
            for base in cls.bases_by_class_name.get(class_name, ())
        )

    @classmethod
    def validate(cls, code_tree: ast.Module, file_path: str) -> list[int]:
        """Collects class definitions; verdicts are delivered by `postprocess_validation`
        because whether a class is a neomodel node depends on classes in other files.
        """

        guarded = GUARDED_DIRECTORY in PurePath(file_path).parts

        for node in ast.walk(code_tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = {
                name
                for base in node.bases
                if (name := cls._base_name(base)) is not None
            }
            cls.bases_by_class_name.setdefault(node.name, set()).update(bases)
            if guarded:
                label = cls._label_override(node) or node.name
                if label in STAGING_LABELS:
                    cls.candidates.append((file_path, node.lineno, label, node.name))

        return []

    @classmethod
    def postprocess_validation(cls) -> list[tuple[str, list[int]]] | None:
        lines_per_file: dict[str, list[int]] = {}
        for file_path, lineno, _label, class_name in cls.candidates:
            if cls._is_neomodel_node(class_name, frozenset()):
                lines_per_file.setdefault(file_path, []).append(lineno)
        return [(path, sorted(lines)) for path, lines in lines_per_file.items()]

    @classmethod
    def expose_validation(cls, invalid_files: list[str]) -> None:
        if invalid_files:
            rptint(
                "Bold move: you've given a neomodel [b]StructuredNode[/b] a staging label "
                "inside [b]clinical_mdr_api[/b]. Staging owns that label. The MDR side is "
                "not supposed to know it exists, let alone mint nodes for it through the "
                "ORM, minus the [b]:CDISCStaging[/b] marker, conveniently outside every "
                "RBAC filter. Isolation, but make it decorative.\n"
            )
            rptint(
                "Fix: pick a label that isn't in [b]STAGING_LABELS[/b] (rename the class or "
                "set [b]__label__[/b]). If you really need staging data, it lives in "
                "[b]standards_import[/b] and is reached with the raw driver, not neomodel."
            )
            super().expose_validation(invalid_files)


if __name__ == "__main__":
    NoNeomodelNodeForStagingLabel.validate_and_report_me(sys.argv[1:])
