import csv
import re

from .functions.parsers import map_boolean
from .functions.utils import load_env
from .utils.importer import BaseImporter, open_file
from .utils.metrics import Metrics

metrics = Metrics()

API_HEADERS = {"Accept": "application/json"}

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False") == "True"
API_BASE_URL = load_env("API_BASE_URL")

MDR_MIGRATION_STUDY = load_env("MDR_MIGRATION_STUDY")
MDR_MIGRATION_STUDY_TYPE = load_env("MDR_MIGRATION_STUDY_TYPE")
MDR_MIGRATION_PROJECTS = load_env("MDR_MIGRATION_PROJECTS")

MDR_MOCKUP_OBJECTIVES_OBJECTS = load_env("MDR_MOCKUP_OBJECTIVES_OBJECTS")
MDR_MOCKUP_ENDPOINTS_OBJECTS = load_env("MDR_MOCKUP_ENDPOINTS_OBJECTS")
MDR_MOCKUP_TIMEFRAMES_OBJECTS = load_env("MDR_MOCKUP_TIMEFRAMES_OBJECTS")
MDR_MOCKUP_STUDY_OBJECTIVES = load_env("MDR_MOCKUP_STUDY_OBJECTIVES")
MDR_MOCKUP_STUDY_ENDPOINTS = load_env("MDR_MOCKUP_STUDY_ENDPOINTS")


# ---------------------------------------------------------------
# ETL for mockup
# ---------------------------------------------------------------
#
# Library objects
objective_template_mapper = {
    "OBJECTIVE": lambda row, headers: {
        "path": "/objective-templates",
        "body": {
            "name": row[headers.index("name")],
            "library_name": row[headers.index("library")],
            "indication_uids": [],
            "category_uids": [],
        },
    }
}

objective_mapper = {
    "OBJECTIVE": lambda row, headers: {
        "path": "/objectives",
        "name": row[headers.index("name")],
        "library_name": row[headers.index("library")],
        "first_value": row[headers.index("first_value")],
        "first_conjunction": row[headers.index("first_conjunction")],
        "second_value": row[headers.index("second_value")],
        "second_conjunction": row[headers.index("second_conjunction")],
    }
}

endpoint_template_mapper = {
    "ENDPOINT": lambda row, headers: {
        "path": "/endpoint-templates",
        "body": {
            "name": row[headers.index("name")],
            "library_name": row[headers.index("library")],
        },
    }
}

endpoint_mapper = {
    "ENDPOINT": lambda row, headers: {
        "path": "/endpoints",
        "name": row[headers.index("name")],
        "library_name": row[headers.index("library")],
        "first_value": row[headers.index("first_value")],
        "first_conjunction": row[headers.index("first_conjunction")],
        "second_value": row[headers.index("second_value")],
        "second_conjunction": row[headers.index("second_conjunction")],
    }
}

timeframe_template_mapper = {
    "TIMEFRAME": lambda row, headers: {
        "path": "/timeframe-templates",
        "body": {
            "name": row[headers.index("name")],
            "library_name": row[headers.index("library")],
        },
    }
}

timeframe_mapper = {
    "TIMEFRAME": lambda row, headers: {
        "path": "/timeframes",
        "name": row[headers.index("name")],
        "library_name": row[headers.index("library")],
        "first_value": row[headers.index("first_value")],
        "first_conjunction": row[headers.index("first_conjunction")],
        "second_value": row[headers.index("second_value")],
        "second_conjunction": row[headers.index("second_conjunction")],
    }
}

# Study
study_mapper = {
    "STUDY": lambda row, headers: {
        "path": "/studies",
        "body": {
            "study_number": row[headers.index("IMPACT_NUM")],
            "study_acronym": None,  # row[headers.index("TRL_ID")]
            "project_number": row[headers.index("PROJ")],
        },
        "patch": {
            "ct_gov_id": row[headers.index("CLINICAL_TRIALS_GOV")],
            "eudract_id": row[headers.index("EUDRACT_NUM")],
        },
    },
    "STUDY_TYPE": lambda row, headers: {
        "patch": {
            "study_number": row[headers.index("IMPACT_NUM")],
            "study_define_param_name": row[headers.index("TSPARAM")],
            "c_value": row[headers.index("TSVAL")],
            "c_code": row[headers.index("TSVALCD")],
        },
        "component_mappings": {
            "Intervention Model": "study_intervention",
            "Trial is Randomized": "study_intervention",
            "Trial Blinding Schema": "study_intervention",
            "Control Type Response": "study_intervention",
            "Trial Title": "study_description",
            "Trial Phase Classification": "high_level_study_design",
            "Trial Type Response": "high_level_study_design",
        },
        "parameter_mappings": {
            "Intervention Model": "intervention_model_code",
            "Trial is Randomized": "is_trial_randomised",
            "Trial Blinding Schema": "trial_blinding_schema_code",
            "Control Type Response": "control_type_code",
            "Trial Title": "study_title",
            "Trial Phase Classification": "trial_phase_code",
            "Trial Type Response": "trial_type_codes",
        },
    },
}


# project
project_mapper = {
    "PROJECT": lambda row, headers: {
        "path": "/projects",
        "clinical_programme_path": "/clinical-programmes",
        "body": {
            "project_number": row[headers.index("project_code")],
            "name": row[headers.index("project_name")],
            "brand_name": row[headers.index("brand_name")],
            "description": row[headers.index("description")] or None,
            "clinical_programme_uid": "temp",
        },
        "clinical_programme_body": {
            "name": row[headers.index("clinical_programme_name")]
        },
    }
}


class Mockdata(BaseImporter):
    logging_name = "mockdata"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)
        self.all_activity_instances = self.api.get_all_activity_objects(
            "activity-instances"
        )
        self.template_parameters_dict = self.get_template_parameter_values()
        self.all_studies_dict = self.api.get_studies_as_dict()

    ### Helper functions
    def get_template_parameter_values(self):
        values = {}
        for res in self.all_activity_instances:
            values[res["name"]] = res
        return values

    # Handler for templates for objective, timeframe and endpoint
    def handle_templates(self, csvfile, mapper):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        for row in readCSV:
            data = mapper(row, headers)
            self.log.info(f"Adding template '{data['body']['name']}'")
            res = self.api.post_to_api(data)
            if res is not None:
                if self.api.approve_item(res["uid"], data["path"]):
                    self.log.info(f"Approved template '{data['body']['name']}'")
                    self.metrics.icrement(data["path"] + "--Approve")
                else:
                    self.log.error(
                        f"Failed to approve template '{data['body']['name']}'"
                    )
                    self.metrics.icrement(data["path"] + "--ApproveError")

    # Handler for objective, timeframe and endpoint
    def general_handler(self, csvfile, objecttype, mapper):
        self.log.info(f"Fetching existing templates for {objecttype}")
        templates = self.api.get_templates_as_dict(f"/{objecttype}-templates")

        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        for row in readCSV:
            _class = objecttype.upper()
            data = mapper[_class](row, headers)
            # get the objectives
            if data["name"] in templates:
                template = templates[data["name"]]
            else:
                self.log.error(
                    "%s template with name %s is not found", objecttype, data["name"]
                )
                self.metrics.icrement(data["path"] + "--ERROR")
                continue
            # get the values correctly with the conjections
            parameter_values = []
            types = []
            for temp_type in re.findall("\[.*?\]", template["name"]):
                types.append(temp_type.replace("[", "").replace("]", ""))

            # first value
            if data["first_value"]:
                first_value = data["first_value"]
                if "+" in first_value:
                    all_values = first_value.split("+")
                else:
                    all_values = [first_value]
                values = self.create_values(all_values, types[0])
                if values is None:
                    continue
                if data["first_conjunction"]:
                    conjunction = data["first_conjunction"]
                else:
                    conjunction = ""
                parameter_values.append(
                    {"values": values, "conjunction": conjunction, "position": 1}
                )
            if data["second_value"]:
                second_value = data["second_value"]
                if "+" in second_value:
                    all_values = second_value.split()
                else:
                    all_values = [second_value]
                values = self.create_values(all_values, types[1])
                if values is None:
                    continue
                if data["second_conjunction"]:
                    conjunction = data["second_conjunction"]
                else:
                    conjunction = ""
                parameter_values.append(
                    {"values": values, "conjunction": conjunction, "position": 2}
                )
            body = {
                "parameter_values": parameter_values,
                f"{objecttype}_template_uid": template["uid"],
                "library_name": data["library_name"],
            }
            self.log.info(
                f"Adding '{objecttype}' with name '{data['name']}' to library '{data['library_name']}'"
            )
            res = self.api.post_to_api({"body": body, "path": data["path"]})
            if res is not None:
                if self.api.approve_item(res["uid"], data["path"]):
                    self.log.info("Approve ok")
                    self.metrics.icrement(data["path"] + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(data["path"] + "--ApproveError")
            else:
                self.log.error(
                    f"Failed to add '{objecttype}' with name '{data['name']}' to library '{data['library_name']}'"
                )

    def create_values(self, all_values, value_type):
        values = []
        index = 1
        for value_name in all_values:
            if value_name in self.template_parameters_dict:
                value = self.template_parameters_dict[value_name]
            else:
                self.log.warning(
                    "template parameter with name %s is not found", value_name
                )
                # self.metrics.icrement(data["path"] + "--TEMPLATE_PARAMATER_VALUE_DOES_NOT_EXISTS")
                return None
            new_value = {}
            new_value["uid"] = value["uid"]
            new_value["name"] = value["name"]
            new_value["type"] = value_type
            new_value["index"] = index
            index += 1
            values.append(new_value)
        return values

    # Adding objevtive templates and approving them
    @open_file()
    def handle_objective_templates(self, csvfile):
        mapper = objective_template_mapper["OBJECTIVE"]
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        snomed_uid = self.api.find_dictionary_uid("SNOMED")
        all_categories = self.api.get_terms_for_codelist_name("Objective Category")

        for row in readCSV:
            data = mapper(row, headers)
            indications = row[headers.index("indication")]
            if indications != "":
                for ind in indications.split("|"):
                    uid = self.api.find_dictionary_item_uid_from_name(snomed_uid, ind)
                    if uid is not None:
                        data["body"]["indication_uids"].append(uid)
                    else:
                        self.log.warning(f"Unable to find indication {ind}")

            categories = row[headers.index("category")]
            if categories != "":
                for cat in categories.split("|"):
                    uid = self.get_uid_for_sponsor_preferred_name(all_categories, cat)
                    if uid is not None:
                        data["body"]["category_uids"].append(uid)
                    else:
                        self.log.warning(f"Unable to find category {cat}")
            testing = row[headers.index("testing")]
            if testing.lower() == "yes":
                data["body"]["confirmatory_testing"] = True
            elif testing.lower() == "no":
                data["body"]["confirmatory_testing"] = False
            self.log.info(f"Adding template '{data['body']['name']}'")
            res = self.api.post_to_api(data)
            if res is not None:
                if self.api.approve_item(res["uid"], data["path"]):
                    self.log.info(f"Approved template '{data['body']['name']}'")
                    self.metrics.icrement(data["path"] + "--Approve")
                else:
                    self.log.error(
                        f"Failed to approve template '{data['body']['name']}'"
                    )
                    self.metrics.icrement(data["path"] + "--ApproveError")

    # Adding objectives and approving them
    @open_file()
    def handle_objectives(self, csvfile):
        mapper = objective_mapper
        self.general_handler(csvfile, "objective", mapper)

    # Adding endpoint templates and approving them
    @open_file()
    def handle_endpoint_templates(self, csvfile):
        mapper = endpoint_template_mapper["ENDPOINT"]
        self.handle_templates(csvfile, mapper)

    # Adding endpoint and approving them
    @open_file()
    def handle_endpoints(self, csvfile):
        mapper = endpoint_mapper
        self.general_handler(csvfile, "endpoint", mapper)

    # Adding timeframe templates and approving them
    @open_file()
    def handle_timeframe_templates(self, csvfile):
        mapper = timeframe_template_mapper["TIMEFRAME"]
        self.handle_templates(csvfile, mapper)

    # Adding timeframe and approving them
    @open_file()
    def handle_timeframes(self, csvfile):
        mapper = timeframe_mapper
        self.general_handler(csvfile, "timeframe", mapper)

    # Study objectives
    @open_file()
    def handle_study_objectives(self, csvfile):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        all_studies_dict = self.api.get_studies_as_dict()
        for row in readCSV:
            study_id = row[headers.index("study_id")]
            if study_id in all_studies_dict:
                study = all_studies_dict[study_id]
            else:
                self.log.warning("Study with Study Id '%s' is not found", study_id)
                self.metrics.icrement(
                    "/study-objectives/" + "--STUDY_ID_DOES_NOT_EXISTS"
                )
                continue
            objective_name = row[headers.index("objective")]
            objective = self.api.find_object_by_key(objective_name, "/objectives")
            if objective is None:
                objective_uid = ""
            else:
                objective_uid = objective["uid"]
            objective_level = row[headers.index("objective_level")]
            body = {
                "objective_uid": objective_uid,
                "objective_level_uid": objective_level,
            }
            self.log.info(
                f"Add study objective '{objective_name}' for study id '{study_id}'"
            )
            path = f"/studies/{study['uid']}/study-objectives"
            self.api.simple_post_to_api(path, body, "/study-objectives")

    # Study endpoints
    @open_file()
    def handle_study_endpoints(self, csvfile):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        all_studies_dict = self.api.get_studies_as_dict()
        for row in readCSV:
            body = {}
            study_id = row[headers.index("study_id")]
            if study_id in all_studies_dict:
                study = all_studies_dict[study_id]
            else:
                self.log.warning("Study with Study Id '%s' is not found", study_id)
                self.metrics.icrement(
                    "/study-endpoints/" + "--STUDY_ID_DOES_NOT_EXISTS"
                )
                continue
            endpoint_name = row[headers.index("endpoint")]
            endpoint = self.api.find_object_by_key(endpoint_name, "/endpoints")
            if endpoint is not None:
                body["endpoint_uid"] = endpoint["uid"]
            timeframe_name = row[headers.index("timeframe")]
            timeframe = self.api.find_object_by_key(timeframe_name, "/timeframes")
            if timeframe is not None:
                body["timeframe_uid"] = timeframe["uid"]
            units = row[headers.index("units")].split("+")
            if not len(units) == 1 and units[0] == 1:
                separator = row[headers.index("unit_seperator")]
                body["endpoint_units"] = {"units": units, "separator": separator}
            endpoint_level = row[headers.index("endpoint_level")]
            if endpoint_level != "":
                body["endpoint_level"] = endpoint_level
            # study objective
            all_study_objectives = self.api.get_study_objectives_for_study(study["uid"])
            study_objective = row[headers.index("study_objective")]
            if study_objective in all_study_objectives:
                body["study_objective_uid"] = all_study_objectives[study_objective]
            path = f"/studies/{study['uid']}/study-endpoints"
            self.log.info(
                f"Add study endpoint '{endpoint_name}' for study id '{study_id}'"
            )
            self.api.simple_post_to_api(path, body, "/study-endpoints")

    def update_data(
        self, patch, study_data
    ):  # smarter solution for this when I know more about the data to patch
        study_data["current_metadata"]["identification_metadata"][
            "registry_identifiers"
        ]["ct_gov_id"] = patch["ct_gov_id"]
        study_data["current_metadata"]["identification_metadata"][
            "registry_identifiers"
        ]["eudract_id"] = patch["eudract_id"]

    @open_file()
    def handle_study(self, csvfile):
        readCSV = csv.reader(csvfile, delimiter=",")
        study_headers = next(readCSV)
        # Fetching existing data
        all_studies = self.api.get_all_identifiers(
            self.api.get_all_from_api("/studies"), "current_metadata"
        )
        all_studies = [
            study["identification_metadata"]["study_number"] for study in all_studies
        ]
        for row in readCSV:
            # only for not empty rows
            if row:
                _class = "STUDY"
                data = study_mapper[_class](row, study_headers)
                # Checking if study already exists by study number
                if data["body"]["study_number"] not in all_studies:
                    all_studies.append(data["body"]["study_number"])
                    study_data = self.api.post_to_api(data)
                    # Patch the update information
                    if study_data is not None:
                        # we need to keep track of previously patched data in order to know if specific field is for example
                        # array field, and if so then we have to append new value to array instead just patching single value
                        patched_data = {}
                        self.update_data(data["patch"], study_data)
                        self.api.patch_to_api(study_data, data["path"])
                        patched_data.update(data["patch"])
                        with open(
                            MDR_MIGRATION_STUDY_TYPE, encoding="utf-8", errors="ignore"
                        ) as study_type_csv_file:
                            readStudyTypeCSV = csv.reader(
                                study_type_csv_file, delimiter=","
                            )
                            study_type_headers = next(readStudyTypeCSV)
                            for study_type_row in readStudyTypeCSV:
                                # only for not empty rows
                                if study_type_row:
                                    # have to prepare structure here, as /studies POST request returns actually only
                                    # identification metadata and version metadata
                                    study_data_template = study_data
                                    study_data_template["current_metadata"][
                                        "high_level_study_design"
                                    ] = {}
                                    study_data_template["current_metadata"][
                                        "study_intervention"
                                    ] = {}
                                    study_data_template["current_metadata"][
                                        "study_description"
                                    ] = {}
                                    _class = "STUDY_TYPE"
                                    study_patch_data = study_mapper[_class](
                                        study_type_row, study_type_headers
                                    )
                                    if (
                                        data["body"]["study_number"]
                                        == study_patch_data["patch"]["study_number"]
                                    ):
                                        parameter_name = study_patch_data["patch"][
                                            "study_define_param_name"
                                        ]
                                        component_name = study_patch_data[
                                            "component_mappings"
                                        ][parameter_name]
                                        api_param_name = study_patch_data[
                                            "parameter_mappings"
                                        ][parameter_name]
                                        data_to_patch = study_patch_data["patch"][
                                            "c_code"
                                        ]
                                        if api_param_name.endswith("Codes"):
                                            if api_param_name not in patched_data:
                                                dict_to_patch = {
                                                    "term_uid": data_to_patch
                                                }
                                                study_data_template["current_metadata"][
                                                    component_name
                                                ][api_param_name] = [dict_to_patch]
                                                patched_data[api_param_name] = [
                                                    dict_to_patch
                                                ]
                                            else:
                                                dict_to_patch = {
                                                    "term_uid": data_to_patch
                                                }
                                                existingCodes = patched_data[
                                                    api_param_name
                                                ]
                                                existingCodes.append(dict_to_patch)
                                                study_data_template["current_metadata"][
                                                    component_name
                                                ][api_param_name] = existingCodes
                                                patched_data[api_param_name] = (
                                                    existingCodes
                                                )
                                        elif api_param_name.endswith("_code"):
                                            dict_to_patch = {"term_uid": data_to_patch}
                                            study_data_template["current_metadata"][
                                                component_name
                                            ][api_param_name] = dict_to_patch
                                        elif api_param_name == "is_trial_randomised":
                                            data_to_patch = map_boolean(
                                                study_patch_data["patch"]["c_value"]
                                            )
                                            study_data_template["current_metadata"][
                                                component_name
                                            ][api_param_name] = data_to_patch
                                            patched_data[api_param_name] = data_to_patch
                                        else:
                                            study_data_template["current_metadata"][
                                                component_name
                                            ][api_param_name] = data_to_patch
                                            patched_data[api_param_name] = data_to_patch

                                        self.api.patch_to_api(
                                            study_data_template, data["path"]
                                        )
                else:
                    self.metrics.icrement(data["path"] + "--AlreadyExist")

    @open_file()
    def handle_projects(self, csvfile):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        # Fetching existing data
        all_programmes = self.api.get_all_identifiers(
            self.api.get_all_from_api("/clinical-programmes"), "name", "uid"
        )
        all_projects = self.api.get_all_identifiers(
            self.api.get_all_from_api("/projects"), "name"
        )

        for row in readCSV:
            _class = "PROJECT"
            data = project_mapper[_class](row, headers)
            # creating clinical program if it does not already exists
            if data["clinical_programme_body"]["name"] in all_programmes:
                uid = all_programmes[data["clinical_programme_body"]["name"]]
            else:
                res = self.api.post_to_api(
                    data,
                    data["clinical_programme_body"],
                    data["clinical_programme_path"],
                )
                if res is not None:
                    uid = res["uid"]
                    all_programmes[data["clinical_programme_body"]["name"]] = uid
                else:
                    continue  # there will be a error log from the api call

            if data["body"]["name"] not in all_projects:
                all_projects.append(data["body"]["name"])
                data["body"]["clinical_programme_uid"] = uid
                self.api.post_to_api(data)
            else:
                self.metrics.icrement(data["path"] + "--AlreadyExist")

    def run(self):
        self.log.info("Migrating mock data")
        self.handle_projects(MDR_MIGRATION_PROJECTS)
        self.handle_study(MDR_MIGRATION_STUDY)
        self.handle_objective_templates(MDR_MOCKUP_OBJECTIVES_OBJECTS)
        self.handle_objectives(MDR_MOCKUP_OBJECTIVES_OBJECTS)
        self.handle_endpoint_templates(MDR_MOCKUP_ENDPOINTS_OBJECTS)
        self.handle_endpoints(MDR_MOCKUP_ENDPOINTS_OBJECTS)
        self.handle_timeframe_templates(MDR_MOCKUP_TIMEFRAMES_OBJECTS)
        self.handle_timeframes(MDR_MOCKUP_TIMEFRAMES_OBJECTS)
        self.handle_study_objectives(MDR_MOCKUP_STUDY_OBJECTIVES)
        self.handle_study_endpoints(MDR_MOCKUP_STUDY_ENDPOINTS)
        self.log.info("Done migrating mock data")


def main():
    metr = Metrics()
    migrator = Mockdata(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
