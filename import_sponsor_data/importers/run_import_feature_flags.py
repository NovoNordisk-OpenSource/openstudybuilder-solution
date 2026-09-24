"""Import feature flags from CSV into the API."""

# pylint: disable=logging-fstring-interpolation
import argparse
import csv

import requests

from .functions.parsers import map_boolean
from .functions.utils import load_env
from .utils.importer import BaseImporter, open_file
from .utils.metrics import Metrics
from .utils.path_join import path_join

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
API_BASE_URL = load_env("API_BASE_URL")
REQUEST_TIMEOUT_SECONDS = 30


class FeatureFlags(BaseImporter):
    """Import and optionally reconcile feature flags against the API."""

    logging_name = "feature_flags"

    def __init__(self, api=None, metrics_inst=None):
        """Initialize the feature flag importer."""
        super().__init__(api=api, metrics_inst=metrics_inst)

    @open_file()
    # pylint: disable=too-many-locals
    def handle_feature_flags(self, csvfile, update: bool = False):
        """Create, update, or retire feature flags to match the input CSV."""
        feature_flags_in_db = requests.get(
            path_join(self.api.api_base_url, "/feature-flags?include_retired=true"),
            headers=self.api.api_headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        ).json()
        feature_flags_in_db = {item["name"]: item for item in feature_flags_in_db}

        csv_data = csv.DictReader(csvfile)
        feature_flags_in_csv = {item["name"]: item for item in csv_data}

        # Version metadata fields returned by the API but not present in CSV import body
        version_fields = {
            "uid",
            "status",
            "version",
            "start_date",
            "end_date",
            "author_username",
            "change_description",
        }

        for feature_flag_name, feature_flag_data in feature_flags_in_csv.items():
            body = {
                "section": feature_flag_data["section"],
                "feature": feature_flag_data["feature"],
                "name": feature_flag_data["name"],
                "enabled": map_boolean(feature_flag_data["enabled"]),
                "description": feature_flag_data["description"] or None,
            }

            if update and feature_flag_data["name"] in feature_flags_in_db:
                _old = dict(feature_flags_in_db[feature_flag_data["name"]])
                _uid = str(_old["uid"])
                if _old.get("status") == "Retired":
                    self.log.info(
                        f"Reactivate feature flag '{feature_flag_data['name']}' before update"
                    )
                    self.api.post_to_api(
                        {
                            "path": f"feature-flags/{_uid}/activations",
                            "body": {},
                        }
                    )
                    _old["status"] = "Final"
                for field in version_fields:
                    _old.pop(field, None)
                _old.pop("name", None)  # name is not patchable; compare remaining

                patch_body = {
                    "section": body["section"],
                    "feature": body["feature"],
                    "enabled": body["enabled"],
                    "description": body["description"],
                }
                comparable_old = {
                    "section": _old.get("section"),
                    "feature": _old.get("feature"),
                    "enabled": _old.get("enabled"),
                    "description": _old.get("description"),
                }

                if comparable_old == patch_body:
                    self.log.info(
                        "Feature flag '%s' already exists with provided values %s",
                        feature_flag_data["name"],
                        body,
                    )
                    continue

                self.log.info(
                    f"Update feature flag '{feature_flag_data['name']}' from {_old} to {body}"
                )

                patch_body["uid"] = _uid
                self.api.patch_to_api(body=patch_body, path="feature-flags")
            elif not update and feature_flag_data["name"] in feature_flags_in_db:
                self.log.info(
                    f"Skipping. Feature flag '{feature_flag_data['name']}' already exists."
                )
            else:
                data = {
                    "path": "feature-flags",
                    "body": body,
                }

                self.log.info(f"Add feature flag '{data['body']['name']}'")

                self.api.post_to_api(data)

        if update:
            for feature_flag_name, feature_flag_data in feature_flags_in_db.items():
                if feature_flag_name not in feature_flags_in_csv:
                    if feature_flag_data.get("status") == "Retired":
                        self.log.info(
                            f"Skipping. Feature flag '{feature_flag_name}' is already deprecated."
                        )
                        continue
                    self.log.info(f"Deprecate feature flag '{feature_flag_name}'")
                    self.api.delete_to_api(
                        f"feature-flags/{feature_flag_data['uid']}/activations"
                    )

    def run(self, update: bool = False):
        """Run the feature flag import using the configured input path."""
        feature_flags = load_env("FEATURE_FLAGS")
        self.log.info("Importing feature flags")

        self.handle_feature_flags(feature_flags, update=update)

        self.log.info("Done importing feature flags")


def main(update: bool = False):
    """Run the feature flag importer entrypoint."""
    metr = Metrics()
    migrator = FeatureFlags(metrics_inst=metr)
    migrator.run(update=update)
    metr.print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--update",
        action="store_true",
        help="Whether to update existing feature flags or not.",
    )
    args = parser.parse_args()

    main(update=args.update)
