import asyncio
import inspect
import json
import logging
import math
import sys
import time
from typing import Sequence

import aiohttp
import requests

from .metrics import Metrics
from .path_join import path_join

# CDISC codelists
CODELIST_STUDY_TYPE = "Study Type"
CODELIST_TRIAL_INDICATION_TYPE = "Trial Indication Type"
CODELIST_TRIAL_TYPE = "Trial Type"
CODELIST_TRIAL_PHASE = "Trial Phase"
CODELIST_INTERVENTION_TYPE = "Intervention Type"
CODELIST_CONTROL_TYPE = "Control Type"
CODELIST_INTERVENTION_MODEL = "Intervention Model"
CODELIST_TRIAL_BLINDING_SCHEMA = "Trial Blinding Schema"
CODELIST_AGE_UNIT = "Age Unit"
CODELIST_ROUTE_OF_ADMINISTRATION = "Route of Administration"
CODELIST_DOSAGE_FORM = "Pharmaceutical Dosage Form"
CODELIST_FREQUENCY = "Frequency"
CODELIST_SDTM_DOMAIN_ABBREVIATION = "SDTM Domain Abbreviation"
CODELIST_UNIT = "Unit"
CODELIST_SEX_OF_PARTICIPANTS = "Sex of Participants"

# Sponsor defined codelists
CODELIST_DELIVERY_DEVICE = "Delivery Device"
CODELIST_COMPOUND_DISPENSED_IN = "Compound Dispensed In"
CODELIST_FLOWCHART_GROUP = "Flowchart Group"
CODELIST_EPOCH_TYPE = "Epoch Type"
CODELIST_EPOCH_SUBTYPE = "Epoch Sub Type"
CODELIST_VISIT_TYPE = "VisitType"
CODELIST_TIMEPOINT_REFERENCE = "Time Point Reference"
CODELIST_VISIT_CONTACT_MODE = "Visit Contact Mode"
CODELIST_ARM_TYPE = "Arm Type"
CODELIST_ELEMENT_TYPE = "Element Type"
CODELIST_ELEMENT_SUBTYPE = "Element Sub Type"
CODELIST_NULL_FLAVOR = "Null Flavor"
CODELIST_UNIT_SUBSET = "Unit Subset"
CODELIST_UNIT_DIMENSION = "Unit Dimension"
CODELIST_OBJECTIVE_CATEGORY = "Objective Category"
CODELIST_CRITERIA_CATEGORY = "Criteria Category"
CODELIST_CRITERIA_SUBCATEGORY = "Criteria Sub Category"
CODELIST_CRITERIA_TYPE = "Criteria Type"
CODELIST_ENDPOINT_CATEGORY = "Endpoint Category"
CODELIST_FOOTNOTE_TYPE = "Footnote Type"
CODELIST_OBJECTIVE_LEVEL = "Objective Level"
CODELIST_ENDPOINT_LEVEL = "Endpoint Level"
CODELIST_ENDPOINT_SUBLEVEL = "Endpoint Sub Level"
CODELIST_TYPE_OF_TREATMENT = "Type of Treatment"

CODELIST_NAME_MAP = {
    CODELIST_STUDY_TYPE: "C99077",
    CODELIST_TRIAL_INDICATION_TYPE: "C66736",
    CODELIST_TRIAL_TYPE: "C66739",
    CODELIST_TRIAL_PHASE: "C66737",
    CODELIST_INTERVENTION_TYPE: "C99078",
    CODELIST_CONTROL_TYPE: "C66785",
    CODELIST_INTERVENTION_MODEL: "C99076",
    CODELIST_TRIAL_BLINDING_SCHEMA: "C66735",
    CODELIST_AGE_UNIT: "C66781",
    CODELIST_ROUTE_OF_ADMINISTRATION: "C66729",
    CODELIST_DOSAGE_FORM: "C66726",
    CODELIST_FREQUENCY: "C71113",
    CODELIST_SDTM_DOMAIN_ABBREVIATION: "C66734",
    CODELIST_UNIT: "C71620",
    CODELIST_SEX_OF_PARTICIPANTS: "C66732",
}

# Unit subsets
UNIT_SUBSET_AGE = "Age Unit"
UNIT_SUBSET_DOSE = "Dose Unit"
UNIT_SUBSET_STUDY_TIME = "Study Time"
UNIT_SUBSET_TIME = "Time Unit"
UNIT_SUBSET_STRENGTH = "Strength Unit"
UNIT_SUBSET_STUDY_PREFERRED_TIME_UNIT = "Study Preferred Time Unit"
UNIT_SUBSET_ENDPOINT_UNIT = "Endpoint Unit"

SLEEP_BEFORE_APPROVE = 0.05


def status_ok(status):
    return 200 <= status < 300


def get_error_message(response):
    if "message" in response:
        return response["message"]
    if "detail" in response:
        return str(response["detail"])
    return str(response)


# ---------------------------------------------------------------
# Api bindings
# ---------------------------------------------------------------
#
class ApiBinding:
    def __init__(self, api_base_url, api_headers, metrics, logger=None):
        self.api_headers = api_headers
        self.api_base_url = api_base_url
        if metrics is None:
            self.metrics = Metrics()
        else:
            self.metrics = metrics
        self.sem = asyncio.Semaphore(8)
        if logger is not None:
            self.log = logger
        else:
            self.log = logging.getLogger("legacy_mdr_migrations - apibinding")
        self.verify_connection()

        # execute the check if called methods is not db-schema-migration repository
        if "db-schema-migration" not in inspect.currentframe().f_code.co_filename:
            self.check_for_ct_packages()

    def update_headers(self, api_headers):
        self.api_headers = api_headers

    # ---------------------------------------------------------------
    # Verify connection to api (and database)
    # ---------------------------------------------------------------
    #
    # Verify that Clinical MDR API is online
    # TODO Replace with api health check resource ...
    def verify_connection(self):
        try:
            response = requests.get(
                path_join(self.api_base_url, "openapi.json"), headers=self.api_headers
            )
            response.raise_for_status()
        except Exception as e:
            self.log.critical(
                f"Failed to connect to backend, is it running?\nError was:\n{e}"
            )
            sys.exit(1)

    # Verify that the bare minimum of CT packages are available.
    def check_for_ct_packages(self):
        packages = self.get_all_from_api("/ct/packages")
        package_names = set()
        for package in packages:
            package_names.add(package.get("catalogue_name"))
        mandatory_packages = {"ADAM CT", "CDASH CT", "DEFINE-XML CT", "SDTM CT"}
        optional_packages = {
            "COA CT",
            "GLOSSARY CT",
            "PROTOCOL CT",
            "QRS CT",
            "QS-FT CT",
            "SEND CT",
        }
        missing = mandatory_packages - package_names
        if len(missing) > 0:
            self.log.critical(
                f"Missing CT packages: {','.join(missing)}.\nPlease run the clinical standards import before this tool."
            )
            sys.exit(1)
        missing = optional_packages - package_names
        if len(missing) > 0:
            self.log.warning(f"Missing optional CT packages: {','.join(missing)}.")

    def simple_delete(self, path, simple_path=None):
        if simple_path is None:
            simple_path = path
        response = requests.delete(
            path_join(self.api_base_url, path), headers=self.api_headers
        )
        if response.ok:
            self.metrics.icrement(simple_path + "--DELETE")
            self.log.debug("DELETE %s %s", path, "success")
            return True

        self.log.debug("DELETE %s", path)
        self.log.warning(response.text)
        self.metrics.icrement(simple_path + "--ERROR")
        return False

    def simple_post_to_api(self, path, body, simple_path=None, params=None):
        if simple_path is None:
            simple_path = path
        response = requests.post(
            path_join(self.api_base_url, path),
            headers=self.api_headers,
            json=body,
            params=params,
        )
        if response.ok:
            self.metrics.icrement(simple_path + "--POST")
            self.log.debug("POST %s %s", path, "success")
            return response.json()

        self.log.debug("POST %s", path)
        if "message" in response.json() and (
            "already exist" in response.json()["message"]
            or "all ready" in response.json()["message"]
            or "Duplicate template" in response.json()["message"]
            or "There is already" in response.json()["message"]
        ):
            self.log.warning(response.json()["message"])
            self.metrics.icrement(simple_path + "--AlreadyExists")
        elif (
            "message" in response.json()
            and "no approved objective" in response.json()["message"]
        ):
            self.log.warning(response.json()["message"])
            self.metrics.icrement(simple_path + "--NoObjective")
        else:
            self.log.warning(response.text)
            self.metrics.icrement(simple_path + "--ERROR")
        return None

    def post_to_api(self, object, body=None, path=None):
        if path is None:
            response = requests.post(
                path_join(self.api_base_url, object["path"]),
                headers=self.api_headers,
                json=object["body"],
            )
            path = object["path"]
        else:
            response = requests.post(
                path_join(self.api_base_url, path), headers=self.api_headers, json=body
            )
        short_path = "".join([i for i in path if not i.isdigit()])

        if response.ok:
            self.metrics.icrement(short_path + "--POST")
            if "name" in object["body"]:
                self.log.debug("POST %s %s", object["path"], object["body"]["name"])
            else:
                self.log.debug("POST %s %s", object["path"], "success")
            return response.json()

        if "name" in object["body"]:
            self.log.debug("POST %s %s", object["path"], object["body"]["name"])
        else:
            self.log.debug("POST %s %s", object["path"], "no name")
        if "message" in response.json() and (
            "already exists" in response.json()["message"]
            or "Duplicate template" in response.json()["message"]
            or "already has" in response.json()["message"]
        ):
            self.log.warning("Post to %s failed: %s", path, response.json()["message"])
            self.metrics.icrement(short_path + "--AlreadyExists")
        elif "message" in response.json() and (
            "not found" in response.json()["message"]
            or "does not exist" in response.json()["message"]
        ):
            self.log.warning("Post to %s failed: %s", path, response.json()["message"])
            self.metrics.icrement(short_path + "--NotFound")
        else:
            self.log.warning("Post to %s failed: %s", path, response.text)
            self.metrics.icrement(short_path + "--ERROR")
        return None

    def patch_to_api(self, body, path):
        url = path_join(self.api_base_url, path, body["uid"])
        response = requests.patch(url, headers=self.api_headers, json=body)
        if response.ok:
            self.metrics.icrement(path + "--Patch")
            self.log.info("Patch %s %s", path, "success")
            return response.json()

        self.log.warning("Patch %s %s", path, "error")
        if (
            "message" in response.json().keys()
            and "already exists" in response.json()["message"]
        ):
            self.log.warning(response.json()["message"])
            self.metrics.icrement(path + "--AlreadyExists")
        else:
            self.log.warning(response.text)
            self.metrics.icrement(path + "--Patch-ERROR")
        return None

    def approve_item(self, uid: str, url: str):
        full_url = path_join(self.api_base_url, url, uid, "approvals")
        response = requests.post(full_url, headers=self.api_headers)
        if not response.ok:
            self.log.warning("Failed to approve %s %s", uid, response.content)
            return None

        return response.json()

    def approve_item_names_and_attributes(self, uid: str, url: str):
        full_url = path_join(self.api_base_url, url, uid, "names/approvals")
        response = requests.post(full_url, headers=self.api_headers)
        if not response.ok:
            self.log.warning("Failed to approve names %s %s", uid, response.content)
            return False
        full_url = path_join(self.api_base_url, url, uid, "attributes/approvals")
        response = requests.post(full_url, headers=self.api_headers)
        if not response.ok:
            self.log.warning(
                "Failed to approve attributes %s %s", uid, response.content
            )
            return False

        return True

    def get_all_from_api(self, path, params=None, items_only=True):
        # print(path_join(self.api_base_url, path), params, self.api_headers)
        if params is None:
            params = {
                "page_number": 1,
                "page_size": 0,
            }
        else:
            if "page_size" not in params:
                params["page_size"] = 0
            if "page_number" not in params:
                params["page_number"] = 1

        response = requests.get(
            path_join(self.api_base_url, path), params=params, headers=self.api_headers
        )

        if response.ok:
            try:
                res = response.json()
            except json.JSONDecodeError:
                self.log.error(
                    "Failed to decode json for %s, data: %s", path, response.text
                )
                return None
            if "items" in res and items_only:
                self.metrics.icrement(path + "--GET", len(res["items"]))
                return res["items"]

            return res

        try:
            message = response.json().get("message")
        except json.JSONDecodeError:
            message = None
        if message is not None:
            self.log.error(
                "get %s, message: %s, status: %s %s",
                path,
                message,
                response.status_code,
                response.reason,
            )
        else:
            self.log.error(
                "get %s reply: %s status: %s %s",
                path,
                response.text,
                response.status_code,
                response.reason,
            )
        return None

    def get_all_from_api_paged(
        self, path, params=None, items_only=True, page_size=1000
    ):
        page_number = 1
        page_params = {
            "page_number": page_number,
            "page_size": page_size,
            "total_count": True,
        }
        if params is not None:
            page_params.update(params)
        self.log.info(f"Fetching {path}, page size: {page_size}")
        data = self.get_all_from_api(path, params=page_params, items_only=False)
        all_items = data["items"]
        count = data["total"]

        nbr_pages = math.ceil(count / page_size)
        # Get remaining pages
        page_params["total_count"] = False
        while page_size * page_number < count:
            page_number += 1
            page_params["page_number"] = page_number
            self.log.info(f"Fetching {path}, page {page_number} of {nbr_pages}")
            additional_data = self.get_all_from_api(
                path, params=page_params, items_only=True
            )
            all_items.extend(additional_data)
        if items_only:
            return all_items
        return data

    def get_all_identifiers(self, responses: list, identifier: str, value: str = None):
        if value is None:
            identifiers = []
            for response_item in responses:
                identifiers.append(response_item[identifier])
            return identifiers

        identifiers = {}
        if responses is None:
            return identifiers
        for response_item in responses:
            identifiers[response_item[identifier]] = response_item[value]
        return identifiers

    def response_to_dict(self, responses: list, identifier: str):
        items = {}
        if responses is None:
            return items
        for response_item in responses:
            items[response_item[identifier]] = response_item
        return items

    # Alternative version of get_all_identifiers() that returns a dict with only lower case keys.
    # Each item is list of all found values.
    def get_all_identifiers_multiple(
        self, responses: list, identifier: str, values: Sequence[str]
    ):
        identifiers = {}
        if responses is None:
            return identifiers
        for response_item in responses:
            ident = response_item[identifier].lower()
            if ident not in identifiers:
                identifiers[ident] = []
            requested_values = {}
            for value in values:
                requested_values[value] = response_item[value]
            identifiers[ident].append(requested_values)
        return identifiers

    def get_libraries(self):
        response = requests.get(
            path_join(self.api_base_url, "libraries"), headers=self.api_headers
        )
        response.raise_for_status()
        libs = response.json()
        lib_names = [lib["name"] for lib in libs]
        self.log.info("Existing libraries: %s", lib_names)
        return lib_names

    def create_library(self, object):
        self.metrics.icrement("/libraries")
        response = requests.post(
            path_join(self.api_base_url, "libraries"),
            headers=self.api_headers,
            json=object,
        )
        response.raise_for_status()

    # Get all terms from a codelist identified by codelist name
    def get_terms_for_codelist_name(self, codelist_name: str):
        if codelist_name in CODELIST_NAME_MAP:
            params = {
                "codelist_uid": CODELIST_NAME_MAP[codelist_name],
                "page_number": 1,
                "page_size": 0,
            }
        else:
            params = {"codelist_name": codelist_name, "page_number": 1, "page_size": 0}
        response = requests.get(
            path_join(self.api_base_url, "ct/terms"),
            params=params,
            headers=self.api_headers,
        )
        response.raise_for_status()
        result = response.json()
        return result["items"]

    # Get all terms from a codelist identified by codelist uid
    def get_terms_for_codelist_uid(self, codelist_uid: str):
        response = requests.get(
            path_join(self.api_base_url, "ct/terms"),
            params={"codelist_uid": codelist_uid, "page_number": 1, "page_size": 0},
            headers=self.api_headers,
        )
        response.raise_for_status()
        result = response.json()
        return result["items"]

    def get_filtered_terms(self, filters: dict):
        filters = json.dumps(filters)
        response = requests.get(
            self.api_base_url + "/ct/terms/attributes",
            params={
                "page_number": 1,
                "page_size": 0,
                "filters": filters,
            },
            headers=self.api_headers,
        )
        response.raise_for_status()
        result = response.json()
        return result["items"]

    # Get terms from a catalogue that have a given concept id
    def lookup_terms_from_concept_id(
        self, concept_id: str, catalogue_name=None, code_submission_value=None
    ):
        filters_dict = {"concept_id": {"v": [concept_id], "op": "eq"}}
        if catalogue_name:
            filters_dict["catalogue_name"] = {"v": [catalogue_name], "op": "eq"}
        if code_submission_value:
            filters_dict["code_submission_value"] = {
                "v": [code_submission_value],
                "op": "eq",
            }
        filters = json.dumps(filters_dict)
        response = requests.get(
            self.api_base_url + "/ct/terms/attributes",
            params={
                "library_name": "CDISC",
                "page_number": 1,
                "page_size": 0,
                "filters": filters,
            },
            headers=self.api_headers,
        )
        response.raise_for_status()
        result = response.json()
        return result["items"]

    # Get all dictionary mapping all codelist names to a uid
    def get_code_lists_uids(self):
        response = requests.get(
            path_join(
                self.api_base_url, "ct/codelists/names?page_number=1&page_size=0"
            ),
            headers=self.api_headers,
        )
        response.raise_for_status()
        result = response.json()
        codelists_uids = {}
        for res in result["items"]:
            codelists_uids[res["name"]] = res["codelist_uid"]
        return codelists_uids

    def get_all_activity_objects(self, object_type, filters=None):
        page_number = 1
        page_size = 100
        total_count = True
        params = {
            "page_number": page_number,
            "page_size": page_size,
            "total_count": total_count,
        }
        if filters:
            params["filters"] = filters
        self.log.info(
            f"Getting {object_type} page_number:{page_number}, page_size:{page_size}"
        )
        all_activities_initial = self.get_all_from_api(
            f"/concepts/activities/{object_type}", params=params, items_only=False
        )
        if all_activities_initial:
            all_activity_objects = all_activities_initial["items"]
            count = all_activities_initial["total"]
        else:
            all_activity_objects = []
            count = 0

        while page_size * page_number < count:
            page_number += 1
            total_count = False
            params = {
                "page_number": page_number,
                "page_size": page_size,
                "total_count": total_count,
            }
            if filters:
                params["filters"] = filters
            self.log.info(
                f"Getting {object_type} page_number:{page_number}, page_size:{page_size}, total:{count}"
            )
            items = self.get_all_from_api(
                f"/concepts/activities/{object_type}", params=params, items_only=True
            )
            if items:
                all_activity_objects += items
        return all_activity_objects

    def get_study_objectives_for_study(self, study_uid):
        params = {
            "page_number": 1,
            "page_size": 0,
        }
        response = requests.get(
            path_join(self.api_base_url, "studies", study_uid, "study-objectives"),
            headers=self.api_headers,
            params=params,
        )
        response.raise_for_status()
        result = response.json()
        temp_dict = {}
        for res in result["items"]:
            temp_dict[res["objective"]["name"]] = res["study_objective_uid"]
        return temp_dict

    def get_templates_as_dict(self, path):
        params = {
            "page_number": 1,
            "page_size": 0,
        }
        response = requests.get(
            path_join(self.api_base_url, path), headers=self.api_headers, params=params
        )
        response.raise_for_status()
        result = response.json()
        objective_temp_dict = {}
        result = result["items"] if isinstance(result, dict) else result
        for res in result:
            objective_temp_dict[res["name"]] = res
        return objective_temp_dict

    def find_object_by_key(self, name, path, key="name"):
        params = {"filters": '{"' + key + '":{"v":["' + name + '"],"op":"eq"}}'}
        response = requests.get(
            path_join(self.api_base_url, path),
            params=params,
            headers=self.api_headers,
        )
        if response.ok and len(response.json()["items"]):
            return response.json()["items"][0]

        return None

    # Find the uid for a dictionary from its name
    def find_dictionary_uid(self, name):
        response = requests.get(
            path_join(self.api_base_url, "dictionaries/codelists"),
            params={"library_name": name},
            headers=self.api_headers,
        )
        if response.ok:
            # This assumes there is only one version, do we need to handle multiple?
            return response.json()["items"][0]["codelist_uid"]

        return None

    # Find a term via its name from a dictionary
    def find_dictionary_item_uid_from_name(self, dict_uid, name):
        response = requests.get(
            path_join(self.api_base_url, "dictionaries/terms"),
            params={
                "codelist_uid": dict_uid,
                "filters": json.dumps({"name": {"v": [name]}}),
                "page_number": 1,
                "page_size": 0,
            },
            headers=self.api_headers,
        )
        if response.ok and len(response.json()["items"]) > 0:
            # This assumes there is only one version, do we need to handle multiple?
            return response.json()["items"][0]["term_uid"]
        return None

    def get_studies_as_dict(self, path="/studies"):
        params = {
            "page_number": 1,
            "page_size": 0,
        }
        response = requests.get(
            path_join(self.api_base_url, path), headers=self.api_headers, params=params
        )
        response.raise_for_status()
        result = response.json()
        temp_dict = {}
        for res in result["items"]:
            temp_dict[
                res["current_metadata"]["identification_metadata"]["study_id"]
            ] = res
        return temp_dict

    def simple_approve(self, path: str):
        path = path_join(self.api_base_url, path)
        res = requests.post(path, headers=self.api_headers)
        if not res.ok:
            self.log.warning("Failed to approve %s", path)
            return False

        return True

    def simple_approve2(self, url: str, path: str, label=""):
        url = path_join(url, path)
        res = requests.post(path_join(self.api_base_url, url), headers=self.api_headers)
        if not res.ok:
            self.log.warning("Failed to approve %s", url)
            self.metrics.icrement(f"{url}--{label}ApproveError")
            return False

        self.metrics.icrement(f"{url}--{label}Approve")
        return True

    def simple_patch(self, body, url, path):
        full_url = path_join(self.api_base_url, url)
        response = requests.patch(full_url, headers=self.api_headers, json=body)
        if response.ok:
            self.metrics.icrement(path + "--Patch")
            self.log.info("Patch %s %s", path, "success")
            return response.json()

        if (
            "message" in response.json().keys()
            and "already exists" in response.json()["message"]
        ):
            self.log.warning("Patch %s %s", url, "error, item already exists")
            self.metrics.icrement(path + "--AlreadyExists")
        elif (
            "message" in response.json().keys()
            and "does not exist" in response.json()["message"]
        ):
            self.log.warning("Patch %s %s", url, "error, item not found")
            self.metrics.icrement(path + "--NotFound")
        else:
            self.log.warning("Patch %s %s", url, response.text)
            self.metrics.icrement(path + "--Patch-ERROR")
        return None

    # ---------------------------------------------------------------
    # Async building blocks
    # ---------------------------------------------------------------
    #
    async def new_version_to_api_async(self, path: str, session: aiohttp.ClientSession):
        async with session.post(
            path_join(self.api_base_url, path), json={}, headers=self.api_headers
        ) as response:
            status = response.status
            try:
                result = await response.json()
            except aiohttp.ContentTypeError:
                textresult = await response.text()
                result = {}
                self.log.error(
                    f"Failed to post to '{path}', status: {status}, message: {textresult}"
                )
            return status, result

    async def patch_to_api_async(
        self, path: str, body: dict, session: aiohttp.ClientSession
    ):
        async with session.patch(
            path_join(self.api_base_url, path), json=body, headers=self.api_headers
        ) as response:
            status = response.status
            try:
                result = await response.json()
            except aiohttp.ContentTypeError:
                textresult = await response.text()
                result = {}
                self.log.error(
                    f"Failed to patch to '{path}', status: {status}, message: {textresult}"
                )
            return status, result

    # This gives reasonable waiting for lock on atomic incrementing of identifiers
    async def post_to_api_async(
        self,
        url: str,
        body: dict,
        session: aiohttp.ClientSession,
        logfile_name: str | None = None,
    ):
        async with self.sem:
            async with session.post(
                path_join(self.api_base_url, url), json=body, headers=self.api_headers
            ) as response:
                status = response.status
                try:
                    result = await response.json()
                    if logfile_name and status not in [200, 201]:
                        with open(logfile_name, "a") as logfile:
                            logfile.write(
                                (
                                    f"Failed to post to '{url}', status: {status}, "
                                    f"message: {result['message'] if 'message' in result else result['detail']}, body: {body}\n"
                                )
                            )
                except aiohttp.ContentTypeError:
                    textresult = await response.text()
                    result = {}
                    self.log.error(
                        f"Failed to post to '{url}', status: {status}, message: {textresult}"
                    )
                return status, result

    async def approve_async(self, url: str, session: aiohttp.ClientSession):
        async with session.post(
            path_join(self.api_base_url, url), json={}, headers=self.api_headers
        ) as response:
            status = response.status
            if response.ok:
                result = await response.json()
            else:
                try:
                    error_result = await response.json()
                    error_message = get_error_message(error_result)
                except aiohttp.ContentTypeError:
                    error_message = await response.text()
                self.log.warning(
                    f"Failed to approve {url}, status: {status}, message: {error_message}"
                )
                result = {}
            return status, result

    async def approve_item_async(
        self, uid: str, url: str, session: aiohttp.ClientSession
    ):
        url = path_join(self.api_base_url, url, uid, "approvals")
        async with session.post(
            url,
            json={},
            headers=self.api_headers,
        ) as response:
            status = response.status
            if response.ok:
                result = await response.json()
            else:
                try:
                    error_result = await response.json()
                    error_message = get_error_message(error_result)
                except aiohttp.ContentTypeError:
                    error_message = await response.text()
                self.log.warning(
                    f"Failed to approve {url}, status: {status}, message: {error_message}"
                )
                result = {}
            if not response.ok:
                self.metrics.icrement(url + "--ApproveError")
            else:
                self.metrics.icrement(url + "--Approve")
            return status, result

    async def post_then_approve(
        self, data: dict, session: aiohttp.ClientSession, approve: bool
    ):
        self.log.debug(f"Post to {data['path']}")
        status, response = await self.post_to_api_async(
            url=data["path"], body=data["body"], session=session
        )
        if status >= 400:
            if "message" in response:
                errormsg = response["message"]
            else:
                errormsg = str(response)

            if "name" in data["body"]:
                name = data["body"]["name"]
            elif "term_uid" in data["body"]:
                name = data["body"]["term_uid"]
            else:
                name = str(data["body"])

            self.log.error(
                f"Failed to post '{name}' to '{data['path']}', error: {errormsg}"
            )
            return
        uid = response.get("uid")
        if approve is True and uid is not None:
            # Sleeping to avoid errors when running locally (with limited resources for the db).
            time.sleep(SLEEP_BEFORE_APPROVE)
            self.log.info(f"Approve object with uid '{uid}'")
            status, result = await self.approve_item_async(
                uid=uid, url=data["approve_path"], session=session
            )
            return result
        if approve is True and uid is None:
            self.log.error("No uid returned, unable to approve")
        return response

    async def new_version_patch_then_approve(
        self, data: dict, session: aiohttp.ClientSession, approve: bool
    ):
        status, response = await self.new_version_to_api_async(
            path=data["new_path"], session=session
        )
        if not status_ok(status):
            error_msg = get_error_message(response)
            if "New draft version can be created only for FINAL versions" in error_msg:
                self.log.warning(
                    "Failed to create new version, item is already in DRAFT"
                )
            else:
                self.log.error(f"Failed to create new version: {error_msg}")
                return
        status, response = await self.patch_to_api_async(
            path=data["patch_path"], body=data["body"], session=session
        )
        if not status_ok(status):
            self.log.error(f"Failed to patch: {get_error_message(response)}")
            return
        uid = response.get("uid")
        if approve and uid is not None:
            # Sleeping to avoid errors when running locally (with limited resources for the db).
            time.sleep(SLEEP_BEFORE_APPROVE)
            status, reponse = await self.approve_item_async(
                uid=response.get("uid"), url=data["approve_path"], session=session
            )
            if not status_ok(status):
                self.log.error(f"Failed to approve the new version of: {uid}")
            return response
        elif approve:
            self.log.error("No uid returned, unable to approve the new version")
