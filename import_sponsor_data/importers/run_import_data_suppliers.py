# pylint: disable=logging-fstring-interpolation
import csv

from .functions.parsers import map_boolean
from .functions.utils import load_env
from .utils.importer import BaseImporter, open_file
from .utils.metrics import Metrics

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
API_BASE_URL = load_env("API_BASE_URL")


class DataSuppliers(BaseImporter):
    logging_name = "data_suppliers"

    def __init__(self, api=None, metrics_inst=None):
        super().__init__(api=api, metrics_inst=metrics_inst)

    @open_file()
    def handle_data_suppliers(self, csvfile):
        csv_data = csv.DictReader(csvfile)
        data_suppliers_in_csv = {item["NAME"]: item for item in csv_data}

        data_supplier_types_terms = {
            term["name"]["sponsor_preferred_name"]: term["term_uid"]
            for term in self.fetch_codelist_terms("Data Supplier Type")
        }
        origin_sources_terms = {
            term["name"]["sponsor_preferred_name"]: term["term_uid"]
            for term in self.fetch_codelist_terms("Origin Source")
        }
        origin_types_terms = {
            term["name"]["sponsor_preferred_name"]: term["term_uid"]
            for term in self.fetch_codelist_terms("Origin Type")
        }

        for data_supplier_name, data_supplier_data in data_suppliers_in_csv.items():
            data = {
                "path": "data-suppliers",
                "body": {
                    "name": data_supplier_name,
                    "description": data_supplier_data["DESCRIPTION"],
                    "api_base_url": data_supplier_data["API_BASE_URL"],
                    "ui_base_url": data_supplier_data["UI_BASE_URL"],
                    "order": data_supplier_data["ORDER"],
                    "supplier_type_uid": data_supplier_types_terms[
                        data_supplier_data["TYPE_TERM_SPONSOR_NAME"]
                    ],
                    "origin_source_uid": origin_sources_terms[
                        data_supplier_data["ORIGIN_SOURCE_TERM_SPONSOR_NAME"]
                    ],
                    "origin_type_uid": origin_types_terms[
                        data_supplier_data["ORIGIN_TYPE_TERM_SPONSOR_NAME"]
                    ],
                },
            }

            self.log.info(f"Add data supplier '{data['body']['name']}'")

            rs = self.api.post_to_api(data)

            if rs is not None and map_boolean(data_supplier_data["is_retired"]):
                self.api.delete_to_api(f'{data["path"]}/{rs["uid"]}/activations')

    def run(self):
        data_suppliers = load_env("MDR_DATA_SUPPLIERS")
        self.log.info("Importing data suppliers")

        self.handle_data_suppliers(data_suppliers)

        self.log.info("Done importing data suppliers")


def main():
    metr = Metrics()
    migrator = DataSuppliers(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
