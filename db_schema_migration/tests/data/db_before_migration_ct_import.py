# Data inserted into the MDR database (DATABASE_NAME) before the migration is run.
# Cypher statements delimited by ";\n". Leave empty if the migration needs no pre-existing MDR data.
# WITH "
# MATCH p=(:CTCodelistRoot)--{3}(b)
# RETURN p LIMIT 50
# " AS query
# CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll",ifNotExists: true})
# YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
# RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;
TEST_DATA = """
CREATE RANGE INDEX IF NOT EXISTS FOR ()-[rel:HAS_DATASET_VARIABLE]-() ON (rel.version_number);
CREATE TEXT INDEX IF NOT EXISTS FOR (n:CTCatalogue) ON (n.name);
CREATE TEXT INDEX IF NOT EXISTS FOR (n:CTPackage) ON (n.name);
CREATE TEXT INDEX IF NOT EXISTS FOR (n:Library) ON (n.name);
CREATE CONSTRAINT constraint_CTPackage_uid IF NOT EXISTS FOR (node:CTPackage) REQUIRE (node.uid) IS NODE KEY;
CREATE CONSTRAINT constraint_DatasetVariable_uid IF NOT EXISTS FOR (node:DatasetVariable) REQUIRE (node.uid) IS NODE KEY;
CREATE CONSTRAINT constraint_DataModelCatalogue_name IF NOT EXISTS FOR (node:DataModelCatalogue) REQUIRE (node.name) IS NODE KEY;
CREATE CONSTRAINT constraint_CTCodelistRoot_uid IF NOT EXISTS FOR (node:CTCodelistRoot) REQUIRE (node.uid) IS NODE KEY;
CREATE CONSTRAINT UNIQUE_IMPORT_NAME IF NOT EXISTS FOR (node:`UNIQUE IMPORT LABEL`) REQUIRE (node.`UNIQUE IMPORT ID`) IS UNIQUE;
UNWIND [{name:"SENDIG", properties:{data_model_type:"Implementation Guide"}}] AS row
MERGE (n:DataModelCatalogue{name: row.name}) SET n += row.properties;
UNWIND [{uid:"FWORRESU", properties:{}}, {uid:"GVTPT", properties:{}}, {uid:"GVTPTNUM", properties:{}}, {uid:"GVSTRESN", properties:{}}, {uid:"GVLAT", properties:{}}, {uid:"GVDRVFL", properties:{}}, {uid:"GVREFID", properties:{}}, {uid:"GVDTC", properties:{}}, {uid:"GVMETHOD", properties:{}}, {uid:"GVREASEX", properties:{}}, {uid:"GVELTM", properties:{}}, {uid:"GVUSCHFL", properties:{}}, {uid:"GVSPCUFL", properties:{}}, {uid:"GVCAT", properties:{}}, {uid:"GVDY", properties:{}}, {uid:"GVSPCCND", properties:{}}, {uid:"GVSTRESU", properties:{}}, {uid:"GVGRPID", properties:{}}] AS row
MERGE (n:DatasetVariable{uid: row.uid}) SET n += row.properties;
UNWIND [{_id:40, properties:{name:"DEFINE-XML CT"}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CTCatalogue;
UNWIND [{_id:39, properties:{name:"CDISC", is_editable:false}}] AS row
MERGE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:Library;
UNWIND [{uid:"C165635", properties:{}}, {uid:"C165636", properties:{}}, {uid:"C170448", properties:{}}, {uid:"C170449", properties:{}}, {uid:"C170450", properties:{}}, {uid:"C170451", properties:{}}, {uid:"C170452", properties:{}}, {uid:"C172331", properties:{}}, {uid:"C172332", properties:{}}, {uid:"C176227", properties:{}}, {uid:"C177903", properties:{}}, {uid:"C103329", properties:{}}, {uid:"C100129", properties:{}}, {uid:"C117744", properties:{}}, {uid:"C117745", properties:{}}, {uid:"C66788", properties:{}}, {uid:"C160924", properties:{}}] AS row
MERGE (n:CTCodelistRoot{uid: row.uid}) SET n += row.properties;
UNWIND [{uid:"DEFINE-XML__CT__2019-12-20", properties:{name:"DEFINE-XML CT 2019-12-20", effective_date:datetime('2019-12-20T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:54.142Z')}}, {uid:"DEFINE-XML__CT__2020-03-27", properties:{name:"DEFINE-XML CT 2020-03-27", effective_date:datetime('2020-03-27T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:54.246Z')}}, {uid:"DEFINE-XML__CT__2020-06-26", properties:{name:"DEFINE-XML CT 2020-06-26", effective_date:datetime('2020-06-26T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:54.272Z')}}, {uid:"DEFINE-XML__CT__2020-11-06", properties:{name:"DEFINE-XML CT 2020-11-06", effective_date:datetime('2020-11-06T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:54.39Z')}}, {uid:"DEFINE-XML__CT__2020-12-18", properties:{name:"DEFINE-XML CT 2020-12-18", effective_date:datetime('2020-12-18T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:54.425Z')}}, {uid:"DEFINE-XML__CT__2021-03-26", properties:{name:"DEFINE-XML CT 2021-03-26", effective_date:datetime('2021-03-26T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:54.501Z')}}, {uid:"DEFINE-XML__CT__2021-06-25", properties:{name:"DEFINE-XML CT 2021-06-25", effective_date:datetime('2021-06-25T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:54.541Z')}}, {uid:"DEFINE-XML__CT__2021-09-24", properties:{name:"DEFINE-XML CT 2021-09-24", effective_date:datetime('2021-09-24T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:54.617Z')}}, {uid:"DEFINE-XML__CT__2021-12-17", properties:{name:"DEFINE-XML CT 2021-12-17", effective_date:datetime('2021-12-17T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:54.68Z')}}, {uid:"DEFINE-XML__CT__2022-09-30", properties:{name:"DEFINE-XML CT 2022-09-30", effective_date:datetime('2022-09-30T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:54.897Z')}}, {uid:"DEFINE-XML__CT__2022-12-16", properties:{name:"DEFINE-XML CT 2022-12-16", effective_date:datetime('2022-12-16T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:54.97Z')}}, {uid:"DEFINE-XML__CT__2023-06-30", properties:{name:"DEFINE-XML CT 2023-06-30", effective_date:datetime('2023-06-30T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:55.206Z')}}, {uid:"DEFINE-XML__CT__2023-12-15", properties:{name:"DEFINE-XML CT 2023-12-15", effective_date:datetime('2023-12-15T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:55.347Z')}}, {uid:"DEFINE-XML__CT__2024-03-29", properties:{name:"DEFINE-XML CT 2024-03-29", effective_date:datetime('2024-03-29T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:55.461Z')}}, {uid:"DEFINE-XML__CT__2024-09-27", properties:{name:"DEFINE-XML CT 2024-09-27", effective_date:datetime('2024-09-27T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:55.509Z')}}, {uid:"DEFINE-XML__CT__2025-03-28", properties:{name:"DEFINE-XML CT 2025-03-28", effective_date:datetime('2025-03-28T00:00:00Z'), user_initials:"testuser", import_date:datetime('2025-10-02T12:53:55.615Z')}}] AS row
MERGE (n:CTPackage{uid: row.uid}) SET n += row.properties;
UNWIND [{start: {_id:39}, end: {name:"SENDIG"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:DataModelCatalogue{name: row.end.name})
MERGE (start)-[r:CONTAINS_CATALOGUE]->(end) SET r += row.properties;
UNWIND [{start: {name:"SENDIG"}, end: {uid:"FWORRESU"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVTPT"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVTPTNUM"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVSTRESN"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVLAT"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVDRVFL"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVREFID"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVDTC"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVMETHOD"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVREASEX"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVELTM"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVUSCHFL"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVSPCUFL"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVCAT"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVDY"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVSPCCND"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVSTRESU"}, properties:{}}, {start: {name:"SENDIG"}, end: {uid:"GVGRPID"}, properties:{}}] AS row
MATCH (start:DataModelCatalogue{name: row.start.name})
MATCH (end:DatasetVariable{uid: row.end.uid})
MERGE (start)-[r:HAS_DATASET_VARIABLE]->(end) SET r += row.properties;
UNWIND [{start: {_id:39}, end: {_id:40}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
MERGE (start)-[r:CONTAINS_CATALOGUE]->(end) SET r += row.properties;
UNWIND [{start: {_id:40}, end: {uid:"DEFINE-XML__CT__2019-12-20"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2020-03-27"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2020-06-26"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2020-11-06"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2020-12-18"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2021-03-26"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2021-06-25"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2021-09-24"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2021-12-17"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2022-09-30"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2022-12-16"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2023-06-30"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2023-12-15"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2024-03-29"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2024-09-27"}, properties:{}}, {start: {_id:40}, end: {uid:"DEFINE-XML__CT__2025-03-28"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTPackage{uid: row.end.uid})
MERGE (start)-[r:CONTAINS_PACKAGE]->(end) SET r += row.properties;
UNWIND [{start: {_id:39}, end: {uid:"C100129"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTCodelistRoot{uid: row.end.uid})
MERGE (start)-[r:CONTAINS_CODELIST]->(end) SET r += row.properties;
UNWIND [{start: {_id:40}, end: {uid:"C160924"}, properties:{}}, {start: {_id:40}, end: {uid:"C165635"}, properties:{}}, {start: {_id:40}, end: {uid:"C165636"}, properties:{}}, {start: {_id:40}, end: {uid:"C170448"}, properties:{}}, {start: {_id:40}, end: {uid:"C170449"}, properties:{}}, {start: {_id:40}, end: {uid:"C170450"}, properties:{}}, {start: {_id:40}, end: {uid:"C170451"}, properties:{}}, {start: {_id:40}, end: {uid:"C170452"}, properties:{}}, {start: {_id:40}, end: {uid:"C172331"}, properties:{}}, {start: {_id:40}, end: {uid:"C172332"}, properties:{}}, {start: {_id:40}, end: {uid:"C176227"}, properties:{}}, {start: {_id:40}, end: {uid:"C177903"}, properties:{}}, {start: {_id:40}, end: {uid:"C103329"}, properties:{}}, {start: {_id:40}, end: {uid:"C117744"}, properties:{}}, {start: {_id:40}, end: {uid:"C117745"}, properties:{}}, {start: {_id:40}, end: {uid:"C66788"}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:CTCodelistRoot{uid: row.end.uid})
MERGE (start)-[r:HAS_CODELIST]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
DROP CONSTRAINT UNIQUE_IMPORT_NAME;
"""

# Data inserted into the CDISC staging database (STAGING_DATABASE_NAME) before the migration is run.
# Cypher statements delimited by ";\n".
# It must reflect the staging database as it is BEFORE the migration:
#   - nodes carry NO :CDISCStaging label yet
#   - relationships use the OLD types listed in migration_ct_import.REL_TYPE_RENAMES
#   - nodes use the OLD labels listed in migration_ct_import.LABEL_RENAMES (e.g. :Version)
# Sampled from a real CDISC staging database: one relationship per distinct (start labels, type, end labels)
# pattern, plus one node for any label not covered by a relationship.
STAGING_TEST_DATA = """
CREATE CONSTRAINT UNIQUE_IMPORT_NAME FOR (node:`UNIQUE IMPORT LABEL`) REQUIRE (node.`UNIQUE IMPORT ID`) IS UNIQUE;
UNWIND [{_id:3397663, properties:{method:"Use preferred term", name:"Percutaneous Coronary Intervention for ST Elevation Myocardial Infarction-Stable-Over 12 Hours From Symptom Onset"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:SponsorName;
UNWIND [{_id:3334306, properties:{conceptId:"C115797"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:VersionedTerm;
UNWIND [{href:"/mdr/cdashig/1-1-1/scenarios/DA.Denormalized", properties:{version_number:"1-1-1", label:"Drug Accountability (Denormalized)", title:"Drug Accountability (Denormalized)", catalogue:"CDASHIG", ordinal:"1"}}] AS row
CREATE (n:DataModelScenario{href: row.href}) SET n += row.properties;
UNWIND [{version_number:"9-0", catalogue:"FBDE", properties:{data_model_type:"Foundational Model", library:"Sponsor", import_date_time:datetime('2025-10-02T15:40:05.9188+02:00'), author_id:"CDISC_IMPORT"}}] AS row
CREATE (n:DataModelImport{version_number: row.version_number, catalogue: row.catalogue}) SET n += row.properties;
UNWIND [{_id:2492139, properties:{submissionValue:"QSCAT", synonyms:["Category of Questionnaire"], preferredTerm:"CDISC Questionnaire Category Terminology", name:"Category of Questionnaire", definition:"A grouping of observations within the Questionnaire domain.", extensible:"true"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:GroupedCodelistProperties;
UNWIND [{_id:1669286, properties:{conceptId:"C100000"}}, {_id:1802694, properties:{conceptId:"C132367"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:GroupedTerm;
UNWIND [{_id:3326511, properties:{conceptId:"C100129"}}, {_id:3327306, properties:{conceptId:"C141656"}}, {_id:3327307, properties:{conceptId:"C141657"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:VersionedCodelist;
UNWIND [{_id:10, properties:{submissionValue:"QSCAT", synonyms:["Category of Questionnaire"], preferredTerm:"CDISC Questionnaire Category Terminology", name:"Category of Questionnaire", conceptId:"C100129", definition:"A grouping of observations within the Questionnaire domain.", extensible:"true"}}, {_id:2, properties:{submissionValue:"FTCAT", synonyms:["Category of Functional Test"], preferredTerm:"CDISC Functional Test Category Terminology", name:"Category of Functional Test", conceptId:"C115304", definition:"A grouping of observations within the Functional Test domain.", extensible:"true"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:RawCodelist;
UNWIND [{_id:3317789, properties:{solution:"Ignoring data value with extra quotes from package SEND CT 2018-12-21"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:InconsistencySolution;
UNWIND [{name:"FBDE v0.2", properties:{registration_status:"Final", effective_date:"2025-08-25", description:"File Based Data Exchange", version_number:"9-0", href:"/mdr/fbde/9-0", source:"Sponsor Lab Data Specifications"}}] AS row
CREATE (n:Version{name: row.name}) SET n += row.properties;
UNWIND [{uid:"job-1", properties:{kind:"import", status:"SUCCEEDED", effective_date:"2014-09-26", author_id:"CDISC_IMPORT"}}] AS row
CREATE (n:Job{uid: row.uid}) SET n += row.properties;
UNWIND [{_id:0, properties:{effectiveDate:"2014-09-26"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:RawPackage;
UNWIND [{_id:1668840, properties:{conceptId:"C100129"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:GroupedCodelist;
UNWIND [{_id:3328004, properties:{submissionValue:"QSCAT", synonyms:["Category of Questionnaire"], preferredTerm:"CDISC Questionnaire Category Terminology", name:"Category of Questionnaire", definition:"A grouping of observations within the Questionnaire domain.", extensible:"true"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:CodelistVersion;
UNWIND [{_id:3361367, properties:{preferredTerm:"Percutaneous Coronary Intervention for ST Elevation Myocardial Infarction-Stable-Over 12 Hours From Symptom Onset", definition:"A percutaneous coronary intervention is necessary for a myocardial infarction that presents with ST segment elevation and the subject does not have recurrent or persistent symptoms, symptoms of heart failure or ventricular arrhythmia. The presentation is past twelve hours since onset of symptoms."}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:TermVersion;
UNWIND [{name:"Finding", version_number:"9-0", catalogue:"FBDE", properties:{description:"Finding related data", href:"/mdr/fbde/9-0/classes/Finding", subclasses:[]}}] AS row
CREATE (n:DataModelClass{name: row.name, version_number: row.version_number, catalogue: row.catalogue}) SET n += row.properties;
UNWIND [{_id:2736833, properties:{property:"definition", inconsistency:"unwanted quotes"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:InconsistentCodelistProperties;
UNWIND [{_id:2625993, properties:{property:"definition", catalogues_1:["SDTM CT 2017-03-31", "SDTM CT 2017-03-31", "SEND CT 2017-03-31"], value_2:"A measurement of the folate hydrolase mRNA gin a biological specimen.", inconsistency:"conflicting values", catalogues_2:["SEND CT 2017-03-31"], value_1:"A measurement of the folate hydrolase mRNA in a biological specimen."}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:InconsistentTermProperties;
UNWIND [{_id:1, properties:{`_links.self.type`:"Terminology", registrationStatus:"Final", name:"QS-FT CT 2014-09-26", `_links.self.title`:"QS-FT Controlled Terminology Package 19 Effective 2014-09-26", description:"CDISC Controlled Terminology for QS-FT is the set of CDISC-developed or CDISC-adopted standard expressions (values) used with data items within CDISC-defined QS-FT datasets.", `_links.self.href`:"/mdr/ct/packages/qs-ftct-2014-09-26", source:"QS-FT Controlled Terminology developed by the CDISC Terminology Team in collaboration with the National Cancer Institute's Enterprise Vocabulary Services (EVS)", label:"QS-FT Controlled Terminology Package 19 Effective 2014-09-26", version:"2014-09-26", effectiveDate:"2014-09-26"}}, {_id:917048, properties:{`_links.self.type`:"Terminology", registrationStatus:"Final", `_links.self.title`:"Define-XML Controlled Terminology Package 46 Effective 2021-06-25", name:"DEFINE-XML CT 2021-06-25", description:"CDISC Controlled Terminology for Define-XML is the set of CDISC-developed or CDISC-adopted standard expressions (values) used with data items within CDISC-defined DEFINE-XML datasets.", label:"Define-XML Controlled Terminology Package 46 Effective 2021-06-25", source:"Define-XML Controlled Terminology developed by the CDISC Terminology Team in collaboration with the National Cancer Institute's Enterprise Vocabulary Services (EVS)", `_links.self.href`:"/mdr/ct/packages/define-xmlct-2021-06-25", version:"2021-06-25", effectiveDate:"2021-06-25"}}, {_id:997730, properties:{`_links.self.type`:"Terminology", registrationStatus:"Final", description:"CDISC Controlled Terminology for Define-XML is the set of CDISC-developed or CDISC-adopted standard expressions (values) used with data items within CDISC-defined DEFINE-XML datasets.", label:"Define-XML Controlled Terminology Package 47 Effective 2021-09-24", source:"Define-XML Controlled Terminology developed by the CDISC Terminology Team in collaboration with the National Cancer Institute's Enterprise Vocabulary Services (EVS)", version:"2021-09-24", `_links.priorVersion.href`:"/mdr/ct/packages/define-xmlct-2021-06-25", `_links.priorVersion.title`:"Define-XML Controlled Terminology Package 46 Effective 2021-06-25", `_links.self.title`:"Define-XML Controlled Terminology Package 47 Effective 2021-09-24", name:"DEFINE-XML CT 2021-09-24", `_links.priorVersion.type`:"Terminology", `_links.self.href`:"/mdr/ct/packages/define-xmlct-2021-09-24", effectiveDate:"2021-09-24"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:RawCatalogue;
UNWIND [{_id:11, properties:{submissionValue:"ADAS-COG", synonyms:["ADC"], preferredTerm:"Alzheimer's Disease Assessment Scale-Cognitive CDISC Version Questionnaire", conceptId:"C100762", definition:"The CDISC version of the Alzheimer's Disease Assessment Scale-Cognitive (ADAS-Cog CDISC Version) containing 15 summary-level tests. This version is based on combining the total pool of ADAS-Cog tests that were observed during a review of multiple case report forms administered in clinical trials of Alzheimer's disease, as well as the CRF administered in the Alzheimer's Disease Neuroimaging Initiative (ADNI) observational study. (Modified from Mohs RC, Rosen WG, Davis KL. The Alzheimer's disease assessment scale: an instrument for assessing treatment efficacy. Psychopharmacol Bull 1983;19(3):448-450. Rosen WG, Mohs RC, Davis KL. A new rating scale for Alzheimer's disease. Am J Psychiatry 1984;141(11):1356-1364. Mohs RC, Knopman D, Petersen RC et al. Development of cognitive instruments for use in clinical trials of antidementia drugs: additions to the Alzheimer's Disease Assessment Scale that broaden its scope. The Alzheimer's Disease Cooperative Study. Alzheimer Dis Assoc Disord 1997;11 Suppl 2:S13-S21. Wouters H, van Gool WA, Schmand B, Lindeboom R. Revising the ADAS-cog for a more accurate assessment of cognitive impairment. Alzheimer Dis Assoc Disord 2008;22(3):236-244.)."}}, {_id:13090, properties:{submissionValue:"Percutaneous Coronary Intervention (PCI) for St Elevation Myocardial Infarction (STEMI) (Stable, >12 Hrs From Symptom Onset)", preferredTerm:"Percutaneous Coronary Intervention for ST Elevation Myocardial Infarction-Stable-Over 12 Hours From Symptom Onset", conceptId:"C100000", definition:"A percutaneous coronary intervention is necessary for a myocardial infarction that presents with ST segment elevation and the subject does not have recurrent or persistent symptoms, symptoms of heart failure or ventricular arrhythmia. The presentation is past twelve hours since onset of symptoms."}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:RawTerm;
UNWIND [{_id:2537710, properties:{preferredTerm:"Percutaneous Coronary Intervention for ST Elevation Myocardial Infarction-Stable-Over 12 Hours From Symptom Onset", definition:"A percutaneous coronary intervention is necessary for a myocardial infarction that presents with ST segment elevation and the subject does not have recurrent or persistent symptoms, symptoms of heart failure or ventricular arrhythmia. The presentation is past twelve hours since onset of symptoms."}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:GroupedTermProperties;
UNWIND [{_id:2647823, properties:{property:"terms", inconsistency:"Codelist definitions contain inconsistent sets of terms"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:InconsistentCodelistTerms;
UNWIND [{_id:3433974, properties:{simple_datatype:"Character", implements_variables:[], name:"UNITCOLL", length:"40", version_number:"9-0", href:"/mdr/fbde/9-0/classes/Finding/variables/UNITCOLL", label:"Collected unit. UNITCOLL should be compliant with CDISC CT codelist UNIT (e.g. 'mmol/L') or Novo Nordisk-defined extensions.  Supplier should not perform unit-based conversion of results.  UNITCOLL should be NULL for unitless data, e.g. pH.", catalogue:"FBDE", ordinal:"12"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:DataModelVariable;
UNWIND [{start: {_id:3397663}, end: {_id:3361367}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:SPONSOR_NAME_FOR]->(end) SET r += row.properties;
UNWIND [{start: {_id:3326511}, end: {_id:1668840}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_SOURCE_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {_id:1802694}, end: {_id:2625993}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_INCONSISTENCY]->(end) SET r += row.properties;
UNWIND [{start: {_id:0}, end: {_id:1669286}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_GROUPED_TERM]->(end) SET r += row.properties;
UNWIND [{start: {_id:0}, end: {_id:1668840}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_GROUPED_CODELIST]->(end) SET r += row.properties;
UNWIND [{start: {_id:1668840}, end: {_id:10}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:SOURCE_CODELIST_DEF]->(end) SET r += row.properties;
UNWIND [{start: {_id:3361367}, end: {_id:2537710}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:FROM_PACKAGE]->(end) SET r += row.properties;
UNWIND [{start: {_id:3327306}, end: {_id:3327307}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:PAIRED_WITH_CODES]->(end) SET r += row.properties;
UNWIND [{start: {_id:997730}, end: {_id:917048}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_PRIOR_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {_id:10}, end: {_id:11}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_RAW_TERM]->(end) SET r += row.properties;
UNWIND [{start: {_id:1669286}, end: {_id:13090}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:SOURCE_TERM_DEF]->(end) SET r += row.properties;
UNWIND [{start: {_id:3326511}, end: {_id:3328004}, properties:{end_date:"2017-06-30", version:1, start_date:"2014-09-26"}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_VERSION]->(end) SET r += row.properties;
UNWIND [{start: {_id:2736833}, end: {_id:3317789}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_SOLUTION]->(end) SET r += row.properties;
UNWIND [{start: {_id:3326511}, end: {_id:3334306}, properties:{submissionValue:"GOSE", start_date:"2014-09-26"}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_TERM]->(end) SET r += row.properties;
UNWIND [{start: {_id:0}, end: {_id:1}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_RAW_CATALOGUE]->(end) SET r += row.properties;
UNWIND [{start: {_id:1668840}, end: {_id:2492139}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_GROUPED_PROPERTIES]->(end) SET r += row.properties;
UNWIND [{start: {_id:1}, end: {_id:2}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:HAS_RAW_CODELIST]->(end) SET r += row.properties;
UNWIND [{start: {catalogue:"FBDE", version_number:"9-0"}, end: {name:"FBDE v0.2"}, properties:{}}] AS row
MATCH (start:DataModelImport{version_number: row.start.version_number, catalogue: row.start.catalogue})
MATCH (end:Version{name: row.end.name})
CREATE (start)-[r:INCLUDES]->(end) SET r += row.properties;
UNWIND [{start: {name:"Finding", catalogue:"FBDE", version_number:"9-0"}, end: {_id:3433974}, properties:{}}] AS row
MATCH (start:DataModelClass{name: row.start.name, version_number: row.start.version_number, catalogue: row.start.catalogue})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:CONTAINS]->(end) SET r += row.properties;
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
DROP CONSTRAINT UNIQUE_IMPORT_NAME;
"""
