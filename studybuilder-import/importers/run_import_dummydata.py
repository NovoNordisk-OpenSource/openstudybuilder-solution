# pylint: disable=missing-timeout,logging-fstring-interpolation

"""Creates dummy data and dummy studies. API URL must be set in the API_BASE_URL environment variable."""

import base64
import json
from functools import lru_cache
from random import randint

import requests

from .utils.api_bindings import CODELIST_NAME_MAP
from .utils.importer import BaseImporter
from .utils.path_join import path_join

LIBRARY_NAME_SPONSOR = "Sponsor"
LIBRARY_NAME_REQUESTED = "Requested"


def activity_payload(nbr, library_name, activity_group_uid, activity_subgroup_uid):
    return {
        "path": "/concepts/activities/activities",
        "body": {
            "name": f"{library_name} Activity {nbr}",
            "name_sentence_case": f"{library_name.lower()} activity {nbr}",
            "definition": f"Definition of {library_name} activity {nbr}",
            "abbreviation": f"Abb {nbr}",
            "library_name": library_name,
            "is_data_collected": True,
            "activity_groupings": [
                {
                    "activity_group_uid": activity_group_uid,
                    "activity_subgroup_uid": activity_subgroup_uid,
                }
            ],
        },
    }


def activity_instance_class_payload(n: int, library: str):
    return {
        "path": "/activity-instance-classes",
        "body": {
            "name": f"{library} ActivityInstanceClass {n}",
            "name_sentence_case": f"{library.lower()} activity instance class {n}",
            "definition": f"Definition of {library} activity instance class {n}",
            "library_name": library,
        },
    }


def activity_instance_payload(
    n: int,
    library_name: str,
    instance_class_uid: str,
    activity_uid: str,
    activity_group_uid: str,
    activity_subgroup_uid: str,
):
    return {
        "path": "/concepts/activities/activity-instances",
        "body": {
            "name": f"{library_name} Activity Instance {n}",
            "name_sentence_case": f"{library_name.lower()} activity instance {n}",
            "definition": f"Definition of {library_name} activity instance {n}",
            "abbreviation": f"Abb {n}",
            "activity_instance_class_uid": instance_class_uid,
            "topic_code": f"{n:04x}",
            "adam_param_code": (
                base64.b64encode(f"{n:02x}".encode()).strip(b"=").decode()
            ),
            "library_name": library_name,
            "activity_groupings": [
                {
                    "activity_uid": activity_uid,
                    "activity_group_uid": activity_group_uid,
                    "activity_subgroup_uid": activity_subgroup_uid,
                }
            ],
        },
    }


def activity_group_payload(nbr):
    return {
        "path": "/concepts/activities/activity-groups",
        "body": {
            "name": f"Group {nbr}",
            "name_sentence_case": f"group {nbr}",
            "definition": f"Definition of group {nbr}",
            "abbreviation": f"Abb {nbr}",
            "library_name": LIBRARY_NAME_SPONSOR,
        },
    }


def activity_subgroup_payload(nbr, groups):
    return {
        "path": "/concepts/activities/activity-sub-groups",
        "body": {
            "name": f"Subgroup {nbr}",
            "name_sentence_case": f"subgroup {nbr}",
            "definition": f"Definition of subgroup {nbr}",
            "abbreviation": f"Abb {nbr}",
            "library_name": LIBRARY_NAME_SPONSOR,
            "activity_groups": groups,
        },
    }


def library_payload():
    return {
        "path": "/libraries",
        "body": {
            "name": "Dummy",
            "is_editable": True,
        },
    }


def clinical_programme_payload():
    return {
        "path": "/clinical-programmes",
        "body": {
            "name": "Dummy",
        },
    }


def project_payload(clinical_programme_uid: str):
    return {
        "path": "/projects",
        "body": dict(
            name="Dummy",
            project_number="999",
            description="Dummy project for dummy studies",
            clinical_programme_uid=clinical_programme_uid,
        ),
    }


def study_payload(nbr, project_number):
    return {
        "path": "/studies",
        "body": {
            "study_number": str(3000 + nbr),
            "study_acronym": f"DummyStudy {nbr}",
            "project_number": project_number,
        },
    }


def study_arm_payload(nbr, arm_type_uid, study_uid):
    return {
        "path": f"/studies/{study_uid}/study-arms",
        "body": {
            "arm_type_uid": arm_type_uid,
            "name": f"Test Study Arm {nbr} name",
            "short_name": f"Test Study Arm {nbr} short name",
            "randomization_group": f"Dummy Randomization Group {nbr}",
            "code": f"Dummy Code {nbr}",
            "description": f"Arm nbr {nbr} for study {study_uid}",
            "arm_colour": get_color(nbr),
        },
    }


def study_element_payload(nbr, element_type_uid, element_subtype_uid, study_uid):
    return {
        "path": f"/studies/{study_uid}/study-elements",
        "body": {
            "planned_duration": {},
            "code": element_type_uid,
            "element_subtype_uid": element_subtype_uid,
            "name": f"Test Study Element {nbr} name",
            "short_name": f"Test Study Element {nbr} short name",
            "start_rule": "Dummy start rule",
            "end_rule": "Dummy end rule",
            "description": f"Element nbr {nbr} for study {study_uid}",
            "element_colour": get_color(nbr),
        },
    }


def study_epoch_payload(
    nbr, epoch_uid, epoch_subtype_uid, duration_unit_uid, study_uid
):
    return {
        "path": f"/studies/{study_uid}/study-epochs",
        "body": {
            "study_uid": study_uid,
            "start_rule": "Dummy start rule",
            "end_rule": "Dummy end rule",
            "epoch": epoch_uid,
            "epoch_subtype": epoch_subtype_uid,
            "duration_unit": duration_unit_uid,
            "order": nbr,
            "description": f"Epoch nbr {nbr} for study {study_uid}",
            "duration": 0,
            "color_hash": get_color(nbr),
        },
    }


def study_activity_payload(
    soa_group_term_uid,
    activity_uid,
    activity_subgroup_uid,
    activity_group_uid,
    study_uid,
):
    return {
        "path": f"/studies/{study_uid}/study-activities",
        "body": {
            "soa_group_term_uid": soa_group_term_uid,
            "activity_uid": activity_uid,
            "activity_subgroup_uid": activity_subgroup_uid,
            "activity_group_uid": activity_group_uid,
        },
    }


def objective_template_payload(nbr, indication_uids, category_uids):
    return {
        "path": "/objective-templates",
        "body": {
            "name": f"<p>Test {nbr} [ActivityInstance] [CompoundDosing] [Compound]</p>",
            "is_confirmatory_testing": bool(randint(0, 1)),
            "indication_uids": indication_uids,
            "category_uids": category_uids,
            "library_name": LIBRARY_NAME_SPONSOR,
        },
    }


def endpoint_template_payload(nbr, indication_uids, category_uids, subcategory_uids):
    return {
        "path": "/endpoint-templates",
        "body": {
            "name": f"<p>Test {nbr} [ActivityInstance] [CompoundDosing] [Compound]</p>",
            "indication_uids": indication_uids,
            "category_uids": category_uids,
            "subcategory_uids": subcategory_uids,
            "library_name": LIBRARY_NAME_SPONSOR,
        },
    }


def criteria_template_payload(
    nbr, indication_uids, category_uids, subcategory_uids, type_uid
):
    return {
        "path": "/criteria-templates",
        "body": {
            "name": f"<p>Test {nbr} [ActivityInstance] [CompoundDosing] [Compound]</p>",
            "type_uid": type_uid,
            "indication_uids": indication_uids,
            "category_uids": category_uids,
            "subcategory_uids": subcategory_uids,
            "library_name": LIBRARY_NAME_SPONSOR,
        },
    }


def activity_instruction_template_payload(
    nbr, indication_uids, activity_uids, activity_group_uids, activity_subgroup_uids
):
    return {
        "path": "/activity-instruction-templates",
        "body": {
            "name": f"<p>Test {nbr} [ActivityInstance] [CompoundDosing] [Compound]</p>",
            "indication_uids": indication_uids,
            "activity_uids": activity_uids,
            "activity_group_uids": activity_group_uids,
            "activity_subgroup_uids": activity_subgroup_uids,
            "library_name": LIBRARY_NAME_SPONSOR,
        },
    }


def footnote_template_payload(
    nbr,
    indication_uids,
    type_uid,
    activity_uids,
    activity_group_uids,
    activity_subgroup_uids,
):
    return {
        "path": "/footnote-templates",
        "body": {
            "name": f"<p>Test {nbr} [ActivityInstance] [CompoundDosing] [Compound]</p>",
            "type_uid": type_uid,
            "indication_uids": indication_uids,
            "activity_uids": activity_uids,
            "activity_group_uids": activity_group_uids,
            "activity_subgroup_uids": activity_subgroup_uids,
            "library_name": LIBRARY_NAME_SPONSOR,
        },
    }


def timeframe_template_payload(nbr):
    return {
        "path": "/timeframe-templates",
        "body": {
            "name": f"<p>Test {nbr} [ActivityInstance] [CompoundDosing] [Compound]</p>",
            "library_name": LIBRARY_NAME_SPONSOR,
        },
    }


def visit_group_name(n: int):
    if 5 < n and n % 5:
        return f"VG{int(n/5)}"
    return None


def study_visit_payload(
    nbr,
    study_uid,
    epoch_uid,
    visit_type_uid,
    time_unit_uid,
    time_reference_uid,
    contact_mode_uid,
    time_value: int | None = None,
    is_global_anchor_visit: bool = False,
):
    return {
        "path": f"/studies/{study_uid}/study-visits",
        "body": {
            "study_epoch_uid": epoch_uid,
            "visit_type_uid": visit_type_uid,
            "time_reference_uid": time_reference_uid,
            "time_value": 5 * (nbr - 2) if time_value is None else time_value,
            "time_unit_uid": time_unit_uid,
            "visit_sublabel_codelist_uid": None,
            "visit_sublabel_reference": None,
            # "legacy_subname": "string",
            "consecutive_visit_group": visit_group_name(nbr),
            "show_visit": True,
            "min_visit_window_value": -1,
            "max_visit_window_value": 1,
            "visit_window_unit_uid": time_unit_uid,
            "description": f"Dummy visit {nbr} for dummy study {study_uid}",
            "start_rule": None,
            "end_rule": None,
            "visit_contact_mode_uid": contact_mode_uid,
            "epoch_allocation_uid": None,
            "visit_class": "SINGLE_VISIT",
            "visit_subclass": "SINGLE_VISIT",
            "is_global_anchor_visit": is_global_anchor_visit,
        },
    }


def get_color(nbr):
    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#00FFFF", "#FF00FF"]
    color = colors[nbr % len(colors)]
    return color


def get_arm_types(nbr):
    arm_types = [
        "Investigational Arm",
        "Comparator Arm",
        "Placebo Arm",
        "Observational Arm",
    ]
    return arm_types[nbr % len(arm_types)]


def get_element_types(nbr):
    element_types_and_element_subtypes = {
        "Treatment": ["Treatment"],
        "No Treatment": ["Follow-up", "Run-in", "Screening", "Wash-out"],
    }
    element_types = list(element_types_and_element_subtypes.keys())
    element_type = element_types[nbr % len(element_types)]
    element_subtypes = element_types_and_element_subtypes[element_type]

    return element_type, element_subtypes[nbr % len(element_subtypes)]


def get_epoch_subtype(nbr):
    epoch_subtypes = [
        "Screening",
        "Run-in",
        "Dose Escalation",
        "Treatment",
        "Maintenance",
        "Observation",
        "Wash-out",
        "Elimination",
        "Follow-up",
        "Intervention",
    ]
    return epoch_subtypes[nbr % len(epoch_subtypes)]


def get_soa_group_name(nbr):
    soa_groups = [
        "HIDDEN",
        "REMINDERS",
        "TRIAL MATERIAL",
        "HEALTH ECONOMICS",
        "BIOMARKERS",
        "HUMAN BIOSAMPLES",
        "GENETICS",
        "SAFETY",
        "PHARMACODYNAMICS",
        "PHARMACOKINETICS",
        "IMMUNOGENICITY",
        "ELIGIBILITY AND OTHER CRITERIA",
        "INFORMED CONSENT",
        "EFFICACY",
        "SUBJECT RELATED INFORMATION",
    ]
    return soa_groups[nbr % len(soa_groups)]


def iter_one_visit_per_group(visits):
    """Iterates over visits dictionary yielding only the visits that are the first in their group or not grouped"""

    last_group = None

    for visit in visits:
        if (
            not visit["consecutive_visit_group"]
            or visit["consecutive_visit_group"] != last_group
        ):
            last_group = visit["consecutive_visit_group"]
            yield visit


class DummyData(BaseImporter):
    logging_name = "dummydata"

    def __init__(
        self,
        options,
    ):
        super().__init__()
        self.options = options
        self.library = None
        self.clinical_programme = None
        self.project = None
        self.studies = {}
        self.objective_templates = []
        self.endpoint_templates = []
        self.criteria_templates = []
        self.activity_instruction_templates = []
        self.footnote_templates = []
        self.timeframe_templates = []
        self.activity_groups = []
        self.activity_groupings = []
        self.activities = []
        self.activity_instance_classes = []
        self.activity_instances = []
        self.req_activities = []

    @lru_cache(maxsize=10000)
    def lookup_ct_term_uid(
        self, codelist_name, value, key="sponsor_preferred_name", uid_key="term_uid"
    ):
        filters = {key: {"v": [value]}}
        if codelist_name in CODELIST_NAME_MAP:
            self.log.info(
                f"Looking up term with '{key}' == '{value}' in codelist '{codelist_name}': {CODELIST_NAME_MAP[codelist_name]}, returning uid from '{uid_key}'"
            )
            params = {
                "codelist_uid": CODELIST_NAME_MAP[codelist_name],
                "page_size": 1,
                "filters": json.dumps(filters),
            }
        else:
            self.log.info(
                f"Looking up term with '{key}' == '{value}' in codelist '{codelist_name}', returning uid from '{uid_key}'"
            )
            params = {
                "codelist_name": codelist_name,
                "page_size": 1,
                "filters": json.dumps(filters),
            }
        data = self.api.get_all_identifiers(
            self.api.get_all_from_api("/ct/terms/names", params=params),
            identifier=key,
            value=uid_key,
        )
        uid = data.get(value, None)
        if uid:
            self.log.debug(
                f"Found term with '{key}' == '{value}' in codelist '{codelist_name}', uid '{uid}'"
            )
            return uid

        err = f"Could not find term with '{key}' == '{value}' in codelist '{codelist_name}'"
        self.log.error(err)

        if not self.options.desperate:
            raise RuntimeError(err)

    @lru_cache(maxsize=10000)
    def get_term_uids_by_codelist(self, codelist_name):
        rs = requests.get(
            f"{self.api.api_base_url}/ct/terms?page_size=0&codelist_name={codelist_name}",
            headers=self.api.api_headers,
        ).json()["items"]

        return [item["term_uid"] for item in rs]

    @lru_cache(maxsize=10000)
    def lookup_concept_uid(self, name, endpoint, subset=None):
        self.log.info(f"Looking up concept {endpoint} with name '{name}'")
        filters = {"name": {"v": [name]}}
        path = f"/concepts/{endpoint}"
        params = {"filters": json.dumps(filters)}
        if subset:
            params["subset"] = subset
        items = self.api.get_all_from_api(path, params={"filters": json.dumps(filters)})
        if items is not None and len(items) > 0:
            uid = items[0].get("uid", None)
            self.log.info(
                f"Found concept {endpoint} with name '{name}' and uid '{uid}'"
            )
            return uid

        err = f"Could not find concept {endpoint} with name '{name}'"
        self.log.error(err)

        if not self.options.desperate:
            raise RuntimeError(err)

    def simple_post_and_approve(self, obj, method="POST", obj_uid=None):
        url = path_join(self.api.api_base_url, obj["path"])
        _url = None
        if obj_uid:
            _url = f"{url}/{obj_uid}"
            obj["body"]["change_description"] = "updated"
            obj["body"]["name"] += " updated"
            if obj["body"].get("name_sentence_case"):
                obj["body"]["name_sentence_case"] += " updated"
        response = requests.api.request(
            method=method,
            url=_url or url,
            headers=self.api.api_headers,
            json=obj["body"],
        )

        if response.ok:
            data = response.json()
            uid = data["uid"]
            approve_url = path_join(url, uid, "approvals")
            response = requests.post(approve_url, headers=self.api.api_headers)
            if response.ok:
                self.log.info(f"Posted and approved {obj['path']}: {uid}")

                if randint(0, 1):
                    new_version_url = path_join(url, uid, "versions")
                    new_version_response = requests.post(
                        new_version_url,
                        headers=self.api.api_headers,
                        json={
                            "change_description": "updated",
                            "name": obj["body"]["name"],
                        },
                    )
                    if new_version_response.ok:
                        self.simple_post_and_approve(obj, method="PATCH", obj_uid=uid)

                return uid

            self.log.error(f"Failed to approve {obj['path']}: {response.text}")
        else:
            self.log.error(f"Failed to post {obj['path']}: {response.text}")

        if not self.options.desperate:
            response.raise_for_status()

    def simple_post(self, obj, return_key="uid"):
        url = path_join(self.api.api_base_url, obj["path"])
        response = requests.post(
            url,
            headers=self.api.api_headers,
            json=obj["body"],
        )

        if response.ok:
            data = response.json()
            self.log.info(f"Posted {obj['path']}: {data.get('uid')}")

            if return_key is not None:
                return data[return_key]

            return data

        self.log.warning(f"Failed to post {obj['path']}: {response.text}")

        if not self.options.desperate:
            response.raise_for_status()

    def simple_get(self, url, params=None, *, return_key=None):
        url = path_join(self.api.api_base_url, url)

        response = requests.get(
            url,
            params=params,
            headers=self.api.api_headers,
        )

        if response.ok:
            data = response.json()
            if return_key:
                return data[return_key]
            return data

        self.log.error(f"Failed to GET {url}: {response.text}")

        if not self.options.desperate:
            response.raise_for_status()

    def create_activity_groups(self):
        total = self.simple_get(
            "/concepts/activities/activity-groups",
            {"page_size": 1, "total_count": True},
            return_key="total",
        )

        create = max(self.options.activity_groups - total, 0)

        self.log.info(
            "======== Found %i activity groups, creating %i ========", total, create
        )

        for n in range(total, total + create):
            payload = activity_group_payload(n)
            self.simple_post_and_approve(payload)

        self.activity_groups = [
            item["uid"]
            for item in self.simple_get(
                "/concepts/activities/activity-groups",
                {"page_size": 0},
                return_key="items",
            )
        ]

    def create_activity_subgroups(self):
        total = self.simple_get(
            "/concepts/activities/activity-sub-groups",
            {"page_size": 1, "total_count": True},
            return_key="total",
        )

        create = max(self.options.activity_subgroups - total, 0)

        self.log.info(
            "======== Found %i activity subgroups, creating %i ========", total, create
        )

        for n in range(total, total + create):
            group = self.activity_groups[n % len(self.activity_groups)]
            payload = activity_subgroup_payload(n, [group])
            self.simple_post_and_approve(payload)

        self.activity_groupings = [
            (None, activity_group["uid"], item["uid"])
            for item in self.simple_get(
                "/concepts/activities/activity-sub-groups",
                {"page_size": 0},
                return_key="items",
            )
            for activity_group in item["activity_groups"]
        ]

    def create_activities(self):
        total = self.simple_get(
            "/concepts/activities/activities",
            {
                "filters": json.dumps(
                    {
                        "library_name": {
                            "v": [LIBRARY_NAME_REQUESTED, LIBRARY_NAME_SPONSOR]
                        }
                    }
                ),
                "page_size": 1,
                "total_count": True,
            },
            return_key="total",
        )

        create = max(self.options.activities - total, 0)

        self.log.info(
            "======== Found %i activities, creating %i ========", total, create
        )
        libs = [LIBRARY_NAME_REQUESTED, LIBRARY_NAME_SPONSOR]
        for n in range(total, total + create):
            grouping = self.activity_groupings[n % len(self.activity_groupings)]
            payload = activity_payload(
                n,
                libs[n % 2],
                *grouping[1:],
            )
            self.simple_post_and_approve(payload)

        activities = self.simple_get(
            "/concepts/activities/activities",
            {
                "filters": json.dumps(
                    {
                        "library_name": {
                            "v": [LIBRARY_NAME_REQUESTED, LIBRARY_NAME_SPONSOR]
                        }
                    }
                ),
                "page_size": 0,
            },
            return_key="items",
        )

        self.activities = [item["uid"] for item in activities]

        self.activity_groupings = [
            (
                item["uid"],
                activity_grouping["activity_group_uid"],
                activity_grouping["activity_subgroup_uid"],
            )
            for item in activities
            for activity_grouping in item["activity_groupings"]
        ]

    def create_activity_requests(self):
        total = self.simple_get(
            "/concepts/activities/activities",
            {"library_name": LIBRARY_NAME_REQUESTED, "page_size": 1, "total_count": True},
            return_key="total",
        )

        create = max(self.options.activity_requests - total, 0)

        self.log.info(
            "======== Found %i activity requests, creating %i ========", total, create
        )

        for n in range(total, total + create):
            grouping = self.activity_groupings[n % len(self.activity_groupings)]
            payload = activity_payload(
                n,
                LIBRARY_NAME_REQUESTED,
                *grouping[1:],
            )
            self.simple_post_and_approve(payload)

        self.req_activities = [
            item["uid"]
            for item in self.simple_get(
                "/concepts/activities/activities",
                {"library_name": LIBRARY_NAME_REQUESTED, "page_size": 0},
                return_key="items",
            )
        ]

    def create_activity_instance_classes(self):
        total = self.simple_get(
            "/activity-instance-classes",
            {"page_size": 1, "total_count": True},
            return_key="total",
        )

        create = max(int(self.options.activity_instances / 5) - total, 0)

        self.log.info(
            "======== Found %i activity instance classes, creating %i ========",
            total,
            create,
        )

        for n in range(total, total + create):
            payload = activity_instance_class_payload(n, LIBRARY_NAME_SPONSOR)
            self.simple_post_and_approve(payload)

        self.activity_instance_classes = [
            item["uid"]
            for item in self.simple_get(
                "/activity-instance-classes",
                {"page_size": 0},
                return_key="items",
            )
        ]

    def create_activity_instances(self):
        total = self.simple_get(
            "/concepts/activities/activity-instances",
            {"page_size": 1, "total_count": True},
            return_key="total",
        )

        create = max(self.options.activity_instances - total, 0)

        self.log.info(
            "======== Found %i activity instances, creating %i ========", total, create
        )

        for n in range(total, total + create):
            grouping = self.activity_groupings[(n + 3) % len(self.activity_groupings)]
            instance_class_uid = self.activity_instance_classes[
                n % len(self.activity_instance_classes)
            ]
            payload = activity_instance_payload(
                n,
                LIBRARY_NAME_SPONSOR,
                instance_class_uid,
                *grouping,
            )
            self.simple_post_and_approve(payload)

        self.activity_instances = [
            item["uid"]
            for item in self.simple_get(
                "/concepts/activities/activity-instances",
                {"page_size": 0},
                return_key="items",
            )
        ]

    def create_library(self):
        payload = library_payload()
        name = payload["body"]["name"]

        for programme in self.simple_get("/libraries", {"page_size": 0}):
            if programme["name"] == name:
                self.library = programme
                self.log.info("======== Using library: %s ========", programme["name"])
                return

        self.log.info("======== Creating library: %s ========", name)

        self.library = self.simple_post(payload, return_key=None)

    def create_clinical_programme(self):
        payload = clinical_programme_payload()
        name = payload["body"]["name"]

        for programme in self.simple_get("/clinical-programmes", {"page_size": 0})[
            "items"
        ]:
            if programme["name"] == name:
                self.clinical_programme = programme
                self.log.info(
                    "======== Using clinical programme: %s ========", programme["name"]
                )
                return

        self.log.info("======== Creating clinical programme: %s ========", name)

        self.clinical_programme = self.simple_post(payload, return_key=None)

    def create_project(self):
        payload = project_payload(clinical_programme_uid=self.clinical_programme["uid"])
        name = payload["body"]["name"]

        for project in self.simple_get("/projects", {"page_size": 0})["items"]:
            if project["name"] == name:
                self.project = project
                self.log.info("======== Using project: %s ========", project["name"])
                return

        self.log.info("======== Creating project: %s ========", name)

        self.project = self.simple_post(payload, return_key=None)

    def create_studies(self):
        time_units = requests.get(
            f"{self.api.api_base_url}/concepts/unit-definitions?subset=Study Time&page_size=0",
            headers=self.api.api_headers,
        ).json()["items"]

        visit_type_uids = sorted(
            self.get_term_uids_by_codelist("VisitType"), reverse=True
        )

        time_unit_uids = [
            unit["uid"]
            for unit in time_units
            if unit["conversion_factor_to_master"] > 1
        ]

        time_reference_uid = self.lookup_ct_term_uid(
            "Time Point Reference", "Global anchor visit"
        )

        filters = {
            "current_metadata.identification_metadata.project_number": {
                "v": [self.project["project_number"]]
            }
        }
        studies = self.simple_get(
            "/studies",
            {
                "page_size": 0,
                "filters": json.dumps(filters),
            },
        )["items"]

        found = len(studies)
        self.log.info(
            "======== Found %i dummy studies, creating %i ========",
            found,
            self.options.studies,
        )

        for n in range(self.options.studies):
            if n in [0, 5, 10, 15]:
                self.refresh_auth()

            payload = study_payload(found + n, self.project["project_number"])
            uid = self.simple_post(payload)

            if uid is not None:
                self.studies[uid] = {
                    "arms": [],
                    "elements": [],
                    "epochs": [],
                    "visits": [],
                    "activities": [],
                }
                self.log.info(
                    "======== Creating %i study arms for dummy study %i ========",
                    self.options.study_arms,
                    n,
                )
                for m in range(self.options.study_arms):
                    self.create_study_arm(m, uid)

                self.log.info(
                    "======== Creating %i study elements for dummy study %i ========",
                    self.options.study_elements,
                    n,
                )
                for m in range(self.options.study_elements):
                    self.create_study_element(m, uid)

                self.log.info(
                    "======== Creating 4 study epochs for dummy study %i ========",
                    n,
                )
                self.create_study_epochs(uid, "Screening", 1)
                self.create_study_epochs(uid, "Intervention", 2)
                self.create_study_epochs(uid, "Intervention", 3)
                self.create_study_epochs(uid, "Follow-up", 4)

                self.log.info(
                    "======== Creating %i study activities for dummy study %i ========",
                    self.options.study_activities,
                    n,
                )
                self.create_study_activities(self.options.study_activities, uid)

                self.log.info(
                    "======== Creating 43 study visits for dummy study %i ========",
                    n,
                )
                epoch_uid = self.studies[uid]["epochs"][0]

                self.create_study_visit(
                    nbr=1,
                    study_uid=uid,
                    epoch_uid=epoch_uid,
                    visit_type_uid=visit_type_uids[m % len(visit_type_uids)],
                    time_unit_uid=time_unit_uids[m % len(time_unit_uids)],
                    time_reference_uid=time_reference_uid,
                )

                epoch_uid = self.studies[uid]["epochs"][1]

                for j in range(2, 19):
                    self.create_study_visit(
                        nbr=j,
                        study_uid=uid,
                        epoch_uid=epoch_uid,
                        visit_type_uid=visit_type_uids[m % len(visit_type_uids)],
                        time_unit_uid=time_unit_uids[m % len(time_unit_uids)],
                        time_reference_uid=time_reference_uid
                        if j != 2
                        else self.lookup_ct_term_uid(
                            "Time Point Reference", "Global anchor visit"
                        ),
                        time_value=None if j != 2 else 0,
                        is_global_anchor_visit=j == 2,
                    )

                epoch_uid = self.studies[uid]["epochs"][2]

                for j in range(19, 43):
                    self.create_study_visit(
                        nbr=j,
                        study_uid=uid,
                        epoch_uid=epoch_uid,
                        visit_type_uid=visit_type_uids[m % len(visit_type_uids)],
                        time_unit_uid=time_unit_uids[m % len(time_unit_uids)],
                        time_reference_uid=time_reference_uid,
                    )

                epoch_uid = self.studies[uid]["epochs"][3]

                self.create_study_visit(
                    nbr=43,
                    study_uid=uid,
                    epoch_uid=epoch_uid,
                    visit_type_uid=visit_type_uids[m % len(visit_type_uids)],
                    time_unit_uid=time_unit_uids[m % len(time_unit_uids)],
                    time_reference_uid=time_reference_uid,
                )

                self.create_study_activity_schedules(uid)

    def create_study_arm(self, nbr, study_uid):
        arm_type = get_arm_types(nbr)
        arm_type_uid = self.lookup_ct_term_uid("Arm Type", arm_type)
        payload = study_arm_payload(nbr, arm_type_uid, study_uid)
        uid = self.simple_post(payload, "arm_uid")
        if uid is not None:
            self.studies[study_uid]["arms"].append(uid)

    def create_study_element(self, nbr, study_uid):
        element_type, element_subtype = get_element_types(nbr)
        element_uid = self.lookup_ct_term_uid("Element Type", element_type)
        element_subtype_uid = self.lookup_ct_term_uid(
            "Element Sub Type", element_subtype
        )
        payload = study_element_payload(
            nbr, element_uid, element_subtype_uid, study_uid
        )
        uid = self.simple_post(payload, "element_uid")
        if uid is not None:
            self.studies[study_uid]["elements"].append(uid)

    def create_study_epochs(self, study_uid, subtype_name, nbr):
        epoch_subtype_uid = self.lookup_ct_term_uid("Epoch Sub Type", subtype_name)
        epoch_uid = self.simple_post(
            {
                "path": f"/studies/{study_uid}/study-epochs/preview",
                "body": {"study_uid": study_uid, "epoch_subtype": epoch_subtype_uid},
            },
            return_key="epoch",
        )
        duration_unit = self.lookup_concept_uid("day", "unit-definitions")
        payload = study_epoch_payload(
            nbr, epoch_uid, epoch_subtype_uid, duration_unit, study_uid
        )
        uid = self.simple_post(payload)
        if uid is not None:
            self.studies[study_uid]["epochs"].append(uid)

    def create_study_activities(self, nbr_activities_per_study, study_uid):
        activities = requests.get(
            f"""{self.api.api_base_url}/concepts/activities/activities?sort_by={{"uid": false}}&page_size={nbr_activities_per_study}""",
            headers=self.api.api_headers,
        ).json()["items"]

        for idx, activity in enumerate(activities):
            soa_group_term_uid = self.lookup_ct_term_uid(
                "Flowchart Group",
                get_soa_group_name(idx),
            )
            for groupings in activity["activity_groupings"]:
                payload = study_activity_payload(
                    soa_group_term_uid,
                    activity["uid"],
                    groupings["activity_subgroup_uid"],
                    groupings["activity_group_uid"],
                    study_uid,
                )

                uid = self.simple_post(payload, "study_activity_uid")

                if uid is not None:
                    self.studies[study_uid]["activities"].append(uid)

    def create_study_activity_schedules(self, study_uid):
        for study_visit in iter_one_visit_per_group(self.studies[study_uid]["visits"]):
            for study_activity_uid in self.studies[study_uid]["activities"]:
                if randint(1, 80) % 4:
                    continue

                payload = {
                    "study_activity_uid": study_activity_uid,
                    "study_visit_uid": study_visit["uid"],
                }

                study_activity_schedule_uid = self.simple_post(
                    {
                        "path": f"/studies/{study_uid}/study-activity-schedules",
                        "body": payload,
                    },
                    "study_activity_schedule_uid",
                )

    def create_study_visit(
        self,
        nbr,
        study_uid,
        epoch_uid,
        visit_type_uid,
        time_unit_uid,
        time_reference_uid,
        time_value: int | None = None,
        is_global_anchor_visit: bool = False,
    ):
        contact_mode_uids = self.get_term_uids_by_codelist("Visit Contact Mode")

        payload = study_visit_payload(
            nbr,
            study_uid,
            epoch_uid,
            visit_type_uid,
            time_unit_uid,
            time_reference_uid,
            contact_mode_uids[nbr % len(contact_mode_uids)],
            time_value=time_value,
            is_global_anchor_visit=is_global_anchor_visit,
        )

        study_visit = self.simple_post(payload, return_key=None)

        if study_visit:
            self.studies[study_uid]["visits"].append(study_visit)

    def create_syntax_templates(self):
        req = requests.get(
            f"{self.api.api_base_url}/dictionaries/codelists?library_name=SNOMED&page_size=0",
            headers=self.api.api_headers,
        ).json()

        disease_disorder_codelist_uid = next(
            codelist
            for codelist in req["items"]
            if codelist["name"] == "DiseaseDisorder"
        )["codelist_uid"]
        disease_disorder_terms = requests.get(
            f"{self.api.api_base_url}/dictionaries/terms?codelist_uid={disease_disorder_codelist_uid}&page_size=0",
            headers=self.api.api_headers,
        ).json()["items"]
        disease_disorder_term_uids = [
            disease_disorder_term["term_uid"]
            for disease_disorder_term in disease_disorder_terms
        ]

        self.create_objective_templates(disease_disorder_term_uids)

        self.create_endpoint_templates(disease_disorder_term_uids)

        self.create_criteria_templates(disease_disorder_term_uids)

        self.create_activity_instruction_templates(disease_disorder_term_uids)

        self.create_footnote_templates(disease_disorder_term_uids)

        self.create_timeframe_templates()

    def create_objective_templates(self, disease_disorder_term_uids):
        objective_category_uids = self.get_term_uids_by_codelist("Objective Category")

        total = self.simple_get(
            "/objective-templates",
            {"page_size": 1, "total_count": True},
            return_key="total",
        )

        create = max(self.options.objective_templates - total, 0)

        self.log.info(
            "======== Found %i objective templates, creating %i ========", total, create
        )

        for n in range(total, total + create):
            payload = objective_template_payload(
                n, disease_disorder_term_uids[n::4], objective_category_uids[n::4]
            )
            self.simple_post_and_approve(payload)

        self.objective_templates = [
            item["uid"]
            for item in self.simple_get(
                "/objective-templates",
                {"page_size": 0},
                return_key="items",
            )
        ]

    def create_endpoint_templates(self, disease_disorder_term_uids):
        endpoint_category_uids = self.get_term_uids_by_codelist("Endpoint Category")
        endpoint_subcategory_uids = self.get_term_uids_by_codelist(
            "Endpoint Sub Category"
        )

        total = self.simple_get(
            "/endpoint-templates",
            {"page_size": 1, "total_count": True},
            return_key="total",
        )

        create = max(self.options.endpoint_templates - total, 0)

        self.log.info(
            "======== Found %i endpoint templates, creating %i ========", total, create
        )

        for n in range(total, total + create):
            payload = endpoint_template_payload(
                n,
                disease_disorder_term_uids[n::4],
                endpoint_category_uids[n::4],
                endpoint_subcategory_uids[n::4],
            )
            self.simple_post_and_approve(payload)

        self.endpoint_templates = [
            item["uid"]
            for item in self.simple_get(
                "/endpoint-templates",
                {"page_size": 0},
                return_key="items",
            )
        ]

    def create_criteria_templates(self, disease_disorder_term_uids):
        criteria_type_uids = self.get_term_uids_by_codelist("Criteria Type")
        criteria_category_uids = self.get_term_uids_by_codelist("Criteria Category")
        criteria_subcategory_uids = self.get_term_uids_by_codelist(
            "Criteria Sub Category"
        )

        self.log.info(
            "======== Creating %i criteria templates of each type ========",
            self.options.criteria_templates,
        )

        for criteria_type_uid in criteria_type_uids:
            total = self.simple_get(
                "/criteria-templates",
                {
                    "page_size": 1,
                    "total_count": True,
                    "filters": json.dumps(
                        {"type.term_uid": {"v": [criteria_type_uid]}}
                    ),
                },
                return_key="total",
            )

            for n in range(total, self.options.criteria_templates):
                payload = criteria_template_payload(
                    n,
                    disease_disorder_term_uids[n::4],
                    criteria_category_uids[n::4],
                    criteria_subcategory_uids[n::4],
                    criteria_type_uid,
                )
                self.simple_post_and_approve(payload)

        self.criteria_templates = [
            item["uid"]
            for item in self.simple_get(
                "/criteria-templates",
                {"page_size": 0},
                return_key="items",
            )
        ]

    def create_activity_instruction_templates(self, disease_disorder_term_uids):
        total = self.simple_get(
            "/activity-instruction-templates",
            {"page_size": 1, "total_count": True},
            return_key="total",
        )

        create = max(self.options.activity_instruction_templates - total, 0)

        self.log.info(
            "======== Found %i activity instruction templates, creating %i ========",
            total,
            create,
        )

        for n in range(total, total + create):
            groupings = self.activity_groupings[n % len(self.activity_groupings)]
            payload = activity_instruction_template_payload(
                n,
                disease_disorder_term_uids[n::4],
                [groupings[0]],
                [groupings[1]],
                [groupings[2]],
            )
            self.simple_post_and_approve(payload)

        self.activity_instruction_templates = [
            item["uid"]
            for item in self.simple_get(
                "/activity-instruction-templates",
                {"page_size": 0},
                return_key="items",
            )
        ]

    def create_footnote_templates(self, disease_disorder_term_uids):
        footnote_type_uids = self.get_term_uids_by_codelist("Footnote Type")

        self.log.info(
            "======== Creating %i footnote templates of each type ========",
            self.options.footnote_templates,
        )

        for footnote_type_uid in footnote_type_uids:
            total = self.simple_get(
                "/footnote-templates",
                {
                    "page_size": 1,
                    "total_count": True,
                    "filters": json.dumps(
                        {"type.term_uid": {"v": [footnote_type_uid]}}
                    ),
                },
                return_key="total",
            )

            for n in range(total, self.options.footnote_templates):
                groupings = self.activity_groupings[n % len(self.activity_groupings)]
                payload = footnote_template_payload(
                    n,
                    disease_disorder_term_uids[n::4],
                    footnote_type_uid,
                    [groupings[0]],
                    [groupings[1]],
                    [groupings[2]],
                )
                self.simple_post_and_approve(payload)

        self.footnote_templates = [
            item["uid"]
            for item in self.simple_get(
                "/footnote-templates",
                {"page_size": 0},
                return_key="items",
            )
        ]

    def create_timeframe_templates(self):
        total = self.simple_get(
            "/timeframe-templates",
            {"page_size": 1, "total_count": True},
            return_key="total",
        )

        create = max(self.options.timeframe_templates - total, 0)

        self.log.info(
            "======== Found %i timeframe templates, creating %i ========",
            total,
            create,
        )

        for n in range(total, total + create):
            payload = timeframe_template_payload(n)
            uid = self.simple_post_and_approve(payload)
            if uid is not None:
                self.timeframe_templates.append(uid)

        self.footnote_templates = [
            item["uid"]
            for item in self.simple_get(
                "/timeframe-templates",
                {"page_size": 0},
                return_key="items",
            )
        ]

    def run(self):
        self.log.info("======== Importing dummy data ========")
        self.create_library()
        self.create_clinical_programme()
        self.create_project()
        self.create_activity_groups()
        self.create_activity_subgroups()
        self.create_activities()
        # self.create_activity_requests()
        self.create_activity_instance_classes()
        self.create_activity_instances()
        self.create_syntax_templates()
        self.create_studies()
        self.log.info("Done importing dummy data")


def parse_args():
    import argparse
    from os import getenv

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--desperate",
        action="store_true",
        help="Desperately create dummy data, ignoring error responses from the API",
    )

    parser.add_argument(
        "--objective-templates",
        type=int,
        default=getenv("num_objective_templates", 151),
        help="Number of objective templates to create",
    )
    parser.add_argument(
        "--endpoint-templates",
        type=int,
        default=getenv("num_endpoint_templates", 151),
        help="Number of endpoint templates to create",
    )
    parser.add_argument(
        "--criteria-templates",
        type=int,
        default=getenv("num_criteria_templates", 151),
        help="Number of criteria templates to create",
    )
    parser.add_argument(
        "--activity-instruction-templates",
        type=int,
        default=getenv("num_activity_instruction_templates", 151),
        help="Number of activity instruction_templates to create",
    )
    parser.add_argument(
        "--footnote-templates",
        type=int,
        default=getenv("num_footnote_templates", 151),
        help="Number of footnote templates to create",
    )
    parser.add_argument(
        "--timeframe-templates",
        type=int,
        default=getenv("num_timeframe_templates", 151),
        help="Number of timeframe templates to create",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=getenv("num_epochs", 19),
        help="Number of epochs to create",
    )
    parser.add_argument(
        "--activity-groups",
        type=int,
        default=getenv("num_activity_groups", 31),
        help="Number of activity groups to create",
    )
    parser.add_argument(
        "--activity-subgroups",
        type=int,
        default=getenv("num_activity_subgroups", 53),
        help="Number of activity sub-groups to create",
    )
    parser.add_argument(
        "--activities",
        type=int,
        default=getenv("num_activities", 300),
        help="Number of activities to create",
    )
    parser.add_argument(
        "--activity-instances",
        type=int,
        default=getenv("num_activity_instances", 91),
        help="Number of activity instances to create",
    )
    # parser.add_argument(
    #     "--activity-requests",
    #     type=int,
    #     default=getenv("num_activity_requests", 51),
    #     help="Number of activity requests to create",
    # )
    parser.add_argument(
        "--studies",
        type=int,
        default=getenv("num_studies", 13),
        help="Number of studies to create",
    )
    parser.add_argument(
        "--study-arms",
        type=int,
        default=getenv("num_arms", 2),
        help="Number of arms to create",
    )
    parser.add_argument(
        "--study-elements",
        type=int,
        default=getenv("num_elements", 8),
        help="Number of elements to create",
    )
    parser.add_argument(
        "--study-epochs",
        type=int,
        default=getenv("num_study_epochs", 11),
        help="Number of epochs to create per study",
    )
    parser.add_argument(
        "--study-activities",
        type=int,
        default=getenv("num_study_activities", 197),
        help="Number of activities to create per study",
    )
    parser.add_argument(
        "--study-visits",
        type=int,
        default=getenv("num_study_visits", 37),
        help="Number of visits to create  per study",
    )

    options = parser.parse_args()

    return options


def main():
    options = parse_args()
    migrator = DummyData(options)
    migrator.run()


if __name__ == "__main__":
    main()
