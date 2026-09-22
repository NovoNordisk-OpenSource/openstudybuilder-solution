# WITH "
# MATCH (n:UnitDefinitionRoot {uid: 'UnitDefinition_000001'})-[ver:HAS_VERSION]->(m)
# MATCH (n)-[cc:CONTAINS_CONCEPT]-(l:Library)
# RETURN *
# " AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll",ifNotExists: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;
USER_INFO_EXAMPLE_HAS_VERSION = """
UNWIND [{_id:1169074, properties:{us_conventional_unit:false, si_unit:true, display_unit:true, name:"mL/dL/min", master_unit:true, comment:"", definition:"milli-liter per deci-liter per minute\n", molecular_weight_conv_expon:0, convertible_unit:true, conversion_factor_to_master:1.0, legacy_code:"mL/dL/min", order:21}}, {_id:1169093, properties:{us_conventional_unit:true, si_unit:true, display_unit:true, name:"mL/dL/min", master_unit:true, comment:"", definition:"milli-liter per deci-liter per minute\n", molecular_weight_conv_expon:0, convertible_unit:true, conversion_factor_to_master:1.0, legacy_code:"mL/dL/min", order:21}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:TemplateParameterTermValue:UnitDefinitionValue;
UNWIND [{uid:"UnitDefinition_000001", properties:{}}] AS row
MERGE (n:ConceptRoot{uid: row.uid}) SET n += row.properties SET n:TemplateParameterTermRoot:UnitDefinitionRoot;
UNWIND [{_id:1151418, properties:{name:"Sponsor", is_editable:true}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:Library;
UNWIND [{start: {_id:1151418}, end: {uid:"UnitDefinition_000001"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:ConceptRoot{uid: row.end.uid})
MERGE (start)-[r:CONTAINS_CONCEPT]->(end) SET r += row.properties;
UNWIND [{start: {uid:"UnitDefinition_000001"}, end: {_id:1169074}, properties:{end_date:datetime('2024-08-08T14:33:53.839901Z'), change_description:"Initial version", version:"0.1", status:"Draft", user_initials:"unknown-user", start_date:datetime('2024-08-08T14:33:52.907081Z')}}, {start: {uid:"UnitDefinition_000001"}, end: {_id:1169093}, properties:{end_date:datetime('2024-08-09T09:37:01.93974Z'), change_description:"Approved version", version:"1.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2024-08-08T14:33:53.839901Z')}}, {start: {uid:"UnitDefinition_000001"}, end: {_id:1169093}, properties:{end_date:datetime('2024-08-09T09:37:08.873586Z'), change_description:"New draft created", version:"1.1", status:"Draft", user_initials:"unknown-user", start_date:datetime('2024-08-09T09:37:01.93974Z')}}, {start: {uid:"UnitDefinition_000001"}, end: {_id:1169074}, properties:{end_date:datetime('2024-08-09T09:37:39.425972Z'), change_description:"Migration modification", version:"1.2", status:"Draft", user_initials:"unknown-user", start_date:datetime('2024-08-09T09:37:08.873586Z')}}, {start: {uid:"UnitDefinition_000001"}, end: {_id:1169093}, properties:{change_description:"Approved version", version:"2.0", status:"Final", user_initials:"unknown-user", start_date:datetime('2024-08-09T09:37:39.425972Z')}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;

UNWIND [{uid:"UnitDefinition_000389", properties:{}}] AS row
MERGE (n:ConceptRoot{uid: row.uid}) SET n += row.properties SET n:UnitDefinitionRoot;
UNWIND [{_id:1151418, properties:{name:"Sponsor", is_editable:true}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:Library;
UNWIND [{_id:24, properties:{us_conventional_unit:false, display_unit:false, si_unit:false, name:"ab1 upd1", master_unit:false, convertible_unit:false}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:UnitDefinitionValue;
UNWIND [{start: {uid:"UnitDefinition_000389"}, end: {_id:24}, properties:{change_description:"Initial version", version:"0.5", user_initials:"ABZO", status:"Draft", start_date:datetime('2024-12-02T11:05:52.569722Z')}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {_id:1151418}, end: {uid:"UnitDefinition_000389"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:ConceptRoot{uid: row.end.uid})
MERGE (start)-[r:CONTAINS_CONCEPT]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
"""

# WITH "
# MATCH (n:CTPackage {uid: 'ADAM CT 2014-09-26'})-[cp:CONTAINS_PACKAGE]-(m)-[cc:CONTAINS_CATALOGUE]-(l)
# RETURN *
# " AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll",ifNotExists: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;
USER_INFO_EXAMPLE_CT_PACKAGE = """
UNWIND [{_id:8016, properties:{name:"ADAM CT"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCatalogue;
UNWIND [{_id:8014, properties:{name:"CDISC", is_editable:false}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:Library;
UNWIND [{uid:"ADAM CT 2014-09-26", properties:{name:"ADAM CT 2014-09-26", effective_date:date('2014-09-26'), import_date:datetime('2024-08-08T13:50:35.882Z'), user_initials:"TEST"}}] AS row
MERGE (n:CTPackage{uid: row.uid}) SET n += row.properties;
UNWIND [{start: {_id:8014}, end: {_id:8016}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:CONTAINS_CATALOGUE]->(end) SET r += row.properties;
UNWIND [{start: {_id:8016}, end: {uid:"ADAM CT 2014-09-26"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTPackage{uid: row.end.uid})
MERGE (start)-[r:CONTAINS_PACKAGE]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
"""

# WITH "
# MATCH (sr:StudyRoot)-[v1:AUDIT_TRAIL]-(n1:Create)-[v1after:AFTER]-(m1)
# MATCH (sr)-[v2:AUDIT_TRAIL]-(n2:Edit)-[v2before:BEFORE]-(m2)
# MATCH (n2)-[v2after:AFTER]-(m3)
# RETURN *
# LIMIT 1
# " AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll",ifNotExists: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;
USER_INFO_EXAMPLE_STUDY_ACTIONS = """
UNWIND [{_id:1173565, properties:{date:datetime('2024-08-09T09:38:34.086311Z'), user_initials:"unknown-user"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:StudyAction:Create;
UNWIND [{_id:1173190, properties:{study_id_prefix:"CDISC DEV", study_number:"0"}}, {_id:1173532, properties:{study_acronym:"CDISC360-2", study_id_prefix:"CDISC DEV", study_number:"0"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:StudyValue;
UNWIND [{_id:1173533, properties:{date:datetime('2024-08-09T09:38:34.086311Z'), user_initials:"unknown-user"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:StudyAction:Edit;
UNWIND [{_id:1173564, properties:{value:false, field_name:"pediatric_study_indicator"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:StudyField:StudyBooleanField;
UNWIND [{uid:"Study_000001", properties:{}}] AS row
MERGE (n:StudyRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{start: {_id:1173533}, end: {_id:1173190}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:BEFORE]->(end) SET r += row.properties;
UNWIND [{start: {uid:"Study_000001"}, end: {_id:1173533}, properties:{}}] AS row
MATCH (start:StudyRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:AUDIT_TRAIL]->(end) SET r += row.properties;
UNWIND [{start: {uid:"Study_000001"}, end: {_id:1173565}, properties:{}}] AS row
MATCH (start:StudyRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:AUDIT_TRAIL]->(end) SET r += row.properties;
UNWIND [{start: {_id:1173533}, end: {_id:1173532}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:AFTER]->(end) SET r += row.properties;
UNWIND [{start: {_id:1173565}, end: {_id:1173564}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:AFTER]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
"""


# WITH "
# MATCH (intervention:TemplateParameter {name:'Intervention'})-[rel:HAS_PARENT_PARAMETER]->(actvity_instance:TemplateParameter {name:'ActivityInstance'})
# RETURN *
# " AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll",ifNotExists: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;
INTERVENTION_AND_AI_TEMPLATE_PARAMETER_NODES = """
CREATE TEXT INDEX IF NOT EXISTS FOR (n:TemplateParameter) ON (n.name);
CREATE CONSTRAINT UNIQUE_IMPORT_NAME IF NOT EXISTS FOR (node:`UNIQUE IMPORT LABEL`) REQUIRE (node.`UNIQUE IMPORT ID`) IS UNIQUE;
UNWIND [{_id:3, properties:{name:"ActivityInstance"}}, {_id:5, properties:{name:"Intervention"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:TemplateParameter;
UNWIND [{start: {_id:5}, end: {_id:3}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_PARENT_PARAMETER]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
"""


# WITH "
# MATCH (n:CTPackage|StudyAction|Edit|Create|Delete)
# WHERE n.author_id = 'qphm'
# RETURN *
# LIMIT 5
# " AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll",ifNotExists: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;
QPHM_NODES = """
UNWIND [{_id:1042986, properties:{date:datetime('2024-03-22T10:24:50.544452Z'), author_id:"qphm", user_initials:"QPHM"}}, {_id:1042997, properties:{date:datetime('2024-03-22T10:25:42.311568Z'), author_id:"qphm", user_initials:"QPHM"}}, {_id:1043007, properties:{date:datetime('2024-03-22T10:26:18.500148Z'), author_id:"qphm", user_initials:"QPHM"}}, {_id:1043020, properties:{date:datetime('2024-03-22T10:26:44.784021Z'), author_id:"qphm", user_initials:"QPHM"}}, {_id:1043063, properties:{date:datetime('2024-03-22T10:28:52.337857Z'), author_id:"qphm", user_initials:"QPHM", status:"DRAFT"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:StudyAction:Create;
"""

# WITH "
# MATCH (n)-[ver:HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_DRAFT|LATEST_LOCKED|LATEST_RELEASED]->(m)
# WHERE ver.author_id = 'qphm'
# RETURN *
# " AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll",ifNotExists: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;
QPHM_RELATIONSHIPS = """
UNWIND [{_id:1043116, properties:{name:"Dose Escalation 5", name_sentence_case:"dose escalation 5"}}, {_id:1043159, properties:{name:"Dose Escalation 6", name_sentence_case:"dose escalation 6"}}, {_id:1043187, properties:{name:"Dose Escalation 7", name_sentence_case:"dose escalation 7"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermNameValue;
UNWIND [{_id:1043113, properties:{preferred_term:"UNK", code_submission_value:"DOSE ESCALATION EPOCH 5", definition:"", name_submission_value:"DOSE ESCALATION EPOCH 5"}}, {_id:1043156, properties:{preferred_term:"UNK", code_submission_value:"DOSE ESCALATION EPOCH 6", definition:"", name_submission_value:"DOSE ESCALATION EPOCH 6"}}, {_id:1043180, properties:{preferred_term:"UNK", code_submission_value:"DOSE ESCALATION EPOCH 7", definition:"", name_submission_value:"DOSE ESCALATION EPOCH 7"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermAttributesValue;
UNWIND [{_id:1043112, properties:{}}, {_id:1043155, properties:{}}, {_id:1043179, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermAttributesRoot;
UNWIND [{uid:"CTTerm_001189", properties:{}}, {uid:"CTTerm_001190", properties:{}}, {uid:"CTTerm_001191", properties:{}}] AS row
MERGE (n:CTTermRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{uid:"C99079", properties:{}}] AS row
MERGE (n:CTCodelistRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{_id:1043115, properties:{}}, {_id:1043158, properties:{}}, {_id:1043185, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermNameRoot;
UNWIND [{start: {uid:"C99079"}, end: {uid:"CTTerm_001189"}, properties:{author_id:"qphm", start_date:datetime('2024-03-22T10:29:40.264419Z'), user_initials:"QPHM"}}, {start: {uid:"C99079"}, end: {uid:"CTTerm_001190"}, properties:{author_id:"qphm", start_date:datetime('2024-03-22T10:29:57.333142Z'), user_initials:"QPHM"}}, {start: {uid:"C99079"}, end: {uid:"CTTerm_001191"}, properties:{author_id:"qphm", start_date:datetime('2024-03-22T10:30:10.114175Z'), user_initials:"QPHM"}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:CTTermRoot{uid: row.end.uid})
MERGE (start)-[r:HAS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {_id:1043115}, end: {_id:1043116}, properties:{change_description:"Approved version", author_id:"qphm", version:"1.0", status:"Final", start_date:datetime('2024-03-22T10:29:40.456989Z'), user_initials:"QPHM"}}, {start: {_id:1043158}, end: {_id:1043159}, properties:{change_description:"Approved version", author_id:"qphm", version:"1.0", status:"Final", start_date:datetime('2024-03-22T10:29:57.402455Z'), user_initials:"QPHM"}}, {start: {_id:1043185}, end: {_id:1043187}, properties:{change_description:"Approved version", author_id:"qphm", version:"1.0", status:"Final", start_date:datetime('2024-03-22T10:30:10.166368Z'), user_initials:"QPHM"}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {_id:1043112}, end: {_id:1043113}, properties:{change_description:"Approved version", author_id:"qphm", version:"1.0", status:"Final", start_date:datetime('2024-03-22T10:29:40.073735Z'), user_initials:"QPHM"}}, {start: {_id:1043155}, end: {_id:1043156}, properties:{change_description:"Approved version", author_id:"qphm", version:"1.0", status:"Final", start_date:datetime('2024-03-22T10:29:57.198776Z'), user_initials:"QPHM"}}, {start: {_id:1043179}, end: {_id:1043180}, properties:{change_description:"Approved version", author_id:"qphm", version:"1.0", status:"Final", start_date:datetime('2024-03-22T10:30:10.009216Z'), user_initials:"QPHM"}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
"""

TEST_DATA = "\n".join(
    [
        USER_INFO_EXAMPLE_HAS_VERSION,
        USER_INFO_EXAMPLE_CT_PACKAGE,
        USER_INFO_EXAMPLE_STUDY_ACTIONS,
        INTERVENTION_AND_AI_TEMPLATE_PARAMETER_NODES,
        QPHM_NODES,
        QPHM_RELATIONSHIPS,
    ]
)
