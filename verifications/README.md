# Introduction

The purpose of test scripts contained in this component is to verify that DB and API look and behave as expected.
This is done by:

- Running a set of DB constraints checks on the target database.
- Calling a set of GET endpoints in the SB API and verifying that they all return HTTP status code 200.


A Verification pipeline (ADO, retired — to be re-authored as a GitHub Actions workflow) executed these test scripts against a target environment (DEV/EDU/TST/VAL/PRD).

# Getting Started

## Installation

Python 3.14 and Pipenv are prerequisites — see the
[root README](../README.md#prerequisites).

```sh
pipenv sync --dev
```

## Available Actions

There is **one** test suite. What varies is *which* tests are selected and *which*
report formats are produced. The three run variants differ only by their `-m` tag
filter; each has an `-allure` twin that runs the same selection and additionally
writes Allure result files.

| Script | Tests selected | Reports produced |
|--------|----------------|------------------|
| `pipenv run test` | everything under `tests/` | JUnit XML, Cucumber JSON, coverage |
| `pipenv run test-allure` | everything under `tests/` | the above **+ Allure results** |
| `pipenv run test-only-endpoints` | `impact:api`, `impact:consumer_api`, `impact:api_soa` | JUnit XML, Cucumber JSON, coverage |
| `pipenv run test-only-endpoints-allure` | same as above | the above **+ Allure results** |
| `pipenv run test-only-db` | `impact:data_schema`, `impact:business_rules`, `impact:performance`, `impact:library_quality` | JUnit XML, Cucumber JSON, coverage |
| `pipenv run test-only-db-allure` | same as above, **minus** `impact:library_quality` | the above **+ Allure results** |

Any variant accepts extra pytest arguments, so a narrower selection can be run
ad hoc without a dedicated script:

```sh
pipenv run test -m impact:data_schema
pipenv run test-allure -m "impact:api or impact:api_soa"
```

Non-test actions:

- `pipenv run format` — formats code with black and isort.
- `pipenv run lint` — lints code with pylint.
- `pipenv run token` — fetches an API auth token (`utils.auth`).
- `pipenv run audit` — runs `pip-audit` against the locked dependencies.

## Test Selection Tags

Tests are tagged in the Gherkin feature files under `features/` with `@impact:*`
tags. pytest-bdd turns each Gherkin tag into a pytest marker of the same name, so
any tag can be used as a selector:

```sh
pipenv run test -m impact:business_rules
pipenv run test -m "impact:data_schema or impact:business_rules"
pipenv run test -m "not impact:performance"
```

Each tag states which category the test belongs to and how critical a failure in
it is. `tests/conftest.py` maps the tag onto an Allure **severity**, so the same
tag that selects the test also determines where it lands in the criticality
breakdown of the Allure report — and groups it as an Allure *epic* of the same
name.

| Tag | Category | Allure severity |
|-----|----------|-----------------|
| `impact:data_schema` | Database / schema verification | Critical |
| `impact:business_rules` | Business rule verification | Critical |
| `impact:performance` | Performance-related checks | Normal |
| `impact:api` | API endpoint checks | Normal |
| `impact:consumer_api` | Consumer API checks | Normal |
| `impact:api_soa` | SOA-related API checks | Normal |
| `impact:library_quality` | Library / dictionary content quality | Minor |
| *(untagged)* | — | Minor |

A `@REQ_ID:<id>` tag on a scenario is picked up by the same hook and attached to
the Allure result as a `requirement` label.

Registered markers live in `pyproject.toml` under
`[tool.pytest.ini_options].markers`; the severity mapping lives in
`tests/conftest.py` (`IMPACT_TO_SEVERITY`). Adding a new tag means touching both.

## Test Reports

Every variant writes the same set of files, into the same paths:

| Artefact | Path | Produced by |
|----------|------|-------------|
| JUnit XML | `test_report.xml` | all variants |
| Cucumber JSON | `cucumber.json` | all variants |
| Coverage (HTML / XML) | `test_coverage/`, `coverage.xml` | all variants |
| Allure results (JSON) | `reports/allure-results/` | `-allure` variants only |

Because the paths are fixed, running a partial variant overwrites the previous
run's report. Archive or rename the artefacts between runs if both are needed.

The JUnit XML report uses test method docstrings and test parameter values to
generate test names rather than plain test method names.


## Environment Variables

Test scripts are dependent on the following environment variables:

```
DATABASE_URL
DATABASE_NAME
API_BASE_URL
CONSUMER_API_BASE_URL
API_AUTH_TOKEN
```

Crete an `.env` file in project root locally, for example:

```
DATABASE_URL=bolt://neo4j:<your-neo4j-password>@localhost:7687
DATABASE_NAME=
API_BASE_URL=http://localhost:8000
CONSUMER_API_BASE_URL=http://localhost:8008
API_AUTH_TOKEN=

STUDY_UID=Study_000039                       # Study UID used to test various endpoints
STUDY_NUMBER=3003                            # Study Number used to test various endpoints
LIBRARY_NAME=SNOMED                          # Name of Library/Dictionary used to test various endpoints
CT_CODELIST_UID=CTCodelist_000001            # CT CodeList UID used to test various endpoints
CT_TERM_UID=CTTerm_000001                    # CT Term UID used to test various endpoints
```

## Dependencies

- For the purpose of verifying SB API endpoints, test script assumes that it can reach SB API that operates on the same database as the test script.

  This is achieved by setting the API environment variables `NEO4J_DSN` / `NEO4J_DATABASE` to the same values as corresponding `DATABASE_URL` / `DATABASE_NAME` environment variables for the migration script, e.g.

  ```
  NEO4J_DSN=bolt://neo4j:<your-neo4j-password>@localhost:7687
  NEO4J_DATABASE=schema.migration.test
  ```


# Allure Reporting

Allure is **not** a separate test suite — it is how a run gets published. The
`-allure` scripts run the same tests as their plain counterparts and add
`--alluredir reports/allure-results`, which makes each test emit a JSON result
file. That directory is the publishable artefact:

- **CI:** upload `reports/allure-results` to the Allure server, which merges it
  with previous runs and serves the history, trend, severity and epic views.
  Because severity comes from the `impact:*` tags (see
  [Test Selection Tags](#test-selection-tags)), the server's severity breakdown
  is the criticality view of the run.
- **Locally:** render the same results as a throwaway HTML report.

Pick the `-allure` variant matching the scope you want published:

```sh
pipenv run test-allure                      # whole suite
pipenv run test-only-endpoints-allure       # API/endpoint tests only
pipenv run test-only-db-allure              # database tests only
```

To view a run locally, install the [Allure Report](https://allurereport.org/docs/install/)
CLI, then either:

```sh
allure serve reports/allure-results               # build + open in browser, not persisted
allure generate reports/allure-results -o reports/allure-report --clean
```

`allure serve` is a developer convenience only. Trend and history across runs
come from the Allure server, not from a local `generate`.

