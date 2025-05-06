"""Configuration parameters."""

import os
import urllib.parse
from os import environ

from neomodel import config as neomodel_config
from pydantic_settings import BaseSettings

_UPPERCASE_FALSE_STRINGS = ("", "FALSE", "0", "OFF", "NO", "DISABLED")
_UPPERCASE_TRUE_STRINGS = ("TRUE", "1", "ON", "YES", "Y", "ENABLED")


# Teach urljoin that Neo4j DSN URLs like bolt:// and neo4j:// semantically similar to http://
for scheme in ("bolt", "bolt+s", "neo4j", "neo4j+s"):
    urllib.parse.uses_relative.append(scheme)
    urllib.parse.uses_netloc.append(scheme)

neo4j_dsn = environ.get("NEO4J_DSN")
neomodel_config.DATABASE_URL = neo4j_dsn
db_name = environ.get("NEO4J_DATABASE")
if db_name:
    neomodel_config.DATABASE_URL = urllib.parse.urljoin(neo4j_dsn, f"/{db_name}")


class Settings(BaseSettings):
    app_name: str = "Clinical MDR API"
    neo4j_dsn: str | None
    neo4j_database: str = environ.get("NEO4J_DATABASE") or "neo4j"


settings = Settings()

NUMBER_OF_UID_DIGITS = 6

CACHE_MAX_SIZE = int(environ.get("CACHE_MAX_SIZE", 1000))
CACHE_TTL = int(environ.get("CACHE_TTL", 3600))

MAX_INT_NEO4J = 9223372036854775807
DEFAULT_PAGE_NUMBER = 1
DEFAULT_PAGE_SIZE = 10
DEFAULT_HEADER_PAGE_SIZE = 10
DEFAULT_FILTER_OPERATOR = "and"
MAX_PAGE_SIZE = 1000
PAGE_SIZE_100 = 100
NON_VISIT_NUMBER = 29999
UNSCHEDULED_VISIT_NUMBER = 29500
VISIT_0_NUMBER = 0
FIXED_WEEK_PERIOD = 7

OPERATIONAL_SOA_DOCX_TEMPLATE = "operational-soa-template.docx"
XML_STYLESHEET_DIR_PATH = "xml_stylesheets/"

SDTM_CT_CATALOGUE_NAME = "SDTM CT"
ADAM_CT_CATALOGUE_NAME = "ADAM CT"
REQUESTED_LIBRARY_NAME = "Requested"
CDISC_LIBRARY_NAME = "CDISC"
CT_UID_BOOLEAN_YES = "C49488_Y"
CT_UID_BOOLEAN_NO = "C49487_N"
CT_UID_NA_VALUE = "C48660_NA"
CT_UID_POSITIVE_INFINITY = "CTTerm_000097"
STUDY_OBJECTIVE_LEVEL_NAME = "Objective Level"
STUDY_EPOCH_TYPE_NAME = "Epoch Type"
STUDY_EPOCH_SUBTYPE_NAME = "Epoch Sub Type"
STUDY_EPOCH_EPOCH_NAME = "Epoch"
BASIC_EPOCH_NAME = "Basic"
STUDY_EPOCH_EPOCH_UID = "C99079"
STUDY_DISEASE_MILESTONE_TYPE_NAME = "Disease Milestone Type"

STUDY_VISIT_TYPE_NAME = "VisitType"
STUDY_VISIT_TYPE_INFORMATION_VISIT = "Information"
STUDY_VISIT_REPEATING_FREQUENCY = "Repeating Visit Frequency"
STUDY_VISIT_NAME = "VisitName"
STUDY_DAY_NAME = "StudyDay"
STUDY_DURATION_DAYS_NAME = "StudyDurationDays"
STUDY_WEEK_NAME = "StudyWeek"
STUDY_DURATION_WEEKS_NAME = "StudyDurationWeeks"
WEEK_IN_STUDY_NAME = "WeekInStudy"
STUDY_TIMEPOINT_NAME = "TimePoint"
STUDY_VISIT_TIMEREF_NAME = "Time Point Reference"
STUDY_ELEMENT_SUBTYPE_NAME = "Element Sub Type"
GLOBAL_ANCHOR_VISIT_NAME = "Global anchor visit"
PREVIOUS_VISIT_NAME = "Previous Visit"
ANCHOR_VISIT_IN_VISIT_GROUP = "Anchor visit in visit group"
STUDY_ENDPOINT_LEVEL_NAME = "Endpoint Level"
STUDY_ENDPOINT_TP_NAME = "StudyEndpoint"
STUDY_FIELD_PREFERRED_TIME_UNIT_NAME = "preferred_time_unit"
STUDY_FIELD_SOA_PREFERRED_TIME_UNIT_NAME = "soa_preferred_time_unit"
STUDY_FIELD_SOA_SHOW_EPOCHS = "soa_show_epochs"
STUDY_FIELD_SOA_SHOW_MILESTONES = "soa_show_milestones"
STUDY_FIELD_SOA_BASELINE_AS_TIME_ZERO = "baseline_as_time_zero"
STUDY_SOA_PREFERENCES_FIELDS = (
    # can't be a set: Neomodel's transform_operator_to_filter is strict for IN operator only accepts list or tuple
    STUDY_FIELD_SOA_SHOW_EPOCHS,
    STUDY_FIELD_SOA_SHOW_MILESTONES,
    STUDY_FIELD_SOA_BASELINE_AS_TIME_ZERO,
)

STUDY_VISIT_CONTACT_MODE_NAME = "Visit Contact Mode"
STUDY_VISIT_EPOCH_ALLOCATION_NAME = "Epoch Allocation"
DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"
OPERATOR_PARAMETER_NAME = "Operator"

DAY_UNIT_NAME = "day"
DAYS_UNIT_NAME = "days"
# conversion to second which is master unit for time units
DAY_UNIT_CONVERSION_FACTOR_TO_MASTER = 86400
WEEK_UNIT_NAME = "week"
# conversion to second which is master unit for time units
WEEK_UNIT_CONVERSION_FACTOR_TO_MASTER = 604800
STUDY_TIME_UNIT_SUBSET = "Study Time"

DEFAULT_STUDY_FIELD_CONFIG_FILE = (
    "clinical_mdr_api/tests/data/study_fields_modified.csv"
)

LIBRARY_SUBSTANCES_CODELIST_NAME = "UNII"

SPONSOR_MODEL_PREFIX = "mastermodel"
SPONSOR_MODEL_VERSION_NUMBER_PREFIX = "NN"

APPINSIGHTS_CONNECTION = environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")

OPENAPI_SCHEMA_API_ROOT_PATH = environ.get("UVICORN_ROOT_PATH") or "/"

TRACING_DISABLED = environ.get("TRACING_DISABLED", "").upper().strip() not in (
    _UPPERCASE_FALSE_STRINGS
)
TRACING_METRICS_HEADER = environ.get("TRACING_METRICS_HEADER", "").upper().strip() in (
    _UPPERCASE_TRUE_STRINGS
)

TRACE_REQUEST_BODY = environ.get("TRACE_REQUEST_BODY", "").upper().strip() in (
    _UPPERCASE_TRUE_STRINGS
)
TRACE_REQUEST_BODY_MIN_STATUS_CODE = int(
    environ.get("TRACE_REQUEST_BODY_MIN_STATUS_CODE", "400")
)
TRACE_REQUEST_BODY_TRUNCATE_BYTES = int(
    environ.get("TRACE_REQUEST_BODY_TRUNCATE_BYTES", "2048")
)
TRACE_QUERY_MAX_LEN = int(environ.get("TRACE_QUERY_MAX_LEN", "4000"))


# Absolute path of application root directory
APP_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

MS_GRAPH_GROUPS_QUERY = environ.get("MS_GRAPH_GROUPS_QUERY")
MS_GRAPH_INTEGRATION_ENABLED = environ.get(
    "MS_GRAPH_INTEGRATION_ENABLED", ""
).upper().strip() not in (_UPPERCASE_FALSE_STRINGS)

ALLOW_ORIGIN_REGEX = environ.get("ALLOW_ORIGIN_REGEX")
ALLOW_CREDENTIALS = environ.get("ALLOW_CREDENTIALS", "true").upper().strip() not in (
    _UPPERCASE_FALSE_STRINGS
)
ALLOW_METHODS = environ.get("ALLOW_METHODS", "*").split(",")
ALLOW_HEADERS = environ.get("ALLOW_HEADERS", "*").split(",")
SLOW_QUERY_TIME_SECS = 1
