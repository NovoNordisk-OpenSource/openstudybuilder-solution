import asyncio
import copy
import csv
import json
import logging
import threading
import time
from collections.abc import Callable
from functools import lru_cache, wraps
from typing import Dict

import aiohttp
import requests

from ..functions.utils import create_logger, load_env
from ..utils import import_templates
from .api_bindings import (
    CODELIST_NAME_MAP,
    CODELIST_SDTM_DOMAIN_ABBREVIATION,
    UNIT_SUBSET_AGE,
    ApiBinding,
    get_error_message,
    status_ok,
)
from .metrics import Metrics

logger = logging.getLogger("legacy_mdr_migrations - utils")

metrics = Metrics()

API_HEADERS = {"Accept": "application/json", "User-Agent": "test"}

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
API_BASE_URL = load_env("API_BASE_URL")


# Decorator to avoid starting every function with the open() context manager
def open_file():
    def open_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self = args[0]
            filename = args[1]
            if filename:
                self.log.info(f"Opening file: {filename}")
                try:
                    with open(filename, encoding="utf-8", errors="ignore") as textfile:
                        return func(self, textfile, *args[2:], **kwargs)
                except FileNotFoundError:
                    self.log.error(f"File {filename} not found, skipping")
            else:
                self.log.info("Empty filename, skipping")

        return wrapper

    return open_decorator


# Decorator to avoid starting every function with the open() context manager
def open_file_async():
    def open_decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            self = args[0]
            filename = args[1]
            if filename:
                self.log.info(f"Opening file: {filename}")
                try:
                    with open(filename, encoding="utf-8", errors="ignore") as textfile:
                        await func(self, textfile, *args[2:], **kwargs)
                except FileNotFoundError:
                    self.log.error(f"File {filename} not found, skipping")
            else:
                self.log.info("Empty filename, skipping")

        return wrapper

    return open_decorator


class BaseImporter:
    logging_name = "legacy_mdr_migrations"

    def __init__(self, api=None, metrics_inst=None):
        self.log = create_logger(self.logging_name)
        if metrics_inst is None:
            self.metrics = Metrics()
        else:
            self.metrics = metrics_inst
        if api is None:
            headers = self._authenticate(API_HEADERS)
            self.api = ApiBinding(API_BASE_URL, headers, self.metrics, logger=self.log)
        else:
            self.api = api

        self.visit_type_codelist_name = "VisitType"
        self.element_subtype_codelist_name = "Element Sub Type"
        self._start_auth_refresh()

    def _start_auth_refresh(self, interval=25 * 60):
        def refresh_loop():
            while True:
                try:
                    time.sleep(interval)
                    self.refresh_auth()
                    self.log.info("Auth token refreshed")
                except Exception as e:
                    self.log.error("Auth refresh failed: %s", e)

        t = threading.Thread(target=refresh_loop, daemon=True)
        t.start()

    def refresh_auth(self):
        headers = self._authenticate(API_HEADERS)
        self.api.update_headers(headers)

    @staticmethod
    def _authenticate(headers: Dict) -> Dict:
        """Authenticates with client secret flow and appends Authorization header the dict of API request headers"""

        headers = headers.copy()

        client_id = load_env("CLIENT_ID", "")

        api_token = load_env("STUDYBUILDER_API_TOKEN", "")

        if api_token:
            logger.info(
                "Using API access token from STUDYBUILDER_API_TOKEN env variable"
            )
            headers["Authorization"] = f"Bearer {api_token}"

        elif client_id:
            logger.info(
                "Fetching API access token using CLIENT_SECRET, TOKEN_ENDPOINT, SCOPE env variables"
            )
            client_secret = load_env("CLIENT_SECRET")
            token_endpoint = load_env("TOKEN_ENDPOINT")
            scope = load_env("SCOPE")

            response = requests.post(
                token_endpoint,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "client_credentials",
                    "scope": scope,
                },
            )

            response.raise_for_status()
            payload = response.json()

            access_token = payload.get("access_token")
            if not access_token:
                msg = "missing access token from token payload"
                logger.error(msg)
                raise RuntimeError(msg)

            token_type = payload.get("token_type")
            if not access_token:
                msg = "missing token type from token payload"
                logger.error(msg)
                raise RuntimeError(msg)
            logger.info(
                "Successfully fetched API access token of type '%s'", token_type
            )
            headers["Authorization"] = f"{token_type} {access_token}"

        else:
            logger.info(
                "No authentication method specified, proceeding without Authorization header"
            )

        return headers

    def run(self):
        pass

    def prepare(self):
        pass

    ############ helper functions ###########

    # Check if a codelist contains a term with sponsor preferred name equal to the given name.
    def search_codelist(self, codelist, name):
        for item in codelist:
            if (
                item.get("name", {}).get("sponsor_preferred_name", "").lower()
                == name.lower()
            ):
                return True
        return False

    # Search a codelist for a term with the given sponsor preferred name.
    # For use with codelists fetched like:
    # terms = self.api.get_terms_for_codelist_name("Objective Category")
    def get_uid_for_sponsor_preferred_name(self, terms, name):
        for item in terms:
            try:
                if item["name"]["sponsor_preferred_name"] == name:
                    return item["term_uid"]
            except KeyError:
                pass

    async def post_and_approve_term(self, data: dict, session: aiohttp.ClientSession):
        post_data = {
            "catalogue_names": data.get("catalogue_names", []),
            "codelists": [],
            "nci_preferred_name": data["nci_preferred_name"],
            "definition": data["definition"],
            "sponsor_preferred_name": data["sponsor_preferred_name"],
            "sponsor_preferred_name_sentence_case": data[
                "sponsor_preferred_name_sentence_case"
            ],
            "library_name": data["library_name"],
            "concept_id": None,
        }
        term_name = post_data["sponsor_preferred_name"]
        term_definition = post_data["definition"]
        # Post the new term
        status, result = await self.api.post_to_api_async(
            url="/ct/terms", body=post_data, session=session
        )
        if status == 201:
            self.log.info(
                f"Created new term with name '{term_name}' and definition '{term_definition}'"
            )
            term_uid = result["term_uid"]
        else:
            self.log.error(
                f"Failed to create new term with name '{term_name}' and definition '{term_definition}', skipping"
            )
            return
        time.sleep(0.1)
        # Approve the term name
        status, result = await self.api.approve_async(
            "/ct/terms/" + term_uid + "/names/approvals", session=session
        )
        if status != 201:
            self.log.error(
                f"Failed to approve term name '{term_name}' with uid '{term_uid}'"
            )
            metrics.icrement("/ct/terms--NamesApproveError")
        else:
            self.log.info(f"Approved term name '{term_name}' with uid '{term_uid}'")
            metrics.icrement("/ct/terms--NamesApprove")

        # Approve the term attributes
        status, result = await self.api.approve_async(
            "/ct/terms/" + term_uid + "/attributes/approvals", session=session
        )
        if status != 201:
            self.log.error(
                f"Failed to approve term attributes '{term_name}' with uid '{term_uid}'"
            )
            metrics.icrement("/ct/terms--AttributesApproveError")
        else:
            self.log.info(
                f"Approved term attributes '{term_name}' with uid '{term_uid}'"
            )
            metrics.icrement("/ct/terms--AttributesApprove")
        return term_uid

    async def patch_term_if_required(
        self, existing_data: dict, new_data: dict, session: aiohttp.ClientSession
    ):
        existing_name = existing_data.get("name", {}).get("sponsor_preferred_name")
        new_name = new_data["sponsor_preferred_name"]
        if existing_name == new_name:
            return
        term_uid = existing_data["term_uid"]
        self.log.info(
            f"Sponsor name for term '{term_uid}' changed from '{existing_name}' to "
            f"'{new_name}', creating new version"
        )
        version_status, version_result = await self.api.new_version_to_api_async(
            f"/ct/terms/{term_uid}/names/versions", session
        )
        if not status_ok(version_status):
            error_msg = get_error_message(version_result)
            if (
                "New draft version can be created only for FINAL versions"
                not in error_msg
            ):
                self.log.error(
                    f"Failed to create new version for term '{term_uid}' name: {error_msg}"
                )
                return
            self.log.info(
                f"Term '{term_uid}' name is already in DRAFT, continuing with patch"
            )
        patch_status, patch_result = await self.api.patch_to_api_async(
            f"/ct/terms/{term_uid}/names",
            {
                "sponsor_preferred_name": new_name,
                "sponsor_preferred_name_sentence_case": new_data[
                    "sponsor_preferred_name_sentence_case"
                ],
                "change_description": "Sponsor name updated during term import",
            },
            session,
        )
        if not status_ok(patch_status):
            self.log.error(
                f"Failed to patch name for term '{term_uid}': "
                f"{get_error_message(patch_result)}"
            )
            return
        await asyncio.sleep(0.1)
        approve_status, _ = await self.api.approve_async(
            f"/ct/terms/{term_uid}/names/approvals", session
        )
        if not status_ok(approve_status):
            self.log.error(f"Failed to approve updated name for term '{term_uid}'")
        else:
            self.log.info(f"Updated sponsor name for term '{term_uid}' to '{new_name}'")

    def find_term_in_codelists(self, codelists, term_name=None):
        codelist_uids = [cl["codelist_uid"] for cl in codelists]
        self.log.debug(
            f"Looking up term with name '{term_name}' across codelists {codelist_uids}"
        )
        # Pass 1: exact submission value match via filtered API call.
        for codelist in codelists:
            existing_term = self.api.find_term_by_submission_value(
                codelist["codelist_uid"], codelist["submission_value"]
            )
            if existing_term:
                self.log.debug(
                    f"Found term by exact submission value '{codelist['submission_value']}' "
                    f"in codelist '{codelist['codelist_uid']}', uid '{existing_term.get('term_uid')}'"
                )
                return existing_term

        # Fetch all terms for the target codelists once for the remaining passes.
        terms_by_cl = {}
        for codelist in codelists:
            cl_uid = codelist["codelist_uid"]
            if cl_uid in terms_by_cl:
                continue
            terms_by_cl[cl_uid] = (
                self.api.get_all_from_api(f"/ct/codelists/{cl_uid}/terms") or []
            )

        # Pass 2: case-insensitive submission value match (e.g. UPPERCASE → camelCase).
        for codelist in codelists:
            target = (codelist.get("submission_value") or "").lower()
            if not target:
                self.log.error(
                    f"Codelist '{codelist['codelist_uid']}' has no submission value"
                )
                continue
            for term in terms_by_cl[codelist["codelist_uid"]]:
                if (term.get("submission_value") or "").lower() == target:
                    self.log.debug(
                        f"Found term by case-insensitive submission value '{codelist['submission_value']}' "
                        f"in codelist '{codelist['codelist_uid']}', uid '{term.get('term_uid')}'"
                    )
                    return term

        # Pass 3: sponsor preferred name match.
        if term_name:
            for codelist in codelists:
                for term in terms_by_cl[codelist["codelist_uid"]]:
                    if term.get("name", {}).get("sponsor_preferred_name") == term_name:
                        self.log.debug(
                            f"Found term by sponsor preferred name '{term_name}' "
                            f"in codelist '{codelist['codelist_uid']}', uid '{term.get('term_uid')}'"
                        )
                        return term
        self.log.debug(
            f"No matching term found in codelists {codelist_uids} for name '{term_name}'"
        )
        return None

    def find_term_by_concept_id_list(self, concept_id_list):
        for concept_id in concept_id_list:
            matching_terms = self.api.lookup_terms_from_concept_id(concept_id)
            if len(matching_terms) > 0:
                return matching_terms[0]

    def _find_term_in_codelist_by_uid(self, codelist_uid, term_uid):
        terms = self.api.get_all_from_api(f"/ct/codelists/{codelist_uid}/terms")
        if not terms:
            return None
        for term in terms:
            if term.get("term_uid") == term_uid:
                return term
        return None

    async def process_simple_term_migration(
        self, data: dict, session: aiohttp.ClientSession
    ):
        if data["term"]["concept_id"]:
            # This is a CDISC term, look it up
            cid_list = data["term"]["concept_id"].split("|")
            matching_term = self.find_term_by_concept_id_list(cid_list)
            if matching_term is None:
                self.log.error(
                    f"Could not find term with concept id '{data['term']['concept_id']}', skipping"
                )
                return
            term_uid = matching_term["term_uid"]
            self.log.info(
                f"Found term with uid '{term_uid}' for concept id '{data['term']['concept_id']}'"
            )
        elif (
            data["term"]["existing_cl_submval"]
            and data["term"]["existing_term_submval"]
        ):
            # This is a term that already exists in a codelist, look it up
            existing_cl_uid = self.api.get_codelist_uid(
                data["term"]["existing_cl_submval"]
            )
            if existing_cl_uid is None:
                self.log.error(
                    f"Could not find codelist with submission value '{data['term']['existing_cl_submval']}', skipping"
                )
                return
            existing_term = self.api.find_term_by_submission_value(
                existing_cl_uid,
                data["term"]["existing_term_submval"],
            )
            if existing_term is None:
                self.log.error(
                    f"Could not find term with submission value '{data['term']['existing_term_submval']}' in codelist '{data['term']['existing_cl_submval']}', skipping"
                )
                return
            term_uid = existing_term["term_uid"]
            self.log.info(
                f"Found existing term with uid '{term_uid}' for submission value '{data['term']['existing_term_submval']}'"
            )
        else:
            # This is a sponsor term, find an existing matching sponsor term, or create a new one
            term_name = data["term"]["sponsor_preferred_name"]
            term_definition = data["term"]["definition"]

            # Look in the target codelists first by submission value, then by sponsor name.
            existing_term = self.find_term_in_codelists(data["codelists"], term_name)

            # Check if the term needs updating
            if existing_term:
                await self.patch_term_if_required(existing_term, data["term"], session)
                term_uid = existing_term["term_uid"]
            else:
                # Term is not already in any of the current codelists, look for a matching term by name and definition
                existing_term = self.api.find_sponsor_term_by_name_and_definition(
                    term_name, term_definition
                )
                if existing_term is None:
                    self.log.info(
                        f"Creating new term with name '{term_name}' and definition '{term_definition}'"
                    )
                    term_uid = await self.post_and_approve_term(data["term"], session)
                    if not term_uid:
                        return
                else:
                    term_uid = existing_term["term_uid"]
                    self.log.info(
                        f"Found existing term with name '{term_name}' and definition '{term_definition}', uid '{term_uid}'"
                    )

        # Add the term to the codelist(s)
        for codelist in data["codelists"]:
            codelist_uid = codelist["codelist_uid"]
            self.log.info(
                f"Add term with uid '{term_uid}' to codelist with uid '{codelist_uid}'"
            )
            try:
                order = int(codelist.get("order", 0))
            except ValueError:
                order = None
            status, result = await self.api.post_to_api_async(
                url=f"/ct/codelists/{codelist_uid}/terms",
                body={
                    "term_uid": term_uid,
                    "order": order,
                    "submission_value": codelist["submission_value"],
                },
                session=session,
            )
            if status == 201:
                self.log.info(
                    f"Added term with uid '{term_uid}' to codelist with uid '{codelist_uid}'"
                )
                continue

            # The add failed. If the term is already in this codelist with a different
            # submission value, patch it; otherwise report the original error.
            current = self._find_term_in_codelist_by_uid(codelist_uid, term_uid)
            if current is None:
                self.log.error(
                    f"Failed to add term with uid '{term_uid}' to codelist with uid '{codelist_uid}', error: {result}"
                )
                continue
            current_submval = current.get("submission_value")
            new_submval = codelist["submission_value"]
            if current_submval == new_submval:
                self.log.info(
                    f"Term '{term_uid}' already in codelist '{codelist_uid}' with submission value '{new_submval}', nothing to do"
                )
                continue
            self.log.info(
                f"Term '{term_uid}' already in codelist '{codelist_uid}' with submission value "
                f"'{current_submval}', patching to '{new_submval}'"
            )
            patch_status, patch_result = await self.api.patch_to_api_async(
                f"/ct/terms/{term_uid}/codelists",
                {
                    "codelist_uid": codelist_uid,
                    "order": order,
                    "submission_value": new_submval,
                },
                session,
            )
            if not status_ok(patch_status):
                self.log.error(
                    f"Failed to patch submission value for term '{term_uid}' "
                    f"in codelist '{codelist_uid}': {get_error_message(patch_result)}"
                )

        if "parents" in data:
            for parent in data["parents"]:
                if parent["parent_type"] in ["type", "subtype", "specialization"]:
                    parent_term = await self.api.find_term_by_submission_value_async(
                        parent["parent_codelist_uid"],
                        parent["parent_term_submval"],
                        session,
                    )
                elif parent["parent_type"] == "predecessor":
                    parent_term = await self.api.find_term_by_concept_id_async(
                        parent["parent_concept_id"], session
                    )
                else:
                    self.log.error(
                        f"Unknown relationship type '{parent['parent_type']}'"
                    )
                    parent_term = None

                if not parent_term:
                    self.log.error(
                        f"Could not find parent term for with submission value '{parent.get('parent_term_submval')}', skipping"
                    )
                    continue

                self.log.info(
                    f"Add term '{parent_term['term_uid']}' as parent of type '{parent['parent_type']}' of term '{term_uid}'"
                )
                status, result = await self.api.post_to_api_async(
                    f"/ct/terms/{term_uid}/parents?parent_uid={parent_term['term_uid']}&relationship_type={parent['parent_type']}",
                    {},
                    session,
                )

                if status != 201:
                    self.log.error(
                        "Failed to add term '%s' as parent of type '%s' of term '%s', error: %s",
                        parent_term["term_uid"],
                        parent["parent_type"],
                        term_uid,
                        result,
                    )
                else:
                    self.log.info(
                        "Added term '%s' as parent of type '%s' of term '%s'",
                        parent_term["term_uid"],
                        parent["parent_type"],
                        term_uid,
                    )

    async def update_term_order(
        self,
        codelist_uid: str,
        term_submval: str,
        order: int,
        session: aiohttp.ClientSession,
    ):
        existing_term = self.api.find_term_by_submission_value(
            codelist_uid, term_submval
        )
        if not existing_term:
            self.log.error(
                f"Could not find term with submission value '{term_submval}' in codelist with uid '{codelist_uid}', skipping"
            )
            return
        data = {
            "codelist_uid": codelist_uid,
            "order": order,
            "submission_value": term_submval,
        }
        return await self.api.patch_to_api_async(
            f"ct/terms/{existing_term['term_uid']}/codelists", data, session
        )

    # Retry a function that sporadically fails.
    # After the first failure it will sleep for retry_delay seconds,
    # then double the delay for each subsequent failure.
    def retry_function(
        self,
        function: Callable,
        args: list,
        nbr_retries: int = 3,
        retry_delay: float = 0.5,
    ):
        for n in range(nbr_retries + 1):
            try:
                return function(*args)
            except Exception:
                self.log.warning(
                    f"Function failed, retry {n+1} of {nbr_retries} in {retry_delay} seconds"
                )
                time.sleep(retry_delay)
                retry_delay = 2 * retry_delay

    @lru_cache(maxsize=10000)
    def lookup_concept_uid(
        self, name, endpoint, subset=None, library=None, only_final=False
    ):
        self.log.debug(f"Looking up concept {endpoint} with name '{name}'")
        filt = {"name": {"v": [name], "op": "eq"}}
        if library is not None:
            if isinstance(library, tuple):
                filt["library_name"] = {"v": list(library), "op": "eq"}
            else:
                filt["library_name"] = {"v": [library], "op": "eq"}
        if only_final:
            filt["status"] = {"v": ["Final"], "op": "eq"}
        path = f"/concepts/{endpoint}"
        params = {"filters": json.dumps(filt)}
        if subset:
            params["subset"] = subset
        items = self.api.get_all_from_api(path, params={"filters": json.dumps(filt)})
        if items is not None and len(items) > 0:
            uid = items[0].get("uid", None)
            self.log.debug(
                f"Found concept {endpoint} with name '{name}' and uid '{uid}'"
            )
            return uid
        self.log.warning(f"Could not find concept {endpoint} with name '{name}'")

    @lru_cache(maxsize=10000)
    def lookup_ct_term_uid(
        self, codelist_name, value, key="sponsor_preferred_name", uid_key="term_uid"
    ):
        filt = {key: {"v": [value], "op": "eq"}}
        if codelist_name in CODELIST_NAME_MAP:
            self.log.debug(
                f"Looking up term with '{key}' == '{value}' in codelist '{codelist_name}': {CODELIST_NAME_MAP[codelist_name]}, returning uid from '{uid_key}'"
            )
            params = {
                "codelist_uid": CODELIST_NAME_MAP[codelist_name],
                "page_size": 1,
                "filters": json.dumps(filt),
            }
        else:
            self.log.debug(
                f"Looking up term with '{key}' == '{value}' in codelist '{codelist_name}', returning uid from '{uid_key}'"
            )
            params = {
                "codelist_name": codelist_name,
                "page_size": 1,
                "filters": json.dumps(filt),
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
        self.log.warning(
            f"Could not find term with '{key}' == '{value}' in codelist '{codelist_name}'"
        )

    def lookup_unit_uid(self, name, subset=None):
        uid = self.lookup_concept_uid(name, "unit-definitions", subset=subset)
        if uid is None:
            self.log.debug(
                f"Unit name '{name}' not found, trying again with lowercase '{name.lower()}'"
            )
            uid = self.lookup_concept_uid(
                name.lower(), "unit-definitions", subset=subset
            )
        if uid is None:
            self.log.debug(
                f"Unit name '{name}' not found, trying again with uppercase '{name.upper()}'"
            )
            uid = self.lookup_concept_uid(
                name.upper(), "unit-definitions", subset=subset
            )
        if uid is None:
            self.log.warning(f"Could not find unit with name '{name}'")
        else:
            self.log.debug(f"Looked up unit name '{name}', found uid '{uid}'")
        return uid

    @lru_cache(maxsize=10000)
    def lookup_codelist_term_uid(self, codelist_name, sponsor_preferred_name):
        self.log.debug(
            f"Looking up term with name '{sponsor_preferred_name}' from codelist '{codelist_name}'"
        )
        terms = self.fetch_codelist_terms(codelist_name)
        if terms is not None:
            for term in terms:
                if term["name"]["sponsor_preferred_name"] == sponsor_preferred_name:
                    uid = term["term_uid"]
                    self.log.debug(
                        f"Found term with sponsor preferred name '{sponsor_preferred_name}' and uid '{uid}'"
                    )
                    return uid
        self.log.warning(
            f"Could not find term with sponsor preferred name '{sponsor_preferred_name}'"
        )

    @lru_cache(maxsize=10000)
    def fetch_codelist_terms(self, name):
        if name in CODELIST_NAME_MAP:
            self.log.debug(
                f"Fetching terms for codelist with name '{name}', id {CODELIST_NAME_MAP[name]}"
            )
            params = {"codelist_uid": CODELIST_NAME_MAP[name]}
        else:
            self.log.debug(f"Fetching terms for codelist with name '{name}'")
            params = {"codelist_name": name}
        items = self.api.get_all_from_api("/ct/terms", params=params)
        if items is None:
            items = []
        self.log.debug(f"Got {len(items)} terms from codelist with name '{name}'")
        return items

    @lru_cache(maxsize=10000)
    def get_codelist_uid_from_submval(self, submval):
        params = {
            "filters": json.dumps({"submission_value": {"v": [submval], "op": "eq"}}),
            "page_number": 1,
            "page_size": 0,
        }
        cl_attrs = self.api.get_all_from_api("/ct/codelists/attributes", params=params)
        if len(cl_attrs) == 0:
            self.log.warning(
                f"Unable to find codelist for submission value '{submval}'"
            )
            return
        cl_uid = cl_attrs[0]["codelist_uid"]
        return cl_uid

    @lru_cache(maxsize=10000)
    def fetch_terms_for_codelist_submval(self, submval):
        cl_uid = self.get_codelist_uid_from_submval(submval)
        if cl_uid is None:
            return []
        terms = self.api.get_all_from_api(f"/ct/codelists/{cl_uid}/terms")
        return terms

    def create_or_get_numeric_value(self, value, subset):
        if value is None:
            return None
        data = copy.deepcopy(import_templates.numeric_value_with_unit)
        for key in data.keys():
            if not key.lower().endswith("uid"):
                data[key] = value.get(key, data[key])
        data["unit_definition_uid"] = self.lookup_unit_uid(
            value["unit_label"], subset=subset
        )
        data["library_name"] = "Sponsor"
        for key, val in data.items():
            if val == "string":
                data[key] = None
        val = self.api.simple_post_to_api("/concepts/numeric-values-with-unit", data)
        if val is not None:
            return val.get("uid", None)

    def create_or_get_lag_time(self, value):
        data = copy.deepcopy(import_templates.lag_time)
        for key in data.keys():
            if not key.lower().endswith("uid"):
                data[key] = value.get(key, data[key])
        data["unit_definition_uid"] = self.lookup_unit_uid(
            value["unit_label"], subset=UNIT_SUBSET_AGE
        )
        data["sdtm_domain_uid"] = self.lookup_ct_term_uid(
            CODELIST_SDTM_DOMAIN_ABBREVIATION, value["sdtm_domain_label"]
        )
        data["library_name"] = "Sponsor"
        for key, val in data.items():
            if val == "string":
                data[key] = None
        # print(json.dumps(data, indent=2))
        val = self.api.simple_post_to_api("/concepts/lag-times", data)
        if val is not None:
            return val.get("uid", None)

    @lru_cache(maxsize=10000)
    def lookup_dictionary_uid(self, name):
        self.log.debug(f"Looking up dictionary with name '{name}'")
        items = self.api.get_all_from_api(
            "/dictionaries/codelists", params={"library_name": name}
        )
        if items is not None and len(items) > 0:
            uid = items[0].get("codelist_uid", None)
            self.log.debug(f"Found dictionary with name '{name}' and uid '{uid}'")
            return uid
        self.log.warning(f"Could not find dictionary with name '{name}'")

    @lru_cache(maxsize=10000)
    def lookup_ct_codelist_uid(self, name):
        self.log.debug(f"Looking up ct codelist with name '{name}'")
        filt = {"name": {"v": [name], "op": "eq"}}
        items = self.api.get_all_from_api(
            "/ct/codelists/names", params={"filters": json.dumps(filt)}
        )
        if items is not None and len(items) > 0:
            uid = items[0].get("codelist_uid", None)
            self.log.debug(f"Found ct codelist with name '{name}' and uid '{uid}'")
            return uid
        self.log.warning(f"Could not find ct codelist with name '{name}'")

    @lru_cache(maxsize=10000)
    def fetch_dictionary_terms(self, name):
        uid = self.lookup_dictionary_uid(name)
        self.log.debug(f"Fetching terms for dictionary with name '{name}'")
        items = self.api.get_all_from_api(
            "/dictionaries/terms", params={"codelist_uid": uid}
        )
        if items is None:
            items = []
        self.log.debug(f"Got {len(items)} terms from dictionary with name '{name}'")
        return items

    @lru_cache(maxsize=10000)
    def lookup_dictionary_term_uid(self, dictionary_name, term_name):
        self.log.debug(
            f"Looking up term with name '{term_name}' from dictionary '{dictionary_name}'"
        )
        snomed_uid = self.lookup_dictionary_uid(dictionary_name)
        filt = {"name": {"v": [term_name], "op": "eq"}}
        items = self.api.get_all_from_api(
            "/dictionaries/terms",
            params={"codelist_uid": snomed_uid, "filters": json.dumps(filt)},
        )
        if items is not None and len(items) > 0:
            uid = items[0].get("term_uid", None)
            self.log.debug(f"Found term with name '{term_name}' and uid '{uid}'")
            return uid
        self.log.warning(f"Could not find term with name '{term_name}'")

    @lru_cache(maxsize=10000)
    def lookup_codelist_term_name_from_concept_id(self, codelist_name, concept_id):
        self.log.debug(
            f"Looking up term with concept id '{concept_id}' from codelist '{codelist_name}'"
        )
        terms = self.fetch_codelist_terms(codelist_name)
        if terms is not None:
            for term in terms:
                if term["attributes"]["concept_id"] == concept_id:
                    name = term["name"]["sponsor_preferred_name"]
                    self.log.debug(
                        f"Found term with concept id '{concept_id}' and name '{name}'"
                    )
                    return name
        self.log.warning(
            f"Could not find term with concept id '{concept_id}' in codelist '{codelist_name}'"
        )

    @open_file_async()
    async def import_codelist_terms(self, csvfile, session):
        readCSV = csv.DictReader(csvfile, delimiter=",")
        api_tasks = []
        codelist_uid_by_submval = {}
        parent_codelist_uid = None
        for row in readCSV:
            term_codelists = []
            parents = []
            for codelist_submval in row["CODELIST_SUBMVAL"].split("|"):
                if codelist_submval not in codelist_uid_by_submval:
                    codelist_uid = self.api.get_codelist_uid(codelist_submval)
                else:
                    codelist_uid = codelist_uid_by_submval[codelist_submval]

                if codelist_uid is None:
                    self.log.warning(
                        "Codelist submission value '%s' not found, skipping.",
                        codelist_submval,
                    )
                    self.metrics.icrement(
                        "/ct/codelists/-Names Epoch Type - SkippedASMissingcodelist_uid"
                    )
                    continue

                codelist_uid_by_submval[codelist_submval] = codelist_uid
                term_codelists.append(codelist_uid)

            parent_terms = row.get(
                "PARENT_CODELIST_SUBMVAL__TERM_SUBMVAL__TYPE", ""
            ).strip()
            if parent_terms:
                for parent_term in parent_terms.split("|"):
                    if not parent_term.strip():
                        continue
                    parent_codelist_submval, parent_term_submval, parent_type = (
                        parent_term.split(":")
                    )
                    parent_codelist_submval = parent_codelist_submval.strip()
                    parent_term_submval = parent_term_submval.strip()
                    parent_type = parent_type.strip().lower()

                    parent_codelist_uid = self.api.get_codelist_uid(
                        parent_codelist_submval
                    )
                    parents.append(
                        {
                            "parent_codelist_uid": parent_codelist_uid,
                            "parent_type": parent_type,
                            "parent_term_submval": parent_term_submval,
                        }
                    )

            # Check if this term replaces an existing term
            replaces_concept_id = row.get("REPLACES_CONCEPT_ID")
            if replaces_concept_id:
                parent_type = "predecessor"
                parents.append(
                    {
                        "parent_concept_id": replaces_concept_id,
                        "parent_type": parent_type,
                    }
                )

            if not row.get("CONCEPT_ID") and not row.get("DEFINITION"):
                self.log.error(
                    f"Row does not have a concept id or definition, skipping: {row}"
                )
                continue
            name = row.get("SPONSOR_NAME")
            name_sentence_case = row.get("SPONSOR_NAME_SENTENCE_CASE")
            if not name_sentence_case:
                name_sentence_case = name.lower()

            if row.get("CONCEPT_ID"):
                library_name = "CDISC"
            else:
                library_name = "Sponsor"
            catalogue_names = row.get("CATALOGUE_NAMES")
            if catalogue_names:
                catalogue_names = catalogue_names.split("|")
            else:
                catalogue_names = []

            codelists = [
                {
                    "codelist_uid": codelist_uid,
                    "submission_value": row.get("TERM_SUBMVAL"),
                    "order": row.get("ORDER"),
                }
                for codelist_uid in term_codelists
            ]
            use_existing_cl_term = row.get("USE_EXISTING_CL_TERM", None)
            if use_existing_cl_term:
                existing_cl_submval, existing_term_submval = use_existing_cl_term.split(
                    ":"
                )
            else:
                existing_cl_submval = None
                existing_term_submval = None

            data = {
                "codelists": codelists,
                "parents": parents,
                "term": {
                    "concept_id": row.get("CONCEPT_ID"),
                    "catalogue_names": catalogue_names,
                    "nci_preferred_name": row.get("NCI_NAME", "UNK"),
                    "definition": row.get("DEFINITION"),
                    "sponsor_preferred_name": name,
                    "sponsor_preferred_name_sentence_case": name_sentence_case,
                    "library_name": library_name,
                    "existing_cl_submval": existing_cl_submval,
                    "existing_term_submval": existing_term_submval,
                },
            }

            # TODO check if already exists
            self.log.info(
                f"Adding term with name '{name}' to codelists with uid '{term_codelists}'"
            )
            api_tasks.append(
                self.process_simple_term_migration(data=data, session=session)
            )
        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def import_codelist_term_ordering(self, csvfile, session):
        # self.code_lists_uids = self.api.get_code_lists_uids()
        readCSV = csv.DictReader(csvfile, delimiter=",")
        api_tasks = []
        codelist_uid = None
        codelist_submval = None
        for row in readCSV:
            # Get the codelist uid
            if codelist_uid is None:
                codelist_submval = row["CODELIST_SUBMVAL"]
                codelist_uid = self.api.get_codelist_uid(codelist_submval)
            elif codelist_submval != row["CODELIST_SUBMVAL"]:
                self.log.error("All rows in the file should specify the same codelist")
                continue
            if codelist_uid is None:
                self.log.warning(
                    f"Codelist submission value '{codelist_submval}' not found, skipping."
                )
                self.metrics.icrement("/ct/codelists - SkippedASMissingcodelist_uid")
                continue
            try:
                order = int(row.get("ORDER"))
            except ValueError:
                self.log.error(f"Row does not have a valid order, skipping: {row}")
                continue
            term_submval = row.get("TERM_SUBMVAL")
            self.log.info(
                f"Setting order {order} for term '{term_submval}' in codelist '{codelist_uid}'"
            )

            api_tasks.append(
                self.update_term_order(
                    codelist_uid, term_submval, order, session=session
                )
            )
        await asyncio.gather(*api_tasks)
