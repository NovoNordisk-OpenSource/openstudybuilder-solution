# Overview

This document describes a set of GET endpoints in the OpenStudyBuilder Consumer API, which expose information about various entities defined in the `Library` section of OpenStudyBuilder.

Detailed API specification of each endpoint is found in the `consumer_api/openapi.json` file.

# Library Activities

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

## FS-ConsumerApi-Library-ActivityInstances-Get-010 [`URS-ConsumerApi-Library-Activities`]

Consumers must be able to retrieve a paginated list of all library activity instances by calling the `GET /library/activity-instances` endpoint.

### Request

It must be possible to filter items by `library`, `status` and `activity_uid`.

It must be possible to sort items by `uid` and `name` fields.

### Response

Response must include basic information about each activity instance, together with linked activity, activity group(s) and activity subgroup(s).

### Test coverage

| Test File                    | Test Function                                                 |
| ---------------------------- | ------------------------------------------------------------- |
| tests/v1/test_api_library.py | test_get_library_activity_instances                           |
| tests/v1/test_api_library.py | test_get_library_activity_instances_pagination_sorting        |
| tests/v1/test_api_library.py | test_get_library_activity_instances_all                       |
| tests/v1/test_api_library.py | test_get_library_activity_instances_filtering                 |
| tests/v1/test_api_library.py | test_get_library_activity_instances_invalid_pagination_params |
| tests/v1/test_api_library.py | test_get_library_activity_instances_activity_items            |

# Library CT Codelists

## FS-ConsumerApi-Library-Codelists-Get-010 [`URS-ConsumerApi-Library-ControlledTerminology`]

Consumers must be able to retrieve a paginated list of all CT codelists by calling the `GET /library/ct/codelists` endpoint.

### Request

It must be possible to filter items by `name_status` and `attributes_status` (_Final, Draft, Retired_). Both filters default to _Final_.

### Response

Response must include basic information about each codelist: UID, name, submission value, sponsor preferred name, NCI preferred name, definition, is_extensible flag, library name, name status, name version, attributes status, and attributes version.

Items are sorted by ascending codelist name.

### Test coverage

| Test File                       | Test Function                                     |
| ------------------------------- | ------------------------------------------------- |
| tests/v1/test_api_library_ct.py | test_get_codelists                                |
| tests/v1/test_api_library_ct.py | test_get_codelists_pagination                     |
| tests/v1/test_api_library_ct.py | test_get_codelists_invalid_pagination_params      |
| tests/v1/test_api_library_ct.py | test_get_codelists_default_status_filter          |
| tests/v1/test_api_library_ct.py | test_get_codelists_filter_name_status_draft       |
| tests/v1/test_api_library_ct.py | test_get_codelists_filter_attributes_status_draft |
| tests/v1/test_api_library_ct.py | test_get_codelists_filter_both_statuses_explicit  |

# Library CT Codelist Terms

## FS-ConsumerApi-Library-CodelistTerms-Get-010 [`URS-ConsumerApi-Library-ControlledTerminology`]

Consumers must be able to retrieve a paginated list of CT codelist terms by calling the `GET /library/ct/codelist-terms` endpoint.

### Request

The optional `codelist_submission_value` query parameter filters terms by codelist submission value (e.g. `TIMELB`, `TIMEREF`, `VISCNTMD`, `FLWCRTGRP`, `EPOCHSTP`).

The optional `codelist_uid` query parameter filters terms by codelist UID.

Both `codelist_submission_value` and `codelist_uid` can be provided together. If neither is provided, all terms are returned.

It must be possible to filter items by `name_status` and `attributes_status` (_Final, Draft, Retired_). Both filters default to _Final_.

### Response

Response must include basic information about each codelist term: term UID, codelist UID, order, ordinal, submission value, sponsor preferred name, concept ID, NCI preferred name, and library name.

Items are sorted by ascending codelist UID, then term UID.

If the specified codelist does not exist, an empty list is returned.

### Test coverage

| Test File                       | Test Function                                              |
| ------------------------------- | ---------------------------------------------------------- |
| tests/v1/test_api_library_ct.py | test_get_codelist_terms                                    |
| tests/v1/test_api_library_ct.py | test_get_codelist_terms_nonexistent_codelist               |
| tests/v1/test_api_library_ct.py | test_get_codelist_terms_pagination                         |
| tests/v1/test_api_library_ct.py | test_get_codelist_terms_no_filters                         |
| tests/v1/test_api_library_ct.py | test_get_codelist_terms_filter_by_codelist_uid             |
| tests/v1/test_api_library_ct.py | test_get_codelist_terms_filter_by_both_params              |
| tests/v1/test_api_library_ct.py | test_get_codelist_terms_filter_by_nonexistent_codelist_uid |
| tests/v1/test_api_library_ct.py | test_get_codelist_terms_invalid_pagination_params          |
| tests/v1/test_api_library_ct.py | test_get_codelist_terms_default_status_filter              |
| tests/v1/test_api_library_ct.py | test_get_codelist_terms_filter_name_status_draft           |
| tests/v1/test_api_library_ct.py | test_get_codelist_terms_filter_attributes_status_draft     |
| tests/v1/test_api_library_ct.py | test_get_codelist_terms_filter_both_statuses_explicit      |

# Library Unit Definitions

## FS-ConsumerApi-Library-UnitDefinitions-Get-010 [`URS-ConsumerApi-Library-UnitDefinitions`]

Consumers must be able to retrieve a paginated list of unit definitions by calling the `GET /library/unit-definitions` endpoint.

### Request

The optional `subset` query parameter filters unit definitions by subset name (e.g. `Study Time`). If omitted, all unit definitions are returned.

It must be possible to filter items by `status` (_Final, Draft, Retired_). The filter defaults to _Final_.

### Response

Response must include basic information about each unit definition: UID, name, library name, status, version, and the list of subsets the unit definition belongs to (each subset includes term UID, term name, term submission value, codelist UID, codelist name, and codelist submission value).

Items are sorted by ascending name.

If the specified subset does not exist, an empty list is returned.

### Test coverage

| Test File                       | Test Function                                          |
| ------------------------------- | ------------------------------------------------------ |
| tests/v1/test_api_library_ct.py | test_get_unit_definitions                              |
| tests/v1/test_api_library_ct.py | test_get_unit_definitions_nonexistent_subset           |
| tests/v1/test_api_library_ct.py | test_get_unit_definitions_without_subset               |
| tests/v1/test_api_library_ct.py | test_get_unit_definitions_pagination                   |
| tests/v1/test_api_library_ct.py | test_get_unit_definitions_invalid_pagination_params    |
| tests/v1/test_api_library_ct.py | test_get_unit_definitions_default_status_filter        |
| tests/v1/test_api_library_ct.py | test_get_unit_definitions_filter_status_draft          |
| tests/v1/test_api_library_ct.py | test_get_unit_definitions_filter_status_explicit_final |

# Projects

## FS-ConsumerApi-Projects-Get-010 [`URS-ConsumerApi-Projects`]

Consumers must be able to retrieve a paginated list of all projects by calling the `GET /library/projects` endpoint.

### Request

The endpoint takes pagination parameters only; filtering and client-selected sorting are not supported.

### Response

Response must include basic information about each project: UID, project ID, name and description, together with a nested `clinical_programme` object holding the UID and name of the clinical programme the project belongs to.

Items are sorted by ascending project ID.

The returned `id` values are the ones accepted as `project_id` by the `POST /studies` endpoint.

### Test coverage

| Test File                     | Test Function                               |
| ----------------------------- | ------------------------------------------- |
| tests/v1/test_api_projects.py | test_get_projects                           |
| tests/v1/test_api_projects.py | test_get_projects_pagination                |
| tests/v1/test_api_projects.py | test_get_projects_all                       |
| tests/v1/test_api_projects.py | test_get_projects_sorted_by_ascending_id    |
| tests/v1/test_api_projects.py | test_get_projects_invalid_pagination_params |
