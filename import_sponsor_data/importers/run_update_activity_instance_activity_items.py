import asyncio
import csv
import json
from collections import defaultdict

import aiohttp

from importers.functions.parsers import map_boolean
from importers.functions.utils import load_env
from importers.utils.importer import BaseImporter, open_file_async
from importers.utils.metrics import Metrics
from importers.utils.path_join import path_join

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
API_BASE_URL = load_env("API_BASE_URL")


ACTIVITY_INSTANCES_PATH = "/concepts/activities/activity-instances"


class ActivityInstanceActivityItems(BaseImporter):
    logging_name = "activity_instance_activity_items"

    def __init__(self, api=None, metrics_inst=None):
        super().__init__(api=api, metrics_inst=metrics_inst)

    async def _patch_attributes(
        self,
        activity_instance_name,
        activity_instance_uid,
        payload,
        session,
        status,
    ):
        part_path = path_join(
            ACTIVITY_INSTANCES_PATH, activity_instance_uid, "attributes"
        )
        body = dict(payload)
        body["change_description"] = "Import script updated activity items"

        if status == "Final":
            status_code, response = await self.api.new_version_to_api_async(
                path=path_join(part_path, "versions"),
                session=session,
            )
            if status_code >= 400:
                error_message = (
                    response.get("message") or response.get("detail") or str(response)
                )
                self.log.error(
                    f"Failed to create new attributes version for activity instance '{activity_instance_name}' ({activity_instance_uid}): {error_message}"
                )
                return

        status_code, response = await self.api.patch_to_api_async(
            path=part_path,
            body=body,
            session=session,
        )
        if status_code >= 400:
            error_message = (
                response.get("message") or response.get("detail") or str(response)
            )
            self.log.error(
                f"Failed to patch activity instance '{activity_instance_name}' ({activity_instance_uid}) (attributes): {error_message}"
            )
            return

        status_code, _ = await self.api.approve_async(
            path_join(part_path, "approvals"), session=session
        )
        if status_code >= 400:
            self.log.error(
                f"Failed to approve activity instance '{activity_instance_name}' ({activity_instance_uid}) (attributes)"
            )

    def _fetch_reference_data(self):
        """Fetch all lookup dictionaries needed for resolving activity item references."""
        activity_item_class_uid_by_name = self.api.get_all_identifiers(
            self.api.get_all_from_api("/activity-item-classes"),
            identifier="name",
            value="uid",
        )

        codelist_uid_by_submission_value = self.api.get_all_identifiers(
            self.api.get_all_from_api("/ct/codelists"),
            identifier="attributes.submission_value",
            value="codelist_uid",
        )

        all_terms = self.api.get_all_from_api("/ct/terms")
        term_uid_by_cl_and_submval = {}
        for term in all_terms:
            for ct_codelist in term.get("codelists", []):
                key = (
                    ct_codelist["codelist_submission_value"],
                    ct_codelist["submission_value"],
                )
                term_uid_by_cl_and_submval[key] = term["term_uid"]

        unit_uid_by_name = self.api.get_all_identifiers(
            self.api.get_all_from_api("/concepts/unit-definitions"),
            identifier="name",
            value="uid",
        )

        return {
            "activity_item_class_uid_by_name": activity_item_class_uid_by_name,
            "codelist_uid_by_submission_value": codelist_uid_by_submission_value,
            "term_uid_by_cl_and_submval": term_uid_by_cl_and_submval,
            "unit_uid_by_name": unit_uid_by_name,
        }

    def _build_activity_item(self, activity_item, activity_instance_name, ref_data):
        """Build a single activity item payload from a CSV row. Returns None if the item should be skipped."""
        activity_item_class_uid = ref_data["activity_item_class_uid_by_name"].get(
            activity_item["ACTIVITY_ITEM_CLASS_NAME"]
        )
        if not activity_item_class_uid:
            self.log.warning(
                f"Activity item class '{activity_item['ACTIVITY_ITEM_CLASS_NAME']}' not found for activity item in instance '{activity_instance_name}'"
            )
            return None

        ct_codelist_uid = None
        ct_terms = []
        unit_definition_uids = []
        text_value = None
        item_type = activity_item["ACTIVITY_ITEM_TYPE"]
        item_value = activity_item["ACTIVITY_ITEM_VALUE"]

        if item_type == "codelist":
            ct_codelist_uid = ref_data["codelist_uid_by_submission_value"].get(
                item_value
            )
            if not ct_codelist_uid:
                self.log.warning(
                    f"Codelist '{item_value}' not found for activity item in instance '{activity_instance_name}'"
                )
                return None
        elif item_type == "terms":
            ct_terms = self._resolve_terms(item_value, activity_instance_name, ref_data)
        elif item_type == "units":
            unit_definition_uids = self._resolve_units(
                item_value, activity_instance_name, ref_data
            )
        elif item_type == "text_value":
            text_value = item_value
        elif item_type == "" and item_value == "":
            pass
        else:
            self.log.warning(
                f"Unknown activity item type '{item_type}' for activity item in instance '{activity_instance_name}'"
            )
            return None

        return {
            "activity_item_class_uid": activity_item_class_uid,
            "ct_codelist_uid": ct_codelist_uid,
            "ct_terms": ct_terms,
            "unit_definition_uids": unit_definition_uids,
            "is_adam_param_specific": map_boolean(
                activity_item["IS_ADAM_PARAM_SPECIFIC"]
            ),
            "text_value": text_value,
        }

    def _resolve_terms(self, item_value, activity_instance_name, ref_data):
        codelist_submission_value, term_submission_values = item_value.split(
            ":", maxsplit=1
        )
        ct_terms = []
        for term in term_submission_values.split("|"):
            term_uid = ref_data["term_uid_by_cl_and_submval"].get(
                (codelist_submission_value, term)
            )
            if not term_uid:
                self.log.warning(
                    f"'{activity_instance_name}': Term submission value '{term}' with codelist submission value '{codelist_submission_value}'"
                    f" not found "
                )
                continue
            ct_terms.append(
                {
                    "term_uid": term_uid,
                    "codelist_uid": ref_data["codelist_uid_by_submission_value"][
                        codelist_submission_value
                    ],
                }
            )
        return ct_terms

    def _resolve_units(self, item_value, activity_instance_name, ref_data):
        unit_definition_uids = []
        for unit_name in item_value.split("|"):
            if unit_name not in ref_data["unit_uid_by_name"]:
                self.log.warning(
                    f"Unit '{unit_name}' not found for activity item in instance '{activity_instance_name}'"
                )
                continue
            unit_definition_uids.append(ref_data["unit_uid_by_name"][unit_name])
        return unit_definition_uids

    @staticmethod
    def _build_attributes_payload(existing_activity_instance, payload_activity_items):
        return {
            "activity_instance_class_uid": existing_activity_instance[
                "activity_instance_class"
            ]["uid"],
            "name": existing_activity_instance["name"],
            "name_sentence_case": existing_activity_instance["name_sentence_case"],
            "definition": existing_activity_instance["definition"],
            "adam_param_code": existing_activity_instance["adam_param_code"],
            "activity_items": payload_activity_items,
            "legacy_description": existing_activity_instance["legacy_description"],
            "topic_code": existing_activity_instance["topic_code"],
            "library_name": existing_activity_instance["library_name"],
            "nci_concept_id": existing_activity_instance["nci_concept_id"],
            "is_required_for_activity": existing_activity_instance[
                "is_required_for_activity"
            ],
            "is_default_selected_for_activity": existing_activity_instance[
                "is_default_selected_for_activity"
            ],
            "is_data_sharing": existing_activity_instance["is_data_sharing"],
            "is_legacy_usage": existing_activity_instance["is_legacy_usage"],
        }

    @staticmethod
    def _normalize_activity_item_for_patch(item):
        activity_item_class_uid = item.get("activity_item_class_uid") or (
            item.get("activity_item_class") or {}
        ).get("uid")

        ct_codelist_uid = item.get("ct_codelist_uid") or (
            item.get("ct_codelist") or {}
        ).get("codelist_uid")

        ct_terms = []
        for term in item.get("ct_terms", []):
            term_uid = term.get("term_uid") or term.get("uid")
            codelist_uid = term.get("codelist_uid") or (term.get("codelist") or {}).get(
                "codelist_uid"
            )
            if term_uid:
                ct_terms.append(
                    {
                        "term_uid": term_uid,
                        "codelist_uid": codelist_uid,
                    }
                )

        unit_definition_uids = item.get("unit_definition_uids")
        if unit_definition_uids is None:
            unit_definition_uids = [
                unit.get("uid")
                for unit in item.get("unit_definitions", [])
                if unit.get("uid")
            ]

        return {
            "activity_item_class_uid": activity_item_class_uid,
            "ct_codelist_uid": ct_codelist_uid,
            "ct_terms": ct_terms,
            "unit_definition_uids": unit_definition_uids,
            "is_adam_param_specific": item.get("is_adam_param_specific"),
            "text_value": item.get("text_value"),
        }

    @staticmethod
    def _activity_item_key(item):
        return item.get("activity_item_class_uid")

    @staticmethod
    def _activity_items_equal(left, right):
        def normalize_terms(terms):
            normalized = []
            for term in terms or []:
                normalized.append((term.get("term_uid"), term.get("codelist_uid")))
            return sorted(normalized)

        return (
            left.get("activity_item_class_uid") == right.get("activity_item_class_uid")
            and left.get("ct_codelist_uid") == right.get("ct_codelist_uid")
            and left.get("is_adam_param_specific")
            == right.get("is_adam_param_specific")
            and left.get("text_value") == right.get("text_value")
            and sorted(left.get("unit_definition_uids") or [])
            == sorted(right.get("unit_definition_uids") or [])
            and normalize_terms(left.get("ct_terms"))
            == normalize_terms(right.get("ct_terms"))
        )

    def _merge_activity_items(self, existing_items, imported_items):
        merged_items = [
            self._normalize_activity_item_for_patch(item)
            for item in (existing_items or [])
        ]

        # Map activity-item-class UID to the item position in merged_items.
        existing_index_by_key = {}
        for index, existing_item in enumerate(merged_items):
            activity_item_key = self._activity_item_key(existing_item)
            if activity_item_key is not None:
                existing_index_by_key[activity_item_key] = index

        for imported_item in imported_items:
            activity_item_key = self._activity_item_key(imported_item)
            if activity_item_key is None:
                continue

            existing_index = existing_index_by_key.get(activity_item_key)
            if existing_index is None:
                existing_index_by_key[activity_item_key] = len(merged_items)
                merged_items.append(imported_item)
                continue

            existing_item = merged_items[existing_index]
            if not self._activity_items_equal(existing_item, imported_item):
                merged_items[existing_index] = imported_item

        return merged_items

    @open_file_async()
    async def handle_activity_instance_activity_items(
        self, csvfile, session, merge_activity_items=True
    ):
        read_csv = csv.DictReader(csvfile, delimiter=",", skipinitialspace=True)
        api_tasks = []

        activity_items_grouped_by_instance = defaultdict(list)
        for row in read_csv:
            activity_items_grouped_by_instance[row["ACTIVITY_INSTANCE_NAME"]].append(
                row
            )

        all_names = list(activity_items_grouped_by_instance.keys())
        batch_size = 100
        existing_instances = []
        for i in range(0, len(all_names), batch_size):
            batch = all_names[i : i + batch_size]
            batch_result = self.api.get_all_activity_objects(
                "activity-instances",
                filters=json.dumps(
                    {
                        "name": {
                            "v": batch,
                            "op": "in",
                        }
                    }
                ),
            )
            if batch_result:
                existing_instances.extend(batch_result)

        if not existing_instances:
            self.log.warning(
                "No activity instances found for any of the activity items being imported"
            )
            return

        ref_data = self._fetch_reference_data()
        existing_instances_by_name = {
            instance["name"]: instance for instance in existing_instances
        }

        for (
            activity_instance_name,
            activity_items,
        ) in activity_items_grouped_by_instance.items():
            existing_activity_instance = existing_instances_by_name.get(
                activity_instance_name
            )
            if not existing_activity_instance:
                self.log.warning(
                    f"Activity instance '{activity_instance_name}' doesn't exist"
                )
                continue

            instance_status = existing_activity_instance.get("status")
            if instance_status == "Retired":
                self.log.warning(
                    f"Activity instance '{activity_instance_name}' is retired, skipping"
                )
                continue

            self.log.debug(
                f"Processing activity instance '{activity_instance_name}' (status: {instance_status}, {len(activity_items)} items)"
            )

            payload_activity_items = []
            for activity_item in activity_items:
                item_payload = self._build_activity_item(
                    activity_item, activity_instance_name, ref_data
                )
                if item_payload is not None:
                    payload_activity_items.append(item_payload)

            if merge_activity_items:
                activity_items_for_payload = self._merge_activity_items(
                    existing_activity_instance.get("activity_items", []),
                    payload_activity_items,
                )
            else:
                activity_items_for_payload = payload_activity_items

            attributes_payload = self._build_attributes_payload(
                existing_activity_instance, activity_items_for_payload
            )

            api_tasks.append(
                self._patch_attributes(
                    activity_instance_name=activity_instance_name,
                    activity_instance_uid=existing_activity_instance["uid"],
                    payload=attributes_payload,
                    session=session,
                    status=instance_status,
                )
            )

        await asyncio.gather(*api_tasks)

    async def async_run(self):
        mdr_migration_activity_instance_activity_items = load_env(
            "MDR_MIGRATION_ACTIVITY_INSTANCE_ACTIVITY_ITEMS"
        )
        merge_activity_items = map_boolean(
            load_env("MDR_MIGRATION_ACTIVITY_INSTANCE_MERGE_ACTIVITY_ITEMS", "True")
        )

        timeout = aiohttp.ClientTimeout(None)
        conn = aiohttp.TCPConnector(limit=4, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
            await self.handle_activity_instance_activity_items(
                mdr_migration_activity_instance_activity_items,
                session,
                merge_activity_items=merge_activity_items,
            )

    def run(self):
        self.log.info("Updating activity items for activity instances")
        asyncio.run(self.async_run())
        self.log.info("Done updating activity items")


def main():
    metr = Metrics()
    migrator = ActivityInstanceActivityItems(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="run_update_activity_instance_activity_items.py"
    )
    args = parser.parse_args()
    main()
