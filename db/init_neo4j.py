from neo4j import GraphDatabase
from os import environ
from neo4j.work.transaction import Transaction
from db_schema import build_schema_queries, SCHEMA_CLEAR_QUERY

from datetime import datetime

DATABASE = environ.get("NEO4J_MDR_DATABASE")
DATABASE_DBNAME = environ.get("NEO4J_MDR_DATABASE_DBNAME", None)
NEO4J_MDR_CLEAR_DATABASE = environ.get("NEO4J_MDR_CLEAR_DATABASE", "false")
NEO4J_MDR_BACKUP_DATABASE = environ.get("NEO4J_MDR_BACKUP_DATABASE", "false")
CLEAR_DATABASE = NEO4J_MDR_CLEAR_DATABASE.lower() == "true"
BACKUP_DATABASE = NEO4J_MDR_BACKUP_DATABASE.lower() == "true"
DEFAULT_AUTHOR_ID = environ.get("NEO4J_MDR_DEFAULT_AUTHOR_ID", "fd909732-bc9e-492b-a1ed-6e27757a4f00")

uri = "neo4j://{}:{}".format(
    environ.get("NEO4J_MDR_HOST"), environ.get("NEO4J_MDR_BOLT_PORT")
)
driver = GraphDatabase.driver(
    uri,
    auth=(environ.get("NEO4J_MDR_AUTH_USER"), environ.get("NEO4J_MDR_AUTH_PASSWORD")),
)


def run_querystring(tx: Transaction, query: str, parameters = None , **kwparameters) -> None:
    tx.run(query, parameters, **kwparameters).consume()


def run_querystring_read(tx: Transaction, query: str):
    result = tx.run(query)
    return result.data()


# Using merge so it wont fail if init is run multiple times
# Used as the default set of Template Parameter allowing the end user to create Objectif Template for example
def pre_load_template_parameter_tree(tx: Transaction):
    cypher = """
        // activity
        MERGE (activity:TemplateParameter {name: "Activity"})
        // activity sub group
        MERGE (activity_sub_group:TemplateParameter {name: "ActivitySubGroup"})
        // activity group
        MERGE (activity_group:TemplateParameter {name: "ActivityGroup"})
        // activity-instance
        MERGE (activity_instance:TemplateParameter {name: "ActivityInstance"})

        // reminders
        MERGE (reminder:TemplateParameter {name: "Reminder"})
        MERGE (reminder)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        
        // interventions
        MERGE (interventions:TemplateParameter {name: "Intervention"})
        MERGE (compoundDosing:TemplateParameter {name: "CompoundDosing"})
        MERGE (compoundDosing)-[:HAS_PARENT_PARAMETER]->(interventions)
        MERGE (compound:TemplateParameter {name: "Compound"})
        MERGE (compound)-[:HAS_PARENT_PARAMETER]->(compoundDosing)
        
        // special-purposes
        MERGE (special_purposes:TemplateParameter {name: "SpecialPurpose"})
        MERGE (special_purposes)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        
        // findings
        MERGE (findings:TemplateParameter {name: "Finding"})
        MERGE (findings)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        MERGE (categoricFinding:TemplateParameter {name: "CategoricFinding"})
        MERGE (categoricFinding)-[:HAS_PARENT_PARAMETER]->(findings)
        MERGE (ratingScale:TemplateParameter {name: "RatingScale"})
        MERGE (ratingScale)-[:HAS_PARENT_PARAMETER]->(categoricFinding)
        MERGE (laboratoryActivity:TemplateParameter {name: "LaboratoryActivity"})
        MERGE (laboratoryActivity)-[:HAS_PARENT_PARAMETER]->(categoricFinding)
        MERGE (numericFinding:TemplateParameter {name: "NumericFinding"})
        MERGE (numericFinding)-[:HAS_PARENT_PARAMETER]->(findings)
        MERGE (laboratoryActivity)-[:HAS_PARENT_PARAMETER]->(numericFinding)
        MERGE (textualFinding:TemplateParameter {name: "TextualFinding"})
        MERGE (textualFinding)-[:HAS_PARENT_PARAMETER]->(findings)

        // events
        MERGE (events:TemplateParameter {name: "Event"})
        MERGE (events)-[:HAS_PARENT_PARAMETER]->(activity_instance)

        // simple concepts
        MERGE (simple_concepts:TemplateParameter {name:"SimpleConcept"})
        MERGE (numeric_values:TemplateParameter {name:"NumericValue"})
        MERGE (numeric_values)-[:HAS_PARENT_PARAMETER]->(simple_concepts)
        MERGE (numeric_value_with_unit:TemplateParameter {name:"NumericValueWithUnit"})
        MERGE (numeric_value_with_unit)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (text_values:TemplateParameter {name:"TextValue"})
        MERGE (text_values)-[:HAS_PARENT_PARAMETER]->(simple_concepts)
        MERGE (visit_names:TemplateParameter {name:"VisitName"})
        MERGE (visit_names)-[:HAS_PARENT_PARAMETER]->(text_values)
        MERGE (dose_value:TemplateParameter {name:"DoseValue"})
        MERGE (dose_value)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (study_days:TemplateParameter {name:"StudyDay"})
        MERGE (study_days)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (study_weeks:TemplateParameter {name:"StudyWeek"})
        MERGE (study_weeks)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (study_duration_days:TemplateParameter {name:"StudyDurationDays"})
        MERGE (study_duration_days)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (study_duration_weeks:TemplateParameter {name:"StudyDurationWeeks"})
        MERGE (study_duration_weeks)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (week_in_study:TemplateParameter {name:"WeekInStudy"})
        MERGE (week_in_study)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (time_points:TemplateParameter {name:"TimePoint"})
        MERGE (time_points)-[:HAS_PARENT_PARAMETER]->(simple_concepts)
        MERGE (lag_time:TemplateParameter {name:"LagTime"})
        MERGE (lag_time)-[:HAS_PARENT_PARAMETER]->(numeric_values)

        // Units
        MERGE (unit:TemplateParameter {name: "Unit"})

        // Unit subsets
        MERGE (age_unit:TemplateParameter {name: "Age Unit"})
        MERGE (age_unit)-[:HAS_PARENT_PARAMETER]->(unit)
        MERGE (study_time:TemplateParameter {name: "Study Time"})
        MERGE (study_time)-[:HAS_PARENT_PARAMETER]->(unit)
        MERGE (time_unit:TemplateParameter {name: "Time Unit"})
        MERGE (time_unit)-[:HAS_PARENT_PARAMETER]->(unit)
        MERGE (dose_unit:TemplateParameter {name: "Dose Unit"})
        MERGE (dose_unit)-[:HAS_PARENT_PARAMETER]->(unit)
        MERGE (strength_unit:TemplateParameter {name: "Strength Unit"})
        MERGE (strength_unit)-[:HAS_PARENT_PARAMETER]->(unit)
        
        // comparator
        MERGE (comparator:TemplateParameter {name: "Comparator"})

        //Study Endpoint
        MERGE (endpoint:TemplateParameter {name: "StudyEndpoint"})
    """
    run_querystring(tx, cypher)


# using merge so it wont fail if init is run multiple times.
def create_special_template_parameters(tx: Transaction):
    # (re)-creates the NA template parameter value, which is an instance of every template parameter
    cypher = f"""
    MERGE (r:TemplateParameterValueRoot{{uid: "NA"}})
    WITH r
    OPTIONAL MATCH (r)-[x:HAS_VERSION|LATEST|LATEST_FINAL]->()
    DELETE x
    WITH r
    MERGE (r)-[:LATEST]->(v:TemplateParameterValue{{name: "NA"}})
    MERGE (r)-[:LATEST_FINAL]->(v)
    MERGE (r)-[:HAS_VERSION{{change_description: "Initial version", start_date: datetime(), end_date: datetime(), status: "Final", author_id: "{DEFAULT_AUTHOR_ID}", version: "1.0"}}]->(v)
    WITH r
    MATCH (n:TemplateParameter) 
    MERGE (n)-[:HAS_VALUE]->(r)
    """
    run_querystring(tx, cypher)

# Preload :Counter nodes for all relevant types, as if :Counter nodes doesn't exist and API is launched with a few process workers
# and some request is sent, then the code to create :Counter is not atomic and different workers duplicate :Counter nodes.
def pre_load_counter_nodes(tx: Transaction):
    counter_names = [
        "ActiveSubstanceCounter",
        "ActivityCounter",
        "ActivityDefinitionCounter",
        "ActivityGroupCounter",
        "ActivityGroupingCounter",
        "ActivityInstanceClassCounter",
        "ActivityInstanceCounter",
        "ActivityInstructionCounter",
        "ActivityInstructionTemplateCounter",
        "ActivityItemClassCounter",
        "ActivityItemCounter",
        "ActivitySubGroupCounter",
        "BrandCounter",
        "CTCodelistCounter",
        "CTConfigCounter",
        "CTTermCounter",
        "CategoricFindingCounter",
        "ClinicalProgrammeCounter",
        "CompoundAliasCounter",
        "CompoundCounter",
        "CriteriaCounter",
        "CriteriaPreInstanceCounter",
        "CriteriaTemplateCounter",
        "DataSupplierCounter",
        "DictionaryCodelistCounter",
        "DictionaryTermCounter",
        "EndpointCounter",
        "EndpointTemplateCounter",
        "EventCounter",
        "FootnoteCounter",
        "FootnotePreInstanceCounter",
        "FootnoteTemplateCounter",
        "LagTimeCounter",
        "MedicinalProductCounter",
        "NumericFindingCounter",
        "NumericValueCounter",
        "NumericValueWithUnitCounter",
        "ObjectiveCounter",
        "ObjectiveTemplateCounter",
        "OdmFormCounter",
        "OdmItemCounter",
        "OdmItemGroupCounter",
        "OdmStudyEventCounter",
        "OdmVendorAttributeCounter",
        "OdmVendorNamespaceCounter",
        "PharmaceuticalProductCounter",
        "ProjectCounter",
        "StudyActivityCounter",
        "StudyActivityGroupCounter",
        "StudyActivityInstanceCounter",
        "StudyActivityInstructionCounter",
        "StudyActivityScheduleCounter",
        "StudyActivitySubGroupCounter",
        "StudyArmCounter",
        "StudyBranchArmCounter",
        "StudyCohortCounter",
        "StudyCompoundCounter",
        "StudyCompoundDosingCounter",
        "StudyCounter",
        "StudyCriteriaCounter",
        "StudyDayCounter",
        "StudyDefinitionDocumentCounter",
        "StudyDesignCellCounter",
        "StudyDiseaseMilestoneCounter",
        "StudyDurationDaysCounter",
        "StudyDurationWeeksCounter",
        "StudyElementCounter",
        "StudyEndpointCounter",
        "StudyEpochCounter",
        "StudyObjectiveCounter",
        "StudySoAFootnoteCounter",
        "StudySoAGroupCounter",
        "StudyStandardVersionCounter",
        "StudyVersionCounter",
        "StudyVisitCounter",
        "StudyVisitGroupCounter",
        "StudyWeekCounter",
        "TemplateParameterTermCounter",
        "TemplateParameterValueCounter",
        "TextValueCounter",
        "TextualFindingCounter",
        "TimePointCounter",
        "TimeframeCounter",
        "TimeframeTemplateCounter",
        "UnitDefinitionCounter",
        "VisitNameCounter",
        "WeekInStudyCounter"
    ]
    for counter_name in counter_names:
        cypher = f"MERGE (c:Counter:{counter_name} {{counterId: '{counter_name}'}}) ON CREATE SET c.count = 0"
        run_querystring(tx, cypher)
        print(f"{cypher}")


def make_db_name():
    if (
        DATABASE_DBNAME is None
        or DATABASE_DBNAME.lower() == ""
        or DATABASE_DBNAME.lower().startswith("auto")
    ):
        now = datetime.now()
        date_str = now.strftime("%Y.%m.%d-%H.%M")
        db_name = "{}-{}".format(DATABASE, date_str)
        print(f"Using auto-generated database name: '{db_name}'")
    else:
        db_name = DATABASE_DBNAME
        print(f"Using provided database name: '{db_name}'")
    return db_name


print("\n-- Clear and backup --")
print(f"Clear database: {CLEAR_DATABASE}")
print(f"Keep backup of database: {BACKUP_DATABASE}")
# Clear database if requested
if CLEAR_DATABASE:
    with driver.session(database="system") as session:
        querystring = (
            "SHOW ALIASES FOR DATABASE YIELD * WHERE name='{}' RETURN database".format(
                DATABASE
            )
        )
        db_name_reply = session.read_transaction(run_querystring_read, querystring)
        if db_name_reply:
            db_name = db_name_reply[0]["database"]
            print(f"Dropping alias '{DATABASE}' for database '{db_name}'")
            querystring = "DROP ALIAS `{}` IF EXISTS FOR DATABASE".format(DATABASE)
            session.write_transaction(run_querystring, querystring)
            if not BACKUP_DATABASE:
                # Delete the database
                querystring = "DROP DATABASE `{}` IF EXISTS".format(db_name)
                print("Dropping database '{}'".format(db_name))
                session.write_transaction(run_querystring, querystring)
            else:
                print("Keeping database '{}'".format(db_name))
        else:
            querystring = "SHOW DATABASE `{}`".format(DATABASE)
            existing = session.read_transaction(run_querystring_read, querystring)
            if len(existing) > 0:
                print(
                    "Database '{}' already exists but is not an alias".format(DATABASE)
                )
                if BACKUP_DATABASE:
                    raise RuntimeError(
                        "Unable to keep a backup since the database is not an alias"
                    )
                else:
                    querystring = "DROP DATABASE `{}` IF EXISTS".format(DATABASE)
                    print("Dropping database '{}'".format(DATABASE))
                    session.write_transaction(run_querystring, querystring)

# Create database and alias if not exists
print("\n-- Creating database and alias --")
with driver.session(database="system") as session:
    querystring = "SHOW DATABASE `{}`".format(DATABASE)
    existing = session.read_transaction(run_querystring_read, querystring)
    if len(existing) > 0:
        print(
            "Database (or alias) '{}' already exists, skipping create step".format(
                DATABASE
            )
        )
    else:
        new_db_name = make_db_name()
        if new_db_name.lower() == DATABASE.lower():
            raise RuntimeError(
                "Database name and alias must be different. Provided db name: {new_db_name}, alias: {DATABASE}"
            )
        print("Creating database '{}'".format(new_db_name))
        querystring = "CREATE DATABASE `{}` IF NOT EXISTS".format(new_db_name)
        session.write_transaction(run_querystring, querystring)
        print("Creating alias '{}' for database '{}'".format(DATABASE, new_db_name))
        querystring = "CREATE ALIAS `{}` IF NOT EXISTS FOR DATABASE `{}`".format(
            DATABASE, new_db_name
        )
        session.write_transaction(run_querystring, querystring)

# Todo: Additional system db operations (set up roles and permissions)

# Create indexes and constraints
print("\n-- Setting up indexes and constraints on specific nodes --")
with driver.session(database=DATABASE) as session:
    print(SCHEMA_CLEAR_QUERY)
    session.write_transaction(run_querystring, SCHEMA_CLEAR_QUERY)

    for query in build_schema_queries():
        print(query)
        session.write_transaction(run_querystring, query)

    print(
        "\n-- Preloading TemplateParameter tree (Activity, Activity Group, Findings, Dose unit...) --"
    )
    with session.begin_transaction() as tx:
        pre_load_template_parameter_tree(tx)

    print("\n-- Creating special template parameters (NA...) --")
    with session.begin_transaction() as tx:
        create_special_template_parameters(tx)

    print(
        "\n-- Preloading :Counter nodes --"
    )
    with session.begin_transaction() as tx:
        pre_load_counter_nodes(tx)

    session.close()

driver.close()
