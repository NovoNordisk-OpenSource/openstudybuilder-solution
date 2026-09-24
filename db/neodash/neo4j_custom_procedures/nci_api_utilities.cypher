CALL apoc.custom.declareProcedure('nci_get_concept_code_from_term(term::STRING) :: (code::STRING)','with $term as term
with apoc.text.replace(term," ","%20") as term
CALL apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search?fromRecord=0&include=minimal&pageSize=10&term="+term+"&type=match&value=term")YIELD value
return value.concepts[0].code as code')

CALL apoc.custom.declareProcedure('get_parent_concept_code(ccode::STRING) :: (code::STRING)','CALL apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+$ccode+"/parents") YIELD value With collect(value) as values return values[0].code as code')

CALL apoc.custom.declareProcedure('get_nci_concept_definition(ccode::STRING) :: (conceptDefinition::STRING)','
 CALL apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+$ccode+"?include=definitions") YIELD value WITH value, [def IN value.definitions where def.source="NCI"] as def return def[0]["definition"] as conceptDefinition')

CALL apoc.custom.declareProcedure('get_nci_concept_synonyms(ccode::STRING) :: (conceptSynonyms::STRING)','
 CALL apoc.load.json("https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/"+$ccode+"?include=synonyms") YIELD value WITH value, [sym IN value.synonyms where sym.source="NCI"] as sym return sym[0]["name"] as conceptSynonyms')
