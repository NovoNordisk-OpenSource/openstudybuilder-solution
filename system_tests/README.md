# System Tests

End-to-end tests for OpenStudyBuilder, written in Gherkin and run with
[Cypress](https://docs.cypress.io/).

Two independent suites:

| Directory | Covers |
|---|---|
| `ui-tests/` | The OpenStudyBuilder web application |
| `neodash-test/` | The NeoDash reports |

Both are npm projects with their own `package.json` and `package-lock.json`.
Run every command from inside the suite directory.

Node.js 20 is a prerequisite — see the
[root README](../README.md#prerequisites).

## Configuration

Each suite is configured by two files in its own directory:

| File | Purpose |
|---|---|
| `cypress.config.js` | Cypress configuration, including `baseUrl` |
| `cypress.env.json` | Environment values, including the API endpoint and authentication |

Set `baseUrl` in `cypress.config.js` to the application under test, and the
`API` value in `cypress.env.json` to its API, for example
`http://localhost:8000/api` for a local setup.

### Authentication

The suites detect whether authentication values are present and include the
login steps only if they are. To run against an environment with
authentication enabled, fill in `cypress.env.json`:

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

`STATIC_IDTOKEN` and `STATIC_SESSION_STATE` are mock values used only by the
frontend; they are not part of the authentication flow and should be left as
they are.

## Install

```sh
cd ui-tests        # or: cd neodash-test
npm ci
```

## Run

```sh
npm test                    # clean previous results, then run all tests headless with Allure output
npm run test-chrome         # same, in Chrome
npm run test:no-allure      # run headless without Allure, JUnit output only
npm run test:clean          # delete the results directory
```

To open the interactive Cypress runner:

```sh
npx cypress open
```

`ui-tests/` also has scripts for running a subset:

```sh
npm run test:run-studies    # runs the library specs — see note
npm run test:run-library    # runs the studies specs — see note
npm run test:run-authonly
```

**Note:** the `--spec` globs for `test:run-studies` and `test:run-library` are
swapped in `ui-tests/package.json`; each runs the other's suite. Nothing in CI
uses them, so the labels have never been load-bearing. Fixing them means
swapping the two globs in `package.json`.

Run a single feature file directly:

```sh
npx cypress run --spec "cypress/e2e/features/<path-to>.feature"
```

The `host` Cypress environment variable is read from the `$cypresshost` shell
variable by the `test:run*` scripts. Set it when running against anything
other than the configured `baseUrl`.

## Reports

Test results are written to `results/allure` by the Allure-enabled scripts,
via [`@shelex/cypress-allure-plugin`](https://github.com/Shelex/cypress-allure-plugin).
The `test:no-allure*` variants produce JUnit XML only.

## Continuous integration

[`.github/workflows/system-tests-build.yml`](../.github/workflows/system-tests-build.yml)
installs both suites with `npm ci`, checks the SBOM, and builds the Cypress
Docker image.
