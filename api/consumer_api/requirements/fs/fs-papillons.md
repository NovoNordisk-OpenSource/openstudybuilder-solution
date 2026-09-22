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
