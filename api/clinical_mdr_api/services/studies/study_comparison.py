from collections.abc import Callable
from dataclasses import dataclass
from fnmatch import fnmatchcase
from typing import Any

from pydantic import BaseModel

from clinical_mdr_api.models.study_selections.study_comparison import (
    StudyComparison,
    StudyComparisonChangeType,
    StudyComparisonFieldChange,
    StudyComparisonItemChange,
    StudyComparisonSection,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_activity_group import (
    StudyActivityGroupService,
)
from clinical_mdr_api.services.studies.study_activity_instance_selection import (
    StudyActivityInstanceSelectionService,
)
from clinical_mdr_api.services.studies.study_activity_instruction import (
    StudyActivityInstructionService,
)
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_activity_subgroup import (
    StudyActivitySubGroupService,
)
from clinical_mdr_api.services.studies.study_arm_selection import (
    StudyArmSelectionService,
)
from clinical_mdr_api.services.studies.study_branch_arm_selection import (
    StudyBranchArmSelectionService,
)
from clinical_mdr_api.services.studies.study_cohort_selection import (
    StudyCohortSelectionService,
)
from clinical_mdr_api.services.studies.study_compound_dosing_selection import (
    StudyCompoundDosingSelectionService,
)
from clinical_mdr_api.services.studies.study_compound_selection import (
    StudyCompoundSelectionService,
)
from clinical_mdr_api.services.studies.study_criteria_selection import (
    StudyCriteriaSelectionService,
)
from clinical_mdr_api.services.studies.study_data_supplier import (
    StudyDataSupplierSelectionService,
)
from clinical_mdr_api.services.studies.study_design_cell import StudyDesignCellService
from clinical_mdr_api.services.studies.study_design_class import (
    StudyDesignClassService,
)
from clinical_mdr_api.services.studies.study_disease_milestone import (
    StudyDiseaseMilestoneService,
)
from clinical_mdr_api.services.studies.study_element_selection import (
    StudyElementSelectionService,
)
from clinical_mdr_api.services.studies.study_endpoint_selection import (
    StudyEndpointSelectionService,
)
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.services.studies.study_objective_selection import (
    StudyObjectiveSelectionService,
)
from clinical_mdr_api.services.studies.study_soa_footnote import (
    StudySoAFootnoteService,
)
from clinical_mdr_api.services.studies.study_soa_group import StudySoAGroupService
from clinical_mdr_api.services.studies.study_source_variable import (
    StudySourceVariableService,
)
from clinical_mdr_api.services.studies.study_standard_version_selection import (
    StudyStandardVersionService,
)
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from common.exceptions import NotFoundException

# Audit/bookkeeping properties that change with every edit and carry no
# information about the study content itself.
IGNORED_FIELDS = frozenset(
    {
        "start_date",
        "end_date",
        "change_type",
        "author_username",
        "author_id",
        "possible_actions",
        "study_version",
        "study_value_version",
    }
)

LABEL_FIELDS = (
    "name",
    "visit_name",
    "epoch_name",
    "short_name",
    "acronym",
    "text",
    "activity.name",
    "activity_instance.name",
    "compound.name",
    "objective.name",
    "endpoint.name",
    "criteria.name",
    "study_activity_name",
    "footnote.name",
)


@dataclass(frozen=True)
class _Section:
    name: str
    title: str
    key_fields: tuple[str, ...]
    loader: Callable[[str, str | None], list[Any]]


def _items_of(result: Any) -> list[Any]:
    if result is None:
        return []
    if hasattr(result, "items") and not isinstance(result, dict):
        return list(result.items)
    if isinstance(result, list):
        return result
    return [result]


def _list_loader(
    call: Callable[[str, str | None], Any],
) -> Callable[[str, str | None], list[Any]]:
    def load(study_uid: str, version: str | None) -> list[Any]:
        try:
            return _items_of(call(study_uid, version))
        except NotFoundException:
            # A study version may legitimately lack a component altogether
            return []

    return load


def _load_soa_splits(study_uid: str, version: str | None) -> list[Any]:
    # StudyService.get_study_soa_splits refuses locked studies, which is
    # exactly what historical versions usually are
    node = MetaRepository().study_definition_repository.get_soa_split_uids(
        study_uid=study_uid, study_value_version=version
    )
    return (
        []
        if node is None
        else StudyService._study_array_field_to_study_soa_splits(study_uid, node)
    )


SECTIONS: tuple[_Section, ...] = (
    _Section(
        "study",
        "Study definition",
        ("uid",),
        _list_loader(
            lambda uid, v: StudyService().get_by_uid(uid, study_value_version=v)
        ),
    ),
    _Section(
        "standard_versions",
        "Standard versions",
        ("uid",),
        _list_loader(
            lambda uid, v: StudyStandardVersionService().get_standard_versions_in_study(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "design_class",
        "Study design class",
        ("study_uid",),
        _list_loader(
            lambda uid, v: StudyDesignClassService().get_study_design_class(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "source_variable",
        "Study source variable",
        ("study_uid",),
        _list_loader(
            lambda uid, v: StudySourceVariableService().get_study_source_variable(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "arms",
        "Study arms",
        ("arm_uid",),
        _list_loader(
            lambda uid, v: StudyArmSelectionService().get_all_selection(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "branch_arms",
        "Study branch arms",
        ("branch_arm_uid",),
        _list_loader(
            lambda uid, v: StudyBranchArmSelectionService().get_all_selection(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "cohorts",
        "Study cohorts",
        ("cohort_uid",),
        _list_loader(
            lambda uid, v: StudyCohortSelectionService().get_all_selection(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "epochs",
        "Study epochs",
        ("uid",),
        _list_loader(
            lambda uid, v: StudyEpochService.get_all_epochs(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "elements",
        "Study elements",
        ("element_uid",),
        _list_loader(
            lambda uid, v: StudyElementSelectionService().get_all_selection(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "design_cells",
        "Study design cells",
        ("design_cell_uid",),
        _list_loader(
            lambda uid, v: StudyDesignCellService().get_all_design_cells(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "disease_milestones",
        "Disease milestones",
        ("uid",),
        _list_loader(
            lambda uid, v: StudyDiseaseMilestoneService().get_all_disease_milestones(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "visits",
        "Study visits",
        ("uid",),
        _list_loader(
            lambda uid, v: StudyVisitService.get_all_visits(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "objectives",
        "Study objectives",
        ("study_objective_uid",),
        _list_loader(
            lambda uid, v: StudyObjectiveSelectionService().get_all_selection(
                study_uid=uid, no_brackets=False, study_value_version=v
            )
        ),
    ),
    _Section(
        "endpoints",
        "Study endpoints",
        ("study_endpoint_uid",),
        _list_loader(
            lambda uid, v: StudyEndpointSelectionService().get_all_selection(
                study_uid=uid, no_brackets=False, study_value_version=v
            )
        ),
    ),
    _Section(
        "criteria",
        "Study criteria",
        ("study_criteria_uid",),
        _list_loader(
            lambda uid, v: StudyCriteriaSelectionService().get_all_selection(
                study_uid=uid, no_brackets=False, study_value_version=v
            )
        ),
    ),
    _Section(
        "compounds",
        "Study compounds",
        ("study_compound_uid",),
        _list_loader(
            lambda uid, v: StudyCompoundSelectionService().get_all_selection(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "compound_dosings",
        "Study compound dosings",
        ("study_compound_dosing_uid",),
        _list_loader(
            lambda uid, v: StudyCompoundDosingSelectionService().get_all_compound_dosings(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "soa_groups",
        "SoA groups",
        ("study_soa_group_uid",),
        _list_loader(
            lambda uid, v: StudySoAGroupService().get_all_selection(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "activity_groups",
        "Study activity groups",
        ("study_activity_group_uid",),
        _list_loader(
            lambda uid, v: StudyActivityGroupService().get_all_selection(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "activity_subgroups",
        "Study activity subgroups",
        ("study_activity_subgroup_uid",),
        _list_loader(
            lambda uid, v: StudyActivitySubGroupService().get_all_selection(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "activities",
        "Study activities",
        ("study_activity_uid",),
        _list_loader(
            lambda uid, v: StudyActivitySelectionService().get_all_selection(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "activity_instances",
        "Study activity instances",
        ("study_activity_instance_uid",),
        _list_loader(
            lambda uid, v: StudyActivityInstanceSelectionService().get_all_selection(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "activity_schedules",
        "Study activity schedules",
        ("study_activity_schedule_uid",),
        _list_loader(
            lambda uid, v: StudyActivityScheduleService().get_all_schedules(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "activity_instructions",
        "Study activity instructions",
        ("study_activity_instruction_uid",),
        _list_loader(
            lambda uid, v: StudyActivityInstructionService().get_all_instructions(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "soa_footnotes",
        "SoA footnotes",
        ("uid",),
        _list_loader(
            lambda uid, v: StudySoAFootnoteService().get_all_by_study_uid(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "data_suppliers",
        "Study data suppliers",
        ("study_data_supplier_uid",),
        _list_loader(
            lambda uid, v: StudyDataSupplierSelectionService().get_all_selections(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "preferred_time_unit",
        "Preferred time unit",
        ("study_uid",),
        _list_loader(
            lambda uid, v: StudyService().get_study_preferred_time_unit(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "protocol_soa_preferred_time_unit",
        "Preferred time unit (protocol SoA)",
        ("study_uid",),
        _list_loader(
            lambda uid, v: StudyService().get_study_preferred_time_unit(
                study_uid=uid, for_protocol_soa=True, study_value_version=v
            )
        ),
    ),
    _Section(
        "soa_preferences",
        "SoA preferences",
        ("study_uid",),
        _list_loader(
            lambda uid, v: StudyService().get_study_soa_preferences(
                study_uid=uid, study_value_version=v
            )
        ),
    ),
    _Section(
        "soa_splits",
        "SoA splits",
        ("uid",),
        _list_loader(_load_soa_splits),
    ),
)


def _lookup(data: dict[str, Any], dotted: str) -> Any:
    current: Any = data
    for part in dotted.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def to_plain(item: Any) -> dict[str, Any]:
    if isinstance(item, BaseModel):
        return item.model_dump(mode="json")
    return dict(item)


def flatten(value: Any, path: str = "", out: dict[str, Any] | None = None):
    """Flattens nested dicts/lists to {dotted.path: scalar} so that changes are
    reported on the innermost field that differs.
    Lists of objects are keyed by their `uid` when every element has one."""
    out = {} if out is None else out
    if isinstance(value, dict):
        for key, sub in value.items():
            if key in IGNORED_FIELDS:
                continue
            flatten(sub, f"{path}.{key}" if path else key, out)
        if not value and path:
            out[path] = value
    elif isinstance(value, list) and value and all(isinstance(v, dict) for v in value):
        uids = [v.get("uid") for v in value]
        use_uids = all(uids) and len(set(uids)) == len(uids)
        for index, sub in enumerate(value):
            flatten(sub, f"{path}[{uids[index] if use_uids else index}]", out)
    else:
        out[path] = value
    return out


def _item_key(item: dict[str, Any], key_fields: tuple[str, ...]) -> str | None:
    for field in key_fields:
        value = _lookup(item, field)
        if value is not None:
            return str(value)
    return None


def _item_label(item: dict[str, Any]) -> str | None:
    for field in LABEL_FIELDS:
        value = _lookup(item, field)
        if isinstance(value, str) and value:
            return value
    return None


def _index_items(
    items: list[Any], key_fields: tuple[str, ...]
) -> dict[str, dict[Any, Any]]:
    indexed: dict[str, dict[Any, Any]] = {}
    for position, item in enumerate(items):
        plain = to_plain(item)
        key = _item_key(plain, key_fields) or f"#{position}"
        # Guard against several rows sharing one identity (e.g. split cohorts)
        suffix, unique_key = 1, key
        while unique_key in indexed:
            suffix += 1
            unique_key = f"{key}#{suffix}"
        indexed[unique_key] = plain
    return indexed


def is_ignored(field: str, ignore_fields: tuple[str, ...]) -> bool:
    """Patterns (wildcards allowed) match the full dotted path or its last segment."""
    last = field.rsplit(".", 1)[-1]
    return any(
        fnmatchcase(field, pattern) or fnmatchcase(last, pattern)
        for pattern in ignore_fields
    )


def _is_identifier(field: str) -> bool:
    last = field.rsplit(".", 1)[-1]
    return last == "uid" or last.endswith(("_uid", "_uids"))


def _signature(
    data: dict[str, Any], ignore_fields: tuple[str, ...]
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (field, repr(value))
            for field, value in flatten(data).items()
            if value is not None
            and not _is_identifier(field)
            and not is_ignored(field, ignore_fields)
        )
    )


def _pair_recreated(
    result: list[StudyComparisonItemChange],
    old: dict[str, dict[str, Any]],
    new: dict[str, dict[str, Any]],
    include_unchanged: bool,
    ignore_fields: tuple[str, ...],
) -> list[StudyComparisonItemChange]:
    """Turn a REMOVED and an ADDED item with equal values (apart from uids) into one RECREATED item."""
    removed: dict[tuple, list[StudyComparisonItemChange]] = {}
    for item in result:
        if item.change_type == StudyComparisonChangeType.REMOVED:
            signature = _signature(old[item.key], ignore_fields)
            if signature:
                removed.setdefault(signature, []).append(item)
    paired: list[StudyComparisonItemChange] = []
    replaced: set[int] = set()
    for item in result:
        if item.change_type != StudyComparisonChangeType.ADDED:
            continue
        candidates = removed.get(_signature(new[item.key], ignore_fields))
        if not candidates:
            continue
        gone = candidates.pop(0)
        replaced.update((id(gone), id(item)))
        paired.append(
            StudyComparisonItemChange(
                key=f"{gone.key} -> {item.key}",
                label=item.label or gone.label,
                change_type=StudyComparisonChangeType.RECREATED,
                changes=diff_fields(
                    old[gone.key], new[item.key], include_unchanged, ignore_fields
                ),
            )
        )
    return [item for item in result if id(item) not in replaced] + paired


def diff_fields(
    old: dict[str, Any],
    new: dict[str, Any],
    include_unchanged: bool = False,
    ignore_fields: tuple[str, ...] = (),
) -> list[StudyComparisonFieldChange]:
    flat_old, flat_new = flatten(old), flatten(new)
    if ignore_fields:
        flat_old = {
            k: v for k, v in flat_old.items() if not is_ignored(k, ignore_fields)
        }
        flat_new = {
            k: v for k, v in flat_new.items() if not is_ignored(k, ignore_fields)
        }
    result = []
    for field in sorted(flat_old.keys() | flat_new.keys()):
        old_value, new_value = flat_old.get(field), flat_new.get(field)
        changed = old_value != new_value
        if changed or (include_unchanged and new_value is not None):
            result.append(
                StudyComparisonFieldChange(
                    field=field,
                    old_value=old_value,
                    new_value=new_value,
                    changed=changed,
                )
            )
    return result


def diff_indexed(
    old: dict[str, dict[str, Any]],
    new: dict[str, dict[str, Any]],
    include_unchanged: bool = False,
    ignore_fields: tuple[str, ...] = (),
) -> list[StudyComparisonItemChange]:
    result: list[StudyComparisonItemChange] = []
    for key in old.keys() | new.keys():
        if key not in new:
            result.append(
                StudyComparisonItemChange(
                    key=key,
                    label=_item_label(old[key]),
                    change_type=StudyComparisonChangeType.REMOVED,
                    changes=diff_fields(old[key], {}, ignore_fields=ignore_fields),
                )
            )
        elif key not in old:
            result.append(
                StudyComparisonItemChange(
                    key=key,
                    label=_item_label(new[key]),
                    change_type=StudyComparisonChangeType.ADDED,
                    changes=diff_fields({}, new[key], ignore_fields=ignore_fields),
                )
            )
        else:
            changes = diff_fields(old[key], new[key], include_unchanged, ignore_fields)
            modified = any(change.changed for change in changes)
            if modified or include_unchanged:
                result.append(
                    StudyComparisonItemChange(
                        key=key,
                        label=_item_label(new[key]) or _item_label(old[key]),
                        change_type=(
                            StudyComparisonChangeType.MODIFIED
                            if modified
                            else StudyComparisonChangeType.UNCHANGED
                        ),
                        changes=changes,
                    )
                )
    result = _pair_recreated(result, old, new, include_unchanged, ignore_fields)
    return sorted(result, key=lambda c: (c.label or "", c.key))


def diff_items(
    items_a: list[Any],
    items_b: list[Any],
    key_fields: tuple[str, ...],
    include_unchanged: bool = False,
    ignore_fields: tuple[str, ...] = (),
) -> list[StudyComparisonItemChange]:
    return diff_indexed(
        _index_items(items_a, key_fields),
        _index_items(items_b, key_fields),
        include_unchanged,
        ignore_fields,
    )


# (source section, relation, target section, path of the referenced uid(s))
RELATIONSHIPS: tuple[tuple[str, str, str, str], ...] = (
    ("branch_arms", "belongs to arm", "arms", "arm_root.arm_uid"),
    ("cohorts", "includes arm", "arms", "arm_roots.arm_uid"),
    (
        "cohorts",
        "includes branch arm",
        "branch_arms",
        "branch_arm_roots.branch_arm_uid",
    ),
    ("design_cells", "in arm", "arms", "study_arm_uid"),
    ("design_cells", "in branch arm", "branch_arms", "study_branch_arm_uid"),
    ("design_cells", "in epoch", "epochs", "study_epoch_uid"),
    ("design_cells", "in element", "elements", "study_element_uid"),
    ("visits", "in epoch", "epochs", "study_epoch_uid"),
    (
        "activities",
        "in activity subgroup",
        "activity_subgroups",
        "study_activity_subgroup.study_activity_subgroup_uid",
    ),
    (
        "activities",
        "in activity group",
        "activity_groups",
        "study_activity_group.study_activity_group_uid",
    ),
    ("activities", "in SoA group", "soa_groups", "study_soa_group.study_soa_group_uid"),
    ("activity_instances", "instance of activity", "activities", "study_activity_uid"),
    ("activity_schedules", "scheduled activity", "activities", "study_activity_uid"),
    (
        "activity_schedules",
        "scheduled activity instance",
        "activity_instances",
        "study_activity_instance_uid",
    ),
    ("activity_schedules", "scheduled at visit", "visits", "study_visit_uid"),
    ("activity_instructions", "instructs activity", "activities", "study_activity_uid"),
    (
        "activity_subgroups",
        "in activity group",
        "activity_groups",
        "study_activity_group_uid",
    ),
    ("activity_subgroups", "contains activity", "activities", "study_activity_uids"),
    ("activity_groups", "in SoA group", "soa_groups", "study_soa_group_uid"),
    (
        "activity_groups",
        "contains activity subgroup",
        "activity_subgroups",
        "study_activity_subgroup_uids",
    ),
    (
        "compound_dosings",
        "dosing of compound",
        "compounds",
        "study_compound.study_compound_uid",
    ),
    ("compound_dosings", "dosing in element", "elements", "study_element.element_uid"),
    ("soa_footnotes", "references", "", "referenced_items.item_uid"),
)

RELATIONSHIPS_SECTION = "relationships"


def _values(data: Any, dotted: str) -> list[str]:
    """Collects all non-null values found at a dotted path, descending into lists."""
    current = [data]
    for part in dotted.split("."):
        nxt = []
        for node in current:
            for item in node if isinstance(node, list) else [node]:
                if isinstance(item, dict) and item.get(part) is not None:
                    nxt.append(item[part])
        current = nxt
    return [
        str(v) for node in current for v in (node if isinstance(node, list) else [node])
    ]


def extract_relationships(
    indexed: dict[str, dict[str, dict[Any, Any]]],
) -> dict[str, str | None]:
    """Turns the references between loaded study items into edges.
    Returns {edge key: display label}; the key only holds identifiers so an
    edge is the same on both versions even when names are edited."""
    sections = {section.name: section for section in SECTIONS}
    labels = {
        name: {key: _item_label(item) for key, item in items.items()}
        for name, items in indexed.items()
    }
    edges: dict[str, str | None] = {}
    for source, relation, target, path in RELATIONSHIPS:
        for source_key, item in indexed.get(source, {}).items():
            source_label = labels[source].get(source_key) or source_key
            for ref in _values(item, path):
                edge = f"{source}[{source_key}] {relation} {target or 'item'}[{ref}]"
                ref_label = labels.get(target, {}).get(ref) or ref
                edges[edge] = (
                    f"{sections[source].title}: {source_label} {relation} {ref_label}"
                )
    return edges


# Pseudo version selecting the current draft. Study versions can only be
# loaded by number for LOCKED/RELEASED snapshots, the draft is the "latest" value.
DRAFT_VERSION = "draft"


def _resolve_version(version: str) -> str | None:
    return None if version == DRAFT_VERSION else version


class StudyComparisonService:
    @staticmethod
    def _load(
        study_uid: str, version: str | None
    ) -> dict[str, dict[str, dict[Any, Any]]]:
        return {
            section.name: _index_items(
                section.loader(study_uid, version), section.key_fields
            )
            for section in SECTIONS
        }

    @staticmethod
    def _section(
        name: str, title: str, items: list[StudyComparisonItemChange]
    ) -> StudyComparisonSection:
        counts = dict.fromkeys(StudyComparisonChangeType, 0)
        for item in items:
            counts[item.change_type] += 1
        return StudyComparisonSection(
            section=name,
            title=title,
            added=counts[StudyComparisonChangeType.ADDED],
            removed=counts[StudyComparisonChangeType.REMOVED],
            modified=counts[StudyComparisonChangeType.MODIFIED],
            recreated=counts[StudyComparisonChangeType.RECREATED],
            unchanged=counts[StudyComparisonChangeType.UNCHANGED],
            items=items,
        )

    def compare(
        self,
        study_uid: str,
        version_a: str,
        version_b: str,
        include_unchanged: bool = False,
        ignore_fields: tuple[str, ...] = (),
    ) -> StudyComparison:
        resolved_a, resolved_b = _resolve_version(version_a), _resolve_version(
            version_b
        )
        for version in (resolved_a, resolved_b):
            StudyService.check_if_study_uid_and_version_exists(study_uid, version)

        data_a, data_b = (
            self._load(study_uid, resolved_a),
            self._load(study_uid, resolved_b),
        )

        sections = [
            self._section(
                section.name,
                section.title,
                diff_indexed(
                    data_a[section.name],
                    data_b[section.name],
                    include_unchanged,
                    ignore_fields,
                ),
            )
            for section in SECTIONS
        ]

        edges_a, edges_b = extract_relationships(data_a), extract_relationships(data_b)
        relationship_changes = [
            StudyComparisonItemChange(
                key=key,
                label=edges_a[key],
                change_type=StudyComparisonChangeType.REMOVED,
            )
            for key in edges_a.keys() - edges_b.keys()
        ] + [
            StudyComparisonItemChange(
                key=key,
                label=edges_b[key],
                change_type=StudyComparisonChangeType.ADDED,
            )
            for key in edges_b.keys() - edges_a.keys()
        ]
        if include_unchanged:
            relationship_changes += [
                StudyComparisonItemChange(
                    key=key,
                    label=edges_b[key],
                    change_type=StudyComparisonChangeType.UNCHANGED,
                )
                for key in edges_a.keys() & edges_b.keys()
            ]
        sections.append(
            self._section(
                RELATIONSHIPS_SECTION,
                "Relationships between study components",
                sorted(relationship_changes, key=lambda c: (c.label or "", c.key)),
            )
        )

        return StudyComparison(
            study_uid=study_uid,
            version_a=version_a,
            version_b=version_b,
            has_changes=any(
                section.added
                or section.removed
                or section.modified
                or section.recreated
                for section in sections
            ),
            sections=sections,
        )
