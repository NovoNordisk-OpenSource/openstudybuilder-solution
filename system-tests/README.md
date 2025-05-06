# UI Tests Readme

## Introduction

This repository contains the Cypress tests for the Clinical MDR + Studybuilder project.

For any issues, please refer to the official Cypress documentation:
[https://docs.cypress.io/guides/getting-started/installing-cypress](https://docs.cypress.io/guides/getting-started/installing-cypress)

## Cypress Installation and Configuration

### Prerequisites

- The configuration files `./ui-tests/cypress.json` and `./ui-tests/cypress.env.json` are located in the root of the repository.
- Ensure the `baseUrl` in `cypress.json` matches the homepage URL of the environment where you plan to run the tests:
  ```json
  {
    "baseUrl": "http://localhost:8080"
  }
  ```
- Ensure the `api` variable in `cypress.env.json` matches the API endpoint of your setup:
  ```json
  {
    "api": "http://localhost:8000/api"
  }
  ```

## Authentication Configuration

This test suite will automatically detect provided environment variables to determine if authentication steps should be included during the test execution.

### Running Tests with Authentication

- Provide authentication data in `./ui-tests/cypress.env.json`.
- Static variables are mocked data that should remain unchanged. This data is only for frontend operations and is not required for the proper authentication flow.
- The structure of `./ui-tests/cypress.env.json` should be as below:
  ```json
  {
      "API": "",
      "TOKEN_ENDPOINT": "",
      "TESTUSER_MAIL": "",
      "TESTUSER_NAME": "",
      "GRANT_TYPE": "",
      "CLIENT_ID": "",
      "SCOPE": "",
      "CLIENT_SECRET": "",
      "STATIC_IDTOKEN": "",
      "STATIC_SESSION_STATE": ""
  }
  ```

### Installation

Run `yarn install` in the ui-tests directory of the repository to install Cypress and all dependencies.

## Running Tests

You can run Cypress tests using the terminal in two ways:

- `yarn run cypress open`: Launches the Cypress Test Runner GUI.
- `yarn run test:run`: Executes tests in the terminal.

### Cypress Open

The command `yarn run cypress open` launches the Cypress Test Runner GUI on your local environment. This interactive dashboard is ideal for users unfamiliar with Cypress or those who want to observe the test execution in real-time.

### Test Run

The command `yarn run test:run` initiates the headless version of Cypress and runs all available tests, suitable for use in a CI/CD pipeline or Dockerized environment. This mode is generally used by developers and testers for automated testing.

Ensure that `yarn run test:run` works correctly before pushing tests to the repository, as there can be differences between the GUI and headless versions of the test runner.

### Test Report Generation

Test reports are generated using Allure Reporter. In order to generate the report for Allure framework use commands included in `ui-tests/package.json` which are defined to make use of Allure:

- `test:run`
- `test:run-chrome`

This commands will generate the results into `./ui-tests/results/allure` from where those can be sent to Allure service. 

### Using Flags for Terminal Runner

Example of running a specific feature file:
```sh
npx cypress run --spec "cypress/integration/filenameYouWantToRun.feature"
```

