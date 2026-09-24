"""Convert activity instances and items CSVs into ODM CRF import CSV files.

Converted from make_odm_from_activity_instances.groovy.
"""

import csv
import logging
import os
import sys
from collections import OrderedDict
from pathlib import Path

from importers.functions.utils import load_env

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

CRF_DIR = BASE_DIR / "datafiles" / "libraries" / "concepts" / "crfs"

ODM_FORMS_PATH = CRF_DIR / "odm_forms.csv"
ODM_ITEM_GROUPS_PATH = CRF_DIR / "odm_item_groups.csv"
ODM_ITEMS_PATH = CRF_DIR / "odm_items.csv"
ODM_ITEM_GROUPS_TO_ODM_FORMS_PATH = CRF_DIR / "odm_item_groups_to_odm_forms.csv"
ODM_ITEMS_TO_ODM_ITEM_GROUPS_PATH = CRF_DIR / "odm_items_to_odm_item_groups.csv"
ODM_ITEMS_TO_ACTIVITY_INSTANCES_PATH = CRF_DIR / "odm_items_to_activity_instances.csv"
ODM_STUDY_EVENTS_PATH = CRF_DIR / "odm_study_events.csv"
ODM_FORMS_TO_ODM_STUDY_EVENTS_PATH = CRF_DIR / "odm_forms_to_odm_study_events.csv"

IGNORE_LIST = []

TMP_FOLDER = Path(__file__).resolve().parent.parent / "tmp"
DEBUG_PATH = TMP_FOLDER / "debug_items.txt"

debug_list: list[str] = []


def debug(msg: str = "") -> None:
    debug_list.append(str(msg))


def get_csv(filepath: str) -> list[dict]:
    with open(filepath, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def append_unique(existing, item):
    if item not in existing:
        existing.append(item)


def save_list_of_dict_to_csv(filepath: str, data: list[dict]) -> None:
    if not data:
        logger.info(f"Skipping empty file: {filepath}")
        return
    debug(f"Saving data in file {filepath}")
    existing: list[dict] = []
    if os.path.isfile(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing = list(reader)
    seen: set[tuple] = set()
    combined: list[dict] = []
    for row in existing + data:
        key = tuple(sorted(row.items()))
        if key not in seen:
            seen.add(key)
            combined.append(row)
        else:
            debug(f"  Duplicate entry {key}")
    header = list(combined[0].keys())
    logger.info(
        f"Saving file: {filepath} ({len(existing)} existing + {len(data)} new rows)"
    )
    with open(filepath, "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(combined)


def parse_terms_info(value: str):
    """Parse 'codelist:term1|term2' into (codelist, [terms])."""
    parts = value.split(":", 1)
    if len(parts) == 2:
        codelist = parts[0]
        terms = parts[1].split("|")
        return codelist, terms
    return "", []


# ---------------------------------------------------------------------------
# Step 1: Reformat items
# ---------------------------------------------------------------------------


def reformat(instances_file: str, items_file: str) -> dict:
    instances_raw = get_csv(instances_file)
    items_raw = get_csv(items_file)

    all_items: dict[str, list[dict]] = {}
    for item in items_raw:
        key = item["ACTIVITY_INSTANCE_NAME"]
        all_items.setdefault(key, []).append(item)

    instances: dict[str, dict] = OrderedDict()
    for row in instances_raw:
        items = all_items.get(row["activity_instance"])
        if not items:
            debug(f"instance does not have items: {row['activity_instance']}")
            continue
        instance = {
            "name": row["activity_instance"],
            "group": row["Assm. group"],
            "class": row["sub_domain_class"],
            "standard_unit": "",
        }
        properties: dict[str, dict] = {}

        for item in items:
            codelist, terms = "", []
            if item["ACTIVITY_ITEM_TYPE"] == "terms":
                codelist, terms = parse_terms_info(item["ACTIVITY_ITEM_VALUE"])

            class_name = item["ACTIVITY_ITEM_CLASS_NAME"]

            if class_name == "numeric_finding_original_result":
                properties.setdefault("result", {})
                properties["result"]["datatype"] = "INTEGER"
                properties["result"]["item_class"] = class_name

            elif class_name == "numeric_finding_original_result_unit":
                if codelist and terms:
                    properties.setdefault("result", {})
                    properties["result"]["unit"] = {
                        "codelist": codelist,
                        "terms": terms,
                    }

            elif class_name == "categoric_finding_original_result":
                properties.setdefault("result", {})
                properties["result"]["datatype"] = "string"
                properties["result"]["item_class"] = class_name
                if codelist and terms:
                    properties.setdefault("result", {})
                    properties["result"]["unit"] = {
                        "codelist": codelist,
                        "terms": terms,
                    }

            elif class_name == "textual_finding_original_result":
                properties.setdefault("result", {})
                properties["result"]["datatype"] = "string"
                properties["result"]["item_class"] = class_name
                if codelist and terms:
                    properties.setdefault("result", {})
                    properties["result"]["unit"] = {
                        "codelist": codelist,
                        "terms": terms,
                    }

            elif class_name == "domain":
                properties.setdefault("sdtm", {})
                properties["sdtm"]["item_class"] = class_name
                if codelist and terms:
                    properties["sdtm"]["domain"] = {
                        "codelist": codelist,
                        "terms": terms,
                    }

            elif class_name == "test_code":
                properties.setdefault("sdtm", {})
                if codelist and terms:
                    properties["sdtm"]["test_code"] = {
                        "codelist": codelist,
                        "terms": terms,
                    }

            elif class_name == "test_name":
                properties.setdefault("sdtm", {})
                if codelist and terms:
                    properties["sdtm"]["test_name"] = {
                        "codelist": codelist,
                        "terms": terms,
                    }

            elif class_name == "unit_dimension":
                properties[class_name] = {"codelist": codelist, "terms": terms}

            elif class_name == "standard_unit":
                instance["standard_unit"] = item["ACTIVITY_ITEM_VALUE"]

            elif class_name == "fasting_status":
                properties[class_name] = {"collect": "yes", "item_class": class_name}

            elif codelist and terms:
                properties.setdefault(class_name, {})
                properties[class_name]["datatype"] = "string"
                properties[class_name]["terms"] = {"codelist": codelist, "terms": terms}
                properties[class_name]["item_class"] = class_name

            elif class_name == "specimen":
                properties.setdefault(class_name, {})
                properties[class_name]["collect"] = "yes"
                properties[class_name]["item_class"] = class_name
                properties[class_name]["datatype"] = "string"

            elif class_name in IGNORE_LIST:
                pass

            else:
                if "info" in instance:
                    instance["info"] = (
                        instance["info"]
                        + f", {item["ACTIVITY_ITEM_CLASS_NAME"]} {item["ACTIVITY_ITEM_TYPE"]} {item["ACTIVITY_ITEM_VALUE"]}"
                    )
                else:
                    instance["info"] = (
                        f"Unused activity items: {item["ACTIVITY_ITEM_CLASS_NAME"]} {item["ACTIVITY_ITEM_TYPE"]} {item["ACTIVITY_ITEM_VALUE"]}"
                    )
                debug(
                    f"reformat - Ignoring: {item['ACTIVITY_INSTANCE_NAME']}\t"
                    f"{class_name}\t{item['ACTIVITY_ITEM_TYPE']}"
                )

        instance["properties"] = properties
        instances[row["activity_instance"]] = instance

    return instances


# ---------------------------------------------------------------------------
# ODM structure builders
# ---------------------------------------------------------------------------

forms: list[dict] = []
item_groups: list[dict] = []
odm_items: list[dict] = []

odm_item_groups_to_odm_forms: list[dict] = []
odm_items_to_odm_item_groups: list[dict] = []
odm_items_to_activity_instances: list[dict] = []
odm_study_events: list[dict] = []
odm_forms_to_odm_study_events: list[dict] = []


def add_form(form_name: str) -> dict:
    for form in forms:
        if form["name"] == form_name:
            return form
    form = {
        "oid": "ImportedInstance_F_" + form_name.replace(" ", "_"),
        "name": form_name,
        "repeating": "No",
        "sdtm_version": "",
        "translated_texts": "Description::en::This form is generated from an Activity Instance",
        "aliases": "a::Form aliases",
    }
    forms.append(form)
    debug(f"  Adding form: {form}")
    return form


def add_group(instance_name: str, domains: str) -> dict:
    for group in item_groups:
        if group["name"] == instance_name:
            return group
    oid = str(len(item_groups) + 1)
    group = {
        "oid": "ImportedInstance_G_" + oid,
        "name": instance_name,
        "repeating": "No",
        "is_reference_data": "No",
        "sas_dataset_name": "",
        "origin": "Collected Value",
        "purpose": "Tabulation",
        "comment": "",
        "sdtm_domains": domains,
        "translated_texts": "",
        "aliases": "a::Group aliases",
    }
    item_groups.append(group)
    debug(f"  Adding group: {group}")
    return group


ODM_ITEM_TEMPLATE = {
    "oid": "",
    "name": "",
    "prompt": "",
    "datatype": "",
    "length": "",
    "significant_digits": "",
    "sas_field_name": "",
    "sds_var_name": "",
    "origin": "Collected Value",
    "comment": "",
    "unit_definitions": "",
    "codelist_submission_value": "",
    "terms": "",
    "translated_texts": "",
    "aliases": "",
}


def make_odm_item_row(
    name: str,
    k: str,
    prop: dict,
    domains: str,
    sdtm_annotation: str,
    standard_unit: str,
) -> dict | None:
    oid = str(len(odm_items) + 1)
    odm_item = dict(ODM_ITEM_TEMPLATE)

    if k == "result":
        odm_item["oid"] = "ImportedInstance_Item_" + oid
        odm_item["name"] = name
        odm_item["prompt"] = name
        odm_item["datatype"] = prop.get("datatype", "")
        odm_item["sds_var_name"] = sdtm_annotation
        if "unit" in prop:
            odm_item["unit_definitions"] = "||".join(prop["unit"]["terms"])
            odm_item["sds_var_name"] = odm_item["sds_var_name"].replace(
                "ORRES", "ORRES/ORRESU"
            )
        # Using standard_unit if no units attached to result unit
        elif standard_unit:
            odm_item["unit_definitions"] = f"{standard_unit}"
        odm_item["length"] = 3 if prop.get("datatype") == "INTEGER" else 20

    # elif k == "location":
    elif k in ["location", "laterality", "position", "specimen"]:
        odm_item["oid"] = "ImportedInstance_Item_" + oid
        odm_item["name"] = k
        odm_item["prompt"] = k
        odm_item["datatype"] = prop.get("datatype", "")
        if "terms" in prop:
            odm_item["codelist_submission_value"] = prop["terms"]["codelist"]
            odm_item["terms"] = "||".join(prop["terms"]["terms"])
            odm_item["sds_var_name"] = (
                f"{domains}:{domains}{odm_item["codelist_submission_value"]}"
            )
        odm_item["length"] = 8 if prop.get("datatype") == "INTEGER" else 20

    else:
        debug(f"make_odm_item - Ignoring: {k}")
        debug(
            f"  name:{name} k:{k} prop:{prop} domains:{domains} sdtm_annotation:{sdtm_annotation} "
        )
        return None

    return odm_item if odm_item["oid"] else None


def convert_activities(instances: dict) -> None:
    for i, (name, instance) in enumerate(instances.items(), start=1):
        try:
            domains = "||".join(instance["properties"]["sdtm"]["domain"]["terms"])
            codelist = instance["properties"]["sdtm"]["test_code"]["codelist"]
            test_code = instance["properties"]["sdtm"]["test_code"]["terms"]
            debug(f"instance['properties']['sdtm']: {instance['properties']['sdtm']}")
            debug(f"codelist: {codelist}")
            debug(f"test_code: {test_code}")
            sdtm_annotation = (
                f"{domains}:{domains}ORRES where {domains}TESTCD={test_code}"
            )
        except KeyError:
            domains = ""
            codelist = ""
            test_code = ""
            sdtm_annotation = ""

        # TODO: Not sure what to do with this
        try:
            finding_category = f"{instance['properties']['finding_category']['terms']['codelist']}:{",".join(instance['properties']['finding_category']['terms']['terms'])}"
            debug(f"finding_category: {finding_category}")
        except KeyError:
            finding_category = ""

        for j, (k, prop) in enumerate(instance["properties"].items(), start=1):
            odm_item = make_odm_item_row(
                name, k, prop, domains, sdtm_annotation, instance["standard_unit"]
            )
            if not odm_item:
                continue
            if k == "result":
                order_number = 1
            else:
                order_number = 2

            odm_item["comment"] = finding_category

            debug(f"  creating odm_item {odm_item}")
            odm_items.append(odm_item)

            form = add_form(instance["group"])

            group = add_group(instance["name"], domains)
            if "info" in instance:
                group["translated_texts"] = (
                    f"Description::en::Not all activity items included, see design notes||osb:DesignNotes::en::{instance["info"]}"
                )

            # Only need to add once per group
            append_unique(
                odm_item_groups_to_odm_forms,
                {
                    "item_group_oid": group["oid"],
                    "form_oid": form["oid"],
                    "order_number": i,
                    "mandatory": "Yes",
                    "collection_exception_condition_oid": "",
                },
            )

            odm_items_to_odm_item_groups.append(
                {
                    "item_oid": odm_item["oid"],
                    "item_group_oid": group["oid"],
                    "order_number": order_number,
                    "mandatory": "No",
                    "key_sequence": "",
                    "method_oid": "",
                    "imputation_method_oid": "",
                    "role": "",
                    "role_codelist_oid": "",
                    "collection_exception_condition_oid": "",
                }
            )

            odm_items_to_activity_instances.append(
                {
                    "item_oid": odm_item["oid"],
                    "activity_instance_name": instance["name"],
                    "activity_item_class_name": prop.get("item_class", ""),
                    "order": j,
                    "primary": "No",
                    "preset_response_value": "",
                    "value_condition": "",
                    "value_dependent_map": "",
                }
            )

        for form in forms:
            append_unique(
                odm_forms_to_odm_study_events,
                {
                    "form_oid": form["oid"],
                    "study_event_oid": "imported_activity_instances",
                    "order_number": 1,
                    "mandatory": "No",
                    "locked": "No",
                    "collection_exception_condition_oid": "",
                },
            )

    odm_study_events.append(
        {
            "oid": "imported_activity_instances",
            "name": "Activity Instance import",
            "effective_date": "",
            "retired_date": "",
            "description": "",
            "display_in_tree": "True",
        }
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    try:
        mdr_migration_activity_instances = load_env("MDR_MIGRATION_ACTIVITY_INSTANCES")
        mdr_migration_activity_instance_activity_items = load_env(
            "MDR_MIGRATION_ACTIVITY_INSTANCE_ACTIVITY_ITEMS"
        )
        debug("Step 1: Reformat activity instances")
        logger.info("Step 1: Reformat activity instances")
        instances = reformat(
            mdr_migration_activity_instances,
            mdr_migration_activity_instance_activity_items,
        )
        debug("\nStep 2: Create OSB ODM content")
        logger.info("Step 2: Create OSB ODM content")
        convert_activities(instances)

        save_list_of_dict_to_csv(str(ODM_ITEMS_PATH), odm_items)
        save_list_of_dict_to_csv(str(ODM_FORMS_PATH), forms)
        save_list_of_dict_to_csv(str(ODM_ITEM_GROUPS_PATH), item_groups)
        save_list_of_dict_to_csv(
            str(ODM_ITEM_GROUPS_TO_ODM_FORMS_PATH), odm_item_groups_to_odm_forms
        )
        save_list_of_dict_to_csv(
            str(ODM_ITEMS_TO_ODM_ITEM_GROUPS_PATH), odm_items_to_odm_item_groups
        )
        save_list_of_dict_to_csv(
            str(ODM_ITEMS_TO_ACTIVITY_INSTANCES_PATH), odm_items_to_activity_instances
        )
        save_list_of_dict_to_csv(str(ODM_STUDY_EVENTS_PATH), odm_study_events)
        save_list_of_dict_to_csv(
            str(ODM_FORMS_TO_ODM_STUDY_EVENTS_PATH), odm_forms_to_odm_study_events
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

    # Write debug items to tmp file
    TMP_FOLDER.mkdir(parents=True, exist_ok=True)
    with open(DEBUG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(debug_list) + "\n")
    logger.info(f"debug items written to {DEBUG_PATH}")

    logger.info("done")


if __name__ == "__main__":
    main()
