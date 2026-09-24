# pylint: disable=unused-argument,redefined-outer-name

import logging

from clinical_mdr_api.models.concepts.compound import Compound
from clinical_mdr_api.models.concepts.compound_alias import CompoundAlias
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyCompoundDosingInput,
    StudySelectionCompound,
    StudySelectionCompoundCreateInput,
)
from clinical_mdr_api.services.concepts.compound_alias_service import (
    CompoundAliasService,
)
from clinical_mdr_api.services.concepts.compound_service import CompoundService
from clinical_mdr_api.services.studies.study_compound_dosing_selection import (
    StudyCompoundDosingSelectionService,
)
from clinical_mdr_api.services.studies.study_compound_selection import (
    StudyCompoundSelectionService,
)
from clinical_mdr_api.services.studies.study_interventions import (
    StudyInterventionsService,
)
from clinical_mdr_api.tests.integration.utils.utils import CT_CODELIST_UIDS, TestUtils

log = logging.getLogger(__name__)


def test_get_table(
    tst_study, study_epochs, study_arms, study_elements, study_design_cells
):
    # Create CT Terms
    catalogue_name = "SDTM CT"
    library_name = "Sponsor"

    ct_term_dosage = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.dosage_form,
        submission_value="dosage_form_1",
        sponsor_preferred_name="dosage_form_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        approve=True,
    )
    ct_term_delivery_device = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.delivery_device,
        submission_value="delivery_device_1",
        sponsor_preferred_name="delivery_device_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        approve=True,
    )
    ct_term_dose_frequency = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.frequency,
        submission_value="dose_frequency_1",
        sponsor_preferred_name="dose_frequency_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        approve=True,
    )
    ct_term_dispenser = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.dispenser,
        submission_value="dispenser_1",
        sponsor_preferred_name="dispenser_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        approve=True,
    )
    ct_term_roa = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.roa,
        submission_value="route_of_administration_1",
        sponsor_preferred_name="route_of_administration_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        approve=True,
    )

    # Create Numeric values with unit
    # strength_value = TestUtils.create_numeric_value_with_unit(value=5, unit="mg/mL")
    dose_value = TestUtils.create_numeric_value_with_unit(value=10, unit="mg")
    # half_life = TestUtils.create_numeric_value_with_unit(value=8, unit="hours")

    # # Create Lag-times
    # lag_time = TestUtils.create_lag_time(value=7, unit="days")

    # # Create Brands
    # brands = [
    #     TestUtils.create_brand(name=name) for name in ["Brand A", "Brand B", "Brand C"]
    # ]

    # Create compounds
    compound1: Compound = TestUtils.create_compound(
        name="name-AAA",
    )
    compound_alias1a: CompoundAlias = TestUtils.create_compound_alias(
        compound_uid=compound1.uid
    )
    compound_alias1b: CompoundAlias = TestUtils.create_compound_alias(
        compound_uid=compound1.uid
    )

    compound2: Compound = TestUtils.create_compound(
        name="name-BBB",
    )
    compound_alias2a: CompoundAlias = TestUtils.create_compound_alias(
        compound_uid=compound2.uid
    )
    compound_alias2b: CompoundAlias = TestUtils.create_compound_alias(
        compound_uid=compound2.uid
    )

    CompoundService().approve(compound1.uid)
    CompoundService().approve(compound2.uid)
    CompoundAliasService().approve(compound_alias1a.uid)
    CompoundAliasService().approve(compound_alias2a.uid)
    CompoundAliasService().approve(compound_alias1b.uid)
    CompoundAliasService().approve(compound_alias2b.uid)

    pharmaceutical_product1 = TestUtils.create_pharmaceutical_product(
        external_id="external_id1",
        dosage_form_uids=[ct_term_dosage.term_uid],
        route_of_administration_uids=[ct_term_roa.term_uid],
        formulations=[],
        approve=True,
    )
    medicinal_product1 = TestUtils.create_medicinal_product(
        name="medicinal_product1",
        external_id="external_id1",
        dose_value_uids=[dose_value.uid],
        dose_frequency_uids=[ct_term_dose_frequency.term_uid],
        delivery_device_uid=ct_term_delivery_device.term_uid,
        dispenser_uid=ct_term_dispenser.term_uid,
        pharmaceutical_product_uids=[pharmaceutical_product1.uid],
        compound_uid=compound1.uid,
        approve=True,
    )
    medicinal_product2 = TestUtils.create_medicinal_product(
        name="medicinal_product2",
        external_id="external_id2",
        dose_value_uids=[dose_value.uid],
        dose_frequency_uids=[ct_term_dose_frequency.term_uid],
        delivery_device_uid=ct_term_delivery_device.term_uid,
        dispenser_uid=ct_term_dispenser.term_uid,
        pharmaceutical_product_uids=[pharmaceutical_product1.uid],
        compound_uid=compound2.uid,
        approve=True,
    )

    # Make a compound selection with compound alias 'compound_alias1a'
    study_compound_created1: StudySelectionCompound = TestUtils.create_study_compound(
        study_uid=tst_study.uid,
        medicinal_product_uid=medicinal_product1.uid,
        compound_alias_uid=compound_alias1a.uid,
    )

    # Make a compound selection with another compound alias, while keeping all other details the same
    study_compound_created2: (
        StudySelectionCompound
    ) = StudyCompoundSelectionService().make_selection(
        study_uid=tst_study.uid,
        selection_create_input=StudySelectionCompoundCreateInput(
            medicinal_product_uid=medicinal_product2.uid,
            compound_alias_uid=compound_alias2a.uid,
        ),
    )

    study_compound_dosing_selection_service = StudyCompoundDosingSelectionService()

    # Make a compound dosing selection with just-created study compound 'study_compound_created1'
    study_compound_dosing_selection_service.make_selection(
        study_uid=tst_study.uid,
        selection_create_input=StudyCompoundDosingInput(
            study_compound_uid=study_compound_created1.study_compound_uid,
            dose_value_uid=dose_value.uid,
            study_element_uid=study_elements[0].element_uid,
        ),
    )

    # Make a compound dosing selection with another study compound, while keeping all other details the same
    study_compound_dosing_selection_service.make_selection(
        study_uid=tst_study.uid,
        selection_create_input=StudyCompoundDosingInput(
            study_compound_uid=study_compound_created2.study_compound_uid,
            dose_value_uid=dose_value.uid,
            study_element_uid=study_elements[1].element_uid,
        ),
    )

    table = StudyInterventionsService().get_table(tst_study.uid)

    assert len(table.rows) == 8, "Incorrect number of rows"
    assert len(table.rows[0].cells) == 3, "Incorrect number of columns"
    assert table.num_header_rows == 1, "Incorrect number of header rows"
    assert table.num_header_cols == 1, "Incorrect number of header columns"

    for row in table.rows:
        assert len(row.cells) == 3

    assert table.rows[0].cells[1].text == study_arms[0].name, "arm name mismatch"
    assert table.rows[0].cells[2].text == study_arms[1].name, "arm name mismatch"
    # assert table.rows[1].cells[1].text == compound1.name, "compound name mismatch"
    # assert table.rows[1].cells[2].text == compound2.name, "compound name mismatch"
    # table.data[2] intervention type is missing from test data
    # table.data[3] is not implemented
    # assert (
    #     table.rows[4].cells[1].text
    #     == table.rows[4].cells[2].text
    #     == ct_term_dosage.sponsor_preferred_name
    # )
    # assert (
    #     table.rows[5].cells[1].text
    #     == table.rows[5].cells[2].text
    #     == ct_term_roa.sponsor_preferred_name
    # )

    # assert ct_term_delivery_device.sponsor_preferred_name in table.rows[6].cells[1].text
    # assert ct_term_dispenser.sponsor_preferred_name in table.rows[6].cells[1].text
    assert table.rows[6].cells[1].text == table.rows[6].cells[2].text
