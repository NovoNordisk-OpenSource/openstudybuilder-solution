from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionPostInput,
)
from clinical_mdr_api.models.study_selections.study_visit import (
    StudyVisit,
    StudyVisitCreateInput,
    StudyVisitEditInput,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
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
from common.config import (
    DAY_UNIT_CONVERSION_FACTOR_TO_MASTER,
    WEEK_UNIT_CONVERSION_FACTOR_TO_MASTER,
)

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
    "conversion_factor_to_master": DAY_UNIT_CONVERSION_FACTOR_TO_MASTER,
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
    "conversion_factor_to_master": WEEK_UNIT_CONVERSION_FACTOR_TO_MASTER,
}


def generate_default_input_data_for_visit():
    day_uid = get_unit_uid_by_name("day")
    week_uid = get_unit_uid_by_name("week")
    return {
        "visit_sublabel_reference": None,
        "consecutive_visit_group": None,
        "show_visit": True,
        "min_visit_window_value": -1,
        "max_visit_window_value": 1,
        "visit_window_unit_uid": day_uid,
        "time_unit_uid": week_uid,
        "time_value": 12,
        "description": "description",
        "start_rule": "start_rule",
        "end_rule": "end_rule",
        "visit_contact_mode_uid": "VisitContactMode_0001",
        "visit_type_uid": "VisitType_0003",
        "time_reference_uid": "VisitSubType_0005",
        "is_global_anchor_visit": False,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
    }


def create_study_visit_codelists(
    create_unit_definitions=True,
    use_test_utils: bool = False,
    create_epoch_codelist: bool = True,
):
    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils)
    if create_epoch_codelist:
        create_study_epoch_codelists_ret_cat_and_lib(use_test_utils)

    unit_dim_codelist = create_codelist(
        "Unit Dimension", "CTCodelist_UnitDim", catalogue_name, library_name
    )
    create_ct_term(
        unit_dim_codelist.codelist_uid,
        "TIME",
        "TIME_UID",
        1,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        unit_dim_codelist.codelist_uid,
        "WEEK",
        "WEEK_UID",
        2,
        catalogue_name,
        library_name,
    )

    ct_unit_codelist = create_codelist(
        "CT Unit", "CTCodelist_CTUnit", catalogue_name, library_name
    )
    create_ct_term(
        ct_unit_codelist.codelist_uid,
        "ct unit 1",
        "unit1-ct-uid",
        1,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        ct_unit_codelist.codelist_uid,
        "ct unit 2",
        "unit2-ct-uid",
        2,
        catalogue_name,
        library_name,
    )
    if create_unit_definitions:
        unit_service = UnitDefinitionService(meta_repository=MetaRepository())
        week_unit = unit_service.post(UnitDefinitionPostInput(**WEEK))
        unit_service.approve(uid=week_unit.uid)
        day_unit = unit_service.post(UnitDefinitionPostInput(**DAY))
        unit_service.approve(uid=day_unit.uid)

    codelist = create_codelist(
        "VisitType", "CTCodelist_00004", catalogue_name, library_name
    )
    create_ct_term(
        codelist.codelist_uid,
        "Information",
        "VisitType_0000",
        0,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "BASELINE",
        "VisitType_0001",
        1,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "BASELINE2",
        "VisitType_0002",
        2,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "Visit Type2",
        "VisitType_0003",
        3,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "Visit Type3",
        "VisitType_0004",
        4,
        catalogue_name,
        library_name,
    )

    codelist = create_codelist(
        "Time Point Reference", "CTCodelist_00005", catalogue_name, library_name
    )
    create_ct_term(
        codelist.codelist_uid,
        "BASELINE",
        "VisitSubType_0001",
        1,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "BASELINE2",
        "VisitSubType_0002",
        2,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "Visit Sub Type2",
        "VisitSubType_0003",
        3,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "Visit Sub Type3",
        "VisitSubType_0004",
        4,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "Global anchor visit",
        "VisitSubType_0005",
        5,
        catalogue_name,
        library_name,
    )

    codelist = create_codelist(
        "Visit Contact Mode", "CTCodelist_00006", catalogue_name, library_name
    )
    create_ct_term(
        codelist.codelist_uid,
        "On Site Visit",
        "VisitContactMode_0001",
        1,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "Phone Contact",
        "VisitContactMode_0002",
        2,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "Virtual Visit",
        "VisitContactMode_0003",
        3,
        catalogue_name,
        library_name,
    )

    codelist = create_codelist(
        "Epoch Allocation", "CTCodelist_00007", catalogue_name, library_name
    )
    create_ct_term(
        codelist.codelist_uid,
        "Previous Visit",
        "EpochAllocation_0001",
        1,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "Current Visit",
        "EpochAllocation_0002",
        2,
        catalogue_name,
        library_name,
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
        visit_type_uid="VisitType_0001",
        time_reference_uid="VisitSubType_0001",
        time_value=0,
        time_unit_uid=day_uid,
    )
    create_visit_with_update(
        study_uid=study_uid,
        study_epoch_uid=epoch1.uid,
        visit_type_uid="VisitType_0003",
        time_reference_uid="VisitSubType_0001",
        time_value=12,
        time_unit_uid=day_uid,
    )
    create_visit_with_update(
        study_uid=study_uid,
        study_epoch_uid=epoch1.uid,
        visit_type_uid="VisitType_0003",
        time_reference_uid="VisitSubType_0001",
        time_value=10,
        time_unit_uid=day_uid,
    )

    version3 = create_visit_with_update(
        study_uid=study_uid,
        study_epoch_uid=epoch1.uid,
        visit_type_uid="VisitType_0004",
        time_reference_uid="VisitSubType_0001",
        time_value=20,
        time_unit_uid=day_uid,
    )
    version4 = create_visit_with_update(
        study_uid=study_uid,
        study_epoch_uid=epoch2.uid,
        visit_type_uid="VisitType_0002",
        time_reference_uid="VisitSubType_0001",
        time_value=30,
        time_unit_uid=day_uid,
        visit_sublabel_reference=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="ANCHOR_VISIT_IN_GROUP_OF_SUBV",
    )
    create_visit_with_update(
        study_uid=study_uid,
        study_epoch_uid=epoch2.uid,
        visit_type_uid="VisitType_0003",
        time_reference_uid="VisitSubType_0002",
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
        visit_type_uid="VisitType_0004",
        time_reference_uid="VisitSubType_0001",
        time_value=35,
        time_unit_uid=day_uid,
    )
