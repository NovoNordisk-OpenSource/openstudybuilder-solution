import csv
import json
from collections import defaultdict

from importers.functions.parsers import map_boolean

from .functions.utils import load_env
from .utils.importer import BaseImporter, open_file
from .utils.metrics import Metrics

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
API_BASE_URL = load_env("API_BASE_URL")
MDR_MIGRATION_ODM_VENDOR_NAMESPACES = load_env("MDR_MIGRATION_ODM_VENDOR_NAMESPACES")
MDR_MIGRATION_ODM_VENDOR_ATTRIBUTES = load_env("MDR_MIGRATION_ODM_VENDOR_ATTRIBUTES")
MDR_MIGRATION_ODM_VENDOR_ELEMENTS = load_env("MDR_MIGRATION_ODM_VENDOR_ELEMENTS")
MDR_MIGRATION_ODM_STUDY_EVENTS = load_env("MDR_MIGRATION_ODM_STUDY_EVENTS")
MDR_MIGRATION_ODM_FORMS = load_env("MDR_MIGRATION_ODM_FORMS")
MDR_MIGRATION_ODM_ITEM_GROUPS = load_env("MDR_MIGRATION_ODM_ITEM_GROUPS")
MDR_MIGRATION_ODM_ITEMS = load_env("MDR_MIGRATION_ODM_ITEMS")
MDR_MIGRATION_ODM_FORMS_TO_ODM_STUDY_EVENTS = load_env(
    "MDR_MIGRATION_ODM_FORMS_TO_ODM_STUDY_EVENTS"
)
MDR_MIGRATION_ODM_ITEM_GROUPS_TO_ODM_FORMS = load_env(
    "MDR_MIGRATION_ODM_ITEM_GROUPS_TO_ODM_FORMS"
)
MDR_MIGRATION_ODM_ITEMS_TO_ODM_ITEM_GROUPS = load_env(
    "MDR_MIGRATION_ODM_ITEMS_TO_ODM_ITEM_GROUPS"
)
MDR_MIGRATION_ODM_ITEMS_TO_ACTIVITY_INSTANCES = load_env(
    "MDR_MIGRATION_ODM_ITEMS_TO_ACTIVITY_INSTANCES"
)


# name, prefix, namespace
def odm_vendor_namespace(data):
    return {
        "path": "/odms/vendor-namespaces",
        "body": {
            "name": data["name"],
            "prefix": data["prefix"],
            "url": data["url"],
        },
    }


def odm_vendor_attribute(data):
    return {
        "path": "/odms/vendor-attributes",
        "body": {
            "name": data["name"],
            "compatible_types": (
                data["compatible_types"].split("||")
                if data["vendor_namespace_uid"]
                else []
            ),
            "data_type": data["data_type"],
            "value_regex": data["value_regex"] or None,
            "vendor_namespace_uid": data["vendor_namespace_uid"],
            "vendor_element_uid": data["vendor_element_uid"],
        },
    }


def odm_vendor_element(data, vendor_namespace_uid):
    return {
        "path": "/odms/vendor-elements",
        "body": {
            "name": data["name"],
            "compatible_types": data["compatible_types"].split("||"),
            "vendor_namespace_uid": vendor_namespace_uid,
        },
    }


def odm_study_event(data):
    return {
        "path": "/odms/study-events",
        "body": {
            "name": data["name"],
            "oid": data["oid"],
            "effective_date": data["effective_date"] or None,
            "retired_date": data["retired_date"] or None,
            "description": f"description for {data['name']}",
        },
    }


def odm_form(data):
    return {
        "path": "/odms/forms",
        "body": {
            "name": data["name"],
            "oid": data["oid"],
            "repeating": data["repeating"],
            "translated_texts": data.get("translated_texts", []),
            "aliases": data.get("aliases", []),
        },
    }


def odm_item_group(data, domain_uids):
    return {
        "path": "/odms/item-groups",
        "body": {
            "name": data["name"],
            "oid": data["oid"],
            "repeating": data["repeating"],
            "is_reference_data": data["is_reference_data"],
            "sas_dataset_name": data["sas_dataset_name"],
            "origin": data["origin"],
            "purpose": data["purpose"],
            "locked": "no",
            "comment": data["comment"],
            "translated_texts": data.get("translated_texts", []),
            "aliases": data.get("aliases", []),
            "sdtm_domain_uids": domain_uids,
        },
    }


def odm_item(data, units, terms):
    try:
        length = int(data["length"])
    except ValueError:
        length = None
    try:
        significant_digits = int(data["significant_digits"])
    except ValueError:
        significant_digits = None

    return {
        "path": "/odms/items",
        "body": {
            "name": data["name"],
            "oid": data["oid"],
            "datatype_uid": data["datatype"],
            "prompt": data["prompt"],
            "length": length,
            "significant_digits": significant_digits,
            "sas_field_name": data["sas_field_name"],
            "sds_var_name": data["sds_var_name"],
            "origin": data["origin"],
            "comment": data["comment"],
            "allows_multi_choice": False,
            "translated_texts": data.get("translated_texts", []),
            "aliases": data.get("aliases", []),
            "external_question": data.get("external_question", None),
            "codelist": (
                {
                    "uid": data["codelist"]["uid"],
                    "allows_multi_choice": data["codelist"]["allows_multi_choice"],
                }
                if data["codelist"]
                else None
            ),
            "unit_definitions": units,
            "terms": terms,
        },
    }


def odm_form_to_study_event(uid, data):
    return {
        "path": f"/odms/study-events/{uid}/forms",
        "body": [
            {
                "uid": data["uid"],
                "order_number": data["order_number"],
                "mandatory": data["mandatory"],
                "locked": data["locked"],
                "collection_exception_condition_oid": data[
                    "collection_exception_condition_oid"
                ]
                or None,
            }
        ],
    }


def odm_item_group_to_form(uid, data):
    return {
        "path": f"/odms/forms/{uid}/item-groups",
        "body": [
            {
                "uid": data["uid"],
                "order_number": data["order_number"],
                "mandatory": data["mandatory"],
                "collection_exception_condition_oid": data[
                    "collection_exception_condition_oid"
                ]
                or None,
                "vendor": {"attributes": []},
            }
        ],
    }


def odm_item_to_item_group(uid, data):
    return {
        "path": f"/odms/item-groups/{uid}/items",
        "body": [
            {
                "uid": data["uid"],
                "order_number": data["order_number"],
                "mandatory": data["mandatory"],
                "key_sequence": data["key_sequence"] or None,
                "method_oid": data["method_oid"] or None,
                "imputation_method_oid": data["imputation_method_oid"] or None,
                "role": data["role"] or None,
                "role_codelist_oid": data["role_codelist_oid"] or None,
                "collection_exception_condition_oid": data[
                    "collection_exception_condition_oid"
                ]
                or None,
                "vendor": {"attributes": []},
            }
        ],
    }


def odm_item_to_activity_instance(item):
    return {
        "path": "/odms/items/",
        "body": item,
    }


class Crfs(BaseImporter):
    logging_name = "crfs"

    def __init__(self, api=None, metrics_inst=None):
        super().__init__(api=api, metrics_inst=metrics_inst)

    def _fetch_codelist_terms_and_return_codelist_uid(
        self, codelists, codelist_submval
    ):
        codelist = self.api.get_codelist_uid(codelist_submval)
        if codelist not in codelists:
            new_codelist = {}
            terms = self.api.get_all_from_api(f"/ct/codelists/{codelist}/terms")
            for term in terms:
                new_codelist[term["submission_value"]] = term["term_uid"]
                codelists[codelist] = new_codelist
        return codelist

    def _transform_external_question(
        self, codelists, external_question: str | None, item_oid: str
    ):
        if not external_question:
            return None

        codelist_submval, _, term_submval = external_question.partition("::")
        if not codelist_submval or not term_submval:
            self.log.warning(
                "Malformed external_question '%s' of odm item '%s'; expected 'codelist_submission_value::term_submission_value'",
                external_question,
                item_oid,
            )
            return None

        codelist_uid = self._fetch_codelist_terms_and_return_codelist_uid(
            codelists, codelist_submval
        )
        term_uid = codelists.get(codelist_uid, {}).get(term_submval)
        if term_uid is None:
            self.log.warning(
                "Unable to find external_question '%s' in codelist '%s' of odm item '%s'",
                term_submval,
                codelist_submval,
                item_oid,
            )
            return None

        return {"codelist_uid": codelist_uid, "term_uid": term_uid}

    def _transform_aliases(self, aliases: str | None):
        rs = []

        if not aliases:
            return rs

        for alias in aliases.split("||"):
            _alias = alias.split("::", maxsplit=1)
            if not _alias[0]:
                continue
            context, name = _alias
            rs.append(
                {
                    "name": name,
                    "context": context,
                }
            )

        return rs

    def _transform_translated_texts(self, translated_texts: str | None):
        rs = []

        if not translated_texts:
            return rs

        for translated_text in translated_texts.split("||"):
            _translated_text = translated_text.split("::", maxsplit=2)
            if not _translated_text[0]:
                continue
            text_type, language, text = _translated_text
            rs.append(
                {
                    "text_type": text_type,
                    "language": language,
                    "text": text,
                }
            )

        return rs

    @open_file()
    def handle_odm_vendor_namespaces(self, csvfile):
        csvdata = csv.DictReader(csvfile)
        res = []
        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info("Adding odm vendor namespace '%s'", row["name"])
            data = odm_vendor_namespace(row)

            res.append(self.api.post_to_api(data))
        return res

    @open_file()
    def handle_odm_vendor_attributes(self, csvfile, namespace_uids):
        csvdata = csv.DictReader(csvfile)

        existing_attrs = {
            a["name"]: a["uid"]
            for a in (self.api.get_all_from_api("/odms/vendor-attributes") or [])
        }

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info("Adding odm vendor attribute '%s'", row["name"])

            row["vendor_element_uid"] = None
            row["vendor_namespace_uid"] = None

            if row["element_name"]:
                element_rs = self.api.get_all_from_api(
                    "/odms/vendor-elements",
                    params={
                        "filters": json.dumps(
                            {"name": {"v": [row["element_name"]], "op": "eq"}}
                        ),
                        "page_number": 1,
                        "page_size": 0,
                    },
                )

                if not element_rs:
                    self.log.warning(
                        "Unable to find vendor element '%s', skipping",
                        row["element_name"],
                    )
                    continue

                row["vendor_element_uid"] = element_rs[0]["uid"]

            if not row["vendor_element_uid"]:
                namespace_name = row.get("namespace", "")
                row["vendor_namespace_uid"] = namespace_uids.get(namespace_name)
                if not row["vendor_namespace_uid"]:
                    self.log.warning(
                        "Namespace '%s' not found for attribute '%s', skipping",
                        namespace_name,
                        row["name"],
                    )
                    continue

            existing_uid = existing_attrs.get(row["name"])
            if existing_uid:
                self.log.info("Updating existing vendor attribute '%s'", row["name"])
                self.api.patch_to_api(
                    {
                        "uid": existing_uid,
                        "name": row["name"],
                        "compatible_types": row["compatible_types"].split("||"),
                        "data_type": row["data_type"],
                        "value_regex": row["value_regex"] or None,
                        "change_description": "Updated by import",
                    },
                    "/odms/vendor-attributes",
                )
            else:
                data = odm_vendor_attribute(row)
                self.api.post_to_api(data)

    @open_file()
    def handle_odm_vendor_elements(self, csvfile, namespace_uids):
        csvdata = csv.DictReader(csvfile)

        for row in csvdata:
            if len(row) == 0:
                continue
            ns_uid = namespace_uids.get(row.get("namespace", "OpenStudyBuilder"))
            if not ns_uid:
                self.log.warning(
                    "Namespace '%s' not found for vendor element '%s', skipping",
                    row.get("namespace"),
                    row["name"],
                )
                continue
            self.log.info("Adding odm vendor element '%s'", row["name"])
            data = odm_vendor_element(row, ns_uid)

            self.api.post_to_api(data)

    @open_file()
    def handle_odm_study_events(self, csvfile):
        csvdata = csv.DictReader(csvfile)

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info("Adding odm study event '%s'", row["name"])
            data = odm_study_event(row)

            self.api.post_to_api(data)

    @open_file()
    def handle_odm_forms(self, csvfile):
        csvdata = csv.DictReader(csvfile)

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info("Adding odm form '%s'", row["name"])

            row["aliases"] = self._transform_aliases(row["aliases"])
            row["translated_texts"] = self._transform_translated_texts(
                row["translated_texts"]
            )

            data = odm_form(row)

            self.api.post_to_api(data)

    @open_file()
    def handle_odm_item_groups(self, csvfile):
        csvdata = csv.DictReader(csvfile)
        params = {
            "filters": json.dumps(
                {"name": {"v": ["SDTM Domain Abbreviation"], "op": "eq"}}
            ),
            "page_number": 1,
            "page_size": 0,
        }
        domain_cl_uid = self.api.get_all_from_api(
            "/ct/codelists/attributes", params=params
        )
        if len(domain_cl_uid) == 0:
            self.log.warning("Unable to find codelist for SDTM domain abbreviation")
            return
        cl_uid = domain_cl_uid[0]["codelist_uid"]
        domain_terms = self.api.get_all_from_api(f"/ct/codelists/{cl_uid}/terms")

        all_sdtm_domains = self.api.get_all_identifiers(
            domain_terms,
            identifier="submission_value",
            value="term_uid",
        )

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info("Adding odm item group '%s'", row["name"])

            # Look up sdtm domains
            domains = []
            for domain in row["sdtm_domains"].split("||"):
                if not domain:
                    continue
                domain_uid = all_sdtm_domains.get(domain)
                if domain_uid is not None:
                    domains.append(domain_uid)
                else:
                    self.log.warning("Unable to find domain '%s'", domain)

            row["aliases"] = self._transform_aliases(row["aliases"])
            row["translated_texts"] = self._transform_translated_texts(
                row["translated_texts"]
            )

            data = odm_item_group(row, domains)

            self.api.post_to_api(data)

    @open_file()
    def handle_odm_items(self, csvfile):
        csvdata = csv.DictReader(csvfile)
        codelists = {}

        all_units = self.api.get_all_identifiers(
            self.api.get_all_from_api("/concepts/unit-definitions"),
            identifier="name",
            value="uid",
        )

        codelist_odm_datatype = self._fetch_codelist_terms_and_return_codelist_uid(
            codelists, "CODMDT"
        )

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info("Adding odm item '%s'", row["name"])

            row["external_question"] = self._transform_external_question(
                codelists, row["external_question"], row["oid"]
            )

            row["codelist"] = {}
            term_dicts = []
            codelist_submission_value = row["codelist_submission_value"]
            if codelist_submission_value != "":
                row["codelist"]["uid"] = (
                    self._fetch_codelist_terms_and_return_codelist_uid(
                        codelists, codelist_submission_value
                    )
                )
                row["codelist"]["allows_multi_choice"] = False
                terms = row["terms"]
                if terms != "":
                    for term in terms.split("||"):
                        term = term.strip().split("_")[0]
                        term_uid = codelists.get(row["codelist"]["uid"], {}).get(term)
                        if term_uid is not None:
                            term_dict = {
                                "uid": term_uid,
                                "mandatory": True,
                                "order": len(term_dicts) + 1,
                            }
                            term_dicts.append(term_dict)
                        else:
                            self.log.warning(
                                "Unable to find term '%s' in codelist '%s'",
                                term,
                                row["codelist"]["uid"],
                            )

            units = []
            unit_definitions = row["unit_definitions"]
            if unit_definitions != "":
                for unit in unit_definitions.split("||"):
                    unit_uid = all_units.get(unit)
                    if unit_uid is not None:
                        unit_dict = {"uid": unit_uid, "mandatory": True}
                        units.append(unit_dict)
                    else:
                        self.log.warning("Unable to find unit '%s'", unit)

            row["aliases"] = self._transform_aliases(row["aliases"])
            row["translated_texts"] = self._transform_translated_texts(
                row["translated_texts"]
            )

            row["datatype"] = codelists.get(codelist_odm_datatype, {}).get(
                row["datatype"]
            )

            if row["datatype"] is None:
                self.log.warning(
                    "Unable to find datatype '%s' in codelist '%s'; skipping odm item '%s'",
                    row["datatype"],
                    codelist_odm_datatype,
                    row["oid"],
                )

            data = odm_item(row, units, term_dicts)

            self.api.post_to_api(data)

    @open_file()
    def handle_odm_forms_to_study_events(self, csvfile):
        csvdata = csv.DictReader(csvfile)
        odm_forms = self.api.get_all_from_api("/odms/forms")
        odm_study_events = self.api.get_all_from_api("/odms/study-events")

        all_forms = {}
        for form in odm_forms:
            all_forms[form["oid"]] = form["uid"]

        all_study_events = {}
        for study_event in odm_study_events:
            all_study_events[study_event["oid"]] = study_event["uid"]

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(
                "Adding odm form '%s' to study event '%s'",
                row["form_oid"],
                row["study_event_oid"],
            )

            if row["form_oid"] not in all_forms:
                self.log.warning("form '%s' not found, skipping", row["form_oid"])
                continue
            if row["study_event_oid"] not in all_study_events:
                self.log.warning(
                    "Study Event '%s' not found, skipping", row["study_event_oid"]
                )
                continue

            row["uid"] = all_forms[row["form_oid"]]

            data = odm_form_to_study_event(
                all_study_events[row["study_event_oid"]], row
            )

            self.api.post_to_api(data)

    @open_file()
    def handle_odm_item_groups_to_forms(self, csvfile):
        csvdata = csv.DictReader(csvfile)
        odm_itemgroups = self.api.get_all_from_api("/odms/item-groups")
        odm_forms = self.api.get_all_from_api("/odms/forms")

        all_itemgroups = {}
        for itemgroup in odm_itemgroups:
            all_itemgroups[itemgroup["oid"]] = itemgroup["uid"]

        all_forms = {}
        for form in odm_forms:
            all_forms[form["oid"]] = form["uid"]

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(
                "Adding odm item group '%s' to form '%s'",
                row["item_group_oid"],
                row["form_oid"],
            )

            if row["item_group_oid"] not in all_itemgroups:
                self.log.warning(
                    "Item group '%s' not found, skipping", row["item_group_oid"]
                )
                continue
            if row["form_oid"] not in all_forms:
                self.log.warning("Form '%s' not found, skipping", row["form_oid"])
                continue

            row["uid"] = all_itemgroups[row["item_group_oid"]]

            data = odm_item_group_to_form(all_forms[row["form_oid"]], row)

            self.api.post_to_api(data)

    @open_file()
    def handle_odm_items_to_item_groups(self, csvfile):
        csvdata = csv.DictReader(csvfile)
        odm_items = self.api.get_all_from_api("/odms/items")
        odm_itemgroups = self.api.get_all_from_api("/odms/item-groups")

        all_items = {}
        for item in odm_items:
            all_items[item["oid"]] = item["uid"]

        all_itemgroups = {}
        for itemgroup in odm_itemgroups:
            all_itemgroups[itemgroup["oid"]] = itemgroup["uid"]

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(
                "Adding odm item '%s' to item group '%s'",
                row["item_oid"],
                row["item_group_oid"],
            )

            if row["item_oid"] not in all_items:
                self.log.warning("Item '%s' not found, skipping", row["item_oid"])
                continue
            if row["item_group_oid"] not in all_itemgroups:
                self.log.warning(
                    "Item group '%s' not found, skipping", row["item_group_oid"]
                )
                continue

            row["uid"] = all_items[row["item_oid"]]

            data = odm_item_to_item_group(all_itemgroups[row["item_group_oid"]], row)

            self.api.post_to_api(data)

    @open_file()
    def handle_odm_items_to_activity_instances(self, csvfile):
        csvdata = list(csv.DictReader(csvfile))

        item_oids = {data["item_oid"] for data in csvdata}
        activity_instance_names = {data["activity_instance_name"] for data in csvdata}

        odm_items = self.api.get_all_from_api(
            "/odms/items",
            params={"filters": json.dumps({"oid": {"v": list(item_oids)}})},
        )
        activity_instances = self.api.get_all_from_api(
            "/concepts/activities/activity-instances",
            params={
                "filters": json.dumps({"name": {"v": list(activity_instance_names)}})
            },
        )

        data_grouped_by_item = defaultdict(list)
        for row in csvdata:
            item_oid = row.get("item_oid")
            if item_oid:
                data_grouped_by_item[item_oid].append(row)

        for item_oid, rows in data_grouped_by_item.items():
            if not (
                item := next((oi for oi in odm_items if oi["oid"] == item_oid), None)
            ):
                self.log.warning("ODM Item '%s' not found, skipping", item_oid)
                continue

            activity_instances_to_add = []

            for row in rows:
                if len(row) == 0:
                    continue

                self.log.info(
                    "Connecting ODM Item '%s' to Activity Instance '%s' with Activity Item Class '%s'",
                    item_oid,
                    row["activity_instance_name"],
                    row["activity_item_class_name"],
                )

                if not (
                    activity_instance := next(
                        (
                            ai
                            for ai in activity_instances
                            if ai["name"] == row["activity_instance_name"]
                        ),
                        None,
                    )
                ):
                    self.log.warning(
                        "Activity Instance '%s' not found, skipping",
                        row["activity_instance_name"],
                    )
                    continue

                if not (
                    activity_item_class := next(
                        (
                            ai["activity_item_class"]
                            for ai in activity_instance["activity_items"]
                            if ai["activity_item_class"]["name"]
                            == row["activity_item_class_name"]
                        ),
                        None,
                    )
                ):
                    self.log.warning(
                        "Activity Item Class '%s' not found in Activity Instance '%s', skipping",
                        row["activity_item_class_name"],
                        row["activity_instance_name"],
                    )
                    continue

                activity_instances_to_add.append(
                    {
                        "activity_instance_uid": activity_instance["uid"],
                        "activity_item_class_uid": activity_item_class["uid"],
                        "order": row["order"] if row["order"].isdigit() else 99999,
                        "primary": map_boolean(row["primary"]),
                        "preset_response_value": row["preset_response_value"],
                        "value_condition": row["value_condition"],
                        "value_dependent_map": row["value_dependent_map"],
                    }
                )

            item["codelist"] = (
                {
                    "uid": item["codelist"].get("uid"),
                    "allows_multi_choice": item["codelist"].get(
                        "allows_multi_choice", False
                    ),
                }
                if item["codelist"]
                else None
            )

            for term in item.get("terms", []):
                term["uid"] = term["term_uid"]

            if activity_instances_to_add:
                item["activity_instances"] = activity_instances_to_add

                data = odm_item_to_activity_instance(item)

                self.api.patch_to_api(data["body"], data["path"])

    def run(self):
        self.log.info("Importing CRFs")
        vendor_namespace_res = self.handle_odm_vendor_namespaces(
            MDR_MIGRATION_ODM_VENDOR_NAMESPACES
        )
        if vendor_namespace_res:
            namespace_uids = {
                ns["name"]: ns["uid"] for ns in vendor_namespace_res if ns
            }
            self.handle_odm_vendor_elements(
                MDR_MIGRATION_ODM_VENDOR_ELEMENTS,
                namespace_uids,
            )
            self.handle_odm_vendor_attributes(
                MDR_MIGRATION_ODM_VENDOR_ATTRIBUTES,
                namespace_uids,
            )
        self.handle_odm_study_events(MDR_MIGRATION_ODM_STUDY_EVENTS)
        self.handle_odm_forms(MDR_MIGRATION_ODM_FORMS)
        self.handle_odm_item_groups(MDR_MIGRATION_ODM_ITEM_GROUPS)
        self.handle_odm_items(MDR_MIGRATION_ODM_ITEMS)
        self.handle_odm_forms_to_study_events(
            MDR_MIGRATION_ODM_FORMS_TO_ODM_STUDY_EVENTS
        )
        self.handle_odm_item_groups_to_forms(MDR_MIGRATION_ODM_ITEM_GROUPS_TO_ODM_FORMS)
        self.handle_odm_items_to_item_groups(MDR_MIGRATION_ODM_ITEMS_TO_ODM_ITEM_GROUPS)
        self.handle_odm_items_to_activity_instances(
            MDR_MIGRATION_ODM_ITEMS_TO_ACTIVITY_INSTANCES
        )
        self.log.info("Done importing CRFs")


def main():
    metr = Metrics()
    migrator = Crfs(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
