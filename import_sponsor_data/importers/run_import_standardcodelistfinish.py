import csv

from .functions.utils import create_logger, load_env
from .utils.importer import BaseImporter, open_file
from .utils.metrics import Metrics

logger = create_logger("legacy_mdr_migrations")

metrics = Metrics()

API_HEADERS = {"Accept": "application/json"}

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False") == "True"
API_BASE_URL = load_env("API_BASE_URL")

# SPONSOR DEFINED CODELISTS
MDR_MIGRATION_DOSAGE_FORM = load_env("MDR_MIGRATION_DOSAGE_FORM")

dosage_form = {
    "MDR_MIGRATION_DOSAGE_FORM": lambda row, headers: {
        "path": "/ct/terms",
        "uid": row[headers.index("CT_CD")],
        "body": {
            "sponsor_preferred_name": row[headers.index("CD_VAL_LB")],
            "sponsor_preferred_name_sentence_case": row[headers.index("CD_VAL_LB_LC")],
            "change_description": "Migration",
        },
    }
}


# Finishing touches for standard codelists in sponsor library
# TODO remove this altogether?
class StandardCodelistFinish(BaseImporter):
    logging_name = "standard_codelists_finish"

    def __init__(self, api=None, metrics_inst=None):
        super().__init__(api=api, metrics_inst=metrics_inst)

    @open_file()
    def dosage_form(self, csvfile):
        # Add sponsor preferred names to dosage forms
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        for row in readCSV:
            # TODO check if already exists
            _class = "MDR_MIGRATION_DOSAGE_FORM"
            data = dosage_form[_class](row, headers)
            # Start a new version
            self.api.post_to_api(
                {"path": f"/ct/terms/{data['uid']}/names/versions", "body": {}}
            )
            # path the names
            res = self.api.simple_patch(
                data["body"], f"/ct/terms/{data['uid']}/names", "/ct/terms/names"
            )
            # Approve
            if res is not None:
                # Approve Names
                self.api.simple_approve2(
                    "/ct/terms", f"/{res['term_uid']}/names/approvals", label="Names"
                )

    def run(self):
        self.log.info("Finalizing sponsor library")
        self.dosage_form(MDR_MIGRATION_DOSAGE_FORM)
        self.log.info("Done finalizing sponsor library")


def main():
    metr = Metrics()
    migrator = StandardCodelistFinish(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
