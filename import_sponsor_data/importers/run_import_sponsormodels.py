import asyncio
import csv
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from typing import Any

import aiohttp

from importers.functions.caselessdict import CaselessDict
from importers.functions.utils import load_env
from importers.utils.importer import BaseImporter, open_file_async
from importers.utils.metrics import Metrics
from importers.utils.sponsor_model_schema import (
    DEFAULT_LIBRARY,
    DEFAULT_SCHEMA_VERSION,
    PropertyDefinition,
    PropertyType,
    SponsorModelSchema,
)

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False") == "True"
API_BASE_URL = load_env("API_BASE_URL")

MDR_MIGRATION_ACTIVITY_INSTANCE_CLASS_MODEL_RELS = load_env(
    "MDR_MIGRATION_ACTIVITY_INSTANCE_CLASS_MODEL_RELS"
)
MDR_MIGRATION_ACTIVITY_ITEM_CLASS_MODEL_RELS = load_env(
    "MDR_MIGRATION_ACTIVITY_ITEM_CLASS_MODEL_RELS"
)
MDR_MIGRATION_ACTIVITY_ITEM_CLASS_VALID_CODELIST_RELS = load_env(
    "MDR_MIGRATION_ACTIVITY_ITEM_CLASS_VALID_CODELIST_RELS"
)
MDR_MIGRATION_SPONSOR_MODEL_DIRECTORY = load_env(
    "MDR_MIGRATION_SPONSOR_MODEL_DIRECTORY"
)
MDR_MIGRATION_SPONSOR_MODEL_DATASETS = load_env("MDR_MIGRATION_SPONSOR_MODEL_DATASETS")
MDR_MIGRATION_SPONSOR_MODEL_DATASET_VARIABLES = load_env(
    "MDR_MIGRATION_SPONSOR_MODEL_DATASET_VARIABLES"
)
MDR_MIGRATION_SPONSOR_MODEL_WRITE_LOGFILE = load_env(
    "MDR_MIGRATION_SPONSOR_MODEL_WRITE_LOGFILE"
)

SPONSOR_MODELS_PATH_PREFIX = "/standards/sponsor-models/"
SPONSOR_MODELS_PATH = SPONSOR_MODELS_PATH_PREFIX + "models"
SPONSOR_MODELS_SCHEMA_PATH = SPONSOR_MODELS_PATH_PREFIX + "schema"
SPONSOR_MODELS_DATASETS_PATH = SPONSOR_MODELS_PATH_PREFIX + "datasets"
SPONSOR_MODELS_DATASET_VARIABLES_PATH = SPONSOR_MODELS_PATH_PREFIX + "dataset-variables"
ACTIVITY_INSTANCE_CLASSES_PATH = "/activity-instance-classes"
ACTIVITY_ITEM_CLASSES_PATH = "/activity-item-classes"


class FieldMapper:  # pylint: disable=too-few-public-methods
    """
    Maps CSV fields to API fields with automatic transformation based on PropertyDefinition.
    """

    def __init__(self, parser_instance):
        """
        Initialize with reference to parser instance for accessing parsing methods.

        Args:
            parser_instance: Instance of SponsorModels class with parsing methods
        """
        self.parser = parser_instance
        self._transformers = {
            PropertyType.STRING: lambda v: v or None,  # Empty string becomes None
            PropertyType.BOOLEAN: self.parser.parse_bool,
            PropertyType.REVERSE_BOOLEAN: lambda v: self.parser.reverse_bool(
                self.parser.parse_bool(v)
            ),
            PropertyType.INTEGER: self.parser.parse_int,
            PropertyType.LIST_SPACE_SEPARATED: lambda v: v.split(" ") if v else None,
            PropertyType.LIST_COMMA_SEPARATED: lambda v: (
                [k.strip() for k in v.split(",")] if v else None
            ),
        }

    def map_row_to_body(
        self,
        headers: list[str],
        row: list[str],
        property_definitions: list[PropertyDefinition],
        include_dynamic_fields: bool = True,
    ) -> dict[str, Any]:
        """
        Map a CSV row to API body based on property definitions.

        Args:
            headers: CSV headers
            row: CSV row values
            property_definitions: List of property definitions
            include_dynamic_fields: Whether to include fields not in definitions - Defaults to True

        Returns:
            Dictionary ready to send to API
        """
        body = {}
        processed_csv_fields = set()

        # Process defined properties
        for prop_def in property_definitions:
            # Skip if conditional check fails
            if prop_def.conditional_check and not prop_def.conditional_check(headers):
                continue

            # Check if field exists in CSV headers
            if prop_def.csv_field not in headers:
                if prop_def.default_value is not None:
                    body[prop_def.api_field] = prop_def.default_value
                elif prop_def.required:
                    raise ValueError(
                        f"Required field '{prop_def.csv_field}' not found in CSV headers"
                    )
                continue

            # Mark as processed
            processed_csv_fields.add(prop_def.csv_field)

            # Get value from row
            value = row[headers.index(prop_def.csv_field)]

            # Apply default_value if cell is empty and a default is provided
            # Note: default_value applies when the CSV header EXISTS but the cell is EMPTY
            # This is different from when the header is missing entirely
            if not value and prop_def.default_value is not None:
                body[prop_def.api_field] = prop_def.default_value
                continue

            # Apply transformation
            if prop_def.custom_transformer:
                transformed_value = prop_def.custom_transformer(value)
            elif prop_def.property_type == PropertyType.CUSTOM:
                raise ValueError(
                    f"PropertyType.CUSTOM requires custom_transformer for field '{prop_def.csv_field}'"
                )
            else:
                transformer = self._transformers[prop_def.property_type]
                transformed_value = transformer(value)

            body[prop_def.api_field] = transformed_value

        # Add dynamic fields (not in definitions)
        if include_dynamic_fields:
            for header in headers:
                if header not in processed_csv_fields:
                    value = row[headers.index(header)]
                    # Sanitize field name: lowercase, replace spaces with underscores
                    field_name = header.lower().replace(" ", "_").replace("-", "_")
                    # Skip if already set by a property definition (e.g. 'Length' would overwrite 'Standard Length' → 'length')
                    if field_name not in body:
                        body[field_name] = value if value else None

        return body


# ---------------------------------------------------------------
# SponsorModels with datasets and variables
# ---------------------------------------------------------------
class SponsorModels(BaseImporter):
    logging_name = "sponsor_models"

    def __init__(self, api=None, metrics_inst=None):
        super().__init__(api=api, metrics_inst=metrics_inst)

        self._common_body_params = {}
        self._model_body_params = {}
        self.logfile_name = (
            f"sponsor_model_import_issues_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
            if MDR_MIGRATION_SPONSOR_MODEL_WRITE_LOGFILE
            else None
        )

        # Initialize field mapper for CSV to API transformations
        self.field_mapper = FieldMapper(self)

        # Per-row {header: cell} context, populated while iterating CSV rows and
        # read by custom transformers (e.g. the dataset Class transformer reads
        # row_context["Table"]).
        self.row_context: dict[str, str] = {}

        # Load the field schema (single source of truth for CSV -> API mapping).
        # Per-model schema version and library are read from model_info.json.
        self._schema_version = DEFAULT_SCHEMA_VERSION
        self._library_name = DEFAULT_LIBRARY
        self.schema = SponsorModelSchema(self)
        # Fail fast at startup if the default schema is missing or invalid.
        self.schema.load(DEFAULT_SCHEMA_VERSION)
        self.log.info(
            "Loaded sponsor model field schema version %s", DEFAULT_SCHEMA_VERSION
        )

    def parse_bool(self, cell: str | None) -> bool | None:
        if cell is None:
            return None
        else:
            return cell in ["Y", "X", "true", "True", "Yes", "1"]

    def reverse_bool(self, boolean: bool | None) -> bool | None:
        if boolean is None:
            return None
        else:
            return False if boolean else True

    def parse_int(self, cell: str | None) -> int | None:
        if cell is None:
            return None
        try:
            return int(cell)
        except (ValueError, TypeError):
            return None

    def parse_instance_class_name(self, name: str) -> str:
        parsed = name.replace("AP ", "AssociatedPersons")
        return parsed

    def parse_item_class_name(self, name: str) -> str:
        return name.replace(" ", "").lower()

    def parse_variable_class_name(self, name: str) -> str:
        return name.replace("__", "--")

    def parse_valid_codelist_uids(self, name: str) -> list[str]:
        return name.split(";")

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

    @open_file_async()
    async def handle_activity_instance_class_relations(
        self, instance_class_csvfile, session
    ):
        api_tasks = []

        # Parse and PATCH ActivityInstanceClasses
        csv_reader = csv.reader(instance_class_csvfile, delimiter=",")
        headers = next(csv_reader)
        existing_instance_classes = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_INSTANCE_CLASSES_PATH),
            identifier="name",
            value="uid",
        )

        existing_instance_classes = {
            self.parse_instance_class_name(i): v
            for i, v in existing_instance_classes.items()
        }

        grouped_items = {}

        for row in csv_reader:
            class_cell = row[headers.index("activity_instance_class")]
            if class_cell:
                activity_instance_class_uid = existing_instance_classes.get(
                    self.parse_instance_class_name(class_cell),
                    None,
                )
                if activity_instance_class_uid is not None:
                    grouped_items[activity_instance_class_uid] = row[
                        headers.index("dataset_class")
                    ]

        for instance_class_uid, dataset in grouped_items.items():
            data = {
                "body": {
                    "dataset_class_uid": dataset,
                },
            }
            self.log.info(
                "Adding relationship to dataset for activity instance class '%s'",
                instance_class_uid,
            )
            api_tasks.append(
                self.api.patch_to_api_async(
                    path=f"{ACTIVITY_INSTANCE_CLASSES_PATH}/{instance_class_uid}/model-mappings",
                    body=data["body"],
                    session=session,
                )
            )

        # Finally, push all tasks
        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def handle_activity_item_class_relations(self, item_class_csvfile, session):
        api_tasks = []

        # Parse and PATCH ActivityItemClasses
        csv_reader = csv.reader(item_class_csvfile, delimiter=",")
        headers = next(csv_reader)
        existing_item_classes = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_ITEM_CLASSES_PATH),
            identifier="name",
            value="uid",
        )

        existing_item_classes = {
            self.parse_item_class_name(i): v for i, v in existing_item_classes.items()
        }

        grouped_items = defaultdict(list)

        for row in csv_reader:
            class_cell = row[headers.index("activity_item_class")]
            if class_cell:
                activity_item_class_uid = existing_item_classes.get(
                    self.parse_item_class_name(class_cell),
                    None,
                )
                if activity_item_class_uid is not None:
                    variable_class_uid = self.parse_variable_class_name(
                        row[headers.index("variable_class")]
                    )
                    # There are some duplicates in the CSV file
                    if variable_class_uid not in grouped_items[activity_item_class_uid]:
                        grouped_items[activity_item_class_uid].append(
                            variable_class_uid
                        )

        for item_class_uid, variables in grouped_items.items():
            data = {
                "body": {
                    "variable_class_uids": variables,
                },
            }
            self.log.info(
                "Adding relationships to variables for activity item class '%s'",
                item_class_uid,
            )
            api_tasks.append(
                self.api.patch_to_api_async(
                    path=f"{ACTIVITY_ITEM_CLASSES_PATH}/{item_class_uid}/model-mappings",
                    body=data["body"],
                    session=session,
                )
            )

        # Finally, push all tasks
        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def handle_activity_item_class_valid_codelist_relations(
        self, item_class_csvfile, session
    ):
        api_tasks = []

        # Parse and PATCH ActivityItemClasses
        csv_reader = csv.reader(item_class_csvfile, delimiter=",")
        headers = next(csv_reader)
        existing_item_classes = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_ITEM_CLASSES_PATH),
            identifier="name",
            value="uid",
        )

        existing_item_classes = {
            self.parse_item_class_name(i): v for i, v in existing_item_classes.items()
        }

        all_codelist_uids = self._get_codelists_uid_and_submval()
        for row in csv_reader:
            class_cell = row[headers.index("activity_item_class")]
            if class_cell:
                activity_item_class_uid = existing_item_classes.get(
                    self.parse_item_class_name(class_cell),
                    None,
                )
                if activity_item_class_uid is not None:
                    codelist_names = self.parse_valid_codelist_uids(
                        row[headers.index("codelist")]
                    )
                    codelist_uids = [
                        all_codelist_uids.get(codelist_submval)
                        for codelist_submval in codelist_names
                    ]
                    data = {"body": {"valid_codelist_uids": codelist_uids}}
                    self.log.info(
                        "Adding relationships to valid codelists for activity item class '%s'",
                        activity_item_class_uid,
                    )
                    api_tasks.append(
                        self.api.patch_to_api_async(
                            path=f"{ACTIVITY_ITEM_CLASSES_PATH}/{activity_item_class_uid}/valid-codelist-mappings",
                            body=data["body"],
                            session=session,
                        )
                    )

        # Finally, push all tasks
        await asyncio.gather(*api_tasks)

    async def handle_schemas(self, session):
        """
        Register every available field-schema version with the API.

        Sponsor models reference a schema_version; the schema itself is posted
        here (as raw YAML text) so the API holds the source of truth. Run once,
        before sponsor models are created.

        Schemas are posted sequentially, in ascending (library, version) order,
        so that successive versions of the same schema root are created in order
        (v1 before v2, ...). ``available_schemas()`` already returns them sorted;
        we must not fan them out concurrently, which would lose that ordering.
        """
        for schema in self.schema.available_schemas():
            self.log.info(
                "Posting field schema '%s' version %s",
                schema["library_name"],
                schema["schema_version"],
            )
            await self.api.post_to_api_async(
                url=SPONSOR_MODELS_SCHEMA_PATH,
                body=schema,
                session=session,
                logfile_name=self.logfile_name,
            )

    async def handle_sponsor_model(self, session) -> bool:
        existing_sponsor_models = self.api.get_all_identifiers(
            self.api.get_all_from_api(SPONSOR_MODELS_PATH),
            identifier="name",
            value="uid",
        )

        sponsor_model_name = self._common_body_params["sponsor_model_name"]
        if sponsor_model_name in existing_sponsor_models:
            self.log.info(
                f"Sponsor model version {sponsor_model_name} already exists in database. Skipping import."
            )
            return False

        api_tasks = []

        data = {
            "body": self._model_body_params,
        }
        self.log.info(
            f"Add sponsor model for Implementation Guide '{data['body']['ig_uid']}' version '{data['body']['ig_version_number']}'"
        )

        api_tasks.append(
            self.api.post_to_api_async(
                url=SPONSOR_MODELS_PATH,
                body=data["body"],
                session=session,
                logfile_name=self.logfile_name,
            )
        )
        await asyncio.gather(*api_tasks)

        return True

    def parse_dataset_class_name(
        self, class_name: str, dataset_name: str | None = None
    ) -> str:
        # First, remove prefixes like AP
        class_name = class_name.replace("AP ", "")

        # In case the class_name passed is "CO" or "DM" or similar
        # Then it should become "Special-Purpose-CO" - see below
        if dataset_name is None:
            if len(class_name) == 2:
                dataset_name = class_name
                class_name = "Special-Purpose"

        # Sentence case
        class_name = class_name.title()

        # Switch some special names
        if class_name in ["Identifiers", "Timing"]:
            class_name = "General Observations"

        # Transform spaces
        # But first, "Special Purpose" needs a dash
        if "Special Purpose" in class_name:
            class_name = "Special-Purpose"
        class_name = class_name.replace(" ", "__")

        # Treat classes that require su ffix with dataset name
        # For example, "APDM" -> "Special-Purpose-DM"
        if class_name in [
            "Relationship",
            "Special-Purpose",
            "Study__Reference",
            "Trial__Design",
        ]:
            dataset_name = (
                dataset_name.replace("AP", "")
                if dataset_name.startswith("AP")
                else dataset_name
            )
            class_name = f"{class_name}-{dataset_name}"

        return class_name

    @open_file_async()
    async def handle_datasets(self, csvfile, session):
        """
        Populate sponsor model datasets using the field mapper system.

        This method:
        - Automatically maps CSV fields to API fields using PropertyDefinition
        - Applies appropriate transformations based on property types
        - Includes any extra CSV columns not in the property definitions
        """
        csv_reader = csv.reader(csvfile, delimiter=",")
        headers = next(csv_reader)
        api_tasks = []

        # Get property definitions for datasets from the loaded schema
        property_definitions = self.schema.get_property_definitions(
            "dataset", self._schema_version, self._library_name
        )

        # Auto-increment enrich_build_order when the CSV has no 'enrich_build_order' column
        # Replace with sponsor-specific name if necessary
        order_auto = "enrich_build_order" not in headers
        enrich_build_order_counter = 0

        for row in csv_reader:
            # Store row context for custom transformers that need it (e.g., parse_dataset_class_name)
            self.row_context = {headers[i]: row[i] for i in range(len(headers))}

            # Map CSV row to API body using field mapper
            body = self.field_mapper.map_row_to_body(
                headers=headers,
                row=row,
                property_definitions=property_definitions,
                include_dynamic_fields=True,  # Include any extra CSV columns
            )

            # Auto-assign enrich_build_order when the CSV has no 'enrich_build_order' column
            if order_auto:
                enrich_build_order_counter += 1
                body["enrich_build_order"] = enrich_build_order_counter

            # Add common parameters
            body.update(self._common_body_params)

            data = {"body": body}

            self.log.info(
                f"Add sponsor model dataset '{data['body']['dataset_uid']}' to sponsor model '{data['body']['sponsor_model_name']}'"
            )
            api_tasks.append(
                self.api.post_to_api_async(
                    url=SPONSOR_MODELS_DATASETS_PATH,
                    body=data["body"],
                    session=session,
                    logfile_name=self.logfile_name,
                )
            )

            # If relevant, add a sponsor term to the Domain codelist
            if data["body"]["is_basic_std"] is False:
                term_data = {
                    "body": {
                        "catalogue_names": ["SDTM CT"],
                        "codelists": [
                            {
                                "codelist_uid": "C66734",
                                "submission_value": data["body"]["dataset_uid"],
                                "order": data["body"]["enrich_build_order"],
                            }
                        ],
                        "nci_preferred_name": "UNK",
                        "definition": data["body"]["comment"],
                        "sponsor_preferred_name": data["body"]["label"],
                        "sponsor_preferred_name_sentence_case": data["body"][
                            "label"
                        ].lower(),
                        "library_name": self._common_body_params["library_name"],
                    },
                }
                api_tasks.append(
                    self.api.post_to_api_async(
                        url="/ct/terms",
                        body=term_data["body"],
                        session=session,
                        logfile_name=self.logfile_name,
                    )
                )

        await asyncio.gather(*api_tasks)

    # Get a dictionary mapping submission values to term uids for a codelist identified by its uid
    def _get_submissionvalues_for_codelist(self, cl_uid):
        terms = self.api.get_all_from_api(f"/ct/codelists/{cl_uid}/terms")
        submvals = CaselessDict(
            self.api.get_all_identifiers(
                terms,
                identifier="submission_value",
                value="term_uid",
            )
        )
        return submvals

    def parse_referenced_ct(self, headers, row, all_codelist_uids) -> tuple[dict, dict]:
        # Sponsor specific code
        # Custom logic to extract CT relationships at sponsor model level
        references_codelists = []
        references_terms = []
        xml_codelist_multi = self.parse_bool(row[headers.index("xmlcodelist_multi")])
        term = row[headers.index("term")] or None
        # Some Variables link to multiple codelists
        if xml_codelist_multi is True and term != "*":
            for submval in row[headers.index("term")].split("|"):
                submval = re.sub(r"[()]", "", submval)
                if submval in all_codelist_uids:
                    references_codelists.append(all_codelist_uids.get(submval))
        # All others link to a single one
        else:
            _codelist_uid = all_codelist_uids.get(row[headers.index("xmlcodelist")])
            if _codelist_uid:
                references_codelists.append(_codelist_uid)

                # Variables referencing a single codelist can reference specific Terms too
                # As a subset of the referenced codelist
                if row[headers.index("xmlcodelistvalues")]:
                    terms_in_codelist = self._get_submissionvalues_for_codelist(
                        _codelist_uid
                    )
                    for term_submval in row[headers.index("xmlcodelistvalues")].split(
                        "|"
                    ):
                        # Known special case
                        if term_submval == "U":
                            term_submval = "UNKNOWN"
                        if term_submval in terms_in_codelist:
                            references_terms.append(terms_in_codelist[term_submval])
        return references_codelists, references_terms

    @open_file_async()
    async def handle_dataset_variables(self, csvfile, session):
        """
        Populate sponsor model dataset variables using the field mapper system.

        This method:
        - Automatically maps CSV fields to API fields using PropertyDefinition
        - Applies appropriate transformations based on property types
        - Includes any extra CSV columns not in the property definitions
        - Handles special CT references separately (not in property definitions)
        """
        csv_reader = csv.reader(csvfile, delimiter=",")
        headers = next(csv_reader)
        api_tasks = []

        all_codelist_uids = self.api.get_codelists_uid_and_submval()

        # Get property definitions for dataset variables from the loaded schema
        property_definitions = self.schema.get_property_definitions(
            "dataset_variable", self._schema_version, self._library_name
        )

        # Per-dataset order counter: used when the CSV has no order column
        # Replace with sponsor-specific name if necessary
        order_auto = "order" not in headers
        order_counters: dict[str, int] = defaultdict(int)

        for row in csv_reader:
            # Store row context for custom transformers
            self.row_context = {headers[i]: row[i] for i in range(len(headers))}

            # Parse CT references (special handling not in property definitions)
            references_codelists, references_terms = self.parse_referenced_ct(
                headers=headers, row=row, all_codelist_uids=all_codelist_uids
            )

            # Map CSV row to API body using field mapper
            body = self.field_mapper.map_row_to_body(
                headers=headers,
                row=row,
                property_definitions=property_definitions,
                include_dynamic_fields=True,  # Include any extra CSV columns
            )

            # Auto-assign order when the CSV has no Order column: 1-based counter per DataSet
            if order_auto:
                order_counters[body["dataset_uid"]] += 1
                body["order"] = order_counters[body["dataset_uid"]]

            # Add CT references (not handled by property definitions)
            body["references_codelists"] = references_codelists
            body["references_terms"] = references_terms

            # Add common parameters
            body.update(self._common_body_params)

            data = {"body": body}

            self.log.info(
                f"Add sponsor model variable '{data['body']['dataset_variable_uid']}' to dataset '{data['body']['dataset_uid']}'"
            )
            api_tasks.append(
                self.api.post_to_api_async(
                    url=SPONSOR_MODELS_DATASET_VARIABLES_PATH,
                    body=data["body"],
                    session=session,
                    logfile_name=self.logfile_name,
                )
            )
        await asyncio.gather(*api_tasks)

    async def async_run(self):
        timeout = aiohttp.ClientTimeout(None)
        conn = aiohttp.TCPConnector(limit=4, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
            await self.handle_activity_instance_class_relations(
                MDR_MIGRATION_ACTIVITY_INSTANCE_CLASS_MODEL_RELS,
                session,
            )
            await self.handle_activity_item_class_relations(
                MDR_MIGRATION_ACTIVITY_ITEM_CLASS_MODEL_RELS,
                session,
            )
            await self.handle_activity_item_class_valid_codelist_relations(
                MDR_MIGRATION_ACTIVITY_ITEM_CLASS_VALID_CODELIST_RELS,
                session,
            )

            # Register all field-schema versions before any sponsor model
            # references one via its schema_version.
            await self.handle_schemas(session)

            # For each subfolder in the sponsor models folder, import the corresponding sponsor model
            for root, dirs, _ in os.walk(MDR_MIGRATION_SPONSOR_MODEL_DIRECTORY):
                dirs.sort()
                for dir_name in dirs:
                    sponsor_model_path = os.path.join(root, dir_name)
                    model_info_path = os.path.join(
                        sponsor_model_path, "model_info.json"
                    )

                    # Subfolders without a model_info.json - such as the shared
                    # 'schemas' folder - are not sponsor models.
                    if not os.path.isfile(model_info_path):
                        self.log.debug(
                            "Skipping '%s', no model_info.json found",
                            sponsor_model_path,
                        )
                        continue

                    # Open file model_info.json in directory
                    with open(model_info_path) as f:
                        model_info = json.load(f)
                        if "exclude" in model_info and model_info["exclude"]:
                            self.log.info(
                                f"Skipping sponsor model '{model_info['sponsor_model_name']}'"
                            )
                            continue
                        library_name = model_info.get("library_name", DEFAULT_LIBRARY)
                        self._library_name = library_name

                        # Which field-schema version this sponsor model follows.
                        # Defaults to 1 when absent. Loading validates it (and
                        # fails fast if that library/version schema file is missing).
                        self._schema_version = model_info.get(
                            "schema_version", DEFAULT_SCHEMA_VERSION
                        )
                        self.schema.load(self._schema_version, self._library_name)
                        self.log.info(
                            "Sponsor model '%s' uses field schema '%s' version %s",
                            model_info["sponsor_model_name"],
                            self._library_name,
                            self._schema_version,
                        )

                        self._common_body_params = {
                            "target_data_model_catalogue": model_info["ig_uid"],
                            "sponsor_model_name": model_info["sponsor_model_name"],
                            "sponsor_model_version_number": model_info[
                                "sponsor_model_version_number"
                            ],
                            "library_name": library_name,
                        }

                        self._model_body_params = {
                            "ig_uid": model_info["ig_uid"],
                            "ig_version_number": model_info["ig_version_number"],
                            "version_number": model_info[
                                "sponsor_model_version_number"
                            ],
                            "library_name": library_name,
                            "schema_version": self._schema_version,
                        }
                        if "name_qualifier" in model_info:
                            self._model_body_params["name_qualifier"] = model_info[
                                "name_qualifier"
                            ]

                    continue_import = await self.handle_sponsor_model(session)
                    if continue_import:
                        await self.handle_datasets(
                            os.path.join(
                                sponsor_model_path, MDR_MIGRATION_SPONSOR_MODEL_DATASETS
                            ),
                            session,
                        )
                        await self.handle_dataset_variables(
                            os.path.join(
                                sponsor_model_path,
                                MDR_MIGRATION_SPONSOR_MODEL_DATASET_VARIABLES,
                            ),
                            session,
                        )

    def run(self):
        self.log.info("Importing sponsor models")

        # Create a file to log issues
        if self.logfile_name:
            with open(self.logfile_name, "w") as f:
                f.write("Sponsor Model Import Issues\n")

        asyncio.run(self.async_run())
        self.log.info("Done importing sponsor models")


def main():
    metr = Metrics()
    migrator = SponsorModels(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
