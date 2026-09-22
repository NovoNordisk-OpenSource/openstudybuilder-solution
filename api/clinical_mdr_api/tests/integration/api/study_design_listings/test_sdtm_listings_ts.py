"""
Tests for /listings/studies/all/adam/ endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import (
    CTTermNameTSParameterInput,
)
from clinical_mdr_api.models.listings.listings_sdtm import StudySummaryListing
from clinical_mdr_api.services.controlled_terminologies.ct_term_name import (
    CTTermNameService,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    create_reason_for_lock_unlock_terms,
    fix_study_preferred_time_unit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_arm,
    create_study_branch_arm,
    create_study_cohort,
    create_study_design_cell,
    create_study_element,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    edit_study_epoch,
    generate_study_root,
    get_catalogue_name_library_name,
    patch_study_branch_arm,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

study_uid: str
reason_for_lock_term_uid: str
reason_for_unlock_term_uid: str

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def api_client(test_data: None):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    global study_uid, reason_for_lock_term_uid, reason_for_unlock_term_uid
    study_uid = "study_root"
    inject_and_clear_db("SDTMTSListingTest.api")
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    TestUtils.create_library(name="UCUM", is_editable=True)
    study = generate_study_root()
    lock_unlock_data = create_reason_for_lock_unlock_terms()
    reason_for_lock_term_uid = lock_unlock_data["reason_for_lock_terms"][0].term_uid
    reason_for_unlock_term_uid = lock_unlock_data["reason_for_unlock_terms"][0].term_uid
    # Create an epoch
    create_study_epoch_codelists_ret_cat_and_lib()
    _catalogue_name, library_name = get_catalogue_name_library_name()
    catalogue_name = "SDTM CT"
    study_epoch = create_study_epoch("EpochSubType_0001")
    study_epoch2 = create_study_epoch("EpochSubType_0001")
    # Create a study element
    element_type_codelist = create_codelist(
        "Element Type",
        "CTCodelist_ElementType",
        catalogue_name,
        library_name,
        submission_value="ELEMSTP",
    )
    element_type_term = create_ct_term(
        "Element Type",
        "ElementType_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": element_type_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Element Type",
            },
        ],
    )
    element_type_term_2 = create_ct_term(
        "Element Type 2",
        "ElementType_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": element_type_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Element Type2",
            },
        ],
    )
    study_elements = [
        create_study_element(element_type_term.uid, study.uid),
        create_study_element(element_type_term_2.uid, study.uid),
    ]

    codelist = create_codelist(
        name="Arm Type",
        uid="CTCodelist_00004",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="ARMTTP",
    )
    arm_type = create_ct_term(
        name="Arm Type",
        uid="ArmType_0001",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "Arm Type",
            },
        ],
    )

    create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_1",
        short_name="Arm_Short_Name_1",
        code="Arm_code_1",
        description="desc...",
        randomization_group="Arm_randomizationGroup",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )
    create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_2",
        short_name="Arm_Short_Name_2",
        code="Arm_code_2",
        description="desc...",
        randomization_group="Arm_randomizationGroup2",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )
    create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_3",
        short_name="Arm_Short_Name_3",
        code="Arm_code_3",
        description="desc...",
        randomization_group="Arm_randomizationGroup3",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )

    create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_9",
        short_name="Arm_Short_Name_9",
        code="Arm_code_9",
        description="desc...",
        randomization_group="Arm_randomizationGroup9",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )

    create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch.uid,
        study_arm_uid="StudyArm_000002",
        study_uid=study.uid,
    )
    create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid="StudyArm_000002",
        study_uid=study.uid,
    )

    create_study_design_cell(
        study_element_uid=study_elements[1].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid="StudyArm_000001",
        study_uid=study.uid,
    )

    branch_arm = create_study_branch_arm(
        study_uid=study.uid,
        name="Branch_Arm_Name_1",
        short_name="Branch_Arm_Short_Name_1",
        code="Branch_Arm_code_1",
        description="desc...",
        randomization_group="Branch_Arm_randomizationGroup",
        number_of_subjects=100,
        arm_uid="StudyArm_000002",
    )
    branch_arm = patch_study_branch_arm(
        branch_arm_uid=branch_arm.branch_arm_uid, study_uid=study.uid
    )

    create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid="StudyArm_000003",
        study_uid=study.uid,
    )

    create_study_cohort(
        study_uid=study.uid,
        name="Cohort_Name_1",
        short_name="Cohort_Short_Name_1",
        code="Cohort_code_1",
        description="desc...",
        number_of_subjects=100,
        arm_uids=["StudyArm_000001"],
    )
    # edit an epoch to track if the relationships have been updated
    edit_study_epoch(epoch_uid=study_epoch2.uid)

    code_codelist = create_codelist(
        name="Trial Summary Parameter Test Code",
        uid="C66738",
        catalogue=catalogue_name,
        library=library_name,
    )
    name_codelist = create_codelist(
        name="Trial Summary Parameter Test Name",
        uid="C67152",
        catalogue=catalogue_name,
        library=library_name,
        paired_code_codelist_uid="C66738",
    )

    _narms = create_ct_term(
        name="C98771",
        uid="C98771",
        preferred_term="Planned Number of Arms",
        definition="The planned number of intervention groups.",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": code_codelist.codelist_uid,
                "order": 1,
                "submission_value": "NARMS",
            },
            {
                "uid": name_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Planned Number of Arms",
            },
        ],
    )

    _ncohorts = create_ct_term(
        name="C126063",
        uid="C126063",
        preferred_term="Number of Groups or Cohorts",
        definition="The number of groups or cohorts that are part of the study.",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": code_codelist.codelist_uid,
                "order": 1,
                "submission_value": "NCOHORT",
            },
            {
                "uid": name_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Number of Groups/Cohorts",
            },
        ],
    )
    # Creating library and catalogue for study standard version
    TestUtils.create_library(name=settings.cdisc_library_name, is_editable=True)
    TestUtils.create_ct_catalogue(
        library=settings.cdisc_library_name,
        catalogue_name=settings.sdtm_ct_catalogue_name,
    )
    TestUtils.create_ct_catalogue(
        library=settings.cdisc_library_name,
        catalogue_name=settings.ddf_ct_catalogue_name,
    )
    TestUtils.create_ct_codelists_using_cypher()
    TestUtils.create_study_fields_ct_data()
    TestUtils.set_study_standard_version(study_uid=study.uid)
    fix_study_preferred_time_unit(study_uid=study.uid)

    # --- Field-based TS parameters (test Block 1 of get_ts) ---
    # Create CT terms for TS parameters and link them to study fields
    # and linked to study fields via RELATED_STUDY_FIELD_SELECTION.

    # SHORTTL - plain text field, no reference
    _shorttl = create_ct_term(
        name="Study Short Title",
        uid="C99079",
        preferred_term="Study Short Title",
        definition="A short title for the study.",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": code_codelist.codelist_uid,
                "order": 1,
                "submission_value": "SHORTTL",
            },
            {
                "uid": name_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Study Short Title",
            },
        ],
    )

    # REGID - registry identifier fields produce one row per filled field via the
    # dedicated REGID Cypher block (branch 2). TSVCDREF is driven by
    # FieldConfiguration.registry_identifier_vcdref_map(), not tsp.reference.
    _regid = create_ct_term(
        name="Registry Identifier",
        uid="C98783",
        preferred_term="Registry Identifier",
        definition="An identifier from a clinical trial registry.",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": code_codelist.codelist_uid,
                "order": 1,
                "submission_value": "REGID",
            },
            {
                "uid": name_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Registry Identifier",
            },
        ],
    )

    # PHASE - CT term field (tests CT term resolution: ctnv.name → TSVAL, concept_id → TSVALCD)
    _phase = create_ct_term(
        name="Trial Phase",
        uid="C98770",
        preferred_term="Trial Phase",
        definition="The phase of the clinical study.",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": code_codelist.codelist_uid,
                "order": 1,
                "submission_value": "PHASE",
            },
            {
                "uid": name_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Trial Phase",
            },
        ],
    )

    # Create the actual phase value CT term that will be selected on the study field
    phase_codelist = create_codelist(
        name="Trial Phase",
        uid="CTCodelist_Phase",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="TPHASE",
    )
    _phase_value_term = create_ct_term(
        name="Phase I Trial",
        uid="C15600",
        preferred_term="Phase I Trial",
        definition="Phase I clinical trial.",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": phase_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Phase I Trial",
            },
            {"uid": "C66737", "order": 1, "submission_value": "Phase I Trial"},
        ],
    )
    # Set concept_id on the phase term attributes (create_ct_term defaults concept_id to None)
    db.cypher_query("""
        MATCH (tr:CTTermRoot {uid: 'C15600'})-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
        SET tav.concept_id = 'C15600'
        """)

    # RANDFL - boolean field (tests boolean → CT term: Yes/No name, concept_id)
    _randfl = create_ct_term(
        name="Trial is Randomized",
        uid="C98767",
        preferred_term="Trial is Randomized",
        definition="An indicator of whether the trial uses randomization.",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": code_codelist.codelist_uid,
                "order": 1,
                "submission_value": "RANDFL",
            },
            {
                "uid": name_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Trial is Randomized",
            },
        ],
    )

    # Create Yes/No CT terms for boolean value resolution
    bool_codelist = create_codelist(
        name="No Yes Response",
        uid="C66742",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="NY",
    )
    _yes_term = create_ct_term(
        name="Yes",
        uid="C49488",
        preferred_term="Yes",
        definition="The affirmative response.",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {"uid": bool_codelist.codelist_uid, "order": 1, "submission_value": "Y"},
        ],
    )
    # Set concept_id on the Yes term attributes
    db.cypher_query("""
        MATCH (tr:CTTermRoot {uid: 'C49488'})-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
        SET tav.concept_id = 'C49488'
        """)

    # PLANSUB - integer field (tests sf:StudyIntField → sf.value as TSVAL)
    _plansub = create_ct_term(
        name="Planned Number of Subjects",
        uid="C49695",
        preferred_term="Planned Number of Subjects",
        definition="The intended number of subjects to be enrolled.",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": code_codelist.codelist_uid,
                "order": 1,
                "submission_value": "PLANSUB",
            },
            {
                "uid": name_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Planned Number of Subjects",
            },
        ],
    )

    # SSTDTC - time field (tests sf:StudyTimeField → TSVCDREF='ISO8601')
    _sstdtc = create_ct_term(
        name="Study Start Date",
        uid="C99158",
        preferred_term="Study Start Date",
        definition="The date the study started.",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": code_codelist.codelist_uid,
                "order": 1,
                "submission_value": "SSTDTC",
            },
            {
                "uid": name_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Study Start Date",
            },
        ],
    )

    # STYPE - CT codelist single-select field (tests CTCodelist → CTTerm resolution for study_type_code)
    _stype = create_ct_term(
        name="Study Type",
        uid="C142175",
        preferred_term="Study Type",
        definition="The type of the clinical study.",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": code_codelist.codelist_uid,
                "order": 1,
                "submission_value": "STYPE",
            },
            {
                "uid": name_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Study Type",
            },
        ],
    )

    # Create the actual study type value term in the existing C99077 codelist
    _study_type_value = create_ct_term(
        name="Interventional Study",
        uid="C98388",
        preferred_term="Interventional Study",
        definition="A study in which participants are assigned to receive interventions.",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {"uid": "C99077", "order": 1, "submission_value": "INTERVENTIONAL"},
        ],
    )
    db.cypher_query("""
        MATCH (tr:CTTermRoot {uid: 'C98388'})-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
        SET tav.concept_id = 'C98388'
        """)

    # DATATYPE codelist — all available data types, used to link MetaStudyField via HAS_SEMANTIC_DATA_TYPE
    data_type_codelist = create_codelist(
        name="Data Type",
        uid="CTCodelist_DataType",
        catalogue=settings.ddf_ct_catalogue_name,
        library=library_name,
        submission_value=settings.data_type_cl_submval,
    )
    _data_type_terms = [
        ("DT_BASE64BINARY", "Base 64 Binary"),
        ("DT_BASE64FLOAT", "Base64 Float"),
        ("DT_BIT", "BIT"),
        ("DT_BOOLEAN", "Boolean"),
        ("DT_COMMENT", "Comment"),
        ("DT_CTTERM", "CTterm"),
        ("DT_DATE", "Date"),
        ("DT_DATETIME", "Date Time"),
        ("DT_DOUBLE", "Double"),
        ("DT_DURATIONDATETIME", "Duration Date Time"),
        ("DT_FLOAT", "Float"),
        ("DT_HEXBINARY", "Hex Binary"),
        ("DT_HEXFLOAT", "hex Float"),
        ("DT_INCOMPLETEDATE", "Incomplete Date"),
        ("DT_INCOMPLETEDATETIME", "Incomplete Date Time"),
        ("DT_INCOMPLETETIME", "Incomplete Time"),
        ("DT_INTEGER", "Integer"),
        ("DT_INTERVALEDATETIME", "Intervale Date Time"),
        ("DT_PARTIALDATE", "Partial Date"),
        ("DT_PARTIALDATETIME", "Partial Date Time"),
        ("DT_PARTIALTIME", "Partial Time"),
        ("DT_SPONSORNAME", "SPONSOR_NAME"),
        ("DT_STRING", "String"),
        ("DT_TEXT", "Text"),
        ("DT_TIME", "Time"),
        ("DT_URI", "URI"),
    ]
    for i, (dt_uid, dt_name) in enumerate(_data_type_terms):
        create_ct_term(
            name=dt_name,
            uid=dt_uid,
            preferred_term=dt_name,
            definition=f"Data type: {dt_name}",
            catalogue_name=catalogue_name,
            library_name=library_name,
            codelists=[
                {
                    "uid": data_type_codelist.codelist_uid,
                    "order": i + 1,
                    "submission_value": dt_name,
                },
            ],
        )

    # INDIC - dictionary multiselect field (tests DictionaryTermRoot → dtv.name/dictionary_id)
    _indic = create_ct_term(
        name="Trial Disease/Condition/Indication",
        uid="C98769",
        preferred_term="Trial Disease/Condition/Indication",
        definition="The disease, condition, or indication studied in the trial.",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": code_codelist.codelist_uid,
                "order": 1,
                "submission_value": "INDIC",
            },
            {
                "uid": name_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Trial Disease/Condition/Indication",
            },
        ],
    )

    # Create dictionary codelist and term for disease_condition_or_indication_codes
    TestUtils.create_library(name="SNOMED", is_editable=True)
    dict_codelist = TestUtils.create_dictionary_codelist(
        name="SNOMED",
        library_name="SNOMED",
        approve=True,
    )
    dict_term = TestUtils.create_dictionary_term(
        codelist_uid=dict_codelist.codelist_uid,
        dictionary_id="25064002",
        name="Headache",
        name_sentence_case="Headache",
        abbreviation="HA",
        definition="Pain in the head.",
        library_name="SNOMED",
        approve=True,
    )

    # Bind TS parameter terms to MetaStudyField via the lightweight service endpoint
    ts_service = CTTermNameService()
    ts_service.patch_trial_summary_parameter(
        "C99079",
        CTTermNameTSParameterInput(
            osb_field_name="study_short_title",
            semantic_data_type_uid="DT_TEXT",
            required_level="Required",
            cardinality="One",
            notes="Short title of the study.",
            osb_page_reference="p.42",
        ),
    )
    ts_service.approve("C99079")
    # C98783 (REGID) is intentionally NOT linked to a MetaStudyField via
    # patch_trial_summary_parameter. Registry identifier rows are produced by the
    # dedicated REGID Cypher block that matches StudyTextField nodes directly;
    # adding a RELATED_STUDY_FIELD_SELECTION would cause the field-based branch to
    # also find C98783 and emit a spurious row with TSVAL=NULL.
    ts_service.patch_trial_summary_parameter(
        "C98770",
        CTTermNameTSParameterInput(
            osb_field_name="trial_phase_code",
            response_codelist_uid="C66737",
            semantic_data_type_uid="DT_CTTERM",
        ),
    )
    ts_service.approve("C98770")
    ts_service.patch_trial_summary_parameter(
        "C98767",
        CTTermNameTSParameterInput(
            osb_field_name="is_trial_randomised", semantic_data_type_uid="DT_BOOLEAN"
        ),
    )
    ts_service.approve("C98767")
    ts_service.patch_trial_summary_parameter(
        "C49695",
        CTTermNameTSParameterInput(
            osb_field_name="number_of_expected_subjects",
            semantic_data_type_uid="DT_INTEGER",
        ),
    )
    ts_service.approve("C49695")
    ts_service.patch_trial_summary_parameter(
        "C99158",
        CTTermNameTSParameterInput(
            osb_field_name="planned_study_length",
            semantic_data_type_uid="DT_DURATIONDATETIME",
        ),
    )
    ts_service.approve("C99158")
    ts_service.patch_trial_summary_parameter(
        "C142175",
        CTTermNameTSParameterInput(
            osb_field_name="study_type_code",
            response_codelist_uid="C99077",
            semantic_data_type_uid="DT_CTTERM",
        ),
    )
    ts_service.approve("C142175")
    ts_service.patch_trial_summary_parameter(
        "C98769",
        CTTermNameTSParameterInput(
            osb_field_name="disease_condition_or_indication_codes",
            response_dictionary_uids=[dict_codelist.codelist_uid],
            semantic_data_type_uid="DT_STRING",
        ),
    )
    ts_service.approve("C98769")

    # Set study field values via PATCH API (creates StudyField nodes with MetaStudyField links)
    day_unit_uid = db.cypher_query(
        "MATCH (u:UnitDefinitionRoot)-[:LATEST]->(v:UnitDefinitionValue {name: $name}) RETURN u.uid",
        {"name": settings.day_unit_name},
    )[0][0][0]
    client = TestClient(app)
    response = client.patch(
        f"/studies/{study_uid}",
        json={
            "current_metadata": {
                "study_description": {"study_short_title": "P1 Safety"},
                "identification_metadata": {
                    "registry_identifiers": {
                        "ct_gov_id": "NCT12345678",
                        "eudract_id": "2021-000001-12",
                        "eu_trial_number": "2021-000001-12-00",
                    }
                },
                "high_level_study_design": {
                    "study_type_code": {"term_uid": "C98388"},
                    "trial_phase_code": {"term_uid": "C15600"},
                },
                "study_intervention": {
                    "is_trial_randomised": True,
                    "planned_study_length": {
                        "duration_value": 14,
                        "duration_unit_code": {"uid": day_unit_uid},
                    },
                },
                "study_population": {
                    "number_of_expected_subjects": 150,
                    "disease_condition_or_indication_codes": [
                        {"term_uid": dict_term.term_uid},
                    ],
                },
            }
        },
    )
    assert_response_status_code(response, 200)


def test_ts_listing(api_client: TestClient):
    response = api_client.get(
        "/listings/studies/study_root/sdtm/ts",
        params={"page_size": 100},
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res is not None

    # STUDYID is derived from project_number + study_number which may change after PATCH
    study_id = res[0]["STUDYID"]

    expected_output = [
        # Disease/Condition/Indication - dictionary field (dtv.name → TSVAL, dictionary_id → TSVALCD, library → TSVCDREF)
        StudySummaryListing(
            DOMAIN="TS",
            STUDYID=study_id,
            TSPARM="Trial Disease/Condition/Indication",
            TSPARMCD="INDIC",
            TSVAL="Headache",
            TSVALCD="25064002",
            TSVALNF="",
            TSVCDREF="SNOMED",
            TSVCDVER="",
        ).model_dump(),
        # Arm count (from design cells) - computed block
        StudySummaryListing(
            DOMAIN="TS",
            STUDYID=study_id,
            TSPARM="Planned Number of Arms",
            TSPARMCD="NARMS",
            TSVAL="3",
            TSVALCD="",
            TSVALNF="",
            TSVCDREF="",
            TSVCDVER="",
        ).model_dump(),
        # Cohort count - computed block
        StudySummaryListing(
            DOMAIN="TS",
            STUDYID=study_id,
            TSPARM="Number of Groups/Cohorts",
            TSPARMCD="NCOHORT",
            TSVAL="1",
            TSVALCD="",
            TSVALNF="",
            TSVCDREF="",
            TSVCDVER="",
        ).model_dump(),
        # Trial Phase - CT term field (ctnv.name → TSVAL, concept_id → TSVALCD, TSVCDREF='CDISC')
        StudySummaryListing(
            DOMAIN="TS",
            STUDYID=study_id,
            TSPARM="Trial Phase",
            TSPARMCD="PHASE",
            TSVAL="Phase I Trial",
            TSVALCD="C15600",
            TSVALNF="",
            TSVCDREF="CDISC",
            TSVCDVER="",
        ).model_dump(),
        # Planned Number of Subjects - integer field (sf.value as plain number)
        StudySummaryListing(
            DOMAIN="TS",
            STUDYID=study_id,
            TSPARM="Planned Number of Subjects",
            TSPARMCD="PLANSUB",
            TSVAL="150",
            TSVALCD="",
            TSVALNF="",
            TSVCDREF="",
            TSVCDVER="",
        ).model_dump(),
        # Trial is Randomized - boolean field (CT term Yes → ctnv.name, concept_id)
        StudySummaryListing(
            DOMAIN="TS",
            STUDYID=study_id,
            TSPARM="Trial is Randomized",
            TSPARMCD="RANDFL",
            TSVAL="Yes",
            TSVALCD="C49488",
            TSVALNF="",
            TSVCDREF="CDISC",
            TSVCDVER="",
        ).model_dump(),
        # Registry identifiers - each filled registry field yields its own REGID row;
        # TSVCDREF is driven by FieldConfiguration.registry_identifier_vcdref_map().
        # The three rows below represent ct_gov_id, eudract_id and eu_trial_number.
        # Note: the ordering of REGID rows in the result is not guaranteed, so the
        # assertion below compares them as a sorted set.
        StudySummaryListing(
            DOMAIN="TS",
            STUDYID=study_id,
            TSPARM="Registry Identifier",
            TSPARMCD="REGID",
            TSVAL="NCT12345678",
            TSVALCD="",
            TSVALNF="",
            TSVCDREF="ClinicalTrials.gov",
            TSVCDVER="",
        ).model_dump(),
        StudySummaryListing(
            DOMAIN="TS",
            STUDYID=study_id,
            TSPARM="Registry Identifier",
            TSPARMCD="REGID",
            TSVAL="2021-000001-12",
            TSVALCD="",
            TSVALNF="",
            TSVCDREF="EUDRACT",
            TSVCDVER="",
        ).model_dump(),
        StudySummaryListing(
            DOMAIN="TS",
            STUDYID=study_id,
            TSPARM="Registry Identifier",
            TSPARMCD="REGID",
            TSVAL="2021-000001-12-00",
            TSVALCD="",
            TSVALNF="",
            TSVCDREF="ETN",
            TSVCDVER="",
        ).model_dump(),
        # Study Short Title - plain text field
        StudySummaryListing(
            DOMAIN="TS",
            STUDYID=study_id,
            TSPARM="Study Short Title",
            TSPARMCD="SHORTTL",
            TSVAL="P1 Safety",
            TSVALCD="",
            TSVALNF="",
            TSVCDREF="",
            TSVCDVER="",
        ).model_dump(),
        # Study Start Date - time field (TSVCDREF='ISO8601')
        StudySummaryListing(
            DOMAIN="TS",
            STUDYID=study_id,
            TSPARM="Study Start Date",
            TSPARMCD="SSTDTC",
            TSVAL="P14D",
            TSVALCD="",
            TSVALNF="",
            TSVCDREF="ISO8601",
            TSVCDVER="",
        ).model_dump(),
        # Study Type - CT codelist single-select (ctnv.name → TSVAL, concept_id → TSVALCD, TSVCDREF='CDISC')
        StudySummaryListing(
            DOMAIN="TS",
            STUDYID=study_id,
            TSPARM="Study Type",
            TSPARMCD="STYPE",
            TSVAL="Interventional Study",
            TSVALCD="C98388",
            TSVALNF="",
            TSVCDREF="CDISC",
            TSVCDVER="",
        ).model_dump(),
    ]

    # Compare as a sorted set using a composite key so that:
    # - REGID row ordering within the same TSPARMCD is not assumed
    # - Numeric TSVAL values (e.g. arm count returned as int) are handled via str()
    def _row_key(r: dict[str, str]) -> tuple[str, str, str]:
        return (r["TSPARMCD"] or "", str(r["TSVAL"] or ""), r["TSVCDREF"] or "")

    assert sorted(res, key=_row_key) == sorted(expected_output, key=_row_key)


def test_ts_listing_versioning(api_client: TestClient):
    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study_uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    # Lock
    response = api_client.post(
        f"/studies/{study_uid}/locks",
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": reason_for_lock_term_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        "/listings/studies/study_root/sdtm/ts",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res is not None
    ts_before_unlock = res

    # Unlock -- Study remain unlocked
    response = api_client.post(
        f"/studies/{study_uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": reason_for_unlock_term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # get all visits
    response = api_client.get(
        f"/studies/{study_uid}/study-arms/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res

    # edit study arm
    response = api_client.delete(
        f"/studies/{study_uid}/study-arms/{old_res[0]['arm_uid']}"
    )
    assert_response_status_code(response, 204)

    # get all study visits of a specific study version
    response = api_client.get(
        f"/listings/studies/{study_uid}/sdtm/ts?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["items"] == ts_before_unlock

    response = api_client.get(
        "/listings/studies/study_root/sdtm/ts",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res[1]["TSVAL"] == "2"
