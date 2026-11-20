# Overview

This document describes a set of GET endpoints in the OpenStudyBuilder Consumer API, which expose information about various OpenStudyBuilder entities in the format suitable for SDTM generation.

Detailed API specification of each endpoint is found in the `consumer_api/openapi.json` file.

# Schedule of Activities

## FS-ConsumerApi-Papillons-Soa-Get-010 [`URS-ConsumerApi-Studies-Papillons`]

Consumers must be able to retrieve SoA in the Papillons-suitable format by calling the `GET /papillons/soa` endpoint.

### Request

Consumer must send `project` and `study_number` query parameters.

Endpoint must support the following optional query parameters:

- subpart
- study_version_number
- datetime

### Response

Response must include information about schedule of activities, i.e. matrix of activites (topic codes) and visits for the specified study and study version or datetime.

### Test coverage

| Test File                    | Test Function          |
| ---------------------------- | ---------------------- |
| tests/v1/test_api_studies.py | test_get_papillons_soa |

# Non-Standard Variables

## FS-ConsumerApi-Papillons-NonStandardVariables-Get-010 [`URS-ConsumerApi-Library-Papillons-NonStandardVariables`]

Consumers must be able to retrieve Non-Standard Variables in the MMA SDTM_QNAM import format by calling the `GET /papillons/non-standard-variables` endpoint.

### Request

The endpoint takes no parameters and returns the full, unpaged set of results.

### Response

Response must be a `text/csv` document, `|`-delimited, containing one row per Final Non-Standard Variable whose Data Type belongs to the SEMTCDT (Semantic Data Type) codelist, using the MMA SDTM_QNAM column set (`cd_list_id`, `cd_val`, `cd_val_lb`, `cd_val_short_lb`, `cd_val_desc`, `sdtm_qnam_data_type`, `sdtm_qnam_length`, `sdtm_qnam_ct`, `sdtm_qnam_algorithm`, `sdtm_qnam_multiple`, `sdtm_qnam_qorig`, `cd_val_std`, `cd_list_val_status`).

The `sdtm_qnam_data_type` column must hold the NSVXMLDT (NSV XML Data Type) equivalent of the variable's SEMTCDT data type, resolved by walking the `IS_SPECIALIZATION_OF` relationship up to the nearest NSVXMLDT-tagged ancestor.

The `sdtm_qnam_qorig` column must hold the MMA QORIG value derived from the variable's origin type and origin source, or an empty string if the pair has no MMA mapping.

Only Non-Standard Variables in Final status must be included.

### Test coverage

| Test File                                         | Test Function                                       |
| -------------------------------------------------- | ---------------------------------------------------- |
| tests/v1/test_papillons_non_standard_variables.py  | test_response_is_csv_with_expected_header            |
| tests/v1/test_papillons_non_standard_variables.py  | test_export_contains_exactly_the_created_final_nsvs  |
| tests/v1/test_papillons_non_standard_variables.py  | test_row_matches_exact_expected_values               |
| tests/v1/test_papillons_non_standard_variables.py  | test_zero_length_nsv_is_not_collapsed_to_empty_string |
| tests/v1/test_papillons_non_standard_variables.py  | test_unmapped_origin_pair_resolves_to_empty_qorig    |
| tests/v1/test_papillons_non_standard_variables.py  | test_semtcdt_to_nsv_xml_dt_traversal_zero_hop        |
| tests/v1/test_papillons_non_standard_variables.py  | test_semtcdt_to_nsv_xml_dt_traversal_two_hops        |
| tests/v1/test_papillons_non_standard_variables.py  | test_unknown_semtcdt_term_resolves_to_none           |

## FS-ConsumerApi-Papillons-DataTypeMapping-Get-010 [`URS-ConsumerApi-Library-Papillons-NonStandardVariables`]

Consumers must be able to resolve a single SEMTCDT (Semantic Data Type) term to its NSVXMLDT (NSV XML Data Type) equivalent by calling the `GET /papillons/data-type-mapping/{semtcdt_term}` endpoint.

### Request

Consumer must send the SEMTCDT term's submission value as the `semtcdt_term` path parameter, e.g. `code`, `ctTerm`, `text`.

### Response

Response must include the requested `semtcdt_term` and the resolved `nsv_xml_term`, using the same `IS_SPECIALIZATION_OF` traversal as the `sdtm_qnam_data_type` column of `GET /papillons/non-standard-variables`. If the term cannot be resolved to an NSVXMLDT ancestor, or does not exist, `nsv_xml_term` must be `null`.

### Test coverage

| Test File                                         | Test Function                                         |
| -------------------------------------------------- | ------------------------------------------------------ |
| tests/v1/test_papillons_non_standard_variables.py  | test_data_type_mapping_endpoint_resolves_known_terms   |
| tests/v1/test_papillons_non_standard_variables.py  | test_data_type_mapping_endpoint_unknown_term_returns_null |

# Study Metadata

## FS-ConsumerApi-Papillons-StudyMetadata-AuxiliaryDevices-Get-010 [`URS-ConsumerApi-Studies-Papillons`]

Consumers must be able to retrieve the auxiliary devices selected for a study by calling the `GET /papillons/study-metadata` endpoint.

### Request

Same parameters as the rest of `GET /papillons/study-metadata`: `project_id` and `study_number`, optionally `subpart` and one of `study_version_number` or `datetime`.

### Response

Response must include an `auxiliary_devices` list, ordered by `order`. Each item must hold the selection `uid`, its `order`, the device CT term from the `DEVICE_DEF` codelist as a conflict-aware CT term object (`device`), and the term's SDTM `algorithm` text, resolved at the study's CT package date.

### Test coverage

| Test File                             | Test Function                                              |
| ------------------------------------- | ---------------------------------------------------------- |
| tests/v1/test_api_study_metadata.py   | test_get_study_metadata_returns_200_and_shape              |
| tests/v1/test_api_study_metadata.py   | test_get_study_metadata_auxiliary_devices_shape_and_content |

# Topic Code Definitions

## FS-ConsumerApi-Papillons-TopicCdDef-Get-010 [`URS-ConsumerApi-Library-Papillons-TopicCodeDefinitions`]

Consumers must be able to retrieve a paginated list of topic code definitions (`TOPIC_CD_DEF`) by calling the `GET /papillons/topic-cd-def` endpoint.

### Request

Endpoint must support the optional `datetime` query parameter (ISO 8601 format, e.g. `2021-01-01T09:00:00Z`; a value that is not an ISO 8601 date and time, such as a number, or has no timezone is rejected with a 400 error). If specified, the latest Final version of each activity instance that had started by that moment is used, and instances without a Final version by then are omitted; otherwise the latest Final version is used. A newer Draft or later retirement does not remove an instance that already had a Final version by the requested moment, while instances first finalized later remain omitted. With `datetime` only the activity instance version is time-travelled: activity item classes, CT terms, units and Activity Instance Classes are read in their current state.

It must be possible to sort items by `lb`, `topic_cd` and `short_topic_cd` fields, in ascending or descending order. Default sorting is by `lb` ascending.

### Response

Response must include one item per library activity instance that has a Final version, with the following fields: `uid`, `lb`, `topic_cd`, `short_topic_cd`, `description`, `molecular_weight`, `sas_display_format`, `general_domain_class`, `sub_domain_class`, `sub_domain_type`, `cat`, `sub_cat`, `catgo_resp_list`, `convert_to_us_conv_unit`, `version`, `status`, `std_unit`, `topic_cd_type` and `unit_dimension`.

- `cat` and `sub_cat` hold the category and subcategory of the activity instance (from the `finding_`, `intervention_` or `event_` category/subcategory activity items): the name of the selected CT term, or the item's text value when the item holds text.
- `catgo_resp_list` holds the submission value of the response codelist selected on the `categoric_finding_original_result` activity item.
- `convert_to_us_conv_unit` is `true` if any unit of the instance is a US conventional unit, `false` if it has units but none is US conventional, and `null` if it has no units.
- `version` and `status` come from the Final version listed: the highest approved version number and its status (`Final`). A newer unapproved Draft does not change them, and a Retired instance is still listed with its last Final version.
- `general_domain_class` and `sub_domain_class` are the names of Activity Instance Classes, returned as stored. They are found by following the instance's activity items to their activity item classes and from there to the Activity Instance Classes those are attached to (each class points to its parent through `PARENT_CLASS`). `general_domain_class` is the class at level 2 (e.g. `Finding`, `Event`, `Intervention`) and `sub_domain_class` the class at level 3 (e.g. `NumericFindings`, `CategoricFindings`, `TextualFindings`). Only classes in the instance's own class lineage (its Activity Instance Class and that class's ancestors) are considered, so an activity item class attached to several sibling branches (for example `location`) cannot classify the instance under another branch. Both are `null` if no such class is found, for example when the instance has no activity items. When several remain, the alphabetically first name is returned. The same rule makes the item-based columns (`cat`, `sub_cat`, `catgo_resp_list`, `std_unit`, `unit_dimension`) deterministic.
- `sub_domain_type` is not part of the class hierarchy and still comes from legacy node labels. It is always set and is one of `Compound`, `LaboratoryActivity`, `RatingScale` or `Other`; instances created through the API do not carry the labels, so it is `Other` for them.
- `std_unit` holds the name of the standard unit, `unit_dimension` the submission value of the unit dimension term, and `topic_cd_type` the name of the activity instance class.

`uid`, `sub_domain_type`, `version` and `status` are always set. The other fields are `null` when the activity instance has no corresponding data.

Activity instances that have never been approved (Draft only) must not be included.

### Test coverage

| Test File                                  | Test Function                                           |
| ------------------------------------------ | ------------------------------------------------------- |
| tests/v1/test_papillons_topic_cd_def.py    | test_data |
| tests/v1/test_papillons_topic_cd_def.py    | test_response_shape |
| tests/v1/test_papillons_topic_cd_def.py    | test_lists_final_instances_only |
| tests/v1/test_papillons_topic_cd_def.py    | test_row_matches_created_values |
| tests/v1/test_papillons_topic_cd_def.py    | test_fixture_exercises_every_column_variant |
| tests/v1/test_papillons_topic_cd_def.py    | test_molecular_weight_zero_is_not_collapsed_to_null |
| tests/v1/test_papillons_topic_cd_def.py    | test_terms_give_names_for_categories_and_submission_values_for_dimension |
| tests/v1/test_papillons_topic_cd_def.py    | test_classification_follows_item_classes_up_the_class_hierarchy |
| tests/v1/test_papillons_topic_cd_def.py    | test_classification_ignores_item_classes_shared_with_other_class_branches |
| tests/v1/test_papillons_topic_cd_def.py    | test_newer_unapproved_draft_does_not_hide_final_version |
| tests/v1/test_papillons_topic_cd_def.py    | test_retired_instance_is_listed_with_its_final_version |
| tests/v1/test_papillons_topic_cd_def.py    | test_default_sort_is_by_label_ascending |
| tests/v1/test_papillons_topic_cd_def.py    | test_sort_order_desc_reverses_asc |
| tests/v1/test_papillons_topic_cd_def.py    | test_pages_follow_the_full_sorted_listing |
| tests/v1/test_papillons_topic_cd_def.py    | test_datetime_in_the_future_matches_the_default_listing |
| tests/v1/test_papillons_topic_cd_def.py    | test_datetime_between_two_final_versions_returns_the_earlier_one |
| tests/v1/test_papillons_topic_cd_def.py    | test_datetime_before_creation_returns_nothing |
| tests/v1/test_papillons_topic_cd_def.py    | test_invalid_parameters_are_rejected |
