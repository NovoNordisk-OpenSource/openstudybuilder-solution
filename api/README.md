# Overview

This repository contains the OpenStudyBuilder API providing read/write access to clinical metadata stored in a neo4j database.


# Technology stack
* Python with [FastAPI](https://fastapi.tiangolo.com/)
* [Neo4j](https://neo4j.com/) database


# Development Environment Setup

## Setup python virtual environment

Python 3.14 and Pipenv are prerequisites — see the
[root README](../README.md#prerequisites).

Run `pipenv sync --dev` from the `api` directory to install the dependencies.

## Setup environment variables
Copy `.env.example` and name it `.env` and update the variables as needed.

All variables must be in `UPPER_CASE`.

Notes:
- Update the value of `UID` to your actual user id reported by `id` command.
- `NEO4J_DSN` variable needs to be in alignment with the actual environment variables used when starting the target neo4j database, e.g.

  ```
  NEO4J_MDR_BOLT_PORT=7687
  NEO4J_MDR_HOST=localhost
  NEO4J_MDR_AUTH_USER=neo4j
  NEO4J_MDR_AUTH_PASSWORD=<your-neo4j-password>
  ```
- To enable authentication, update the following variables according to your auth configuration. The placeholders below are obvious test values — replace `<...>` with the real tenant ID, app IDs, and client secret from your Azure AD app registration.
  ```shell
  OAUTH_ENABLED=True
  OAUTH_METADATA_URL='https://login.microsoftonline.com/<tenant-id>/v2.0/.well-known/openid-configuration?appid=<api-app-id>'
  OAUTH_API_APP_ID='<api-app-id>'
  
  # required for MS Graph API integration only, which will be used by a future feature #
  OAUTH_API_APP_SECRET='<api-app-client-secret>'
  MS_GRAPH_INTEGRATION_ENABLED=true
  # optional, for MS Graph API integration: filter expression for group discovery  #
  MS_GRAPH_GROUPS_QUERY="$filter=startsWith(displayName, 'OpenStudyBuilder')"
  
  # required for the FastAPI-built-in Swagger UI only #
  OAUTH_SWAGGER_APP_ID='<swagger-app-id>'
  ```

- For integration with Azure Monitoring / Application Insights (logs, tracing, correlation) update these variables:
  ```shell
  APPLICATIONINSIGHTS_CONNECTION_STRING='InstrumentationKey=00000000-0000-0000-0000-000000000000'
  UVICORN_LOG_CONFIG='logging-azure.yaml'
  TRACING_ENABLED=true
  ```


## Launch API locally

Start the API locally by running:

```bash
$ pipenv run dev
```


## Verify the API is running
If the setup is correctly done, the API should be available at:

- http://localhost:8000/

and the API specification in the form of SwaggerUI at:

- http://localhost:8000/docs/

## Additional information

You might want to use a start script like this:

```sh
#!/usr/bin/env bash
pipenv sync
pipenv run dev
```

All in all, you should be able to start the API by performing these steps:
* Start docker service by running `sudo service start docker`
* Start database container by running `docker start neo4j_local`
* Install Python virtual environment by running `pipenv sync`
* Start the API by running `pipenv run dev`



## Useful shortcuts (i.e. scripts defined in Pipfile)
- `pipenv run format` - Formats all Python code using [Black](https://black.readthedocs.io/en/stable/) and [isort](https://pycqa.github.io/isort/)
- `pipenv run testunit` - Runs all tests defined in `clinical_mdr_api/tests/unit/` and `common/tests/unit/` and generates test and coverage reports
- `pipenv run testint` - Runs all tests defined in the `clinical_mdr_api/tests/integration` folder and generates test and coverage reports
- `pipenv run testauth` - Runs the authentication tests in `clinical_mdr_api/tests/auth/`, `common/tests/auth/` and `extensions/tests/auth/`.
- `pipenv run test-telemetry` - Runs all tests defined in the `clinical_mdr_api/tests/telemetry` folder and generates test and coverage reports
- `pipenv run test` - Runs all tests (no path filter)
- `pipenv run mypy` - Performs type checking [mypy](https://mypy.readthedocs.io/)
- `pipenv run sblint` - Performs static code analysis using [SBLint](./sblint)
- `pipenv run lint` - Performs static code analysis using [Pylint](https://pylint.pycqa.org/en/latest/)
- `pipenv run openapi` - Generates API specification in the [OpenAPI](https://swagger.io/specification/) format and stores it in `openapi.json` file
- `pipenv run neomodel-schema` - Generates a single-file snapshot of the neomodel schema (nodes, properties, relationships) used for drift detection
- `pipenv run schemathesis` - Checks API implementation against the specification defined in `openapi.json` file using the [schemathesis](https://schemathesis.readthedocs.io/en/stable/) tool

## Neomodel schema snapshot

To generate a local snapshot for comparison/testing, run:

```bash
pipenv run neomodel-schema -o neomodel_schema.generated.json
```

This creates one file containing the current neomodel schema structure.
In CI, this schema functionality follows the OpenAPI-style behavior: when drift is detected, `neomodel_schema.json` is updated and auto-committed by the pipeline.

## Running tests
- Running unit/integration tests requires a Neo4j database. Start one with the
  scripts in [`db/`](../db/README.md), or see the
  [root README](../README.md#start-the-neo4j-database).

- If you want to execute only a subset of tests instead of using shortcuts defined above, you can run:
  ```bash
  $ pipenv run pytest {test file path}::{test class}::{test method}
  ```
  Below is an example:
  ```bash
  $ pipenv run pytest clinical_mdr_api/tests/integration/services/test_listing_study_design.py::TestStudyListing::test_registry_identifiers_listing
  ```

## Running Schemathesis checks
- Set the following environment variables in `.env` file
  ```
  SCHEMATHESIS_STUDY_UID=Study_000006
  SCHEMATHESIS_HOOKS=clinical_mdr_api.hooks.schemathesis_hooks
  ```

- Run `pipenv run schemathesis` (to test the main API) or `pipenv run consumer-api-schemathesis` (to test the Consumer API). 

- To run schemathesis checks on a subset of endpoints and/or http methods, 
you can specify parameters for the desired http methods (`--include-method`) and/or endpoint paths (`--include-path-regex`).

  For example, this will only test `POST` endpoints `OR` endpoints whose path starts with `/concepts/numeric-values-with-unit`:

  ```
  pipenv run schemathesis --include-method POST --include-path-regex ^/concepts/numeric-values-with-unit
  ```

## Authentication setup

See [doc/Auth.md](doc/Auth.md)



# REST API Guidelines
In general, we are following [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/).

## HTTP Methods

This is the default usage of the HTTP Methods:

| Method     | Usage                                                                                                                                                                                         | Success Response Code |
|------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------| 
| **GET**    | **Get existing** - Returns a single entity or a list of entities. This is read only.                                                                                                          | 200 - OK              |
| **POST**   | **Create new** - Creates a new entity or multiple new entities. This is non-idempotent. Responses can be cached.                                                                              | 201 - Created         |
| **PUT**    | **Overwrite entirely** - Overwrites an existing or multiple existing entities entirely. Does not create a new entity (use POST in this case). This is idempotent. Responses cannot be cached. | 200 - OK              |
| **PATCH**  | **Update partially** - Updates some part of an existing entity or multiple existing entities.                                                                                                 | 200 - OK              |
| **DELETE** | **Delete existing** - Deletes an existing or multiple existing entities.                                                                                                                      | 204 - No Content      |

E.g.:

| Resource     | GET - read                                      | POST - create             | PUT - overwrite                                                         | PATCH - Update partially                                                                 | DELETE - delete                        |
|--------------|-------------------------------------------------|---------------------------|-------------------------------------------------------------------------|------------------------------------------------------------------------------------------|----------------------------------------|
| /studies     | Returns a list of study objects.                | Creates a new study.      | Bulk update of studies where each study will be completely overwritten. | Bulk update of studies where each study will only modified with the provided parameters. | Deletes all studies.                   |
| /studies/xyz | Returns the specific study identified by 'xyz'. | Method not allowed (405). | Overwrites the entire study identified by 'xyz'.                        | Updates only the specified parts of the study identified by 'xyz'                        | Deletes the study identified by 'xyz'. |

## API Conventions

### Paths
- We use only nouns in URLs (preferably in plural form). The API describes resources, so the only place where actions should appear is in the HTTP methods.
- Endpoints names should be specified in `kebab-case` (lowercase). 
- We avoid deep nesting of the endpoints if possible.
- We minimize the number of root endpoints.
- Every endpoint must contain a description string describing its functionality.
- Endpoint parameters (path/query/body fields) should be explicitly typed.
- We avoid PUT requests if possible.
- We have a unified method of pagination for query results. 

E.g.
- GET `/concepts/unit-definitions`
- GET `/studies/{study_uid}/study-disease-milestones/{study_disease_milestone_uid}`


### Query Parameters
- Parameter names and variables should be specified in `snake_case`. 
- Parameter abbreviations like `UID` should contain a prefix of the referenced entity type, e.g. `study_uid`.
- Each parameter should explicitly state whether it is `required`, `optional` and/or `nullable`.

E.g.
- GET  /studies?**page_number**=1&**page_size**=10


### Body (JSON payloads)
- Fields should be specified in `snake_case`. 
- Each field should explicitly state whether it is `required`, `optional` and/or `nullable`.


## Error Handling
During processing of http requests, different types errors may be detected and reported to consumers. 
Broadly speaking, they fall into the following categories:

1. Validation errors raised by pydantic or our code when our business rules or additional validation constraints are unmet, resulting in HTTP response status `400`.
   - Example response when API consumer tries to create an entity with the same name as the name of an already existing entity of same type:
      ```
      {
        "time": "2023-05-16T07:33:40.888526",
        "path": "http://localhost:8000/libraries",
        "method": "POST"
        "type": "ValidationException",
        "message": "Request failed due to validation errors",
        "errors": [
          {
            "loc": [
              "body",
              "name"
            ],
            "msg": "field required",
            "type": "value_error.missing"
          },
          {
            "loc": [
              "body",
              "activity_item_class_uid"
            ],
            "msg": "field required",
            "type": "value_error.missing"
          },
          {
            "loc": [
              "body",
              "library_name"
            ],
            "msg": "field required",
            "type": "value_error.missing"
          }
        ]
      }
      ``` 

1. "Not found" errors raised by our code when a referenced entity does not exist, resulting in HTTP response status `404`. 
   - Example response:
      ```
      {
        "time": "2023-05-16T07:34:43.330141",
        "path": "http://localhost:8000/concepts/compounds/XYZ",
        "method": "GET"
        "type": "NotFoundException",
        "message": "CompoundAR with uid XYZ does not exist or there's no version with requested status or version number.",
      }
      ``` 


1. Authentication/Authorization errors
   - Example 1: `Bearer` token not supplied in the `Authorization` header, resulting in response status `401` 
       ```
      // Example to be added later
      ```   
   - Example 2: The supplied `Bearer` token does not contain the required permissions for the requested endpoint, resulting in response status `403`

      ```
      // Example to be added later
      ```   


All exceptions raised explicitly in our code and their corresponding HTTP response statuses are defined [here](common/exceptions.py). 
No other exceptions should ever be raised by our code.




# Code Style

- We should follow the rules mentioned here: https://pep8.org. 
- All code must be formatted using [Black](https://black.readthedocs.io/en/stable/) and [isort](https://pycqa.github.io/isort/) tools (run `pipenv run format` to auto-format all code).
- All code must pass [Pylint](https://pylint.pycqa.org/en/latest/) static code analysis. Pylint rules which we are globally ignoring are stored in the [pyproject.toml](pyproject.toml) file.


# Source Code Management

We are using the 'Git-flow-Workflow' approach described [here](
https://www.atlassian.com/de/git/tutorials/comparing-workflows/gitflow-workflow).


# Domain Driven Design Approach

See [Domain Driven Design developer's guide](./doc/ddd_developers_guide/ddd-developers-guide.md) for clinical_mdr_api.

