# Introduction
The purpose of migration scripts contained in this repository is to convert existing data stored in SB database from one data model to another.

This is needed when due to SB API and/or underlying data model refactorings, 
the data currently stored in production database becomes incompatible with the latest SB API. In such cases, when releasing a new version of the SB API to production, we need to migrate the affected production data into the new data model, without losing any of the relevant information stored in the production database.


This repo aims to provide means to:
1. ## Insert data conforming to the `old` data model into a database
   - Initial test data for a specific migration should be placed in `tests/data` folder, e.g. `tests/data/db_before_migration_001.py`.
     See [extracting test data](#extracting-test-data) on how to extract the data.
2. ## Migrate this data into the `new` data model
   - Migration script defining the needed data modifications for a specific release to production is stored in the `migrations` folder, e.g. `migrations/migration_001.py`.
   - Human readable overview of the needed changes are also stored in the `migrations` folder, e.g. `migrations/migration_overview_001.md`.
3. ## Verify that the migrated data and the related API endpoints look and behave as expected
   - Test scripts for verifying each specific migration are located in the `tests` folder, e.g. `tests/test_migration_001.py`.
   - Note that migration-identifying suffix (e.g. `001`) on each of the files performing/testing/describing a migration should be the same.


# Getting Started

## Installation
`pipenv install --dev`

## Available Actions
- `pipenv run migrate`
   - Performs data migration on the database defined by `DATABASE_URL` and `DATABASE_NAME` environment params.
   - Requires a running SB API, and a database with a complete dataset.
   - After finishing, the result can be verified with the `verify` action.

- `pipenv run verify`
   - Verifies that database nodes/relations and API endpoints look and behave as expected. No changes are made to the data.
   - Requires a running SB API and database.

- `pipenv run test`
   - Tests a specific migration script: inserts test data, runs the migration script, then verifies the migrated data.
   - Requires a running SB API and database.
   - The database will be cleared and then populated with all necessary data.
   - Note that the database is only cleared if it contains a small number of nodes. This is meant to prevent accidentally clearing a "real" database.

- `pipenv run format`
   - Formats code with black and isort.

- `pipenv run lint`
   - Lints code with pylint.


## Environment Variables
Migration and test/verify scripts are dependent on the following environment variables:
```
DATABASE_URL
DATABASE_NAME
API_BASE_URL
API_AUTH_TOKEN
CREATE_DB
```

Crete an `.env` file in project root locally, for example:
```
DATABASE_URL=bolt://neo4j:test1234@localhost:7687
DATABASE_NAME=schema.migration.test
API_BASE_URL=http://localhost:8000
API_AUTH_TOKEN=
CREATE_DB=true

MDR_MIGRATION_ACTIVE_SUBSTANCES=migration_data/datafiles/compounds/active_substances.json
MDR_MIGRATION_PHARMACEUTICAL_PRODUCTS=migration_data/datafiles/compounds/pharmaceutical_products.json
MDR_MIGRATION_MEDICINAL_PRODUCTS=migration_data/datafiles/compounds/medicinal_products.json
MDR_MIGRATION_COMPOUNDS=migration_data/datafiles/compounds/compounds.json
```


## Dependencies
- For the purpose of verifying SB API endpoints after a migration is performed,
test script assumes that it can reach SB API that operates on the same database
as the test script. 

  This is achieved by setting the API environment variables `NEO4J_DSN` / `NEO4J_DATABASE` to the same values as corresponding `DATABASE_URL` / `DATABASE_NAME` environment variables for the migration script, e.g.
  ```
  NEO4J_DSN=bolt://neo4j:test1234@localhost:7687
  NEO4J_DATABASE=schema.migration.test
  ```

# Data corrections
TODO move higher up!

This repository also contains data corrections, that correct errors and mistakes in the StudyBuilder database.

The code is structired similar to the migrations:
- `data_corrections/correction_NNN.py`: the code performing the corrections.
- `verifications/correction_verification_NNN.py`: verification that the correction was applied sucessfully.
- `tests/test_correction_NNN.py`: tests used for both testing and verification.
- `tests/data/db_before_correction_NNN.py`: data used by tests.

## Corrections

Each correction is performed by one or several functions defined in `data_corrections/correction_NNN.py`.

The file itself must have a module docstring, at the very top. It also needs a variable `CORRECTION_DESC` defined like in this example:
```python
""" PRD Data Corrections, for release 1.5"""

CORRECTION_DESC = "data-correction-release-1.5"
```

The functions must follow this pattern:
```python
@capture_changes(docs_only=False, verify_func=correction_verification_NNN.test_example_correction)
def example_correction(db_driver, log, run_label):
    """
    ## Example correction function

    ### Change Description
    This correction adds the missing `is_dummy` property on the `HAS_DUMMY_VALUE` relationship
    between `DummyRoot` and `DummyValue` nodes.

    - [Related PR](https://dev.azure.com/orgremoved/Clinical-MDR/_git/neo4j-mdr-db/pullrequest/123456)

    ### Nodes and relationships affected
    - `HAS_DUMMY_VALUE` between `DummyRoot` and `DummyValue` nodes.
    - Expected changes: 123 relationship properties added.
    """

    desc = "Add missing 'is_dummy' property on 'HAS_DUMMY_VALUE' relationships"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(db_driver,
        """
        MATCH (:DummyRoot)-[hd:HAS_DUMMY_VALUE]-(:DummyValue)
        SET hd.is_dummy = true
        """
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates
```

### Capture changes
If the optional `docs_only` argument is left out or set to `False`,
the `capture_changes` decorator uses [Change Data Capture](https://neo4j.com/docs/cdc/current/)
to record the database changes performed by the function.

The decorator assumes that the first three arguments to the function are as shown.
- `db_driver`: a [neo4j Driver](https://neo4j.com/docs/api/python-driver/current/api.html#neo4j.Driver).
- `log`: a logger instance.
- `run_label`: a string label indentifying the run, used to separate output from different runs.

It also assumes that the function has a docstring, defined at the very top of the function as shown above.

The changes are stored in the subdirectory `correction_change_logs`,
where each function writes a separate file named as `{function_name}.{run_label}.json`.

A summary of all changes is also stored in markdown format, as `summary.{run_label}.md`.

The `verify_func` argument can be used to provide a function that verifies that
the correction was successful.
This must be a function that takes no arguments, and any return value from the function is ignored.
It should use `assert` to verify the result.
The example reuses a function from the verifications.
Any failure is logged in the markdown summary.

#### Functions calling other functions

Example:

```python
@capture_changes(has_subtasks=True)
def example_correction(db_driver, log, run_label):
    """
    ## Correction function calling other functions
    """

    contains_updates = False
    for parameter in ["one", "two", "three"]:
        updated = example_subtask(db_driver, log, run_label, parameter)
        contains_updates = contains_updates or updated
    return contains_updates

@capture_changes(task_level=1)
def example_subtask(db_driver, log, run_label, some_parameter):
    """
    ## Correction function called from another function
    """

    _, summary = run_cypher_query(db_driver,
        f"""
        MATCH (:DummyRoot)-[hd:HAS_DUMMY_VALUE]-(:DummyValue)
        SET hd.{some_parameter} = true
        """
    )
    counters = summary.counters
    return counters.contains_updates
```

Setting the `has_subtasks` argument to true adds some more headings in the markdown file,
to get the logs from the subtasks correctly into the index.

The sub tasks should then have their `task_level` set according to the level they run at.
Multiple levels are supported (functions calling other functions that also call functions etc),
by incrementing the `task_level` for each additional level.


### Function return value
The function should return a boolean indicating if changes were made to the database or not. 
The example uses the counters returned by the Cypher query. This information is used by the tests.

### Logging
The example logs a description and prints a summary table of the change counters.
This is recommended but not required. 

## Tests
The tests are defined in `tests/test_correction_NNN.py`.

Example test:
```python
def test_example_correction(correction):
    LOGGER.info(f"Check for missing is_dummy properties")

    records, summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (root:DummyRoot)-[hd:HAS_DUMMY_VALUE]->(:DummyValue)
        WHERE hd.is_dummy IS NULL
        RETURN root, hd
        """,
    )
    assert len(records) == 0


@pytest.mark.order(after="test_example_correction")
def test_repeat_test_example_correction():
    assert not correction_NNN.example_correction(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )
```

The first test uses the `corrections` fixture, which inserts the test data and runs the corrections.
It asserts that no uncorrected nodes or properties exist.

The second test runs after the first, as defined by the `order` pytest mark.
This test assert that the output of the correction function is `False`,
to check that no changes were performed by a second execution of the correction function.

### Test data
The tests run on data that is set up by `tests/data/db_before_correction_NNN.py`.


## Verification
Verification is performed by `verifications/correction_verification_NNN.py`.

The tests can reuse the verifications, example:
```python
def test_example_correction(correction):
    correction_verification_NNN.test_example_correction()
```

## Publish change logs

The `upload_to_wiki.py` script publishes the Markdown summary
created by a correction run as a wiki page.
The linked json files are first uploaded as attachments.
The links are then updated in the Markdown file, before posting it as a new Wiki page.
The name for the new Wiki page is the `WIKI_PAGE_NAME` env variable followed by the date and time, like "{WIKI_PAGE_NAME} 2024-02-03 12:34".
Use the `WIKI_PATH` to determine where in the wiki the page is created.
The new page is created as a subpage under `WIKI_PATH`.
If the full `WIKI_PATH` path doesn't already exist,
placeholder pages are created to ensure that the summary page can be created.

Set the `PROJECT` and `WIKI_IDENTIFIER` environment variables to tell which Wiki to upload to.

The script can use a
[Personal Access Token](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows)
for running locally.
Store the token in the `WIKI_PERSONAL_ACCESS_TOKEN` environment variable to use this method. 
If given, this token is then used with the "Basic" authentication type.

For running in pipelies, instead give a system token in the `WIKI_API_TOKEN` enviromnent variable.
If given, this token is then used with the "Bearer" authentication type.

Run the script, providing the markdown file as an argument:
```sh
python upload_to_wiki.py correction_change_logs/summary.correction.md
```

# Extracting test data
Test data can be extracted as Cypher statements using `apoc.export.cyper.query()`.

Example, extract a small set of terms with their names and attributes:
```
WITH "MATCH (tr:CTTermRoot)-[hnr:HAS_NAME_ROOT]->(tnr:CTTermNameRoot)-[hnv:HAS_VERSION]->(tnv:CTTermNameValue)
MATCH (tr)-[har:HAS_ATTRIBUTES_ROOT]->(tar:CTTermAttributesRoot)-[hav:HAS_VERSION]->(tav:CTTermAttributesValue)
RETURN * LIMIT 20" as query
CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "updateAll"})
YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
RETURN cypherStatements;
```

Create a file in `test/data` called `db_before_migration_{number}.py`
with a number that matches the migration script you are working on.

Copy the Cypher statements out put by the extract queries into strings.
Then join them together to one string called `TEST_DATA`:

```py
TEST_DATA_CT_TERMS = """
(copied Cypher statements, should end with a semicolon)
"""

TEST_DATA_CT_EXAMPLE1 = """
(another set of copied Cypher statements, also ending with a semicolon)
"""


# Complete test data set
TEST_DATA = "\n".join(
    [
        TEST_DATA_CT_TERMS,
        TEST_DATA_EXAMPLE1,
    ]
)
```

