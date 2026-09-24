# with " match (a:DatasetScenario)
#  match (b:StudyStandardVersion)
#  match (c:DatasetScenarioInstance)
#   return * limit 1000
#  " AS query
#  CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll",ifNotExists: true})
#  YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
#  RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;


MIGRATED_INDEXES = """
CREATE RANGE INDEX IF NOT EXISTS FOR (n:DatasetScenario) ON (n.uid);
CREATE RANGE INDEX IF NOT EXISTS FOR (n:StudySelection) ON (n.uid);
CREATE RANGE INDEX IF NOT EXISTS FOR (n:StudyStandardVersion) ON (n.uid);
CREATE TEXT INDEX IF NOT EXISTS FOR (n:DatasetScenarioInstance) ON (n.label);
CREATE CONSTRAINT UNIQUE_IMPORT_NAME IF NOT EXISTS FOR (node:`UNIQUE IMPORT LABEL`) REQUIRE (node.`UNIQUE IMPORT ID`) IS UNIQUE;
UNWIND [{_id:151447, properties:{uid:"PK__Sample__Collection__at__Fixed__Time__Points"}}, {_id:151448, properties:{uid:"PK__Sample__Collection__over__a__Time__Interval"}}, {_id:151449, properties:{uid:"Scenario__3__colon____Central__Processing__with__Investigator__Assessment__of__Clinical__Significance__Assessment__for__Abnormal__Values"}}, {_id:151450, properties:{uid:"Scenario__2__colon____Local__Processing"}}, {_id:151451, properties:{uid:"Scenario__1__colon____Central__Processing"}}, {_id:151452, properties:{uid:"PE__Traditional__Scenario"}}, {_id:151453, properties:{uid:"SR__-__Implementation__Options__colon____Horizontal-Generic"}}, {_id:151454, properties:{uid:"SR__-__Denormalized__-__Implementation__Options__colon____Horizontal-Example"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:DatasetScenario;
UNWIND [{_id:151493, properties:{label:"PK Sample Collection at Fixed Time Points"}}, {_id:151494, properties:{label:"PK Sample Collection over a Time Interval"}}, {_id:151495, properties:{label:"Scenario 3: Central Processing with Investigator Assessment of Clinical Significance Assessment for Abnormal Values"}}, {_id:151496, properties:{label:"Scenario 2: Local Processing"}}, {_id:151497, properties:{label:"Scenario 1: Central Processing"}}, {_id:151498, properties:{label:"PE Traditional Scenario"}}, {_id:151499, properties:{label:"SR - Implementation Options: Horizontal-Generic"}}, {_id:151500, properties:{label:"SR - Denormalized - Implementation Options: Horizontal-Example"}}, {_id:151501, properties:{label:"DD - Implementation Options: Horizontal-Generic"}}, {_id:151502, properties:{label:"DD - Denormalized - Implementation Options: Horizontal-Example"}}, {_id:151503, properties:{label:"VS - Implementation Options: Horizontal-Generic"}}, {_id:151504, properties:{label:"VS - Denormalized - Implementation Options: Horizontal-Example"}}, {_id:151505, properties:{label:"SC - Denormalized - Implementation Options: Horizontal-Example"}}, {_id:151506, properties:{label:"SC - Implementation Options: Horizontal-Generic"}}, {_id:151507, properties:{label:"Scenario 1: Central Reading"}}, {_id:151508, properties:{label:"Scenario 3: Central Reading with Investigator Assessment of Clinical Significance Assessment and/or Overall Interpretation"}}, {_id:151509, properties:{label:"Scenario 2: Local Reading"}}, {_id:151510, properties:{label:"DA - Implementation Options: Horizontal-Generic"}}, {_id:151511, properties:{label:"DA - Denormalized - Implementation Options: Horizontal-Example"}}, {_id:152465, properties:{label:"VS - Implementation Options: HorizontalGeneric"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:DatasetScenarioInstance;
UNWIND [{_id:152466, properties:{label:"Local Processing"}}, {_id:152467, properties:{label:"Central Processing"}}, {_id:152468, properties:{label:"PE-Traditional"}}, {_id:152469, properties:{label:"SC - Implementation Options: HorizontalGeneric"}}, {_id:152470, properties:{label:"DD - Implementation Options: HorizontalGeneric"}}, {_id:152471, properties:{label:"DA - Implementation Options: HorizontalGeneric"}}, {_id:152472, properties:{label:"Central Processing with CS"}}, {_id:152473, properties:{label:"Local Reading"}}, {_id:152474, properties:{label:"Central Reading with Investigator Assessment"}}, {_id:152475, properties:{label:"Central Reading"}}, {_id:153507, properties:{label:"DA - Implementation Options: HorizontalGeneric"}}, {_id:153508, properties:{label:"DD - Implementation Options: HorizontalGeneric"}}, {_id:153509, properties:{label:"VS - Implementation Options: HorizontalGeneric"}}, {_id:153510, properties:{label:"STUDY PARTICIPATION DISPOSITION EVENT"}}, {_id:153511, properties:{label:"PROTOCOL MILESTONE/OTHER EVENT"}}, {_id:153512, properties:{label:"Birth date collection using a single date field"}}, {_id:153513, properties:{label:"Birth date collection using three date fields"}}, {_id:153514, properties:{label:"SC - Implementation Options: HorizontalGeneric"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:DatasetScenarioInstance;
UNWIND [{_id:227107, properties:{uid:"StudyStandardVersion_000001", description:"A StudyStandardVersion is automatically created whenever the study is locked.The StudyStandardVersion has been generated using the latest CTPackage available, with the unique ID 'SDTM CT 2021-06-25'. Additionally, a Sponsor CTPackage was created with today's date as the effective date.", automatically_created:true, status:"DRAFT"}}, {_id:227120, properties:{uid:"StudyStandardVersion_000001", description:"A StudyStandardVersion is automatically created whenever the study is locked.The StudyStandardVersion has been generated using the latest CTPackage available, with the unique ID 'SDTM CT 2021-06-25'. Additionally, a Sponsor CTPackage was created with today's date as the effective date.", automatically_created:true, status:"DRAFT"}}, {_id:233618, properties:{uid:"StudyStandardVersion_000002", description:"Testing Data Standards", automatically_created:false, status:"DRAFT"}}, {_id:234013, properties:{uid:"StudyStandardVersion_000003", description:"controlled terminology (CT) fot study ANOVA360", automatically_created:false, status:"DRAFT"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:StudyStandardVersion:StudySelection;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
"""


# with "
#   MATCH (air:ActivityInstanceRoot)-[aihv:LATEST]-(aiv:ActivityInstanceValue)-[aiha:HAS_ACTIVITY]-(agrp:ActivityGrouping)-[hg:HAS_GROUPING]-(av:ActivityValue)-[ahv:LATEST]-(ar:ActivityRoot)
#   WITH * LIMIT 5
#   MATCH (agrp)-[isg:IN_SUBGROUP]-(avg:ActivityValidGroup)
#   MATCH (avg)-[ig:IN_GROUP]-(agv:ActivityGroupValue)-[aghv:LATEST]-(agr:ActivityGroupRoot)
#   MATCH (avg)-[avghg:HAS_GROUP]-(asgv:ActivitySubGroupValue)-[asghv:LATEST]-(asgr:ActivitySubGroupRoot)
#   RETURN *
# " AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll",ifNotExists: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;
ACTIVITY_GROUPING = """
CREATE RANGE INDEX IF NOT EXISTS FOR (n:ActivityGroupValue) ON (n.name);
CREATE RANGE INDEX IF NOT EXISTS FOR (n:ActivityGrouping) ON (n.uid);
CREATE RANGE INDEX IF NOT EXISTS FOR (n:ActivityInstanceValue) ON (n.name);
CREATE RANGE INDEX IF NOT EXISTS FOR (n:ActivitySubGroupValue) ON (n.name);
CREATE RANGE INDEX IF NOT EXISTS FOR (n:ActivityValidGroup) ON (n.uid);
CREATE RANGE INDEX IF NOT EXISTS FOR (n:ActivityValue) ON (n.name);
CREATE RANGE INDEX IF NOT EXISTS FOR (n:ConceptValue) ON (n.name);
CREATE RANGE INDEX IF NOT EXISTS FOR (n:TemplateParameterTermValue) ON (n.name);
CREATE CONSTRAINT constraint_ActivityGroupRoot_uid IF NOT EXISTS FOR (node:ActivityGroupRoot) REQUIRE (node.uid) IS NODE KEY;
CREATE CONSTRAINT constraint_ActivitySubGroupRoot_uid IF NOT EXISTS FOR (node:ActivitySubGroupRoot) REQUIRE (node.uid) IS NODE KEY;
CREATE CONSTRAINT constraint_ActivityRoot_uid IF NOT EXISTS FOR (node:ActivityRoot) REQUIRE (node.uid) IS NODE KEY;
CREATE CONSTRAINT constraint_ConceptRoot_uid IF NOT EXISTS FOR (node:ConceptRoot) REQUIRE (node.uid) IS NODE KEY;
CREATE CONSTRAINT constraint_ActivityInstanceRoot_uid IF NOT EXISTS FOR (node:ActivityInstanceRoot) REQUIRE (node.uid) IS NODE KEY;
CREATE CONSTRAINT constraint_TemplateParameterTermRoot_uid IF NOT EXISTS FOR (node:TemplateParameterTermRoot) REQUIRE (node.uid) IS NODE KEY;
CREATE CONSTRAINT UNIQUE_IMPORT_NAME IF NOT EXISTS FOR (node:`UNIQUE IMPORT LABEL`) REQUIRE (node.`UNIQUE IMPORT ID`) IS UNIQUE;
UNWIND [{_id:2131345, properties:{topic_code:"SF36V2_ACT_2_GENERAL_HEALTH_ONE_WEEK_AGO", is_derived:false, adam_param_code:"SF36402", name:"SF-36 v2.0 Acute - Comp Week Ago Rate Gen Health Now", name_sentence_case:"sf-36 v2.0 acute - comp week ago rate gen health now", is_default_selected_for_activity:false, is_data_sharing:true, is_required_for_activity:true, legacy_description:"The Short Form 36 Health Survey Acute, US Version 2.0 (SF36 v2.0 Acute)\n2. Compared to one week ago, how would you rate your health in general now?", is_legacy_usage:false, is_research_lab:false}}, {_id:2131346, properties:{topic_code:"SF36V2_ACT_11A_GH_TRUE_FALSE_SICK_EASIER", is_derived:false, adam_param_code:"SF36411A", name:"SF-36 v2.0 Acute - Get Sick Little Easier than Other", name_sentence_case:"sf-36 v2.0 acute - get sick little easier than other", is_default_selected_for_activity:false, is_data_sharing:true, is_required_for_activity:true, legacy_description:"The Short Form 36 Health Survey Acute, US Version 2.0 (SF36 v2.0 Acute)\n11a. I seem to get sick a little\neasier than other people", is_legacy_usage:false, is_research_lab:false}}, {_id:2131347, properties:{topic_code:"SF36V2_ACT_11B_GH_TRUE_FALSE_AS_HEALTHY", is_derived:false, adam_param_code:"SF36411B", name:"SF-36 v2.0 Acute - I Am as Healthy as Anybody I Know", name_sentence_case:"sf-36 v2.0 acute - i am as healthy as anybody i know", is_default_selected_for_activity:false, is_data_sharing:true, is_required_for_activity:true, legacy_description:"The Short Form 36 Health Survey Acute, US Version 2.0 (SF36 v2.0 Acute)\n11b. I am as healthy as anybody I know", is_legacy_usage:false, is_research_lab:false}}, {_id:2131348, properties:{topic_code:"SF36V2_ACT_11C_GH_TRUE_FALSE_HEALTH_TO_GET_WORSE", is_derived:false, adam_param_code:"SF36411C", name:"SF-36 v2.0 Acute - I Expect My Health to Get Worse", name_sentence_case:"sf-36 v2.0 acute - i expect my health to get worse", is_default_selected_for_activity:false, is_data_sharing:true, is_required_for_activity:true, legacy_description:"The Short Form 36 Health Survey Acute, US Version 2.0 (SF36 v2.0 Acute)\n11c. I expect my health to \nget worse", is_legacy_usage:false, is_research_lab:false}}, {_id:2131349, properties:{topic_code:"SF36V2_ACT_10_SF_P1W_SOCIAL_TIME", is_derived:false, adam_param_code:"SF36410", name:"SF-36 v2.0 Acute - Time Phys/Emotional Interfered", name_sentence_case:"sf-36 v2.0 acute - time phys/emotional interfered", is_default_selected_for_activity:false, is_data_sharing:true, is_required_for_activity:true, legacy_description:"The Short Form 36 Health Survey Acute, US Version 2.0 (SF36 v2.0 Acute)\n10. During the past week, how much of the time has your physical health or emotional problems interfered with your social activities (like visiting with friends, relatives, etc.)?", is_research_lab:false, is_legacy_usage:false}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:ActivityInstanceValue:TemplateParameterTermValue;
UNWIND [{uid:"ActivityGroup_000004", properties:{}}] AS row
MERGE (n:ActivityGroupRoot{uid: row.uid}) SET n += row.properties SET n:ConceptRoot:TemplateParameterTermRoot;
UNWIND [{uid:"ActivitySubGroup_000278", properties:{}}] AS row
MERGE (n:ActivitySubGroupRoot{uid: row.uid}) SET n += row.properties SET n:ConceptRoot:TemplateParameterTermRoot;
UNWIND [{_id:1019360, properties:{name:"Patient-Reported Outcome", name_sentence_case:"patient-reported outcome"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:ActivitySubGroupValue:TemplateParameterTermValue;
UNWIND [{_id:852504, properties:{name:"Clinical Outcome Assessments", name_sentence_case:"clinical outcome assessments", definition:"Definition not provided"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:TemplateParameterTermValue:ActivityGroupValue;
UNWIND [{_id:2127227, properties:{uid:"ActivityGrouping_011820"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ActivityGrouping;
UNWIND [{uid:"CategoricFinding_000001", properties:{}}, {uid:"CategoricFinding_000002", properties:{}}, {uid:"CategoricFinding_000003", properties:{}}, {uid:"CategoricFinding_000004", properties:{}}, {uid:"CategoricFinding_000005", properties:{}}] AS row
MERGE (n:ConceptRoot{uid: row.uid}) SET n += row.properties SET n:ActivityInstanceRoot:TemplateParameterTermRoot;
UNWIND [{_id:1019331, properties:{uid:"ActivityValidGroup_000381"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ActivityValidGroup;
UNWIND [{uid:"Activity_003228", properties:{}}] AS row
MERGE (n:ActivityRoot{uid: row.uid}) SET n += row.properties SET n:ConceptRoot:TemplateParameterTermRoot;
UNWIND [{_id:2127786, properties:{synonyms:[], nci_concept_id:"C101880", name:"SF36 Health Survey Acute V2.0", is_request_rejected:false, name_sentence_case:"sf36 health survey acute v2.0", definition:"A question associated with the SF36 v2.0 Acute questionnaire.", is_request_final:false, is_data_collected:true, is_multiple_selection_allowed:true}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:ActivityValue:TemplateParameterTermValue;
UNWIND [{start: {_id:2127227}, end: {_id:1019331}, properties:{`UNIQUE IMPORT ID REL`:2429561}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:IN_SUBGROUP]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivitySubGroup_000278"}, end: {_id:1019360}, properties:{`UNIQUE IMPORT ID REL`:2756156}}] AS row
MATCH (start:ActivitySubGroupRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {uid:"Activity_003228"}, end: {_id:2127786}, properties:{`UNIQUE IMPORT ID REL`:2188219}}] AS row
MATCH (start:ActivityRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:2131348}, end: {_id:2127227}, properties:{`UNIQUE IMPORT ID REL`:5375826}}, {start: {_id:2131347}, end: {_id:2127227}, properties:{`UNIQUE IMPORT ID REL`:5375855}}, {start: {_id:2131346}, end: {_id:2127227}, properties:{`UNIQUE IMPORT ID REL`:5375864}}, {start: {_id:2131349}, end: {_id:2127227}, properties:{`UNIQUE IMPORT ID REL`:7934692}}, {start: {_id:2131345}, end: {_id:2127227}, properties:{`UNIQUE IMPORT ID REL`:8903562}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_ACTIVITY]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivityGroup_000004"}, end: {_id:852504}, properties:{`UNIQUE IMPORT ID REL`:2100594}}] AS row
MATCH (start:ActivityGroupRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:1019360}, end: {_id:1019331}, properties:{`UNIQUE IMPORT ID REL`:2714826}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_GROUP]->(end) SET r += row.properties;
UNWIND [{start: {_id:1019331}, end: {_id:852504}, properties:{`UNIQUE IMPORT ID REL`:2714825}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:IN_GROUP]->(end) SET r += row.properties;
UNWIND [{start: {_id:2127786}, end: {_id:2127227}, properties:{`UNIQUE IMPORT ID REL`:2386459}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_GROUPING]->(end) SET r += row.properties;
UNWIND [{start: {uid:"CategoricFinding_000005"}, end: {_id:2131345}, properties:{`UNIQUE IMPORT ID REL`:8904525}}, {start: {uid:"CategoricFinding_000004"}, end: {_id:2131346}, properties:{`UNIQUE IMPORT ID REL`:8904536}}, {start: {uid:"CategoricFinding_000003"}, end: {_id:2131347}, properties:{`UNIQUE IMPORT ID REL`:8904547}}, {start: {uid:"CategoricFinding_000002"}, end: {_id:2131348}, properties:{`UNIQUE IMPORT ID REL`:8904557}}, {start: {uid:"CategoricFinding_000001"}, end: {_id:2131349}, properties:{`UNIQUE IMPORT ID REL`:8904568}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
DROP CONSTRAINT UNIQUE_IMPORT_NAME;
"""

TEST_DATA = "\n".join(
    [
        MIGRATED_INDEXES,
        ACTIVITY_GROUPING,
    ]
)
