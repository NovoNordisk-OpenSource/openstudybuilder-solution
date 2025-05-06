import csv

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
MDR_MIGRATION_ODM_TEMPLATES = load_env("MDR_MIGRATION_ODM_TEMPLATES")
MDR_MIGRATION_ODM_FORMS = load_env("MDR_MIGRATION_ODM_FORMS")
MDR_MIGRATION_ODM_ITEMGROUPS = load_env("MDR_MIGRATION_ODM_ITEMGROUPS")
MDR_MIGRATION_ODM_ITEMS = load_env("MDR_MIGRATION_ODM_ITEMS")
MDR_MIGRATION_ODM_ALIAS = load_env("MDR_MIGRATION_ODM_ALIAS")
MDR_MIGRATION_ODM_TEMPLATE_TO_FORM_RELATIONSHIP = load_env(
    "MDR_MIGRATION_ODM_TEMPLATE_TO_FORM_RELATIONSHIP"
)
MDR_MIGRATION_ODM_FORM_TO_ITEMGROUP_RELATIONSHIP = load_env(
    "MDR_MIGRATION_ODM_FORM_TO_ITEMGROUP_RELATIONSHIP"
)
MDR_MIGRATION_ODM_ITEMGROUP_TO_ITEM_RELATIONSHIP = load_env(
    "MDR_MIGRATION_ODM_ITEMGROUP_TO_ITEM_RELATIONSHIP"
)


# name, prefix, namespace
def odm_vendor_namespace(data):
    return {
        "path": "/concepts/odms/vendor-namespaces",
        "body": {
            "name": data["name"],
            "prefix": data["prefix"],
            "url": data["url"],
        },
    }


# name, data_type, value_regex
def odm_vendor_attribute(data, vendor_namespace_uid):
    return {
        "path": "/concepts/odms/vendor-attributes",
        "body": {
            "name": data["name"],
            "compatible_types": data["compatible_types"].split("|"),
            "data_type": data["data_type"],
            "value_regex": data["value_regex"],
            "vendor_namespace_uid": vendor_namespace_uid,
        },
    }


# library,oid,name,effectivedate,retireddate
def odm_template(data):
    return {
        "path": "/concepts/odms/study-events",
        "body": {
            "name": data["name"],
            "library_name": data["library"],
            "oid": data["oid"],
            "effective_date": data["effectivedate"],
            "retired_date": data["retireddate"],
            "description": f"description for {data['name']}",
        },
    }


# library,uid,context,name
def odm_alias(data):
    return {
        "path": "/concepts/odms/aliases",
        "body": {
            "name": data["name"],
            "library_name": data["library"],
            "context": data["context"],
        },
    }


# library,oid,name,prompt,repeating,language,description,instruction
def odm_form(data, alias_uids):
    return {
        "path": "/concepts/odms/forms",
        "body": {
            "name": data["name"],
            "library_name": data["library"],
            "oid": data["oid"],
            "repeating": "yes" if data["repeating"].lower() == "true" else "no",
            "descriptions": [
                {
                    "name": data["name"],
                    "library_name": data["library"],
                    "language": data["language"],
                    "description": data["description"] or None,
                    "instruction": data["instruction"] or None,
                    "sponsor_instruction": None,
                }
            ],
            "alias_uids": alias_uids,
        },
    }


# library,oid,name,prompt,repeating,isreferencedata,sasdatasetname,domain,origin,purpose,comment,language,description,instruction
def odm_itemgroup(data, alias_uids, domain_uids):
    return {
        "path": "/concepts/odms/item-groups",
        "body": {
            "name": data["name"],
            "library_name": data["library"],
            "oid": data["oid"],
            "repeating": "yes" if data["repeating"].lower() == "true" else "no",
            "is_reference_data": (
                "yes" if data["isreferencedata"].lower() == "true" else "no"
            ),
            "sas_dataset_name": data["sasdatasetname"],
            "origin": data["origin"],
            "purpose": data["purpose"],
            "locked": "no",
            "comment": data["comment"],
            "descriptions": [
                {
                    "name": data["name"],
                    "library_name": data["library"],
                    "language": data["language"],
                    "description": data["description"] or None,
                    "instruction": data["instruction"] or None,
                    "sponsor_instruction": None,
                },
            ],
            "alias_uids": alias_uids,
            "sdtm_domain_uids": domain_uids,
        },
    }


# library,oid,name,prompt,datatype,length,significantdigits,codelist,term,unit,sasfieldname,sdsvarname,origin,comment,language,description,instruction
def odm_item(data, alias_uids, units, terms):
    return {
        "path": "/concepts/odms/items",
        "body": {
            "name": data["name"],
            "library_name": data["library"],
            "oid": data["oid"],
            "datatype": data["datatype"],
            "prompt": data["prompt"],
            "length": int(data["length"]),
            "significant_digits": int(data["significantdigits"]),
            "sas_field_name": data["sasfieldname"],
            "sds_var_name": data["sdsvarname"],
            "origin": data["origin"],
            "comment": data["comment"],
            "allows_multi_choice": False,
            "descriptions": [
                {
                    "name": data["name"],
                    "library_name": data["library"],
                    "language": data["language"],
                    "description": data["description"] or None,
                    "instruction": data["instruction"] or None,
                    "sponsor_instruction": None,
                },
            ],
            "alias_uids": alias_uids,
            "codelist_uid": data["codelist"] if data["codelist"] != "" else None,
            "unit_definitions": units,
            "terms": terms,
        },
    }


def odm_template_to_form_relationship(uid, data):
    return {
        "path": f"/concepts/odms/study-events/{uid}/forms",
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


def odm_form_to_itemgroup_relationship(uid, data):
    return {
        "path": f"/concepts/odms/forms/{uid}/item-groups",
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


def odm_itemgroup_to_item_relationship(uid, data):
    return {
        "path": f"/concepts/odms/item-groups/{uid}/items",
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


class Crfs(BaseImporter):
    logging_name = "crfs"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)

    def _fetch_codelist_terms(self, codelists, codelist):
        if codelist not in codelists:
            new_codelist = {}
            terms = self.api.get_all_from_api(
                f"/ct/terms/attributes?codelist_uid={codelist}"
            )
            for term in terms:
                new_codelist[term["concept_id"]] = term["term_uid"]
                codelists[codelist] = new_codelist

    @open_file()
    def handle_odm_vendor_namespaces(self, csvfile):
        csvdata = csv.DictReader(csvfile)
        res = []
        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(f'Adding odm vendor namespace {row["name"]}')
            data = odm_vendor_namespace(row)

            # Create vendor namespace, and leave in draft state (no approve)
            # TODO check if it exists before posting?
            res.append(self.api.post_to_api(data))
        return res

    @open_file()
    def handle_odm_vendor_attributes(self, csvfile, vendor_namespace_uid):
        csvdata = csv.DictReader(csvfile)

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(f'Adding odm vendor attribute {row["name"]}')
            data = odm_vendor_attribute(row, vendor_namespace_uid)

            # Create vendor attribute, and leave in draft state (no approve)
            # TODO check if it exists before posting?
            res = self.api.post_to_api(data)

    @open_file()
    def handle_odm_templates(self, csvfile):
        csvdata = csv.DictReader(csvfile)

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(f'Adding odm template {row["name"]}')
            data = odm_template(row)

            # Create template, and leave in draft state (no approve)
            # TODO check if it exists before posting?
            res = self.api.post_to_api(data)

    @open_file()
    def handle_odm_forms(self, csvfile):
        csvdata = csv.DictReader(csvfile)

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(f'Adding odm form {row["name"]}')
            data = odm_form(row, [])

            # Create template, and leave in draft state (no approve)
            # TODO check if it exists before posting?
            self.api.post_to_api(data)

    @open_file()
    def handle_odm_itemgroups(self, csvfile):
        csvdata = csv.DictReader(csvfile)
        domain_list = self.api.get_all_from_api(
            "/ct/terms?codelist_name=SDTM Domain Abbreviation"
        )
        all_sdtm_domains = {}
        for item in domain_list:
            all_sdtm_domains[item["attributes"]["code_submission_value"]] = item[
                "term_uid"
            ]

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(f"Adding odm item group '{row['name']}'")

            # Look up sdtm domains
            domains = []
            for raw_domain in row["domain"].split("|"):
                if not raw_domain:
                    continue
                if "_" in raw_domain:
                    domain = raw_domain.split("_")[1]
                else:
                    domain = raw_domain
                domain_uid = all_sdtm_domains.get(domain)
                if domain_uid is not None:
                    domains.append(domain_uid)
                else:
                    self.log.warning(f"Unable to find domain '{raw_domain}'")

            data = odm_itemgroup(row, [], domains)

            # Create template, and leave in draft state (no approve)
            # TODO check if it exists before posting?
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

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(f'Adding odm item {row["name"]}')

            codelist = row["codelist"]
            term_dicts = []
            if codelist != "":
                self._fetch_codelist_terms(codelists, codelist)
                terms = row["term"]
                if terms != "":
                    for term in terms.split("|"):
                        term = term.strip().split("_")[0]
                        term_uid = codelists.get(codelist, {}).get(term)
                        if term_uid is not None:
                            term_dict = {
                                "uid": term_uid,
                                "mandatory": True,
                                "order": len(term_dicts) + 1,
                            }
                            term_dicts.append(term_dict)
                        else:
                            self.log.warning(
                                f"Unable to find term {term} in codelist {codelist}"
                            )

            units = []
            unit = row["unit"]
            if unit != "":
                unit_uid = all_units.get(unit)
                if unit_uid is not None:
                    unit_dict = {"uid": unit_uid, "mandatory": True}
                    units.append(unit_dict)
                else:
                    self.log.warning(f"Unable to find unit {unit}")

            data = odm_item(row, [], units, term_dicts)

            # Create template, and leave in draft state (no approve)
            # TODO check if it exists before posting?
            self.api.post_to_api(data)

    @open_file()
    def handle_odm_aliases(self, csvfile):
        csvdata = csv.DictReader(csvfile)

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(f'Adding odm alias {row["name"]}')
            data = odm_alias(row)

            # Create alias, and leave in draft state (no approve)
            # TODO check if it exists before posting?
            res = self.api.post_to_api(data)

    @open_file()
    def handle_odm_template_to_form_relationship(self, csvfile):
        csvdata = csv.DictReader(csvfile)
        odm_forms = self.api.get_all_from_api("/concepts/odms/forms")
        odm_templates = self.api.get_all_from_api("/concepts/odms/study-events")

        all_forms = {}
        for form in odm_forms:
            all_forms[form["oid"]] = form["uid"]

        all_templates = {}
        for template in odm_templates:
            all_templates[template["oid"]] = template["uid"]

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(
                f"Adding odm form '{row['oid_form']}' to template '{row['oid_template']}'"
            )

            if row["oid_form"] not in all_forms:
                self.log.warning(f"form '{row['oid_form']}' not found, skipping")
                continue
            if row["oid_template"] not in all_templates:
                self.log.warning(
                    f"Template '{row['oid_template']}' not found, skipping"
                )
                continue

            row["uid"] = all_forms[row["oid_form"]]

            data = odm_template_to_form_relationship(
                all_templates[row["oid_template"]], row
            )

            self.api.post_to_api(data)

    @open_file()
    def handle_odm_form_to_itemgroup_relationship(self, csvfile):
        csvdata = csv.DictReader(csvfile)
        odm_itemgroups = self.api.get_all_from_api("/concepts/odms/item-groups")
        odm_forms = self.api.get_all_from_api("/concepts/odms/forms")

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
                f"Adding odm item group '{row['oid_itemgroup']}' to form '{row['oid_form']}'"
            )

            if row["oid_itemgroup"] not in all_itemgroups:
                self.log.warning(
                    f"Item group '{row['oid_itemgroup']}' not found, skipping"
                )
                continue
            if row["oid_form"] not in all_forms:
                self.log.warning(f"Form '{row['oid_form']}' not found, skipping")
                continue

            row["uid"] = all_itemgroups[row["oid_itemgroup"]]

            data = odm_form_to_itemgroup_relationship(all_forms[row["oid_form"]], row)

            self.api.post_to_api(data)

    @open_file()
    def handle_odm_itemgroup_to_item_relationship(self, csvfile):
        csvdata = csv.DictReader(csvfile)
        odm_items = self.api.get_all_from_api("/concepts/odms/items")
        odm_itemgroups = self.api.get_all_from_api("/concepts/odms/item-groups")

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
                f"Adding odm item '{row['oid_item']}' to item group '{row['oid_itemgroup']}'"
            )

            if row["oid_item"] not in all_items:
                self.log.warning(f"Item '{row['oid_item']}' not found, skipping")
                continue
            if row["oid_itemgroup"] not in all_itemgroups:
                self.log.warning(
                    f"Item group '{row['oid_itemgroup']}' not found, skipping"
                )
                continue

            row["uid"] = all_items[row["oid_item"]]

            data = odm_itemgroup_to_item_relationship(
                all_itemgroups[row["oid_itemgroup"]], row
            )

            self.api.post_to_api(data)

    def run(self):
        self.log.info("Importing CRFs")
        vendor_namespace_res = self.handle_odm_vendor_namespaces(
            MDR_MIGRATION_ODM_VENDOR_NAMESPACES
        )
        if vendor_namespace_res:
            self.handle_odm_vendor_attributes(
                MDR_MIGRATION_ODM_VENDOR_ATTRIBUTES,
                (
                    vendor_namespace_res[0]
                    and vendor_namespace_res[0]["uid"]
                    or "OdmVendorNamespace_000001"
                ),
            )
        self.handle_odm_templates(MDR_MIGRATION_ODM_TEMPLATES)
        self.handle_odm_forms(MDR_MIGRATION_ODM_FORMS)
        self.handle_odm_itemgroups(MDR_MIGRATION_ODM_ITEMGROUPS)
        self.handle_odm_items(MDR_MIGRATION_ODM_ITEMS)
        self.handle_odm_aliases(MDR_MIGRATION_ODM_ALIAS)
        self.handle_odm_template_to_form_relationship(
            MDR_MIGRATION_ODM_TEMPLATE_TO_FORM_RELATIONSHIP
        )
        self.handle_odm_form_to_itemgroup_relationship(
            MDR_MIGRATION_ODM_FORM_TO_ITEMGROUP_RELATIONSHIP
        )
        self.handle_odm_itemgroup_to_item_relationship(
            MDR_MIGRATION_ODM_ITEMGROUP_TO_ITEM_RELATIONSHIP
        )
        self.log.info("Done importing CRFs")


def main():
    metr = Metrics()
    migrator = Crfs(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
