"""
This script imports the CDISC data models & IGs into the MDR database.
"""

import time
import os
import csv
from src.scripts.entities.cdisc_data_models.data_model_type import (
    DataModelType,
)
from src.scripts.utils import (
    create_user,
    parse_ig_name,
    sanitize_string,
    load_env,
)

AUTHOR_ID = "CDISC_IMPORT"
DATA_MODEL_ROOT_LABEL = "DataModelRoot"
DATA_MODEL_VALUE_LABEL = "DataModelValue"
DATA_MODEL_IG_ROOT_LABEL = "DataModelIGRoot"
DATA_MODEL_IG_VALUE_LABEL = "DataModelIGValue"
DATASET_CLASS_ROOT_LABEL = "DatasetClass"
DATASET_CLASS_VALUE_LABEL = "DatasetClassInstance"
SCENARIO_ROOT_LABEL = "DatasetScenario"
SCENARIO_VALUE_LABEL = "DatasetScenarioInstance"
DATASET_ROOT_LABEL = "Dataset"
DATASET_VALUE_LABEL = "DatasetInstance"
VARIABLE_CLASS_ROOT_LABEL = "VariableClass"
VARIABLE_CLASS_VALUE_LABEL = "VariableClassInstance"
DATASET_VARIABLE_ROOT_LABEL = "DatasetVariable"
DATASET_VARIABLE_VALUE_LABEL = "DatasetVariableInstance"
SCENARIO_VARIABLE_VALUE_LABEL = "ScenarioVariableImplementation"
VERSION_TO_DATA_MODEL_REL_TYPE = "CONTAINS_DATA_MODEL"
VERSION_TO_DATA_MODEL_IG_REL_TYPE = "CONTAINS_DATA_MODEL_IG"
VERSION_TO_CLASS_REL_TYPE = "CONTAINS_DATASET_CLASS"
VERSION_TO_DATASET_REL_TYPE = "CONTAINS_DATASET"
VERSION_TO_SCENARIO_REL_TYPE = "CONTAINS_DATASET_SCENARIO"
VERSION_TO_VARIABLE_CLASS_REL_TYPE = "CONTAINS_VARIABLE_CLASS"
VERSION_TO_DATASET_VARIABLE_REL_TYPE = "CONTAINS_DATASET_VARIABLE"
CATALOGUE_TO_DATA_MODEL_REL_TYPE = "HAS_DATA_MODEL"
CATALOGUE_TO_DATA_MODEL_IG_REL_TYPE = "HAS_DATA_MODEL_IG"
CATALOGUE_TO_CLASS_ROOT_REL_TYPE = "HAS_DATASET_CLASS"
CATALOGUE_TO_DATASET_ROOT_REL_TYPE = "HAS_DATASET"
CATALOGUE_TO_SCENARIO_REL_TYPE = "HAS_DATASET_SCENARIO"
CATALOGUE_TO_VARIABLE_CLASS_ROOT_REL_TYPE = "HAS_VARIABLE_CLASS"
CATALOGUE_TO_DATASET_VARIABLE_ROOT_REL_TYPE = "HAS_DATASET_VARIABLE"
CLASS_TO_VARIABLE_CLASS_ROOT_REL_TYPE = "HAS_VARIABLE_CLASS"
CLASS_TO_DATASET_VARIABLE_ROOT_REL_TYPE = "HAS_DATASET_VARIABLE"
CLASS_TO_SCENARIO_REL_TYPE = "HAS_DATASET_SCENARIO"
SCENARIO_TO_VARIABLE_REL_TYPE = "HAS_DATASET_VARIABLE"
VARIABLE_TO_SCENARIO_VARIABLE_REL_TYPE = "HAS_SCENARIO_IMPLEMENTATION"
VERSION_TO_SCENARIO_VARIABLE_REL_TYPE = "CONTAINS_SCENARIO_VARIABLE"
SCENARIO_VARIABLE_TO_SCENARIO_REL_TYPE = "IMPLEMENTS_SCENARIO"
MODEL_VERSION_REL_TYPE = "HAS_VERSION"
CLASS_VERSION_REL_TYPE = "HAS_INSTANCE"
VARIABLE_VERSION_REL_TYPE = "HAS_INSTANCE"
SCENARIO_VERSION_REL_TYPE = "HAS_INSTANCE"

VARIABLE_VALUE_LIST_MAPPINGS_FILE = load_env(
    "VARIABLE_VALUE_LIST_MAPPINGS_FILE",
    "cdisc_data/extra/variable_value_list_mappings.csv",
)


class ValueListMapping:
    def __init__(
        self,
        variable_uid,
        dataset_uid,
        term_code_submission_value,
        term_uid,
        codelist_uid,
        model_name,
    ):
        self.variable_uid = variable_uid
        self.dataset_uid = dataset_uid
        self.term_code_submission_value = term_code_submission_value
        self.term_uid = term_uid
        self.codelist_uid = codelist_uid
        self.model_name = model_name


def import_from_cdisc_db_into_mdr(
    catalogue: str,
    version_number: str,
    cdisc_neo4j_driver,
    cdisc_db_name: str,
    mdr_neo4j_driver,
    mdr_db_name: str,
    author_id: str,
):
    global AUTHOR_ID
    AUTHOR_ID = author_id

    start_time = time.time()

    if catalogue is None or version_number is None:
        print(
            f"WARNING: No catalogue or version number specified. Not importing anything."
        )
        return

    with cdisc_neo4j_driver.session(database=cdisc_db_name) as session:
        # read from the CDISC DB
        version_data = session.read_transaction(get_version, catalogue, version_number)
        classes_data = session.read_transaction(get_classes, catalogue, version_number)
        scenarios_data = session.read_transaction(
            get_scenarios, catalogue, version_number
        )
        variables_data = session.read_transaction(
            get_variables, catalogue, version_number
        )

        session.close()

        if len(version_data) > 0 and "version" in version_data[0]:
            with mdr_neo4j_driver.session(database=mdr_db_name) as session:
                # write to the clinical MDR db
                print("==  * Merging structure nodes and relationships.")
                session.write_transaction(
                    merge_structure_nodes_and_relationships,
                    version_data[0]["version"],
                    classes_data,
                    scenarios_data,
                    variables_data,
                )

                print("==  * Merging Data Model / Implementation Guide.")
                session.write_transaction(merge_data_model, version_data[0]["version"])

                print("==  * Merging Classes.")
                (
                    added_classes,
                    updated_classes,
                    unchanged_classes,
                ) = session.write_transaction(
                    merge_classes, version_data[0]["version"], classes_data
                )
                print(f"==      Added classes:       {added_classes:6}")
                print(f"==      Updated classes:     {updated_classes:6}")
                print(f"==      Unchanged classes:   {unchanged_classes:6}")

                print("==  * Merging Scenarii.")
                (
                    added_scenarii,
                    updated_scenarii,
                    unchanged_scenarii,
                ) = session.write_transaction(
                    merge_scenarios, version_data[0]["version"], scenarios_data
                )
                print(f"==      Added scenarii:      {added_scenarii:6}")
                print(f"==      Updated scenarii:    {updated_scenarii:6}")
                print(f"==      Unchanged scenarii:  {unchanged_scenarii:6}")

                print("==  * Merging Variables.")
                (
                    added_variables,
                    updated_variables,
                    unchanged_variables,
                ) = session.write_transaction(
                    merge_variables, version_data[0]["version"], variables_data
                )
                print(f"==      Added variables:     {added_variables:6}")
                print(f"==      Updated variables:   {updated_variables:6}")
                print(f"==      Unchanged variables: {unchanged_variables:6}")

                # This has to happen after the variables creation transaction has been committed
                # Otherwise, new variables are not matched
                if (
                    version_data[0]["version"]["data_model_type"]
                    == DataModelType.IMPLEMENTATION.value
                ):
                    print("==  * Linking dataset variables with variable classes.")
                    session.write_transaction(
                        link_variables_with_variables,
                        version_data[0]["version"],
                        variables_data,
                    )

                session.close()

        with mdr_neo4j_driver.session(database=mdr_db_name) as session:
            session.write_transaction(create_user, author_id)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"== Duration: {round(elapsed_time, 1)} seconds")
    print("============================================")


def get_version(tx, catalogue: str, prefixed_version_number: str):
    version_data = tx.run(
        """
        MATCH (import:DataModelImport{catalogue: $catalogue, version_number: $prefixed_version_number})-[:INCLUDES]->(version)
        RETURN
            version{uid: version.name, catalogue: $catalogue, library: import.library, data_model_type: import.data_model_type, implements_data_model: import.implements_data_model, .*} AS version
        """,
        catalogue=catalogue,
        prefixed_version_number=prefixed_version_number,
    ).data()
    for item in version_data:
        item["version"]["uid"] = sanitize_string(item["version"]["uid"])

    return version_data


def get_classes(tx, catalogue: str, prefixed_version_number: str):
    classes_data = tx.run(
        """
        MATCH (import:DataModelImport{catalogue: $catalogue, version_number: $prefixed_version_number})
            -[:INCLUDES]->(version)-[:CONTAINS]->(class)
        RETURN class
        """,
        catalogue=catalogue,
        prefixed_version_number=prefixed_version_number,
    ).data()
    for item in classes_data:
        item["class"]["uid"] = sanitize_string(item["class"]["name"])

    return classes_data


def get_scenarios(tx, catalogue: str, prefixed_version_number: str):
    scenarios_data = tx.run(
        """
        MATCH (import:DataModelImport{catalogue: $catalogue, version_number: $prefixed_version_number})
            -[:INCLUDES]->(version)-[:CONTAINS]->(class:DataModelClass)-[:CONTAINS]->(scenario:DataModelScenario)
        RETURN scenario, class.href AS dataset_href
        """,
        catalogue=catalogue,
        prefixed_version_number=prefixed_version_number,
    ).data()
    for item in scenarios_data:
        item["scenario"]["uid"] = sanitize_string(item["scenario"]["title"])

    return scenarios_data


def get_variables(tx, catalogue: str, prefixed_version_number: str):
    # Get variables from cdisc database
    # Some of them are beneath an extra Scenario level
    variables_data = tx.run(
        """
        MATCH (import:DataModelImport{catalogue: $catalogue, version_number: $prefixed_version_number})
            -[:INCLUDES]->(version)-[:CONTAINS]->(class:DataModelClass)-[:CONTAINS]->(variable:DataModelVariable)
        RETURN variable, class.href AS parent_href, "class" AS parent_type
        UNION
        MATCH (import:DataModelImport{catalogue: $catalogue, version_number: $prefixed_version_number})
            -[:INCLUDES]->(version)-[:CONTAINS]->(class:DataModelClass)-[:CONTAINS]->(scenario:DataModelScenario)-[:CONTAINS]->(variable:DataModelVariable)
        RETURN variable, scenario.href AS parent_href, "scenario" AS parent_type
        """,
        catalogue=catalogue,
        prefixed_version_number=prefixed_version_number,
    ).data()
    for item in variables_data:
        item["variable"]["uid"] = sanitize_string(item["variable"]["name"])

    return variables_data


def merge_structure_nodes_and_relationships(
    tx, version_data, classes_data, scenarios_data, variables_data
):
    merge_catalogues_and_versions(tx, version_data)
    merge_version_independent_data(
        tx,
        version_data=version_data,
        classes_data=classes_data,
        scenarios_data=scenarios_data,
        variables_data=variables_data,
    )


def merge_catalogues_and_versions(tx, version_data):
    tx.run(
        """
        WITH $version_data as version_data
        WITH version_data, coalesce(version_data.library, 'CDISC') AS library_name
        WITH version_data, library_name, library_name='Sponsor' AS is_editable
        MERGE (library:Library{name: library_name})
        ON CREATE SET library.is_editable = is_editable
        WITH library, $version_data as version_data
        MERGE (catalogue:DataModelCatalogue{name: version_data.catalogue})
        ON CREATE SET catalogue.data_model_type = version_data.data_model_type
        MERGE (library)-[:CONTAINS_CATALOGUE]->(catalogue)
        MERGE (version:DataModelVersion{uid: version_data.uid})
        ON CREATE SET
            version.name = version_data.name,
            version.label = version_data.label,
            version.description = version_data.description,
            version.source = version_data.source,
            version.effective_date = date(version_data.effective_date),
            version.registration_status = version_data.registration_status,
            version.href = version_data.href,
            version.implements_data_model = version_data.implements_data_model,
            
            version.import_date = datetime(),
            version.author_id = $author_id
        MERGE (catalogue)-[:CONTAINS_VERSION]->(version)
        """,
        version_data=version_data,
        author_id=AUTHOR_ID,
    )


def merge_version_independent_data(
    tx, version_data, classes_data, scenarios_data, variables_data
):
    data_model_root_label = ""
    contains_model_rel_type = ""
    catalogue_to_model_rel_type = ""
    data_model_uid = ""
    class_root_label = ""
    scenario_root_label = SCENARIO_ROOT_LABEL
    variable_root_label = ""
    catalogue_to_dataset_rel_type = ""
    catalogue_to_variable_rel_type = ""
    catalogue_to_scenario_rel_type = CATALOGUE_TO_SCENARIO_REL_TYPE

    if version_data["data_model_type"] == DataModelType.FOUNDATIONAL.value:
        data_model_root_label = DATA_MODEL_ROOT_LABEL
        class_root_label = DATASET_CLASS_ROOT_LABEL
        variable_root_label = VARIABLE_CLASS_ROOT_LABEL
        contains_model_rel_type = VERSION_TO_DATA_MODEL_REL_TYPE
        catalogue_to_model_rel_type = CATALOGUE_TO_DATA_MODEL_REL_TYPE
        catalogue_to_dataset_rel_type = CATALOGUE_TO_CLASS_ROOT_REL_TYPE
        catalogue_to_variable_rel_type = CLASS_TO_VARIABLE_CLASS_ROOT_REL_TYPE
        data_model_uid = sanitize_string(version_data["catalogue"])

    elif version_data["data_model_type"] == DataModelType.IMPLEMENTATION.value:
        data_model_root_label = DATA_MODEL_IG_ROOT_LABEL
        class_root_label = DATASET_ROOT_LABEL
        variable_root_label = DATASET_VARIABLE_ROOT_LABEL
        contains_model_rel_type = VERSION_TO_DATA_MODEL_IG_REL_TYPE
        catalogue_to_model_rel_type = CATALOGUE_TO_DATA_MODEL_IG_REL_TYPE
        catalogue_to_dataset_rel_type = CATALOGUE_TO_DATASET_ROOT_REL_TYPE
        catalogue_to_variable_rel_type = CLASS_TO_DATASET_VARIABLE_ROOT_REL_TYPE
        data_model_uid = sanitize_string(
            parse_ig_name(
                catalogue=version_data["catalogue"], href=version_data["href"]
            )
        )

    query = f"""
        WITH $version_data as version_data
        MATCH (library:Library{{name: coalesce(version_data.library, 'CDISC')}})
        MATCH (catalogue:DataModelCatalogue{{name: version_data.catalogue}})
        MATCH (version:DataModelVersion{{uid: version_data.uid}})

        MERGE (dm_root:{data_model_root_label}{{uid: $data_model_uid}})
        MERGE (library)-[:{contains_model_rel_type}]->(dm_root)
        MERGE (catalogue)-[:{catalogue_to_model_rel_type}]->(dm_root)

        WITH catalogue
        UNWIND $classes_data AS class
            MERGE (class_root:{class_root_label}{{uid:class.class.uid}})
            MERGE (catalogue)-[:{catalogue_to_dataset_rel_type}]->(class_root)
        WITH catalogue
        UNWIND $variables_data AS variable
            MERGE (variable_root:{variable_root_label}{{uid:variable.variable.uid}})
            MERGE (catalogue)-[:{catalogue_to_variable_rel_type}]->(variable_root)
        WITH catalogue
        UNWIND $scenarios_data AS scenario
            MERGE (scenario_root:{scenario_root_label}{{uid:scenario.scenario.uid}})
            MERGE (catalogue)-[:{catalogue_to_scenario_rel_type}]->(scenario_root)
    """

    tx.run(
        query,
        version_data=version_data,
        classes_data=classes_data,
        scenarios_data=scenarios_data,
        variables_data=variables_data,
        data_model_uid=data_model_uid,
    )


def merge_data_model(tx, version_data):
    is_foundational = (
        version_data["data_model_type"] == DataModelType.FOUNDATIONAL.value
    )
    data_model_uid = sanitize_string(
        version_data["catalogue"]
        if is_foundational
        else parse_ig_name(
            catalogue=version_data["catalogue"], href=version_data["href"]
        )
    )
    label_prefix = "DataModel" if is_foundational else "DataModelIG"
    root_label = label_prefix + "Root"
    value_label = label_prefix + "Value"
    version_rel_type = (
        "CONTAINS_DATA_MODEL" if is_foundational else "CONTAINS_DATA_MODEL_IG"
    )
    result = tx.run(
        f"""
        MATCH (dm_root:{root_label}{{uid: $data_model_uid}})-[:{MODEL_VERSION_REL_TYPE}]->(dm_value:{value_label})
        RETURN DISTINCT dm_value.version_number AS version_number
    """,
        data_model_uid=data_model_uid,
    )
    existing_versions = list(result.value())

    prefixed_version_number = _prettify_version_number(version_data["version_number"])
    version_number = _prettify_version_number(
        version_data["version_number"], number_only=True
    )
    if prefixed_version_number not in existing_versions:
        tx.run(
            f"""
            WITH $version_data as version_data
            MATCH (dm_root:{root_label}{{uid: $data_model_uid}})
            MATCH (dm_root)-[r1:{MODEL_VERSION_REL_TYPE}]->(:{value_label})<-[:LATEST]-(dm_root)
            SET r1.end_date=datetime(version_data.effective_date), r1.change_description="New version imported"
            WITH dm_root
            MATCH (dm_root)-[r2]->(:{value_label})
            WHERE NOT type(r2)='{MODEL_VERSION_REL_TYPE}'
            DELETE r2
        """,
            version_data=version_data,
            data_model_uid=data_model_uid,
        )
        # Then, create new version with relationships
        tx.run(
            f"""
            WITH $version_data as version_data
            MATCH (dm_root:{root_label}{{uid: $data_model_uid}})
            CREATE (dm_value:{value_label})
            SET
                dm_value.name = version_data.name,
                dm_value.description = version_data.description,
                dm_value.version_number = $prefixed_version_number,
                dm_value.effective_date = date(version_data.effective_date)
            CREATE (dm_root)-[:{MODEL_VERSION_REL_TYPE} {{
                change_description: "Initial import",
                start_date: datetime(version_data.effective_date),
                status: version_data.registration_status,
                author_id: $author_id,
                version: $version_number
            }}]->(dm_value)
            CREATE (dm_root)-[:LATEST_FINAL]->(dm_value)
            CREATE (dm_root)-[:LATEST]->(dm_value)
            WITH dm_value, version_data
            MATCH (v:DataModelVersion {{uid: version_data.uid}})
            CREATE (v)-[:{version_rel_type}]->(dm_value)
        """,
            data_model_uid=data_model_uid,
            version_data=version_data,
            version_number=version_number,
            prefixed_version_number=prefixed_version_number,
            author_id=AUTHOR_ID,
        )

    if not is_foundational:
        link_ig_with_data_model(tx, version_data)


def _get_class_instances(tx, catalogue, data_model_type, uid):
    class_root_label = ""
    version_to_class_rel_type = ""
    if data_model_type == DataModelType.FOUNDATIONAL.value:
        class_root_label = DATASET_CLASS_ROOT_LABEL
        version_to_class_rel_type = VERSION_TO_CLASS_REL_TYPE
    elif data_model_type == DataModelType.IMPLEMENTATION.value:
        class_root_label = DATASET_ROOT_LABEL
        version_to_class_rel_type = VERSION_TO_DATASET_REL_TYPE
    result = tx.run(
        f"""
                MATCH (:{class_root_label}{{uid: $uid}})-[:{CLASS_VERSION_REL_TYPE}]->(value)
                    <-[:{version_to_class_rel_type}]-(:DataModelVersion)<-[:CONTAINS_VERSION]-(catalogue:DataModelCatalogue {{name: $catalogue}})
                RETURN DISTINCT value
                """,
        uid=uid,
        catalogue=catalogue,
    )
    records = [record for record in result]

    return records


def _get_scenario_instances(tx, catalogue, uid):
    scenario_root_label = SCENARIO_ROOT_LABEL
    version_to_scenario_rel_type = VERSION_TO_SCENARIO_REL_TYPE
    result = tx.run(
        f"""
                MATCH (:{scenario_root_label}{{uid: $uid}})-[:HAS_INSTANCE]->(instance)
                    <-[:{version_to_scenario_rel_type}]-(:DataModelVersion)<-[:CONTAINS_VERSION]-(catalogue:DataModelCatalogue {{name: $catalogue}})
                RETURN DISTINCT instance
                """,
        uid=uid,
        catalogue=catalogue,
    )
    records = [record for record in result]

    return records


def _get_variable_instances(tx, catalogue, data_model_type, parent_type, uid):
    model_root_label = ""
    model_value_label = ""
    class_value_label = ""
    scenario_value_label = SCENARIO_VALUE_LABEL
    variable_root_label = ""
    scenario_variable_value_label = SCENARIO_VARIABLE_VALUE_LABEL
    version_to_variable_rel_type = ""
    class_to_scenario_rel_type = CLASS_TO_SCENARIO_REL_TYPE
    scenario_to_variable_rel_type = SCENARIO_TO_VARIABLE_REL_TYPE
    variable_to_scenario_variable_rel_type = VARIABLE_TO_SCENARIO_VARIABLE_REL_TYPE
    scenario_variable_to_scenario_rel_type = SCENARIO_VARIABLE_TO_SCENARIO_REL_TYPE
    if data_model_type == DataModelType.FOUNDATIONAL.value:
        model_root_label = DATA_MODEL_ROOT_LABEL
        model_value_label = DATA_MODEL_VALUE_LABEL
        class_value_label = DATASET_CLASS_VALUE_LABEL
        variable_root_label = VARIABLE_CLASS_ROOT_LABEL
        version_to_variable_rel_type = VERSION_TO_VARIABLE_CLASS_REL_TYPE
    elif data_model_type == DataModelType.IMPLEMENTATION.value:
        model_root_label = DATA_MODEL_IG_ROOT_LABEL
        model_value_label = DATA_MODEL_IG_VALUE_LABEL
        class_value_label = DATASET_VALUE_LABEL
        variable_root_label = DATASET_VARIABLE_ROOT_LABEL
        version_to_variable_rel_type = VERSION_TO_DATASET_VARIABLE_REL_TYPE

    query = ""

    if parent_type == "class":
        query = f"""
            MATCH (:{variable_root_label}{{uid: $uid}})-[:HAS_INSTANCE]->(instance)
                <-[:{version_to_variable_rel_type}]-(:DataModelVersion)<-[:CONTAINS_VERSION]-(catalogue:DataModelCatalogue {{name: $catalogue}})
            RETURN DISTINCT instance
        """
    elif parent_type == "scenario":
        # Merges properties from the DatasetVariableInstance and its ScenarioVariableImplementation nodes
        # For scenarii in the given catalogue and dataset
        # Includes the node id of the variable and scenario variable implementation nodes
        query = f"""
            MATCH (:{variable_root_label}{{uid: $uid}})-[:HAS_INSTANCE]->(instance)
                <-[:{scenario_to_variable_rel_type}]-(scenario:{scenario_value_label})<-[:{class_to_scenario_rel_type}]-(:{class_value_label})
                <--(:{model_value_label})<--(:{model_root_label})<--(catalogue:DataModelCatalogue {{name: $catalogue}})
            MATCH (scenario)<-[:{scenario_variable_to_scenario_rel_type}]-(impl:{scenario_variable_value_label})
                <-[:{variable_to_scenario_variable_rel_type}]-(instance)
            RETURN DISTINCT apoc.map.mergeList([{{id: id(instance)}}, {{id_impl: id(impl)}}, instance{{.*}}, impl{{.*}}]) AS instance
        """
    result = tx.run(
        query,
        uid=uid,
        catalogue=catalogue,
    )
    records = [record for record in result]

    return records


def _get_reusable_class(existing_classes, target_class):
    for _class in existing_classes:
        value = _class["value"]
        reusable_version_id = (
            value.id if hasattr(value, "id") else value.get("id", None)
        )

        if (
            value.get("title", None) != target_class.get("title", None)
            or value.get("label", None) != target_class.get("label", None)
            or value.get("description", None) != target_class.get("description", None)
        ):
            continue
        else:
            return reusable_version_id
    return None


def merge_classes(tx, version_data, classes_data):
    nbr_unchanged = 0
    nbr_updated = 0
    nbr_new = 0
    for class_data in classes_data:
        _class = class_data.get("class", None)

        records = _get_class_instances(
            tx,
            catalogue=version_data["catalogue"],
            data_model_type=version_data["data_model_type"],
            uid=_class["uid"],
        )
        if records:
            reusable_version_id = _get_reusable_class(records, _class)

            if reusable_version_id is None:
                create_new_class_instance(tx, version_data=version_data, _class=_class)
                nbr_updated += 1

            else:
                use_existing_class_instance(
                    tx,
                    version_data=version_data,
                    _class=_class,
                    reusable_instance_id=reusable_version_id,
                )
                nbr_unchanged += 1
        else:
            create_initial_class_instance(tx, version_data=version_data, _class=_class)
            nbr_new += 1

    for class_data in [
        c["class"]
        for c in classes_data
        if c["class"]["subclasses"] is not None and len(c["class"]["subclasses"]) > 0
    ]:
        link_class_with_subclasses(
            tx,
            _class=class_data,
            subclasses=class_data.get("subclasses", []),
            prefixed_version_number=_prettify_version_number(
                version_data["version_number"]
            ),
        )
    return nbr_new, nbr_updated, nbr_unchanged


def _get_reusable_scenario(existing_scenarios, target_scenario):
    for scenario in existing_scenarios:
        instance = scenario["instance"]
        reusable_version_id = (
            instance.id if hasattr(instance, "id") else instance.get("id", None)
        )
        if instance.get("label", None) != target_scenario.get("label", None):
            continue
        else:
            return reusable_version_id


def merge_scenarios(tx, version_data, scenarios_data):
    nbr_unchanged = 0
    nbr_updated = 0
    nbr_new = 0
    for scenario_data in scenarios_data:
        scenario = scenario_data.get("scenario", None)
        dataset_href = scenario_data.get("dataset_href", None)

        records = _get_scenario_instances(
            tx,
            catalogue=version_data["catalogue"],
            uid=scenario["uid"],
        )
        if records:
            reusable_instance_id = _get_reusable_scenario(records, scenario)
            if reusable_instance_id is None:
                create_new_scenario_instance(
                    tx,
                    version_data=version_data,
                    scenario=scenario,
                    dataset_href=dataset_href,
                )
                nbr_updated += 1
            else:
                use_existing_scenario_instance(
                    tx,
                    version_data=version_data,
                    scenario=scenario,
                    dataset_href=dataset_href,
                    reusable_instance_id=reusable_instance_id,
                )
                nbr_unchanged += 1
        else:
            create_initial_scenario_instance(tx, version_data, scenario, dataset_href)
            nbr_new += 1

    return nbr_new, nbr_updated, nbr_unchanged


def _get_reusable_variable_ids(existing_variables, target_variable):
    for _variable in existing_variables:
        value = _variable["instance"]
        reusable_version_id = (
            value.id if hasattr(value, "id") else value.get("id", None)
        )
        # For scenarii, it will reuse a variable if a combination of variable and scenario variable implementation
        # Properties already matches that new one
        reusable_scenario_impl_id = value.get("id_impl", None)
        if (
            value.get("title", None) != target_variable.get("title", None)
            or value.get("label", None) != target_variable.get("label", None)
            or value.get("description", None)
            != target_variable.get("description", None)
            or value.get("role", None) != target_variable.get("role", None)
            or value.get("notes", None) != target_variable.get("notes", None)
            or value.get("variable_c_code", None)
            != target_variable.get("variable_c_code", None)
            or value.get("usage_restrictions", None)
            != target_variable.get("usage_restrictions", None)
            or value.get("examples", None) != target_variable.get("examples", None)
            or value.get("value_list", None) != target_variable.get("value_list", None)
            or value.get("described_value_domain", None)
            != target_variable.get("described_value_domain", None)
            or value.get("role_description", None)
            != target_variable.get("role_description", None)
            or value.get("simple_datatype", None)
            != target_variable.get("simple_datatype", None)
            or value.get("length", None) != target_variable.get("length", None)
            or value.get("implementation_notes", None)
            != target_variable.get("implementation_notes", None)
            or value.get("mapping_instructions", None)
            != target_variable.get("mapping_instructions", None)
            or value.get("prompt", None) != target_variable.get("prompt", None)
            or value.get("question_text", None)
            != target_variable.get("question_text", None)
            or value.get("completion_instructions", None)
            != target_variable.get("completion_instructions", None)
            or value.get("core", None) != target_variable.get("core", None)
            or value.get("analysis_variable_set", None)
            != target_variable.get("analysis_variable_set", None)
        ):
            continue
        else:
            return reusable_version_id, reusable_scenario_impl_id
    return None, None


def merge_variables(tx, version_data, variables_data):
    nbr_unchanged = 0
    nbr_updated = 0
    nbr_new = 0
    for variable_data in variables_data:
        # First, iterate over all variables
        # If this uid already has at least one instance
        # Then either create a new one if some properties changed
        # Or reuse the instance with same properties
        # If there are no instances at all, create one for the first time
        variable = variable_data.get("variable", None)
        parent_href = variable_data.get("parent_href", None)
        parent_type = variable_data.get("parent_type", None)

        value_list_mappings = parse_value_list_mapping_file()

        records = _get_variable_instances(
            tx,
            catalogue=version_data["catalogue"],
            data_model_type=version_data["data_model_type"],
            parent_type=parent_type,
            uid=variable["uid"],
        )
        if records:
            (
                reusable_instance_id,
                reusable_scenario_impl_id,
            ) = _get_reusable_variable_ids(records, variable)
            if reusable_instance_id is None:
                create_new_variable_instance(
                    tx,
                    version_data=version_data,
                    variable=variable,
                    parent_href=parent_href,
                    parent_type=parent_type,
                    value_list_mappings=value_list_mappings,
                )
                nbr_updated += 1
            else:
                use_existing_variable_instance(
                    tx,
                    version_data=version_data,
                    variable=variable,
                    parent_href=parent_href,
                    instance_node_id=reusable_instance_id,
                    scenario_impl_node_id=reusable_scenario_impl_id,
                    parent_type=parent_type,
                )
                nbr_unchanged += 1
        else:
            create_initial_variable_instance(
                tx,
                version_data=version_data,
                variable=variable,
                parent_href=parent_href,
                parent_type=parent_type,
                value_list_mappings=value_list_mappings,
            )
            nbr_new += 1

    for variable_data in variables_data:
        # Iterate again over all variables to create the QUALIFIES_VARIABLES relationships
        # Those exist between two variables of the same version
        # So we need to ensure everything has been created first or we will miss relationships
        variable = variable_data.get("variable", None)
        if (
            "qualifies_variables" in variable
            and len(variable["qualifies_variables"]) > 0
        ):
            create_qualify_variable_relationships(
                tx,
                source_variable=variable,
                prefixed_version_number=_prettify_version_number(
                    version_data["version_number"]
                ),
            )

    return nbr_new, nbr_updated, nbr_unchanged


def parse_value_list_mapping_file() -> "dict[str, ValueListMapping]":
    # Read the variable value list mappings CSV file
    # And load the records into a dictionary of ValueListMapping objects
    # Dictionary entry key should be sponsormodelname_datasetuid_value
    value_list_mappings = {}

    if os.path.isfile(VARIABLE_VALUE_LIST_MAPPINGS_FILE) is True:
        with open(VARIABLE_VALUE_LIST_MAPPINGS_FILE, "r") as f:
            csv_reader = csv.reader(f)

            headers = next(csv_reader)

            for row in csv_reader:
                sponsor_model_name = row[headers.index("model_name")]
                dataset_uid = row[headers.index("dataset_uid")]
                variable_uid = row[headers.index("variable_uid")]
                code_submission_value = row[headers.index("term_code_submission_value")]

                key = f"{sponsor_model_name}_{dataset_uid}_{variable_uid}_{code_submission_value}"

                # Create a ValueListMapping object and add it to the dictionary
                # You would need to define the ValueListMapping class
                value_list_mappings[key] = ValueListMapping(
                    model_name=sponsor_model_name,
                    dataset_uid=dataset_uid,
                    term_code_submission_value=code_submission_value,
                    term_uid=row[headers.index("term_uid")],
                    variable_uid=variable_uid,
                    codelist_uid=row[headers.index("codelist_uid")],
                )

    return value_list_mappings


def create_initial_class_instance(tx, version_data, _class):
    model_value_label = ""
    class_root_label = ""
    class_value_label = ""
    model_to_class_rel_type = ""
    version_to_model_rel_type = ""
    version_to_class_rel_type = ""
    prefixed_version_number = _prettify_version_number(version_data["version_number"])
    if version_data["data_model_type"] == DataModelType.FOUNDATIONAL.value:
        model_value_label = DATA_MODEL_VALUE_LABEL
        class_root_label = DATASET_CLASS_ROOT_LABEL
        class_value_label = DATASET_CLASS_VALUE_LABEL
        model_to_class_rel_type = CATALOGUE_TO_CLASS_ROOT_REL_TYPE
        version_to_model_rel_type = VERSION_TO_DATA_MODEL_REL_TYPE
        version_to_class_rel_type = VERSION_TO_CLASS_REL_TYPE
    elif version_data["data_model_type"] == DataModelType.IMPLEMENTATION.value:
        model_value_label = DATA_MODEL_IG_VALUE_LABEL
        class_root_label = DATASET_ROOT_LABEL
        class_value_label = DATASET_VALUE_LABEL
        model_to_class_rel_type = CATALOGUE_TO_DATASET_ROOT_REL_TYPE
        version_to_model_rel_type = VERSION_TO_DATA_MODEL_IG_REL_TYPE
        version_to_class_rel_type = VERSION_TO_DATASET_REL_TYPE

    tx.run(
        f"""
            MATCH (root:{class_root_label}{{uid: $uid}})
            CREATE (instance: {class_value_label})
            SET
               instance.title = $class_data.title,
               instance.label = $class_data.label,
               instance.description = $class_data.description
            CREATE (root)-[:{CLASS_VERSION_REL_TYPE}]->(instance)

            WITH instance
            MATCH (dmv:DataModelVersion {{href: $version_href}})-[{version_to_model_rel_type}]->(model_value:{model_value_label})
            MERGE (dmv)-[contains_class:{version_to_class_rel_type}]->(instance)
            SET contains_class.href=$class_data.href
            MERGE (model_value)-[has_class:{model_to_class_rel_type}]->(instance)
            ON CREATE SET has_class.ordinal = $class_data.ordinal

            WITH instance
            MATCH ()-[rel]->(prior_instance_node)<-[:{CLASS_VERSION_REL_TYPE}]-(prior_root_node)
            WHERE rel.href=$class_data.prior_version AND (rel:{VERSION_TO_CLASS_REL_TYPE} OR rel:{VERSION_TO_DATASET_REL_TYPE})
            CALL apoc.do.when($uid<>prior_root_node.uid,
                'WITH $instance AS instance, $prior_instance_node AS prior_instance_node MERGE (instance)<-[rep:REPLACED_BY]-(prior_instance_node) SET rep.catalogue=$catalogue, rep.version_number=$prefixed_version_number RETURN rep',
                '',
                {{prior_instance_node: prior_instance_node, instance: instance, catalogue: $class_data.catalogue, prefixed_version_number: $prefixed_version_number}}
            )
            YIELD value AS result
            RETURN result
        """,
        uid=_class["uid"],
        effective_date=version_data["effective_date"],
        class_data=_class,
        version_href=version_data["href"],
        prefixed_version_number=prefixed_version_number,
        author_id=AUTHOR_ID,
    )

    if version_data["data_model_type"] == DataModelType.IMPLEMENTATION.value:
        link_dataset_with_class(tx, _class, prefixed_version_number)


def create_new_class_instance(tx, version_data, _class):
    model_value_label = ""
    class_value_label = ""
    model_to_class_rel_type = ""
    version_to_model_rel_type = ""
    version_to_class_rel_type = ""
    prefixed_version_number = _prettify_version_number(version_data["version_number"])
    if version_data["data_model_type"] == DataModelType.FOUNDATIONAL.value:
        model_value_label = DATA_MODEL_VALUE_LABEL
        class_value_label = DATASET_CLASS_VALUE_LABEL
        model_to_class_rel_type = CATALOGUE_TO_CLASS_ROOT_REL_TYPE
        version_to_model_rel_type = VERSION_TO_DATA_MODEL_REL_TYPE
        version_to_class_rel_type = VERSION_TO_CLASS_REL_TYPE
    elif version_data["data_model_type"] == DataModelType.IMPLEMENTATION.value:
        model_value_label = DATA_MODEL_IG_VALUE_LABEL
        class_value_label = DATASET_VALUE_LABEL
        model_to_class_rel_type = CATALOGUE_TO_DATASET_ROOT_REL_TYPE
        version_to_model_rel_type = VERSION_TO_DATA_MODEL_IG_REL_TYPE
        version_to_class_rel_type = VERSION_TO_DATASET_REL_TYPE

    tx.run(
        f"""
            MATCH (root{{uid: $uid}})
            CREATE (new_instance: {class_value_label})
            SET
               new_instance.title = $class_data.title,
               new_instance.label = $class_data.label,
               new_instance.description = $class_data.description
            CREATE (root)-[:{CLASS_VERSION_REL_TYPE}]->(new_instance)

            WITH new_instance
            MATCH (dmv:DataModelVersion {{href: $version_href}})-[{version_to_model_rel_type}]->(model_value:{model_value_label})
            MERGE (dmv)-[contains_class:{version_to_class_rel_type}]->(new_instance)
            SET contains_class.href=$class_data.href
            MERGE (model_value)-[has_class:{model_to_class_rel_type}]->(new_instance)
            ON CREATE SET has_class.ordinal = $class_data.ordinal

            WITH new_instance
            MATCH ()-[rel]->(prior_instance_node)<-[:{CLASS_VERSION_REL_TYPE}]-(prior_root_node)
            WHERE rel.href=$class_data.prior_version AND (rel:{VERSION_TO_CLASS_REL_TYPE} OR rel:{VERSION_TO_DATASET_REL_TYPE})
            CALL apoc.do.when($uid<>prior_root_node.uid,
                'WITH $new_instance AS new_instance, $prior_instance_node AS prior_instance_node MERGE (new_instance)<-[rep:REPLACED_BY]-(prior_instance_node) SET rep.catalogue=$catalogue, rep.version_number=$prefixed_version_number RETURN rep',
                '',
                {{prior_instance_node: prior_instance_node, new_instance: new_instance, catalogue: $class_data.catalogue, prefixed_version_number: $prefixed_version_number}}
            )
            YIELD value AS result
            RETURN result
        """,
        uid=_class["uid"],
        effective_date=version_data["effective_date"],
        class_data=_class,
        version_href=version_data["href"],
        prefixed_version_number=prefixed_version_number,
        author_id=AUTHOR_ID,
    )

    if version_data["data_model_type"] == DataModelType.IMPLEMENTATION.value:
        link_dataset_with_class(tx, _class, prefixed_version_number)


def use_existing_class_instance(tx, version_data, _class, reusable_instance_id):
    model_value_label = ""
    model_to_class_rel_type = ""
    version_to_model_rel_type = ""
    version_to_class_rel_type = ""
    prefixed_version_number = _prettify_version_number(version_data["version_number"])
    if version_data["data_model_type"] == DataModelType.FOUNDATIONAL.value:
        model_value_label = DATA_MODEL_VALUE_LABEL
        model_to_class_rel_type = CATALOGUE_TO_CLASS_ROOT_REL_TYPE
        version_to_model_rel_type = VERSION_TO_DATA_MODEL_REL_TYPE
        version_to_class_rel_type = VERSION_TO_CLASS_REL_TYPE
    elif version_data["data_model_type"] == DataModelType.IMPLEMENTATION.value:
        model_value_label = DATA_MODEL_IG_VALUE_LABEL
        model_to_class_rel_type = CATALOGUE_TO_DATASET_ROOT_REL_TYPE
        version_to_model_rel_type = VERSION_TO_DATA_MODEL_IG_REL_TYPE
        version_to_class_rel_type = VERSION_TO_DATASET_REL_TYPE
    tx.run(
        f"""
            MATCH (instance)
            WHERE id(instance)=$reusable_instance_id
            MATCH (dmv:DataModelVersion {{href: $version_href}})-[{version_to_model_rel_type}]->(model_value:{model_value_label})
            MERGE (dmv)-[contains_class:{version_to_class_rel_type}]->(instance)
            SET contains_class.href=$class_data.href
            MERGE (model_value)-[has_class:{model_to_class_rel_type}]->(instance)
            ON CREATE SET has_class.ordinal = $class_data.ordinal

            WITH instance
            MATCH ()-[rel]->(prior_instance_node)<-[:{CLASS_VERSION_REL_TYPE}]-(prior_root_node)
            WHERE rel.href=$class_data.prior_version AND (rel:{VERSION_TO_CLASS_REL_TYPE} OR rel:{VERSION_TO_DATASET_REL_TYPE})
            CALL apoc.do.when($uid<>prior_root_node.uid,
                'WITH $instance AS instance, $prior_instance_node AS prior_instance_node MERGE (instance)<-[rep:REPLACED_BY]-(prior_instance_node) SET rep.catalogue=$catalogue, rep.version_number=$prefixed_version_number RETURN rep',
                '',
                {{prior_instance_node: prior_instance_node, instance: instance, catalogue: $class_data.catalogue, prefixed_version_number: $prefixed_version_number}}
            )
            YIELD value AS result
            RETURN result
        """,
        uid=_class["uid"],
        reusable_instance_id=reusable_instance_id,
        class_data=_class,
        version_href=version_data["href"],
        prefixed_version_number=prefixed_version_number,
    )

    if version_data["data_model_type"] == DataModelType.IMPLEMENTATION.value:
        link_dataset_with_class(tx, _class, prefixed_version_number)


def create_initial_scenario_instance(tx, version_data, scenario, dataset_href):
    prefixed_version_number = _prettify_version_number(version_data["version_number"])
    class_value_label = ""
    scenario_root_label = SCENARIO_ROOT_LABEL
    scenario_value_label = SCENARIO_VALUE_LABEL
    class_to_scenario_rel_type = CLASS_TO_SCENARIO_REL_TYPE
    version_to_class_rel_type = ""
    version_to_scenario_rel_type = VERSION_TO_SCENARIO_REL_TYPE
    if version_data["data_model_type"] == DataModelType.FOUNDATIONAL.value:
        class_value_label = DATASET_CLASS_VALUE_LABEL
        version_to_class_rel_type = VERSION_TO_CLASS_REL_TYPE
    elif version_data["data_model_type"] == DataModelType.IMPLEMENTATION.value:
        class_value_label = DATASET_VALUE_LABEL
        version_to_class_rel_type = VERSION_TO_DATASET_REL_TYPE

    tx.run(
        f"""
            MATCH (root:{scenario_root_label}{{uid: $uid}})
            CREATE (instance:{scenario_value_label})
            SET
               instance.label = $scenario_data.label
            CREATE (root)-[:{SCENARIO_VERSION_REL_TYPE}]->(instance)

            WITH instance
            MATCH (dmv:DataModelVersion {{href: $version_href}})-[rel:{version_to_class_rel_type}]->(class_value:{class_value_label})
                WHERE rel.href=$dataset_href
            MERGE (dmv)-[contains_scenario:{version_to_scenario_rel_type} {{href: $scenario_data.href}}]->(instance)
            MERGE (class_value)-[has_scenario:{class_to_scenario_rel_type}]->(instance)
            SET contains_scenario.href=$scenario_data.href, has_scenario.ordinal = $scenario_data.ordinal, has_scenario.version_number = $prefixed_version_number
        """,
        uid=scenario["uid"],
        effective_date=version_data["effective_date"],
        prefixed_version_number=prefixed_version_number,
        scenario_data=scenario,
        version_href=version_data["href"],
        dataset_href=dataset_href,
        author_id=AUTHOR_ID,
    )


def create_new_scenario_instance(tx, version_data, scenario, dataset_href):
    prefixed_version_number = _prettify_version_number(version_data["version_number"])
    class_value_label = ""
    scenario_value_label = SCENARIO_VALUE_LABEL
    class_to_scenario_rel_type = CLASS_TO_SCENARIO_REL_TYPE
    version_to_class_rel_type = ""
    version_to_scenario_rel_type = VERSION_TO_SCENARIO_REL_TYPE
    if version_data["data_model_type"] == DataModelType.FOUNDATIONAL.value:
        class_value_label = DATASET_CLASS_VALUE_LABEL
        version_to_class_rel_type = VERSION_TO_CLASS_REL_TYPE
    elif version_data["data_model_type"] == DataModelType.IMPLEMENTATION.value:
        class_value_label = DATASET_VALUE_LABEL
        version_to_class_rel_type = VERSION_TO_DATASET_REL_TYPE

    tx.run(
        f"""
        MATCH (root{{uid: $uid}})
        CREATE (new_instance: {scenario_value_label})
        SET
            new_instance.label = $scenario_data.label
        CREATE (root)-[:{SCENARIO_VERSION_REL_TYPE}]->(new_instance)

        WITH new_instance
        MATCH (dmv:DataModelVersion {{href: $version_href}})-[rel:{version_to_class_rel_type}]->(class_value:{class_value_label})
            WHERE rel.href=$dataset_href
        MERGE (dmv)-[contains_scenario:{version_to_scenario_rel_type} {{href: $scenario_data.href}}]->(new_instance)
        CREATE (class_value)-[has_scenario:{class_to_scenario_rel_type}]->(new_instance)
        SET contains_scenario.href=$scenario_data.href, has_scenario.ordinal = $scenario_data.ordinal, has_scenario.version_number = $prefixed_version_number
        """,
        uid=scenario["uid"],
        effective_date=version_data["effective_date"],
        prefixed_version_number=prefixed_version_number,
        scenario_data=scenario,
        version_href=version_data["href"],
        dataset_href=dataset_href,
        author_id=AUTHOR_ID,
    )


def use_existing_scenario_instance(
    tx, version_data, scenario, dataset_href, reusable_instance_id
):
    prefixed_version_number = _prettify_version_number(version_data["version_number"])
    class_value_label = ""
    class_to_scenario_rel_type = CLASS_TO_SCENARIO_REL_TYPE
    version_to_class_rel_type = ""
    version_to_scenario_rel_type = VERSION_TO_SCENARIO_REL_TYPE
    if version_data["data_model_type"] == DataModelType.FOUNDATIONAL.value:
        class_value_label = DATASET_CLASS_VALUE_LABEL
        version_to_class_rel_type = VERSION_TO_CLASS_REL_TYPE
    elif version_data["data_model_type"] == DataModelType.IMPLEMENTATION.value:
        class_value_label = DATASET_VALUE_LABEL
        version_to_class_rel_type = VERSION_TO_DATASET_REL_TYPE

    tx.run(
        f"""
        MATCH (instance)
        WHERE id(instance)=$reusable_instance_id
        MATCH (dmv:DataModelVersion {{href: $version_href}})-[rel:{version_to_class_rel_type}]->(class_value:{class_value_label})
            WHERE rel.href=$dataset_href
        MERGE (dmv)-[:{version_to_scenario_rel_type} {{href: $scenario_data.href}}]->(instance)
        CREATE (class_value)-[has_scenario:{class_to_scenario_rel_type}]->(instance)
        SET has_scenario.ordinal = $scenario_data.ordinal, has_scenario.version_number = $prefixed_version_number
        """,
        uid=scenario["uid"],
        reusable_instance_id=reusable_instance_id,
        effective_date=version_data["effective_date"],
        prefixed_version_number=prefixed_version_number,
        scenario_data=scenario,
        version_href=version_data["href"],
        dataset_href=dataset_href,
    )


def build_variable_instance_query(
    instance_node_variable_name: str,
    parent_type: str,
    version_data: dict,
    create_version: bool = True,
):
    class_value_label = ""
    scenario_value_label = SCENARIO_VALUE_LABEL
    variable_value_label = ""
    scenario_variable_value_label = SCENARIO_VARIABLE_VALUE_LABEL
    variable_value_to_scenario_variable_value_rel_type = (
        VARIABLE_TO_SCENARIO_VARIABLE_REL_TYPE
    )
    class_to_variable_rel_type = ""
    scenario_to_variable_rel_type = SCENARIO_TO_VARIABLE_REL_TYPE
    version_to_class_rel_type = ""
    version_to_scenario_rel_type = VERSION_TO_SCENARIO_REL_TYPE
    version_to_variable_rel_type = ""
    version_to_scenario_variable_rel_type = VERSION_TO_SCENARIO_VARIABLE_REL_TYPE
    scenario_variable_to_scenario_rel_type = SCENARIO_VARIABLE_TO_SCENARIO_REL_TYPE
    if version_data["data_model_type"] == DataModelType.FOUNDATIONAL.value:
        class_value_label = DATASET_CLASS_VALUE_LABEL
        variable_value_label = VARIABLE_CLASS_VALUE_LABEL
        class_to_variable_rel_type = CLASS_TO_VARIABLE_CLASS_ROOT_REL_TYPE
        version_to_class_rel_type = VERSION_TO_CLASS_REL_TYPE
        version_to_variable_rel_type = VERSION_TO_VARIABLE_CLASS_REL_TYPE
    elif version_data["data_model_type"] == DataModelType.IMPLEMENTATION.value:
        class_value_label = DATASET_VALUE_LABEL
        variable_value_label = DATASET_VARIABLE_VALUE_LABEL
        class_to_variable_rel_type = CLASS_TO_DATASET_VARIABLE_ROOT_REL_TYPE
        version_to_class_rel_type = VERSION_TO_DATASET_REL_TYPE
        version_to_variable_rel_type = VERSION_TO_DATASET_VARIABLE_REL_TYPE

    create = f"""
            CREATE ({instance_node_variable_name}:{variable_value_label})
            SET
               {instance_node_variable_name}.title = $variable_data.title,
               {instance_node_variable_name}.label = $variable_data.label,
               {instance_node_variable_name}.simple_datatype = $variable_data.simple_datatype,
               {instance_node_variable_name}.length = $variable_data.length
    """
    with_clause = f" WITH {instance_node_variable_name} "

    versioning = f"""
        , root
        CREATE (root)-[:{VARIABLE_VERSION_REL_TYPE}]->({instance_node_variable_name})
    """

    variable_parents = ""

    codelists = """
        UNWIND $variable_data.codelists AS codelist
        MATCH (c:CTCodelistRoot {uid: codelist})
    """

    prior_version = f"""
        MATCH ()-[rel]->(prior_instance_node)<-[:{VARIABLE_VERSION_REL_TYPE}]-(prior_root_node)
        WHERE rel.href=$variable_data.prior_version AND 
            (rel:{VERSION_TO_VARIABLE_CLASS_REL_TYPE} OR rel:{VERSION_TO_DATASET_VARIABLE_REL_TYPE})
        CALL apoc.do.when($uid<>prior_root_node.uid,
            'WITH ${instance_node_variable_name} AS {instance_node_variable_name}, $prior_instance_node AS prior_instance_node MERGE ({instance_node_variable_name})<-[rep:REPLACED_BY]-(prior_instance_node) SET rep.catalogue=$catalogue, rep.version_number=$prefixed_version_number RETURN rep',
            '',
            {{prior_instance_node: prior_instance_node, {instance_node_variable_name}: {instance_node_variable_name}, catalogue: $variable_data.catalogue, prefixed_version_number: $prefixed_version_number}}
        )
        YIELD value AS result
        RETURN result
    """

    if parent_type == "class":
        create += f""",
                {instance_node_variable_name}.description = $variable_data.description,
                {instance_node_variable_name}.role = $variable_data.role,
                {instance_node_variable_name}.notes = $variable_data.notes,
                {instance_node_variable_name}.variable_c_code = $variable_data.variable_c_code,
                {instance_node_variable_name}.usage_restrictions = $variable_data.usage_restrictions,
                {instance_node_variable_name}.examples = $variable_data.examples,
                {instance_node_variable_name}.value_list = $variable_data.value_list,
                {instance_node_variable_name}.described_value_domain = $variable_data.described_value_domain,
                {instance_node_variable_name}.role_description = $variable_data.role_description,
                {instance_node_variable_name}.implementation_notes = $variable_data.implementation_notes,
                {instance_node_variable_name}.mapping_instructions = $variable_data.mapping_instructions,
                {instance_node_variable_name}.prompt = $variable_data.prompt,
                {instance_node_variable_name}.question_text = $variable_data.question_text,
                {instance_node_variable_name}.completion_instructions = $variable_data.completion_instructions,
                {instance_node_variable_name}.core = $variable_data.core,
                {instance_node_variable_name}.analysis_variable_set = $variable_data.analysis_variable_set
        """

        variable_parents = f"""
            MATCH (dmv:DataModelVersion {{href: $version_href}})-[rel:{version_to_class_rel_type}]->(class_value:{class_value_label})
                WHERE rel.href=$parent_href
            MERGE (dmv)-[:{version_to_variable_rel_type} {{href: $variable_data.href}}]->({instance_node_variable_name})
            MERGE (class_value)-[has_variable:{class_to_variable_rel_type} {{
                ordinal: $variable_data.ordinal,
                version_number: $prefixed_version_number
            }}]->({instance_node_variable_name})
        """

        codelists += f"""
            MERGE ({instance_node_variable_name})-[:REFERENCES_CODELIST]->(c)
        """

    elif parent_type == "scenario":
        scenario_value_variable_name = "scenario_variable_value"

        # Note: This clause will only be used if we are creating a new version
        create += f"""
            CREATE ({scenario_value_variable_name}:{scenario_variable_value_label})
            SET
                {scenario_value_variable_name}.description = $variable_data.description,
                {scenario_value_variable_name}.role = $variable_data.role,
                {scenario_value_variable_name}.notes = $variable_data.notes,
                {scenario_value_variable_name}.variable_c_code = $variable_data.variable_c_code,
                {scenario_value_variable_name}.usage_restrictions = $variable_data.usage_restrictions,
                {scenario_value_variable_name}.examples = $variable_data.examples,
                {scenario_value_variable_name}.value_list = $variable_data.value_list,
                {scenario_value_variable_name}.described_value_domain = $variable_data.described_value_domain,
                {scenario_value_variable_name}.role_description = $variable_data.role_description,
                {scenario_value_variable_name}.implementation_notes = $variable_data.implementation_notes,
                {scenario_value_variable_name}.mapping_instructions = $variable_data.mapping_instructions,
                {scenario_value_variable_name}.prompt = $variable_data.prompt,
                {scenario_value_variable_name}.question_text = $variable_data.question_text,
                {scenario_value_variable_name}.completion_instructions = $variable_data.completion_instructions,
                {scenario_value_variable_name}.core = $variable_data.core
        """

        variable_parents = ""
        # If we are not creating a new version, we need to match the ScenarioVariableImplementation node
        if create_version is False:
            variable_parents = f"MATCH ({scenario_value_variable_name}) WHERE id({scenario_value_variable_name})=$scenario_impl_node_id"

        # Regardless of whether we are creating a new version
        # We need to create the various relationships for the new catalogue version
        variable_parents += f"""
            MATCH (dmv:DataModelVersion {{href: $version_href}})-[rel:{version_to_scenario_rel_type}]->(scenario_value:{scenario_value_label})
                WHERE rel.href=$parent_href
            MERGE (dmv)-[:{version_to_variable_rel_type} {{href: $variable_data.href}}]->({instance_node_variable_name})
            MERGE (scenario_value)-[has_variable:{scenario_to_variable_rel_type} {{
                ordinal: $variable_data.ordinal,
                version_number: $prefixed_version_number
            }}]->({instance_node_variable_name})
            MERGE (dmv)-[contains_scenario_variable:{version_to_scenario_variable_rel_type}]->({scenario_value_variable_name})
            MERGE ({scenario_value_variable_name})-[:{scenario_variable_to_scenario_rel_type}]->(scenario_value)
            MERGE ({instance_node_variable_name})-[var_sc_rel:{variable_value_to_scenario_variable_value_rel_type}{{version_number: $prefixed_version_number}}]->({scenario_value_variable_name})
        """

        codelists += f"""
            MERGE ({scenario_value_variable_name})-[:REFERENCES_CODELIST]->(c)
        """

        with_clause += f", {scenario_value_variable_name}"

    if create_version is True:
        full_query = with_clause.join(
            [create, versioning, variable_parents, codelists, prior_version]
        )
    else:
        full_query = with_clause.join([variable_parents, prior_version])

    return full_query


def create_initial_variable_instance(
    tx, version_data, variable, parent_href, parent_type, value_list_mappings
):
    prefixed_version_number = _prettify_version_number(version_data["version_number"])
    variable_root_label = ""
    if version_data["data_model_type"] == DataModelType.FOUNDATIONAL.value:
        variable_root_label = VARIABLE_CLASS_ROOT_LABEL
    elif version_data["data_model_type"] == DataModelType.IMPLEMENTATION.value:
        variable_root_label = DATASET_VARIABLE_ROOT_LABEL

    initial_part = f"""
        MATCH (root:{variable_root_label}{{uid: $uid}})
        WITH root
    """

    full_query = initial_part + build_variable_instance_query(
        instance_node_variable_name="value",
        parent_type=parent_type,
        version_data=version_data,
    )

    tx.run(
        full_query,
        uid=variable["uid"],
        effective_date=version_data["effective_date"],
        prefixed_version_number=prefixed_version_number,
        variable_data=variable,
        version_href=version_data["href"],
        parent_href=parent_href,
        author_id=AUTHOR_ID,
    )

    if "value_list" in variable:
        link_variable_with_value_terms(
            tx,
            version_data=version_data,
            variable=variable,
            parent_href=parent_href,
            value_list_mappings=value_list_mappings,
        )


def create_new_variable_instance(
    tx, version_data, variable, parent_href, parent_type, value_list_mappings
):
    prefixed_version_number = _prettify_version_number(version_data["version_number"])
    variable_root_label = ""
    if version_data["data_model_type"] == DataModelType.FOUNDATIONAL.value:
        variable_root_label = VARIABLE_CLASS_ROOT_LABEL
    elif version_data["data_model_type"] == DataModelType.IMPLEMENTATION.value:
        variable_root_label = DATASET_VARIABLE_ROOT_LABEL

    initial_part = f"""
        MATCH (root:{variable_root_label}{{uid: $uid}})
        WITH root
    """

    full_query = initial_part + build_variable_instance_query(
        instance_node_variable_name="new_value",
        parent_type=parent_type,
        version_data=version_data,
    )
    tx.run(
        full_query,
        uid=variable["uid"],
        effective_date=version_data["effective_date"],
        prefixed_version_number=prefixed_version_number,
        variable_data=variable,
        version_href=version_data["href"],
        parent_href=parent_href,
        author_id=AUTHOR_ID,
    )

    if "value_list" in variable:
        link_variable_with_value_terms(
            tx,
            version_data=version_data,
            variable=variable,
            parent_href=parent_href,
            value_list_mappings=value_list_mappings,
        )


def use_existing_variable_instance(
    tx,
    version_data,
    variable,
    parent_href,
    instance_node_id,
    parent_type,
    scenario_impl_node_id=None,
):
    prefixed_version_number = _prettify_version_number(version_data["version_number"])

    initial_part = """
        MATCH (instance)
        WHERE id(instance)=$instance_node_id
    """

    full_query = initial_part + build_variable_instance_query(
        instance_node_variable_name="instance",
        parent_type=parent_type,
        create_version=False,
        version_data=version_data,
    )

    tx.run(
        full_query,
        uid=variable["uid"],
        instance_node_id=instance_node_id,
        scenario_impl_node_id=scenario_impl_node_id,
        effective_date=version_data["effective_date"],
        prefixed_version_number=prefixed_version_number,
        variable_data=variable,
        version_href=version_data["href"],
        parent_href=parent_href,
    )


def link_ig_with_data_model(tx, version_data):
    tx.run(
        """
        MATCH (ig:DataModelIGValue {name:$ig_name})
        MATCH (:DataModelVersion {href:$implements})-[:CONTAINS_DATA_MODEL]->(dm:DataModelValue)
        MERGE (ig)-[:IMPLEMENTS]->(dm)
    """,
        ig_name=version_data["name"],
        implements=version_data["implements_data_model"],
    )


def link_dataset_with_class(tx, _class, prefixed_version_number):
    if "implements_class" in _class:
        tx.run(
            f"""
                MATCH (:DataModelVersion)-[rel:{VERSION_TO_DATASET_REL_TYPE}]->(dataset_instance:DatasetInstance)
                WHERE rel.href=$class_href
                MATCH (:DataModelVersion)-[implemented_rel:{VERSION_TO_CLASS_REL_TYPE}]->(class_instance:DatasetClassInstance)
                WHERE implemented_rel.href=$implements_class_href
                MERGE (dataset_instance)-[:IMPLEMENTS_DATASET_CLASS {{
                    catalogue: $catalogue,
                    version_number: $prefixed_version_number
                }}]->(class_instance)
            """,
            class_href=_class["href"],
            implements_class_href=_class["implements_class"],
            catalogue=_class["catalogue"],
            prefixed_version_number=prefixed_version_number,
        )


def link_class_with_subclasses(tx, _class, subclasses, prefixed_version_number):
    tx.run(
        f"""
            UNWIND $subclasses AS subclass_href
            MATCH (:DataModelVersion)-[rel]->(class_value)
            WHERE rel.href=$class_href AND type(rel) IN ["{VERSION_TO_CLASS_REL_TYPE}", "{VERSION_TO_DATASET_REL_TYPE}"]
            MATCH (:DataModelVersion)-[rel_sub:{VERSION_TO_CLASS_REL_TYPE}]->(subclass_value)
            WHERE rel_sub.href=subclass_href AND type(rel_sub) IN ["{VERSION_TO_CLASS_REL_TYPE}", "{VERSION_TO_DATASET_REL_TYPE}"]
            MERGE (class_value)<-[:HAS_PARENT_CLASS {{
                catalogue: $catalogue,
                version_number: $prefixed_version_number
            }}]-(subclass_value)
        """,
        class_href=_class["href"],
        subclasses=subclasses,
        catalogue=_class["catalogue"],
        prefixed_version_number=prefixed_version_number,
    )


def link_variables_with_variables(tx, version_data, variables_data):
    prefixed_version_number = _prettify_version_number(version_data["version_number"])
    for variable_data in variables_data:
        variable = variable_data.get("variable", None)
        if variable:
            link_variable_with_variable(
                tx, version_data, variable, prefixed_version_number
            )


def link_variable_with_variable(tx, version_data, variable, prefixed_version_number):
    match = f"""
        UNWIND $classes_href AS class_href
        MATCH ()-[rel]->(target_variable_value)
        WHERE rel.href=class_href AND (rel:{VERSION_TO_VARIABLE_CLASS_REL_TYPE} OR rel:{VERSION_TO_DATASET_VARIABLE_REL_TYPE})
        MATCH (n {{uid: $uid}})-->(source_variable_value)<--(source_dmv:DataModelVersion {{name: $source_version}})
        WHERE n:DatasetVariable OR n:VariableClass
    """

    common_params = {
        "uid": variable["uid"],
        "source_version": version_data["name"],
        "prefixed_version_number": prefixed_version_number,
    }

    if "implements_variables" in variable and len(variable["implements_variables"]) > 0:
        tx.run(
            f"""
                {match}
                MERGE (source_variable_value)-[:IMPLEMENTS_VARIABLE{{
                    catalogue: $catalogue,
                    version_number: $prefixed_version_number
                }}]->(target_variable_value)
            """,
            classes_href=variable["implements_variables"],
            catalogue=variable["catalogue"],
            **common_params,
        )

    if "mapping_targets" in variable and len(variable["mapping_targets"]) > 0:
        tx.run(
            f"""
                {match}
                MERGE (source_variable_value)-[:HAS_MAPPING_TARGET{{
                    version_number: $prefixed_version_number
                }}]->(target_variable_value)
            """,
            classes_href=variable["mapping_targets"],
            **common_params,
        )


def terms_name_codelist_mapping(tx, term_name):
    # This query gets all Terms with code_submission_value = _value
    # It also gets the codelists these belong to
    # And it only returns the most recent version of a term for each codelist
    terms_data = tx.run(
        """
        MATCH (codelist_value:CTCodelistAttributesValue)<-[:LATEST]-(:CTCodelistAttributesRoot)<--(codelist_root:CTCodelistRoot)
            -->(ct:CTCodelistTerm)-->(term_root:CTTermRoot)-->(:CTTermAttributesRoot)-[version_rel:HAS_VERSION]->(term:CTTermAttributesValue)
        WHERE ct.submission_value=$code_submission_value
        WITH codelist_root, codelist_value, version_rel, term_root
        ORDER BY codelist_root.uid, version_rel.start_date DESC
        WITH codelist_root, codelist_value, collect(term_root)[0] AS term_root
        RETURN DISTINCT term_root.uid AS term_uid, collect(DISTINCT {uid:codelist_root.uid, submission_value: codelist_value.submission_value}) AS codelists
    """,
        code_submission_value=term_name,
    ).data()

    return terms_data


def link_variable_with_value_terms(
    tx,
    version_data: dict,
    variable: dict,
    parent_href: str,
    value_list_mappings: "dict[str, ValueListMapping]",
):
    previous_codelist_uid = None
    match_variable_clause = f"""
        MATCH (dmv:DataModelVersion)-[rel:{VERSION_TO_DATASET_VARIABLE_REL_TYPE}]->(variable_instance:DatasetVariableInstance)
        WHERE rel.href=$variable_href
    """
    create_relationship_clause = """
        CREATE (term)<-[:HAS_SELECTED_TERM]-(ctx:CTTermContext)-[:HAS_SELECTED_CODELIST]->(cl)
        CREATE (variable_instance)-[:REFERENCES_TERM]->(ctx)
    """
    for _value in variable["value_list"]:
        terms_data = terms_name_codelist_mapping(tx, _value)

        # If there is only one CCode in a single codelist
        # Then link the variable with it
        if len(terms_data) == 1 and len(terms_data[0]["codelists"]) == 1:
            match_term_and_codelist = """
                MATCH (term: CTTermRoot {uid: $term_uid})
                MATCH (cl:CTCodelistRoot {uid: $codelist_uid})
            """
            query = " ".join(
                [
                    match_variable_clause,
                    match_term_and_codelist,
                    create_relationship_clause,
                ]
            )
            tx.run(
                query,
                term_uid=terms_data[0]["term_uid"],
                codelist_uid=terms_data[0]["codelists"][0]["uid"],
                variable_href=variable["href"],
            )
            # Store the codelist name in the list for the next case
            if previous_codelist_uid is None:
                previous_codelist_uid = terms_data[0]["codelists"][0]["uid"]

        # Else, if other elements in the value_list had a single match, then use the term coming from the same codelist
        else:
            if previous_codelist_uid is not None:
                # Hardcoding based on past data knowledge
                if _value == "U":
                    _value = "UNKNOWN"

                    # Re-run the terms query for the replacement
                    terms_data = terms_name_codelist_mapping(tx, _value)

                # Link variable with terms
                # Find the term which belongs to the same codelist as the previous hit
                # For example, UNKNOWN in the STENRF codelist for the --STRTPT variables
                term_uid = next(
                    (
                        term_data["term_uid"]
                        for term_data in terms_data
                        if previous_codelist_uid
                        in [codelist["uid"] for codelist in term_data["codelists"]]
                    ),
                    None,
                )

                if term_uid is not None:
                    match_term_and_codelist = "MATCH (term: CTTermRoot {uid: $term_uid})<--(:CTCodelistTerm)<--(cl:CTCodelistRoot{uid: $codelist_uid})"
                    query = " ".join(
                        [
                            match_variable_clause,
                            match_term_and_codelist,
                            create_relationship_clause,
                        ]
                    )
                    tx.run(
                        query,
                        variable_href=variable["href"],
                        term_uid=term_uid,
                        codelist_uid=previous_codelist_uid,
                    )

                    # Relationship created, go to next value in value_list
                    continue

            # If we reach here, it means there was more than one match for the value (or none)
            # It also means the script could not figure out a codelist from other values in the value_list (if any)
            # So, if one of the terms is in a codelist which submission_value is the same name as the variable uid, then use that term
            if len(terms_data) > 0 and (
                any(
                    [
                        variable["name"]
                        in [
                            codelist["submission_value"]
                            for codelist in term_data["codelists"]
                        ]
                        for term_data in terms_data
                    ]
                )
                or (
                    variable["name"] == "DOMAIN"
                    and any(
                        [
                            "SDOMAIN"
                            in [
                                codelist["submission_value"]
                                for codelist in term_data["codelists"]
                            ]
                            for term_data in terms_data
                        ]
                    )
                )
            ):
                term_uid = next(
                    (
                        term_data["term_uid"]
                        for term_data in terms_data
                        if variable["name"]
                        in [
                            codelist["submission_value"]
                            for codelist in term_data["codelists"]
                        ]
                    ),
                    None,
                )

                if term_uid is None and variable["name"] == "DOMAIN":
                    term_uid = next(
                        (
                            term_data["term_uid"]
                            for term_data in terms_data
                            if "SDOMAIN"
                            in [
                                codelist["submission_value"]
                                for codelist in term_data["codelists"]
                            ]
                        ),
                        None,
                    )

                match_term_and_codelist = "MATCH (term: CTTermRoot {uid: $term_uid})"
                query = " ".join(
                    [
                        match_variable_clause,
                        match_term_and_codelist,
                        create_relationship_clause,
                    ]
                )
                tx.run(
                    query,
                    term_uid=term_uid,
                    variable_href=variable["href"],
                )

            elif value_list_mappings:
                # Finally, search the value list mappings coming from the file  for a match
                value_list_mapping = value_list_mappings.get(
                    f"{version_data['name']}_{parent_href.split('/')[-1]}_{variable['uid']}_{_value}",
                    None,
                )

                if value_list_mapping is not None:
                    # Create the relationship between DatasetVariable and CTTerm corresponding to the value
                    match_term_and_codelist = "MATCH (term: CTTermRoot {uid: $term_uid})<--(:CTCodelistTerm)<--(cl:CTCodelistRoot{uid: $codelist_uid})"
                    query = " ".join(
                        [
                            match_variable_clause,
                            match_term_and_codelist,
                            create_relationship_clause,
                        ]
                    )
                    tx.run(
                        query,
                        variable_href=variable["href"],
                        term_uid=value_list_mapping.term_uid,
                        codelist_uid=value_list_mapping.codelist_uid,
                    )


def create_qualify_variable_relationships(tx, source_variable, prefixed_version_number):
    tx.run(
        f"""
            UNWIND $targets_href AS target_href
            MATCH ()-[source_rel:{VERSION_TO_VARIABLE_CLASS_REL_TYPE}]->(source_variable_value)
            WHERE source_rel.href=$source_href
            MATCH ()-[target_rel:{VERSION_TO_VARIABLE_CLASS_REL_TYPE}]->(target_variable_value)
            WHERE target_rel.href=target_href
                MERGE (source_variable_value)-[:QUALIFIES_VARIABLE{{
                    catalogue: $catalogue,
                    version_number: $prefixed_version_number
                }}]->(target_variable_value)
        """,
        source_href=source_variable["href"],
        targets_href=source_variable["qualifies_variables"],
        catalogue=source_variable["catalogue"],
        prefixed_version_number=prefixed_version_number,
    )


def _prettify_version_number(version_number: str, number_only=False):
    """
    Format a version number string to a standardized format.

    Args:
        version_number (str): The version number to format
        number_only (bool, optional): If True, extracts only the numeric parts of the version.
            For major.minor format, returns the last 2 parts.
            For major.minor.patch format, returns the last 3 parts.
            Defaults to False.

    Returns:
        str: The formatted version number string
    """
    version = version_number.replace("-", ".")
    if number_only:
        parts = version.split(".")
        nbr_parts = 2
        if len(parts) > 2 and parts[-3].isnumeric():
            # the version is major.minor.patch
            nbr_parts = 3
        version = ".".join(parts[-nbr_parts:])
    return version
