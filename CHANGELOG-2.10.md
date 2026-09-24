## V 2.10

New Features and Enhancements
============

### Highlights

- **Trial Summary Parameters and other study attributes can now be maintained in the application** — a new library code list at *Library › Trial Summary Parameters*, a study-level attributes page, a migration bringing existing studies onto the new structure, importer support, and inclusion in the SDTM Study Design Datasets specification. The parameter slots are also readable directly through `GET /meta-study-fields`.
- **Study definitions are now available in USDM v4.** The remaining v4 field mappings are complete, study epoch labels carry through to the mapped definition, and a new in-application JSON viewer at *Studies › USDM* presents the definition as a collapsible tree with a sticky path bar.
- **Study creation and Schedule of Activities submission can be driven through the consumer API**, alongside a new study-metadata listing that returns the full study design structure — epochs, visits, design cells and arms.
- **Comments can be added to study activities** at *Studies › Study Activities*, with an indicator marking commented activities and a filter to show only those that carry comments.
- **Managing how activities link to activity instances has been reworked:** a new form handles group and subgroup linking, editing has moved onto *Library › Activities*, and the activity-instance wizard now covers findings creation and interventions.
- **Non-standard variables are now typed against a curated semantic data-type code list.** A new sponsor subset code list restricts which XML data types apply to them, and a consumer API endpoint exposes each variable's ODM data type alongside its semantic data type, so downstream tools can produce Define.xml without re-deriving it.
- **SDTM annotations can be shown automatically in CRFs.** Dataset variables are now retrievable for CRF activity instances, backed by a new report linking activity instance classes, SDTM dataset variables, activity item classes and code lists.
- **The documentation portal gained a reports and dashboards section** — eight new report and dashboard guides with an index page, a new page on navigating the portal, refreshed data-specification and protocol-milestone guides, and 94 new or updated screenshots.
- **The full stack now runs locally behind a single address.** A new `gateway` reverse-proxy container fronts every service, so `docker compose up` gives you the application, both extension APIs, the documentation portal, the dashboards and the database browser on one port instead of one address per service. See **Running the application** below.
- **The open-source components are now published as one repository.** See **Renamed and moved** below.
- **Readme** files got updated, please refere to the single component readme files

### Renamed, moved and restructured

There has been a huge refactoring for the structure of the components including renamings. The following changes are available:

| Old name | Now |
| --- | --- |
| `clinical-mdr-api` | `api/` |
| `studybuilder` | `frontend/` |
| `neo4j-mdr-db` | `db/` |
| `db-schema-migration` | `db_schema_migration/` |
| `mdr-standards-import` | `import_standards/` |
| `studybuilder-import` | `import_sponsor_data/` |
| `studybuilder-export` | `export/` |
| `documentation-portal` | `documentation_portal/` |
| `osb-neodash` | `neodash/` |
| `system-tests` | `system_tests/` |
| `verifications` | `verifications/` |
| `studybuilder-load-test` | `load_tests/` |
| `build-tools` | `_tools/` |

The application is now running through a gateway using a different default port. The default Services are now available on the following addresses:

| Address | Serves |
| --- | --- |
| `http://localhost:8080/` | Application frontend |
| `http://localhost:8080/api/` | API |
| `http://localhost:8080/consumer-api/` | Consumer API |
| `http://localhost:8080/extensions-api/` | Extensions API |
| `http://localhost:8080/doc/` | Documentation portal |
| `http://localhost:8080/neodash/` | Dashboards |
| `http://localhost:8080/browser/` | Database browser |

### New features

- **api:** Added Trial Summary Parameters and Other Study Attributes, with a new library code list, a study-level attributes page, and inclusion in the SDTM Study Design Datasets specification — `GET /meta-study-fields`.
- **api:** Added lag time values and units on study epochs, available behind a feature flag and included in the study epochs tabular export.
- **api:** Added consumer API endpoints for creating a study, submitting a Schedule of Activities, and listing projects — `GET /v1/library/projects`.
- **api:** Added the ability to run long-running operations as background jobs, with their status visible in the application — `GET /jobs`, `GET /jobs/{job_uid}` and `POST /studies/{study_uid}/clone/async`.
- **api:** Added an export of the study design matrix to a spreadsheet.
- **api:** Added retrieval of dataset variables for CRF activity instances, so SDTM annotations can be shown automatically in CRFs.
- **api:** Added a consumer API study-metadata listing covering the full study design structure, including epochs, visits and design cells.
- **api:** Added an API endpoint backing the new form for managing activity-to-instance groupings.
- **db:** Added a report linking activity instance classes, SDTM dataset variables, activity item classes and code lists.
- **frontend:** Added selectable application themes, including high- and low-contrast options, saved as a user preference — chosen under *Preferences* in the account menu.
- **frontend:** Added support for interventions in the activity instance wizard.
- **frontend:** Added a JSON viewer for USDM study definitions at *Studies › USDM*, with a collapsible tree and a sticky path bar.
- **frontend:** Added a form for managing how activities link to activity instances, moving group and subgroup editing onto *Library › Activities*.
- **frontend:** Refined the activity commenting experience following review feedback.
- **frontend:** Added commenting on study activities at *Studies › Study Activities*, with an indicator on commented activities and a filter to show only those that have comments.
- **repository root:** Added a Docker Compose configuration that runs the full application stack locally behind a new `gateway` reverse proxy, reachable at `http://localhost:8080`.

### Improvements

- **api:** Improved controlled terminology listing filters to cover plain columns as well as nested objects, and added caching for code list lookups.
- **api:** Added NCI concept identifier and name fields to activity instance classes.
- **api:** Removed the obsolete sponsor compound flag from compounds.
- **api:** Added consumer API support for non-standard variables, including data type alignment checks.
- **api:** Improved uniqueness checks so non-standard variable names are validated independently of activity item classes.
- **api:** Added study epoch lag time to the consumer API.
- **api:** Refined the list of available lag time units for study epochs.
- **api:** Added support for external questions in CDISC ODM and corrected inconsistent vendor extension attribute naming.
- **api:** Improved the controlled terminology values returned by the consumer API.
- **api:** Improved handling of multiple sponsor models so schemas are resolved dynamically.
- **api:** Added an option to automatically approve items created by the product catalogue import.
- **api:** Updated the product catalogue import to the latest external interface version and added support for importing unique ingredient identifiers.
- **api:** Added audit trail history for feature flags, and feature flags are now addressed by their unique identifier — `/feature-flags/{uid}` replaces `/feature-flags/{serial_number}`, so clients calling the old path need updating.
- **api:** Expanded USDM coverage with intervention administrations and procedures, schedule timing details, activity and epoch sequencing, and additional study fields.
- **api:** Replaced deprecated database query syntax, improving query performance.
- **api:** Improved reliability of study epoch operations by making them transactional.
- **api:** Changed CRF item data types to reference controlled-terminology terms instead of plain strings.
- **api:** Added a fields parameter to the CRF endpoints so clients can request only the data they need.
- **api:** Added support for specialisation relationships between controlled-terminology terms.
- **api:** Improved how user details are resolved for comments so displayed names stay current.
- **db:** Extended the data model with parent-type relationships between code-list terms.
- **db:** Extended the data model to support non-standard variables.
- **db_schema_migration:** Relaxed the ordinal term validation rule.
- **db_schema_migration:** Removed the previous External Data File Specifications dashboard ahead of its replacement.
- **db_schema_migration:** Added a data migration for the reorganised data-type code list.
- **documentation_portal:** Updated the Study Data Specifications section of the user guide.
- **documentation_portal:** Updated and finalised the Reports and Dashboards section of the user guide.
- **documentation_portal:** Updated the user guide for protocol Schedule of Activities milestones.
- **frontend:** Refined the *Library › Trial Summary Parameters* screens following review.
- **frontend:** Renamed the Compounds menu item to *Library › Interventions*, matching the current library structure.
- **frontend:** Improved the Activities by Grouping tab under *Library › Activities* to list only final activities.
- **frontend:** Added cohorts to *Studies › Study Structure* for studies with a manual design class, allowed text values for cohort codes, and disabled browser autofill across forms.
- **frontend:** Added validation to reject non-integer lag time values on study epochs.
- **frontend:** Improved the CRF editing screens following design review.
- **frontend:** Improved the Schedule of Activities so the expanded or condensed view is retained when switching tabs.
- **frontend:** Improved the USDM JSON viewer by rendering empty arrays and objects inline.
- **frontend:** Improved performance when selecting a study to copy properties or population from.
- **frontend:** Improved search results by highlighting the matching terms.
- **frontend:** Improved the drag-and-drop guard in the CRF tree to prevent invalid moves.
- **frontend:** Redesigned the CRF tree in *Library › CRF Builder* and reworked its reordering behaviour.
- **frontend:** Made the casing of CRF data-type names consistent.
- **frontend:** Improved page load times by requesting only the fields each view needs.
- **frontend:** Improved data tables across the application, including remembering each user's column layout between sessions.
- **frontend:** Improved data-type term matching so names are accepted with or without spaces.
- **frontend:** Added the ability to specify a specialisation when adding parent or child code-list terms.
- **frontend:** Improved the activity list so filter values reload to match the selected active or archived library.
- **frontend:** Further refined filter behaviour when switching between active and archived activities.
- **frontend:** Improved the activity list so filters reset when the archived-items switch is toggled.
- **import_sponsor_data:** Added a sponsor-defined subset code list for non-standard variable XML data types.
- **import_sponsor_data:** Improved non-standard variable imports to use the semantic data type code list.
- **import_sponsor_data:** Added 'Pre-filled syringe' to the compound dispensed-in code list.
- **import_sponsor_data:** Improved the code-list import so existing submission-value term names are updated, and made lookups faster.
- **import_sponsor_data:** Added a feature flag controlling the non-standard-variable capability.
- **import_sponsor_data:** Added nmol/mL to the strength unit code-list subset.
- **import_sponsor_data:** Added activity instances to the CRF import data files.
- **import_sponsor_data:** Added support for patching code-list names and attributes during import.
- **import_sponsor_data:** Restructured sponsor code-list definitions to introduce the new data-type subsets.
- **import_standards:** Reduced the memory required to import external data standards.

Fixes and Infrastructure
============

## Bug fixes

- **api:** Fixed failures when filtering controlled terminology terms.
- **api:** Fixed an error when opening filters on controlled terminology catalogues.
- **api:** Fixed several issues in the CRF module.
- **api:** Fixed line breaks in visit short names in the Protocol Schedule of Activities when the name contains a hyphen.
- **api:** Fixed null flavour values not being returned by the consumer API.
- **api:** Fixed the top row of the Protocol Schedule of Activities not always being representative.
- **api:** Fixed the CDISC-defined column not appearing for non-standard variables in the table and overview.
- **api:** Fixed study epoch labels in USDM output so the short name is passed through instead of repeating the name.
- **api:** Fixed study epoch creation so an epoch given an explicit order is inserted at the correct position.
- **api:** Fixed a set of API errors and schema mismatches surfaced by contract testing.
- **api:** Fixed sub-visits appearing out of chronological order in the detailed Schedule of Activities for studies with sub-parts.
- **api:** Fixed study locking and unlocking failing after a study sub-part acronym had been changed.
- **api:** Fixed reordering of CRF items so the chosen order is preserved and is not altered by vendor extensions.
- **api:** Fixed versioning of activity instance groupings to prevent data-integrity problems.
- **api:** Fixed a concurrency failure when deleting study activity schedules together with their activities.
- **api:** Fixed inconsistent timestamps when releasing and locking study versions.
- **api:** Fixed a validation error when retrieving study visits that prevented the Schedule of Activities from loading for some studies.
- **api:** Fixed an error in the header-values endpoint when filtering on fields other than the field name.
- **api:** Fixed footnotes being filtered out of the detailed Schedule of Activities view.
- **db:** Fixed the Visits Label tab in the external data file specification report.
- **db_schema_migration:** Fixed sponsor model import leaving dataset variables without a parent.
- **db_schema_migration:** Added a migration that creates the archived library in existing environments.
- **frontend:** Fixed study arm data not appearing in several screens.
- **frontend:** Fixed navigation back to the parent study from *Studies › Study List*.
- **frontend:** Fixed the delete confirmation showing an internal identifier instead of the activity instance name.
- **frontend:** Fixed numeric input validation.
- **frontend:** Fixed an error when saving a non-standard variable with all required information provided.
- **frontend:** Fixed the sub-part inheritance notice and the copy-from-study selection lists.
- **frontend:** Fixed a race condition between study epochs and the study design cell matrix.
- **frontend:** Fixed the study activity instances list not refreshing when the Reviewed checkbox is changed.
- **frontend:** Fixed empty columns in the activity groupings history dialog.
- **frontend:** Fixed an error when selecting a study directly from a row in *Studies › Study List*.
- **frontend:** Fixed footnote letters not being shown in the detailed Schedule of Activities when activity, group or subgroup names are long.
- **frontend:** Corrected which users are permitted to edit *Library › Template Study*.
- **frontend:** Fixed duplicate item-group names appearing in the CRF tree.
- **import_sponsor_data:** Fixed importer type handling after stricter API field validation.
- **import_sponsor_data:** Fixed an error when viewing archived items by ensuring the archived library is created during import.
- **import_standards:** Fixed a query syntax error in the standards import.



## Internal / Infrastructure

- **.github:** Excluded version control internals from the secret scan.
- **.github:** Extended the secret scan to cover the files changed in a pull request.
- **.github:** Added a daily automated secret scan of the main branch.
- **.github:** Added a traceability section to the pull request template.
- **.github:** Added an automated secret scan as a required pull request check.
- **.github:** Improved change detection so continuous integration runs only the affected component checks.
- **.github:** Consolidated the continuous integration setup for the verifications component.
- **.github:** Consolidated the continuous integration setup for five components.
- **.github:** Added an aggregator job so pull requests have a single required status check.
- **.github:** Wired continuous integration for the repository components.
- **api:** Reorganised the repository's developer assistant configuration.
- **api:** Removed obsolete build pipeline definitions and helper scripts.
- **api:** Consolidated the continuous integration setup for the API.
- **api:** Fixed failing tests around study versioning.
- **api:** Improved the internal review and summarisation tooling.
- **api:** Fixed API contract-test failures after a testing-framework upgrade.
- **api:** Relocated code-list ordinal and type properties onto sponsor name records.
- **api:** Added an internal tooling skill for summarising code changes.
- **db:** Added an automated container image build for the database component.
- **db:** Updated the graph structure so CRF items reference controlled-terminology terms for data types.
- **db:** Moved creation of the archived library out of the base database setup.
- **db:** Updated the data-model diagrams and reports for the relocated code-list properties.
- **db_schema_migration:** Added a schema migration for sponsor model schemas.
- **db_schema_migration:** Removed leftover artefacts from an earlier schema migration.
- **db_schema_migration:** Updated outdated documentation links.
- **db_schema_migration:** Consolidated the continuous integration setup for the schema migration component.
- **db_schema_migration:** Cleaned up unused files in the schema migration component.
- **db_schema_migration:** Made the data-type code-list migration tolerant of environments where that code list is absent.
- **db_schema_migration:** Updated pinned dependencies to clear reported vulnerabilities.
- **db_schema_migration:** Added a data migration for the relocated code-list ordinal and type properties.
- **documentation_portal:** Wired dependency vulnerability scanning into the build so it stops on high-severity findings.
- **frontend:** Updated the application to serve its web font locally instead of from an external content delivery network.
- **frontend:** Fixed the container build so the correct web server configuration template is selected.
- **frontend:** Updated the demo build to use the API specification from the repository instead of a vendored copy.
- **frontend:** Updated frontend dependencies to clear reported vulnerabilities.
- **frontend:** Reworked CRF components to use controlled-terminology submission values for data types.
- **frontend:** Wired dependency vulnerability scanning into the build so it stops on high-severity findings.
- **frontend:** Updated the code-list screens for the relocated ordinal and type properties.
- **import_sponsor_data:** Fixed a conflicting import path in the sponsor data import.
- **import_sponsor_data:** Renamed the sponsor data import component for consistency.
- **import_sponsor_data:** Aligned the importer with the updated CRF item endpoint.
- **import_sponsor_data:** Upgraded an HTTP client dependency.
- **import_sponsor_data:** Updated test data files to cover the new data-type code lists.
- **import_standards:** Moved code-list type and ordinal properties onto the sponsor name records during standards import.
- **load_tests:** Removed an obsolete submodule reference from the load test setup.
- **repository root:** Updated the logical data model diagram for study epoch lag time.
- **repository root:** Tidied up the component README files.
- **repository root:** Added repository orientation documentation.
- **repository root:** Standardised naming of all root folders to use underscores.
- **repository root:** Standardised naming of two root folders.
- **repository root:** Added a security policy to the repository root.
- **repository root:** Reorganised the repository root folder structure.
- **system_tests:** Fixed end-to-end tests ahead of the release.
- **system_tests:** Added end-to-end tests for Other Study Attributes and Trial Summary Parameters.
- **system_tests:** Updated end-to-end test dependencies flagged by automated dependency scanning.
- **system_tests:** Migrated end-to-end tests off a deprecated test runner interface.
- **system_tests:** Fixed end-to-end tests ahead of the release.
- **system_tests:** Added end-to-end tests for study epoch lag time.
- **system_tests:** Added end-to-end tests for the background jobs interface.
- **system_tests:** Fixed end-to-end tests ahead of the release.
- **system_tests:** Fixed and refactored end-to-end tests for study data suppliers.
- **system_tests:** Fixed end-to-end tests failing after recent changes.
- **system_tests:** Automated previously manual tests for study activity instances.
- **system_tests:** Adjusted end-to-end tests for the revised study cloning behaviour.
- **system_tests:** Fixed and cleaned up end-to-end tests for the CRF tree.
- **system_tests:** Updated the end-to-end test runner to clear a reported advisory.
- **system_tests:** Fixed end-to-end tests and updated their dependencies.
- **system_tests:** Updated end-to-end test dependencies to clear reported vulnerabilities.
- **system_tests:** Refactored end-to-end test file naming and folder layout for readability.
- **system_tests:** Fixed and cleaned up end-to-end test steps for status management.
- **system_tests:** Improved the continuous integration setup for the end-to-end test suite.
- **system_tests:** Consolidated the continuous integration setup for the end-to-end test suite.
- **system_tests:** Extended the automated test suite to cover activity instances with categorical findings.
- **system_tests:** Switched the automated test suite to configure feature flags through the API.
- **system_tests:** Adjusted automated tests for recent failures.
- **system_tests:** Extended the automated test suite to cover compound dosing composition.
- **system_tests:** Refactored the study activities scenarios in the automated test suite.
- **system_tests:** Adjusted the sign-in step used by the automated test suite.
- **system_tests:** Extended the automated test suite to cover archiving of placeholder activities.
- **system_tests:** Adjusted automated tests for changes in sponsor data.
- **system_tests:** Applied test fixes across the automated suite ahead of the release.
- **system_tests:** Corrected naming and scenarios in the automated test suite.
- **system_tests:** Improved automated testing of the reporting dashboards.
- **system_tests:** Extended the automated test suite to cover editing instance attributes through the wizard.
- **verifications:** Cleaned up the verifications folder.
- **verifications:** Fixed failing data-integrity checks.
