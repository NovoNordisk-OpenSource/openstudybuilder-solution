import unittest

from neomodel import db

from clinical_mdr_api.models.concepts.compound import Compound
from clinical_mdr_api.models.concepts.compound_alias import CompoundAlias
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyCompoundDosing,
    StudyCompoundDosingInput,
    StudySelectionCompound,
    StudySelectionCompoundCreateInput,
    StudySelectionElement,
    StudySelectionElementCreateInput,
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
from clinical_mdr_api.services.studies.study_element_selection import (
    StudyElementSelectionService,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_INSTANCES,
    STARTUP_ACTIVITY_SUB_GROUPS,
    STARTUP_CT_TERM,
    STARTUP_NUMERIC_VALUES_WITH_UNITS,
    STARTUP_PROJECTS_CYPHER,
    STARTUP_STUDY_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
)
from clinical_mdr_api.tests.integration.utils.utils import STUDY_UID, TestUtils
from common.config import settings


class TestStudyCompoundsService(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("study.compounds.service")

        db.cypher_query(STARTUP_CT_TERM)
        db.cypher_query(STARTUP_STUDY_CYPHER)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)
        db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
        db.cypher_query(STARTUP_PROJECTS_CYPHER)

        catalogue_name = "SDTM CT"
        library_name = "Sponsor"
        self.element_subtype_codelist = create_codelist(
            "Element Subtype",
            "CTCodelist_ElementType",
            catalogue_name,
            library_name,
            submission_value=settings.study_element_subtype_cl_submval,
        )
        self.element_type_term = create_ct_term(
            "Element Type",
            "ElementType_0001",
            catalogue_name,
            library_name,
            codelists=[
                {
                    "uid": self.element_subtype_codelist.codelist_uid,
                    "order": 1,
                    "submission_value": "Element Type",
                }
            ],
        )

        self.dose_form_codelist = create_codelist(
            "Dosage Form",
            "CTCodelist_DoseForm",
            catalogue_name,
            library_name,
            submission_value=settings.dosage_form_cl_submval,
        )

        self.ct_term_dosage = create_ct_term(
            "Dosage Form 1",
            "dosage_form_uid1",
            catalogue_name,
            library_name,
            codelists=[
                {
                    "uid": self.dose_form_codelist.codelist_uid,
                    "order": 1,
                    "submission_value": "Dosage Form 1",
                }
            ],
        )

        self.roa_codelist = create_codelist(
            "Route of Administration",
            "CTCodelist_ROA",
            catalogue_name,
            library_name,
            submission_value=settings.route_of_administration_cl_submval,
        )

        self.ct_term_roa = create_ct_term(
            "ROA 1",
            "route_of_administration_uid1",
            catalogue_name,
            library_name,
            codelists=[
                {
                    "uid": self.roa_codelist.codelist_uid,
                    "order": 1,
                    "submission_value": "ROA 1",
                }
            ],
        )

        self.dd_codelist = create_codelist(
            "Delivery Device",
            "CTCodelist_DD",
            catalogue_name,
            library_name,
            submission_value=settings.delivery_device_cl_submval,
        )

        self.ct_term_dd = create_ct_term(
            "DD 1",
            "delivery_device_uid1",
            catalogue_name,
            library_name,
            codelists=[
                {
                    "uid": self.dd_codelist.codelist_uid,
                    "order": 1,
                    "submission_value": "DD 1",
                }
            ],
        )

        self.disp_codelist = create_codelist(
            "Dispenser",
            "CTCodelist_DISP",
            catalogue_name,
            library_name,
            submission_value=settings.compound_dispensed_in_cl_submval,
        )

        self.ct_term_disp = create_ct_term(
            "Disp 1",
            "dispenser_uid1",
            catalogue_name,
            library_name,
            codelists=[
                {
                    "uid": self.disp_codelist.codelist_uid,
                    "order": 1,
                    "submission_value": "Disp 1",
                }
            ],
        )

        self.freq_codelist = create_codelist(
            "Dose Frequency",
            "CTCodelist_DF",
            catalogue_name,
            library_name,
            submission_value=settings.dose_frequency_cl_submval,
        )

        self.ct_term_freq = create_ct_term(
            "Freq 1",
            "dose_frequency_uid1",
            catalogue_name,
            library_name,
            codelists=[
                {
                    "uid": self.freq_codelist.codelist_uid,
                    "order": 1,
                    "submission_value": "Freq 1",
                }
            ],
        )

        super().setUp()

    def test_audit_trail(self):
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
            dosage_form_uids=["dosage_form_uid1"],
            route_of_administration_uids=["route_of_administration_uid1"],
            formulations=[],
            approve=True,
        )
        medicinal_product1 = TestUtils.create_medicinal_product(
            name="medicinal_product1",
            external_id="external_id1",
            dose_value_uids=["NumericValueWithUnit_000001"],
            dose_frequency_uids=["dose_frequency_uid1"],
            delivery_device_uid="delivery_device_uid1",
            dispenser_uid="dispenser_uid1",
            pharmaceutical_product_uids=[pharmaceutical_product1.uid],
            compound_uid=compound1.uid,
            approve=True,
        )

        medicinal_product2 = TestUtils.create_medicinal_product(
            name="medicinal_product2",
            external_id="external_id2",
            dose_value_uids=["NumericValueWithUnit_000001"],
            dose_frequency_uids=["dose_frequency_uid1"],
            delivery_device_uid="delivery_device_uid1",
            dispenser_uid="dispenser_uid1",
            pharmaceutical_product_uids=[pharmaceutical_product1.uid],
            compound_uid=compound2.uid,
            approve=True,
        )

        study_selection_element: (
            StudySelectionElement
        ) = StudyElementSelectionService().make_selection(
            study_uid=STUDY_UID,
            selection_create_input=StudySelectionElementCreateInput(
                name="Elem1",
                short_name="el1",
                element_subtype_uid=self.element_type_term.uid,
            ),
        )

        # Make a compound selection with compound alias 'compound_alias1a'
        study_compound_created1: StudySelectionCompound = (
            TestUtils.create_study_compound(
                study_uid=STUDY_UID,
                medicinal_product_uid=medicinal_product1.uid,
                compound_alias_uid=compound_alias1a.uid,
                # delivery_device_uid="delivery_device_uid1",
                # dispenser_uid="dispenser_uid1",
                # dose_value_uid="NumericValueWithUnit_000001",
            )
        )
        assert study_compound_created1.study_compound_uid == "StudyCompound_000001"

        # Make a compound selection with another compound alias, while keeping all other details the same
        study_compound_created2: (
            StudySelectionCompound
        ) = StudyCompoundSelectionService().make_selection(
            study_uid=STUDY_UID,
            selection_create_input=StudySelectionCompoundCreateInput(
                medicinal_product_uid=medicinal_product2.uid,
                compound_alias_uid=compound_alias2a.uid,
            ),
        )
        assert study_compound_created2.study_compound_uid == "StudyCompound_000003"

        # Make a compound dosing selection with just-created study compound 'study_compound_created1'
        study_compound_dosing_created1: (
            StudyCompoundDosing
        ) = StudyCompoundDosingSelectionService().make_selection(
            study_uid=STUDY_UID,
            selection_create_input=StudyCompoundDosingInput(
                study_compound_uid=study_compound_created1.study_compound_uid,
                study_element_uid=study_selection_element.element_uid,
            ),
        )

        assert (
            study_compound_dosing_created1.study_compound_dosing_uid
            == "StudyCompoundDosing_000001"
        )

        # Make a compound dosing selection with another study compound, while keeping all other details the same
        study_compound_dosing_created2: (
            StudyCompoundDosing
        ) = StudyCompoundDosingSelectionService().make_selection(
            study_uid=STUDY_UID,
            selection_create_input=StudyCompoundDosingInput(
                study_compound_uid=study_compound_created2.study_compound_uid,
                study_element_uid=study_selection_element.element_uid,
            ),
        )
        assert (
            study_compound_dosing_created2.study_compound_dosing_uid
            == "StudyCompoundDosing_000002"
        )

        # Now call audit trail
        items = StudyCompoundDosingSelectionService().get_all_selection_audit_trail(
            STUDY_UID
        )
        assert len(items) == 2
