from src.scripts.entities.cdisc_data_models.data_model_import import (
    DataModelImport,
)
from src.scripts.exceptions.version_exists import VersionExists
from src.scripts.repositories.mapping import (
    map_version,
    map_classes,
    map_variables,
    map_scenarios,
)

def create_indexes_if_not_existent(tx):
    for querystring in [
        "CREATE INDEX index_codelist_concept_id IF NOT EXISTS FOR (n:Codelist) ON (n.concept_id)",
        "CREATE INDEX index_term_concept_id IF NOT EXISTS FOR (n:Term) ON (n.concept_id)",
        "CREATE INDEX index_variable IF NOT EXISTS FOR (n:DataModelVariable) ON (n.href)",
        "CREATE CONSTRAINT constraint_import_effective_date IF NOT EXISTS FOR (n:Import) REQUIRE (n.effective_date) IS NODE KEY",
        "CREATE CONSTRAINT data_model_import_node_key IF NOT EXISTS FOR (n:DataModelImport) REQUIRE (n.catalogue, n.version_number) IS NODE KEY",
        "CREATE CONSTRAINT data_model_class_node_key IF NOT EXISTS FOR (n:DataModelClass) REQUIRE (n.catalogue, n.version_number, n.name) IS NODE KEY",
        "CREATE CONSTRAINT data_model_scenario_node_key IF NOT EXISTS FOR (n:DataModelScenario) REQUIRE (n.href) IS NODE KEY",
        "CREATE CONSTRAINT constraint_package_uid IF NOT EXISTS FOR (n:Package) REQUIRE (n.name) IS NODE KEY",
        "CREATE CONSTRAINT contraint_version_name IF NOT EXISTS FOR (n:Version) REQUIRE (n.name) IS NODE KEY",
        "CREATE CONSTRAINT constraint_codelist_uid IF NOT EXISTS FOR (n:Codelist) REQUIRE (n.effective_date, n.concept_id) IS NODE KEY",
        "CREATE CONSTRAINT constraint_term_uid IF NOT EXISTS FOR (n:Term) REQUIRE (n.effective_date, n.concept_id, n.code_submission_value) IS NODE KEY",
    ]:
        tx.run(querystring)


def await_indexes(tx):
    tx.run("CALL db.awaitIndexes(5000)")


def create_data_model_import_node(tx, dm_import: DataModelImport):
    """
    Creates the `DataModelImport` node for the specified catalogue and version if it doesn't exist.

    Returns the internal Neo4j id of the created node on success.
    Returns False if the node was not created. Reasons might include: the node was already existent, db error.
    """

    if _does_data_model_import_node_exists(tx, dm_import):
        raise VersionExists

    result = tx.run(
        """
        CREATE (import:DataModelImport{
            library: $library,
            catalogue: $catalogue,
            version_number: $version_number,
            implements_data_model: $implements_data_model,
            data_model_type: $data_model_type,
            author_id: $author_id
        })
        SET
            import:Running,
            import.import_date_time = datetime($import_date_time)
        RETURN id(import) AS import_id
        """,
        library=dm_import.library,
        catalogue=dm_import.catalogue,
        version_number=dm_import.version_number,
        data_model_type=dm_import.get_type().value,
        implements_data_model=dm_import.get_implements_data_model(),
        author_id=dm_import.author_id,
        import_date_time=dm_import.import_date_time,
    ).single()

    import_id = result.get("import_id", None)
    if import_id is None:
        raise Exception
    return import_id


def _does_data_model_import_node_exists(tx, dm_import: DataModelImport):
    result = tx.run(
        """
        MATCH (import:DataModelImport{catalogue: $catalogue, version_number: $version_number})
        WITH import LIMIT 1
        RETURN count(import) = 1 AS does_import_exist
        """,
        catalogue=dm_import.catalogue,
        version_number=dm_import.version_number,
    ).single()

    return result is not None and result["does_import_exist"] == True


def create_data_model_import(dm_import: DataModelImport, session):
    catalogue = dm_import.catalogue
    version_number = dm_import.version_number

    version_data = map_version(dm_import.get_version())
    classes_data = map_classes(dm_import.get_classes())
    scenarios_data = map_scenarios(dm_import.get_scenarios())
    variables_data = map_variables(dm_import.get_variables())

    with session.begin_transaction() as tx:
        _create_version(
            tx,
            catalogue=catalogue,
            version_number=version_number,
            version_data=version_data,
        )
        _create_classes(
            tx,
            catalogue=catalogue,
            version_number=version_number,
            classes_data=classes_data,
        )
        if scenarios_data is not None and len(scenarios_data) > 0:
            _create_scenarios(
                tx,
                catalogue=catalogue,
                version_number=version_number,
                scenarios_data=scenarios_data,
            )
        _create_variables(
            tx,
            catalogue=catalogue,
            version_number=version_number,
            variables_data=variables_data,
        )
        tx.commit()

    with session.begin_transaction() as tx:
        _create_version_contains_class(
            tx,
            catalogue=catalogue,
            version_number=version_number,
            version_data=version_data,
        )
        _create_class_contains_variable(
            tx,
            catalogue=catalogue,
            version_number=version_number,
            classes_data=classes_data,
        )
        if scenarios_data is not None and len(scenarios_data) > 0:
            _create_scenario_contains_variable(
                tx,
                catalogue=catalogue,
                version_number=version_number,
                scenarios_data=scenarios_data,
            )
        tx.commit()


# Create nodes


def _create_version(tx, catalogue, version_number, version_data):
    tx.run(
        """
        MATCH (import:DataModelImport{catalogue: $catalogue, version_number: $version_number})
        WITH import, $version AS v
        CREATE (version:Version{
            name: v.name
        })
        SET
            version.label = v.label,
            version.description = v.description,
            version.source = v.source,
            version.registration_status = v.registration_status,
            version.version_number = v.version_number,
            version.effective_date = v.effective_date,
            version.href = v.href,
            version.prior_version = v.prior_version
        CREATE (import)-[:INCLUDES]->(version)
        """,
        catalogue=catalogue,
        version_number=version_number,
        version=version_data,
    )


def _create_classes(tx, catalogue, version_number, classes_data):
    tx.run(
        """
        UNWIND $classes AS c
            CREATE (class:DataModelClass{
                catalogue: $catalogue,
                version_number: $version_number,
                name: c.name
            })
            SET
                class.title = c.title,
                class.label = c.label,
                class.description = c.description,
                class.ordinal = c.ordinal,
                class.href = c.href,
                class.implements_class = c.implements_class,
                class.subclasses = c.subclasses,
                class.prior_version = c.prior_version
        """,
        catalogue=catalogue,
        version_number=version_number,
        classes=classes_data,
    )


def _create_scenarios(tx, catalogue, version_number, scenarios_data):
    tx.run(
        """
        UNWIND $scenarios AS s
            CREATE (scenario:DataModelScenario{
                catalogue: $catalogue,
                version_number: $version_number,
                title: s.title
            })
            SET
                scenario.label = s.label,
                scenario.ordinal = s.ordinal,
                scenario.href = s.href

            WITH s, scenario
            MATCH (dataset:DataModelClass{href: s.dataset_href})
            CREATE (dataset)-[:CONTAINS]->(scenario)
        """,
        catalogue=catalogue,
        version_number=version_number,
        scenarios=scenarios_data,
    )


def _create_variables(tx, catalogue, version_number, variables_data):
    tx.run(
        """
        UNWIND $variables AS v
            CREATE (variable:DataModelVariable{href: v.href})
            SET
                variable.catalogue = $catalogue,
                variable.version_number = $version_number,
                variable.name = v.name,
                variable.title = v.title,
                variable.label = v.label,
                variable.description = v.description,
                variable.ordinal = v.ordinal,
                variable.role = v.role,
                variable.notes = v.notes,
                variable.variable_c_code = v.variable_c_code,
                variable.usage_restrictions = v.usage_restrictions,
                variable.examples = v.examples,
                variable.value_list = v.value_list,
                variable.described_value_domain = v.described_value_domain,
                variable.qualifies_variables = v.qualifies_variables,
                variable.role_description = v.role_description,
                variable.simple_datatype = v.simple_datatype,
                variable.length = v.length,
                variable.implementation_notes = v.implementation_notes,
                variable.mapping_instructions = v.mapping_instructions,
                variable.prompt = v.prompt,
                variable.question_text = v.question_text,
                variable.completion_instructions = v.completion_instructions,
                variable.core = v.core,
                variable.codelists = v.codelists,
                variable.implements_variables = v.implements_variables,
                variable.mapping_targets = v.mapping_targets,
                variable.prior_version = v.prior_version,
                variable.analysis_variable_set = v.analysis_variable_set
        """,
        catalogue=catalogue,
        version_number=version_number,
        variables=variables_data,
    )


def _create_version_contains_class(tx, catalogue, version_number, version_data):
    tx.run(
        """
        WITH $version AS v
        MATCH (version:Version{name: v.name})
        UNWIND v.classes AS c
            MATCH (class:DataModelClass{
                catalogue: $catalogue,
                version_number: $version_number,
                name: c.name
            })
            CREATE (version)-[contains:CONTAINS]->(class)
        """,
        catalogue=catalogue,
        version_number=version_number,
        version=version_data,
    )


def _create_class_contains_variable(tx, catalogue, version_number, classes_data):
    tx.run(
        """
        UNWIND $classes AS c
            MATCH (class:DataModelClass{name: c.name, catalogue: $catalogue, version_number: $version_number})
            UNWIND c.variables AS v
                MATCH (variable:DataModelVariable{href: v.href})
                CREATE (class)-[contains:CONTAINS]->(variable)
        """,
        catalogue=catalogue,
        version_number=version_number,
        classes=classes_data,
    )


def _create_scenario_contains_variable(tx, catalogue, version_number, scenarios_data):
    tx.run(
        """
        UNWIND $scenarios AS s
            MATCH (scenario:DataModelScenario{href: s.href})
            UNWIND s.variables AS v
                MATCH (variable:DataModelVariable{href: v.href})
                CREATE (scenario)-[contains:CONTAINS]->(variable)
        """,
        catalogue=catalogue,
        version_number=version_number,
        scenarios=scenarios_data,
    )

