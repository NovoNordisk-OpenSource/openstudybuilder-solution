from clinical_mdr_api.models.study_selections.study_comparison import (
    StudyComparisonChangeType,
)
from clinical_mdr_api.services.studies import study_comparison as sc
from clinical_mdr_api.services.studies.study_comparison import (
    StudyComparisonService,
    diff_fields,
    diff_items,
    flatten,
)


def test_flatten_ignores_audit_fields_and_keys_lists_by_uid():
    flat = flatten(
        {
            "name": "x",
            "start_date": "2020",
            "author_username": "me",
            "timing": {"unit": "days"},
            "terms": [{"uid": "t2", "v": 1}, {"uid": "t1", "v": 2}],
            "tags": ["a", "b"],
        }
    )
    assert flat == {
        "name": "x",
        "timing.unit": "days",
        "terms[t2].uid": "t2",
        "terms[t2].v": 1,
        "terms[t1].uid": "t1",
        "terms[t1].v": 2,
        "tags": ["a", "b"],
    }


def test_flatten_list_of_dicts_without_uids_uses_index():
    assert flatten({"rows": [{"a": 1}, {"a": 2}]}) == {"rows[0].a": 1, "rows[1].a": 2}


def test_diff_fields_reports_changed_added_and_removed_fields():
    changes = diff_fields({"a": 1, "b": 2, "c": 3}, {"a": 1, "b": 5, "d": 4})
    assert {c.field: (c.old_value, c.new_value) for c in changes} == {
        "b": (2, 5),
        "c": (3, None),
        "d": (None, 4),
    }


def test_diff_items_added_removed_modified_and_unchanged():
    a = [
        {"uid": "1", "name": "same"},
        {"uid": "2", "name": "old"},
        {"uid": "3", "name": "gone"},
    ]
    b = [
        {"uid": "1", "name": "same", "start_date": "ignored"},
        {"uid": "2", "name": "new"},
        {"uid": "4", "name": "fresh"},
    ]
    result = {c.key: c for c in diff_items(a, b, ("uid",))}
    assert set(result) == {"2", "3", "4"}
    assert result["3"].change_type == StudyComparisonChangeType.REMOVED
    assert [(c.field, c.old_value, c.new_value) for c in result["3"].changes] == [
        ("name", "gone", None),
        ("uid", "3", None),
    ]
    assert result["4"].change_type == StudyComparisonChangeType.ADDED
    assert result["2"].change_type == StudyComparisonChangeType.MODIFIED
    assert result["2"].label == "new"
    assert [(c.field, c.old_value, c.new_value) for c in result["2"].changes] == [
        ("name", "old", "new")
    ]


def test_diff_items_duplicate_keys_do_not_collapse():
    a = [{"uid": "1", "v": 1}, {"uid": "1", "v": 2}]
    b = [{"uid": "1", "v": 1}, {"uid": "1", "v": 3}]
    result = diff_items(a, b, ("uid",))
    assert len(result) == 1
    assert result[0].key == "1#2"


def test_compare_builds_sections(monkeypatch):
    monkeypatch.setattr(
        sc.StudyService,
        "check_if_study_uid_and_version_exists",
        staticmethod(lambda study_uid, study_value_version=None: None),
    )
    data = {
        "1": [{"uid": "v1", "name": "Visit 1"}],
        "2": [{"uid": "v1", "name": "Visit 1b"}, {"uid": "v2", "name": "Visit 2"}],
    }
    monkeypatch.setattr(
        sc,
        "SECTIONS",
        (sc._Section("visits", "Visits", ("uid",), lambda uid, v: data[v]),),
    )

    result = StudyComparisonService().compare("Study_1", "1", "2")

    assert result.has_changes
    section, relationships = result.sections
    assert (section.added, section.removed, section.modified) == (1, 0, 1)
    assert relationships.section == "relationships"
    assert relationships.items == []


def test_extract_relationships_resolves_labels_and_nested_lists():
    indexed = {
        "arms": {"A1": {"arm_uid": "A1", "name": "Placebo"}},
        "epochs": {"E1": {"uid": "E1", "epoch_name": "Treatment"}},
        "design_cells": {
            "C1": {
                "design_cell_uid": "C1",
                "study_arm_uid": "A1",
                "study_epoch_uid": "E1",
                "study_element_uid": None,
            }
        },
        "cohorts": {
            "K1": {"cohort_uid": "K1", "name": "Co", "arm_roots": [{"arm_uid": "A1"}]}
        },
    }
    edges = sc.extract_relationships(indexed)
    assert edges == {
        "design_cells[C1] in arm arms[A1]": "Study design cells: C1 in arm Placebo",
        "design_cells[C1] in epoch epochs[E1]": "Study design cells: C1 in epoch Treatment",
        "cohorts[K1] includes arm arms[A1]": "Study cohorts: Co includes arm Placebo",
    }


def test_compare_reports_added_and_removed_relationships(monkeypatch):
    monkeypatch.setattr(
        sc.StudyService,
        "check_if_study_uid_and_version_exists",
        staticmethod(lambda study_uid, study_value_version=None: None),
    )
    cells = {
        "1": [{"design_cell_uid": "C1", "study_arm_uid": "A1"}],
        "2": [{"design_cell_uid": "C1", "study_arm_uid": "A2"}],
    }
    monkeypatch.setattr(
        sc,
        "SECTIONS",
        (
            sc._Section(
                "design_cells",
                "Study design cells",
                ("design_cell_uid",),
                lambda uid, v: cells[v],
            ),
        ),
    )

    result = StudyComparisonService().compare("Study_1", "1", "2")

    relationships = result.sections[-1]
    assert (relationships.added, relationships.removed) == (1, 1)
    assert {i.change_type for i in relationships.items} == {
        StudyComparisonChangeType.ADDED,
        StudyComparisonChangeType.REMOVED,
    }


def test_draft_version_is_resolved_to_latest(monkeypatch):
    checked, loaded = [], []
    monkeypatch.setattr(
        sc.StudyService,
        "check_if_study_uid_and_version_exists",
        staticmethod(
            lambda study_uid, study_value_version=None: checked.append(
                study_value_version
            )
        ),
    )

    def loader(uid, version):
        loaded.append(version)
        return []

    monkeypatch.setattr(
        sc, "SECTIONS", (sc._Section("visits", "Visits", ("uid",), loader),)
    )

    result = StudyComparisonService().compare("Study_1", "2", "draft")

    assert checked == ["2", None]
    assert loaded == ["2", None]
    assert (result.version_a, result.version_b) == ("2", "draft")


def test_include_unchanged_returns_everything_with_changed_flags():
    a = [{"uid": "1", "name": "same", "x": 1}, {"uid": "2", "name": "old", "x": 1}]
    b = [{"uid": "1", "name": "same", "x": 1}, {"uid": "2", "name": "new", "x": 1}]

    only_changes = {c.key: c for c in diff_items(a, b, ("uid",))}
    assert set(only_changes) == {"2"}
    assert [c.field for c in only_changes["2"].changes] == ["name"]

    everything = {c.key: c for c in diff_items(a, b, ("uid",), include_unchanged=True)}
    assert everything["1"].change_type == StudyComparisonChangeType.UNCHANGED
    assert {c.field for c in everything["1"].changes} == {"name", "uid", "x"}
    assert not any(c.changed for c in everything["1"].changes)
    assert everything["2"].change_type == StudyComparisonChangeType.MODIFIED
    assert {c.field: c.changed for c in everything["2"].changes} == {
        "name": True,
        "uid": False,
        "x": False,
    }


def test_compare_with_unchanged_does_not_report_changes(monkeypatch):
    monkeypatch.setattr(
        sc.StudyService,
        "check_if_study_uid_and_version_exists",
        staticmethod(lambda study_uid, study_value_version=None: None),
    )
    same = [{"design_cell_uid": "C1", "study_arm_uid": "A1"}]
    monkeypatch.setattr(
        sc,
        "SECTIONS",
        (
            sc._Section(
                "design_cells", "Cells", ("design_cell_uid",), lambda uid, v: same
            ),
        ),
    )

    result = StudyComparisonService().compare("S", "1", "2", include_unchanged=True)

    assert not result.has_changes
    assert result.sections[0].unchanged == 1
    assert result.sections[-1].unchanged == 1  # relationship C1 -> A1


def test_ignore_fields_matches_path_last_segment_and_wildcards():
    old = {"uid": "1", "arm_uid": "x", "name": "a", "sub": {"uid": "u1", "v": 1}}
    new = {"uid": "2", "arm_uid": "y", "name": "a", "sub": {"uid": "u2", "v": 2}}
    assert {c.field for c in diff_fields(old, new)} == {
        "uid",
        "arm_uid",
        "sub.uid",
        "sub.v",
    }
    assert {c.field for c in diff_fields(old, new, ignore_fields=("uid", "*_uid"))} == {
        "sub.v"
    }
    assert {c.field for c in diff_fields(old, new, ignore_fields=("sub.*",))} == {
        "uid",
        "arm_uid",
    }


def test_deleted_and_recreated_item_is_detected_ignoring_uids():
    a = [{"uid": "1", "name": "Arm A", "n": 5}, {"uid": "2", "name": "Gone"}]
    b = [{"uid": "9", "name": "Arm A", "n": 5}, {"uid": "3", "name": "New"}]
    items = {i.change_type: i for i in sc.diff_items(a, b, ("uid",))}
    assert set(items) == {"RECREATED", "REMOVED", "ADDED"}
    recreated = items["RECREATED"]
    assert recreated.label == "Arm A"
    assert [(c.field, c.old_value, c.new_value) for c in recreated.changes] == [
        ("uid", "1", "9")
    ]


def test_recreated_requires_equal_values():
    a = [{"uid": "1", "name": "Arm A", "n": 5}]
    b = [{"uid": "9", "name": "Arm A", "n": 6}]
    assert {i.change_type for i in sc.diff_items(a, b, ("uid",))} == {
        "REMOVED",
        "ADDED",
    }
