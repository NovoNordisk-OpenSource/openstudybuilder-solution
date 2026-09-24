ACTIVITY_000317_VERSIONING_GAP = """
// Test data for Bug #3221548: Activity_000317 versioning gap between version 7.0 and 7.1
// Create ActivityRoot for Activity_000317
CREATE (ar:ActivityRoot:ConceptRoot {uid: "Activity_000317", name: "Physical Examination"}),
       (av70:ActivityValue:ConceptValue {
           uid: "ActivityValue_000317_v7_0",
           name: "Physical Examination",
           version: "7.0"
       }),
       (av71:ActivityValue:ConceptValue {
           uid: "ActivityValue_000317_v7_1",
           name: "Physical Examination",
           version: "7.1"
       })

// Create HAS_VERSION relationships with the versioning gap
// Version 7.0 ends on 2024-11-14, but version 7.1 doesn't start until 2024-12-20
CREATE (ar)-[:HAS_VERSION {
    version: "7.0",
    start_date: datetime("2024-10-01T10:00:00.000000Z"),
    end_date: datetime("2024-11-14T15:20:11.139020Z")
}]->(av70)

CREATE (ar)-[:HAS_VERSION {
    version: "7.1",
    start_date: datetime("2024-12-20T12:41:58.289320Z"),
    end_date: null
}]->(av71)

// Add LATEST relationship to current version
CREATE (ar)-[:LATEST]->(av71);
"""

# Submission values with unwanted suffixes in category codelists
# Query
# WITH "
# MATCH (clr:CTCodelistRoot)-[har:HAS_ATTRIBUTES_ROOT]-(clar:CTCodelistAttributesRoot)-[clalat:LATEST]-(clav:CTCodelistAttributesValue)
# WHERE clav.submission_value IN ['EVNTCAT', 'EVNTSCAT', 'FINDCAT', 'FINDSCAT', 'INTVCAT', 'INTVSCAT']
# CALL {
#     WITH clr
#     MATCH (clr)-[ht:HAS_TERM]->(clt:CTCodelistTerm)
#     WITH clt, ht LIMIT 10
#     RETURN clt, ht
# }
# RETURN *
# " as query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll"})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements;

CATEGORY_CODELIST_TERMS_WITH_SUFFIX = """
CREATE RANGE INDEX FOR (n:CTCodelistAttributesValue) ON (n.code_submission_value);
CREATE RANGE INDEX FOR (n:CTCodelistAttributesValue) ON (n.concept_id);
CREATE RANGE INDEX FOR (n:CTCodelistAttributesValue) ON (n.name);
CREATE RANGE INDEX FOR (n:CTCodelistAttributesValue) ON (n.submission_value);
CREATE RANGE INDEX FOR (n:CTCodelistTerm) ON (n.submission_value);
CREATE CONSTRAINT constraint_CTCodelistRoot_uid FOR (node:CTCodelistRoot) REQUIRE (node.uid) IS NODE KEY;
CREATE CONSTRAINT UNIQUE_IMPORT_NAME FOR (node:`UNIQUE IMPORT LABEL`) REQUIRE (node.`UNIQUE IMPORT ID`) IS UNIQUE;
UNWIND [{_id:25000, properties:{}}, {_id:25001, properties:{}}, {_id:25002, properties:{}}, {_id:25003, properties:{}}, {_id:25004, properties:{}}, {_id:25005, properties:{}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistAttributesRoot;
UNWIND [{_id:25201, properties:{preferred_term:"Finding Category Definition", name:"Finding Category Definition", definition:"Finding Category Definition", extensible:true, submission_value:"FINDCAT"}}, {_id:25202, properties:{preferred_term:"Intervention Category Definition", name:"Intervention Category Definition", definition:"Intervention Category Definition", extensible:true, submission_value:"INTVCAT"}}, {_id:25203, properties:{preferred_term:"Finding Subcategory Definition", name:"Finding Subcategory Definition", definition:"Finding Subcategory Definition", extensible:true, submission_value:"FINDSCAT"}}, {_id:25204, properties:{preferred_term:"Event Subcategory Definition", name:"Event Subcategory Definition", definition:"Event Subcategory Definition", extensible:true, submission_value:"EVNTSCAT"}}, {_id:25205, properties:{preferred_term:"Intervention Subcategory Definition", name:"Intervention Subcategory Definition", definition:"Intervention Subcategory Definition", extensible:true, submission_value:"INTVSCAT"}}, {_id:25206, properties:{preferred_term:"Event Category Definition", name:"Event Category Definition", definition:"Event Category Definition", extensible:true, submission_value:"EVNTCAT"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistAttributesValue;
UNWIND [{uid:"CTCodelist_000038", properties:{}}, {uid:"CTCodelist_000039", properties:{}}, {uid:"CTCodelist_000040", properties:{}}, {uid:"CTCodelist_000041", properties:{}}, {uid:"CTCodelist_000042", properties:{}}, {uid:"CTCodelist_000043", properties:{}}] AS row
MERGE (n:CTCodelistRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{_id:3010938, properties:{submission_value:"SHORT-ACTING INTRV_SUB_CAT"}}, {_id:3010939, properties:{submission_value:"KNEE SURGERY INTRV_SUB_CAT"}}, {_id:3010940, properties:{submission_value:"FIRST DOSE AFTER CROSSOVER INTRV_SUB_CAT"}}, {_id:3010941, properties:{submission_value:"BARIATRIC SURGERY INTRV_SUB_CAT"}}, {_id:3010942, properties:{submission_value:"LONG-ACTING INTRV_SUB_CAT"}}, {_id:3010943, properties:{submission_value:"WASHOUT MEDICATION INTRV_CAT"}}, {_id:3010944, properties:{submission_value:"VASO OCCLUSIVE CRISIS INTRV_CAT"}}, {_id:3010947, properties:{submission_value:"SICKLE CELL DISEASE INTRV_CAT"}}, {_id:3010950, properties:{submission_value:"PARKINSONS DISEASE INTRV_CAT"}}, {_id:3010954, properties:{submission_value:"NICOTINE INTRV_CAT"}}, {_id:3010968, properties:{submission_value:"DOSE AS REPORTED AS PART OF HYPO INTRV_CAT"}}, {_id:3010971, properties:{submission_value:"CONCOMITANT MEDICATION INTRV_CAT"}}, {_id:3010972, properties:{submission_value:"CLAMP TERMINATION INTRV_CAT"}}, {_id:3010975, properties:{submission_value:"BLOOD TRANSFUSION INTRV_CAT"}}, {_id:3010976, properties:{submission_value:"ANTI-DIABETIC TREATMENT INTRV_CAT"}}, {_id:3011055, properties:{submission_value:"SCHOOL FUNCTIONING FIND_SUB_CAT"}}, {_id:3011087, properties:{submission_value:"PRESCRIPTION MEDICATION FOR OBESITY FIND_SUB_CAT"}}, {_id:3011098, properties:{submission_value:"PHYSICAL HEALTH FIND_SUB_CAT"}}, {_id:3011138, properties:{submission_value:"NEOPLASM TREATMENT FIND_SUB_CAT"}}, {_id:3011263, properties:{submission_value:"EXPERIENCE FIND_SUB_CAT"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistTerm;
UNWIND [{_id:3011264, properties:{submission_value:"EXAMINATION OF THE PATIENT FIND_SUB_CAT"}}, {_id:3011309, properties:{submission_value:"DEVICE USABILITY 3 FIND_SUB_CAT"}}, {_id:3011330, properties:{submission_value:"COMPREHENSION FIND_SUB_CAT"}}, {_id:3011338, properties:{submission_value:"CHAIN AMYLOIDOSIS EXCLUDED FIND_SUB_CAT"}}, {_id:3011354, properties:{submission_value:"BLEEDS FIND_SUB_CAT"}}, {_id:3011394, properties:{submission_value:"WPAI-GH V2.0 FIND_CAT"}}, {_id:3011419, properties:{submission_value:"TREATING PHYSICIAN PRACTICE AND SPECIALITY FIND_CAT"}}, {_id:3011465, properties:{submission_value:"RISK FACTORS FOR BREAST NEOPLASM FIND_CAT"}}, {_id:3011474, properties:{submission_value:"PUMP_RELATED_DETAILS_AND_ASSESSMENTS FIND_CAT"}}, {_id:3011499, properties:{submission_value:"PHYSICAL EXAMINATION FIND_CAT"}}, {_id:3011529, properties:{submission_value:"PAIN RATING FIND_CAT"}}, {_id:3011534, properties:{submission_value:"NYHA CLASS FIND_CAT"}}, {_id:3011584, properties:{submission_value:"INCLUSION CRITERIA FIND_CAT"}}, {_id:3011641, properties:{submission_value:"EVALUATION OF COMORBIDITIES FIND_CAT"}}, {_id:3011662, properties:{submission_value:"DOSING DAY CRITERIA FIND_CAT"}}, {_id:3011743, properties:{submission_value:"RUN-IN FAILURE EVNT_SUB_CAT"}}, {_id:3011744, properties:{submission_value:"SCREENING FAILURE EVNT_SUB_CAT"}}, {_id:3011745, properties:{submission_value:"PREMATURE DISCONTINUATION OF TRIAL PRODUCT EVNT_SUB_CAT"}}, {_id:3011746, properties:{submission_value:"CONGENITAL EVNT_SUB_CAT"}}, {_id:3011747, properties:{submission_value:"ADVERSE EVENT EVNT_SUB_CAT"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistTerm;
UNWIND [{_id:3011748, properties:{submission_value:"ACQUIRED EVNT_SUB_CAT"}}, {_id:3011749, properties:{submission_value:"PREDISPOSING FACTORS EVNT_SUB_CAT"}}, {_id:3011752, properties:{submission_value:"USE ERROR EVNT_CAT"}}, {_id:3011757, properties:{submission_value:"RISK FACTORS FOR SKIN CANCER EVNT_CAT"}}, {_id:3011759, properties:{submission_value:"RISK FACTORS FOR BREAST NEOPLASM EVNT_CAT"}}, {_id:3011766, properties:{submission_value:"PARKINSONS DISEASE EVNT_CAT"}}, {_id:3011775, properties:{submission_value:"MACROVASCULAR COMPLICATIONS EVNT_CAT"}}, {_id:3011780, properties:{submission_value:"HYPERGLYCAEMIC EPISODES EVNT_CAT"}}, {_id:3011784, properties:{submission_value:"GENE CONSENT EVNT_CAT"}}, {_id:3011792, properties:{submission_value:"DIAGNOSIS OF DIABETES EVNT_CAT"}}, {_id:3011795, properties:{submission_value:"DEVICE USE EVNT_CAT"}}, {_id:3011796, properties:{submission_value:"DEVICE PROBLEMS EVNT_CAT"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistTerm;
UNWIND [{start: {uid:"CTCodelist_000042"}, end: {_id:3010938}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:190, start_date:datetime('2023-06-21T12:50:52.627527Z')}}, {start: {uid:"CTCodelist_000042"}, end: {_id:3010939}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:50:52.50315Z')}}, {start: {uid:"CTCodelist_000042"}, end: {_id:3010940}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:3, start_date:datetime('2023-06-21T12:50:52.405736Z')}}, {start: {uid:"CTCodelist_000042"}, end: {_id:3010941}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:50:52.248904Z')}}, {start: {uid:"CTCodelist_000042"}, end: {_id:3010942}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:125, start_date:datetime('2023-06-21T12:50:52.127424Z')}}, {start: {uid:"CTCodelist_000039"}, end: {_id:3010943}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:50:49.739463Z')}}, {start: {uid:"CTCodelist_000039"}, end: {_id:3010944}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:50:49.596022Z')}}, {start: {uid:"CTCodelist_000039"}, end: {_id:3010947}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:50:49.077673Z')}}, {start: {uid:"CTCodelist_000039"}, end: {_id:3010950}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:50:48.61691Z')}}, {start: {uid:"CTCodelist_000039"}, end: {_id:3010954}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:50:47.957648Z')}}, {start: {uid:"CTCodelist_000039"}, end: {_id:3010968}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:50:45.31633Z')}}, {start: {uid:"CTCodelist_000039"}, end: {_id:3010971}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:34, start_date:datetime('2023-06-21T12:50:44.853865Z')}}, {start: {uid:"CTCodelist_000039"}, end: {_id:3010972}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:50:44.726266Z')}}, {start: {uid:"CTCodelist_000039"}, end: {_id:3010975}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:200, start_date:datetime('2023-06-21T12:50:44.349963Z')}}, {start: {uid:"CTCodelist_000039"}, end: {_id:3010976}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:50:44.228793Z')}}, {start: {uid:"CTCodelist_000040"}, end: {_id:3011055}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:50:27.776383Z')}}, {start: {uid:"CTCodelist_000040"}, end: {_id:3011087}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:3, start_date:datetime('2023-06-21T12:50:21.634532Z')}}, {start: {uid:"CTCodelist_000040"}, end: {_id:3011098}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:50:19.312781Z')}}, {start: {uid:"CTCodelist_000040"}, end: {_id:3011138}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:50:11.513687Z')}}, {start: {uid:"CTCodelist_000040"}, end: {_id:3011263}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:49:44.362687Z')}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {uid:"CTCodelist_000040"}, end: {_id:3011264}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:2, start_date:datetime('2023-06-21T12:49:44.222523Z')}}, {start: {uid:"CTCodelist_000040"}, end: {_id:3011309}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:49:35.844323Z')}}, {start: {uid:"CTCodelist_000040"}, end: {_id:3011330}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:49:31.839391Z')}}, {start: {uid:"CTCodelist_000040"}, end: {_id:3011338}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:49:30.293226Z')}}, {start: {uid:"CTCodelist_000040"}, end: {_id:3011354}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:49:27.156145Z')}}, {start: {uid:"CTCodelist_000038"}, end: {_id:3011394}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:49:18.906553Z')}}, {start: {uid:"CTCodelist_000038"}, end: {_id:3011419}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:49:14.045859Z')}}, {start: {uid:"CTCodelist_000038"}, end: {_id:3011465}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:49:05.673968Z')}}, {start: {uid:"CTCodelist_000038"}, end: {_id:3011474}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:160, start_date:datetime('2023-06-21T12:49:03.677594Z')}}, {start: {uid:"CTCodelist_000038"}, end: {_id:3011499}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1608, start_date:datetime('2023-06-21T12:48:56.930718Z')}}, {start: {uid:"CTCodelist_000038"}, end: {_id:3011529}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:48:51.307222Z')}}, {start: {uid:"CTCodelist_000038"}, end: {_id:3011534}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:48:50.429718Z')}}, {start: {uid:"CTCodelist_000038"}, end: {_id:3011584}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:913, start_date:datetime('2023-06-21T12:48:39.819907Z')}}, {start: {uid:"CTCodelist_000038"}, end: {_id:3011641}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:48:27.924673Z')}}, {start: {uid:"CTCodelist_000038"}, end: {_id:3011662}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:415, start_date:datetime('2023-06-21T12:48:23.968143Z')}}, {start: {uid:"CTCodelist_000041"}, end: {_id:3011743}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:48:08.371261Z')}}, {start: {uid:"CTCodelist_000041"}, end: {_id:3011744}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:48:08.261847Z')}}, {start: {uid:"CTCodelist_000041"}, end: {_id:3011745}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:160, start_date:datetime('2023-06-21T12:48:08.149641Z')}}, {start: {uid:"CTCodelist_000041"}, end: {_id:3011746}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:48:08.049085Z')}}, {start: {uid:"CTCodelist_000041"}, end: {_id:3011747}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:10, start_date:datetime('2023-06-21T12:48:07.939334Z')}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {uid:"CTCodelist_000041"}, end: {_id:3011748}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:48:07.83359Z')}}, {start: {uid:"CTCodelist_000041"}, end: {_id:3011749}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:48:07.736198Z')}}, {start: {uid:"CTCodelist_000043"}, end: {_id:3011752}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:48:05.189657Z')}}, {start: {uid:"CTCodelist_000043"}, end: {_id:3011757}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:3, start_date:datetime('2023-06-21T12:48:04.030441Z')}}, {start: {uid:"CTCodelist_000043"}, end: {_id:3011759}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:48:03.58607Z')}}, {start: {uid:"CTCodelist_000043"}, end: {_id:3011766}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:48:02.325902Z')}}, {start: {uid:"CTCodelist_000043"}, end: {_id:3011775}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:48:00.721064Z')}}, {start: {uid:"CTCodelist_000043"}, end: {_id:3011780}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:81, start_date:datetime('2023-06-21T12:47:59.953686Z')}}, {start: {uid:"CTCodelist_000043"}, end: {_id:3011784}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:72, start_date:datetime('2023-06-21T12:47:59.296709Z')}}, {start: {uid:"CTCodelist_000043"}, end: {_id:3011792}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:45, start_date:datetime('2023-06-21T12:47:57.818808Z')}}, {start: {uid:"CTCodelist_000043"}, end: {_id:3011795}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:1, start_date:datetime('2023-06-21T12:47:57.384097Z')}}, {start: {uid:"CTCodelist_000043"}, end: {_id:3011796}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:10, start_date:datetime('2023-06-21T12:47:57.182656Z')}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {_id:25000}, end: {_id:25201}, properties:{}}, {start: {_id:25001}, end: {_id:25202}, properties:{}}, {start: {_id:25002}, end: {_id:25203}, properties:{}}, {start: {_id:25003}, end: {_id:25204}, properties:{}}, {start: {_id:25004}, end: {_id:25205}, properties:{}}, {start: {_id:25005}, end: {_id:25206}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {uid:"CTCodelist_000038"}, end: {_id:25000}, properties:{}}, {start: {uid:"CTCodelist_000039"}, end: {_id:25001}, properties:{}}, {start: {uid:"CTCodelist_000040"}, end: {_id:25002}, properties:{}}, {start: {uid:"CTCodelist_000041"}, end: {_id:25003}, properties:{}}, {start: {uid:"CTCodelist_000042"}, end: {_id:25004}, properties:{}}, {start: {uid:"CTCodelist_000043"}, end: {_id:25005}, properties:{}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:HAS_ATTRIBUTES_ROOT]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
DROP CONSTRAINT UNIQUE_IMPORT_NAME;
"""


# HAS_VERSIONs with status Retired that are missing a corresponding Final or Draft HAS_VERSION
# Query:
# MATCH (root)-[ret:HAS_VERSION {status: "Retired"}]->(value)
#     WHERE NOT (root)-[:HAS_VERSION {status: "Final"}]->(value) AND NOT (root)-[:HAS_VERSION {status: "Draft"}]->(value)
# WITH root LIMIT 5
# MATCH (root)-[hv:HAS_VERSION]->(any_value)
# WITH
#     collect(DISTINCT root) + collect(DISTINCT any_value) AS importNodes,
#     collect(DISTINCT hv) AS importRels
# CALL apoc.export.cypher.data(importNodes, importRels,
#   NULL,
#   { format: "plain", cypherFormat: "create", stream: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements
MISSING_RETIRED_RELS = """
CREATE RANGE INDEX FOR (n:ActivityInstanceValue) ON (n.name);
CREATE RANGE INDEX FOR (n:ActivityValue) ON (n.name);
CREATE RANGE INDEX FOR (n:ConceptValue) ON (n.name);
CREATE RANGE INDEX FOR (n:TemplateParameterTermValue) ON (n.name);
CREATE CONSTRAINT constraint_ActivityInstanceRoot_uid FOR (node:ActivityInstanceRoot) REQUIRE (node.uid) IS NODE KEY;
CREATE CONSTRAINT constraint_ActivityRoot_uid FOR (node:ActivityRoot) REQUIRE (node.uid) IS NODE KEY;
CREATE CONSTRAINT constraint_ConceptRoot_uid FOR (node:ConceptRoot) REQUIRE (node.uid) IS NODE KEY;
CREATE CONSTRAINT constraint_TemplateParameterTermRoot_uid FOR (node:TemplateParameterTermRoot) REQUIRE (node.uid) IS NODE KEY;
CREATE CONSTRAINT UNIQUE_IMPORT_NAME FOR (node:`UNIQUE IMPORT LABEL`) REQUIRE (node.`UNIQUE IMPORT ID`) IS UNIQUE;
UNWIND [{_id:1049688, properties:{topic_code:"PHYSICAL EXAMINATION", is_derived:false, adam_param_code:"PHYSEXAM", name:"Physical Examination", name_sentence_case:"physical examination", is_default_selected_for_activity:false, is_data_sharing:true, is_required_for_activity:false, legacy_description:"Needed for the flowchart, but there will be no actual data collection for this topic code", is_legacy_usage:false}}, {_id:926983, properties:{topic_code:"PHYSICAL EXAMINATION", adam_param_code:"PHYSEXAM", name:"Physical Examination", name_sentence_case:"physical examination", is_default_selected_for_activity:false, is_data_sharing:true, is_required_for_activity:false, legacy_description:"Needed for the flowchart, but there will be no actual data collection for this topic code", is_legacy_usage:false}}, {_id:917327, properties:{topic_code:"PHYSICAL EXAMINATION", adam_param_code:"PHYSEXAM", name:"Physical Examination", name_sentence_case:"physical examination", is_default_selected_for_activity:false, is_data_sharing:false, is_required_for_activity:false, legacy_description:"Needed for the flowchart, but there will be no actual data collection for this topic code", is_legacy_usage:false}}, {_id:884362, properties:{topic_code:"PHYSICAL EXAMINATION", adam_param_code:"PHYSEXAM", name:"Physical Examination", name_sentence_case:"physical examination", legacy_description:"Needed for the flowchart, but there will be no actual data collection for this topic code"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:ActivityInstanceValue:TemplateParameterTermValue;
UNWIND [{uid:"ActivityInstance_000623", properties:{}}] AS row
CREATE (n:ConceptRoot{uid: row.uid}) SET n += row.properties SET n:ActivityInstanceRoot:TemplateParameterTermRoot;
UNWIND [{uid:"Activity_003053", properties:{}}, {uid:"Activity_003360", properties:{}}, {uid:"Activity_004655", properties:{}}, {uid:"Activity_004657", properties:{}}] AS row
CREATE (n:ActivityRoot{uid: row.uid}) SET n += row.properties SET n:ConceptRoot:TemplateParameterTermRoot;
UNWIND [{_id:1159465, properties:{name:"Blood Pressure", is_request_rejected:false, name_sentence_case:"blood pressure", is_request_final:false, is_data_collected:true, is_multiple_selection_allowed:true}}, {_id:935697, properties:{name:"Blood Pressure", name_sentence_case:"blood pressure", is_data_collected:true}}, {_id:1203485, properties:{request_rationale:"The assessment is missing", is_request_rejected:true, name:"Temporary Discontinuation of Trial Treatment ", name_sentence_case:"temporary discontinuation of trial treatment ", is_request_final:true, is_data_collected:true, is_multiple_selection_allowed:true}}, {_id:953569, properties:{request_rationale:"The assessment is missing", name:"Temporary Discontinuation of Trial Treatment ", name_sentence_case:"temporary discontinuation of trial treatment ", is_data_collected:true}}, {_id:1424076, properties:{request_rationale:"Needed for antibody analysis", contact_person:"CGZR", is_request_rejected:true, name:"Anti-cagrilintide antibodies neutralising endogenous amylin", name_sentence_case:"anti-cagrilintide antibodies neutralising endogenous amylin", is_request_final:true, is_data_collected:true, reason_for_rejecting:"Please use the existing activity Anti-Endogenous Amylin Antibody Neutralising, which captures anti-cagrilintide antibodies neutralising endogenous Amylin in serum.\n", is_multiple_selection_allowed:true}}, {_id:1421486, properties:{request_rationale:"Needed for antibody analysis", is_request_rejected:false, name:"Anti-cagrilintide antibodies neutralising endogenous amylin", name_sentence_case:"anti-cagrilintide antibodies neutralising endogenous amylin", is_request_final:true, is_data_collected:true, is_multiple_selection_allowed:true}}, {_id:1424078, properties:{request_rationale:"Needed for endpoint analysis", contact_person:"CGZR", is_request_rejected:true, name:"Fasting plasma glucose (FPG)", name_sentence_case:"fasting plasma glucose (fpg)", is_request_final:true, is_data_collected:true, reason_for_rejecting:"Please use the existing activity Glucose, from Glucose Metabolism subgroup, which collects the measurement for plasma glucose. Please contact me for more information regarding this", is_multiple_selection_allowed:true}}, {_id:1421496, properties:{request_rationale:"Needed for endpoint analysis", name:"Fasting plasma glucose (FPG)", is_request_rejected:false, name_sentence_case:"fasting plasma glucose (fpg)", is_request_final:true, is_data_collected:true, is_multiple_selection_allowed:true}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:ActivityValue:TemplateParameterTermValue;
UNWIND [{start: {uid:"Activity_003053"}, end: {_id:1159465}, properties:{change_description:"Inactivated version", author_id:"b5ab03b0-5d25-4abc-a2e9-0af5029dbf7d", version:"3.0", status:"Retired", start_date:datetime('2024-04-29T15:20:35.476054Z')}}, {start: {uid:"Activity_003053"}, end: {_id:935697}, properties:{end_date:datetime('2023-11-28T15:36:12.106935Z'), change_description:"New draft created", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.1", status:"Draft", start_date:datetime('2023-11-28T15:31:02.984521Z')}}, {start: {uid:"Activity_003360"}, end: {_id:953569}, properties:{end_date:datetime('2024-06-03T14:43:15.93365Z'), change_description:"Approved version", author_id:"9e642601-db61-430a-a619-101e13145d87", version:"1.0", status:"Final", start_date:datetime('2023-12-15T11:47:38.942265Z')}}, {start: {uid:"Activity_003053"}, end: {_id:935697}, properties:{end_date:datetime('2024-04-29T15:20:35.476054Z'), change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"2.0", status:"Final", start_date:datetime('2023-11-28T15:36:12.106935Z')}}, {start: {uid:"Activity_003053"}, end: {_id:935697}, properties:{end_date:datetime('2023-11-28T15:31:02.984521Z'), change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2023-11-27T11:02:45.553605Z')}}, {start: {uid:"Activity_004655"}, end: {_id:1421486}, properties:{end_date:datetime('2024-09-17T15:42:09.947089Z'), change_description:"Initial version", author_id:"58dcf243-8d58-46ce-b524-289da8374055", version:"0.1", status:"Draft", start_date:datetime('2024-09-17T15:42:09.526338Z')}}, {start: {uid:"Activity_004657"}, end: {_id:1421496}, properties:{end_date:datetime('2024-09-17T15:44:51.138679Z'), change_description:"Initial version", author_id:"58dcf243-8d58-46ce-b524-289da8374055", version:"0.1", status:"Draft", start_date:datetime('2024-09-17T15:44:50.765338Z')}}, {start: {uid:"Activity_003053"}, end: {_id:935697}, properties:{end_date:datetime('2023-11-27T11:02:45.553605Z'), change_description:"Initial version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"0.1", status:"Draft", start_date:datetime('2023-11-27T11:02:42.151641Z')}}, {start: {uid:"Activity_003360"}, end: {_id:1203485}, properties:{change_description:"Inactivated version", author_id:"1d485f33-92cd-4327-aef1-7b30dc44e52e", version:"2.0", status:"Retired", start_date:datetime('2024-06-03T14:43:15.93365Z')}}, {start: {uid:"Activity_004657"}, end: {_id:1421496}, properties:{end_date:datetime('2024-09-18T13:45:31.978382Z'), change_description:"Approved version", author_id:"58dcf243-8d58-46ce-b524-289da8374055", version:"1.0", status:"Final", start_date:datetime('2024-09-17T15:44:51.138679Z')}}, {start: {uid:"Activity_004657"}, end: {_id:1424078}, properties:{change_description:"Retiring rejected Activity Request", author_id:"ed8da613-ea0d-41aa-aa51-5c0881e9d82f", version:"2.0", status:"Retired", start_date:datetime('2024-09-18T13:45:31.978382Z')}}, {start: {uid:"Activity_003360"}, end: {_id:953569}, properties:{end_date:datetime('2023-12-15T11:47:38.942265Z'), change_description:"Initial version", author_id:"9e642601-db61-430a-a619-101e13145d87", version:"0.1", status:"Draft", start_date:datetime('2023-12-15T11:47:38.062341Z')}}, {start: {uid:"Activity_004655"}, end: {_id:1421486}, properties:{end_date:datetime('2024-09-18T13:14:30.904366Z'), change_description:"Approved version", author_id:"58dcf243-8d58-46ce-b524-289da8374055", version:"1.0", status:"Final", start_date:datetime('2024-09-17T15:42:09.947089Z')}}, {start: {uid:"Activity_004655"}, end: {_id:1424076}, properties:{change_description:"Retiring rejected Activity Request", author_id:"ed8da613-ea0d-41aa-aa51-5c0881e9d82f", version:"2.0", status:"Retired", start_date:datetime('2024-09-18T13:14:30.904366Z')}}] AS row
MATCH (start:ActivityRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivityInstance_000623"}, end: {_id:926983}, properties:{end_date:datetime('2024-03-27T08:55:56.03807Z'), change_description:"Approved version", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"3.0", status:"Final", start_date:datetime('2023-12-04T11:00:46.520314Z')}}, {start: {uid:"ActivityInstance_000623"}, end: {_id:926983}, properties:{end_date:datetime('2023-10-27T14:18:59.828418Z'), change_description:"Migration modification", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.2", status:"Draft", start_date:datetime('2023-10-27T14:09:41.914088Z')}}, {start: {uid:"ActivityInstance_000623"}, end: {_id:884362}, properties:{end_date:datetime('2023-10-27T13:55:37.603931Z'), change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2023-06-21T13:21:22.025653Z')}}, {start: {uid:"ActivityInstance_000623"}, end: {_id:926983}, properties:{end_date:datetime('2023-11-27T11:23:36.682473Z'), change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"2.0", status:"Final", start_date:datetime('2023-10-27T14:18:59.828418Z')}}, {start: {uid:"ActivityInstance_000623"}, end: {_id:884362}, properties:{end_date:datetime('2023-06-21T13:21:22.025653Z'), change_description:"Initial version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"0.1", status:"Draft", start_date:datetime('2023-06-21T13:21:20.139746Z')}}, {start: {uid:"ActivityInstance_000623"}, end: {_id:926983}, properties:{end_date:datetime('2023-12-04T11:00:46.520314Z'), change_description:"New draft created", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"2.1", status:"Draft", start_date:datetime('2023-11-27T11:23:36.682473Z')}}, {start: {uid:"ActivityInstance_000623"}, end: {_id:1049688}, properties:{change_description:"Inactivated version", author_id:"1d485f33-92cd-4327-aef1-7b30dc44e52e", version:"4.0", status:"Retired", start_date:datetime('2024-03-27T08:55:56.03807Z')}}, {start: {uid:"ActivityInstance_000623"}, end: {_id:917327}, properties:{end_date:datetime('2023-10-27T14:09:41.914088Z'), change_description:"New draft created", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.1", status:"Draft", start_date:datetime('2023-10-27T13:55:37.603931Z')}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
DROP CONSTRAINT UNIQUE_IMPORT_NAME;"""


# Test data for duplicated submsission values in the Unit codelist
# Based on extraction queries from extract_queries.md
_DUPLICATES_IN_UNITS_QUERY = """
// Define the Cypher query to extract the relevant subgraph
WITH "
MATCH (clr:CTCodelistRoot {uid: 'C71620'})-[:HAS_NAME_ROOT]->(clnr:CTCodelistNameRoot)-[:LATEST]-(clnv)
MATCH (cl_lib:Library)-[:CONTAINS_CODELIST]->(clr)
MATCH (clr)-[:HAS_ATTRIBUTES_ROOT]->(clar:CTCodelistAttributesRoot)-[:LATEST]-(clav)
CALL {
    WITH clr
    MATCH (clr:CTCodelistRoot)-[ht:HAS_TERM]->(clt:CTCodelistTerm)
    WITH clr, collect(clt.submission_value) AS term_submvals
    WITH clr, apoc.coll.duplicates(term_submvals) AS duplicates
    WHERE size(duplicates) > 0
    RETURN duplicates
}
MATCH (clr)-[:HAS_TERM]-(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]-(tr)
WHERE clt.submission_value IN duplicates
MATCH (tav:CTTermAttributesValue)-[:LATEST]-(tar:CTTermAttributesRoot)--(tr)--(tnr:CTTermNameRoot)-[:LATEST]-(tnv:CTTermNameValue)
MATCH (t_lib:Library)-[:CONTAINS_TERM]->(tr)
OPTIONAL MATCH (tr)<-[:HAS_SELECTED_TERM]-(ctx:CTTermContext)--(uv:UnitDefinitionValue)-[:HAS_VERSION]-(ur:UnitDefinitionRoot)
OPTIONAL MATCH (ctx)-[:HAS_SELECTED_CODELIST]->(clr)
RETURN * LIMIT 100
" AS cypherQuery

// Execute the query and collect nodes and relationships
CALL apoc.cypher.run(cypherQuery, {}) YIELD value
UNWIND value as row
WITH [key IN keys(row) WHERE apoc.meta.cypher.isType(row[key], "NODE") | row[key]] AS nodes_in_row
UNWIND nodes_in_row as node
WITH collect(DISTINCT node) AS all_nodes
WITH all_nodes, [node IN all_nodes | elementId(node)] AS node_ids
MATCH (n)-[rel]->(m)
WHERE elementId(n) IN node_ids
AND elementId(m) IN node_ids
WITH all_nodes, collect(DISTINCT rel) AS all_rels
CALL apoc.export.cypher.data(all_nodes, all_rels,
   NULL,
   { format: "plain", cypherFormat: "create", stream: true})
YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
RETURN cypherStatements
"""
DUPLICATES_IN_UNITS = """
CREATE CONSTRAINT UNIQUE_IMPORT_NAME FOR (node:`UNIQUE IMPORT LABEL`) REQUIRE (node.`UNIQUE IMPORT ID`) IS UNIQUE;
UNWIND [{_id:851308, properties:{name:"Arbitrary U/mL", name_sentence_case:"Arbitrary U/mL"}}, {_id:2384934, properties:{name:"mL/min/1.73 m2", name_sentence_case:"mL/min/1.73 m2"}}, {_id:2381286, properties:{name:"ms", name_sentence_case:"ms"}}, {_id:2391674, properties:{name:"Therapeutic Cells", name_sentence_case:"Therapeutic Cells"}}, {_id:3794443, properties:{name:"Arbitrary U/mL", name_sentence_case:"arbitrary U/mL"}}, {_id:3818715, properties:{name:"RFU", name_sentence_case:"RFU"}}, {_id:3812842, properties:{name:"mL/min/1.73m2", name_sentence_case:"ml/min/1.73m2"}}, {_id:3813077, properties:{name:"gtt", name_sentence_case:"gtt"}}, {_id:3850939, properties:{name:"Therapeutic Cells", name_sentence_case:"therapeutic cells"}}, {_id:3848290, properties:{name:"gtt", name_sentence_case:"gtt"}}, {_id:3790939, properties:{name:"msec", name_sentence_case:"msec"}}, {_id:3821874, properties:{name:"NIU", name_sentence_case:"NIU"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermNameValue;
UNWIND [{_id:1020798, properties:{us_conventional_unit:false, si_unit:false, display_unit:true, name:"arbitrary units/mL", master_unit:false, definition:"arbitrary units/mL", use_complex_unit_conversion:false, use_molecular_weight:false, conversion_factor_to_master:1.0, convertible_unit:false, legacy_code:"arbitrary units/mL", order:1}}, {_id:852360, properties:{us_conventional_unit:false, si_unit:false, display_unit:true, name:"arbitrary units/mL", master_unit:false, definition:"arbitrary units/mL", use_complex_unit_conversion:false, use_molecular_weight:false, conversion_factor_to_master:1.0, convertible_unit:false, legacy_code:"arbitrary units/mL", order:1}}, {_id:852380, properties:{us_conventional_unit:false, si_unit:false, display_unit:true, name:"arbitrary units/mL", master_unit:false, definition:"arbitrary units/mL", use_complex_unit_conversion:false, use_molecular_weight:false, conversion_factor_to_master:1.0, convertible_unit:false, legacy_code:"arbitrary units/mL", order:1}}, {_id:852312, properties:{us_conventional_unit:false, display_unit:true, si_unit:false, master_unit:false, name:"RFU", definition:"Relative Fluorescence Intensity Unit", use_complex_unit_conversion:false, use_molecular_weight:false, conversion_factor_to_master:1.0, convertible_unit:false, order:1, legacy_code:"RFU"}}, {_id:852290, properties:{us_conventional_unit:false, display_unit:true, si_unit:false, master_unit:false, name:"RFU", definition:"Relative Fluorescence Intensity Unit", use_complex_unit_conversion:false, use_molecular_weight:false, conversion_factor_to_master:1.0, convertible_unit:false, order:1, legacy_code:"RFU"}}, {_id:1020776, properties:{us_conventional_unit:false, display_unit:true, si_unit:false, master_unit:false, name:"RFU", definition:"Relative Fluorescence Intensity Unit", use_complex_unit_conversion:false, use_molecular_weight:false, conversion_factor_to_master:1.0, convertible_unit:false, order:1, legacy_code:"RFU"}}, {_id:852170, properties:{us_conventional_unit:false, display_unit:true, si_unit:false, master_unit:false, name:"mL/min/1.73m2", definition:"CDISC code: C67412_x000D_\nCDISC submission value: mL/min/1.73m2_x000D_\nCDISC synonym: _x000D_\nCDISC Description: A metric unit of volumetric flow rate defined as the rate at which one milliliter of matter travels during the period of time equal to one minute per 1.73 meters squared of body surface area._x000D_\nNCI preferred term: Milliliter per Minute per 1.73 m2 of Body Surface Area", use_complex_unit_conversion:false, use_molecular_weight:false, conversion_factor_to_master:1.0, convertible_unit:true, legacy_code:"mL/min/1.73m2", order:2140}}, {_id:851928, properties:{us_conventional_unit:true, display_unit:true, si_unit:false, master_unit:true, name:"mL/min/SSA", definition:"CDISC code: C67412_x000D_\nCDISC submission value: mL/min/1.73m2_x000D_\nCDISC synonym: _x000D_\nCDISC Description: A metric unit of volumetric flow rate defined as the rate at which one milliliter of matter travels during the period of time equal to one minute per 1.73 meters squared of body surface area._x000D_\nNCI preferred term: Milliliter per Minute per 1.73 m2 of Body Surface Area", use_complex_unit_conversion:false, use_molecular_weight:false, conversion_factor_to_master:1.0, convertible_unit:true, order:2140, legacy_code:"mL/min/SSA"}}, {_id:852190, properties:{us_conventional_unit:true, display_unit:true, si_unit:false, master_unit:false, name:"mL/min/1.73m2", definition:"CDISC code: C67412_x000D_\nCDISC submission value: mL/min/1.73m2_x000D_\nCDISC synonym: _x000D_\nCDISC Description: A metric unit of volumetric flow rate defined as the rate at which one milliliter of matter travels during the period of time equal to one minute per 1.73 meters squared of body surface area._x000D_\nNCI preferred term: Milliliter per Minute per 1.73 m2 of Body Surface Area", use_complex_unit_conversion:false, use_molecular_weight:false, conversion_factor_to_master:1.0, convertible_unit:true, legacy_code:"mL/min/1.73m2", order:2140}}, {_id:851906, properties:{us_conventional_unit:false, display_unit:true, si_unit:false, master_unit:true, name:"mL/min/SSA", definition:"CDISC code: C67412_x000D_\nCDISC submission value: mL/min/1.73m2_x000D_\nCDISC synonym: _x000D_\nCDISC Description: A metric unit of volumetric flow rate defined as the rate at which one milliliter of matter travels during the period of time equal to one minute per 1.73 meters squared of body surface area._x000D_\nNCI preferred term: Milliliter per Minute per 1.73 m2 of Body Surface Area", use_complex_unit_conversion:false, use_molecular_weight:false, conversion_factor_to_master:1.0, convertible_unit:true, order:2140, legacy_code:"mL/min/SSA"}}, {_id:852359, properties:{us_conventional_unit:true, si_unit:true, display_unit:true, master_unit:false, name:"msec", definition:"CDISC code: C41140_x000D_\nCDISC submission value: msec_x000D_\nCDISC synonym: Millisecond_x000D_\nCDISC Description: A unit of time, which is equal to one thousandth of a second.(NCI)_x000D_\nNCI preferred term: Millisecond_x000D_\n_x000D_\n[time subset]", use_complex_unit_conversion:false, use_molecular_weight:false, conversion_factor_to_master:0.001, convertible_unit:true, order:1950, legacy_code:"msec"}}, {_id:1021075, properties:{us_conventional_unit:true, si_unit:true, display_unit:true, master_unit:false, name:"msec", definition:"CDISC code: C41140\nCDISC submission value: msec\nCDISC synonym: Millisecond\nCDISC Description: A unit of time, which is equal to one thousandth of a second.(NCI)\nNCI preferred term: Millisecond\n\n[time subset]", use_complex_unit_conversion:false, use_molecular_weight:false, conversion_factor_to_master:1.0, convertible_unit:true, order:1950, legacy_code:"msec"}}, {_id:852339, properties:{us_conventional_unit:false, si_unit:true, display_unit:true, master_unit:false, name:"msec", definition:"CDISC code: C41140_x000D_\nCDISC submission value: msec_x000D_\nCDISC synonym: Millisecond_x000D_\nCDISC Description: A unit of time, which is equal to one thousandth of a second.(NCI)_x000D_\nNCI preferred term: Millisecond_x000D_\n_x000D_\n[time subset]", use_complex_unit_conversion:false, use_molecular_weight:false, conversion_factor_to_master:0.001, convertible_unit:true, order:1950, legacy_code:"msec"}}, {_id:1020792, properties:{us_conventional_unit:false, si_unit:true, display_unit:true, master_unit:false, name:"msec", definition:"CDISC code: C41140\nCDISC submission value: msec\nCDISC synonym: Millisecond\nCDISC Description: A unit of time, which is equal to one thousandth of a second.(NCI)\nNCI preferred term: Millisecond\n\n[time subset]", use_complex_unit_conversion:false, use_molecular_weight:false, conversion_factor_to_master:1.0, convertible_unit:true, order:1950, legacy_code:"msec"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:TemplateParameterTermValue:UnitDefinitionValue;
UNWIND [{_id:2602849, properties:{}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistAttributesRoot;
UNWIND [{_id:2382007, properties:{}}, {_id:871067, properties:{}}, {_id:871070, properties:{}}, {_id:871058, properties:{}}, {_id:3865936, properties:{}}, {_id:3866089, properties:{}}, {_id:3865965, properties:{}}, {_id:2381301, properties:{}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermContext;
UNWIND [{_id:2612573, properties:{name:"Unit", name_sentence_case:"unit"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistNameValue;
UNWIND [{_id:2602848, properties:{}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistNameRoot;
UNWIND [{_id:37, properties:{name:"CDISC", is_editable:false}}, {_id:847729, properties:{name:"Sponsor", is_editable:true}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:Library;
UNWIND [{_id:851304, properties:{}}, {_id:2384930, properties:{}}, {_id:2381282, properties:{}}, {_id:2391670, properties:{}}, {_id:2842219, properties:{}}, {_id:3225015, properties:{}}, {_id:3096548, properties:{}}, {_id:3103090, properties:{}}, {_id:3773711, properties:{}}, {_id:3747057, properties:{}}, {_id:2781991, properties:{}}, {_id:3289763, properties:{}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermAttributesRoot;
UNWIND [{_id:3865675, properties:{submission_value:"Arbitrary U/mL"}}, {_id:3864606, properties:{submission_value:"mL/min/1.73 m2"}}, {_id:3864704, properties:{submission_value:"ms"}}, {_id:3864173, properties:{submission_value:"Therapeutic Cells"}}, {_id:2842236, properties:{submission_value:"Arbitrary U/mL"}}, {_id:3225096, properties:{submission_value:"NIU"}}, {_id:3096572, properties:{submission_value:"mL/min/1.73 m2"}}, {_id:3103097, properties:{submission_value:"gtt"}}, {_id:3773732, properties:{submission_value:"Therapeutic Cells"}}, {_id:3747134, properties:{submission_value:"gtt"}}, {_id:2782083, properties:{submission_value:"ms"}}, {_id:3289814, properties:{submission_value:"NIU"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistTerm;
UNWIND [{_id:851307, properties:{}}, {_id:2384933, properties:{}}, {_id:2381285, properties:{}}, {_id:2391673, properties:{}}, {_id:2842218, properties:{}}, {_id:3225014, properties:{}}, {_id:3096547, properties:{}}, {_id:3103089, properties:{}}, {_id:3773710, properties:{}}, {_id:3747056, properties:{}}, {_id:2781990, properties:{}}, {_id:3289762, properties:{}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermNameRoot;
UNWIND [{_id:851305, properties:{preferred_term:"Arbitrary Units per Milliliter", definition:"A unit of arbitrary units per milliliter"}}, {_id:2384931, properties:{preferred_term:"mL/min/1.73 m2", definition:"Created by Veeva Library Importer", name_submission_value:"mL/min/1.73 m2"}}, {_id:2381283, properties:{preferred_term:"ms", definition:"Created by Veeva Library Importer", name_submission_value:"ms"}}, {_id:2391671, properties:{preferred_term:"Therapeutic Cells", definition:"Created by Veeva Library Importer", name_submission_value:"Therapeutic Cells"}}, {_id:3794442, properties:{preferred_term:"Arbitrary Unit per Milliliter", concept_id:"C191361", synonyms:["AU/mL"], definition:"A unit based on or subject to individual judgment, preference, or predetermined reference per unit of volume equal to one milliliter."}}, {_id:3818714, properties:{preferred_term:"Relative Fluorescence Intensity Unit", concept_id:"C77535", synonyms:["Relative Fluorescence Intensity Unit", "Relative Fluorescence Unit", "Relative Intensity Unit", "RFIU", "RIU"], definition:"An arbitrary unit used to measure the intensity of the emitted fluorescent light in a sample; it is dependent on instrument and measurement parameters."}}, {_id:3812841, properties:{preferred_term:"Milliliter per Minute per 1.73 m2 of Body Surface Area", concept_id:"C67412", synonyms:["mL/min/1.73m2"], definition:"A metric unit of volumetric flow rate defined as the rate at which one milliliter of matter travels during the period of time equal to one minute per 1.73 meters squared of body surface area."}}, {_id:3813076, properties:{preferred_term:"Medical Drop", concept_id:"C69442", synonyms:["Drop"], definition:"A unit of volume equal to 0.05 milliliter (20 drops/ml).(NCI)"}}, {_id:3850938, properties:{preferred_term:"Therapeutic Cells Dosing Unit", concept_id:"C187669", synonyms:[], definition:"A dosing unit for the number of therapeutic cells administered."}}, {_id:3848289, properties:{preferred_term:"Metric Drop", concept_id:"C48491", synonyms:["Metric Drop"], definition:"A unit of volume equal to 0.05 milliliter (20 drops/ml).(NCI)"}}, {_id:3790938, properties:{preferred_term:"Millisecond", concept_id:"C41140", synonyms:["Millisecond", "ms", "msec"], definition:"A unit of time, which is equal to one thousandth of a second.(NCI)"}}, {_id:3821873, properties:{preferred_term:"Normalized Fluorescence Intensity Unit", concept_id:"C154680", synonyms:["NFIU", "NIU", "Normalized Fluorescence Intensity Unit", "Normalized Intensity Unit"], definition:"A relative fluorescence intensity unit that is adjusted to a reference standard. (NCI)"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermAttributesValue;
UNWIND [{uid:"UnitDefinition_000394", properties:{}}, {uid:"UnitDefinition_000393", properties:{}}, {uid:"UnitDefinition_000413", properties:{}}, {uid:"UnitDefinition_000404", properties:{}}] AS row
CREATE (n:ConceptRoot{uid: row.uid}) SET n += row.properties SET n:UnitDefinitionRoot;
UNWIND [{_id:2612572, properties:{preferred_term:"Unit", concept_id:"C71620", synonyms:["Unit"], name:"Unit", definition:"Terminology codelist used for units within CDISC.", extensible:"true", submission_value:"UNIT"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistAttributesValue;
UNWIND [{uid:"UnitDefinition_000327", properties:{}}, {uid:"UnitDefinition_000304", properties:{}}, {uid:"UnitDefinition_000264", properties:{}}, {uid:"UnitDefinition_000178", properties:{}}, {uid:"UnitDefinition_000320", properties:{}}] AS row
CREATE (n:ConceptRoot{uid: row.uid}) SET n += row.properties SET n:UnitDefinitionRoot:TemplateParameterTermRoot;
UNWIND [{uid:"C71620", properties:{}}] AS row
CREATE (n:CTCodelistRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{uid:"CTTerm_000255", properties:{}}, {uid:"CTTerm_001325", properties:{}}, {uid:"CTTerm_001227", properties:{}}, {uid:"CTTerm_001758", properties:{}}, {uid:"C191361", properties:{}}, {uid:"C77535", properties:{}}, {uid:"C67412", properties:{}}, {uid:"C69442", properties:{}}, {uid:"C187669", properties:{}}, {uid:"C48491", properties:{}}, {uid:"C41140", properties:{}}, {uid:"C154680", properties:{}}] AS row
CREATE (n:CTTermRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{_id:2384936, properties:{us_conventional_unit:false, si_unit:false, display_unit:false, master_unit:false, name:"mL/min/1.73 m2", use_complex_unit_conversion:false, use_molecular_weight:false, convertible_unit:false}}, {_id:2381288, properties:{us_conventional_unit:false, display_unit:false, si_unit:false, master_unit:false, name:"ms", use_complex_unit_conversion:false, use_molecular_weight:false, convertible_unit:false}}, {_id:2391676, properties:{us_conventional_unit:false, si_unit:false, display_unit:false, master_unit:false, name:"Therapeutic Cells", use_complex_unit_conversion:false, use_molecular_weight:false, convertible_unit:false}}, {_id:2391643, properties:{us_conventional_unit:false, display_unit:false, si_unit:false, master_unit:false, name:"gtt", use_complex_unit_conversion:false, use_molecular_weight:false, convertible_unit:false}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:UnitDefinitionValue;
UNWIND [{start: {_id:2602849}, end: {_id:2612572}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {_id:2781990}, end: {_id:3790939}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2014-09-26T00:00:00Z')}}, {start: {_id:3103089}, end: {_id:3813077}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2014-09-26T00:00:00Z')}}, {start: {_id:3747056}, end: {_id:3848290}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2015-06-26T00:00:00Z')}}, {start: {_id:3096547}, end: {_id:3812842}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2014-09-26T00:00:00Z')}}, {start: {_id:2842218}, end: {_id:3794443}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2022-12-16T00:00:00Z')}}, {start: {_id:851307}, end: {_id:851308}, properties:{change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:40:53.656377Z')}}, {start: {_id:2391673}, end: {_id:2391674}, properties:{change_description:"Approved version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"1.0", status:"Final", start_date:datetime('2025-08-28T13:58:13.530385Z')}}, {start: {_id:2391673}, end: {_id:2391674}, properties:{end_date:datetime('2025-08-28T13:58:13.530385Z'), change_description:"Initial version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"0.1", status:"Draft", start_date:datetime('2025-08-28T13:58:13.330708Z')}}, {start: {_id:3225014}, end: {_id:3818715}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2014-09-26T00:00:00Z')}}, {start: {_id:2381285}, end: {_id:2381286}, properties:{change_description:"Approved version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"1.0", status:"Final", start_date:datetime('2025-08-26T06:49:48.172041Z')}}, {start: {_id:2381285}, end: {_id:2381286}, properties:{end_date:datetime('2025-08-26T06:49:48.172041Z'), change_description:"Initial version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"0.1", status:"Draft", start_date:datetime('2025-08-26T06:49:47.54344Z')}}, {start: {_id:2384933}, end: {_id:2384934}, properties:{end_date:datetime('2025-08-27T13:47:07.988183Z'), change_description:"Initial version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"0.1", status:"Draft", start_date:datetime('2025-08-27T13:47:07.653052Z')}}, {start: {_id:2384933}, end: {_id:2384934}, properties:{change_description:"Approved version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"1.0", status:"Final", start_date:datetime('2025-08-27T13:47:07.988183Z')}}, {start: {_id:851307}, end: {_id:851308}, properties:{end_date:datetime('2022-09-21T19:40:53.656377Z'), change_description:"Initial version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:40:49.546278Z')}}, {start: {_id:3773710}, end: {_id:3850939}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2022-06-24T00:00:00Z')}}, {start: {_id:3289762}, end: {_id:3821874}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2018-09-28T00:00:00Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {_id:847729}, end: {uid:"UnitDefinition_000304"}, properties:{}}, {start: {_id:847729}, end: {uid:"UnitDefinition_000264"}, properties:{}}, {start: {_id:847729}, end: {uid:"UnitDefinition_000320"}, properties:{}}, {start: {_id:847729}, end: {uid:"UnitDefinition_000327"}, properties:{}}, {start: {_id:847729}, end: {uid:"UnitDefinition_000178"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:ConceptRoot{uid: row.end.uid})
CREATE (start)-[r:CONTAINS_CONCEPT]->(end) SET r += row.properties;
UNWIND [{start: {_id:2381288}, end: {_id:871070}, properties:{}}, {start: {_id:2384936}, end: {_id:871067}, properties:{}}, {start: {_id:2391643}, end: {_id:3865965}, properties:{}}, {start: {_id:2391676}, end: {_id:871058}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_CT_UNIT]->(end) SET r += row.properties;
UNWIND [{start: {_id:2382007}, end: {uid:"CTTerm_000255"}, properties:{}}, {start: {_id:3866089}, end: {uid:"C67412"}, properties:{}}, {start: {_id:3865936}, end: {uid:"C77535"}, properties:{}}, {start: {_id:871067}, end: {uid:"CTTerm_001325"}, properties:{}}, {start: {_id:871070}, end: {uid:"CTTerm_001227"}, properties:{}}, {start: {_id:2381301}, end: {uid:"C41140"}, properties:{}}, {start: {_id:3865965}, end: {uid:"C48491"}, properties:{}}, {start: {_id:871058}, end: {uid:"CTTerm_001758"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTTermRoot{uid: row.end.uid})
CREATE (start)-[r:HAS_SELECTED_TERM]->(end) SET r += row.properties;
UNWIND [{start: {_id:2602849}, end: {_id:2612572}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {uid:"UnitDefinition_000394"}, end: {_id:2384936}, properties:{change_description:"Approved version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"1.0", status:"Final", start_date:datetime('2025-08-27T13:47:09.322941Z')}}, {start: {uid:"UnitDefinition_000394"}, end: {_id:2384936}, properties:{end_date:datetime('2025-08-27T13:47:09.322941Z'), change_description:"Initial version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"0.1", status:"Draft", start_date:datetime('2025-08-27T13:47:08.730063Z')}}, {start: {uid:"UnitDefinition_000413"}, end: {_id:2391676}, properties:{end_date:datetime('2025-08-28T13:58:14.263988Z'), change_description:"Initial version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"0.1", status:"Draft", start_date:datetime('2025-08-28T13:58:13.993211Z')}}, {start: {uid:"UnitDefinition_000413"}, end: {_id:2391676}, properties:{change_description:"Approved version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"1.0", status:"Final", start_date:datetime('2025-08-28T13:58:14.263988Z')}}, {start: {uid:"UnitDefinition_000393"}, end: {_id:2381288}, properties:{end_date:datetime('2025-08-26T06:49:49.606907Z'), change_description:"Initial version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"0.1", status:"Draft", start_date:datetime('2025-08-26T06:49:49.006196Z')}}, {start: {uid:"UnitDefinition_000393"}, end: {_id:2381288}, properties:{change_description:"Approved version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"1.0", status:"Final", start_date:datetime('2025-08-26T06:49:49.606907Z')}}, {start: {uid:"UnitDefinition_000404"}, end: {_id:2391643}, properties:{change_description:"Approved version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"1.0", status:"Final", start_date:datetime('2025-08-28T13:57:35.362856Z')}}, {start: {uid:"UnitDefinition_000404"}, end: {_id:2391643}, properties:{end_date:datetime('2025-08-28T13:57:35.362856Z'), change_description:"Initial version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"0.1", status:"Draft", start_date:datetime('2025-08-28T13:57:35.070103Z')}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {_id:37}, end: {uid:"C48491"}, properties:{}}, {start: {_id:37}, end: {uid:"C154680"}, properties:{}}, {start: {_id:37}, end: {uid:"C187669"}, properties:{}}, {start: {_id:37}, end: {uid:"C77535"}, properties:{}}, {start: {_id:847729}, end: {uid:"CTTerm_000255"}, properties:{}}, {start: {_id:37}, end: {uid:"C69442"}, properties:{}}, {start: {_id:847729}, end: {uid:"CTTerm_001758"}, properties:{}}, {start: {_id:847729}, end: {uid:"CTTerm_001227"}, properties:{}}, {start: {_id:847729}, end: {uid:"CTTerm_001325"}, properties:{}}, {start: {_id:37}, end: {uid:"C191361"}, properties:{}}, {start: {_id:37}, end: {uid:"C67412"}, properties:{}}, {start: {_id:37}, end: {uid:"C41140"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTTermRoot{uid: row.end.uid})
CREATE (start)-[r:CONTAINS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {uid:"UnitDefinition_000320"}, end: {_id:1021075}, properties:{}}, {start: {uid:"UnitDefinition_000304"}, end: {_id:1020776}, properties:{}}, {start: {uid:"UnitDefinition_000327"}, end: {_id:1020798}, properties:{}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {_id:852380}, end: {_id:2382007}, properties:{}}, {start: {_id:852360}, end: {_id:2382007}, properties:{}}, {start: {_id:1020798}, end: {_id:2382007}, properties:{}}, {start: {_id:851928}, end: {_id:3866089}, properties:{}}, {start: {_id:851906}, end: {_id:3866089}, properties:{}}, {start: {_id:852190}, end: {_id:3866089}, properties:{}}, {start: {_id:852170}, end: {_id:3866089}, properties:{}}, {start: {_id:852290}, end: {_id:3865936}, properties:{}}, {start: {_id:1020776}, end: {_id:3865936}, properties:{}}, {start: {_id:852312}, end: {_id:3865936}, properties:{}}, {start: {_id:852339}, end: {_id:2381301}, properties:{}}, {start: {_id:1021075}, end: {_id:2381301}, properties:{}}, {start: {_id:1020792}, end: {_id:2381301}, properties:{}}, {start: {_id:852359}, end: {_id:2381301}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_CT_UNIT]->(end) SET r += row.properties;
UNWIND [{start: {_id:2602848}, end: {_id:2612573}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2014-09-26T00:00:00Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {_id:2382007}, end: {uid:"C71620"}, properties:{}}, {start: {_id:3866089}, end: {uid:"C71620"}, properties:{}}, {start: {_id:3865936}, end: {uid:"C71620"}, properties:{}}, {start: {_id:871067}, end: {uid:"C71620"}, properties:{}}, {start: {_id:871070}, end: {uid:"C71620"}, properties:{}}, {start: {_id:2381301}, end: {uid:"C71620"}, properties:{}}, {start: {_id:3865965}, end: {uid:"C71620"}, properties:{}}, {start: {_id:871058}, end: {uid:"C71620"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTCodelistRoot{uid: row.end.uid})
CREATE (start)-[r:HAS_SELECTED_CODELIST]->(end) SET r += row.properties;
UNWIND [{start: {uid:"C71620"}, end: {_id:3096572}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", start_date:datetime('2022-06-24T00:00:00Z')}}, {start: {uid:"C71620"}, end: {_id:2782083}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", start_date:datetime('2022-06-24T00:00:00Z')}}, {start: {uid:"C71620"}, end: {_id:3864704}, properties:{author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", start_date:datetime('2025-08-26T06:49:47.253622Z')}}, {start: {uid:"C71620"}, end: {_id:3773732}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", start_date:datetime('2022-06-24T00:00:00Z')}}, {start: {uid:"C71620"}, end: {_id:3865675}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", start_date:datetime('2022-09-21T19:40:49.119448Z')}}, {start: {uid:"C71620"}, end: {_id:3864173}, properties:{author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", start_date:datetime('2025-08-28T13:58:13.309295Z')}}, {start: {uid:"C71620"}, end: {_id:3103097}, properties:{end_date:datetime('2015-06-26T00:00:00Z'), author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", start_date:datetime('2014-09-26T00:00:00Z')}}, {start: {uid:"C71620"}, end: {_id:3864606}, properties:{author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", start_date:datetime('2025-08-27T13:47:07.623061Z')}}, {start: {uid:"C71620"}, end: {_id:3747134}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", start_date:datetime('2015-06-26T00:00:00Z')}}, {start: {uid:"C71620"}, end: {_id:3289814}, properties:{end_date:datetime('2019-09-27T00:00:00Z'), author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", start_date:datetime('2018-09-28T00:00:00Z')}}, {start: {uid:"C71620"}, end: {_id:3225096}, properties:{end_date:datetime('2018-09-28T00:00:00Z'), author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", start_date:datetime('2014-09-26T00:00:00Z')}}, {start: {uid:"C71620"}, end: {_id:2842236}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", start_date:datetime('2022-12-16T00:00:00Z')}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {uid:"C48491"}, end: {_id:3747056}, properties:{}}, {start: {uid:"C154680"}, end: {_id:3289762}, properties:{}}, {start: {uid:"C187669"}, end: {_id:3773710}, properties:{}}, {start: {uid:"C77535"}, end: {_id:3225014}, properties:{}}, {start: {uid:"C69442"}, end: {_id:3103089}, properties:{}}, {start: {uid:"CTTerm_000255"}, end: {_id:851307}, properties:{}}, {start: {uid:"CTTerm_001758"}, end: {_id:2391673}, properties:{}}, {start: {uid:"CTTerm_001227"}, end: {_id:2381285}, properties:{}}, {start: {uid:"CTTerm_001325"}, end: {_id:2384933}, properties:{}}, {start: {uid:"C191361"}, end: {_id:2842218}, properties:{}}, {start: {uid:"C67412"}, end: {_id:3096547}, properties:{}}, {start: {uid:"C41140"}, end: {_id:2781990}, properties:{}}] AS row
MATCH (start:CTTermRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_NAME_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:2781990}, end: {_id:3790939}, properties:{}}, {start: {_id:3103089}, end: {_id:3813077}, properties:{}}, {start: {_id:3096547}, end: {_id:3812842}, properties:{}}, {start: {_id:2842218}, end: {_id:3794443}, properties:{}}, {start: {_id:3747056}, end: {_id:3848290}, properties:{}}, {start: {_id:851307}, end: {_id:851308}, properties:{}}, {start: {_id:2391673}, end: {_id:2391674}, properties:{}}, {start: {_id:3225014}, end: {_id:3818715}, properties:{}}, {start: {_id:2381285}, end: {_id:2381286}, properties:{}}, {start: {_id:2384933}, end: {_id:2384934}, properties:{}}, {start: {_id:3773710}, end: {_id:3850939}, properties:{}}, {start: {_id:3289762}, end: {_id:3821874}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:2602848}, end: {_id:2612573}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {uid:"UnitDefinition_000320"}, end: {_id:1020792}, properties:{end_date:datetime('2024-02-07T08:22:52.785257Z'), change_description:"Migration modification", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"1.2", status:"Draft", start_date:datetime('2024-02-07T08:20:48.971305Z')}}, {start: {uid:"UnitDefinition_000304"}, end: {_id:852290}, properties:{end_date:datetime('2022-09-21T19:42:27.570118Z'), change_description:"Initial version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:42:25.998011Z')}}, {start: {uid:"UnitDefinition_000264"}, end: {_id:852170}, properties:{end_date:datetime('2022-09-21T19:42:18.714276Z'), change_description:"Initial version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:42:16.560711Z')}}, {start: {uid:"UnitDefinition_000327"}, end: {_id:1020798}, properties:{change_description:"Approved version", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"2.0", status:"Final", start_date:datetime('2024-02-07T08:22:55.163655Z')}}, {start: {uid:"UnitDefinition_000264"}, end: {_id:852190}, properties:{end_date:datetime('2024-02-07T08:20:22.766552Z'), change_description:"New draft created", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"1.1", status:"Draft", start_date:datetime('2024-02-07T08:17:57.903116Z')}}, {start: {uid:"UnitDefinition_000327"}, end: {_id:1020798}, properties:{end_date:datetime('2024-02-07T08:22:55.163655Z'), change_description:"Migration modification", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"1.2", status:"Draft", start_date:datetime('2024-02-07T08:20:51.968993Z')}}, {start: {uid:"UnitDefinition_000320"}, end: {_id:852359}, properties:{end_date:datetime('2024-02-07T08:20:48.971305Z'), change_description:"New draft created", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"1.1", status:"Draft", start_date:datetime('2024-02-07T08:18:08.782732Z')}}, {start: {uid:"UnitDefinition_000304"}, end: {_id:852312}, properties:{end_date:datetime('2024-02-07T08:20:41.489232Z'), change_description:"New draft created", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"1.1", status:"Draft", start_date:datetime('2024-02-07T08:18:05.712059Z')}}, {start: {uid:"UnitDefinition_000320"}, end: {_id:1021075}, properties:{change_description:"Approved version", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"3.0", status:"Final", start_date:datetime('2024-02-08T12:58:31.791193Z')}}, {start: {uid:"UnitDefinition_000327"}, end: {_id:852380}, properties:{end_date:datetime('2024-02-07T08:20:51.968993Z'), change_description:"New draft created", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"1.1", status:"Draft", start_date:datetime('2024-02-07T08:18:09.960912Z')}}, {start: {uid:"UnitDefinition_000320"}, end: {_id:852339}, properties:{end_date:datetime('2022-09-21T19:42:30.955477Z'), change_description:"Initial version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:42:29.391513Z')}}, {start: {uid:"UnitDefinition_000320"}, end: {_id:1021075}, properties:{end_date:datetime('2024-02-08T12:57:03.4058Z'), change_description:"New draft created", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"2.1", status:"Draft", start_date:datetime('2024-02-08T12:55:12.680283Z')}}, {start: {uid:"UnitDefinition_000304"}, end: {_id:1020776}, properties:{change_description:"Approved version", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"2.0", status:"Final", start_date:datetime('2024-02-07T08:22:46.281359Z')}}, {start: {uid:"UnitDefinition_000178"}, end: {_id:851928}, properties:{end_date:datetime('2024-02-07T08:17:40.863117Z'), change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:41:56.707902Z')}}, {start: {uid:"UnitDefinition_000320"}, end: {_id:1021075}, properties:{end_date:datetime('2024-02-08T12:55:12.680283Z'), change_description:"Approved version", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"2.0", status:"Final", start_date:datetime('2024-02-07T08:22:52.785257Z')}}, {start: {uid:"UnitDefinition_000304"}, end: {_id:1020776}, properties:{end_date:datetime('2024-02-07T08:22:46.281359Z'), change_description:"Migration modification", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"1.2", status:"Draft", start_date:datetime('2024-02-07T08:20:41.489232Z')}}, {start: {uid:"UnitDefinition_000264"}, end: {_id:852190}, properties:{end_date:datetime('2024-02-07T08:17:57.903116Z'), change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:42:18.714276Z')}}, {start: {uid:"UnitDefinition_000327"}, end: {_id:852360}, properties:{end_date:datetime('2022-09-21T19:42:32.439623Z'), change_description:"Initial version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:42:30.973567Z')}}, {start: {uid:"UnitDefinition_000178"}, end: {_id:851928}, properties:{end_date:datetime('2024-02-07T08:19:37.96302Z'), change_description:"New draft created", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"1.1", status:"Draft", start_date:datetime('2024-02-07T08:17:40.863117Z')}}, {start: {uid:"UnitDefinition_000304"}, end: {_id:852312}, properties:{end_date:datetime('2024-02-07T08:18:05.712059Z'), change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:42:27.570118Z')}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {uid:"UnitDefinition_000320"}, end: {_id:1020792}, properties:{end_date:datetime('2024-02-08T12:58:31.791193Z'), change_description:"Migration modification", author_id:"fee04f84-dd5d-4e5a-93c6-84ffa45f758f", version:"2.2", status:"Draft", start_date:datetime('2024-02-08T12:57:03.4058Z')}}, {start: {uid:"UnitDefinition_000178"}, end: {_id:851906}, properties:{end_date:datetime('2022-09-21T19:41:56.707902Z'), change_description:"Initial version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:41:55.332741Z')}}, {start: {uid:"UnitDefinition_000320"}, end: {_id:852359}, properties:{end_date:datetime('2024-02-07T08:18:08.782732Z'), change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:42:30.955477Z')}}, {start: {uid:"UnitDefinition_000327"}, end: {_id:852380}, properties:{end_date:datetime('2024-02-07T08:18:09.960912Z'), change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:42:32.439623Z')}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {uid:"UnitDefinition_000394"}, end: {_id:2384936}, properties:{}}, {start: {uid:"UnitDefinition_000413"}, end: {_id:2391676}, properties:{}}, {start: {uid:"UnitDefinition_000393"}, end: {_id:2381288}, properties:{}}, {start: {uid:"UnitDefinition_000404"}, end: {_id:2391643}, properties:{}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_DRAFT]->(end) SET r += row.properties;
UNWIND [{start: {_id:37}, end: {uid:"C71620"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTCodelistRoot{uid: row.end.uid})
CREATE (start)-[r:CONTAINS_CODELIST]->(end) SET r += row.properties;
UNWIND [{start: {_id:2781991}, end: {_id:3790938}, properties:{}}, {start: {_id:3103090}, end: {_id:3813076}, properties:{}}, {start: {_id:3747057}, end: {_id:3848289}, properties:{}}, {start: {_id:3096548}, end: {_id:3812841}, properties:{}}, {start: {_id:2842219}, end: {_id:3794442}, properties:{}}, {start: {_id:2384930}, end: {_id:2384931}, properties:{}}, {start: {_id:851304}, end: {_id:851305}, properties:{}}, {start: {_id:2391670}, end: {_id:2391671}, properties:{}}, {start: {_id:3225015}, end: {_id:3818714}, properties:{}}, {start: {_id:2381282}, end: {_id:2381283}, properties:{}}, {start: {_id:3773711}, end: {_id:3850938}, properties:{}}, {start: {_id:3289763}, end: {_id:3821873}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {uid:"UnitDefinition_000327"}, end: {_id:1020798}, properties:{}}, {start: {uid:"UnitDefinition_000320"}, end: {_id:1021075}, properties:{}}, {start: {uid:"UnitDefinition_000304"}, end: {_id:1020776}, properties:{}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:3289814}, end: {uid:"C154680"}, properties:{}}, {start: {_id:3864704}, end: {uid:"CTTerm_001227"}, properties:{}}, {start: {_id:3225096}, end: {uid:"C77535"}, properties:{}}, {start: {_id:3865675}, end: {uid:"CTTerm_000255"}, properties:{}}, {start: {_id:3773732}, end: {uid:"C187669"}, properties:{}}, {start: {_id:3103097}, end: {uid:"C69442"}, properties:{}}, {start: {_id:3864173}, end: {uid:"CTTerm_001758"}, properties:{}}, {start: {_id:3864606}, end: {uid:"CTTerm_001325"}, properties:{}}, {start: {_id:2782083}, end: {uid:"C41140"}, properties:{}}, {start: {_id:3747134}, end: {uid:"C48491"}, properties:{}}, {start: {_id:2842236}, end: {uid:"C191361"}, properties:{}}, {start: {_id:3096572}, end: {uid:"C67412"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTTermRoot{uid: row.end.uid})
CREATE (start)-[r:HAS_TERM_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:2781991}, end: {_id:3790938}, properties:{}}, {start: {_id:3103090}, end: {_id:3813076}, properties:{}}, {start: {_id:2842219}, end: {_id:3794442}, properties:{}}, {start: {_id:3747057}, end: {_id:3848289}, properties:{}}, {start: {_id:3096548}, end: {_id:3812841}, properties:{}}, {start: {_id:851304}, end: {_id:851305}, properties:{}}, {start: {_id:2391670}, end: {_id:2391671}, properties:{}}, {start: {_id:3225015}, end: {_id:3818714}, properties:{}}, {start: {_id:2381282}, end: {_id:2381283}, properties:{}}, {start: {_id:2384930}, end: {_id:2384931}, properties:{}}, {start: {_id:3773711}, end: {_id:3850938}, properties:{}}, {start: {_id:3289763}, end: {_id:3821873}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:2391670}, end: {_id:2391671}, properties:{}}, {start: {_id:851304}, end: {_id:851305}, properties:{}}, {start: {_id:2381282}, end: {_id:2381283}, properties:{}}, {start: {_id:2384930}, end: {_id:2384931}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_DRAFT]->(end) SET r += row.properties;
UNWIND [{start: {_id:2781990}, end: {_id:3790939}, properties:{}}, {start: {_id:3103089}, end: {_id:3813077}, properties:{}}, {start: {_id:3096547}, end: {_id:3812842}, properties:{}}, {start: {_id:2842218}, end: {_id:3794443}, properties:{}}, {start: {_id:3747056}, end: {_id:3848290}, properties:{}}, {start: {_id:2384933}, end: {_id:2384934}, properties:{}}, {start: {_id:2391673}, end: {_id:2391674}, properties:{}}, {start: {_id:3225014}, end: {_id:3818715}, properties:{}}, {start: {_id:2381285}, end: {_id:2381286}, properties:{}}, {start: {_id:851307}, end: {_id:851308}, properties:{}}, {start: {_id:3773710}, end: {_id:3850939}, properties:{}}, {start: {_id:3289762}, end: {_id:3821874}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {_id:2602849}, end: {_id:2612572}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2014-09-26T00:00:00Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {uid:"C71620"}, end: {_id:2602849}, properties:{}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_ATTRIBUTES_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {uid:"UnitDefinition_000404"}, end: {_id:2391643}, properties:{}}, {start: {uid:"UnitDefinition_000394"}, end: {_id:2384936}, properties:{}}, {start: {uid:"UnitDefinition_000413"}, end: {_id:2391676}, properties:{}}, {start: {uid:"UnitDefinition_000393"}, end: {_id:2381288}, properties:{}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:847729}, end: {uid:"UnitDefinition_000394"}, properties:{}}, {start: {_id:847729}, end: {uid:"UnitDefinition_000413"}, properties:{}}, {start: {_id:847729}, end: {uid:"UnitDefinition_000393"}, properties:{}}, {start: {_id:847729}, end: {uid:"UnitDefinition_000404"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:ConceptRoot{uid: row.end.uid})
CREATE (start)-[r:CONTAINS_CONCEPT]->(end) SET r += row.properties;
UNWIND [{start: {uid:"C71620"}, end: {_id:2602848}, properties:{}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_NAME_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:2602848}, end: {_id:2612573}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {uid:"C48491"}, end: {_id:3747057}, properties:{}}, {start: {uid:"C154680"}, end: {_id:3289763}, properties:{}}, {start: {uid:"C187669"}, end: {_id:3773711}, properties:{}}, {start: {uid:"CTTerm_000255"}, end: {_id:851304}, properties:{}}, {start: {uid:"C77535"}, end: {_id:3225015}, properties:{}}, {start: {uid:"C69442"}, end: {_id:3103090}, properties:{}}, {start: {uid:"CTTerm_001758"}, end: {_id:2391670}, properties:{}}, {start: {uid:"CTTerm_001227"}, end: {_id:2381282}, properties:{}}, {start: {uid:"CTTerm_001325"}, end: {_id:2384930}, properties:{}}, {start: {uid:"C191361"}, end: {_id:2842219}, properties:{}}, {start: {uid:"C67412"}, end: {_id:3096548}, properties:{}}, {start: {uid:"C41140"}, end: {_id:2781991}, properties:{}}] AS row
MATCH (start:CTTermRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_ATTRIBUTES_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:3289763}, end: {_id:3821873}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"2.0", status:"Final", start_date:datetime('2019-09-27T00:00:00Z')}}, {start: {_id:3103090}, end: {_id:3813076}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2014-09-26T00:00:00Z')}}, {start: {_id:3096548}, end: {_id:3812841}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"2.0", status:"Final", start_date:datetime('2023-03-31T00:00:00Z')}}, {start: {_id:2781991}, end: {_id:3790938}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"3.0", status:"Final", start_date:datetime('2022-06-24T00:00:00Z')}}, {start: {_id:2842219}, end: {_id:3794442}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"2.0", status:"Final", start_date:datetime('2024-09-27T00:00:00Z')}}, {start: {_id:3747057}, end: {_id:3848289}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"2.0", status:"Final", start_date:datetime('2017-12-22T00:00:00Z')}}, {start: {_id:2391670}, end: {_id:2391671}, properties:{end_date:datetime('2025-08-28T13:58:13.780594Z'), change_description:"Initial version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"0.1", status:"Draft", start_date:datetime('2025-08-28T13:58:13.273085Z')}}, {start: {_id:2384930}, end: {_id:2384931}, properties:{change_description:"Approved version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"1.0", status:"Final", start_date:datetime('2025-08-27T13:47:08.350746Z')}}, {start: {_id:851304}, end: {_id:851305}, properties:{end_date:datetime('2022-09-21T19:40:54.816517Z'), change_description:"Initial version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:40:48.566692Z')}}, {start: {_id:851304}, end: {_id:851305}, properties:{change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:40:54.816517Z')}}, {start: {_id:2391670}, end: {_id:2391671}, properties:{change_description:"Approved version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"1.0", status:"Final", start_date:datetime('2025-08-28T13:58:13.780594Z')}}, {start: {_id:2381282}, end: {_id:2381283}, properties:{change_description:"Approved version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"1.0", status:"Final", start_date:datetime('2025-08-26T06:49:48.628993Z')}}, {start: {_id:2381282}, end: {_id:2381283}, properties:{end_date:datetime('2025-08-26T06:49:48.628993Z'), change_description:"Initial version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"0.1", status:"Draft", start_date:datetime('2025-08-26T06:49:46.983156Z')}}, {start: {_id:3225015}, end: {_id:3818714}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"3.0", status:"Final", start_date:datetime('2019-09-27T00:00:00Z')}}, {start: {_id:2384930}, end: {_id:2384931}, properties:{end_date:datetime('2025-08-27T13:47:08.350746Z'), change_description:"Initial version", author_id:"66a8b400-a0ee-46eb-a8b6-ab44f321f532", version:"0.1", status:"Draft", start_date:datetime('2025-08-27T13:47:07.572015Z')}}, {start: {_id:3773711}, end: {_id:3850938}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2022-06-24T00:00:00Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {uid:"UnitDefinition_000327"}, end: {_id:1020798}, properties:{}}, {start: {uid:"UnitDefinition_000304"}, end: {_id:1020776}, properties:{}}, {start: {uid:"UnitDefinition_000320"}, end: {_id:1020792}, properties:{}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_DRAFT]->(end) SET r += row.properties;
UNWIND [{start: {uid:"UnitDefinition_000394"}, end: {_id:2384936}, properties:{}}, {start: {uid:"UnitDefinition_000413"}, end: {_id:2391676}, properties:{}}, {start: {uid:"UnitDefinition_000393"}, end: {_id:2381288}, properties:{}}, {start: {uid:"UnitDefinition_000404"}, end: {_id:2391643}, properties:{}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {_id:851307}, end: {_id:851308}, properties:{}}, {start: {_id:2391673}, end: {_id:2391674}, properties:{}}, {start: {_id:2381285}, end: {_id:2381286}, properties:{}}, {start: {_id:2384933}, end: {_id:2384934}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_DRAFT]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
DROP CONSTRAINT UNIQUE_IMPORT_NAME;
"""


# Negative duration of HAS_TERM
# Based on extraction queries from extract_queries.md
_NEGATIVE_DURATION_HAS_TERM_QUERY = """
// Define the Cypher query to extract the relevant subgraph
WITH "
MATCH (root)-[v:HAS_TERM]->(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]-(tr)
WHERE v.end_date IS NOT NULL AND v.end_date < v.start_date
RETURN *
" AS cypherQuery

// Execute the query and collect nodes and relationships
CALL apoc.cypher.run(cypherQuery, {}) YIELD value
UNWIND value as row
WITH [key IN keys(row) WHERE apoc.meta.cypher.isType(row[key], "NODE") | row[key]] AS nodes_in_row
UNWIND nodes_in_row as node
WITH collect(DISTINCT node) AS all_nodes
WITH all_nodes, [node IN all_nodes | elementId(node)] AS node_ids
MATCH (n)-[rel]->(m)
WHERE elementId(n) IN node_ids
AND elementId(m) IN node_ids
WITH all_nodes, collect(DISTINCT rel) AS all_rels
CALL apoc.export.cypher.data(all_nodes, all_rels,
   NULL,
   { format: "plain", cypherFormat: "create", stream: true})
YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
RETURN cypherStatements
"""
NEGATIVE_DURATION_HAS_TERM = """
CREATE CONSTRAINT UNIQUE_IMPORT_NAME FOR (node:`UNIQUE IMPORT LABEL`) REQUIRE (node.`UNIQUE IMPORT ID`) IS UNIQUE;
UNWIND [{uid:"CTTerm_000703", properties:{}}] AS row
CREATE (n:CTTermRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{uid:"CTCodelist_000047", properties:{}}] AS row
CREATE (n:CTCodelistRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{_id:3865227, properties:{submission_value:"VITAL SIGNS FIND_CAT"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistTerm;
UNWIND [{start: {_id:3865227}, end: {uid:"CTTerm_000703"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTTermRoot{uid: row.end.uid})
CREATE (start)-[r:HAS_TERM_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {uid:"CTCodelist_000047"}, end: {_id:3865227}, properties:{end_date:datetime('2025-02-10T15:44:04.653422Z'), author_id:"1d485f33-92cd-4327-aef1-7b30dc44e52e", start_date:datetime('2025-02-10T15:45:45.64869Z'), order:999999}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_TERM]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
DROP CONSTRAINT UNIQUE_IMPORT_NAME;
"""

# Duplicated term names in codelists
# Skip the Units codelist (handled separately)
# and the CDISC glossary.
_DUPLICATED_TERM_NAMES_QUERY = """
// Define the Cypher query to extract the relevant subgraph
WITH "
MATCH (clr:CTCodelistRoot)-[:HAS_NAME_ROOT]->(clnr:CTCodelistNameRoot)-[:LATEST]-(clnv)
WHERE clr.uid <> 'C71620' AND clr.uid <> 'C67497'
MATCH (cl_lib:Library)-[:CONTAINS_CODELIST]->(clr)
MATCH (clr)-[:HAS_ATTRIBUTES_ROOT]->(clar:CTCodelistAttributesRoot)-[:LATEST]-(clav)
CALL {
    WITH clr
    MATCH (clr)-[ht:HAS_TERM]->(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(tnv:CTTermNameValue)
    WHERE ht.end_date IS NULL
    WITH clr, collect(tnv.name) AS term_names
    WITH clr, apoc.coll.duplicates(term_names) AS duplicates
    WHERE size(duplicates) > 0
    RETURN duplicates
}
MATCH (clr)-[:HAS_TERM]-(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]-(tr)
MATCH (tav:CTTermAttributesValue)-[:LATEST]-(tar:CTTermAttributesRoot)--(tr)--(tnr:CTTermNameRoot)-[:LATEST]-(tnv:CTTermNameValue)
WHERE tnv.name IN duplicates
MATCH (t_lib:Library)-[:CONTAINS_TERM]->(tr)
RETURN * LIMIT 30
" AS cypherQuery

// Execute the query and collect nodes and relationships
CALL apoc.cypher.run(cypherQuery, {}) YIELD value
UNWIND value as row
WITH [key IN keys(row) WHERE apoc.meta.cypher.isType(row[key], "NODE") | row[key]] AS nodes_in_row
UNWIND nodes_in_row as node
WITH collect(DISTINCT node) AS all_nodes
WITH all_nodes, [node IN all_nodes | elementId(node)] AS node_ids
MATCH (n)-[rel]->(m)
WHERE elementId(n) IN node_ids
AND elementId(m) IN node_ids
WITH all_nodes, collect(DISTINCT rel) AS all_rels
CALL apoc.export.cypher.data(all_nodes, all_rels,
   NULL,
   { format: "plain", cypherFormat: "create", stream: true})
YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
RETURN cypherStatements
"""
DUPLICATE_TERM_NAMES = """
CREATE CONSTRAINT UNIQUE_IMPORT_NAME FOR (node:`UNIQUE IMPORT LABEL`) REQUIRE (node.`UNIQUE IMPORT ID`) IS UNIQUE;
UNWIND [{_id:3784730, properties:{name:"Direct Glomerular Filtration Rate from Beta-Trace Protein Adjusted for Standard BSA Measurement", name_sentence_case:"direct glomerular filtration rate from beta-trace protein adjusted for standard BSA measurement"}}, {_id:3784726, properties:{name:"Direct Glomerular Filtration Rate from Beta-Trace Protein Adjusted for Standard BSA Measurement", name_sentence_case:"direct glomerular filtration rate from beta-trace protein adjusted for standard BSA measurement"}}, {_id:851373, properties:{name:"Score", name_sentence_case:"Score"}}, {_id:3843510, properties:{name:"Score", name_sentence_case:"score"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermNameValue;
UNWIND [{_id:2594782, properties:{}}, {_id:2602254, properties:{}}, {_id:849846, properties:{}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistAttributesRoot;
UNWIND [{_id:2612058, properties:{name:"Laboratory Test Code", name_sentence_case:"laboratory test code"}}, {_id:2612559, properties:{name:"Laboratory Test Name", name_sentence_case:"laboratory test name"}}, {_id:849850, properties:{name:"Unit Dimension"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistNameValue;
UNWIND [{_id:2594781, properties:{}}, {_id:2602253, properties:{}}, {_id:849849, properties:{}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistNameRoot;
UNWIND [{_id:37, properties:{name:"CDISC", is_editable:false}}, {_id:847729, properties:{name:"Sponsor", is_editable:true}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:Library;
UNWIND [{_id:2629046, properties:{}}, {_id:2628959, properties:{}}, {_id:851369, properties:{}}, {_id:3676213, properties:{}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermAttributesRoot;
UNWIND [{_id:2629080, properties:{submission_value:"GFRBSB2M"}}, {_id:2628979, properties:{submission_value:"GFRBSBTP"}}, {_id:2628978, properties:{submission_value:"GFR from Beta-Trace Protein Adj for BSA"}}, {_id:2629079, properties:{submission_value:"GFR from B-2 Microglobulin Adj for BSA"}}, {_id:3865662, properties:{submission_value:"Score"}}, {_id:3676225, properties:{submission_value:"SCORE"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistTerm;
UNWIND [{_id:2629045, properties:{}}, {_id:2628958, properties:{}}, {_id:851372, properties:{}}, {_id:3676212, properties:{}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermNameRoot;
UNWIND [{_id:3784728, properties:{preferred_term:"Direct Glomerular Filtration Rate from Beta-Trace Protein Adjusted for Standard BSA Measurement", concept_id:"C100450", synonyms:["GFR from B-2 Microglobulin Adj for BSA"], definition:"A direct measurement of the glomerular filtration rate (GFR) based on the clearance of beta-2 microglobulin after adjusting it for the standard body surface area value 1.73m2."}}, {_id:3784724, properties:{preferred_term:"Direct Glomerular Filtration Rate from Beta-Trace Protein Adjusted for Standard BSA Measurement", concept_id:"C100449", synonyms:["GFR from Beta-Trace Protein Adj for BSA"], definition:"A direct measurement of the glomerular filtration rate (GFR) based on the clearance of beta-trace protein after adjusting it for the standard body surface area value 1.73m2."}}, {_id:851370, properties:{preferred_term:"Score", definition:"A unit of measure referring to grading or rating of the result or entity."}}, {_id:3843509, properties:{preferred_term:"Score", concept_id:"C25338", synonyms:["Score"], definition:"A value (e.g., number, numeric range, ratio) that assesses and orders a result or response for purposes of comparison."}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTTermAttributesValue;
UNWIND [{_id:2612057, properties:{preferred_term:"Laboratory Test Code", concept_id:"C65047", synonyms:["Laboratory Test Code"], name:"Laboratory Test Code", definition:"Terminology used for laboratory test codes of the CDISC Study Data Tabulation Model.", extensible:"true", submission_value:"LBTESTCD"}}, {_id:2612558, properties:{preferred_term:"Laboratory Test Name", concept_id:"C67154", synonyms:["Laboratory Test Name"], name:"Laboratory Test Name", definition:"Terminology used for laboratory test names of the CDISC Study Data Tabulation Model.", extensible:"true", submission_value:"LBTEST"}}, {_id:849847, properties:{preferred_term:"Unit Dimension", name:"Unit Dimension", definition:"Unit Dimension act as a reference to a set of unit definitions where unit conversion is possible.Y", extensible:true, submission_value:"UNITDIM"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCodelistAttributesValue;
UNWIND [{uid:"C65047", properties:{}}, {uid:"C67154", properties:{}}, {uid:"CTCodelist_000001", properties:{}}] AS row
CREATE (n:CTCodelistRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{uid:"C100450", properties:{}}, {uid:"C100449", properties:{}}, {uid:"CTTerm_000268", properties:{}}, {uid:"C25338", properties:{}}] AS row
CREATE (n:CTTermRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{start: {_id:2594782}, end: {_id:2612057}, properties:{}}, {start: {_id:849846}, end: {_id:849847}, properties:{}}, {start: {_id:2602254}, end: {_id:2612558}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {uid:"C67154"}, end: {uid:"C65047"}, properties:{}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:CTCodelistRoot{uid: row.end.uid})
CREATE (start)-[r:PAIRED_CODE_CODELIST]->(end) SET r += row.properties;
UNWIND [{start: {_id:2628958}, end: {_id:3784726}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"2.0", status:"Final", start_date:datetime('2025-03-28T00:00:00Z')}}, {start: {_id:851372}, end: {_id:851373}, properties:{end_date:datetime('2022-09-21T19:41:00.797722Z'), change_description:"Initial version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:40:59.730047Z')}}, {start: {_id:3676212}, end: {_id:3843510}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2021-06-25T00:00:00Z')}}, {start: {_id:2629045}, end: {_id:3784730}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"2.0", status:"Final", start_date:datetime('2025-03-28T00:00:00Z')}}, {start: {_id:851372}, end: {_id:851373}, properties:{change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:41:00.797722Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {_id:849846}, end: {_id:849847}, properties:{}}, {start: {_id:2594782}, end: {_id:2612057}, properties:{}}, {start: {_id:2602254}, end: {_id:2612558}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:37}, end: {uid:"C100450"}, properties:{}}, {start: {_id:37}, end: {uid:"C25338"}, properties:{}}, {start: {_id:847729}, end: {uid:"CTTerm_000268"}, properties:{}}, {start: {_id:37}, end: {uid:"C100449"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTTermRoot{uid: row.end.uid})
CREATE (start)-[r:CONTAINS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {_id:849849}, end: {_id:849850}, properties:{end_date:datetime('2022-09-21T19:36:26.553464Z'), change_description:"Initial version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:36:24.265398Z')}}, {start: {_id:2594781}, end: {_id:2612058}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2014-09-26T00:00:00Z')}}, {start: {_id:2602253}, end: {_id:2612559}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2014-09-26T00:00:00Z')}}, {start: {_id:849849}, end: {_id:849850}, properties:{change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:36:26.553464Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {uid:"C65047"}, end: {_id:2628979}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", start_date:datetime('2014-09-26T00:00:00Z')}}, {start: {uid:"C67154"}, end: {_id:2628978}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", start_date:datetime('2014-09-26T00:00:00Z')}}, {start: {uid:"CTCodelist_000001"}, end: {_id:3865662}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:119, start_date:datetime('2023-02-13T15:34:19.520741Z')}}, {start: {uid:"C65047"}, end: {_id:2629080}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", start_date:datetime('2014-09-26T00:00:00Z')}}, {start: {uid:"CTCodelist_000001"}, end: {_id:3676225}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", order:119, start_date:datetime('2022-09-21T19:40:47.571686Z')}}, {start: {uid:"C67154"}, end: {_id:2629079}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", start_date:datetime('2014-09-26T00:00:00Z')}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {_id:2594781}, end: {_id:2612058}, properties:{}}, {start: {_id:849849}, end: {_id:849850}, properties:{}}, {start: {_id:2602253}, end: {_id:2612559}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:2628958}, end: {_id:3784726}, properties:{}}, {start: {_id:851372}, end: {_id:851373}, properties:{}}, {start: {_id:3676212}, end: {_id:3843510}, properties:{}}, {start: {_id:2629045}, end: {_id:3784730}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {uid:"C100450"}, end: {_id:2629045}, properties:{}}, {start: {uid:"C25338"}, end: {_id:3676212}, properties:{}}, {start: {uid:"C100449"}, end: {_id:2628958}, properties:{}}, {start: {uid:"CTTerm_000268"}, end: {_id:851372}, properties:{}}] AS row
MATCH (start:CTTermRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_NAME_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:37}, end: {uid:"C67154"}, properties:{}}, {start: {_id:847729}, end: {uid:"CTCodelist_000001"}, properties:{}}, {start: {_id:37}, end: {uid:"C65047"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTCodelistRoot{uid: row.end.uid})
CREATE (start)-[r:CONTAINS_CODELIST]->(end) SET r += row.properties;
UNWIND [{start: {_id:2628959}, end: {_id:3784724}, properties:{}}, {start: {_id:851369}, end: {_id:851370}, properties:{}}, {start: {_id:3676213}, end: {_id:3843509}, properties:{}}, {start: {_id:2629046}, end: {_id:3784728}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {_id:2629079}, end: {uid:"C100450"}, properties:{}}, {start: {_id:2629080}, end: {uid:"C100450"}, properties:{}}, {start: {_id:2628978}, end: {uid:"C100449"}, properties:{}}, {start: {_id:2628979}, end: {uid:"C100449"}, properties:{}}, {start: {_id:3865662}, end: {uid:"CTTerm_000268"}, properties:{}}, {start: {_id:3676225}, end: {uid:"C25338"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTTermRoot{uid: row.end.uid})
CREATE (start)-[r:HAS_TERM_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:849849}, end: {_id:849850}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_DRAFT]->(end) SET r += row.properties;
UNWIND [{start: {_id:2628959}, end: {_id:3784724}, properties:{}}, {start: {_id:851369}, end: {_id:851370}, properties:{}}, {start: {_id:3676213}, end: {_id:3843509}, properties:{}}, {start: {_id:2629046}, end: {_id:3784728}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
UNWIND [{start: {_id:851369}, end: {_id:851370}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_DRAFT]->(end) SET r += row.properties;
UNWIND [{start: {_id:2628958}, end: {_id:3784726}, properties:{}}, {start: {_id:851372}, end: {_id:851373}, properties:{}}, {start: {_id:3676212}, end: {_id:3843510}, properties:{}}, {start: {_id:2629045}, end: {_id:3784730}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {uid:"C67154"}, end: {_id:2602254}, properties:{}}, {start: {uid:"CTCodelist_000001"}, end: {_id:849846}, properties:{}}, {start: {uid:"C65047"}, end: {_id:2594782}, properties:{}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_ATTRIBUTES_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:2602254}, end: {_id:2612558}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"2.0", status:"Final", start_date:datetime('2015-03-27T00:00:00Z')}}, {start: {_id:849846}, end: {_id:849847}, properties:{end_date:datetime('2022-09-21T19:36:29.306724Z'), change_description:"Initial version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:36:23.74379Z')}}, {start: {_id:849846}, end: {_id:849847}, properties:{change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:36:29.306724Z')}}, {start: {_id:2594782}, end: {_id:2612057}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"2.0", status:"Final", start_date:datetime('2015-03-27T00:00:00Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {_id:2594781}, end: {_id:2612058}, properties:{}}, {start: {_id:849849}, end: {_id:849850}, properties:{}}, {start: {_id:2602253}, end: {_id:2612559}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {uid:"C67154"}, end: {_id:2602253}, properties:{}}, {start: {uid:"C65047"}, end: {_id:2594781}, properties:{}}, {start: {uid:"CTCodelist_000001"}, end: {_id:849849}, properties:{}}] AS row
MATCH (start:CTCodelistRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_NAME_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {uid:"C100450"}, end: {_id:2629046}, properties:{}}, {start: {uid:"C25338"}, end: {_id:3676213}, properties:{}}, {start: {uid:"CTTerm_000268"}, end: {_id:851369}, properties:{}}, {start: {uid:"C100449"}, end: {_id:2628959}, properties:{}}] AS row
MATCH (start:CTTermRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_ATTRIBUTES_ROOT]->(end) SET r += row.properties;
UNWIND [{start: {_id:2628959}, end: {_id:3784724}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"2.0", status:"Final", start_date:datetime('2025-03-28T00:00:00Z')}}, {start: {_id:851369}, end: {_id:851370}, properties:{end_date:datetime('2022-09-21T19:41:00.995318Z'), change_description:"Initial version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"0.1", status:"Draft", start_date:datetime('2022-09-21T19:40:59.655403Z')}}, {start: {_id:3676213}, end: {_id:3843509}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"2.0", status:"Final", start_date:datetime('2024-03-29T00:00:00Z')}}, {start: {_id:2629046}, end: {_id:3784728}, properties:{author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"2.0", status:"Final", start_date:datetime('2025-03-28T00:00:00Z')}}, {start: {_id:851369}, end: {_id:851370}, properties:{change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2022-09-21T19:41:00.995318Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {_id:851372}, end: {_id:851373}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_DRAFT]->(end) SET r += row.properties;
UNWIND [{start: {_id:849846}, end: {_id:849847}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_DRAFT]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
DROP CONSTRAINT UNIQUE_IMPORT_NAME;
"""


# HAS_VERSION relationships where not the latest has no end_date
# Based on extraction queries from extract_queries.md
_NOT_LATEST_HAS_VERSION_LACKS_END_DATE_QUERY = """
// Define the Cypher query to extract the relevant subgraph
WITH "
MATCH (root)-[:HAS_VERSION]->()
WHERE none(label in labels(root) WHERE label IN [
        'ClassVariableRoot',
        'DataModelIGRoot',
        'DatasetClassRoot',
        'DatasetRoot',
        'DatasetScenarioRoot',
        'DatasetVariableRoot',
        'StudyRoot'
    ])
        CALL {
                WITH root
                MATCH (root)-[hv:HAS_VERSION]-()
                WITH hv
                // Sort by version and dates
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) DESC,
                    toInteger(split(hv.version, '.')[1]) DESC,
                    hv.end_date DESC,
                    hv.start_date DESC
                WITH collect(hv) as hvs
                // Return all except the very latest
                RETURN tail(hvs) as not_latest
            }
        WITH root WHERE any(v IN not_latest WHERE v.end_date IS NULL)
        MATCH (root)-[:HAS_VERSION]-(value)
        RETURN *
" AS cypherQuery

// Execute the query and collect nodes and relationships
CALL apoc.cypher.run(cypherQuery, {}) YIELD value
UNWIND value as row
WITH [key IN keys(row) WHERE apoc.meta.cypher.isType(row[key], "NODE") | row[key]] AS nodes_in_row
UNWIND nodes_in_row as node
WITH collect(DISTINCT node) AS all_nodes
WITH all_nodes, [node IN all_nodes | elementId(node)] AS node_ids
MATCH (n)-[rel]->(m)
WHERE elementId(n) IN node_ids
AND elementId(m) IN node_ids
WITH all_nodes, collect(DISTINCT rel) AS all_rels
CALL apoc.export.cypher.data(all_nodes, all_rels,
   NULL,
   { format: "plain", cypherFormat: "create", stream: true})
YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
RETURN cypherStatements
"""
NOT_LATEST_HAS_VERSION_WITHOUT_END_DATE = """
CREATE CONSTRAINT UNIQUE_IMPORT_NAME FOR (node:`UNIQUE IMPORT LABEL`) REQUIRE (node.`UNIQUE IMPORT ID`) IS UNIQUE;
UNWIND [{_id:884392, properties:{topic_code:"PROPHYLAXIS_TREATMENT_RECEIVED_YN", is_derived:false, adam_param_code:"PRF8TRT", name:"Subject Received Prev. Prophylaxis Trt", name_sentence_case:"subject received prev. prophylaxis trt", is_default_selected_for_activity:false, is_data_sharing:false, is_required_for_activity:false, legacy_description:"Sponsor defined: Has the subject received any previous prophylaxis/\nprevention treatment", is_legacy_usage:false}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:ConceptValue:ActivityInstanceValue:TemplateParameterTermValue;
UNWIND [{uid:"ActivityInstance_000638", properties:{}}] AS row
CREATE (n:ConceptRoot{uid: row.uid}) SET n += row.properties SET n:ActivityInstanceRoot:TemplateParameterTermRoot;
UNWIND [{start: {uid:"ActivityInstance_000638"}, end: {_id:884392}, properties:{}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_RETIRED]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivityInstance_000638"}, end: {_id:884392}, properties:{}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_DRAFT]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivityInstance_000638"}, end: {_id:884392}, properties:{change_description:"Approved version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"1.0", status:"Final", start_date:datetime('2023-06-21T13:21:25.625338Z')}}, {start: {uid:"ActivityInstance_000638"}, end: {_id:884392}, properties:{end_date:datetime('2023-06-21T13:21:25.625338Z'), change_description:"Initial version", author_id:"fd909732-bc9e-492b-a1ed-6e27757a4f00", version:"0.1", status:"Draft", start_date:datetime('2023-06-21T13:21:23.597929Z')}}, {start: {uid:"ActivityInstance_000638"}, end: {_id:884392}, properties:{change_description:"Inactivated version", author_id:"b5ab03b0-5d25-4abc-a2e9-0af5029dbf7d", version:"1.0", status:"Retired", start_date:datetime('2024-09-27T11:09:59.320553Z')}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivityInstance_000638"}, end: {_id:884392}, properties:{}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST_FINAL]->(end) SET r += row.properties;
UNWIND [{start: {uid:"ActivityInstance_000638"}, end: {_id:884392}, properties:{}}] AS row
MATCH (start:ConceptRoot{uid: row.start.uid})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:LATEST]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
DROP CONSTRAINT UNIQUE_IMPORT_NAME;
"""


# Test data for Bug #3473052: Isolated orphan nodes with no relationships
ISOLATED_ORPHAN_NODES = """
// Create isolated orphan nodes (nodes with no relationships)
CREATE (sa1:StudyAction {uid: "orphan_study_action_1", date: datetime("2024-01-01T00:00:00Z")});
CREATE (sa2:StudyAction {uid: "orphan_study_action_2", date: datetime("2024-01-02T00:00:00Z")});
CREATE (n1:Notification {uid: "orphan_notification_1", message: "Test notification"});
CREATE (sas1:StudyActivitySchedule {uid: "orphan_schedule_1", name: "Test schedule"});
CREATE (sas2:StudyActivitySchedule {uid: "orphan_schedule_2", name: "Test schedule 2"});
"""

# Test data for Bug #3473115: StudySelection nodes not connected to audit trail
ORPHAN_STUDY_SELECTION_NODES = """
// Create a proper StudySelection connected to audit trail (should NOT be deleted)
CREATE (sa_good:StudyAction {uid: "good_study_action", date: datetime("2024-01-01T00:00:00Z")})
CREATE (ss_good:StudySelection {uid: "good_study_selection", name: "Connected selection"})
CREATE (sa_good)-[:AFTER]->(ss_good);

// Create orphan StudySelection nodes (not connected via AFTER from StudyAction)
CREATE (ss_orphan1:StudySelection {uid: "orphan_study_selection_1", name: "Orphan selection 1"});
CREATE (ss_orphan2:StudySelection {uid: "orphan_study_selection_2", name: "Orphan selection 2"});

// Create an orphan StudySelection with outgoing relationship but no AFTER from StudyAction
CREATE (ss_orphan3:StudySelection {uid: "orphan_study_selection_3", name: "Orphan with outgoing rel"})
CREATE (library_item:LibraryItem {uid: "library_item_1", name: "Some library item"})
CREATE (ss_orphan3)-[:REFERENCES]->(library_item);
"""

TEST_DATA = "".join(
    [
        ACTIVITY_000317_VERSIONING_GAP,
        CATEGORY_CODELIST_TERMS_WITH_SUFFIX,
        MISSING_RETIRED_RELS,
        DUPLICATES_IN_UNITS,
        NEGATIVE_DURATION_HAS_TERM,
        DUPLICATE_TERM_NAMES,
        NOT_LATEST_HAS_VERSION_WITHOUT_END_DATE,
        ISOLATED_ORPHAN_NODES,
        ORPHAN_STUDY_SELECTION_NODES,
    ]
)
