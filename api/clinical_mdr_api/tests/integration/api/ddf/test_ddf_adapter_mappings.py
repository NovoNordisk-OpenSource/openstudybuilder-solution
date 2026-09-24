"""
Tests for DDF adapter mappings
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from starlette.testclient import TestClient
from usdm_model import Administration as USDMAdministration
from usdm_model import AliasCode as USDMAliasCode
from usdm_model import Code as USDMCode
from usdm_model import Indication as USDMIndication
from usdm_model import InterventionalStudyDesign as USDMInterventionalStudyDesign
from usdm_model import Procedure as USDMProcedure
from usdm_model import (
    StudyArm,
    StudyCohort,
)
from usdm_model import StudyDesignPopulation as USDMStudyDesignPopulation
from usdm_model import (
    StudyElement,
    StudyEpoch,
)

from clinical_mdr_api.main import app
from clinical_mdr_api.models.study_selections.study import (
    RegistryIdentifiersJsonModel,
    StudyDescriptionJsonModel,
    StudyIdentificationMetadataJsonModel,
    StudyMetadataJsonModel,
    StudyPatchRequestJsonModel,
)
from clinical_mdr_api.services.ddf.usdm_mapper import USDMMapper
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_arm_selection import (
    StudyArmSelectionService,
)
from clinical_mdr_api.services.studies.study_cohort_selection import (
    StudyCohortSelectionService,
)
from clinical_mdr_api.services.studies.study_compound_dosing_selection import (
    StudyCompoundDosingSelectionService,
)
from clinical_mdr_api.services.studies.study_criteria_selection import (
    StudyCriteriaSelectionService,
)
from clinical_mdr_api.services.studies.study_design_cell import StudyDesignCellService
from clinical_mdr_api.services.studies.study_element_selection import (
    StudyElementSelectionService,
)
from clinical_mdr_api.services.studies.study_endpoint_selection import (
    StudyEndpointSelectionService,
)
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "ddfadapter.tests.unit"
    inject_and_clear_db(db_name)
    inject_base_data()

    yield


@pytest.fixture(scope="module")
def ddf_mapper(tst_study):
    mapper = USDMMapper(
        get_osb_study_design_cells=StudyDesignCellService().get_all_design_cells,
        get_osb_study_arms=StudyArmSelectionService().get_all_selection,
        get_osb_study_cohorts=StudyCohortSelectionService().get_all_selection,
        get_osb_study_epochs=StudyEpochService.get_all_epochs,
        get_osb_study_elements=StudyElementSelectionService().get_all_selection,
        get_osb_study_endpoints=StudyEndpointSelectionService().get_all_selection,
        get_osb_study_visits=StudyVisitService.get_all_visits,
        get_osb_study_activities=StudyActivitySelectionService().get_all_selection,
        get_osb_activity_schedules=StudyActivityScheduleService().get_all_schedules,
        get_osb_study_criteria=StudyCriteriaSelectionService().get_all_selection,
        get_osb_study_compound_dosings=StudyCompoundDosingSelectionService().get_all_compound_dosings,
    )
    return mapper


def test_ddf_study_arms(ddf_mapper, tst_study, study_arms):
    ddf_arms = ddf_mapper._get_study_arms(tst_study)
    for ddf_arm, sb_arm in zip(ddf_arms, study_arms):
        assert ddf_arm.description == sb_arm.description
        assert ddf_arm.type.code == sb_arm.arm_type.term_uid


def test_ddf_study_cells(ddf_mapper, tst_study, study_design_cells):
    ddf_study_cells = ddf_mapper._get_study_cells(tst_study)
    for ddf_study_cell, sb_study_design_cell in zip(
        ddf_study_cells, study_design_cells
    ):
        assert ddf_study_cell.armId == ddf_mapper._id_manager.get_id(
            StudyArm.__name__, sb_study_design_cell.study_arm_uid
        )
        assert ddf_study_cell.epochId == ddf_mapper._id_manager.get_id(
            StudyEpoch.__name__, sb_study_design_cell.study_epoch_uid
        )
        assert ddf_study_cell.elementIds == [
            ddf_mapper._id_manager.get_id(
                StudyElement.__name__, sb_study_design_cell.study_element_uid
            )
        ]


def test_ddf_study_description(ddf_mapper, tst_study):
    ddf_study_description = ddf_mapper._get_study_description(tst_study)
    assert (
        ddf_study_description
        == tst_study.current_metadata.study_description.study_title
    )


def test_ddf_study_acronym_returned_when_set(ddf_mapper, tst_study):
    expected_acronym = "TST-ACR"
    identification_metadata = StudyIdentificationMetadataJsonModel(
        study_acronym=expected_acronym
    )
    current_metadata = StudyMetadataJsonModel(
        identification_metadata=identification_metadata
    )
    study_patch_request = StudyPatchRequestJsonModel(current_metadata=current_metadata)
    patched_study = StudyService().patch(
        uid=tst_study.uid,
        dry=False,
        study_patch_request=study_patch_request,
    )

    assert ddf_mapper._get_study_acronym(patched_study) == expected_acronym


def test_ddf_study_acronym_none_when_unset(ddf_mapper, tst_study):
    identification_metadata = StudyIdentificationMetadataJsonModel(study_acronym=None)
    current_metadata = StudyMetadataJsonModel(
        identification_metadata=identification_metadata
    )
    study_patch_request = StudyPatchRequestJsonModel(current_metadata=current_metadata)
    patched_study = StudyService().patch(
        uid=tst_study.uid,
        dry=False,
        study_patch_request=study_patch_request,
    )

    assert ddf_mapper._get_study_acronym(patched_study) is None


def test_ddf_study_brief_title_returned_when_set(ddf_mapper, tst_study):
    expected_brief_title = "TST-BRIEF"
    study_description = StudyDescriptionJsonModel(
        study_short_title=expected_brief_title
    )
    current_metadata = StudyMetadataJsonModel(study_description=study_description)
    study_patch_request = StudyPatchRequestJsonModel(current_metadata=current_metadata)
    patched_study = StudyService().patch(
        uid=tst_study.uid,
        dry=False,
        study_patch_request=study_patch_request,
    )

    assert ddf_mapper._get_study_brief_title(patched_study) == expected_brief_title


def test_ddf_study_brief_title_none_when_unset(ddf_mapper, tst_study):
    study_description = StudyDescriptionJsonModel(study_short_title=None)
    current_metadata = StudyMetadataJsonModel(study_description=study_description)
    study_patch_request = StudyPatchRequestJsonModel(current_metadata=current_metadata)
    patched_study = StudyService().patch(
        uid=tst_study.uid,
        dry=False,
        study_patch_request=study_patch_request,
    )

    assert ddf_mapper._get_study_brief_title(patched_study) is None


def test_ddf_study_activities(ddf_mapper, tst_study, study_activities):
    ddf_study_activities = ddf_mapper._get_study_activities(tst_study)
    assert ddf_study_activities is not None
    assert len(ddf_study_activities) > 0


def test_study_elements(ddf_mapper, tst_study, study_elements):
    ddf_study_elements = ddf_mapper._get_study_elements(tst_study)
    assert ddf_study_elements is not None
    assert len(ddf_study_elements) > 0


def test_study_epochs(ddf_mapper, tst_study, study_epochs):
    ddf_study_epochs = ddf_mapper._get_study_epochs(tst_study)
    assert ddf_study_epochs is not None
    assert len(ddf_study_epochs) > 0


def test_study_epochs_label_uses_short_name(ddf_mapper, tst_study, monkeypatch):
    """USDM StudyEpoch.label is sourced from OSB StudyEpoch short_name (was
    previously duplicating epoch_name)."""
    epoch = MagicMock()
    epoch.uid = "StudyEpoch_000010"
    epoch.epoch_name = "Wash Out"
    epoch.short_name = "Washout"
    epoch.order = 1
    epoch.description = None
    epoch.epoch_type_ctterm = None

    fake_result = MagicMock()
    fake_result.items = [epoch]
    monkeypatch.setattr(
        ddf_mapper, "_get_osb_study_epochs", lambda *args, **kwargs: fake_result
    )

    ddf_study_epochs = ddf_mapper._get_study_epochs(tst_study)

    assert ddf_study_epochs[0].label == "Washout"


def test_study_visits(ddf_mapper, tst_study, study_visits):
    ddf_study_encounters = ddf_mapper._get_study_encounters(tst_study)
    assert ddf_study_encounters is not None
    assert len(ddf_study_encounters) > 0


def test_study_identifier(ddf_mapper, tst_study):
    ri_metadata = RegistryIdentifiersJsonModel()
    ri_metadata.ct_gov_id = "ct_gov_has_value"
    ri_metadata.eudract_id = "eudract_id_has_value"
    identification_metadata = StudyIdentificationMetadataJsonModel(
        registry_identifiers=ri_metadata
    )
    current_metadata = StudyMetadataJsonModel(
        identification_metadata=identification_metadata
    )
    study_patch_request = StudyPatchRequestJsonModel(current_metadata=current_metadata)
    study_service = StudyService()
    patched_study = study_service.patch(
        uid=tst_study.uid,
        dry=False,
        study_patch_request=study_patch_request,
    )

    ddf_study_identifiers, ddf_organizations = (
        ddf_mapper._get_study_identifiers_and_organizations(patched_study)
    )
    assert ddf_study_identifiers is not None
    assert ddf_organizations is not None


def test_ddf_study_version_identifier_uses_helper(ddf_mapper, tst_study):
    version_metadata = tst_study.current_metadata.version_metadata
    expected = version_metadata.study_status
    if version_metadata.version_number:
        expected += f" v{version_metadata.version_number}"

    assert ddf_mapper._get_study_version(tst_study) == expected


def test_ddf_get_study_version_structural_defaults_and_happy_path(ddf_mapper):
    # Structural default branches: versionIdentifier is required str on
    # usdm_model.StudyVersion v4, so the helper must return a real "" rather
    # than None when OSB metadata is missing.
    no_metadata_study = SimpleNamespace(current_metadata=None)
    assert ddf_mapper._get_study_version(no_metadata_study) == ""

    no_version_study = SimpleNamespace(
        current_metadata=SimpleNamespace(version_metadata=None),
    )
    assert ddf_mapper._get_study_version(no_version_study) == ""

    # Happy path: status + version_number combine into "<status> v<n>".
    populated_study = SimpleNamespace(
        current_metadata=SimpleNamespace(
            version_metadata=SimpleNamespace(
                study_status="DRAFT",
                version_number="0.1",
            ),
        ),
    )
    assert ddf_mapper._get_study_version(populated_study) == "DRAFT v0.1"


def test_therapeutic_areas_empty_when_unset(ddf_mapper, tst_study):
    """tst_study has no therapeutic_area_codes set, should return []."""
    ddf_therapeutic_areas = ddf_mapper._get_therapeutic_areas(tst_study)
    assert ddf_therapeutic_areas == []


def test_study_indications_empty_when_unset(ddf_mapper, tst_study):
    """tst_study has no disease_condition_or_indication_codes set, should return []."""
    ddf_indications = ddf_mapper._get_study_indications(tst_study)
    assert ddf_indications == []


def test_study_indications_attaches_dictionary_code(ddf_mapper, tst_study):
    """When a study population indication has a term_uid, the resulting USDM
    Indication must carry a Code in its codes[] list (the field added by
    Enabler #3690246 — therapeuticAreas + indications USDM mapping)."""
    fake_population = SimpleNamespace(
        rare_disease_indicator=False,
        disease_condition_or_indication_codes=[
            SimpleNamespace(
                term_uid="DictionaryTerm_TEST_001",
                name="Type 2 diabetes mellitus",
            )
        ],
    )
    fake_metadata = SimpleNamespace(study_population=fake_population)
    fake_study = SimpleNamespace(current_metadata=fake_metadata)

    fake_code = USDMCode(
        id="Code_TEST",
        code="44054006",
        codeSystem="SNOMED",
        codeSystemVersion="2025-03-28",
        decode="Type 2 diabetes mellitus",
    )

    with (
        patch.object(
            ddf_mapper, "get_dictionary_term_as_usdm_code", return_value=fake_code
        ),
        patch.object(
            ddf_mapper,
            "get_dictionary_term_definition",
            return_value="Diabetes mellitus type 2 (disorder)",
        ),
    ):
        ddf_indications = ddf_mapper._get_study_indications(fake_study)

    assert len(ddf_indications) == 1
    indication = ddf_indications[0]
    assert isinstance(indication, USDMIndication)
    assert indication.name == "Type 2 diabetes mellitus"
    assert indication.description == "Diabetes mellitus type 2 (disorder)"
    assert indication.isRareDisease is False
    assert len(indication.codes) == 1
    assert indication.codes[0].code == "44054006"
    assert indication.codes[0].codeSystem == "SNOMED"


@pytest.fixture(scope="module")
def study_activities_with_instances(tst_study, study_activities):
    """Create activity instances with NCI concept IDs and attach them to study activities."""
    activity_instance_class = TestUtils.create_activity_instance_class(
        name="NumericFindings"
    )
    activity_instance = TestUtils.create_activity_instance(
        activity_instance_class_uid=activity_instance_class.uid,
        name="Systolic Blood Pressure",
        name_sentence_case="Systolic blood pressure",
        nci_concept_id="C25298",
        nci_concept_name="Systolic Blood Pressure",
        topic_code="SYSBP",
        activities=[study_activities[0].activity.uid],
        activity_subgroups=[
            study_activities[0].study_activity_subgroup.activity_subgroup_uid
        ],
        activity_groups=[study_activities[0].study_activity_group.activity_group_uid],
    )
    TestUtils.batch_select_study_activity_instances(
        study_uid=tst_study.uid,
        study_activity_uid=study_activities[0].study_activity_uid,
        activity_instance_uids=[activity_instance.uid],
    )
    return study_activities


def test_biomedical_concepts_populated(
    ddf_mapper, tst_study, study_activities_with_instances
):
    ddf_study_activities = ddf_mapper._get_study_activities(tst_study)
    bc_ids = [bc_id for a in ddf_study_activities for bc_id in a.biomedicalConceptIds]
    assert (
        len(bc_ids) > 0
    ), "Expected at least one activity to have biomedicalConceptIds"


def test_biomedical_concepts_on_study_version(
    ddf_mapper, tst_study, study_activities_with_instances
):
    ddf_mapper._get_study_activities(tst_study)
    bcs = list(ddf_mapper._bc_by_nci_id.values())
    assert len(bcs) > 0, "Expected biomedicalConcepts to be non-empty"
    bc = next(bc for bc in bcs if bc.code.standardCode.code == "C25298")
    assert bc.code.standardCode.codeSystem == "http://www.cdisc.org"
    assert bc.name == "Systolic Blood Pressure"


def test_biomedical_concept_reference_url(
    ddf_mapper, tst_study, study_activities_with_instances
):
    ddf_mapper._get_study_activities(tst_study)
    bcs = list(ddf_mapper._bc_by_nci_id.values())
    bc = next(bc for bc in bcs if bc.code.standardCode.code == "C25298")
    assert "/mdr/specializations/sdtm/packages/" in bc.reference
    assert bc.reference.endswith("/datasetspecializations/SYSBP")


def test_ddf_study_cohorts(ddf_mapper, tst_study, monkeypatch):
    """Happy path: each OSB cohort selection maps to a usdm_model.StudyCohort
    with name from sc.name, label from sc.short_name, description passed
    through, instanceType set, and a stable id from IdManager keyed on
    cohort_uid. A None description on OSB stays None on the USDM side
    (skip-rather-than-blank — no empty-string placeholder)."""
    selection_a = MagicMock()
    selection_a.cohort_uid = "StudyCohort_A"
    selection_a.name = "Active arm cohort"
    selection_a.short_name = "ACT"
    selection_a.description = "Subjects randomised to the active arm."

    selection_b = MagicMock()
    selection_b.cohort_uid = "StudyCohort_B"
    selection_b.name = "Placebo cohort"
    selection_b.short_name = "PBO"
    selection_b.description = None

    fake_result = MagicMock()
    fake_result.items = [selection_a, selection_b]
    monkeypatch.setattr(
        ddf_mapper, "_get_osb_study_cohorts", lambda **kwargs: fake_result
    )

    ddf_cohorts = ddf_mapper._get_study_cohorts(tst_study)

    assert len(ddf_cohorts) == 2
    assert all(isinstance(c, StudyCohort) for c in ddf_cohorts)
    assert all(c.instanceType == "StudyCohort" for c in ddf_cohorts)

    assert ddf_cohorts[0].id == ddf_mapper._id_manager.get_id(
        StudyCohort.__name__, "StudyCohort_A"
    )
    assert ddf_cohorts[0].name == "Active arm cohort"
    assert ddf_cohorts[0].label == "ACT"
    assert ddf_cohorts[0].description == "Subjects randomised to the active arm."

    assert ddf_cohorts[1].name == "Placebo cohort"
    assert ddf_cohorts[1].label == "PBO"
    assert ddf_cohorts[1].description is None


def test_ddf_study_cohorts_empty(ddf_mapper, tst_study, monkeypatch):
    """A study with no cohort selections produces an empty list and the
    helper does not raise."""
    fake_result = MagicMock()
    fake_result.items = []
    monkeypatch.setattr(
        ddf_mapper, "_get_osb_study_cohorts", lambda **kwargs: fake_result
    )

    ddf_cohorts = ddf_mapper._get_study_cohorts(tst_study)

    assert ddf_cohorts == []


def test_ddf_eligibility_inc_exc_naming_and_linkage(ddf_mapper, tst_study, monkeypatch):
    """Happy-path mapping for _get_eligibility_criteria covering the three
    invariants REQUIREMENTS §8 / audit §MAJOR call out:

    1. Per-category INC{n} / EXC{n} naming — first inclusion is INC1,
       first exclusion is EXC1.
    2. ``identifier`` is a global running index across categories, emitted
       as a ``str`` (not int).
    3. ``criterionItemId`` on EligibilityCriterion equals the ``id`` of
       its matching EligibilityCriterionItem.
    """
    inclusion_selection = MagicMock()
    inclusion_selection.study_criteria_uid = "StudyCriteria_INC_001"
    inclusion_selection.criteria.name_plain = "Subject is at least 18 years old."
    inclusion_selection.template = None
    inclusion_selection.criteria_type.term_uid = "C25532"

    exclusion_selection = MagicMock()
    exclusion_selection.study_criteria_uid = "StudyCriteria_EXC_001"
    exclusion_selection.criteria.name_plain = "Subject is pregnant."
    exclusion_selection.template = None
    exclusion_selection.criteria_type.term_uid = "C25370"

    fake_result = MagicMock()
    fake_result.items = [inclusion_selection, exclusion_selection]
    monkeypatch.setattr(
        ddf_mapper, "_get_osb_study_criteria", lambda **kwargs: fake_result
    )

    criteria, criterion_items = ddf_mapper._get_eligibility_criteria(tst_study)

    assert [c.name for c in criteria] == ["INC1", "EXC1"]
    assert [c.name for c in criterion_items] == ["INC1", "EXC1"]
    assert [c.identifier for c in criteria] == ["1", "2"]
    assert all(isinstance(c.identifier, str) for c in criteria)
    assert criteria[0].criterionItemId == criterion_items[0].id
    assert criteria[1].criterionItemId == criterion_items[1].id


def test_ddf_eligibility_unknown_category_falls_back_to_uid(
    ddf_mapper, tst_study, monkeypatch
):
    """A selection whose category is neither Inclusion (C25532) nor
    Exclusion (C25370) must fall back to the raw study_criteria_uid for
    EligibilityCriterion.name and the matching EligibilityCriterionItem.name,
    rather than minting an INC{n}/EXC{n} short label."""
    selection = MagicMock()
    selection.study_criteria_uid = "StudyCriteria_OTHER_001"
    selection.criteria.name_plain = "Subject is willing to participate."
    selection.template = None
    selection.criteria_type.term_uid = "C99999"

    fake_result = MagicMock()
    fake_result.items = [selection]
    monkeypatch.setattr(
        ddf_mapper, "_get_osb_study_criteria", lambda **kwargs: fake_result
    )

    criteria, criterion_items = ddf_mapper._get_eligibility_criteria(tst_study)

    assert len(criteria) == 1
    assert len(criterion_items) == 1
    assert criteria[0].name == "StudyCriteria_OTHER_001"
    assert criterion_items[0].name == "StudyCriteria_OTHER_001"


def test_get_ct_package_term_as_usdm_code_exact_match_c1909(ddf_mapper, monkeypatch):
    """Regression test: get_ct_package_term_as_usdm_code must use exact uid match
    (cttr.uid = $concept_id) so that C1909 resolves to 'Pharmacologic Substance'
    and not to a later term whose uid merely starts with 'C1909' (e.g. C190958
    'Harvey-Bradshaw Index ...' introduced in 2022).

    We mock db.cypher_query to return the single row that the corrected query
    produces for C1909, then assert code and decode are correct.
    """
    library_node = {"name": "CDISC"}
    term_name_value_node = {"name": "Pharmacologic Substance"}

    monkeypatch.setattr(
        "clinical_mdr_api.services.ddf.usdm_mapper.db",
        type(
            "FakeDB",
            (),
            {
                "cypher_query": staticmethod(
                    lambda q, p: ([[library_node, term_name_value_node]], None)
                )
            },
        )(),
    )

    result = ddf_mapper.get_ct_package_term_as_usdm_code("C1909")

    assert result.code == "C1909"
    assert result.decode == "Pharmacologic Substance"
    assert result.codeSystem == "CDISC"


def test_get_ct_package_term_as_usdm_code_none_returns_void(ddf_mapper):
    """When concept_id is None the helper must return the void code (empty decode)
    without hitting the database."""
    result = ddf_mapper.get_ct_package_term_as_usdm_code(None)

    assert result.code == ""
    assert result.decode == ""


# ---------------------------------------------------------------------------
# ADO 873821: rare-disease guard, InterventionalStudyDesign, blindingSchema,
# StudyVersion.rationale
# ---------------------------------------------------------------------------


def test_rare_disease_none_with_populated_codes_emits_indications(ddf_mapper):
    """rare_disease_indicator=None must not suppress indications when disease
    codes are present. The resulting isRareDisease must be False (safe default)."""
    fake_population = SimpleNamespace(
        rare_disease_indicator=None,
        disease_condition_or_indication_codes=[
            SimpleNamespace(
                term_uid="DictionaryTerm_RARE_001",
                name="Wilson Disease",
            )
        ],
    )
    fake_study = SimpleNamespace(
        current_metadata=SimpleNamespace(study_population=fake_population)
    )

    fake_code = USDMCode(
        id="Code_RARE",
        code="88",
        codeSystem="SNOMED",
        codeSystemVersion="2025-01-01",
        decode="Wilson Disease",
    )

    with (
        patch.object(
            ddf_mapper, "get_dictionary_term_as_usdm_code", return_value=fake_code
        ),
        patch.object(
            ddf_mapper,
            "get_dictionary_term_definition",
            return_value="Wilson disease (disorder)",
        ),
    ):
        ddf_indications = ddf_mapper._get_study_indications(fake_study)

    assert len(ddf_indications) == 1
    indication = ddf_indications[0]
    assert isinstance(indication, USDMIndication)
    assert indication.name == "Wilson Disease"
    assert indication.isRareDisease is False


def test_rare_disease_true_preserved(ddf_mapper):
    """rare_disease_indicator=True must be passed through as isRareDisease=True."""
    fake_population = SimpleNamespace(
        rare_disease_indicator=True,
        disease_condition_or_indication_codes=[
            SimpleNamespace(
                term_uid=None,
                name="Rare Orphan Condition",
            )
        ],
    )
    fake_study = SimpleNamespace(
        current_metadata=SimpleNamespace(study_population=fake_population)
    )

    ddf_indications = ddf_mapper._get_study_indications(fake_study)

    assert len(ddf_indications) == 1
    assert ddf_indications[0].isRareDisease is True


def test_study_designs_returns_interventional_study_design(
    ddf_mapper, tst_study, monkeypatch
):
    """_get_study_designs must return an InterventionalStudyDesign with
    instanceType='InterventionalStudyDesign', and model/subTypes/intentTypes
    populated (non-None, since helpers return void code / empty list at minimum).

    _get_study_population is monkeypatched because tst_study has no population
    data — the population helper is tested separately."""
    stub_population = USDMStudyDesignPopulation(
        id="pop-stub-id",
        name="Stub Population",
        includesHealthySubjects=False,
        instanceType="StudyDesignPopulation",
    )
    monkeypatch.setattr(
        ddf_mapper, "_get_study_population", lambda study: stub_population
    )

    designs = ddf_mapper._get_study_designs(tst_study)

    assert len(designs) == 1
    design = designs[0]
    assert isinstance(design, USDMInterventionalStudyDesign)
    assert design.instanceType == "InterventionalStudyDesign"
    # model is required on InterventionalStudyDesign — must be populated
    assert design.model is not None
    # subTypes and intentTypes are lists (may be empty when OSB has no data)
    assert isinstance(design.subTypes, list)
    assert isinstance(design.intentTypes, list)


def test_blinding_schema_populated_when_code_set(ddf_mapper):
    """_get_blinding_schema returns an AliasCode when the OSB blinding code is set."""
    fake_blinding_code = SimpleNamespace(term_uid="C15228_OPENLABEL")
    fake_study = SimpleNamespace(
        current_metadata=SimpleNamespace(
            study_intervention=SimpleNamespace(
                trial_blinding_schema_code=fake_blinding_code
            )
        )
    )

    fake_code = USDMCode(
        id="Code_BLIND",
        code="C15228",
        codeSystem="CDISC",
        codeSystemVersion="2024",
        decode="Open Label",
    )

    with patch.object(
        ddf_mapper, "get_ct_package_term_as_usdm_code", return_value=fake_code
    ):
        result = ddf_mapper._get_blinding_schema(fake_study)

    assert result is not None
    assert isinstance(result, USDMAliasCode)
    assert result.instanceType == "AliasCode"
    assert result.standardCode.code == "C15228"


def test_blinding_schema_none_when_unset(ddf_mapper):
    """_get_blinding_schema returns None when trial_blinding_schema_code is absent."""
    fake_study = SimpleNamespace(
        current_metadata=SimpleNamespace(
            study_intervention=SimpleNamespace(trial_blinding_schema_code=None)
        )
    )

    result = ddf_mapper._get_blinding_schema(fake_study)

    assert result is None


def test_ct_term_lookup_strips_term_uid_suffix(ddf_mapper, monkeypatch):
    """Suffixed OSB term_uids ("C15228_OPENLABEL") must resolve on the bare C-code."""
    queried = []

    def fake_cypher_query(_query, params):
        queried.append(params["concept_id"])
        return [], None

    monkeypatch.setattr(
        "clinical_mdr_api.services.ddf.usdm_mapper.db.cypher_query", fake_cypher_query
    )

    ddf_mapper.get_ct_package_term_as_usdm_code("C15228_OPENLABEL")
    ddf_mapper.get_ct_package_term_as_usdm_code("C15228")

    assert queried == ["C15228", "C15228"]


def test_unit_definition_ct_term_lookup_is_cached(ddf_mapper, monkeypatch):
    """Repeated dose-unit lookups must hit the cache, not Neo4j."""
    calls = []

    def fake_cypher_query(_query, params):
        calls.append(params["uid"])
        return [["C28253"]], None

    monkeypatch.setattr(
        "clinical_mdr_api.services.ddf.usdm_mapper.db.cypher_query", fake_cypher_query
    )
    ddf_mapper._unit_ct_term_cache = {}

    first = ddf_mapper._get_ct_term_uid_for_unit_definition("UnitDefinition_000001")
    second = ddf_mapper._get_ct_term_uid_for_unit_definition("UnitDefinition_000001")

    assert first == second == "C28253"
    assert calls == ["UnitDefinition_000001"]


def test_study_version_rationale_uses_version_description(ddf_mapper):
    """StudyVersion.rationale must equal version_description when set."""
    version_description = "Update NYHA classification"
    fake_study = SimpleNamespace(
        current_metadata=SimpleNamespace(
            version_metadata=SimpleNamespace(version_description=version_description)
        )
    )

    assert ddf_mapper._get_study_rationale(fake_study) == version_description


def test_study_version_rationale_defaults_to_empty_when_none(ddf_mapper):
    """StudyVersion.rationale must default to '' when version_description is None."""
    fake_study = SimpleNamespace(
        current_metadata=SimpleNamespace(
            version_metadata=SimpleNamespace(version_description=None)
        )
    )

    assert ddf_mapper._get_study_rationale(fake_study) == ""


# ---------------------------------------------------------------------------
# ADO 254080: timing windowLabel, activity next/previousId, entryId,
# plannedDuration, StudyElement transition rules + name
# ---------------------------------------------------------------------------


def test_timing_window_label_populated_when_window_values_exist(
    ddf_mapper, monkeypatch
):
    """windowLabel must be set when min/max window values are both non-zero."""
    visit = SimpleNamespace(
        uid="Visit_WIN",
        is_global_anchor_visit=False,
        time_value=7,
        time_unit_name="days",
        min_visit_window_value=1,
        max_visit_window_value=2,
        visit_window_unit_name="days",
        study_epoch=None,
        study_epoch_uid="Epoch_001",
    )
    fake_visits = MagicMock()
    fake_visits.items = [visit]
    monkeypatch.setattr(ddf_mapper, "_get_osb_study_visits", lambda uid: fake_visits)
    monkeypatch.setattr(ddf_mapper, "_get_osb_activity_schedules", lambda uid: [])
    fake_study = SimpleNamespace(
        uid="Study_WIN_TEST",
        current_metadata=SimpleNamespace(
            study_intervention=SimpleNamespace(planned_study_length=None)
        ),
    )

    timelines = ddf_mapper._get_study_schedule_timelines(fake_study)
    timing = timelines[0].timings[0]

    assert timing.windowLabel == "1..2 days"
    assert timing.windowLower is not None
    assert timing.windowUpper is not None


def test_timing_window_label_none_when_no_window(ddf_mapper, monkeypatch):
    """windowLabel must be None when window values are absent."""
    visit = SimpleNamespace(
        uid="Visit_NOWIN",
        is_global_anchor_visit=True,
        time_value=0,
        time_unit_name="days",
        min_visit_window_value=None,
        max_visit_window_value=None,
        visit_window_unit_name="days",
        study_epoch=None,
        study_epoch_uid="Epoch_001",
    )
    fake_visits = MagicMock()
    fake_visits.items = [visit]
    monkeypatch.setattr(ddf_mapper, "_get_osb_study_visits", lambda uid: fake_visits)
    monkeypatch.setattr(ddf_mapper, "_get_osb_activity_schedules", lambda uid: [])
    fake_study = SimpleNamespace(
        uid="Study_NOWIN_TEST",
        current_metadata=SimpleNamespace(
            study_intervention=SimpleNamespace(planned_study_length=None)
        ),
    )

    timelines = ddf_mapper._get_study_schedule_timelines(fake_study)
    timing = timelines[0].timings[0]

    assert timing.windowLabel is None


def test_activity_next_previous_ids_chained_in_soa_order(ddf_mapper, monkeypatch):
    """Three activities in known SoA order must form the linked list:
    (None, a2) / (a1, a3) / (a2, None)."""

    def _make_activity(uid, soa_order, grp_order, sub_order, act_order):
        a = MagicMock()
        a.study_activity_uid = uid
        a.order = act_order
        a.study_soa_group = SimpleNamespace(order=soa_order)
        a.study_activity_group = SimpleNamespace(order=grp_order)
        a.study_activity_subgroup = SimpleNamespace(
            order=sub_order, activity_subgroup_name="Sub"
        )
        a.activity = SimpleNamespace(uid=f"{uid}_act", name="Test Activity")
        return a

    act1 = _make_activity("SA_001", 1, 1, 1, 1)
    act2 = _make_activity("SA_002", 1, 1, 1, 2)
    act3 = _make_activity("SA_003", 1, 2, 1, 1)

    fake_result = MagicMock()
    # Deliberately scramble the order so sorting is exercised
    fake_result.items = [act3, act1, act2]
    monkeypatch.setattr(
        ddf_mapper, "_get_osb_study_activities", lambda uid: fake_result
    )
    monkeypatch.setattr(ddf_mapper, "_load_biomedical_concept_data", lambda uid: None)
    ddf_mapper._study_activity_bc_ids = {}

    fake_study = SimpleNamespace(uid="Study_TEST")
    activities = ddf_mapper._get_study_activities(fake_study)

    # Sorted order should be act1, act2, act3
    assert activities[0].previousId is None
    assert activities[0].nextId == ddf_mapper._id_manager.get_id("Activity", "SA_002")
    assert activities[1].previousId == ddf_mapper._id_manager.get_id(
        "Activity", "SA_001"
    )
    assert activities[1].nextId == ddf_mapper._id_manager.get_id("Activity", "SA_003")
    assert activities[2].previousId == ddf_mapper._id_manager.get_id(
        "Activity", "SA_002"
    )
    assert activities[2].nextId is None


def test_activity_next_previous_ids_none_when_order_missing(ddf_mapper, monkeypatch):
    """Activities with a missing order component must not raise and must leave
    nextId/previousId as None."""
    act1 = MagicMock()
    act1.study_activity_uid = "SA_X01"
    act1.order = None  # missing
    act1.study_soa_group = SimpleNamespace(order=1)
    act1.study_activity_group = SimpleNamespace(order=1)
    act1.study_activity_subgroup = SimpleNamespace(
        order=1, activity_subgroup_name="Sub"
    )
    act1.activity = SimpleNamespace(uid="SA_X01_act", name="Activity X1")

    act2 = MagicMock()
    act2.study_activity_uid = "SA_X02"
    act2.order = 2
    act2.study_soa_group = SimpleNamespace(order=1)
    act2.study_activity_group = SimpleNamespace(order=1)
    act2.study_activity_subgroup = SimpleNamespace(
        order=1, activity_subgroup_name="Sub"
    )
    act2.activity = SimpleNamespace(uid="SA_X02_act", name="Activity X2")

    fake_result = MagicMock()
    fake_result.items = [act1, act2]
    monkeypatch.setattr(
        ddf_mapper, "_get_osb_study_activities", lambda uid: fake_result
    )
    monkeypatch.setattr(ddf_mapper, "_load_biomedical_concept_data", lambda uid: None)
    ddf_mapper._study_activity_bc_ids = {}

    fake_study = SimpleNamespace(uid="Study_MISSING_ORDER")
    activities = ddf_mapper._get_study_activities(fake_study)

    assert all(a.nextId is None for a in activities)
    assert all(a.previousId is None for a in activities)


def test_entry_id_equals_first_scheduled_activity_instance(ddf_mapper, monkeypatch):
    """entryId on the timeline must equal the id of the first ScheduledActivityInstance."""
    visit_a = SimpleNamespace(
        uid="Visit_A",
        is_global_anchor_visit=True,
        time_value=0,
        time_unit_name="days",
        min_visit_window_value=None,
        max_visit_window_value=None,
        visit_window_unit_name="days",
        study_epoch=None,
        study_epoch_uid="Epoch_001",
    )
    visit_b = SimpleNamespace(
        uid="Visit_B",
        is_global_anchor_visit=False,
        time_value=7,
        time_unit_name="days",
        min_visit_window_value=None,
        max_visit_window_value=None,
        visit_window_unit_name="days",
        study_epoch=None,
        study_epoch_uid="Epoch_001",
    )
    fake_visits = MagicMock()
    fake_visits.items = [visit_a, visit_b]
    monkeypatch.setattr(ddf_mapper, "_get_osb_study_visits", lambda uid: fake_visits)
    monkeypatch.setattr(ddf_mapper, "_get_osb_activity_schedules", lambda uid: [])
    fake_study = SimpleNamespace(
        uid="Study_ENTRYID_TEST",
        current_metadata=SimpleNamespace(
            study_intervention=SimpleNamespace(planned_study_length=None)
        ),
    )

    timelines = ddf_mapper._get_study_schedule_timelines(fake_study)
    timeline = timelines[0]

    assert timeline.entryId != ""
    assert timeline.entryId == timeline.instances[0].id


def test_planned_duration_built_when_study_length_set(ddf_mapper, monkeypatch):
    """plannedDuration must be a Duration with text='P52W' when
    planned_study_length is 52 weeks."""
    fake_visits = MagicMock()
    fake_visits.items = []
    monkeypatch.setattr(ddf_mapper, "_get_osb_study_visits", lambda uid: fake_visits)
    monkeypatch.setattr(ddf_mapper, "_get_osb_activity_schedules", lambda uid: [])

    fake_study = SimpleNamespace(
        uid="Study_PLANDUR_TEST",
        current_metadata=SimpleNamespace(
            study_intervention=SimpleNamespace(
                planned_study_length=SimpleNamespace(
                    duration_value=52,
                    duration_unit_code=SimpleNamespace(name="weeks"),
                )
            )
        ),
    )

    timelines = ddf_mapper._get_study_schedule_timelines(fake_study)
    pd = timelines[0].plannedDuration

    assert pd is not None
    assert pd.text == "P52W"
    assert pd.durationWillVary is False


def test_planned_duration_absent_when_study_length_none(ddf_mapper, monkeypatch):
    """plannedDuration must be None when planned_study_length is None."""
    fake_visits = MagicMock()
    fake_visits.items = []
    monkeypatch.setattr(ddf_mapper, "_get_osb_study_visits", lambda uid: fake_visits)
    monkeypatch.setattr(ddf_mapper, "_get_osb_activity_schedules", lambda uid: [])

    fake_study = SimpleNamespace(
        uid="Study_PLANDUR_NONE_TEST",
        current_metadata=SimpleNamespace(
            study_intervention=SimpleNamespace(planned_study_length=None)
        ),
    )

    timelines = ddf_mapper._get_study_schedule_timelines(fake_study)

    assert timelines[0].plannedDuration is None


def test_study_element_transition_rules_when_rules_set(ddf_mapper, monkeypatch):
    """transitionStartRule and transitionEndRule must be TransitionRule objects
    when OSB start_rule/end_rule are set."""
    element = MagicMock()
    element.element_uid = "Element_001"
    element.name = "Treatment Period"
    element.description = "Active treatment."
    element.start_rule = "Informed consent signed"
    element.end_rule = "End of treatment visit completed"

    fake_result = MagicMock()
    fake_result.items = [element]
    monkeypatch.setattr(ddf_mapper, "_get_osb_study_elements", lambda uid: fake_result)

    fake_study = SimpleNamespace(uid="Study_TEST")
    elements = ddf_mapper._get_study_elements(fake_study)

    assert len(elements) == 1
    el = elements[0]
    assert el.transitionStartRule is not None
    assert el.transitionStartRule.text == "Informed consent signed"
    assert el.transitionEndRule is not None
    assert el.transitionEndRule.text == "End of treatment visit completed"


def test_study_element_transition_rules_none_when_unset(ddf_mapper, monkeypatch):
    """transitionStartRule and transitionEndRule must be None when OSB rules
    are absent (skip-rather-than-blank)."""
    element = MagicMock()
    element.element_uid = "Element_002"
    element.name = "Screening"
    element.description = None
    element.start_rule = None
    element.end_rule = None

    fake_result = MagicMock()
    fake_result.items = [element]
    monkeypatch.setattr(ddf_mapper, "_get_osb_study_elements", lambda uid: fake_result)

    fake_study = SimpleNamespace(uid="Study_TEST")
    elements = ddf_mapper._get_study_elements(fake_study)

    assert elements[0].transitionStartRule is None
    assert elements[0].transitionEndRule is None


def test_study_element_name_carries_osb_name(ddf_mapper, monkeypatch):
    """StudyElement.name must carry the human-readable OSB element name,
    not the generated ID string."""
    element = MagicMock()
    element.element_uid = "Element_003"
    element.name = "Run-in Period"
    element.description = None
    element.start_rule = None
    element.end_rule = None

    fake_result = MagicMock()
    fake_result.items = [element]
    monkeypatch.setattr(ddf_mapper, "_get_osb_study_elements", lambda uid: fake_result)

    fake_study = SimpleNamespace(uid="Study_TEST")
    elements = ddf_mapper._get_study_elements(fake_study)

    assert elements[0].name == "Run-in Period"
    # id should be the generated ID, not the human name
    assert elements[0].id != "Run-in Period"


# ---------------------------------------------------------------------------
# ADO 254079: administrations + procedure description/code
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def study_compound_dosing_data(tst_study, study_elements):
    """Seed one compound dosing so _get_study_interventions builds an Administration.

    Creates: compound → compound_alias → medicinal_product → study_compound →
    study_element → study_compound_dosing.  Returns a dict with the seeded
    objects so tests can assert against expected values."""
    compound = TestUtils.create_compound(name="Compound-DDF-Test", approve=True)
    compound_alias = TestUtils.create_compound_alias(
        name="CompoundAlias-DDF-Test",
        compound_uid=compound.uid,
        approve=True,
    )
    # Pharmaceutical product and medicinal product are required by
    # StudySelectionCompoundCreateInput.medicinal_product_uid (non-nullable str).
    # The dose value uid must also be registered on the medicinal product.
    # Use a unit definition without CT linkage here; the test for CT code resolution
    # uses monkeypatch to inject _get_ct_term_uid_for_unit_definition directly.
    dose_value = TestUtils.create_numeric_value_with_unit(
        value=100.0,
        unit="mg",
    )
    pharmaceutical_product = TestUtils.create_pharmaceutical_product(approve=True)
    medicinal_product = TestUtils.create_medicinal_product(
        compound_uid=compound.uid,
        pharmaceutical_product_uids=[pharmaceutical_product.uid],
        dose_value_uids=[dose_value.uid],
        approve=True,
    )
    # study_elements fixture creates 5 elements (no planned_duration).
    # Use the first one; duration-absent behaviour is tested via monkeypatch in
    # test_administration_duration_emitted_when_no_planned_duration.
    study_element = study_elements[0]

    study_compound = TestUtils.create_study_compound(
        study_uid=tst_study.uid,
        compound_alias_uid=compound_alias.uid,
        medicinal_product_uid=medicinal_product.uid,
    )

    dosing = TestUtils.create_study_compound_dosing(
        study_uid=tst_study.uid,
        study_compound_uid=study_compound.study_compound_uid,
        study_element_uid=study_element.element_uid,
        dose_value_uid=dose_value.uid,
    )

    return {
        "compound": compound,
        "compound_alias": compound_alias,
        "medicinal_product": medicinal_product,
        "study_compound": study_compound,
        "study_element": study_element,
        "dose_value": dose_value,
        "dosing": dosing,
    }


def test_administrations_one_per_dosing(
    ddf_mapper, tst_study, study_compound_dosing_data, monkeypatch
):
    """Case 1: seeded compound dosing produces exactly one Administration.

    Both _get_ct_term_uid_for_unit_definition and get_ct_package_term_as_usdm_code
    are monkeypatched so we can assert the full wiring chain:
      unit_definition_uid -> _get_ct_term_uid_for_unit_definition
                          -> get_ct_package_term_as_usdm_code
                          -> Administration.dose.unit.standardCode.code
    without depending on the test DB containing a specific CT graph."""
    expected_ct_uid = "C28253"  # Milligram — canonical CDISC unit code for mg
    resolved_code = USDMCode(
        id="Code_C28253",
        code=expected_ct_uid,
        codeSystem="CDISC",
        codeSystemVersion="2024",
        decode="Milligram",
        instanceType="Code",
    )
    monkeypatch.setattr(
        ddf_mapper,
        "_get_ct_term_uid_for_unit_definition",
        lambda uid: expected_ct_uid,
    )
    monkeypatch.setattr(
        ddf_mapper,
        "get_ct_package_term_as_usdm_code",
        lambda concept_id: resolved_code,
    )

    interventions = ddf_mapper._get_study_interventions(tst_study)

    assert len(interventions) == 1
    admins = interventions[0].administrations
    assert len(admins) >= 1, "Expected at least one Administration from seeded dosing"

    # Find the one we seeded (may be more if other tests also seed dosings)
    dosing_uid = study_compound_dosing_data["dosing"].study_compound_dosing_uid
    admin = next(
        (
            a
            for a in admins
            if ddf_mapper._id_manager.get_id(USDMAdministration.__name__, dosing_uid)
            == a.id
        ),
        None,
    )
    assert admin is not None, f"Administration for dosing {dosing_uid} not found"
    assert isinstance(admin, USDMAdministration)
    assert admin.instanceType == "Administration"

    # dose: value=100; unit code must carry the expected CT uid, proving the full
    # chain: unit_definition_uid -> helper -> get_ct_package_term_as_usdm_code.
    assert admin.dose is not None
    assert admin.dose.value == 100.0
    assert admin.dose.unit is not None
    assert admin.dose.unit.standardCode.code == expected_ct_uid

    # duration must be present and durationWillVary=False
    assert admin.duration is not None
    assert admin.duration.durationWillVary is False


def test_administrations_empty_when_no_dosings(ddf_mapper, tst_study, monkeypatch):
    """Case 2: a study with no compound dosings produces administrations=[]."""
    fake_result = MagicMock()
    fake_result.items = []
    monkeypatch.setattr(
        ddf_mapper,
        "_get_osb_study_compound_dosings",
        lambda **kwargs: fake_result,
    )

    interventions = ddf_mapper._get_study_interventions(tst_study)
    assert interventions[0].administrations == []


def test_administration_duration_emitted_when_no_planned_duration(
    ddf_mapper, tst_study, monkeypatch
):
    """Case 3: dosing whose element has no planned_duration still produces an
    Administration with durationWillVary=False and no invented quantity."""
    dosing = MagicMock()
    dosing.study_compound_dosing_uid = "Dosing_NoDuration"
    dosing.dose_value = None
    dosing.dose_frequency = None
    dosing.study_compound.compound_uid = "Compound_NoDuration"
    dosing.study_element.planned_duration = None

    fake_result = MagicMock()
    fake_result.items = [dosing]
    monkeypatch.setattr(
        ddf_mapper,
        "_get_osb_study_compound_dosings",
        lambda **kwargs: fake_result,
    )

    interventions = ddf_mapper._get_study_interventions(tst_study)
    admins = interventions[0].administrations
    assert len(admins) == 1
    admin = admins[0]
    assert admin.duration is not None
    assert admin.duration.durationWillVary is False
    assert admin.duration.quantity is None


def test_administration_dose_unit_falls_back_to_void_when_no_ct_linkage(
    ddf_mapper, tst_study, monkeypatch
):
    """Dose unit with no HAS_CT_UNIT linkage must fall back to void code (code='').
    Units genuinely without CT linkage (e.g. UnitDefinition_000415 in live DB) are
    real — the mapper must not crash and must not invent a code."""
    dose_value_mock = MagicMock()
    # unit_definition_uid points to a unit with no CT linkage (mocked via monkeypatch)
    dose_value_mock.unit_definition_uid = "UnitDefinition_NO_CT"
    dose_value_mock.value = 50.0

    dosing = MagicMock()
    dosing.study_compound_dosing_uid = "Dosing_NoCtUnit"
    dosing.dose_value = dose_value_mock
    dosing.dose_frequency = None
    dosing.study_compound.compound_uid = "Compound_NoCtUnit"
    dosing.study_element.planned_duration = None

    fake_result = MagicMock()
    fake_result.items = [dosing]
    monkeypatch.setattr(
        ddf_mapper,
        "_get_osb_study_compound_dosings",
        lambda **kwargs: fake_result,
    )
    # _get_ct_term_uid_for_unit_definition returns None for unknown uid
    monkeypatch.setattr(
        ddf_mapper,
        "_get_ct_term_uid_for_unit_definition",
        lambda uid: None,
    )

    interventions = ddf_mapper._get_study_interventions(tst_study)
    admins = interventions[0].administrations
    assert len(admins) == 1
    admin = admins[0]
    assert admin.dose is not None
    assert admin.dose.value == 50.0
    # void code fallback: code=""
    assert admin.dose.unit.standardCode.code == ""


def test_procedure_description_from_activity_definition(ddf_mapper, tst_study):
    """Case 4a: when an activity has a definition, Procedure.description is populated."""
    activity_group = TestUtils.create_activity_group(name="ProcDescGroup")
    activity_subgroup = TestUtils.create_activity_subgroup(name="ProcDescSubGroup")
    activity_with_def = TestUtils.create_activity(
        name="ActivityWithDef",
        definition="Measure systolic blood pressure with standard cuff.",
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
    )
    sa = TestUtils.create_study_activity(
        study_uid=tst_study.uid,
        activity_uid=activity_with_def.uid,
        activity_subgroup_uid=activity_subgroup.uid,
        activity_group_uid=activity_group.uid,
        soa_group_term_uid="term_efficacy_uid",
    )

    ddf_activities = ddf_mapper._get_study_activities(tst_study)
    matched = next(
        (
            a
            for a in ddf_activities
            if a.id == ddf_mapper._id_manager.get_id("Activity", sa.study_activity_uid)
        ),
        None,
    )
    assert matched is not None
    assert len(matched.definedProcedures) == 1
    procedure = matched.definedProcedures[0]
    assert isinstance(procedure, USDMProcedure)
    assert (
        procedure.description == "Measure systolic blood pressure with standard cuff."
    )


def test_procedure_description_none_when_no_definition(ddf_mapper, tst_study):
    """Case 4b: when an activity has no definition, Procedure.description is None."""
    activity_group = TestUtils.create_activity_group(name="ProcNoDefGroup")
    activity_subgroup = TestUtils.create_activity_subgroup(name="ProcNoDefSubGroup")
    activity_no_def = TestUtils.create_activity(
        name="ActivityNoDef",
        definition=None,
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
    )
    sa = TestUtils.create_study_activity(
        study_uid=tst_study.uid,
        activity_uid=activity_no_def.uid,
        activity_subgroup_uid=activity_subgroup.uid,
        activity_group_uid=activity_group.uid,
        soa_group_term_uid="term_efficacy_uid",
    )

    ddf_activities = ddf_mapper._get_study_activities(tst_study)
    matched = next(
        (
            a
            for a in ddf_activities
            if a.id == ddf_mapper._id_manager.get_id("Activity", sa.study_activity_uid)
        ),
        None,
    )
    assert matched is not None
    assert len(matched.definedProcedures) == 1
    assert matched.definedProcedures[0].description is None


def test_procedure_code_uses_nci_concept_id_when_present(
    ddf_mapper, tst_study, monkeypatch
):
    """Case 5a: when activity.nci_concept_id is set, Procedure.code.code matches it."""
    fake_code = USDMCode(
        id="Code_NCI_TEST",
        code="C99001",
        codeSystem="CDISC",
        codeSystemVersion="2024",
        decode="Test Procedure",
    )

    activity = MagicMock()
    activity.uid = "Activity_NCI_TEST"
    activity.name = "NCI Test Activity"
    activity.definition = None
    activity.nci_concept_id = "C99001"

    sa = MagicMock()
    sa.study_activity_uid = "StudyActivity_NCI_TEST"
    sa.activity = activity
    sa.study_activity_subgroup = None
    sa.study_soa_group = None
    sa.study_activity_group = None
    sa.order = 999

    fake_sas = MagicMock()
    fake_sas.items = [sa]

    with (
        patch.object(ddf_mapper, "_get_osb_study_activities", return_value=fake_sas),
        patch.object(
            ddf_mapper, "get_ct_package_term_as_usdm_code", return_value=fake_code
        ),
    ):
        ddf_activities = ddf_mapper._get_study_activities(tst_study)

    assert len(ddf_activities) == 1
    procedure = ddf_activities[0].definedProcedures[0]
    assert procedure.code.code == "C99001"


def test_procedure_code_void_when_no_nci_concept_id(ddf_mapper, tst_study, monkeypatch):
    """Case 5b: when activity.nci_concept_id is absent, Procedure.code is the void code."""
    activity = MagicMock()
    activity.uid = "Activity_NO_NCI"
    activity.name = "No NCI Activity"
    activity.definition = None
    activity.nci_concept_id = None

    sa = MagicMock()
    sa.study_activity_uid = "StudyActivity_NO_NCI"
    sa.activity = activity
    sa.study_activity_subgroup = None
    sa.study_soa_group = None
    sa.study_activity_group = None
    sa.order = 998

    fake_sas = MagicMock()
    fake_sas.items = [sa]

    with patch.object(ddf_mapper, "_get_osb_study_activities", return_value=fake_sas):
        ddf_activities = ddf_mapper._get_study_activities(tst_study)

    assert len(ddf_activities) == 1
    procedure = ddf_activities[0].definedProcedures[0]
    # void code has code=""
    assert procedure.code.code == ""
