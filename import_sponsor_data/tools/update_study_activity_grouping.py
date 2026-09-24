import csv
import json
import sys

if len(sys.argv) < 4:
    print("Too few arguments! Example, update study activities for Study_999999:")
    print(
        "python tools/update_study_activity_grouping.py datafiles/sponsor_library/activity/activity_instance.csv datafiles/mockup/exported/concepts.activities.activities.json datafiles/mockup/exported/studies.Study_999999.study-activities.json"
    )
    sys.exit()

# Load activity data from csv
fname = sys.argv[1]
with open(fname) as activities:
    csv_data = csv.DictReader(activities)
    unique_activities = {}

    group_counter = 1
    subgroup_counter = 1
    for row in csv_data:
        activity_name = row["activity"]
        group_name = row["Assm. group"]
        subgroup_name = row["Assm. subgroup"]

        if not activity_name or not group_name or not subgroup_name:
            print(f"Skipping incomplete row: {row}")
            continue
        grouping = {
            "activity_group_name": group_name,
            "activity_subgroup_name": subgroup_name,
            "activity_group_uid": f"ActivityGroup_{group_counter}",
            "activity_subgroup_uid": f"ActivitySubGroup_{subgroup_counter}",
        }
        group_counter += 1
        subgroup_counter += 1
        if activity_name not in unique_activities:
            unique_activities[activity_name] = [grouping]
        else:
            unique_activities[activity_name].append(grouping)

# Load activity data from json
fname = sys.argv[2]
with open(fname) as f:
    raw1 = f.read()

json_activities = json.loads(raw1)
for item in json_activities:
    name = item["name"]
    groupings = item["activity_groupings"]
    if name not in unique_activities:
        unique_activities[name] = groupings


studyact_fname = sys.argv[3]
with open(studyact_fname) as f:
    raw2 = f.read()

study_activities = json.loads(raw2)

for item in study_activities:
    group_uid = None
    subgroup_uid = None
    act_name = item["activity"]["name"]
    if "activity_groups" in item["activity"]:
        del item["activity"]["activity_groups"]
    if "activity_subgroups" in item["activity"]:
        del item["activity"]["activity_subgroups"]
    if "activity_group" in item["activity"]:
        del item["activity"]["activity_group"]
    if "activity_subgroup" in item["activity"]:
        del item["activity"]["activity_subgroup"]

    if act_name not in unique_activities:
        print(f"Unknown activity: {act_name}")
        continue
    groupings = unique_activities[act_name]
    item["activity"]["activity_groupings"] = groupings

    item["study_activity_subgroup"] = {
        "study_activity_subgroup_uid": "not used by import",
        "activity_subgroup_uid": groupings[0]["activity_subgroup_uid"],
    }
    item["study_activity_group"] = {
        "study_activity_group_uid": "not used by import",
        "activity_group_uid": groupings[0]["activity_group_uid"],
    }

updated_json = json.dumps(study_activities, indent=2)
print(updated_json)
print(f"Overwrite {studyact_fname}? [y/n]")
reply = input().lower()
if reply == "y":
    with open(studyact_fname, "w") as f:
        f.write(updated_json)
