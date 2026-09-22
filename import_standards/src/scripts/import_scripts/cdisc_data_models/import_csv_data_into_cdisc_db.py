import time, traceback, csv
from os import path, environ
from src.scripts.entities.cdisc_data_models.data_model_import import (
    DataModelImport,
    DataModelType,
)
from src.scripts.entities.cdisc_data_models.version import Version


from src.scripts.repositories.repository import (
    await_indexes,
    create_indexes_if_not_existent,
    create_data_model_import_node,
    create_data_model_import,
)
from src.scripts.exceptions.version_exists import VersionExists
from src.scripts.utils import (
    get_classes_csv_filename,
    get_variables_csv_filename,
)

NEO4J_MDR_DATABASE = environ.get("NEO4J_MDR_DATABASE", "neo4j")


def print_summary(tx, import_id, start_time):
    result = tx.run(
        """
        MATCH (import:DataModelImport) WHERE id(import) = $import_id
        RETURN
            import.catalogue as catalogue,
            import.version_number as version_number,
            import.data_model_type as data_model_type
        """,
        import_id=import_id,
    ).single()

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"==")
    print(f"== Summary for the import into the CDISC DB:")
    print(f"==")
    print(f"==      catalogue: {result.get('catalogue', 'n/a')}")
    print(f"==      version number: {result.get('version_number', 'n/a')}")
    print(f"==      type: {result.get('data_model_type', 'n/a')}")
    print(f"==")
    print(f"== Duration: {round(elapsed_time, 1)} seconds")


def finish_import(tx, import_id):
    tx.run(
        """
        MATCH (import:DataModelImport) WHERE id(import) = $import_id
        REMOVE import:Running
        """,
        import_id=import_id,
    ).single()


def process_model(
    data_directory: str,
    filename: str,
    dm_import: DataModelImport,
    data_model_type: DataModelType,
    catalogue: str,
    version_number: str,
    ig_catalogue: str = None,
):
    print(f"==  * Processing file: '{filename}'.")
    with open(filename, "r") as version_file:
        class_reader = csv.DictReader(version_file)
        version_csv_data = next(class_reader)
        version_csv_data["href"] = (
            f"/mdr/{ig_catalogue.lower() if ig_catalogue else catalogue.lower()}/{version_number}"
        )
        version_csv_data["source"] = "Sponsor Lab Data Specifications"
        version = Version(dm_import, version_number=version_number)
        version.load_from_csv_data(
            catalogue=catalogue,
            version_csv_data=version_csv_data,
            data_model_type=data_model_type,
        )
        dm_import.set_type(data_model_type)
        dm_import.set_implements_data_model(version.get_implements_data_model())
        dm_import.add_version(version)
        class_filename = get_classes_csv_filename(version.data_model_type)
        class_filepath = path.join(
            data_directory, catalogue, version_number, class_filename
        )
        variable_filename = get_variables_csv_filename(version.data_model_type)
        variable_filepath = path.join(
            data_directory, catalogue, version_number, variable_filename
        )
        if path.exists(class_filepath) and path.exists(variable_filepath):
            with open(class_filepath, "r") as class_file:
                class_reader = csv.DictReader(class_file)
                all_variables = []
                with open(variable_filepath, "r") as variable_file:
                    variable_reader = csv.DictReader(variable_file)
                    all_variables = [row for row in variable_reader]
                for class_csv_data in class_reader:
                    class_suffix = (
                        "classes"
                        if version.data_model_type == DataModelType.FOUNDATIONAL
                        else "datasets"
                    )
                    class_header = (
                        "dataset_class"
                        if version.data_model_type == DataModelType.FOUNDATIONAL
                        else "dataset"
                    )
                    class_csv_data["href"] = "/".join(
                        [
                            "/mdr",
                            ig_catalogue.lower() if ig_catalogue else catalogue.lower(),
                            version_number,
                            class_suffix,
                            class_csv_data["name"],
                        ]
                    )
                    version.load_class_from_csv_data(
                        class_csv_data=class_csv_data,
                        data_model_type=version.data_model_type,
                        catalogue=ig_catalogue if ig_catalogue else catalogue,
                        variables_csv_data=[
                            variable
                            for variable in all_variables
                            if variable[class_header] == class_csv_data["name"]
                        ],
                    )
        else:
            print(
                f"===  * No classes or datasets found for the catalogue='{ig_catalogue if ig_catalogue else catalogue}' in version='{version_number}'."
            )


def import_data_model_csv_data_into_cdisc_db(
    library: str,
    catalogue: str,
    version_number: str,
    data_directory: str,
    cdisc_import_neo4j_driver,
    cdisc_import_db_name: str,
    author_id: str,
):
    """
    Import the new data found on disc into the intermediate CDISC database

    Args:
        catalogue (str): Data Model catalogue name
        version (str): version number
        data_directory (str): the path of the directory in which the JSON files reside;
        if this is relative, it needs to be relative to the location of this script
        cdisc_import_neo4j_driver : the Neo4j driver instance that is used in order to connect to the Neo4j DBMS
        that holds the cdisc-import database (cf. cdisc_import_db_name);
        https://neo4j.com/docs/api/python-driver/current/api.html#neo4j.Driver
        cdisc_import_db_name (str): the name of the Neo4j database in which the CDISC data is loaded
        in the first place (after it will be loaded into the default MDR db)
        author_id (str): the id of the user that triggers this step
    """
    try:
        start_time = time.time()

        # If using a staging database, it might not exist yet
        # so we need to create it first
        if cdisc_import_db_name != NEO4J_MDR_DATABASE:
            with cdisc_import_neo4j_driver.session(database="system") as session:
                session.run(
                    "CREATE DATABASE $database IF NOT EXISTS",
                    database=cdisc_import_db_name,
                )

        with cdisc_import_neo4j_driver.session(
            database=cdisc_import_db_name
        ) as session:
            session.write_transaction(create_indexes_if_not_existent)
            session.write_transaction(await_indexes)

            dm_import = DataModelImport(
                library=library,
                catalogue=catalogue,
                version_number=version_number,
                author_id=author_id,
            )
            process_model(
                data_directory=data_directory,
                filename=path.join(
                    data_directory, catalogue, version_number, "data_model.csv"
                ),
                dm_import=dm_import,
                data_model_type=DataModelType.FOUNDATIONAL,
                catalogue=catalogue,
                version_number=version_number,
            )
            if "-" in catalogue:
                ig_catalogue_name = f"{catalogue}-IG"
            else:
                ig_catalogue_name = f"{catalogue}IG"
            dm_import_ig = DataModelImport(
                library=library,
                catalogue=ig_catalogue_name,
                version_number=version_number,
                author_id=author_id,
            )
            process_model(
                data_directory=data_directory,
                filename=path.join(
                    data_directory, catalogue, version_number, "data_modelIG.csv"
                ),
                dm_import=dm_import_ig,
                data_model_type=DataModelType.IMPLEMENTATION,
                catalogue=catalogue,
                ig_catalogue=ig_catalogue_name,
                version_number=version_number,
            )

            import_id = session.write_transaction(
                create_data_model_import_node, dm_import
            )
            create_data_model_import(dm_import, session)

            with session.begin_transaction() as tx:
                finish_import(tx, import_id)
                print_summary(tx, import_id, start_time)
                tx.commit()

            start_time_ig = time.time()
            import_id_ig = session.write_transaction(
                create_data_model_import_node, dm_import_ig
            )
            create_data_model_import(dm_import_ig, session)

            with session.begin_transaction() as tx:
                finish_import(tx, import_id_ig)
                print_summary(tx, import_id_ig, start_time_ig)
                tx.commit()

            session.close()

    except VersionExists:
        print(
            f"== The `DataModelImport` node already exists. Skipping the import for the catalogue='{catalogue}' in version='{version_number}'."
        )
    except Exception as e:
        print(f"== Exception:")
        traceback.print_exception(type(e), e, e.__traceback__)
        print(
            f"== Aborting the import for the catalogue='{catalogue}' in version='{version_number}'."
        )
    finally:
        print(f"============================================")
