import copy
from abc import ABC, abstractmethod
from typing import Any, Generic

from neo4j.graph import Node
from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.concepts.utils import (
    list_concept_wildcard_properties,
)
from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameterTermRoot,
)
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    calculate_total_count_from_query_result,
    sb_clear_cache,
    validate_filter_by_dict,
    validate_filters_and_add_search_string,
)
from common.config import settings
from common.exceptions import NotFoundException


class ConceptGenericRepository(
    LibraryItemRepositoryImplBase, Generic[_AggregateRootType], ABC
):
    root_class = type
    value_class = type
    return_model: type = BaseModel
    filter_query_parameters: dict[Any, Any] = {}
    sort_by: dict[Any, Any] | None = None
    wildcard_properties_list: list[str] | None = None

    @abstractmethod
    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> _AggregateRootType:
        raise NotImplementedError

    @abstractmethod
    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> _AggregateRootType:
        raise NotImplementedError

    @abstractmethod
    def specific_alias_clause(self, **kwargs) -> str:
        """
        Methods is overridden in the ConceptGenericRepository subclasses
        and it contains matches and traversals specific for domain object represented by subclass repository.
        :return str:
        """

    def specific_header_match_clause(self) -> str | None:
        return None

    # pylint: disable=unused-argument
    def specific_header_match_clause_lite(self, field_name: str) -> str | None:
        """This is a lightweight version of the header match clause.
        It should fetch only the required field, without supporting wildcard filtering.
        """
        return None

    def _create_new_value_node(self, ar: _AggregateRootType) -> VersionValue:
        return self.value_class(  # type: ignore[call-overload]
            nci_concept_id=getattr(ar.concept_vo, "nci_concept_id", None),
            nci_concept_name=getattr(ar.concept_vo, "nci_concept_name", None),
            name=ar.concept_vo.name,
            name_sentence_case=ar.concept_vo.name_sentence_case,
            definition=ar.concept_vo.definition,
            abbreviation=ar.concept_vo.abbreviation,
            external_id=getattr(ar.concept_vo, "external_id", None),
        )

    def _has_data_changed(self, ar: _AggregateRootType, value: VersionValue) -> bool:
        return (
            ar.concept_vo.name != value.name
            or getattr(ar.concept_vo, "nci_concept_id", None)
            != getattr(value, "nci_concept_id", None)
            or getattr(ar.concept_vo, "nci_concept_name", None)
            != getattr(value, "nci_concept_name", None)
            or ar.concept_vo.name_sentence_case != value.name_sentence_case
            or ar.concept_vo.definition != value.definition
            or ar.concept_vo.abbreviation != value.abbreviation
            or getattr(ar.concept_vo, "external_id", None)
            != getattr(value, "external_id", None)
        )

    def generate_uid(self) -> str:
        return self.root_class.get_next_free_uid_and_increment_counter()

    def generic_match_clause(self, **kwargs):
        concept_label = self.root_class.__label__
        concept_value_label = self.value_class.__label__

        version = kwargs.get("version", None)
        rel = (
            "hv:HAS_VERSION WHERE hv.version = $requested_version"
            if version is not None
            else ":LATEST"
        )

        return f"""CYPHER runtime=slotted MATCH (concept_root:{concept_label})-[{rel}]->(concept_value:{concept_value_label})"""

    def minimal_count_query(
        self,
        filter_by: dict[str, dict[str, Any]] | None,
        return_all_versions: bool,
        library: str | None = None,
        **kwargs,
    ) -> tuple[str | None, dict[str, Any]]:
        concept_label = self.root_class.__label__
        concept_value_label = self.value_class.__label__

        if self._has_uid_and_library_on_parent_root():
            concept_root = "parent_root"
            library_relationship = self.parent_root_class.LIBRARY_REL_LABEL
        else:
            concept_root = "concept_root"
            library_relationship = self.root_class.LIBRARY_REL_LABEL

        # we do not support minimal count queries when a specific version is requested
        if kwargs.get("version", None) is not None:
            return None, {}

        filter_by = validate_filter_by_dict(filter_by)
        # no filters, we can return a minimal count query
        if not filter_by or len(filter_by) == 0:
            if return_all_versions:
                # when all versions are requested, we need to count the Value nodes
                query = f"""MATCH ({concept_root}:{concept_label})-[hv:HAS_VERSION]->(concept_value:{concept_value_label}) RETURN count(DISTINCT hv) AS count"""
                return query, {}
            # when only latest versions are requested, count roots with a LATEST (Final) version,
            # applying the same library filter used for the items query
            if library:
                query = (
                    f"MATCH (lib:Library {{name: $library_name}})-[:{library_relationship}]->({concept_root}:{concept_label})-[:LATEST]->(:{concept_value_label})"
                    f" RETURN count(DISTINCT {concept_root}) AS count"
                )
                return query, {"library_name": library}
            # default: exclude archived concepts (same as create_query_filter_statement with library=None)
            query = (
                f"MATCH (lib:Library)-[:{library_relationship}]->({concept_root}:{concept_label})-[:LATEST]->(:{concept_value_label})"
                f" WHERE lib.name <> $excluded_library_name RETURN count(DISTINCT {concept_root}) AS count"
            )
            return query, {"excluded_library_name": settings.archived_library_name}

        # if the only filter is for status, we return a specific count query
        if len(filter_by) == 1 and "status" in filter_by and not return_all_versions:
            query = f"""
                MATCH ({concept_root}:{concept_label})-[hv:HAS_VERSION]->(concept_value:{concept_value_label})
                WHERE hv.end_date IS NULL AND hv.status IN $status
                RETURN count(DISTINCT {concept_root}) AS count
            """
            params = {"status": filter_by["status"]["v"]}
            return query, params
        # else, a generic count query needs to be used
        return None, {}

    def generic_alias_clause(self, **kwargs):
        version = kwargs.get("version", None)
        where_version = (
            "WHERE hv.version = $requested_version" if version is not None else ""
        )

        return f"""
            DISTINCT concept_root, concept_value,
            head([(library)-[:CONTAINS_CONCEPT]->(concept_root) | library]) AS library
            CALL (concept_root, concept_value) {{
                MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
                {where_version}
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS version_rel
            }}
            WITH
                concept_root,
                concept_root.uid AS uid,
                concept_value as concept_value,
                library,
                version_rel
                CALL (version_rel) {{
                    OPTIONAL MATCH (author: User)
                    WHERE author.user_id = version_rel.author_id
                    RETURN author
                }}
            WITH
                uid,
                concept_root,
                concept_value.nci_concept_id AS nci_concept_id,
                concept_value.nci_concept_name AS nci_concept_name,
                concept_value.name AS name,
                concept_value.name_sentence_case AS name_sentence_case,
                concept_value.external_id AS external_id,
                concept_value.definition AS definition,
                concept_value.abbreviation AS abbreviation,
                CASE WHEN concept_value:TemplateParameterTermValue THEN true ELSE false END AS template_parameter,
                library,
                library.name AS library_name,
                library.is_editable AS is_library_editable,
                version_rel.start_date AS start_date,
                version_rel.end_date AS end_date,
                version_rel.status AS status,
                version_rel.version AS version,
                version_rel.change_description AS change_description,
                version_rel.author_id AS author_id,
                coalesce(author.username, version_rel.author_id) AS author_username,
                concept_value
        """

    def generic_alias_clause_all_versions(self):
        return """
            DISTINCT concept_root, concept_value,
            head([(library)-[:CONTAINS_CONCEPT]->(concept_root) | library]) AS library
            CALL (concept_root, concept_value) {
                MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                RETURN hv AS version_rel
            }
            WITH
                concept_root,
                concept_root.uid AS uid,
                concept_value as concept_value,
                library.name AS library_name,
                library.is_editable AS is_library_editable,
                version_rel
                CALL (version_rel) {
                    OPTIONAL MATCH (author: User)
                    WHERE author.user_id = version_rel.author_id
                    RETURN author
                }    
            WITH
                uid,
                concept_root,
                concept_value.nci_concept_id AS nci_concept_id,
                concept_value.nci_concept_name AS nci_concept_name,
                concept_value.name AS name,
                concept_value.name_sentence_case AS name_sentence_case,
                concept_value.external_id AS external_id,
                concept_value.definition AS definition,
                concept_value.abbreviation AS abbreviation,
                CASE WHEN concept_value:TemplateParameterTermValue THEN true ELSE false END AS template_parameter,
                library_name,
                is_library_editable,
                version_rel.start_date AS start_date,
                version_rel.end_date AS end_date,
                version_rel.status AS status,
                version_rel.version AS version,
                version_rel.change_description AS change_description,
                version_rel.author_id AS author_id,
                coalesce(author.username, version_rel.author_id) AS author_username,
                concept_value
        """

    def generic_match_clause_all_versions(self):
        return self.generic_match_clause()

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict[Any, Any]]:
        statements = []
        params = {}

        if self._has_uid_and_library_on_parent_root():
            concept_root = "parent_root"
            library_relationship = self.parent_root_class.LIBRARY_REL_LABEL
        else:
            concept_root = "concept_root"
            library_relationship = self.root_class.LIBRARY_REL_LABEL

        library_filter = (
            "EXISTS { MATCH (library:Library {name: $library_name})-[:%s]->(%s) }"
            % (library_relationship, concept_root)
        )

        if library:
            statements.append(library_filter)
            params["library_name"] = library

        else:
            # Exclude archived concepts when no library is specified
            statements.append(f"NOT {library_filter}")
            params["library_name"] = settings.archived_library_name

        if uids := kwargs.get("uids"):
            statements.append(f"{concept_root}.uid IN $uids")
            params["uids"] = uids

        statement = f"WHERE {' AND '.join(statements)}"
        return statement, params

    @classmethod
    # pylint: disable=unused-argument
    def format_filter_sort_keys(cls, key: str):
        """
        Maps a fieldname as provided by the API query (equal to output model) to the same fieldname as defined in the database and/or Cypher query

        :param key: Fieldname to map
        :return str:
        """
        return key

    @classmethod
    def format_filter_sort_keys_for_headers_lite(cls, key: str):
        """
        Maps a fieldname as provided by the API query (equal to output model) to the corresponding fieldname as defined in the database and/or Cypher query

        :param key: Fieldname to map
        :return str:
        """
        return key.replace(".", "_")

    def find_by_uid(
        self,
        uid: str,
        *,
        version: str | None = None,
    ) -> _AggregateRootType | None:
        """Single-query read-only lookup by UID.

        Uses the Cypher-based find_all path (one DB round-trip) instead of
        the neomodel ORM find_by_uid_2 path which issues many separate queries.
        Not suitable for write operations — use find_by_uid_2(for_update=True) for those.
        """
        results, _ = self.find_all(uids=[uid], version=version)
        return results[0] if results else None

    def find_all(
        self,
        library: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        return_all_versions: bool = False,
        uids: list[str] | None = None,
        **kwargs,
    ) -> tuple[list[_AggregateRootType], int]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Concept aggregates.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param library:
        :param sort_by:
        :param page_number:
        :param page_size:
        :param filter_by:
        :param filter_operator:
        :param total_count:
        :param return_all_versions:
        :return GenericFilteringReturn[_AggregateRootType]:
        """
        match_clause = (
            self.generic_match_clause(**kwargs)
            if not return_all_versions
            else self.generic_match_clause_all_versions()
        )

        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            library=library, uids=uids, **kwargs
        )
        self.filter_query_parameters = filter_query_parameters
        self.sort_by = sort_by

        match_clause += filter_statements

        alias_clause = (
            self.generic_alias_clause(**kwargs)
            if not return_all_versions
            else self.generic_alias_clause_all_versions()
        ) + self.specific_alias_clause(**kwargs)

        minimal_count_query, minimal_count_params = self.minimal_count_query(
            filter_by=filter_by,
            return_all_versions=return_all_versions,
            library=library,
            **kwargs,
        )
        filtering_active = minimal_count_query is None

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
            return_model=self.return_model,
            wildcard_properties_list=self.wildcard_properties_list,
            format_filter_sort_keys=self.format_filter_sort_keys,
            one_element_extra=filtering_active,
        )

        if kwargs.get("version", None) is not None:
            query.parameters.update({"requested_version": kwargs["version"]})

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()

        extracted_items = self._retrieve_concepts_from_cypher_res(
            result_array, attributes_names
        )
        total_amount = calculate_total_count_from_query_result(
            len(extracted_items),
            page_number,
            page_size,
            total_count,
            extra_requested=filtering_active,
        )
        if 0 < page_size < len(extracted_items):
            extracted_items = extracted_items[:page_size]
        if total_amount is None:
            if minimal_count_query is not None:
                count_result, _ = db.cypher_query(
                    query=minimal_count_query, params=minimal_count_params
                )
                total_amount = count_result[0][0] if len(count_result) > 0 else 0
            else:
                total_amount = -1
        return extracted_items, total_amount

    def _retrieve_concepts_from_cypher_res(
        self, result_array, attribute_names
    ) -> list[_AggregateRootType]:
        """
        Method maps the result of the cypher query into real aggregate objects.
        :param result_array:
        :param attribute_names:
        :return Iterable[_AggregateRootType]:
        """
        concept_ars = []
        for concept in result_array:
            concept_dictionary = {}
            for concept_property, attribute_name in zip(concept, attribute_names):
                concept_dictionary[attribute_name] = concept_property
            concept_ars.append(
                self._create_aggregate_root_instance_from_cypher_result(
                    concept_dictionary
                )
            )

        return concept_ars

    def get_distinct_headers(
        self,
        field_name: str,
        search_string: str = "",
        library: str | None = None,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        **kwargs,
    ) -> list[Any]:
        # pylint: disable=unused-argument
        """
        Method runs a cypher query to fetch possible values for a given field_name, with a limit of page_size.
        It uses generic filtering capability, on top of filtering the field_name with provided search_string.

        :param field_name: Field name for which to return possible values
        :param search_string
        :param library:
        :param filter_by:
        :param filter_operator: Same as for generic filtering
        :param page_size: Max number of values to return. Default 10
        :return list[Any]:
        """

        # Add header field name to filter_by, to filter with a CONTAINS pattern
        filter_by = validate_filters_and_add_search_string(
            search_string, field_name, filter_by
        )
        # Match clause
        match_clause = self.generic_match_clause(**kwargs)
        if self.specific_header_match_clause():
            match_clause += self.specific_header_match_clause()

        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            library=library, **kwargs
        )
        match_clause += filter_statements

        # Aliases clause
        alias_clause = self.generic_alias_clause(**kwargs) + self.specific_alias_clause(
            **kwargs
        )

        # Use Cypher query class to use reusable helper methods
        query = CypherQueryBuilder(
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            match_clause=match_clause,
            alias_clause=alias_clause,
            return_model=self.return_model,
            wildcard_properties_list=list_concept_wildcard_properties(
                self.return_model
            ),
            format_filter_sort_keys=self.format_filter_sort_keys,
        )

        query.parameters.update(filter_query_parameters)

        header_alias = self.format_filter_sort_keys(field_name)
        query.full_query = query.build_header_query(
            header_alias=header_alias, page_size=page_size
        )
        result_array, _ = query.execute()

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    def get_distinct_headers_lite(
        self,
        field_name: str,
        search_string: str = "",
        library: str | None = None,
        page_size: int = 10,
        filter_by: dict[str, Any] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        **kwargs,
    ) -> list[Any]:
        match_clause = self.generic_match_clause()

        # Set header field name in the `filter_by` dict,
        # which will be used to generate `WHERE toLower(toString(field_name)) CONTAINS ...` clause
        filter_by = validate_filters_and_add_search_string(
            search_string, field_name, filter_by=filter_by
        )

        # This will allow filtering by library (if specified)
        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            library=library, kwargs=kwargs
        )

        match_clause += filter_statements

        # Specific match clauses for each field, so that only necessary data is fetched

        if field_name in [
            "abbreviation",
            "adam_param_code",
            "analyte_number",
            "comment",
            "compatible_types",
            "contact_person",
            "context",
            "conversion_factor_to_master",
            "convertible_unit",
            "data_type",
            "datatype",
            "definition",
            "description",
            "display_in_tree",
            "display_unit",
            "effective_date",
            "external_id",
            "inn",
            "instruction",
            "is_data_collected",
            "is_data_sharing",
            "is_default_selected_for_activity",
            "is_derived",
            "is_legacy_usage",
            "is_multiple_selection_allowed",
            "is_preferred_synonym",
            "is_reference_data",
            "is_request_final",
            "is_request_rejected",
            "is_required_for_activity",
            "is_research_lab",
            "language",
            "legacy_code",
            "legacy_description",
            "length",
            "long_number",
            "master_unit",
            "molecular_weight",
            "name",
            "name_sentence_case",
            "nci_concept_id",
            "nci_concept_name",
            "oid",
            "order",
            "origin",
            "prefix",
            "prompt",
            "purpose",
            "reason_for_rejecting",
            "repeating",
            "request_rationale",
            "retired_date",
            "sas_dataset_name",
            "sas_field_name",
            "sds_var_name",
            "short_number",
            "si_unit",
            "significant_digits",
            "sponsor_instruction",
            "synonyms",
            "topic_code",
            "url",
            "us_conventional_unit",
            "use_complex_unit_conversion",
            "use_molecular_weight",
            "value",
            "value_regex",
        ]:
            match_clause += f"""
                WITH concept_value.{field_name} AS {field_name}
            """

        elif field_name in ["version", "start_date", "status"]:
            match_clause += """
                CALL (concept_root, concept_value) {
                    MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
                    WITH hv
                    ORDER BY
                        toInteger(split(hv.version, '.')[0]) ASC,
                        toInteger(split(hv.version, '.')[1]) ASC,
                        hv.start_date ASC
                    WITH collect(hv) as hvs
                    RETURN last(hvs) AS version_rel
                }
                WITH version_rel.version AS version,
                     version_rel.start_date AS start_date,
                     version_rel.status AS status
            """

        elif field_name == "library_name":
            match_clause += """
                WITH DISTINCT concept_root,
                    head([(library)-[:CONTAINS_CONCEPT]->(concept_root) | library]) AS library
                WITH library.name AS library_name
            """

        elif field_name == "author_username":
            match_clause += """
                CALL (concept_root, concept_value) {
                    MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
                    WITH hv
                    ORDER BY
                        toInteger(split(hv.version, '.')[0]) ASC,
                        toInteger(split(hv.version, '.')[1]) ASC,
                        hv.start_date ASC
                    WITH collect(hv) as hvs
                    RETURN last(hvs) AS version_rel
                }
                CALL (version_rel) {
                    OPTIONAL MATCH (author: User)
                    WHERE author.user_id = version_rel.author_id
                    RETURN author
                }
                WITH author.username AS author_username
            """

        else:
            if self.specific_header_match_clause_lite(field_name):
                match_clause += self.specific_header_match_clause_lite(field_name)

        query = CypherQueryBuilder(
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            match_clause=match_clause,
            alias_clause=field_name.replace(".", "_"),
            return_model=self.return_model,
            format_filter_sort_keys=self.format_filter_sort_keys_for_headers_lite,
        )

        query.parameters.update(filter_query_parameters)

        query.full_query = query.build_header_query(
            header_alias=field_name.replace(".", "_"), page_size=page_size
        )
        result_array, _ = query.execute()

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save(
        self, item: _AggregateRootType, force_new_value_node: bool = False
    ) -> None:
        if item.uid is not None and item.repository_closure_data is None:
            self._create(item)
        elif item.uid is not None and not item.is_deleted:
            self._update(item, force_new_value_node)
        elif item.is_deleted:
            assert item.uid is not None
            self._soft_delete(item.uid)
        if item.repository_closure_data is not None:
            (
                root,
                _,
                library,
                _,
            ) = item.repository_closure_data
            value = root.has_latest_value.single()

            item.repository_closure_data = (
                root,
                value,
                library,
                copy.deepcopy(item),
            )

    def _soft_delete(self, uid: str) -> None:
        label = self.root_class.__label__
        db.cypher_query(
            f"""
            MATCH (otr:{label} {{uid: $uid}})-[latest_draft:LATEST_DRAFT|LATEST_RETIRED]->(otv)
            WHERE NOT (otr)-[:HAS_VERSION {{version:'Final'}}]->()
            SET otr:Deleted{label}
            WITH otr
            REMOVE otr:{label}
            WITH otr
            MATCH (otr)-[v:HAS_VERSION]->()
            WHERE v.end_date IS NULL
            SET v.end_date = datetime(apoc.date.toISO8601(datetime().epochSeconds, 's'))
            """,
            {"uid": uid},
        )

    def final_concept_exists(self, uid: str) -> bool:
        query = f"""
            MATCH (concept_root:{self.root_class.__label__} {{uid: $uid}})-[:LATEST_FINAL]->(concept_value)
            RETURN concept_root
            """
        result, _ = db.cypher_query(query, {"uid": uid})
        return len(result) > 0 and len(result[0]) > 0

    def final_concept_value(self, uid: str) -> Node | None:
        query = f"""
            MATCH (concept_root:{self.root_class.__label__} {{uid: $uid}})-[:LATEST_FINAL]->(concept_value)
            RETURN concept_value
            """
        result, _ = db.cypher_query(query, {"uid": uid})
        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0]
        return None

    def latest_concept_is_final(self, uid: str) -> bool:
        """Check if the LATEST version of a concept has Final status.
        Uses the HAS_VERSION relationship's status property for the current version."""
        # The current version is determined by HAS_VERSION relationship where end_date IS NULL
        # This is more reliable than LATEST_* relationships after retire/reactivate cycles

        query = f"""
            MATCH (concept_root:{self.root_class.__label__} {{uid: $uid}})
            MATCH (concept_root)-[hv:HAS_VERSION]->(version_value:{self.value_class.__label__})
            WHERE hv.end_date IS NULL
            RETURN hv.status = 'Final' as is_final
            """
        result, _ = db.cypher_query(query, {"uid": uid})

        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0] is True

        return False

    def get_latest_concept_name(self, uid: str) -> str | None:
        """Get the name of the LATEST version of a concept.
        Uses the HAS_VERSION relationship to find the current version."""
        query = f"""
            MATCH (concept_root:{self.root_class.__label__} {{uid: $uid}})
            MATCH (concept_root)-[hv:HAS_VERSION]->(version_value:{self.value_class.__label__})
            WHERE hv.end_date IS NULL
            RETURN version_value.name as name
            """
        result, _ = db.cypher_query(query, {"uid": uid})

        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0]

        return None

    def latest_concept_in_library_exists_by_name(
        self, library_name: str, concept_name: str
    ) -> bool:
        query = f"""
            MATCH (l:Library {{name: $library_name}})-[:CONTAINS_CONCEPT]->
                    (concept_root:{self.root_class.__label__})-[:LATEST]->
                    (concept_value:{self.value_class.__label__}{{name: $concept_name}})
            RETURN concept_root
            """
        result, _ = db.cypher_query(
            query, {"concept_name": concept_name, "library_name": library_name}
        )
        return len(result) > 0 and len(result[0]) > 0

    def latest_concept_in_library_exists_by_property_value(
        self, library_name: str, property_name: str, property_value: str
    ) -> bool:
        query = f"""
            MATCH (l:Library {{name: $library_name}})-[:CONTAINS_CONCEPT]->
                    (concept_root:{self.root_class.__label__})-[:LATEST]->
                    (concept_value:{self.value_class.__label__}{{{property_name}: $property_value}})
            RETURN concept_root
            """
        result, _ = db.cypher_query(
            query, {"property_value": property_value, "library_name": library_name}
        )
        return len(result) > 0 and len(result[0]) > 0

    def _is_new_version_necessary(
        self, ar: _AggregateRootType, value: VersionValue
    ) -> bool:
        return self._has_data_changed(ar, value)

    def _get_or_create_value(
        self,
        root: VersionRoot,
        ar: _AggregateRootType,
        force_new_value_node: bool = False,
    ) -> VersionValue:
        if not force_new_value_node:
            for itm in root.has_version.all():
                if not self._has_data_changed(ar, itm):
                    return itm
            latest_draft = root.latest_draft.get_or_none()
            if latest_draft and not self._has_data_changed(ar, latest_draft):
                return latest_draft
            latest_final = root.latest_final.get_or_none()
            if latest_final and not self._has_data_changed(ar, latest_final):
                return latest_final
            latest_retired = root.latest_retired.get_or_none()
            if latest_retired and not self._has_data_changed(ar, latest_retired):
                return latest_retired
        new_value = self._create_new_value_node(ar=ar)
        self._db_save_node(new_value)
        return new_value

    @classmethod
    def is_concept_node_a_tp(cls, concept_node: VersionValue) -> bool:
        labels = concept_node.labels()
        for label in labels:
            if "TemplateParameterTermValue" in label:
                return True
        return False

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        if versioned_object.concept_vo.is_template_parameter:
            # neomodel can't add custom label to already existing node, we have to manage that by executing cypher query
            template_parameter_name = self.root_class.__name__.removesuffix("Root")
            # we want to initiate a Comparator TemplateParameter type with the same template parameter terms as we do
            # for Compound TemplateParameter
            if template_parameter_name == "Compound":
                template_parameter_names = [template_parameter_name, "Comparator"]
            else:
                template_parameter_names = [template_parameter_name]
            for template_param_name in template_parameter_names:
                query = """
                    MATCH (template_parameter:TemplateParameter {name:$template_parameter_name})
                    MATCH (concept_root:ConceptRoot {uid: $uid})-[:LATEST]->(concept_value)
                    SET concept_root:TemplateParameterTermRoot
                    SET concept_value:TemplateParameterTermValue
                    MERGE (template_parameter)-[:HAS_PARAMETER_TERM]->(concept_root)
                """
                db.cypher_query(
                    query,
                    {
                        "uid": versioned_object.uid,
                        "template_parameter_name": template_param_name,
                    },
                )
                TemplateParameterTermRoot.generate_node_uids_if_not_present()

    def _update_versioning_relationship_query(
        self, status: str, merge_query: str | None = None
    ) -> str:
        query = f"""
            MATCH (library:Library)-[:CONTAINS_CONCEPT]->(concept_root)-[latest_has_version:HAS_VERSION]->(concept_value)
            WHERE latest_has_version.end_date is null
            MATCH (concept_root)-[latest_status_relationship:LATEST_{status.upper()}]->(:{self.value_class.__label__})
            WITH *
            """
        if merge_query:
            query += merge_query
        else:
            query += f"""
            CREATE (concept_root)-[:LATEST]->(concept_value)
            CREATE (concept_root)-[:LATEST_{status.upper()}]->(concept_value)
            CREATE (concept_root)-[new_has_version:HAS_VERSION]->(concept_value)
            """
        query += """
            SET new_has_version.start_date = $start_date
            SET new_has_version.end_date = null
            SET new_has_version.change_description = $change_description
            SET new_has_version.version = $new_version
            SET new_has_version.status = $new_status
            SET new_has_version.author_id = $author_id
            SET latest_has_version.end_date = $start_date
            WITH *
            DELETE status_relationship, latest_status_relationship
        """
        return query

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def archive(self, uid: str) -> None:
        """
        Moves concept to 'Archived' library

        Renames old CONTAINS/CONTAINS_CONCEPT relationship to CONTAINED,
        (actually recreates it, copies it's properties and deletes the old one),
        adds end_date to it, and creates a new CONTAINS/CONTAINS_CONCEPT to the new library.
        """

        query = f"""
            MATCH (concept_root:{self.root_class.__label__} {{uid: $uid}})
                  <-[prev_rel:{self.root_class.LIBRARY_REL_LABEL}]-(prev_library:Library)
            MATCH (new_library:Library {{name: $library}})

            CREATE (prev_library)-[contained:CONTAINED]->(concept_root)
            SET contained = properties(prev_rel)
            SET contained.end_date = datetime({{timezone: 'UTC'}})

            CREATE (new_library)-[new_rel:{self.root_class.LIBRARY_REL_LABEL}]->(concept_root)
            SET new_rel = properties(prev_rel)
            REMOVE new_rel.end_date
            SET new_rel.start_date = contained.end_date
            SET new_rel.author_id = $author_id

            DELETE prev_rel

            RETURN concept_root, new_library
            """

        results, _ = db.cypher_query(
            query,
            {
                "uid": uid,
                "library": settings.archived_library_name,
                "author_id": self.author_id,
            },
        )

        # also raises NotFoundException if 'Archived' library doesn't exist, or found multiple concepts
        NotFoundException.raise_if_not(
            len(results) == 1, self.root_class.__label__, uid
        )
