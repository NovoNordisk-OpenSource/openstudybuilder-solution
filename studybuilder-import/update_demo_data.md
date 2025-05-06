# Updating the demo studies

This readme is intended to show how to update the demo study data that is included in this repo.

## File structure
Studies are stored as json, using the same data format as provided by the api.
This means the data includes a lot more data than is needed for the import.

For example, a study arm returned by the api includes a lot of details on the arm type:

```
    {
        "accepted_version": false,
        "arm_colour": "#9FA8DAFF",
        "arm_connected_branch_arms": null,
        "arm_type": {
            "catalogue_name": "SDTM CT",
            "change_description": "Approved version",
            "codelist_uid": "CTCodelist_000022",
            "end_date": null,
            "library_name": "Sponsor",
            "order": 1,
            "possible_actions": [
                "inactivate",
                "newVersion"
            ],
            "sponsor_preferred_name": "Investigational Arm",
            "sponsor_preferred_name_sentence_case": "investigational arm",
            "start_date": "2022-10-18T12:53:21.759357",
            "status": "Final",
            "term_uid": "CTTerm_000081",
            "author_username": "xyz@example.com",
            "version": "1.0"
        },
        "arm_uid": "StudyArm_000005",
        ...
```
Most of these details are not required when creating a new study arm,
the only thing we need for the arm type is the uid.
This is looked up by using `sponsor_preferred_name` from `arm_type`,
which is the only data used from the `arm_type` section.

### A note on uids
The api typically returns both the name and the uid for any linked items.

For example an activity subgroup that belongs to the activity group named "General" will include this:
```
    "activity_group": {
      "name": "General",
      "uid": "ActivityGroup_000003"
    },
```
The `uid` here, as for most items, is determined at creation time.
Hence, the "General" group in the StudyBuilder instance we are importing into
is likely to have a different `uid` than it had in the instance the data was exported from.
Thus we cannot rely on the `uid` in the exported data, and instead look up the group by name.

For this reason, all the uids in the data are ignored by the import scripts.
The only exception to this is that the uid of a study in `studies.json` used as part of the filenames
of the json files belonging to this study.
The importer only uses this information to pick up the correct files.

### The json data
All data is stored with filenames corresponding to the api endpoint it was exported from,
with slashes replaced by dots.

For example unit definitions:

`/concepts/unit-definitions --> concepts.unit-definitions.json` 

Studies:
`/studies --> studies.json` 

Then for data belonging to a specific study, the uid is part of the filename.
If the `studies.json` file includes a study with uid "Study_000004", then this will be part of the filenames.
Thus the uid in `studies.json` must match the uid in the filenames.
This is the only time a uid in the json files is used.

Example: study epochs for study with uid "Study_000004":

`/studies/Study_000004/study-epochs --> studies.Study_000004.study-epochs.json`


## Adding a new study

### Creating the study
The first step of adding a new study is to build it in StudyBuilder.
Just use the StudyBuilder application as usual, and build the full study definition. 
When creating the study, pick a study number that isn't already used in studybuilder-import.

### Exporting the study to json
Once the complete study has been created, use `studybuilder-export` to export it to json.
See the `studybuilder-export` readme for details.

It's recommended to use the `INCLUDE_STUDY_NUMBERS` to export only the desired study.
This saves a little time and avoids cluttering the export directory with files
that anyway won't be used.

### Add the study
The first step is to add the new study to `datafiles/mockup/exported/studies.json`.
This contains a list of studies.
Simply copy the entry for the new study from the exported `studies.json` into `datafiles/mockup/exported/studies.json`.

Then, check if studybuilder-import already contains a study with the same uid as the new one.
If yes, then the uid of the new study must be changed.
Assuming the uid of the new study we exported is "Study_000002",
this would collide with the demo study already included.
We can then change the uid of the new study to "Study_000003" in `datafiles/mockup/exported/studies.json`.

Next, we need to rename the files that were exported to the new names, example:
`studies.Study_000002.study-epochs.json --> studies.Study_000003.study-epochs.json`

These files all include references to the old uid.
These are ignored by the importer and can be left as they are.

### Add the study definition data
Copy all the study definition files `studies.Study_000003.*.json`  to `datafiles/mockup/exported/`

### Add any needed concepts
If the study uses any newly added concepts, like units, compunds, activities etc,
these must also be added to the corresponding json files.

Assuming that the new study adds a new coumpound, we need to add the new coumpound and its alias(es) to
`datafiles/mockup/exported/concepts.compounds.json`
and
`datafiles/mockup/exported/concepts.compound-aliases.json`.

The files contain lists of the compounds and their aliases.
The exported concept files are very long as they contain all the concepts in the library,
not only the ones used by the study we are interested in.
To keep the files in studybuilder-import manageable, we only copy over what is required.

Start by identifyig what compounds are used in the study.
This is easiest done by looking at the uids in the exported files.

Open `studies.Study_000003.study-compounds.json` and note down `compound.uid`
and `compound_alias.uid` for each item in the list. 

Locate the corresponding compounds in the exported `concepts.compounds.json`.
Copy them and add to the list in `datafiles/mockup/exported/concepts.compounds.json`.

Do the same for the the compound aliases, files `concepts.compound-aliases.json`
and `datafiles/mockup/exported/concepts.compound-aliases.json`.

Other parts of the study have deeper dependency graphs.
For example study endpoints:
```
study endpoint ─┬─ endpoint template ─── template parameters
                ├─ timeframe template ─── template parameters
                └─  study objective ─── objective template ─── template parameters
``` 
The syntax templates depend on their respective template parameters.
These can be many different things, such as activity instances or compounds. 

### Run the import
Start by making a backup of the database. Use the export script in the `neo4j-mdr-db` repo.
This creates a point we can return to, to retry the import from a clean state
in case something goes wrong when trying to import the new data.

Run the import to check that the data is imported properly.
It is sufficient to run only the json import step:
```
pipenv run mockdatajson
```

Check the log messages for errors related to missing items.
Example:
```
ERROR: Could not find criteria template with name 'some name'
```
This means that the study requires a criteria template that wasn't available.

Check what criteria templates the study uses in `datafiles/mockup/exported/studies.Study_000003.study-criteria.json`.

Locate any missing criteria in the exported `criteria-templates.json` and copy them to `datafiles/mockup/exported/criteria-templates.json`.

After fixing the issues that were found, restore the database backup, and repeat the import.




