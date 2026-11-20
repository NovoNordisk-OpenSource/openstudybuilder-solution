"""Reads explanations for the app's "type"-like enums out of their own source.

Every member of `InconsistencyType`, `ResolutionStrategy` and its neighbours already
carries a docstring explaining what it means — see `models/inconsistencies.py`. Python
does not expose those anywhere at runtime: `member.__doc__` falls back to the class
docstring (HANDOVER.md trap #7 notes the same gap for `openapi.json`). Re-typing the
same explanations into a second dict for this endpoint would be exactly the kind of
documentation drift this codebase has already been burned by; parsing them straight out
of the source instead leaves exactly one place to edit.
"""

import ast
import inspect
import textwrap
from enum import Enum
from functools import lru_cache

from standards_import.models.inconsistencies import (
    InconsistencyStatus,
    InconsistencyType,
    MatchTier,
    ResolutionStrategy,
    ReviewPass,
    RuleScope,
)
from standards_import.models.packages import EffectiveDateStatus
from standards_import.models.type_descriptions import EnumDescription

# Only enums with prose worth surfacing. EntityType (CODELIST/TERM) and ImportJobStatus
# (RUNNING/SUCCEEDED/FAILED) are left out on purpose: their members are self-explanatory
# and were never given docstrings, so including them would only ever produce nulls.
DESCRIBED_ENUMS: dict[str, type[Enum]] = {
    "inconsistency_type": InconsistencyType,
    "resolution_strategy": ResolutionStrategy,
    "match_tier": MatchTier,
    "inconsistency_status": InconsistencyStatus,
    "rule_scope": RuleScope,
    "effective_date_status": EffectiveDateStatus,
    "review_pass": ReviewPass,
}


@lru_cache
def _member_docs(enum_cls: type[Enum]) -> dict[str, str]:
    """The trailing string literal under each member's assignment, by member name.

    A member with no such literal is simply absent here. Cached because the enums this
    reads are fixed at import time — parsing and re-parsing the same source on every
    request would be pure waste.
    """

    source = textwrap.dedent(inspect.getsource(enum_cls))
    class_node = ast.parse(source).body[0]

    docs: dict[str, str] = {}
    pending_name: str | None = None
    for node in class_node.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            pending_name = node.targets[0].id
            continue
        if (
            pending_name is not None
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            docs[pending_name] = inspect.cleandoc(node.value.value)
        pending_name = None
    return docs


def describe(enum_cls: type[Enum]) -> EnumDescription:
    member_docs = _member_docs(enum_cls)
    return EnumDescription(
        description=enum_cls.__doc__,
        values={member.value: member_docs.get(member.name) for member in enum_cls},
    )


def get_type_descriptions() -> dict[str, EnumDescription]:
    return {key: describe(enum_cls) for key, enum_cls in DESCRIBED_ENUMS.items()}
