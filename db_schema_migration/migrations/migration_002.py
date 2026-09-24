"""Schema migrations needed for release to PROD post-February 2023."""

import asyncio
import os

import aiohttp
from import_sponsor_data.importers.run_import_activities import Activities

from migrations.common import migrate_ct_config_values, migrate_indexes_and_constraints
from migrations.utils.utils import get_db_connection, get_logger

logger = get_logger(os.path.basename(__file__))
DB_CONNECTION = get_db_connection()


async def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Release-specific migrations
    migrate_syntax_templates_and_instances(DB_CONNECTION)

    # Default study preferred time unit
    migrate_study_preferred_time_unit(DB_CONNECTION)

    # Sort out versioning relationships
    migrate_item_versioning(DB_CONNECTION)

    # Adding sequence_id on all Syntax Root nodes
    migrate_syntax_sequence_id(DB_CONNECTION)

    # Activity instance class nodes and relationship between ActivityInstanceValue and ActivityInstanceClassRoot
    await migrate_activity_instance_class_relationship(DB_CONNECTION)

    # ActivityItemClass relationship to CTTerm that represents Role and Data type
    migrate_role_and_data_type(DB_CONNECTION)

    # ActivityInstanceValue dummy relationship to ActivityValue when missing
    migrate_activity_instances_without_activity(DB_CONNECTION)

    # Renaming OdmTemplate* nodes
    migrate_odm_templates(DB_CONNECTION)


def run():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


def migrate_syntax_templates_and_instances(db_connection):
    logger.info("Migrating Syntax Templates & Instances...")

    logger.info(
        """Adding `SyntaxInstanceRoot` and `SyntaxInstanceValue` labels.
        Renaming `CONTAINS_ACTIVITY_INSTRUCTION` relationship to `CONTAINS_SYNTAX_INSTANCE`"""
    )
    db_connection.cypher_query(
        """MATCH (:Library)-[rel:CONTAINS_ACTIVITY_INSTRUCTION]->(q:ActivityInstructionRoot)
        SET q:SyntaxInstanceRoot
        WITH *
        CALL apoc.refactor.setType(rel, 'CONTAINS_SYNTAX_INSTANCE') YIELD input, output
        MATCH (q)-[:LATEST|:LATEST_DRAFT|:LATEST_FINAL|:HAS_VERSION]-(v)
        SET v:SyntaxInstanceValue
        RETURN *"""
    )
    logger.info(
        """Adding `SyntaxInstanceRoot`, `SyntaxInstanceValue` and `SyntaxIndexingInstanceRoot`, `SyntaxIndexingInstanceValue` labels.
        Renaming `CONTAINS_CRITERIA` relationship to `CONTAINS_SYNTAX_INSTANCE`"""
    )
    db_connection.cypher_query(
        """MATCH (:Library)-[rel:CONTAINS_CRITERIA]->(q:CriteriaRoot)
        SET q:SyntaxInstanceRoot
        SET q:SyntaxIndexingInstanceRoot
        WITH *
        CALL apoc.refactor.setType(rel, 'CONTAINS_SYNTAX_INSTANCE') YIELD input, output
        MATCH (q)-[:LATEST|:LATEST_DRAFT|:LATEST_FINAL|:HAS_VERSION]-(v)
        SET v:SyntaxInstanceValue
        SET v:SyntaxIndexingInstanceValue
        RETURN *"""
    )
    logger.info(
        """Adding `SyntaxInstanceRoot`, `SyntaxInstanceValue` and `SyntaxIndexingInstanceRoot`, `SyntaxIndexingInstanceValue` labels.
        Renaming `CONTAINS_ENDPOINT` relationship to `CONTAINS_SYNTAX_INSTANCE`"""
    )
    db_connection.cypher_query(
        """MATCH (:Library)-[rel:CONTAINS_ENDPOINT]->(q:EndpointRoot)
        SET q:SyntaxInstanceRoot
        SET q:SyntaxIndexingInstanceRoot
        WITH *
        CALL apoc.refactor.setType(rel, 'CONTAINS_SYNTAX_INSTANCE') YIELD input, output
        MATCH (q)-[:LATEST|:LATEST_DRAFT|:LATEST_FINAL|:HAS_VERSION]-(v)
        SET v:SyntaxInstanceValue
        SET v:SyntaxIndexingInstanceValue
        RETURN *"""
    )
    logger.info(
        """Adding `SyntaxInstanceRoot`, `SyntaxInstanceValue` and `SyntaxIndexingInstanceRoot`, `SyntaxIndexingInstanceValue` labels.
        Renaming `CONTAINS_OBJECTIVE` relationship to `CONTAINS_SYNTAX_INSTANCE`"""
    )
    db_connection.cypher_query(
        """MATCH (:Library)-[rel:CONTAINS_OBJECTIVE]->(q:ObjectiveRoot)
        SET q:SyntaxInstanceRoot
        SET q:SyntaxIndexingInstanceRoot
        WITH *
        CALL apoc.refactor.setType(rel, 'CONTAINS_SYNTAX_INSTANCE') YIELD input, output
        MATCH (q)-[:LATEST|:LATEST_DRAFT|:LATEST_FINAL|:HAS_VERSION]-(v)
        SET v:SyntaxInstanceValue
        SET v:SyntaxIndexingInstanceValue
        RETURN *"""
    )
    logger.info("""Adding `SyntaxInstanceRoot` and `SyntaxInstanceValue` labels.
        Renaming `CONTAINS_TIMEFRAME` relationship to `CONTAINS_SYNTAX_INSTANCE`""")
    db_connection.cypher_query(
        """MATCH (:Library)-[rel:CONTAINS_TIMEFRAME]->(q:TimeframeRoot)
        SET q:SyntaxInstanceRoot
        WITH *
        CALL apoc.refactor.setType(rel, 'CONTAINS_SYNTAX_INSTANCE') YIELD input, output
        MATCH (q)-[:LATEST|:LATEST_DRAFT|:LATEST_FINAL|:HAS_VERSION]-(v)
        SET v:SyntaxInstanceValue
        RETURN *"""
    )

    logger.info(
        """Adding `SyntaxTemplateRoot` and `SyntaxTemplateValue` labels.
        Renaming `CONTAINS_ACTIVITY_DESCRIPTION_TEMPLATE` relationship to `CONTAINS_SYNTAX_TEMPLATE`"""
    )
    db_connection.cypher_query(
        """MATCH (:Library)-[rel:CONTAINS_ACTIVITY_DESCRIPTION_TEMPLATE]->(q:ActivityDescriptionTemplateRoot)
        SET q:SyntaxTemplateRoot
        WITH *
        CALL apoc.refactor.setType(rel, 'CONTAINS_SYNTAX_TEMPLATE') YIELD input, output
        MATCH (q)-[:LATEST|:LATEST_DRAFT|:LATEST_FINAL|:HAS_VERSION]-(v)
        SET v:SyntaxTemplateValue
        RETURN *"""
    )
    logger.info(
        """Adding `SyntaxTemplateRoot`, `SyntaxTemplateValue` and `SyntaxIndexingTemplateRoot`, `SyntaxIndexingTemplateValue` labels.
        Renaming `CONTAINS_CRITERIA_TEMPLATE` relationship to `CONTAINS_SYNTAX_TEMPLATE`"""
    )
    db_connection.cypher_query(
        """MATCH (:Library)-[rel:CONTAINS_CRITERIA_TEMPLATE]->(q:CriteriaTemplateRoot)
        SET q:SyntaxTemplateRoot
        SET q:SyntaxIndexingTemplateRoot
        WITH *
        CALL apoc.refactor.setType(rel, 'CONTAINS_SYNTAX_TEMPLATE') YIELD input, output
        MATCH (q)-[:LATEST|:LATEST_DRAFT|:LATEST_FINAL|:HAS_VERSION]-(v)
        SET v:SyntaxTemplateValue
        SET v:SyntaxIndexingTemplateValue
        RETURN *"""
    )
    logger.info(
        """Adding `SyntaxTemplateRoot`, `SyntaxTemplateValue` and `SyntaxIndexingTemplateRoot`, `SyntaxIndexingTemplateValue` labels.
        Renaming `CONTAINS_ENDPOINT_TEMPLATE` relationship to `CONTAINS_SYNTAX_TEMPLATE`"""
    )
    db_connection.cypher_query(
        """MATCH (:Library)-[rel:CONTAINS_ENDPOINT_TEMPLATE]->(q:EndpointTemplateRoot)
        SET q:SyntaxTemplateRoot
        SET q:SyntaxIndexingTemplateRoot
        WITH *
        CALL apoc.refactor.setType(rel, 'CONTAINS_SYNTAX_TEMPLATE') YIELD input, output
        MATCH (q)-[:LATEST|:LATEST_DRAFT|:LATEST_FINAL|:HAS_VERSION]-(v)
        SET v:SyntaxTemplateValue
        SET v:SyntaxIndexingTemplateValue
        RETURN *"""
    )
    logger.info(
        """Adding `SyntaxTemplateRoot`, `SyntaxTemplateValue` and `SyntaxIndexingTemplateRoot`, `SyntaxIndexingTemplateValue` labels.
        Renaming `CONTAINS_OBJECTIVE_TEMPLATE` relationship to `CONTAINS_SYNTAX_TEMPLATE`"""
    )
    db_connection.cypher_query(
        """MATCH (:Library)-[rel:CONTAINS_OBJECTIVE_TEMPLATE]->(q:ObjectiveTemplateRoot)
        SET q:SyntaxTemplateRoot
        SET q:SyntaxIndexingTemplateRoot
        WITH *
        CALL apoc.refactor.setType(rel, 'CONTAINS_SYNTAX_TEMPLATE') YIELD input, output
        MATCH (q)-[:LATEST|:LATEST_DRAFT|:LATEST_FINAL|:HAS_VERSION]-(v)
        SET v:SyntaxTemplateValue
        SET v:SyntaxIndexingTemplateValue
        RETURN *"""
    )
    logger.info(
        """Adding `SyntaxTemplateRoot` and `SyntaxTemplateValue` labels.
        Renaming `CONTAINS_TIMEFRAME_TEMPLATE` relationship to `CONTAINS_SYNTAX_TEMPLATE`"""
    )
    db_connection.cypher_query(
        """MATCH (:Library)-[rel:CONTAINS_TIMEFRAME_TEMPLATE]->(q:TimeframeTemplateRoot)
        SET q:SyntaxTemplateRoot
        WITH *
        CALL apoc.refactor.setType(rel, 'CONTAINS_SYNTAX_TEMPLATE') YIELD input, output
        MATCH (q)-[:LATEST|:LATEST_DRAFT|:LATEST_FINAL|:HAS_VERSION]-(v)
        SET v:SyntaxTemplateValue
        RETURN *"""
    )

    logger.info(
        "Renaming `TemplateParameterValueRoot` label to `TemplateParameterTermRoot`"
    )
    db_connection.cypher_query(
        "MATCH (t:TemplateParameterValueRoot) REMOVE t:TemplateParameterValueRoot SET t:TemplateParameterTermRoot"
    )
    logger.info(
        "Renaming `TemplateParameterValue` label to `TemplateParameterTermValue`"
    )
    db_connection.cypher_query(
        "MATCH (t:TemplateParameterValue) REMOVE t:TemplateParameterValue SET t:TemplateParameterTermValue"
    )
    logger.info(
        "Renaming `ActivityDescriptionTemplateRoot` label to `ActivityInstructionTemplateRoot`"
    )
    db_connection.cypher_query(
        "MATCH (a:ActivityDescriptionTemplateRoot) REMOVE a:ActivityDescriptionTemplateRoot SET a:ActivityInstructionTemplateRoot"
    )
    logger.info(
        "Renaming `ActivityDescriptionTemplateValue` label to `ActivityInstructionTemplateValue`"
    )
    db_connection.cypher_query(
        "MATCH (a:ActivityDescriptionTemplateValue) REMOVE a:ActivityDescriptionTemplateValue SET a:ActivityInstructionTemplateValue"
    )
    logger.info("Renaming `HAS_VALUE` relationship to `HAS_PARAMETER_TERM`")
    db_connection.cypher_query(
        """MATCH (:TemplateParameter)-[rel:HAS_VALUE]->(:TemplateParameterTermRoot) WITH rel
        CALL apoc.refactor.setType(rel, 'HAS_PARAMETER_TERM') YIELD input, output RETURN *"""
    )
    logger.info("Renaming `HAS_SUB_CATEGORY` relationship to `HAS_SUBCATEGORY`")
    db_connection.cypher_query(
        """MATCH (:SyntaxIndexingTemplateRoot)-[rel:HAS_SUB_CATEGORY]->(:CTTermRoot) WITH rel
        CALL apoc.refactor.setType(rel, 'HAS_SUBCATEGORY') YIELD input, output RETURN *"""
    )
    logger.info("Renaming `HAS_DISEASE_DISORDER` relationship to `HAS_INDICATION`")
    db_connection.cypher_query(
        """MATCH ()-[rel:HAS_DISEASE_DISORDER]->() WITH rel
        CALL apoc.refactor.setType(rel, 'HAS_INDICATION') YIELD input, output RETURN *"""
    )
    logger.info(
        "Renaming `OV_USES_VALUE`, `EV_USES_VALUE`, `TV_USES_VALUE`, `CT_USES_VALUE` and `AT_USES_VALUE` relationships to `USES_VALUE`"
    )
    db_connection.cypher_query(
        """MATCH ()-[rel:OV_USES_VALUE|EV_USES_VALUE|TV_USES_VALUE|CT_USES_VALUE|AT_USES_VALUE]->() WITH rel
        CALL apoc.refactor.setType(rel, 'USES_VALUE') YIELD input, output RETURN *"""
    )
    logger.info(
        """Renaming `OT_USES_PARAMETER`, `ET_USES_PARAMETER`, `TT_USES_PARAMETER`,
        `CT_USES_PARAMETER` and `AT_USES_PARAMETER` relationships to `USES_PARAMETER`"""
    )
    db_connection.cypher_query(
        """MATCH ()-[rel:OT_USES_PARAMETER|ET_USES_PARAMETER|TT_USES_PARAMETER|CT_USES_PARAMETER|AT_USES_PARAMETER]->() WITH rel
        CALL apoc.refactor.setType(rel, 'USES_PARAMETER') YIELD input, output RETURN *"""
    )


def migrate_study_preferred_time_unit(db_connection):
    # Add default 'preferred_time_unit' StudyTimeField node to each latest StudyValue
    logger.info("Migrating default study preferred time unit...")
    result, _ = db_connection.cypher_query(
        """MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)
        WHERE NOT exists((study_value)-[:HAS_TIME_FIELD]->(:StudyTimeField {field_name:'preferred_time_unit'}))
        RETURN study_root.uid as study_uid"""
    )

    if result:
        for study_uid in result[0]:
            logger.info(
                "Creating default study preferred time unit on Study '%s' node",
                study_uid,
            )
            statement = """
                MATCH (n:StudyRoot {uid:$study_uid})-[:LATEST]->(study_value:StudyValue)
                MATCH (:UnitDefinitionValue {name:"day"})<-[:LATEST]-(ud_root:UnitDefinitionRoot)
                MERGE (study_value)-[:HAS_TIME_FIELD]->
                (:StudyField:StudyTimeField {field_name:"preferred_time_unit", value:ud_root.uid})-[:HAS_UNIT_DEFINITION]->(ud_root)
                """
            db_connection.cypher_query(statement, params={"study_uid": study_uid})


def migrate_item_versioning(db_connection):
    # Add default 'preferred_time_unit' StudyTimeField node to each latest StudyValue
    logger.info("Migrating item versioning relationships...")

    logger.info("Add missing HAS_VERSIONs for LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED")
    query = """
        MATCH (root)-[lat:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(value)
        WHERE none(label in labels(root) WHERE label IN ["ClassVariableRoot", "DatasetClassRoot", "DatasetRoot", "DatasetScenarioRoot", "DatasetVariableRoot", "StudyRoot"])
            AND lat.version IS NOT NULL AND lat.status IS NOT NULL
            AND NOT (root)-[:HAS_VERSION {version: lat.version, status: lat.status}]->(value)
        CREATE (root)-[hv:HAS_VERSION]->(value)
        SET hv = lat
        SET lat = {}
    """
    db_connection.cypher_query(query)

    logger.info("Remove duplicated HAS_VERSION relationships")
    query = """
        MATCH (root)-[hv1:HAS_VERSION]->(value)
        WHERE none(label in labels(root) WHERE label IN ["ClassVariableRoot", "DatasetClassRoot", "DatasetRoot", "DatasetScenarioRoot", "DatasetVariableRoot", "StudyRoot"])
        MATCH (root)-[hv2:HAS_VERSION {version: hv1.version, start_date: hv1.start_date}]->(value)
        WHERE hv2.end_date < hv1.end_date OR (hv2.end_date IS NULL AND hv1.end_date IS NOT NULL)
        DELETE hv2
    """
    db_connection.cypher_query(query)

    logger.info(
        "Remove any properties from LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED relationships"
    )
    query = """
        MATCH (root)-[lat:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(value)
        WHERE none(label in labels(root) WHERE label IN ["ClassVariableRoot", "DatasetClassRoot", "DatasetRoot", "DatasetScenarioRoot", "DatasetVariableRoot", "StudyRoot"])
            AND size(keys(properties(lat))) > 0
        SET lat = {}
    """
    db_connection.cypher_query(query)


def migrate_syntax_sequence_id(db_connection):
    logger.info("Preparing data for Syntax sequence_id...")
    db_connection.cypher_query(
        """MATCH (t:SyntaxTemplateRoot)<-[l_rel:CONTAINS_SYNTAX_TEMPLATE]-(l:Library {name: "User Defined"})
        WHERE EXISTS((t)<-[:CONTAINS_SYNTAX_TEMPLATE]-(:Library {name: "Sponsor"}))
        DELETE l_rel"""
    )
    db_connection.cypher_query("""MATCH (n:SyntaxTemplateRoot)<-[r]-(m:Library) 
        WITH n, m, type(r) as t, tail(collect(r)) as coll 
        FOREACH(x in coll | DELETE x)""")
    db_connection.cypher_query(
        """MATCH (t:CriteriaTemplateRoot)-[r:HAS_TYPE]->(:CTTermRoot)
        WITH t, MAX(ID(r)) AS max_id
        MATCH (t)-[r:HAS_TYPE]->(:CTTermRoot)
        WHERE NOT ID(r) = max_id
        DELETE r"""
    )
    db_connection.cypher_query(
        """MATCH (t:ObjectiveTemplateRoot)-[r:LATEST_FINAL]->(:ObjectiveTemplateValue)
        WITH t, MAX(ID(r)) AS max_id
        MATCH (t)-[r:LATEST_FINAL]->(:ObjectiveTemplateValue)
        WHERE NOT ID(r) = max_id
        DELETE r"""
    )

    logger.info("Migrating Syntax sequence_id...")

    logger.info("Add sequence_id to all Syntax Templates except Criteria Templates")
    query = """
        MATCH (t:SyntaxTemplateRoot)
        WHERE NOT t:CriteriaTemplateRoot
        SET t.sequence_id = apoc.text.replace(t.uid, '[a-z_-]|(?<=_)[0]*(?=[1-9])', '');
    """
    db_connection.cypher_query(query)

    logger.info("Add sequence_id to Criteria Templates")
    query = """
        MATCH (t:CriteriaTemplateRoot)
        MATCH (t)-[:HAS_TYPE]->(:CTTermRoot)-->(:CTTermNameRoot)-[:LATEST]->(ctnv:CTTermNameValue)
        WITH t, apoc.text.replace(t.uid, '[^0-9]', '') as uid, "Criteria" + apoc.text.replace(ctnv.name, ' |Criteria|CRITERIA|criteria', '') + "Template" as special_abbr
        SET t.sequence_id = apoc.text.replace(special_abbr + "_" + uid, '[a-z_-]|(?<=_)[0]*(?=[1-9])', '');
    """
    db_connection.cypher_query(query)


async def migrate_activity_instance_class_relationship(db_connection):
    logger.info("Migrating activity instance classes")
    timeout = aiohttp.ClientTimeout(None)
    conn = aiohttp.TCPConnector(limit=4, force_close=True)
    activities = Activities()

    filename = "../import_sponsor_data/datafiles/sponsor_library/activity/activity_instance_class.csv"
    async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
        await activities.handle_activity_instance_classes(filename, session)

    logger.info(
        "Migrating (:ActivityInstanceValue)-[:ACTIVITY_INSTANCE_CLASS]->(:ActivityInstanceClassRoot) relationship"
        "Removing extra ActivityInstance labels like: FindingRoot:CategoricFindingRoot"
        "Removing extra relationship from ActivityInstanceValue to ActivityDefinition node"
    )
    query = """
        MATCH (activity_instance_root:ActivityInstanceRoot)-[]->(activity_instance_value:ActivityInstanceValue)
        WITH activity_instance_root, activity_instance_value,
            CASE
                WHEN "CategoricFindingValue" in labels(activity_instance_value) THEN "CategoricFinding"
                WHEN "TextualFindingValue" in labels(activity_instance_value) THEN "TextualFinding"
                WHEN "NumericFindingValue" in labels(activity_instance_value) THEN "NumericFinding"
                WHEN "EventValue" in labels(activity_instance_value) THEN "Event"
            END AS instance_class
        MATCH (activity_instance_class_value:ActivityInstanceClassValue {name:instance_class})<-[]-(activity_instance_class_root)
        MERGE (activity_instance_value)-[:ACTIVITY_INSTANCE_CLASS]->(activity_instance_class_root)
        WITH activity_instance_root, activity_instance_value, instance_class
        CALL apoc.do.case([
            "CategoricFindingValue" in labels(activity_instance_value),
            'REMOVE activity_instance_root:FindingRoot:CategoricFindingRoot
            REMOVE activity_instance_value:FindingValue:CategoricFindingValue',

            "TextualFindingValue" in labels(activity_instance_value),
            'REMOVE activity_instance_root:FindingRoot:TextualFindingRoot
            REMOVE activity_instance_value:FindingValue:TextualFindingValue',

            "NumericFindingValue" in labels(activity_instance_value),
            'REMOVE activity_instance_root:FindingRoot:NumericFindingRoot
            REMOVE activity_instance_value:FindingValue:NumericFindingValue',

            "EventValue" in labels(activity_instance_value),
            'REMOVE activity_instance_root:EventRoot
            REMOVE activity_instance_value:EventValue'
        ],
        '',
        {
            activity_instance_root: activity_instance_root,
            activity_instance_value: activity_instance_value
        })
        YIELD value
        OPTIONAL MATCH (activity_instance_value)-[:DEFINED_BY]->(activity_definition:ActivityDefinition)
        DETACH DELETE activity_definition
        RETURN value
    """
    db_connection.cypher_query(query)


def migrate_role_and_data_type(db_connection):
    logger.info(
        "Migrating dummy relationship between ActivityItemClassValue and CTTerm that represents Role and Data type"
    )
    _result, _ = db_connection.cypher_query(
        """WITH head([(na_root:CTTermRoot)-[:HAS_NAME_ROOT]->()-[:LATEST]->(na_value:CTTermNameValue {name:"Not Applicable"}) | na_root]) as na_root

        MATCH (:ActivityItemClassRoot)-[:LATEST]->(activity_item_class_value:ActivityItemClassValue)
        WHERE NOT exists((activity_item_class_value)-[:HAS_ROLE]->())
        MERGE (activity_item_class_value)-[:HAS_ROLE]->(na_root)
        WITH *
        MATCH (:ActivityItemClassRoot)-[:LATEST]->(activity_item_class_value:ActivityItemClassValue)
        WHERE NOT exists((activity_item_class_value)-[:HAS_DATA_TYPE]->())
        MERGE (activity_item_class_value)-[:HAS_DATA_TYPE]->(na_root)
        """
    )


def migrate_activity_instances_without_activity(db_connection):
    logger.info(
        "Adding a dummy relationship to ActivityValue for ActivityInstanceValues missing an activity"
    )
    _result, _ = db_connection.cypher_query(
        """WITH head([(ar:ActivityRoot)-[:LATEST]->(av:ActivityValue {name: "Technical Complaint"}) | av]) as activity_val

        MATCH (n:ActivityInstanceValue)
        WHERE NOT (n)-[:IN_HIERARCHY]->(:ActivityValue)
        MERGE (n)-[:IN_HIERARCHY]->(activity_val)
        """
    )


def migrate_odm_templates(db_connection):
    logger.info("Migrating ODM Templates...")

    logger.info("Renaming `OdmTemplateRoot` label to `OdmStudyEventRoot`")
    db_connection.cypher_query(
        "MATCH (o:OdmTemplateRoot) REMOVE o:OdmTemplateRoot SET o:OdmStudyEventRoot"
    )
    logger.info("Renaming `OdmTemplateValue` label to `OdmStudyEventValue`")
    db_connection.cypher_query(
        "MATCH (o:OdmTemplateValue) REMOVE o:OdmTemplateValue SET o:OdmStudyEventValue"
    )

    logger.info("Adding `display_in_tree` property to `OdmStudyEventValue`")
    db_connection.cypher_query(
        "MATCH (o:OdmStudyEventValue) SET o.display_in_tree=true"
    )


if __name__ == "__main__":
    run()
