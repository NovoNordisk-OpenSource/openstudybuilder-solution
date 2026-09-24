import asyncio
import csv
import json
from functools import lru_cache

import aiohttp

from importers.functions.caselessdict import CaselessDict
from importers.functions.parsers import map_boolean
from importers.functions.utils import load_env
from importers.utils.importer import BaseImporter, open_file_async
from importers.utils.metrics import Metrics
from importers.utils.path_join import path_join

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

# Column names in activity instances CSV
COL_GROUP = "Assm. group"
COL_SUBGROUP = "Assm. subgroup"
COL_ACTIVITY = "activity"
COL_ACTIVITY_INSTANCE = "activity_instance"
COL_SUB_DOMAIN_CLASS = "sub_domain_class"
COL_DEFINITION = "definition"
COL_ADAM_PARAM_CODE = "adam_param_code"
COL_LEGACY_DESCRIPTION = "legacy_description"
COL_TOPIC_CODE = "TOPIC_CD"
COL_NCI_CONCEPT_ID = "nci_concept_id"
COL_IS_REQUIRED_FOR_ACTIVITY = "is_required_for_activity"
COL_IS_DEFAULT_SELECTED_FOR_ACTIVITY = "is_default_selected_for_activity"
COL_IS_DATA_SHARING = "is_data_sharing"
COL_IS_LEGACY_USAGE = "is_legacy_usage"

NULL_DEFINITIONS = ("", "TBD", "null")


class ConflictingItemError(ValueError):
    pass


# Activities with instances, groups and subgroups in sponsor library
class Activities(BaseImporter):
    logging_name = "activities"

    def __init__(self, api=None, metrics_inst=None):
        super().__init__(api=api, metrics_inst=metrics_inst)
        self._limit_import_to = None

    def compare_properties(self, new, existing, properties_to_compare):
        for prop_name in properties_to_compare:
            if prop_name not in existing and prop_name.endswith("_uid"):
                # For properties ending with _uid, the existing value is nested
                existing_prop_name = prop_name[0:-4]
                existing_value = existing.get(existing_prop_name, {}).get("uid")
            else:
                existing_value = existing.get(prop_name)

            # Treat empty or "TBD" definitions as None to avoid unnecessary updates
            if prop_name == "definition" and existing_value in NULL_DEFINITIONS:
                existing_value = None
            new_value = new.get(prop_name)
            if existing_value != new_value:
                self.log.debug(
                    f"Difference found in property '{prop_name}': Existing='{existing_value}', New='{new_value}'"
                )
                return False
        return True

    def limit_import_to(self, limit):
        if limit is not None:
            self.log.info(f"Limiting import to: {', '.join(limit)}")
        else:
            self.log.info("Importing all activity content")
        self._limit_import_to = limit

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

    @lru_cache(maxsize=10000)
    def _get_codelist_submval(self, cl_uid):
        cl = self.api.get_all_from_api(f"/ct/codelists/{cl_uid}/attributes")
        return cl.get("submission_value")

    @lru_cache(maxsize=10000)
    def fetch_codelist_terms(self, cl_uid):
        cl_terms = self.api.get_all_from_api(f"/ct/codelists/{cl_uid}/terms")
        return cl_terms

    # Get all terms from a codelist identified by its submission value
    def _get_codelist_terms(self, codelist_submval):
        all_codelist_uids = self._get_codelists_uid_and_submval()
        cl_uid = all_codelist_uids.get(codelist_submval)
        terms = self.api.get_all_from_api(f"/ct/codelists/{cl_uid}/terms")
        return terms

    # Get a dictionary mapping submission values to term uids for a codelist identified by its submission value
    def _get_submissionvalues_for_codelist(self, cl):
        terms = self._get_codelist_terms(cl)
        submvals = CaselessDict(
            self.api.get_all_identifiers(
                terms,
                identifier="submission_value",
                value="term_uid",
            )
        )
        return submvals

    # Get a dictionary of terms for the most common SDTM variable codelists
    def _get_terms_for_codelist_submvals(self):
        self.log.info("Fetching terms for common sdtm variable codelists")
        codelists = ["FATESTCD", "LBTESTCD", "VSTESTCD", "PROTMLST", "RPTESTCD"]

        result = {"NO_LINKAGE_NEEDED": []}
        for cd in codelists:
            result[cd] = self._get_submissionvalues_for_codelist(cd)
        self.terms_for_codelist_submval = result

    @open_file_async()
    async def handle_activity_groups_or_subgroups(self, csvfile, session, group_type):
        # Populate then activity groups in sponsor library
        csv_data = csv.DictReader(csvfile)
        api_tasks = []

        if group_type == "group":
            col_name = COL_GROUP
            api_endpoint = ACTIVITY_GROUPS_PATH
        elif group_type == "subgroup":
            col_name = COL_SUBGROUP
            api_endpoint = ACTIVITY_SUBGROUPS_PATH
        else:
            raise ValueError("group_type must be either 'group' or 'subgroup'")

        existing_rows = self.api.get_all_identifiers(
            self.api.get_all_from_api(api_endpoint),
            identifier="name",
            value="uid",
        )

        unique_items = {}
        for row in csv_data:
            item_name = row[col_name].strip()
            if item_name and item_name not in unique_items:
                unique_items[item_name] = {
                    "name": item_name,
                    "name_sentence_case": item_name.lower(),
                    "definition": None,
                    "library_name": "Sponsor",
                }

        for _key, itemdata in unique_items.items():
            data = {
                "path": api_endpoint,
                "approve_path": api_endpoint,
                "body": itemdata,
            }
            if not existing_rows.get(data["body"]["name"]):
                self.log.info(
                    f"Add activity {group_type} '{data['body']['name']}' to library '{data['body']['library_name']}'"
                )
                api_tasks.append(
                    self.api.post_then_approve(data=data, session=session, approve=True)
                )  # TODO Verify if activity groups can be approved?
            else:
                # Already exists, skip.
                # Do we need patch functionality here?
                self.log.info(
                    f"Activity {group_type} '{data['body']['name']}' already exists in library '{data['body']['library_name']}'"
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
        if new_groupings == old_groupings:
            self.log.info("Groupings are equal")
            return True
        elif new_groupings <= old_groupings:
            self.log.info(
                "New groupings are a subset of old groupings, no changes needed"
            )
            return True
        self.log.info("Groupings are not equal")
        return False

    def _are_activities_equal(self, old, new):
        existing_groupings = old["activity_groupings"]
        new_groupings = new["activity_groupings"]

        # Treat empty or "TBD" definitions as None to avoid unnecessary updates
        old_definition = old.get("definition")
        if old_definition in NULL_DEFINITIONS:
            old_definition = None

        return (
            old.get("nci_concept_id") == new.get("nci_concept_id")
            and old.get("is_data_collected") == new.get("is_data_collected")
            and old.get("name_sentence_case") == new.get("name_sentence_case")
            and old_definition == new.get("definition")
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
                "definition": item["definition"] or None,
                "activity_groupings": item["activity_groupings"],
                "library_name": item["library_name"],
                "status": item["status"],
            }

        api_tasks = []

        unique_activities = {}

        for row in csv_data:
            activity_name = row[COL_ACTIVITY].strip()
            group_name = row[COL_GROUP].strip()
            subgroup_name = row[COL_SUBGROUP].strip()

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
                    # Merge new groupings with existing groupings before patching.
                    updated_groupings = []
                    for grouping in existing["activity_groupings"]:
                        updated_groupings.append(
                            {
                                "activity_group_uid": grouping["activity_group_uid"],
                                "activity_subgroup_uid": grouping[
                                    "activity_subgroup_uid"
                                ],
                            }
                        )
                    for grouping in item_data["activity_groupings"]:
                        if grouping not in updated_groupings:
                            updated_groupings.append(grouping)
                    data["body"]["activity_groupings"] = updated_groupings
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
            new_is_specific = map_boolean(new.get("is_domain_specific"), default=False)

            # Treat empty or "TBD" definitions as None to avoid unnecessary updates
            existing_definition = existing.get("definition")
            if existing_definition in NULL_DEFINITIONS:
                existing_definition = None

            result = (
                existing_parent_uid == new_parent_uid
                and existing.get("name") == new.get("name")
                and existing.get("level") == new.get("level")
                and existing.get("library_name") == new.get("library_name")
                and existing.get("is_domain_specific") == new_is_specific
                and existing_definition == new.get("definition")
                and existing.get("order") == new_order
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
                    "definition": row[headers.index("DEFINITION")] or None,
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
                        "definition": row[headers.index("DEFINITION")] or None,
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
                current_class = existing_rows.get(current_class_name)
                if current_class is not None:
                    current_uid = current_class.get("uid")
                    current_parent_uid = (current_class.get("parent_class") or {}).get(
                        "uid"
                    )
                else:
                    current_uid = None
                    current_parent_uid = None
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
                if current_parent_uid == parent_uid:
                    self.log.info(
                        f"Activity instance class '{current_class_name}' already connected to parent '{parent_class_name}'"
                    )
                else:
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
            _new = sorted(
                new.get("activity_instance_classes") or [],
                key=lambda x: x.get("name", ""),
            )
            _existing = sorted(
                existing.get("activity_instance_classes") or [],
                key=lambda x: x.get("name", ""),
            )
            return _new == _existing

        properties_to_compare = [
            "name",
            "display_name",
            "library_name",
            "mandatory",
            "definition",
            "nci_concept_id",
            "order",
            "role_uid",
            "data_type_uid",
        ]

        if self.compare_properties(new, existing, properties_to_compare) is False:
            self.log.debug("Difference found in basic properties")
            return False
        if not are_instance_classes_equal():
            self.log.debug(
                "Instance classes are not equal ; either the list is different, or attached properties are"
            )
            return False

        return True

    @open_file_async()
    async def handle_activity_item_classes(self, csvfile, session):
        # Populate the activity item classes in sponsor library
        readCSV = csv.DictReader(csvfile, delimiter=",")
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

        semantic_roles = self.api.get_all_identifiers(
            self._get_codelist_terms("ROLE"),
            identifier="submission_value",
            value="term_uid",
        )
        data_types = self.api.get_all_identifiers(
            self._get_codelist_terms("DATATYPE"),
            identifier="submission_value",
            value="term_uid",
        )

        activity_item_data = {}
        for row in readCSV:
            activity_instance_class_name = row["ACTIVITY_INSTANCE_CLASS"]
            instance_class_uid = available_instance_classes.get(
                activity_instance_class_name
            )
            role = row["SEMANTIC_ROLE"]
            if role in semantic_roles:
                role_uid = semantic_roles[role]
            else:
                self.log.warning(
                    f"The role ({role}) wasn't found for the following ActivityInstanceClass ({activity_instance_class_name})"
                )
                continue
            data_type = row["SEMANTIC_DATA_TYPE"]
            if data_type in data_types:
                data_type_uid = data_types[data_type]
            else:
                self.log.warning(
                    f"The data_type ({data_type}) wasn't found for the following ActivityInstanceClass ({activity_instance_class_name})"
                )
                continue
            activity_item_class_name = row["ACTIVITY_ITEM_CLASS"]
            if instance_class_uid is None:
                self.log.warning(
                    f"Activity instance class '{activity_instance_class_name}' "
                    f"wasn't found in available activity instance classes in the db"
                )
                continue

            order = int(row["ORDER"]) if row["ORDER"] else None

            data = {
                "path": ACTIVITY_ITEM_CLASSES_PATH,
                "approve_path": ACTIVITY_ITEM_CLASSES_PATH,
                "body": {
                    "name": activity_item_class_name,
                    "display_name": row["DISPLAY_LABEL"],
                    "order": order,
                    "definition": (
                        row["DEFINITION"].strip() if row["DEFINITION"] else None
                    ),
                    "nci_concept_id": row["NCI_C_CODE"] or None,
                    "activity_instance_classes": [
                        {
                            "uid": instance_class_uid,
                            "name": activity_instance_class_name,
                            "mandatory": map_boolean(row["MANDATORY"]),
                            "is_adam_param_specific_enabled": map_boolean(
                                row["IS_ADAM_PARAM_SPECIFIC_ENABLED"]
                            ),
                            "is_additional_optional": map_boolean(
                                row["ADDITIONAL_OPTIONAL_ACTIVITY_ITEM"]
                            ),
                            "is_default_linked": map_boolean(
                                row["DEFAULT_LINKED_TO_INSTANCE"]
                            ),
                        }
                    ],
                    "activity_instance_class_names": [activity_instance_class_name],
                    "role_uid": role_uid,
                    "data_type_uid": data_type_uid,
                    "library_name": "Sponsor",
                },
            }
            if activity_item_class_name not in activity_item_data:
                activity_item_data[activity_item_class_name] = data
            else:
                self.log.info(
                    f"Trying to link {activity_item_class_name} "
                    f"to additional instance class {activity_instance_class_name}"
                )
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
                            "mandatory": map_boolean(row["MANDATORY"]),
                            "is_adam_param_specific_enabled": map_boolean(
                                row["IS_ADAM_PARAM_SPECIFIC_ENABLED"]
                            ),
                            "is_additional_optional": map_boolean(
                                row["ADDITIONAL_OPTIONAL_ACTIVITY_ITEM"]
                            ),
                            "is_default_linked": map_boolean(
                                row["DEFAULT_LINKED_TO_INSTANCE"]
                            ),
                        }
                    )
                    activity_item_data[activity_item_class_name]["body"][
                        "activity_instance_class_names"
                    ].append(activity_instance_class_name)

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

    def _normalize_instance_item(self, item):
        activity_item_class_uid = item.get("activity_item_class_uid") or (
            item.get("activity_item_class") or {}
        ).get("uid")

        unit_definition_uids = item.get("unit_definition_uids")
        if unit_definition_uids is None:
            unit_definition_uids = [
                unit.get("uid") for unit in item.get("unit_definitions", [])
            ]

        term_uids = item.get("ct_term_uids")
        if term_uids is None:
            term_uids = []
            for term in item.get("ct_terms", []):
                term_uid = term.get("term_uid") or term.get("uid")
                if term_uid:
                    term_uids.append(term_uid)

        return (
            activity_item_class_uid,
            frozenset(term_uids),
            frozenset(uid for uid in unit_definition_uids if uid is not None),
        )

    def compare_instance_items(self, old, new):
        new_items = {self._normalize_instance_item(item) for item in new}
        old_items = {self._normalize_instance_item(item) for item in old}
        return new_items == old_items

    def _normalize_instance_grouping(self, item):
        return (
            item.get("activity_uid") or (item.get("activity") or {}).get("uid"),
            item.get("activity_group_uid")
            or (item.get("activity_group") or {}).get("uid"),
            item.get("activity_subgroup_uid")
            or (item.get("activity_subgroup") or {}).get("uid"),
        )

    def compare_instance_groupings(self, old, new):
        # Convert both old and new to lists of tuples, (activity_uid, group_uid, subgroup_uid)
        # These are hashable so the lists can be made into sets for easy comparison
        new_groupings = {self._normalize_instance_grouping(item) for item in new}
        old_groupings = {self._normalize_instance_grouping(item) for item in old}
        return new_groupings == old_groupings

    def are_instance_attributes_equal(self, new, existing):
        # Define properties to compare directly
        properties_to_compare = [
            "activity_instance_class_uid",
            "library_name",
            "name_sentence_case",
            "definition",
            "adam_param_code",
            "legacy_description",
            "topic_code",
            "nci_concept_id",
            "is_required_for_activity",
            "is_default_selected_for_activity",
            "is_data_sharing",
            "is_legacy_usage",
        ]

        # Compare all properties
        if self.compare_properties(new, existing, properties_to_compare) is False:
            self.log.debug("Difference found in simple properties")
            return False

        # Compare complex structures
        if not self.compare_instance_items(
            existing.get("activity_items", []), new.get("activity_items", [])
        ):
            self.log.debug("Difference found in activity_items")
            return False

        return True

    def are_instance_groupings_equal(self, new, existing):
        if not self.compare_instance_groupings(
            existing.get("activity_groupings", []), new.get("activity_groupings", [])
        ):
            self.log.debug("Difference found in activity_groupings")
            return False

        return True

    def are_instances_equal(self, new, existing):
        return self.are_instance_attributes_equal(
            new, existing
        ) and self.are_instance_groupings_equal(new, existing)

    def _split_activity_instance_payload(self, body):
        attributes_payload = {
            key: value for key, value in body.items() if key != "activity_groupings"
        }
        groupings_payload = {"activity_groupings": body.get("activity_groupings", [])}
        return attributes_payload, groupings_payload

    async def _approve_activity_instance_part(
        self, activity_instance_name, activity_instance_uid, part, session
    ):
        part_path = path_join(
            ACTIVITY_INSTANCES_PATH, activity_instance_uid, part, "approvals"
        )
        status, _ = await self.api.approve_async(part_path, session=session)
        if status >= 400:
            self.log.error(
                f"Failed to approve activity instance '{activity_instance_name}' ({part})"
            )

    async def _post_and_approve_activity_instance(self, data, session):
        """Post a new activity instance and approve both attributes and groupings separately."""
        self.log.debug(f"Post to {data['path']}")
        status, response = await self.api.post_to_api_async(
            url=data["path"], body=data["body"], session=session
        )
        if status >= 400:
            error_message = (
                response.get("message") or response.get("detail") or str(response)
            )
            name = data["body"].get("name", str(data["body"]))
            self.log.error(
                f"Failed to post '{name}' to '{data['path']}', error: {error_message}"
            )
            return
        uid = response.get("uid")
        if uid is None:
            self.log.error("No uid returned, unable to approve")
            return response
        activity_instance_name = data["body"].get("name", uid)
        await self._approve_activity_instance_part(
            activity_instance_name, uid, "attributes", session
        )
        await self._approve_activity_instance_part(
            activity_instance_name, uid, "groupings", session
        )
        return response

    async def _patch_activity_instance_part(
        self,
        activity_instance_name,
        activity_instance_uid,
        part,
        payload,
        session,
    ):
        part_path = path_join(ACTIVITY_INSTANCES_PATH, activity_instance_uid, part)
        body = dict(payload)
        body["change_description"] = "Migration modification"

        status, response = await self.api.new_version_to_api_async(
            path=path_join(part_path, "versions"),
            session=session,
        )
        if status >= 400:
            error_message = (
                response.get("message") or response.get("detail") or str(response)
            )
            if "New draft version can be created only for FINAL versions" in str(
                error_message
            ):
                self.log.warning(
                    f"Skipping new {part} version for '{activity_instance_name}' because it is already in draft"
                )
            else:
                self.log.error(
                    f"Failed to create new {part} version for activity instance '{activity_instance_name}': {error_message}"
                )
                return

        status, response = await self.api.patch_to_api_async(
            path=part_path,
            body=body,
            session=session,
        )
        if status >= 400:
            error_message = (
                response.get("message") or response.get("detail") or str(response)
            )
            self.log.error(
                f"Failed to patch activity instance '{activity_instance_name}' ({part}): {error_message}"
            )
            return

        status, _ = await self.api.approve_async(
            path_join(part_path, "approvals"), session=session
        )
        if status >= 400:
            self.log.error(
                f"Failed to approve activity instance '{activity_instance_name}' ({part})"
            )

    async def _patch_activity_instance_parts(
        self,
        activity_instance_name,
        activity_instance_uid,
        attributes_payload,
        groupings_payload,
        patch_attributes,
        patch_groupings,
        session,
    ):
        if not patch_attributes and not patch_groupings:
            self.log.info(
                f"Identical activity instance '{activity_instance_name}' already exists"
            )
            return

        if patch_attributes:
            self.log.info(
                f"Patch activity instance attributes '{activity_instance_name}'"
            )
            await self._patch_activity_instance_part(
                activity_instance_name=activity_instance_name,
                activity_instance_uid=activity_instance_uid,
                part="attributes",
                payload=attributes_payload,
                session=session,
            )

        if patch_groupings:
            self.log.info(
                f"Patch activity instance groupings '{activity_instance_name}'"
            )
            await self._patch_activity_instance_part(
                activity_instance_name=activity_instance_name,
                activity_instance_uid=activity_instance_uid,
                part="groupings",
                payload=groupings_payload,
                session=session,
            )

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
            activity_instance_name = row[COL_ACTIVITY_INSTANCE].strip()
            activity = row[COL_ACTIVITY].strip()
            group = row[COL_GROUP].strip()
            subgroup = row[COL_SUBGROUP].strip()
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

            # find related Activity Instance Class
            sub_domain_class = row[COL_SUB_DOMAIN_CLASS]
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
                    "definition": row.get(COL_DEFINITION) or None,
                    "adam_param_code": row[COL_ADAM_PARAM_CODE] or None,
                    "activity_groupings": activity_groupings,
                    "activity_items": [],  # activity items are imported by run_update_activity_instance_activity_items.py
                    "legacy_description": row[COL_LEGACY_DESCRIPTION] or None,
                    "topic_code": row[COL_TOPIC_CODE] or None,
                    "library_name": "Sponsor",
                    "nci_concept_id": row.get(COL_NCI_CONCEPT_ID) or None,
                    "is_required_for_activity": map_boolean(
                        row.get(COL_IS_REQUIRED_FOR_ACTIVITY)
                    ),
                    "is_default_selected_for_activity": map_boolean(
                        row.get(COL_IS_DEFAULT_SELECTED_FOR_ACTIVITY)
                    ),
                    "is_data_sharing": map_boolean(
                        row.get(COL_IS_DATA_SHARING), default=True
                    ),
                    "is_legacy_usage": map_boolean(row.get(COL_IS_LEGACY_USAGE)),
                },
            }
            if activity_instance_name not in all_data:
                # This is a new activity instance
                all_data[activity_instance_name] = data
            else:
                # This activity instance already exists, add more data to it
                # Groupings
                current_groupings = all_data[activity_instance_name]["body"][
                    "activity_groupings"
                ]
                for grouping in data["body"]["activity_groupings"]:
                    if grouping not in current_groupings:
                        current_groupings.append(grouping)

        for activity_instance_name, activity_instance_data in all_data.items():

            topic_code = activity_instance_data["body"]["topic_code"]
            if (
                activity_instance_name not in existing_rows_by_name
                and topic_code not in existing_rows_by_tc
            ):
                self.log.info(f"Adding activity instance '{activity_instance_name}'")
                api_tasks.append(
                    self._post_and_approve_activity_instance(
                        data=activity_instance_data, session=session
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
            else:
                existing_instance = existing_rows_by_tc.get(topic_code)
                if existing_instance is None:
                    self.log.warning(
                        f"Cannot patch activity instance '{activity_instance_name}' because no existing instance was found for topic code '{topic_code}'"
                    )
                    continue
                existing_uid = existing_instance.get("uid")

                patch_attributes = not self.are_instance_attributes_equal(
                    activity_instance_data["body"], existing_instance
                )
                patch_groupings = not self.are_instance_groupings_equal(
                    activity_instance_data["body"], existing_instance
                )

                if patch_attributes or patch_groupings:
                    attributes_payload, groupings_payload = (
                        self._split_activity_instance_payload(
                            activity_instance_data["body"]
                        )
                    )
                    api_tasks.append(
                        self._patch_activity_instance_parts(
                            activity_instance_name=activity_instance_name,
                            activity_instance_uid=existing_uid,
                            attributes_payload=attributes_payload,
                            groupings_payload=groupings_payload,
                            patch_attributes=patch_attributes,
                            patch_groupings=patch_groupings,
                            session=session,
                        )
                    )
                else:
                    self.log.info(
                        f"Identical activity instance '{activity_instance_name}' already exists"
                    )
        await asyncio.gather(*api_tasks)

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
            # Activity Groups
            if (
                self._limit_import_to is None
                or ACTIVITY_GROUPS in self._limit_import_to
            ):
                await self.handle_activity_groups_or_subgroups(
                    mdr_migration_activity_instances, session, "group"
                )
            else:
                self.log.info("Skipping activity groups import")

            # Activity Subgroups
            if (
                self._limit_import_to is None
                or ACTIVITY_SUBGROUPS in self._limit_import_to
            ):
                await self.handle_activity_groups_or_subgroups(
                    mdr_migration_activity_instances, session, "subgroup"
                )
            else:
                self.log.info("Skipping activity subgroups import")

            # The full import may time a while, we refresh the auth token between steps
            # to make sure it does not expire while the import is running.

            # Activities
            if self._limit_import_to is None or ACTIVITIES in self._limit_import_to:
                await self.handle_activities(mdr_migration_activity_instances, session)
            else:
                self.log.info("Skipping activities import")

            # Activity Instance Classes
            if (
                self._limit_import_to is None
                or ACTIVITY_INSTANCE_CLASSES in self._limit_import_to
            ):
                await self.handle_activity_instance_classes(
                    mdr_migration_activity_instance_classes, session
                )
                await self.handle_activity_instance_class_parent_relationship(
                    mdr_migration_activity_instance_classes, session
                )
            else:
                self.log.info("Skipping activity instance classes import")

            # Activity Item Classes
            if (
                self._limit_import_to is None
                or ACTIVITY_ITEM_CLASSES in self._limit_import_to
            ):
                await self.handle_activity_item_classes(
                    mdr_migration_activity_item_classes, session
                )
            else:
                self.log.info("Skipping activity item classes import")

            # Activity Instances
            if (
                self._limit_import_to is None
                or ACTIVITY_INSTANCES in self._limit_import_to
            ):
                await self.handle_activity_instances(
                    mdr_migration_activity_instances, session
                )
            else:
                self.log.info("Skipping activity instances import")

    def run(self):
        self.log.info("Importing activities")
        asyncio.run(self.async_run())
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
