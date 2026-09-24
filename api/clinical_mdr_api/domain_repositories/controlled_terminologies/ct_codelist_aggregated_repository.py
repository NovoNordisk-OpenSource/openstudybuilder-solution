from datetime import datetime
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_get_all_query_utils import (
    TS_PARAMETER_NESTED_FIELDS_MAP,
    create_codelist_attributes_aggregate_instances_from_cypher_result,
    create_codelist_filter_statement,
    create_codelist_name_aggregate_instances_from_cypher_result,
    format_codelist_filter_sort_keys,
    format_codelist_term_filter_sort_keys,
    list_codelist_wildcard_properties,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
    CTPairedCodelists,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_term import (
    CTCodelistTermAR,
    CTPairedCodelistTermAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import (
    CTCodelistTerm,
    CTPairedCodelistTerm,
)
from clinical_mdr_api.models.controlled_terminologies.ct_stats import CodelistCount
from clinical_mdr_api.repositories._utils import (
    ComparisonOperator,
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    calculate_total_count_from_query_result,
    escape_lucene_special_chars,
    validate_filter_by_dict,
    validate_filters_and_add_search_string,
)
from common.config import settings
from common.exceptions import BusinessLogicException, ValidationException


class CTCodelistAggregatedRepository:
    generic_final_alias_clause = """
        CALL (rel_data_attributes) {
            OPTIONAL MATCH (attributes_author: User)
            WHERE attributes_author.user_id = rel_data_attributes.author_id
            RETURN attributes_author
        }
        CALL (rel_data_name) {
            OPTIONAL MATCH (name_author: User)
            WHERE name_author.user_id = rel_data_name.author_id
            RETURN name_author
        }
        WITH 
            codelist_root.uid AS codelist_uid,
            head([(codelist_root)-[:HAS_PARENT_CODELIST]->(ccr:CTCodelistRoot) | ccr.uid]) AS parent_codelist_uid,
            [(codelist_root)<-[:HAS_PARENT_CODELIST]-(ccr:CTCodelistRoot) | ccr.uid] AS child_codelist_uids,
            catalogue_names,
            codelist_attributes_value AS value_node_attributes,
            codelist_name_value AS value_node_name,
            CASE WHEN codelist_name_value:TemplateParameter THEN true ELSE false END AS is_template_parameter,
            library.name AS library_name,
            library.is_editable AS is_library_editable,
            {
                start_date: rel_data_attributes.start_date,
                end_date: NULL,
                status: rel_data_attributes.status,
                version: rel_data_attributes.version,
                change_description: rel_data_attributes.change_description,
                author_id: rel_data_attributes.author_id,
                author_username: coalesce(attributes_author.username, rel_data_attributes.author_id)
            } AS rel_data_attributes,
            {
                start_date: rel_data_name.start_date,
                end_date: NULL,
                status: rel_data_name.status,
                version: rel_data_name.version,
                change_description: rel_data_name.change_description,
                author_id: rel_data_name.author_id,
                author_username: coalesce(name_author.username, rel_data_name.author_id)
            } AS rel_data_name,
            head([(codelist_root)-[:PAIRED_CODE_CODELIST]->(paired_codes_cl_root:CTCodelistRoot) | paired_codes_cl_root.uid]) AS paired_codes_codelist_uid,
            head([(codelist_root)<-[:PAIRED_CODE_CODELIST]-(paired_names_cl_root:CTCodelistRoot) | paired_names_cl_root.uid]) AS paired_names_codelist_uid,
            head([(codelist_root)-[:PAIRED_CODE_CODELIST]->(pcr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(pcv:CTCodelistAttributesValue) | pcv.name]) AS paired_codes_codelist_name,
            head([(codelist_root)<-[:PAIRED_CODE_CODELIST]-(pnr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(pnv:CTCodelistAttributesValue) | pnv.name]) AS paired_names_codelist_name
        // Precedence (codes wins over names) must stay in sync with
        // _paired_codelist_info_from() in services/controlled_terminologies/ct_codelist.py,
        // which builds the same `paired_codelist` field for the API response.
        WITH *,
            coalesce(paired_codes_codelist_uid, paired_names_codelist_uid) AS paired_codelist_uid,
            coalesce(paired_codes_codelist_name, paired_names_codelist_name) AS paired_codelist_name
    """
    generic_alias_clause = f"""
        DISTINCT codelist_root, codelist_name_root, codelist_name_value, codelist_attributes_root, codelist_attributes_value
        ORDER BY codelist_root.uid
        WITH DISTINCT codelist_root, codelist_name_root, codelist_name_value, codelist_attributes_root, codelist_attributes_value, 
        [(cat:CTCatalogue)-[:HAS_CODELIST]->(codelist_root) | cat.name] AS catalogue_names,
        head([(lib)-[:CONTAINS_CODELIST]->(codelist_root) | lib]) AS library
        CALL (codelist_attributes_root, codelist_attributes_value) {{
                MATCH (codelist_attributes_root)-[hv:HAS_VERSION]->(codelist_attributes_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS rel_data_attributes
        }}
        CALL (codelist_name_root, codelist_name_value) {{
                MATCH (codelist_name_root)-[hv:HAS_VERSION]->(codelist_name_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS rel_data_name
        }}
        {generic_final_alias_clause}
    """
    sponsor_alias_clause = f"""
        DISTINCT codelist_root, codelist_name_root, codelist_name_value, codelist_attributes_root, codelist_attributes_value, attr_v_rel, name_v_rel
        ORDER BY codelist_root.uid
        WITH DISTINCT codelist_root, codelist_name_root, codelist_name_value, codelist_attributes_root, codelist_attributes_value,
        attr_v_rel AS rel_data_attributes, name_v_rel AS rel_data_name,
        [(cat:CTCatalogue)-[:HAS_CODELIST]->(codelist_root) | cat.name] AS catalogue_names,
        head([(lib)-[:CONTAINS_CODELIST]->(codelist_root) | lib]) AS library
        {generic_final_alias_clause}
    """

    def _create_codelist_aggregate_instances_from_cypher_result(
        self, codelist_dict: dict[str, Any]
    ) -> tuple[CTCodelistNameAR, CTCodelistAttributesAR, CTPairedCodelists]:
        """
        Method creates a tuple of CTCodelistNameAR and CTCodelistAttributesAR objects for one CTCodelistRoot node.
        The term_dict is a find_all_aggregated_result method result for one CTCodelistRoot node.

        :param codelist_dict:
        :return (CTCodelistNameAR, CTCodelistAttributesAR):
        """
        codelist_name_ar = create_codelist_name_aggregate_instances_from_cypher_result(
            codelist_dict=codelist_dict, is_aggregated_query=True
        )
        codelist_attributes_ar = (
            create_codelist_attributes_aggregate_instances_from_cypher_result(
                codelist_dict=codelist_dict, is_aggregated_query=True
            )
        )
        paired_codelists = CTPairedCodelists(
            paired_names_codelist_uid=codelist_dict.get("paired_names_codelist_uid"),
            paired_codes_codelist_uid=codelist_dict.get("paired_codes_codelist_uid"),
            paired_names_codelist_name=codelist_dict.get("paired_names_codelist_name"),
            paired_codes_codelist_name=codelist_dict.get("paired_codes_codelist_name"),
        )
        return codelist_name_ar, codelist_attributes_ar, paired_codelists

    def minimal_count_query(
        self,
        catalogue_name: str | None,
        library: str | None,
        package: str | None,
        is_sponsor: bool,
        filter_by: dict[str, dict[str, Any]] | None,
        term_filter: dict[str, str | list[Any]] | None,
    ) -> tuple[str | None, dict[str, Any]]:

        filter_by = validate_filter_by_dict(filter_by)
        # if filters are provided, no minimal query can be made
        if filter_by is not None and len(filter_by) > 0:
            return None, {}
        # if term filters are provided, no minimal query can be made
        if term_filter is not None and len(term_filter) > 0:
            return None, {}

        where_clauses = []
        params = {}
        if catalogue_name:
            where_clauses.append(
                "(codelist_root)<-[:HAS_CODELIST]-(:CTCatalogue {name: $catalogue_name})"
            )
            params["catalogue_name"] = catalogue_name
        if library:
            where_clauses.append(
                "(:Library {name: $library})-[:CONTAINS_CODELIST]->(codelist_root)"
            )
            params["library"] = library
        if package:
            where_clauses.append("""
                (:CTPackage {name: $package})-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
                (:CTCodelistAttributesValue)<-[:HAS_VERSION]-(:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(codelist_root)
                """)
            params["package"] = package
        if is_sponsor:
            where_clauses.append("""
                EXISTS {
                    MATCH (lib:Library)-[:CONTAINS_CODELIST]->(codelist_root)
                    WHERE lib.name <> $cdisc_library_name
                }
                """)
            params["cdisc_library_name"] = settings.cdisc_library_name
        query = "MATCH (codelist_root:CTCodelistRoot)"
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        query += " RETURN count(DISTINCT codelist_root) AS count"
        return query, params

    def find_all_aggregated_result(
        self,
        catalogue_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        is_sponsor: bool = False,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        term_filter: dict[str, str | list[Any]] | None = None,
    ) -> tuple[
        list[tuple[CTCodelistNameAR, CTCodelistAttributesAR, CTPairedCodelists]], int
    ]:
        """
        Method runs a cypher query to fetch all data related to the CTCodelistName* and CTCodelistAttributes*.
        It allows to filter the query output by catalogue_name, library and package.
        It returns the array of Tuples where each tuple is consists of CTCodelistNameAR and CTCodelistAttributesAR objects.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param catalogue_name:
        :param library:
        :param package:
        :param sort_by:
        :param page_number:
        :param page_size:
        :param filter_by:
        :param filter_operator:
        :param total_count:
        :return GenericFilteringReturn[tuple[CTCodelistNameAR, CTCodelistAttributesAR]]:
        """
        # If library is not explicitly passed but is in filter_by, extract it
        # so it can be used in the optimized MATCH clause path
        if not library and filter_by and "library_name" in filter_by:
            library_filter: list[str] = filter_by["library_name"]["v"]
            if len(library_filter) == 1:
                library = library_filter[0]
                del filter_by["library_name"]

        # Build match_clause
        # Build specific filtering for catalogue, package and library
        # This is separate from generic filtering as the list of filters is predefined
        # We can therefore do this filtering in an efficient way in the Cypher MATCH clause
        filter_statements, filter_query_parameters = create_codelist_filter_statement(
            catalogue_name=catalogue_name,
            library_name=library,
            package=package,
            is_sponsor=is_sponsor,
        )
        match_clause = self._generate_generic_match_clause(
            library_name=library,
            package=package,
            is_sponsor=is_sponsor,
            term_filter=term_filter,
        )
        match_clause += filter_statements

        # Build alias_clause
        alias_clause = (
            self.sponsor_alias_clause if is_sponsor else self.generic_alias_clause
        )

        minimal_count_query, minimal_count_params = self.minimal_count_query(
            catalogue_name=catalogue_name,
            library=library,
            package=package,
            is_sponsor=is_sponsor,
            filter_by=filter_by,
            term_filter=term_filter,
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
            wildcard_properties_list=list_codelist_wildcard_properties(),
            format_filter_sort_keys=format_codelist_filter_sort_keys,
            one_element_extra=filtering_active,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()

        codelists_ars = []
        for codelist in result_array:
            codelist_dictionary = {}
            for codelist_property, attribute_name in zip(codelist, attributes_names):
                codelist_dictionary[attribute_name] = codelist_property
            codelists_ars.append(
                self._create_codelist_aggregate_instances_from_cypher_result(
                    codelist_dictionary
                )
            )

        total = calculate_total_count_from_query_result(
            len(codelists_ars),
            page_number,
            page_size,
            total_count,
            extra_requested=filtering_active,
        )
        if 0 < page_size < len(codelists_ars):
            codelists_ars = codelists_ars[:page_size]
        if total is None:
            count_result, _ = db.cypher_query(
                query=minimal_count_query, params=minimal_count_params
            )
            total = count_result[0][0] if len(count_result) > 0 else 0

        return codelists_ars, total

    def get_distinct_headers(
        self,
        field_name: str,
        catalogue_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        is_sponsor: bool = False,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ) -> list[Any]:
        """
        Method runs a cypher query to fetch possible values for a given field_name, with a limit of page_size.
        It uses generic filtering capability, on top of filtering the field_name with provided search_string.

        :param field_name: Field name for which to return possible values
        :param catalogue_name:
        :param library:
        :param package:
        :param search_string:
        :param filter_by:
        :param filter_operator: Same as for generic filtering
        :param page_size: Max number of values to return. Default 10
        :return list[Any]:
        """

        # Build match_clause
        # Build specific filtering for catalogue, package and library
        # This is separate from generic filtering as the list of filters is predefined
        # We can therefore do this filtering in an efficient way in the Cypher MATCH clause
        filter_statements, filter_query_parameters = create_codelist_filter_statement(
            catalogue_name=catalogue_name,
            library_name=library,
            package=package,
            is_sponsor=is_sponsor,
        )
        match_clause = self._generate_generic_match_clause(
            library_name=library, package=package, is_sponsor=is_sponsor
        )
        match_clause += filter_statements

        # Build alias_clause
        alias_clause = (
            self.sponsor_alias_clause if is_sponsor else self.generic_alias_clause
        )

        # Add header field name to filter_by, to filter with a CONTAINS pattern
        filter_by = validate_filters_and_add_search_string(
            search_string, field_name, filter_by
        )

        # Use Cypher query class to use reusable helper methods
        query = CypherQueryBuilder(
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            match_clause=match_clause,
            alias_clause=alias_clause,
            wildcard_properties_list=list_codelist_wildcard_properties(),
            format_filter_sort_keys=format_codelist_filter_sort_keys,
        )

        query.full_query = query.build_header_query(
            header_alias=format_codelist_filter_sort_keys(field_name),
            page_size=page_size,
        )

        query.parameters.update(filter_query_parameters)
        result_array, _ = query.execute()

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    def _generate_generic_match_clause(
        self,
        library_name: str | None = None,
        package: str | None = None,
        is_sponsor: bool = False,
        term_filter: dict[str, str | list[Any]] | None = None,
    ):
        match_clause = ""

        if is_sponsor:
            ValidationException.raise_if_not(
                package,
                msg="Package must be provided when fetching sponsor codelists.",
            )
            if term_filter:
                ValidationException.raise_if(
                    "term_uids" not in term_filter,
                    msg="term_uids must be provided for term filtering.",
                )

                operation_function = "all"
                if "operator" in term_filter and term_filter["operator"] != "and":
                    operation_function = "any"

                match_clause += f"""MATCH (codelist_root:CTCodelistRoot)-[_has_term:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(ct_term:CTTermRoot)
                WHERE ct_term.uid IN {term_filter["term_uids"]} AND _has_term.end_date IS NULL
                WITH codelist_root, collect(ct_term.uid) as ct_term_uids
                WHERE {operation_function}(term_uid IN {term_filter["term_uids"]} WHERE term_uid IN ct_term_uids)
                """

            match_clause += f"""
                MATCH (package:CTPackage)-[:EXTENDS_PACKAGE]->(parent_package:CTPackage)
                WITH package, parent_package, datetime(toString(date(package.effective_date)) + 'T23:59:59') AS exact_datetime
                {"WHERE package.name=$package_name" if package else ""}
                """

            if library_name:
                if library_name == settings.cdisc_library_name:
                    # We must look in the library and the parent package
                    match_clause += f"""
                        MATCH (parent_package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
                            (codelist_attributes_value:CTCodelistAttributesValue)<-[attr_v_rel:HAS_VERSION]-(codelist_attributes_root:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                            (codelist_root{":CTCodelistRoot" if not term_filter else ""})
                            -[:HAS_NAME_ROOT]->(codelist_name_root:CTCodelistNameRoot)-[name_v_rel:HAS_VERSION]->(codelist_name_value:CTCodelistNameValue)
                        WHERE name_v_rel.start_date<= exact_datetime < name_v_rel.end_date OR (name_v_rel.end_date IS NULL AND name_v_rel.start_date <= exact_datetime)
                        MATCH (library:Library)-->(codelist_root)
                        WITH DISTINCT codelist_root, codelist_name_root, codelist_name_value, codelist_attributes_root, codelist_attributes_value, attr_v_rel, name_v_rel
                    """
                # We will look only in a specific library (sponsor)
                else:
                    match_clause += f"""
                        MATCH (:Library {{name:"{library_name}"}})-->(codelist_root{":CTCodelistRoot" if not term_filter else ""})
                            -[:HAS_ATTRIBUTES_ROOT]->(codelist_attributes_root:CTCodelistAttributesRoot)-[attr_v_rel:HAS_VERSION]->(codelist_attributes_value:CTCodelistAttributesValue)
                        MATCH (codelist_root)-[:HAS_NAME_ROOT]->(codelist_name_root:CTCodelistNameRoot)-[name_v_rel:HAS_VERSION]->(codelist_name_value:CTCodelistNameValue)
                        WHERE name_v_rel.start_date<= exact_datetime < name_v_rel.end_date OR (name_v_rel.end_date IS NULL AND name_v_rel.start_date <= exact_datetime)
                            AND (attr_v_rel.start_date<= exact_datetime < attr_v_rel.end_date OR (attr_v_rel.end_date IS NULL AND attr_v_rel.start_date <= exact_datetime))
                        WITH DISTINCT codelist_root, codelist_name_root, codelist_name_value, codelist_attributes_root, codelist_attributes_value, attr_v_rel, name_v_rel
                    """
            else:
                # Otherwise, we need to combine the sponsor terms with the terms in the parent package
                match_clause += f"""
                CALL (package, parent_package, exact_datetime) {{
                    MATCH (parent_package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
                        (codelist_attributes_value:CTCodelistAttributesValue)<-[attr_v_rel:HAS_VERSION]-(codelist_attributes_root:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                        (codelist_root{":CTCodelistRoot" if not term_filter else ""})
                        -[:HAS_NAME_ROOT]->(codelist_name_root:CTCodelistNameRoot)-[name_v_rel:HAS_VERSION]->(codelist_name_value:CTCodelistNameValue)
                    WHERE name_v_rel.start_date<= exact_datetime < name_v_rel.end_date OR (name_v_rel.end_date IS NULL AND name_v_rel.start_date <= exact_datetime)
                    RETURN DISTINCT codelist_root, codelist_name_root, codelist_name_value, codelist_attributes_root, codelist_attributes_value, attr_v_rel, name_v_rel

                    UNION
                    WITH exact_datetime
                    MATCH (l:Library WHERE NOT l.name=$cdisc_library_name)-->(codelist_root{":CTCodelistRoot" if not term_filter else ""})
                        -[:HAS_ATTRIBUTES_ROOT]->(codelist_attributes_root:CTCodelistAttributesRoot)-[attr_v_rel:HAS_VERSION]->(codelist_attributes_value:CTCodelistAttributesValue)
                    MATCH (codelist_root)-[:HAS_NAME_ROOT]->(codelist_name_root:CTCodelistNameRoot)-[name_v_rel:HAS_VERSION]->(codelist_name_value:CTCodelistNameValue)
                    WHERE (name_v_rel.start_date<= exact_datetime < name_v_rel.end_date OR (name_v_rel.end_date IS NULL AND name_v_rel.start_date <= exact_datetime))
                        AND (attr_v_rel.start_date<= exact_datetime < attr_v_rel.end_date OR (attr_v_rel.end_date IS NULL AND attr_v_rel.start_date <= exact_datetime))
                    RETURN DISTINCT codelist_root, codelist_name_root, codelist_name_value, codelist_attributes_root, codelist_attributes_value, attr_v_rel, name_v_rel
                }}
            """
        else:
            if term_filter:
                ValidationException.raise_if(
                    "term_uids" not in term_filter,
                    msg="term_uids must be provided for term filtering.",
                )

                operation_function = "all"
                if "operator" in term_filter and term_filter["operator"] != "and":
                    operation_function = "any"

                match_clause += f"""MATCH (codelist_root:CTCodelistRoot)-[_has_term:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(ct_term:CTTermRoot)
                WHERE ct_term.uid IN {term_filter["term_uids"]} AND _has_term.end_date IS NULL
                WITH codelist_root, collect(ct_term.uid) as ct_term_uids
                WHERE {operation_function}(term_uid IN {term_filter["term_uids"]} WHERE term_uid IN ct_term_uids)
                """

            if package:
                match_clause += f"""
                MATCH (package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
                (codelist_attributes_value:CTCodelistAttributesValue)<-[]-(codelist_attributes_root:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                (codelist_root{":CTCodelistRoot" if not term_filter else ""})-[:HAS_NAME_ROOT]->(codelist_name_root:CTCodelistNameRoot)-[:LATEST]->(codelist_name_value:CTCodelistNameValue)
                """
            else:
                match_clause += f"""
                MATCH (codelist_name_value:CTCodelistNameValue)<-[:LATEST]-(codelist_name_root:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-(codelist_root{":CTCodelistRoot" if not term_filter else ""})
                -[:HAS_ATTRIBUTES_ROOT]->(codelist_attributes_root:CTCodelistAttributesRoot)-[:LATEST]->(codelist_attributes_value:CTCodelistAttributesValue)
                """

        return match_clause

    def count_all(self) -> list[CodelistCount]:
        """
        Returns the count of CT Codelists in the database, grouped by Library

        :return: list[CodelistCount] - count of CT Codelists
        """
        query = """
            MATCH (n:CTCodelistRoot)<-[:CONTAINS_CODELIST]-(l:Library)
            RETURN l.name as library_name, count(n) as count
            """

        result, _ = db.cypher_query(query)
        return [CodelistCount(library_name=item[0], count=item[1]) for item in result]

    def get_change_percentage(self) -> float:
        """
        Returns the percentage of CT Codelists with more than one version

        :return: float - percentage
        """
        query = """
            MATCH (r:CTCodelistNameRoot)-->(v:CTCodelistNameValue)
            RETURN CASE count(r)
                WHEN 0 THEN 0
                ELSE (count(v)-count(r))/count(r)
                END AS percentage
            """

        result, _ = db.cypher_query(query)
        return result[0][0] if len(result) > 0 else 0.0

    def search_fulltext(
        self,
        search_string: str,
        only_response_codelists: bool = False,
        only_ordinal_codelists: bool = False,
        match_whole_words: bool = False,
        page_number: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, str]], int]:
        """
        Searches codelists using a full-text index on submission_value.

        :param search_string: The search string to use for full-text search
        :param only_response_codelists: If True, only return codelists that have a HAS_VALID_CODELIST_FOR_ITEMS relationship
        :param only_ordinal_codelists: If True, only return codelists where is_ordinal is True
        :param match_whole_words: If True, match whole words only (wraps search string in quotes)
        :param page_number: Page number for pagination
        :param page_size: Number of results per page (max 20 from full-text index)
        :return: Tuple of (list of dicts with uid, name, submission_value, and total count)
        """
        # Escape special Lucene characters to prevent query syntax errors
        escaped_search_string = escape_lucene_special_chars(search_string)

        if match_whole_words:
            lucene_query = f"{escaped_search_string}~{settings.fuzziness_level}"
        else:
            lucene_query = f"*{escaped_search_string}*~{settings.fuzziness_level}"

        where_clauses = []
        if only_ordinal_codelists:
            where_clauses.append("name_value.is_ordinal = true")
        if only_response_codelists:
            where_clauses.append(
                "EXISTS { MATCH (codelist_root)<-[:HAS_VALID_CODELIST_FOR_ITEMS]-() }"
            )

        where_statement = ""
        if where_clauses:
            where_statement = "WHERE " + " AND ".join(where_clauses)

        skip = (page_number - 1) * page_size

        query = f"""
            CALL db.index.fulltext.queryNodes('codelist_fulltext_index', $search_string, {{limit: 50}})
            YIELD node, score
            MATCH (node)<-[:LATEST]-(:CTCodelistNameRoot|CTCodelistAttributesRoot)<-[:HAS_NAME_ROOT|HAS_ATTRIBUTES_ROOT]-(codelist_root:CTCodelistRoot)
            WITH DISTINCT codelist_root, score
            MATCH (library:Library)-[:CONTAINS_CODELIST]->(codelist_root)
            MATCH (attr_value:CTCodelistAttributesValue)<-[:LATEST]-(:CTCodelistAttributesRoot)
                <--(codelist_root)-->(:CTCodelistNameRoot)-[:LATEST]->(name_value:CTCodelistNameValue)
            {where_statement}
            RETURN codelist_root.uid AS uid, name_value.name AS sponsor_preferred_name, attr_value.submission_value AS submission_value, library.name AS library_name
            ORDER BY score DESC
            SKIP $skip LIMIT $page_size
        """

        params = {
            "search_string": lucene_query,
            "skip": skip,
            "page_size": page_size,
        }

        result, _ = db.cypher_query(query, params)

        items = [
            {
                "uid": row[0],
                "sponsor_preferred_name": row[1],
                "submission_value": row[2],
                "library_name": row[3],
            }
            for row in result
        ]

        return items, 0

    def search_fulltext_by_term(
        self,
        search_string: str,
        only_response_codelists: bool = False,
        only_ordinal_codelists: bool = False,
        match_whole_words: bool = False,
        page_number: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, str]], int]:
        """
        Searches terms using a full-text index and returns codelists containing those terms.

        :param search_string: The search string to use for full-text search on terms
        :param only_response_codelists: If True, only return codelists that have a HAS_VALID_CODELIST_FOR_ITEMS relationship
        :param only_ordinal_codelists: If True, only return codelists where is_ordinal is True
        :param match_whole_words: If True, match whole words only
        :param page_number: Page number for pagination
        :param page_size: Number of results per page
        :return: Tuple of (list of dicts with uid, sponsor_preferred_name, submission_value, library_name)
        """
        # Escape special Lucene characters to prevent query syntax errors
        escaped_search_string = escape_lucene_special_chars(search_string)

        if match_whole_words:
            lucene_query = f"{escaped_search_string}~{settings.fuzziness_level}"
        else:
            lucene_query = f"*{escaped_search_string}*~{settings.fuzziness_level}"

        where_clauses = []
        if only_ordinal_codelists:
            where_clauses.append("name_value.is_ordinal = true")
        if only_response_codelists:
            where_clauses.append(
                "EXISTS { MATCH (codelist_root)<-[:HAS_VALID_CODELIST_FOR_ITEMS]-() }"
            )

        where_statement = ""
        if where_clauses:
            where_statement = "WHERE " + " AND ".join(where_clauses)

        skip = (page_number - 1) * page_size

        query = f"""
            CALL db.index.fulltext.queryNodes('term_fulltext_index', $search_string, {{limit: 250}})
            YIELD node, score
            MATCH (node)<-[:LATEST]-(:CTTermNameRoot|CTTermAttributesRoot)<-[:HAS_NAME_ROOT|HAS_ATTRIBUTES_ROOT]-(term_root:CTTermRoot)
            MATCH (codelist_root:CTCodelistRoot)-[:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root)
            WITH DISTINCT codelist_root, max(score) AS score
            MATCH (library:Library)-[:CONTAINS_CODELIST]->(codelist_root)
            MATCH (attr_value:CTCodelistAttributesValue)<-[:LATEST]-(:CTCodelistAttributesRoot)
                <--(codelist_root)-->(:CTCodelistNameRoot)-[:LATEST]->(name_value:CTCodelistNameValue)
            {where_statement}
            RETURN codelist_root.uid AS uid, name_value.name AS sponsor_preferred_name, attr_value.submission_value AS submission_value, library.name AS library_name
            ORDER BY score DESC
            SKIP $skip LIMIT $page_size
        """

        params = {
            "search_string": lucene_query,
            "skip": skip,
            "page_size": page_size,
        }

        result, _ = db.cypher_query(query, params)

        items = [
            {
                "uid": row[0],
                "sponsor_preferred_name": row[1],
                "submission_value": row[2],
                "library_name": row[3],
            }
            for row in result
        ]

        return items, 0

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    def find_all_terms_aggregated_result(
        self,
        codelist_uid: str | None = None,
        codelist_submission_value: str | None = None,
        codelist_name: str | None = None,
        package: str | None = None,
        include_removed: bool | None = None,
        at_specific_date_time: datetime | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        include_ts_parameters: bool = True,
    ) -> tuple[list[CTCodelistTermAR], int]:
        BusinessLogicException.raise_if_not(
            codelist_uid or codelist_submission_value or codelist_name,
            msg="At least one of codelist_uid, submission_value or name must be provided.",
        )
        if at_specific_date_time:
            end_date_where = "WHERE (ht.end_date IS NULL OR ht.end_date > datetime($at_specific_date_time)) AND ht.start_date <= datetime($at_specific_date_time)"
        elif not include_removed:
            end_date_where = "WHERE ht.end_date IS NULL"
        else:
            end_date_where = ""
        # Build match_clause
        if codelist_uid:
            root_match_clause = (
                "MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})"
            )
        elif codelist_submission_value:
            root_match_clause = """
                                MATCH (codelist_root:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->
                                (:CTCodelistAttributesRoot)-[:LATEST]->(:CTCodelistAttributesValue {submission_value: $codelist_submission_value})
                                """
        else:
            root_match_clause = """
                                MATCH (codelist_root:CTCodelistRoot)-[:HAS_NAME_ROOT]->
                                (:CTCodelistNameRoot)-[:LATEST]->(:CTCodelistNameValue {name: $codelist_name})
                                """
        if package:
            match_clause = f"""
                {root_match_clause}
                MATCH (codelist_root)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:HAS_VERSION]->
                    (:CTCodelistAttributesValue)<-[:CONTAINS_ATTRIBUTES]-(pcl:CTPackageCodelist)<-[:CONTAINS_CODELIST]-(:CTPackage {{name: $package}})
                MATCH (codelist_root)-[ht:HAS_TERM]->(ct_cl_term:CTCodelistTerm)-[:HAS_TERM_ROOT]->(ct_term_root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->
                    (tar:CTTermAttributesRoot)-[hav:HAS_VERSION {{status: "Final"}}]->(tav:CTTermAttributesValue)<-[:CONTAINS_ATTRIBUTES]-(:CTPackageTerm)<-[:CONTAINS_TERM]-(pcl)
                MATCH (library:Library)-[:CONTAINS_TERM]->(ct_term_root)-[:HAS_NAME_ROOT]->(tnr:CTTermNameRoot)-[:LATEST]->(tnv:CTTermNameValue)
            """
        else:
            # TODO if at_specific_date_time is provided, the query should fetch the term name and attributes
            # at the specific date time, not the latest ones.
            match_clause = f"""
                {root_match_clause}
                MATCH (codelist_root)-[ht:HAS_TERM]->(ct_cl_term:CTCodelistTerm)-[:HAS_TERM_ROOT]->(ct_term_root:CTTermRoot)<-[:CONTAINS_TERM]-(library:Library)
                {end_date_where}
                MATCH (ct_term_root)-[:HAS_NAME_ROOT]->(tnr:CTTermNameRoot)-[:LATEST]->(tnv:CTTermNameValue)
                MATCH (ct_term_root)-[:HAS_ATTRIBUTES_ROOT]->(tar:CTTermAttributesRoot)-[:LATEST]->(tav:CTTermAttributesValue)
            """

        if package:
            alias_clause = """
                DISTINCT codelist_root, ht, ct_cl_term, ct_term_root, tnr, tnv, tav, library, hav AS rel_data_attributes
                CALL (tnr, tnv) {
                    MATCH (tnr)-[hv:HAS_VERSION]->(tnv)
                    WITH hv
                    ORDER BY
                        toInteger(split(hv.version, '.')[0]) ASC,
                        toInteger(split(hv.version, '.')[1]) ASC,
                        hv.end_date ASC,
                        hv.start_date ASC
                    WITH collect(hv) as hvs
                    RETURN last(hvs) AS rel_data_name
                }
            """
        else:
            alias_clause = """
                DISTINCT codelist_root, ht, ct_cl_term, ct_term_root, tnr, tnv, tar, tav, library
                CALL (tar, tav) {
                    MATCH (tar)-[hv:HAS_VERSION]->(tav)
                    WITH hv 
                    ORDER BY
                        toInteger(split(hv.version, '.')[0]) ASC,
                        toInteger(split(hv.version, '.')[1]) ASC,
                        hv.end_date ASC,
                        hv.start_date ASC
                    WITH collect(hv) as hvs
                    RETURN last(hvs) AS rel_data_attributes
                }
                CALL (tnr, tnv) {
                    MATCH (tnr)-[hv:HAS_VERSION]->(tnv)
                    WITH hv
                    ORDER BY
                        toInteger(split(hv.version, '.')[0]) ASC,
                        toInteger(split(hv.version, '.')[1]) ASC,
                        hv.end_date ASC,
                        hv.start_date ASC
                    WITH collect(hv) as hvs
                    RETURN last(hvs) AS rel_data_name
                }
            """

        final_alias_clause = f"""
            {alias_clause}
            WITH *, codelist_root.uid IN $ts_codelist_uids AS is_ts_term
            CALL apoc.when(
                coalesce(is_ts_term, false) AND coalesce($include_ts_parameters, true),
                'OPTIONAL MATCH (tnv)-[:RELATED_STUDY_FIELD_SELECTION]->(msf:MetaStudyField)
                 OPTIONAL MATCH (msf)-[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(dt_term:CTTermRoot)
                 OPTIONAL MATCH (dt_term)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(dt_name:CTTermNameValue)
                 OPTIONAL MATCH (tnv)-[:RESPONSE_CODELIST]->(resp_cl:CTCodelistRoot)
                 OPTIONAL MATCH (resp_cl)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST_FINAL]->(resp_cl_name:CTCodelistNameValue)
                 OPTIONAL MATCH (tnv)-[:RESPONSE_DICTIONARY]->(resp_dict:DictionaryCodelistRoot)
                 OPTIONAL MATCH (tnv)-[:VALID_NULL_FLAVOR]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(nf_term:CTTermRoot)
                 OPTIONAL MATCH (nf_term)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST_FINAL]->(nf_name:CTTermNameValue)
                 RETURN msf.osb_field_name AS osb_field_name, msf.osb_page_reference AS osb_page_reference, dt_term.uid AS semantic_data_type_uid, dt_name.name AS semantic_data_type_name,
                        resp_cl.uid AS response_codelist_uid,
                        resp_cl_name.name AS response_codelist_name,
                        collect(DISTINCT resp_dict.uid) AS response_dictionary_uids,
                        collect(DISTINCT nf_term.uid) AS valid_null_flavor_term_uids,
                        collect(DISTINCT nf_name.name) AS valid_null_flavor_term_names',
                'RETURN null AS osb_field_name, null AS osb_page_reference, null AS semantic_data_type_uid, null AS semantic_data_type_name,
                        null AS response_codelist_uid,
                        null AS response_codelist_name,
                        [] AS response_dictionary_uids,
                        [] AS valid_null_flavor_term_uids,
                        [] AS valid_null_flavor_term_names',
                {{tnv: tnv}}
            ) YIELD value AS ts_props
            WITH
            ct_term_root.uid AS term_uid,
            ct_cl_term.submission_value AS submission_value,
            ht.order AS order,
            ht.ordinal AS ordinal,
            ht.start_date AS start_date,
            ht.end_date AS end_date,
            tav.definition AS definition,
            tav.concept_id AS concept_id,
            tav.preferred_term AS nci_preferred_name,
            rel_data_attributes.start_date AS attributes_date,
            rel_data_attributes.status AS attributes_status,
            coalesce(head([(user:User)-[*0]-() WHERE user.user_id=rel_data_attributes.author_id | user.username]), rel_data_attributes.author_id) AS attributes_author,
            tnv.name AS sponsor_preferred_name,
            tnv.name_sentence_case AS sponsor_preferred_name_sentence_case,
            rel_data_name.start_date AS name_date,
            rel_data_name.status AS name_status,
            coalesce(head([(user:User)-[*0]-() WHERE user.user_id=rel_data_name.author_id | user.username]), rel_data_name.author_id) AS name_author,
            library.name AS library_name,
            tnv.reference AS reference,
            tnv.required_level AS required_level,
            tnv.cardinality AS cardinality,
            tnv.notes AS notes,
            ts_props.osb_page_reference AS osb_page_reference,
            ts_props.osb_field_name AS osb_field_name,
            ts_props.semantic_data_type_uid AS semantic_data_type_uid,
            ts_props.semantic_data_type_name AS semantic_data_type_name,
            ts_props.response_codelist_uid AS response_codelist_uid,
            ts_props.response_codelist_name AS response_codelist_name,
            ts_props.response_dictionary_uids AS response_dictionary_uids,
            ts_props.valid_null_flavor_term_uids AS valid_null_flavor_term_uids,
            ts_props.valid_null_flavor_term_names AS valid_null_flavor_term_names

        """

        if sort_by is None:
            sort_by = {"order": True}

        query = CypherQueryBuilder(
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            match_clause=match_clause,
            alias_clause=final_alias_clause,
            wildcard_properties_list=list_codelist_wildcard_properties(
                target_model=CTCodelistTerm, transform=False
            ),
            format_filter_sort_keys=format_codelist_term_filter_sort_keys,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            total_count=total_count,
        )
        query.parameters.update({"codelist_uid": codelist_uid})
        query.parameters["ts_codelist_uids"] = [
            settings.ts_parmcd_codelist_uid,
            settings.ts_parm_codelist_uid,
        ]
        query.parameters["include_ts_parameters"] = include_ts_parameters
        if package:
            query.parameters.update({"package": package})
        if at_specific_date_time:
            query.parameters.update({"at_specific_date_time": at_specific_date_time})
        if codelist_uid:
            query.parameters.update({"codelist_uid": codelist_uid})
        if codelist_submission_value:
            query.parameters.update(
                {"codelist_submission_value": codelist_submission_value}
            )
        if codelist_name:
            query.parameters.update({"codelist_name": codelist_name})

        result_array, attributes_names = query.execute()

        codelist_term_ars = []
        for term in result_array:
            term_dictionary = {}
            for term_property, attribute_name in zip(term, attributes_names):
                term_dictionary[attribute_name] = term_property
            codelist_term_ars.append(CTCodelistTermAR.from_result_dict(term_dictionary))

        total = calculate_total_count_from_query_result(
            len(codelist_term_ars), page_number, page_size, total_count
        )
        if total is None:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            total = count_result[0][0] if len(count_result) > 0 else 0

        return codelist_term_ars, total

    def get_distinct_term_headers(
        self,
        codelist_uid: str,
        field_name: str,
        package: str | None = None,
        include_removed: bool | None = None,
        include_ts_parameters: bool = False,
        search_string: str | None = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ) -> list[Any]:
        """
        Method runs a cypher query to fetch possible values for a given field_name, with a limit of page_size.
        It uses generic filtering capability, on top of filtering the field_name with provided search_string.

        :param codelist_uid: UID of the Codelist for which to return possible values
        :param field_name: Field name for which to return possible values
        :param package:
        :param search_string:
        :param filter_by:
        :param filter_operator: Same as for generic filtering
        :param page_size: Max number of values to return. Default 10
        :return list[Any]:
        """

        # Add header field name to filter_by, to filter with a CONTAINS pattern
        if search_string != "":
            if filter_by is None:
                filter_by = {}
            filter_by[field_name] = {
                "v": [search_string],
                "op": ComparisonOperator.CONTAINS,
            }

        if not include_removed:
            end_date_where = "WHERE ht.end_date IS NULL"
        else:
            end_date_where = ""

        # Build match_clause
        if package:
            match_clause = """
                MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:HAS_VERSION]->(:CTCodelistAttributesValue)<-[:CONTAINS_ATTRIBUTES]-(pcl:CTPackageCodelist)<-[:CONTAINS_CODELIST]-(:CTPackage {name: $package})
                MATCH (codelist_root)-[ht:HAS_TERM]->(ct_cl_term:CTCodelistTerm)-[:HAS_TERM_ROOT]->(ct_term_root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(tar:CTTermAttributesRoot)-[hav:HAS_VERSION {status: "Final"}]->(tav:CTTermAttributesValue)<-[:CONTAINS_ATTRIBUTES]-(:CTPackageTerm)<-[:CONTAINS_TERM]-(pcl)
                MATCH (library:Library)-[:CONTAINS_TERM]->(ct_term_root)-[:HAS_NAME_ROOT]->(tnr:CTTermNameRoot)-[:LATEST]->(tnv:CTTermNameValue)
            """
        else:
            match_clause = f"""
                MATCH (codelist_root:CTCodelistRoot {{uid: $codelist_uid}})-[ht:HAS_TERM]->(ct_cl_term:CTCodelistTerm)-[:HAS_TERM_ROOT]->(ct_term_root:CTTermRoot)<-[:CONTAINS_TERM]-(library:Library)
                {end_date_where}
                MATCH (ct_term_root)-[:HAS_NAME_ROOT]->(tnr:CTTermNameRoot)-[:LATEST]->(tnv:CTTermNameValue)
                MATCH (ct_term_root)-[:HAS_ATTRIBUTES_ROOT]->(tar:CTTermAttributesRoot)-[:LATEST]->(tav:CTTermAttributesValue)
            """

        if package:
            alias_clause = """
                DISTINCT codelist_root, ht, ct_cl_term, ct_term_root, tnr, tnv, tav, library, hav AS rel_data_attributes
                CALL (tnr, tnv) {
                    MATCH (tnr)-[hv:HAS_VERSION]->(tnv)
                    WITH hv
                    ORDER BY
                        toInteger(split(hv.version, '.')[0]) ASC,
                        toInteger(split(hv.version, '.')[1]) ASC,
                        hv.end_date ASC,
                        hv.start_date ASC
                    WITH collect(hv) as hvs
                    RETURN last(hvs) AS rel_data_name
                }
            """
        else:
            alias_clause = """
                DISTINCT codelist_root, ht, ct_cl_term, ct_term_root, tnr, tnv, tar, tav, library
                CALL (tar, tav) {
                    MATCH (tar)-[hv:HAS_VERSION]->(tav)
                    WITH hv 
                    ORDER BY
                        toInteger(split(hv.version, '.')[0]) ASC,
                        toInteger(split(hv.version, '.')[1]) ASC,
                        hv.end_date ASC,
                        hv.start_date ASC
                    WITH collect(hv) as hvs
                    RETURN last(hvs) AS rel_data_attributes
                }
                CALL (tnr, tnv) {
                    MATCH (tnr)-[hv:HAS_VERSION]->(tnv)
                    WITH hv
                    ORDER BY
                        toInteger(split(hv.version, '.')[0]) ASC,
                        toInteger(split(hv.version, '.')[1]) ASC,
                        hv.end_date ASC,
                        hv.start_date ASC
                    WITH collect(hv) as hvs
                    RETURN last(hvs) AS rel_data_name
                }
            """

        final_alias_clause = f"""
            {alias_clause}
            WITH *, codelist_root.uid IN $ts_codelist_uids AS is_ts_term
            CALL apoc.when(
                coalesce(is_ts_term, false) AND coalesce($include_ts_parameters, true),
                'OPTIONAL MATCH (tnv)-[:RELATED_STUDY_FIELD_SELECTION]->(msf:MetaStudyField)
                 OPTIONAL MATCH (msf)-[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(dt_term:CTTermRoot)
                 OPTIONAL MATCH (dt_term)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(dt_name:CTTermNameValue)
                 OPTIONAL MATCH (tnv)-[:RESPONSE_CODELIST]->(resp_cl:CTCodelistRoot)
                 OPTIONAL MATCH (resp_cl)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST_FINAL]->(resp_cl_name:CTCodelistNameValue)
                 OPTIONAL MATCH (tnv)-[:RESPONSE_DICTIONARY]->(resp_dict:DictionaryCodelistRoot)
                 OPTIONAL MATCH (tnv)-[:VALID_NULL_FLAVOR]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(nf_term:CTTermRoot)
                 OPTIONAL MATCH (nf_term)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST_FINAL]->(nf_name:CTTermNameValue)
                 RETURN msf.osb_field_name AS osb_field_name, msf.osb_page_reference AS osb_page_reference, dt_term.uid AS semantic_data_type_uid, dt_name.name AS semantic_data_type_name,
                        resp_cl.uid AS response_codelist_uid,
                        resp_cl_name.name AS response_codelist_name,
                        collect(DISTINCT resp_dict.uid) AS response_dictionary_uids,
                        collect(DISTINCT nf_term.uid) AS valid_null_flavor_term_uids,
                        collect(DISTINCT nf_name.name) AS valid_null_flavor_term_names',
                'RETURN null AS osb_field_name, null AS osb_page_reference, null AS semantic_data_type_uid, null AS semantic_data_type_name,
                        null AS response_codelist_uid,
                        null AS response_codelist_name,
                        [] AS response_dictionary_uids,
                        [] AS valid_null_flavor_term_uids,
                        [] AS valid_null_flavor_term_names',
                {{tnv: tnv}}
            ) YIELD value AS ts_props
            WITH
            ct_term_root.uid AS term_uid,
            ct_cl_term.submission_value AS submission_value,
            ht.order AS order,
            ht.ordinal AS ordinal,
            ht.start_date AS start_date,
            ht.end_date AS end_date,
            tav.definition AS definition,
            tav.concept_id AS concept_id,
            tav.preferred_term AS nci_preferred_name,
            rel_data_attributes.start_date AS attributes_date,
            rel_data_attributes.status AS attributes_status,
            coalesce(head([(user:User)-[*0]-() WHERE user.user_id=rel_data_attributes.author_id | user.username]), rel_data_attributes.author_id) AS attributes_author,
            tnv.name AS sponsor_preferred_name,
            tnv.name_sentence_case AS sponsor_preferred_name_sentence_case,
            rel_data_name.start_date AS name_date,
            rel_data_name.status AS name_status,
            coalesce(head([(user:User)-[*0]-() WHERE user.user_id=rel_data_name.author_id | user.username]), rel_data_name.author_id) AS name_author,
            library.name AS library_name,
            tnv.reference AS reference,
            tnv.required_level AS required_level,
            tnv.cardinality AS cardinality,
            tnv.notes AS notes,
            ts_props.osb_page_reference AS osb_page_reference,
            ts_props.osb_field_name AS osb_field_name,
            ts_props.semantic_data_type_uid AS semantic_data_type_uid,
            ts_props.semantic_data_type_name AS semantic_data_type_name,
            ts_props.response_codelist_uid AS response_codelist_uid,
            ts_props.response_codelist_name AS response_codelist_name,
            ts_props.response_dictionary_uids AS response_dictionary_uids,
            ts_props.valid_null_flavor_term_uids AS valid_null_flavor_term_uids,
            ts_props.valid_null_flavor_term_names AS valid_null_flavor_term_names

        """

        # Use Cypher query class to use reusable helper methods
        query = CypherQueryBuilder(
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            match_clause=match_clause,
            alias_clause=final_alias_clause,
            wildcard_properties_list=list_codelist_wildcard_properties(
                target_model=CTCodelistTerm, transform=False
            ),
            format_filter_sort_keys=format_codelist_term_filter_sort_keys,
        )
        query.parameters.update({"codelist_uid": codelist_uid})
        query.parameters["ts_codelist_uids"] = [
            settings.ts_parmcd_codelist_uid,
            settings.ts_parm_codelist_uid,
        ]
        query.parameters["include_ts_parameters"] = include_ts_parameters
        if package:
            query.parameters.update({"package": package})

        # The alias clause exposes flat aliases (e.g. `definition`, `concept_id`),
        # so most field names map 1:1. Only the nested Trial Summary parameter
        # response models need translation to their flat Cypher aliases.
        query.full_query = query.build_header_query(
            header_alias=TS_PARAMETER_NESTED_FIELDS_MAP.get(field_name, field_name),
            page_size=page_size,
        )

        result_array, _ = query.execute()

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    def merge_link_to_codes_codelist(self, codelist_uid: str, codes_codelist_uid: str):
        """
        Create a PAIRED_CODE_CODELIST relationship between two CTCodelistRoot nodes.
        """
        query = """
            MATCH (names_codelist_root:CTCodelistRoot {uid: $codelist_uid}), (codes_codelist_root:CTCodelistRoot {uid: $codes_codelist_uid})
            OPTIONAL MATCH (names_codelist_root)-[existing_codes:PAIRED_CODE_CODELIST]->(:CTCodelistRoot)
            OPTIONAL MATCH (codes_codelist_root)<-[existing_names:PAIRED_CODE_CODELIST]-(:CTCodelistRoot)
            DELETE existing_codes
            DELETE existing_names
            MERGE (names_codelist_root)-[:PAIRED_CODE_CODELIST]->(codes_codelist_root)
        """
        db.cypher_query(
            query,
            {"codelist_uid": codelist_uid, "codes_codelist_uid": codes_codelist_uid},
        )

    def remove_link_to_codes_codelist(self, codelist_uid: str):
        """
        Remove a PAIRED_CODE_CODELIST relationship between two CTCodelistRoot nodes.
        """
        query = """
            MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})-[pcl:PAIRED_CODE_CODELIST]->(:CTCodelistRoot)
            DELETE pcl
        """
        db.cypher_query(query, {"codelist_uid": codelist_uid})

    def remove_link_from_codes_codelist(self, codelist_uid: str):
        """
        Remove a PAIRED_CODE_CODELIST relationship between two CTCodelistRoot nodes.
        """
        query = """
            MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})<-[pcl:PAIRED_CODE_CODELIST]-(:CTCodelistRoot)
            DELETE pcl
        """
        db.cypher_query(query, {"codelist_uid": codelist_uid})

    def get_paired_codelist_uids(
        self, codelist_uid: str
    ) -> tuple[str | None, str | None]:
        """
        Get the UID of the linked codes codelist for a given codelist.
        Returns None if no linked codes codelist exists.
        """
        query = """
            MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})
            OPTIONAL MATCH (codelist_root)-[:PAIRED_CODE_CODELIST]->(codes_codelist_root:CTCodelistRoot)
            OPTIONAL MATCH (codelist_root)<-[:PAIRED_CODE_CODELIST]-(names_codelist_root:CTCodelistRoot)
            RETURN codes_codelist_root.uid AS codes_codelist_uid, names_codelist_root.uid AS names_codelist_uid
        """
        result, _ = db.cypher_query(query, {"codelist_uid": codelist_uid})
        return result[0] if result else (None, None)

    def find_paired_codelist_terms(
        self,
        names_codelist_uid: str,
        codes_codelist_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> tuple[list[CTPairedCodelistTermAR], int]:
        match_clause = """
            CALL {
                MATCH (:CTCodelistRoot {uid: $names_codelist_uid})-[ht:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr:CTTermRoot)
                WHERE ht.end_date IS NULL
                RETURN tr
                UNION
                MATCH (:CTCodelistRoot {uid: $codes_codelist_uid})-[ht:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr:CTTermRoot)
                WHERE ht.end_date IS NULL
                RETURN tr
            }
            WITH DISTINCT tr AS term_root
            OPTIONAL MATCH (:CTCodelistRoot {uid: $names_codelist_uid})-[names_ht:HAS_TERM]->(names_clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root)
            WHERE names_ht.end_date IS NULL
            OPTIONAL MATCH (:CTCodelistRoot {uid: $codes_codelist_uid})-[codes_ht:HAS_TERM]->(codes_clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root)
            WHERE codes_ht.end_date IS NULL
            MATCH (term_root)<-[:CONTAINS_TERM]-(library:Library)
            MATCH (term_root)-[:HAS_NAME_ROOT]->(tnr:CTTermNameRoot)-[:LATEST]->(tnv:CTTermNameValue)
            MATCH (term_root)-[:HAS_ATTRIBUTES_ROOT]->(tar:CTTermAttributesRoot)-[:LATEST]->(tav:CTTermAttributesValue)
        """

        alias_clause = """
            DISTINCT term_root, names_ht, codes_ht, names_clt, codes_clt, tnr, tnv, tar, tav, library
            CALL (tar, tav) {
                MATCH (tar)-[hv:HAS_VERSION]->(tav)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS rel_data_attributes
            }
            CALL (tnr, tnv) {
                MATCH (tnr)-[hv:HAS_VERSION]->(tnv)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS rel_data_name
            }
            WITH
            term_root.uid AS term_uid,
            names_clt.submission_value AS name_submission_value,
            codes_clt.submission_value AS code_submission_value,
            COALESCE(names_ht.order, codes_ht.order) AS order,
            COALESCE(names_ht.ordinal, codes_ht.ordinal) AS ordinal,
            COALESCE(names_ht.start_date, codes_ht.start_date) AS start_date,
            COALESCE(names_ht.end_date, codes_ht.end_date) AS end_date,
            tav.definition AS definition,
            tav.concept_id AS concept_id,
            tav.preferred_term AS nci_preferred_name,
            rel_data_attributes.start_date AS attributes_date,
            rel_data_attributes.status AS attributes_status,
            coalesce(head([(user:User)-[*0]-() WHERE user.user_id=rel_data_attributes.author_id | user.username]), rel_data_attributes.author_id) AS attributes_author,
            tnv.name AS sponsor_preferred_name,
            tnv.name_sentence_case AS sponsor_preferred_name_sentence_case,
            rel_data_name.start_date AS name_date,
            rel_data_name.status AS name_status,
            coalesce(head([(user:User)-[*0]-() WHERE user.user_id=rel_data_name.author_id | user.username]), rel_data_name.author_id) AS name_author,
            library.name AS library_name
        """

        if sort_by is None:
            sort_by = {"order": True}

        query = CypherQueryBuilder(
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            match_clause=match_clause,
            alias_clause=alias_clause,
            wildcard_properties_list=list_codelist_wildcard_properties(
                target_model=CTPairedCodelistTerm, transform=False
            ),
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            total_count=total_count,
        )
        query.parameters.update(
            {
                "names_codelist_uid": names_codelist_uid,
                "codes_codelist_uid": codes_codelist_uid,
            }
        )

        result_array, attributes_names = query.execute()

        paired_term_ars = []
        for term in result_array:
            term_dictionary = {}
            for term_property, attribute_name in zip(term, attributes_names):
                term_dictionary[attribute_name] = term_property
            paired_term_ars.append(
                CTPairedCodelistTermAR.from_result_dict(term_dictionary)
            )

        total = calculate_total_count_from_query_result(
            len(paired_term_ars), page_number, page_size, total_count
        )
        if total is None:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            total = count_result[0][0] if len(count_result) > 0 else 0

        return paired_term_ars, total
