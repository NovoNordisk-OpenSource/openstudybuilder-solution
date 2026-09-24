import json
import os

from .functions.utils import load_env
from .run_import_mockdatajson import MockdataJson
from .utils.importer import open_file
from .utils.metrics import Metrics
from .utils.path_join import path_join

metrics = Metrics()

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
MDR_MIGRATION_STUDY_VERSIONS = (
    load_env("MDR_MIGRATION_STUDY_VERSIONS", default="False").lower() == "true"
)
MDR_MIGRATION_VERSIONED_STUDY_PATH = load_env(
    "MDR_MIGRATION_VERSIONED_STUDY_PATH", default=""
)


class MockdataJsonE2E(MockdataJson):
    logging_name = "mockdata_e2e"

    section_urls = {
        "activity": "/studies/{uid}/study-activities",
        "arm": "/studies/{uid}/study-arms",
        "compound": "/studies/{uid}/study-compounds",
        "criteria": "/studies/{uid}/study-criteria",
        "objective": "/studies/{uid}/study-objectives",
    }

    section_uid_keys = {
        "activity": "study_activity_uid",
        "arm": "arm_uid",
        "compound": "study_compound_uid",
        "criteria": "study_criteria_uid",
        "objective": "study_objective_uid",
    }

    def lock_study(self, study_id, desc):
        uid = self.lookup_study_uid_from_id(study_id)
        self.log.info(f"Locking study {study_id} with uid {uid}")
        self.api.simple_post_to_api(
            f"/studies/{uid}/locks", body={"change_description": desc}
        )

    def unlock_study(self, study_id):
        uid = self.lookup_study_uid_from_id(study_id)
        self.log.info(f"Unlocking study {study_id} with uid {uid}")
        self.api.simple_delete(f"/studies/{uid}/locks")

    def release_study(self, study_id, desc):
        uid = self.lookup_study_uid_from_id(study_id)
        self.log.info(f"Releasing study {study_id} with uid {uid}")
        self.api.simple_post_to_api(
            f"/studies/{uid}/release", body={"change_description": desc}
        )

    def import_study(self, path):
        self.log.info(f"Importing new version of study from {path}")
        studies_json = os.path.join(
            MDR_MIGRATION_VERSIONED_STUDY_PATH, path, "studies.json"
        )
        self.import_dir = os.path.join(MDR_MIGRATION_VERSIONED_STUDY_PATH, path)
        self.handle_studies(studies_json)

    def clear_study_sections(self, study_id, sections):
        study_uid = self.lookup_study_uid_from_id(study_id)
        for section in sections:
            self._clear_study_objects(study_uid, section)

    def _clear_study_objects(self, study_uid, section):
        self.log.info(f"clearing study {section}")
        section_url = self.section_urls[section].format(uid=study_uid)
        items = self.api.get_all_from_api(section_url)
        uid_key = self.section_uid_keys[section]
        for item in items:
            item_uid = item[uid_key]
            self.log.info(f"clearing study {section} with uid {item_uid}")
            self.api.simple_delete(path_join(section_url, item_uid))

    # Handle studies.
    @open_file()
    def handle_study_versions(self, jsonfile):
        self.log.info("======== Running versioning sequence ========")
        versions = json.load(jsonfile)
        for action in versions:
            if action["action"] == "Lock":
                self.lock_study(action["study_id"], action["desc"])
            elif action["action"] == "Unlock":
                self.unlock_study(action["study_id"])
            elif action["action"] == "Release":
                self.release_study(action["study_id"], action["desc"])
            elif action["action"] == "Import":
                self.import_study(action["dir"])
            elif action["action"] == "Clear":
                self.clear_study_sections(action["study_id"], action["sections"])

    def run(self):
        self.log.info("======== Migrating versioned study for E2E ========")
        if MDR_MIGRATION_STUDY_VERSIONS and MDR_MIGRATION_VERSIONED_STUDY_PATH:
            # Requested activities
            activity_request_json = os.path.join(
                MDR_MIGRATION_VERSIONED_STUDY_PATH, "activity-requests.json"
            )
            self.handle_activities(activity_request_json)

            # User defined criteria templates
            criteria_template_json = os.path.join(
                MDR_MIGRATION_VERSIONED_STUDY_PATH, "criteria-templates.json"
            )
            self.handle_all_templates(criteria_template_json, "criteria")

            # USer defined objective templates
            objective_template_json = os.path.join(
                MDR_MIGRATION_VERSIONED_STUDY_PATH, "objective-templates.json"
            )
            self.handle_all_templates(objective_template_json, "objective")

            versions_json = os.path.join(
                MDR_MIGRATION_VERSIONED_STUDY_PATH, "versions.json"
            )
            self.handle_study_versions(versions_json)
        elif not MDR_MIGRATION_STUDY_VERSIONS:
            self.log.info("Import is disabled by env MDR_MIGRATION_STUDY_VERSIONS")
        elif not MDR_MIGRATION_VERSIONED_STUDY_PATH:
            self.log.info(
                "Import skipped because env MDR_MIGRATION_VERSIONED_STUDY_PATH is not set"
            )
        self.log.info("Done migrating versioned study for E2E")


def main():
    metr = Metrics()
    migrator = MockdataJsonE2E(metrics_inst=metr)
    migrator.run()
    migrator.print_cache_stats()
    metr.print()


if __name__ == "__main__":
    main()
