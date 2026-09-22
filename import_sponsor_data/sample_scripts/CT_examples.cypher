

// SCript to produce the CodeList List based on the schema dated 2021-02-09 in 2020-06626
MATCH (a:Library)-[r1:HAS_MODEL]->(b:CTModel {name:'SDTM'})-[r2:HAS_PACKAGE]->(c:CTPackage {id:'sdtmct-2020-06-26'})-[r3:VALID_IN_PACKAGE]->(d:CTCodeListVersion)-[r4:FOR]->(e:CTCodeListValue)
MATCH (d)-[r5:HAS]->(f:CTCodeListRoot)-[r6:HAS_LABEL]->(g:CTCodeListLabel)
MATCH (d)-[r7:HAS_VERSION]->(h:CTTermVersion)-[r8:HAS]->(i:CTTermRoot)-[r9:HAS_VALUE]->(j:CTTermValue)
RETURN DISTINCT b.name AS Model, c.effectiveDate AS PackageVersion, e.conceptId AS ID, g.name AS Label, e.submissionValue AS Code, a.name AS Library, e.definition AS Definition, e.extensible AS Extensible

// Script that return the CodeList and the Terms for the SEX CodeList in 2020-06-26
MATCH (a:Library)-[r1:HAS_MODEL]->(b:CTModel {name:'SDTM'})-[r2:HAS_PACKAGE]->(c:CTPackage {id:'sdtmct-2020-06-26'})-[r3:VALID_IN_PACKAGE]->(d:CTCodeListVersion {id:'C66731-SDTM-2020-06-26'})-[r4:FOR]->(e:CTCodeListValue)
MATCH (d)-[r5:HAS]->(f:CTCodeListRoot)-[r6:HAS_LABEL]->(g:CTCodeListLabel)
MATCH (d)-[r7:HAS_VERSION]->(h:CTTermVersion)-[r8:HAS]->(i:CTTermRoot)-[r9:HAS_VALUE]->(j:CTTermValue)
RETURN a, b, c, d, e, f, g, h, i, j

// Script to get every Terms for the "ROUTE" Codelist as a Table
MATCH (a:Library)-[r1:HAS_MODEL]->(b:CTModel {name:'SDTM'})-[r2:HAS_PACKAGE]->(c:CTPackage {id:'sdtmct-2020-06-26'})-[r3:VALID_IN_PACKAGE]->(d:CTCodeListVersion {id:'C66729-SDTM-2020-06-26'})-[r4:FOR]->(e:CTCodeListValue)
MATCH (d)-[r5:HAS]->(f:CTCodeListRoot)-[r6:HAS_LABEL]->(g:CTCodeListLabel)
MATCH (d)-[r7:HAS_VERSION]->(h:CTTermVersion)-[r8:HAS]->(i:CTTermRoot)-[r9:HAS_VALUE]->(j:CTTermValue)
RETURN DISTINCT a.name As Library, b.name AS Model,e.submissionValue AS CD_LIST_ID, j.submissionValue AS CD_VAL, j.name AS CD_VAL_LIB, toLower(j.name) AS CD_VAL_LB_LC, j.conceptId AS CD_VAL_SHORT

// Script to get every Terms for the "ROUTE" CodeList as a Table, with the CodeListName and the TermName
// **********************TO DO : Update the Label to Name***********************************************
MATCH (a:Library)-[r1:HAS_MODEL]->(b:CTModel {name:'SDTM'})-[r2:HAS_PACKAGE]->(c:CTPackage {id:'sdtmct-2020-06-26'})-[r3:VALID_IN_PACKAGE]->(d:CTCodeListVersion {id:'C66729-SDTM-2020-06-26'})-[r4:FOR]->(e:CTCodeListValue)
MATCH (d)-[r5:HAS]->(f:CTCodeListRoot)-[r6:HAS_LABEL]->(g:CTCodeListLabel)
MATCH (d)-[r7:HAS_VERSION]->(h:CTTermVersion)-[r8:HAS]->(i:CTTermRoot)-[r9:HAS_VALUE]->(j:CTTermValue)
RETURN DISTINCT a.name As Library, b.name AS Model,e.submissionValue AS CD_LIST_ID, e.conceptId AS CodeListConceptId, j.submissionValue AS CD_VAL, j.name AS CD_VAL_LIB, toLower(j.name) AS CD_VAL_LB_LC, j.conceptId AS CD_VAL_SHORT, g.name AS CodeListName, j.name AS TermName


MATCH (n1:CTCodelistRoot)
MATCH (n1)-[r1]->(n2:CTCodelistNameRoot)-[r2]->(n3:CTCodelistNameValue)
MATCH (n1)-[r3]->(n4:CTCodelistAttributesRoot)-[r4]->(n5:CTCodelistAttributesValue)
MATCH (n1)-[r5]->(n6:CTTermRoot)
MATCH (n6)-[r6]->(n7:CTTermNameRoot)-[r7]->(n8:CTTermNameValue)
MATCH (n6)-[r8]->(n9:CTTermAttributesRoot)-[r9]->(n10:CTTermAttributesValue)
WITH n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, r1, r2, r3, r4, r5, r6, r7, r8, r9, COUNT(n10) AS Count
//WHERE Count > 1
RETURN n1, n2, n3, n4, n5, n6, n7, n8, n9, n10 LIMIT 800;

// Find Terms with multi code lists
MATCH (n1:CTCodelistRoot)-[r1:HAS_TERM]->(n2:CTTermRoot)
WITH n2,COUNT(r1) AS TermCount
WHERE TermCount >= 4
MATCH (n2)<-[:HAS_TERM]-(n1:CTCodelistRoot)
RETURN n2,
    COLLECT(n1) AS Codelist
    ORDER BY size(Codelist) DESC;