import ssl
import httpx
import httpx_auth
from os import environ
import os
import logging
import sys
import json

OUTPUT_DIR = environ.get("OUTPUT_DIR", "./output")
LOG_LEVEL = environ.get("LOG_LEVEL", "INFO")

INCLUDE_STUDY_NUMBERS = environ.get("INCLUDE_STUDY_NUMBERS", "")
EXCLUDE_STUDY_NUMBERS = environ.get("EXCLUDE_STUDY_NUMBERS", "")

DEFAULT_QUERY_PARAMS = {
    "page_size": 0,
    "page_number": 1,
}

# ---------------------------------------------------------------
# Api bindings
# ---------------------------------------------------------------
#
class StudyExporter:
    def __init__(self):
        numeric_level = getattr(logging, LOG_LEVEL.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError("Invalid log level: %s" % LOG_LEVEL)
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.log = logging.getLogger("studybuilder_export")
        self.api_base_url = self._read_env("API_BASE_URL")
        self._create_httpx_client()
        self.verify_connection()

    def _read_env(self, varname):
        value = environ.get(varname)
        if not value:
            msg = f"missing {varname} env variable"
            self.log.error(msg)
            raise RuntimeError(msg)
        return value

    def _create_httpx_client(self):
        """
        Creates the HTTPX client with the appropriate authentication method
        based on the environment variables.
        """
        client_id = environ.get("CLIENT_ID", "")
        scope = environ.get("SCOPE", "")
        token_endpoint = environ.get("TOKEN_ENDPOINT", "")
        auth_endpoint = environ.get("AUTH_ENDPOINT", "")
        client_secret = environ.get("CLIENT_SECRET", "")

        # HTTPX doesn't automatically use the REQUESTS_CA_BUNDLE environment variable
        ca_bundle = os.environ.get("REQUESTS_CA_BUNDLE", "")
        if ca_bundle:
            context = ssl.create_default_context(
                cafile=ca_bundle
            )
        else:
            context = None

        if not client_id:
            self.log.info("No CLIENT_ID provided, running without authentication")
            auth = None
        elif client_secret:
            self.log.info("CLIENT_ID and CLIENT_SECRET provided, enabling authentication")
            auth = httpx_auth.OAuth2ClientCredentials(
                token_url=token_endpoint,
                client_id=client_id,
                client_secret=client_secret,
                scope=scope,
            )
        else:
            self.log.info("CLIENT_ID provided without CLIENT_SECRET, using interactive authentication")
            auth = httpx_auth.OAuth2AuthorizationCodePKCE(
                authorization_url=auth_endpoint,
                token_url=token_endpoint,
                client_id=client_id,
                scope=scope,
            )
        self.client = httpx.Client(base_url=self.api_base_url, auth=auth, verify=context, timeout=60)


    # ---------------------------------------------------------------
    # Verify connection to api (and database)
    # ---------------------------------------------------------------
    #
    # Verify that Clinical MDR API is online
    # TODO Replace with api health check resource ...
    def verify_connection(self):
        try:
            response = self.client.get("/libraries")
            response.raise_for_status()
            self.log.info(f"Connected to api at {self.api_base_url}")
        except Exception as e:
            self.log.error(
                f"Failed to connect to backend, is it running?\nError was:\n{e}"
            )
            sys.exit(1)

    def get_from_api(self, path, params=None, items_only=True):
        # Make sure that we always provide the page_size parameter,
        # otherwise the api uses its default of 10.
        if params is None:
            params = DEFAULT_QUERY_PARAMS
        else:
            for key, value in DEFAULT_QUERY_PARAMS.items():
                if key not in params:
                    params[key] = value

        response = self.client.get(path, params=params)
        if response.is_success:
            self.log.info(f"Successfully fetched data from: {path}")
            data = response.json()
            if items_only and isinstance(data, dict) and "items" in data.keys():
                return data["items"]
            return data
        else:
            if "message" in response.json():
                self.log.error("get %s %s", path, response.json()["message"])
            else:
                self.log.error("get %s %s", path, response.text)
            return None

    def get_from_api_paged(self, path, params=None, page_size=100):
        page_number = 1
        page_params = {
            "page_number": page_number,
            "page_size": page_size,
            "total_count": True,
        }
        page_params.update(params)
        data = self.get_from_api(path, params=page_params, items_only=False)
        all_data = data["items"]
        count = data["total"]

        # Get remaining pages
        page_params["total_count"] = False
        while page_size * page_number < count:
            page_number += 1
            page_params["page_number"] = page_number
            data = self.get_from_api(path, params=page_params, items_only=True)
            all_data.extend(data)
        return all_data

    def get_dictionary_uid(self, library):
        params = {"library_name": library}
        data = self.get_from_api(f"/dictionaries/codelists", params=params)
        if data is None:
            return None
        if len(data) == 0:
            return None
        return data[0].get("codelist_uid")

    def save_formatted_json(self, data, dir, filename):
        filename = filename.replace("/", ".")
        path = os.path.join(dir, filename)
        with open(path, "w") as f:
            self.log.info(f"Saving to file: {path}")
            f.write(json.dumps(data, indent=2, sort_keys=True))

    def filter_studies(self, studies):
        include_numbers = [
            int(nbr) for nbr in INCLUDE_STUDY_NUMBERS.split(",") if len(nbr.strip()) > 0
        ]
        exclude_numbers = [
            int(nbr) for nbr in EXCLUDE_STUDY_NUMBERS.split(",") if len(nbr.strip()) > 0
        ]
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


study_optional_fields = [
    "current_metadata.study_description",
    "current_metadata.identification_metadata",
    "current_metadata.high_level_study_design",
    "current_metadata.study_population",
    "current_metadata.study_intervention",
]

study_design_endpoints = [
    "studies/{study_uid}/study-arms",
    "studies/{study_uid}/study-cohorts",
    "studies/{study_uid}/study-elements",
    "studies/{study_uid}/study-branch-arms",
    "studies/{study_uid}/study-epochs",
    "studies/{study_uid}/study-visits",
    "studies/{study_uid}/study-design-cells",
    "studies/{study_uid}/study-endpoints",
    "studies/{study_uid}/study-criteria",
    "studies/{study_uid}/study-activities",
    "studies/{study_uid}/study-objectives",
    "studies/{study_uid}/study-activity-schedules",
    "studies/{study_uid}/study-compounds",
]

template_endpoints = [
    "criteria-templates",
    "endpoint-templates",
    "objective-templates",
    "timeframe-templates",
    "footnote-templates",
    "activity-instruction-templates",
]

syntax_pre_instance_endpoints = [
    "criteria-pre-instances",
    "endpoint-pre-instances",
    "objective-pre-instances",
    "footnote-pre-instances",
    "activity-instruction-pre-instances",
]

sponsor_ct_extensions = [
    {
        "endpoint": "ct/terms",
        "parameters": {"codelist_name": "Unit", "library_name": "Sponsor"},
        "page_size": None,
    }
]

concept_endpoints = [
    {
        "endpoint": "concepts/unit-definitions",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/compounds",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/compound-aliases",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/activities/activity-instances",
        "parameters": {"library_name": "Sponsor"},
        "page_size": 100,
    },
    {
        "endpoint": "concepts/activities/activity-groups",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/activities/activity-sub-groups",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/activities/activities",
        "parameters": {"library_name": "Sponsor"},
        "page_size": 100,
    },
    {
        "endpoint": "concepts/odms/items",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/odms/item-groups",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/odms/templates",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/odms/forms",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/numeric-values",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/numeric-values-with-unit",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/text-values",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/visit-names",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/study-days",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/study-weeks",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/study-duration-days",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/study-duration-weeks",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/time-points",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    },
    {
        "endpoint": "concepts/lag-times",
        "parameters": {"library_name": "Sponsor"},
        "page_size": None,
    }
]

activity_endpoints = [
    {
        "endpoint": "activity-item-classes",
        "parameters": {"library_name": "Sponsor"},
        "page_size": 100,
    },
    {
        "endpoint": "activity-instance-classes",
        "parameters": {"library_name": "Sponsor"},
        "page_size": 100,
    }
]

dictionaries = [
    "SNOMED",
    "UNII",
    "MED-RT",
    "UCUM"
]


def run_export():
    try:
        os.mkdir("output")
    except FileExistsError:
        pass
    api = StudyExporter()

    # Clinical programmes
    api.log.info("=== Export clinical programmes ===")
    programmes = api.get_from_api("/clinical-programmes")
    api.save_formatted_json(programmes, OUTPUT_DIR, "clinical-programmes.json")

    # Brands
    api.log.info("=== Export brands ===")
    brands = api.get_from_api("/brands")
    api.save_formatted_json(brands, OUTPUT_DIR, "brands.json")

    # Projects
    api.log.info("=== Export projects ===")
    projects = api.get_from_api("/projects")
    api.save_formatted_json(projects, OUTPUT_DIR, "projects.json")

    # Studies
    api.log.info("=== Export studies ===")
    studies = api.get_from_api(f"/studies")
    studies = api.filter_studies(studies)
    api.save_formatted_json(studies, OUTPUT_DIR, "studies.json")
    study_uids = [s["uid"] for s in studies]
    api.log.info(f"Found studies {study_uids}")

    # Study metadata
    api.log.info("=== Export study metadata ===")
    # Include all optional fields
    # , --> %2C
    # + --> %2B
    fields = "%2C".join(["%2B" + f for f in study_optional_fields])
    for uid in study_uids:
        api.log.info(f"Export metadata for study uid: {uid}")
        study = api.get_from_api(f"/studies/{uid}?fields={fields}")
        api.save_formatted_json(study, OUTPUT_DIR, f"studies/{uid}.json")

    # Study design
    api.log.info("=== Export study design ===")
    for uid in study_uids:
        api.log.info(f"Export study design for study uid: {uid}")
        for ep in study_design_endpoints:
            study_ep = ep.format(study_uid=uid)
            data = api.get_from_api(f"/{study_ep}")
            api.save_formatted_json(data, OUTPUT_DIR, f"{study_ep}.json")

    # Templates
    api.log.info("=== Export syntax templates ===")
    for ep in template_endpoints:
        data = api.get_from_api(f"/{ep}")
        api.save_formatted_json(data, OUTPUT_DIR, f"{ep}.json")

    # Templates pre-instances
    api.log.info("=== Export syntax pre-instances ===")
    for ep in syntax_pre_instance_endpoints:
        data = api.get_from_api(f"/{ep}")
        api.save_formatted_json(data, OUTPUT_DIR, f"{ep}.json")

    # Sponsor extensions to CT packages
    api.log.info("=== Export sponsor extensions ===")
    for ext in sponsor_ct_extensions:
        ep = ext["endpoint"]
        params = ext["parameters"]
        page_size = ext["page_size"]
        codelist_name = params["codelist_name"]
        api.log.info(f"Export sponsor extensions to {codelist_name} codelist")

        # Small dataset, no need to split into pages.
        if page_size is None:
            data = api.get_from_api(f"/{ep}", params=params)
            api.save_formatted_json(data, OUTPUT_DIR, f"{ep}.{codelist_name}.json")

        # Large dataset, split request into pages.
        else:
            data = api.get_from_api_paged(f"/{ep}", params=params, page_size=page_size)
            api.save_formatted_json(data, OUTPUT_DIR, f"{ep}.{codelist_name}.json")

    # Concepts
    api.log.info("=== Export concepts ===")
    for cpt in concept_endpoints:
        ep = cpt["endpoint"]
        params = cpt["parameters"]
        page_size = cpt["page_size"]
        concept_name = ep.rsplit("/", 1)[1]
        api.log.info(f"Export concept: {concept_name}")

        # Small dataset, no need to split into pages.
        if page_size is None:
            data = api.get_from_api(f"/{ep}", params=params)
            api.save_formatted_json(data, OUTPUT_DIR, f"{ep}.json")

        # Large dataset, split request into pages.
        else:
            data = api.get_from_api_paged(f"/{ep}", params=params, page_size=page_size)
            api.save_formatted_json(data, OUTPUT_DIR, f"{ep}.json")

    # Activity items etc
    api.log.info("=== Export activity items, classes etc ===")
    for cpt in activity_endpoints:
        ep = cpt["endpoint"]
        params = cpt["parameters"]
        page_size = cpt["page_size"]
        api.log.info(f"Export activity data: {ep}")

        # Small dataset, no need to split into pages.
        if page_size is None:
            data = api.get_from_api(f"/{ep}", params=params)
            api.save_formatted_json(data, OUTPUT_DIR, f"{ep}.json")

        # Large dataset, split request into pages.
        else:
            data = api.get_from_api_paged(f"/{ep}", params=params, page_size=page_size)
            api.save_formatted_json(data, OUTPUT_DIR, f"{ep}.json")

    # Dictionaries
    api.log.info("=== Export dictionaries ===")
    for d in dictionaries:
        api.log.info(f"Export dictionary: {d}")
        uid = api.get_dictionary_uid(d)
        if uid is None:
            api.log.error(f"Could not find dictionary: {d}")
            continue
        params = {"codelist_uid": uid}
        data = api.get_from_api("/dictionaries/terms", params=params)
        api.save_formatted_json(data, OUTPUT_DIR, f"dictionaries.{d}.json")


    # All done
    api.log.info(f"=== Export completed successfully ===")


if __name__ == "__main__":
    run_export()
