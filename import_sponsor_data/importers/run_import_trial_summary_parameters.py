import csv
import re

from .functions.utils import load_env
from .utils.importer import BaseImporter, open_file
from .utils.metrics import Metrics

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False") == "True"
API_BASE_URL = load_env("API_BASE_URL")

MDR_MIGRATION_TRIAL_SUMMARY_PARAMETERS = load_env(
    "MDR_MIGRATION_TRIAL_SUMMARY_PARAMETERS"
)

TRIAL_SUMMARY_TEST_CODE_CODELIST_UID = "C66738"


class TrialSummaryParameters(BaseImporter):
    logging_name = "trial_summary_parameters"

    def __init__(self, api=None, metrics_inst=None):
        super().__init__(api=api, metrics_inst=metrics_inst)

    def _build_lookup_maps(self):
        # Map submission_value -> term_uid for C66738 (Trial Summary Test Code)
        ts_terms = self.api.get_all_from_api(
            f"/ct/codelists/{TRIAL_SUMMARY_TEST_CODE_CODELIST_UID}/terms"
        )
        self._ts_term_map = {
            term["submission_value"]: term["term_uid"]
            for term in (ts_terms or [])
            if term.get("submission_value")
        }
        self.log.info(f"Loaded {len(self._ts_term_map)} terms from C66738")

        # Map submission_value -> term_uid for DATATYPE sponsor codelist
        datatype_codelist_uid = self.api.get_codelist_uid("SEMTCDT")
        if datatype_codelist_uid:
            datatype_terms = self.api.get_all_from_api(
                f"/ct/codelists/{datatype_codelist_uid}/terms"
            )
            self._datatype_map = {
                term["submission_value"]: term["term_uid"]
                for term in (datatype_terms or [])
                if term.get("submission_value")
            }
            self.log.info(
                f"Loaded {len(self._datatype_map)} terms from DATATYPE codelist"
            )
        else:
            self.log.warning("DATATYPE codelist not found")
            self._datatype_map = {}

        # Map submission_value -> term_uid for NULLFLVR sponsor codelist
        nullflvr_codelist_uid = self.api.get_codelist_uid("NULLFLVR")
        if nullflvr_codelist_uid:
            nullflvr_terms = self.api.get_all_from_api(
                f"/ct/codelists/{nullflvr_codelist_uid}/terms"
            )
            self._nullflvr_map = {
                term["submission_value"]: term["term_uid"]
                for term in (nullflvr_terms or [])
                if term.get("submission_value")
            }
            self.log.info(
                f"Loaded {len(self._nullflvr_map)} terms from NULLFLVR codelist"
            )
        else:
            self.log.warning("NULLFLVR codelist not found")
            self._nullflvr_map = {}

    def _get_dictionary_codelist_uids(self, library_name):
        items = self.api.get_all_from_api(
            "/dictionaries/codelists",
            params={"library_name": library_name, "page_size": 0},
        )
        if not items:
            return []
        return [item["codelist_uid"] for item in items if item.get("codelist_uid")]

    @open_file()
    def handle_trial_summary_parameters(self, csvfile):
        self._build_lookup_maps()
        reader = csv.DictReader(csvfile)
        for row in reader:
            tsparmcd = row.get("tsparmcd", "").strip()
            if not tsparmcd:
                continue

            term_uid = self._ts_term_map.get(tsparmcd)
            if not term_uid:
                self.log.warning(
                    f"CTTerm not found in C66738 for tsparmcd '{tsparmcd}', skipping"
                )
                continue

            body = {}

            core = row.get("core", "").strip()
            if core:
                body["required_level"] = core

            cardinality = row.get("cardinality", "").strip()
            if cardinality:
                body["cardinality"] = cardinality

            notes = row.get("notes", "").strip()
            if notes:
                body["notes"] = notes

            format_val = row.get("term", "").strip()
            if format_val:
                bracket_match = re.fullmatch(r"\((.+)\)", format_val)
                if bracket_match:
                    codelist_submval = bracket_match.group(1)
                    if codelist_submval == "NY":
                        datatype_uid = self._datatype_map.get("boolean")
                        if datatype_uid:
                            body["semantic_data_type_uid"] = datatype_uid
                        else:
                            self.log.warning(
                                f"DATATYPE term 'boolean' not found for '{tsparmcd}'"
                            )
                    else:
                        datatype_uid = self._datatype_map.get("ctTerm")
                        if datatype_uid:
                            body["semantic_data_type_uid"] = datatype_uid
                        else:
                            self.log.warning(
                                f"DATATYPE term 'ctTerm' not found for '{tsparmcd}'"
                            )
                    codelist_uid = self.api.get_codelist_uid(codelist_submval)
                    if codelist_uid:
                        body["response_codelist_uid"] = codelist_uid
                    else:
                        self.log.warning(
                            f"Response codelist '{codelist_submval}' not found for '{tsparmcd}'"
                        )
                else:
                    _library_datatype_map = {
                        "unii": "unii",
                        "snomed": "snomed",
                        "med-rt": "medrt",
                    }
                    if format_val == "ISO 8601":
                        tsparm = row.get("tsparm", "").strip().lower()
                        if "datetime" in tsparm:
                            datatype_submval = "durationDatetime"
                        elif "date" in tsparm:
                            datatype_submval = "date"
                        else:
                            datatype_submval = "durationDatetime"
                        datatype_uid = self._datatype_map.get(datatype_submval)
                        if datatype_uid:
                            body["semantic_data_type_uid"] = datatype_uid
                        else:
                            self.log.warning(
                                f"DATATYPE term '{datatype_submval}' not found for '{tsparmcd}'"
                            )
                    else:
                        dict_datatype_submval = _library_datatype_map.get(
                            format_val.lower()
                        )
                        if dict_datatype_submval:
                            dict_uids = self._get_dictionary_codelist_uids(format_val)
                            if dict_uids:
                                body["response_dictionary_uids"] = dict_uids
                            else:
                                self.log.warning(
                                    f"No dictionary codelists found for library '{format_val}' for '{tsparmcd}'"
                                )
                            datatype_uid = self._datatype_map.get(dict_datatype_submval)
                            if datatype_uid:
                                body["semantic_data_type_uid"] = datatype_uid
                            else:
                                self.log.warning(
                                    f"DATATYPE term '{dict_datatype_submval}' not found for '{tsparmcd}'"
                                )
                        else:
                            datatype_uid = self._datatype_map.get(format_val)
                            if datatype_uid:
                                body["semantic_data_type_uid"] = datatype_uid
                            else:
                                self.log.warning(
                                    f"DATATYPE term '{format_val}' not found for '{tsparmcd}'"
                                )
            else:
                datatype_uid = self._datatype_map.get("text")
                if datatype_uid:
                    body["semantic_data_type_uid"] = datatype_uid
                else:
                    self.log.warning(f"DATATYPE term 'text' not found for '{tsparmcd}'")

            nullflavor_val = row.get("nullflavor", "").strip()
            if nullflavor_val:
                null_flavor_uids = []
                for nf in nullflavor_val.split(","):
                    nf = nf.strip()
                    uid = self._nullflvr_map.get(nf)
                    if uid:
                        null_flavor_uids.append(uid)
                    else:
                        self.log.debug(
                            f"Null flavor '{nf}' not found in NULLFLVR codelist for '{tsparmcd}', skipping"
                        )
                if null_flavor_uids:
                    body["valid_null_flavor_term_uids"] = null_flavor_uids

            osb_field_name = row.get("OSB Field", "").strip()
            if osb_field_name:
                body["osb_field_name"] = osb_field_name

            osb_page_reference = row.get("\ufeffOSB Page URI", "").strip()
            if osb_page_reference:
                body["osb_page_reference"] = osb_page_reference

            self.log.info(
                f"Posting trial summary parameter for '{tsparmcd}' (term_uid: {term_uid})"
            )
            self.log.debug(f"Payload: {body}")
            res = self.api.simple_patch(
                body,
                f"/ct/terms/{term_uid}/names/trial-summary-parameters",
                "/ct/terms/names/trial-summary-parameters",
            )
            if res is not None:
                self.api.simple_approve(
                    f"/ct/terms/{term_uid}/names/approvals",
                )

    def run(self):
        self.log.info("Importing trial summary parameters")
        self.handle_trial_summary_parameters(MDR_MIGRATION_TRIAL_SUMMARY_PARAMETERS)
        self.log.info("Done importing trial summary parameters")


def main():
    metr = Metrics()
    migrator = TrialSummaryParameters(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
