# Test data for correction 019: Remove Veeva-imported codelists and terms
#
# Scenarios:
# A: Veeva codelist with 2 Veeva-only terms — full deletion
# B: Veeva codelist with mixed terms (Veeva + CDISC) — unlink CDISC term, delete codelist + Veeva term
# C: Non-Veeva codelist with non-Veeva terms — completely untouched
# D: Veeva term with CTTermContext reference (protected) — term preserved
# E: Veeva term with orphaned CTTermContext (no incoming rels) — term and context deleted
# F: Veeva codelist containing protected term D — codelist preserved

TEST_DATA_REMOVE_VEEVA_IMPORTS = """
CREATE (sponsor_lib:Library {name: 'Sponsor', is_editable: true, uid: 'library_sponsor'});
CREATE (cdisc_lib:Library {name: 'CDISC', is_editable: false, uid: 'library_cdisc'});
CREATE (catalogue:CTCatalogue {name: 'SDTM CT', uid: 'CTCatalogue_000001'});

CREATE (clr_a:CTCodelistRoot {uid: 'CTCodelistRoot_veeva_a'})
CREATE (clnr_a:CTCodelistNameRoot {uid: 'CTCodelistNameRoot_veeva_a'})
CREATE (clnv_a:CTCodelistNameValue {name: 'Veeva Codelist A', uid: 'CTCodelistNameValue_veeva_a'})
CREATE (clar_a:CTCodelistAttributesRoot {uid: 'CTCodelistAttributesRoot_veeva_a'})
CREATE (clav_a:CTCodelistAttributesValue {definition: 'Created by Veeva Library Importer', uid: 'CTCodelistAttributesValue_veeva_a'})
CREATE (clr_a)-[:HAS_NAME_ROOT]->(clnr_a)
CREATE (clnr_a)-[:HAS_VERSION]->(clnv_a)
CREATE (clnr_a)-[:LATEST]->(clnv_a)
CREATE (clnr_a)-[:LATEST_FINAL]->(clnv_a)
CREATE (clr_a)-[:HAS_ATTRIBUTES_ROOT]->(clar_a)
CREATE (clar_a)-[:HAS_VERSION]->(clav_a)
CREATE (clar_a)-[:LATEST]->(clav_a)
CREATE (clar_a)-[:LATEST_FINAL]->(clav_a);

MATCH (catalogue:CTCatalogue {uid: 'CTCatalogue_000001'})
MATCH (clr_a:CTCodelistRoot {uid: 'CTCodelistRoot_veeva_a'})
MATCH (sponsor_lib:Library {uid: 'library_sponsor'})
CREATE (catalogue)-[:HAS_CODELIST]->(clr_a)
CREATE (sponsor_lib)-[:CONTAINS_CODELIST]->(clr_a);

CREATE (tr_a1:CTTermRoot {uid: 'CTTermRoot_veeva_a1'})
CREATE (tnr_a1:CTTermNameRoot {uid: 'CTTermNameRoot_veeva_a1'})
CREATE (tnv_a1:CTTermNameValue {name: 'Veeva Term A1', uid: 'CTTermNameValue_veeva_a1'})
CREATE (tar_a1:CTTermAttributesRoot {uid: 'CTTermAttributesRoot_veeva_a1'})
CREATE (tav_a1:CTTermAttributesValue {definition: 'Created by Veeva Library Importer', uid: 'CTTermAttributesValue_veeva_a1'})
CREATE (tr_a1)-[:HAS_NAME_ROOT]->(tnr_a1)
CREATE (tnr_a1)-[:HAS_VERSION]->(tnv_a1)
CREATE (tnr_a1)-[:LATEST]->(tnv_a1)
CREATE (tnr_a1)-[:LATEST_FINAL]->(tnv_a1)
CREATE (tr_a1)-[:HAS_ATTRIBUTES_ROOT]->(tar_a1)
CREATE (tar_a1)-[:HAS_VERSION]->(tav_a1)
CREATE (tar_a1)-[:LATEST]->(tav_a1)
CREATE (tar_a1)-[:LATEST_FINAL]->(tav_a1);

MATCH (sponsor_lib:Library {uid: 'library_sponsor'})
MATCH (tr_a1:CTTermRoot {uid: 'CTTermRoot_veeva_a1'})
CREATE (sponsor_lib)-[:CONTAINS_TERM]->(tr_a1);

MATCH (clr_a:CTCodelistRoot {uid: 'CTCodelistRoot_veeva_a'})
MATCH (tr_a1:CTTermRoot {uid: 'CTTermRoot_veeva_a1'})
CREATE (clt_a1:CTCodelistTerm {uid: 'CTCodelistTerm_veeva_a1'})
CREATE (clr_a)-[:HAS_TERM]->(clt_a1)
CREATE (clt_a1)-[:HAS_TERM_ROOT]->(tr_a1);

CREATE (tr_a2:CTTermRoot {uid: 'CTTermRoot_veeva_a2'})
CREATE (tnr_a2:CTTermNameRoot {uid: 'CTTermNameRoot_veeva_a2'})
CREATE (tnv_a2:CTTermNameValue {name: 'Veeva Term A2', uid: 'CTTermNameValue_veeva_a2'})
CREATE (tar_a2:CTTermAttributesRoot {uid: 'CTTermAttributesRoot_veeva_a2'})
CREATE (tav_a2:CTTermAttributesValue {definition: 'Created by Veeva Library Importer', uid: 'CTTermAttributesValue_veeva_a2'})
CREATE (tr_a2)-[:HAS_NAME_ROOT]->(tnr_a2)
CREATE (tnr_a2)-[:HAS_VERSION]->(tnv_a2)
CREATE (tnr_a2)-[:LATEST]->(tnv_a2)
CREATE (tnr_a2)-[:LATEST_FINAL]->(tnv_a2)
CREATE (tr_a2)-[:HAS_ATTRIBUTES_ROOT]->(tar_a2)
CREATE (tar_a2)-[:HAS_VERSION]->(tav_a2)
CREATE (tar_a2)-[:LATEST]->(tav_a2)
CREATE (tar_a2)-[:LATEST_FINAL]->(tav_a2);

MATCH (sponsor_lib:Library {uid: 'library_sponsor'})
MATCH (tr_a2:CTTermRoot {uid: 'CTTermRoot_veeva_a2'})
CREATE (sponsor_lib)-[:CONTAINS_TERM]->(tr_a2);

MATCH (clr_a:CTCodelistRoot {uid: 'CTCodelistRoot_veeva_a'})
MATCH (tr_a2:CTTermRoot {uid: 'CTTermRoot_veeva_a2'})
CREATE (clt_a2:CTCodelistTerm {uid: 'CTCodelistTerm_veeva_a2'})
CREATE (clr_a)-[:HAS_TERM]->(clt_a2)
CREATE (clt_a2)-[:HAS_TERM_ROOT]->(tr_a2);

CREATE (clr_b:CTCodelistRoot {uid: 'CTCodelistRoot_veeva_b'})
CREATE (clnr_b:CTCodelistNameRoot {uid: 'CTCodelistNameRoot_veeva_b'})
CREATE (clnv_b:CTCodelistNameValue {name: 'Veeva Codelist B', uid: 'CTCodelistNameValue_veeva_b'})
CREATE (clar_b:CTCodelistAttributesRoot {uid: 'CTCodelistAttributesRoot_veeva_b'})
CREATE (clav_b:CTCodelistAttributesValue {definition: 'Created by Library Importer', uid: 'CTCodelistAttributesValue_veeva_b'})
CREATE (clr_b)-[:HAS_NAME_ROOT]->(clnr_b)
CREATE (clnr_b)-[:HAS_VERSION]->(clnv_b)
CREATE (clnr_b)-[:LATEST]->(clnv_b)
CREATE (clnr_b)-[:LATEST_FINAL]->(clnv_b)
CREATE (clr_b)-[:HAS_ATTRIBUTES_ROOT]->(clar_b)
CREATE (clar_b)-[:HAS_VERSION]->(clav_b)
CREATE (clar_b)-[:LATEST]->(clav_b)
CREATE (clar_b)-[:LATEST_FINAL]->(clav_b);

MATCH (catalogue:CTCatalogue {uid: 'CTCatalogue_000001'})
MATCH (clr_b:CTCodelistRoot {uid: 'CTCodelistRoot_veeva_b'})
MATCH (sponsor_lib:Library {uid: 'library_sponsor'})
CREATE (catalogue)-[:HAS_CODELIST]->(clr_b)
CREATE (sponsor_lib)-[:CONTAINS_CODELIST]->(clr_b);

CREATE (tr_b1:CTTermRoot {uid: 'CTTermRoot_veeva_b1'})
CREATE (tnr_b1:CTTermNameRoot {uid: 'CTTermNameRoot_veeva_b1'})
CREATE (tnv_b1:CTTermNameValue {name: 'Veeva Term B1', uid: 'CTTermNameValue_veeva_b1'})
CREATE (tar_b1:CTTermAttributesRoot {uid: 'CTTermAttributesRoot_veeva_b1'})
CREATE (tav_b1:CTTermAttributesValue {definition: 'Created by Library Importer', uid: 'CTTermAttributesValue_veeva_b1'})
CREATE (tr_b1)-[:HAS_NAME_ROOT]->(tnr_b1)
CREATE (tnr_b1)-[:HAS_VERSION]->(tnv_b1)
CREATE (tnr_b1)-[:LATEST]->(tnv_b1)
CREATE (tnr_b1)-[:LATEST_FINAL]->(tnv_b1)
CREATE (tr_b1)-[:HAS_ATTRIBUTES_ROOT]->(tar_b1)
CREATE (tar_b1)-[:HAS_VERSION]->(tav_b1)
CREATE (tar_b1)-[:LATEST]->(tav_b1)
CREATE (tar_b1)-[:LATEST_FINAL]->(tav_b1);

MATCH (sponsor_lib:Library {uid: 'library_sponsor'})
MATCH (tr_b1:CTTermRoot {uid: 'CTTermRoot_veeva_b1'})
CREATE (sponsor_lib)-[:CONTAINS_TERM]->(tr_b1);

MATCH (clr_b:CTCodelistRoot {uid: 'CTCodelistRoot_veeva_b'})
MATCH (tr_b1:CTTermRoot {uid: 'CTTermRoot_veeva_b1'})
CREATE (clt_b1:CTCodelistTerm {uid: 'CTCodelistTerm_veeva_b1'})
CREATE (clr_b)-[:HAS_TERM]->(clt_b1)
CREATE (clt_b1)-[:HAS_TERM_ROOT]->(tr_b1);

CREATE (tr_cdisc:CTTermRoot {uid: 'CTTermRoot_cdisc_in_veeva'})
CREATE (tnr_cdisc:CTTermNameRoot {uid: 'CTTermNameRoot_cdisc_in_veeva'})
CREATE (tnv_cdisc:CTTermNameValue {name: 'CDISC Term In Veeva Codelist', uid: 'CTTermNameValue_cdisc_in_veeva'})
CREATE (tar_cdisc:CTTermAttributesRoot {uid: 'CTTermAttributesRoot_cdisc_in_veeva'})
CREATE (tav_cdisc:CTTermAttributesValue {definition: 'CDISC definition', uid: 'CTTermAttributesValue_cdisc_in_veeva'})
CREATE (tr_cdisc)-[:HAS_NAME_ROOT]->(tnr_cdisc)
CREATE (tnr_cdisc)-[:HAS_VERSION]->(tnv_cdisc)
CREATE (tnr_cdisc)-[:LATEST]->(tnv_cdisc)
CREATE (tnr_cdisc)-[:LATEST_FINAL]->(tnv_cdisc)
CREATE (tr_cdisc)-[:HAS_ATTRIBUTES_ROOT]->(tar_cdisc)
CREATE (tar_cdisc)-[:HAS_VERSION]->(tav_cdisc)
CREATE (tar_cdisc)-[:LATEST]->(tav_cdisc)
CREATE (tar_cdisc)-[:LATEST_FINAL]->(tav_cdisc);

MATCH (cdisc_lib:Library {uid: 'library_cdisc'})
MATCH (tr_cdisc:CTTermRoot {uid: 'CTTermRoot_cdisc_in_veeva'})
CREATE (cdisc_lib)-[:CONTAINS_TERM]->(tr_cdisc);

MATCH (clr_b:CTCodelistRoot {uid: 'CTCodelistRoot_veeva_b'})
MATCH (tr_cdisc:CTTermRoot {uid: 'CTTermRoot_cdisc_in_veeva'})
CREATE (clt_cdisc:CTCodelistTerm {uid: 'CTCodelistTerm_cdisc_in_veeva'})
CREATE (clr_b)-[:HAS_TERM]->(clt_cdisc)
CREATE (clt_cdisc)-[:HAS_TERM_ROOT]->(tr_cdisc);

CREATE (clr_c:CTCodelistRoot {uid: 'CTCodelistRoot_cdisc_c'})
CREATE (clnr_c:CTCodelistNameRoot {uid: 'CTCodelistNameRoot_cdisc_c'})
CREATE (clnv_c:CTCodelistNameValue {name: 'CDISC Codelist C', uid: 'CTCodelistNameValue_cdisc_c'})
CREATE (clar_c:CTCodelistAttributesRoot {uid: 'CTCodelistAttributesRoot_cdisc_c'})
CREATE (clav_c:CTCodelistAttributesValue {definition: 'CDISC definition', uid: 'CTCodelistAttributesValue_cdisc_c'})
CREATE (clr_c)-[:HAS_NAME_ROOT]->(clnr_c)
CREATE (clnr_c)-[:HAS_VERSION]->(clnv_c)
CREATE (clnr_c)-[:LATEST]->(clnv_c)
CREATE (clnr_c)-[:LATEST_FINAL]->(clnv_c)
CREATE (clr_c)-[:HAS_ATTRIBUTES_ROOT]->(clar_c)
CREATE (clar_c)-[:HAS_VERSION]->(clav_c)
CREATE (clar_c)-[:LATEST]->(clav_c)
CREATE (clar_c)-[:LATEST_FINAL]->(clav_c);

MATCH (catalogue:CTCatalogue {uid: 'CTCatalogue_000001'})
MATCH (clr_c:CTCodelistRoot {uid: 'CTCodelistRoot_cdisc_c'})
MATCH (cdisc_lib:Library {uid: 'library_cdisc'})
CREATE (catalogue)-[:HAS_CODELIST]->(clr_c)
CREATE (cdisc_lib)-[:CONTAINS_CODELIST]->(clr_c);

CREATE (tr_c1:CTTermRoot {uid: 'CTTermRoot_cdisc_c1'})
CREATE (tnr_c1:CTTermNameRoot {uid: 'CTTermNameRoot_cdisc_c1'})
CREATE (tnv_c1:CTTermNameValue {name: 'CDISC Term C1', uid: 'CTTermNameValue_cdisc_c1'})
CREATE (tar_c1:CTTermAttributesRoot {uid: 'CTTermAttributesRoot_cdisc_c1'})
CREATE (tav_c1:CTTermAttributesValue {definition: 'CDISC definition', uid: 'CTTermAttributesValue_cdisc_c1'})
CREATE (tr_c1)-[:HAS_NAME_ROOT]->(tnr_c1)
CREATE (tnr_c1)-[:HAS_VERSION]->(tnv_c1)
CREATE (tnr_c1)-[:LATEST]->(tnv_c1)
CREATE (tnr_c1)-[:LATEST_FINAL]->(tnv_c1)
CREATE (tr_c1)-[:HAS_ATTRIBUTES_ROOT]->(tar_c1)
CREATE (tar_c1)-[:HAS_VERSION]->(tav_c1)
CREATE (tar_c1)-[:LATEST]->(tav_c1)
CREATE (tar_c1)-[:LATEST_FINAL]->(tav_c1);

MATCH (cdisc_lib:Library {uid: 'library_cdisc'})
MATCH (tr_c1:CTTermRoot {uid: 'CTTermRoot_cdisc_c1'})
CREATE (cdisc_lib)-[:CONTAINS_TERM]->(tr_c1);

MATCH (clr_c:CTCodelistRoot {uid: 'CTCodelistRoot_cdisc_c'})
MATCH (tr_c1:CTTermRoot {uid: 'CTTermRoot_cdisc_c1'})
CREATE (clt_c1:CTCodelistTerm {uid: 'CTCodelistTerm_cdisc_c1'})
CREATE (clr_c)-[:HAS_TERM]->(clt_c1)
CREATE (clt_c1)-[:HAS_TERM_ROOT]->(tr_c1);

CREATE (tr_d:CTTermRoot {uid: 'CTTermRoot_veeva_protected_d'})
CREATE (tnr_d:CTTermNameRoot {uid: 'CTTermNameRoot_veeva_protected_d'})
CREATE (tnv_d:CTTermNameValue {name: '/10^9', uid: 'CTTermNameValue_veeva_protected_d'})
CREATE (tar_d:CTTermAttributesRoot {uid: 'CTTermAttributesRoot_veeva_protected_d'})
CREATE (tav_d:CTTermAttributesValue {definition: 'Created by Veeva Library Importer', uid: 'CTTermAttributesValue_veeva_protected_d'})
CREATE (tr_d)-[:HAS_NAME_ROOT]->(tnr_d)
CREATE (tnr_d)-[:HAS_VERSION]->(tnv_d)
CREATE (tnr_d)-[:LATEST]->(tnv_d)
CREATE (tnr_d)-[:LATEST_FINAL]->(tnv_d)
CREATE (tr_d)-[:HAS_ATTRIBUTES_ROOT]->(tar_d)
CREATE (tar_d)-[:HAS_VERSION]->(tav_d)
CREATE (tar_d)-[:LATEST]->(tav_d)
CREATE (tar_d)-[:LATEST_FINAL]->(tav_d);

MATCH (sponsor_lib:Library {uid: 'library_sponsor'})
MATCH (tr_d:CTTermRoot {uid: 'CTTermRoot_veeva_protected_d'})
CREATE (sponsor_lib)-[:CONTAINS_TERM]->(tr_d);

MATCH (tr_d:CTTermRoot {uid: 'CTTermRoot_veeva_protected_d'})
CREATE (ctx_d:CTTermContext {uid: 'CTTermContext_unit_d'})
CREATE (udv_d:UnitDefinitionValue {uid: 'UnitDefinitionValue_d', name: '/10^9'})
CREATE (udr_d:UnitDefinitionRoot {uid: 'UnitDefinitionRoot_d'})
CREATE (udr_d)-[:HAS_VERSION]->(udv_d)
CREATE (udr_d)-[:LATEST]->(udv_d)
CREATE (udr_d)-[:LATEST_FINAL]->(udv_d)
CREATE (udv_d)-[:HAS_CT_UNIT]->(ctx_d)
CREATE (ctx_d)-[:HAS_SELECTED_TERM]->(tr_d);

MATCH (clr_c:CTCodelistRoot {uid: 'CTCodelistRoot_cdisc_c'})
MATCH (tr_d:CTTermRoot {uid: 'CTTermRoot_veeva_protected_d'})
CREATE (clt_d:CTCodelistTerm {uid: 'CTCodelistTerm_veeva_d_in_cdisc'})
CREATE (clr_c)-[:HAS_TERM]->(clt_d)
CREATE (clt_d)-[:HAS_TERM_ROOT]->(tr_d);

CREATE (tr_e:CTTermRoot {uid: 'CTTermRoot_veeva_orphaned_e'})
CREATE (tnr_e:CTTermNameRoot {uid: 'CTTermNameRoot_veeva_orphaned_e'})
CREATE (tnv_e:CTTermNameValue {name: 'Veeva Term E Orphaned', uid: 'CTTermNameValue_veeva_orphaned_e'})
CREATE (tar_e:CTTermAttributesRoot {uid: 'CTTermAttributesRoot_veeva_orphaned_e'})
CREATE (tav_e:CTTermAttributesValue {definition: 'Created by Veeva Library Importer', uid: 'CTTermAttributesValue_veeva_orphaned_e'})
CREATE (tr_e)-[:HAS_NAME_ROOT]->(tnr_e)
CREATE (tnr_e)-[:HAS_VERSION]->(tnv_e)
CREATE (tnr_e)-[:LATEST]->(tnv_e)
CREATE (tnr_e)-[:LATEST_FINAL]->(tnv_e)
CREATE (tr_e)-[:HAS_ATTRIBUTES_ROOT]->(tar_e)
CREATE (tar_e)-[:HAS_VERSION]->(tav_e)
CREATE (tar_e)-[:LATEST]->(tav_e)
CREATE (tar_e)-[:LATEST_FINAL]->(tav_e);

MATCH (sponsor_lib:Library {uid: 'library_sponsor'})
MATCH (tr_e:CTTermRoot {uid: 'CTTermRoot_veeva_orphaned_e'})
CREATE (sponsor_lib)-[:CONTAINS_TERM]->(tr_e);

MATCH (tr_e:CTTermRoot {uid: 'CTTermRoot_veeva_orphaned_e'})
CREATE (ctx_e:CTTermContext {uid: 'CTTermContext_orphaned_e'})
CREATE (ctx_e)-[:HAS_SELECTED_TERM]->(tr_e);

CREATE (clr_f:CTCodelistRoot {uid: 'CTCodelistRoot_veeva_f'})
CREATE (clnr_f:CTCodelistNameRoot {uid: 'CTCodelistNameRoot_veeva_f'})
CREATE (clnv_f:CTCodelistNameValue {name: 'Veeva Codelist F', uid: 'CTCodelistNameValue_veeva_f'})
CREATE (clar_f:CTCodelistAttributesRoot {uid: 'CTCodelistAttributesRoot_veeva_f'})
CREATE (clav_f:CTCodelistAttributesValue {definition: 'Created by Veeva Library Importer', uid: 'CTCodelistAttributesValue_veeva_f'})
CREATE (clr_f)-[:HAS_NAME_ROOT]->(clnr_f)
CREATE (clnr_f)-[:HAS_VERSION]->(clnv_f)
CREATE (clnr_f)-[:LATEST]->(clnv_f)
CREATE (clnr_f)-[:LATEST_FINAL]->(clnv_f)
CREATE (clr_f)-[:HAS_ATTRIBUTES_ROOT]->(clar_f)
CREATE (clar_f)-[:HAS_VERSION]->(clav_f)
CREATE (clar_f)-[:LATEST]->(clav_f)
CREATE (clar_f)-[:LATEST_FINAL]->(clav_f);

MATCH (catalogue:CTCatalogue {uid: 'CTCatalogue_000001'})
MATCH (clr_f:CTCodelistRoot {uid: 'CTCodelistRoot_veeva_f'})
MATCH (sponsor_lib:Library {uid: 'library_sponsor'})
CREATE (catalogue)-[:HAS_CODELIST]->(clr_f)
CREATE (sponsor_lib)-[:CONTAINS_CODELIST]->(clr_f);

MATCH (clr_f:CTCodelistRoot {uid: 'CTCodelistRoot_veeva_f'})
MATCH (tr_d:CTTermRoot {uid: 'CTTermRoot_veeva_protected_d'})
CREATE (clt_f_d:CTCodelistTerm {uid: 'CTCodelistTerm_veeva_f_d'})
CREATE (clr_f)-[:HAS_TERM]->(clt_f_d)
CREATE (clt_f_d)-[:HAS_TERM_ROOT]->(tr_d)
"""
