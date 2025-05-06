import re

from fastapi import FastAPI
from fastapi.routing import APIRoute

# Helpers
from starlette.routing import Mount

from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.concepts.unit_definitions.unit_definition import (
    UnitDefinitionService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist import (
    CTCodelistService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from clinical_mdr_api.tests.integration.utils.utils import LIBRARY_NAME, TestUtils
from common import config

library_data = {"name": "Test library", "is_editable": True}

template_data = {
    "name": "Test_Name_Template",
    "library": library_data,
    "library_name": "Test library",
}

criteria_template_data = template_data
criteria_template_data["type_uid"] = "C25532"

DATA_MAP = {"objective-templates": template_data, "libraries": library_data}

STARTUP_ODM_CONDITIONS = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_description_root1:ConceptRoot:OdmDescriptionRoot {uid: "odm_description1"})
MERGE (odm_description_value1:ConceptValue:OdmDescriptionValue {name: "name1", language: "ENG", description: "description1", instruction: "instruction1", sponsor_instruction: "sponsor_instruction1"})
MERGE (odm_description_root1)-[ld:LATEST_FINAL]->(odm_description_value1)
MERGE (odm_description_root1)-[l:LATEST]->(odm_description_value1)
CREATE (odm_description_root1)-[hv:HAS_VERSION]->(odm_description_value1)
SET hv = final_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_condition_root1:ConceptRoot:OdmConditionRoot {uid: "odm_condition1"})
MERGE (odm_condition_value1:ConceptValue:OdmConditionValue {oid: "oid1", name: "name1"})
MERGE (odm_condition_root1)-[ld1:LATEST_FINAL]->(odm_condition_value1)
MERGE (odm_condition_root1)-[l1:LATEST]->(odm_condition_value1)
MERGE (odm_condition_root1)-[hv1:HAS_VERSION]->(odm_condition_value1)
SET hv1 = final_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_condition_root2:ConceptRoot:OdmConditionRoot {uid: "odm_condition2"})
MERGE (odm_condition_value2:ConceptValue:OdmConditionValue {oid: "oid2", name: "name2"})
MERGE (odm_condition_root2)-[ld2:LATEST_FINAL]->(odm_condition_value2)
MERGE (odm_condition_root2)-[l2:LATEST]->(odm_condition_value2)
MERGE (odm_condition_root2)-[hv2:HAS_VERSION]->(odm_condition_value2)
SET hv2 = final_properties

MERGE (odm_condition_root1)-[:HAS_DESCRIPTION]->(odm_description_root1)
MERGE (odm_condition_root2)-[:HAS_DESCRIPTION]->(odm_description_root1)

"""

STARTUP_ODM_METHODS = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_description_root1:ConceptRoot:OdmDescriptionRoot {uid: "odm_description1"})
MERGE (odm_description_value1:ConceptValue:OdmDescriptionValue {name: "name1", language: "ENG", description: "description1", instruction: "instruction1", sponsor_instruction: "sponsor_instruction1"})
MERGE (odm_description_root1)-[ld:LATEST_FINAL]->(odm_description_value1)
MERGE (odm_description_root1)-[l:LATEST]->(odm_description_value1)
CREATE (odm_description_root1)-[hv:HAS_VERSION]->(odm_description_value1)
SET hv = final_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_method_root1:ConceptRoot:OdmMethodRoot {uid: "odm_method1"})
MERGE (odm_method_value1:ConceptValue:OdmMethodValue {oid: "oid1", name: "name1", method_type: "type1"})
MERGE (odm_method_root1)-[ld1:LATEST_FINAL]->(odm_method_value1)
MERGE (odm_method_root1)-[l1:LATEST]->(odm_method_value1)
MERGE (odm_method_root1)-[hv1:HAS_VERSION]->(odm_method_value1)
SET hv1 = final_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_method_root2:ConceptRoot:OdmMethodRoot {uid: "odm_method2"})
MERGE (odm_method_value2:ConceptValue:OdmMethodValue {oid: "oid2", name: "name2", method_type: "type2"})
MERGE (odm_method_root2)-[ld2:LATEST_FINAL]->(odm_method_value2)
MERGE (odm_method_root2)-[l2:LATEST]->(odm_method_value2)
MERGE (odm_method_root2)-[hv2:HAS_VERSION]->(odm_method_value2)
SET hv2 = final_properties

MERGE (odm_method_root1)-[:HAS_DESCRIPTION]->(odm_description_root1)
MERGE (odm_method_root2)-[:HAS_DESCRIPTION]->(odm_description_root1)

"""

STARTUP_ODM_FORMAL_EXPRESSIONS = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
author_id: "unknown-user",
version: "0.1"
} AS draft_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_formal_expression_root1:ConceptRoot:OdmFormalExpressionRoot {uid: "odm_formal_expression1"})
MERGE (odm_formal_expression_value1:ConceptValue:OdmFormalExpressionValue {context: "context1", expression: "expression1"})
MERGE (odm_formal_expression_root1)-[ld1:LATEST_DRAFT]->(odm_formal_expression_value1)
MERGE (odm_formal_expression_root1)-[l1:LATEST]->(odm_formal_expression_value1)
MERGE (odm_formal_expression_root1)-[hv1:HAS_VERSION]->(odm_formal_expression_value1)
SET hv1 = draft_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_formal_expression_root2:ConceptRoot:OdmFormalExpressionRoot {uid: "odm_formal_expression2"})
MERGE (odm_formal_expression_value2:ConceptValue:OdmFormalExpressionValue {context: "context2", expression: "expression2"})
MERGE (odm_formal_expression_root2)-[ld2:LATEST_DRAFT]->(odm_formal_expression_value2)
MERGE (odm_formal_expression_root2)-[l2:LATEST]->(odm_formal_expression_value2)
MERGE (odm_formal_expression_root2)-[hv2:HAS_VERSION]->(odm_formal_expression_value2)
SET hv2 = draft_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_formal_expression_root3:ConceptRoot:OdmFormalExpressionRoot {uid: "odm_formal_expression3"})
MERGE (odm_formal_expression_value3:ConceptValue:OdmFormalExpressionValue {context: "context1", expression: "expression1"})
MERGE (odm_formal_expression_root3)-[ld3:LATEST_DRAFT]->(odm_formal_expression_value3)
MERGE (odm_formal_expression_root3)-[l3:LATEST]->(odm_formal_expression_value3)
MERGE (odm_formal_expression_root3)-[hv3:HAS_VERSION]->(odm_formal_expression_value3)
SET hv3 = draft_properties
"""

STARTUP_ODM_DESCRIPTIONS = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
author_id: "unknown-user",
version: "0.1"
} AS draft_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_description_root2:ConceptRoot:OdmDescriptionRoot {uid: "odm_description2"})
MERGE (odm_description_value2:ConceptValue:OdmDescriptionValue {name: "name2", language: "language2", description: "description2", instruction: "instruction2", sponsor_instruction: "sponsor_instruction2"})
MERGE (odm_description_root2)-[ld2:LATEST_DRAFT]->(odm_description_value2)
MERGE (odm_description_root2)-[l2:LATEST]->(odm_description_value2)
MERGE (odm_description_root2)-[hv2:HAS_VERSION]->(odm_description_value2)
SET hv2 = draft_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_description_root3:ConceptRoot:OdmDescriptionRoot {uid: "odm_description3"})
MERGE (odm_description_value3:ConceptValue:OdmDescriptionValue {name: "name3", language: "ENG", description: "description3", instruction: "instruction3", sponsor_instruction: "sponsor_instruction3"})
MERGE (odm_description_root3)-[ld3:LATEST_DRAFT]->(odm_description_value3)
MERGE (odm_description_root3)-[l3:LATEST]->(odm_description_value3)
CREATE (odm_description_root3)-[hv3:HAS_VERSION]->(odm_description_value3)
SET hv3 = draft_properties
"""

STARTUP_ODM_ALIASES = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
author_id: "unknown-user",
version: "0.1"
} AS draft_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_alias_root1:ConceptRoot:OdmAliasRoot {uid: "odm_alias1"})
MERGE (odm_alias_value1:ConceptValue:OdmAliasValue {context: "context1", name: "name1"})
MERGE (odm_alias_root1)-[ld1:LATEST_DRAFT]->(odm_alias_value1)
MERGE (odm_alias_root1)-[l1:LATEST]->(odm_alias_value1)
MERGE (odm_alias_root1)-[hv1:HAS_VERSION]->(odm_alias_value1)
SET hv1 = draft_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_alias_root2:ConceptRoot:OdmAliasRoot {uid: "odm_alias2"})
MERGE (odm_alias_value2:ConceptValue:OdmAliasValue {context: "context2", name: "name2"})
MERGE (odm_alias_root2)-[ld2:LATEST_DRAFT]->(odm_alias_value2)
MERGE (odm_alias_root2)-[l2:LATEST]->(odm_alias_value2)
MERGE (odm_alias_root2)-[hv2:HAS_VERSION]->(odm_alias_value2)
SET hv2 = draft_properties
"""

STARTUP_CT_TERM_WITHOUT_CATALOGUE = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties

MERGE (Library:Library {name:"Sponsor", is_editable:true})
MERGE (Library)-[:CONTAINS_TERM]->(TermRoot:CTTermRoot {concept_id: "concept_id1", uid: "term1"})
MERGE (TermRoot)-[:HAS_ATTRIBUTES_ROOT]->(TermAttrRoot:CTTermAttributesRoot)
MERGE (TermAttrValue:CTTermAttributesValue {code_submission_value: "code_submission_value1", concept_id: "concept_id1", definition: "definition1", preferred_term: "preferred_term1", synonyms: "synonyms1"})
MERGE (TermAttrRoot)-[lf1:LATEST_FINAL]->(TermAttrValue)
MERGE (TermAttrRoot)-[:LATEST]->(TermAttrValue)
MERGE (TermAttrRoot)-[hv1:HAS_VERSION]->(TermAttrValue)

MERGE (TermRoot)-[:HAS_NAME_ROOT]->(TermNameRoot:CTTermNameRoot)
MERGE (TermNameValue:CTTermNameValue {name: "name1", name_sentence_case: "name_sentence_case1"})
MERGE (TermNameRoot)-[lf2:LATEST_FINAL]->(TermNameValue)
MERGE (TermNameRoot)-[:LATEST]->(TermNameValue)
MERGE (TermNameRoot)-[hv2:HAS_VERSION]->(TermNameValue)
SET hv1 = final_properties
SET hv2 = final_properties
"""

STARTUP_CT_TERM = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties

MERGE (Library:Library {name:"Sponsor", is_editable:true})
MERGE (Library)-[:CONTAINS_CATALOGUE]->(Catalogue:CTCatalogue {name:"SDTM CT"})
MERGE (Library)-[:CONTAINS_CODELIST]->(CodelistRoot:CTCodelistRoot {uid: "codelist_root1"})
MERGE (Catalogue)-[:HAS_CODELIST]->(CodelistRoot)
MERGE (Library)-[:CONTAINS_TERM]->(TermRoot1:CTTermRoot {concept_id: "concept_id1", uid: "term1"})
MERGE (CodelistRoot)-[:HAS_TERM]->(TermRoot1)
MERGE (TermRoot1)-[:HAS_ATTRIBUTES_ROOT]->(TermAttrRoot1:CTTermAttributesRoot)
MERGE (TermAttrValue1:CTTermAttributesValue {code_submission_value: "code_submission_value1", concept_id: "concept_id1", definition: "definition1", preferred_term: "preferred_term1", synonyms: "synonyms1"})
MERGE (TermAttrRoot1)-[lf1:LATEST_FINAL]->(TermAttrValue1)
MERGE (TermAttrRoot1)-[:LATEST]->(TermAttrValue1)
MERGE (TermAttrRoot1)-[hv1:HAS_VERSION]->(TermAttrValue1)
SET hv1 = final_properties

MERGE (TermRoot1)-[:HAS_NAME_ROOT]->(TermNameRoot1:CTTermNameRoot)
MERGE (TermNameRoot1)-[:LATEST]->(TermNameValue1:CTTermNameValue {name: "name1", name_sentence_case: "name1"})
MERGE (TermNameRoot1)-[lf2:LATEST_FINAL]->(TermNameValue1)
MERGE (TermNameRoot1)-[hv2:HAS_VERSION]->(TermNameValue1)
SET hv2 = final_properties

MERGE (Library)-[:CONTAINS_TERM]->(TermRoot2:CTTermRoot {concept_id: "concept_id2", uid: "term2"})
MERGE (CodelistRoot)-[:HAS_TERM]->(TermRoot2)
MERGE (TermRoot2)-[:HAS_ATTRIBUTES_ROOT]->(TermAttrRoot2:CTTermAttributesRoot)
MERGE (TermAttrValue2:CTTermAttributesValue {code_submission_value: "code_submission_value2", concept_id: "concept_id2", definition: "definition2", preferred_term: "preferred_term2", synonyms: "synonyms2"})
MERGE (TermAttrRoot2)-[lf3:LATEST_FINAL]->(TermAttrValue2)
MERGE (TermAttrRoot2)-[:LATEST]->(TermAttrValue2)
MERGE (TermAttrRoot2)-[hv3:HAS_VERSION]->(TermAttrValue2)
SET hv3 = final_properties

MERGE (TermRoot2)-[:HAS_NAME_ROOT]->(TermNameRoot2:CTTermNameRoot)
MERGE (TermNameRoot2)-[:LATEST]->(TermNameValue2:CTTermNameValue {name: "name1", name_sentence_case: "name1"})
MERGE (TermNameRoot2)-[lf4:LATEST_FINAL]->(TermNameValue2)
MERGE (TermNameRoot2)-[hv4:HAS_VERSION]->(TermNameValue2)
SET hv4 = final_properties
"""

STARTUP_UNIT_DEFINITIONS = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
author_id: "unknown-user",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties,
{
start_date: datetime(),
author_id: "Dictionary Codelist Test"
} AS has_term_properties

MERGE (library:Library {name:"Sponsor", is_editable:true})
MERGE (library)-[:CONTAINS_CONCEPT]->(unit_def_root:ConceptRoot:UnitDefinitionRoot {uid:"unit_definition_root1"})
MERGE (unit_def_value:ConceptValue:UnitDefinitionValue { name:"name1", unit_ct_uid: "unit1-ct-uid", convertible_unit: true, display_unit: true, master_unit: true, si_unit: true, us_conventional_unit: true, use_complex_unit_conversion: true, unit_dimension_uid: "unit1-dimension", legacy_code: "unit1-legacy-code", use_molecular_weight: false, conversion_factor_to_master: 1.0 })
MERGE (unit_def_root)-[ld1:LATEST_DRAFT]-(unit_def_value)
MERGE (unit_def_root)-[l1:LATEST]->(unit_def_value)
MERGE (unit_def_root)-[hv1:HAS_VERSION]->(unit_def_value)
SET hv1 = draft_properties

MERGE (codelist_root1:DictionaryCodelistRoot {uid:"codelist_root1_uid"})
MERGE (library)-[:CONTAINS_DICTIONARY_CODELIST]->(codelist_root1)
MERGE (codelist_value1:DictionaryCodelistValue {name:"name1"})
MERGE (codelist_root1)-[lf1:LATEST_FINAL]->(codelist_value1)
MERGE (codelist_root1)-[l2:LATEST]->(codelist_value1)
MERGE (codelist_root1)-[hv2:HAS_VERSION]->(codelist_value1)
SET hv2 = final_properties

MERGE (codelist_root1)-[has_term1:HAS_TERM]->(term_root1:DictionaryTermRoot:UCUMTermRoot {uid:"term_root1_uid"})
-[:LATEST]->(term_value1:DictionaryTermValue:UCUMTermValue {
name:"name1", dictionary_id:"dictionary_id1", name_sentence_case:"Name1", abbreviation:"abbreviation1", definition:"definition1"})

MERGE (library)-[:CONTAINS_DICTIONARY_TERM]->(term_root1)
MERGE (term_root1)-[lf2:LATEST_FINAL]->(term_value1)
MERGE (term_root1)-[hv3:HAS_VERSION]->(term_value1)
SET hv3 = final_properties
SET has_term1 = has_term_properties
MERGE (unit_def_value)-[hut1:HAS_UCUM_TERM]->(term_root1)

MERGE (library)-[:CONTAINS_TERM]->(cttr:CTTermRoot {uid: "C25532_name1", concept_id: "C25532"})
MERGE (cttr)-[:HAS_NAME_ROOT]->(cttnr:CTTermNameRoot)
MERGE (unit_def_value)-[hcu1:HAS_CT_UNIT]->(cttr)
MERGE (cttnr)-[:LATEST]->(cttnv:CTTermNameValue {name: "name1", name_sentence_case: "name1"})
MERGE (cttnr)-[latest_final1:LATEST_FINAL]->(cttnv)
MERGE (cttnr)-[has_version1:HAS_VERSION]->(cttnv)
SET has_version1 = final_properties
"""

STARTUP_ODM_ITEM_GROUPS = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties

MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_description_root1:ConceptRoot:OdmDescriptionRoot {uid: "odm_description1"})
MERGE (odm_description_value1:ConceptValue:OdmDescriptionValue {name: "name1", language: "ENG", description: "description1", instruction: "instruction1"})
MERGE (odm_description_root1)-[ld1:LATEST_FINAL]->(odm_description_value1)
MERGE (odm_description_root1)-[l1:LATEST]->(odm_description_value1)
CREATE (odm_description_root1)-[hv1:HAS_VERSION]->(odm_description_value1)
SET hv1 = final_properties

MERGE (item_group_root1:ConceptRoot:OdmItemGroupRoot {uid: "odm_item_group1"})
MERGE (item_group_value1:ConceptValue:OdmItemGroupValue {oid: "oid1", name: "name1", repeating: false, is_reference_data: false, sas_dataset_name: "sas_dataset_name1", origin: "origin1", purpose: "purpose1", comment: "comment1"})
MERGE (library)-[r0:CONTAINS_CONCEPT]->(item_group_root1)
MERGE (item_group_root1)-[r1:LATEST_FINAL]->(item_group_value1)
MERGE (item_group_root1)-[hv2:HAS_VERSION]->(item_group_value1)
MERGE (item_group_root1)-[:LATEST]->(item_group_value1)
MERGE (item_group_root1)-[:HAS_DESCRIPTION]->(odm_description_root1)
SET hv2 = final_properties

MERGE (item_group_root2:ConceptRoot:OdmItemGroupRoot {uid: "odm_item_group2"})
MERGE (item_group_value2:ConceptValue:OdmItemGroupValue {oid: "oid2", name: "name2", repeating: false, is_reference_data: true, sas_dataset_name: "sas_dataset_name2", origin: "origin2", purpose: "purpose2", comment: "comment2"})
MERGE (library)-[:CONTAINS_CONCEPT]->(item_group_root2)
MERGE (item_group_root2)-[r2:LATEST_FINAL]->(item_group_value2)
MERGE (item_group_root2)-[hv3:HAS_VERSION]->(item_group_value2)
MERGE (item_group_root2)-[:LATEST]->(item_group_value2)
MERGE (item_group_root2)-[:HAS_DESCRIPTION]->(odm_description_root1)
SET hv3 = final_properties

WITH *
MATCH (ct_term_root1:CTTermRoot {uid: "term1"})
MATCH (ct_term_root2:CTTermRoot {uid: "term2"})
MERGE (item_group_root1)-[:HAS_SDTM_DOMAIN]->(ct_term_root1)
MERGE (item_group_root1)-[:HAS_SDTM_DOMAIN]->(ct_term_root2)
MERGE (item_group_root2)-[:HAS_SDTM_DOMAIN]->(ct_term_root1)
"""

STARTUP_ODM_ITEMS = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties

MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_description_root1:ConceptRoot:OdmDescriptionRoot {uid: "odm_description1"})
MERGE (odm_description_value1:ConceptValue:OdmDescriptionValue {name: "name1", language: "ENG", description: "description1", instruction: "instruction1"})
MERGE (odm_description_root1)-[ld1:LATEST_FINAL]->(odm_description_value1)
MERGE (odm_description_root1)-[l1:LATEST]->(odm_description_value1)
CREATE (odm_description_root1)-[hv1:HAS_VERSION]->(odm_description_value1)
SET hv1 = final_properties

MERGE (item_root1:ConceptRoot:OdmItemRoot {uid: "odm_item1"})
MERGE (item_value1:ConceptValue:OdmItemValue {oid: "oid1", name: "name1", datatype: "datatype1", length: 1, significant_digits: 1, sas_field_name: "sasfieldname1", sds_var_name: "sdsvarname1", origin: "origin1", comment: "comment1"})
MERGE (library)-[:CONTAINS_CONCEPT]->(item_root1)
MERGE (item_root1)-[r1:LATEST_FINAL]->(item_value1)
MERGE (item_root1)-[hv2:HAS_VERSION]->(item_value1)
MERGE (item_root1)-[:LATEST]->(item_value1)
MERGE (item_root1)-[:HAS_DESCRIPTION]->(odm_description_root1)
SET hv2 = final_properties

MERGE (item_root2:ConceptRoot:OdmItemRoot {uid: "odm_item2"})
MERGE (item_value2:ConceptValue:OdmItemValue {oid: "oid2", name: "name2", datatype: "datatype2", length: 2, significant_digits: 2, sas_field_name: "sasfieldname2", sds_var_name: "sdsvarname2", origin: "origin2", comment: "comment2"})
MERGE (library)-[:CONTAINS_CONCEPT]->(item_root2)
MERGE (item_root2)-[r2:LATEST_FINAL]->(item_value2)
MERGE (item_root2)-[hv3:HAS_VERSION]->(item_value2)
MERGE (item_root2)-[:LATEST]->(item_value2)
MERGE (item_root2)-[:HAS_DESCRIPTION]->(odm_description_root1)
SET hv3 = final_properties
"""

STARTUP_ODM_FORMS = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_description_root1:ConceptRoot:OdmDescriptionRoot {uid: "odm_description1"})
MERGE (odm_description_value1:ConceptValue:OdmDescriptionValue {name: "name1", language: "ENG", description: "description1", instruction: "instruction1"})
MERGE (odm_description_root1)-[ld1:LATEST_FINAL]->(odm_description_value1)
MERGE (odm_description_root1)-[l1:LATEST]->(odm_description_value1)
CREATE (odm_description_root1)-[hv1:HAS_VERSION]->(odm_description_value1)
SET hv1 = final_properties

MERGE (odm_form_root1:ConceptRoot:OdmFormRoot {uid: "odm_form1"})
MERGE (odm_form_value1:ConceptValue:OdmFormValue {oid: "oid1", name: "name1", repeating: true})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_form_root1)
MERGE (odm_form_root1)-[r1:LATEST_FINAL]->(odm_form_value1)
MERGE (odm_form_root1)-[hv2:HAS_VERSION]->(odm_form_value1)
MERGE (odm_form_root1)-[:LATEST]->(odm_form_value1)
MERGE (odm_form_root1)-[:HAS_DESCRIPTION]->(odm_description_root1)
SET hv2 = final_properties

MERGE (odm_form_root2:ConceptRoot:OdmFormRoot {uid: "odm_form2"})
MERGE (odm_form_value2:ConceptValue:OdmFormValue {oid: "oid2", name: "name2", repeating: true})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_form_root2)
MERGE (odm_form_root2)-[r2:LATEST_FINAL]->(odm_form_value2)
MERGE (odm_form_root2)-[hv3:HAS_VERSION]->(odm_form_value2)
MERGE (odm_form_root2)-[:LATEST]->(odm_form_value2)
MERGE (odm_form_root2)-[:HAS_DESCRIPTION]->(odm_description_root1)
SET hv3 = final_properties
"""

STARTUP_ODM_STUDY_EVENTS = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties

MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (StudyEventRoot:ConceptRoot:OdmStudyEventRoot {uid: "odm_study_event1"})
MERGE (StudyEventValue:ConceptValue:OdmStudyEventValue {oid: "oid1", name: "name1", effective_date: date(), retired_date: date(), description: "description", display_in_tree: true})
MERGE (library)-[:CONTAINS_CONCEPT]->(StudyEventRoot)
MERGE (StudyEventRoot)-[r1:LATEST_FINAL]->(StudyEventValue)
MERGE (StudyEventRoot)-[r2:LATEST]->(StudyEventValue)
MERGE (StudyEventRoot)-[hv:HAS_VERSION]->(StudyEventValue)
SET hv = final_properties
"""

STARTUP_ODM_XML_EXPORTER = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
author_id: "unknown-user",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties

MERGE (Library:Library {name:"Sponsor", is_editable:true})
MERGE (Library)-[:CONTAINS_CATALOUGE]->(Catalogue:CTCatalogue {name:"SDTM CT"})

WITH *
MATCH (oa:OdmAliasRoot {uid: "odm_alias1"})
MATCH (ofr:OdmFormRoot {uid: "odm_form1"})
MATCH (oigr:OdmItemGroupRoot {uid: "odm_item_group1"})
MATCH (oir:OdmItemRoot {uid: "odm_item1"})
MERGE (ofr)-[:HAS_ALIAS]->(oa)
MERGE (oigr)-[:HAS_ALIAS]->(oa)
MERGE (oir)-[:HAS_ALIAS]->(oa)

WITH *
MATCH (ItemRoot:OdmItemRoot {uid: "odm_item1"})
MATCH (UnitRoot:UnitDefinitionRoot {uid: "unit_definition_root1"})
MERGE (ItemRoot)-[:HAS_UNIT_DEFINITION]->(UnitRoot)

MERGE (CodelistRoot:CTCodelistRoot {uid: "codelist_root1"})
MERGE (Library)-[:CONTAINS_CODELIST]->(CodelistRoot)
MERGE (Catalogue)-[:HAS_CODELIST]->(CodelistRoot)
MERGE (ItemRoot)-[:HAS_CODELIST]->(CodelistRoot)

WITH *
MATCH (CTTerm:CTTermRoot {uid: "term1"})
MERGE (ItemRoot)-[:HAS_CODELIST_TERM {order: "1", mandatory: false, display_text: "custom text"}]->(CTTerm)

MERGE (CodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(CodelistAttrRoot:CTCodelistAttributesRoot)
MERGE (CodelistAttrValue:CTCodelistAttributesValue {name:"name1", definition:"definition1", preferred_term: "preferred_term1", synonyms: "synonyms1", submission_value: "submission_value1", extensible:false})
MERGE (CodelistAttrRoot)-[lf1:LATEST_FINAL]->(CodelistAttrValue)
MERGE (CodelistAttrRoot)-[hv1:HAS_VERSION]->(CodelistAttrValue)
MERGE (CodelistAttrRoot)-[:LATEST]->(CodelistAttrValue)
SET hv1 = final_properties

MERGE (Library)-[:CONTAINS_TERM]->(TermRoot:CTTermRoot {concept_id: "concept_id1", uid: "uid1"})
MERGE (CodelistRoot)-[:HAS_TERM]->(TermRoot)
MERGE (TermRoot)-[:HAS_ATTRIBUTES_ROOT]->(TermAttrRoot:CTTermAttributesRoot)
MERGE (TermAttrValue:CTTermAttributesValue {code_submission_value: "code_submission_value1", concept_id: "concept_id1", definition: "definition1", preferred_term: "preferred_term1", synonyms: "synonyms1"})
MERGE (TermAttrRoot)-[lf2:LATEST_FINAL]->(TermAttrValue)
MERGE (TermAttrRoot)-[hv2:HAS_VERSION]->(TermAttrValue)
MERGE (TermAttrRoot)-[:LATEST]->(TermAttrValue)
SET hv2 = final_properties

WITH *
MATCH (ConditionRoot1:OdmConditionRoot {uid: "odm_condition1"})
MATCH (ConditionRoot2:OdmConditionRoot {uid: "odm_condition2"})
MATCH (FormalExpression:OdmFormalExpressionRoot {uid: "odm_formal_expression1"})
MERGE (ConditionRoot1)-[:HAS_FORMAL_EXPRESSION]->(FormalExpression)
MERGE (ConditionRoot2)-[:HAS_FORMAL_EXPRESSION]->(FormalExpression)

WITH *
MATCH (MethodRoot1:OdmMethodRoot {uid: "odm_method1"})
MATCH (MethodRoot2:OdmMethodRoot {uid: "odm_method2"})
MATCH (FormalExpression:OdmFormalExpressionRoot {uid: "odm_formal_expression1"})
MERGE (MethodRoot1)-[:HAS_FORMAL_EXPRESSION]->(FormalExpression)
MERGE (MethodRoot2)-[:HAS_FORMAL_EXPRESSION]->(FormalExpression)

WITH *
MATCH (ItemGroupRoot:OdmItemGroupRoot {uid: "odm_item_group1"})
MATCH (ItemRoot:OdmItemRoot {uid: "odm_item1"})
MERGE (ItemGroupRoot)-[:ITEM_REF {order_number: "1", mandatory: true, collection_exception_condition_oid: "oid1", method_oid: "oid1", vendor: '{"attributes": [{"uid": "odm_vendor_attribute3", "value": "No"}]}'}]->(ItemRoot)

WITH *
MATCH (FormRoot:OdmFormRoot {uid: "odm_form1"})
MATCH (ItemGroupRoot:OdmItemGroupRoot {uid: "odm_item_group1"})
MATCH (VendorElementRoot:OdmVendorElementRoot {uid: "odm_vendor_element1"})
MERGE (FormRoot)-[:ITEM_GROUP_REF {order_number: "1", mandatory: true, collection_exception_condition_oid: "oid2", vendor: '{"attributes": [{"uid": "odm_vendor_attribute3", "value": "No"}]}'}]->(ItemGroupRoot)
MERGE (FormRoot)-[:HAS_VENDOR_ELEMENT]->(VendorElementRoot)

WITH *
MATCH (StudyEventRoot:OdmStudyEventRoot {uid: "odm_study_event1"})
MATCH (FormRoot:OdmFormRoot {uid: "odm_form1"})
MERGE (StudyEventRoot)-[:FORM_REF {order_number: "1", mandatory: true, locked: false, collection_exception_condition_oid: "oid1"}]->(FormRoot)
"""

STARTUP_ODM_VENDOR_NAMESPACES = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (odm_vendor_namespace_root1:ConceptRoot:OdmVendorNamespaceRoot {uid: "odm_vendor_namespace1"})
MERGE (odm_vendor_namespace_value1:ConceptValue:OdmVendorNamespaceValue {name: "nameOne", prefix: "prefix", url: "url1"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_vendor_namespace_root1)
MERGE (odm_vendor_namespace_root1)-[r1:LATEST_FINAL]->(odm_vendor_namespace_value1)
MERGE (odm_vendor_namespace_root1)-[:LATEST]->(odm_vendor_namespace_value1)
MERGE (odm_vendor_namespace_root1)-[hv1:HAS_VERSION]->(odm_vendor_namespace_value1)
SET hv1 = final_properties

MERGE (odm_vendor_namespace_root2:ConceptRoot:OdmVendorNamespaceRoot {uid: "odm_vendor_namespace2"})
MERGE (odm_vendor_namespace_value2:ConceptValue:OdmVendorNamespaceValue {name: "OSB", prefix: "osb", url: "url2"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_vendor_namespace_root2)
MERGE (odm_vendor_namespace_root2)-[r2:LATEST_FINAL]->(odm_vendor_namespace_value2)
MERGE (odm_vendor_namespace_root2)-[:LATEST]->(odm_vendor_namespace_value2)
MERGE (odm_vendor_namespace_root2)-[hv2:HAS_VERSION]->(odm_vendor_namespace_value2)
SET hv2 = final_properties
"""

STARTUP_ODM_VENDOR_ELEMENTS = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

WITH *
MATCH (odm_vendor_namespace_root1:ConceptRoot:OdmVendorNamespaceRoot {uid: "odm_vendor_namespace1"})
MATCH (odm_vendor_namespace_root2:ConceptRoot:OdmVendorNamespaceRoot {uid: "odm_vendor_namespace2"})

MERGE (odm_vendor_element_root1:ConceptRoot:OdmVendorElementRoot {uid: "odm_vendor_element1"})
MERGE (odm_vendor_element_value1:ConceptValue:OdmVendorElementValue {name: "nameOne", compatible_types: '["FormDef","ItemGroupDef","ItemDef"]'})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_vendor_element_root1)
MERGE (odm_vendor_element_root1)-[r1:LATEST_FINAL]->(odm_vendor_element_value1)
MERGE (odm_vendor_element_root1)-[hv1:HAS_VERSION]->(odm_vendor_element_value1)
MERGE (odm_vendor_element_root1)-[:LATEST]->(odm_vendor_element_value1)
MERGE (odm_vendor_namespace_root1)-[:HAS_VENDOR_ELEMENT]->(odm_vendor_element_root1)
SET hv1 = final_properties

MERGE (odm_vendor_element_root2:ConceptRoot:OdmVendorElementRoot {uid: "odm_vendor_element2"})
MERGE (odm_vendor_element_value2:ConceptValue:OdmVendorElementValue {name: "nameTwo", compatible_types: '["FormDef","ItemGroupDef","ItemDef"]'})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_vendor_element_root2)
MERGE (odm_vendor_element_root2)-[r2:LATEST_FINAL]->(odm_vendor_element_value2)
MERGE (odm_vendor_element_root2)-[hv2:HAS_VERSION]->(odm_vendor_element_value2)
MERGE (odm_vendor_element_root2)-[:LATEST]->(odm_vendor_element_value2)
MERGE (odm_vendor_namespace_root2)-[:HAS_VENDOR_ELEMENT]->(odm_vendor_element_root2)
SET hv2 = final_properties

MERGE (odm_vendor_element_root3:ConceptRoot:OdmVendorElementRoot {uid: "odm_vendor_element3"})
MERGE (odm_vendor_element_value3:ConceptValue:OdmVendorElementValue {name: "nameThree", compatible_types: '["FormDef","ItemGroupDef","ItemDef"]'})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_vendor_element_root3)
MERGE (odm_vendor_element_root3)-[r3:LATEST_FINAL]->(odm_vendor_element_value3)
MERGE (odm_vendor_element_root3)-[hv3:HAS_VERSION]->(odm_vendor_element_value3)
MERGE (odm_vendor_element_root3)-[:LATEST]->(odm_vendor_element_value3)
MERGE (odm_vendor_namespace_root3)-[:HAS_VENDOR_ELEMENT]->(odm_vendor_element_root3)
SET hv3 = final_properties

MERGE (odm_vendor_element_root4:ConceptRoot:OdmVendorElementRoot {uid: "odm_vendor_element4"})
MERGE (odm_vendor_element_value4:ConceptValue:OdmVendorElementValue {name: "nameThree", compatible_types: '["NonCompatibleVendor"]'})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_vendor_element_root4)
MERGE (odm_vendor_element_root4)-[r4:LATEST_FINAL]->(odm_vendor_element_value4)
MERGE (odm_vendor_element_root4)-[hv4:HAS_VERSION]->(odm_vendor_element_value4)
MERGE (odm_vendor_element_root4)-[:LATEST]->(odm_vendor_element_value4)
MERGE (odm_vendor_namespace_root4)-[:HAS_VENDOR_ELEMENT]->(odm_vendor_element_root4)
SET hv4 = final_properties
"""

STARTUP_ODM_VENDOR_ATTRIBUTES = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

WITH *
MATCH (odm_vendor_namespace_root:ConceptRoot:OdmVendorNamespaceRoot {uid: "odm_vendor_namespace1"})
MATCH (odm_vendor_element_root1:OdmVendorElementRoot {uid:"odm_vendor_element1"})
MATCH (odm_vendor_element_root3:OdmVendorElementRoot {uid:"odm_vendor_element3"})

MERGE (odm_vendor_attribute_root1:ConceptRoot:OdmVendorAttributeRoot {uid: "odm_vendor_attribute1"})
MERGE (odm_vendor_attribute_value1:ConceptValue:OdmVendorAttributeValue {name: "nameOne", data_type: "string", value_regex: "^[a-zA-Z]+$"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_vendor_attribute_root1)
MERGE (odm_vendor_attribute_root1)-[r1:LATEST_FINAL]->(odm_vendor_attribute_value1)
MERGE (odm_vendor_attribute_root1)-[hv1:HAS_VERSION]->(odm_vendor_attribute_value1)
MERGE (odm_vendor_attribute_root1)-[:LATEST]->(odm_vendor_attribute_value1)
MERGE (odm_vendor_element_root1)-[:HAS_VENDOR_ATTRIBUTE {value: "value1"}]->(odm_vendor_attribute_root1)
SET hv1 = final_properties

MERGE (odm_vendor_attribute_root2:ConceptRoot:OdmVendorAttributeRoot {uid: "odm_vendor_attribute2"})
MERGE (odm_vendor_attribute_value2:ConceptValue:OdmVendorAttributeValue {name: "nameTwo", data_type: "string"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_vendor_attribute_root2)
MERGE (odm_vendor_attribute_root2)-[r2:LATEST_FINAL]->(odm_vendor_attribute_value2)
MERGE (odm_vendor_attribute_root2)-[hv2:HAS_VERSION]->(odm_vendor_attribute_value2)
MERGE (odm_vendor_attribute_root2)-[:LATEST]->(odm_vendor_attribute_value2)
MERGE (odm_vendor_element_root1)-[:HAS_VENDOR_ATTRIBUTE {value: "value2"}]->(odm_vendor_attribute_root2)
SET hv2 = final_properties

MERGE (odm_vendor_attribute_root3:ConceptRoot:OdmVendorAttributeRoot {uid: "odm_vendor_attribute3"})
MERGE (odm_vendor_attribute_value3:ConceptValue:OdmVendorAttributeValue {name: "nameThree", compatible_types: '["FormDef","ItemGroupDef","ItemDef","ItemGroupRef","ItemRef"]', data_type: "string", value_regex: "^[a-zA-Z]+$"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_vendor_attribute_root3)
MERGE (odm_vendor_attribute_root3)-[r4:LATEST_FINAL]->(odm_vendor_attribute_value3)
MERGE (odm_vendor_attribute_root3)-[hv4:HAS_VERSION]->(odm_vendor_attribute_value3)
MERGE (odm_vendor_attribute_root3)-[:LATEST]->(odm_vendor_attribute_value3)
MERGE (odm_vendor_namespace_root)-[:HAS_VENDOR_ATTRIBUTE {value: "value3"}]->(odm_vendor_attribute_root3)
SET hv4 = final_properties

MERGE (odm_vendor_attribute_root4:ConceptRoot:OdmVendorAttributeRoot {uid: "odm_vendor_attribute4"})
MERGE (odm_vendor_attribute_value4:ConceptValue:OdmVendorAttributeValue {name: "nameFour", compatible_types: '["FormDef","ItemGroupDef","ItemDef","ItemGroupRef","ItemRef"]', data_type: "string"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_vendor_attribute_root4)
MERGE (odm_vendor_attribute_root4)-[r5:LATEST_FINAL]->(odm_vendor_attribute_value4)
MERGE (odm_vendor_attribute_root4)-[hv5:HAS_VERSION]->(odm_vendor_attribute_value4)
MERGE (odm_vendor_attribute_root4)-[:LATEST]->(odm_vendor_attribute_value4)
MERGE (odm_vendor_namespace_root)-[:HAS_VENDOR_ATTRIBUTE {value: "value4"}]->(odm_vendor_attribute_root4)
SET hv5 = final_properties

MERGE (odm_vendor_attribute_root5:ConceptRoot:OdmVendorAttributeRoot {uid: "odm_vendor_attribute5"})
MERGE (odm_vendor_attribute_value5:ConceptValue:OdmVendorAttributeValue {name: "nameFive", compatible_types: '["NonCompatibleVendor"]', data_type: "string"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_vendor_attribute_root5)
MERGE (odm_vendor_attribute_root5)-[r6:LATEST_FINAL]->(odm_vendor_attribute_value5)
MERGE (odm_vendor_attribute_root5)-[hv6:HAS_VERSION]->(odm_vendor_attribute_value5)
MERGE (odm_vendor_attribute_root5)-[:LATEST]->(odm_vendor_attribute_value5)
MERGE (odm_vendor_namespace_root)-[:HAS_VENDOR_ATTRIBUTE {value: "value5"}]->(odm_vendor_attribute_root5)
SET hv6 = final_properties

MERGE (odm_vendor_attribute_root7:ConceptRoot:OdmVendorAttributeRoot {uid: "odm_vendor_attribute7"})
MERGE (odm_vendor_attribute_value7:ConceptValue:OdmVendorAttributeValue {name: "nameSeven", data_type: "string"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_vendor_attribute_root7)
MERGE (odm_vendor_attribute_root7)-[r7:LATEST_FINAL]->(odm_vendor_attribute_value7)
MERGE (odm_vendor_attribute_root7)-[hv7:HAS_VERSION]->(odm_vendor_attribute_value7)
MERGE (odm_vendor_attribute_root7)-[:LATEST]->(odm_vendor_attribute_value7)
MERGE (odm_vendor_element_root3)-[:HAS_VENDOR_ATTRIBUTE {value: "value7"}]->(odm_vendor_attribute_root7)
SET hv7 = final_properties
"""

STARTUP_CRITERIA = """
WITH
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties
// Create codelist
MERGE (cdisc:Library {name:"CDISC", is_editable: True})
MERGE (catalogue:CTCatalogue {name:"SDTM CT"})
MERGE (cdisc)-[:CONTAINS_CATALOGUE]->(catalogue)
MERGE (cdisc)-[:CONTAINS_CODELIST]->(codelist_root:CTCodelistRoot {uid:"CTCodelist_000001"})
MERGE (catalogue)-[:HAS_CODELIST]-(codelist_root)
// Create Inclusion criteria term
CREATE (cdisc)-[:CONTAINS_TERM]->(incr:CTTermRoot {uid: "C25532"})-[:HAS_NAME_ROOT]->
(incnr:CTTermNameRoot)-[:LATEST]->(incnv:CTTermNameValue {
name: "INCLUSION CRITERIA",
name_sentence_case: "Inclusion Criteria"})
MERGE (incnr)-[incnrel:LATEST_FINAL]->(incnv)
MERGE (incnr)-[incnrel_hv:HAS_VERSION]->(incnv)
SET incnrel_hv = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(incr)
CREATE (incar:CTTermAttributesRoot)-[:LATEST]->(incav:CTTermAttributesValue {
code_submission_value: "Inclusion Criteria",
definition: "Inclusion Criteria",
preferred_term: "Inclusion Criteria"})
MERGE (incr)-[:HAS_ATTRIBUTES_ROOT]->(incar)-[incarel:LATEST_FINAL]->(incav)
MERGE (incar)-[incarel_hv:HAS_VERSION]->(incav)
SET incarel_hv = final_properties
// Create Exclusion criteria term
CREATE (cdisc)-[:CONTAINS_TERM]->(excr:CTTermRoot {uid: "C25370"})-[:HAS_NAME_ROOT]->
(excnr:CTTermNameRoot)-[:LATEST]->(excnv:CTTermNameValue {
name: "EXCLUSION CRITERIA",
name_sentence_case: "Exclusion Criteria"})
MERGE (excnr)-[excnrel:LATEST_FINAL]->(excnv)
MERGE (excnr)-[excnrel_hv:HAS_VERSION]->(excnv)
SET excnrel_hv = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(excr)
CREATE (excar:CTTermAttributesRoot)-[:LATEST]->(excav:CTTermAttributesValue {
code_submission_value: "Exclusion Criteria",
definition: "Exclusion Criteria",
preferred_term: "Exclusion Criteria"})
MERGE (excr)-[:HAS_ATTRIBUTES_ROOT]->(excar)-[excarel:LATEST_FINAL]->(excav)
MERGE (excar)-[excarel_hv:HAS_VERSION]->(excav)
SET excarel_hv = final_properties
"""

STARTUP_TIME_POINTS = """
WITH {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties
MATCH (lib {name:"Sponsor"})
MERGE (lib)-[:CONTAINS_CONCEPT]->(unit_def_root:ConceptRoot:UnitDefinitionRoot {uid:"UnitDefinition_000001"})-[:LATEST]-
(unit_def_value:ConceptValue:UnitDefinitionValue {
name:"name_1",
unit_ct_uid: "unit1-ct-uid",
convertible_unit: true,
display_unit: true,
master_unit: true,
si_unit: true,
us_conventional_unit: true,
use_complex_unit_conversion: true,
unit_dimension_uid: "unit1-dimension",
legacy_code: "unit1-legacy-code",
use_molecular_weight: false,
conversion_factor_to_master: 1.0
})
MERGE (unit_def_root)-[unit_final1:LATEST_FINAL]-(unit_def_value)
MERGE (unit_def_root)-[unit_hv1:HAS_VERSION]-(unit_def_value)
SET unit_hv1 = final_properties
MERGE (lib)-[:CONTAINS_CONCEPT]->(numeric_value_root:ConceptRoot:SimpleConceptRoot:NumericValueRoot {uid:"NumericValue_000001"})-[:LATEST]-(numeric_value_value:ConceptValue:SimpleConceptValue:NumericValue {
name:"1.23",
value:1.23})
MERGE (numeric_value_root)-[numeric_value_final1:LATEST_FINAL]-(numeric_value_value)
MERGE (numeric_value_root)-[numeric_value_hv1:HAS_VERSION]-(numeric_value_value)
SET numeric_value_hv1 = final_properties
MERGE (lib)-[:CONTAINS_CONCEPT]->(numeric_value_root2:ConceptRoot:SimpleConceptRoot:NumericValueRoot {uid:"NumericValue_000002"})-[:LATEST]-(numeric_value_value2:ConceptValue:SimpleConceptValue:NumericValue {
name:"3.21",
value:3.21})
MERGE (numeric_value_root2)-[numeric_value_final2:LATEST_FINAL]-(numeric_value_value2)
MERGE (numeric_value_root2)-[numeric_value_hv2:HAS_VERSION]-(numeric_value_value2)
SET numeric_value_hv2 = final_properties
MERGE (cc:CTCatalogue {name: "SDTM CT"})-[:HAS_CODELIST]->(cr:CTCodelistRoot {uid:"CTCodelistRoot_000001"})-[:HAS_NAME_ROOT]
->(codelist_ver_root:CTCodelistNameRoot)-[:LATEST_FINAL]->(codelist_ver_value:CTCodelistNameValue {name:"codelist_name"})
CREATE (codelist_ver_root)-[:LATEST]->(codelist_ver_value)
MERGE (editable_lib:Library{ name:"Sponsor", is_editable:true})
MERGE (editable_lib)-[:CONTAINS_CODELIST]->(cr)

MERGE (cr)-[has_term:HAS_TERM]->(term_root:CTTermRoot {uid:"CTTermRoot_000001"})-[:HAS_NAME_ROOT]->
    (term_ver_root:CTTermNameRoot)-[:LATEST]-(term_ver_value:CTTermNameValue 
        {name:"term_value_name1", name_sentence_case:"term_value_name_sentence_case"})
MERGE (editable_lib)-[:CONTAINS_TERM]->(term_root)
MERGE (term_ver_root)-[lf:LATEST_FINAL]->(term_ver_value)
set has_term.order = 1
set lf.change_description = "Approved version"
set lf.start_date = datetime()
set lf.status = "Final"
set lf.author_id = "unknown-user"
set lf.version = "1.0"
"""

STARTUP_NUMERIC_VALUES_WITH_UNITS = """
MERGE (lib:Library{name:"Sponsor", is_editable:true})

WITH {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties
MATCH (lib {name:"Sponsor"})
MERGE (lib)-[:CONTAINS_CONCEPT]->(unit_def_root:ConceptRoot:UnitDefinitionRoot {uid:"UnitDefinition_000001"})-[:LATEST]-
(unit_def_value:ConceptValue:UnitDefinitionValue {
name:"name_1",
unit_ct_uid: "unit1-ct-uid",
convertible_unit: true,
display_unit: true,
master_unit: true,
si_unit: true,
us_conventional_unit: true,
use_complex_unit_conversion: true,
unit_dimension_uid: "unit1-dimension",
legacy_code: "unit1-legacy-code",
use_molecular_weight: false,
conversion_factor_to_master: 1.0
})

MERGE (unit_def_root)-[unit_final1:LATEST_FINAL]-(unit_def_value)
MERGE (unit_def_root)-[unit_hv1:HAS_VERSION]-(unit_def_value)
SET unit_hv1 = final_properties

MERGE (lib)-[:CONTAINS_CONCEPT]->(numeric_value_root:ConceptRoot:SimpleConceptRoot:NumericValueRoot:NumericValueWithUnitRoot {uid:"NumericValueWithUnit_000001"})-[:LATEST]-(numeric_value_value:ConceptValue:SimpleConceptValue:NumericValue:NumericValueWithUnitValue {
name:"1.23 [UnitDefinition_000001]",
value:1.23})
MERGE (numeric_value_root)-[numeric_value_final1:LATEST_FINAL]-(numeric_value_value)
MERGE (numeric_value_root)-[numeric_value_hv1:HAS_VERSION]-(numeric_value_value)
MERGE (numeric_value_value)-[:HAS_UNIT_DEFINITION]->(unit_def_root)
SET numeric_value_hv1 = final_properties

MERGE (lib)-[:CONTAINS_CONCEPT]->(numeric_value_root2:ConceptRoot:SimpleConceptRoot:NumericValueRoot:NumericValueWithUnitRoot {uid:"NumericValueWithUnit_000002"})-[:LATEST]-(numeric_value_value2:ConceptValue:SimpleConceptValue:NumericValue:NumericValueWithUnitValue {
name:"3.21 [UnitDefinition_000001]",
value:3.21})
MERGE (numeric_value_root2)-[numeric_value_final2:LATEST_FINAL]-(numeric_value_value2)
MERGE (numeric_value_root2)-[numeric_value_hv2:HAS_VERSION]-(numeric_value_value2)
MERGE (numeric_value_value2)-[:HAS_UNIT_DEFINITION]->(unit_def_root)
SET numeric_value_hv2 = final_properties

"""

STARTUP_ACTIVITY_INSTANCES_CT_INIT = """
WITH
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties

MERGE (library:Library {name:"CDISC", is_editable: false})
MERGE (catalogue:CTCatalogue {name:"SDTM"})
MERGE (library)-[:CONTAINS_CATALOGUE]->(catalogue)
MERGE (library)-[:CONTAINS_CODELIST]->(codelist_root:CTCodelistRoot {uid:"CTCodelist_000001"})
MERGE (catalogue)-[:HAS_CODELIST]-(codelist_root)
CREATE (library)-[:CONTAINS_TERM]->(sdtm_variable1:CTTermRoot {uid: "sdtm_variable_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root1:CTTermNameRoot)-[:LATEST]->(term_ver_value1:CTTermNameValue {
name: "sdtm_variable_name1",
name_sentence_case: "sdtm_variable_name1"})
MERGE (term_ver_root1)-[latest_final1:LATEST_FINAL]->(term_ver_value1)
MERGE (term_ver_root1)-[has_version1:HAS_VERSION]->(term_ver_value1)
SET has_version1 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_variable1)

CREATE (library)-[:CONTAINS_TERM]->(sdtm_subcat1:CTTermRoot {uid: "sdtm_subcat_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root2:CTTermNameRoot)-[:LATEST]->(term_ver_value2:CTTermNameValue {
name: "sdtm_subcat_name1",
name_sentence_case: "sdtm_subcat_name1"})
MERGE (term_ver_root2)-[latest_final2:LATEST_FINAL]->(term_ver_value2)
MERGE (term_ver_root2)-[has_version2:HAS_VERSION]->(term_ver_value2)
SET has_version2 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_subcat1)

CREATE (library)-[:CONTAINS_TERM]->(sdtm_cat1:CTTermRoot {uid: "sdtm_cat_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root3:CTTermNameRoot)-[:LATEST]->(term_ver_value3:CTTermNameValue {
name: "sdtm_cat_name1",
name_sentence_case: "sdtm_cat_name1"})
MERGE (term_ver_root3)-[latest_final3:LATEST_FINAL]->(term_ver_value3)
MERGE (term_ver_root3)-[has_version3:HAS_VERSION]->(term_ver_value3)
SET has_version3 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_cat1)

CREATE (library)-[:CONTAINS_TERM]->(sdtm_domain1:CTTermRoot {uid: "sdtm_domain_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root4:CTTermNameRoot)-[:LATEST]->(term_ver_value4:CTTermNameValue {
name: "sdtm_domain_name1",
name_sentence_case: "sdtm_domain_name1"})
MERGE (term_ver_root4)-[latest_final4:LATEST_FINAL]->(term_ver_value4)
MERGE (term_ver_root4)-[has_version4:HAS_VERSION]->(term_ver_value4)
SET has_version4 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_domain1)

CREATE (library)-[:CONTAINS_TERM]->(sdtm_variable2:CTTermRoot {uid: "sdtm_variable_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root5:CTTermNameRoot)-[:LATEST]->(term_ver_value5:CTTermNameValue {
name: "sdtm_variable_name2",
name_sentence_case: "sdtm_variable_name2"})
MERGE (term_ver_root5)-[latest_final5:LATEST_FINAL]->(term_ver_value5)
MERGE (term_ver_root5)-[has_version5:HAS_VERSION]->(term_ver_value5)
SET has_version5 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_variable2)

CREATE (library)-[:CONTAINS_TERM]->(sdtm_subcat2:CTTermRoot {uid: "sdtm_subcat_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root6:CTTermNameRoot)-[:LATEST]->(term_ver_value6:CTTermNameValue {
name: "sdtm_subcat_name2",
name_sentence_case: "sdtm_subcat_name2"})
MERGE (term_ver_root6)-[latest_final6:LATEST_FINAL]->(term_ver_value6)
MERGE (term_ver_root6)-[has_version6:HAS_VERSION]->(term_ver_value6)
SET has_version6 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_subcat2)

CREATE (library)-[:CONTAINS_TERM]->(sdtm_cat2:CTTermRoot {uid: "sdtm_cat_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root7:CTTermNameRoot)-[:LATEST]->(term_ver_value7:CTTermNameValue {
name: "sdtm_cat_name2",
name_sentence_case: "sdtm_cat_name2"})
MERGE (term_ver_root7)-[latest_final7:LATEST_FINAL]->(term_ver_value7)
MERGE (term_ver_root7)-[has_version7:HAS_VERSION]->(term_ver_value7)
SET has_version7 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_cat2)

CREATE (library)-[:CONTAINS_TERM]->(sdtm_domain2:CTTermRoot {uid: "sdtm_domain_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root8:CTTermNameRoot)-[:LATEST]->(term_ver_value8:CTTermNameValue {
name: "sdtm_domain_name2",
name_sentence_case: "sdtm_domain_name2"})
MERGE (term_ver_root8)-[latest_final8:LATEST_FINAL]->(term_ver_value8)
MERGE (term_ver_root8)-[has_version8:HAS_VERSION]->(term_ver_value8)
SET has_version8 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_domain2)

CREATE (library)-[:CONTAINS_TERM]->(specimen1:CTTermRoot {uid: "specimen_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root9:CTTermNameRoot)-[:LATEST]->(term_ver_value9:CTTermNameValue {
name: "specimen_name1",
name_sentence_case: "specimen_name_sentence_case1"})
MERGE (term_ver_root9)-[latest_final9:LATEST_FINAL]->(term_ver_value9)
MERGE (term_ver_root9)-[has_version9:HAS_VERSION]->(term_ver_value9)
SET has_version9 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(specimen1)

CREATE (library)-[:CONTAINS_TERM]->(specimen2:CTTermRoot {uid: "specimen_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root10:CTTermNameRoot)-[:LATEST]->(term_ver_value10:CTTermNameValue {
name: "specimen_name2",
name_sentence_case: "specimen_name_sentence_case2"})
MERGE (term_ver_root10)-[latest_final10:LATEST_FINAL]->(term_ver_value10)
MERGE (term_ver_root10)-[has_version10:HAS_VERSION]->(term_ver_value10)
SET has_version10 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(specimen2)

CREATE (library)-[:CONTAINS_TERM]->(test_code1:CTTermRoot {uid: "test_code_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root11:CTTermNameRoot)-[:LATEST]->(term_ver_value11:CTTermNameValue {
name: "test_code_name1",
name_sentence_case: "test_code_name_sentence_case1"})
MERGE (term_ver_root11)-[latest_final11:LATEST_FINAL]->(term_ver_value11)
MERGE (term_ver_root11)-[has_version11:HAS_VERSION]->(term_ver_value11)
SET has_version11 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(test_code1)

CREATE (library)-[:CONTAINS_TERM]->(test_code2:CTTermRoot {uid: "test_code_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root12:CTTermNameRoot)-[:LATEST]->(term_ver_value12:CTTermNameValue {
name: "test_code_name2",
name_sentence_case: "test_code_name_sentence_case2"})
MERGE (term_ver_root12)-[latest_final12:LATEST_FINAL]->(term_ver_value12)
MERGE (term_ver_root12)-[has_version12:HAS_VERSION]->(term_ver_value12)
SET has_version12 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(test_code2)

CREATE (library)-[:CONTAINS_TERM]->(unit_dimension1:CTTermRoot {uid: "unit_dimension_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root13:CTTermNameRoot)-[:LATEST]->(term_ver_value13:CTTermNameValue {
name: "unit_dimension_name1",
name_sentence_case: "unit_dimension_name_sentence_case1"})
MERGE (term_ver_root13)-[latest_final13:LATEST_FINAL]->(term_ver_value13)
MERGE (term_ver_root13)-[has_version13:HAS_VERSION]->(term_ver_value13)
SET has_version13 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(unit_dimension1)

CREATE (library)-[:CONTAINS_TERM]->(unit_dimension2:CTTermRoot {uid: "unit_dimension_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root14:CTTermNameRoot)-[:LATEST]->(term_ver_value14:CTTermNameValue {
name: "unit_dimension_name2",
name_sentence_case: "unit_dimension_name_sentence_case2"})
MERGE (term_ver_root14)-[latest_final14:LATEST_FINAL]->(term_ver_value14)
MERGE (term_ver_root14)-[has_version14:HAS_VERSION]->(term_ver_value14)
SET has_version14 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(unit_dimension2)

CREATE (library)-[:CONTAINS_TERM]->(categoric_response_value1:CTTermRoot {uid: "categoric_response_value_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root15:CTTermNameRoot)-[:LATEST]->(term_ver_value15:CTTermNameValue {
name: "categoric_response_value_name1",
name_sentence_case: "categoric_response_value_name_sentence_case1"})
MERGE (term_ver_root15)-[latest_final15:LATEST_FINAL]->(term_ver_value15)
MERGE (term_ver_root15)-[has_version15:HAS_VERSION]->(term_ver_value15)
SET has_version15 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(categoric_response_value1)

CREATE (library)-[:CONTAINS_TERM]->(categoric_response_value2:CTTermRoot {uid: "categoric_response_value_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root16:CTTermNameRoot)-[:LATEST]->(term_ver_value16:CTTermNameValue {
name: "categoric_response_value_name2",
name_sentence_case: "categoric_response_value_name_sentence_case2"})
MERGE (term_ver_root16)-[latest_final16:LATEST_FINAL]->(term_ver_value16)
MERGE (term_ver_root16)-[has_version16:HAS_VERSION]->(term_ver_value16)
SET has_version16 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(categoric_response_value2)

CREATE (library)-[:CONTAINS_TERM]->(categoric_response_list1:CTTermRoot {uid: "categoric_response_list_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root17:CTTermNameRoot)-[:LATEST]->(term_ver_value17:CTTermNameValue {
name: "categoric_response_list_name1",
name_sentence_case: "categoric_response_list_name_sentence_case1"})
MERGE (term_ver_root17)-[latest_final17:LATEST_FINAL]->(term_ver_value17)
MERGE (term_ver_root17)-[has_version17:HAS_VERSION]->(term_ver_value17)
SET has_version17 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(categoric_response_list1)

CREATE (library)-[:CONTAINS_TERM]->(categoric_response_list2:CTTermRoot {uid: "categoric_response_list_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root18:CTTermNameRoot)-[:LATEST]->(term_ver_value18:CTTermNameValue {
name: "categoric_response_list_name2",
name_sentence_case: "categoric_response_list_name_sentence_case2"})
MERGE (term_ver_root18)-[latest_final18:LATEST_FINAL]->(term_ver_value18)
MERGE (term_ver_root18)-[has_version18:HAS_VERSION]->(term_ver_value18)
SET has_version18 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(categoric_response_list2)

CREATE (library)-[:CONTAINS_TERM]->(dose_frequency1:CTTermRoot {uid: "dose_frequency_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root19:CTTermNameRoot)-[:LATEST]->(term_ver_value19:CTTermNameValue {
name: "dose_frequency_name1",
name_sentence_case: "dose_frequency_name_sentence_case1"})
MERGE (term_ver_root19)-[latest_final19:LATEST_FINAL]->(term_ver_value19)
MERGE (term_ver_root19)-[has_version19:HAS_VERSION]->(term_ver_value19)
SET has_version19 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dose_frequency1)

CREATE (library)-[:CONTAINS_TERM]->(dose_frequency2:CTTermRoot {uid: "dose_frequency_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root20:CTTermNameRoot)-[:LATEST]->(term_ver_value20:CTTermNameValue {
name: "dose_frequency_name2",
name_sentence_case: "dose_frequency_name_sentence_case2"})
MERGE (term_ver_root20)-[latest_final20:LATEST_FINAL]->(term_ver_value20)
MERGE (term_ver_root20)-[has_version20:HAS_VERSION]->(term_ver_value20)
SET has_version20 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dose_frequency2)

CREATE (library)-[:CONTAINS_TERM]->(dose_frequency3:CTTermRoot {uid: "dose_frequency_uidXYZ"})-[:HAS_NAME_ROOT]->
(term_ver_root20b:CTTermNameRoot)-[:LATEST]->(term_ver_value20b:CTTermNameValue {
name: "dose_frequency_name3",
name_sentence_case: "dose_frequency_name_sentence_case3"})
MERGE (term_ver_root20b)-[latest_final20b:LATEST_FINAL]->(term_ver_value20b)
MERGE (term_ver_root20b)-[has_version20b:HAS_VERSION]->(term_ver_value20b)
SET has_version20b = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dose_frequency3)

CREATE (library)-[:CONTAINS_TERM]->(dose_unit1:CTTermRoot {uid: "dose_unit_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root21:CTTermNameRoot)-[:LATEST]->(term_ver_value21:CTTermNameValue {
name: "dose_unit_name1",
name_sentence_case: "dose_unit_name_sentence_case1"})
MERGE (term_ver_root21)-[latest_final21:LATEST_FINAL]->(term_ver_value21)
MERGE (term_ver_root21)-[has_version21:HAS_VERSION]->(term_ver_value21)
SET has_version21 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dose_unit1)

CREATE (library)-[:CONTAINS_TERM]->(dose_unit2:CTTermRoot {uid: "dose_unit_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root22:CTTermNameRoot)-[:LATEST]->(term_ver_value22:CTTermNameValue {
name: "dose_unit_name2",
name_sentence_case: "dose_unit_name_sentence_case2"})
MERGE (term_ver_root22)-[latest_final22:LATEST_FINAL]->(term_ver_value22)
MERGE (term_ver_root22)-[has_version22:HAS_VERSION]->(term_ver_value22)
SET has_version22 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dose_unit2)

CREATE (library)-[:CONTAINS_TERM]->(dosage_form1:CTTermRoot {uid: "dosage_form_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root23:CTTermNameRoot)-[:LATEST]->(term_ver_value23:CTTermNameValue {
name: "dosage_form_name1",
name_sentence_case: "dosage_form_name_sentence_case1"})
MERGE (term_ver_root23)-[latest_final23:LATEST_FINAL]->(term_ver_value23)
MERGE (term_ver_root23)-[has_version23:HAS_VERSION]->(term_ver_value23)
SET has_version23 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dosage_form1)

CREATE (library)-[:CONTAINS_TERM]->(dosage_form2:CTTermRoot {uid: "dosage_form_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root24:CTTermNameRoot)-[:LATEST]->(term_ver_value24:CTTermNameValue {
name: "dosage_form_name2",
name_sentence_case: "dosage_form_name_sentence_case2"})
MERGE (term_ver_root24)-[latest_final24:LATEST_FINAL]->(term_ver_value24)
MERGE (term_ver_root24)-[has_version24:HAS_VERSION]->(term_ver_value24)
SET has_version24 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dosage_form2)

CREATE (library)-[:CONTAINS_TERM]->(route_of_administration1:CTTermRoot {uid: "route_of_administration_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root25:CTTermNameRoot)-[:LATEST]->(term_ver_value25:CTTermNameValue {
name: "route_of_administration_name1",
name_sentence_case: "route_of_administration_name_sentence_case1"})
MERGE (term_ver_root25)-[latest_final25:LATEST_FINAL]->(term_ver_value25)
MERGE (term_ver_root25)-[has_version25:HAS_VERSION]->(term_ver_value25)
SET has_version25 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(route_of_administration1)

CREATE (library)-[:CONTAINS_TERM]->(route_of_administration2:CTTermRoot {uid: "route_of_administration_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root26:CTTermNameRoot)-[:LATEST]->(term_ver_value26:CTTermNameValue {
name: "route_of_administration_name2",
name_sentence_case: "route_of_administration_name_sentence_case2"})
MERGE (term_ver_root26)-[latest_final26:LATEST_FINAL]->(term_ver_value26)
MERGE (term_ver_root26)-[has_version26:HAS_VERSION]->(term_ver_value26)
SET has_version26 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(route_of_administration2)

CREATE (library)-[:CONTAINS_TERM]->(delivery_device1:CTTermRoot {uid: "delivery_device_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root27:CTTermNameRoot)-[:LATEST]->(term_ver_value27:CTTermNameValue {
name: "delivery_device_name1",
name_sentence_case: "delivery_device_name_sentence_case1"})
MERGE (term_ver_root27)-[latest_final27:LATEST_FINAL]->(term_ver_value27)
MERGE (term_ver_root27)-[has_version27:HAS_VERSION]->(term_ver_value27)
SET has_version27 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(delivery_device1)

CREATE (library)-[:CONTAINS_TERM]->(delivery_device2:CTTermRoot {uid: "delivery_device_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root28:CTTermNameRoot)-[:LATEST]->(term_ver_value28:CTTermNameValue {
name: "delivery_device_name2",
name_sentence_case: "delivery_device_name_sentence_case2"})
MERGE (term_ver_root28)-[latest_final28:LATEST_FINAL]->(term_ver_value28)
MERGE (term_ver_root28)-[has_version28:HAS_VERSION]->(term_ver_value28)
SET has_version28 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(delivery_device2)

CREATE (library)-[:CONTAINS_TERM]->(dispenser1:CTTermRoot {uid: "dispenser_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root29:CTTermNameRoot)-[:LATEST]->(term_ver_value29:CTTermNameValue {
name: "dispenser_name1",
name_sentence_case: "dispenser_name_sentence_case1"})
MERGE (term_ver_root29)-[latest_final29:LATEST_FINAL]->(term_ver_value29)
MERGE (term_ver_root29)-[has_version29:HAS_VERSION]->(term_ver_value29)
SET has_version29 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dispenser1)

CREATE (library)-[:CONTAINS_TERM]->(dispenser2:CTTermRoot {uid: "dispenser_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root30:CTTermNameRoot)-[:LATEST]->(term_ver_value30:CTTermNameValue {
name: "dispenser_name2",
name_sentence_case: "dispenser_name_sentence_case2"})
MERGE (term_ver_root30)-[latest_final30:LATEST_FINAL]->(term_ver_value30)
MERGE (term_ver_root30)-[has_version30:HAS_VERSION]->(term_ver_value30)
SET has_version30 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dispenser2)
"""

STARTUP_ACTIVITY_INSTANCES = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
author_id: "unknown-user",
version: "0.1"
} AS draft_properties,

{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties

MERGE (library:Library {name:"Sponsor", is_editable:true})
MERGE (activity_hierarchy_root1:ActivityRoot {uid:"activity_root1"})-[:LATEST]->(activity_hierarchy_value1)
MERGE (library)-[:CONTAINS_CONCEPT]->(
activity_instance_root1:ConceptRoot:ActivityInstanceRoot:TemplateParameterTermRoot:ReminderRoot {uid:"activity_instance_root1"})
-[:LATEST]->(activity_instance_value1:ConceptValue:ActivityInstanceValue:TemplateParameterTermValue:ReminderValue {
name:"name1",
name_sentence_case:"name1",
definition:"definition1",
abbreviation:"abbv",
topic_code:"topic_code1",
adam_param_code:"adam_param_code1",
is_required_for_activity:false,
is_default_selected_for_activity:false,
is_data_sharing:false,
is_legacy_usage:false,
legacy_description:"legacy_description1"
})-[:HAS_ACTIVITY]-(activity_grouping:ActivityGrouping {uid:"ActivityGrouping_000001"})
MERGE (activity_grouping)<-[:HAS_GROUPING]-(activity_hierarchy_value1)
MERGE (activity_instance_root1)-[latest_final1:LATEST_FINAL]->(activity_instance_value1)
MERGE (activity_instance_root1)-[has_version1:HAS_VERSION]->(activity_instance_value1)
SET has_version1 = final_properties
MERGE (sdtm_variable1:CTTermRoot {uid:"sdtm_variable_uid1"})
MERGE (activity_instance_value1)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:TABULATED_IN]->(sdtm_variable1)
MERGE (sdtm_subcat1:CTTermRoot {uid:"sdtm_subcat_uid1"})
MERGE (activity_instance_value1)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SDTM_SUBCAT]->(sdtm_subcat1)
MERGE (sdtm_cat1:CTTermRoot {uid:"sdtm_cat_uid1"})
MERGE (activity_instance_value1)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SDTM_CAT]->(sdtm_cat1)
MERGE (sdtm_domain1:CTTermRoot {uid:"sdtm_domain_uid1"})
MERGE (activity_instance_value1)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SDTM_DOMAIN]->(sdtm_domain1)
MERGE (specimen1:CTTermRoot {uid:"specimen_uid1"})
MERGE (activity_instance_value1)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SPECIMEN]->(specimen1)

MERGE (activity_hierarchy_root2:ActivityRoot {uid:"activity_root2"})-[:LATEST]->(activity_hierarchy_value2)
MERGE (library)-[:CONTAINS_CONCEPT]->(
activity_instance_root2:ConceptRoot:ActivityInstanceRoot:TemplateParameterTermRoot:ReminderRoot {uid:"activity_instance_root2"})
-[:LATEST]->(activity_instance_value2:ConceptValue:ActivityInstanceValue:TemplateParameterTermValue:ReminderValue {
name:"name2",
name_sentence_case: "name2",
definition:"definition2",
abbreviation:"abbv",
topic_code:"topic_code2",
adam_param_code:"adam_param_code2",
is_required_for_activity:false,
is_default_selected_for_activity:false,
is_data_sharing:false,
is_legacy_usage:false,
legacy_description:"legacy_description2"
})-[:HAS_ACTIVITY]->(activity_grouping2:ActivityGrouping {uid:"ActivityGrouping_000002"})
MERGE (activity_grouping2)<-[:HAS_GROUPING]-(activity_hierarchy_value2)
MERGE (activity_instance_root2)-[latest_draft2:LATEST_DRAFT]->(activity_instance_value2)
MERGE (activity_instance_root2)-[has_version2:HAS_VERSION]->(activity_instance_value2)
SET has_version2 = draft_properties
MERGE (sdtm_variable2:CTTermRoot {uid:"sdtm_variable_uid2"})
MERGE (activity_instance_value2)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:TABULATED_IN]->(sdtm_variable2)
MERGE (sdtm_subcat2:CTTermRoot {uid:"sdtm_subcat_uid2"})
MERGE (activity_instance_value2)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SDTM_SUBCAT]->(sdtm_subcat2)
MERGE (sdtm_cat2:CTTermRoot {uid:"sdtm_cat_uid2"})
MERGE (activity_instance_value2)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SDTM_CAT]->(sdtm_cat2)
MERGE (sdtm_domain2:CTTermRoot {uid:"sdtm_domain_uid2"})
MERGE (activity_instance_value2)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SDTM_DOMAIN]->(sdtm_domain2)
MERGE (specimen2:CTTermRoot {uid:"specimen_uid2"})
MERGE (activity_instance_value2)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SPECIMEN]->(specimen2)
"""

STARTUP_ACTIVITY_INSTANCES_TOPICCDDEF = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
author_id: "unknown-user",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime('2021-10-01T12:00:00.0+0200'),
end_date: datetime('2021-10-03T12:00:00.0+0200'),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties,
{
change_description: "Approved version",
start_date: datetime('2021-10-03T12:00:00.0+0200'),
status: "Final",
author_id: "unknown-user",
version: "2.0"
} AS final2_properties

MERGE (library:Library {name:"Sponsor", is_editable:true})
MERGE (activity_root1:ActivityRoot {uid:"activity_root1"})-[:LATEST]->(activity_value1)
MERGE (activity_root1)-[hv1:HAS_VERSION]->(activity_value1)
SET hv1 = final_properties
MERGE (library)-[:CONTAINS_CONCEPT]->(
activity_instance_root1:ConceptRoot:ActivityInstanceRoot:FindingRoot:NumericFindingRoot {uid:"activity_instance_root1"})
-[:LATEST]->(new_activity_instance_value1:ConceptValue:ActivityInstanceValue:FindingValue:NumericFindingValue {
name:"new_name1",
name_sentence_case:"new_name1",
definition:"definition1",
abbreviation:"abbv",
topic_code:"topic_code1",
adam_param_code:"adam_param_code1",
legacy_description:"legacy_description1",
molecular_weight:1.0,
value_sas_display_format:"string"
})-[:HAS_ACTIVITY]->(activity_grouping:ActivityGrouping {uid:"ActivityGrouping_000001"})
MERGE (activity_grouping)<-[:HAS_GROUPING]-(activity_value1)
MERGE (activity_instance_root1)-[latest_final2:LATEST_FINAL]->(new_activity_instance_value1)
MERGE (activity_instance_root1)-[hv2:HAS_VERSION]->(new_activity_instance_value1)
SET hv2 = final2_properties

MERGE (activity_instance_root1)-[hv3a:HAS_VERSION]->(activity_instance_value1:ConceptValue:
ActivityInstanceValue:FindingValue:NumericFindingValue {
name:"name1"})
MERGE (activity_instance_value1)-[:HAS_ACTIVITY]->(activity_grouping)
SET activity_instance_value1=new_activity_instance_value1
SET activity_instance_value1.molecular_weight = 0.0
SET activity_instance_value1.name="name1"
SET hv3a = final_properties



MERGE (activity_root2:ActivityRoot {uid:"activity_root2"})-[:LATEST]->(activity_value2)
MERGE (activity_root2)-[hv4:HAS_VERSION]->(activity_value2)
SET hv4 = final_properties
MERGE (library)-[:CONTAINS_CONCEPT]->(
activity_instance_root2:ConceptRoot:ActivityInstanceRoot:InterventionRoot:CompoundDosingRoot {uid:"activity_instance_root2"})
-[:LATEST]->(activity_instance_value2:ConceptValue:ActivityInstanceValue:InterventionValue:CompoundDosingValue {
name:"name2",
name_sentence_case:"name2",
definition:"definition2",
abbreviation:"abbv",
topic_code:"topic_code2",
adam_param_code:"adam_param_code2",
legacy_description:"legacy_description2"
})-[:HAS_ACTIVITY]->(activity_grouping2:ActivityGrouping {uid:"ActivityGrouping_000002"})
MERGE (activity_grouping2)<-[:HAS_GROUPING]-(activity_value2)
MERGE (activity_instance_root2)-[latest_final3:LATEST_FINAL]->(activity_instance_value2)
MERGE (activity_instance_root2)-[hv5:HAS_VERSION]->(activity_instance_value2)
SET hv5 = final2_properties
"""

STARTUP_ACTIVITY_GROUPS = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
author_id: "unknown-user",
version: "0.1"
} AS draft_properties,

{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties

MERGE (library:Library {name:"Sponsor", is_editable:true})
MERGE (library)-[:CONTAINS_CONCEPT]->(activity_group_root1:ConceptRoot:ActivityGroupRoot {uid:"activity_group_root1"})
-[:LATEST]->(activity_group_value1:ConceptValue:ActivityGroupValue {
name:"name1",
name_sentence_case:"name1",
definition:"definition1",
abbreviation:"abbv"
})
MERGE (activity_group_root1)-[latest_final1:LATEST_FINAL]->(activity_group_value1)
MERGE (activity_group_root1)-[has_version1:HAS_VERSION]->(activity_group_value1)
SET has_version1 = final_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(activity_group_root2:ConceptRoot:ActivityGroupRoot {uid:"activity_group_root2"})
-[:LATEST]->(activity_group_value2:ConceptValue:ActivityGroupValue {
name:"name2",
name_sentence_case:"name2",
definition:"definition2",
abbreviation:"abbv"
})
MERGE (activity_group_root2)-[latest_draft2:LATEST_DRAFT]->(activity_group_value2)
MERGE (activity_group_root2)-[:LATEST_FINAL]->(activity_group_value2)
MERGE (activity_group_root2)-[has_version2:HAS_VERSION]->(activity_group_value2)
SET has_version2 = draft_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(activity_group_root3:ConceptRoot:ActivityGroupRoot {uid:"activity_group_root3"})
-[:LATEST]->(activity_group_value3:ConceptValue:ActivityGroupValue {
name:"name3",
name_sentence_case:"name3",
definition:"definition3",
abbreviation:"abbv"
})
MERGE (activity_group_root3)-[latest_final3:LATEST_FINAL]->(activity_group_value3)
MERGE (activity_group_root3)-[has_version3:HAS_VERSION]->(activity_group_value3)
SET has_version3 = final_properties
"""

STARTUP_ACTIVITY_SUB_GROUPS = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
author_id: "unknown-user",
version: "0.1"
} AS draft_properties,

{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties

MERGE (library:Library {name:"Sponsor", is_editable:true})
MERGE (library)-[:CONTAINS_CONCEPT]->(activity_subgroup_root1:ConceptRoot:ActivitySubGroupRoot {uid:"activity_subgroup_root1"})
-[:LATEST]->(activity_subgroup_value1:ConceptValue:ActivitySubGroupValue {
name:"name1",
name_sentence_case:"name1",
definition:"definition1",
abbreviation:"abbv"
})
MERGE (activity_subgroup_root1)-[latest_final1:LATEST_FINAL]->(activity_subgroup_value1)
MERGE (activity_subgroup_root1)-[has_version1:HAS_VERSION]->(activity_subgroup_value1)
SET has_version1 = final_properties
WITH *
MERGE (activity_group_root1:ConceptRoot:ActivityGroupRoot {uid:"activity_group_root1"})
-[:LATEST]->(activity_group_value1:ConceptValue:ActivityGroupValue)
MERGE (avf1:ActivityValidGroup {uid:"ActivityValidGroup_000001"})
MERGE (avf1)-[:IN_GROUP]->(activity_group_value1)
MERGE (activity_subgroup_value1)-[:HAS_GROUP]->(avf1)
MERGE (activity_group_root1)-[group_has_version:HAS_VERSION]->(activity_group_value1)
SET group_has_version = draft_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(activity_subgroup_root2:ConceptRoot:ActivitySubGroupRoot {uid:"activity_subgroup_root2"})
-[:LATEST]->(activity_subgroup_value2:ConceptValue:ActivitySubGroupValue {
name:"name2",
name_sentence_case:"name2",
definition:"definition2",
abbreviation:"abbv"
})
MERGE (activity_subgroup_root2)-[latest_draft2:LATEST_DRAFT]->(activity_subgroup_value2)
MERGE (activity_subgroup_root2)-[has_version2:HAS_VERSION]->(activity_subgroup_value2)
SET has_version2 = draft_properties

WITH *
MERGE (activity_group_root2:ConceptRoot:ActivityGroupRoot {uid:"activity_group_root2"})
-[:LATEST]->(activity_group_value2:ConceptValue:ActivityGroupValue)
MERGE (activity_group_root2)-[hvg2:HAS_VERSION]->(activity_group_value2)
SET hvg2 = draft_properties
MERGE (avf2:ActivityValidGroup {uid:"ActivityValidGroup_000002"})
MERGE (avf2)-[:IN_GROUP]->(activity_group_value2)
MERGE (activity_subgroup_value2)-[:HAS_GROUP]->(avf2)

MERGE (library)-[:CONTAINS_CONCEPT]->(activity_subgroup_root3:ConceptRoot:ActivitySubGroupRoot {uid:"activity_subgroup_root3"})
-[:LATEST]->(activity_subgroup_value3:ConceptValue:ActivitySubGroupValue {
name:"name3",
name_sentence_case:"name3",
definition:"definition3",
abbreviation:"abbv"
})
MERGE (activity_subgroup_root3)-[latest_final3:LATEST_FINAL]->(activity_subgroup_value3)
MERGE (activity_subgroup_root3)-[has_version3:HAS_VERSION]->(activity_subgroup_value3)
SET has_version3 = final_properties
WITH *
MERGE (activity_group_root3:ConceptRoot:ActivityGroupRoot {uid:"activity_group_root3"})
-[:LATEST]->(activity_group_value3:ConceptValue:ActivityGroupValue)
MERGE (activity_group_root3)-[:HAS_VERSION]->(activity_group_value3)
MERGE (avf3:ActivityValidGroup {uid:"ActivityValidGroup_000003"})
MERGE (avf3)-[:IN_GROUP]->(activity_group_value3)
MERGE (activity_subgroup_value3)-[:HAS_GROUP]->(avf3)
MERGE (:Counter:ActivityValidGroupCounter {count: 3, counterId:'ActivityValidGroupCounter'})
"""

STARTUP_ACTIVITIES = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
author_id: "unknown-user",
version: "0.1"
} AS draft_properties,

{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties

MERGE (library:Library {name:"Sponsor", is_editable:true})
MERGE (library)-[:CONTAINS_CONCEPT]->(activity_root1:ConceptRoot:ActivityRoot {uid:"activity_root1"})
-[:LATEST]->(activity_value1:ConceptValue:ActivityValue {
name:"name1",
name_sentence_case:"name1",
definition:"definition1",
abbreviation:"abbv"
})
MERGE (activity_root1)-[latest_final1:LATEST_FINAL]->(activity_value1)
MERGE (activity_root1)-[has_version1:HAS_VERSION]->(activity_value1)
SET has_version1 = final_properties
MERGE (activity_subgroup_root1:ConceptRoot:ActivitySubGroupRoot {uid:"activity_subgroup_root1"})
-[:LATEST]->(activity_subgroup_value1:ConceptValue:ActivitySubGroupValue)
MERGE (activity_subgroup_root1)-[hvs1:HAS_VERSION]->(activity_subgroup_value1)
SET hvs1 = final_properties
MERGE (activity_subgroup_root1)-[:LATEST_FINAL]->(activity_subgroup_value1)
MERGE (activity_value1)-[:HAS_GROUPING]->(activity_grouping:ActivityGrouping {uid:"ActivityGrouping_000001"})
WITH *
MERGE (activity_valid_group:ActivityValidGroup {uid:"ActivityValidGroup_000001"})
MERGE (activity_grouping)-[:IN_SUBGROUP]->(activity_valid_group)
MERGE (activity_valid_group)<-[:HAS_GROUP]-(activity_subgroup_value1)
WITH *
MERGE (activity_group_root:ActivityGroupRoot:ConceptRoot {uid:"activity_group_root1"})-[:LATEST]->(activity_group_value:ActivityGroupValue:ConceptValue)
MERGE (activity_group_root)-[hvg1:HAS_VERSION]->(activity_group_value)
SET hvg1 = final_properties
MERGE (activity_group_root)-[:LATEST_FINAL]->(activity_group_value)
MERGE (activity_valid_group)-[:IN_GROUP]->(activity_group_value)

MERGE (library)-[:CONTAINS_CONCEPT]->(activity_root2:ConceptRoot:ActivityRoot {uid:"activity_root2"})
-[:LATEST]->(activity_value2:ConceptValue:ActivityValue {
name:"name2",
name_sentence_case:"name2",
definition:"definition2",
abbreviation:"abbv"
})
MERGE (activity_root2)-[latest_draft2:LATEST_DRAFT]->(activity_value2)
MERGE (activity_root2)-[has_version2:HAS_VERSION]->(activity_value2)
SET has_version2 = draft_properties
MERGE (activity_subgroup_root2:ConceptRoot:ActivitySubGroupRoot {uid:"activity_subgroup_root2"})
-[:LATEST]->(activity_subgroup_value2:ConceptValue:ActivitySubGroupValue)
MERGE (activity_subgroup_root2)-[hvsg2:HAS_VERSION]->(activity_subgroup_value2)
SET hvsg2 = draft_properties
MERGE (activity_value2)-[:HAS_GROUPING]->(activity_grouping2:ActivityGrouping {uid:"ActivityGrouping_000002"})
WITH *
MERGE (activity_valid_group2:ActivityValidGroup {uid:"ActivityValidGroup_000002"})
MERGE (activity_grouping2)-[:IN_SUBGROUP]->(activity_valid_group2)
MERGE (activity_valid_group2)<-[:HAS_GROUP]-(activity_subgroup_value2)
WITH *
MERGE (activity_group_root2:ActivityGroupRoot:ConceptRoot {uid:"activity_group_root2"})-[:LATEST]->(activity_group_value2:ActivityGroupValue:ConceptValue)
MERGE (activity_group_root2)-[hvg2:HAS_VERSION]->(activity_group_value2)
SET hvg2 = draft_properties
MERGE (activity_valid_group2)-[:IN_GROUP]->(activity_group_value2)

MERGE (library)-[:CONTAINS_CONCEPT]->(activity_root3:ConceptRoot:ActivityRoot {uid:"activity_root3"})
-[:LATEST]->(activity_value3:ConceptValue:ActivityValue {
name:"name3",
name_sentence_case:"name3",
definition:"definition3",
abbreviation:"abbv"
})
MERGE (activity_root3)-[latest_final3:LATEST_FINAL]->(activity_value3)
MERGE (activity_root3)-[has_version3:HAS_VERSION]->(activity_value3)
SET has_version3 = final_properties
MERGE (activity_subgroup_root3:ConceptRoot:ActivitySubGroupRoot {uid:"activity_subgroup_root3"})
-[:LATEST]->(activity_subgroup_value3:ConceptValue:ActivitySubGroupValue)
MERGE (activity_subgroup_root3)-[hvs3:HAS_VERSION]->(activity_subgroup_value3)
SET hvs3 = final_properties
MERGE (activity_subgroup_root3)-[:LATEST_FINAL]->(activity_subgroup_value3)
MERGE (activity_value3)-[:HAS_GROUPING]->(activity_grouping3:ActivityGrouping {uid:"ActivityGrouping_000003"})
WITH *
MERGE (activity_valid_group3:ActivityValidGroup {uid:"ActivityValidGroup_000003"})
MERGE (activity_grouping3)-[:IN_SUBGROUP]->(activity_valid_group3)
MERGE (activity_valid_group3)<-[:HAS_GROUP]-(activity_subgroup_value3)
WITH *
MERGE (activity_group_root3:ConceptRoot:ActivityGroupRoot {uid:"activity_group_root3"})-[:LATEST]->(activity_group_value3:ConceptValue:ActivityGroupValue)
MERGE (activity_group_root3)-[hvg3:HAS_VERSION]->(activity_group_value3)
SET hvg3 = final_properties
MERGE (activity_group_root3)-[:LATEST_FINAL]->(activity_group_value3)
MERGE (activity_valid_group3)-[:IN_GROUP]->(activity_group_value3)
MERGE (:Counter:ActivityValidGroupCounter {count: 3, counterId:'ActivityValidGroupCounter'})
MERGE (:Counter:ActivityGroupingCounter {count: 3, counterId:'ActivityGroupingCounter'})
"""

STARTUP_DICTIONARY_CODELISTS_CYPHER = """
// SNOMED Library with two codelists
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
author_id: "unknown-user",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties
CREATE (library:Library {name:"SNOMED", is_editable:true})
MERGE (library)-[:CONTAINS_DICTIONARY_CODELIST]->(codelist_root1:DictionaryCodelistRoot {uid:"codelist_root1_uid"})
-[:LATEST]->(codelist_value1:DictionaryCodelistValue:TemplateParameter {name:"name1"})
MERGE (codelist_root1)-[latest_final1:LATEST_FINAL]->(codelist_value1)
MERGE (codelist_root1)-[hv1:HAS_VERSION]->(codelist_value1)
SET hv1 = final_properties

MERGE (library)-[:CONTAINS_DICTIONARY_CODELIST]->(codelist_root2:DictionaryCodelistRoot {uid:"codelist_root2_uid"})
-[:LATEST]->(codelist_value2:DictionaryCodelistValue {name:"name2"})
MERGE (codelist_root2)-[latest_draft2:LATEST_DRAFT]->(codelist_value2)
MERGE (codelist_root2)-[hv2:HAS_VERSION]->(codelist_value2)
SET hv2 = draft_properties


// UNII Library with UNII codelist
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
author_id: "unknown-user",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties
CREATE (library:Library {name:"UNII", is_editable:true})
MERGE (library)-[:CONTAINS_DICTIONARY_CODELIST]->(codelist_root1:DictionaryCodelistRoot {uid:"codelist_unii_uid"})
-[:LATEST]->(codelist_value1:DictionaryCodelistValue:TemplateParameter {name:"UNII"})
MERGE (codelist_root1)-[latest_final1:LATEST_FINAL]->(codelist_value1)
MERGE (codelist_root1)-[hv3:HAS_VERSION]->(codelist_value1)
SET hv3 = final_properties



// MED-RT Library with PClass codelist
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
author_id: "unknown-user",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties
CREATE (library:Library {name:"MED-RT", is_editable:true})
MERGE (library)-[:CONTAINS_DICTIONARY_CODELIST]->(codelist_root1:DictionaryCodelistRoot {uid:"codelist_pclass_uid"})
-[:LATEST]->(codelist_value1:DictionaryCodelistValue:TemplateParameter {name:"PClass"})
MERGE (codelist_root1)-[latest_final1:LATEST_FINAL]->(codelist_value1)
MERGE (codelist_root1)-[hv4:HAS_VERSION]->(codelist_value1)
SET hv4 = final_properties

"""

STARTUP_DICTIONARY_TERMS_CYPHER = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
author_id: "unknown-user",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties,
{
start_date: datetime(),
author_id: "Dictionary Codelist Test"
} AS has_term_properties
MATCH (library:Library {name:"SNOMED"})
MERGE (codelist_root1:DictionaryCodelistRoot {uid:"codelist_root1_uid"})
MERGE (codelist_root1)-[has_term1:HAS_TERM]->(term_root1:DictionaryTermRoot:SnomedTermRoot {uid:"term_root1_uid"})
-[:LATEST]->(term_value1:DictionaryTermValue:SnomedTermValue {
name:"name1", dictionary_id:"dictionary_id1", name_sentence_case:"Name1", abbreviation:"abbreviation1", definition:"definition1"})
MERGE (codelist_root1)-[has_term4:HAS_TERM]->(term_root4:DictionaryTermRoot:SnomedTermRoot {uid:"term_root4_uid"})
-[:LATEST]->(term_value4:DictionaryTermValue:SnomedTermValue {
name:"name4", dictionary_id:"dictionary_id4", name_sentence_case:"Name4", abbreviation:"abbreviation4", definition:"definition4"})
MERGE (library)-[:CONTAINS_DICTIONARY_TERM]->(term_root1)
MERGE (term_root1)-[:LATEST_FINAL]->(term_value1)
MERGE (term_root1)-[hv1:HAS_VERSION]->(term_value1)
MERGE (library)-[:CONTAINS_DICTIONARY_TERM]->(term_root4)
MERGE (term_root4)-[:LATEST_FINAL]->(term_value4)
MERGE (term_root4)-[hv2:HAS_VERSION]->(term_value4)
SET hv1 = final_properties
SET has_term1 = has_term_properties
SET hv2 = final_properties
SET has_term4 = has_term_properties

MERGE (codelist_root2:DictionaryCodelistRoot {uid:"codelist_root2_uid"})
MERGE (codelist_root2)-[has_term2:HAS_TERM]->(term_root2:DictionaryTermRoot:SnomedTermRoot {uid:"term_root2_uid"})
-[:LATEST]->(term_value2:DictionaryTermValue:SnomedTermValue {
name:"name2", dictionary_id:"dictionary_id2", name_sentence_case:"Name2", abbreviation:"abbreviation2", definition:"definition2"})
MERGE (library)-[:CONTAINS_DICTIONARY_TERM]->(term_root2)
MERGE (term_root2)-[:LATEST_DRAFT]->(term_value2)
MERGE (term_root2)-[hv3:HAS_VERSION]->(term_value2)
SET hv3 = draft_properties
SET has_term2 = has_term_properties

MERGE (codelist_root2)-[has_term3:HAS_TERM]->(term_root3:DictionaryTermRoot:SnomedTermRoot {uid:"term_root3_uid"})
-[:LATEST]->(term_value3:DictionaryTermValue:SnomedTermValue {
name:"name3", dictionary_id:"dictionary_id3", name_sentence_case:"Name3", abbreviation:"abbreviation3", definition:"definition3"})
MERGE (library)-[:CONTAINS_DICTIONARY_TERM]->(term_root3)
MERGE (term_root3)-[:LATEST_DRAFT]->(term_value3)
MERGE (term_root3)-[:LATEST_FINAL]->(term_value3)
MERGE (term_root3)-[hv4:HAS_VERSION]->(term_value3)
CREATE (term_root3)-[hv5:HAS_VERSION]->(term_value3)
SET hv4 = draft_properties
SET hv5 = final_properties
SET has_term3 = has_term_properties

MERGE (codelist_root2)-[has_term5:HAS_TERM]->(term_root5:DictionaryTermRoot:SnomedTermRoot {uid:"term_root5_uid"})
-[:LATEST]->(term_value5:DictionaryTermValue:SnomedTermValue {
name:"name5", dictionary_id:"dictionary_id5", name_sentence_case:"Name5", abbreviation:"abbreviation5", definition:"definition5"})
MERGE (library)-[:CONTAINS_DICTIONARY_TERM]->(term_root5)
MERGE (term_root5)-[:LATEST_DRAFT]->(term_value5)
MERGE (term_root5)-[hv6:HAS_VERSION]->(term_value5)
SET hv6 = draft_properties
SET has_term5 = has_term_properties
"""

STARTUP_CT_CATALOGUE_CYPHER = """
WITH  {
change_description: "Approved version",
start_date: datetime("2020-03-27T00:00:00"),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS old_props,
{
change_description: "Approved version",
start_date: datetime("2020-06-26T00:00:00"),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS new_props
MERGE (catalogue:CTCatalogue {name:"catalogue"})-[:HAS_CODELIST]->
(codelist_to_update:CTCodelistRoot {uid:"updated_codelist_uid"})-[:HAS_ATTRIBUTES_ROOT]->
(codelist_attr_root_to_update:CTCodelistAttributesRoot)-[final1:LATEST_FINAL]->(val1:CTCodelistAttributesValue
{name:"old_name", extensible:false})
MERGE (codelist_attr_root_to_update)-[final1hv:HAS_VERSION]->(val1)
SET final1hv = old_props
MERGE (catalogue)-[:HAS_CODELIST]->(codelist_to_delete:CTCodelistRoot {uid:"deleted_codelist_uid"})-[:HAS_ATTRIBUTES_ROOT]->
(codelist_attr_to_delete)-[final2:LATEST_FINAL]->(val2:CTCodelistAttributesValue 
{name:"old_name", extensible:false})
MERGE (codelist_attr_to_delete)-[final2hv:HAS_VERSION]->(val2)
SET final2hv=old_props
MERGE (codelist_to_update)-[:HAS_TERM]->(term_to_update:CTTermRoot {uid:"updated_term_uid"})
-[:HAS_ATTRIBUTES_ROOT]->(term_attr_root_to_update:CTTermAttributesRoot)-[final3:LATEST_FINAL]->(val3:CTTermAttributesValue 
{name_submission_value:"old_submission_value", preferred_term:"old_preferred_term"})
MERGE (term_attr_root_to_update)-[final3hv:HAS_VERSION]->(val3)
SET final3hv = old_props
MERGE (codelist_to_delete)-[:HAS_TERM]->(:CTTermRoot {uid:"deleted_term_uid"})
-[:HAS_ATTRIBUTES_ROOT]->(root4:CTTermAttributesRoot)-[final4:LATEST_FINAL]->(val4:CTTermAttributesValue 
{name_submission_value:"old_submission_value", preferred_term:"old_preferred_term"})
MERGE (root4)-[final4hv:HAS_VERSION]->(val4)
SET final4hv=old_props

MERGE (codelist_attr_root_to_update)-[final5:LATEST_FINAL]->(val5:CTCodelistAttributesValue 
{name:"new_name", definition: "new_definition"})
MERGE (codelist_attr_root_to_update)-[final5hv:HAS_VERSION]->(val5)
SET final5hv=new_props
MERGE (catalogue)-[:HAS_CODELIST]->(codelist_to_add:CTCodelistRoot {uid:"added_codelist_uid"})-[:HAS_ATTRIBUTES_ROOT]->
(root6:CTCodelistAttributesRoot)-[final6:LATEST_FINAL]->(val6:CTCodelistAttributesValue 
{name:"new_name", definition:"codelist_added"})
MERGE (root6)-[final6hv:HAS_VERSION]->(val6)
SET final6hv=new_props
MERGE (term_attr_root_to_update)-[final7:LATEST_FINAL]->(val7:CTTermAttributesValue 
{name_submission_value:"new_submission_value", definition:"new_definition"})
MERGE (term_attr_root_to_update)-[final7hv:HAS_VERSION]->(val7)
SET final7hv=new_props
MERGE (codelist_to_add)-[:HAS_TERM]->(:CTTermRoot {uid:"added_term_uid"})-
[:HAS_ATTRIBUTES_ROOT]->(root8:CTTermAttributesRoot)-[final8:LATEST_FINAL]->(val8:CTTermAttributesValue 
{name_submission_value:"old_submission_value", preferred_term:"old_preferred_term"})
MERGE (root8)-[final8hv:HAS_VERSION]->(val8)
SET final8hv=new_props
"""

STARTUP_CT_PACKAGE_CYPHER = """
WITH  {
change_description: "Approved version",
start_date: datetime("2020-03-27T00:00:00"),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS old_props,
{
change_description: "Approved version",
start_date: datetime("2020-06-26T00:00:00"),
status: "Final",
author_id: "unknown-user",
version: "2.0"
} AS new_props
MERGE (catalogue:CTCatalogue {name:"catalogue"})-[:CONTAINS_PACKAGE]->(old_package:CTPackage{
uid:"old_package_uid",
name:"old_package",
effective_date:date("2020-03-27"), 
label:"label",
href:"href",
description:"description",
source:"source",
registration_status:"status",
import_date:datetime("2020-03-27T00:00:00Z"),
author_id:"unknown-user"
})
MERGE (catalogue)-[:CONTAINS_PACKAGE]->(new_package:CTPackage{
uid:"new_package_uid", 
name:"new_package", 
effective_date:date("2020-06-26"), 
label:"label",
href:"href",
description:"description",
source:"source",
registration_status:"status",
import_date:datetime("2020-03-27T00:00:00Z"),
author_id:"unknown-user"
})

MERGE (old_package)-[:CONTAINS_CODELIST]->(package_codelist1:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->(codelist_attr_value_to_update:CTCodelistAttributesValue 
{name:"old_name", extensible:false})<-[final1hv:HAS_VERSION]-(codelist_attr_root_to_update:CTCodelistAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(codelist_to_update:CTCodelistRoot {uid:"updated_codelist_uid"})
SET final1hv = old_props
MERGE (codelist_to_update)-[:HAS_NAME_ROOT]->(codelist_name_root_to_update:CTCodelistNameRoot)-[final2:LATEST_FINAL]->(codelist_name_value_to_update:CTCodelistNameValue)
MERGE (codelist_name_root_to_update)-[:LATEST]->(codelist_name_value_to_update)
MERGE (codelist_name_root_to_update)-[final2hv:HAS_VERSION]->(codelist_name_value_to_update)
SET final2hv=old_props
MERGE (old_package)-[:CONTAINS_CODELIST]->(package_codelist2:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->(codelist_attributes_value_to_delete:CTCodelistAttributesValue 
{name:"old_name", extensible:false})<-[final3:LATEST_FINAL]-(codelist_attributes_root_to_delete:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(codelist_to_delete:CTCodelistRoot {uid:"deleted_codelist_uid"})
MERGE (codelist_attributes_root_to_delete)-[final3hv:HAS_VERSION]->(codelist_attributes_value_to_delete)
SET final3hv=old_props
MERGE (package_codelist1)-[contains_term:CONTAINS_TERM]->(package_term1:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(term_attr_value_to_update:CTTermAttributesValue 
{name_submission_value:"old_submission_value", preferred_term:"old_preferred_term"})<-[final4:LATEST_FINAL]-(term_attr_root_to_update:CTTermAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(term_to_update:CTTermRoot {uid:"updated_term_uid"})<-[:HAS_TERM]-(codelist_to_update)
MERGE (term_attr_root_to_update)-[final4hv:HAS_VERSION]->(term_attr_value_to_update)
SET final4hv=old_props
MERGE (package_term1)-[:CONTAINS_ATTRIBUTES]->(not_modified_term_value:CTTermAttributesValue 
{name_submission_value:"not_modified_submission_value", preferred_term:"not_modified_preferred_term"})<-[final5:LATEST_FINAL]-(not_modified_term_attrs_root:CTTermAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(not_modified_term:CTTermRoot {uid:"not_modified_term_uid"})<-[:HAS_TERM]-(codelist_to_update)
MERGE (not_modified_term_attrs_root)-[final5hv:HAS_VERSION]->(not_modified_term_value)
SET final5hv=old_props
MERGE (package_codelist2)-[:CONTAINS_TERM]->(package_term2:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(term_attrs_val6:CTTermAttributesValue 
{name_submission_value:"old_submission_value", preferred_term:"old_preferred_term"})<-[final6:LATEST_FINAL]-(term_attrs_root6:CTTermAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(:CTTermRoot {uid:"deleted_term_uid"})<-[:HAS_TERM]-(codelist_to_delete)
MERGE (term_attrs_root6)-[final6hv:HAS_VERSION]->(term_attrs_val6)
SET final6hv=old_props

MERGE (new_package)-[:CONTAINS_CODELIST]->(package_codelist3:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->(attr_val7:CTCodelistAttributesValue 
{name:"new_name", definition: "new_definition"})<-[final7:LATEST_FINAL]-(codelist_attr_root_to_update)
MERGE (codelist_attr_root_to_update)-[final7hv:HAS_VERSION]->(attr_val7)
SET final7hv = new_props
MERGE (new_package)-[:CONTAINS_CODELIST]->(package_codelist4:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->(attr_val8:CTCodelistAttributesValue 
{name:"new_name", definition:"codelist_added"})<-[final8:LATEST_FINAL]-(attr_root8:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(codelist_to_add:CTCodelistRoot {uid:"added_codelist_uid"})
MERGE (attr_root8)-[final8hv:HAS_VERSION]->(attr_val8)
SET final8hv = new_props
MERGE (attr_root8)-[:LATEST]->(attr_val8)
MERGE (package_codelist3)-[:CONTAINS_TERM]->(package_term3:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(attr_val9:CTTermAttributesValue 
{name_submission_value:"new_submission_value", definition:"new_definition"})<-[final9:LATEST_FINAL]-(term_attr_root_to_update)
MERGE (term_attr_root_to_update)-[final9hv:HAS_VERSION]->(attr_val9)
SET final9hv = new_props
MERGE (package_codelist3)-[:CONTAINS_TERM]->(package_term5:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(not_modified_term_value)
MERGE (package_codelist4)-[:CONTAINS_TERM]->(package_term4:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(attr_value10:CTTermAttributesValue
{name_submission_value:"old_submission_value", preferred_term:"old_preferred_term"})<-[final10:LATEST_FINAL]-(attr_root10:CTTermAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(:CTTermRoot {uid:"added_term_uid"})<-[:HAS_TERM]-(codelist_to_add)
MERGE (attr_root10)-[final10hv:HAS_VERSION]->(attr_value10)
SET final10hv = new_props
"""

STARTUP_CT_PACKAGE_CYPHER_CDISC_CT = """
WITH  {
change_description: "Approved version",
start_date: datetime("2020-03-27T00:00:00"),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS old_props,
{
change_description: "Approved version",
start_date: datetime("2020-06-26T00:00:00"),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS new_props

MERGE (cat:CTCatalogue {name: "catalogue2"})-[:CONTAINS_PACKAGE] -> (package1:CTPackage{
uid:"package1_uid",name:"package1",effective_date:date("2020-06-26")})
-[:CONTAINS_CODELIST]->(p_codelist1:CTPackageCodelist {uid:"package1_uid_cdlist_code1"})
-[:CONTAINS_ATTRIBUTES]->(:CTCodelistAttributesValue 
{name:"codelist_name1", extensible:false, submission_value:"submission_value1", definition: "definition1", 
preferred_term:"codelist_pref_term1", synonyms:apoc.text.split("synonym1",",")})
MERGE (p_codelist1)-[:CONTAINS_TERM]->(:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(:CTTermAttributesValue 
{concept_id:"concept_id", code_submission_value:"code_submission_value",definition:"definition",
preferred_term:"pref_term",synonyms:apoc.text.split("syn1,syn2",",")})

MERGE (cat2:CTCatalogue {name: "catalogue3"})-[:CONTAINS_PACKAGE] -> (package2:CTPackage{
uid:"package2_uid",name:"package2",effective_date:date("2020-06-26")})
-[:CONTAINS_CODELIST]->(p_codelist2:CTPackageCodelist {uid:"package2_uid_cdlist_code2"})
-[:CONTAINS_ATTRIBUTES]->(:CTCodelistAttributesValue 
{name:"codelist_name2", extensible:false, submission_value:"submission_value2", definition: "definition2", 
preferred_term:"codelist_pref_term2", synonyms:apoc.text.split("synonym2",",")})
MERGE (p_codelist2)-[:CONTAINS_TERM]->(:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(:CTTermAttributesValue 
{concept_id:"concept_id2", code_submission_value:"code_submission_value2",definition:"definition2",
preferred_term:"pref_term2",synonyms:apoc.text.split("syn1,syn2",",")})

MERGE (catalogue:CTCatalogue {name:"catalogue"})-[:CONTAINS_PACKAGE]->(old_package:CTPackage{
uid:"old_package_uid",
name:"old_package",
effective_date:date("2020-03-27"), 
label:"label",
href:"href",
description:"description",
source:"source",
registration_status:"status",
import_date:datetime("2020-03-27T00:00:00Z"),
author_id:"unknown-user"
})
MERGE (catalogue)-[:CONTAINS_PACKAGE]->(new_package:CTPackage{
uid:"new_package_uid", 
name:"new_package", 
effective_date:date("2020-06-26"), 
label:"label",
href:"href",
description:"description",
source:"source",
registration_status:"status",
import_date:datetime("2020-03-27T00:00:00Z"),
author_id:"unknown-user"
})

MERGE (old_package)-[:CONTAINS_CODELIST]->(package_codelist1:CTPackageCodelist {uid:"old_package_uid_codelist_code1"})-[:CONTAINS_ATTRIBUTES]->(cav1:CTCodelistAttributesValue 
{name:"old_name1", extensible:false, submission_value:"old_submission_value1", definition:"old_definition1", preferred_term:"old_pref_term1", synonyms:apoc.text.split("syn1,syn2",",")})
<-[final1:LATEST_FINAL]-(codelist_attr_root_to_update:CTCodelistAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(codelist_to_update:CTCodelistRoot {uid:"updated_codelist_uid"})
MERGE (codelist_attr_root_to_update)-[hv1:HAS_VERSION]->(cav1)
SET hv1 = old_props
MERGE (codelist_to_update)-[:HAS_NAME_ROOT]->(cnr:CTCodelistNameRoot)-[final2:LATEST_FINAL]->(cnv:CTCodelistNameValue)
MERGE (cnr)-[hv2:HAS_VERSION]->(cnv)
SET hv2=old_props

MERGE (old_package)-[:CONTAINS_CODELIST]->(package_codelist2:CTPackageCodelist {uid:"old_package_uid_codelist_code2"})-[:CONTAINS_ATTRIBUTES]->(cav3:CTCodelistAttributesValue 
{name:"old_name2", extensible:false, submission_value:"old_submission_value2", definition: "old_definition2", preferred_term:"old_pref_term2", synonyms:apoc.text.split("synonym",",")})
<-[final3:LATEST_FINAL]-(car3:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(codelist_to_delete:CTCodelistRoot {uid:"deleted_codelist_uid"})
MERGE (car3)-[hv3:HAS_VERSION]->(cav3)
SET hv3=old_props

MERGE (package_codelist1)-[contains_term:CONTAINS_TERM]->(package_term1:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(cav4:CTTermAttributesValue 
{concept_id:"concept_id1", code_submission_value:"code_submission_value1",definition:"definition1",
preferred_term:"pref_term1",synonyms:apoc.text.split("syn1,syn2",",")})<-[final4:LATEST_FINAL]-(term_attr_root_to_update:CTTermAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(term_to_update:CTTermRoot {uid:"updated_term_uid"})<-[:HAS_TERM]-(codelist_to_update)
MERGE (term_attr_root_to_update)-[hv4:HAS_VERSION]->(cav4)
SET hv4=old_props

//MERGE (package_term1)-[:CONTAINS_ATTRIBUTES]->(not_modified_term_value:CTTermAttributesValue 
//{name_submission_value:"not_modified_submission_value", preferred_term:"not_modified_preferred_term"})<-[final5:LATEST_FINAL]-(:CTTermAttributesRoot)
//<-[:HAS_ATTRIBUTES_ROOT]-(not_modified_term:CTTermRoot {uid:"not_modified_term_uid"})<-[:HAS_TERM]-(codelist_to_update)
//SET final5=old_props

MERGE (package_codelist2)-[:CONTAINS_TERM]->(package_term2:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(cav6:CTTermAttributesValue 
{concept_id:"concept_id2", code_submission_value:"code_submission_value2",
definition:"definition2",preferred_term:"pref_term2",synonyms:apoc.text.split("syn",",")})<-[final6:LATEST_FINAL]-(car6:CTTermAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(:CTTermRoot {uid:"deleted_term_uid"})<-[:HAS_TERM]-(codelist_to_delete)
MERGE (car6)-[hv6:HAS_VERSION]->(cav6)
SET hv6=old_props


MERGE (new_package)-[:CONTAINS_CODELIST]->(package_codelist3:CTPackageCodelist {uid:"new_package_uid_codelist_code3"})-[:CONTAINS_ATTRIBUTES]->(cav7:CTCodelistAttributesValue 
{name:"new_name", definition: "new_definition", extensible:true, submission_value:"new_submission_value", preferred_term:"new_pref_term1"})
<-[final7:LATEST_FINAL]-(codelist_attr_root_to_update)
MERGE (codelist_attr_root_to_update)-[hv7:HAS_VERSION]->(cav7)
SET hv7 = new_props

MERGE (new_package)-[:CONTAINS_CODELIST]->(package_codelist4:CTPackageCodelist {uid:"new_package_uid_codelist_code4"})-[:CONTAINS_ATTRIBUTES]->(cav8:CTCodelistAttributesValue 
{name:"new_name", submission_value:"new_submission_value",definition:"codelist_added", extensible:false, preferred_term:"new_pref_term", synonyms:apoc.text.split("syn1,syn2,syn3",",")})
<-[final8:LATEST_FINAL]-(car8:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(codelist_to_add:CTCodelistRoot {uid:"added_codelist_uid"})
MERGE (car8)-[hv8:HAS_VERSION]->(cav8)
SET hv8 = new_props

MERGE (package_codelist3)-[:CONTAINS_TERM]->(package_term3:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(cav9:CTTermAttributesValue 
{concept_id:"concept_id3", code_submission_value:"code_submission_value3",definition:"definition3",preferred_term:"pref_term3"})
<-[final9:LATEST_FINAL]-(term_attr_root_to_update)
MERGE (term_attr_root_to_update)-[hv9:HAS_VERSION]->(cav9)
SET hv9 = new_props

//MERGE (package_codelist3)-[:CONTAINS_TERM]->(package_term5:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(not_modified_term_value)
MERGE (package_codelist4)-[:CONTAINS_TERM]->(package_term4:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(cav10:CTTermAttributesValue
{concept_id:"concept_id4", code_submission_value:"code_submission_value4",
definition:"definition4",preferred_term:"pref_term4",synonyms:apoc.text.split("syn1,syn2,syn3",",")})<-[final10:LATEST_FINAL]-(car10:CTTermAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(:CTTermRoot {uid:"added_term_uid"})<-[:HAS_TERM]-(codelist_to_add)
MERGE (car10)-[hv10:HAS_VERSION]->(cav10)
SET hv10 = new_props

"""

STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER = """
MERGE (cr:CTCodelistRoot {uid: "ct_codelist_root1"})
MERGE (cr)-[:HAS_ATTRIBUTES_ROOT]->(car:CTCodelistAttributesRoot)-
    [:LATEST]->(cav:CTCodelistAttributesValue {name: "codelist attributes value1",
                                               submission_value: "codelist submission value1",
                                               preferred_term: "codelist preferred term",
                                               definition: "codelist definition",
                                               extensible: false})
MERGE (:CTTermRoot {uid:"ct_term_root1"})
MERGE (cc:CTCatalogue {name: "SDTM CT"})-[:HAS_CODELIST]->(cr)
MERGE (car)-[hv1:HAS_VERSION]->(cav)
CREATE (car)-[hv2:HAS_VERSION]->(cav)
MERGE (car)-[lf:LATEST_FINAL]->(cav)
set hv1.change_description = "Approved version"
set hv1.start_date = datetime("2020-06-26T00:00:00")
set hv1.status = "Final"
set hv1.author_id = "unknown-user"
set hv1.version = "1.0"
set hv2.change_description = "Initial version"
set hv2.start_date = datetime("2020-03-27T00:00:00")
set hv2.end_date = datetime("2020-06-26T00:00:00")
set hv2.status = "Draft"
set hv2.author_id = "unknown-user"
set hv2.version = "0.1"
MERGE (lib:Library{name:"Sponsor", is_editable:true})
MERGE (lib)-[:CONTAINS_CODELIST]->(cr)

MERGE (cr2:CTCodelistRoot {uid: "ct_codelist_root2"})
MERGE (cr2)-[:HAS_ATTRIBUTES_ROOT]->(car2:CTCodelistAttributesRoot)-[:LATEST]->
    (cav2:CTCodelistAttributesValue {name: "codelist attributes value2",
                                    submission_value: "codelist submission value2",
                                    preferred_term: "codelist preferred term",
                                    definition: "codelist definition",
                                    extensible: false})
MERGE (cc)-[:HAS_CODELIST]->(cr2)
MERGE (car2)-[hv3:HAS_VERSION]->(cav2)
CREATE (car2)-[hv4:HAS_VERSION]->(cav2)
MERGE (car2)-[lf2:LATEST_FINAL]->(cav2)
MERGE (car2)-[ld2:LATEST_DRAFT]->(cav2)
set hv3.change_description = "Approved version"
set hv3.start_date = datetime("2020-03-27T00:00:00")
set hv3.end_date = datetime("2020-06-26T00:00:00")
set hv3.status = "Final"
set hv3.author_id = "unknown-user"
set hv3.version = "1.0"
set hv4.change_description = "latest draft"
set hv4.start_date = datetime("2020-06-26T00:00:00")
set hv4.status = "Draft"
set hv4.author_id = "unknown-user"
set hv4.version = "1.1"
MERGE (lib2:Library{name:"CDISC", is_editable:false})-[:CONTAINS_CODELIST]->(cr2)

MERGE (cr3:CTCodelistRoot {uid: "ct_codelist_root3"})
MERGE (cr3)-[:HAS_ATTRIBUTES_ROOT]->(car3:CTCodelistAttributesRoot)-[:LATEST]->
    (cav3:CTCodelistAttributesValue {name: "codelist attributes value3",
                                    submission_value: "codelist submission value3",
                                    preferred_term: "codelist preferred term",
                                    definition: "codelist definition",
                                    extensible: false})
MERGE (cc)-[:HAS_CODELIST]->(cr3)
MERGE (car3)-[ld3:LATEST_DRAFT]->(cav3)
MERGE (car3)-[hv5:HAS_VERSION]->(cav3)
set hv5.change_description = "latest draft"
set hv5.start_date = datetime("2020-06-26T00:00:00")
set hv5.status = "Draft"
set hv5.author_id = "unknown-user"
set hv5.version = "0.1"


MERGE (cr3)-[:HAS_NAME_ROOT]->(cnr:CTCodelistNameRoot)-[:LATEST]->(cnv:CTCodelistNameValue {name: "codelist_name_value"})
MERGE (cnr)-[hv6:HAS_VERSION]->(cnv)
MERGE (cnr)-[lf3:LATEST_FINAL]->(cnv)
CREATE (cnr)-[hv7:HAS_VERSION]->(cnv)
set hv7.change_description = "Approved version"
set hv7.start_date = datetime("2020-06-26T00:00:00")
set hv7.status = "Final"
set hv7.author_id = "unknown-user"
set hv7.version = "1.0"
set hv6.change_description = "Initial version"
set hv6.start_date = datetime("2020-03-27T00:00:00")
set hv6.end_date = datetime("2020-06-26T00:00:00")
set hv6.status = "Draft"
set hv6.author_id = "unknown-user"
set hv6.version = "0.1"
MERGE (lib)-[:CONTAINS_CODELIST]->(cr3)
"""

STARTUP_CT_CODELISTS_NAME_CYPHER = """
MERGE (cr:CTCodelistRoot {uid: "ct_codelist_root1"})
MERGE (cr)-[:HAS_NAME_ROOT]->(cnr:CTCodelistNameRoot)-[:LATEST]->
    (cnv:TemplateParameter:CTCodelistNameValue {name: "tp_codelist_name_value"})
MERGE (cc:CTCatalogue {name: "SDTM CT"})-[:HAS_CODELIST]->(cr)
MERGE (cnr)-[hv1:HAS_VERSION]->(cnv)
CREATE (cnr)-[hv2:HAS_VERSION]->(cnv)
MERGE (cnr)-[lf:LATEST_FINAL]->(cnv)
set hv2.change_description = "Approved version"
set hv2.start_date = datetime("2020-06-26T00:00:00")
set hv2.status = "Final"
set hv2.author_id = "unknown-user"
set hv2.version = "1.0"
set hv1.change_description = "Initial version"
set hv1.start_date = datetime("2020-03-27T00:00:00")
set hv1.end_date = datetime("2020-06-26T00:00:00")
set hv1.status = "Draft"
set hv1.author_id = "unknown-user"
set hv1.version = "0.1"
MERGE (lib:Library{name:"Sponsor", is_editable:true})
MERGE (lib)-[:CONTAINS_CODELIST]->(cr)

MERGE (cr2:CTCodelistRoot {uid: "ct_codelist_root2"})
MERGE (cr2)-[:HAS_NAME_ROOT]->(cnr2:CTCodelistNameRoot)-[:LATEST]->
    (cnv2:CTCodelistNameValue {name: "not_tp_codelist_name_value"})
MERGE (cc)-[:HAS_CODELIST]->(cr2)
MERGE (cnr2)-[hv3:HAS_VERSION]->(cnv2)
CREATE (cnr2)-[hv4:HAS_VERSION]->(cnv2)
CREATE (cnr2)-[hv5:HAS_VERSION]->(cnv2)
MERGE (cnr2)-[lf2:LATEST_FINAL]->(cnv2)
MERGE (cnr2)-[ld2:LATEST_DRAFT]->(cnv2)
set hv5.change_description = "Approved version"
set hv5.start_date = datetime("2020-03-27T00:00:00")
set hv5.end_date = datetime("2020-06-26T00:00:00")
set hv5.status = "Final"
set hv5.author_id = "unknown-user"
set hv5.version = "1.0"
set hv4.change_description = "latest draft"
set hv4.start_date = datetime("2020-06-26T00:00:00")
set hv4.status = "Draft"
set hv4.author_id = "unknown-user"
set hv4.version = "1.1"
set hv3.change_description = "Initial version"
set hv3.start_date = datetime("2020-03-27T00:00:00")
set hv3.end_date = datetime("2020-06-26T00:00:00")
set hv3.status = "Draft"
set hv3.author_id = "unknown-user"
set hv3.version = "0.1"
MERGE (lib2:Library{name:"CDISC", is_editable:false})-[:CONTAINS_CODELIST]->(cr2)

MERGE (cr3:CTCodelistRoot {uid: "ct_codelist_root3"})
MERGE (cr3)-[:HAS_NAME_ROOT]->(cnr3:CTCodelistNameRoot)-[:LATEST]->
    (cnv3:CTCodelistNameValue {name: "codelist_name_value"})
MERGE (cc)-[:HAS_CODELIST]->(cr3)
MERGE (cnr3)-[ld3:LATEST_DRAFT]->(cnv3)
MERGE (cnr3)-[hv6:HAS_VERSION]->(cnv3)
set hv6.change_description = "latest draft"
set hv6.start_date = datetime("2020-06-26T00:00:00")
set hv6.status = "Draft"
set hv6.author_id = "unknown-user"
set hv6.version = "0.1"
MERGE (lib)-[:CONTAINS_CODELIST]->(cr3)
"""

STARTUP_CT_TERM_ATTRIBUTES_CYPHER = """
MERGE (cc:CTCatalogue {name: "SDTM CT"})-[:HAS_CODELIST]->(cr:CTCodelistRoot {uid:"editable_cr"})-[:HAS_NAME_ROOT]
->(codelist_ver_root:CTCodelistNameRoot)-[:HAS_VERSION{change_description: "Approved version",start_date: datetime(),status: "Final",author_id: "unknown-user",version : "1.0"}]->(codelist_ver_value:CTCodelistNameValue)
MERGE (cr)-[:HAS_ATTRIBUTES_ROOT]->(car:CTCodelistAttributesRoot)-[:LATEST]->(cav:CTCodelistAttributesValue {name: "codelist attributes value1", submission_value: "codelist submission value1", preferred_term: "codelist preferred term", definition: "codelist definition", extensible: true})

CREATE (codelist_ver_root)-[:LATEST]->(codelist_ver_value)
CREATE (codelist_ver_root)-[:LATEST_FINAL]->(codelist_ver_value)
MERGE (car)-[hv1:HAS_VERSION]->(cav)
CREATE (car)-[hv2:HAS_VERSION]->(cav)
MERGE (car)-[lf1:LATEST_FINAL]->(cav)
set hv2.change_description = "Approved version"
set hv2.start_date = datetime("2020-06-26T00:00:00")
set hv2.status = "Final"
set hv2.author_id = "unknown-user"
set hv2.version = "1.0"
set hv1.change_description = "Initial version"
set hv1.start_date = datetime("2020-03-27T00:00:00")
set hv1.end_date = datetime("2020-06-26T00:00:00")
set hv1.status = "Draft"
set hv1.author_id = "unknown-user"
set hv1.version = "0.1"

MERGE (editable_lib:Library{name:"Sponsor", is_editable:true})
MERGE (editable_lib)-[:CONTAINS_CODELIST]->(cr)

MERGE (cc)-[:HAS_CODELIST]->(cr2:CTCodelistRoot {uid:"non_editable_cr"})
MERGE (non_editable_lib:Library{ name:"CDISC", is_editable:false})-[:CONTAINS_CODELIST]->(cr2)

MERGE (cr)-[has_term1:HAS_TERM]->(term_root:CTTermRoot {uid:"term_root_final"})-[:HAS_ATTRIBUTES_ROOT]->
    (term_ver_root:CTTermAttributesRoot)-[:LATEST]-(term_ver_value:CTTermAttributesValue 
        {code_submission_value: "code_submission_value1", name_submission_value:"name_submission_value1", 
        preferred_term:"preferred_term", definition:"definition"})
MERGE (term_root)-[:HAS_NAME_ROOT]->(term_name_ver_root:CTTermNameRoot)-[:LATEST]-(term_name_ver_value:CTTermNameValue 
        {name:"term_value_name1", name_sentence_case:"term_value_name_sentence_case"})
MERGE (editable_lib)-[:CONTAINS_TERM]->(term_root)
MERGE (term_ver_root)-[hv3:HAS_VERSION]->(term_ver_value)
MERGE (term_ver_root)-[lf2:LATEST_FINAL]->(term_ver_value)
CREATE (term_ver_root)-[hv4:HAS_VERSION]->(term_ver_value)
MERGE (term_name_ver_root)-[latest_final:LATEST_FINAL]->(term_name_ver_value)
MERGE (term_name_ver_root)-[latest_final_hv:HAS_VERSION]->(term_name_ver_value)
set has_term1.order = 1
set hv4.change_description = "Approved version"
set hv4.start_date = datetime()
set hv4.status = "Final"
set hv4.author_id = "unknown-user"
set hv4.version = "1.0"
set latest_final_hv.change_description = "Approved version"
set latest_final_hv.start_date = datetime()
set latest_final_hv.status = "Final"
set latest_final_hv.author_id = "unknown-user"
set latest_final_hv.version = "1.0"
set hv3.change_description = "Initial version"
set hv3.start_date = datetime()
set hv3.end_date = datetime()
set hv3.status = "Draft"
set hv3.author_id = "unknown-user"
set hv3.version = "0.1"

MERGE (cr)-[has_term2:HAS_TERM]->(term_root2:CTTermRoot {uid:"term_root_draft"})-[:HAS_ATTRIBUTES_ROOT]->
    (term_ver_root2:CTTermAttributesRoot)-[:LATEST]-(term_ver_value2:CTTermAttributesValue 
        {code_submission_value: "code_submission_value2", name_submission_value:"name_submission_value2", preferred_term:"preferred_term", definition:"definition"})
MERGE (term_ver_root2)-[ld:LATEST_DRAFT]->(term_ver_value2)
MERGE (term_ver_root2)-[hv5:HAS_VERSION]->(term_ver_value2)
MERGE (editable_lib)-[:CONTAINS_TERM]->(term_root2)
set has_term2.order = 2
set hv5.change_description = "latest draft"
set hv5.start_date = datetime()
set hv5.status = "Draft"
set hv5.author_id = "unknown-user"
set hv5.version = "0.1"

MERGE (cr2)-[has_term3:HAS_TERM]->(term_root3:CTTermRoot {uid:"term_root_final_non_edit"})-[:HAS_ATTRIBUTES_ROOT]->
    (term_ver_root3:CTTermAttributesRoot)-[:LATEST]-(term_ver_value3:CTTermAttributesValue 
        {code_submission_value: "code_submission_value3", name_submission_value:"name_submission_value3", preferred_term:"preferred_term", definition:"definition"})
MERGE (non_editable_lib)-[:CONTAINS_TERM]->(term_root3)
MERGE (term_ver_root3)-[hv6:HAS_VERSION]->(term_ver_value3)
MERGE (term_ver_root3)-[lf3:LATEST_FINAL]->(term_ver_value3)
CREATE (term_ver_root3)-[hv7:HAS_VERSION]->(term_ver_value3)
set has_term3.order = 3
set hv7.change_description = "Approved version"
set hv7.start_date = datetime()
set hv7.status = "Final"
set hv7.author_id = "unknown-user"
set hv7.version = "1.0"
set hv6.change_description = "Initial version"
set hv6.start_date = datetime()
set hv6.end_date = datetime()
set hv6.status = "Draft"
set hv6.author_id = "unknown-user"
set hv6.version = "0.1"

MERGE (cr2)-[has_term4:HAS_TERM]->(term_root4:CTTermRoot {uid:"term_root_draft_non_edit"})-[:HAS_ATTRIBUTES_ROOT]->
    (term_ver_root4:CTTermAttributesRoot)-[:LATEST]-(term_ver_value4:CTTermAttributesValue 
        {code_submission_value: "code_submission_value4", name_submission_value:"name_submission_value4", preferred_term:"preferred_term", definition:"definition"})
MERGE (term_ver_root4)-[ld2:LATEST_DRAFT]->(term_ver_value4)
MERGE (term_ver_root4)-[hv8:HAS_VERSION]->(term_ver_value4)
MERGE (non_editable_lib)-[:CONTAINS_TERM]->(term_root4)
set has_term4.order = 4
set hv8.change_description = "latest draft"
set hv8.start_date = datetime()
set hv8.status = "Draft"
set hv8.author_id = "unknown-user"
set hv8.version = "0.1"
"""

STARTUP_CT_TERM_NAME_CYPHER = """
MERGE (cc:CTCatalogue {name: "SDTM CT"})
MERGE (cc)-[:HAS_CODELIST]->(cr:CTCodelistRoot {uid:"editable_cr"})-[:HAS_NAME_ROOT]
->(codelist_ver_root:CTCodelistNameRoot)-[:LATEST_FINAL]->(codelist_ver_value:CTCodelistNameValue {name:"Objective Level"})
CREATE (codelist_ver_root)-[:LATEST]->(codelist_ver_value)
CREATE (codelist_ver_root)-[:HAS_VERSION{change_description: "Approved version",start_date: datetime(),status: "Final",author_id: "unknown-user",version : "1.0"}]->(codelist_ver_value)
MERGE (editable_lib:Library{ name:"Sponsor", is_editable:true})
MERGE (editable_lib)-[:CONTAINS_CODELIST]->(cr)

MERGE (cc)-[:HAS_CODELIST]->(cr2:CTCodelistRoot {uid:"non_editable_cr"})
MERGE (non_editable_lib:Library{ name:"CDISC"})
ON CREATE
    SET non_editable_lib.is_editable = false
MERGE (non_editable_lib)-[:CONTAINS_CODELIST]->(cr2)

MERGE (cr)-[has_term:HAS_TERM]->(term_root:CTTermRoot {uid:"term_root_final"})-[:HAS_NAME_ROOT]->
    (term_ver_root:CTTermNameRoot)-[:LATEST]-(term_ver_value:CTTermNameValue 
        {name:"term_value_name1", name_sentence_case:"term_value_name_sentence_case"})
MERGE (editable_lib)-[:CONTAINS_TERM]->(term_root)
MERGE (term_ver_root)-[hv1:HAS_VERSION]->(term_ver_value)
CREATE (term_ver_root)-[hv2:HAS_VERSION]->(term_ver_value)
MERGE (term_ver_root)-[lf:LATEST_FINAL]->(term_ver_value)
set has_term.order = 1
set hv2.change_description = "Approved version"
set hv2.start_date = datetime()
set hv2.status = "Final"
set hv2.author_id = "unknown-user"
set hv2.version = "1.0"
set hv1.change_description = "Initial version"
set hv1.start_date = datetime()
set hv1.end_date = datetime()
set hv1.status = "Draft"
set hv1.author_id = "unknown-user"
set hv1.version = "0.1"

MERGE (cr)-[has_term2:HAS_TERM]->(term_root2:CTTermRoot {uid:"term_root_draft"})-[:HAS_NAME_ROOT]->
    (term_ver_root2:CTTermNameRoot)-[:LATEST]-(term_ver_value2:CTTermNameValue 
        {name:"term_value_name2", name_sentence_case:"term_value_name_sentence_case"})
MERGE (term_ver_root2)-[ld:LATEST_DRAFT]->(term_ver_value2)
MERGE (term_ver_root2)-[hv3:HAS_VERSION]->(term_ver_value2)
MERGE (term_root2)-[:HAS_ATTRIBUTES_ROOT]->(term_attributes_root:CTTermAttributesRoot)-[ld_attributes:LATEST_DRAFT]->
(term_attributes_value:CTTermAttributesValue { 
                code_submission_value: "code_submission_value",
                name_submission_value: "name_submission_value",
                preferred_term: "nci_preferred_name",
                definition: "definition"})
MERGE (term_attributes_root)-[:LATEST]->(term_attributes_value)
MERGE (term_attributes_root)-[hv_attributes:HAS_VERSION]->(term_attributes_value)
MERGE (editable_lib)-[:CONTAINS_TERM]->(term_root2)
set has_term2.order = 2
set has_term2.start_date=datetime()
set has_term2.author_id= "unknown-user"
set hv3.change_description = "latest draft"
set hv3.start_date = datetime()
set hv3.status = "Draft"
set hv3.author_id = "unknown-user"
set hv3.version = "0.1"
set hv_attributes.change_description = "latest draft"
set hv_attributes.start_date = datetime()
set hv_attributes.status = "Draft"
set hv_attributes.author_id = "unknown-user"
set hv_attributes.version = "0.1"

MERGE (cr2)-[has_term3:HAS_TERM]->(term_root3:CTTermRoot {uid:"term_root_final_non_edit"})-[:HAS_NAME_ROOT]->
    (term_ver_root3:CTTermNameRoot)-[:LATEST]-(term_ver_value3:CTTermNameValue 
        {name:"term_value_name3", name_sentence_case:"term_value_name_sentence_case"})
MERGE (non_editable_lib)-[:CONTAINS_TERM]->(term_root3)
MERGE (term_ver_root3)-[hv4:HAS_VERSION]->(term_ver_value3)
MERGE (term_ver_root3)-[lf2:LATEST_FINAL]->(term_ver_value3)
CREATE (term_ver_root3)-[hv5:HAS_VERSION]->(term_ver_value3)
set has_term3.order = 3
set hv5.change_description = "Approved version"
set hv5.start_date = datetime()
set hv5.status = "Final"
set hv5.author_id = "unknown-user"
set hv5.version = "1.0"
set hv4.change_description = "Initial version"
set hv4.start_date = datetime()
set hv4.end_date = datetime()
set hv4.status = "Draft"
set hv4.author_id = "unknown-user"
set hv4.version = "0.1"

MERGE (cr2)-[has_term4:HAS_TERM]->(term_root4:CTTermRoot {uid:"term_root_draft_non_edit"})-[:HAS_NAME_ROOT]->
    (term_ver_root4:CTTermNameRoot)-[:LATEST]-(term_ver_value4:CTTermNameValue 
        {name:"term_value_name4", name_sentence_case:"term_value_name_sentence_case"})
MERGE (term_ver_root4)-[ld2:LATEST_DRAFT]->(term_ver_value4)
MERGE (term_ver_root4)-[hv6:HAS_VERSION]->(term_ver_value4)
MERGE (non_editable_lib)-[:CONTAINS_TERM]->(term_root4)
set has_term4.order = 4
set hv6.change_description = "latest draft"
set hv6.start_date = datetime()
set hv6.status = "Draft"
set hv6.author_id = "unknown-user"
set hv6.version = "0.1"

MERGE (cr)-[has_term5:HAS_TERM]->(term_root5:CTTermRoot {uid:"term_root_final5"})-[:HAS_NAME_ROOT]->
    (term_ver_root5:CTTermNameRoot)-[:LATEST]-(term_ver_value5:CTTermNameValue 
        {name:"term_value_name1", name_sentence_case:"term_value_name_sentence_case"})
MERGE (editable_lib)-[:CONTAINS_TERM]->(term_root5)
MERGE (term_ver_root5)-[hv7:HAS_VERSION]->(term_ver_value5)
CREATE (term_ver_root5)-[hv8:HAS_VERSION]->(term_ver_value5)
MERGE (term_ver_root5)-[lf12:LATEST_FINAL]->(term_ver_value5)
set has_term5.order = 1
set hv8.change_description = "Approved version"
set hv8.start_date = datetime()
set hv8.status = "Final"
set hv8.author_id = "unknown-user"
set hv8.version = "1.0"
set hv7.change_description = "Initial version"
set hv7.start_date = datetime()
set hv7.end_date = datetime()
set hv7.status = "Draft"
set hv7.author_id = "unknown-user"
set hv7.version = "0.1"
"""

STARTUP_PARAMETERS_CYPHER = f"""
WITH {{
    change_description: "Approved version",
    start_date: datetime(),
    status: "Final",
    author_id: "unknown-user",
    version: "1.0"
}} AS final_properties
MERGE (l:Library {{name:"Library", is_editable:true}})

MERGE (intervention:TemplateParameter {{name: 'Intervention'}})
MERGE (pr1:TemplateParameterTermRoot {{uid: 'Intervention-99991'}})-[:LATEST_FINAL]->(prv1:TemplateParameterTermValue {{name: 'human insulin'}})
MERGE (intervention)-[:HAS_PARAMETER_TERM]->(pr1)
MERGE (pr1)-[hv1:HAS_VERSION]->(prv1)
set hv1 = final_properties
MERGE (pr2:TemplateParameterTermRoot {{uid: 'Intervention-99992'}})-[:LATEST_FINAL]->(prv2:TemplateParameterTermValue {{name: 'Metformin'}})
MERGE (intervention)-[:HAS_PARAMETER_TERM]->(pr2)
MERGE (pr2)-[hv2:HAS_VERSION]->(prv2)
set hv2 = final_properties

MERGE (indication:TemplateParameter {{name: 'Indication'}})
MERGE (pr3:TemplateParameterTermRoot {{uid: 'Indication-99991'}})-[:LATEST_FINAL]->(prv3:TemplateParameterTermValue {{name: 'type 2 diabetes'}})
MERGE (indication)-[:HAS_PARAMETER_TERM]->(pr3)
MERGE (pr3)-[hv3:HAS_VERSION]->(prv3)
set hv3 = final_properties
MERGE (pr4:TemplateParameterTermRoot {{uid: 'Indication-99992'}})-[:LATEST_FINAL]->(prv4:TemplateParameterTermValue {{name: 'coronary heart disease'}})
MERGE (indication)-[:HAS_PARAMETER_TERM]->(pr4)
MERGE (pr4)-[hv4:HAS_VERSION]->(prv4)
set hv4 = final_properties
MERGE (pr5:TemplateParameterTermRoot {{uid: 'Indication-99993'}})-[:LATEST_FINAL]->(prv5:TemplateParameterTermValue {{name: 'breathing problems'}})
MERGE (indication)-[:HAS_PARAMETER_TERM]->(pr5)
MERGE (pr5)-[hv5:HAS_VERSION]->(prv5)
set hv5 = final_properties

//Study Endpoint
MERGE (endpoint:TemplateParameter {{name: '{config.STUDY_ENDPOINT_TP_NAME}'}})

CREATE (l)-[:CONTAINS]->(pr1)
CREATE (l)-[:CONTAINS]->(pr2)
CREATE (l)-[:CONTAINS]->(pr3)
CREATE (l)-[:CONTAINS]->(pr4)
CREATE (l)-[:CONTAINS]->(pr5)
"""

STARTUP_STUDY_FIELD_CYPHER = """
MERGE (l:Library {name:"CDISC", is_editable:false})
MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"catalogue_name"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
// Set counter for CTCodelist
MERGE (:Counter:CTCodelistCounter {count: 1, counterId:'CTCodelistCounter'})
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
CREATE (p2:Project {description: "Description DEF", name: "Project DEF", project_number: "456", uid :"project_uid_2"})
CREATE (c)-[:HOLDS_PROJECT]->(p2)
"""

STARTUP_STUDY_PROTOCOL_TITLE_CYPHER = """
WITH {
    change_description: "Approved version",
    start_date: datetime(),
    status: "Final",
    author_id: "unknown-user",
    version: "1.0"
} AS final_properties
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue)
MERGE (sr)-[hv:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
SET hv = final_properties
SET ld = final_properties
MERGE (sv)-[:HAS_TEXT_FIELD]->(:StudyField:StudyTextField {field_name: "eudract_id", value: "2019-123456-42"})
MERGE (sv)-[:HAS_TEXT_FIELD]->(:StudyField:StudyTextField {field_name: "investigational_new_drug_application_number_ind", value: "ind-number-777"})
MERGE (sv)-[:HAS_TEXT_FIELD]->(:StudyField:StudyTextField {field_name: "study_short_title", value: "Study short title"})
MERGE (cp:ClinicalProgramme{uid: "ClinicalProgramme_000001"})
    SET cp.name="Test CP"
MERGE (p:Project{uid: "Project_000001"})
    SET p.description="description", p.name="name", p.project_number="project_number"
MERGE (cp)-[:HOLDS_PROJECT]->(p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)

// Compound
CREATE (cr:ConceptRoot:CompoundRoot:TemplateParameterTermRoot {uid : "TemplateParameter_000001"})
CREATE (cv:ConceptValue:CompoundValue:TemplateParameterTermValue {definition: "definition", is_sponsor_compound: true, is_name_inn: true, name: "name", author_id: "author_id"})
MERGE (cr)-[lat:LATEST]->(cv)
MERGE (cr)-[lf:LATEST_FINAL]->(cv)
MERGE (cr)-[hv2:HAS_VERSION]->(cv)
MERGE (lib:Library{name:"Sponsor", is_editable:true})-[:CONTAINS_CONCEPT]->(cr)
MERGE (n:TemplateParameter {name : "Compound"})-[:HAS_PARAMETER_TERM]->(cr)
SET hv2 = final_properties

// Compound Alias
CREATE (car:ConceptRoot:CompoundAliasRoot:TemplateParameterTermRoot {uid : "TemplateParameter_000002"})
CREATE (cav:ConceptValue:CompoundAliasValue:TemplateParameterTermValue {definition: "definition", name: "name", author_id: "author_id"})
MERGE (car)-[lat1:LATEST]->(cav)
MERGE (car)-[lf1:LATEST_FINAL]->(cav)
MERGE (car)-[hv3:HAS_VERSION]->(cav)
MERGE (cav)-[:IS_COMPOUND]->(cr)
MERGE (lib)-[:CONTAINS_CONCEPT]->(car)
MERGE (:TemplateParameter {name : "CompoundAlias"})-[:HAS_PARAMETER_TERM]->(car)
SET hv3 = final_properties
MERGE (cav)-[:IS_COMPOUND]->(cr)

MERGE (sv)-[:HAS_STUDY_COMPOUND]->(sc:StudyCompound:StudySelection)-[:HAS_SELECTED_COMPOUND]->(cav)
set sc.order = 1
set sc.uid = "StudyCompound_000001"
CREATE (sa:StudyAction:Create)-[:AFTER]->(sc)
set sa.date = datetime()
set sa.author_id = "unknown-user"

WITH sc
MATCH (term_root:CTTermRoot {uid: "term_root_final"})
MERGE (sc)-[:HAS_TYPE_OF_TREATMENT]->(term_root)
"""

STARTUP_STUDY_CYPHER = """
MERGE (l:Library {name:"CDISC", is_editable:false})
MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"catalogue_name"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
// Set counter for CTCodelist
MERGE (:Counter:CTCodelistCounter {count: 1, counterId:'CTCodelistCounter'})
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
SET ld.start_date=datetime("2021-09-27"), ld.status="DRAFT"
MERGE (sr)-[lv:HAS_VERSION]->(sv)
SET lv.start_date=datetime("2021-09-27"), lv.status="DRAFT"
MERGE (p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
"""

STARTUP_STUDY_OBJECTIVE_CYPHER = """
MERGE (l:Library {name:"CDISC"})
ON CREATE 
    SET l.is_editable = false
MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"catalogue_name"})
MERGE (m:Counter{counterId:"CTCodelistCounter"})
ON CREATE SET m:CTCodelistCounter, m.count=0
WITH m
CALL apoc.atomic.add(m,'count',1,1) yield oldValue, newValue
MERGE (codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelist)
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:0})
MERGE (p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
MERGE (ot:ObjectiveTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid:"ObjectiveTemplate_000001", sequence_id: "O1"})-[relt:LATEST_FINAL]->(otv:ObjectiveTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name :"objective_1", name_plain : "objective_1"})
MERGE (ot)-[relthv:HAS_VERSION]->(otv)
MERGE (ot)-[:LATEST]->(otv)
MERGE (ot2:ObjectiveTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid:"ObjectiveTemplate_0000022", sequence_id: "O22"})-[relt2:LATEST_FINAL]->(otv2:ObjectiveTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name :"objective_2", name_plain : "objective_2"})
MERGE (ot2)-[relt2hv:HAS_VERSION]->(otv2)
MERGE (ot2)-[:LATEST]->(otv2)
MERGE (ot3:ObjectiveTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid:"ObjectiveTemplate_000003", sequence_id: "O3"})-[relt3:LATEST_FINAL]->(otv3:ObjectiveTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name :"objective_3", name_plain : "objective_3"})
MERGE (ot3)-[relt3hv:HAS_VERSION]->(otv3)
MERGE (ot3)-[:LATEST]->(otv3)
MERGE (ot4:ObjectiveTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid:"ObjectiveTemplate_000004", sequence_id: "O4"})-[relt4:LATEST_FINAL]->(otv4:ObjectiveTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name :"objective_4", name_plain : "objective_4"})
MERGE (ot4)-[relt4hv:HAS_VERSION]->(otv4)
MERGE (ot4)-[:LATEST]->(otv4)
MERGE (or:ObjectiveRoot:SyntaxInstanceRoot:SyntaxIndexingInstanceRoot)-[rel:LATEST_FINAL]->(ov:ObjectiveValue:SyntaxInstanceValue:SyntaxIndexingInstanceValue {name :"objective_1", name_plain : "objective_1"})
MERGE (or)-[relhv:HAS_VERSION]->(ov)
MERGE (or)-[:LATEST]->(ov)
MERGE (or2:ObjectiveRoot:SyntaxInstanceRoot:SyntaxIndexingInstanceRoot)-[rel2:LATEST_FINAL]->(ov2:ObjectiveValue:SyntaxInstanceValue:SyntaxIndexingInstanceValue {name :"objective_2", name_plain : "objective_2"})
MERGE (or2)-[rel2hv:HAS_VERSION]->(ov2)
MERGE (or2)-[:LATEST]->(ov2)
MERGE (or3:ObjectiveRoot:SyntaxInstanceRoot:SyntaxIndexingInstanceRoot)-[rel3:LATEST_DRAFT]->(ov3:ObjectiveValue:SyntaxInstanceValue:SyntaxIndexingInstanceValue {name :"objective_3", name_plain : "objective_3"})
MERGE (or3)-[rel3hv:HAS_VERSION]->(ov3)
MERGE (or3)-[:LATEST]->(ov3)
MERGE (or4:ObjectiveRoot:SyntaxInstanceRoot:SyntaxIndexingInstanceRoot)-[rel4:LATEST_RETIRED]->(ov4:ObjectiveValue:SyntaxInstanceValue:SyntaxIndexingInstanceValue {name :"objective_5", name_plain : "objective_5"})
MERGE (or4)-[rel4hv:HAS_VERSION]->(ov4)
MERGE (or4)-[:LATEST]->(ov4)
MERGE (lib:Library{name:"Sponsor", is_editable:true})
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(ot)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(ot2)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(ot3)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(ot4)
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(or)
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(or2)
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(or3)
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(or4)
MERGE (ot)-[:HAS_OBJECTIVE]->(or)
MERGE (ot2)-[:HAS_OBJECTIVE]->(or2)
MERGE (ot3)-[:HAS_OBJECTIVE]->(or3)
MERGE (ot4)-[:HAS_OBJECTIVE]->(or4)
set relthv.change_description="Approved version"
set relthv.start_date= datetime()
set relthv.status = "Final"
set relthv.author_id = "unknown-user"
set relthv.version = "1.0"
set relt2hv.change_description="Approved version"
set relt2hv.start_date= datetime()
set relt2hv.status = "Final"
set relt2hv.author_id = "unknown-user"
set relt2hv.version = "1.0"
set relt3hv.change_description="Approved version"
set relt3hv.start_date= datetime()
set relt3hv.status = "Final"
set relt3hv.author_id = "unknown-user"
set relt3hv.version = "1.0"
set relt4hv.change_description="Approved version"
set relt4hv.start_date= datetime()
set relt4hv.status = "Final"
set relt4hv.author_id = "unknown-user"
set relt4hv.version = "1.0"

set relhv.change_description="Approved version"
set relhv.start_date= datetime()
set relhv.status = "Final"
set relhv.author_id = "unknown-user"
set relhv.version = "1.0"
set rel2hv.change_description="Approved version"
set rel2hv.start_date= datetime()
set rel2hv.status = "Final"
set rel2hv.author_id = "unknown-user"
set rel2hv.version = "1.0"
set rel3hv.change_description="Initial version"
set rel3hv.start_date= datetime()
set rel3hv.status = "Draft"
set rel3hv.author_id = "unknown-user"
set rel3hv.version = "0.1"

set rel4hv.change_description="Retired version"
set rel4hv.start_date= datetime()
set rel4hv.status = "Retired"
set rel4hv.author_id = "unknown-user"
set rel4hv.version = "1.0"
"""

STARTUP_STUDY_ENDPOINT_CYPHER = """
MERGE (l:Library {name:"CDISC"})
ON CREATE 
    SET l.is_editable=false
MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"catalogue_name"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
// Set counter for CTCodelist
MERGE (counter:Counter{counterId:"CTCodelistCounter"})
ON CREATE SET counter:CTCodelistCounter, counter.count=0
WITH counter
CALL apoc.atomic.add(counter,'count',1,1) yield oldValue, newValue

WITH {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties

MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
WITH final_properties, p

MERGE (unit_def_root:ConceptRoot:UnitDefinitionRoot {uid:"unit 1"})-[:LATEST]-(unit_def_value:ConceptValue:UnitDefinitionValue {name:"name 1"})
MERGE (unit_def_root)-[unit_final1:LATEST_FINAL]-(unit_def_value)
MERGE (unit_def_root)-[unit_hv1:HAS_VERSION]-(unit_def_value)
SET unit_hv1 = final_properties
MERGE (unit_def_root2:ConceptRoot:UnitDefinitionRoot {uid:"unit 2"})-[:LATEST]-(unit_def_value2:ConceptValue:UnitDefinitionValue {name:"name 2"})
MERGE (unit_def_root2)-[unit_final2:LATEST_FINAL]-(unit_def_value2)
MERGE (unit_def_root2)-[unit_hv2:HAS_VERSION]-(unit_def_value2)
SET unit_hv2 = final_properties
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:"0"})
MERGE (p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
MERGE (sr)-[hv:HAS_VERSION]->(sv)
CREATE (sr)-[hv2:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
set hv.status = "DRAFT"
set hv.start_date = datetime()
set hv.author_id = "unknown-user"
set hv2 = hv
set ld = hv

MERGE (ot:ObjectiveTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid:"ObjectiveTemplate_000001", sequence_id: "O1"})-[relt:LATEST_FINAL]->(otv:ObjectiveTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name :"objective_1", name_plain : "objective_1"})
MERGE (or:ObjectiveRoot:SyntaxInstanceRoot:SyntaxIndexingInstanceRoot)-[rel:LATEST_FINAL]->(ov:ObjectiveValue:SyntaxInstanceValue:SyntaxIndexingInstanceValue {name : "objective_1", name_plain : "objective_1"})
MERGE (ot)-[relthv:HAS_VERSION]->(otv)
MERGE (or)-[relhv:HAS_VERSION]->(ov)
MERGE (or)-[:LATEST]->(ov)
MERGE (ot)-[:LATEST]->(otv)
MERGE (lib:Library{name:"Sponsor", is_editable:true})
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(or)
MERGE (ot)-[:HAS_OBJECTIVE]->(or)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(ot)
set relthv = final_properties

set relhv = final_properties

MERGE (sv)-[:HAS_STUDY_OBJECTIVE]->(so:StudyObjective:StudySelection)-[:HAS_SELECTED_OBJECTIVE]->(ov)
set so.order = 1
set so.uid = "StudyObjective_000001"
CREATE (sa:StudyAction:Create)-[:AFTER]->(so)
set sa.date = datetime()
set sa.author_id = "unknown-user"

// Set counter for study objective UID 
MERGE (:Counter:StudyObjectiveCounter {count: 1, counterId:'StudyObjectiveCounter'})

MERGE (et:EndpointTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid:"EndpointTemplate_000001", sequence_id: "E1"})-[end_relt:LATEST_FINAL]->(etv:EndpointTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er:EndpointRoot:SyntaxInstanceRoot:SyntaxIndexingInstanceRoot)-[end_rel:LATEST_FINAL]->(ev:EndpointValue:SyntaxInstanceValue:SyntaxIndexingInstanceValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er)-[:LATEST]->(ev)
MERGE (et)-[:LATEST]->(etv)
MERGE (er)-[end_rel_hv:HAS_VERSION]->(ev)
MERGE (et)-[end_relt_hv:HAS_VERSION]->(etv)
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(er)
MERGE (et)-[:HAS_ENDPOINT]->(er)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(et)
set end_relt_hv = final_properties
set end_rel_hv = final_properties

MERGE (et2:EndpointTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid:"EndpointTemplate_000022", sequence_id: "E22"})-[end_relt2:LATEST_FINAL]->(etv2:EndpointTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "endpoint_template_2", name_plain : "endpoint_template_2"})
MERGE (et2)-[:LATEST]->(etv2)
MERGE (et2)-[end_relt2_hv:HAS_VERSION]->(etv2)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(et2)
set end_relt2_hv = final_properties

MERGE (tt:TimeframeTemplateRoot:SyntaxTemplateRoot {uid:"TimeframeTemplate_000011", sequence_id: "T11"})-[tim_relt:LATEST_FINAL]->(ttv:TimeframeTemplateValue:SyntaxTemplateValue {name : "timeframe_1", name_plain : "timeframe_1"})
MERGE (tr:TimeframeRoot:SyntaxInstanceRoot)-[tim_rel:LATEST_FINAL]->(tv:TimeframeValue:SyntaxInstanceValue {name : "timeframe_1", name_plain : "timeframe_1"})
MERGE (tr)-[:LATEST]->(tv)
MERGE (tt)-[:LATEST]->(ttv)
MERGE (tr)-[tim_rel_hv:HAS_VERSION]->(tv)
MERGE (tt)-[tim_relt_hv:HAS_VERSION]->(ttv)
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(tr)
MERGE (tt)-[:HAS_TIMEFRAME]->(tr)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(tt)
set tim_relt_hv = final_properties
set tim_rel_hv = final_properties
WITH final_properties

MATCH (termroot:CTTermRoot {uid:"term_root_final"})
MERGE (termroot)<-[has_term:HAS_TERM]-(codelistroot:CTCodelistRoot {uid: "ct_codelist_root_endpoint"})-[:HAS_NAME_ROOT]->(cnr:CTCodelistNameRoot)-[:LATEST_FINAL]->
    (cnv:TemplateParameter:CTCodelistNameValue {name: "Endpoint Level"})
set has_term.order = 1
MERGE (cnr)-[clname_hv:HAS_VERSION]->(cnv)
MERGE (cnr)-[:LATEST]->(cnv)
set clname_hv = final_properties

WITH *
MATCH (termroot1:CTTermRoot {uid:"term_root_final5"})
MERGE (termroot1)<-[has_term1:HAS_TERM]-(codelistroot)
set has_term.order = 1

MERGE (catalogue:CTCatalogue {name:"SDTM CT"}) 
SET catalogue.uid="CTCatalogue_000001"
MERGE (catalogue)-[:HAS_CODELIST]->(codelistroot)

WITH *
MATCH (termroot2:CTTermRoot {uid:"term_root_final_non_edit"})
MERGE (termroot2)<-[has_term2:HAS_TERM]-(codelistroot2:CTCodelistRoot {uid: "ct_codelist_root_endpoint_sub"})-[:HAS_NAME_ROOT]->(cnr2:CTCodelistNameRoot)-[:LATEST_FINAL]->
    (cnv2:TemplateParameter:CTCodelistNameValue {name: "Endpoint Sub Level"})
set has_term2.order = 1
MERGE (cnr2)-[clname_hv2:HAS_VERSION]->(cnv2)
MERGE (cnr2)-[:LATEST]->(cnv2)
set clname_hv2 = final_properties

MERGE (catalogue)-[:HAS_CODELIST]->(codelistroot2)
"""

STARTUP_STUDY_LIST_CYPHER = """
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:"0"})
MERGE (sr)-[hv:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
set hv.status = "DRAFT"
set hv.start_date = datetime()
set hv.author_id = "unknown-user"
set ld = hv

MERGE (ot:ObjectiveTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid:"ObjectiveTemplate_000001", sequence_id: "O1"})-[relt:LATEST_FINAL]->(otv:ObjectiveTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "objective_1", name_plain : "objective_1"})
MERGE (or:ObjectiveRoot:SyntaxInstanceRoot:SyntaxIndexingInstanceRoot)-[rel:LATEST_FINAL]->(ov:ObjectiveValue:SyntaxInstanceValue:SyntaxIndexingInstanceValue {name : "objective_1", name_plain : "objective_1"})
MERGE (or)-[:LATEST]->(ov)
MERGE (ot)-[:LATEST]->(otv)
MERGE (or)-[rel_hv:HAS_VERSION]->(ov)
MERGE (ot)-[relt_hv:HAS_VERSION]->(otv)
MERGE (lib:Library{name:"Sponsor", is_editable:true})
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(or)
MERGE (ot)-[:HAS_OBJECTIVE]->(or)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(ot)
set relt_hv.change_description="Approved version"
set relt_hv.start_date= datetime()
set relt_hv.status = "Final"
set relt_hv.author_id = "unknown-user"
set relt_hv.version = "1.0"

set rel_hv.change_description="Approved version"
set rel_hv.start_date= datetime()
set rel_hv.status = "Final"
set rel_hv.author_id = "unknown-user"
set rel_hv.version = "1.0"

MERGE (sv)-[:HAS_STUDY_OBJECTIVE]->(so:StudyObjective:StudySelection)-[:HAS_SELECTED_OBJECTIVE]->(ov)
set so.order = 1
set so.uid = "StudyObjective_000001"
CREATE (sa:StudyAction:Create)-[:AFTER]->(so)
set sa.date = datetime()
set sa.author_id = "unknown-user"


MERGE (et:EndpointTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot)-[end_relt:LATEST_FINAL]->(etv:EndpointTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er:EndpointRoot:SyntaxInstanceRoot:SyntaxIndexingInstanceRoot)-[end_rel:LATEST_FINAL]->(ev:EndpointValue:SyntaxInstanceValue:SyntaxIndexingInstanceValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er)-[:LATEST]->(ev)
MERGE (et)-[:LATEST]->(etv)
MERGE (er)-[end_rel_hv:HAS_VERSION]->(ev)
MERGE (et)-[end_relt_hv:HAS_VERSION]->(etv)
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(er)
MERGE (et)-[:HAS_ENDPOINT]->(er)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(et)
set end_relt_hv.change_description="Approved version"
set end_relt_hv.start_date= datetime()
set end_relt_hv.status = "Final"
set end_relt_hv.author_id = "unknown-user"
set end_relt_hv.version = "1.0"

set end_rel_hv.change_description="Approved version"
set end_rel_hv.start_date= datetime()
set end_rel_hv.status = "Final"
set end_rel_hv.author_id = "unknown-user"
set end_rel_hv.version = "1.0"

MERGE (sv)-[:HAS_STUDY_ENDPOINT]->(se:StudyEndpoint:StudySelection)-[:HAS_SELECTED_ENDPOINT]->(ev)
set se.order = 1
set se.uid = "StudyEndpoint_000001"
CREATE (saa:StudyAction:Create)-[:AFTER]->(se)
set saa.date = datetime()
set saa.author_id = "unknown-user"

MERGE (cp:ClinicalProgramme{uid: "ClinicalProgramme_000001"})
    SET cp.name="Test CP"
MERGE (p:Project{uid: "Project_000001"})
    SET p.description="description", p.name="name", p.project_number="123"
MERGE (cp)-[:HOLDS_PROJECT]->(p)-[:HAS_FIELD]->(sf:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
"""

STARTUP_STUDY_COMPOUND_CYPHER = """
MERGE (l:Library {name:"CDISC", is_editable:false})
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
MERGE (c)-[:HOLDS_PROJECT]->(p)
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:0})
MERGE (p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
MERGE (sr)-[hv:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
set hv.status = "DRAFT"
set hv.start_date = datetime()
set hv.author_id = "unknown-user"
set ld = hv

// Compound
CREATE (cr:ConceptRoot:CompoundRoot:TemplateParameterTermRoot {uid : "TemplateParameter_000001"})
CREATE (cv:ConceptValue:CompoundValue:TemplateParameterTermValue {definition: "definition", is_sponsor_compound: true, is_name_inn: true, name: "name", author_id: "author_id"})
MERGE (cr)-[lat:LATEST]->(cv)
MERGE (cr)-[lf:LATEST_FINAL]->(cv)
MERGE (cr)-[fhvc:HAS_VERSION]->(cv)
CREATE (cr)-[dhvc:HAS_VERSION]->(cv)
MERGE (lib:Library{name:"Sponsor", is_editable:true})-[:CONTAINS_CONCEPT]->(cr)
MERGE (n:TemplateParameter {name : "Compound"})-[:HAS_PARAMETER_TERM]->(cr)
set fhvc.change_description = "Approved version"
set fhvc.start_date = datetime()
set fhvc.status = "Final"
set fhvc.author_id = "unknown-user"
set fhvc.version = "1.0"
set dhvc.change_description = "Initial version"
set dhvc.start_date = datetime()
set dhvc.end_date = datetime()
set dhvc.status = "Draft"
set dhvc.author_id = "unknown-user"
set dhvc.version = "0.1"

// Compound Alias
CREATE (car:ConceptRoot:CompoundAliasRoot:TemplateParameterTermRoot {uid : "TemplateParameter_000002"})
CREATE (cav:ConceptValue:CompoundAliasValue:TemplateParameterTermValue {definition: "definition", name: "name", author_id: "author_id"})
MERGE (car)-[lat1:LATEST]->(cav)
MERGE (car)-[lf1:LATEST_FINAL]->(cav)
MERGE (car)-[hv1:HAS_VERSION]->(cav)
MERGE (cav)-[:IS_COMPOUND]->(cr)
MERGE (lib)-[:CONTAINS_CONCEPT]->(car)
MERGE (:TemplateParameter {name : "CompoundAlias"})-[:HAS_PARAMETER_TERM]->(car)
set hv1.change_description = "Approved version"
set hv1.start_date = datetime()
set hv1.status = "Final"
set hv1.author_id = "unknown-user"
set hv1.version = "1.0"

// Pharmaceutical dosage form
WITH (cv)
MATCH (term_root:CTTermRoot {uid: "CTTerm_000003"})
MERGE (cv)-[:HAS_DOSAGE_FORM]->(term_root)

// Route of administration
WITH (cv)
MATCH (term_root:CTTermRoot {uid: "CTTerm_000002"})
MERGE (cv)-[:HAS_ROUTE_OF_ADMINISTRATION]->(term_root)

// Delivery device
WITH (cv)
MATCH (term_root:CTTermRoot {uid: "CTTerm_000005"})
MERGE (cv)-[:HAS_DELIVERY_DEVICE]->(term_root)

// Dispenser
WITH (cv)
MATCH (term_root:CTTermRoot {uid: "CTTerm_000004"})
MERGE (cv)-[:HAS_DISPENSER]->(term_root)

// Dose frequency
WITH (cv)
MATCH (term_root:CTTermRoot {uid: "dose_frequency_uid1"})
MERGE (cv)-[:HAS_DOSE_FREQUENCY]->(term_root)

WITH (cv)
MATCH (term_root:CTTermRoot {uid: "dose_frequency_uidXYZ"})
MERGE (cv)-[:HAS_DOSE_FREQUENCY]->(term_root)

// Strength
WITH (cv)
MATCH (term_root:NumericValueWithUnitRoot {uid: "NumericValueWithUnit_000001"})
MERGE (cv)-[:HAS_STRENGTH_VALUE]->(term_root)

// Half-life
WITH (cv)
MATCH (term_root:NumericValueWithUnitRoot {uid: "NumericValueWithUnit_000001"})
MERGE (cv)-[:HAS_HALF_LIFE]->(term_root)

// Dose value
WITH (cv)
MATCH (term_root:NumericValueWithUnitRoot {uid: "NumericValueWithUnit_000001"})
MERGE (cv)-[:HAS_DOSE_VALUE]->(term_root)

// Lag-time
// WITH (cv)
// MATCH (term_root:NumericValueWithUnitRoot {uid: "LagTime_000001"})
// MERGE (cv)-[:HAS_LAG_TIME]->(term_root)
"""

STARTUP_STUDY_COMPOUND_DOSING_CYPHER = """
MATCH (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue)
MATCH (est:CTTermRoot {uid: "ElementSubTypeTermUid_1"})
MERGE (sv)-[:HAS_STUDY_ELEMENT]->(se:StudyElement:StudySelection)-[:HAS_ELEMENT_SUBTYPE]->(est)
set se.order = 1
set se.uid = "StudyElement_000001"
set se.name = "Element_Name_1"
set se.short_name = "Element_Short_Name_1"
set se.code = "Code1"
set se.description = "Description"
CREATE (sa1:StudyAction:Create)-[:AFTER]->(se)
set sa1.date = datetime()
set sa1.author_id = "unknown-user"

WITH sv
MATCH (cav:CompoundAliasValue)<-[:LATEST]-(car:CompoundAliasRoot {uid: "TemplateParameter_000002"})
MERGE (sv)-[:HAS_STUDY_COMPOUND]->(sc:StudyCompound:StudySelection)-[:HAS_SELECTED_COMPOUND]->(cav)
set sc.order = 1
set sc.uid = "StudyCompound_000001"
CREATE (sa2:StudyAction:Create)-[:AFTER]->(sc)
set sa2.date = datetime()
set sa2.author_id = "unknown-user"

WITH sc
MATCH (term_root:CTTermRoot {uid: "CTTerm_000001"})
MERGE (sc)-[:HAS_TYPE_OF_TREATMENT]->(term_root)
"""

STARTUP_STUDY_CRITERIA_CYPHER = """
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
WITH p

MATCH (incl:CTTermRoot {uid: "C25532"}), (excl:CTTermRoot {uid: "C25370"})
MERGE (library:Library{name: "Sponsor", is_editable: True})
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:0})
MERGE (p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
MERGE (incl)<-[:HAS_TYPE]-(ctr1:CriteriaTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid: "incl_criteria_1"})-[relt:LATEST_FINAL]->(ctv1:CriteriaTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "incl_criteria_1", guidance_text: "Guidance text", name_plain : "incl_criteria_1"})
MERGE (incl)<-[:HAS_TYPE]-(ctr2:CriteriaTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid: "incl_criteria_2"})-[relt2:LATEST_FINAL]->(ctv2:CriteriaTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "incl_criteria_2", name_plain : "incl_criteria_2"})
MERGE (incl)<-[:HAS_TYPE]-(ctr3:CriteriaTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid: "incl_criteria_3"})-[relt3:LATEST_FINAL]->(ctv3:CriteriaTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "incl_criteria_3", name_plain : "incl_criteria_3"})
MERGE (incl)<-[:HAS_TYPE]-(ctr4:CriteriaTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid: "incl_criteria_4"})-[relt4:LATEST_FINAL]->(ctv4:CriteriaTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "incl_criteria_4", name_plain : "incl_criteria_4"})
MERGE (ctr1)-[:LATEST]->(ctv1)
MERGE (ctr2)-[:LATEST]->(ctv2)
MERGE (ctr3)-[:LATEST]->(ctv3)
MERGE (ctr4)-[:LATEST]->(ctv4)
MERGE (ctr1)-[hv1:HAS_VERSION]->(ctv1)
MERGE (ctr2)-[hv2:HAS_VERSION]->(ctv2)
MERGE (ctr3)-[hv3:HAS_VERSION]->(ctv3)
MERGE (ctr4)-[hv4:HAS_VERSION]->(ctv4)
set hv1.change_description="Approved version"
set hv1.start_date= datetime()
set hv1.status = "Final"
set hv1.author_id = "unknown-user"
set hv1.version = "1.0"
set hv2.change_description="Approved version"
set hv2.start_date= datetime()
set hv2.status = "Final"
set hv2.author_id = "unknown-user"
set hv2.version = "1.0"
set hv3.change_description="Approved version"
set hv3.start_date= datetime()
set hv3.status = "Final"
set hv3.author_id = "unknown-user"
set hv3.version = "1.0"
set hv4.change_description="Approved version"
set hv4.start_date= datetime()
set hv4.status = "Final"
set hv4.author_id = "unknown-user"
set hv4.version = "1.0"
MERGE (library)-[:CONTAINS_SYNTAX_TEMPLATE]->(ctr1)
MERGE (library)-[:CONTAINS_SYNTAX_TEMPLATE]->(ctr2)
MERGE (library)-[:CONTAINS_SYNTAX_TEMPLATE]->(ctr3)
MERGE (library)-[:CONTAINS_SYNTAX_TEMPLATE]->(ctr4)
MERGE (excl)<-[:HAS_TYPE]-(ctr5:CriteriaTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid: "excl_criteria_1"})-[relt5:LATEST_FINAL]->(ctv5:CriteriaTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name :"excl_criteria_1", name_plain : "excl_criteria_1"})
MERGE (excl)<-[:HAS_TYPE]-(ctr6:CriteriaTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid: "excl_criteria_2"})-[relt6:LATEST_FINAL]->(ctv6:CriteriaTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name :"excl_criteria_2", name_plain : "excl_criteria_2"})
MERGE (ctr5)-[:LATEST]->(ctv5)
MERGE (ctr6)-[:LATEST]->(ctv6)
MERGE (ctr5)-[hv5:HAS_VERSION]->(ctv5)
MERGE (ctr6)-[hv6:HAS_VERSION]->(ctv6)
set hv5.change_description="Approved version"
set hv5.start_date= datetime()
set hv5.status = "Final"
set hv5.author_id = "unknown-user"
set hv5.version = "1.0"
set hv6.change_description="Approved version"
set hv6.start_date= datetime()
set hv6.status = "Final"
set hv6.author_id = "unknown-user"
set hv6.version = "1.0"
MERGE (library)-[:CONTAINS_SYNTAX_TEMPLATE]->(ctr5)
MERGE (library)-[:CONTAINS_SYNTAX_TEMPLATE]->(ctr6)
"""


STARTUP_STUDY_ACTIVITY_CYPHER = """
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue)
"""

STARTUP_SINGLE_STUDY_CYPHER = """
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:"0"})
MERGE (sr)-[hv:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
set hv.status = "DRAFT"
set hv.start_date = datetime()
set hv.author_id = "unknown-user"
set ld.status = "DRAFT"
set ld.start_date = datetime()
set ld.author_id = "unknown-user"
"""

REMOVE_TRIGGERS = """
CALL apoc.trigger.removeAll();
"""

CREATE_BASE_TEMPLATE_PARAMETER_TREE = f"""
        // activity
        MERGE (activity:TemplateParameter {{name: "Activity"}})
        // activity sub group
        MERGE (activity_subgroup:TemplateParameter {{name: "ActivitySubGroup"}})
        // activity group
        MERGE (activity_group:TemplateParameter {{name: "ActivityGroup"}})
        // activity-instance
        MERGE (activity_instance:TemplateParameter {{name: "ActivityInstance"}})

        // reminders
        MERGE (reminder:TemplateParameter {{name: "Reminder"}})
        MERGE (reminder)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        
        // interventions
        MERGE (interventions:TemplateParameter {{name: "Intervention"}})
        MERGE (interventions)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        MERGE (compound_dosing:TemplateParameter {{name: "CompoundDosing"}})
        MERGE (compound_dosing)-[:HAS_PARENT_PARAMETER]->(interventions)
        MERGE (compound_alias:TemplateParameter {{name: "CompoundAlias"}})
        MERGE (compound_alias)-[:HAS_PARENT_PARAMETER]->(compound_dosing)
        
        // special-purposes
        MERGE (special_purposes:TemplateParameter {{name: "SpecialPurpose"}})
        MERGE (special_purposes)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        
        // findings
        MERGE (findings:TemplateParameter {{name: "Finding"}})
        MERGE (findings)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        MERGE (categoric_finding:TemplateParameter {{name: "CategoricFinding"}})
        MERGE (categoric_finding)-[:HAS_PARENT_PARAMETER]->(findings)
        MERGE (rating_scale:TemplateParameter {{name: "RatingScale"}})
        MERGE (rating_scale)-[:HAS_PARENT_PARAMETER]->(categoric_finding)
        MERGE (laboratory_activity:TemplateParameter {{name: "LaboratoryActivity"}})
        MERGE (laboratory_activity)-[:HAS_PARENT_PARAMETER]->(categoric_finding)
        MERGE (numeric_finding:TemplateParameter {{name: "NumericFinding"}})
        MERGE (numeric_finding)-[:HAS_PARENT_PARAMETER]->(findings)
        MERGE (laboratory_activity)-[:HAS_PARENT_PARAMETER]->(numeric_finding)
        MERGE (textual_finding:TemplateParameter {{name: "TextualFinding"}})
        MERGE (textual_finding)-[:HAS_PARENT_PARAMETER]->(findings)

        // events
        MERGE (events:TemplateParameter {{name: "Event"}})
        MERGE (events)-[:HAS_PARENT_PARAMETER]->(activity_instance)

        //simple concepts
        MERGE (simple_concepts:TemplateParameter {{name:"SimpleConcept"}})
        MERGE (numeric_values:TemplateParameter {{name:"NumericValue"}})
        MERGE (numeric_values)-[:HAS_PARENT_PARAMETER]->(simple_concepts)
        MERGE (numeric_value_with_unit:TemplateParameter {{name:"NumericValueWithUnit"}})
        MERGE (numeric_value_with_unit)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (text_values:TemplateParameter {{name:"TextValue"}})
        MERGE (text_values)-[:HAS_PARENT_PARAMETER]->(simple_concepts)
        MERGE (visit_names:TemplateParameter {{name:"VisitName"}})
        MERGE (visit_names)-[:HAS_PARENT_PARAMETER]->(text_values)
        MERGE (study_days:TemplateParameter {{name:"StudyDay"}})
        MERGE (study_days)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (study_weeks:TemplateParameter {{name:"StudyWeek"}})
        MERGE (study_weeks)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (study_duration_days:TemplateParameter {{name:"StudyDurationDays"}})
        MERGE (study_duration_days)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (study_duration_weeks:TemplateParameter {{name:"StudyDurationWeeks"}})
        MERGE (study_duration_weeks)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (week_in_study:TemplateParameter {{name:"WeekInStudy"}})
        MERGE (week_in_study)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (time_points:TemplateParameter {{name:"TimePoint"}})
        MERGE (time_points)-[:HAS_PARENT_PARAMETER]->(simple_concepts)
        MERGE (lag_time:TemplateParameter {{name:"LagTime"}})
        MERGE (lag_time)-[:HAS_PARENT_PARAMETER]->(numeric_values)

        //Study Endpoint
        MERGE (endpoint:TemplateParameter {{name: '{config.STUDY_ENDPOINT_TP_NAME}'}})
"""

CREATE_NA_TEMPLATE_PARAMETER = """
   MERGE (r:TemplateParameterTermRoot{uid: "NA"})
    WITH r
    OPTIONAL MATCH (r)-[x:HAS_VERSION|LATEST|LATEST_FINAL]->()
    DELETE x
    WITH r
    MERGE (r)-[:LATEST]->(v:TemplateParameterTermValue{name: "NA"})
    MERGE (r)-[:LATEST_FINAL]->(v)
    MERGE (r)-[:HAS_VERSION{change_description: "initial version", start_date: datetime(), end_date: datetime(), status: "Final", author_id: "import-procedure", version: "1.0"}]->(v)
    WITH r
    MATCH (n:TemplateParameter) 
    MERGE (n)-[:HAS_PARAMETER_TERM]->(r)
    """


def get_codelist_with_term_cypher(
    name: str,
    codelist_name: str = "tp_codelist_name_value",
    codelist_uid: str = "ct_codelist_root1",
    term_uid: str = "term_root_final",
) -> str:
    return """
WITH {
  change_description: "Approved version",
  start_date: datetime("2020-06-26T00:00:00"),
  status: "Final",
  author_id: "unknown-user",
  version: "1.0"
} AS final_version_props
MERGE (clr:CTCodelistRoot {uid: "%(codelist_uid)s"})
MERGE (clr)-[:HAS_NAME_ROOT]->(cnr:CTCodelistNameRoot)-[:LATEST]->
    (cnv:TemplateParameter:CTCodelistNameValue {name: "%(codelist_name)s"})
MERGE (cc:CTCatalogue {name: "SDTM CT"})
MERGE (cc)-[:HAS_CODELIST]->(clr)
MERGE (cnr)-[cl_lf:LATEST_FINAL]->(cnv)
MERGE (cnr)-[cl_hv:HAS_VERSION]->(cnv)
set cl_hv = final_version_props
MERGE (lib:Library {name: "Sponsor", is_editable: true})
MERGE (lib)-[:CONTAINS_CODELIST]->(clr)

MERGE (clr)-[has_term1:HAS_TERM]->(term_root:CTTermRoot {uid:"%(term_uid)s"})-[:HAS_ATTRIBUTES_ROOT]->
    (term_ver_root:CTTermAttributesRoot)-[:LATEST]-(term_ver_value:CTTermAttributesValue
        {code_submission_value: "code_submission_value1", name_submission_value:"name_submission_value1",
        preferred_term:"preferred_term", definition:"definition"})
MERGE (term_root)-[:HAS_NAME_ROOT]->(term_name_ver_root:CTTermNameRoot)-[:LATEST]-(term_name_ver_value:CTTermNameValue
        {name: "%(name)s", name_sentence_case:"term_value_name_sentence_case"})
MERGE (lib)-[:CONTAINS_TERM]->(term_root)
MERGE (term_ver_root)-[lf:LATEST_FINAL]->(term_ver_value)
MERGE (term_ver_root)-[hv:HAS_VERSION]->(term_ver_value)
set hv = final_version_props
MERGE (term_name_ver_root)-[tnvr_lf:LATEST_FINAL]->(term_name_ver_value)
MERGE (term_name_ver_root)-[tnvr_hv:HAS_VERSION]->(term_name_ver_value)
set tnvr_hv = final_version_props
""" % {
        "name": name,
        "codelist_name": codelist_name,
        "codelist_uid": codelist_uid,
        "term_uid": term_uid,
    }


STARTUP_STUDY_ARM_CYPHER = """
WITH {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties

MERGE (l:Library {name:"CDISC", is_editable:false})
MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"catalogue_name"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
// Set counter for CTCodelist
MERGE (:Counter:CTCodelistCounter {count: 1, counterId:'CTCodelistCounter'})
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
WITH final_properties, p

MERGE (unit_def_root:ConceptRoot:UnitDefinitionRoot {uid:"unit 1"})-[:LATEST]-(unit_def_value:ConceptValue:UnitDefinitionValue {name:"name 1"})
MERGE (unit_def_root)-[unit_final1:LATEST_FINAL]-(unit_def_value)
MERGE (unit_def_root)-[unit_hv1:HAS_VERSION]-(unit_def_value)
SET unit_hv1 = final_properties
MERGE (unit_def_root2:ConceptRoot:UnitDefinitionRoot {uid:"unit 2"})-[:LATEST]-(unit_def_value2:ConceptValue:UnitDefinitionValue {name:"name 2"})
MERGE (unit_def_root2)-[unit_final2:LATEST_FINAL]-(unit_def_value2)
MERGE (unit_def_root2)-[unit_hv2:HAS_VERSION]-(unit_def_value2)
SET unit_hv2 = final_properties
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:"0"})
MERGE (p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
MERGE (sr)-[hv:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
set hv.status = "DRAFT"
set hv.start_date = datetime()
set hv.author_id = "unknown-user"
set ld = hv


MERGE (ot:ObjectiveTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid:"ObjectiveTemplate_000001", sequence_id: "O1"})-[relt:LATEST_FINAL]->(otv:ObjectiveTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "objective_1", name_plain : "objective_1"})
MERGE (or:ObjectiveRoot:SyntaxInstanceRoot:SyntaxIndexingInstanceRoot)-[rel:LATEST_FINAL]->(ov:ObjectiveValue:SyntaxInstanceValue:SyntaxIndexingInstanceValue {name : "objective_1", name_plain : "objective_1"})
MERGE (or)-[:LATEST]->(ov)
MERGE (ot)-[:LATEST]->(otv)
MERGE (or)-[rel_hv:HAS_VERSION]->(ov)
MERGE (ot)-[relt_hv:HAS_VERSION]->(otv)
MERGE (lib:Library{name:"Sponsor", is_editable:true})
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(or)
MERGE (ot)-[:HAS_OBJECTIVE]->(or)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(ot)
set relt_hv = final_properties

set rel_hv = final_properties

MERGE (sv)-[:HAS_STUDY_OBJECTIVE]->(so:StudyObjective:StudySelection)-[:HAS_SELECTED_OBJECTIVE]->(ov)
set so.order = 1
set so.uid = "StudyObjective_000001"
CREATE (sa:StudyAction:Create)-[:AFTER]->(so)
set sa.date = datetime()
set sa.author_id = "unknown-user"

// Set counter for study objective UID 
MERGE (:Counter:StudyObjectiveCounter {count: 1, counterId:'StudyObjectiveCounter'})

MERGE (et:EndpointTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot)-[end_relt:LATEST_FINAL]->(etv:EndpointTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er:EndpointRoot:SyntaxInstanceRoot:SyntaxIndexingInstanceRoot)-[end_rel:LATEST_FINAL]->(ev:EndpointValue:SyntaxInstanceValue:SyntaxIndexingInstanceValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er)-[:LATEST]->(ev)
MERGE (et)-[:LATEST]->(etv)
MERGE (er)-[end_rel_hv:HAS_VERSION]->(ev)
MERGE (et)-[end_relt_hv:HAS_VERSION]->(etv)
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(er)
MERGE (et)-[:HAS_ENDPOINT]->(er)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(et)
set end_relt_hv = final_properties
set end_rel_hv = final_properties

MERGE (et2:EndpointTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot)-[end_relt2:LATEST_FINAL]->(etv2:EndpointTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "endpoint_template_2", name_plain : "endpoint_template_2"})
MERGE (et2)-[:LATEST]->(etv2)
MERGE (et2)-[end_relt2_hv:HAS_VERSION]->(etv2)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(et2)
set end_relt2_hv = final_properties

MERGE (tt:TimeframeTemplateRoot:SyntaxTemplateRoot)-[tim_relt:LATEST_FINAL]->(ttv:TimeframeTemplateValue:SyntaxTemplateValue {name : "timeframe_1", name_plain : "timeframe_1"})
MERGE (tr:TimeframeRoot:SyntaxInstanceRoot)-[tim_rel:LATEST_FINAL]->(tv:TimeframeValue:SyntaxInstanceValue {name : "timeframe_1", name_plain : "timeframe_1"})
MERGE (tr)-[:LATEST]->(tv)
MERGE (tt)-[:LATEST]->(ttv)
MERGE (tr)-[tim_rel_hv:HAS_VERSION]->(tv)
MERGE (tt)-[tim_relt_hv:HAS_VERSION]->(ttv)
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(tr)
MERGE (tt)-[:HAS_TIMEFRAME]->(tr)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(tt)
set tim_relt_hv = final_properties
set tim_rel_hv = final_properties
WITH final_properties

MATCH (termroot:CTTermRoot {uid:"term_root_final"})
MERGE (termroot)<-[has_term:HAS_TERM]-(codelistroot:CTCodelistRoot {uid: "ct_codelist_root_endpoint"})-[:HAS_NAME_ROOT]->(cnr:CTCodelistNameRoot)-[:LATEST_FINAL]->
    (cnv:TemplateParameter:CTCodelistNameValue {name: "Endpoint Level"})
set has_term.order = 1
MERGE (cnr)-[clname_hv:HAS_VERSION]->(cnv)
set clname_hv = final_properties

MERGE (catalogue:CTCatalogue {name:"SDTM CT"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelistroot)
"""

STARTUP_STUDY_ELEMENT_CYPHER = """
WITH {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
author_id: "unknown-user",
version: "1.0"
} AS final_properties

MERGE (l:Library {name:"CDISC", is_editable:false})
MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"catalogue_name"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
// Set counter for CTCodelist
MERGE (:Counter:CTCodelistCounter {count: 1, counterId:'CTCodelistCounter'})
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
WITH final_properties, p

MERGE (unit_def_root:ConceptRoot:UnitDefinitionRoot {uid:"unit 1"})-[:LATEST]-(unit_def_value:ConceptValue:UnitDefinitionValue {name:"name 1"})
MERGE (unit_def_root)-[unit_final1:LATEST_FINAL]-(unit_def_value)
SET unit_final1 = final_properties
MERGE (unit_def_root2:ConceptRoot:UnitDefinitionRoot {uid:"unit 2"})-[:LATEST]-(unit_def_value2:ConceptValue:UnitDefinitionValue {name:"name 2"})
MERGE (unit_def_root2)-[unit_final2:LATEST_FINAL]-(unit_def_value2)
SET unit_final2 = final_properties
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:"0"})
MERGE (p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
MERGE (sr)-[hv:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
set hv.status = "DRAFT"
set hv.start_date = datetime()
set hv.author_id = "unknown-user"
set ld = hv

MERGE (ot:ObjectiveTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid:"ObjectiveTemplate_000001", sequence_id: "O1"})-[relt:LATEST_FINAL]->(otv:ObjectiveTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "objective_1", name_plain : "objective_1"})
MERGE (or:ObjectiveRoot:SyntaxInstanceRoot:SyntaxIndexingInstanceRoot)-[rel:LATEST_FINAL]->(ov:ObjectiveValue:SyntaxInstanceValue:SyntaxIndexingInstanceValue {name : "objective_1", name_plain : "objective_1"})
MERGE (or)-[:LATEST]->(ov)
MERGE (ot)-[:LATEST]->(otv)
MERGE (or)-[hv2:HAS_VERSION]->(ov)
MERGE (ot)-[hv2t:HAS_VERSION]->(otv)
MERGE (lib:Library{name:"Sponsor", is_editable:true})
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(or)
MERGE (ot)-[:HAS_OBJECTIVE]->(or)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(ot)
set hv2t = final_properties

set hv2 = final_properties

MERGE (sv)-[:HAS_STUDY_OBJECTIVE]->(so:StudyObjective:StudySelection)-[:HAS_SELECTED_OBJECTIVE]->(ov)
set so.order = 1
set so.uid = "StudyObjective_000001"
CREATE (sa:StudyAction:Create)-[:AFTER]->(so)
set sa.date = datetime()
set sa.author_id = "unknown-user"

// Set counter for study objective UID 
MERGE (:Counter:StudyObjectiveCounter {count: 1, counterId:'StudyObjectiveCounter'})

MERGE (et:EndpointTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot)-[end_relt:LATEST_FINAL]->(etv:EndpointTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er:EndpointRoot:SyntaxInstanceRoot:SyntaxIndexingInstanceRoot)-[end_rel:LATEST_FINAL]->(ev:EndpointValue:SyntaxInstanceValue:SyntaxIndexingInstanceValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er)-[:LATEST]->(ev)
MERGE (et)-[:LATEST]->(etv)
MERGE (er)-[hv3:HAS_VERSION]->(ev)
MERGE (et)-[hv3t:HAS_VERSION]->(etv)
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(er)
MERGE (et)-[:HAS_ENDPOINT]->(er)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(et)
set hv3t = final_properties
set hv3 = final_properties

MERGE (et2:EndpointTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot)-[end_relt2:LATEST_FINAL]->(etv2:EndpointTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "endpoint_template_2", name_plain : "endpoint_template_2"})
MERGE (et2)-[:LATEST]->(etv2)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(et2)
set end_relt2 = final_properties

MERGE (tt:TimeframeTemplateRoot:SyntaxTemplateRoot)-[tim_relt:LATEST_FINAL]->(ttv:TimeframeTemplateValue:SyntaxTemplateValue {name : "timeframe_1", name_plain : "timeframe_1"})
MERGE (tr:TimeframeRoot:SyntaxInstanceRoot)-[tim_rel:LATEST_FINAL]->(tv:TimeframeValue:SyntaxInstanceValue {name : "timeframe_1", name_plain : "timeframe_1"})
MERGE (tr)-[:LATEST]->(tv)
MERGE (tt)-[:LATEST]->(ttv)
MERGE (tr)-[hv4:HAS_VERSION]->(tv)
MERGE (tt)-[hv4t:HAS_VERSION]->(ttv)
MERGE (lib)-[:CONTAINS_SYNTAX_INSTANCE]->(tr)
MERGE (tt)-[:HAS_TIMEFRAME]->(tr)
MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(tt)
set hv4t = final_properties
set hv4 = final_properties
WITH tim_rel

MATCH (termroot:CTTermRoot {uid:"term_root_final"})
MERGE (termroot)<-[has_term:HAS_TERM]-(codelistroot:CTCodelistRoot {uid: "ct_codelist_root_endpoint"})-[:HAS_NAME_ROOT]->(cnr:CTCodelistNameRoot)-[:LATEST_FINAL]->
    (cnv:TemplateParameter:CTCodelistNameValue {name: "Endpoint Level"})
set has_term.order = 1

MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"SDTM CT"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelistroot)
"""


STARTUP_STUDY_BRANCH_ARM_CYPHER = """
MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)
MERGE (sv)-[:HAS_STUDY_ARM]->(sar:StudyArm:StudySelection{uid : "StudyArm_000001"})
set sar.order = 1
set sar.name = "StudyArm_000001"
set sar.short_name = "StudyArm_000001"
CREATE (sa2:StudyAction:Create)-[:AFTER]->(sar)
set sa2.date = datetime()
set sa2.author_id = "unknown-user"
MERGE (sr)-[:AUDIT_TRAIL]->(sa2)
// Set counter for study arm UID 
MERGE (:Counter:StudyArmCounter {count: 1, counterId:'StudyArmCounter'})

WITH sv

MATCH (termroot:CTTermRoot {uid:"term_root_final"})
MATCH (sar:StudyArm {uid:"StudyArm_000001"})
CREATE (sar)-[:HAS_ARM_TYPE]->(termroot)

WITH sv


MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)
MERGE (sv)-[:HAS_STUDY_ARM]->(sar:StudyArm:StudySelection{uid : "StudyArm_000002"})
set sar.order = 2
set sar.name = "StudyArm_000002"
set sar.short_name = "StudyArm_000002"
CREATE (sa2:StudyAction:Create)-[:AFTER]->(sar)
set sa2.date = datetime()
set sa2.author_id = "unknown-user"
MERGE (sr)-[:AUDIT_TRAIL]->(sa2)
// Set counter for study arm UID 
MERGE (:Counter:StudyArmCounter {count: 2, counterId:'StudyArmCounter2'})

WITH sv
MATCH (termroot:CTTermRoot {uid:"term_root_final_non_edit"})
MATCH (sar:StudyArm {uid:"StudyArm_000002"})
CREATE (sar)-[:HAS_ARM_TYPE]->(termroot)

WITH sv

MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)
MERGE (sv)-[:HAS_STUDY_ARM]->(sar:StudyArm:StudySelection{uid : "StudyArm_000003"})
set sar.order = 3
set sar.name = "StudyArm_000003"
set sar.short_name = "StudyArm_000003"
CREATE (sa3:StudyAction:Create)-[:AFTER]->(sar)
set sa3.date = datetime()
set sa3.author_id = "unknown-user"
MERGE (sr)-[:AUDIT_TRAIL]->(sa3)
// Set counter for study arm UID 
MERGE (:Counter:StudyArmCounter {count: 3, counterId:'StudyArmCounter3'})

WITH sv
MATCH (termroot:CTTermRoot {uid:"term_root_final"})
MATCH (sar:StudyArm {uid:"StudyArm_000003"})
CREATE (sar)-[:HAS_ARM_TYPE]->(termroot)

"""

STARTUP_PROJECTS_CYPHER = """
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"

CREATE (p1:Project)
SET p1.name = "Project 1",
    p1.description = "Description 1",
    p1.project_number = "PRJ-001",
    p1.uid = "project_uid1"
CREATE (c)-[:HOLDS_PROJECT]->(p1)

CREATE (p2:Project)
SET p2.name = "Project 2",
    p2.description = "Description 2",
    p2.project_number = "PRJ-002",
    p2.uid = "project_uid2"
CREATE (c)-[:HOLDS_PROJECT]->(p2)
"""


def get_path(path):
    if "{uid}" in path:
        path.replace("{uid}", "1234")
    return path


def is_specific(path):
    # return "_uid}" in path
    if any(
        x in path
        for x in ("_uid}", "{serial_number}", "{catalogue_name}", "{study_number}")
    ):
        return True
    return False


def create_stub(path, methods):
    if is_specific(path):
        path = re.sub(r"{[^}]+_uid}", "1", path)
        path = path.replace("{catalogue_name}", "1")
        path = path.replace("{study_number}", "1")
        retval = {
            "id": 1,
            "path_spec": path,
            "path_ready": path,
            "is_specific": True,
            "methods": methods,
        }
    else:
        retval = {"path_ready": path, "is_specific": False, "methods": methods}
    prefix = path.split("/")[1]
    retval["data"] = DATA_MAP.get(prefix, {})
    return retval


def create_paths():
    from clinical_mdr_api.main import app

    return _create_paths(app)


def _create_paths(app: FastAPI, path_prefix="") -> list[dict[str, any]]:
    paths = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            path = create_stub(path_prefix + route.path, route.methods)
            paths.append(path)
        elif isinstance(route, Mount):
            paths += _create_paths(route.app, route.path)
    return paths


def inject_base_data(inject_unit_subset: bool = True) -> Study:
    """
    The data included as generic base data is the following
    - names specified below
    * Clinical Programme - ClinicalProgramme
    * Project - Project
    * Study - study_root
    * Libraries :
        * CDISC - non editable
        * Sponsor - editable
        * SNOMED - editable
    * Catalogues :
        * SDTM CT
        * ADAM CT
    # Codelists
        * Those defined in CT_CODELIST_NAMES/CT_CODELIST_UIDS constants

    Returns created Study object
    """

    # Inject generic base data
    TestUtils.create_dummy_user()

    ## Parent objects for study
    clinical_programme = TestUtils.create_clinical_programme(name="CP")
    project = TestUtils.create_project(
        name="Project ABC",
        project_number="123",
        description="Base project",
        clinical_programme_uid=clinical_programme.uid,
    )

    ## Libraries
    TestUtils.create_library(config.CDISC_LIBRARY_NAME, True)
    TestUtils.create_library("Sponsor", True)
    TestUtils.create_library("SNOMED", True)
    TestUtils.create_library(name=config.REQUESTED_LIBRARY_NAME, is_editable=True)
    TestUtils.create_ct_catalogue(
        library=config.CDISC_LIBRARY_NAME, catalogue_name=config.SDTM_CT_CATALOGUE_NAME
    )
    TestUtils.create_ct_catalogue(
        library=config.CDISC_LIBRARY_NAME, catalogue_name=config.ADAM_CT_CATALOGUE_NAME
    )
    unit_subsets = []
    if inject_unit_subset:
        unit_subset_codelist = TestUtils.create_ct_codelist(
            name="Unit Subset",
            sponsor_preferred_name="unit subset",
            extensible=True,
            approve=True,
        )
        unit_subset_term = TestUtils.create_ct_term(
            codelist_uid=unit_subset_codelist.codelist_uid,
            sponsor_preferred_name_sentence_case="study time",
            sponsor_preferred_name="Study Time",
        )
        unit_subsets.append(unit_subset_term.term_uid)

    ## Unit Definitions
    TestUtils.create_unit_definition(
        name=config.DAY_UNIT_NAME,
        convertible_unit=True,
        display_unit=True,
        master_unit=False,
        si_unit=True,
        us_conventional_unit=True,
        conversion_factor_to_master=config.DAY_UNIT_CONVERSION_FACTOR_TO_MASTER,
        unit_subsets=unit_subsets,
    )
    TestUtils.create_unit_definition(
        name=config.DAYS_UNIT_NAME,
        convertible_unit=True,
        display_unit=True,
        master_unit=False,
        si_unit=True,
        us_conventional_unit=True,
        conversion_factor_to_master=config.DAY_UNIT_CONVERSION_FACTOR_TO_MASTER,
        unit_subsets=unit_subsets,
    )
    TestUtils.create_unit_definition(
        name=config.WEEK_UNIT_NAME,
        convertible_unit=True,
        display_unit=True,
        master_unit=False,
        si_unit=True,
        us_conventional_unit=True,
        conversion_factor_to_master=config.WEEK_UNIT_CONVERSION_FACTOR_TO_MASTER,
        unit_subsets=unit_subsets,
    )

    ## Codelists
    TestUtils.create_ct_codelists_using_cypher()

    ## Study snapshot definition
    ## It needs CDISC Library and SDTM CT catalogue
    TestUtils.create_study_fields_configuration()

    ## Study
    study = TestUtils.create_study("123", "study_root", project.project_number)

    TestUtils.set_study_standard_version(
        study_uid=study.uid, catalogue=config.SDTM_CT_CATALOGUE_NAME
    )

    return study


def fix_study_preferred_time_unit(study_uid):
    """Fix up Cypher-injected study to have a preferred time unit for the protocol SOA which is mandatory for locking"""

    unit_definition_service = UnitDefinitionService(meta_repository=MetaRepository())

    unit_definitions = {
        u.name: u
        for u in unit_definition_service.get_all(library_name=LIBRARY_NAME).items
    }
    if unit_definition := unit_definitions.get(config.DAY_UNIT_NAME):
        if unit_definition.status in {
            LibraryItemStatus.DRAFT,
            LibraryItemStatus.RETIRED,
        }:
            unit_definition_service.approve(unit_definition.uid)

    else:
        codelists = (
            CTCodelistService()
            .get_all_codelists(
                filter_by={"codelist_name_value.name": {"v": ["Unit Subset"]}}
            )
            .items
        )
        if codelists:
            unit_subset_codelist = codelists[0]
        else:
            unit_subset_codelist = TestUtils.create_ct_codelist(
                name="Unit Subset",
                sponsor_preferred_name="unit subset",
                extensible=True,
                approve=True,
            )

        if (
            terms := CTTermService()
            .get_all_terms(
                codelist_name=None,
                codelist_uid=None,
                library=unit_subset_codelist.library_name,
                package=None,
                filter_by={"name.sponsor_preferred_name": {"v": ["Study Time"]}},
            )
            .items
        ):
            unit_subset_term = terms[0]
        else:
            unit_subset_term = TestUtils.create_ct_term(
                codelist_uid=unit_subset_codelist.codelist_uid,
                sponsor_preferred_name_sentence_case="study time",
                sponsor_preferred_name="Study Time",
            )

        unit_definition = TestUtils.create_unit_definition(
            name=config.DAY_UNIT_NAME,
            convertible_unit=True,
            display_unit=True,
            master_unit=False,
            si_unit=True,
            us_conventional_unit=True,
            conversion_factor_to_master=config.DAY_UNIT_CONVERSION_FACTOR_TO_MASTER,
            unit_subsets=[unit_subset_term.term_uid],
        )
        TestUtils.create_unit_definition(
            name=config.WEEK_UNIT_NAME,
            convertible_unit=True,
            display_unit=True,
            master_unit=False,
            si_unit=True,
            us_conventional_unit=True,
            conversion_factor_to_master=config.WEEK_UNIT_CONVERSION_FACTOR_TO_MASTER,
            unit_subsets=[unit_subset_term.term_uid],
        )

    TestUtils.post_study_preferred_time_unit(
        study_uid,
        unit_definition_uid=unit_definition.uid,
        for_protocol_soa=True,
    )
