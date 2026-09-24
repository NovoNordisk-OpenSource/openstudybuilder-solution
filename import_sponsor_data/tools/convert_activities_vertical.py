import csv
import json
import os
from collections import defaultdict
from pathlib import Path

import pandas as pd

# Clear the terminal in VS Code
print("\033[2J\033[H")

MDR_ACTIVITY_PATH = os.path.join("datafiles", "sponsor_library", "activity")

# Unknown: DRUG ACCOU(tability?)
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


def save_to_file(data, name):
    try:
        transposed_activities_file = os.path.join(MDR_ACTIVITY_PATH, name)
        with open(
            transposed_activities_file, mode="w", newline="", encoding="utf-8"
        ) as csvfile:
            fieldnames = data[0].keys()  # header
            # print("fieldnames:", fieldnames)
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        print(" saved", MDR_ACTIVITY_PATH, name)

        df = pd.DataFrame.from_dict(data)

        # print (df)
        # df.to_excel(name+".xlsx", index=False)

    except Exception as error:
        print("Error", error)


# -------
# NOTE: 2026-03-04 Columns not to be used
# si_unit
# us_conv_unit
# NOTE: 2026-03-04 Standards team considering skipping "Assm. Group" and "Assm. subgroup"
# NOTE: 2026-03-04 "Assm. group" and "Assm. subgroup" are relationships, not properties


def handle_activity_instances(csvfile):
    file_data = []
    with open(csvfile) as csvfile:
        readCSV = csv.DictReader(csvfile, delimiter=",")
        cols = readCSV.fieldnames
        for row in readCSV:
            file_data.append(row)

    print("len(file_data)", len(file_data))

    # Remove records without Assessment group/subgroup as they are needed
    # NOTE: See note about groups above
    file_data = [
        row
        for row in file_data
        if row["activity"] and row["Assm. group"] and row["Assm. subgroup"]
    ]
    print(f"Activity instances with Assessment group/subgroup {len(file_data)}")

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
        row["categoric_finding_original_result"] = row.pop("Response list")
        row["finding_category"] = row.pop("sdtm_cat")
        row["finding_subcategory"] = row.pop("sdtm_sub_cat")
        row["domain"] = row.pop("SDTM_DOMAIN")

    # --
    # -- Separate output for instances and items
    # --

    # Instance "information"
    print("transposing columns")
    instance_cols = []
    instance_cols.append("activity")
    instance_cols.append("activity_instance_class")
    # GENERAL_DOMAIN_CLASS is not used in the API. Only used when looking for activity_instance_class
    instance_cols.append("GENERAL_DOMAIN_CLASS")
    instance_cols.append("legacy_description")
    instance_cols.append("topic_code")
    instance_cols.append("activity_group")
    instance_cols.append("activity_subgroup")
    instance_cols.append("adam_param_code")

    # Create instance file
    instance_rows = []
    for row in file_data:
        transposed_row = {"activity_instance": row["activity_instance"]}
        for item in instance_cols:
            new_item = transposed_row.copy()
            new_item["activity_relation"] = item
            new_item["activity_value"] = row[item]
            instance_rows.append(new_item)

    if instance_rows:
        save_to_file(instance_rows, "activity_instances.csv")

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
    item_cols.append("categoric_finding_original_result")

    # Create item file
    item_rows = []
    for row in file_data:
        # transposed_row = {x:row[x] for x in row.keys() if not x in item_cols}
        # transposed_row = {"activity_instance": row["activity_instance"], "ActivityInstanceClassValue": row["ActivityInstanceClassValue"]}
        transposed_row = {"activity_instance": row["activity_instance"]}
        # print("\n new transposed row", transposed_row['TOPIC_CD'])
        for item in item_cols:

            # print("item", item)
            if row[item] == "" or row[item] == "No Linkage Needed":
                pass
            else:
                new_item = transposed_row.copy()
                new_item["activity_item_type"] = item
                new_item["codelist"] = ""  # row['codelist']
                new_item["activity_item_value"] = row[item]
                item_rows.append(new_item)
        # If item has a 'codelist' it should have test_code and test_name
        if row["codelist"] != "":
            # Add test code
            new_item = transposed_row.copy()
            new_item["activity_item_type"] = "test_code"
            new_item["codelist"] = row["codelist"] + "CD"
            new_item["activity_item_value"] = row["sdtm_variable"]
            item_rows.append(new_item)
            # Add test name
            new_item = transposed_row.copy()
            new_item["activity_item_type"] = "test_name"
            new_item["codelist"] = row["codelist"]
            new_item["activity_item_value"] = row["sdtm_variable_name"]
            item_rows.append(new_item)

    print("len(item_rows)", len(item_rows))

    if item_rows:
        save_to_file(item_rows, "activity__instance_activity_items.csv")

    return


if __name__ == "__main__":
    mdr_migration_activity_instances = os.path.join(
        MDR_ACTIVITY_PATH, "activity_instance.csv"
    )
    print("mdr_migration_activity_instances", mdr_migration_activity_instances)
    handle_activity_instances(mdr_migration_activity_instances)
