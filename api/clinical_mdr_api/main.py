"""Application main file."""

# Placed at the top to ensure logging is configured before anything else is loaded
from common.config import settings
from common.database import configure_app_database
from common.logger import default_logging_config

default_logging_config()

configure_app_database(settings.neo4j_dsn)


import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from neomodel import db as neomodel_db
from starlette.exceptions import HTTPException as StarletteHTTPException

from clinical_mdr_api.utils.api_version import get_api_version
from common.app_factory import (
    build_middlewares,
    build_openapi_func,
    register_exception_handlers,
)
from common.auth.discovery import reconfigure_with_openid_discovery
from common.database import log_rbac_guard_result

log = logging.getLogger(__name__)


# Middlewares — no exclude_clients for the main app (unlike the other three apps)
middlewares = build_middlewares(
    service_name="clinical-mdr-api", tracing_exclude_clients=None
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.oauth_enabled:
        # Reconfiguring Swagger UI settings with OpenID Connect discovery
        await reconfigure_with_openid_discovery()

    try:
        # If the `mdr` role from db/init_neo4j.py is active, this connection cannot
        # see :CDISCStaging nodes at all — a non-zero count means either Community
        # edition or the roles are not provisioned yet, and the app must keep working
        # either way (this is defence in depth, not the isolation mechanism).
        rows, _ = neomodel_db.cypher_query("MATCH (n:CDISCStaging) RETURN count(n)")
        log_rbac_guard_result(
            "mdr connection cannot see :CDISCStaging", rows[0][0] == 0
        )
    except Exception:  # pylint: disable=broad-except
        log.exception("Could not check the RBAC guard status at startup")

    yield


app = FastAPI(
    title=settings.app_name,
    middleware=middlewares,
    lifespan=lifespan,
    swagger_ui_init_oauth=settings.swagger_ui_init_oauth,
    version=get_api_version(),
    swagger_ui_parameters={"docExpansion": "none"},
    description="""
## NOTICE

This license information is applicable to the swagger documentation of the clinical-mdr-api, that is the openapi.json.

## License Terms (MIT)

Copyright (C) 2025 Novo Nordisk A/S, Danish company registration no. 24256790

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Licenses and Acknowledgements for Incorporated Software

This component contains software licensed under different licenses when compiled, please refer to the third-party-licenses.md file for further information and full license texts.

## Authentication

Supports OAuth2 [Authorization Code Flow](https://datatracker.ietf.org/doc/html/rfc6749#section-4.1),
at paths described in the OpenID Connect Discovery metadata document (whose URL is defined by the `OAUTH_METADATA_URL` environment variable).

Microsoft Identity Platform documentation can be read 
([here](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)).

Authentication can be turned off with `OAUTH_ENABLED=false` environment variable. 

When authentication is turned on, all requests to protected API endpoints must provide a valid bearer (JWT) token inside the `Authorization` http header. 
""",
    # Putting False here as pydantic v2 separates input and output schemas if it sees any differences in usage the same model between GET and POST/PUT/PATCH flow
    # but in this case it generates totally the same -Input and -Output models which duplicates model schema in openapi documentation.
    # Model schema duplication causes issues for open-source users.
    # For more information please lookup here https://fastapi.tiangolo.com/how-to/separate-openapi-schemas/
    separate_input_output_schemas=False,
)


register_exception_handlers(
    app,
    # StarletteHTTPException (not fastapi.HTTPException) so request-body-parsing errors
    # are also caught — see the original handler docstring in consumer_api for details.
    http_exception_class=StarletteHTTPException,
    include_value_error=True,
    validation_error_include_headers=True,
)


# Late import of routers, because they do run code on import, and we want monkey-patching like tracing to work

from clinical_mdr_api import routers

# Include routers here
app.include_router(routers.system_router, tags=["System"])
app.include_router(
    routers.preferences_router, prefix="/user-preferences", tags=["User Preferences"]
)

app.include_router(
    routers.feature_flags_router,
    prefix="/feature-flags",
    tags=["Feature Flags"],
)
app.include_router(
    routers.data_completeness_tags_router,
    prefix="/data-completeness-tags",
    tags=["Data Completeness Tags"],
)
app.include_router(
    routers.notifications_router,
    prefix="/notifications",
    tags=["Notifications"],
)
app.include_router(routers.iso_router, prefix="/iso", tags=["ISO Standards"])
app.include_router(routers.jobs_router, prefix="/jobs", tags=["Jobs"])
app.include_router(
    routers.odm_study_events_router,
    prefix="/odms/study-events",
    tags=["ODM Study Events"],
)
app.include_router(routers.odm_forms_router, prefix="/odms/forms", tags=["ODM Forms"])
app.include_router(
    routers.odm_item_groups_router,
    prefix="/odms/item-groups",
    tags=["ODM Item Groups"],
)
app.include_router(routers.odm_item_router, prefix="/odms/items", tags=["ODM Items"])
app.include_router(
    routers.odm_conditions_router,
    prefix="/odms/conditions",
    tags=["ODM Conditions"],
)
app.include_router(
    routers.odm_methods_router,
    prefix="/odms/methods",
    tags=["ODM Methods"],
)
app.include_router(
    routers.odm_vendor_namespace_router,
    prefix="/odms/vendor-namespaces",
    tags=["ODM Vendor Namespaces"],
)
app.include_router(
    routers.odm_vendor_attribute_router,
    prefix="/odms/vendor-attributes",
    tags=["ODM Vendor Attributes"],
)
app.include_router(
    routers.odm_vendor_element_router,
    prefix="/odms/vendor-elements",
    tags=["ODM Vendor Elements"],
)
app.include_router(
    routers.odm_metadata_router,
    prefix="/odms/metadata",
    tags=["ODM Metadata"],
)
app.include_router(
    routers.activity_instruction_templates_router,
    prefix="/activity-instruction-templates",
    tags=["Activity Instruction Templates"],
)
app.include_router(
    routers.activity_instructions_router,
    prefix="/activity-instructions",
    tags=["Activity Instructions"],
)
app.include_router(
    routers.activity_instruction_pre_instances_router,
    prefix="/activity-instruction-pre-instances",
    tags=["Activity Instruction Pre-Instances"],
)
app.include_router(
    routers.footnote_templates_router,
    prefix="/footnote-templates",
    tags=["Footnote Templates"],
)
app.include_router(routers.footnote_router, prefix="/footnotes", tags=["Footnotes"])
app.include_router(
    routers.footnote_pre_instances_router,
    prefix="/footnote-pre-instances",
    tags=["Footnote Pre-Instances"],
)
app.include_router(
    routers.criteria_templates_router,
    prefix="/criteria-templates",
    tags=["Criteria Templates"],
)
app.include_router(
    routers.criteria_pre_instances_router,
    prefix="/criteria-pre-instances",
    tags=["Criteria Pre-Instances"],
)
app.include_router(routers.criteria_router, prefix="/criteria", tags=["Criteria"])
app.include_router(
    routers.objective_templates_router,
    prefix="/objective-templates",
    tags=["Objective Templates"],
)
app.include_router(
    routers.objective_pre_instances_router,
    prefix="/objective-pre-instances",
    tags=["Objective Pre-Instances"],
)
app.include_router(routers.objectives_router, prefix="/objectives", tags=["Objectives"])
app.include_router(
    routers.endpoint_templates_router,
    prefix="/endpoint-templates",
    tags=["Endpoint Templates"],
)
app.include_router(
    routers.endpoint_pre_instances_router,
    prefix="/endpoint-pre-instances",
    tags=["Endpoint Pre-Instances"],
)
app.include_router(routers.endpoints_router, prefix="/endpoints", tags=["Endpoints"])
app.include_router(
    routers.timeframe_templates_router,
    prefix="/timeframe-templates",
    tags=["Timeframe templates"],
)
app.include_router(routers.timeframes_router, prefix="/timeframes", tags=["Timeframes"])
app.include_router(routers.libraries_router, prefix="/libraries", tags=["Libraries"])
app.include_router(routers.ct_catalogues_router, prefix="/ct", tags=["CT Catalogues"])
app.include_router(routers.ct_packages_router, prefix="/ct", tags=["CT Packages"])
app.include_router(routers.ct_codelists_router, prefix="/ct", tags=["CT Codelists"])
app.include_router(
    routers.ct_codelist_attributes_router, prefix="/ct", tags=["CT Codelists"]
)
app.include_router(
    routers.ct_codelist_names_router, prefix="/ct", tags=["CT Codelists"]
)
app.include_router(routers.ct_terms_router, prefix="/ct", tags=["CT Terms"])
app.include_router(routers.ct_term_attributes_router, prefix="/ct", tags=["CT Terms"])
app.include_router(routers.ct_term_names_router, prefix="/ct", tags=["CT Terms"])
app.include_router(routers.ct_stats_router, prefix="/ct", tags=["CT Stats"])
app.include_router(routers.meta_study_fields_router, tags=["Meta Study Fields"])
app.include_router(
    routers.dictionary_codelists_router,
    prefix="/dictionaries",
    tags=["Dictionary Codelists"],
)
app.include_router(
    routers.dictionary_terms_router, prefix="/dictionaries", tags=["Dictionary Terms"]
)
app.include_router(
    routers.template_parameters_router,
    prefix="/template-parameters",
    tags=["Template Parameters"],
)
app.include_router(
    routers.activity_instances_router,
    prefix="/concepts/activities/activity-instances",
    tags=["Activity Instances"],
)
app.include_router(
    routers.activity_instance_classes_router,
    prefix="/activity-instance-classes",
    tags=["Activity Instance Classes"],
)
app.include_router(
    routers.activity_item_classes_router,
    prefix="/activity-item-classes",
    tags=["Activity Item Classes"],
)
app.include_router(routers.compounds_router, prefix="/concepts", tags=["Compounds"])
app.include_router(
    routers.active_substances_router, prefix="/concepts", tags=["Active Substances"]
)
app.include_router(
    routers.pharmaceutical_products_router,
    prefix="/concepts",
    tags=["Pharmaceutical Products"],
)
app.include_router(
    routers.medicinal_products_router,
    prefix="/concepts",
    tags=["Medicinal Products"],
)
app.include_router(
    routers.compound_aliases_router, prefix="/concepts", tags=["Compound Aliases"]
)
app.include_router(
    routers.activities_router,
    prefix="/concepts/activities",
    tags=["Activities"],
)
app.include_router(
    routers.activity_subgroups_router,
    prefix="/concepts/activities",
    tags=["Activity Subgroups"],
)
app.include_router(
    routers.activity_groups_router,
    prefix="/concepts/activities",
    tags=["Activity Groups"],
)
app.include_router(
    routers.numeric_values_router,
    prefix="/concepts/numeric-values",
    tags=["Numeric Values"],
)
app.include_router(
    routers.numeric_values_with_unit_router,
    prefix="/concepts/numeric-values-with-unit",
    tags=["Numeric Values With Unit"],
)
app.include_router(
    routers.text_values_router, prefix="/concepts/text-values", tags=["Text Values"]
)
app.include_router(
    routers.visit_names_router, prefix="/concepts/visit-names", tags=["Visit Names"]
)
app.include_router(
    routers.study_days_router, prefix="/concepts/study-days", tags=["Study Days"]
)
app.include_router(
    routers.study_weeks_router, prefix="/concepts/study-weeks", tags=["Study Weeks"]
)
app.include_router(
    routers.study_duration_days_router,
    prefix="/concepts/study-duration-days",
    tags=["Study Duration Days"],
)
app.include_router(
    routers.study_duration_weeks_router,
    prefix="/concepts/study-duration-weeks",
    tags=["Study Duration Weeks"],
)
app.include_router(
    routers.time_points_router, prefix="/concepts/time-points", tags=["Time Points"]
)
app.include_router(
    routers.lag_times_router, prefix="/concepts/lag-times", tags=["Lag Times"]
)
app.include_router(routers.projects_router, prefix="/projects", tags=["Projects"])
app.include_router(
    routers.clinical_programmes_router,
    prefix="/clinical-programmes",
    tags=["Clinical Programmes"],
)
app.include_router(routers.admin_router, prefix="/admin", tags=["Admin"])
app.include_router(routers.brands_router, prefix="/brands", tags=["Brands"])
app.include_router(routers.comments_router, prefix="", tags=["Comments"])

app.include_router(routers.studies_router, prefix="/studies", tags=["Studies"])

app.include_router(routers.study_router, prefix="", tags=["Study Selections"])
app.include_router(
    routers.unit_definition_router,
    prefix="/concepts/unit-definitions",
    tags=["Unit Definitions"],
)
app.include_router(
    routers.metadata_router, prefix="/listings", tags=["Listing Metadata"]
)
app.include_router(
    routers.listing_router, prefix="/listings", tags=["Listing Legacy CDW MMA"]
)
app.include_router(
    routers.sdtm_listing_router, prefix="/listings", tags=["SDTM Study Design Listings"]
)
app.include_router(
    routers.adam_listing_router, prefix="/listings", tags=["ADaM Study Design Listings"]
)
app.include_router(
    routers.study_listing_router, prefix="/listings", tags=["Study Design Listings"]
)
app.include_router(
    routers.data_models_router,
    prefix="/standards",
    tags=["Data models"],
)
app.include_router(
    routers.data_model_igs_router,
    prefix="/standards",
    tags=["Data model implementation guides"],
)
app.include_router(
    routers.sponsor_models_router,
    prefix="/standards/sponsor-models/models",
    tags=["Sponsor models"],
)
app.include_router(
    routers.sponsor_model_schemas_router,
    prefix="/standards/sponsor-models/schema",
    tags=["Sponsor model schemas"],
)
app.include_router(
    routers.sponsor_model_datasets_router,
    prefix="/standards/sponsor-models/datasets",
    tags=["Sponsor model datasets"],
)
app.include_router(
    routers.sponsor_model_dataset_variables_router,
    prefix="/standards/sponsor-models/dataset-variables",
    tags=["Sponsor model variables"],
)
app.include_router(
    routers.dataset_classes_router,
    prefix="/standards",
    tags=["Dataset classes"],
)
app.include_router(
    routers.datasets_router,
    prefix="/standards",
    tags=["Datasets"],
)
app.include_router(
    routers.dataset_scenarios_router,
    prefix="/standards",
    tags=["Dataset scenarios"],
)
app.include_router(
    routers.class_variables_router,
    prefix="/standards",
    tags=["Class variables"],
)
app.include_router(
    routers.dataset_variables_router,
    prefix="/standards",
    tags=["Dataset variables"],
)
app.include_router(
    routers.integrations.msgraph.router,
    prefix="/integrations/ms-graph",
    tags=["MS Graph API integrations"],
)
app.include_router(routers.ddf_router, prefix="/usdm/v4", tags=["USDM endpoints"])
app.include_router(
    routers.data_supplier_rules_router,
    prefix="/data-suppliers/rules",
    tags=["Data Supplier Rules"],
)
app.include_router(
    routers.data_suppliers_router, prefix="/data-suppliers", tags=["Data Suppliers"]
)

# Mount the Standards Import API's routers under /standards-import so both halves of
# the database (MDR + staging) are served by a single process. The import is inside the
# `if` block so `standards_import.main` is never imported here — that module calls
# `configure_database` at module level, which would conflict with this app's own call.
if settings.standards_import_enabled:
    from standards_import.routers import (  # pylint: disable=wrong-import-position
        codelists as si_codelists,
        effective_dates as si_effective_dates,
        imports as si_imports,
        inconsistencies as si_inconsistencies,
        jobs as si_jobs,
        package_files as si_package_files,
        resolution_rules as si_resolution_rules,
        sponsor_impact as si_sponsor_impact,
        type_descriptions as si_type_descriptions,
    )

    app.include_router(si_package_files.router, prefix="/standards-import")
    app.include_router(si_package_files.discovery_router, prefix="/standards-import")
    app.include_router(si_package_files.pairings_router, prefix="/standards-import")
    app.include_router(si_package_files.changelog_router, prefix="/standards-import")
    app.include_router(si_effective_dates.router, prefix="/standards-import")
    app.include_router(si_sponsor_impact.router, prefix="/standards-import")
    app.include_router(si_imports.router, prefix="/standards-import")
    app.include_router(si_inconsistencies.router, prefix="/standards-import")
    app.include_router(si_inconsistencies.options_router, prefix="/standards-import")
    app.include_router(si_resolution_rules.router, prefix="/standards-import")
    app.include_router(si_jobs.router, prefix="/standards-import")
    app.include_router(si_type_descriptions.router, prefix="/standards-import")
    app.include_router(si_codelists.router, prefix="/standards-import")


# `custom_openapi` is kept as a module-level name for backwards compatibility — the
# OpenAPI generation script (`generate_openapi_json.py`) imports it by name.
custom_openapi = build_openapi_func(
    app,
    remove_422=True,
    separate_input_output_schemas=app.separate_input_output_schemas,
)
setattr(app, "openapi", custom_openapi)
