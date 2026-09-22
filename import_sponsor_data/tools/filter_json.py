import json
import sys

helptext = """
Filters a json datafile (assumed to contain a list of objects) to include only the ones referenced by another json file.
Arguments:
- name of datafile to filter
- key to filter on, full path separated by "."
- name of datafile used as filter
- key to use as filter, full path separated by "."

Example 1, reduce the activities file:
 "concepts.activities.activities.json"
by only inlcuding activities that are referenced by the file:
 "studies.Study_000002.study-activities.json"
> python tools/filter_json.py datafiles/mockup/exported/concepts.activities.activities.json uid datafiles/mockup/exported/studies.Study_000002.study-activities.json activity.uid

Example 2, reduce the activity subgroups file:
 "concepts.activities.activity-sub-groups.json"
by only inlcuding the subgroups that are referenced by the file:
 "studies.Study_000002.study-activities.json"
> python tools/filter_json.py datafiles/mockup/exported/concepts.activities.activity-sub-groups.json uid datafiles/mockup/exported/studies.Study_000002.study-activities.json activity.activity_subgroup.uid
"""

try:
    datafilename = sys.argv[1]
    datakey = sys.argv[2]
    keyfilename = sys.argv[3]
    filterkey = sys.argv[4]
except IndexError:
    print("\nERROR! Missing argument!\n")
    print(helptext)
    sys.exit(1)

filterkeypath = filterkey.split(".")
datakeypath = datakey.split(".")

keys = set()

with open(keyfilename) as keyfile:
    keydata = json.load(keyfile)

    for item in keydata:
        value = item
        for k in filterkeypath:
            value = value.get(k, {})
        if value is not None and not isinstance(value, (dict, list)):
            keys.add(value)

print("Keys to keep:")
listing = "\n".join([f"- {v}" for v in sorted(keys)])
print(listing)

new_data = []
kept = 0
dropped = 0
invalid = 0

with open(datafilename) as datafile:
    data = json.load(datafile)

    for item in data:
        value = item
        for k in datakeypath:
            value = value.get(k, {})
        if value is None and isinstance(value, (dict, list)):
            invalid += 1
            continue
        if value in keys:
            kept += 1
            new_data.append(item)
        else:
            dropped += 1

jsondata = json.dumps(new_data, indent=2)

print(f"Total: {len(data)}, kept: {kept}, dropped {dropped}, invalid: {invalid}")

# Move to an argument?
outfilename = "filtered.json"

print(f"Writing output to {outfilename}")
with open(outfilename, "w") as outfile:
    outfile.write(jsondata)
