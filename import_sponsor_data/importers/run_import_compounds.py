import copy
import json
from functools import lru_cache

from .functions.utils import load_env
from .utils import import_templates
from .utils.api_bindings import (
    CODELIST_COMPOUND_DISPENSED_IN,
    CODELIST_DELIVERY_DEVICE,
    CODELIST_DOSAGE_FORM,
    CODELIST_FREQUENCY,
    CODELIST_ROUTE_OF_ADMINISTRATION,
    CODELIST_SDTM_DOMAIN_ABBREVIATION,
    UNIT_SUBSET_AGE,
    UNIT_SUBSET_DOSE,
    UNIT_SUBSET_STRENGTH,
)
from .utils.importer import BaseImporter, open_file
from .utils.metrics import Metrics
from .utils.path_join import path_join

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False") == "True"
API_BASE_URL = load_env("API_BASE_URL")

MDR_MIGRATION_COMPOUNDS = load_env("MDR_MIGRATION_COMPOUNDS")
MDR_MIGRATION_ACTIVE_SUBSTANCES = load_env("MDR_MIGRATION_ACTIVE_SUBSTANCES")
MDR_MIGRATION_PHARMACEUTICAL_PRODUCTS = load_env(
    "MDR_MIGRATION_PHARMACEUTICAL_PRODUCTS"
)
MDR_MIGRATION_MEDICINAL_PRODUCTS = load_env("MDR_MIGRATION_MEDICINAL_PRODUCTS")


def make_payload(path, body):
    return {"path": path, "body": body}


# Fill simple values into a template.
# Set library_name to Sponsor if not given in the data
def fill_template(data, template):
    filled_template = copy.deepcopy(template)
    for key in filled_template.keys():
        if not key.lower().endswith("uid"):
            if key in data:
                value = data.get(key, None)
                if not isinstance(value, (dict, list, tuple)):
                    filled_template[key] = value
    if filled_template.get("library_name") == "string":
        filled_template["library_name"] = "Sponsor"
    return filled_template


class Compounds(BaseImporter):
    logging_name = "compounds"

    def __init__(self, api=None, metrics_inst=None):
        super().__init__(api=api, metrics_inst=metrics_inst)
        self.dose_units = self.api.get_all_identifiers(
            self.api.get_all_from_api(
                f"/concepts/unit-definitions?subset={UNIT_SUBSET_DOSE}"
            ),
            identifier="name",
            value="uid",
        )
        self.age_units = self.api.get_all_identifiers(
            self.api.get_all_from_api(
                f"/concepts/unit-definitions?subset={UNIT_SUBSET_AGE}"
            ),
            identifier="name",
            value="uid",
        )
        self.strength_units = self.api.get_all_identifiers(
            self.api.get_all_from_api(
                f"/concepts/unit-definitions?subset={UNIT_SUBSET_STRENGTH}"
            ),
            identifier="name",
            value="uid",
        )
        self.sdtm_domains = self.api.get_all_from_api(
            f"/ct/terms?codelist_name={CODELIST_SDTM_DOMAIN_ABBREVIATION}"
        )

    def append_if_not_none(self, thelist, value):
        if value is not None:
            thelist.append(value)

    @lru_cache(maxsize=10000)
    def lookup_substance_uid(self, unii_value):
        self.log.debug(f"Looking up substance with unii code '{unii_value}'")
        filt = {"dictionary_id": {"v": [unii_value], "op": "eq"}}
        items = self.api.get_all_from_api(
            "/dictionaries/substances",
            params={"filters": json.dumps(filt)},
        )
        if items is not None and len(items) > 0:
            uid = items[0].get("term_uid", None)
            self.log.debug(
                f"Found substance with unii code '{unii_value}' and uid '{uid}'"
            )
            return uid
        self.log.warning(f"Could not find substance with unii code '{unii_value}'")

    def post_or_patch_item(self, data, unique_prop, existing_items, compare_function):
        existing_item = existing_items.get(data["body"][unique_prop])
        if existing_item is None:
            self.log.info(f"Add new object '{data['body'][unique_prop]}'")
            post_response = self.api.post_to_api(data)
            if post_response is not None:
                return self.api.approve_item(post_response["uid"], data["path"])

        elif compare_function(data["body"], existing_item):
            self.log.info(
                f"Identical object '{data['body'][unique_prop]}' exists, skipping"
            )
            return existing_item
        else:
            self.log.info(
                f"Patching existing object '{data['body'][unique_prop]}', with uid '{existing_item['uid']}'"
            )
            new_path = path_join(data["path"], existing_item["uid"], "versions")

            data["body"]["change_description"] = "Migration modification"
            data["body"]["uid"] = existing_item["uid"]
            if existing_item["status"] == "Draft":
                self.log.info(
                    f"Object '{data['body'][unique_prop]}' is already in draft status, not creating new version"
                )
                new_ver_response = True
            else:
                new_ver_response = self.api.post_to_api(data, path=new_path)
            if new_ver_response is not None:
                patch_response = self.api.patch_to_api(data["body"], data["path"])
                if patch_response is not None:
                    return self.api.approve_item(existing_item["uid"], data["path"])

    def compare_single_property(self, new, existing, new_prop, existing_prop=None):
        new_value = new.get(new_prop)
        if existing_prop is None:
            existing_prop = new_prop
        if "." in existing_prop:
            prop, uid_key = existing_prop.split(".")
            existing_prop = existing.get(prop)
            existing_value = (
                existing_prop.get(uid_key) if existing_prop is not None else None
            )
        else:
            existing_value = existing.get(existing_prop)
        return new_value == existing_value

    def compare_list_property(self, new, new_prop, existing, existing_prop):
        new_set = set(new.get(new_prop, []))
        if "." in existing_prop:
            # This property is a list of objects, we need to compare a specific key
            prop, key = existing_prop.split(".")
            existing_set = {val[key] for val in existing.get(prop, [])}
        else:
            existing_set = set(existing.get(existing_prop, []))
        if new_set != existing_set:
            self.log.info(
                f"Properties {new_prop} & {existing_prop} differ, {new_set} vs {existing_set}"
            )
            return False
        return True

    def compare_simple_properties(self, new, existing, properties):
        for prop in properties:
            if isinstance(prop, str):
                new_prop = prop
                existing_prop = None
            else:
                new_prop, existing_prop = prop
            if not self.compare_single_property(new, existing, new_prop, existing_prop):
                self.log.info(f"Property '{new_prop}', '{existing_prop}' differs")
                return False
        return True

    def compare_list_properties(self, new, existing, properties):
        for new_prop, existing_prop in properties:
            if not self.compare_list_property(new, new_prop, existing, existing_prop):
                return False
        return True

    def compare_compounds(self, new, existing):
        single_values = [
            "name",
            "name_sentence_case",
            "definition",
            "library_name",
        ]
        if not self.compare_simple_properties(new, existing, single_values):
            return False

        list_values = []
        return self.compare_list_properties(new, existing, list_values)

    def compare_compound_aliases(self, new, existing):
        single_values = [
            "name",
            "name_sentence_case",
            "definition",
            "library_name",
            "abbreviation",
            "is_preferred_synonym",
            ("compound_uid", "compound.uid"),
        ]
        return self.compare_simple_properties(new, existing, single_values)

    @open_file()
    def handle_compounds(self, jsonfile):
        import_data = json.load(jsonfile)

        existing_compounds = self.api.get_all_from_api("/concepts/compounds")
        existing_compounds_by_name = {x["name"]: x for x in existing_compounds}
        existing_compound_aliases = self.api.get_all_from_api(
            "/concepts/compound-aliases"
        )
        existing_compound_aliases_by_name = {
            x["name"]: x for x in existing_compound_aliases
        }

        for compound in import_data:
            data = fill_template(compound, import_templates.compound)

            payload = make_payload("/concepts/compounds", data)
            # print(json.dumps(data, indent=2))

            new_or_old_compound = self.post_or_patch_item(
                payload, "name", existing_compounds_by_name, self.compare_compounds
            )

            # Create an alias for the compound if needed
            if new_or_old_compound is not None:
                compound_uid = new_or_old_compound["uid"]
                self.log.info(
                    f"Create a default compound alias for compound '{data['name']}'"
                )
                data = fill_template(compound, import_templates.compound_alias)
                data["compound_uid"] = compound_uid
                data["is_preferred_synonym"] = True
                # print(json.dumps(data, indent=2))
                payload = make_payload("/concepts/compound-aliases", data)
                self.post_or_patch_item(
                    payload,
                    "name",
                    existing_compound_aliases_by_name,
                    self.compare_compound_aliases,
                )

    def compare_substances(self, new, existing):
        single_values = [
            "external_id",
            "analyte_number",
            "short_number",
            "long_number",
            "inn",
            "library_name",
            ("unii_term_uid", "unii.substance_term_uid"),
        ]
        return self.compare_simple_properties(new, existing, single_values)

    @open_file()
    def handle_active_substances(self, datafile):
        import_data = json.load(datafile)

        existing_substances = self.api.get_all_from_api("/concepts/active-substances")
        existing_substances_by_id = {x["external_id"]: x for x in existing_substances}

        for row in import_data:
            self.log.info(f'Process substance {row["external_id"]}')

            data = fill_template(row, import_templates.active_substance)

            if row.get("unii"):
                unii_uid = self.lookup_substance_uid(row["unii"]["substance_unii"])
                data["unii_term_uid"] = unii_uid
            else:
                del data["unii_term_uid"]

            payload = make_payload("/concepts/active-substances", data)
            # print("--- active substance to post")
            # print(json.dumps(payload, indent=2))

            # Create
            self.post_or_patch_item(
                payload,
                "external_id",
                existing_substances_by_id,
                self.compare_substances,
            )

    def compare_pharmaceutical_products(self, new, existing):
        single_values = [
            "external_id",
            "library_name",
        ]
        if not self.compare_simple_properties(new, existing, single_values):
            return False

        list_values = [
            ("route_of_administration_uids", "routes_of_administration.term_uid"),
            ("dosage_form_uids", "dosage_forms.term_uid"),
        ]
        if not self.compare_list_properties(new, existing, list_values):
            return False

        # Comparing formulations gets a bit more complex
        new_formulations = new["formulations"]
        existing_formulations = existing["formulations"]
        if len(new_formulations) != len(existing_formulations):
            self.log.info(
                f"Formulation count differs: {len(new_formulations)} != {len(existing_formulations)}"
            )
            return False

        old_formul_by_id = {x["external_id"]: x for x in existing_formulations}

        for new_formul in new_formulations:
            existing_formul = old_formul_by_id.get(new_formul["external_id"], None)
            if existing_formul is None:
                self.log.info(
                    f"Formulation with external_id '{new_formul['external_id']}' not found in existing formulations"
                )
                return False
            if not self.compare_formulations(new_formul, existing_formul):
                return False

        return True

    def compare_formulations(self, new, existing):
        single_values = ["external_id"]
        if not self.compare_simple_properties(new, existing, single_values):
            return False

        new_ingredients = new["ingredients"]
        existing_ingredients = existing["ingredients"]
        if len(new_ingredients) != len(existing_ingredients):
            self.log.info(
                f"Ingredient count differs: {len(new_ingredients)} != {len(existing_ingredients)}"
            )
            return False
        old_ing_by_id = {x["external_id"]: x for x in existing_ingredients}
        for new_ing in new_ingredients:
            existing_ing = old_ing_by_id.get(new_ing["external_id"], None)
            if existing_ing is None:
                self.log.info(
                    f"Ingredient with external_id '{new_ing['external_id']}' not found in existing ingredients"
                )
                return False
            if not self.compare_ingredients(new_ing, existing_ing):
                self.log.info(f"Ingredient '{new_ing['external_id']}' differs")
                return False
        return True

    def compare_ingredients(self, new, existing):
        single_values = [
            "external_id",
            "formulation_name",
            ("active_substance_uid", "active_substance.uid"),
            ("strength_uid", "strength.uid"),
            ("half_life_uid", "half_life.uid"),
        ]
        if not self.compare_simple_properties(new, existing, single_values):
            return False

        list_values = [
            ("lag_time_uids", "lag_times.uid"),
        ]
        return self.compare_list_properties(new, existing, list_values)

    @open_file()
    def handle_pharmaceutical_products(self, datafile):
        import_data = json.load(datafile)

        existing_products = self.api.get_all_from_api(
            "/concepts/pharmaceutical-products"
        )
        existing_products_by_id = {x["external_id"]: x for x in existing_products}

        existing_substances = self.api.get_all_from_api("/concepts/active-substances")
        existing_substances_by_id = {x["external_id"]: x for x in existing_substances}

        for row in import_data:
            if len(row) == 0:
                continue
            self.log.info(f'Process pharmaceutical product {row["external_id"]}')

            data = fill_template(row, import_templates.pharmaceutical_product)

            for val in row["dosage_forms"]:
                name = val["name"]
                uid = self.lookup_codelist_term_uid(CODELIST_DOSAGE_FORM, name)
                self.append_if_not_none(data["dosage_form_uids"], uid)
            for val in row["routes_of_administration"]:
                name = val["name"]
                uid = self.lookup_codelist_term_uid(
                    CODELIST_ROUTE_OF_ADMINISTRATION, name
                )
                self.append_if_not_none(data["route_of_administration_uids"], uid)

            for formulation in row["formulations"]:
                formul_data = fill_template(formulation, import_templates.formulation)
                for ingredient in formulation["ingredients"]:
                    ing_data = fill_template(ingredient, import_templates.ingredient)
                    if ingredient["active_substance"] is not None:
                        uid = existing_substances_by_id.get(
                            ingredient["active_substance"]["external_id"], {}
                        ).get("uid")
                        if uid is not None:
                            ing_data["active_substance_uid"] = uid
                    if ingredient.get("half_life") is not None:
                        uid = self.create_or_get_numeric_value(
                            ingredient["half_life"], UNIT_SUBSET_AGE
                        )
                        if uid is not None:
                            ing_data["half_life_uid"] = uid
                    if ingredient.get("strength") is not None:
                        uid = self.create_or_get_numeric_value(
                            ingredient["strength"], UNIT_SUBSET_DOSE
                        )
                        if uid is not None:
                            ing_data["strength_uid"] = uid
                    for lagtime in ingredient.get("lag_times", []):
                        uid = self.create_or_get_lag_time(lagtime)
                        self.append_if_not_none(ing_data["lag_time_uids"], uid)
                    formul_data["ingredients"].append(ing_data)
                data["formulations"].append(formul_data)

            payload = make_payload("/concepts/pharmaceutical-products", data)

            # print("--- product to post")
            # print(json.dumps(payload, indent=2))

            # Create
            self.post_or_patch_item(
                payload,
                "external_id",
                existing_products_by_id,
                self.compare_pharmaceutical_products,
            )

    def compare_medicinal_products(self, new, existing):
        single_values = [
            "external_id",
            "name",
            "name_sentence_case",
            "library_name",
            ("compound_uid", "compound.uid"),
            ("dispenser_uid", "dispenser.term_uid"),
            ("delivery_device_uid", "delivery_device.term_uid"),
        ]
        if not self.compare_simple_properties(new, existing, single_values):
            return False

        list_values = [
            ("dose_value_uids", "dose_values.uid"),
            ("dose_frequency_uids", "dose_frequencies.term_uid"),
            # ("delivery_device_uids", "delivery_devices.term_uid"),
            # ("dispenser_uids", "dispensers.term_uid"),
            ("pharmaceutical_product_uids", "pharmaceutical_products.uid"),
        ]
        return self.compare_list_properties(new, existing, list_values)

    @open_file()
    def handle_medicinal_products(self, datafile):
        import_data = json.load(datafile)

        existing_med_products = self.api.get_all_from_api(
            "/concepts/medicinal-products"
        )
        existing_med_products_by_id = {
            x["external_id"]: x for x in existing_med_products
        }

        ph_products = self.api.get_all_from_api("/concepts/pharmaceutical-products")
        ph_products_by_id = {x["external_id"]: x for x in ph_products}

        compounds = self.api.get_all_from_api("/concepts/compounds")
        compounds_by_name = {x["name"]: x for x in compounds}

        for row in import_data:
            self.log.info(f'Process medicinal product {row["external_id"]}')

            data = fill_template(row, import_templates.medicinal_product)

            for val in row["dose_values"]:
                uid = self.create_or_get_numeric_value(val, UNIT_SUBSET_DOSE)
                self.append_if_not_none(data["dose_value_uids"], uid)

            compound_uid = compounds_by_name.get(
                row.get("compound", {}).get("name"), {}
            ).get("uid")
            data["compound_uid"] = compound_uid

            for freq in row.get("dose_frequencies") or []:
                uid = self.lookup_codelist_term_uid(
                    CODELIST_FREQUENCY, freq.get("name")
                )
                self.append_if_not_none(data["dose_frequency_uids"], uid)

            dispenser_uid = (
                self.lookup_codelist_term_uid(
                    CODELIST_COMPOUND_DISPENSED_IN, row.get("dispenser", {}).get("name")
                )
                if row.get("dispenser") is not None
                else None
            )
            data["dispenser_uid"] = dispenser_uid

            delivery_device_uid = (
                self.lookup_codelist_term_uid(
                    CODELIST_DELIVERY_DEVICE, row.get("delivery_device", {}).get("name")
                )
                if row.get("delivery_device") is not None
                else None
            )
            data["delivery_device_uid"] = delivery_device_uid

            for ph_prod in row["pharmaceutical_products"]:
                id = ph_prod["external_id"]
                uid = ph_products_by_id.get(id, {}).get("uid")
                self.append_if_not_none(data["pharmaceutical_product_uids"], uid)

            payload = make_payload("/concepts/medicinal-products", data)

            # print("--- product to post")
            # print(json.dumps(payload, indent=2))

            # Create
            self.post_or_patch_item(
                payload,
                "external_id",
                existing_med_products_by_id,
                self.compare_medicinal_products,
            )

    def run(self):
        self.log.info("Importing active substances")
        self.handle_active_substances(MDR_MIGRATION_ACTIVE_SUBSTANCES)
        self.log.info("Importing pharmaceutical products")
        self.handle_pharmaceutical_products(MDR_MIGRATION_PHARMACEUTICAL_PRODUCTS)
        self.log.info("Importing compounds")
        self.handle_compounds(MDR_MIGRATION_COMPOUNDS)
        self.log.info("Importing medicinal products")
        self.handle_medicinal_products(MDR_MIGRATION_MEDICINAL_PRODUCTS)


def main():
    metr = Metrics()
    migrator = Compounds(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
