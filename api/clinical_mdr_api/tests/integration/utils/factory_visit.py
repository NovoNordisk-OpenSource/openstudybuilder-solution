from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionPostInput,
)
from clinical_mdr_api.models.study_selections.study_visit import (
    StudyVisit,
    StudyVisitCreateInput,
    StudyVisitEditInput,
)
from clinical_mdr_api.services.concepts.unit_definitions.unit_definition import (
    UnitDefinitionService,
)
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    create_ct_term,
    get_catalogue_name_library_name,
    get_unit_uid_by_name,
)
from clinical_mdr_api.tests.integration.utils.factory_epoch import (
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
)
from common.config import settings

DAY = {
    "name": "day",
    "library_name": "Sponsor",
    "ct_units": ["unit1-ct-uid"],
    "convertible_unit": True,
    "display_unit": True,
    "master_unit": False,
    "si_unit": True,
    "us_conventional_unit": True,
    "use_complex_unit_conversion": False,
    "unit_dimension": "TIME_UID",
    "legacy_code": "unit1-legacy-code",
    "use_molecular_weight": False,
    "conversion_factor_to_master": settings.day_unit_conversion_factor_to_master,
}

WEEK = {
    "name": "week",
    "library_name": "Sponsor",
    "ct_units": ["unit2-ct-uid"],
    "convertible_unit": True,
    "display_unit": True,
    "master_unit": False,
    "si_unit": False,
    "us_conventional_unit": True,
    "use_complex_unit_conversion": False,
    "unit_dimension": "TIME_UID",
    "legacy_code": "unit2-legacy-code",
    "use_molecular_weight": False,
    "conversion_factor_to_master": settings.week_unit_conversion_factor_to_master,
}


def generate_default_input_data_for_visit():
    day_uid = get_unit_uid_by_name("day")
    week_uid = get_unit_uid_by_name("week")
    return {
        "visit_sublabel_reference": None,
        "show_visit": True,
        "min_visit_window_value": -1,
        "max_visit_window_value": 1,
        "visit_window_unit_uid": day_uid,
        "time_unit_uid": week_uid,
        "time_value": 12,
        "description": "description",
        "start_rule": "start_rule",
        "end_rule": "end_rule",
        "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
        "visit_type": {"term_uid": "VisitType_0003"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "is_global_anchor_visit": False,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
    }


def create_study_visit_codelists(
    create_unit_definitions=True,
    use_test_utils: bool = False,
    create_epoch_codelist: bool = True,
):
    _catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils)
    catalogue_name = settings.sdtm_ct_catalogue_name
    if create_epoch_codelist:
        create_study_epoch_codelists_ret_cat_and_lib(use_test_utils)

    unit_dim_codelist = create_codelist(
        "Unit Dimension",
        "CTCodelist_UnitDim",
        catalogue_name,
        library_name,
        submission_value=settings.unit_dimension_cl_submval,
    )
    create_ct_term(
        "TIME",
        "TIME_UID",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": unit_dim_codelist.codelist_uid,
                "order": 1,
                "submission_value": "TIME",
            }
        ],
    )
    create_ct_term(
        "WEEK",
        "WEEK_UID",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": unit_dim_codelist.codelist_uid,
                "order": 2,
                "submission_value": "WEEK",
            }
        ],
    )

    ct_unit_codelist = create_codelist(
        "CT Unit",
        "CTCodelist_CTUnit",
        catalogue_name,
        library_name,
        submission_value=settings.unit_cl_submval,
    )
    create_ct_term(
        "ct unit 1",
        "unit1-ct-uid",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": ct_unit_codelist.codelist_uid,
                "order": 1,
                "submission_value": "ct unit 1",
            }
        ],
    )
    create_ct_term(
        "ct unit 2",
        "unit2-ct-uid",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": ct_unit_codelist.codelist_uid,
                "order": 2,
                "submission_value": "ct unit 2",
            }
        ],
    )
    if create_unit_definitions:
        unit_service = UnitDefinitionService()
        week_unit = unit_service.create(UnitDefinitionPostInput(**WEEK))  # type: ignore[arg-type]
        unit_service.approve(uid=week_unit.uid)
        day_unit = unit_service.create(UnitDefinitionPostInput(**DAY))  # type: ignore[arg-type]
        unit_service.approve(uid=day_unit.uid)

    codelist = create_codelist(
        "VisitType",
        "CTCodelist_00004",
        catalogue_name,
        library_name,
        submission_value="TIMELB",
    )
    create_ct_term(
        "Information",
        "VisitType_0000",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 0,
                "submission_value": "Information",
            }
        ],
    )
    create_ct_term(
        "BASELINE",
        "VisitType_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 0,
                "submission_value": "BASELINE",
            }
        ],
    )
    create_ct_term(
        "BASELINE2",
        "VisitType_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "BASELINE2",
            }
        ],
    )
    create_ct_term(
        "Visit Type2",
        "VisitType_0003",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 2,
                "submission_value": "Visit Type2",
            }
        ],
    )
    create_ct_term(
        "Visit Type3",
        "VisitType_0004",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 3,
                "submission_value": "Visit Type3",
            }
        ],
    )
    create_ct_term(
        "Early discontinuation",
        "VisitType_0005",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 5,
                "submission_value": "Visit Type5",
            }
        ],
    )
    codelist = create_codelist(
        "Time Point Reference",
        "CTCodelist_00005",
        catalogue_name,
        library_name,
        submission_value="TIMEREF",
    )
    create_ct_term(
        "BASELINE",
        "VisitSubType_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "BASELINE",
            }
        ],
    )
    create_ct_term(
        "BASELINE2",
        "VisitSubType_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 2,
                "submission_value": "BASELINE2",
            }
        ],
    )
    create_ct_term(
        "Visit Sub Type2",
        "VisitSubType_0003",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 3,
                "submission_value": "Visit Sub Type2",
            }
        ],
    )
    create_ct_term(
        "Visit Sub Type3",
        "VisitSubType_0004",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 4,
                "submission_value": "Visit Sub Type3",
            }
        ],
    )
    create_ct_term(
        "Global anchor visit",
        "VisitSubType_0005",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 5,
                "submission_value": "Visit Sub Type4",
            }
        ],
    )

    codelist = create_codelist(
        "Visit Contact Mode",
        "CTCodelist_00007",
        catalogue_name,
        library_name,
        submission_value="VISCNTMD",
    )
    create_ct_term(
        "On Site Visit",
        "VisitContactMode_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "On Site Visit",
            }
        ],
    )
    create_ct_term(
        "Phone Contact",
        "VisitContactMode_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 2,
                "submission_value": "Phone Contact",
            }
        ],
    )
    create_ct_term(
        "Virtual Visit",
        "VisitContactMode_0003",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 3,
                "submission_value": "Virtual Visit",
            }
        ],
    )

    codelist = create_codelist(
        "Epoch Allocation",
        "CTCodelist_00008",
        catalogue_name,
        library_name,
        submission_value="EPCHALLC",
    )
    create_ct_term(
        "Previous Visit",
        "EpochAllocation_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "Previous Visit",
            }
        ],
    )
    create_ct_term(
        "Current Visit",
        "EpochAllocation_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 2,
                "submission_value": "Current Visit",
            }
        ],
    )

    codelist = create_codelist(
        "Repeating Visit Frequency",
        "CTCodelist_Repeating_Visit_Frequency",
        catalogue_name,
        library_name,
        submission_value="REPEATING_VISIT_FREQUENCY",
    )
    create_ct_term(
        "Daily",
        "RepeatingVisitFrequency_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "QD",
            }
        ],
    )
    create_ct_term(
        "Weekly",
        "RepeatingVisitFrequency_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 2,
                "submission_value": "EVERY WEEK",
            }
        ],
    )
    create_ct_term(
        "Monthly",
        "RepeatingVisitFrequency_0003",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 3,
                "submission_value": "QM",
            }
        ],
    )


def create_visit_with_update(study_uid="study_root", **inputs) -> StudyVisit:
    visit_service: StudyVisitService = StudyVisitService(study_uid=study_uid)
    datadict = generate_default_input_data_for_visit().copy()
    datadict.update(inputs)
    visit_input = StudyVisitCreateInput(**datadict)
    visit = visit_service.create(study_uid=study_uid, study_visit_input=visit_input)
    return visit


def update_visit_with_update(
    visit_uid: str, study_uid="study_root", **inputs
) -> StudyVisit:
    visit_service: StudyVisitService = StudyVisitService(study_uid=study_uid)
    datadict = generate_default_input_data_for_visit().copy()
    datadict.update(inputs)
    visit_input = StudyVisitEditInput(**datadict)
    visit = visit_service.edit(
        study_uid=study_uid,
        study_visit_uid=visit_uid,
        study_visit_input=visit_input,
    )
    return visit


def preview_visit_with_update(study_uid, **inputs) -> StudyVisit:
    visit_service: StudyVisitService = StudyVisitService(study_uid=study_uid)
    datadict = generate_default_input_data_for_visit().copy()
    datadict.update(inputs)
    del datadict["visit_window_unit_uid"]
    visit_input = StudyVisitCreateInput(**datadict)
    preview: StudyVisit = visit_service.preview(study_uid, visit_input)
    return preview


def create_some_visits(
    use_test_utils: bool = False,
    create_epoch_codelist: bool = True,
    study_uid="study_root",
    epoch1=None,
    epoch2=None,
):
    if use_test_utils:
        create_study_visit_codelists(
            create_unit_definitions=False,
            use_test_utils=use_test_utils,
            create_epoch_codelist=create_epoch_codelist,
        )
    else:
        create_study_visit_codelists(
            use_test_utils=use_test_utils, create_epoch_codelist=create_epoch_codelist
        )
        epoch1 = create_study_epoch("EpochSubType_0001")
        epoch2 = create_study_epoch("EpochSubType_0002")
    day_uid = get_unit_uid_by_name("day")
    create_visit_with_update(
        study_uid=study_uid,
        study_epoch_uid=epoch1.uid,
        visit_type={"term_uid": "VisitType_0001"},
        time_reference={"term_uid": "VisitSubType_0001"},
        time_value=0,
        time_unit_uid=day_uid,
    )
    create_visit_with_update(
        study_uid=study_uid,
        study_epoch_uid=epoch1.uid,
        visit_type={"term_uid": "VisitType_0003"},
        time_reference={"term_uid": "VisitSubType_0001"},
        time_value=12,
        time_unit_uid=day_uid,
    )
    create_visit_with_update(
        study_uid=study_uid,
        study_epoch_uid=epoch1.uid,
        visit_type={"term_uid": "VisitType_0003"},
        time_reference={"term_uid": "VisitSubType_0001"},
        time_value=10,
        time_unit_uid=day_uid,
    )

    version3 = create_visit_with_update(
        study_uid=study_uid,
        study_epoch_uid=epoch1.uid,
        visit_type={"term_uid": "VisitType_0004"},
        time_reference={"term_uid": "VisitSubType_0001"},
        time_value=20,
        time_unit_uid=day_uid,
    )
    version4 = create_visit_with_update(
        study_uid=study_uid,
        study_epoch_uid=epoch2.uid,
        visit_type={"term_uid": "VisitType_0002"},
        time_reference={"term_uid": "VisitSubType_0001"},
        time_value=30,
        time_unit_uid=day_uid,
        visit_sublabel_reference=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="ANCHOR_VISIT_IN_GROUP_OF_SUBV",
    )
    create_visit_with_update(
        study_uid=study_uid,
        study_epoch_uid=epoch2.uid,
        visit_type={"term_uid": "VisitType_0003"},
        time_reference={"term_uid": "VisitSubType_0002"},
        time_value=31,
        time_unit_uid=day_uid,
        visit_sublabel_reference=version4.uid,
        visit_class="SINGLE_VISIT",
        visit_subclass="ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV",
    )

    update_visit_with_update(
        version3.uid,
        study_uid=study_uid,
        uid=version3.uid,
        study_epoch_uid=epoch2.uid,
        visit_type={"term_uid": "VisitType_0004"},
        time_reference={"term_uid": "VisitSubType_0001"},
        time_value=35,
        time_unit_uid=day_uid,
    )
