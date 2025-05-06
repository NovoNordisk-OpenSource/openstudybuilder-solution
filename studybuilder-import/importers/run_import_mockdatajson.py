import copy
import json
import os
from functools import lru_cache
from os import environ

from .functions.utils import load_env
from .utils import import_templates
from .utils.api_bindings import (
    CODELIST_ARM_TYPE,
    CODELIST_COMPOUND_DISPENSED_IN,
    CODELIST_CONTROL_TYPE,
    CODELIST_CRITERIA_CATEGORY,
    CODELIST_CRITERIA_SUBCATEGORY,
    CODELIST_CRITERIA_TYPE,
    CODELIST_DELIVERY_DEVICE,
    CODELIST_DOSAGE_FORM,
    CODELIST_ELEMENT_SUBTYPE,
    CODELIST_ELEMENT_TYPE,
    CODELIST_ENDPOINT_CATEGORY,
    CODELIST_ENDPOINT_LEVEL,
    CODELIST_ENDPOINT_SUBLEVEL,
    CODELIST_EPOCH_SUBTYPE,
    CODELIST_FLOWCHART_GROUP,
    CODELIST_FOOTNOTE_TYPE,
    CODELIST_INTERVENTION_MODEL,
    CODELIST_INTERVENTION_TYPE,
    CODELIST_NULL_FLAVOR,
    CODELIST_OBJECTIVE_CATEGORY,
    CODELIST_OBJECTIVE_LEVEL,
    CODELIST_ROUTE_OF_ADMINISTRATION,
    CODELIST_SEX_OF_PARTICIPANTS,
    CODELIST_STUDY_TYPE,
    CODELIST_TIMEPOINT_REFERENCE,
    CODELIST_TRIAL_BLINDING_SCHEMA,
    CODELIST_TRIAL_INDICATION_TYPE,
    CODELIST_TRIAL_PHASE,
    CODELIST_TRIAL_TYPE,
    CODELIST_TYPE_OF_TREATMENT,
    CODELIST_UNIT,
    CODELIST_UNIT_DIMENSION,
    CODELIST_UNIT_SUBSET,
    CODELIST_VISIT_CONTACT_MODE,
    CODELIST_VISIT_TYPE,
    UNIT_SUBSET_AGE,
    UNIT_SUBSET_DOSE,
    UNIT_SUBSET_STUDY_TIME,
)
from .utils.importer import BaseImporter, open_file
from .utils.metrics import Metrics

metrics = Metrics()

API_HEADERS = {"Accept": "application/json"}

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False").lower() == "true"
API_BASE_URL = load_env("API_BASE_URL")

MDR_MIGRATION_FROM_SAME_ENV = environ.get("MDR_MIGRATION_FROM_SAME_ENV", "False").lower() == "true"

IMPORT_PROJECTS = load_env("IMPORT_PROJECTS")
MDR_MIGRATION_EXPORTED_PROGRAMMES = (
    environ.get("MDR_MIGRATION_EXPORTED_PROGRAMMES", "True").lower() == "true"
)
MDR_MIGRATION_EXPORTED_BRANDS = (
    environ.get("MDR_MIGRATION_EXPORTED_BRANDS", "True").lower() == "true"
)
MDR_MIGRATION_EXPORTED_ACTIVITIES = (
    environ.get("MDR_MIGRATION_EXPORTED_ACTIVITIES", "True").lower() == "true"
)
MDR_MIGRATION_EXPORTED_ACTIVITY_INSTANCES = (
    environ.get("MDR_MIGRATION_EXPORTED_ACTIVITY_INSTANCES", "True").lower() == "true"
)
MDR_MIGRATION_EXPORTED_UNITS = (
    environ.get("MDR_MIGRATION_EXPORTED_UNITS", "True").lower() == "true"
)
MDR_MIGRATION_EXPORTED_COMPOUNDS = (
    environ.get("MDR_MIGRATION_EXPORTED_COMPOUNDS", "True").lower() == "true"
)
MDR_MIGRATION_EXPORTED_TEMPLATES = (
    environ.get("MDR_MIGRATION_EXPORTED_TEMPLATES", "True").lower() == "true"
)
MDR_MIGRATION_EXPORTED_PROJECTS = (
    environ.get("MDR_MIGRATION_EXPORTED_PROJECTS", "True").lower() == "true"
)
MDR_MIGRATION_EXPORTED_STUDIES = (
    environ.get("MDR_MIGRATION_EXPORTED_STUDIES", "True").lower() == "true"
)
MDR_MIGRATION_EXPORTED_CONCEPT_VALUES = (
    environ.get("MDR_MIGRATION_EXPORTED_CONCEPT_VALUES", "True").lower() == "true"
)
INCLUDE_STUDY_NUMBERS = environ.get("INCLUDE_STUDY_NUMBERS", "")
EXCLUDE_STUDY_NUMBERS = environ.get("EXCLUDE_STUDY_NUMBERS", "")
MDR_MIGRATION_INCLUDE_DUMMY_STUDY = (
    environ.get("MDR_MIGRATION_INCLUDE_DUMMY_STUDY", "False").lower() == "true"
)
MDR_MIGRATION_RENUMBER_DUMMY_STUDY = (
    environ.get("MDR_MIGRATION_RENUMBER_DUMMY_STUDY", "False").lower() == "true"
)
MDR_MIGRATION_INCLUDE_EXAMPLE_DESIGNS = (
    environ.get("MDR_MIGRATION_INCLUDE_EXAMPLE_DESIGNS", "False").lower() == "true"
)

MDR_MIGRATION_EXPORTED_DICTIONARIES = (
    environ.get("MDR_MIGRATION_EXPORTED_DICTIONARIES", "True").lower() == "true"
)
DUMMY_STUDY_NUMBER = 9999

EXAMPLE_DESIGNS_START = 9000
EXAMPLE_DESIGNS_END = 9005

PROJECTS = "Projects"
CLINICAL_PROGRAMMES = "ClinicalProgrammes"
BRANDS = "Brands"
ACTIVITIES = "Activities"
ACTIVITY_INSTANCES = "ActivityInstances"
UNITS = "Units"
COMPOUNDS = "Compounds"
TEMPLATES = "Templates"
STUDIES = "Studies"
CONCEPT_VALUES = "ConceptValues"
DICTIONARIES = "Dictionaries"


IMPORT_DIR = os.path.dirname(IMPORT_PROJECTS)

ENDPOINT_TO_KEY_MAP = {
    "objective": {
        "get": "study-objectives",
        "post": "study-objectives?create_objective=true",
        "data": "objective",
        "uid": "study_objective_uid",
    },
    "criteria": {
        "get": "study-criteria",
        "post": "study-criteria",
        "data": "criteria",
        "uid": "study_criteria_uid",
    },
    "endpoint": {
        "get": "study-endpoints",
        "post": "study-endpoints?create_endpoint=true",
        "data": "endpoint",
        "uid": "study_endpoint_uid",
    },
    "activity_instruction": {
        "get": "study-activities",
        "post": "study-activities",
        "data": "activity",
        "uid": "study_activity_uid",
    },
}

# Map for template parameters and concepts numerical values.
# "import" is used to mark which are imported.
# Simple values are created as needed, no need to import.
# LagTime and TimePoint are left out for now.
# They need more data in the POST than what is currently implemented.
TEMPLATE_PARAM_MAP = {
    "NumericValue": {
        "path": "/concepts/numeric-values",
        "template": import_templates.numeric_value,
        "import": False,
    },
    "TextValue": {
        "path": "/concepts/text-values",
        "template": import_templates.text_value,
        "import": False,
    },
    "NumericValueWithUnit": {
        "path": "/concepts/numeric-values-with-unit",
        "template": import_templates.numeric_value_with_unit,
        "import": False,
    },
    "StudyDay": {
        "path": "/concepts/study-days",
        "template": import_templates.study_day,
        "import": True,
    },
    "StudyDurationDays": {
        "path": "/concepts/study-duration-days",
        "template": import_templates.study_duration_days,
        "import": True,
    },
    "StudyDurationWeeks": {
        "path": "/concepts/study-duration-weeks",
        "template": import_templates.study_duration_weeks,
        "import": True,
    },
    "StudyWeek": {
        "path": "/concepts/study-weeks",
        "template": import_templates.study_week,
        "import": True,
    },
    "VisitName": {
        "path": "/concepts/visit-names",
        "template": import_templates.study_week,
        "import": True,
    }
    # TODO handle these two properly
    #    "TimePoint": {
    #        "path": "/concepts/time-points",
    #        "template": import_templates.study_week,
    #        "import": True
    #        },
    #    "LagTime": {
    #        "path": "/concepts/lag-times",
    #        "template": import_templates.study_week,
    #        "import": True
    #        }
}

# Print any object nicely, useful while debugging
def jsonprint(data):
    print(json.dumps(data, indent=2))


class MockdataJson(BaseImporter):
    logging_name = "mockdata_json"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)
        self.log.info("Preparing lookup tables")

        self.import_dir = IMPORT_DIR

        # TODO replace all these lookup tables with lookup functions
        self.all_study_times = self.api.get_all_identifiers(
            self.api.get_all_from_api(
                "/concepts/unit-definitions", params={"subset": UNIT_SUBSET_STUDY_TIME}
            ),
            identifier="name",
            value="uid",
        )

    def lookup_activity_uid(self, name, allow_requested=False):
        if allow_requested:
            library = ("Sponsor", "Requested")
        else:
            library = "Sponsor"
        return self.lookup_concept_uid(name, "activities/activities", library=library, only_final=True)

    def lookup_activity_group_uid(self, name):
        return self.lookup_concept_uid(name, "activities/activity-groups")

    def lookup_activity_subgroup_uid(self, name):
        return self.lookup_concept_uid(name, "activities/activity-sub-groups")

    # Unused for now
    def lookup_activity_instance_uid(self, name):
        return self.lookup_concept_uid(name, "activities/activity-instances")

    def lookup_compound_uid(self, name):
        return self.lookup_concept_uid(name, "compounds")

    def lookup_compound_alias_uid(self, name):
        return self.lookup_concept_uid(name, "compound-aliases")

    def lookup_medicinal_product_uid(self, name):
        return self.lookup_concept_uid(name, "medicinal-products")

    def get_study_by_key(self, key, value, silent=False):
        filt = {key: {"v": [value], "op": "eq"}}
        items = self.api.get_all_from_api(
            "/studies", params={"filters": json.dumps(filt)}, items_only=True
        )
        if items is not None and len(items) > 0:
            uid = items[0]["uid"]
            self.log.debug(f"Found study with '{key}' == '{value}' and uid '{uid}'")
            return items[0]
        if not silent:
            self.log.warning(f"Could not find study with '{key}' == '{value}'")

    def lookup_study_uid_from_id(self, study_id):
        data = self.get_study_by_key(
            "current_metadata.identification_metadata.study_id", study_id, silent=True
        )
        try:
            return data["uid"]
        except (TypeError, KeyError):
            return None

    def lookup_study_uid_from_number(self, study_number):
        data = self.get_study_by_key(
            "current_metadata.identification_metadata.study_number", study_number
        )
        try:
            return data["uid"]
        except (TypeError, KeyError):
            return None

    def fetch_study_compounds(self, study_uid):
        self.log.info(f"Fetching study compounds for study uid '{study_uid}'")
        items = self.api.get_all_from_api(f"/studies/{study_uid}/study-compounds")
        if items is None:
            items = []
        self.log.debug(f"Got {len(items)} study compounds")
        return items

    # @lru_cache(maxsize=10000)
    def lookup_study_epoch_uid(self, study_uid, epoch_name):
        self.log.info(
            f"Looking up study epoch name '{epoch_name}' for study '{study_uid}'"
        )
        filt = {"epoch_name": {"v": [epoch_name], "op": "eq"}}
        items = self.api.get_all_from_api(
            f"/studies/{study_uid}/study-epochs", params={"filters": json.dumps(filt)}
        )
        if items is not None and len(items) > 0:
            uid = items[0].get("uid", None)
            self.log.debug(
                f"Found study epoch with name '{epoch_name}' and uid '{uid}'"
            )
            return uid
        self.log.warning(f"Could not find study epoch with name '{epoch_name}'")

    # @lru_cache(maxsize=10000)
    def get_template_parameters(self, param_type):
        items = self.api.get_all_from_api(
            f"/template-parameters/{param_type}/terms", items_only=False
        )
        return items

    def create_tp_based_on_simple_concept(self, value):
        param_type = value.get("type")
        name = value.get("name")
        details = TEMPLATE_PARAM_MAP.get(param_type, {})
        path = details.get("path")
        data = copy.deepcopy(details.get("template"))
        if path is None:
            self.log.error(
                f"Unknown parameter type '{param_type}', failed to create parameter with name '{name}'"
            )
            return
        for key in data.keys():
            if not key.endswith("uid") and key in value:
                data[key] = value[key]
        # Attempt to set data["value"] if the key exists
        try:
            val = float(name.split(" ")[0])
        except Exception:
            val = None
        data["value"] = val
        data["library_name"] = "Sponsor"
        for key in data.keys():
            if data[key] == "string":
                data[key] = None
        if "template_parameter" in data:
            data["template_parameter"] = True
        res = self.api.simple_post_to_api(path=path, body=data)
        if res:
            self.log.info(
                f"Created parameter with name '{name}' of type '{param_type}'"
            )
            uid = res.get("uid", None)
            return uid
        else:
            self.log.error(
                f"Failed to create parameter with name '{name}' of type '{param_type}'"
            )

    # @lru_cache(maxsize=10000)
    def lookup_or_create_parameter_value_uid(self, value):
        # SimpleConcepts based template parameters have to be created before
        # they are used in instantiation

        param_type = value.get("type", None)
        name = value.get("name", None)
        # Workaround for missing sentence case name in api endpoint
        if name == "≤":
            name = "<="
        elif name == "≥":
            name = ">="
        if param_type in TEMPLATE_PARAM_MAP.keys():
            uid = self.create_tp_based_on_simple_concept(value)
            if uid is not None:
                return uid
        else:
            self.log.info(
                f"Looking up parameter with name '{name}' of type '{param_type}'"
            )
            items = self.get_template_parameters(param_type)
            if items is not None:
                for val in items:
                    # we have to lookup in sentence case as well as if possible we return
                    # name sentence case property for template parameter value
                    # TODO add name_sentence_case property to the /template-parameters/../values endpoint
                    # and compare this value here
                    # used .lower() for a hot fix
                    val_name_sentence_case = val["name"].lower()

                    if val["name"] == name or val_name_sentence_case == name:
                        uid = val.get("uid", None)
                        self.log.debug(
                            f"Found parameter with name '{name}' and sentence case '{val_name_sentence_case}' and uid '{uid}'"
                        )
                        return uid
            self.log.warning(
                f"Could not find parameter with name or name_sentence_case equal to'{name}'"
            )

    # @lru_cache(maxsize=10000)
    def lookup_template_uid(
        self, name, template_type, subtype=None, log=True, shortname=None
    ):
        if shortname is None:
            shortname = name
        path = f"/{template_type}-templates"
        self.log.info(
            f"Looking up {template_type} template with name '{shortname}' and subtype '{subtype}'"
        )
        filt = {"name": {"v": [name], "op": "eq"}}
        if subtype is not None:
            filt["type.name.sponsor_preferred_name"] = {"v": [subtype], "op": "eq"}
        items = self.api.get_all_from_api(path, params={"filters": json.dumps(filt)})
        if items is not None and len(items) > 0:
            uid = items[0].get("uid", None)
            if log:
                self.log.debug(
                    f"Found {template_type} template with name '{shortname}' and uid '{uid}'"
                )
            return uid
        if log:
            self.log.warning(
                f"Could not find {template_type} template with name '{shortname}'"
            )

    def lookup_preinstance_uid(
        self, name, template_type, subtype_id=None, log=True, shortname=None
    ):
        if shortname is None:
            shortname = name
        path = f"/{template_type}-pre-instances"
        self.log.info(
            f"Looking up {template_type} pre-instance with name '{shortname}' and subtype '{subtype_id}'"
        )
        filt = {"name": {"v": [name], "op": "eq"}}
        if subtype_id is not None:
            filt["template_type_uid"] = {"v": [subtype_id], "op": "co"}
        items = self.api.get_all_from_api(path, params={"filters": json.dumps(filt)})
        if items is not None and len(items) > 0:
            uid = items[0].get("uid", None)
            if log:
                self.log.debug(
                    f"Found {template_type} pre-instance with name '{shortname}' and uid '{uid}'"
                )
            return uid
        if log:
            self.log.warning(
                f"Could not find {template_type} pre-instance with name '{shortname}'"
            )

    # @lru_cache(maxsize=10000)
    def lookup_study_template_instance_uid(self, name, study_uid, template_type):
        mapper = ENDPOINT_TO_KEY_MAP[template_type]
        endpoint = mapper["get"]
        data_key = mapper["data"]
        uid_key = mapper["uid"]
        path = f"/studies/{study_uid}/{endpoint}"
        self.log.info(f"Looking for {endpoint.replace('-', ' ')} with name '{name}'")
        items = self.api.get_all_from_api(path, items_only=False)
        # Some of the enpoints return the data under "items".
        if items is not None and "items" in items:
            items = items["items"]
        if items is not None:
            for item in items:
                if not item.get(data_key):
                    continue
                item_name = item[data_key].get("name")
                if item_name == name:
                    uid = item.get(uid_key, None)
                    self.log.debug(
                        f"Found {endpoint.replace('-', ' ')} with name '{name}' and uid '{uid}'"
                    )
                    return uid
        self.log.warning(
            f"Could not find {endpoint.replace('-', ' ')} with name '{name}'"
        )

    @lru_cache(maxsize=10000)
    def lookup_study_objective_uid(self, name, study_uid):
        path = f"/studies/{study_uid}/study-objectives"
        self.log.info(f"Looking up study objective with name '{name}'")
        filt = {"objective.name": {"v": [name], "op": "eq"}}
        items = self.api.get_all_from_api(path, params={"filters": json.dumps(filt)})
        if items is not None and len(items) > 0:
            uid = items[0].get("study_objective_uid", None)
            self.log.debug(f"Found study objective with name '{name}' and uid '{uid}'")
            return uid
        self.log.warning(f"Could not find study objective with name '{name}'")

    @lru_cache(maxsize=10000)
    def lookup_study_visit_uid(self, study_uid, visit_name):
        self.log.info(
            f"Looking up study visit name '{visit_name}' for study '{study_uid}'"
        )
        filt = {"visit_name": {"v": [visit_name], "op": "eq"}}
        items = self.api.get_all_from_api(
            f"/studies/{study_uid}/study-visits", params={"filters": json.dumps(filt)}
        )
        if items is not None and len(items) > 0:
            uid = items[0].get("uid", None)
            self.log.debug(
                f"Found study visit with name '{visit_name}' and uid '{uid}'"
            )
            return uid
        self.log.warning(f"Could not find study visit with name '{visit_name}'")

    @lru_cache(maxsize=10000)
    def lookup_study_activity_uid(
        self, study_uid, activity_name, group_name=None, subgroup_name=None
    ):
        self.log.info(
            f"Looking up study activity name '{activity_name}' with group '{group_name}', subgroup '{subgroup_name}' for study '{study_uid}'"
        )
        # filt = {"activity.name": {"v": [activity_name], "op": "eq"}}
        params = {"activity_names[]": [activity_name]}
        if group_name is not None:
            params["activity_group_names[]"] = [group_name]
        if subgroup_name is not None:
            params["activity_subgroup_names[]"] = [subgroup_name]
        items = self.api.get_all_from_api(
            f"/studies/{study_uid}/study-activities",
            params=params,
        )
        if items is not None and len(items) > 0:
            uid = items[0].get("study_activity_uid")
            self.log.debug(
                f"Found study activity with name '{activity_name}' and uid '{uid}'"
            )
            return uid
        self.log.warning(f"Could not find study activity with name '{activity_name}'")

    def lookup_timeframe(self, name):
        path = "/timeframes"
        self.log.info(f"Looking for timeframe with name '{name}'")
        filt = {"name": {"v": [name], "op": "eq"}}
        items = self.api.get_all_from_api(path, params={"filters": json.dumps(filt)})
        if items is not None and len(items) > 0:
            uid = items[0].get("uid", None)
            self.log.debug(f"Found timeframe with name '{name}' and uid '{uid}'")
            return uid
        self.log.warning(f"Could not find timeframe with name '{name}'")

    def print_cache_stats(self):
        print("\nCache summary")
        print(f"{'function':35s}\thits\tmisses")
        for key in dir(self):
            item = getattr(self, key)
            if hasattr(item, "cache_info"):
                info = item.cache_info()
                print(f"{key:35s}\t{info.hits}\t{info.misses}")

    ####################### Helper functions ######################

    def append_if_not_none(self, thelist, value):
        if value is not None:
            thelist.append(value)

    def fetch_all_activities(self):
        activities = {}
        for item in self.api.get_all_from_api_paged("/concepts/activities/activities"):
            activities[item["name"]] = item["uid"]
        return activities

    def fetch_all_activity_groups(self):
        groups = {}
        for item in self.api.get_all_from_api("/concepts/activities/activity-groups"):
            groups[item["name"]] = item["uid"]
        return groups

    def fetch_all_activity_subgroups(self):
        subs = {}
        for item in self.api.get_all_from_api(
            "/concepts/activities/activity-sub-groups"
        ):
            subs[item["name"]] = item["uid"]
        return subs

    def map_sponsor_name_to_uid(self, data):
        temp_dict = {}
        if data is not None:
            for item in data:
                temp_dict[item["name"]["sponsor_preferred_name"]] = item["term_uid"]
        return temp_dict

    def map_epoch_name_to_uids(self, data):
        temp_dict = {}
        if data is not None:
            for item in data:
                # Remove any trailing number
                name = item["epoch_name"].rstrip("0123456789 ")
                if name not in temp_dict:
                    temp_dict[name] = []
                temp_dict[name].append({"order": item["order"], "uid": item["uid"]})
        new_dict = {}

        def get_order(data):
            return int(data["order"])

        for key, val in temp_dict.items():
            val.sort(key=get_order)
            new_dict[key] = [v["uid"] for v in val]

        return new_dict

    def map_fields_to_dict(self, data, key, value):
        temp_dict = {}
        if data is not None:
            for item in data:
                name = item[key]
                temp_dict[name] = item[value]
        return temp_dict

    def caseless_dict_lookup(self, input_dict, key):
        return next(
            (
                value
                for dict_key, value in input_dict.items()
                if dict_key.lower() == key.lower()
            )
        )

    def _check_for_duplicate_epoch(self, new, existing):
        if existing is None:
            return False
        for item in existing:
            # print(item["epoch_subtype_name"], new["epoch_subtype_name"], item["description"], new["description"])
            if (
                item["epoch_subtype_name"] == new["epoch_subtype_name"]
                and item["description"] == new["description"]
            ):
                return True
        return False

    def _compare_dict_path(self, a, b, path):
        aval = self._get_dict_path(a, path)
        bval = self._get_dict_path(b, path)
        return aval == bval

    def _get_dict_path(self, d, path):
        dp = d
        for p in path:
            if not isinstance(dp, dict) or p not in dp:
                return None
            dp = dp[p]
        return dp

    def _check_for_duplicate_study_compound(self, new, existing):
        if existing is None:
            return False
        for item in existing:
            if (
                item is not None
                and new is not None
                and self._compare_dict_path(item, new, ["compound", "name"])
                and self._compare_dict_path(item, new, ["compound_alias", "name"])
                and self._compare_dict_path(item, new, ["type_of_treatment", "name"])
                and self._compare_dict_path(item, new, ["dosage_form", "name"])
                and self._compare_dict_path(item, new, ["strength_value", "value"])
                and self._compare_dict_path(item, new, ["strength_value", "unit_label"])
                and self._compare_dict_path(
                    item, new, ["route_of_administration", "name"]
                )
                and self._compare_dict_path(item, new, ["dispensed_in", "name"])
                and self._compare_dict_path(item, new, ["device", "name"])
                and item.get("other_info") == new.get("other_info")
            ):
                return True
        return False

    def _check_for_duplicate_visit(self, new, existing):
        if existing is None:
            return False
        for item in existing:
            # print(item["epoch_subtype_name"], new["epoch_subtype_name"], item["description"], new["description"])
            if (
                item["description"] == new["description"]
                and item["visit_type_name"] == new["visit_type_name"]
                and item["time_value"] == new["time_value"]
                and item["time_unit_name"] == new["time_unit_name"]
            ):
                return True
        return False

    def _check_for_duplicate_arm(self, new, existing):
        if existing is None:
            return False
        for item in existing:
            # print(item)
            if item["name"] == new["name"]:
                return True
        return False

    def _check_for_duplicate_element(self, new, existing):
        if existing is None:
            return False
        for item in existing:
            # print(item)
            if item["name"] == new["name"]:
                return True
        return False

    # Recursive walk through a dict to copy all values
    def _copy_parameters(self, data_old, template, clone=True):
        if clone:
            data_new = copy.deepcopy(template)
        else:
            data_new = template
        for key in data_new.keys():
            if not key.lower().endswith("uid") and data_old is not None:
                value = data_old.get(key, None)
                if isinstance(data_new[key], dict):
                    self._copy_parameters(value, data_new[key], clone=False)
                else:
                    data_new[key] = value
        return data_new

    def create_dict_path(self, data, path, key, value):
        pos = data
        if pos is None:
            return
        for p in path:
            if p not in pos:
                pos[p] = {}
            # print("enter",p)
            pos = pos[p]
        # print("create", key, value)
        pos[key] = value

    # Recursive walk through a dict to copy all values
    def _copy_parameters_with_values(self, data_old, template, path=[], data_new={}):
        for key in list(template.keys()):
            if not key.lower().endswith("uid"):
                value_old = data_old.get(key, None)
                # print(json.dumps(value_old, indent=2))
                # print("Process key:", key, type(value_old))
                if isinstance(value_old, dict):
                    # print("Dive deeper:", path, key)
                    self._copy_parameters_with_values(
                        value_old, template[key], path=path + [key], data_new=data_new
                    )
                elif isinstance(value_old, (list, str)) and len(value_old) > 0:
                    # print("Create list or str:", path, key, value_old)
                    # TODO don't simply replace lists, handle properly!
                    self.create_dict_path(data_new, path, key, value_old)
                elif isinstance(value_old, (int, float)):
                    # print("Create number:", path, key, value_old)
                    self.create_dict_path(data_new, path, key, value_old)
                # else:
                # print("Skip:", path, key, value_old)
            # else:
            # print("Skip key:", key)
        return data_new

    def get_dict_path(self, data, path, default=None):
        pos = data
        if pos is None:
            return default
        # print(json.dumps(pos, indent=2))
        for p in path[0:-1]:
            # print("--- go to", p)
            pos = pos.get(p, {})
            # print(json.dumps(pos, indent=2))
        return pos.get(path[-1], default)

    # Some sponsor preferred names have changed.
    # This is a helper to allow importing old data.
    def update_name(self, name, codelist_name):
        if codelist_name == "Study Type":
            suffix = [" Study"]
        elif codelist_name == "Trial Type":
            suffix = [" Study", " Trial"]
        elif codelist_name == "Control Type":
            suffix = [" Control"]
        elif codelist_name == "Trial Blinding Schema":
            suffix = [" Study"]
        elif codelist_name == "Intervention Model Response":
            suffix = [" Study"]
        else:
            return name
        for s in suffix:
            if name.endswith(s):
                return name[0 : -len(suffix)]
        return name

    ################### Study metadata helpers ################

    def fill_age_unit(self, data, key):
        name = self.get_dict_path(
            data, [key, "duration_unit_code", "name"], default=None
        )
        if name:
            uid = self.lookup_unit_uid(name, subset=UNIT_SUBSET_AGE)
            if uid:
                self.log.info(f"Found time unit '{name}' with uid '{uid}'")
                self.create_dict_path(data, [key, "duration_unit_code"], "uid", uid)
            else:
                self.log.warning(f"Could not find time unit '{name}'")

    def fill_general_term(self, data, key, codelist_name):
        name = self.get_dict_path(data, [key, "name"], default=None)
        if name:
            name = self.update_name(name, codelist_name)
            uid = self.lookup_ct_term_uid(codelist_name, name)
            if uid:
                self.log.info(
                    f"Found term '{name}' with uid '{uid}' in codelist '{codelist_name}'"
                )
                self.create_dict_path(data, [key], "term_uid", uid)
            else:
                self.log.warning(
                    f"Could not find term '{name}' in codelist '{codelist_name}'"
                )

    def fill_general_term_list(self, data, key, codelist_name):
        items = data.get(key, [])
        if items:
            for item in items:
                name = item["name"]
                uid = self.lookup_ct_term_uid(codelist_name, name)
                if uid:
                    self.log.info(
                        f"Found term name '{name}' with uid '{uid}' in codelist '{codelist_name}'"
                    )
                    item["term_uid"] = uid
                else:
                    self.log.warning(
                        f"Could not find term '{name}' in codelist '{codelist_name}'"
                    )

    def fill_snomed_term_list(self, data, key):
        items = data.get(key, [])
        if items:
            for item in items:
                name = item["name"]
                uid = self.lookup_dictionary_term_uid("SNOMED", name)
                if uid:
                    self.log.info(
                        f"Found term name '{name}' with uid '{uid}' in SNOMED'"
                    )
                    item["term_uid"] = uid
                else:
                    self.log.warning(f"Could not find term '{name}' in SNOMED'")

    def fill_null_value_codes(self, data, template):
        for key in list(data.keys()):
            if key.endswith("_null_value_code"):
                data_key = key.replace("_null_value_code", "")
                self.log.info(f"Handle null value for {data_key}")
                if data.get(data_key, None) is None:
                    self.log.info(f"No data, update {key}")
                    self.fill_general_term(data, key, CODELIST_NULL_FLAVOR)
                else:
                    self.log.info(f"Data found, null {key}")
                    data[key] = None
            else:
                nullvalue_key = key + "_null_value_code"
                if nullvalue_key in template:
                    self.log.info(
                        f"Data exists for '{key}', set '{nullvalue_key}' to None"
                    )
                    data[nullvalue_key] = None

    ################### Study metadata uid lookups ################

    def fill_high_level_study_design(self, data):
        self.log.info("--- Looking up data for High Level Study Design ---")
        metadata = self.get_dict_path(
            data, ["current_metadata", "high_level_study_design"], default={}
        )
        template = self.get_dict_path(
            import_templates.study_patch,
            ["current_metadata", "high_level_study_design"],
            default={},
        )

        self.fill_age_unit(metadata, "confirmed_response_minimum_duration")

        self.fill_general_term(metadata, "study_type_code", CODELIST_STUDY_TYPE)
        self.fill_general_term(metadata, "trial_phase_code", CODELIST_TRIAL_PHASE)

        items = metadata.get("diagnosis_groups_codes", [])
        if items:
            for item in items:
                name = item["name"]
                uid = self.lookup_ct_term_uid(CODELIST_TRIAL_TYPE, name)
                if uid:
                    self.log.info(f"Found trial type '{name}' with uid '{uid}'")
                    item["term_uid"] = uid
                else:
                    self.log.warning(f"Could not find trial type '{name}'")

        self.fill_null_value_codes(metadata, template)

    def fill_study_population(self, data):
        self.log.info("--- Looking up data for Study Population ---")
        metadata = self.get_dict_path(
            data, ["current_metadata", "study_population"], default={}
        )
        template = self.get_dict_path(
            import_templates.study_patch,
            ["current_metadata", "study_population"],
            default={},
        )

        self.fill_age_unit(metadata, "planned_maximum_age_of_subjects")
        self.fill_age_unit(metadata, "planned_minimum_age_of_subjects")
        self.fill_age_unit(metadata, "stable_disease_minimum_duration")

        self.fill_general_term(
            metadata, "sex_of_participants_code", CODELIST_SEX_OF_PARTICIPANTS
        )

        self.fill_snomed_term_list(metadata, "diagnosis_groups_codes")
        self.fill_snomed_term_list(metadata, "disease_conditions_or_indications_codes")
        self.fill_snomed_term_list(metadata, "therapeutic_area_codes")
        self.fill_null_value_codes(metadata, template)

    def fill_study_intervention(self, data):
        self.log.info("--- Looking up data for Study Interventions ---")
        metadata = self.get_dict_path(
            data, ["current_metadata", "study_intervention"], default={}
        )
        template = self.get_dict_path(
            import_templates.study_patch,
            ["current_metadata", "study_intervention"],
            default={},
        )

        self.fill_general_term(metadata, "control_type_code", CODELIST_CONTROL_TYPE)
        self.fill_general_term(
            metadata, "intervention_model_code", CODELIST_INTERVENTION_MODEL
        )
        self.fill_general_term(
            metadata, "intervention_type_code", CODELIST_INTERVENTION_TYPE
        )
        self.fill_general_term(
            metadata, "trial_blinding_schema_code", CODELIST_TRIAL_BLINDING_SCHEMA
        )
        self.fill_age_unit(metadata, "planned_study_length")
        self.fill_general_term_list(
            metadata, "trial_intent_types_codes", CODELIST_TRIAL_INDICATION_TYPE
        )
        self.fill_null_value_codes(metadata, template)

    ####################### Import functions ######################

    # Projects
    @open_file()
    def handle_projects(self, jsonfile):
        self.log.info("======== Projects ========")
        import_data = json.load(jsonfile)

        all_project_numbers = self.api.get_all_identifiers(
            self.api.get_all_from_api("/projects"), "project_number"
        )
        all_clinical_programmes = self.api.get_all_identifiers(
            self.api.get_all_from_api("/clinical-programmes"),
            identifier="name",
            value="uid",
        )

        # Create the project
        for project in import_data:
            data = self._copy_parameters(
                project,
                import_templates.project,
            )
            program_name = project["clinical_programme"]["name"]
            project_number = project["project_number"]
            data["clinical_programme_uid"] = all_clinical_programmes.get(program_name)
            if data["clinical_programme_uid"] is None:
                self.log.error(
                    f"Unable to find programme {program_name}, skipping this project"
                )
                continue
            # self.log.info(f"=== Handle project '{project_number}' ===")
            # print(json.dumps(data, indent=2))

            if project_number not in all_project_numbers:
                self.log.info(f"Add project '{project_number}'")
                self.api.simple_post_to_api("/projects", data, "/studies")
            else:
                self.log.info(f"Skipping existing project '{project_number}'")

    # Brands
    @open_file()
    def handle_brands(self, jsonfile):
        self.log.info("====== Brands ======")
        import_data = json.load(jsonfile)

        all_brands = self.api.get_all_identifiers(
            self.api.get_all_from_api("/brands", items_only=False),
            identifier="name",
            value="uid",
        )

        for brand in import_data:
            data = self._copy_parameters(
                brand,
                import_templates.brands,
            )
            brand_name = brand["name"]

            if brand_name not in all_brands:
                self.log.info(f"Add brand '{brand_name}' ")
                self.api.simple_post_to_api("/brands", data)
            else:
                self.log.info(f"Skipping existing brand '{brand_name}' ")

    @open_file()
    def handle_clinical_programmes(self, jsonfile):
        self.log.info("===== Clinical Programmes =====")
        import_data = json.load(jsonfile)

        all_clinical_programmes = self.api.get_all_identifiers(
            self.api.get_all_from_api("/clinical-programmes"),
            identifier="name",
            value="uid",
        )

        for programme in import_data:
            data = self._copy_parameters(
                programme,
                import_templates.clinical_programme,
            )
            programme_name = programme["name"]

            if programme_name not in all_clinical_programmes:
                self.log.info(f"Add Clinical Programme '{programme_name}' ")
                self.api.simple_post_to_api("/clinical-programmes", data)
            else:
                self.log.info(
                    f"Skipping existing clinical programme '{programme_name}' "
                )

    def filter_studies(self, studies):
        include_numbers = [
            int(nbr) for nbr in INCLUDE_STUDY_NUMBERS.split(",") if len(nbr.strip()) > 0
        ]
        exclude_numbers = [
            int(nbr) for nbr in EXCLUDE_STUDY_NUMBERS.split(",") if len(nbr.strip()) > 0
        ]
        # Allow skipping the dummy study
        if not MDR_MIGRATION_INCLUDE_DUMMY_STUDY:
            exclude_numbers.append(DUMMY_STUDY_NUMBER)
        if not MDR_MIGRATION_INCLUDE_EXAMPLE_DESIGNS:
            for n in range(EXAMPLE_DESIGNS_START, EXAMPLE_DESIGNS_END + 1):
                exclude_numbers.append(n)
        studies_copy = []
        for study in studies:
            to_copy = True
            study_number = int(
                study["current_metadata"]["identification_metadata"]["study_number"]
            )
            study_uid = study["uid"]
            if len(include_numbers) > 0 and study_number not in include_numbers:
                to_copy = False
            if len(exclude_numbers) > 0 and study_number in exclude_numbers:
                to_copy = False
            if to_copy:
                self.log.info(
                    f"Including study number {study_number} with uid '{study_uid}'"
                )
                studies_copy.append(study)
            else:
                self.log.info(
                    f"Excluding study number {study_number} with uid '{study_uid}'"
                )
        return studies_copy

    # Handle studies.
    @open_file()
    def handle_studies(self, jsonfile):
        self.log.info("======== Studies ========")
        all_studies = json.load(jsonfile)
        filtered_studies = self.filter_studies(all_studies)
        for study_data in filtered_studies:
            exported_uid = study_data["uid"]
            study_json = os.path.join(self.import_dir, f"studies.{exported_uid}.json")
            study_name = self.handle_study(study_json)
            self.handle_study_design(exported_uid, study_name)

    @open_file()
    def handle_study(self, jsonfile):
        import_data = json.load(jsonfile)
        # Create the study
        parent_study = import_data.get("study_parent_part", None)
        if parent_study is None:
            data = self._copy_parameters(
                import_data["current_metadata"]["identification_metadata"],
                import_templates.study,
            )
        else:
            data = self._copy_parameters(
                import_data["current_metadata"]["identification_metadata"],
                import_templates.study_subpart,
            )
            parent_study_number = parent_study["study_number"]
            parent_study_uid = self.lookup_study_uid_from_number(parent_study_number)
            if parent_study_uid is None:
                self.log.error(
                    f"Unable to find parent study with number '{parent_study_number}'"
                )
                return None
            self.log.info(f"Adding subpart to study with uid '{parent_study_uid}'")
            data["study_parent_part_uid"] = parent_study_uid

        study_nbr = import_data["current_metadata"]["identification_metadata"][
            "study_number"
        ]
        study_id = import_data["current_metadata"]["identification_metadata"][
            "study_id"
        ]

        self.log.info(f"=== Handle study '{study_id}' ===")

        # If this is the dummy study, check if we need to give it a new number.
        # The api returns study_number as a string.
        new_study_nbr = None
        if MDR_MIGRATION_RENUMBER_DUMMY_STUDY and int(study_nbr) == DUMMY_STUDY_NUMBER:
            new_study_nbr = int(study_nbr)
            while self.lookup_study_uid_from_number(str(new_study_nbr)) is not None:
                new_study_nbr -= 1
            if new_study_nbr != int(study_nbr):
                study_nbr = str(new_study_nbr)
                data["study_number"] = study_nbr
                study_id = study_id.rsplit("-")[0] + "-" + study_nbr
                data["study_id"] = study_id
                self.log.info(
                    f"Importing dummy study as study number: {study_nbr}, id: {study_id}"
                )

        if self.lookup_study_uid_from_id(study_id) is None:
            self.log.info(f"Add study '{study_id}' with study number '{study_nbr}'")
            study_data = self.api.simple_post_to_api("/studies", data, "/studies")
            if study_data is None:
                self.log.error(
                    "Failed to add study '{study_id}' with study number '{study_nbr}'"
                )
                return None
        else:
            self.log.info(
                f"Skip adding already existing study '{study_id}' with study number {study_nbr}"
            )
            study_data = self.get_study_by_key(
                "current_metadata.identification_metadata.study_id", study_id
            )
        if parent_study is not None:
            # If this is a subpart, we are done and return early.
            return study_id

        # Patch it to add more data
        self.log.info(f"Patching study '{study_id}' with study number {study_nbr} and uid '{study_data['uid']}'")
        patch_data = copy.deepcopy(import_templates.study_patch)

        data = self._copy_parameters_with_values(
            import_data, patch_data, data_new=study_data
        )

        # Update study number if needed
        if new_study_nbr is not None:
            data["current_metadata"]["identification_metadata"][
                "study_number"
            ] = study_nbr
            data["current_metadata"]["identification_metadata"]["study_id"] = study_id

        self.fill_high_level_study_design(data)
        self.fill_study_population(data)
        self.fill_study_intervention(data)

        # print(json.dumps(data, indent=2))
        self.api.patch_to_api(data, "/studies/")
        return study_id

    # Read mockup study designs and fill in the corresponding data
    def handle_study_design(self, exported_uid, study_name):
        self.log.info(f"======== Study Design for {study_name} ========")
        # Epochs

        epoch_json = os.path.join(
            self.import_dir, f"studies.{exported_uid}.study-epochs.json"
        )
        self.handle_study_epochs(epoch_json, study_name)
        ## Visits
        visit_json = os.path.join(
            self.import_dir, f"studies.{exported_uid}.study-visits.json"
        )
        self.handle_study_visits(visit_json, study_name)
        # Arms
        arms_json = os.path.join(
            self.import_dir, f"studies.{exported_uid}.study-arms.json"
        )
        self.handle_study_arms(arms_json, study_name)

        # Study branches
        branches_json = os.path.join(
            self.import_dir, f"studies.{exported_uid}.study-branch-arms.json"
        )
        self.handle_study_branch_arms(branches_json, study_name)

        # TODO Study cohorts
        cohorts_json = os.path.join(
            self.import_dir, f"studies.{exported_uid}.study-cohorts.json"
        )
        self.handle_study_cohorts(cohorts_json, study_name)

        # Elements
        elements_json = os.path.join(
            self.import_dir, f"studies.{exported_uid}.study-elements.json"
        )
        self.handle_study_elements(elements_json, study_name)
        # Matrix
        matrix_json = os.path.join(
            self.import_dir, f"studies.{exported_uid}.study-design-cells.json"
        )
        self.handle_study_matrix(matrix_json, study_name)
        # Activities
        activities_json = os.path.join(
            self.import_dir, f"studies.{exported_uid}.study-activities.json"
        )
        self.handle_study_activities(activities_json, study_name)
        # Criteria
        criteria_json = os.path.join(
            self.import_dir, f"studies.{exported_uid}.study-criteria.json"
        )
        self.handle_study_template_instances(criteria_json, "criteria", study_name)
        # Objectives
        objective_json = os.path.join(
            self.import_dir, f"studies.{exported_uid}.study-objectives.json"
        )
        self.handle_study_template_instances(objective_json, "objective", study_name)
        # Endpoints
        endpoint_json = os.path.join(
            self.import_dir, f"studies.{exported_uid}.study-endpoints.json"
        )
        self.handle_study_template_instances(endpoint_json, "endpoint", study_name)
        # Study compounds
        comp_json = os.path.join(
            self.import_dir, f"studies.{exported_uid}.study-compounds.json"
        )
        self.handle_study_compounds(comp_json, study_name)

        # Get study visit and activity names
        visit_names = self.get_study_visit_names(visit_json)
        activity_names = self.get_study_activity_names(activities_json)

        # Study activity schedule
        sched_json = os.path.join(
            self.import_dir, f"studies.{exported_uid}.study-activity-schedules.json"
        )
        self.handle_study_activity_schedules(
            sched_json, visit_names, activity_names, study_name
        )

    @open_file()
    def handle_study_matrix(self, jsonfile, study_name):
        self.log.info(f"======== Study design matrix for study {study_name} ========")
        study_uid = self.lookup_study_uid_from_id(study_name)
        study_elements = self.api.get_all_from_api(
            f"/studies/{study_uid}/study-elements"
        )

        study_elements = self.map_fields_to_dict(study_elements, "name", "element_uid")
        study_arms = self.api.get_all_from_api(f"/studies/{study_uid}/study-arms")
        study_arms = self.map_fields_to_dict(study_arms, "name", "arm_uid")
        study_branch_arms = self.api.get_all_from_api(
            f"/studies/{study_uid}/study-branch-arms"
        )
        study_branch_arms = self.map_fields_to_dict(
            study_branch_arms, "name", "branch_arm_uid"
        )

        imported = json.load(jsonfile)
        for item in imported:
            data = dict(import_templates.study_design_cell)
            data["activity_instance_uid"] = None
            arm_name = item["study_arm_name"]
            if arm_name is not None:
                try:
                    data["study_arm_uid"] = self.caseless_dict_lookup(
                        study_arms, arm_name
                    )
                except (StopIteration, AttributeError):
                    self.log.warning(
                        f"Unable to find study arm {arm_name}, skipping this entry"
                    )
            else:
                data["study_arm_uid"] = None

            branch_arm_name = item["study_branch_arm_name"]
            if branch_arm_name is not None:
                try:
                    data["study_branch_arm_uid"] = self.caseless_dict_lookup(
                        study_branch_arms, branch_arm_name
                    )
                except (StopIteration, AttributeError):
                    self.log.warning(f"Unable to find study arm {branch_arm_name}")
            else:
                data["study_branch_arm_uid"] = None

            epoch_name = item["study_epoch_name"]
            data["study_epoch_uid"] = self.lookup_study_epoch_uid(study_uid, epoch_name)
            if data["study_epoch_uid"] is not None:
                self.log.info(
                    f"Found study epoch {epoch_name} with uid {data['study_epoch_uid']}"
                )
            else:
                self.log.error(
                    f"Unable to find study epoch {epoch_name}, skipping this entry"
                )
                continue

            element_name = item["study_element_name"]
            try:
                data["study_element_uid"] = self.caseless_dict_lookup(
                    study_elements, element_name
                )
            except StopIteration:
                self.log.error(
                    f"Unable to find study element {element_name}, skipping this entry"
                )
                continue
            data["order"] = item["order"]
            # print(json.dumps(data, indent=2))
            path = f"/studies/{study_uid}/study-design-cells"
            self.log.info(
                f"Add study design cell with epoch '{epoch_name}', arm '{arm_name}', element '{element_name}' for study '{study_name}' with id '{study_uid}'"
            )
            self.api.simple_post_to_api(path, data, "/study-design-cells")

    @open_file()
    def handle_study_activities(self, jsonfile, study_name):
        self.log.info(f"======== Study activities for study {study_name} ========")
        study_uid = self.lookup_study_uid_from_id(study_name)
        imported = json.load(jsonfile)
        for item in imported:
            data = dict(import_templates.study_activity)
            data["activity_instance_uid"] = None

            if not MDR_MIGRATION_FROM_SAME_ENV:
                # Look up the UID by name

                # Workaround for old format data
                if "flowchart_group" in item:
                    flow_name = item["flowchart_group"]["sponsor_preferred_name"]
                else:
                    if "soa_group_term_name" in item["study_soa_group"]:
                        flow_name = item["study_soa_group"]["soa_group_term_name"]
                    else:
                        flow_name = item["study_soa_group"]["soa_group_name"]
                data["soa_group_term_uid"] = self.lookup_codelist_term_uid(CODELIST_FLOWCHART_GROUP, flow_name)
                if data["soa_group_term_uid"] is None:
                    self.log.error(
                        f"Unable to find SoA group {flow_name}, skipping this entry"
                    )
                    continue
            else:
                # Reuse the UID from the exported data
                # Use the UID as name, only used for logging
                flow_name = item["study_soa_group"]["soa_group_term_uid"]
                data["soa_group_term_uid"] = item["study_soa_group"]["soa_group_term_uid"]

            act_name = item["activity"]["name"]

            if not MDR_MIGRATION_FROM_SAME_ENV:
                # Look up the UID by name
                data["activity_uid"] = self.lookup_activity_uid(act_name, allow_requested=True)
            else:
                # Reuse the UID from the exported data
                data["activity_uid"] = item["activity"]["uid"]

            if data["activity_uid"] is None:
                self.log.error(
                    f"Unable to find activity {act_name}, skipping this entry"
                )
                continue

            group_uid = None
            subgroup_uid = None

            if not MDR_MIGRATION_FROM_SAME_ENV:
                # Look up the group and subgroup UIDs by name
                if item.get("study_activity_group", {}).get(
                    "activity_group_name"
                ) and item.get("study_activity_subgroup", {}).get("activity_subgroup_name"):
                    # Group and subgroup names are available in the exported data
                    group_name = item["study_activity_group"]["activity_group_name"]
                    subgroup_name = item["study_activity_subgroup"][
                        "activity_subgroup_name"
                    ]
                    group_uid = self.lookup_activity_group_uid(group_name)
                    subgroup_uid = self.lookup_activity_subgroup_uid(subgroup_name)
                elif item.get("study_activity_group", {}).get(
                    "activity_group_uid"
                ) and item.get("study_activity_subgroup", {}).get("activity_subgroup_uid"):
                    # Group and subgroup uids are not directly available in the exported data,
                    # Look them up via the activity groupings.
                    for grouping in item["activity"]["activity_groupings"]:
                        if (
                            grouping["activity_group_uid"]
                            == item["study_activity_group"]["activity_group_uid"]
                            and grouping["activity_subgroup_uid"]
                            == item["study_activity_subgroup"]["activity_subgroup_uid"]
                        ):
                            group_name = grouping["activity_group_name"]
                            subgroup_name = grouping["activity_subgroup_name"]
                            group_uid = self.lookup_activity_group_uid(group_name)
                            subgroup_uid = self.lookup_activity_subgroup_uid(subgroup_name)
                            break

                if group_uid and subgroup_uid:
                    self.log.info(
                        f"Found group {group_name} and subgroup {subgroup_name} for study activity {act_name}"
                    )
                else:
                    self.log.warning(
                        f"Could not assign group and subgroup for study activity {act_name}"
                    )
                data["activity_group_uid"] = group_uid
                data["activity_subgroup_uid"] = subgroup_uid
            else:
                # Reuse the UIDs from the exported data
                data["activity_group_uid"] = item["study_activity_group"]["activity_group_uid"]
                data["activity_subgroup_uid"] = item["study_activity_subgroup"]["activity_subgroup_uid"]

            # print(json.dumps(data, indent=2))
            path = f"/studies/{study_uid}/study-activities"
            self.log.info(
                f"Add study activity '{act_name}' with SoA group '{flow_name}' for study '{study_name}' with id '{study_uid}'"
            )
            self.api.simple_post_to_api(path, data, "/study-activities")

    @open_file()
    def handle_study_epochs(self, jsonfile, study_name):
        self.log.info(f"======== Study epochs for study '{study_name}' ========")

        # all_unit_subset_terms = self.api.get_all_identifiers(
        #        self.api.get_all_from_api("/ct/terms/names?codelist_name=Unit Subset"),
        #        identifier="sponsor_preferred_name",
        #        value="term_uid")
        # study_time_subset_uid = all_unit_subset_terms["Study Time"]

        study_uid = self.lookup_study_uid_from_id(study_name)
        study_epochs = self.api.get_all_from_api(f"/studies/{study_uid}/study-epochs")

        epochs_to_add = []
        imported = json.load(jsonfile)

        # Need to sort in order
        def get_order(data):
            return int(data["order"])

        imported.sort(key=get_order)

        for imported_epoch in imported:
            epoch_name = imported_epoch["epoch_name"]
            if self._check_for_duplicate_epoch(imported_epoch, study_epochs):
                self.log.info(
                    f"Study epoch '{epoch_name}' with description '{imported_epoch['description']}' already exists, skipping"
                )
                continue

            data = dict(import_templates.study_epoch)
            for key in data.keys():
                if not key.endswith("uid"):
                    data[key] = imported_epoch.get(key, None)

            # Look up study uid
            # study_name = imported_epoch["study_name"]
            data["study_uid"] = study_uid

            # epoch subtype
            epoch_sub_name = imported_epoch["epoch_subtype_name"]

            uid = self.lookup_ct_term_uid(CODELIST_EPOCH_SUBTYPE, epoch_sub_name)
            if uid:
                self.log.info(
                    f"Found epoch subtype '{epoch_sub_name}' with uid '{uid}'"
                )
                data["epoch_subtype"] = uid
            else:
                self.log.error(
                    f"Unable to find epoch subtype {epoch_sub_name}, skipping this entry"
                )
                continue

            # duration unit, is this used??
            # "duration_unit": null,

            # print(json.dumps(data, indent=2))

            # We need to call preview to get the correctly numbered Epoch
            self.log.info(
                f"Preview study epoch '{epoch_name}' for study '{study_name}' with id '{study_uid}'"
            )
            path = f"/studies/{study_uid}/study-epochs/preview"
            preview_data = {
                "epoch_subtype": data["epoch_subtype"],
                "study_uid": data["study_uid"],
            }

            preview = self.api.simple_post_to_api(
                path, preview_data, "/study-epochs/preview"
            )
            if preview is None:
                self.log.error(
                    f"Unable to preview study epoch {epoch_name}, skipping this entry"
                )
                continue

            # Update epoch from preview result
            data["epoch"] = preview["epoch"]

            path = f"/studies/{study_uid}/study-epochs"
            self.log.info(
                f"Add study epoch '{epoch_name}' as '{preview['epoch_name']}' for study '{study_name}' with id '{study_uid}'"
            )
            if epoch_name != preview["epoch_name"]:
                self.log.warning(
                    f"Study epoch '{epoch_name}' changed name to '{preview['epoch_name']}'"
                )
            self.api.simple_post_to_api(path, data, "/study-epochs")

    @open_file()
    def handle_study_visits(self, jsonfile, study_name):
        self.log.info(f"======== Study visits for study '{study_name}' ========")
        study_uid = self.lookup_study_uid_from_id(study_name)
        study_visits = self.api.get_all_from_api(f"/studies/{study_uid}/study-visits")

        imported = json.load(jsonfile)

        # Need to sort in order
        def get_order(data):
            is_subvisit = data.get("visit_sublabel_reference") is not None
            return float(data["unique_visit_number"]) + 0.1 * float(is_subvisit)

        imported.sort(key=get_order)

        for imported_visit in imported:
            data = dict(import_templates.study_visit)
            if self._check_for_duplicate_visit(imported_visit, study_visits):
                self.log.info(
                    f"Study visit of type '{imported_visit['visit_type_name']}' with timing '{imported_visit['time_value']} {imported_visit['time_unit_name']}' and description '{imported_visit['description']}' already exists, skipping"
                )
                continue
            # else:
            #    print(json.dumps(imported_visit, indent=2))
            #    print(json.dumps(study_visits, indent=2))

            for key in data.keys():
                if not key.endswith("uid"):
                    default = data.get(key, None)
                    data[key] = imported_visit.get(key, default)

            data["study_uid"] = study_uid

            if "study_epoch_name" in imported_visit:
                epoch_name = imported_visit["study_epoch_name"]
            else:
                epoch_name = imported_visit["study_epoch"]["sponsor_preferred_name"]
            data["study_epoch_uid"] = self.lookup_study_epoch_uid(study_uid, epoch_name)
            if data["study_epoch_uid"] is not None:
                self.log.info(
                    f"Found study epoch {epoch_name} with uid {data['study_epoch_uid']}"
                )
            else:
                self.log.error(
                    f"Unable to find study epoch {epoch_name}, skipping this entry"
                )
                continue

            visit_type = imported_visit["visit_type_name"]
            data["visit_type_uid"] = self.lookup_ct_term_uid(
                CODELIST_VISIT_TYPE, visit_type
            )
            if data["visit_type_uid"] is not None:
                self.log.info(
                    f"Found visit type {visit_type} with uid {data['visit_type_uid']}"
                )
            else:
                self.log.error(
                    f"Unable to find visit type {visit_type}, skipping this entry"
                )
                continue

            if "time_reference_name" in imported_visit:
                timeref = imported_visit["time_reference_name"]
            else:
                timeref = imported_visit["time_reference"]["sponsor_preferred_name"]
            if timeref is None:
                data["time_reference_uid"] = None
            else:
                data["time_reference_uid"] = self.lookup_ct_term_uid(
                    CODELIST_TIMEPOINT_REFERENCE, timeref
                )
                if data["time_reference_uid"] is not None:
                    self.log.info(
                        f"Found time ref {timeref} with uid {data['time_reference_uid']}"
                    )
                else:
                    self.log.error(
                        f"Unable to find visit time reference {timeref}, skipping this entry"
                    )
                    continue

            timeunit = imported_visit["time_unit_name"]
            if timeunit is None:
                data["time_unit_uid"] = None
            else:
                try:
                    data["time_unit_uid"] = self.caseless_dict_lookup(
                        self.all_study_times, timeunit
                    )
                    self.log.info(
                        f"Found time unit {timeunit} with uid {data['time_unit_uid']}"
                    )
                except StopIteration:
                    self.log.error(
                        f"Unable to find visit time unit {timeunit}, skipping this entry"
                    )
                    continue

            winunit = imported_visit["visit_window_unit_name"]
            if winunit is None:
                data["visit_window_unit_uid"] = None
            else:
                try:
                    data["visit_window_unit_uid"] = self.caseless_dict_lookup(
                        self.all_study_times, winunit
                    )
                    self.log.info(
                        f"Found time window unit {winunit} with uid {data['visit_window_unit_uid']}"
                    )
                except StopIteration:
                    self.log.error(
                        f"Unable to find visit window unit {winunit}, skipping this entry"
                    )
                    continue

            if "visit_contact_mode_name" in imported_visit:
                contmode = imported_visit["visit_contact_mode_name"]
            else:
                contmode = imported_visit["visit_contact_mode"]["sponsor_preferred_name"]
            data["visit_contact_mode_uid"] = self.lookup_ct_term_uid(
                CODELIST_VISIT_CONTACT_MODE, contmode
            )
            if data["visit_contact_mode_uid"] is not None:
                self.log.info(
                    f"Found visit contact mode {contmode} with uid {data['visit_contact_mode_uid']}"
                )
            else:
                self.log.error(
                    f"Unable to find visit contact mode {contmode}, skipping this entry"
                )
                continue

            if data.get("visit_sublabel_reference") is not None:
                self.log.info(
                    f"Looking up parent visit for subvisit of visit {imported_visit['visit_number']}"
                )
                ref_uid = self._find_parent_visit(
                    study_uid, imported_visit["visit_number"]
                )
                data["visit_sublabel_reference"] = ref_uid

            # Remove any remaining "string" values
            for key, item in data.items():
                if item == "string":
                    # print(f"Cleaning {key}")
                    data[key] = None
            # print(json.dumps(data, indent=2))

            if imported_visit["visit_class"] != "MANUALLY_DEFINED_VISIT":
                del data["visit_number"]
                del data["unique_visit_number"]
                del data["visit_short_name"]
                del data["visit_name"]

            path = f"/studies/{study_uid}/study-visits"
            self.log.info(f"Add study visit with desc '{data['description']}'")
            self.api.simple_post_to_api(path, data, "/study-visits")

    def _find_parent_visit(self, study_uid, visit_number):
        # An alternative is to use the specific endpoint for this purpose: /studies/{uid}/anchor-visits-in-group-of-subvisits
        filt = {
            "visit_subclass": {"v": ["ANCHOR_VISIT_IN_GROUP_OF_SUBV"]},
            "visit_number": {"v": [visit_number]},
        }
        params = {"filters": json.dumps(filt)}
        visits = self.api.get_all_from_api(
            f"/studies/{study_uid}/study-visits", params=params, items_only=True
        )
        if len(visits) == 0:
            return None
        return visits[0]["uid"]

    @open_file()
    def handle_study_arms(self, jsonfile, study_name):
        self.log.info(f"======== Study arms for study '{study_name}' ========")

        study_uid = self.lookup_study_uid_from_id(study_name)
        study_arms = self.api.get_all_from_api(f"/studies/{study_uid}/study-arms")

        imported = json.load(jsonfile)
        for imported_arm in imported:
            if self._check_for_duplicate_arm(imported_arm, study_arms):
                self.log.info(
                    f"Study arm '{imported_arm['name']}' with description '{imported_arm['description']}' already exists, skipping"
                )
                continue

            data = dict(import_templates.study_arm)
            for key in data.keys():
                if not key.endswith("uid"):
                    data[key] = imported_arm.get(key, None)

            armtype = imported_arm.get("arm_type", None)
            if armtype is None:
                armtype = {}
            armtype_name = armtype.get("sponsor_preferred_name", "")
            if armtype_name == "":
                # Is this an old json? Try getting "type"
                armtype_name = imported_arm.get("type", None)
                if not armtype_name:
                    self.log.error(
                        "Unable to get arm type name from imported data, skipping this entry"
                    )
                    continue
            data["arm_type_uid"] = self.lookup_ct_term_uid(
                CODELIST_ARM_TYPE, armtype_name
            )
            if data["arm_type_uid"] is None:
                self.log.error(
                    f"Unable to find study arm type {armtype_name}, skipping this entry"
                )
                continue

            # duration unit, is this used??
            # "duration_unit": null,

            # print(json.dumps(data, indent=2))
            path = f"/studies/{study_uid}/study-arms"
            self.log.info(
                f"Add study arm '{imported_arm['name']}' for study '{study_name}' with id '{study_uid}'"
            )
            self.api.simple_post_to_api(path, data, "/study-arms")

    @open_file()
    def handle_study_branch_arms(self, jsonfile, study_name):
        self.log.info(f"======== Study branch arms for study '{study_name}' ========")

        study_uid = self.lookup_study_uid_from_id(study_name)
        study_arms = self.api.get_all_from_api(f"/studies/{study_uid}/study-arms")
        study_branch_arms = self.api.get_all_from_api(
            f"/studies/{study_uid}/study-branch-arms"
        )

        imported = json.load(jsonfile)
        for imported_branch in imported:
            if self._check_for_duplicate_arm(imported_branch, study_branch_arms):
                self.log.info(
                    f"Study branch arm '{imported_branch['name']}' with description '{imported_branch['description']}' already exists, skipping"
                )
                continue

            data = dict(import_templates.study_branch)
            for key in data.keys():
                if not key.endswith("uid"):
                    data[key] = imported_branch.get(key, None)
            armroot = imported_branch.get("arm_root", {})
            if armroot is None:
                armroot = {}
            arm_name = armroot.get("name", "")

            # TODO!!!
            for arm in study_arms:
                if arm["name"] == arm_name:
                    data["arm_uid"] = arm["arm_uid"]
                    break
            if data["arm_uid"] is None:
                self.log.error(
                    f"Unable to find study arm {arm_name}, skipping this entry"
                )
                continue

            # duration unit, is this used??
            # "duration_unit": null,

            # print(json.dumps(data, indent=2))
            path = f"/studies/{study_uid}/study-branch-arms"
            self.log.info(
                f"Add study branch arm '{imported_branch['name']}' for study '{study_name}' with id '{study_uid}'"
            )
            self.api.simple_post_to_api(path, data, "/study-branch-arms")

    @open_file()
    def handle_study_cohorts(self, jsonfile, study_name):
        self.log.info(f"======== Study cohorts for study '{study_name}' ========")

        study_uid = self.lookup_study_uid_from_id(study_name)
        study_arms = self.api.get_all_from_api(f"/studies/{study_uid}/study-arms")
        study_branch_arms = self.api.get_all_from_api(
            f"/studies/{study_uid}/study-branch-arms"
        )
        # TODO fetch exiting cohorts to check for duplicates
        # study_cohorts = self.api.get_all_from_api(
        #    f"/studies/{study_uid}/study-cohorts"
        # )

        imported = json.load(jsonfile)
        for imported_cohort in imported:
            # TODO check for duplicates and patch if the cohort already exists
            # if self._check_for_duplicate_cohort(imported_cohort, study_cohorts):
            #    self.log.info(
            #        f"Study cohort '{imported_cohort['name']}' with description '{imported_cohort['description']}' already exists, skipping"
            #    )
            #    continue

            data = dict(import_templates.study_cohort)
            for key in data.keys():
                if not key.endswith("uid"):
                    data[key] = imported_cohort.get(key, None)

            arm_uids = []
            branch_arm_uids = []
            if imported_cohort["arm_roots"] is not None:
                for arm_root in imported_cohort["arm_roots"]:
                    arm_name = arm_root["name"]
                    found = False
                    for arm in study_arms:
                        if arm["name"] == arm_name:
                            found = True
                            arm_uids.append(arm["arm_uid"])
                    if not found:
                        self.log.error(
                            f"Unable to find study arm {arm_name}, skipping this entry"
                        )
            if imported_cohort["branch_arm_roots"] is not None:
                for branch_arm_root in imported_cohort["branch_arm_roots"]:
                    branch_arm_name = branch_arm_root["name"]
                    found = False
                    for b_arm in study_branch_arms:
                        if b_arm["name"] == branch_arm_name:
                            found = True
                            branch_arm_uids.append(b_arm["branch_arm_uid"])
                    if not found:
                        self.log.error(
                            f"Unable to find study branch arm {branch_arm_name}, skipping this entry"
                        )
            data["arm_uids"] = arm_uids
            data["branch_arm_uids"] = branch_arm_uids

            path = f"/studies/{study_uid}/study-cohorts"
            self.log.info(
                f"Add study cohort '{imported_cohort['name']}' for study '{study_name}' with id '{study_uid}'"
            )
            self.api.simple_post_to_api(path, data, "/study-cohorts")

    @open_file()
    def handle_study_elements(self, jsonfile, study_name):
        self.log.info(f"======== Study elements for study '{study_name}' ========")
        study_uid = self.lookup_study_uid_from_id(study_name)
        study_elements = self.api.get_all_from_api(
            f"/studies/{study_uid}/study-elements"
        )

        imported = json.load(jsonfile)
        for imported_el in imported:
            if self._check_for_duplicate_element(imported_el, study_elements):
                self.log.info(
                    f"Study element '{imported_el['name']}' with description '{imported_el['description']}' already exists, skipping"
                )
                continue

            data = dict(import_templates.study_element)
            for key in data.keys():
                if not key.endswith("uid"):
                    data[key] = imported_el.get(key, None)

            element_subtype_name = imported_el.get("element_subtype", {}).get(
                "sponsor_preferred_name", ""
            )
            if element_subtype_name == "":
                # Old json files? Try with the old name
                element_subtype_name = imported_el.get("element_subtype_name", "")
            data["element_subtype_uid"] = self.lookup_ct_term_uid(
                CODELIST_ELEMENT_SUBTYPE, element_subtype_name
            )
            if data["element_subtype_uid"] is None:
                self.log.error(
                    f"Unable to find element sub type {element_subtype_name}, skipping this entry"
                )
                continue
            no_treatment_subtypes = ("Screening", "Run-in", "Wash-out", "Follow-up")
            treatment_subtypes = ("Treatment",)

            # TODO why is this called "code"??? makes no sense
            # element_type_name = imported_el["code"]
            if element_subtype_name in no_treatment_subtypes:
                element_type_name = "No Treatment"
            elif element_subtype_name in treatment_subtypes:
                element_type_name = "Treatment"
            else:
                element_type_name = ""

            data["code"] = self.lookup_ct_term_uid(
                CODELIST_ELEMENT_TYPE, element_type_name
            )
            if data["code"] is None:
                self.log.error(
                    f"Unable to find element type {element_type_name}, skipping this entry"
                )
                continue

            if (
                "planned_duration" in imported_el
                and imported_el["planned_duration"] is not None
            ):
                unit_name = imported_el["planned_duration"]["duration_unit_code"][
                    "name"
                ]
                uid = self.lookup_unit_uid(unit_name, subset=UNIT_SUBSET_AGE)
                if uid:
                    data["planned_duration"]["duration_unit_code"]["name"] = unit_name
                    data["planned_duration"]["duration_unit_code"]["uid"] = uid
                    data["planned_duration"]["duration_value"] = imported_el[
                        "planned_duration"
                    ]["duration_value"]
                else:
                    self.log.error(
                        f"Unable to find unit {unit_name}, skipping planned duration for this element"
                    )

            # print(json.dumps(data, indent=2))
            path = f"/studies/{study_uid}/study-elements"
            self.log.info(
                f"Add study arm '{imported_el['name']}' for study '{study_name}' with id '{study_uid}'"
            )
            self.api.simple_post_to_api(path, data, "/study-elements")

    def handle_templates(self):
        self.log.info("======== Syntax templates ========")
        objective_template_json = os.path.join(
            self.import_dir, "objective-templates.json"
        )
        self.handle_all_templates(objective_template_json, "objective")

        criteria_template_json = os.path.join(
            self.import_dir, "criteria-templates.json"
        )
        self.handle_all_templates(criteria_template_json, "criteria")

        endpoint_template_json = os.path.join(
            self.import_dir, "endpoint-templates.json"
        )
        self.handle_all_templates(endpoint_template_json, "endpoint")

        timeframe_template_json = os.path.join(
            self.import_dir, "timeframe-templates.json"
        )
        self.handle_all_templates(timeframe_template_json, "timeframe")

        activity_instruction_template_json = os.path.join(
            self.import_dir, "activity-instruction-templates.json"
        )
        self.handle_all_templates(
            activity_instruction_template_json, "activity_instruction"
        )

        footnote_template_json = os.path.join(
            self.import_dir, "footnote-templates.json"
        )
        self.handle_all_templates(footnote_template_json, "footnote")

        self.log.info("======== Syntax template pre-instances ========")
        objective_template_json = os.path.join(
            self.import_dir, "objective-pre-instances.json"
        )
        self.handle_all_templates(
            objective_template_json, "objective", is_preinstance=True
        )

        criteria_template_json = os.path.join(
            self.import_dir, "criteria-pre-instances.json"
        )
        self.handle_all_templates(
            criteria_template_json, "criteria", is_preinstance=True
        )

        endpoint_template_json = os.path.join(
            self.import_dir, "endpoint-pre-instances.json"
        )
        self.handle_all_templates(
            endpoint_template_json, "endpoint", is_preinstance=True
        )

        activity_instruction_template_json = os.path.join(
            self.import_dir, "activity-instruction-pre-instances.json"
        )
        self.handle_all_templates(
            activity_instruction_template_json,
            "activity_instruction",
            is_preinstance=True,
        )

        footnote_template_json = os.path.join(
            self.import_dir, "footnote-pre-instances.json"
        )
        self.handle_all_templates(
            footnote_template_json, "footnote", is_preinstance=True
        )

    def fill_default_parameter_terms(self, imported_template, data, data_template):
        fieldname = "default_parameter_terms"
        if fieldname in data_template:
            data[fieldname] = []
            parameter_template = data_template[fieldname][0]
            value_template = parameter_template["terms"][0]
            if (
                imported_template.get(fieldname) is not None
                and "0" in imported_template[fieldname]
                and imported_template[fieldname]["0"] is not None
            ):
                for parameter in imported_template[fieldname]["0"]:
                    paramdata = copy.deepcopy(parameter_template)
                    for key in paramdata.keys():
                        paramdata[key] = parameter.get(key, None)
                    paramdata["terms"] = []
                    for val in parameter["terms"]:
                        valuedata = copy.deepcopy(value_template)
                        for key in val.keys():
                            if not key.lower().endswith("uid"):
                                valuedata[key] = val.get(key, None)
                            else:
                                valuedata[
                                    key
                                ] = self.lookup_or_create_parameter_value_uid(val)
                        paramdata["terms"].append(valuedata)
                    # Only include if the parameter has some content
                    if len(paramdata["terms"]) > 0:
                        data[fieldname].append(paramdata)

    @open_file()
    def handle_all_templates(self, jsonfile, template_type, is_preinstance=False):
        self.log.info(f"======== {template_type} templates ========")
        import_data = json.load(jsonfile)
        category_codelist = None
        subcategory_codelist = None
        if template_type == "objective":
            if is_preinstance:
                post_data = import_templates.objective_preinstance
            else:
                post_data = import_templates.objective_template
            category_codelist = CODELIST_OBJECTIVE_CATEGORY
            path = "/objective-templates"
            preinstance_path = "/objective-pre-instances"
        elif template_type == "criteria":
            if is_preinstance:
                post_data = import_templates.criteria_preinstance
            else:
                post_data = import_templates.criteria_template
            category_codelist = CODELIST_CRITERIA_CATEGORY
            subcategory_codelist = CODELIST_CRITERIA_SUBCATEGORY
            type_codelist = CODELIST_CRITERIA_TYPE
            path = "/criteria-templates"
            preinstance_path = "/criteria-pre-instances"
        elif template_type == "endpoint":
            if is_preinstance:
                post_data = import_templates.endpoint_preinstance
            else:
                post_data = import_templates.endpoint_template
            category_codelist = CODELIST_ENDPOINT_CATEGORY
            path = "/endpoint-templates"
            preinstance_path = "/endpoint-pre-instances"
        elif template_type == "timeframe":
            post_data = import_templates.timeframe_template
            path = "/timeframe-templates"
            preinstance_path = None
        elif template_type == "activity_instruction":
            if is_preinstance:
                post_data = import_templates.activity_instruction_preinstance
            else:
                post_data = import_templates.activity_instruction_template
            category_codelist = None
            subcategory_codelist = None
            path = "/activity-instruction-templates"
            preinstance_path = "/activity-instruction-pre-instances"
        elif template_type == "footnote":
            if is_preinstance:
                post_data = import_templates.footnote_preinstance
            else:
                post_data = import_templates.footnote_template
            type_codelist = CODELIST_FOOTNOTE_TYPE
            path = "/footnote-templates"
            preinstance_path = "/footnote-pre-instances"
        else:
            raise RuntimeError(f"Unknown template type {template_type}")

        # Create the template
        for imported_template in import_data:
            data = copy.deepcopy(post_data)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    if key in imported_template:
                        value = imported_template.get(key, None)
                        if not isinstance(value, (dict, list, tuple)):
                            data[key] = value
            shortname = imported_template["name"]

            # Get the library name, default to "Sponsor" if not given
            library_name = imported_template.get("library", {}).get("name", "Sponsor")
            data["library_name"] = library_name

            if len(shortname) > 60:
                shortname = shortname[0:60] + "..."

            if is_preinstance:
                parent_name = imported_template["template_name"]
                parent_shortname = parent_name
                if len(parent_shortname) > 60:
                    parent_shortname = parent_shortname[0:60] + "..."

                type_uid = imported_template.get("template_type_uid")
                type_code = None
                type_name = None
                if type_uid:
                    type_code = type_uid.split("_")[0]
                    type_name = self.lookup_codelist_term_name_from_concept_id(
                        type_codelist, type_code
                    )
                parent_uid = self.lookup_template_uid(
                    parent_name,
                    template_type,
                    subtype=type_name,
                    log=True,
                    shortname=parent_shortname,
                )
                if parent_uid is None:
                    self.log.info(
                        f"Unable to find parent '{parent_shortname}' for pre-instance of type '{template_type}'"
                    )
                    continue
                if (
                    self.lookup_preinstance_uid(
                        imported_template["name"],
                        template_type,
                        subtype_id=type_name,
                        log=True,
                        shortname=shortname,
                    )
                    is not None
                ):
                    self.log.info(
                        f"Skipping existing {template_type} pre-instance with name '{shortname}'"
                    )
                    continue
            else:
                type_name = None
                if "type_uid" in post_data:
                    type_name = imported_template["type"]["name"][
                        "sponsor_preferred_name"
                    ]
                if (
                    self.lookup_template_uid(
                        imported_template["name"],
                        template_type,
                        subtype=type_name,
                        log=True,
                        shortname=shortname,
                    )
                    is not None
                ):
                    self.log.info(
                        f"Skipping existing {template_type} template with name '{shortname}'"
                    )
                    continue

            if not is_preinstance:
                self.fill_default_parameter_terms(imported_template, data, post_data)
            else:
                self.fill_parameter_terms(
                    data, imported_template.get("parameter_terms"), post_data
                )

            if "indication_uids" in post_data:
                data["indication_uids"] = []
                if imported_template.get("indications") is not None:
                    for indication in imported_template["indications"]:
                        name = indication["name"]
                        library = indication["library_name"]
                        uid = self.lookup_dictionary_term_uid(library, name)
                        if uid:
                            data["indication_uids"].append(uid)
            if "category_uids" in post_data:
                data["category_uids"] = []
                if imported_template.get("categories") is not None:
                    for category in imported_template["categories"]:
                        name = category["name"]["sponsor_preferred_name"]
                        uid = self.lookup_codelist_term_uid(category_codelist, name)
                        if uid:
                            data["category_uids"].append(uid)
            if "sub_category_uids" in post_data:
                data["sub_category_uids"] = []
                if imported_template.get("sub_categories") is not None:
                    for category in imported_template["sub_categories"]:
                        name = category["name"]["sponsor_preferred_name"]
                        uid = self.lookup_codelist_term_uid(subcategory_codelist, name)
                        if uid:
                            data["category_uids"].append(uid)
            if "activity_uids" in post_data:
                data["activity_uids"] = []
                if imported_template.get("activities") is not None:
                    for act in imported_template["activities"]:
                        name = act["name"]
                        uid = self.lookup_activity_uid(name)
                        if uid:
                            data["activity_uids"].append(uid)
            if "activity_group_uids" in post_data:
                data["activity_group_uids"] = []
                if imported_template.get("activity_groups") is not None:
                    for group in imported_template["activity_groups"]:
                        name = group["name"]
                        uid = self.lookup_activity_group_uid(name)
                        if uid:
                            data["activity_group_uids"].append(uid)
            if "activity_subgroup_uids" in post_data:
                data["activity_subgroup_uids"] = []
                if imported_template.get("activity_subgroups") is not None:
                    for group in imported_template["activity_subgroups"]:
                        name = group["name"]
                        uid = self.lookup_activity_subgroup_uid(name)
                        if uid:
                            data["activity_subgroup_uids"].append(uid)
            if "type_uid" in post_data:
                name = imported_template["type"]["name"]["sponsor_preferred_name"]
                uid = self.lookup_codelist_term_uid(type_codelist, name)
                if uid:
                    data["type_uid"] = uid
            if "study_objective_uid" in post_data:
                # if imported_template["study_objective"] is not None:
                #    name = imported_template["study_objective"]["objective"]["name"]
                #    uid = self.lookup_study_objective_uid(name, study_uid)
                #    if uid:
                #        data["study_objective_uid"] = uid
                # TODO add this, currently not provided by get endpoint. Used by endpoint templates.
                print("TODO lookup objective")
            if "endpoint_units" in post_data:
                # TODO add this, currently not provided by get endpoint. Used by endpoint templates.
                print("TODO lookup endpoint units")

            # print("====================  Data to post for", template_type, "templates")
            # print(json.dumps(data, indent=2))

            if is_preinstance:
                create_path = f"{path}/{parent_uid}/pre-instances"
                approve_path = preinstance_path
            else:
                create_path = path
                approve_path = path
            res = self.api.simple_post_to_api(create_path, data)
            if res is not None:
                if self.api.approve_item(res["uid"], approve_path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.error(
                    f"Failed to add {template_type} template with name '{shortname}'"
                )

    def fill_parameter_terms(self, new_data, imported_values, post_template):
        data_complete = True
        if imported_values is not None and "parameter_terms" in post_template:
            new_data["parameter_terms"] = []
            parameter_template = post_template["parameter_terms"][0]
            term_template = parameter_template["terms"][0]
            for parameter in imported_values:
                paramdata = copy.deepcopy(parameter_template)
                for key in paramdata.keys():
                    paramdata[key] = parameter.get(key, None)
                paramdata["terms"] = []
                for val in parameter["terms"]:
                    termdata = copy.deepcopy(term_template)
                    uid_found = True
                    for key in val.keys():
                        if not key.lower().endswith("uid"):
                            termdata[key] = val.get(key, None)
                        else:
                            termdata[key] = self.lookup_or_create_parameter_value_uid(
                                val
                            )
                            if termdata[key] is None:
                                self.log.warning(
                                    f"Could not find parameter value '{val.get('name', '')}'"
                                )
                                uid_found = False
                                data_complete = False
                    if uid_found:
                        paramdata["terms"].append(termdata)
                # Only include if the parameter has some content
                if len(paramdata["terms"]) > 0:
                    new_data["parameter_terms"].append(paramdata)
        return data_complete

    def create_timeframe(self, timeframe_data):
        existing_uid = self.lookup_timeframe(timeframe_data["name"])
        if existing_uid is not None:
            return existing_uid
        post_data = import_templates.timeframes
        path = "/timeframes"
        data = copy.deepcopy(post_data)
        for key in data.keys():
            if not key.lower().endswith("uid") and key in timeframe_data:
                value = timeframe_data.get(key, None)
                if not isinstance(value, (dict, list, tuple)):
                    data[key] = value
        self.fill_parameter_terms(
            data, timeframe_data.get("parameter_terms"), post_data
        )
        data["name_override"] = None
        data["library_name"] = timeframe_data["library"]["name"]
        data["timeframe_template_uid"] = self.lookup_template_uid(
            timeframe_data["timeframe_template"]["name"], "timeframe"
        )
        res = self.api.simple_post_to_api(path, data, path)
        if res is not None:
            if self.api.approve_item(res["uid"], path):
                self.log.info("Approve ok")
                self.metrics.icrement(path + "--Approve")
                return res["uid"]
            else:
                self.log.error("Approve failed")
                self.metrics.icrement(path + "--ApproveError")
        else:
            self.log.error(
                f"Failed to add timeframe with name '{timeframe_data['timeframe_template']['name']}'"
            )

    @open_file()
    def handle_study_template_instances(self, jsonfile, template_type, study_name):
        self.log.info(f"======== Study {template_type} for study {study_name} =======")
        study_uid = self.lookup_study_uid_from_id(study_name)
        import_data = json.load(jsonfile)
        if template_type == "objective":
            post_data = import_templates.study_objective
            path = f"/studies/{study_uid}/study-objectives"
            params = None
        elif template_type == "criteria":
            post_data = import_templates.study_criteria
            path = f"/studies/{study_uid}/study-criteria"
            params = {"create_criteria": True}
        elif template_type == "endpoint":
            post_data = import_templates.study_endpoint
            path = f"/studies/{study_uid}/study-endpoints"
            params = None
        # elif template_type == "activity_instruction":
        #    post_data = import_templates.study_activity_instruction
        #    path = f"/studies/{study_uid}/study-activities"
        else:
            raise RuntimeError(f"Unknown type {template_type}")
        mapper = ENDPOINT_TO_KEY_MAP[template_type]
        path = f"/studies/{study_uid}/{mapper['post']}"

        data_key_import = f"{template_type}_data"
        data_key_export = template_type
        # Create the template instance
        for imported_template in import_data:
            instance = imported_template[data_key_export]
            if not instance:
                continue
            instance_name = instance.get("name")
            if (
                self.lookup_study_template_instance_uid(
                    instance_name, study_uid, template_type
                )
                is not None
            ):
                self.log.info(
                    f"Skipping existing {template_type} with name {instance_name}"
                )
                continue
            data = copy.deepcopy(post_data)
            for key in data.keys():
                if not key.lower().endswith("uid") and key in imported_template:
                    value = imported_template.get(key, None)
                    if not isinstance(value, (dict, list, tuple)):
                        data[key] = value
            parameters_complete = self.fill_parameter_terms(
                data[data_key_import],
                instance.get("parameter_terms"),
                post_data[data_key_import],
            )
            if not parameters_complete:
                self.log.error(
                    f"Missing parameter values, skipping template instance '{instance_name}'"
                )
                continue
            if f"{template_type}_template_uid" in post_data[data_key_import]:
                template_name = instance[f"{template_type}_template"]["name"]
                template_uid = self.lookup_template_uid(template_name, template_type)
                if template_uid is None:
                    self.log.error(
                        f"Could not find template '{template_name}' in library, skipping template instance '{instance_name}'"
                    )
                    continue
                data[data_key_import][f"{template_type}_template_uid"] = template_uid
            if "name_override" in post_data[data_key_import]:
                data[data_key_import][
                    "name_override"
                ] = None  # imported_template[data_key_export]["name"]
            if "library_name" in post_data[data_key_import]:
                data[data_key_import]["library_name"] = instance["library"]["name"]
            if "objective_level_uid" in post_data:
                data["objective_level_uid"] = self.lookup_codelist_term_uid(
                    CODELIST_OBJECTIVE_LEVEL,
                    imported_template["objective_level"]["sponsor_preferred_name"],
                )
            if "study_objective_uid" in post_data:
                name = imported_template["study_objective"]["objective"]["name"]
                data["study_objective_uid"] = self.lookup_study_template_instance_uid(
                    name, study_uid, "objective"
                )
            if "endpoint_level_uid" in post_data:
                if imported_template["endpoint_level"] is not None:
                    data["endpoint_level_uid"] = self.lookup_codelist_term_uid(
                        CODELIST_ENDPOINT_LEVEL,
                        imported_template["endpoint_level"]["sponsor_preferred_name"],
                    )
                else:
                    data["endpoint_level_uid"] = None
            if "endpoint_sublevel_uid" in post_data:
                if imported_template["endpoint_sublevel"] is not None:
                    data["endpoint_sublevel_uid"] = self.lookup_codelist_term_uid(
                        CODELIST_ENDPOINT_SUBLEVEL,
                        imported_template["endpoint_sublevel"][
                            "sponsor_preferred_name"
                        ],
                    )
                else:
                    data["endpoint_sublevel_uid"] = None
            if "endpoint_units" in post_data:
                # TODO add this once fixed in api!
                # The endpoint currently doesn't provide the unit name, only uid.
                data["endpoint_units"] = {"units": [], "separator": None}
            if "timeframe_uid" in post_data:
                if imported_template["timeframe"] is not None:
                    data["timeframe_uid"] = self.create_timeframe(
                        imported_template["timeframe"]
                    )
                else:
                    data["timeframe_uid"] = None

            # print("====================  Data to post for", template_type, "study templates")
            # print(json.dumps(data, indent=2))
            # TODO check for duplicates before posting
            res = self.api.simple_post_to_api(path, data, path, params=params)
            if res is None:
                self.log.error(f"Failed to add {template_type} template")

    @open_file()
    def handle_compound_aliases(self, jsonfile):
        self.log.info("======== Compound aliases ========")
        import_data = json.load(jsonfile)
        for alias in import_data:
            data = copy.deepcopy(import_templates.compound_alias)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    value = alias.get(key, None)
                    if not isinstance(value, (dict, list, tuple)):
                        data[key] = value
            data["compound_uid"] = self.lookup_compound_uid(alias["compound"]["name"])
            path = "/concepts/compound-aliases"
            res = self.api.simple_post_to_api(path, data, "/concepts/compound-aliases")
            if res is not None:
                if self.api.approve_item(res["uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add compound alias '{data['name']}'")

    @open_file()
    def handle_compounds(self, jsonfile):
        self.log.info("======== Compounds ========")
        import_data = json.load(jsonfile)
        for comp in import_data:
            data = copy.deepcopy(import_templates.compound)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    if key in comp:
                        value = comp.get(key, None)
                        if not isinstance(value, (dict, list, tuple)):
                            data[key] = value
            for device in comp["delivery_devices"]:
                name = device["name"]
                uid = self.lookup_codelist_term_uid(CODELIST_DELIVERY_DEVICE, name)
                self.append_if_not_none(data["delivery_devices_uids"], uid)
            for disp in comp["dispensers"]:
                name = disp["name"]
                uid = self.lookup_codelist_term_uid(
                    CODELIST_COMPOUND_DISPENSED_IN, name
                )
                self.append_if_not_none(data["dispensers_uids"], uid)
            for val in comp["dose_values"]:
                uid = self.create_or_get_numeric_value(val, UNIT_SUBSET_DOSE)
                self.append_if_not_none(data["dose_values_uids"], uid)
            for val in comp["strength_values"]:
                uid = self.create_or_get_numeric_value(val, UNIT_SUBSET_DOSE)
                self.append_if_not_none(data["strength_values_uids"], uid)
            for val in comp["lag_times"]:
                uid = self.create_or_get_lag_time(val)
                self.append_if_not_none(data["lag_times_uids"], uid)
            for val in comp["dose_frequencies"]:
                # TODO get some data that uses this
                uid = self.create_or_get_numeric_value(val, "TODO")
                self.append_if_not_none(data["dose_frequency_uids"], uid)
            uid = self.create_or_get_numeric_value(comp["half_life"], UNIT_SUBSET_AGE)
            data["half_life_uid"] = uid
            # print(json.dumps(data, indent=2))
            path = "/concepts/compounds"
            res = self.api.simple_post_to_api(path, data, "/concepts/compounds")
            if res is not None:
                if self.api.approve_item(res["uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add compound '{data['name']}'")

    def handle_all_value_concepts(self, base_path):
        self.log.info("======== Handle all value concepts ========")
        for value_type, details in TEMPLATE_PARAM_MAP.items():
            if not details["import"]:
                continue
            ep = details["path"]
            filename = ep.strip("/").replace("/", ".") + ".json"
            filepath = os.path.join(base_path, filename)
            self.handle_value_concept(filepath, value_type)

    @open_file()
    def handle_value_concept(self, jsonfile, value_type):
        self.log.info(f"======== Handle concept {value_type} ========")
        imported = json.load(jsonfile)
        details = TEMPLATE_PARAM_MAP.get(value_type, {})
        path = details.get("path")
        for item in imported:
            name = item.get("name")
            data = copy.deepcopy(details.get("template"))
            for key in data.keys():
                if not key.endswith("uid") and key in item:
                    data[key] = item[key]
            # data["unit_definition_uid"] = TODO, unit name is not included in concept endpoint!
            for key in data.keys():
                if data[key] == "string":
                    data[key] = None
            res = self.api.simple_post_to_api(path=path, body=data)
            if res:
                self.log.info(
                    f"Created value with name '{name}' of type '{value_type}'"
                )
                uid = res.get("uid", None)
                return uid
            else:
                self.log.error(
                    f"Failed to create value with name '{name}' of type '{value_type}'"
                )

    @open_file()
    def handle_study_compounds(self, jsonfile, study_name):
        self.log.info(f"======== Study compounds for study {study_name} ========")
        study_uid = self.lookup_study_uid_from_id(study_name)
        imported = json.load(jsonfile)
        existing = self.fetch_study_compounds(study_uid)
        for item in imported:
            if self._check_for_duplicate_study_compound(item, existing):
                self.log.info(
                    f"Skipping existing study compound '{item['compound_alias']['name']}'"
                )
                continue
            data = dict(import_templates.study_compound)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    data[key] = item.get(key, data[key])
            if item.get("compound_alias") is not None:
                data["compound_alias_uid"] = self.lookup_compound_alias_uid(
                    item["compound_alias"]["name"]
                )
            if item.get("medicinal_product") is not None:
                data["medicinal_product_uid"] = self.lookup_medicinal_product_uid(
                    item["medicinal_product"]["name"]
                )
            if item.get("reason_for_missing_null_value") is not None:
                data["reason_for_missing_null_value_uid"] = self.lookup_ct_term_uid(
                    CODELIST_NULL_FLAVOR, item["reason_for_missing_null_value"]["name"]
                )
            if item.get("type_of_treatment") is not None:
                data["type_of_treatment_uid"] = self.lookup_codelist_term_uid(
                    CODELIST_TYPE_OF_TREATMENT, item["type_of_treatment"]["name"]
                )
            # Remove any remaining "string" values
            for key, val in data.items():
                if val == "string":
                    # print(f"Cleaning {key}")
                    data[key] = None
            # print(json.dumps(data, indent=2))
            # TODO check for existing to avoid duplicates! Need to check nearly all fields..
            path = f"/studies/{study_uid}/study-compounds"
            self.log.info(
                f"Add study compound '{item['compound_alias']['name']}' for study '{study_name}' with id '{study_uid}'"
            )
            self.api.simple_post_to_api(path, data)

    @open_file()
    def get_study_activity_names(self, jsonfile):
        self.log.info(f"======== Mapping study activity uids to names ========")
        activities = json.load(jsonfile)
        names = {}
        for activity in activities:
            activity_name = activity.get("activity", {}).get("name")
            group_name = activity.get("study_activity_group", {}).get(
                "activity_group_name"
            )
            subgroup_name = activity.get("study_activity_subgroup", {}).get(
                "activity_subgroup_name"
            )
            uid = activity.get("study_activity_uid")
            names[uid] = {
                "activity": activity_name,
                "group": group_name,
                "subgroup": subgroup_name,
            }
        return names

    @open_file()
    def get_study_visit_names(self, jsonfile):
        self.log.info(f"======== Mapping study visit uids to names ========")
        visits = json.load(jsonfile)
        names = {}
        for visit in visits:
            name = visit.get("visit_name")
            uid = visit.get("uid")
            names[uid] = name
        return names

    @open_file()
    def handle_study_activity_schedules(
        self, jsonfile, visit_names, activity_names, study_name
    ):
        self.log.info(
            f"======== Study activity schedules for study {study_name} ========"
        )

        study_uid = self.lookup_study_uid_from_id(study_name)
        imported = json.load(jsonfile)
        for item in imported:
            data = dict(import_templates.study_activity_schedule)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    data[key] = item.get(key, data[key])

            activity_name = activity_names.get(item["study_activity_uid"])

            visit_name = visit_names.get(item["study_visit_uid"])

            data["study_activity_uid"] = self.lookup_study_activity_uid(
                study_uid,
                activity_name["activity"],
                group_name=activity_name["group"],
                subgroup_name=activity_name["subgroup"],
            )
            if not data["study_activity_uid"]:
                self.log.error(
                    f"Unable to find activity '{activity_name['activity']}' in group '{activity_name['group']}', subgroup '{activity_name['subgroup']}' for visit '{visit_name}'"
                )
                continue
            data["study_visit_uid"] = self.lookup_study_visit_uid(study_uid, visit_name)
            if not data["study_visit_uid"]:
                self.log.error(f"Unable to find study visit with name '{visit_name}'")
                continue
            path = f"/studies/{study_uid}/study-activity-schedules"
            self.log.info(
                f"Schedule study activity {data['study_activity_uid']}, name '{activity_name['activity']}', group '{activity_name['group']}', subgroup '{activity_name['subgroup']}' to visit '{visit_name}'"
            )
            self.api.simple_post_to_api(path, data)

    @open_file()
    def handle_dictionaries(self, jsonfile, dict_name):
        self.log.info(f"======== Dictionary {dict_name} ========")
        imported = json.load(jsonfile)
        codelist_uid = self.lookup_dictionary_uid(dict_name)
        existing_terms = self.fetch_dictionary_terms(dict_name)
        existing_names = [term["name"] for term in existing_terms]
        for term in imported:
            name = term.get("name")
            if name in existing_names:
                self.log.info(f"Skipping existing term '{name}'")
                continue
            data = dict(import_templates.dictionary_term)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    data[key] = term.get(key, data[key])
            data["codelist_uid"] = codelist_uid

            path = "/dictionaries/terms"
            self.log.info(
                f"Adding term '{name}' to dictionary '{dict_name}' with uid '{codelist_uid}'"
            )
            res = self.api.simple_post_to_api(path, data)
            if res is not None:
                if self.api.approve_item(res["term_uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add ct term '{data['name']}'")

    @open_file()
    def handle_ct_extensions(self, jsonfile, codelist_name):
        self.log.info(f"======== CT extensions for {codelist_name} ========")
        imported = json.load(jsonfile)
        codelist_uid = self.lookup_ct_codelist_uid(codelist_name)
        existing_terms = self.fetch_codelist_terms(CODELIST_UNIT)
        existing_names = [
            term["name"]["sponsor_preferred_name"] for term in existing_terms
        ]
        for term in imported:
            name = term.get("name", {}).get("sponsor_preferred_name")
            if name in existing_names:
                self.log.info(f"Skipping existing term '{name}'")
                continue
            data = dict(import_templates.ct_term)
            data["catalogue_name"] = term.get("catalogue_name")
            data["codelist_uid"] = codelist_uid
            data["code_submission_value"] = term.get("attributes", {}).get(
                "code_submission_value"
            )
            data["name_submission_value"] = term.get("attributes", {}).get(
                "name_submission_value"
            )
            data["nci_preferred_name"] = term.get("attributes", {}).get(
                "nci_preferred_name"
            )
            data["definition"] = term.get("attributes", {}).get("definition")
            data["sponsor_preferred_name"] = term.get("name", {}).get(
                "sponsor_preferred_name"
            )
            data["sponsor_preferred_name_sentence_case"] = term.get("name", {}).get(
                "sponsor_preferred_name_sentence_case"
            )
            data["order"] = term.get("name", {}).get("order")
            data["library_name"] = term.get("library_name")

            path = "/ct/terms"
            self.log.info(
                f"Adding term '{name}' to codelist '{codelist_name}' with uid '{codelist_uid}'"
            )
            res = self.api.simple_post_to_api(path, data)
            if res is not None:
                if self.api.approve_item_names_and_attributes(res["term_uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(
                    f"Failed to add ct term '{data['sponsor_preferred_name']}'"
                )

    @open_file()
    def handle_unit_definitions(self, jsonfile):
        self.log.info("======== Unit definitions ========")
        imported = json.load(jsonfile)
        for unit in imported:
            name = unit["name"]
            existing = self.lookup_concept_uid(name, "unit-definitions")
            if existing:
                self.log.info(f"Skipping existing unit '{name}'")
                continue
            data = dict(import_templates.unit_definition)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    data[key] = unit.get(key, data[key])
            data["ct_units"] = []
            for ct in unit["ct_units"]:
                uid = self.lookup_ct_term_uid(CODELIST_UNIT, ct["name"])
                if uid is not None:
                    data["ct_units"].append(uid)
            data["unit_subsets"] = []
            for ct in unit["unit_subsets"]:
                uid = self.lookup_ct_term_uid(CODELIST_UNIT_SUBSET, ct["name"])
                if uid is not None:
                    data["unit_subsets"].append(uid)
            if unit["ucum"] is not None:
                data["ucum"] = self.lookup_dictionary_term_uid(
                    "UCUM", unit.get("ucum", {}).get("name", None)
                )
            if unit["unit_dimension"] is not None:
                data["unit_dimension"] = self.lookup_codelist_term_uid(
                    CODELIST_UNIT_DIMENSION,
                    unit.get("unit_dimension", {}).get("name", None),
                )
            path = "/concepts/unit-definitions"
            res = self.api.simple_post_to_api(path, data)
            if res is not None:
                if self.api.approve_item(res["uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add unit definition '{data['name']}'")

    @open_file()
    def handle_activity_groups(self, jsonfile):
        self.log.info("======== Activity groups ========")
        imported = json.load(jsonfile)
        existing_groups = self.fetch_all_activity_groups()
        existing_names = list(existing_groups.keys())
        for group in imported:
            name = group["name"]
            if name in existing_names:
                self.log.info(f"Skipping existing activity group '{name}'")
                continue
            data = dict(import_templates.activity_groups)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    data[key] = group.get(key, data[key])
            path = "/concepts/activities/activity-groups"
            res = self.api.simple_post_to_api(path, data)
            if res is not None:
                if self.api.approve_item(res["uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add activity '{data['name']}'")

    @open_file()
    def handle_activity_subgroups(self, jsonfile):
        self.log.info("======== Activity sub groups ========")
        imported = json.load(jsonfile)
        existing_subgroups = self.fetch_all_activity_subgroups()
        existing_names = list(existing_subgroups.keys())
        for subgroup in imported:
            name = subgroup["name"]
            if name in existing_names:
                # TODO support patching
                self.log.info(f"Skipping existing activity sub group '{name}'")
                continue
            data = copy.deepcopy(import_templates.activity_subgroups)
            for key in data.keys():
                if not key.lower().endswith("uid") and not isinstance(
                    data[key], (list, dict, tuple)
                ):
                    data[key] = subgroup.get(key, data[key])

            if subgroup.get("activity_groups") is not None:
                for group in subgroup["activity_groups"]:
                    uid = self.lookup_activity_group_uid(group["name"])
                    if uid:
                        data["activity_groups"].append(uid)
            if len(data["activity_groups"]) == 0:
                self.log.warning(f"Skipping subgroup '{name}' because it lacks a group")
                continue
            path = "/concepts/activities/activity-sub-groups"
            res = self.api.simple_post_to_api(path, data)
            if res is not None:
                if self.api.approve_item(res["uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add activity '{data['name']}'")

    @open_file()
    def handle_activities(self, jsonfile):
        self.log.info("======== Activities ========")
        imported = json.load(jsonfile)
        existing_activities = self.fetch_all_activities()
        existing_names = list(existing_activities.keys())
        for activity in imported:
            name = activity["name"]
            if name in existing_names:
                self.log.info(f"Skipping existing activity '{name}'")
                continue
            data = dict(import_templates.activity)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    data[key] = activity.get(key, data[key])

            data["activity_groupings"] = []
            if activity.get("activity_groupings") is not None:
                for grouping in activity["activity_groupings"]:
                    grp_name = grouping["activity_group_name"]
                    subgrp_name = grouping["activity_subgroup_name"]
                    group_uid = self.lookup_activity_group_uid(grp_name)
                    subgroup_uid = self.lookup_activity_subgroup_uid(subgrp_name)
                    if group_uid and subgroup_uid:
                        data["activity_groupings"].append(
                            {
                                "activity_group_uid": group_uid,
                                "activity_subgroup_uid": subgroup_uid,
                            }
                        )

            if len(data["activity_groupings"]) == 0:
                self.log.warning(
                    f"Skipping activity '{name}' because it lacks a grouping"
                )
                continue

            path = "/concepts/activities/activities"
            res = self.api.simple_post_to_api(path, data)
            if res is not None:
                if self.api.approve_item(res["uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add activity '{data['name']}'")

    def run(self):
        self.log.info("Migrating json mock data")

        if MDR_MIGRATION_EXPORTED_PROGRAMMES:
            programmes_json = os.path.join(self.import_dir, "clinical-programmes.json")
            self.handle_clinical_programmes(programmes_json)
        else:
            self.log.info("Skipping clinical programmes")

        if MDR_MIGRATION_EXPORTED_BRANDS:
            brands_json = os.path.join(self.import_dir, "brands.json")
            self.handle_brands(brands_json)
        else:
            self.log.info("Skipping brands")

        # Dictionaries
        if MDR_MIGRATION_EXPORTED_DICTIONARIES:
            snomed_json = os.path.join(self.import_dir, "dictionaries.SNOMED.json")
            self.handle_dictionaries(snomed_json, "SNOMED")
            unii_json = os.path.join(self.import_dir, "dictionaries.UNII.json")
            self.handle_dictionaries(unii_json, "UNII")
            medrt_json = os.path.join(self.import_dir, "dictionaries.MED-RT.json")
            self.handle_dictionaries(medrt_json, "MED-RT")
            ucum_json = os.path.join(self.import_dir, "dictionaries.UCUM.json")
            self.handle_dictionaries(ucum_json, "UCUM")

        # Unit definitions
        if MDR_MIGRATION_EXPORTED_UNITS:
            units_ct_json = os.path.join(self.import_dir, "ct.terms.Unit.json")
            self.handle_ct_extensions(units_ct_json, "Unit")
        else:
            self.log.info("Skipping sponsor defined units")

        # Unit definitions
        if MDR_MIGRATION_EXPORTED_UNITS:
            units_json = os.path.join(self.import_dir, "concepts.unit-definitions.json")
            self.handle_unit_definitions(units_json)
        else:
            self.log.info("Skipping unit definitions")

        # Value concepts
        if MDR_MIGRATION_EXPORTED_CONCEPT_VALUES:
            self.handle_all_value_concepts(self.import_dir)
        else:
            self.log.info("Skipping concept values")

        # Activities
        if MDR_MIGRATION_EXPORTED_ACTIVITIES:
            act_grp_json = os.path.join(
                self.import_dir, "concepts.activities.activity-groups.json"
            )
            self.handle_activity_groups(act_grp_json)
            act_subgrp_json = os.path.join(
                self.import_dir, "concepts.activities.activity-sub-groups.json"
            )
            self.handle_activity_subgroups(act_subgrp_json)
            act_json = os.path.join(
                self.import_dir, "concepts.activities.activities.json"
            )
            self.handle_activities(act_json)
        else:
            self.log.info("Skipping activities")

        # TODO Activity instances

        # Compounds and compound aliases
        if MDR_MIGRATION_EXPORTED_COMPOUNDS:
            compounds_json = os.path.join(self.import_dir, "concepts.compounds.json")
            self.handle_compounds(compounds_json)
            comp_alias_json = os.path.join(
                self.import_dir, "concepts.compound-aliases.json"
            )
            self.handle_compound_aliases(comp_alias_json)
        else:
            self.log.info("Skipping compounds")

        # Syntax templates
        if MDR_MIGRATION_EXPORTED_TEMPLATES:
            self.handle_templates()
        else:
            self.log.info("Skipping syntax templates")

        # Projects
        if MDR_MIGRATION_EXPORTED_PROJECTS:
            self.handle_projects(IMPORT_PROJECTS)
        else:
            self.log.info("Skipping projects")

        # Studies with study design
        if MDR_MIGRATION_EXPORTED_STUDIES:
            studies_json = os.path.join(self.import_dir, "studies.json")
            self.handle_studies(studies_json)
        else:
            self.log.info("Skipping studies")

        self.log.info("Done migrating json mock data")


def main():
    metr = Metrics()
    migrator = MockdataJson(metrics_inst=metr)
    migrator.run()
    migrator.print_cache_stats()
    metr.print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="run_import_mockdatajson.py")
    parser.add_argument(
        "-l",
        "--limit",
        nargs="*",
        choices=[
            PROJECTS,
            CLINICAL_PROGRAMMES,
            BRANDS,
            ACTIVITIES,
            ACTIVITY_INSTANCES,
            UNITS,
            COMPOUNDS,
            TEMPLATES,
            STUDIES,
            CONCEPT_VALUES,
            DICTIONARIES,
        ],
        help="Limit the import to the given data types",
    )
    parser.add_argument(
        "-s",
        "--study",
        nargs="*",
        help="Limit the import to the given study numbers",
        type=int,
    )
    args = parser.parse_args()
    print(args)
    if args.limit:
        if PROJECTS in args.limit:
            MDR_MIGRATION_EXPORTED_PROJECTS = True
        else:
            MDR_MIGRATION_EXPORTED_PROJECTS = False

        if CLINICAL_PROGRAMMES in args.limit:
            MDR_MIGRATION_EXPORTED_PROGRAMMES = True
        else:
            MDR_MIGRATION_EXPORTED_PROGRAMMES = False

        if BRANDS in args.limit:
            MDR_MIGRATION_EXPORTED_BRANDS = True
        else:
            MDR_MIGRATION_EXPORTED_BRANDS = False

        if ACTIVITIES in args.limit:
            MDR_MIGRATION_EXPORTED_ACTIVITIES = True
        else:
            MDR_MIGRATION_EXPORTED_ACTIVITIES = False

        if ACTIVITY_INSTANCES in args.limit:
            MDR_MIGRATION_EXPORTED_ACTIVITY_INSTANCES = True
        else:
            MDR_MIGRATION_EXPORTED_ACTIVITY_INSTANCES = False

        if UNITS in args.limit:
            MDR_MIGRATION_EXPORTED_UNITS = True
        else:
            MDR_MIGRATION_EXPORTED_UNITS = False

        if COMPOUNDS in args.limit:
            MDR_MIGRATION_EXPORTED_COMPOUNDS = True
        else:
            MDR_MIGRATION_EXPORTED_COMPOUNDS = False

        if TEMPLATES in args.limit:
            MDR_MIGRATION_EXPORTED_TEMPLATES = True
        else:
            MDR_MIGRATION_EXPORTED_TEMPLATES = False

        if STUDIES in args.limit:
            MDR_MIGRATION_EXPORTED_STUDIES = True
        else:
            MDR_MIGRATION_EXPORTED_STUDIES = False

        if CONCEPT_VALUES in args.limit:
            MDR_MIGRATION_EXPORTED_CONCEPT_VALUES = True
        else:
            MDR_MIGRATION_EXPORTED_CONCEPT_VALUES = False

        if DICTIONARIES in args.limit:
            MDR_MIGRATION_EXPORTED_DICTIONARIES = True
        else:
            MDR_MIGRATION_EXPORTED_DICTIONARIES = False

    if args.study:
        INCLUDE_STUDY_NUMBERS = ",".join([str(study) for study in args.study])
        MDR_MIGRATION_INCLUDE_DUMMY_STUDY = True
        MDR_MIGRATION_INCLUDE_EXAMPLE_DESIGNS = True

    main()
