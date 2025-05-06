import asyncio
from collections import defaultdict
import csv
import json

import aiohttp

from .functions.caselessdict import CaselessDict
from .functions.parsers import map_boolean
from .functions.utils import load_env
from .utils.importer import BaseImporter, open_file_async
from .utils.metrics import Metrics
from .utils.path_join import path_join

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False") == "True"
API_BASE_URL = load_env("API_BASE_URL")


# ---------------------------------------------------------------
# Utilities for parsing and converting data
# ---------------------------------------------------------------
#

# Set to true to use the old CT API
# TODO this is a temporary workaround, remove when no longer needed.
OLD_CT_API = False


def sample_from_dict(d, sample=10):
    if SAMPLE:
        keys = list(d)[0:sample]
        values = [d[k] for k in keys]
        return dict(zip(keys, values))
    else:
        return d


def sample_from_list(d, sample=10):
    if SAMPLE:
        return d[0:sample]
    else:
        return d


ACTIVITIES_PATH = "/concepts/activities/activities"
ACTIVITY_GROUPS_PATH = "/concepts/activities/activity-groups"
ACTIVITY_SUBGROUPS_PATH = "/concepts/activities/activity-sub-groups"
ACTIVITY_INSTANCE_CLASSES_PATH = "/activity-instance-classes"
ACTIVITY_ITEM_CLASSES_PATH = "/activity-item-classes"
ACTIVITY_ITEMS_PATH = "/activity-items"
ACTIVITY_INSTANCES_PATH = "/concepts/activities/activity-instances"

ACTIVITIES = "Activities"
ACTIVITY_GROUPS = "ActivityGroups"
ACTIVITY_SUBGROUPS = "ActivitySubgroups"
ACTIVITY_INSTANCES = "ActivityInstances"
ACTIVITY_ITEM_CLASSES = "ActivityItemClasses"
ACTIVITY_INSTANCE_CLASSES = "ActivityInstanceClasses"


class ConflictingItemError(ValueError):
    pass


# Activities with instances, groups and subgroups in sponsor library
class Activities(BaseImporter):
    logging_name = "activities"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)
        self._limit_import_to = None

    def limit_import_to(self, limit):
        if limit is not None:
            self.log.info(f"Limiting import to: {', '.join(limit)}")
        else:
            self.log.info("Importing all activity content")
        self._limit_import_to = limit

    # Get all terms belonging to any of the category and subcategory codelists
    def _get_all_cats_and_subcats(self):
        self.ensure_cache()
        sdtm_cat_lists = [
            "QSCAT",
            "ACSPCAT",
            "DECAT",
            "FTCAT",
            "CCCAT",
            "ONCRSCAT",
            "FXRESCAT",
            "ICRESCAT",
            "PYRESCAT",
            "BACAT",
            "CAGTCAT",
            "SAERCAT",
            "CPCAT",
            "IECAT",
            "DSCAT",
            "MSRESCAT",
            "CLCAT",
            "STCAT",
            "EGCATSND",
            "MIRESCAT",
        ]
        sdtm_subcat_lists = ["DSSCAT"]

        all_codelist_uids = self._get_codelists_uid_and_submval()
        sdtm_cat_uids = []
        sdtm_subcat_uids = []
        for submval in sdtm_cat_lists:
            cl_uid = all_codelist_uids.get(submval)
            if cl_uid is not None:
                if OLD_CT_API:
                    sdtm_cat_uids.extend(
                        term
                        for term in self.cache.all_terms_attributes
                        if term["codelist_uid"] == cl_uid
                    )
                else:
                    sdtm_cat_uids.extend(
                        term
                        for term in self.cache.all_terms_attributes
                        if cl_uid in [x["codelist_uid"] for x in term["codelists"]]
                    )
        for submval in sdtm_subcat_lists:
            cl_uid = all_codelist_uids.get(submval)
            if cl_uid is not None:
                if OLD_CT_API:
                    sdtm_subcat_uids.extend(
                        term
                        for term in self.cache.all_terms_attributes
                        if term["codelist_uid"] == cl_uid
                    )
                else:
                    sdtm_subcat_uids.extend(
                        term
                        for term in self.cache.all_terms_attributes
                        if cl_uid in [x["codelist_uid"] for x in term["codelists"]]
                    )
        return sdtm_cat_uids, sdtm_subcat_uids

    # Get a dictionary with key = submission value and value = uid
    def _get_codelists_uid_and_submval(self):
        all_codelist_attributes = self.api.get_all_from_api("/ct/codelists/attributes")

        all_codelist_uids = CaselessDict(
            self.api.get_all_identifiers(
                all_codelist_attributes,
                identifier="submission_value",
                value="codelist_uid",
            )
        )
        return all_codelist_uids

    # Get all terms from a codelist identified by its submission value
    def _get_codelist_terms(self, codelist_submval):
        self.ensure_cache()
        all_codelist_uids = self._get_codelists_uid_and_submval()
        cl_uid = all_codelist_uids.get(codelist_submval)
        if cl_uid is not None:
            if OLD_CT_API:
                terms = [
                    term
                    for term in self.cache.all_terms_attributes
                    if term["codelist_uid"] == cl_uid
                ]
            else:
                terms = [
                    term
                    for term in self.cache.all_terms_attributes
                    if cl_uid in [x["codelist_uid"] for x in term["codelists"]]
                ]
            return terms

    # Get a dictionary mapping submission values to term uids for a codelist identified by its uid
    def _get_submissionvalues_for_codelist(self, cl):
        terms = self._get_codelist_terms(cl)
        name_submvals = CaselessDict(
            self.api.get_all_identifiers(
                terms,
                identifier="name_submission_value",
                value="term_uid",
            )
        )
        code_submvals = CaselessDict(
            self.api.get_all_identifiers(
                terms,
                identifier="code_submission_value",
                value="term_uid",
            )
        )
        name_submvals.update(code_submvals)
        return name_submvals

    # Get a dictionary with valid ct terms that may map to values in a given column of the activity instances file
    def _get_terms_for_item_classes(self):
        ct_codelists = {
            "specimen": "SPECTYPE",
            "domain": "DOMAIN",
            "unit_dimension": "UNITDIM",
            "laterality": "LAT",
            "location": "LOC",
            "position": "POSITION",
        }

        result = {}
        for key, val in ct_codelists.items():
            result[key] = self._get_submissionvalues_for_codelist(val)
        return result

    # Get a dictionary of terms for the most common SDTM variable codelists
    def _get_terms_for_codelist_submvals(self):
        self.log.info("Fetching terms for common sdtm variable codelists")
        codelists = ["FATESTCD", "LBTESTCD", "VSTESTCD", "PROTMLST", "RPTESTCD"]

        result = {"NO_LINKAGE_NEEDED": []}
        for cd in codelists:
            result[cd] = self._get_submissionvalues_for_codelist(cd)
        self.terms_for_codelist_submval = result

    # Add a new codelist to the dictionary of terms for SDTM variable codelists
    def _get_terms_for_additional_codelist_submval(self, submval):
        self.log.info(f"Fetching terms for codelist with submission value '{submval}'")
        cl_terms = self._get_submissionvalues_for_codelist(submval)
        if cl_terms is not None and len(cl_terms) == 0:
            cl_terms = None
        self.terms_for_codelist_submval[submval] = cl_terms

    # Sort a list of activity items by class, returns a dict with class as key
    def _sort_activity_items_by_class(self, items):
        result = {}
        for item in items:
            class_name = item["activity_item_class"]["name"]
            if class_name not in result:
                result[class_name] = {}
            result[class_name][item["name"]] = item
        return result

    @open_file_async()
    async def handle_activity_groups(self, csvfile, session):
        # Populate then activity groups in sponsor library
        csv_data = csv.DictReader(csvfile)
        api_tasks = []

        existing_rows = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_GROUPS_PATH),
            identifier="name",
            value="uid",
        )

        unique_groups = {}
        for row in csv_data:
            group_name = row["Assm. group"]
            if group_name and group_name not in unique_groups:
                unique_groups[group_name] = {
                    "name": group_name,
                    "name_sentence_case": group_name.lower(),
                    "definition": "Definition not provided",
                    "library_name": "Sponsor",
                }

        for _key, itemdata in unique_groups.items():
            data = {
                "path": ACTIVITY_GROUPS_PATH,
                "approve_path": ACTIVITY_GROUPS_PATH,
                "body": itemdata,
            }
            if not existing_rows.get(data["body"]["name"]):
                self.log.info(
                    f"Add activity group '{data['body']['name']}' to library '{data['body']['library_name']}'"
                )
                api_tasks.append(
                    self.api.post_then_approve(data=data, session=session, approve=True)
                )  # TODO Verify if activity groups can be approved?
            else:
                # Already exists, skip.
                # Do we need patch functionality here?
                self.log.info(
                    f"Item '{data['body']['name']}' already exists in library '{data['body']['library_name']}'"
                )
        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def handle_activity_subgroups(self, csvfile, session):
        # Populate then activity subgroups in sponsor library
        csv_data = csv.DictReader(csvfile)

        existing_groups = sample_from_dict(
            self.api.get_all_identifiers(
                self.api.get_all_from_api(ACTIVITY_GROUPS_PATH),
                identifier="name",
                value="uid",
            ),
            sample=10,
        )

        existing_sub_groups = {}

        for item in self.api.get_all_from_api(ACTIVITY_SUBGROUPS_PATH):
            existing_sub_groups[item["name"]] = {
                "uid": item["uid"],
                "activity_groups": item["activity_groups"],
            }

        api_tasks = []

        unique_subgroups = {}

        for row in csv_data:
            group_name = row["Assm. group"]
            subgroup_name = row["Assm. subgroup"]
            if not group_name or not subgroup_name:
                self.log.warning(f"Skipping incomplete row: {row}")
                continue
            if group_name not in existing_groups:
                self.log.warning(
                    f"Group name not found: '{group_name}', skipping row for: '{subgroup_name}'"
                )
                continue
            if subgroup_name not in unique_subgroups:
                self.log.info(
                    f"New subgroup: '{subgroup_name}', in group: '{group_name}'"
                )
                unique_subgroups[subgroup_name] = {
                    "name": subgroup_name,
                    "name_sentence_case": subgroup_name.lower(),
                    "library_name": "Sponsor",
                    "activity_groups": [existing_groups[group_name]],
                }
            else:
                existing_data = unique_subgroups[subgroup_name]
                group_uid = existing_groups[group_name]
                if group_uid not in existing_data["activity_groups"]:
                    self.log.info(
                        f"Adding subgroup: '{subgroup_name}' to group: '{group_name}'"
                    )
                    existing_data["activity_groups"].append(group_uid)
                else:
                    self.log.info(
                        f"No changes: '{subgroup_name}' in group: '{group_name}'"
                    )

        for subgroup_name, item_data in unique_subgroups.items():
            # Check if subgroup exists
            if subgroup_name in existing_sub_groups:
                existing_groups = set(
                    item["uid"]
                    for item in existing_sub_groups[subgroup_name]["activity_groups"]
                )
                if set(item_data["activity_groups"]) == existing_groups:
                    self.log.info(
                        f"Subgroup '{subgroup_name}' already has groups '{item_data['activity_groups']}'"
                    )
                    continue
                data = {
                    "path": ACTIVITY_SUBGROUPS_PATH,
                    "patch_path": path_join(
                        ACTIVITY_SUBGROUPS_PATH,
                        existing_sub_groups[subgroup_name]["uid"],
                    ),
                    "new_path": path_join(
                        ACTIVITY_SUBGROUPS_PATH,
                        existing_sub_groups[subgroup_name]["uid"],
                        "versions",
                    ),
                    "approve_path": ACTIVITY_SUBGROUPS_PATH,
                    "body": item_data,
                }
                data["body"]["change_description"] = "Migration modification"
                self.log.info(
                    f"Patching subgroup '{subgroup_name}' to group '{group_name}'"
                )
                api_tasks.append(
                    self.api.new_version_patch_then_approve(
                        data=data, session=session, approve=True
                    )
                )
            else:
                # Create the new subgroup
                data = {
                    "path": ACTIVITY_SUBGROUPS_PATH,
                    "approve_path": ACTIVITY_SUBGROUPS_PATH,
                    "body": item_data,
                }
                self.log.info(
                    f"Adding subgroup '{subgroup_name}' to groups '{group_name}'"
                )
                api_tasks.append(
                    self.api.post_then_approve(data=data, session=session, approve=True)
                )
        await asyncio.gather(*api_tasks)

    def _are_groupings_equal(self, old, new):
        # Convert both old and new to lists of tuples, (group_uid, subgroup_uid)
        # These are hashable so the lists can be made into sets for easy comparison
        new_groupings = set(
            (item["activity_group_uid"], item["activity_subgroup_uid"]) for item in new
        )
        old_groupings = set(
            (item["activity_group_uid"], item["activity_subgroup_uid"]) for item in old
        )
        return new_groupings == old_groupings

    def _are_activities_equal(self, old, new):
        existing_groupings = old["activity_groupings"]
        new_groupings = new["activity_groupings"]
        return (
            old.get("nci_concept_id") == new.get("nci_concept_id")
            and old.get("is_data_collected") == new.get("is_data_collected")
            and old.get("name_sentence_case") == new.get("name_sentence_case")
            and old.get("definition") == new.get("definition")
            and self._are_groupings_equal(existing_groupings, new_groupings)
        )

    @open_file_async()
    async def handle_activities(self, csvfile, session):
        # Populate the activities in sponsor library
        csv_data = csv.DictReader(csvfile)
        self.log.info("Fetching all existing activity groups and subgroups")
        existing_groups = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_GROUPS_PATH),
            identifier="name",
            value="uid",
        )
        existing_sub_groups = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_SUBGROUPS_PATH),
            identifier="name",
            value="uid",
        )

        self.log.info("Fetching all existing activities")
        existing_activities = {}
        raw_activities = self.api.get_all_activity_objects("activities")
        for item in raw_activities:
            if item["name"] in existing_activities:
                if item["library_name"] == "Requested":
                    # Don't replace with a requested activity
                    continue

            existing_activities[item["name"]] = {
                "uid": item["uid"],
                "name_sentence_case": item["name_sentence_case"],
                "is_data_collected": item["is_data_collected"],
                "nci_concept_id": item["nci_concept_id"] or None,
                "definition": item["definition"] or "TBD",
                "activity_groupings": item["activity_groupings"],
                "library_name": item["library_name"],
                "status": item["status"],
            }

        api_tasks = []

        unique_activities = {}

        for row in csv_data:
            activity_name = row["activity"]
            group_name = row["Assm. group"]
            subgroup_name = row["Assm. subgroup"]

            if not activity_name or not group_name or not subgroup_name:
                self.log.warning(f"Skipping incomplete row: {row}")
                continue
            if group_name not in existing_groups:
                self.log.warning(
                    f"Group name not found: '{group_name}', skipping row for: '{activity_name}'"
                )
                continue
            if subgroup_name not in existing_sub_groups:
                self.log.warning(
                    f"Subgroup name not found: '{subgroup_name}', skipping row for: '{activity_name}'"
                )
                continue
            group_uid = existing_groups[group_name]
            subgroup_uid = existing_sub_groups[subgroup_name]
            grouping = {
                "activity_group_uid": group_uid,
                "activity_subgroup_uid": subgroup_uid,
            }
            # WIP
            # - nci_concept_id: not existing in current data.
            # - is_data_collected: will be False for reminders. These activities don't have instances. These are not yet imported.
            # - definition: not existing in current data.
            # TODO determine how to provide nci_concept_id for activity
            # TODO determine how to specify reminder activities
            if activity_name not in unique_activities:
                unique_activities[activity_name] = {
                    "name": activity_name,
                    "name_sentence_case": activity_name.lower(),
                    "definition": None,
                    "library_name": "Sponsor",
                    "activity_groupings": [grouping],
                    "nci_concept_id": None,
                    "is_data_collected": True,
                }
            else:
                existing_data = unique_activities[activity_name]
                if grouping not in existing_data["activity_groupings"]:
                    existing_data["activity_groupings"].append(grouping)

        for _key, item_data in unique_activities.items():
            activity_name = item_data["name"]
            # Check if activity exists
            try:
                existing = self.get_existing_activity(
                    activity_name, existing_activities
                )
                if existing is not None:
                    existing = existing_activities[activity_name]
                    if (
                        existing["library_name"] == "Requested"
                        and existing["status"] == "Retired"
                    ):
                        self.log.info(
                            f"Activity '{activity_name}' already exists as a retired request, ok to create a new one"
                        )
                    elif existing["library_name"] == "Requested":
                        self.log.warning(
                            f"Activity '{activity_name}' already exists as a requested activity, skipping"
                        )
                        continue
                    elif existing["status"] == "Retired":
                        self.log.warning(
                            f"Activity '{activity_name}' already exists and is retired, skipping"
                        )
                        continue
                    # If the activity does not already have all groups -> patch it
                    groupings = item_data["activity_groupings"]
                    if self._are_activities_equal(
                        existing_activities[activity_name], item_data
                    ):
                        self.log.info(
                            f"Identical activity '{activity_name}' already exists"
                        )
                        if existing["status"] == "Draft":
                            self.log.info(
                                f"Identical activity '{activity_name}' is in draft, approving"
                            )
                            api_tasks.append(
                                self.api.approve_item_async(
                                    uid=existing["uid"],
                                    url=ACTIVITIES_PATH,
                                    session=session,
                                )
                            )
                        continue
                    data = {
                        "path": ACTIVITIES_PATH,
                        "patch_path": path_join(
                            ACTIVITIES_PATH, existing_activities[activity_name]["uid"]
                        ),
                        "new_path": path_join(
                            ACTIVITIES_PATH,
                            existing_activities[activity_name]["uid"],
                            "versions",
                        ),
                        "approve_path": ACTIVITIES_PATH,
                        "body": item_data,
                    }
                    data["body"]["change_description"] = "Migration modification"
                    self.log.info(
                        f"Adding activity '{activity_name}' to groupings '{groupings}'"
                    )
                    api_tasks.append(
                        self.api.new_version_patch_then_approve(
                            data=data, session=session, approve=True
                        )
                    )
                else:  # Create the activity
                    data = {
                        "path": ACTIVITIES_PATH,
                        "approve_path": ACTIVITIES_PATH,
                        "body": item_data,
                    }
                    self.log.info(f"Adding activity '{activity_name}'")
                    api_tasks.append(
                        self.api.post_then_approve(
                            data=data, session=session, approve=True
                        )
                    )
            except ConflictingItemError as e:
                self.log.warning(
                    f"Activity '{activity_name}' already exists as {e}, skipping"
                )

        await asyncio.gather(*api_tasks)

    def get_existing_activity(self, activity_name, existing_activities):
        if activity_name in existing_activities:
            existing = existing_activities[activity_name]
            if (
                existing["library_name"] == "Requested"
                and existing["status"] == "Retired"
            ):
                self.log.info(
                    f"Activity '{activity_name}' already exists as a retired request, ok to create a new one"
                )
                return None
            elif existing["library_name"] == "Requested":
                self.log.warning(
                    f"Activity '{activity_name}' already exists as a requested activity, skipping"
                )
                raise ConflictingItemError("Requested")
            elif existing["status"] == "Retired":
                self.log.warning(
                    f"Activity '{activity_name}' already exists and is retired, skipping"
                )
                raise ConflictingItemError("Retired")
            return existing
        return None

    @open_file_async()
    async def handle_activity_instance_classes(self, csvfile, session):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        api_tasks_for_0_level_ac = []
        api_tasks_for_1_level_ac = []
        api_tasks_for_2_level_ac = []
        api_tasks_for_3_level_ac = []
        api_tasks_for_4_level_ac = []

        migrated_ac_level_0 = []
        migrated_ac_level_1 = []
        migrated_ac_level_2 = []
        migrated_ac_level_3 = []
        migrated_ac_level_4 = []
        existing_rows = self.api.response_to_dict(
            self.api.get_all_from_api(ACTIVITY_INSTANCE_CLASSES_PATH),
            identifier="name",
        )

        def are_instance_classes_equal(new, existing):
            existing_parent_uid = (
                existing.get("parent_class").get("uid")
                if existing.get("parent_class")
                else None
            )
            new_parent_uid = new.get("parent_uid") if new.get("parent_uid") else None
            new_order = int(new.get("order")) if new.get("order") else None
            try:
                new_is_specific = map_boolean(
                    new.get("is_domain_specific"), raise_exception=True
                )
            except ValueError:
                new_is_specific = None
            result = (
                existing_parent_uid == new_parent_uid
                and existing.get("name") == new.get("name")
                and existing.get("level") == new.get("level")
                and existing.get("library_name") == new.get("library_name")
                and existing.get("is_domain_specific") == new_is_specific
                and existing.get("definition") == new.get("definition")
                and existing.get("order") == new_order
                and [domain["uid"] for domain in existing.get("data_domains") or []]
                == new.get("data_domain_uids", [])
            )
            return result

        async def _migrate_aic(data):
            if existing_rows.get(data["body"]["name"]) is None:
                self.log.info(
                    f"Add activity instance class '{data['body']['name']}' to library '{data['body']['library_name']}'"
                )
                response = await self.api.post_then_approve(
                    data=data, session=session, approve=True
                )
                if response:
                    existing_rows[data["body"]["name"]] = response
            elif not are_instance_classes_equal(
                data["body"], existing_rows.get(data["body"]["name"])
            ):
                self.log.info(
                    f"Patch activity instance class '{data['body']['name']}' in library '{data['body']['library_name']}'"
                )
                data["patch_path"] = path_join(
                    ACTIVITY_INSTANCE_CLASSES_PATH,
                    existing_rows[data["body"]["name"]].get("uid"),
                )
                data["new_path"] = path_join(
                    ACTIVITY_INSTANCE_CLASSES_PATH,
                    existing_rows[data["body"]["name"]].get("uid"),
                    "versions",
                )
                data["body"]["change_description"] = "Migration modification"
                response = await self.api.new_version_patch_then_approve(
                    data=data, session=session, approve=True
                )
                if response:
                    existing_rows[data["body"]["name"]] = response
            else:
                self.log.info(
                    f"Identical entry '{data['body']['name']}' already exists in library '{data['body']['library_name']}'"
                )

        with open(
            load_env(
                "MDR_MIGRATION_ACTIVITY_INSTANCE_CLASS_TO_DATA_DOMAIN_RELATIONSHIPS"
            ),
            encoding="utf-8",
        ) as file:
            data_domain_relationships = csv.reader(file)

            # Skip the header row
            next(data_domain_relationships)

            data_domains = set()
            activity_instance_class_data_domain_relationships = defaultdict(set)
            for (
                table,
                _,
                _,
                level_2_class,
            ) in data_domain_relationships:

                if level_2_class.strip():
                    data_domains.add(table.strip())
                    activity_instance_class_data_domain_relationships[
                        level_2_class.strip()
                    ].add(table.strip())

            rs_data_domains = {
                data_domain_term["code_submission_value"]: data_domain_term["term_uid"]
                for data_domain_term in self.api.get_filtered_terms(
                    {"code_submission_value": {"v": list(data_domains)}}
                )
            }

        for row in readCSV:
            # migrating Level 0 ActivityInstanceClass
            ac_0_level_name = row[headers.index("LEVEL_0_CLASS")]
            ac_0_level_data = {
                "path": ACTIVITY_INSTANCE_CLASSES_PATH,
                "approve_path": ACTIVITY_INSTANCE_CLASSES_PATH,
                "body": {
                    "name": ac_0_level_name,
                    "level": 0,
                    "library_name": "Sponsor",
                },
            }
            if ac_0_level_name not in migrated_ac_level_0:
                migrated_ac_level_0.append(ac_0_level_name)
                api_tasks_for_0_level_ac.append(_migrate_aic(ac_0_level_data))

            # migrating Level 1 ActivityInstanceClass
            ac_1_level_name = row[headers.index("LEVEL_1_CLASS")]
            ac_1_level_data = {
                "path": ACTIVITY_INSTANCE_CLASSES_PATH,
                "approve_path": ACTIVITY_INSTANCE_CLASSES_PATH,
                "body": {
                    "name": ac_1_level_name,
                    "level": 1,
                    "parent_uid": existing_rows.get(ac_0_level_name, {}).get("uid"),
                    "library_name": "Sponsor",
                },
            }
            if ac_1_level_name not in migrated_ac_level_1:
                migrated_ac_level_1.append(ac_1_level_name)
                api_tasks_for_1_level_ac.append(_migrate_aic(ac_1_level_data))

            # migrating Level 2 ActivityInstanceClass
            ac_2_level_name = row[headers.index("LEVEL_2_CLASS")]
            ac_2_level_data = {
                "path": ACTIVITY_INSTANCE_CLASSES_PATH,
                "approve_path": ACTIVITY_INSTANCE_CLASSES_PATH,
                "body": {
                    "name": ac_2_level_name,
                    "level": 2,
                    "parent_uid": existing_rows.get(ac_1_level_name, {}).get("uid"),
                    "library_name": "Sponsor",
                    "data_domain_uids": [
                        uid
                        for domain, uid in rs_data_domains.items()
                        if domain
                        in activity_instance_class_data_domain_relationships[
                            ac_2_level_name
                        ]
                    ],
                },
            }
            if ac_2_level_name not in migrated_ac_level_2:
                migrated_ac_level_2.append(ac_2_level_name)
                api_tasks_for_2_level_ac.append(_migrate_aic(ac_2_level_data))

            # migrating Level 3 ActivityInstanceClass
            ac_3_level_name = row[headers.index("LEVEL_3_CLASS")]
            ac_3_level_data = {
                "path": ACTIVITY_INSTANCE_CLASSES_PATH,
                "approve_path": ACTIVITY_INSTANCE_CLASSES_PATH,
                "body": {
                    "name": ac_3_level_name,
                    "level": 3,
                    "parent_uid": existing_rows.get(ac_2_level_name, {}).get("uid"),
                    "is_domain_specific": row[headers.index("DOMAIN_SPECIFIC")],
                    "definition": row[headers.index("DEFINITION")] or "TBD",
                    "order": row[headers.index("ORDER")],
                    "library_name": "Sponsor",
                },
            }
            if ac_3_level_name not in migrated_ac_level_3:
                migrated_ac_level_3.append(ac_3_level_name)
                api_tasks_for_3_level_ac.append(_migrate_aic(ac_3_level_data))

            # migrating Level 4 ActivityInstanceClass
            ac_4_level_name = row[headers.index("LEVEL_4_CLASS")]
            if row[headers.index("LEVEL_4_CLASS")]:
                ac_4_level_data = {
                    "path": ACTIVITY_INSTANCE_CLASSES_PATH,
                    "approve_path": ACTIVITY_INSTANCE_CLASSES_PATH,
                    "body": {
                        "name": ac_4_level_name,
                        "level": 4,
                        "parent_uid": existing_rows.get(ac_3_level_name, {}).get("uid"),
                        "is_domain_specific": row[headers.index("DOMAIN_SPECIFIC")],
                        "definition": row[headers.index("DEFINITION")] or "TBD",
                        "order": row[headers.index("ORDER")],
                        "library_name": "Sponsor",
                    },
                }
                if ac_4_level_name not in migrated_ac_level_4:
                    migrated_ac_level_4.append(ac_4_level_name)
                    api_tasks_for_4_level_ac.append(_migrate_aic(ac_4_level_data))

        await asyncio.gather(*api_tasks_for_0_level_ac)
        await asyncio.gather(*api_tasks_for_1_level_ac)
        await asyncio.gather(*api_tasks_for_2_level_ac)
        await asyncio.gather(*api_tasks_for_3_level_ac)
        await asyncio.gather(*api_tasks_for_4_level_ac)

    @open_file_async()
    async def handle_activity_instance_class_parent_relationship(
        self, csvfile, session
    ):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        existing_rows = self.api.response_to_dict(
            self.api.get_all_from_api(ACTIVITY_INSTANCE_CLASSES_PATH),
            identifier="name",
        )

        for row in readCSV:
            for i in range(1, 4):
                current_class_name = row[headers.index(f"LEVEL_{i}_CLASS")]
                current_uid = existing_rows.get(current_class_name, {}).get("uid")
                parent_class_name = row[headers.index(f"LEVEL_{i-1}_CLASS")]
                parent_uid = existing_rows.get(parent_class_name, {}).get("uid")

                data = {
                    "path": ACTIVITY_INSTANCE_CLASSES_PATH,
                    "approve_path": ACTIVITY_INSTANCE_CLASSES_PATH,
                    "new_path": path_join(
                        ACTIVITY_INSTANCE_CLASSES_PATH, current_uid, "versions"
                    ),
                    "patch_path": path_join(
                        ACTIVITY_INSTANCE_CLASSES_PATH, current_uid
                    ),
                    "body": {
                        "change_description": "StudybuilderImport modification for parent relationship",
                        "parent_uid": parent_uid,
                    },
                }
                self.log.info(
                    f"Patch activity instance class '{current_class_name}' by connecting to parent '{parent_class_name}'"
                )
                response = await self.api.new_version_patch_then_approve(
                    data=data, session=session, approve=True
                )
                if response:
                    existing_rows[current_class_name] = response

    def are_item_classes_equal(self, new, existing):
        def are_instance_classes_equal():
            _new = []
            for i in new.get("activity_instance_classes") or []:
                _new.append(
                    {
                        "name": i["name"],
                        "mandatory": i["mandatory"],
                        "is_adam_param_specific_enabled": i[
                            "is_adam_param_specific_enabled"
                        ],
                    }
                )
            _new = sorted(_new, key=json.dumps)

            _existing = []
            for i in existing.get("activity_instance_classes") or []:
                _existing.append(
                    {
                        "name": i["name"],
                        "mandatory": i["mandatory"],
                        "is_adam_param_specific_enabled": i[
                            "is_adam_param_specific_enabled"
                        ],
                    }
                )
            _existing = sorted(_existing, key=json.dumps)

            return _new == _existing

        new_order = int(new.get("order")) if new.get("order") else None
        result = (
            existing.get("name") == new.get("name")
            and existing.get("library_name") == new.get("library_name")
            and existing.get("mandatory") == new.get("mandatory")
            and existing.get("definition") == new.get("definition")
            and existing.get("nci_concept_id") == new.get("nci_concept_id")
            and existing.get("order") == new_order
            and existing.get("role").get("uid") == new.get("role_uid")
            and existing.get("data_type").get("uid") == new.get("data_type_uid")
            and [codelist["uid"] for codelist in existing.get("codelists") or []]
            == new.get("codelist_uids", [])
            and are_instance_classes_equal()
        )
        return result

    @open_file_async()
    async def handle_activity_item_classes(self, csvfile, session):
        self.ensure_cache()
        # Populate then activity item classes in sponsor library
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        api_tasks = []

        existing_rows = self.api.response_to_dict(
            self.api.get_all_from_api(ACTIVITY_ITEM_CLASSES_PATH),
            identifier="name",
        )
        available_instance_classes = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_INSTANCE_CLASSES_PATH),
            identifier="name",
            value="uid",
        )

        activity_item_data = {}
        for row in readCSV:
            activity_instance_class_name = row[headers.index("ACTIVITY_INSTANCE_CLASS")]
            instance_class_uid = available_instance_classes.get(
                activity_instance_class_name
            )
            role = row[headers.index("SEMANTIC_ROLE")]
            if role in self.cache.all_terms_name_submission_values:
                role_uid = self.cache.all_terms_name_submission_values[role]
            else:
                self.log.warning(
                    f"The role ({role}) wasn't found for the following ActivityInstanceClass ({activity_instance_class_name})"
                )
                continue
            data_type = row[headers.index("SEMANTIC_DATA_TYPE")]
            if data_type in self.cache.all_terms_name_submission_values:
                data_type_uid = self.cache.all_terms_name_submission_values[data_type]
            else:
                self.log.warning(
                    f"The data_type ({data_type}) wasn't found for the following ActivityInstanceClass ({activity_instance_class_name})"
                )
                continue
            activity_item_class_name = row[headers.index("ACTIVITY_ITEM_CLASS")]
            if instance_class_uid is None:
                self.log.warning(
                    f"Activity instance class '{activity_instance_class_name}' "
                    f"wasn't found in available activity instance classes in the db"
                )
                continue

            codelist_uids = []
            codelist_submission_values = [
                value.strip()
                for value in row[headers.index("CODELIST")].split(";")
                if value.strip()
            ]
            for codelist_submission_value in codelist_submission_values:
                _codelist = self.api.find_object_by_key(
                    codelist_submission_value,
                    "ct/codelists/attributes",
                    "submission_value",
                )
                if _codelist:
                    codelist_uids.append(_codelist["codelist_uid"])
                else:
                    self.log.warning(
                        f"The codelist ({codelist_submission_value}) wasn't found for the following ActivityItemClass ({activity_item_class_name})"
                    )

            data = {
                "path": ACTIVITY_ITEM_CLASSES_PATH,
                "approve_path": ACTIVITY_ITEM_CLASSES_PATH,
                "body": {
                    "name": activity_item_class_name,
                    "order": row[headers.index("ORDER")],
                    "definition": row[headers.index("DEFINITION")] or "TBD",
                    "nci_concept_id": row[headers.index("NCI_C_CODE")] or None,
                    "activity_instance_classes": [
                        {
                            "uid": instance_class_uid,
                            "name": activity_instance_class_name,
                            "mandatory": map_boolean(row[headers.index("MANDATORY")]),
                            "is_adam_param_specific_enabled": map_boolean(
                                row[headers.index("IS_ADAM_PARAM_SPECIFIC_ENABLED")]
                            ),
                        }
                    ],
                    "activity_instance_class_names": [activity_instance_class_name],
                    "role_uid": role_uid,
                    "data_type_uid": data_type_uid,
                    "codelist_uids": codelist_uids,
                    "library_name": "Sponsor",
                },
            }
            if activity_item_class_name not in activity_item_data:
                activity_item_data[activity_item_class_name] = data
            else:
                current_instance_classes = (
                    activity_item_data[activity_item_class_name]["body"][
                        "activity_instance_classes"
                    ]
                    or []
                )
                if instance_class_uid not in current_instance_classes:
                    current_instance_classes.append(
                        {
                            "uid": instance_class_uid,
                            "name": activity_instance_class_name,
                            "mandatory": map_boolean(row[headers.index("MANDATORY")]),
                            "is_adam_param_specific_enabled": map_boolean(
                                row[headers.index("IS_ADAM_PARAM_SPECIFIC_ENABLED")]
                            ),
                        }
                    )
                    activity_item_data[activity_item_class_name]["body"][
                        "activity_instance_class_names"
                    ].append(activity_instance_class_name)

            if activity_item_class_name in activity_item_data:
                self.log.info(
                    f"Trying to link {activity_item_class_name} "
                    f"to additional instance class {activity_instance_class_name}"
                )

        for item_name, item_data in activity_item_data.items():
            if item_name not in existing_rows:
                self.log.info(
                    f"Add activity item class '{item_data['body']['name']}' to library '{item_data['body']['library_name']}'"
                )
                if "activity_instance_class_names" in item_data["body"]:
                    item_data["body"].pop("activity_instance_class_names")
                api_tasks.append(
                    self.api.post_then_approve(
                        data=item_data, session=session, approve=True
                    )
                )
            elif not self.are_item_classes_equal(
                item_data["body"], existing_rows[item_name]
            ):
                self.log.info(
                    f"Patch activity item class '{item_data['body']['name']}' to library '{item_data['body']['library_name']}'"
                )
                if "activity_instance_class_names" in item_data["body"]:
                    item_data["body"].pop("activity_instance_class_names")
                item_data["patch_path"] = path_join(
                    ACTIVITY_ITEM_CLASSES_PATH,
                    existing_rows[item_name].get("uid"),
                )
                item_data["new_path"] = path_join(
                    ACTIVITY_ITEM_CLASSES_PATH,
                    existing_rows[item_name].get("uid"),
                    "versions",
                )
                item_data["body"]["change_description"] = "Migration modification"
                api_tasks.append(
                    self.api.new_version_patch_then_approve(
                        data=item_data, session=session, approve=True
                    )
                )
            else:
                self.log.info(
                    f"Identical item class '{item_data['body']['name']}' already exists in library '{item_data['body']['library_name']}'"
                )

        await asyncio.gather(*api_tasks)
        # await session.close()

    def compare_instance_items(self, old, new):
        new_items = set(
            (
                item.get("activity_item_class_uid"),
                frozenset(item.get("ct_term_uids", [])),
                frozenset(item.get("unit_definition_uids", [])),
            )
            for item in new
        )
        old_items = set(
            (
                item.get("activity_item_class", {}).get("uid"),
                frozenset(term["uid"] for term in item.get("ct_terms", [])),
                frozenset(unit["uid"] for unit in item.get("unit_definitions", [])),
            )
            for item in old
        )
        return new_items == old_items

    def compare_instance_groupings(self, old, new):
        # Convert both old and new to lists of tuples, (activity_uid, group_uid, subgroup_uid)
        # These are hashable so the lists can be made into sets for easy comparison
        new_groupings = set(
            (
                item["activity_uid"],
                item["activity_group_uid"],
                item["activity_subgroup_uid"],
            )
            for item in new
        )
        old_groupings = set(
            (
                item.get("activity", {}).get("uid"),
                item.get("activity_group", {}).get("uid"),
                item.get("activity_subgroup", {}).get("uid"),
            )
            for item in old
        )
        return new_groupings == old_groupings

    def are_instances_equal(self, new, existing):
        result = (
            existing.get("activity_instance_class").get("uid")
            == new.get("activity_instance_class_uid")
            and existing.get("library_name") == new.get("library_name")
            and existing.get("name_sentence_case") == new.get("name_sentence_case")
            and existing.get("definition") == new.get("definition")
            and existing.get("adam_param_code") == new.get("adam_param_code")
            and existing.get("legacy_description") == new.get("legacy_description")
            and existing.get("topic_code") == new.get("topic_code")
            and existing.get("nci_concept_id") == new.get("nci_concept_id")
            and existing.get("is_required_for_activity")
            == new.get("is_required_for_activity")
            and existing.get("is_default_selected_for_activity")
            == new.get("is_default_selected_for_activity")
            and existing.get("is_data_sharing") == new.get("is_data_sharing")
            and existing.get("is_legacy_usage") == new.get("is_legacy_usage")
            and self.compare_instance_items(
                existing["activity_items"], new["activity_items"]
            )
            and self.compare_instance_groupings(
                existing["activity_groupings"], new["activity_groupings"]
            )
        )
        return result

    @open_file_async()
    async def handle_activity_instances(self, csvfile, session):
        readCSV = csv.DictReader(csvfile, delimiter=",")
        api_tasks = []

        # get only Final activities in Sponsor library
        activity_filters = {
            "library_name": {"v": ["Sponsor"], "op": "eq"},
            "status": {"v": ["Final"], "op": "eq"},
        }
        all_activities = self.api.get_all_identifiers(
            self.api.get_all_activity_objects(
                "activities", filters=json.dumps(activity_filters)
            ),
            identifier="name",
            value="uid",
        )

        all_activity_instance_classes = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_INSTANCE_CLASSES_PATH),
            identifier="name",
            value="uid",
        )

        all_groups = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_GROUPS_PATH),
            identifier="name",
            value="uid",
        )
        all_subgroups = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_SUBGROUPS_PATH),
            identifier="name",
            value="uid",
        )

        self.all_activity_item_classes = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_ITEM_CLASSES_PATH),
            identifier="name",
            value="uid",
        )

        self.all_units = self.api.get_all_identifiers(
            self.api.get_all_from_api("/concepts/unit-definitions"),
            identifier="name",
            value="uid",
        )

        sdtm_cats, sdtm_subcats = self._get_all_cats_and_subcats()
        self.sdtm_cats = sdtm_cats
        self.sdtm_subcats = sdtm_subcats

        self.log.info("Fetching terms for item classes")
        terms_for_item_classes = self._get_terms_for_item_classes()

        self._get_terms_for_codelist_submvals()

        existing_instances = self.api.get_all_activity_objects("activity-instances")
        existing_rows_by_name = self.api.response_to_dict(
            existing_instances,
            identifier="name",
        )
        existing_rows_by_tc = self.api.response_to_dict(
            existing_instances,
            identifier="topic_code",
        )

        file_data = []
        for row in readCSV:
            file_data.append(row)

        file_data = sample_from_list(file_data, sample=10)
        all_data = {}
        for row in file_data:
            activity_instance_name = row["activity_instance"]
            activity = row["activity"]
            group = row["Assm. group"]
            subgroup = row["Assm. subgroup"]
            if not activity or not group or not subgroup:
                self.log.warning(f"Skipping incomplete row: {row}")
                continue

            # find related Activity hierarchy
            activity_groupings = []
            if (
                activity in all_activities
                and group in all_groups
                and subgroup in all_subgroups
            ):
                grouping = {
                    "activity_group_uid": all_groups[group],
                    "activity_subgroup_uid": all_subgroups[subgroup],
                    "activity_uid": all_activities[activity],
                }
                activity_groupings.append(grouping)
            else:
                act = activity in all_activities
                grp = group in all_groups
                sgrp = subgroup in all_subgroups
                self.log.warning(
                    f"Skipping instance {activity_instance_name} due to missing dependency"
                )
                if not act:
                    self.log.warning(f"Activity '{activity}' not found")
                if not grp:
                    self.log.warning(f"Group '{group}' not found")
                if not sgrp:
                    self.log.warning(f"Subgroup '{subgroup}' not found")
                continue

            domain = row["GENERAL_DOMAIN_CLASS"]
            item_cols = [
                "specimen",
                "SDTM_DOMAIN",
                "sdtm_cat",
                "sdtm_sub_cat",
                "unit_dimension",
                "laterality",
                "location",
                "std_unit",
                "sdtm_variable",
                "sdtm_variable_name",
            ]
            item_data = []
            for col in item_cols:
                value = row[col]
                if col == "sdtm_variable_name":
                    sdtm_codelist = row["stdm_codelist_name"]
                else:
                    sdtm_codelist = row["stdm_codelist"]
                if not value:
                    continue
                if "|" in value:
                    items = value.split("|")
                else:
                    items = [value]
                data = self._create_activity_item(
                    items, col, domain, terms_for_item_classes, sdtm_codelist
                )
                if not data:
                    continue
                existing_for_class = next(
                    (
                        existing
                        for existing in item_data
                        if self._are_items_same_class(data, existing)
                    ),
                    None,
                )
                if existing_for_class:
                    self._append_item_terms_or_units(existing_for_class, data)
                else:
                    item_data.append(data)

            # find related Activity Instance Class
            sub_domain_class = row["sub_domain_class"]
            instance_class_name = sub_domain_class.title().replace(" ", "")
            activity_instance_class_uid = all_activity_instance_classes.get(
                instance_class_name
            )
            if not activity_instance_class_uid:
                # The activity instance type was not recognized
                self.log.warning(
                    f"Activity instance '{activity_instance_name}' has an unknown domain class '{sub_domain_class}'"
                )
                continue
            # WIP, column names in data file are preliminary:
            # - nci_concept_id
            # - is_required_for_activity
            # - is_default_selected_for_activity
            # - is_data_sharing
            # - is_legacy_usage
            data = {
                "path": ACTIVITY_INSTANCES_PATH,
                "approve_path": ACTIVITY_INSTANCES_PATH,
                "body": {
                    "activity_instance_class_uid": activity_instance_class_uid,
                    "name": activity_instance_name,
                    "name_sentence_case": activity_instance_name.lower(),
                    "definition": row.get("definition") or "TBD",
                    "adam_param_code": row["adam_param_code"] or None,
                    "activity_groupings": activity_groupings,
                    "activity_items": item_data,
                    "legacy_description": row["legacy_description"] or None,
                    "topic_code": row["TOPIC_CD"] or None,
                    "library_name": "Sponsor",
                    "nci_concept_id": row.get("nci_concept_id") or None,
                    "is_required_for_activity": map_boolean(
                        row.get("is_required_for_activity")
                    ),
                    "is_default_selected_for_activity": map_boolean(
                        row.get("is_default_selected_for_activity")
                    ),
                    "is_data_sharing": map_boolean(
                        row.get("is_data_sharing"), default=True
                    ),
                    "is_legacy_usage": map_boolean(row.get("is_legacy_usage")),
                },
            }
            if activity_instance_name not in all_data:
                # This is a new activity instance
                all_data[activity_instance_name] = data
            else:
                # This activity instance already exists, add more data to it
                current_activity_items = all_data[activity_instance_name]["body"][
                    "activity_items"
                ]
                # Items
                for activity_item in item_data:
                    existing_for_class = next(
                        (
                            existing
                            for existing in current_activity_items
                            if self._are_items_same_class(activity_item, existing)
                        ),
                        None,
                    )
                    if existing_for_class:
                        # There is already an activity item of this class, add any new units or terms to it
                        self._append_item_terms_or_units(
                            existing_for_class, activity_item
                        )
                    else:
                        current_activity_items.append(activity_item)
                # Groupings
                current_groupings = all_data[activity_instance_name]["body"][
                    "activity_groupings"
                ]
                for grouping in data["body"]["activity_groupings"]:
                    if grouping not in current_groupings:
                        current_groupings.append(grouping)

        for activity_instance_name, activity_instance_data in all_data.items():

            # Convert the sets to lists, needed for json serialization
            for item in activity_instance_data["body"]["activity_items"]:
                item["ct_term_uids"] = list(item["ct_term_uids"])
                item["unit_definition_uids"] = list(item["unit_definition_uids"])

            topic_code = activity_instance_data["body"]["topic_code"]
            if (
                activity_instance_name not in existing_rows_by_name
                and topic_code not in existing_rows_by_tc
            ):
                self.log.info(f"Adding activity instance '{activity_instance_name}'")
                api_tasks.append(
                    self.api.post_then_approve(
                        data=activity_instance_data, session=session, approve=True
                    )
                )
            elif (
                activity_instance_name in existing_rows_by_name
                and existing_rows_by_name[activity_instance_name]["topic_code"]
                != topic_code
            ):
                self.log.warning(
                    f"Not adding activity instance for topic code {topic_code}"
                    f" since instance with name {activity_instance_name} already exists"
                    f" with different topic code {existing_rows_by_name[activity_instance_name]['topic_code']}"
                )
            elif not self.are_instances_equal(
                activity_instance_data["body"], existing_rows_by_tc[topic_code]
            ):
                self.log.info(f"Patch activity instance '{activity_instance_name}'")
                activity_instance_data["patch_path"] = path_join(
                    ACTIVITY_INSTANCES_PATH,
                    existing_rows_by_tc[topic_code].get("uid"),
                )
                activity_instance_data["new_path"] = path_join(
                    ACTIVITY_INSTANCES_PATH,
                    existing_rows_by_tc[topic_code].get("uid"),
                    "versions",
                )
                activity_instance_data["body"][
                    "change_description"
                ] = "Migration modification"
                api_tasks.append(
                    self.api.new_version_patch_then_approve(
                        data=activity_instance_data, session=session, approve=True
                    )
                )
            else:
                self.log.info(
                    f"Identical activity instance '{activity_instance_name}' already exists"
                )
        await asyncio.gather(*api_tasks)

    # Get the item class for combination of column name and domain
    def _get_item_class(self, col, domain):
        if col == "specimen":
            return "specimen"
        if col == "SDTM_DOMAIN":
            return "domain"
        if col == "location":
            return "location"
        if col == "laterality":
            return "laterality"
        if col == "unit_dimension":
            return "unit_dimension"
        if col == "sdtm_cat":
            if domain == "FINDINGS":
                return "finding_category"
            if domain == "EVENTS":
                return "event_category"
            if domain == "INTERVENTIONS":
                return "intervention_category"
        if col == "sdtm_sub_cat":
            if domain == "FINDINGS":
                return "finding_subcategory"
            if domain == "EVENTS":
                return "event_subcategory"
            if domain == "INTERVENTIONS":
                return "intervention_subcategory"
        if col == "sdtm_variable" and domain == "FINDINGS":
            return "test_code"
        if col == "sdtm_variable_name" and domain == "FINDINGS":
            return "test_name"
        if col == "std_unit":
            return "standard_unit"

    # Helper to create a single activity item
    def _create_activity_item(
        self, items, column, domain, terms_for_item_classes, sdtm_codelist
    ):
        item_class = self._get_item_class(column, domain)
        if not item_class:
            return
        unit_uids = set()
        term_uids = set()
        for item in items:
            if item == "":
                continue
            if item_class in ["standard_unit"]:
                unit_uid = self.all_units.get(item)
                if unit_uid:
                    self.log.info(f"Activity item '{item}' found unit def '{unit_uid}'")
                    unit_uids.add(unit_uid)
                else:
                    self.log.warning(
                        f"Activity item '{item}' could not find unit definition"
                    )
            else:
                if item_class == "finding_category":
                    submval = item + " FIND_CAT"
                elif item_class == "finding_subcategory":
                    submval = item + " FIND_SUB_CAT"
                elif item_class == "intervention_category":
                    submval = item + " INTRV_CAT"
                elif item_class == "intervention_subcategory":
                    submval = item + " INTRV_SUB_CAT"
                elif item_class == "event_category":
                    submval = item + " EVNT_CAT"
                elif item_class == "event_subcategory":
                    submval = item + " EVNT_SUB_CAT"
                else:
                    submval = item
                if column == "sdtm_cat" and item in self.sdtm_cats:
                    term_uid = self.sdtm_cats[item]
                    self.log.info(
                        f"Activity item '{item}' found underlying ct term with uid '{term_uid}' for item class '{item_class}'"
                    )
                    term_uids.add(term_uid)
                elif column == "sdtm_sub_cat" and item in self.sdtm_subcats:
                    term_uid = self.sdtm_subcats[item]
                    self.log.info(
                        f"Activity item '{item}' found underlying ct term with uid '{term_uid}' for item class '{item_class}'"
                    )
                    term_uids.add(term_uid)
                elif item_class in terms_for_item_classes:
                    terms = terms_for_item_classes[item_class]
                    if submval in terms:
                        term_uid = terms[submval]
                        self.log.info(
                            f"Activity item '{item}' found underlying ct term with uid '{term_uid}' for item class '{item_class}'"
                        )
                        term_uids.add(term_uid)
                    else:
                        self.log.warning(
                            f"Activity item '{item}' from column '{column}' can't find underlying ct term for item class '{item_class}'"
                        )
                        continue
                elif column in ["sdtm_variable", "sdtm_variable_name"]:
                    if sdtm_codelist not in self.terms_for_codelist_submval:
                        self.log.info(
                            f"Fetching terms for codelist with submission value '{sdtm_codelist}'"
                        )
                        cl_terms = self._get_submissionvalues_for_codelist(
                            sdtm_codelist
                        )
                        if cl_terms is not None and len(cl_terms) == 0:
                            cl_terms = None
                        self.terms_for_codelist_submval[sdtm_codelist] = cl_terms

                    available_terms = self.terms_for_codelist_submval[sdtm_codelist]
                    if available_terms is None:
                        self.log.warning(
                            f"Activity item '{item}' can't find codelist '{sdtm_codelist}' for item class '{item_class}'"
                        )
                        continue
                    if submval in available_terms:
                        term_uid = available_terms[submval]
                        self.log.info(
                            f"Activity item '{item}' found ct term for SDTM variable with submval '{submval}' with uid '{term_uid}' in codelist '{sdtm_codelist}' for item class '{item_class}'"
                        )
                        term_uids.add(term_uid)
                    else:
                        self.log.warning(
                            f"Activity item '{item}' can't find ct term for SDTM variable with submval '{submval}' in codelist '{sdtm_codelist}' for item class '{item_class}'"
                        )
                        continue
                else:
                    self.log.warning(
                        f"Activity item '{item}' from column '{column}' can't find underlying ct term for item class '{item_class}'"
                    )
                    continue
        item_data = {
            "activity_item_class_uid": self.all_activity_item_classes.get(item_class),
            "ct_term_uids": set(),
            "unit_definition_uids": set(),
            "is_adam_param_specific": False,
        }
        if len(unit_uids) > 0 and len(term_uids) > 0:
            self.log.warning(
                f"Activity Item '{items}' can't link both to CTTerm and UnitDefinition, ignoring the units"
            )
        if len(term_uids) > 0:
            item_data["ct_term_uids"] = term_uids
        elif len(unit_uids) > 0:
            item_data["unit_definition_uids"] = unit_uids
        else:
            self.log.warning(
                f"Activity Items '{items}' could not be linked with any related nodes like CTTerm or UnitDefinition"
            )
        if item_data["activity_item_class_uid"] is None:
            self.log.warning(
                f"Activity Items '{items}' have unknown item class '{item_class}'"
            )
            return
        return item_data

    def _are_items_equal(self, new, existing):
        result = (
            existing.get("activity_item_class_uid")
            == new.get("activity_item_class_uid")
            and existing.get("unit_definition_uids") == new.get("unit_definition_uids")
            and existing.get("ct_term_uids") == new.get("ct_term_uids")
        )
        return result

    def _are_items_same_class(self, new, existing):
        return existing.get("activity_item_class_uid") == new.get(
            "activity_item_class_uid"
        )

    def _append_item_terms_or_units(self, existing, additional):
        if not self._are_items_same_class(additional, existing):
            raise RuntimeError(
                f"Trying to merge two items of different classes '{existing['activity_item_class_uid']}' and '{additional['activity_item_class_uid']}'"
            )
        existing["unit_definition_uids"] = (
            existing["unit_definition_uids"] | additional["unit_definition_uids"]
        )
        existing["ct_term_uids"] = existing["ct_term_uids"] | additional["ct_term_uids"]

    async def async_run(self):

        mdr_migration_activity_instances = load_env("MDR_MIGRATION_ACTIVITY_INSTANCES")
        mdr_migration_activity_instance_classes = load_env(
            "MDR_MIGRATION_ACTIVITY_INSTANCE_CLASSES"
        )
        mdr_migration_activity_item_classes = load_env(
            "MDR_MIGRATION_ACTIVITY_ITEM_CLASSES"
        )

        timeout = aiohttp.ClientTimeout(None)
        conn = aiohttp.TCPConnector(limit=4, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
            if (
                self._limit_import_to is None
                or ACTIVITY_GROUPS in self._limit_import_to
            ):
                await self.handle_activity_groups(
                    mdr_migration_activity_instances, session
                )
            else:
                self.log.info("Skipping activity groups import")

            if (
                self._limit_import_to is None
                or ACTIVITY_SUBGROUPS in self._limit_import_to
            ):
                await self.handle_activity_subgroups(
                    mdr_migration_activity_instances, session
                )
            else:
                self.log.info("Skipping activity subgroups import")

            # The full import may time a while, we refresh the auth token between steps
            # to make sure it does not expire while the import is running.

            if self._limit_import_to is None or ACTIVITIES in self._limit_import_to:
                self.refresh_auth()
                await self.handle_activities(mdr_migration_activity_instances, session)
            else:
                self.log.info("Skipping activities import")

            if (
                self._limit_import_to is None
                or ACTIVITY_INSTANCE_CLASSES in self._limit_import_to
            ):
                self.refresh_auth()
                await self.handle_activity_instance_classes(
                    mdr_migration_activity_instance_classes, session
                )
                await self.handle_activity_instance_class_parent_relationship(
                    mdr_migration_activity_instance_classes, session
                )
            else:
                self.log.info("Skipping activity instance classes import")

            if (
                self._limit_import_to is None
                or ACTIVITY_ITEM_CLASSES in self._limit_import_to
            ):
                self.refresh_auth()
                await self.handle_activity_item_classes(
                    mdr_migration_activity_item_classes, session
                )
            else:
                self.log.info("Skipping activity item classes import")

            if (
                self._limit_import_to is None
                or ACTIVITY_INSTANCES in self._limit_import_to
            ):
                self.refresh_auth()
                await self.handle_activity_instances(
                    mdr_migration_activity_instances, session
                )
            else:
                self.log.info("Skipping activity instances import")

    def run(self):
        self.log.info("Importing activities")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_run())
        self.log.info("Done importing activities")


def main(limit=None):
    metr = Metrics()
    migrator = Activities(metrics_inst=metr)
    migrator.limit_import_to(limit)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="run_import_activities.py")
    parser.add_argument(
        "-l",
        "--limit",
        nargs="*",
        choices=[
            ACTIVITIES,
            ACTIVITY_GROUPS,
            ACTIVITY_SUBGROUPS,
            ACTIVITY_INSTANCES,
            ACTIVITY_ITEM_CLASSES,
            ACTIVITY_INSTANCE_CLASSES,
        ],
    )
    args = parser.parse_args()
    main(limit=args.limit)
