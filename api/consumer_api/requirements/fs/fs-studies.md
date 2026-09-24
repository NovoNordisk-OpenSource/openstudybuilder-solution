# Overview

This document describes a set of GET endpoints in the OpenStudyBuilder Consumer API, which expose information about various entities defined in the `Studies` section of OpenStudyBuilder.

Detailed API specification of each endpoint is found in the `consumer_api/openapi.json` file.

# Studies

## FS-ConsumerApi-Studies-Studies-Get-010 [`URS-ConsumerApi-Studies`]

Consumers must be able to retrieve a paginated list of all studies by calling the `GET /studies` endpoint.

### Request

It must be possible to filter items by study `id`.

It must be possible to sort items by `uid`, `id_prefix` and `number` fields.

### Response

Each item in the response must include basic information about a study (`uid`, `id`), together with a list of all existing study versions for each study (`version_status`, `version_number`, `version_started_at`, `version_ended_at`).

### Test coverage

| Test File                    | Test Function                              |
| ---------------------------- | ------------------------------------------ |
| tests/v1/test_api_studies.py | test_get_studies                           |
| tests/v1/test_api_studies.py | test_get_studies_pagination_sorting        |
| tests/v1/test_api_studies.py | test_get_studies_all                       |
| tests/v1/test_api_studies.py | test_get_studies_filtering                 |
| tests/v1/test_api_studies.py | test_get_studies_invalid_pagination_params |
| tests/v1/test_api_studies.py | test_get_studies_returns_data_suppliers    |

## FS-ConsumerApi-Studies-Studies-Post-010 [`URS-ConsumerApi-Studies-Create`]

Consumers with study write access must be able to create a new top-level study definition by calling the `POST /studies` endpoint.

### Request

The request body must accept:

- `study_number`: 1 to 4 digits, optional
- `study_acronym`: optional
- `project_id`: the ID of an existing project, required
- `description`: optional

At least one of `study_number` and `study_acronym` must be provided.

`project_id` must be matched exactly and case-sensitively against existing projects.

Fields that are not part of the request schema must be rejected rather than silently ignored.

The endpoint must reject the request with a validation error if:

- neither `study_number` nor `study_acronym` is provided
- `study_number` is not 1 to 4 digits
- `project_id` does not identify an existing project — the error must point the consumer at the `GET /library/projects` endpoint

The endpoint must reject the request with a conflict error if the study number or the study acronym is already used by another study. Both are unique across all studies, not just within the project.

Creating study subparts is not supported by this endpoint.

### Response

On success, the endpoint must return the created study in `DRAFT` status, including its `uid`, the server-derived `id` (`{project_id}-{study_number}`), `acronym` and `description`.

The `id` must be derived the same way as in the `GET /studies` response, so that a study is identified identically by both endpoints. If the study has no study number, the number part of the `id` is empty.

### Test coverage

| Test File                           | Test Function                                            |
| ----------------------------------- | -------------------------------------------------------- |
| tests/v1/test_api_studies_create.py | test_create_study                                        |
| tests/v1/test_api_studies_create.py | test_create_study_with_study_number_only                 |
| tests/v1/test_api_studies_create.py | test_create_study_with_study_acronym_only                |
| tests/v1/test_api_studies_create.py | test_create_study_with_lowercase_project_id              |
| tests/v1/test_api_studies_create.py | test_create_study_without_study_number_and_study_acronym |
| tests/v1/test_api_studies_create.py | test_create_study_with_invalid_study_number              |
| tests/v1/test_api_studies_create.py | test_create_study_with_unknown_project_id                |
| tests/v1/test_api_studies_create.py | test_create_study_without_project_id                     |
| tests/v1/test_api_studies_create.py | test_create_study_with_unknown_field                     |
| tests/v1/test_api_studies_create.py | test_create_study_with_duplicate_study_number            |
| tests/v1/test_api_studies_create.py | test_create_study_with_duplicate_study_acronym           |
| tests/v1/test_api_studies_create.py | test_created_study_is_returned_by_get_studies            |

# Study Structure

## FS-ConsumerApi-Studies-Activities-Get-010 [`URS-ConsumerApi-Studies-SoA`]

Consumers must be able to retrieve a paginated list of all study activities by calling the `GET /studies/{uid}/study-activities` endpoint.

### Request

It must be possible to filter items by `study_version_number`:

- If `study_version_number` query parameter is provided, study activities associated with the specified study version will be returned.
- Otherwise, study activities for the latest study version will be returned.

It must be possible to sort items by `uid` and `activity_name` fields.

### Response

Response must include basic information about each study activity, together with information about linked entities:

- library activity
- study SoA group
- study activity group
- study activity subgroup.

### Test coverage

| Test File                    | Test Function                                        |
| ---------------------------- | ---------------------------------------------------- |
| tests/v1/test_api_studies.py | test_get_study_activities                            |
| tests/v1/test_api_studies.py | test_get_study_activities_pagination_sorting         |
| tests/v1/test_api_studies.py | test_get_study_activities_all                        |
| tests/v1/test_api_studies.py | test_get_study_activities_all_specific_study_version |

## FS-ConsumerApi-Studies-ActivityInstances-Get-010 [`URS-ConsumerApi-Studies-SoA`]

Consumers must be able to retrieve a paginated list of all study activity instances by calling the `GET /studies/{uid}/study-activity-instances` endpoint.

### Request

It must be possible to filter items by `study_version_number`:

- If `study_version_number` query parameter is provided, study activity instances associated with the specified study version will be returned.
- Otherwise, study activity instances for the latest study version will be returned.

It must be possible to sort items by `uid`, `activity.name` and `activity_instance.name` fields.

### Response

Response must include basic information about each activity instance, together with information about linked entities:

- library activity
- library activity instance
- study SoA group
- study activity group
- study activity subgroup.

### Test coverage

| Test File                    | Test Function                                                |
| ---------------------------- | ------------------------------------------------------------ |
| tests/v1/test_api_studies.py | test_get_study_activity_instances                            |
| tests/v1/test_api_studies.py | test_get_study_activity_instances_pagination_sorting         |
| tests/v1/test_api_studies.py | test_get_study_activity_instances_all                        |
| tests/v1/test_api_studies.py | test_get_study_activity_instances_all_specific_study_version |

## FS-ConsumerApi-Studies-Visits-Get-010 [`URS-ConsumerApi-Studies-SoA`]

Consumers must be able to retrieve a paginated list of all study visits by calling the `GET /studies/{uid}/study-visits` endpoint.

### Request

It must be possible to filter items by `study_version_number`:

- If `study_version_number` query parameter is provided, study visits associated with the specified study version will be returned.
- Otherwise, study visits for the latest study version will be returned.

It must be possible to sort items by `uid`, `visit_name` and `unique_visit_number` fields.

### Response

Response must include basic information about each study visit.

### Test coverage

| Test File                    | Test Function                                    |
| ---------------------------- | ------------------------------------------------ |
| tests/v1/test_api_studies.py | test_get_study_visits                            |
| tests/v1/test_api_studies.py | test_get_study_visits_pagination_sorting         |
| tests/v1/test_api_studies.py | test_get_study_visits_all                        |
| tests/v1/test_api_studies.py | test_get_study_visits_all_specific_study_version |

## FS-ConsumerApi-Studies-SoaDetailed-Get-010 [`URS-ConsumerApi-Studies-SoA`]

Consumers must be able to retrieve a paginated list of detaild SoA items by calling the `GET /studies/{uid}/detailed-soa` endpoint.

### Request

It must be possible to filter items by `study_version_number`:

- If `study_version_number` query parameter is provided, study visits associated with the specified study version will be returned.
- Otherwise, study visits for the latest study version will be returned.

It must be possible to sort items by `visit_short_name`, `epoch_name`, `activity_name`, `activity_group_name`, `activity_subgroup_name`, `soa_group_name` fields.

### Response

Response must include basic information about study visits and activities included in the detailed SoA.

SoA items are sorted by the specified sort criteria and order.

### Test coverage

| Test File                    | Test Function                                          |
| ---------------------------- | ------------------------------------------------------ |
| tests/v1/test_api_studies.py | test_get_study_detailed_soa                            |
| tests/v1/test_api_studies.py | test_get_study_detailed_soa_pagination_sorting         |
| tests/v1/test_api_studies.py | test_get_study_detailed_soa_all                        |
| tests/v1/test_api_studies.py | test_get_study_detailed_soa_all_specific_study_version |

## FS-ConsumerApi-Studies-SoaOperational-Get-010 [`URS-ConsumerApi-Studies-SoA`]

Consumers must be able to retrieve a paginated list of operational SoA items by calling the `GET /studies/{uid}/operational-soa` endpoint.

### Request

It must be possible to filter items by `study_version_number`:

- If `study_version_number` query parameter is provided, study visits associated with the specified study version will be returned.
- Otherwise, study visits for the latest study version will be returned.

It must be possible to sort items by `activity_name`, `visit_uid`, `visit_short_name` fields.

### Response

Response must include basic information about study visits, activities and activity instances included in the operational SoA.

SoA items are sorted by the specified sort criteria and order.

### Test coverage

| Test File                    | Test Function                                             |
| ---------------------------- | --------------------------------------------------------- |
| tests/v1/test_api_studies.py | test_get_study_operational_soa                            |
| tests/v1/test_api_studies.py | test_get_study_operational_soa_pagination_sorting         |
| tests/v1/test_api_studies.py | test_get_study_operational_soa_all                        |
| tests/v1/test_api_studies.py | test_get_study_operational_soa_all_specific_study_version |

## FS-ConsumerApi-Studies-Soa-Post-010 [`URS-ConsumerApi-Studies-SoA-Create`]

Consumers with study write access must be able to create or replace a study Schedule of Activities by calling the `POST /studies/{uid}/soa` endpoint.

### Request

The request body must accept a complete SoA definition composed of:

- `epochs`: study epochs identified by client-side `reference_id`
- `visits`: study visits that reference epochs via `epoch_reference_id`
- `activities`: study activities that reference visits via `visit_reference_ids`

The endpoint must validate:

- controlled terminology and unit identifiers used in epochs and visits
- activity, SoA group, activity group, and activity subgroup identifiers
- cross-references between epochs, visits, and activities
- uniqueness of epoch, visit, and activity `reference_id` values
- uniqueness of epoch `order` values

If the request contains invalid identifiers, invalid references, or duplicate reference data, the endpoint must reject the request with a validation error.

If the study already has an existing SoA, the endpoint must replace existing epochs, visits, and activities with the new payload content.

### Response

On success, the endpoint must return a mapping of submitted reference IDs to created study entity UIDs for:

- `epochs`
- `visits`
- `activities`

### Test coverage

| Test File                | Test Function                                            |
| ------------------------ | -------------------------------------------------------- |
| tests/v1/test_api_soa.py | test_create_soa                                          |
| tests/v1/test_api_soa.py | test_create_soa_rejects_invalid_activity_uid             |
| tests/v1/test_api_soa.py | test_create_soa_rejects_invalid_activity_grouping        |
| tests/v1/test_api_soa.py | test_create_soa_rejects_invalid_uids                     |
| tests/v1/test_api_soa.py | test_create_soa_rejects_invalid_cross_references         |
| tests/v1/test_api_soa.py | test_create_soa_rejects_duplicate_epoch_reference_ids    |
| tests/v1/test_api_soa.py | test_create_soa_rejects_duplicate_epoch_orders           |
| tests/v1/test_api_soa.py | test_create_soa_rejects_duplicate_visit_reference_ids    |
| tests/v1/test_api_soa.py | test_create_soa_rejects_duplicate_activity_reference_ids |
| tests/v1/test_api_soa.py | test_create_soa_replaces_existing_entities               |

# Audit Trail

## FS-ConsumerApi-Studies-AuditTrail-Get-010 [`URS-ConsumerApi-Studies-AuditTrail`]

Consumers must be able to retrieve study audit trail entries by calling the `GET /studies/audit-trail` endpoint.

### Request

The endpoint must accept the following query parameters:

- `from_ts` (required): Start timestamp in ISO format with timezone (e.g., 2024-01-01T00:00:00Z). Audit trail entries with timestamps greater than or equal to this value will be returned.
- `to_ts` (required): End timestamp in ISO format with timezone (e.g., 2024-01-05T00:00:00Z). Audit trail entries with timestamps less than this value will be returned.
- `study_id` (optional): Filter by study ID using case-insensitive partial match (e.g., "XX1234-5678").
- `entity_type` (optional): Filter by entity type (e.g., "StudyActivity").
- `exclude_study_ids` (optional): List of study IDs to exclude using case-insensitive partial match.
- `page_number` (optional): Page number for pagination (default: 1).

### Response

The endpoint must return audit trail entries in CSV format with the following columns:

- `ts`: Timestamp of the action
- `study_uid`: Study UID
- `study_id`: Study ID
- `action`: Action performed (Create, Edit, Delete)
- `entity_uid`: UID of the entity affected by the action
- `entity_type`: Type (node labels) of the entity affected by the action. Multiple labels are separated by '|' character.
- `changed_properties`: List of properties that were changed during the Edit action separated by '|' character.
- `author`: Hashed (MD5) value of the ID of a user that performed the action

The response must have a media type of `text/csv`.

The maximum number of rows returned is limited to 10,000.

### Privacy Requirements

User identifiers must be anonymized by applying MD5 hashing to the author's user ID before including it in the response.

### Test coverage

| Test File                        | Test Function              |
| -------------------------------- | -------------------------- |
| tests/v1/test_api_audit_trail.py | test_get_study_audit_trail |
