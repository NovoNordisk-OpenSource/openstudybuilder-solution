# Introduction

This folder contains functional specifications of the Consumer API and traceability between tests, functional specifications and user requirements.

Approach to managing requirements and tracability:

- URSs, FSs and test traceability are defined in markdown files in this repository.
- URSs are defined in the `consumer_api/requirements/urs` folder.
- FSs and corresponding test traceability are defined in the `consumer_api/requirements/urs` folder.
- Python script (executed by running `pipenv run consumer-api-traceability`) collects the information from all relevant urs/fs markdown files and generates one html tracability document.

## Document formats

It is important that all URS and FS markdown documents follow a strict structure described below.

### URS documents

Each URS must have a unique `id` and `text` in the following format:

- **URS ID**: defined as header 1 element - `# {URS-UNIQUE-ID}`.
- **URS text**: any other valid markdown content apart from header 1 (`# ...`) sections.

Example:

```
# URS-ConsumerApi-Library-Activities

Consumers must be able to retrieve a list of all library activities and activity instances via the Consumer API.
```

### FS documents

Each FS must have a unique `id`, `text`, `link to a URS` and `related tests` in the following format:

- **FS ID** and **link to URS**: stored as header 2 element - `## {FRS-UNIQUE-ID} [URS-UNIQUE-ID]`.
- **FS text**: any other valid markdown content apart from header 1 (`# ...`) and header 2 (`## ...`) elements.
- **Related tests**: defined in a table below a `### Test coverage` section.

Example:

```
## FS-ConsumerApi-Library-Activities-Get-010 [`URS-ConsumerApi-Library-Activities`]

Consumers must be able to retrieve a paginated list of all library activities by calling the `GET /library/activities` endpoint.

### Request

It must be possible to filter items by `library` and `status`.

It must be possible to sort items by `uid` and `name` fields.

### Response

Response must include basic information about each activity, together with linked activity group(s) and activity subgroup(s).

### Test coverage

| Test File                    | Test Function                                         |
| ---------------------------- | ----------------------------------------------------- |
| tests/v1/test_api_library.py | test_get_library_activities                           |
| tests/v1/test_api_library.py | test_get_library_activities_pagination_sorting        |
| tests/v1/test_api_library.py | test_get_library_activities_all                       |
| tests/v1/test_api_library.py | test_get_library_activities_filtering                 |
| tests/v1/test_api_library.py | test_get_library_activities_invalid_pagination_params |
```

# Release process

These pipelines need to run succesfully before a Consumer API deployment can be made to VAL/PRD:

- Build pipeline that builds **just** the Consumer API

  - Runs all Consumer API tests mentioned in the FS traceability document (on top of schemathesis, pylint, SonarLint, snyk etc.), and generates a standard ADO test report
  - New build step/script collects all relevant URSs/FSs/tests, generates and publishes a `traceability.html` document

- Verifications pipeline (only checking Consumer API endpoints)

  - Runs verifications tests against a target environment (DEV/TST/VAL/PRD) and generates a standard ADO test report

- Load tests pipeline (only checking Consumer API endpoints)
  - Runs load tests against a target environment (DEV/TST/VAL/PRD) and generates a standard ADO test report
