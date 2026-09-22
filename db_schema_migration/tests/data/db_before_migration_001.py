"""Cypher queries for generating all relevant test data
in the format valid BEFORE the migration is to take place"""

# Activity groups/subgroups test data extracted from VAL by running:
#
# WITH "MATCH (n:ActivitySubGroupValue)-[r:IN_GROUP]->(m:ActivityGroupValue)
#       WITH n, count(m) as nbr_rels, collect(m) as ms, collect(r) as rels
#       WHERE nbr_rels > 1
#       RETURN *
#     " AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll"})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements;
#
# Note: CREATE INDEX statements removed!
TEST_DATA_ACTIVITIES_GROUPS = """
UNWIND [{_id:852485, properties:{name:"General", name_sentence_case:"general", definition:"Definition not provided"}}, {_id:852479, properties:{name:"Laboratory Assessments", name_sentence_case:"laboratory assessments", definition:"Definition not provided"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:TemplateParameterValue:ActivityGroupValue;
UNWIND [{_id:852492, properties:{name:"24 Hour Urine Collection", name_sentence_case:"24 hour urine collection"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:TemplateParameterValue:ActivitySubGroupValue;
UNWIND [{start: {_id:852492}, end: {_id:852479}, properties:{}}, {start: {_id:852492}, end: {_id:852485}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:IN_GROUP]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
"""

# Activities test data extracted from VAL by running:
#
# WITH "(n:ActivityValue)-[r:IN_SUB_GROUP]->(m:ActivitySubGroupValue)
#       WITH n, count(m) as nbr_rels, collect(m) as ms, collect(r) as rels
#       WHERE nbr_rels > 1
#       RETURN * LIMIT 5
#     " AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll"})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatement;
#
# Note: CREATE INDEX statements removed!
TEST_DATA_ACTIVITIES = """
UNWIND [{_id:856625, properties:{name:"Protein", name_sentence_case:"protein"}}, {_id:856627, properties:{name:"Prothrombin Time", name_sentence_case:"prothrombin time"}}, {_id:856885, properties:{name:"Sodium", name_sentence_case:"sodium"}}, {_id:857123, properties:{name:"Leukocytes", name_sentence_case:"leukocytes"}}, {_id:856357, properties:{name:"Potassium", name_sentence_case:"potassium"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:ActivityValue:TemplateParameterValue;
UNWIND [{_id:852538, properties:{name:"Urine Dipstick", name_sentence_case:"urine dipstick"}}, {_id:852606, properties:{name:"Haematology", name_sentence_case:"haematology"}}, {_id:852516, properties:{name:"Laboratory Assessment", name_sentence_case:"laboratory assessment"}}, {_id:852520, properties:{name:"Biochemistry", name_sentence_case:"biochemistry"}}, {_id:852524, properties:{name:"Coagulation Parameters", name_sentence_case:"coagulation parameters"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:TemplateParameterValue:ActivitySubGroupValue;
UNWIND [{start: {_id:856885}, end: {_id:852520}, properties:{}}, {start: {_id:857123}, end: {_id:852606}, properties:{}}, {start: {_id:857123}, end: {_id:852516}, properties:{}}, {start: {_id:857123}, end: {_id:852538}, properties:{}}, {start: {_id:856625}, end: {_id:852520}, properties:{}}, {start: {_id:856627}, end: {_id:852516}, properties:{}}, {start: {_id:856627}, end: {_id:852524}, properties:{}}, {start: {_id:856885}, end: {_id:852516}, properties:{}}, {start: {_id:856357}, end: {_id:852516}, properties:{}}, {start: {_id:856357}, end: {_id:852520}, properties:{}}, {start: {_id:856625}, end: {_id:852516}, properties:{}}, {start: {_id:856625}, end: {_id:852538}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:IN_SUB_GROUP]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
"""


# CTConfig test data extracted from VAL by running:
#
# WITH "MATCH (root:CTConfigRoot)-[r]-(val:CTConfigValue)
#     WHERE val.study_field_name_property CONTAINS 'JapaneseTrialRegistryIdJapic'
#     RETURN *
#     " AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "create"})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements;
#
# Note: CREATE INDEX statements removed!
TEST_DATA_CT_CONFIG = """
CREATE CONSTRAINT ON (node:`UNIQUE IMPORT LABEL`) ASSERT (node.`UNIQUE IMPORT ID`) IS UNIQUE;
UNWIND [{_id:849695, properties:{study_field_grouping:"id_metadata.registry_identifiers", study_field_name_property:"JapaneseTrialRegistryIdJapic", study_field_data_type:"registry", study_field_name:"japanese_trial_registry_id_JAPIC", study_field_name_api:"japaneseTrialRegistryIdJapic", study_field_null_value_code:"japanese_trial_registry_id_JAPIC_null_value_code"}}, {_id:849697, properties:{study_field_grouping:"id_metadata.registry_identifiers", study_field_data_type:"text", study_field_name_property:"JapaneseTrialRegistryIdJapicNullValueCode", study_field_name:"japanese_trial_registry_id_JAPIC_null_value_code", study_field_name_api:"japaneseTrialRegistryIdJapicNullValueCode"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTConfigValue;
UNWIND [{_id:849696, properties:{uid:"CTConfig_000011"}}, {_id:849694, properties:{uid:"CTConfig_000010"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTConfigRoot;
UNWIND [{start: {_id:849696}, end: {_id:849697}, properties:{}}, {start: {_id:849694}, end: {_id:849695}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:849694}, end: {_id:849695}, properties:{change_description:"Initial version", version:"0.1", user_initials:"00000000-0000-0000-0000-000000000001", status:"Draft", start_date:datetime('2022-09-19T20:02:59.749271Z')}}, {start: {_id:849696}, end: {_id:849697}, properties:{change_description:"Initial version", version:"0.1", user_initials:"00000000-0000-0000-0000-000000000001", status:"Draft", start_date:datetime('2022-09-19T20:02:59.873301Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_DRAFT]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
DROP CONSTRAINT ON (node:`UNIQUE IMPORT LABEL`) ASSERT (node.`UNIQUE IMPORT ID`) IS UNIQUE;
"""


# StudyCriteria test data extracted from VAL by running:
#
# WITH "MATCH (n:StudyCriteria)
#     RETURN *
#     LIMIT 3
#     " AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "create"})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements;
TEST_DATA_STUDY_SELECTION = """
CREATE CONSTRAINT ON (node:`UNIQUE IMPORT LABEL`) ASSERT (node.`UNIQUE IMPORT ID`) IS UNIQUE;
UNWIND [{_id:875418, properties:{uid:"StudyCriteria_000002", accepted_version:false, order:1}}, {_id:875424, properties:{uid:"StudyCriteria_000003", accepted_version:false, order:1}}, {_id:865776, properties:{uid:"StudyCriteria_000001", accepted_version:false, order:1}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:StudyCriteria:StudySelection;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
DROP CONSTRAINT ON (node:`UNIQUE IMPORT LABEL`) ASSERT (node.`UNIQUE IMPORT ID`) IS UNIQUE;
"""


# WITH "MATCH (study_root:StudyRoot)-[latest:LATEST]->(study_value:StudyValue)-[has_text_field:HAS_TEXT_FIELD]->(study_field:StudyTextField)
#     WHERE study_field.field_name='RelapseCriteria'
#     RETURN *
#     LIMIT 1" AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "addStructure", ifNotExists: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;
# WITH "MATCH (study_root:StudyRoot)-[latest:LATEST]->(study_value:StudyValue)-[has_project:HAS_PROJECT]->(study_field:StudyProjectField)
#     RETURN *
#     LIMIT 1" AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "addStructure", ifNotExists: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;
# WITH "MATCH (study_root:StudyRoot)-[latest:LATEST]->(study_value:StudyValue)-[has_array_field:HAS_ARRAY_FIELD]->(study_field:StudyArrayField)
#        WHERE study_field.field_name='TherapeuticAreaCodes'
#        UNWIND study_field.value as val
#        MATCH (dictionary_term_root:DictionaryTermRoot {uid:val})-[latest_final:LATEST_FINAL]->(dictionary_term_value)
#         MATCH (term_root_ta:CTTermRoot {uid:'C101302_THERAREA'})-[has_attributes_root_ta:HAS_ATTRIBUTES_ROOT]->(atrtibutes_root_ta)-[latest_final_attributes_ta:LATEST_FINAL]->(attributes_value_ta)
#        RETURN *
#        LIMIT 1" AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "addStructure", ifNotExists: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;
# WITH "
#     MATCH (study_root:StudyRoot)-[latest:LATEST]->(study_value:StudyValue)-[has_boolean_field:HAS_BOOLEAN_FIELD]->(study_field:StudyBooleanField)
#        WHERE study_field.field_name='IsTrialRandomised'
#        WITH *,
#        CASE WHEN study_field.value=true THEN 'C49488_Y' ELSE 'C49487_N' END AS val
#        MATCH (term_root:CTTermRoot {uid:val})-[has_attributes_root:HAS_ATTRIBUTES_ROOT]->(atrtibutes_root:CTTermAttributesRoot)-[latest_final_attributes:LATEST_FINAL]->(attributes_value:CTTermAttributesValue)
#        MATCH (term_root:CTTermRoot)-[has_name_root:HAS_NAME_ROOT]->(name_root:CTTermNameRoot)-[latest_final_name:LATEST_FINAL]->(term_value:CTTermNameValue)
#        MATCH (term_root_itr:CTTermRoot {uid:'C25196_RANDOM'})-[has_attributes_root_itr:HAS_ATTRIBUTES_ROOT]->(atrtibutes_root_itr)-[latest_final_attributes_itr:LATEST_FINAL]->(attributes_value_itr)
#        RETURN *
#        LIMIT 1" AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "addStructure", ifNotExists: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;
# WITH "
#   MATCH (study_root:StudyRoot)-[latest:LATEST]->(study_value:StudyValue)-[has_text_field:HAS_TEXT_FIELD]->(study_field:StudyTextField)
#       WHERE study_field.field_name='ControlTypeCode'
#       UNWIND study_field.value as val
#       MATCH (term_root:CTTermRoot {uid:val})-[has_attributes_root:HAS_ATTRIBUTES_ROOT]->(atrtibutes_root)-[latest_final_attributes:LATEST_FINAL]->(attributes_value)
#       MATCH (term_root)-[has_name_root:HAS_NAME_ROOT]->(name_root)-[latest_final_name:LATEST_FINAL]->(term_value)
#       MATCH (term_root_control:CTTermRoot {uid:'C49647_TCNTRL'})-[has_attributes_root_control:HAS_ATTRIBUTES_ROOT]->(atrtibutes_root_control)-[latest_final_attributes_control:LATEST_FINAL]->(attributes_value_control)
#       RETURN *
#       LIMIT 1" AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "addStructure", ifNotExists: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;
TEST_DATA_STUDY_FIELDS = """
//StudyTextField without relationship to CTTermRoot/DictionaryTermRoot
UNWIND [{_id:875698, properties:{study_id_prefix:"CDISC DEV", study_number:"0"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyValue;
UNWIND [{_id:865060, properties:{uid:"Study_000002"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyRoot;
UNWIND [{_id:875662, properties:{value:"Test relapse criteria", field_name:"RelapseCriteria"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyField:StudyTextField;
UNWIND [{start: {_id:875698}, end: {_id:875662}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_TEXT_FIELD]->(end)  SET r += row.properties;
UNWIND [{start: {_id:865060}, end: {_id:875698}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end)  SET r += row.properties;
// StudyProjectField without relationship to CTTermRoot/DictionaryTermRoot
UNWIND [{_id:875372, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyProjectField:StudyField;
UNWIND [{_id:875370, properties:{study_id_prefix:"REDACTED", study_number:"1374"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyValue;
UNWIND [{_id:865045, properties:{uid:"Study_000001"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyRoot;
UNWIND [{start: {_id:875370}, end: {_id:875372}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_PROJECT]->(end)  SET r += row.properties;
UNWIND [{start: {_id:865045}, end: {_id:875370}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end)  SET r += row.properties;
// StudyArrayField
UNWIND [{_id:185744, properties:{preferred_term:"Therapeutic Area", concept_id:"C101302", synonyms:["Therapeutic Area"], code_submission_value:"THERAREA", definition:"A knowledge field that focuses on research and development of specific treatments for diseases and pathologic findings, as well as prevention of conditions that negatively impact the health of an individual. (NCI)", name_submission_value:"Therapeutic Area"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:CTTermAttributesValue;
UNWIND [{_id:865662, properties:{value:["DictionaryTerm_000015"], field_name:"TherapeuticAreaCodes"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyField:StudyArrayField;
UNWIND [{_id:865606, properties:{study_acronym:"Acronym for the study", study_id_prefix:"CDISC DEV", study_number:"9999"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyValue;
UNWIND [{_id:847776, properties:{name:"Heart failure", name_sentence_case:"heart failure", definition:"Heart failure (disorder)", abbreviation:"HF", dictionary_id:"84114007"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:SnomedTermValue:TemplateParameterValue:DictionaryTermValue;
UNWIND [{_id:179299, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:CTTermAttributesRoot;
UNWIND [{uid:"C101302_THERAREA", properties:{concept_id:"C101302"}}] AS row
MERGE (n:CTTermRoot{uid: row.uid}) ON CREATE SET n += row.properties;
UNWIND [{uid:"DictionaryTerm_000015", properties:{}}] AS row
MERGE (n:TemplateParameterValueRoot{uid: row.uid}) ON CREATE SET n += row.properties SET n:DictionaryTermRoot:SnomedTermRoot;
UNWIND [{_id:865601, properties:{uid:"Study_000035"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyRoot;
UNWIND [{start: {uid:"C101302_THERAREA"}, end: {_id:179299}, properties:{}}] AS row
MATCH (start:CTTermRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_ATTRIBUTES_ROOT]->(end)  SET r += row.properties;
UNWIND [{start: {uid:"DictionaryTerm_000015"}, end: {_id:847776}, properties:{change_description:"Approved version", version:"1.0", user_initials:"00000000-0000-0000-0000-000000000001", status:"Final", start_date:datetime('2022-09-19T19:57:09.546037Z')}}] AS row
MATCH (start:TemplateParameterValueRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end)  SET r += row.properties;
UNWIND [{start: {_id:179299}, end: {_id:185744}, properties:{change_description:"Imported from CDISC", version:"1.0", status:"Final", user_initials:"TESTUSER", start_date:datetime('2016-03-25T00:00:00Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end)  SET r += row.properties;
UNWIND [{start: {_id:865601}, end: {_id:865606}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end)  SET r += row.properties;
UNWIND [{start: {_id:865606}, end: {_id:865662}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_ARRAY_FIELD]->(end)  SET r += row.properties;
// :StudyBooleanField
UNWIND [{_id:55614, properties:{name:"Yes", name_sentence_case:"yes"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:CTTermNameValue;
UNWIND [{_id:55613, properties:{preferred_term:"Yes", concept_id:"C49488", synonyms:["Yes"], code_submission_value:"Y", definition:"The affirmative response to a question. (NCI)"}}, {_id:54571, properties:{preferred_term:"Randomization", concept_id:"C25196", synonyms:["Trial is Randomized"], code_submission_value:"RANDOM", definition:"The process of assigning trial subjects to treatment or control groups using an element of chance to determine the assignments in order to reduce bias. NOTE: Unequal randomization is used to allocate subjects into groups at a differential rate; for example, three subjects may be assigned to a treatment group for every one assigned to the control group. [ICH E6 1.48] See also balanced study. (CDISC glossary)", name_submission_value:"Trial is Randomized"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:CTTermAttributesValue;
UNWIND [{_id:865606, properties:{study_acronym:"Acronym for the study", study_id_prefix:"CDISC DEV", study_number:"9999"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyValue;
UNWIND [{_id:865616, properties:{value:true, field_name:"IsTrialRandomised"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyField:StudyBooleanField;
UNWIND [{_id:19282, properties:{}}, {_id:16710, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:CTTermAttributesRoot;
UNWIND [{uid:"C25196_RANDOM", properties:{concept_id:"C25196"}}, {uid:"C49488_Y", properties:{concept_id:"C49488"}}] AS row
MERGE (n:CTTermRoot{uid: row.uid}) ON CREATE SET n += row.properties;
UNWIND [{_id:19283, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:CTTermNameRoot;
UNWIND [{_id:865601, properties:{uid:"Study_000035"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyRoot;
UNWIND [{start: {uid:"C49488_Y"}, end: {_id:19282}, properties:{}}, {start: {uid:"C25196_RANDOM"}, end: {_id:16710}, properties:{}}] AS row
MATCH (start:CTTermRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_ATTRIBUTES_ROOT]->(end)  SET r += row.properties;
UNWIND [{start: {uid:"C49488_Y"}, end: {_id:19283}, properties:{}}] AS row
MATCH (start:CTTermRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_NAME_ROOT]->(end)  SET r += row.properties;
UNWIND [{start: {_id:19283}, end: {_id:55614}, properties:{change_description:"Initial import from CDISC", version:"1.0", status:"Final", user_initials:"TESTUSER", start_date:datetime('2022-09-19T17:09:02.616Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end)  SET r += row.properties;
UNWIND [{start: {_id:16710}, end: {_id:54571}, properties:{change_description:"Imported from CDISC", version:"1.0", status:"Final", user_initials:"TESTUSER", start_date:datetime('2014-09-26T00:00:00Z')}}, {start: {_id:19282}, end: {_id:55613}, properties:{change_description:"Imported from CDISC", version:"1.0", status:"Final", user_initials:"TESTUSER", start_date:datetime('2014-09-26T00:00:00Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end)  SET r += row.properties;
UNWIND [{start: {_id:865601}, end: {_id:865606}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end)  SET r += row.properties;
UNWIND [{start: {_id:865606}, end: {_id:865616}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_BOOLEAN_FIELD]->(end)  SET r += row.properties;
// :StudyTextField
UNWIND [{_id:59814, properties:{name:"Active", name_sentence_case:"active"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:CTTermNameValue;
UNWIND [{_id:228653, properties:{preferred_term:"Control Type", concept_id:"C49647", synonyms:["Control Type"], code_submission_value:"TCNTRL", definition:"Comparator against which the study treatment is evaluated.", name_submission_value:"Control Type"}}, {_id:673280, properties:{preferred_term:"Active Control", concept_id:"C49649", synonyms:["Active Control"], code_submission_value:"ACTIVE", definition:"A type of control, which has a demonstrated effect, administered as a comparator to subjects in a clinical trial. [From ICH E10]"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:CTTermAttributesValue;
UNWIND [{_id:875698, properties:{study_id_prefix:"CDISC DEV", study_number:"0"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyValue;
UNWIND [{_id:27792, properties:{}}, {_id:16721, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:CTTermAttributesRoot;
UNWIND [{uid:"C49647_TCNTRL", properties:{concept_id:"C49647"}}, {uid:"C49649_ACTIVE", properties:{concept_id:"C49649"}}] AS row
MERGE (n:CTTermRoot{uid: row.uid}) ON CREATE SET n += row.properties;
UNWIND [{_id:27793, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:CTTermNameRoot;
UNWIND [{_id:865060, properties:{uid:"Study_000002"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyRoot;
UNWIND [{_id:875635, properties:{value:"C49649_ACTIVE", field_name:"ControlTypeCode"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) ON CREATE SET n += row.properties SET n:StudyField:StudyTextField;
UNWIND [{start: {uid:"C49649_ACTIVE"}, end: {_id:27792}, properties:{}}, {start: {uid:"C49647_TCNTRL"}, end: {_id:16721}, properties:{}}] AS row
MATCH (start:CTTermRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_ATTRIBUTES_ROOT]->(end)  SET r += row.properties;
UNWIND [{start: {uid:"C49649_ACTIVE"}, end: {_id:27793}, properties:{}}] AS row
MATCH (start:CTTermRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_NAME_ROOT]->(end)  SET r += row.properties;
UNWIND [{start: {_id:27793}, end: {_id:59814}, properties:{change_description:"Initial import from CDISC", version:"1.0", status:"Final", user_initials:"TESTUSER", start_date:datetime('2022-09-19T17:09:32.624Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end)  SET r += row.properties;
UNWIND [{start: {_id:27792}, end: {_id:673280}, properties:{change_description:"Imported from CDISC", version:"2.0", status:"Final", user_initials:"TESTUSER", start_date:datetime('2020-11-06T00:00:00Z')}}, {start: {_id:16721}, end: {_id:228653}, properties:{change_description:"Imported from CDISC", version:"2.0", status:"Final", user_initials:"TESTUSER", start_date:datetime('2016-09-30T00:00:00Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end)  SET r += row.properties;
UNWIND [{start: {_id:865060}, end: {_id:875698}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end)  SET r += row.properties;
UNWIND [{start: {_id:875698}, end: {_id:875635}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_TEXT_FIELD]->(end)  SET r += row.properties;
"""

# CDISC term test data extracted by running:
#
# WITH "
#   MATCH (term_name_value:CTTermNameValue)<-[name_latest:LATEST]-(term_name_root:CTTermNameRoot)<-[has_name_root:HAS_NAME_ROOT]-(term_root:CTTermRoot)-[hasattr:HAS_ATTRIBUTES_ROOT]->(term_attributes_root:CTTermAttributesRoot)-[attr_latest:LATEST]->(term_attributes_value:CTTermAttributesValue)
#   MATCH (codelist_root:CTCodelistRoot)-[has_term:HAS_TERM]->(term_root)
#   MATCH (term_name_value)<-[name_latest_final:LATEST_FINAL]-(term_name_root)
#   MATCH (term_attributes_root)-[attr_latest_final:LATEST_FINAL]->(term_attributes_value)
#   MATCH (term_root)<-[libterm:CONTAINS_TERM]-(library:Library {name: \"CDISC\"})
#   MATCH (codelist_root)-[has_codelist:HAS_CODELIST]-(codelist)
#   WHERE term_root.uid CONTAINS \"mmol/min\"
#   RETURN *
#   LIMIT 10
# " AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll"})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements;
#
# Note:
#  - CREATE INDEX, CREATE CONSTRAINT and DROP CONSTRAINT statements removed!
TEST_DATA_RESERVED_CHARS_IN_UID = """
UNWIND [{_id:62066, properties:{name:"mmol/min/kPa", name_sentence_case:"mmol/min/kpa"}}, {_id:66890, properties:{name:"mmol/min", name_sentence_case:"mmol/min"}}, {_id:61700, properties:{name:"mmol/min/kPa/L", name_sentence_case:"mmol/min/kPa/L"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermNameValue;
UNWIND [{_id:62065, properties:{preferred_term:"Millimoles per Minute per Kilopascal", concept_id:"C116242", code_submission_value:"mmol/min/kPa", definition:"A unit of gas diffusion capacity equal to one millimole per minute per kilopascal."}}, {_id:61699, properties:{preferred_term:"Millimole per Minute per Thousand Pascal per Liter", concept_id:"C67423", code_submission_value:"mmol/min/kPa/L", definition:"A unit of gas diffusion capacity equal to one millimole per minute per kilopascal per liter of volume."}}, {_id:1318238, properties:{preferred_term:"Millimole per Minute", concept_id:"C85722", code_submission_value:"mmol/min", definition:"A unit of substance flow rate equal to one millimole per minute."}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermAttributesValue;
UNWIND [{name:"CDISC", properties:{is_editable:false}}] AS row
MERGE (n:Library{name: row.name}) SET n += row.properties;
UNWIND [{_id:33260, properties:{uid:"C116242_mmol/min/kPa", concept_id:"C116242"}}, {_id:43770, properties:{uid:"C85722_mmol/min", concept_id:"C85722"}}, {_id:32062, properties:{uid:"C67423_mmol/min/kPa/L", concept_id:"C67423"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermRoot;
UNWIND [{_id:33538, properties:{}}, {_id:44029, properties:{}}, {_id:32547, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermAttributesRoot;
UNWIND [{uid:"C71620", properties:{}}, {uid:"C85494", properties:{}}] AS row
MERGE (n:CTCodelistRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{_id:33539, properties:{}}, {_id:44030, properties:{}}, {_id:32548, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermNameRoot;
UNWIND [{name:"SDTM CT", properties:{}}, {name:"SEND CT", properties:{}}] AS row
MERGE (n:CTCatalogue{name: row.name}) SET n += row.properties;
UNWIND [{start: {uid:"C71620"}, end: {_id:32062}, properties:{start_date:datetime('2014-09-26T00:00:00Z'), user_initials:"USR1"}}, {start: {uid:"C71620"}, end: {_id:33260}, properties:{start_date:datetime('2014-09-26T00:00:00Z'), user_initials:"USR1"}}, {start: {uid:"C85494"}, end: {_id:43770}, properties:{start_date:datetime('2014-09-26T00:00:00Z'), user_initials:"USR1"}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {name:"SEND CT"}, end: {uid:"C71620"}, properties:{}}, {start: {name:"SDTM CT"}, end: {uid:"C85494"}, properties:{}}, {start: {name:"SDTM CT"}, end: {uid:"C71620"}, properties:{}}, {start: {name:"SEND CT"}, end: {uid:"C85494"}, properties:{}}] AS row
MATCH (start:CTCatalogue{name: row.start.name})
MATCH (end:CTCodelistRoot{uid: row.end.uid})
MERGE (start)-[r:HAS_CODELIST]->(end) SET r += row.properties;
UNWIND [{start: {_id:32548}, end: {_id:61700}, properties:{}}, {start: {_id:33539}, end: {_id:62066}, properties:{}}, {start: {_id:44030}, end: {_id:66890}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {name:"CDISC"}, end: {_id:32062}, properties:{}}, {start: {name:"CDISC"}, end: {_id:43770}, properties:{}}, {start: {name:"CDISC"}, end: {_id:33260}, properties:{}}] AS row
MATCH (start:Library{name: row.start.name})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:CONTAINS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {_id:32547}, end: {_id:61699}, properties:{}}, {start: {_id:33538}, end: {_id:62065}, properties:{}}, {start: {_id:44029}, end: {_id:1318238}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:32548}, end: {_id:61700}, properties:{change_description:"Initial import from CDISC", version:"1.0", status:"Final", start_date:datetime('2023-01-17T08:06:55.276Z'), user_initials:"USR1"}}, {start: {_id:33539}, end: {_id:62066}, properties:{change_description:"Initial import from CDISC", version:"1.0", status:"Final", start_date:datetime('2023-01-17T08:06:55.616Z'), user_initials:"USR1"}}, {start: {_id:44030}, end: {_id:66890}, properties:{change_description:"Initial import from CDISC", version:"1.0", status:"Final", start_date:datetime('2023-01-17T08:07:03.454Z'), user_initials:"USR1"}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {_id:32547}, end: {_id:61699}, properties:{change_description:"Imported from CDISC", version:"1.0", status:"Final", start_date:datetime('2014-09-26T00:00:00Z'), user_initials:"USR1"}}, {start: {_id:44029}, end: {_id:1318238}, properties:{change_description:"Imported from CDISC", version:"35.0", status:"Final", start_date:datetime('2016-09-30T00:00:00Z'), user_initials:"USR1"}}, {start: {_id:33538}, end: {_id:62065}, properties:{change_description:"Imported from CDISC", version:"1.0", status:"Final", start_date:datetime('2014-09-26T00:00:00Z'), user_initials:"USR1"}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {_id:33260}, end: {_id:33538}, properties:{}}, {start: {_id:32062}, end: {_id:32547}, properties:{}}, {start: {_id:43770}, end: {_id:44029}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_ATTRIBUTES_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:33260}, end: {_id:33539}, properties:{}}, {start: {_id:43770}, end: {_id:44030}, properties:{}}, {start: {_id:32062}, end: {_id:32548}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_NAME_ROOT]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
"""

# Null flavor codelist extracted by running:
# WITH "MATCH (codelist_root:CTCodelistRoot)-[cl_has_name_root:HAS_NAME_ROOT]-(cl_name_root:CTCodelistNameRoot)-[cl_name_latest:LATEST]-(cl_name_value:CTCodelistNameValue {name: 'Null Flavor'})
#       MATCH (codelist_root)-[cl_has_attr_root:HAS_ATTRIBUTES_ROOT]-(cl_attr_root:CTCodelistAttributesRoot)-[cl_attr_latest:LATEST]-(cl_attr_value:CTCodelistAttributesValue)
#       MATCH (codelist_root)-[has_codelist:HAS_CODELIST]-(cat:CTCatalogue)
#       MATCH (cl_name_root)-[cl_name_latest_final:LATEST_FINAL]-(cl_name_value_final:CTCodelistNameValue)
#       MATCH (cl_attr_root)-[cl_attr_latest_final:LATEST_FINAL]-(cl_attr_value_final:CTCodelistAttributesValue)
#       MATCH (codelist_root)-[contains_cl:CONTAINS_CODELIST]-(library:Library)
#       MATCH (codelist_root)-[has_term:HAS_TERM]-(term:CTTermRoot)
#       MATCH (term)-[t_has_name_root:HAS_NAME_ROOT]-(t_name_root:CTTermNameRoot)
#       MATCH (t_name_root)-[t_name_latest:LATEST]-(t_name_value:CTTermNameValue)
#       MATCH (t_name_root)-[t_name_latest_final:LATEST_FINAL]-(t_name_value_final:CTTermNameValue)
#       MATCH (term)-[t_has_attr_root:HAS_ATTRIBUTES_ROOT]-(t_attr_root:CTTermAttributesRoot)-[t_attr_latest:LATEST]-(t_attr_value:CTTermAttributesValue)
#       MATCH (t_attr_root)-[t_attr_latest_final:LATEST_FINAL]-(t_attr_value_final:CTTermAttributesValue)
#       OPTIONAL MATCH (term)<-[reason:HAS_REASON_FOR_NULL_VALUE]-(template_par)
#       OPTIONAL MATCH (term)<-[libterm:CONTAINS_TERM]-(term_library:Library)
#       RETURN *"
# AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll"})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements;
#
# Extract the needed term with submission value NA
# WITH "MATCH (term_root:CTTermRoot)-[has_name_root:HAS_NAME_ROOT]-(term_name_root:CTTermNameRoot)-[name_latest:LATEST]-(term_name_value:CTTermNameValue {name: 'Not Applicable'})
#       MATCH (term_root)-[has_attr_root:HAS_ATTRIBUTES_ROOT]-(term_attr_root:CTTermAttributesRoot)-[attr_latest:LATEST]-(term_attr_value:CTTermAttributesValue {code_submission_value: 'NA'})
#       MATCH (term_name_root)-[name_latest_final:LATEST_FINAL]-(term_name_value_final:CTTermNameValue)
#       MATCH (term_attr_root)-[attr_latest_final:LATEST_FINAL]-(term_attr_value_final:CTTermAttributesValue)
#       MATCH (term_root)-[has_term:HAS_TERM]-(codelist)
#       MATCH (term_root)-[contains_term:CONTAINS_TERM]-(term_lib)
#       MATCH (codelist)-[has_cl:HAS_CODELIST]-(catalogue)
#       MATCH (codelist)-[contains_cl:CONTAINS_CODELIST]-(library)
#       MATCH (library)-[contains_cat]-(catalogue)
#       return *"
# AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll"})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements;
#
# Note: CREATE INDEX and CREATE CONSTRAINT statements removed!
TEST_DATA_NULL_FLAVOR = """
// Null flavor codelist
UNWIND [{_id:904390, properties:{name:"Unknown", name_sentence_case:"unknown"}}, {_id:904385, properties:{name:"Unencoded", name_sentence_case:"unencoded"}}, {_id:904380, properties:{name:"Trace", name_sentence_case:"trace"}}, {_id:904375, properties:{name:"Positive infinity", name_sentence_case:"positive infinity"}}, {_id:53256, properties:{name:"Not Applicable", name_sentence_case:"not applicable"}}, {_id:56352, properties:{name:"Questionnaire Domain", name_sentence_case:"questionnaire domain"}}, {_id:904355, properties:{name:"No information", name_sentence_case:"no information"}}, {_id:904345, properties:{name:"Masked", name_sentence_case:"masked"}}, {_id:904365, properties:{name:"Negative infinity", name_sentence_case:"negative infinity"}}, {_id:904370, properties:{name:"Not asked", name_sentence_case:"not asked"}}, {_id:904350, properties:{name:"Asked but unknown", name_sentence_case:"asked but unknown"}}, {_id:904360, properties:{name:"Temporarily unavailable", name_sentence_case:"temporarily unavailable"}}, {_id:904335, properties:{name:"Derived", name_sentence_case:"derived"}}, {_id:904340, properties:{name:"Invalid", name_sentence_case:"invalid"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermNameValue;
UNWIND [{_id:903708, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistAttributesRoot;
UNWIND [{name:"CDISC", properties:{is_editable:false}}, {name:"Sponsor", properties:{is_editable:true}}] AS row
MERGE (n:Library{name: row.name}) SET n += row.properties;
UNWIND [{_id:903712, properties:{name:"Null Flavor"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistNameValue;
UNWIND [{_id:903711, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistNameRoot;
UNWIND [{_id:904391, properties:{}}, {_id:904386, properties:{}}, {_id:904371, properties:{}}, {_id:904381, properties:{}}, {_id:19836, properties:{}}, {_id:904376, properties:{}}, {_id:13473, properties:{}}, {_id:904351, properties:{}}, {_id:904361, properties:{}}, {_id:904356, properties:{}}, {_id:904346, properties:{}}, {_id:904366, properties:{}}, {_id:904331, properties:{}}, {_id:904336, properties:{}}, {_id:904341, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermAttributesRoot;
UNWIND [{_id:904389, properties:{}}, {_id:904379, properties:{}}, {_id:904384, properties:{}}, {_id:19837, properties:{}}, {_id:904374, properties:{}}, {_id:13474, properties:{}}, {_id:904354, properties:{}}, {_id:904344, properties:{}}, {_id:904364, properties:{}}, {_id:904369, properties:{}}, {_id:904349, properties:{}}, {_id:904359, properties:{}}, {_id:904334, properties:{}}, {_id:904339, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermNameRoot;
UNWIND [{name:"SDTM CT", properties:{}}] AS row
MERGE (n:CTCatalogue{name: row.name}) SET n += row.properties;
UNWIND [{_id:907956, properties:{field_name:"relapse_criteria"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:StudyField:StudyTextField;
UNWIND [{_id:904387, properties:{preferred_term:"UNK", code_submission_value:"UNK", definition:"A proper value is applicable, but not known.", name_submission_value:"UNK"}}, {_id:904392, properties:{preferred_term:"UNK", code_submission_value:"OTH", definition:"The actual value is not a member of the set of permitted data values in the constrained value domain of a variable (e.g. concept not provided by required code system).", name_submission_value:"OTH"}}, {_id:1319636, properties:{preferred_term:"Questionnaire Domain", concept_id:"C49609", synonyms:["Questionnaires"], code_submission_value:"QS", definition:"A findings domain that contains data for named, stand-alone instruments designed to provide an assessment of a concept. Questionnaires have a defined standard structure, format, and content; consist of conceptually related items that are typically scored; and have documented methods for administration and analysis."}}, {_id:904377, properties:{preferred_term:"UNK", code_submission_value:"TRC", definition:"The content is greater than zero, but too small to be quantified.", name_submission_value:"TRC"}}, {_id:904382, properties:{preferred_term:"UNK", code_submission_value:"UNC", definition:"No attempt has been made to encode the information correctly but the raw source information is represented (usually in originalText).", name_submission_value:"UNC"}}, {_id:904372, properties:{preferred_term:"UNK", code_submission_value:"PINF", definition:"Positive infinity of numbers.", name_submission_value:"PINF"}}, {_id:53255, properties:{preferred_term:"Not Applicable", concept_id:"C48660", synonyms:["NA", "Not Applicable"], code_submission_value:"NOT APPLICABLE", definition:"Determination of a value is not relevant in the current context. (NCI)"}}, {_id:904367, properties:{preferred_term:"UNK", code_submission_value:"NASK", definition:"This information has not been sought (e.g. patient was not asked).", name_submission_value:"NASK"}}, {_id:904362, properties:{preferred_term:"UNK", code_submission_value:"NINF", definition:"Negative infinity of numbers.", name_submission_value:"NINF"}}, {_id:904352, properties:{preferred_term:"UNK", code_submission_value:"NI", definition:"The value is exceptional (missing, omitted, incomplete, improper). No information as to the reason for being an exceptional value is provided. This is the most general exceptional value. It is also the default exceptional value.", name_submission_value:"NI"}}, {_id:904357, properties:{preferred_term:"UNK", code_submission_value:"NAV", definition:"Information is not available at this time, but it is expected that it will be available later.", name_submission_value:"NAV"}}, {_id:904347, properties:{preferred_term:"UNK", code_submission_value:"ASKU", definition:"Information was sought but not found (e.g. patient was asked but didn?t know).", name_submission_value:"ASKU"}}, {_id:904332, properties:{preferred_term:"UNK", code_submission_value:"DER", definition:"An actual value may exist, but it must be derived from the information provided (usually an expression is provided directly).", name_submission_value:"DER"}}, {_id:904337, properties:{preferred_term:"UNK", code_submission_value:"INV", definition:"The value as represented in the instance is not a member of the set of permitted data values in the constrained value domain of a variable.", name_submission_value:"INV"}}, {_id:904342, properties:{preferred_term:"UNK", code_submission_value:"MSK", definition:"There is information on this item available, but it has not been provided by the sender due to security, privacy or other reasons. There may be an alternate mechanism for gaining access to this information. WARNING ? Use of this null flavor does provide information that may be a breach of confidentiality, even though no detailed data are provided. Its primary purpose is for those circumstances where it is necessary to inform the receiver that the information does exist without providing any detail.", name_submission_value:"MSK"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermAttributesValue;
UNWIND [{_id:903709, properties:{preferred_term:"Null Flavor", name:"Null Flavor", definition:"A null flavor is an ancillary piece of data that provides additional information when its primary piece of data is null (has a missing value). There is controlled terminology for the null flavor data item which includes such familiar values as Unknown, Other, and Not Applicable among its fourteen terms.", extensible:true, submission_value:"NULLFLVR"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistAttributesValue;
UNWIND [{_id:907965, properties:{field_name:"stable_disease_minimum_duration"}}, {_id:907951, properties:{field_name:"confirmed_response_minimum_duration"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:StudyField:StudyTimeField;
UNWIND [{_id:904393, properties:{uid:"CTTerm_000102"}}, {_id:904388, properties:{uid:"CTTerm_000101"}}, {_id:904383, properties:{uid:"CTTerm_000100"}}, {_id:904378, properties:{uid:"CTTerm_000099"}}, {_id:19542, properties:{uid:"C49609_QS", concept_id:"C49609"}}, {_id:904373, properties:{uid:"CTTerm_000098"}}, {_id:13236, properties:{uid:"C48660_NOT__APPLICABLE", concept_id:"C48660"}}, {_id:904353, properties:{uid:"CTTerm_000094"}}, {_id:904343, properties:{uid:"CTTerm_000092"}}, {_id:904363, properties:{uid:"CTTerm_000096"}}, {_id:904368, properties:{uid:"CTTerm_000097"}}, {_id:904348, properties:{uid:"CTTerm_000093"}}, {_id:904358, properties:{uid:"CTTerm_000095"}}, {_id:904333, properties:{uid:"CTTerm_000090"}}, {_id:904338, properties:{uid:"CTTerm_000091"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermRoot;
UNWIND [{uid:"CTCodelist_000004", properties:{}}] AS row
MERGE (n:CTCodelistRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{uid:"TemplateParameterValue_000502", properties:{}}] AS row
MERGE (n:TemplateParameterValueRoot{uid: row.uid}) SET n += row.properties SET n:CTTermNameRoot;
UNWIND [{_id:904395, properties:{name:"Other", name_sentence_case:"other"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermNameValue:TemplateParameterValue;
UNWIND [{start: {uid:"CTCodelist_000004"}, end: {_id:904383}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.541661Z')}}, {start: {uid:"CTCodelist_000004"}, end: {_id:904358}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.182353999Z')}}, {start: {uid:"CTCodelist_000004"}, end: {_id:904393}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.702193999Z')}}, {start: {uid:"CTCodelist_000004"}, end: {_id:904378}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.456882Z')}}, {start: {uid:"CTCodelist_000004"}, end: {_id:19542}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.783724Z')}}, {start: {uid:"CTCodelist_000004"}, end: {_id:904388}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.616282Z')}}, {start: {uid:"CTCodelist_000004"}, end: {_id:904363}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.235703Z')}}, {start: {uid:"CTCodelist_000004"}, end: {_id:13236}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.230455999Z')}}, {start: {uid:"CTCodelist_000004"}, end: {_id:904338}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.020785Z')}}, {start: {uid:"CTCodelist_000004"}, end: {_id:904373}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.38126Z')}}, {start: {uid:"CTCodelist_000004"}, end: {_id:904348}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.110943Z')}}, {start: {uid:"CTCodelist_000004"}, end: {_id:904368}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.283378Z')}}, {start: {uid:"CTCodelist_000004"}, end: {_id:904353}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.145426Z')}}, {start: {uid:"CTCodelist_000004"}, end: {_id:904333}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:33.986746Z')}}, {start: {uid:"CTCodelist_000004"}, end: {_id:904343}, properties:{user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.061131Z')}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {name:"Sponsor"}, end: {uid:"CTCodelist_000004"}, properties:{}}] AS row
MATCH (start:Library{name: row.start.name})
MATCH (end:CTCodelistRoot{uid: row.end.uid})
MERGE (start)-[r:CONTAINS_CODELIST]->(end) SET r += row.properties;
UNWIND [{start: {name:"SDTM CT"}, end: {uid:"CTCodelist_000004"}, properties:{}}] AS row
MATCH (start:CTCatalogue{name: row.start.name})
MATCH (end:CTCodelistRoot{uid: row.end.uid})
MERGE (start)-[r:HAS_CODELIST]->(end) SET r += row.properties;
UNWIND [{start: {_id:903708}, end: {_id:903709}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:43:28.239043Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {name:"Sponsor"}, end: {_id:904383}, properties:{}}, {start: {name:"Sponsor"}, end: {_id:904358}, properties:{}}, {start: {name:"Sponsor"}, end: {_id:904393}, properties:{}}, {start: {name:"Sponsor"}, end: {_id:904378}, properties:{}}, {start: {name:"Sponsor"}, end: {_id:904388}, properties:{}}, {start: {name:"Sponsor"}, end: {_id:904363}, properties:{}}, {start: {name:"Sponsor"}, end: {_id:904338}, properties:{}}, {start: {name:"Sponsor"}, end: {_id:904373}, properties:{}}, {start: {name:"Sponsor"}, end: {_id:904348}, properties:{}}, {start: {name:"CDISC"}, end: {_id:13236}, properties:{}}, {start: {name:"CDISC"}, end: {_id:19542}, properties:{}}, {start: {name:"Sponsor"}, end: {_id:904368}, properties:{}}, {start: {name:"Sponsor"}, end: {_id:904353}, properties:{}}, {start: {name:"Sponsor"}, end: {_id:904333}, properties:{}}, {start: {name:"Sponsor"}, end: {_id:904343}, properties:{}}] AS row
MATCH (start:Library{name: row.start.name})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:CONTAINS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {_id:904386}, end: {_id:904387}, properties:{}}, {start: {_id:904381}, end: {_id:904382}, properties:{}}, {start: {_id:904391}, end: {_id:904392}, properties:{}}, {start: {_id:904361}, end: {_id:904362}, properties:{}}, {start: {_id:19836}, end: {_id:1319636}, properties:{}}, {start: {_id:904366}, end: {_id:904367}, properties:{}}, {start: {_id:13473}, end: {_id:53255}, properties:{}}, {start: {_id:904336}, end: {_id:904337}, properties:{}}, {start: {_id:904351}, end: {_id:904352}, properties:{}}, {start: {_id:904376}, end: {_id:904377}, properties:{}}, {start: {_id:904371}, end: {_id:904372}, properties:{}}, {start: {_id:904331}, end: {_id:904332}, properties:{}}, {start: {_id:904356}, end: {_id:904357}, properties:{}}, {start: {_id:904341}, end: {_id:904342}, properties:{}}, {start: {_id:904346}, end: {_id:904347}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:903708}, end: {_id:903709}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:904364}, end: {_id:904365}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.583385Z')}}, {start: {_id:904359}, end: {_id:904360}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.512096Z')}}, {start: {_id:904379}, end: {_id:904380}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.886023Z')}}, {start: {_id:904384}, end: {_id:904385}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.968749Z')}}, {start: {_id:904369}, end: {_id:904370}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.673918Z')}}, {start: {_id:904374}, end: {_id:904375}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.796017Z')}}, {start: {_id:904339}, end: {_id:904340}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.256147Z')}}, {start: {_id:904389}, end: {_id:904390}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:35.01902Z')}}, {start: {_id:13474}, end: {_id:53256}, properties:{change_description:"Initial import from CDISC", version:"1.0", status:"Final", start_date:datetime('2023-01-17T08:06:47.337Z'), user_initials:"USR1"}}, {start: {_id:904349}, end: {_id:904350}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.407962999Z')}}, {start: {_id:19837}, end: {_id:56352}, properties:{change_description:"Initial import from CDISC", version:"1.0", status:"Final", start_date:datetime('2023-01-17T08:06:50.056Z'), user_initials:"USR1"}}, {start: {_id:904354}, end: {_id:904355}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.424289Z')}}, {start: {_id:904344}, end: {_id:904345}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.325836Z')}}, {start: {_id:904334}, end: {_id:904335}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.166839999Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {uid:"CTCodelist_000004"}, end: {_id:903708}, properties:{}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_ATTRIBUTES_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {uid:"TemplateParameterValue_000502"}, end: {_id:904395}, properties:{}}] AS row
MATCH (start:TemplateParameterValueRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:904393}, end: {uid:"TemplateParameterValue_000502"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:TemplateParameterValueRoot{uid: row.end.uid})
MERGE (start)-[r:HAS_NAME_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:904388}, end: {_id:904386}, properties:{}}, {start: {_id:904383}, end: {_id:904381}, properties:{}}, {start: {_id:904363}, end: {_id:904361}, properties:{}}, {start: {_id:904393}, end: {_id:904391}, properties:{}}, {start: {_id:19542}, end: {_id:19836}, properties:{}}, {start: {_id:904368}, end: {_id:904366}, properties:{}}, {start: {_id:13236}, end: {_id:13473}, properties:{}}, {start: {_id:904338}, end: {_id:904336}, properties:{}}, {start: {_id:904353}, end: {_id:904351}, properties:{}}, {start: {_id:904378}, end: {_id:904376}, properties:{}}, {start: {_id:904373}, end: {_id:904371}, properties:{}}, {start: {_id:904333}, end: {_id:904331}, properties:{}}, {start: {_id:904358}, end: {_id:904356}, properties:{}}, {start: {_id:904343}, end: {_id:904341}, properties:{}}, {start: {_id:904348}, end: {_id:904346}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_ATTRIBUTES_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:903711}, end: {_id:903712}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:43:27.08814Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {uid:"CTCodelist_000004"}, end: {_id:903711}, properties:{}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_NAME_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:904384}, end: {_id:904385}, properties:{}}, {start: {_id:904379}, end: {_id:904380}, properties:{}}, {start: {_id:904359}, end: {_id:904360}, properties:{}}, {start: {_id:904389}, end: {_id:904390}, properties:{}}, {start: {_id:904364}, end: {_id:904365}, properties:{}}, {start: {_id:904339}, end: {_id:904340}, properties:{}}, {start: {_id:13474}, end: {_id:53256}, properties:{}}, {start: {_id:904374}, end: {_id:904375}, properties:{}}, {start: {_id:904349}, end: {_id:904350}, properties:{}}, {start: {_id:19837}, end: {_id:56352}, properties:{}}, {start: {_id:904369}, end: {_id:904370}, properties:{}}, {start: {_id:904354}, end: {_id:904355}, properties:{}}, {start: {_id:904334}, end: {_id:904335}, properties:{}}, {start: {_id:904344}, end: {_id:904345}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:907951}, end: {_id:13236}, properties:{}}, {start: {_id:907965}, end: {_id:13236}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_REASON_FOR_NULL_VALUE]->(end) SET r += row.properties;
UNWIND [{start: {_id:903711}, end: {_id:903712}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:904381}, end: {_id:904382}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:35.164817999Z')}}, {start: {_id:904376}, end: {_id:904377}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:35.165887Z')}}, {start: {_id:904331}, end: {_id:904332}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.497778999Z')}}, {start: {_id:904356}, end: {_id:904357}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.911517Z')}}, {start: {_id:19836}, end: {_id:1319636}, properties:{change_description:"Imported from CDISC", version:"23.0", status:"Final", start_date:datetime('2018-03-30T00:00:00Z'), user_initials:"USR1"}}, {start: {_id:904341}, end: {_id:904342}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.761476Z')}}, {start: {_id:904391}, end: {_id:904392}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:35.227045Z')}}, {start: {_id:904386}, end: {_id:904387}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:35.227859Z')}}, {start: {_id:904346}, end: {_id:904347}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.850653Z')}}, {start: {_id:904336}, end: {_id:904337}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.652408Z')}}, {start: {_id:904351}, end: {_id:904352}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.871668Z')}}, {start: {_id:13473}, end: {_id:53255}, properties:{change_description:"Imported from CDISC", version:"1.0", status:"Final", start_date:datetime('2014-09-26T00:00:00Z'), user_initials:"USR1"}}, {start: {_id:904366}, end: {_id:904367}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:35.027664Z')}}, {start: {_id:904361}, end: {_id:904362}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:34.982481Z')}}, {start: {_id:904371}, end: {_id:904372}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:35.121241Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {uid:"TemplateParameterValue_000502"}, end: {_id:904395}, properties:{change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2023-01-17T09:44:35.117470999Z')}}] AS row
MATCH (start:TemplateParameterValueRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {_id:904383}, end: {_id:904384}, properties:{}}, {start: {_id:904378}, end: {_id:904379}, properties:{}}, {start: {_id:904358}, end: {_id:904359}, properties:{}}, {start: {_id:904388}, end: {_id:904389}, properties:{}}, {start: {_id:904363}, end: {_id:904364}, properties:{}}, {start: {_id:19542}, end: {_id:19837}, properties:{}}, {start: {_id:904373}, end: {_id:904374}, properties:{}}, {start: {_id:904333}, end: {_id:904334}, properties:{}}, {start: {_id:904348}, end: {_id:904349}, properties:{}}, {start: {_id:13236}, end: {_id:13474}, properties:{}}, {start: {_id:904353}, end: {_id:904354}, properties:{}}, {start: {_id:904368}, end: {_id:904369}, properties:{}}, {start: {_id:904338}, end: {_id:904339}, properties:{}}, {start: {_id:904343}, end: {_id:904344}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_NAME_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:907956}, end: {_id:13236}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_REASON_FOR_NULL_VALUE]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
// Current "not applicable" term
UNWIND [{_id:65666, properties:{name:"Not Applicable", name_sentence_case:"not applicable"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermNameValue;
UNWIND [{_id:65665, properties:{preferred_term:"Not Applicable", concept_id:"C48660", synonyms:["NA", "Not Applicable"], code_submission_value:"NA", definition:"Determination of a value is not relevant in the current context. (NCI)"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermAttributesValue;
UNWIND [{name:"CDISC", properties:{is_editable:false}}] AS row
MERGE (n:Library{name: row.name}) SET n += row.properties;
UNWIND [{_id:40814, properties:{uid:"C48660_NA", concept_id:"C48660"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermRoot;
UNWIND [{_id:41139, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermAttributesRoot;
UNWIND [{uid:"C150810", properties:{}}, {uid:"C66742", properties:{}}] AS row
MERGE (n:CTCodelistRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{name:"SDTM CT", properties:{}}, {name:"PROTOCOL CT", properties:{}}, {name:"SEND CT", properties:{}}] AS row
MERGE (n:CTCatalogue{name: row.name}) SET n += row.properties;
UNWIND [{_id:41140, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermNameRoot;
UNWIND [{start: {name:"PROTOCOL CT"}, end: {uid:"C66742"}, properties:{}}, {start: {name:"SDTM CT"}, end: {uid:"C66742"}, properties:{}}, {start: {name:"SEND CT"}, end: {uid:"C150810"}, properties:{}}, {start: {name:"SEND CT"}, end: {uid:"C66742"}, properties:{}}] AS row
MATCH (start:CTCatalogue{name: row.start.name})
MATCH (end:CTCodelistRoot{uid: row.end.uid})
MERGE (start)-[r:HAS_CODELIST]->(end) SET r += row.properties;
UNWIND [{start: {uid:"C150810"}, end: {_id:40814}, properties:{start_date:datetime('2021-12-17T00:00:00Z'), user_initials:"USR1"}}, {start: {uid:"C66742"}, end: {_id:40814}, properties:{start_date:datetime('2014-09-26T00:00:00Z'), user_initials:"USR1"}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {name:"CDISC"}, end: {uid:"C150810"}, properties:{}}, {start: {name:"CDISC"}, end: {uid:"C66742"}, properties:{}}] AS row
MATCH (start:Library{name: row.start.name})
MATCH (end:CTCodelistRoot{uid: row.end.uid})
MERGE (start)-[r:CONTAINS_CODELIST]->(end) SET r += row.properties;
UNWIND [{start: {_id:41140}, end: {_id:65666}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {name:"CDISC"}, end: {_id:40814}, properties:{}}] AS row
MATCH (start:Library{name: row.start.name})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:CONTAINS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {_id:41139}, end: {_id:65665}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:41140}, end: {_id:65666}, properties:{change_description:"Initial import from CDISC", version:"1.0", status:"Final", start_date:datetime('2023-01-17T08:06:59.445Z'), user_initials:"USR1"}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {name:"CDISC"}, end: {name:"PROTOCOL CT"}, properties:{}}, {start: {name:"CDISC"}, end: {name:"SDTM CT"}, properties:{}}, {start: {name:"CDISC"}, end: {name:"SEND CT"}, properties:{}}] AS row
MATCH (start:Library{name: row.start.name})
MATCH (end:CTCatalogue{name: row.end.name})
MERGE (start)-[r:CONTAINS_CATALOGUE]->(end) SET r += row.properties;
UNWIND [{start: {_id:41139}, end: {_id:65665}, properties:{change_description:"Imported from CDISC", version:"1.0", status:"Final", start_date:datetime('2014-09-26T00:00:00Z'), user_initials:"USR1"}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {_id:40814}, end: {_id:41139}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_ATTRIBUTES_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:40814}, end: {_id:41140}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_NAME_ROOT]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
"""

# Unit dimension codelist extracted (without its terms) by running:
# WITH "MATCH (codelist_root:CTCodelistRoot)-[cl_has_name_root:HAS_NAME_ROOT]-(cl_name_root:CTCodelistNameRoot)-[cl_name_latest:LATEST]-(cl_name_value:CTCodelistNameValue {name: 'Unit Dimension'})
#       MATCH (codelist_root)-[cl_has_attr_root:HAS_ATTRIBUTES_ROOT]-(cl_attr_root:CTCodelistAttributesRoot)-[cl_attr_latest:LATEST]-(cl_attr_value:CTCodelistAttributesValue)
#       MATCH (codelist_root)-[has_codelist:HAS_CODELIST]-(cat:CTCatalogue)
#       MATCH (cl_name_root)-[cl_name_latest_final:LATEST_FINAL]-(cl_name_value_final:CTCodelistNameValue)
#       MATCH (cl_attr_root)-[cl_attr_latest_final:LATEST_FINAL]-(cl_attr_value_final:CTCodelistAttributesValue)
#       MATCH (codelist_root)-[contains_cl:CONTAINS_CODELIST]-(library:Library)
#       RETURN *"
# AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll"})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements;
#
# Note: CREATE INDEX and CREATE CONSTRAINT statements removed!
TEST_DATA_NOT_EXTENSIBLE_CODELIST = """
UNWIND [{_id:849846, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistAttributesRoot;
UNWIND [{_id:849850, properties:{name:"Unit Dimension"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistNameValue;
UNWIND [{_id:849847, properties:{preferred_term:"Unit Dimension", name:"Unit Dimension", definition:"Unit Dimension act as a reference to a set of unit definitions where unit conversion is possible.Y", extensible:false, submission_value:"UNITDIM"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistAttributesValue;
UNWIND [{_id:41, properties:{name:"SDTM CT"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCatalogue;
UNWIND [{_id:849849, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistNameRoot;
UNWIND [{_id:847729, properties:{name:"Sponsor", is_editable:true}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:Library;
UNWIND [{uid:"CTCodelist_000001", properties:{}}] AS row
MERGE (n:CTCodelistRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{start: {uid:"CTCodelist_000001"}, end: {_id:849849}, properties:{}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_NAME_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:849849}, end: {_id:849850}, properties:{change_description:"Approved version", version:"2.0", status:"Final", start_date:datetime('2023-02-09T10:26:34.032724Z'), user_initials:"USR2"}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {_id:849846}, end: {_id:849847}, properties:{change_description:"Approved version", version:"1.0", user_initials:"00000000-0000-0000-0000-000000000002", status:"Final", start_date:datetime('2022-09-21T19:36:29.306724Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {_id:849849}, end: {_id:849850}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:849846}, end: {_id:849847}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:847729}, end: {uid:"CTCodelist_000001"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTCodelistRoot{uid: row.end.uid})
MERGE (start)-[r:CONTAINS_CODELIST]->(end) SET r += row.properties;
UNWIND [{start: {uid:"CTCodelist_000001"}, end: {_id:849846}, properties:{}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_ATTRIBUTES_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:41}, end: {uid:"CTCodelist_000001"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTCodelistRoot{uid: row.end.uid})
MERGE (start)-[r:HAS_CODELIST]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
"""
# Complete test data set
TEST_DATA = "\n".join(
    [
        TEST_DATA_CT_CONFIG,
        TEST_DATA_ACTIVITIES_GROUPS,
        TEST_DATA_ACTIVITIES,
        TEST_DATA_STUDY_SELECTION,
        TEST_DATA_STUDY_FIELDS,
        TEST_DATA_RESERVED_CHARS_IN_UID,
        TEST_DATA_NULL_FLAVOR,
        TEST_DATA_NOT_EXTENSIBLE_CODELIST,
    ]
)
