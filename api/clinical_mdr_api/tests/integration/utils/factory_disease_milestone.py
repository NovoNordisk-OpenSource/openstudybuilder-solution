from clinical_mdr_api.models.study_selections.study_disease_milestone import (
    StudyDiseaseMilestoneCreateInput,
)
from clinical_mdr_api.services.studies.study_disease_milestone import (
    StudyDiseaseMilestoneService,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    create_ct_term,
    get_catalogue_name_library_name,
)


def create_study_disease_milestone_codelists_ret_cat_and_lib():
    _catalogue_name, library_name = get_catalogue_name_library_name()
    catalogue_name = "SDTM CT"
    codelist = create_codelist(
        "Disease Milestone Type",
        "CTCodelist_00004",
        catalogue_name,
        library_name,
        submission_value="MIDSTYPE",
    )
    create_ct_term(
        "Disease Milestone Type",
        "Disease_Milestone_Type_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 222,
                "submission_value": "Disease Milestone Type",
            }
        ],
    )
    create_ct_term(
        "Disease Milestone Type 2",
        "Disease_Milestone_Type_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 223,
                "submission_value": "Disease Milestone Type 2",
            }
        ],
    )
    create_ct_term(
        "Disease Milestone Type 3",
        "Disease_Milestone_Type_0003",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 224,
                "submission_value": "Disease Milestone Type 3",
            }
        ],
    )
    create_ct_term(
        "Disease Milestone Type 4",
        "Disease_Milestone_Type_0004",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 225,
                "submission_value": "Disease Milestone Type 4",
            }
        ],
    )
    create_ct_term(
        "Disease Milestone Type 5",
        "Disease_Milestone_Type_0005",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 226,
                "submission_value": "Disease Milestone Type 5",
            }
        ],
    )


def create_study_disease_milestone(disease_milestone_type):
    study_disease_milestone_create_input = StudyDiseaseMilestoneCreateInput(
        study_uid="study_root",
        disease_milestone_type=disease_milestone_type,
        repetition_indicator=True,
    )
    item = StudyDiseaseMilestoneService().create(
        "study_root", study_disease_milestone_input=study_disease_milestone_create_input
    )
    return item
