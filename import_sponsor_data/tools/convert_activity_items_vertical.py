#
# Related to: ENABLER 3536678
#
# Converts the activity items in the horizontal instance_activities.csv files to activity_instances_items.csv
#
# NOTE: This script also exists in repo: migration-data
#

import csv
import json
import os
from collections import defaultdict
from pathlib import Path

import pandas as pd

# Unknown: DRUG ACCOU(ntability?)
MMA_SUB_DOMAIN_TO_ACTIVITY_INSTANCE_CLASS = {
    "CATEGORIC FINDINGS": "CategoricFindings",
    "NUMERIC FINDINGS": "NumericFindings",
    "TEXTUAL FINDINGS": "TextualFindings",
    "ADVERSE EVENT": "Events",
    "DISPOSITION": "Events",
    "HYPO": "Events",
    "MEDICAL HISTORY": "Events",
    "PERIODIC": "Events",
    "COMPOUND DOSING": "Interventions",
    "CONCOMITANT MEDICATION": "Interventions",
    "OTHER INTERVENTIONS": "Interventions",
    "SURGERY": "Interventions",
}


def save_to_file(data, path, name):
    try:
        transposed_activities_file = os.path.join(path, name)
        with open(
            transposed_activities_file, mode="w", newline="", encoding="utf-8"
        ) as csvfile:
            fieldnames = data[0].keys()  # header
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        print("Activity instance items saved in folder:", path, "name:", name)

    except Exception as error:
        print("Error", error)


# -------
# NOTE: 2026-03-04 Columns not to be used
# si_unit
# us_conv_unit
# NOTE: 2026-03-04 Standards team considering skipping "Assm. Group" and "Assm. subgroup"
# NOTE: 2026-03-04 "Assm. group" and "Assm. subgroup" are relationships, not properties


# Don't add duplicate items. E.g. activity grouping is not important when updating an activity instance
def add_item(items, item):
    if not item in items:
        items.append(item)


def create_activity_instance_items(path, name, activity_instance_items_vertical_name):
    print("\nReading:", path, "name:", name)

    file_path = os.path.join(path, name)
    file_data = []
    with open(file_path) as csvfile:
        readCSV = csv.DictReader(csvfile, delimiter=",")
        cols = readCSV.fieldnames
        for row in readCSV:
            file_data.append(row)

    print("Existing rows in horizontal file", len(file_data))

    # Remove records without Assessment group/subgroup as they are needed
    # NOTE: See note about groups above
    file_data = [
        row
        for row in file_data
        if row["activity"] and row["Assm. group"] and row["Assm. subgroup"]
    ]
    print(f"Complete Activity instances to convert {len(file_data)}")

    # Rename and remove keys (columns) in dictionary
    for row in file_data:

        # -- Fix instance information
        # Change sub_domain_class to ActivityInstanceClassValue, if it exists
        # API name = activity_instance_class_uid
        if row["sub_domain_class"] in MMA_SUB_DOMAIN_TO_ACTIVITY_INSTANCE_CLASS:
            row["activity_instance_class"] = MMA_SUB_DOMAIN_TO_ACTIVITY_INSTANCE_CLASS[
                row.pop("sub_domain_class")
            ]
        else:
            print(
                f"\nWarning: sub_domain_class not found '{row["sub_domain_class"]}'\n"
            )
        # Rename columns to "properties/relationships"
        row["topic_code"] = row.pop("TOPIC_CD")
        row["activity_group"] = row.pop("Assm. group")
        row["activity_subgroup"] = row.pop("Assm. subgroup")

        # -- Fix item information
        row.pop("stdm_codelist")
        row["codelist"] = row.pop("stdm_codelist_name")
        if row["codelist"] == "NO_LINKAGE_NEEDED":
            row["codelist"] = ""

        # Rename columns to Activity Items
        row["fasting_status"] = row.pop("fasting")
        row["standard_unit"] = row.pop("std_unit")
        # row["categoric_finding_original_result"] = row.pop("Response list")
        row["finding_category"] = row.pop("sdtm_cat")
        row["finding_subcategory"] = row.pop("sdtm_sub_cat")
        row["domain"] = row.pop("SDTM_DOMAIN")

    # Items
    item_cols = []
    item_cols.append("specimen")
    item_cols.append("domain")
    item_cols.append("finding_category")
    item_cols.append("finding_subcategory")
    item_cols.append("unit_dimension")
    item_cols.append("laterality")
    item_cols.append("location")
    item_cols.append("standard_unit")
    # item_cols.append("sdtm_variable")
    # item_cols.append("sdtm_variable_name")
    item_cols.append("position")
    item_cols.append("molecular_weight")
    item_cols.append("fasting_status")
    item_cols.append("loinc")
    # item_cols.append("categoric_finding_original_result")

    # Create item file
    item_rows = []
    for row in file_data:
        transposed_row = {"ACTIVITY_INSTANCE_NAME": row["activity_instance"]}

        # Add default activity items for instance classes
        if row["activity_instance_class"] == "NumericFindings":
            new_item = transposed_row.copy()
            new_item["ACTIVITY_ITEM_CLASS_NAME"] = "numeric_finding_original_result"
            new_item["ACTIVITY_ITEM_TYPE"] = ""
            new_item["ACTIVITY_ITEM_VALUE"] = ""
            new_item["IS_ADAM_PARAM_SPECIFIC"] = ""
            add_item(item_rows, new_item)
            new_item = transposed_row.copy()
            new_item["ACTIVITY_ITEM_CLASS_NAME"] = (
                "numeric_finding_original_result_unit"
            )
            new_item["ACTIVITY_ITEM_TYPE"] = ""
            new_item["ACTIVITY_ITEM_VALUE"] = ""
            new_item["IS_ADAM_PARAM_SPECIFIC"] = ""
            add_item(item_rows, new_item)
        elif row["activity_instance_class"] == "TextualFindings":
            new_item = transposed_row.copy()
            new_item["ACTIVITY_ITEM_CLASS_NAME"] = "textual_finding_original_result"
            new_item["ACTIVITY_ITEM_TYPE"] = ""
            new_item["ACTIVITY_ITEM_VALUE"] = ""
            new_item["IS_ADAM_PARAM_SPECIFIC"] = ""
            add_item(item_rows, new_item)
        elif row["activity_instance_class"] == "CategoricFindings":
            new_item = transposed_row.copy()
            new_item["ACTIVITY_ITEM_CLASS_NAME"] = "categoric_finding_original_result"
            if row["Response list"] != "":
                new_item["ACTIVITY_ITEM_TYPE"] = ""
                new_item["ACTIVITY_ITEM_VALUE"] = ""
            else:
                new_item["ACTIVITY_ITEM_TYPE"] = "codelist"
                new_item["ACTIVITY_ITEM_VALUE"] = row["Response list"]
            new_item["IS_ADAM_PARAM_SPECIFIC"] = ""
            add_item(item_rows, new_item)

        for item in item_cols:
            if row[item] == "" or row[item] == "No Linkage Needed":
                pass
            else:
                new_item = transposed_row.copy()
                new_item["ACTIVITY_ITEM_CLASS_NAME"] = item
                if item == "domain":
                    new_item["ACTIVITY_ITEM_TYPE"] = "terms"
                    new_item["ACTIVITY_ITEM_VALUE"] = "DOMAIN:" + row[item]
                elif item == "finding_category":
                    new_item["ACTIVITY_ITEM_TYPE"] = "terms"
                    new_item["ACTIVITY_ITEM_VALUE"] = "FINDCAT:" + row[item]
                elif item == "finding_subcategory":
                    new_item["ACTIVITY_ITEM_TYPE"] = "terms"
                    new_item["ACTIVITY_ITEM_VALUE"] = "FINDSCAT:" + row[item]
                elif item == "standard_unit":
                    new_item["ACTIVITY_ITEM_TYPE"] = "units"
                    new_item["ACTIVITY_ITEM_VALUE"] = row[item]
                elif item == "unit_dimension":
                    new_item["ACTIVITY_ITEM_TYPE"] = "terms"
                    new_item["ACTIVITY_ITEM_VALUE"] = "UNITDIM:" + row[item]
                elif item == "laterality":
                    new_item["ACTIVITY_ITEM_TYPE"] = "terms"
                    new_item["ACTIVITY_ITEM_VALUE"] = "LAT:" + row[item].replace(
                        "|", "||"
                    )
                elif item == "location":
                    new_item["ACTIVITY_ITEM_TYPE"] = "terms"
                    new_item["ACTIVITY_ITEM_VALUE"] = "LOC:" + row[item].replace(
                        "|", "||"
                    )
                elif item == "position":
                    new_item["ACTIVITY_ITEM_TYPE"] = "terms"
                    new_item["ACTIVITY_ITEM_VALUE"] = "POSITION:" + row[item].replace(
                        "|", "||"
                    )
                else:
                    new_item["ACTIVITY_ITEM_TYPE"] = ""
                    new_item["ACTIVITY_ITEM_VALUE"] = ""
                new_item["IS_ADAM_PARAM_SPECIFIC"] = ""
                add_item(item_rows, new_item)

        # If item has a 'codelist' it should have test_code and test_name
        if row["codelist"] != "":
            # Add test code
            new_item = transposed_row.copy()
            new_item["ACTIVITY_ITEM_CLASS_NAME"] = "test_code"
            new_item["ACTIVITY_ITEM_TYPE"] = "terms"
            new_item["ACTIVITY_ITEM_VALUE"] = (
                row["codelist"] + "CD:" + row["sdtm_variable"]
            )
            new_item["IS_ADAM_PARAM_SPECIFIC"] = ""
            add_item(item_rows, new_item)
            # Add test name
            new_item = transposed_row.copy()
            new_item["ACTIVITY_ITEM_CLASS_NAME"] = "test_name"
            new_item["ACTIVITY_ITEM_TYPE"] = "terms"
            new_item["ACTIVITY_ITEM_VALUE"] = (
                row["codelist"] + ":" + row["sdtm_variable_name"]
            )
            new_item["IS_ADAM_PARAM_SPECIFIC"] = ""
            add_item(item_rows, new_item)

    print("Number of Activity instance items rows", len(item_rows))

    if item_rows:
        save_to_file(item_rows, path, activity_instance_items_vertical_name)

    return


if __name__ == "__main__":
    # Update location 1
    mdr_path = os.path.join("datafiles", "sponsor_library", "activity")
    activity_instance_horizontal_name = "activity_instance.csv"
    activity_instance_items_vertical_name = "activity_instance_activity_items.csv"
    create_activity_instance_items(
        mdr_path,
        activity_instance_horizontal_name,
        activity_instance_items_vertical_name,
    )

    # Update location 2 (same filenames)
    e2e_path = os.path.join("e2e_datafiles", "sponsor_library", "activity")
    create_activity_instance_items(
        e2e_path,
        activity_instance_horizontal_name,
        activity_instance_items_vertical_name,
    )
