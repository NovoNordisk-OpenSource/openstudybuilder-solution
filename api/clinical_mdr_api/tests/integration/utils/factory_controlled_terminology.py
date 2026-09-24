from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_name_repository import (
    CTCodelistNameRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_attributes_repository import (
    CTTermAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_name_repository import (
    CTTermNameRepository,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameAR,
    CTCodelistNameVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import (
    CTCodelistPairedInput,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.controlled_terminologies.ct_codelist import (
    CTCodelistService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term_name import (
    CTTermNameService,
)
from clinical_mdr_api.tests.integration.utils.utils import (
    CT_CATALOGUE_NAME,
    SPONSOR_LIBRARY_NAME,
)
from clinical_mdr_api.tests.unit.domain.controlled_terminology_aggregates.test_ct_codelist_attributes import (
    create_random_ct_codelist_attributes_vo,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID


def get_catalogue_name_library_name(use_test_utils: bool = False):
    if use_test_utils is True:
        catalogue_name = CT_CATALOGUE_NAME
        library_name = SPONSOR_LIBRARY_NAME
    else:
        catalogue_name = "catalogue"
        library_name = "Sponsor"
    return catalogue_name, library_name


def create_codelist(
    name, uid, catalogue, library, submission_value=None, paired_code_codelist_uid=None
):
    ct_codelist_attributes_ar = CTCodelistAttributesAR.from_input_values(
        generate_uid_callback=lambda: uid,
        ct_codelist_attributes_vo=create_random_ct_codelist_attributes_vo(
            catalogue=catalogue,
            submission_value=submission_value,
        ),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=True
        ),
        author_id=AUTHOR_ID,
    )
    CTCodelistAttributesRepository().save(ct_codelist_attributes_ar)
    CTCodelistAttributesService().approve(uid)
    ct_codelist_name_vo = CTCodelistNameVO.from_repository_values(
        catalogue_names=[catalogue], name=name, is_template_parameter=False
    )
    ct_codelist: CTCodelistNameAR = CTCodelistNameAR.from_input_values(
        generate_uid_callback=lambda: ct_codelist_attributes_ar.uid,
        ct_codelist_name_vo=ct_codelist_name_vo,
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=True
        ),
        author_id=AUTHOR_ID,
    )
    CTCodelistNameRepository().save(ct_codelist)
    item = CTCodelistNameService().approve(uid)
    if paired_code_codelist_uid is not None:
        CTCodelistService().update_paired_codelists(
            uid,
            CTCodelistPairedInput(
                paired_codes_codelist_uid=paired_code_codelist_uid,
                paired_names_codelist_uid=None,
            ),
        )
    return item


def create_ct_term(
    name: str,
    uid: str,
    catalogue_name,
    library_name,
    preferred_term="test",
    definition="123",
    codelists=None,
):
    library = LibraryVO.from_repository_values(
        library_name=library_name, is_editable=True
    )

    ct_term_attributes_ar = CTTermAttributesAR.from_input_values(
        author_id=AUTHOR_ID,
        ct_term_attributes_vo=CTTermAttributesVO.from_input_values(
            catalogue_names=[catalogue_name],
            preferred_term=preferred_term,
            definition=definition,
            concept_id=None,
            catalogue_exists_callback=lambda s: True,
        ),
        library=library,
        generate_uid_callback=lambda: uid,
    )

    CTTermAttributesRepository().save(ct_term_attributes_ar)

    CTTermAttributesService().approve(uid)
    term_vo = CTTermNameVO.from_repository_values(
        catalogue_names=[catalogue_name],
        name=name,
        name_sentence_case=name.capitalize(),
    )
    ct_term = CTTermNameAR.from_input_values(
        generate_uid_callback=lambda: uid,
        ct_term_name_vo=term_vo,
        library=library,
        author_id=AUTHOR_ID,
    )
    CTTermNameRepository().save(ct_term)
    CTTermNameService().approve(uid)

    codelist_service = CTCodelistService()
    if codelists is not None:
        for codelist in codelists:
            codelist_service.add_term(
                codelist_uid=codelist["uid"],
                term_uid=ct_term.uid,
                submission_value=codelist["submission_value"],
                order=codelist["order"],
            )

    return ct_term


def get_unit_uid_by_name(unit_name):
    unit_uid = MetaRepository().unit_definition_repository.find_uid_by_name(unit_name)
    return unit_uid
