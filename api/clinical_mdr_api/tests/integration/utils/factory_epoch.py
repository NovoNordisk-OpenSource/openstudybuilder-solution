from clinical_mdr_api.domains.controlled_terminologies.utils import TermParentType
from clinical_mdr_api.models.study_selections.study_epoch import (
    StudyEpochCreateInput,
    StudyEpochEditInput,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    create_ct_term,
    get_catalogue_name_library_name,
)


def create_study_epoch_codelists_ret_cat_and_lib(use_test_utils: bool = False):
    _catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils)
    # Catalogue name must be SDTM CT
    catalogue_name = "SDTM CT"
    ct_term_service = CTTermService()
    codelist = create_codelist(
        "Epoch Type",
        "CTCodelist_00002",
        catalogue_name,
        library_name,
        submission_value="EPOCHTP",
    )
    type1 = create_ct_term(
        "Epoch Type",
        "EpochType_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "EPOCHTYPE1",
            }
        ],
    )
    type2 = create_ct_term(
        "Epoch Type1",
        "EpochType_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 2,
                "submission_value": "EPOCHTYPE2",
            }
        ],
    )
    type3 = create_ct_term(
        "Epoch Type2",
        "EpochType_0003",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 3,
                "submission_value": "EPOCHTYPE3",
            }
        ],
    )
    type4 = create_ct_term(
        "Epoch Type3",
        "EpochType_0004",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 4,
                "submission_value": "EPOCHTYPE4",
            }
        ],
    )

    codelist = create_codelist(
        "Epoch Sub Type",
        "CTCodelist_00003",
        catalogue_name,
        library_name,
        submission_value="EPOCHSTP",
    )
    subtype1 = create_ct_term(
        "Epoch Subtype",
        "EpochSubType_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "EPOCHSUBTYPE1",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=subtype1.uid,
        parent_uid=type1.uid,
        relationship_type=TermParentType.PARENT_TYPE,
    )
    subtype2 = create_ct_term(
        "Epoch Subtype1",
        "EpochSubType_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 2,
                "submission_value": "EPOCHSUBTYPE2",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=subtype2.uid,
        parent_uid=type2.uid,
        relationship_type=TermParentType.PARENT_TYPE,
    )
    subtype3 = create_ct_term(
        "Epoch Subtype2",
        "EpochSubType_0003",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 3,
                "submission_value": "EPOCHSUBTYPE3",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=subtype3.uid,
        parent_uid=type3.uid,
        relationship_type=TermParentType.PARENT_TYPE,
    )
    subtype4 = create_ct_term(
        "Epoch Subtype3",
        "EpochSubType_0004",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 4,
                "submission_value": "EPOCHSUBTYPE4",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=subtype4.uid,
        parent_uid=type4.uid,
        relationship_type=TermParentType.PARENT_TYPE,
    )
    supplemental_subtype = create_ct_term(
        "Basic",
        "Basic_uid",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 5,
                "submission_value": "BASIC",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=supplemental_subtype.uid,
        parent_uid=type1.uid,
        relationship_type=TermParentType.PARENT_TYPE,
    )
    information_subtype = create_ct_term(
        "Information",
        "information_epoch_subtype_uid",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 6,
                "submission_value": "INFOSUBTYPE",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=information_subtype.uid,
        parent_uid=type1.uid,
        relationship_type=TermParentType.PARENT_TYPE,
    )
    codelist = create_codelist(
        "Epoch", "C99079", catalogue_name, library_name, submission_value="EPOCH"
    )

    ep1 = create_ct_term(
        "Epoch Subtype 1",
        "Epoch_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 2,
                "submission_value": "EPOCH_SUBTYPE_1",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=ep1.uid,
        parent_uid=subtype1.uid,
        relationship_type=TermParentType.PARENT_SUB_TYPE,
    )
    ep2 = create_ct_term(
        "Epoch Subtype 2",
        "Epoch_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 3,
                "submission_value": "EPOCH_SUBTYPE_2",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=ep2.uid,
        parent_uid=subtype1.uid,
        relationship_type=TermParentType.PARENT_SUB_TYPE,
    )
    ep3 = create_ct_term(
        "Epoch Subtype 3",
        "Epoch_0003",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 4,
                "submission_value": "EPOCH_SUBTYPE_3",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=ep3.uid,
        parent_uid=subtype1.uid,
        relationship_type=TermParentType.PARENT_SUB_TYPE,
    )

    ep4 = create_ct_term(
        "Epoch Subtype1 1",
        "Epoch_0004",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 6,
                "submission_value": "EPOCH_SUBTYPE_1_1",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=ep4.uid,
        parent_uid=subtype2.uid,
        relationship_type=TermParentType.PARENT_SUB_TYPE,
    )
    ep5 = create_ct_term(
        "Epoch Subtype1 2",
        "Epoch_0005",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 7,
                "submission_value": "EPOCH_SUBTYPE_1_2",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=ep5.uid,
        parent_uid=subtype2.uid,
        relationship_type=TermParentType.PARENT_SUB_TYPE,
    )

    ep6 = create_ct_term(
        "Epoch Subtype2 1",
        "Epoch_0006",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 9,
                "submission_value": "EPOCH_SUBTYPE_2_1",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=ep6.uid,
        parent_uid=subtype3.uid,
        relationship_type=TermParentType.PARENT_SUB_TYPE,
    )
    ep7 = create_ct_term(
        "Epoch Subtype2 2",
        "Epoch_0007",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 10,
                "submission_value": "EPOCH_SUBTYPE_2_2",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=ep7.uid,
        parent_uid=subtype3.uid,
        relationship_type=TermParentType.PARENT_SUB_TYPE,
    )

    ep8 = create_ct_term(
        "Epoch Subtype3 1",
        "Epoch_0008",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 12,
                "submission_value": "EPOCH_SUBTYPE_3_1",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=ep8.uid,
        parent_uid=subtype3.uid,
        relationship_type=TermParentType.PARENT_SUB_TYPE,
    )
    ep9 = create_ct_term(
        "Epoch Subtype3 2",
        "Epoch_0009",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 13,
                "submission_value": "EPOCH_SUBTYPE_3_2",
            }
        ],
    )
    ct_term_service.add_parent(
        term_uid=ep9.uid,
        parent_uid=subtype3.uid,
        relationship_type=TermParentType.PARENT_SUB_TYPE,
    )


def create_study_epoch(epoch_subtype_uid, study_uid="study_root"):
    study_epoch_create_input = StudyEpochCreateInput(
        study_uid=study_uid,
        start_rule="start_rule",
        end_rule="end_rule",
        description="test_description",
        epoch_subtype=epoch_subtype_uid,
        duration=0,
        color_hash="#1100FF",
    )
    item = StudyEpochService().create(
        study_uid, study_epoch_input=study_epoch_create_input
    )
    return item


def edit_study_epoch(epoch_uid, study_uid="study_root"):
    study_epoch_edit_input = StudyEpochEditInput(
        study_uid=study_uid,
        change_description="edit to test",
        start_rule="second_new_start_rule",
    )
    item = StudyEpochService().edit(
        study_uid=study_uid,
        study_epoch_uid=epoch_uid,
        study_epoch_input=study_epoch_edit_input,
    )
    return item
