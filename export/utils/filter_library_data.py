# This script filters the library data to include only the content used by
# the given studies.
# The studies to include are provided as a command line argument.

import os
import argparse
import json

def get_selected_study_uids(study_numbers):
    """
    Get the selected studies from the command line arguments.
    """
    uids = []
    with open(os.path.join("output", 'studies.json'), 'r') as f:
        all_studies = json.load(f)
        for study in all_studies:
            study_number = int(
                study["current_metadata"]["identification_metadata"]["study_number"]
            )
            study_uid = study["uid"]
            if study_number in study_numbers:
                uids.append(study_uid)
    return uids

def check_activity_groupings(study_activity):
    """
    Check if the selected group and subgroup are available in the latest activity
    """
    if study_activity["latest_activity"] is None:
        return True
    selected_subgroup = study_activity["study_activity_subgroup"]["activity_subgroup_uid"]
    selected_group = study_activity["study_activity_group"]["activity_group_uid"]
    selected_grouing = (selected_group, selected_subgroup)
    available_groupings = set()
    for grouping in study_activity["latest_activity"]["activity_groupings"]:
        group_uid = grouping["activity_group_uid"]
        subgroup_uid = grouping["activity_subgroup_uid"]
        available_groupings.add((group_uid, subgroup_uid))
    if selected_grouing not in available_groupings:
        print()
        print(study_activity["study_activity_uid"], study_activity["latest_activity"]["uid"])
        print(
            f"Warning: The selected grouping ({selected_group}, {selected_subgroup}) is not available in the latest activity."
        )
        print(f"Available groupings: {available_groupings}")
        return False
    return True

def list_used_library_data(studies):
    # unique uids for each type of data,
    # except for projects and programmes which instead use names.
    groups = set()
    subgroups = set()
    activities = set()
    soa_group_terms = set()
    instances = set()
    instance_classes = set()
    item_classes = set()
    project_names = set()
    programme_names = set()

    for study_uid in studies:
        with open(os.path.join("output", f"studies.{study_uid}.json"), 'r') as f:
            study = json.load(f)
            project_name = study["current_metadata"]["identification_metadata"]["project_name"]
            project_names.add(project_name)
            programme_name = study["current_metadata"]["identification_metadata"]["clinical_programme_name"]
            programme_names.add(programme_name)
        with open(os.path.join("output", f"studies.{study_uid}.study-activities.json"), 'r') as f:
            study_activities = json.load(f)
            for sa in study_activities:
                check_activity_groupings(sa)
                activity_uid = sa["activity"]["uid"]
                activities.add(activity_uid)
                groupings = sa["activity"]["activity_groupings"]
                for grouping in groupings:
                    group_uid = grouping["activity_group_uid"]
                    if group_uid is not None:
                        groups.add(group_uid)
                    subgroup_uid = grouping["activity_subgroup_uid"]
                    if subgroup_uid is not None:
                        subgroups.add(subgroup_uid)
                soa_group_term_uid = sa["study_soa_group"]["soa_group_term_uid"]
                if soa_group_term_uid is not None:
                    soa_group_terms.add(soa_group_term_uid)
        with open(os.path.join("output", f"studies.{study_uid}.study-activity-instances.json"), 'r') as f:
            study_ais = json.load(f)
            for sai in study_ais:
                instance = sai["activity_instance"]
                if instance is None:
                    continue
                instance_uid = instance["uid"]
                instances.add(instance_uid)
                instance_class_uid = instance["activity_instance_class"]["uid"]
                if instance_class_uid is not None:
                    instance_classes.add(instance_class_uid)
                # activity_items may not be present in study-level data
                items = instance.get("activity_items")
                if items is not None:
                    for item in items:
                        item_class_uid = item["activity_item_class"]["uid"]
                        if item_class_uid is not None:
                            item_classes.add(item_class_uid)

    # If no item_classes found in study data, look them up from library data
    if len(item_classes) == 0 and len(instances) > 0:
        with open(os.path.join("output", "concepts.activities.activity-instances.json"), 'r') as f:
            library_instances = json.load(f)
            for lib_instance in library_instances:
                if lib_instance["uid"] in instances:
                    items = lib_instance.get("activity_items", [])
                    if items:
                        for item in items:
                            item_class_uid = item["activity_item_class"]["uid"]
                            if item_class_uid is not None:
                                item_classes.add(item_class_uid)

    return {"project_names": project_names, "programme_names": programme_names, "groups": groups, "subgroups": subgroups, "activities": activities, "soa_group_terms": soa_group_terms, "instances": instances, "instance_classes": instance_classes, "item_classes": item_classes}

def filter_library_data_file(name, used_identifiers, identifier_key="uid"):
    """
    Filter the library data file to include only the content used by the given studies.
    """
    print(f"Filtering {name} to include only the {len(used_identifiers)} used records.")
    with open(os.path.join("output", name), 'r') as f:
        data = json.load(f)
        filtered_data = []
        for item in data:
            if item[identifier_key] in used_identifiers:
                filtered_data.append(item)
    with open(os.path.join("output", f"filtered_{name}"), 'w') as f:
        json.dump(filtered_data, f, indent=4)

def main():
    parser = argparse.ArgumentParser(
        description="Filter library data to include only the content used by the given studies."
    )
    parser.add_argument(
        "study_numbers",
        type=int,
        nargs="+",
        help="The study numbers to include in the filtered library data.",
    )
    args = parser.parse_args()

    # Get the selected studies
    selected_study_uids = get_selected_study_uids(args.study_numbers)
    print(f"Selected study UIDs: {selected_study_uids}")
    used = list_used_library_data(selected_study_uids)
    # Filter the library data files
    filter_library_data_file("clinical-programmes.json", used["programme_names"], identifier_key="name")
    filter_library_data_file("projects.json", used["project_names"], identifier_key="name")
    filter_library_data_file("concepts.activities.activity-groups.json", used["groups"])
    filter_library_data_file("concepts.activities.activity-sub-groups.json", used["subgroups"])
    filter_library_data_file("concepts.activities.activities.json", used["activities"])
    filter_library_data_file("concepts.activities.activity-instances.json", used["instances"])
    filter_library_data_file("activity-instance-classes.json", used["instance_classes"])
    filter_library_data_file("activity-item-classes.json", used["item_classes"])



if __name__ == "__main__":
    main()
