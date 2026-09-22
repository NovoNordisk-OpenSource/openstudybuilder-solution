import asyncio
import csv

import aiohttp

from .functions.parsers import map_boolean, parse_float, parse_to_int
from .functions.utils import create_logger, load_env
from .utils.api_bindings import (
    CODELIST_NAME_MAP,
    CODELIST_UNIT,
    UNIT_SUBSET_AGE,
    UNIT_SUBSET_DOSE,
    UNIT_SUBSET_ENDPOINT_UNIT,
    UNIT_SUBSET_STRENGTH,
    UNIT_SUBSET_STUDY_PREFERRED_TIME_UNIT,
    UNIT_SUBSET_STUDY_TIME,
    UNIT_SUBSET_TIME,
)
from .utils.importer import BaseImporter, open_file_async
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
MDR_MIGRATION_UNIT_DIF = load_env("MDR_MIGRATION_UNIT_DIF")


# Finishing touches for standard codelists in sponsor library
class Units(BaseImporter):
    logging_name = "unitdefinitions"

    def __init__(self, api=None, metrics_inst=None):
        super().__init__(api=api, metrics_inst=metrics_inst)

    def fetch_ct_units_terms(self):
        codelist_uid = CODELIST_NAME_MAP[CODELIST_UNIT]
        items = self.api.get_all_from_api(f"/ct/codelists/{codelist_uid}/terms")
        if items is None:
            items = []
        self.log.info(f"Got {len(items)} terms from unit codelist")
        return items

    def lookup_ct_unit_uid(self, units, concept_id):
        for unit in units:
            if unit["concept_id"] == concept_id:
                return unit["term_uid"]
        return None

    @open_file_async()
    async def handle_unit_definitions(self, csvfile, session):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        api_tasks = []
        existing_units = self.api.get_all_from_api("/concepts/unit-definitions")
        if existing_units is None:
            existing_units = []
        existing_units_by_uid = {v["uid"]: v for v in existing_units}
        existing_rows = self.api.get_all_identifiers(
            existing_units,
            identifier="name",
            value="uid",
        )

        unit_subset_codelist_uid = self.api.get_codelist_uid("UNITSUBS")
        unit_dim_codelist_uid = self.api.get_codelist_uid("UNITDIM")
        unit_codelist_uid = self.api.get_codelist_uid("UNIT")

        ucum_codelists = self.api.get_all_from_api(
            "/dictionaries/codelists", params={"library_name": "UCUM"}
        )
        all_ucum_terms = {}
        for ucum_codelist in ucum_codelists:
            all_ucum_terms.update(
                self.api.get_all_identifiers(
                    self.api.get_all_from_api(
                        "/dictionaries/terms",
                        params={"codelist_uid": ucum_codelist["codelist_uid"]},
                    ),
                    "name",
                    "term_uid",
                )
            )

        all_unit_dimension_terms = self.api.get_all_identifiers(
            self.api.get_all_from_api(f"/ct/codelists/{unit_dim_codelist_uid}/terms"),
            identifier="submission_value",
            value="term_uid",
        )
        all_unit_subset_terms = self.api.get_all_identifiers(
            self.api.get_all_from_api(
                f"/ct/codelists/{unit_subset_codelist_uid}/terms"
            ),
            identifier="submission_value",
            value="term_uid",
        )
        print(all_unit_subset_terms)
        print(all_unit_dimension_terms)
        all_ct_units = self.fetch_ct_units_terms()

        age_unit_subset_uid = all_unit_subset_terms[UNIT_SUBSET_AGE]
        dose_unit_subset_uid = all_unit_subset_terms[UNIT_SUBSET_DOSE]
        study_time_subset_uid = all_unit_subset_terms[UNIT_SUBSET_STUDY_TIME]
        time_unit_subset_uid = all_unit_subset_terms[UNIT_SUBSET_TIME]
        strength_unit_subset_uid = all_unit_subset_terms[UNIT_SUBSET_STRENGTH]
        endpoint_unit_subset_uid = all_unit_subset_terms[UNIT_SUBSET_ENDPOINT_UNIT]
        study_preferred_unit_subset_uid = all_unit_subset_terms[
            UNIT_SUBSET_STUDY_PREFERRED_TIME_UNIT
        ]
        for row in readCSV:
            name = row[headers.index("UNIT")]

            ucum_uid = all_ucum_terms.get(row[headers.index("UCUM name")])

            unit_dimension_uid = all_unit_dimension_terms.get(
                row[headers.index("UNIT_DIMENSION")]
            )

            ct_units = []
            # Link to CDISC units
            if row[headers.index("CT_CD")] != "":
                ct_unit_uid = self.lookup_ct_unit_uid(
                    all_ct_units,
                    row[headers.index("CT_CD")],
                )
                if ct_unit_uid is not None:
                    self.log.info(
                        f"Linking concept id '{row[headers.index('CT_CD')]}' to term uid '{ct_unit_uid}'"
                    )
                    ct_units.append(ct_unit_uid)
                else:
                    self.log.warning(
                        f"Cannot find uid for concept id '{row[headers.index('CT_CD')]}'"
                    )
            # Link to sponsor defined units
            if row[headers.index("SPDEF_SUBMVAL")] != "":
                submval = row[headers.index("SPDEF_SUBMVAL")]
                unit_term = self.api.find_term_by_submission_value(
                    unit_codelist_uid, submval
                )
                if unit_term is not None:
                    self.log.info(
                        f"Linking submission value '{submval}' to term uid '{unit_term['term_uid']}'"
                    )
                    ct_units.append(unit_term["term_uid"])
                else:
                    self.log.warning(
                        f"Cannot find unit term uid for submission value '{submval}'"
                    )

            unit_subsets = []
            if row[headers.index("AGE_UNIT_SUBSET")] == "Y":
                unit_subsets.append(age_unit_subset_uid)
            if row[headers.index("DOSE_UNIT_SUBSET")] == "Y":
                unit_subsets.append(dose_unit_subset_uid)
            if row[headers.index("STUDY_TIME_UNIT_SUBSET")] == "Y":
                unit_subsets.append(study_time_subset_uid)
            if row[headers.index("TIME_UNIT_SUBSET")] == "Y":
                unit_subsets.append(time_unit_subset_uid)
            if row[headers.index("STRENGTH_UNIT_SUBSET")] == "Y":
                unit_subsets.append(strength_unit_subset_uid)
            if row[headers.index("STUDY_PREFERRED_TIME_UNIT")] == "Y":
                unit_subsets.append(study_preferred_unit_subset_uid)
            if row[headers.index("ENDPOINT_UNITS_SUBSET")] == "Y":
                unit_subsets.append(endpoint_unit_subset_uid)

            # Mark as template parameter if part of any subset
            # template_parameter = len(unit_subsets) > 0
            # All units are template parameters!
            template_parameter = True

            data = {
                "path": "/concepts/unit-definitions",
                "approve_path": "/concepts/unit-definitions",
                "body": {
                    "name": name,
                    "library_name": "Sponsor",
                    "ct_units": ct_units,
                    "unit_subsets": unit_subsets,
                    "convertible_unit": map_boolean(
                        row[headers.index("CONVERTIBLE_UNIT")]
                    ),
                    "display_unit": map_boolean(row[headers.index("DISPLAY_UNIT")]),
                    "master_unit": map_boolean(row[headers.index("MASTER_UNIT")]),
                    "si_unit": map_boolean(row[headers.index("SI_UNIT")]),
                    "us_conventional_unit": map_boolean(
                        row[headers.index("US_CONVENTIONAL_UNIT")]
                    ),
                    "legacy_code": row[headers.index("UNIT")],
                    "use_molecular_weight": map_boolean(
                        row[headers.index("USE_MOLECULAR_WEIGHT")]
                    ),
                    "use_complex_unit_conversion": map_boolean(
                        row[headers.index("USE_COMPLEX_UNIT_CONVERSION")]
                    ),
                    "conversion_factor_to_master": parse_float(
                        row[headers.index("CONVERTION_FACTOR_TO_MASTER")]
                    ),
                    "unit_dimension": unit_dimension_uid,
                    "definition": row[headers.index("description")] or None,
                    "order": parse_to_int(row[headers.index("CD_VAL_SORT_SEQ")]),
                    "ucum": ucum_uid,
                    "comment": row[headers.index("Comment")] or None,
                    "template_parameter": template_parameter,
                },
            }
            if row[headers.index("Migrate Y/N")] not in ("Y", "y"):
                self.log.info(f"Unit '{name}' is not marked for migration, skipping")
            elif existing_rows.get(name):
                equal = self.are_units_equal(
                    data["body"], existing_units_by_uid.get(existing_rows.get(name))
                )
                if equal:
                    self.log.info(
                        f"Skipping existing unit '{name}' with ct codes: {ct_units}"
                    )
                else:
                    self.log.info(f"Updating unit '{name}'")
                    data["body"]["change_description"] = "Migration modification"
                    data["patch_path"] = (
                        f"/concepts/unit-definitions/{existing_rows.get(name)}"
                    )
                    data["new_path"] = (
                        f"/concepts/unit-definitions/{existing_rows.get(name)}/versions"
                    )
                    api_tasks.append(
                        self.api.new_version_patch_then_approve(
                            data=data, session=session, approve=True
                        )
                    )
            else:
                self.log.info(
                    f"Adding unit '{name}' with ct codes: {ct_units}, part of subsets: {unit_subsets}"
                )
                api_tasks.append(
                    self.api.post_then_approve(data=data, session=session, approve=True)
                )

        await asyncio.gather(*api_tasks)

    def are_units_equal(self, new, existing):
        simple_fields = [
            "name",
            "convertible_unit",
            "display_unit",
            "master_unit",
            "si_unit",
            "us_conventional_unit",
            "legacy_code",
            "molecular_weight_conv_expon",
            "conversion_factor_to_master",
            "definition",
            "order",
            "comment",
            "template_parameter",
        ]
        for field in simple_fields:
            if new.get(field) != existing.get(field):
                self.log.info(
                    f"Field {field} is different, new: {new.get(field)}, old: {existing.get(field)}"
                )
                return False
        new_unit_subset = self.make_set_of_optional_list(new["unit_subsets"])
        existing_unit_subset = self.make_set_of_term_uids(existing["unit_subsets"])
        if new_unit_subset != existing_unit_subset:
            self.log.info(
                f"Unit subsets are different, new: {new_unit_subset}, old: {existing_unit_subset}"
            )
            return False
        new_ct_units = self.make_set_of_optional_list(new["ct_units"])
        existing_ct_units = self.make_set_of_term_uids(existing["ct_units"])
        if new_ct_units != existing_ct_units:
            self.log.info(
                f"CT units are different, new: {new_ct_units}, old: {existing_ct_units}"
            )
            return False
        existing_ucum = existing["ucum"]
        if existing_ucum is not None:
            existing_ucum = existing_ucum["term_uid"]
        if new["ucum"] != existing_ucum:
            self.log.info(
                f"UCUM is different, new: {new['ucum']}, old: {existing_ucum}"
            )
            return False
        existing_dimension = existing["unit_dimension"]
        if existing_dimension is not None:
            existing_dimension = existing_dimension["term_uid"]
        if new["unit_dimension"] != existing_dimension:
            self.log.info(
                f"Unit dimension is different, new: {new['unit_dimension']}, old: {existing_dimension}"
            )
            return False
        return True

    def make_set_of_term_uids(self, items):
        if items is None:
            return set()
        return set(item["term_uid"] for item in items)

    def make_set_of_optional_list(self, items):
        if items is None:
            return set()
        return set(items)

    async def async_run(self):
        timeout = aiohttp.ClientTimeout(None)

        conn = aiohttp.TCPConnector(limit=4, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
            await self.handle_unit_definitions(MDR_MIGRATION_UNIT_DIF, session)

    def run(self):
        self.log.info("Importing unit definitions")
        asyncio.run(self.async_run())
        self.log.info("Done importing unit definitions")


def main():
    metr = Metrics()
    migrator = Units(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
