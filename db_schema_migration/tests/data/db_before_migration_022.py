FEATURE_FLAGS = """
UNWIND [{sn:1, properties:{name:"feature_flag_1", description: "description", enabled: true}}, {sn: 2, properties:{name:"feature_flag_2", description: "description", enabled: false}}] AS row
MERGE (n:FeatureFlag{sn: row.sn}) SET n += row.properties;
"""

# Instances split migration - database state before migration
# WITH "
# MATCH (air:ActivityInstanceRoot)
# WITH * LIMIT 5
# MATCH (air)-[aihv:HAS_VERSION]-(aiv:ActivityInstanceValue)-[aiha:HAS_ACTIVITY]-(agrp:ActivityGrouping)-[hg:HAS_GROUPING]-(av:ActivityValue)-[ahv:LATEST]-(ar:ActivityRoot)
#
# MATCH (agrp)-[ssg:HAS_SELECTED_SUBGROUP]-(asgv:ActivitySubGroupValue)-[asghv:HAS_VERSION]-(asgr:ActivitySubGroupRoot)
# MATCH (agrp)-[sg:HAS_SELECTED_GROUP]-(agv:ActivityGroupValue)-[aghv:LATEST]-(agr:ActivityGroupRoot)
# RETURN *
# " AS cypherQuery
#
# // Execute the query and collect nodes and relationships
# CALL apoc.cypher.run(cypherQuery, {}) YIELD value
# UNWIND value as row
# WITH [key IN keys(row) WHERE apoc.meta.cypher.isType(row[key], "NODE") | row[key]] AS nodes_in_row
# UNWIND nodes_in_row as node
# WITH collect(DISTINCT node) AS all_nodes
# WITH all_nodes, [node IN all_nodes | elementId(node)] AS node_ids
# MATCH (n)-[rel]->(m)
# WHERE elementId(n) IN node_ids
# AND elementId(m) IN node_ids
# WITH all_nodes, collect(DISTINCT rel) AS all_rels
#
# // Export the nodes and relationships as cypher statements
# CALL apoc.export.cypher.data(all_nodes, all_rels,
#    NULL,
#    { format: "plain", cypherFormat: "create", stream: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements
INSTANCES_BEFORE_SPLIT = """
CREATE CONSTRAINT UNIQUE_IMPORT_NAME FOR (node:`UNIQUE IMPORT LABEL`) REQUIRE (node.`UNIQUE IMPORT ID`) IS UNIQUE;
UNWIND [{uid:"ActivityGroup_000003", properties:{}}, {uid:"ActivityGroup_000096", properties:{}}, {uid:"ActivityGroup_000004", properties:{}}] AS row
CREATE (n:ActivityGroupRoot{uid: row.uid}) SET n += row.properties SET n:ConceptRoot:TemplateParameterTermRoot;
UNWIND [{_id:3797, properties:{topic_code:"ERYTHROCYTE_MEAN_CORPUSCULAR_HEMOGLOBIN_BLOOD", is_derived:false, adam_param_code:"EMCHB", name:"Erythrocyte Mean Corposcular Haemoglobin Blood", name_sentence_case:"erythrocyte mean corposcular haemoglobin blood", definition:"TBD", is_default_selected_for_activity:false, is_data_sharing:false, is_required_for_activity:false, legacy_description:"A measurement of the mean amount of hemoglobin per erythrocyte in blood calculated as the product of hemoglobin times ten, divided by the number of erythrocytes.", is_legacy_usage:false, is_research_lab:false}}, {_id:3798, properties:{topic_code:"ADA_IGE_0487_0111_SERUM", is_derived:false, adam_param_code:"A0154ES", name:"REDACTED", name_sentence_case:"REDACTED", definition:"TBD", is_default_selected_for_activity:false, is_data_sharing:false, is_required_for_activity:false, legacy_description:"REDACTED", is_legacy_usage:false, is_research_lab:false}}, {_id:3800, properties:{topic_code:"REDACTED", is_derived:false, adam_param_code:"REDACTED", name:"REDACTED", name_sentence_case:"REDACTED", definition:"TBD", is_default_selected_for_activity:false, is_data_sharing:false, is_required_for_activity:false, legacy_description:"REDACTED", is_legacy_usage:false, is_research_lab:false}}, {_id:8587, properties:{topic_code:"EQ5D05_01_MOBILITY", is_derived:false, adam_param_code:"EQ5D0501", name:"EQ-5D-Y-3L - Mobility", name_sentence_case:"eq-5d-y-3l - mobility", definition:"TBD", is_default_selected_for_activity:false, is_data_sharing:false, is_required_for_activity:false, legacy_description:"European Quality of Life Five Dimension Youth Three Level Scale (EQ-5D-Y-3L). Euroqol Research Foundation. EQ-5D Is a Trade Mark of the Euroqol Research Foundation. UK (english) V2.4 - Under each heading, please choose the ONE answer that best describes your health TODAY Mobility (walking about)", is_legacy_usage:false, is_research_lab:false}}, {_id:8588, properties:{topic_code:"EQ5D05_02_LOOKING_AFTER_MYSELF", is_derived:false, adam_param_code:"EQ5D0502", name:"EQ-5D-Y-3L - Looking After Myself", name_sentence_case:"eq-5d-y-3l - looking after myself", definition:"TBD", is_default_selected_for_activity:false, is_data_sharing:false, is_required_for_activity:false, legacy_description:"European Quality of Life Five Dimension Youth Three Level Scale (EQ-5D-Y-3L). Euroqol Research Foundation. EQ-5D Is a Trade Mark of the Euroqol Research Foundation. UK (english) V2.4 - Under each heading, please choose the ONE answer that best describes your health TODAY Looking after myself", is_legacy_usage:false, is_research_lab:false}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:ActivityInstanceValue:TemplateParameterTermValue;
UNWIND [{uid:"ActivitySubGroup_000058", properties:{}}, {uid:"ActivitySubGroup_000006", properties:{}}, {uid:"ActivitySubGroup_000332", properties:{}}, {uid:"ActivitySubGroup_000472", properties:{}}] AS row
CREATE (n:ActivitySubGroupRoot{uid: row.uid}) SET n += row.properties SET n:ConceptRoot:TemplateParameterTermRoot;
UNWIND [{_id:852603, properties:{name:"Haematology", name_sentence_case:"haematology"}}, {_id:852499, properties:{name:"Antibodies", name_sentence_case:"antibodies"}}, {_id:1023822, properties:{name:"Administration of IMP", name_sentence_case:"administration of imp"}}, {_id:8506, properties:{name:"EQ-5D-Y-3L", name_sentence_case:"eq-5d-y-3l"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:ActivitySubGroupValue:TemplateParameterTermValue;
UNWIND [{_id:852482, properties:{name:"Laboratory Assessments", name_sentence_case:"laboratory assessments"}}, {_id:1023809, properties:{name:"Administration of IMP", name_sentence_case:"administration of imp"}}, {_id:852484, properties:{name:"Clinical Outcome Assessments", name_sentence_case:"clinical outcome assessments"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:TemplateParameterTermValue:ActivityGroupValue;
UNWIND [{_id:3703, properties:{uid:"ActivityGrouping_013188"}}, {_id:3705, properties:{uid:"ActivityGrouping_013189"}}, {_id:3700, properties:{uid:"ActivityGrouping_013187"}}, {_id:8519, properties:{uid:"ActivityGrouping_013197"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ActivityGrouping;
UNWIND [{uid:"ActivityInstance_003841", properties:{}}, {uid:"ActivityInstance_003842", properties:{}}, {uid:"ActivityInstance_003843", properties:{}}, {uid:"ActivityInstance_003844", properties:{}}, {uid:"ActivityInstance_003845", properties:{}}] AS row
CREATE (n:ConceptRoot{uid: row.uid}) SET n += row.properties SET n:ActivityInstanceRoot:TemplateParameterTermRoot;
UNWIND [{uid:"Activity_006193", properties:{}}, {uid:"Activity_004092", properties:{}}, {uid:"Activity_006192", properties:{}}, {uid:"Activity_006196", properties:{}}] AS row
CREATE (n:ActivityRoot{uid: row.uid}) SET n += row.properties SET n:ConceptRoot:TemplateParameterTermRoot;
UNWIND [{_id:3702, properties:{synonyms:[], is_request_rejected:false, name:"Erythrocyte Mean Corpuscular Haemoglobin", name_sentence_case:"erythrocyte mean corpuscular haemoglobin", is_request_final:false, is_data_collected:true, is_multiple_selection_allowed:true}}, {_id:3704, properties:{synonyms:[], name:"REDACTED", is_request_rejected:false, name_sentence_case:"REDACTED", is_request_final:false, is_data_collected:true, is_multiple_selection_allowed:true}}, {_id:3699, properties:{synonyms:[], name:"CDR132L B/Placebo", is_request_rejected:false, name_sentence_case:"cdr132l b/placebo", is_request_final:false, is_data_collected:true, is_multiple_selection_allowed:true}}, {_id:8518, properties:{synonyms:[], name:"EQ-5D-Y-3L", is_request_rejected:false, name_sentence_case:"eq-5d-y-3l", is_request_final:false, is_data_collected:true, is_multiple_selection_allowed:true}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:ActivityValue:TemplateParameterTermValue;
UNWIND [{start: {uid:"ActivitySubGroup_000058"}, end: {_id:852603}, properties:{}}, {start: {uid:"ActivitySubGroup_000332"}, end: {_id:1023822}, properties:{}}, {start: {uid:"ActivitySubGroup_000472"}, end: {_id:8506}, properties:{}}, {start: {uid:"ActivitySubGroup_000006"}, end: {_id:852499}, properties:{}}] AS row
MATCH (start:ActivitySubGroupRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_DRAFT]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivitySubGroup_000058"}, end: {_id:852603}, properties:{}}, {start: {uid:"ActivitySubGroup_000332"}, end: {_id:1023822}, properties:{}}, {start: {uid:"ActivitySubGroup_000472"}, end: {_id:8506}, properties:{}}, {start: {uid:"ActivitySubGroup_000006"}, end: {_id:852499}, properties:{}}] AS row
MATCH (start:ActivitySubGroupRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivityGroup_000004"}, end: {_id:852484}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000002", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:42:41.998024Z')}}, {start: {uid:"ActivityGroup_000003"}, end: {_id:852482}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000002", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:42:41.835062Z')}}, {start: {uid:"ActivityGroup_000003"}, end: {_id:852482}, properties:{end_date:datetime('2022-09-21T19:42:41.835062Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000002", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:42:40.794748Z')}}, {start: {uid:"ActivityGroup_000096"}, end: {_id:1023809}, properties:{end_date:datetime('2024-02-18T14:38:26.573031Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000007", version:"0.1", status:"Draft", start_date:datetime('2024-02-18T14:38:25.705223Z')}}, {start: {uid:"ActivityGroup_000096"}, end: {_id:1023809}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000007", version:"1.0", status:"Final", start_date:datetime('2024-02-18T14:38:26.573031Z')}}, {start: {uid:"ActivityGroup_000004"}, end: {_id:852484}, properties:{end_date:datetime('2022-09-21T19:42:41.998024Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000002", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:42:40.822357Z')}}] AS row
MATCH (start:ActivityGroupRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {_id:3798}, end: {_id:3705}, properties:{}}, {start: {_id:3797}, end: {_id:3703}, properties:{}}, {start: {_id:3800}, end: {_id:3700}, properties:{}}, {start: {_id:8588}, end: {_id:8519}, properties:{}}, {start: {_id:8587}, end: {_id:8519}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_ACTIVITY]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivityGroup_000003"}, end: {_id:852482}, properties:{}}, {start: {uid:"ActivityGroup_000004"}, end: {_id:852484}, properties:{}}, {start: {uid:"ActivityGroup_000096"}, end: {_id:1023809}, properties:{}}] AS row
MATCH (start:ActivityGroupRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivityGroup_000003"}, end: {_id:852482}, properties:{}}, {start: {uid:"ActivityGroup_000096"}, end: {_id:1023809}, properties:{}}, {start: {uid:"ActivityGroup_000004"}, end: {_id:852484}, properties:{}}] AS row
MATCH (start:ActivityGroupRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {_id:8519}, end: {_id:852484}, properties:{}}, {start: {_id:3700}, end: {_id:1023809}, properties:{}}, {start: {_id:3705}, end: {_id:852482}, properties:{}}, {start: {_id:3703}, end: {_id:852482}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_SELECTED_GROUP]->(end) SET r += row.properties;
UNWIND [{start: {uid:"Activity_006192"}, end: {_id:3699}, properties:{}}, {start: {uid:"Activity_006193"}, end: {_id:3702}, properties:{}}, {start: {uid:"Activity_004092"}, end: {_id:3704}, properties:{}}, {start: {uid:"Activity_006196"}, end: {_id:8518}, properties:{}}] AS row
MATCH (start:ActivityRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivitySubGroup_000058"}, end: {_id:852603}, properties:{}}, {start: {uid:"ActivitySubGroup_000472"}, end: {_id:8506}, properties:{}}, {start: {uid:"ActivitySubGroup_000332"}, end: {_id:1023822}, properties:{}}, {start: {uid:"ActivitySubGroup_000006"}, end: {_id:852499}, properties:{}}] AS row
MATCH (start:ActivitySubGroupRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivityInstance_003845"}, end: {_id:8588}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000007", version:"1.0", status:"Final", start_date:datetime('2025-11-07T17:45:48.34592Z')}}, {start: {uid:"ActivityInstance_003843"}, end: {_id:3800}, properties:{end_date:datetime('2025-10-31T15:33:50.392545Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000007", version:"0.1", status:"Draft", start_date:datetime('2025-10-31T15:33:47.62683Z')}}, {start: {uid:"ActivityInstance_003842"}, end: {_id:3798}, properties:{end_date:datetime('2025-10-31T15:33:50.527469Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000007", version:"0.1", status:"Draft", start_date:datetime('2025-10-31T15:33:47.623806Z')}}, {start: {uid:"ActivityInstance_003841"}, end: {_id:3797}, properties:{end_date:datetime('2025-10-31T15:33:50.578728Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000007", version:"0.1", status:"Draft", start_date:datetime('2025-10-31T15:33:47.62564Z')}}, {start: {uid:"ActivityInstance_003843"}, end: {_id:3800}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000007", version:"1.0", status:"Final", start_date:datetime('2025-10-31T15:33:50.392545Z')}}, {start: {uid:"ActivityInstance_003841"}, end: {_id:3797}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000007", version:"1.0", status:"Final", start_date:datetime('2025-10-31T15:33:50.578728Z')}}, {start: {uid:"ActivityInstance_003842"}, end: {_id:3798}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000007", version:"1.0", status:"Final", start_date:datetime('2025-10-31T15:33:50.527469Z')}}, {start: {uid:"ActivityInstance_003845"}, end: {_id:8588}, properties:{end_date:datetime('2025-11-07T17:45:48.34592Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000007", version:"0.1", status:"Draft", start_date:datetime('2025-11-07T17:45:45.442978Z')}}, {start: {uid:"ActivityInstance_003844"}, end: {_id:8587}, properties:{end_date:datetime('2025-11-07T17:45:48.163712Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000007", version:"0.1", status:"Draft", start_date:datetime('2025-11-07T17:45:45.413226Z')}}, {start: {uid:"ActivityInstance_003844"}, end: {_id:8587}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000007", version:"1.0", status:"Final", start_date:datetime('2025-11-07T17:45:48.163712Z')}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {_id:3699}, end: {_id:3700}, properties:{}}, {start: {_id:3702}, end: {_id:3703}, properties:{}}, {start: {_id:3704}, end: {_id:3705}, properties:{}}, {start: {_id:8518}, end: {_id:8519}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_GROUPING]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivityInstance_003843"}, end: {_id:3800}, properties:{}}, {start: {uid:"ActivityInstance_003842"}, end: {_id:3798}, properties:{}}, {start: {uid:"ActivityInstance_003841"}, end: {_id:3797}, properties:{}}, {start: {uid:"ActivityInstance_003844"}, end: {_id:8587}, properties:{}}, {start: {uid:"ActivityInstance_003845"}, end: {_id:8588}, properties:{}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:8519}, end: {_id:8506}, properties:{}}, {start: {_id:3700}, end: {_id:1023822}, properties:{}}, {start: {_id:3705}, end: {_id:852499}, properties:{}}, {start: {_id:3703}, end: {_id:852603}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_SELECTED_SUBGROUP]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivityGroup_000096"}, end: {_id:1023809}, properties:{}}, {start: {uid:"ActivityGroup_000003"}, end: {_id:852482}, properties:{}}, {start: {uid:"ActivityGroup_000004"}, end: {_id:852484}, properties:{}}] AS row
MATCH (start:ActivityGroupRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_DRAFT]->(end) SET r += row.properties;
UNWIND [{start: {uid:"Activity_006192"}, end: {_id:3699}, properties:{}}, {start: {uid:"Activity_006193"}, end: {_id:3702}, properties:{}}, {start: {uid:"Activity_004092"}, end: {_id:3704}, properties:{}}, {start: {uid:"Activity_006196"}, end: {_id:8518}, properties:{}}] AS row
MATCH (start:ActivityRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_DRAFT]->(end) SET r += row.properties;
UNWIND [{start: {uid:"Activity_006192"}, end: {_id:3699}, properties:{}}, {start: {uid:"Activity_006193"}, end: {_id:3702}, properties:{}}, {start: {uid:"Activity_004092"}, end: {_id:3704}, properties:{}}, {start: {uid:"Activity_006196"}, end: {_id:8518}, properties:{}}] AS row
MATCH (start:ActivityRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivityInstance_003843"}, end: {_id:3800}, properties:{}}, {start: {uid:"ActivityInstance_003842"}, end: {_id:3798}, properties:{}}, {start: {uid:"ActivityInstance_003841"}, end: {_id:3797}, properties:{}}, {start: {uid:"ActivityInstance_003844"}, end: {_id:8587}, properties:{}}, {start: {uid:"ActivityInstance_003845"}, end: {_id:8588}, properties:{}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_DRAFT]->(end) SET r += row.properties;
UNWIND [{start: {uid:"Activity_006192"}, end: {_id:3699}, properties:{end_date:datetime('2025-10-31T14:29:51.982795Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000007", version:"0.1", status:"Draft", start_date:datetime('2025-10-31T14:29:51.261063Z')}}, {start: {uid:"Activity_006193"}, end: {_id:3702}, properties:{end_date:datetime('2025-10-31T14:29:52.088616Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000007", version:"0.1", status:"Draft", start_date:datetime('2025-10-31T14:29:51.262767Z')}}, {start: {uid:"Activity_006192"}, end: {_id:3699}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000007", version:"1.0", status:"Final", start_date:datetime('2025-10-31T14:29:51.982795Z')}}, {start: {uid:"Activity_006193"}, end: {_id:3702}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000007", version:"1.0", status:"Final", start_date:datetime('2025-10-31T14:29:52.088616Z')}}, {start: {uid:"Activity_004092"}, end: {_id:3704}, properties:{end_date:datetime('2025-10-31T14:29:52.764025Z'), change_description:"Migration modification", author_id:"00000000-0000-0000-0000-000000000007", version:"1.2", status:"Draft", start_date:datetime('2025-10-31T14:29:52.058291Z')}}, {start: {uid:"Activity_004092"}, end: {_id:3704}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000007", version:"2.0", status:"Final", start_date:datetime('2025-10-31T14:29:52.764025Z')}}, {start: {uid:"Activity_006196"}, end: {_id:8518}, properties:{end_date:datetime('2025-11-07T16:26:48.558916Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000007", version:"0.1", status:"Draft", start_date:datetime('2025-11-07T16:26:47.6983Z')}}, {start: {uid:"Activity_006196"}, end: {_id:8518}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000007", version:"1.0", status:"Final", start_date:datetime('2025-11-07T16:26:48.558916Z')}}] AS row
MATCH (start:ActivityRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivityInstance_003845"}, end: {_id:8588}, properties:{}}, {start: {uid:"ActivityInstance_003843"}, end: {_id:3800}, properties:{}}, {start: {uid:"ActivityInstance_003841"}, end: {_id:3797}, properties:{}}, {start: {uid:"ActivityInstance_003842"}, end: {_id:3798}, properties:{}}, {start: {uid:"ActivityInstance_003844"}, end: {_id:8587}, properties:{}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivitySubGroup_000006"}, end: {_id:852499}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000002", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:42:46.445865Z')}}, {start: {uid:"ActivitySubGroup_000058"}, end: {_id:852603}, properties:{end_date:datetime('2022-09-21T19:42:54.984586Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000002", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:42:53.958424Z')}}, {start: {uid:"ActivitySubGroup_000058"}, end: {_id:852603}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000002", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:42:54.984586Z')}}, {start: {uid:"ActivitySubGroup_000332"}, end: {_id:1023822}, properties:{end_date:datetime('2024-02-18T14:38:36.488775Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000007", version:"0.1", status:"Draft", start_date:datetime('2024-02-18T14:38:33.287921Z')}}, {start: {uid:"ActivitySubGroup_000472"}, end: {_id:8506}, properties:{end_date:datetime('2025-11-07T16:23:09.302188Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000007", version:"0.1", status:"Draft", start_date:datetime('2025-11-07T16:23:08.457551Z')}}, {start: {uid:"ActivitySubGroup_000472"}, end: {_id:8506}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000007", version:"1.0", status:"Final", start_date:datetime('2025-11-07T16:23:09.302188Z')}}, {start: {uid:"ActivitySubGroup_000332"}, end: {_id:1023822}, properties:{change_description:"Approved version", author_id:"00000000-0000-0000-0000-000000000007", version:"1.0", status:"Final", start_date:datetime('2024-02-18T14:38:36.488775Z')}}, {start: {uid:"ActivitySubGroup_000006"}, end: {_id:852499}, properties:{end_date:datetime('2022-09-21T19:42:46.445865Z'), change_description:"Initial version", author_id:"00000000-0000-0000-0000-000000000002", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:42:44.122139Z')}}] AS row
MATCH (start:ActivitySubGroupRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
DROP CONSTRAINT UNIQUE_IMPORT_NAME;
"""

TEST_DATA = FEATURE_FLAGS + INSTANCES_BEFORE_SPLIT
