import datetime

import pytest

from clinical_mdr_api.domains.study_selections.study_selection_endpoint import (
    EndpointUnitItem,
    EndpointUnits,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCodelistTermModel,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionEndpoint,
    StudySelectionObjective,
)
from clinical_mdr_api.models.syntax_instances.endpoint import Endpoint
from clinical_mdr_api.models.syntax_instances.objective import Objective
from clinical_mdr_api.models.syntax_instances.timeframe import Timeframe
from clinical_mdr_api.services.studies.study_objectives import StudyObjectivesService

AUTHOR_USERNAME = "unknown-user"
STUDY_UID = "Study_000001"

DATETIME_799 = datetime.datetime(2022, 9, 14, 15, 43, 32, 610799)
DATETIME_811 = datetime.datetime(2022, 9, 14, 15, 43, 32, 561811)
DATETIME_874 = datetime.datetime(2022, 9, 14, 15, 28, 16, 236874)
DATETIME_668 = datetime.datetime(2022, 9, 14, 15, 41, 34, 287668)

TERM_PRI_OBJ = SimpleCodelistTermModel(
    term_uid="C85826",
    term_name="Primary Objective",
    codelist_uid="CTCodelist_123456",
    codelist_name="Objective Level",
    codelist_submission_value="OBJLEVL",
    submission_value="OBJPRIM",
    order=1,
)
TERM_PRI_END = SimpleCodelistTermModel(
    term_uid="C98772",
    term_name="Primary Endpoint",
    codelist_uid="CTCodelist_234567",
    codelist_name="Enedpoint Level",
    codelist_submission_value="ENDPLEVL",
    submission_value="OUTMSPRI",
    order=1,
)
TERM_SEC_END = SimpleCodelistTermModel(
    term_uid="C98781",
    term_name="Secondary Endpoint",
    codelist_uid="CTCodelist_234567",
    codelist_name="Enedpoint Level",
    codelist_submission_value="ENDPLEVL",
    submission_value="OUTMSSEC",
    order=2,
)
TERM_PRI_SUBEND = SimpleCodelistTermModel(
    term_uid="CTTerm_000053",
    term_name="Primary",
    codelist_uid="CTCodelist_345678",
    codelist_name="Endpoint Subevel",
    codelist_submission_value="ENDPSBLV",
    submission_value="PRIMARY ENDPOINT SUB LEVEL",
    order=1,
)

TIMEFRAME_1 = Timeframe(
    uid="Timeframe_000001",
    name="<p>Time Frame: through study completion, an average of 2 year</p>",
    name_plain="Time Frame: through study completion, an average of 2 year",
)
TIMEFRAME_2 = Timeframe(
    uid="Timeframe_000002",
    name="test 25-Hydroxyvitamin D",
    name_plain="test 25-Hydroxyvitamin D",
)

ENDPOINT_4 = Endpoint(
    uid="Endpoint_000004",
    name="<p>Disease control rate of Drug A</p>",
    name_plain="Disease control rate of Drug A",
)
ENDPOINT_3 = Endpoint(
    uid="Endpoint_000003",
    name="<p>Mean Change from Baseline in 25-Hydroxyvitamin D</p>",
    name_plain="Mean Change from Baseline in 25-Hydroxyvitamin D",
)

ENDPOINT_UNITS_ = EndpointUnits(units=tuple(), separator=None)
ENDPOINT_UNITS_2 = EndpointUnits(
    units=(EndpointUnitItem(uid="UnitDefinition_000002", name="Unit2"),), separator=None
)
ENDPOINT_UNITS_6 = EndpointUnits(
    units=(
        EndpointUnitItem(uid="UnitDefinition_000006", name="Unit6"),
        EndpointUnitItem(uid="UnitDefinition_0000011", name="Unit11"),
    ),
    separator="and",
)

OBJECTIVE_3 = Objective(
    uid="Objective_000003",
    name="To compare the effect of Drug A",
    name_plain="To compare the effect of Drug A",
)

STUDY_OBJECTIVE_3 = StudySelectionObjective(
    study_uid=STUDY_UID,
    order=1,
    study_objective_uid="StudyObjective_000003",
    objective_level=TERM_PRI_OBJ,
    objective=OBJECTIVE_3,
    start_date=DATETIME_874,
    author_username=AUTHOR_USERNAME,
    latest_objective=None,
)

STUDY_OBJECTIVES = (STUDY_OBJECTIVE_3,)

STUDY_ENDPOINT_1 = StudySelectionEndpoint(
    study_uid=STUDY_UID,
    order=3,
    study_endpoint_uid="StudyEndpoint_000001",
    study_objective=None,
    endpoint_level=None,
    endpoint_sublevel=None,
    endpoint_units=ENDPOINT_UNITS_,
    endpoint=None,
    timeframe=None,
    start_date=DATETIME_799,
    author_username=AUTHOR_USERNAME,
)
STUDY_ENDPOINT_20 = StudySelectionEndpoint(
    study_uid=STUDY_UID,
    order=2,
    study_endpoint_uid="StudyEndpoint_000020",
    study_objective=STUDY_OBJECTIVE_3,
    endpoint_level=TERM_SEC_END,
    endpoint_sublevel=None,
    endpoint_units=ENDPOINT_UNITS_6,
    endpoint=ENDPOINT_4,
    timeframe=TIMEFRAME_2,
    start_date=DATETIME_811,
    author_username=AUTHOR_USERNAME,
)
STUDY_ENDPOINT_17 = StudySelectionEndpoint(
    study_uid=STUDY_UID,
    order=1,
    study_endpoint_uid="StudyEndpoint_000017",
    study_objective=STUDY_OBJECTIVE_3,
    endpoint_level=TERM_PRI_END,
    endpoint_sublevel=TERM_PRI_SUBEND,
    endpoint_units=ENDPOINT_UNITS_2,
    endpoint=ENDPOINT_3,
    timeframe=TIMEFRAME_1,
    start_date=DATETIME_668,
    author_username=AUTHOR_USERNAME,
)

STUDY_ENDPOINTS = (
    STUDY_ENDPOINT_1,
    STUDY_ENDPOINT_20,
    STUDY_ENDPOINT_17,
)

STANDARD_TREE = {
    "C85826": (
        TERM_PRI_OBJ,
        {
            "StudyObjective_000003": (
                STUDY_OBJECTIVE_3,
                {
                    "C98781": (
                        TERM_SEC_END,
                        {"StudyEndpoint_000020": STUDY_ENDPOINT_20},
                    ),
                    "CTTerm_000053": (
                        TERM_PRI_SUBEND,
                        {"StudyEndpoint_000017": STUDY_ENDPOINT_17},
                    ),
                },
            )
        },
    )
}

CONDENSED_TREE = {
    "C85826": (
        TERM_PRI_OBJ,
        {"StudyObjective_000003": STUDY_OBJECTIVE_3},
        {
            "CTTerm_000053": (
                TERM_PRI_SUBEND,
                {"StudyEndpoint_000017": STUDY_ENDPOINT_17},
            ),
            "C98781": (
                TERM_SEC_END,
                {"StudyEndpoint_000020": STUDY_ENDPOINT_20},
            ),
        },
    )
}


# pylint: disable=redefined-outer-name
@pytest.fixture(scope="module")
def study_objectives_service():
    service = StudyObjectivesService()
    return service


def test_build_standard_tree(study_objectives_service):
    tree = study_objectives_service._build_tree(STUDY_ENDPOINTS)
    assert tree == STANDARD_TREE


def test_build_condensed_tree(study_objectives_service):
    tree = study_objectives_service._build_condensed_tree(STUDY_ENDPOINTS)
    assert tree == CONDENSED_TREE


def test_build_condensed_html(study_objectives_service):
    doc = study_objectives_service._build_condensed_html(CONDENSED_TREE)

    # Check that document is HTML and has table data (not only headers)
    assert "</body>" in doc, "document has no </body>"
    assert "</td>" in doc, "document has no </td>"

    # Search for objective text in document
    for objective in STUDY_OBJECTIVES:
        assert (
            objective.objective_level.term_name in doc
        ), f'objective level "{objective.objective_level.term_name}" was not found in document'
        assert (
            objective.objective.name_plain in doc
        ), f'objective "{objective.objective.name_plain}" was not found in document'

    assert_patterns_in_document(doc)


def test_build_standard_html(study_objectives_service):
    doc = study_objectives_service._build_standard_html(STANDARD_TREE)

    # Check that document is HTML and has table data (not only headers)
    assert "</body>" in doc, "document has no </body>"
    assert "</td>" in doc, "document has no </td>"

    # Search for objective text in document
    for objective in STUDY_OBJECTIVES:
        assert (
            objective.objective_level.term_name in doc
        ), f'objective level "{objective.objective_level.term_name}" was not found in document'
        assert (
            objective.objective.name_plain in doc
        ), f'objective "{objective.objective.name_plain}" was not found in document'

    assert_patterns_in_document(doc)


def test_build_condensed_docx(study_objectives_service):
    docx = study_objectives_service._build_condensed_docx(CONDENSED_TREE).document

    assert len(docx.tables) == 1, "expected exactly 1 table in DOCX document"

    table = docx.tables[0]
    assert len(table.columns) == 2, "expected 2 columns of table"
    assert len(table.rows) == 2, "expected 2 rows of table"

    # extract all text from the table
    doc = "\n".join([cell.text for row in table.rows for cell in row.cells])

    assert_patterns_in_document(doc)


def test_build_standard_docx(study_objectives_service):
    docx = study_objectives_service._build_standard_docx(STANDARD_TREE).document

    assert len(docx.tables) == 1, "expected exactly 1 table in DOCX document"

    table = docx.tables[0]
    assert len(table.columns) == 4, "expected 4 columns of table"
    assert len(table.rows) == 6, "expected 6 rows of table"

    # extract all text from the table
    doc = "\n".join([cell.text for row in table.rows for cell in row.cells])

    assert_patterns_in_document(doc)


def assert_patterns_in_document(doc: str):
    # Search for objective text in document
    for objective in STUDY_OBJECTIVES:
        assert (
            objective.objective_level.term_name in doc
        ), f'objective level "{objective.objective_level.term_name}" was not found in document'
        assert objective.objective.name_plain is not None
        assert (
            objective.objective.name_plain in doc
        ), f'objective "{objective.objective.name_plain}" was not found in document'

    # Search for endpoints text in document
    for endpoint in STUDY_ENDPOINTS:
        if not endpoint.endpoint:
            continue
        if endpoint.endpoint_sublevel:
            assert (
                endpoint.endpoint_sublevel.term_name in doc
            ), f'endpoint sub-level "{endpoint.endpoint_sublevel.term_name}" was not found in document'
        elif endpoint.endpoint_level:
            assert (
                endpoint.endpoint_level.term_name in doc
            ), f'endpoint level "{endpoint.endpoint_level.term_name}" was not found in document'
        assert endpoint.endpoint.name_plain is not None
        assert endpoint.endpoint.name_plain in doc
