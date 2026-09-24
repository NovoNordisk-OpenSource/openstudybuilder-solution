# Introduction 
Simple load testing tool for the OpenStudyBuilder API, based on [Locust](https://locust.io).

# Getting Started

## Installation

Python 3.14 and Pipenv are prerequisites — see the
[root README](../README.md#prerequisites).

```sh
pipenv sync --dev
```

# Execution
1. Run `pipenv run load-test-ui` to start [locust web interface](http://localhost:8089/) on your machine. 

   Specify number of users, test duration and other parameters for load tests in this web interface. 

   **OR**

1. Run `pipenv run load-test-cl` to execute load tests in command-line mode.

   Without changing the parameters, this command will run load tests for 1 minute with 10 concurrent users.
   
   Complete list of command-line options that can be specified can be seen [here](https://docs.locust.io/en/stable/running-without-web-ui.html).

## Environment Variables
By default, load tests will target an API instance running on http://localhost:8000 and assume that authentication is turned off.

It is possible to modify the behavior by specifying non-default values for the following environment variables (for example by creating `.env` file in the project root):



```
API_BASE_URL=http://127.0.0.1:8000                 # Base URL of the target API
CONSUMER_API_BASE_URL=http://127.0.0.1:8008        # Base URL of the target Consumer API
DATABASE_URL=bolt://neo4j:<your-neo4j-password>@localhost:7687  # Target database URL (required — no default)
DATABASE_NAME=neo4j                                # Target database name
TARGET_CONSUMER_API=False                          # Set this to True if the target should be the Consumer API
API_AUTH_TOKEN=                                    # Bearer token (JWT) used to authenticate requests to the target API
STUDY_ID=Study_000039                              # Study UID used to test various endpoints
STUDY_NUMBER=3003                                  # Study Number used to test various endpoints
LIBRARY_NAME=SNOMED                                # Name of Library/Dictionary used to test various endpoints
CT_CODELIST_UID=CTCodelist_000001                  # CT CodeList UID used to test various endpoints
CT_TERM_UID=CTTerm_000001                          # CT Term UID used to test various endpoints
PERFORMANCE_THRESHOLD=2000                         # Endpoints whose median response time is bigger than the specified value (in ms) will be marked as test failures
PREFETCH_ENDPOINTS=false                           # If true, the script will prefetch all the endpoints before running the tests
AUTO_DETECT_BIG_STUDY=true                         # If true, the script will target the study with the highest number of activities * visits
```

## Endpoints Under Test
List of all GET endpoints that are being tested is defined in the `tests/endpoints.py` file. 

During load test execution, endpoints are randomly picked from this list, and required path/query parameter values are replaced with values defined by corresponding environment variables.

# Load Test Pipeline
Apart from being able to run load tests from a local machine, there was also a Load Tests pipeline (ADO, retired — to be re-authored as a GitHub Actions workflow) that could execute load tests against a chosen target environment. After running load tests for the specified number of minutes, the pipeline published two types of reports:
- csv reports with detailed performance statistics of tested endpoints (including any potentially failing endpoints) 

- a JUnit xml report giving a short summary of median response times for all tested endpoints. Endpoints slower than the specified `PERFORMANCE_THRESHOLD` value will be marked as failed test cases.