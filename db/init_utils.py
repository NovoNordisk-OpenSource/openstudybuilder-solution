from os import environ

from neo4j.work.transaction import Transaction

DEFAULT_AUTHOR_ID = environ.get(
    "NEO4J_MDR_DEFAULT_AUTHOR_ID", "fd909732-bc9e-492b-a1ed-6e27757a4f00"
)

# Two least-privileged users, provisioned only on Neo4j Enterprise (fine-grained RBAC
# is an Enterprise feature; on Community these are left unset and role provisioning is
# skipped entirely — see provision_roles_and_users). Both optional: if unset,
# provisioning is skipped and the admin user keeps being used everywhere, exactly as
# before this feature existed.
NEO4J_MDR_ROLE_USER = environ.get("NEO4J_MDR_ROLE_USER")
NEO4J_MDR_ROLE_PASSWORD = environ.get("NEO4J_MDR_ROLE_PASSWORD")
NEO4J_STAGING_ROLE_USER = environ.get("NEO4J_STAGING_ROLE_USER")
NEO4J_STAGING_ROLE_PASSWORD = environ.get("NEO4J_STAGING_ROLE_PASSWORD")


def run_querystring(
    tx: Transaction, query: str, parameters=None, **kwparameters
) -> None:
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
        "StudyAuxiliaryDeviceCounter",
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
        "WeekInStudyCounter",
    ]
    for counter_name in counter_names:
        cypher = f"MERGE (c:Counter:{counter_name} {{counterId: '{counter_name}'}}) ON CREATE SET c.count = 0"
        run_querystring(tx, cypher)
        print(f"{cypher}")


def get_neo4j_edition(session) -> str:
    result = session.read_transaction(
        run_querystring_read, "CALL dbms.components() YIELD edition RETURN edition"
    )
    return result[0]["edition"] if result else "unknown"


def provision_roles_and_users(session):
    """Two least-privileged roles so an MDR connection cannot see `:CDISCStaging`
    nodes and a staging connection can see nothing else.

    Enterprise-only (fine-grained RBAC does not exist on Community) and best-effort:
    skipped, loudly, rather than failing the whole init run, since nothing in the app
    may depend on the DENY for correctness — it is defence in depth, not the mechanism.
    `ON GRAPH *` rather than the single named MDR database, this provides more flexibility
    in the design.
    """

    edition = get_neo4j_edition(session)
    if edition != "enterprise":
        print(
            f"Neo4j edition is '{edition}', not 'enterprise' — fine-grained roles are "
            "an Enterprise feature. Skipping role/user provisioning; every connection "
            "keeps using the admin user."
        )
        return

    if not (
        NEO4J_MDR_ROLE_USER
        and NEO4J_MDR_ROLE_PASSWORD
        and NEO4J_STAGING_ROLE_USER
        and NEO4J_STAGING_ROLE_PASSWORD
    ):
        print(
            "NEO4J_MDR_ROLE_USER/NEO4J_MDR_ROLE_PASSWORD/NEO4J_STAGING_ROLE_USER/"
            "NEO4J_STAGING_ROLE_PASSWORD are not all set — skipping role/user "
            "provisioning; every connection keeps using the admin user."
        )
        return

    print("Neo4j edition is 'enterprise' — provisioning the mdr/staging roles")

    for querystring in [
        "CREATE ROLE mdr IF NOT EXISTS AS COPY OF architect",
        "DENY MATCH {*} ON GRAPH * NODES CDISCStaging TO mdr",
        "DENY CREATE ON GRAPH * NODES CDISCStaging TO mdr",
        "DENY SET PROPERTY {*} ON GRAPH * NODES CDISCStaging TO mdr",
        "DENY SET LABEL CDISCStaging ON GRAPH * TO mdr",
        "DENY DELETE ON GRAPH * NODES CDISCStaging TO mdr",
        # Allowlist only: a wildcard DENY on the staging role would also deny
        # CDISCStaging and win over the GRANT below (DENY always wins), which is why
        # this role only ever GRANTs — never DENYs anything. MATCH is the real
        # isolation boundary and stays scoped to CDISCStaging; CREATE/SET LABEL/DELETE
        # are granted on NODES * rather than per staging label, because Neo4j checks
        # those privileges against *every* label on a node (every staging write
        # creates a node with two labels, e.g. (:RawPackage:CDISCStaging)) — scoping
        # them to CDISCStaging alone would make writing any real staging node
        # forbidden. This never widens what the role can see or match, only what
        # labels it may legally touch on a node it was already allowed to create.
        "CREATE ROLE staging IF NOT EXISTS",
        "GRANT MATCH {*} ON GRAPH * NODES CDISCStaging TO staging",
        "GRANT CREATE ON GRAPH * NODES * TO staging",
        "GRANT SET PROPERTY {*} ON GRAPH * NODES CDISCStaging TO staging",
        "GRANT SET LABEL * ON GRAPH * TO staging",
        "GRANT CREATE NEW NODE LABEL ON DATABASE * TO staging",
        "GRANT CREATE NEW PROPERTY NAME ON DATABASE * TO staging",
        "GRANT CREATE NEW RELATIONSHIP TYPE ON DATABASE * TO staging",
        "GRANT DELETE ON GRAPH * NODES * TO staging",
        "GRANT MATCH {*} ON GRAPH * RELATIONSHIPS * TO staging",
        "GRANT CREATE ON GRAPH * RELATIONSHIPS * TO staging",
        "GRANT DELETE ON GRAPH * RELATIONSHIPS * TO staging",
        "GRANT SET PROPERTY {*} ON GRAPH * RELATIONSHIPS * TO staging",
        "GRANT ACCESS ON DATABASE * TO staging",
    ]:
        print(querystring)
        session.write_transaction(run_querystring, querystring)

    for username, password, role in [
        (NEO4J_MDR_ROLE_USER, NEO4J_MDR_ROLE_PASSWORD, "mdr"),
        (NEO4J_STAGING_ROLE_USER, NEO4J_STAGING_ROLE_PASSWORD, "staging"),
    ]:
        querystring = (
            f"CREATE USER `{username}` IF NOT EXISTS "
            "SET PASSWORD $password CHANGE NOT REQUIRED"
        )
        print(
            f"CREATE USER `{username}` IF NOT EXISTS SET PASSWORD ***** CHANGE NOT REQUIRED"
        )
        session.write_transaction(
            run_querystring, querystring, parameters={"password": password}
        )
        querystring = f"GRANT ROLE {role} TO `{username}`"
        print(querystring)
        session.write_transaction(run_querystring, querystring)
