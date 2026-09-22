"""Configuration parameters."""

import os
import string
from typing import Any, Final, Literal
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings class for the application.

    This class is responsible for:
        - providing a single point of access to all configuration parameters.
        - automatically loading configuration parameters from `.env` (as defined in region `.env variables`).
        - defining parameters that shouldn't be defined in `.env` but still available in the code (as defined in region `non-.env variables`).
        - providing type validation for the parameters.
        - providing default values for the parameters.

    Naming conventions:
        - All parameters must be in `snake_case`.
        - Parameters loaded from `.env` file that need to be post-processed must be in `UPPER_CASE` and prefixed with `ENV_`
        and a corresponding property attribute must be defined in `snake_case` with the original name (i.e. without the prefix).
        See `allow_methods` and `allow_headers` for example.
    """

    app_root_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

    # region .env variables
    model_config = SettingsConfigDict(
        env_file=f"{app_root_dir}/.env",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator(
        "allow_credentials",
        "oauth_enabled",
        "ms_graph_integration_enabled",
        "tracing_enabled",
        "tracing_metrics_header",
        "trace_request_body",
        mode="before",
    )
    @classmethod
    def cast_to_bool(cls, value: str | bool) -> bool:
        if isinstance(value, bool):
            return value

        return value.casefold().strip() in ("true", "1", "on", "yes", "y", "enabled")

    # Application Configuration
    app_name: str = "OpenStudyBuilder API"
    openapi_schema_api_root_path: str = Field(default="/", alias="UVICORN_ROOT_PATH")
    app_debug: bool = False
    color_logs: bool = Field(
        default=True,
        description="Whether to color log messages based on severity when logging to console",
    )
    uid: int = 1000
    number_of_uid_digits: int = 6

    # Database Configuration
    neo4j_database: str | None = None  # deprecated, include database name in NEO4J_DSN
    neo4j_dsn: str
    neo4j_connection_lifetime: float = 29 * 60
    neo4j_liveness_check_timeout: float = 5 * 60
    soft_cardinality_check: bool = (
        True  # This will prevent cardinality violations from being raised as errors.
    )

    # Cache Configuration
    cache_max_size: int = 1000
    cache_ttl: int = 3600

    # Security & CORS
    allow_origin_regex: str | None = None
    allow_credentials: bool = True

    ENV_ALLOW_METHODS: str = Field(default="*", alias="ALLOW_METHODS")

    @property
    def allow_methods(self) -> list[str]:
        return self.ENV_ALLOW_METHODS.split(",")

    ENV_ALLOW_HEADERS: str = Field(default="*", alias="ALLOW_HEADERS")

    @property
    def allow_headers(self) -> list[str]:
        return self.ENV_ALLOW_HEADERS.split(",")

    # Pagination Configuration
    default_page_number: int = 1
    default_page_number_consumer_api: int = 1
    default_page_size: int = 10
    default_header_page_size: int = 10
    default_filter_operator: str = "and"
    max_page_size: int = 1000
    max_page_number: int = 1000000000
    page_size_100: int = 100
    consumer_api_audit_trail_max_rows: int = 10000

    # Performance
    slow_query_duration: int = 1

    # Fuzzy / full text search configuration
    fuzziness_level: float = 0.8

    # Tracing & Monitoring
    uvicorn_log_config: str = ""
    tracing_enabled: bool = True
    tracing_metrics_header: bool = False
    trace_request_body: bool = False
    trace_request_body_min_status_code: int = 400
    trace_request_body_truncate_bytes: int = 2048
    trace_query_max_len: int = 4000
    traceback_max_entries: int = Field(
        default=15,
        description="Limit tracebacks to the N innermost/latest frames",
        ge=0,
    )
    appinsights_connection: str = Field(
        default="", alias="APPLICATIONINSIGHTS_CONNECTION_STRING"
    )
    zipkin_host: str = Field(
        default="",
        description="Enable tracing to Zipkin, hostname or IP of the Zipkin service.",
    )
    zipkin_port: int = 9411
    zipkin_endpoint: str = "/api/v2/spans"
    zipkin_protocol: str = "http"

    # OAuth & Authentication
    oauth_enabled: bool = True
    oauth_rbac_enabled: bool = True
    oauth_metadata_url: str = ""
    oauth_api_app_id: str = ""
    oauth_api_app_secret: SecretStr = SecretStr("")
    dummy_user_id: str = "unknown-user"

    ENV_OAUTH_API_APP_ID_URI: str = Field(default="", alias="OAUTH_API_APP_ID_URI")

    @property
    def oauth_api_app_id_uri(self) -> str:
        return self.ENV_OAUTH_API_APP_ID_URI or f"api://{self.oauth_api_app_id}"

    oauth_swagger_app_id: str = ""
    oauth_ui_app_id: str = ""

    # Testing & Schemathesis
    schemathesis_study_uid: str = ""
    schemathesis_hooks: str = ""

    # Third-party Integrations
    ms_graph_integration_enabled: bool = False
    ms_graph_groups_query: str = "``"

    # API Base URLs
    api_base_url: str = Field(
        default="http://localhost:8000",
        alias="API_BASE_URL",
        description="Base URL for the main API (used for cross-API communications)",
    )

    @field_validator("api_base_url", mode="before")
    @classmethod
    def validate_api_base_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme and parsed.scheme not in ("http", "https"):
            raise ValueError(
                f"api_base_url must use http or https scheme, got: {parsed.scheme}"
            )
        return value

    # gzip API responses (Content-Encoding: gzip)
    gzip_response_min_size: int = Field(
        default=500,
        ge=0,
        description="Minimum response size in bytes to gzip compress, or 0 to disable.",
    )
    gzip_level: int = Field(
        default=5, ge=0, le=9, description="gzip compression level (0 to 9)"
    )

    # endregion

    # region non-.env variables
    templates_directory: str = "templates/"
    jwt_leeway_seconds: int = 10

    @property
    def our_scopes(self) -> dict[str, str]:
        return {
            f"{self.oauth_api_app_id_uri}/API.call": "Make calls to the API",
        }

    @property
    def swagger_ui_init_oauth(self) -> dict[str, Any] | None:
        return (
            {
                "usePkceWithAuthorizationCodeGrant": True,
                "clientId": self.oauth_swagger_app_id or self.oauth_api_app_id,
                "scopes": (
                    ["openid", "profile", "email", "offline_access"]
                    + list(self.our_scopes.keys())
                ),
                "additionalQueryStringParams": {
                    "response_mode": "fragment",
                },
            }
            if self.oauth_enabled
            else None
        )

    max_int_neo4j: int = 9223372036854775807

    non_visit_number: int = 29999
    non_visit_name: str = "Non-visit"
    non_visit_start_rule: str = "Non-visit"
    unscheduled_visit_number: int = 29500
    unscheduled_visit_name: str = "Unscheduled"
    unscheduled_visit_start_rule: str = "Unplanned unscheduled"
    visit_0_number: int = 0
    fixed_week_period: int = 7

    operational_soa_docx_template: str = "operational-soa-template.docx"
    xml_stylesheet_dir_path: str = "xml_stylesheets/"

    sdtm_ct_catalogue_name: str = "SDTM CT"
    adam_ct_catalogue_name: str = "ADAM CT"
    ddf_ct_catalogue_name: str = "DDF CT"
    archived_library_name: str = "Archived"
    sponsor_library_name: str = "Sponsor"
    requested_library_name: str = "Requested"
    cdisc_library_name: str = "CDISC"
    # All editable library names available in the database and for the consumer API Library filter
    # Add additional sponsor library names here to make them selectable
    editable_library_names: list[str] = [sponsor_library_name]
    ct_uid_boolean_yes: str = "C49488"
    ct_uid_boolean_no: str = "C49487"
    ct_uid_boolean_codelist: str = "C66742"
    ct_uid_na_value: str = "C48660"
    ct_concept_id_criteria_type_inclusion: str = "C25532"
    ct_concept_id_criteria_type_exclusion: str = "C25370"
    ct_submval_positive_infinity: str = "PINF"
    study_objective_level_name: str = "Objective Level"
    study_epoch_type_name: str = "Epoch Type"
    study_epoch_subtype_name: str = "Epoch Sub Type"
    study_epoch_epoch_name: str = "Epoch"
    basic_epoch_name: str = "Basic"
    study_epoch_epoch_uid: str = "C99079"
    study_disease_milestone_type_name: str = "Disease Milestone Type"

    special_visit_letters: str = string.ascii_uppercase
    special_visit_max_number: int = len(string.ascii_uppercase)
    study_visit_type_name: str = "VisitType"
    study_visit_type_information_visit: str = "Information"
    study_visit_repeating_frequency: str = "Repeating Visit Frequency"
    study_visit_type_early_discontinuation_visit: str = "Early discontinuation"
    study_visit_name: str = "VisitName"
    study_day_name: str = "StudyDay"
    study_duration_days_name: str = "StudyDurationDays"
    study_week_name: str = "StudyWeek"
    study_duration_weeks_name: str = "StudyDurationWeeks"
    week_in_study_name: str = "WeekInStudy"
    study_timepoint_name: str = "TimePoint"
    study_visit_timeref_name: str = "Time Point Reference"
    study_element_subtype_name: str = "Element Sub Type"
    global_anchor_visit_name: str = "Global anchor visit"
    previous_visit_name: str = "Previous Visit"
    anchor_visit_in_visit_group: str = "Anchor visit in visit group"
    study_endpoint_level_name: str = "Endpoint Level"
    study_endpoint_tp_name: str = "StudyEndpoint"
    study_field_preferred_time_unit_name: str = "preferred_time_unit"
    study_field_soa_preferred_time_unit_name: str = "soa_preferred_time_unit"
    study_field_soa_show_epochs: str = "soa_show_epochs"
    study_field_soa_show_milestones: str = "soa_show_milestones"
    study_field_soa_show_all_visits_lab_table: str = "soa_show_all_visits_lab_table"
    study_field_soa_baseline_as_time_zero: str = "baseline_as_time_zero"
    study_soa_preferences_fields: tuple[str, str, str, str] = (
        # can't be a set: Neomodel's transform_operator_to_filter is strict for IN operator only accepts list or tuple
        study_field_soa_show_epochs,
        study_field_soa_show_milestones,
        study_field_soa_baseline_as_time_zero,
        study_field_soa_show_all_visits_lab_table,
    )
    study_soa_split_uids_field: str = "soa_split_uids"

    soa_insert_space_after_commas_length: int = 8

    study_visit_contact_mode_name: str = "Visit Contact Mode"
    study_visit_epoch_allocation_name: str = "Epoch Allocation"
    date_time_format: str = "%Y-%m-%dT%H:%M:%S.%f%z"
    operator_parameter_name: str = "Operator"

    day_unit_name: str = "day"
    days_unit_name: str = "days"
    # conversion to second which is master unit for time units
    day_unit_conversion_factor_to_master: int = 86400
    week_unit_name: str = "week"
    # conversion to second which is master unit for time units
    week_unit_conversion_factor_to_master: int = 604800
    study_time_unit_subset: str = "Study Time"

    library_substances_codelist_name: str = "UNII"

    sponsor_model_prefix: str = "mastermodel"
    sponsor_model_version_number_prefix: str = "NN"

    # Codelist submission values
    ddf_data_type_cl_submval: str = "DATATYPE"
    ddf_odm_data_type_cl_submval: str = "CODMDT"
    unit_cl_submval: str = "UNIT"
    unit_dimension_cl_submval: str = "UNITDIM"
    unit_subset_cl_submval: str = "UNITSUBS"
    syntax_objective_category_cl_submval: str = "OBJTCAT"
    syntax_endpoint_category_cl_submval: str = "ENDPCAT"
    syntax_endpoint_sub_category_cl_submval: str = "ENDPSCAT"
    syntax_criteria_category_cl_submval: str = "CRITCAT"
    syntax_criteria_sub_category_cl_submval: str = "CRITSCAT"
    syntax_criteria_type_cl_submval: str = "CRITRTP"
    syntax_footnote_type_cl_submval: str = "FTNTTP"
    study_arm_type_cl_submval: str = "ARMTTP"
    study_epoch_cl_submval: str = "EPOCH"
    study_epoch_type_cl_submval: str = "EPOCHTP"
    study_epoch_subtype_cl_submval: str = "EPOCHSTP"
    null_flavor_cl_submval: str = "NULLFLVR"
    data_type_cl_submval: str = "SEMTCDT"
    ts_parmcd_codelist_uid: str = "C66738"
    ts_parm_codelist_uid: str = "C67152"
    study_other_attributes_page_reference: str = "/study_properties/other_attributes"
    study_visit_type_cl_submval: str = "TIMELB"
    repeating_visit_frequency_cl_submval: str = "REPEATING_VISIT_FREQUENCY"
    study_visit_contact_mode_cl_submval: str = "VISCNTMD"
    epoch_allocation_cl_submval: str = "EPCHALLC"
    stdm_domain_cl_submval: str = "DOMAIN"
    stdm_role_cl_submval: str = "ROLE"
    study_endpoint_level_cl_submval: str = "ENDPLEVL"
    study_endpoint_sublevel_cl_submval: str = "ENDPSBLV"
    study_element_type_cl_submval: str = "ELEMTP"
    study_element_subtype_cl_submval: str = "ELEMSTP"
    study_objective_level_cl_submval: str = "OBJTLEVL"
    type_of_treatment_cl_submval: str = "TPOFTRT"
    delivery_device_cl_submval: str = "DLVRDVC"
    compound_dispensed_in_cl_submval: str = "COMPDISP"
    route_of_administration_cl_submval: str = "ROUTE"
    dosage_form_cl_submval: str = "FRM"
    dose_frequency_cl_submval: str = "FREQ"
    time_ref_cl_submval: str = "TIMEREF"
    disease_milestone_cl_submval: str = "MIDSTYPE"
    flowchart_group_cl_submval: str = "FLWCRTGRP"
    data_supplier_type_cl_submval: str = "DATA_SUPPLIER_TYPE"
    origin_source_cl_submval: str = "ORIGINS"
    origin_type_cl_submval: str = "ORIGINT"
    reason_for_lock_cl_submval: str = "RSNFL"
    reason_for_unlock_cl_submval: str = "RSNFUL"
    final_protocol_term_submval: str = "FINAL_PROTOCOL"

    # endregion


settings = Settings()  # type: ignore[call-arg]

# Validation mode constants for database integrity checks
VALIDATION_MODE_STRICT: Final[Literal["strict"]] = "strict"
VALIDATION_MODE_WARNING: Final[Literal["warning"]] = "warning"
VALIDATION_MODE = Literal["strict", "warning"]  # pylint: disable=invalid-name
