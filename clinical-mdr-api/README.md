# Overview

This repository contains an API providing read/write access to Clinical MDR (Clinical Metadata Repository) stored in a neo4j database.


# Technology stack
* Python with [FastAPI](https://fastapi.tiangolo.com/)
* [Neo4j](https://neo4j.com/) database


# Development Environment Setup

## Setup python virtual environment

* Make sure Python 3.11 is installed on your machine.
* Install a recent [Pipenv](https://pipenv.pypa.io/en/latest/) version, e.g. 2023.3.20 or later.
* Run `pipenv sync --dev` from root folder to install the required python libraries.

## Setup environment variables
Copy `.env.example` and name it `.env` and update the variables as needed.

Notes:
- Update the value of `UID` to your actual user id reported by `id` command.
- `NEO4J_DSN` variable needs to be in alignment with the actual environment variables used when starting the target neo4j database, e.g.

  ```
  NEO4J_MDR_BOLT_PORT=7687
  NEO4J_MDR_HOST=localhost
  NEO4J_MDR_AUTH_USER=neo4j
  NEO4J_MDR_AUTH_PASSWORD=test1234
  ```
- To enable authentication, update the following variables according to your auth configuration (the values below are random-generated examples).
  ```shell
  OAUTH_ENABLED=True
  OAUTH_METADATA_URL='https://login.microsoftonline.com/bd70d9d2-5ba8-4bb8-8ca5-55fdaf0c76d1/v2.0/.well-known/openid-configuration?appid=0b4bb293-433f-44d3-b992-8c95ad1665b9'
  OAUTH_API_APP_ID='0b4bb293-433f-44d3-b992-8c95ad1665b9'
  
  # required for MS Graph API integration only, which will be used by a future feature #
  OAUTH_API_APP_SECRET='21u9UAnFKXUCYt6yxqRA7xAQ'
  MS_GRAPH_INTEGRATION_ENABLED=true
  # optional, for MS Graph API integration: filter expression for group discovery  #
  MS_GRAPH_GROUPS_QUERY="$filter=startsWith(displayName, 'StudyBuilder')"
  
  # required for the FastAPI-built-in Swagger UI only #
  OAUTH_SWAGGER_APP_ID='db8a95f6-a638-4535-bb1d-4a131748165a'
  ```

- For integration with Azure Monitoring / Application Insights (logs, tracing, correlation) update these variables:
  ```shell
  APPLICATIONINSIGHTS_CONNECTION_STRING='InstrumentationKey=00000000-0000-0000-0000-000000000000'
  UVICORN_LOG_CONFIG='logging-azure.yaml'
  ```

- The application uses a tracing middleware to log useful information for each request.
  If this is not desired, set `TRACING_DISABLED` variable to `false`:
  ```shell
  TRACING_DISABLED=false
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
- `pipenv run testunit` - Runs all tests defined in the `clinical_mdr_api/tests/unit` folder and generates test and coverage reports
- `pipenv run testint` - Runs all tests defined in the `clinical_mdr_api/tests/integration` folder and generates test and coverage reports
- `pipenv run testauth` - Runs all tests defined in the `clinical_mdr_api/tests/oauth` folder and generates test and coverage reports
- `pipenv run test-telemetry` - Runs all tests defined in the `clinical_mdr_api/tests/telemetry` folder and generates test and coverage reports
- `pipenv run test` - Runs all tests defined in the `clinical_mdr_api/tests` folder
- `pipenv run lint` - Performs static code analysis using [Pylint](https://pylint.pycqa.org/en/latest/)
- `pipenv run openapi` - Generates API specification in the [OpenAPI](https://swagger.io/specification/) format and stores it in `openapi.json` file
- `pipenv run schemathesis` - Checks API implementation against the specification defined in `openapi.json` file using the [schemathesis](https://schemathesis.readthedocs.io/en/stable/) tool

## Running tests
- Running unit/integration tests requires a neo4j database. We recommend using the docker image provided by the `neo4j-mdr-db` repository to start the database locally.

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

1. Validation errors detected and reported by the Pydantic library (an underlying component of FastAPI), resulting in HTTP response status `422`. Pydantic will perform validation of query/path/body fields based on the validation rules we specify for each of these fields, instead of us raising explicit exceptions in our code.
   - Example guides on how to use Pydantic validation of query/path/body fields:
     - https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
     - https://fastapi.tiangolo.com/tutorial/path-params-numeric-validations/
     - https://fastapi.tiangolo.com/tutorial/body-fields/
   - Example response when required fields in the POST payload are not supplied:

      ```
      {
        "detail": [
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

1. Validation errors raised by our code when our business rules or additional validation constraints (not handled by Pydantic) are unmet, resulting in HTTP response status `400`.
   - Example response when API consumer tries to create an entity with the same name as the name of an already existing entity of same type:
      ```
      {
        "type": "ValidationException",
        "message": "Library 'SNOMED' already exists",
        "time": "2023-05-16T07:33:40.888526",
        "path": "http://localhost:8000/libraries",
        "method": "POST"
      }
      ``` 

1. "Not found" errors raised by our code when a referenced entity does not exist, resulting in HTTP response status `404`. 
   - Example response:
      ```
      {
        "type": "NotFoundException",
        "message": "CompoundAR with uid XYZ does not exist or there's no version with requested status or version number.",
        "time": "2023-05-16T07:34:43.330141",
        "path": "http://localhost:8000/concepts/compounds/XYZ",
        "method": "GET"
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


All exceptions raised explicitly in our code and their corresponding  HTTP response statuses are defined [here](clinical_mdr_api/exceptions/__init__.py). 
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



