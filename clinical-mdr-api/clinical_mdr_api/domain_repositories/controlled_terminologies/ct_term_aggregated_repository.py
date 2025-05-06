from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_get_all_query_utils import (
    create_term_attributes_aggregate_instances_from_cypher_result,
    create_term_filter_statement,
    create_term_name_aggregate_instances_from_cypher_result,
    format_term_filter_sort_keys,
    list_term_wildcard_properties,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.models.controlled_terminologies.ct_stats import TermCount
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    validate_filters_and_add_search_string,
)
from common.exceptions import ValidationException


class CTTermAggregatedRepository:
    generic_final_alias_clause = """
        CALL {
            WITH rel_data_attributes
            OPTIONAL MATCH (attributes_author: User)
            WHERE attributes_author.user_id = rel_data_attributes.author_id
            RETURN attributes_author
        }
        CALL {
            WITH rel_data_name
            OPTIONAL MATCH (name_author: User)
            WHERE name_author.user_id = rel_data_name.author_id
            RETURN name_author
        }
        WITH
            term_root.uid AS term_uid,
            codelist_root.uid AS codelist_uid,
            codelist_library.name AS codelist_library_name,
            catalogue.name AS catalogue_name,
            term_attributes_value AS value_node_attributes,
            term_name_value AS value_node_name,
            rel_term.order AS order,
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
            ct_codelist_attributes_value.submission_value AS codelist_submission_value
    """
    generic_alias_clause = f"""
        DISTINCT term_root, term_attributes_root, term_attributes_value, term_name_root, term_name_value, codelist_root, rel_term, ct_codelist_attributes_value
        ORDER BY rel_term.order, term_name_value.name
        WITH DISTINCT term_root, term_attributes_root, term_attributes_value, term_name_root, term_name_value, 
        codelist_root, rel_term,
        head([(catalogue:CTCatalogue)-[:HAS_CODELIST]->(codelist_root) | catalogue]) AS catalogue,
        head([(lib)-[:CONTAINS_TERM]->(term_root) | lib]) AS library,
        ct_codelist_attributes_value
        MATCH (codelist_root)<-[:CONTAINS_CODELIST]-(codelist_library:Library)
        CALL {{
                WITH term_attributes_root, term_attributes_value
                MATCH (term_attributes_root)-[hv:HAS_VERSION]->(term_attributes_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS rel_data_attributes
        }}
        CALL {{
                WITH term_name_root, term_name_value
                MATCH (term_name_root)-[hv:HAS_VERSION]->(term_name_value)
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
        DISTINCT term_root, term_attributes_root, term_attributes_value, term_name_root, term_name_value, attr_v_rel, name_v_rel, codelist_root, rel_term, ct_codelist_attributes_value
        ORDER BY rel_term.order, term_name_value.name
        WITH DISTINCT term_root, term_attributes_root, term_attributes_value, term_name_root, term_name_value, 
        codelist_root, rel_term,
        attr_v_rel AS rel_data_attributes, name_v_rel AS rel_data_name,
        head([(catalogue:CTCatalogue)-[:HAS_CODELIST]->(codelist_root) | catalogue]) AS catalogue,
        head([(lib)-[:CONTAINS_TERM]->(term_root) | lib]) AS library,
        ct_codelist_attributes_value
        MATCH (codelist_root)<-[:CONTAINS_CODELIST]-(codelist_library:Library)
        {generic_final_alias_clause}
    """

    def _create_term_aggregate_instances_from_cypher_result(
        self, term_dict: dict
    ) -> tuple[CTTermNameAR, CTTermAttributesAR]:
        """
        Method creates a tuple of CTTermNameAR and CTTermAttributesAR objects for one CTTermRoot node.
        The term_dict is a find_all_aggregated_result method result for one CTTermRoot node.

        :param term_dict:
        :return (CTTermNameAR, CTTermAttributesAR):
        """

        term_name_ar = create_term_name_aggregate_instances_from_cypher_result(
            term_dict=term_dict, is_aggregated_query=True
        )
        term_attributes_ar = (
            create_term_attributes_aggregate_instances_from_cypher_result(
                term_dict=term_dict, is_aggregated_query=True
            )
        )
        return term_name_ar, term_attributes_ar

    def find_all_aggregated_result(
        self,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        is_sponsor: bool = False,
        include_removed_terms: bool = False,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[tuple[CTTermNameAR, CTTermAttributesAR]]:
        """
        Method runs a cypher query to fetch all data related to the CTTermName* and CTTermAttributes*.
        It allows to filter the query output by codelist_uid, codelist_name, library and package.
        It returns the array of Tuples where each tuple is consists of CTTermNameAR and CTTermAttributesAR objects.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param codelist_uid:
        :param codelist_name:
        :param library:
        :param package:
        :param sort_by:
        :param page_number:
        :param page_size:
        :param filter_by:
        :param filter_operator:
        :param total_count:
        :return GenericFilteringReturn[tuple[CTTermNameAR, CTTermAttributesAR]]:
        """
        # Build match_clause
        match_clause, filter_query_parameters = self._generate_generic_match_clause(
            codelist_uid=codelist_uid,
            codelist_name=codelist_name,
            library_name=library,
            package=package,
            is_sponsor=is_sponsor,
            include_removed_terms=include_removed_terms,
        )

        # Build alias_clause
        alias_clause = (
            self.sponsor_alias_clause if is_sponsor else self.generic_alias_clause
        )

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            implicit_sort_by="term_uid",
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            total_count=total_count,
            wildcard_properties_list=list_term_wildcard_properties(),
            format_filter_sort_keys=format_term_filter_sort_keys,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()

        terms_ars = []
        for term in result_array:
            term_dictionary = {}
            for term_property, attribute_name in zip(term, attributes_names):
                term_dictionary[attribute_name] = term_property
            terms_ars.append(
                self._create_term_aggregate_instances_from_cypher_result(
                    term_dictionary
                )
            )

        total = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                total = count_result[0][0]

        return GenericFilteringReturn.create(items=terms_ars, total=total)

    def get_distinct_headers(
        self,
        field_name: str,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        is_sponsor: bool = False,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        page_size: int = 10,
    ) -> list[Any]:
        """
        Method runs a cypher query to fetch possible values for a given field_name, with a limit of page_size.
        It uses generic filtering capability, on top of filtering the field_name with provided search_string.

        :param field_name: Field name for which to return possible values
        :param codelist_uid:
        :param codelist_name:
        :param library:
        :param package:
        :param search_string:
        :param filter_by:
        :param filter_operator: Same as for generic filtering
        :param page_size: Max number of values to return. Default 10
        :return list[Any]:
        """
        # Build match_clause
        match_clause, filter_query_parameters = self._generate_generic_match_clause(
            codelist_uid=codelist_uid,
            codelist_name=codelist_name,
            library_name=library,
            package=package,
            is_sponsor=is_sponsor,
        )

        # Aliases clause
        alias_clause = (
            self.sponsor_alias_clause if is_sponsor else self.generic_alias_clause
        )

        # Add header field name to filter_by, to filter with a CONTAINS pattern
        filter_by = validate_filters_and_add_search_string(
            search_string, field_name, filter_by
        )

        # Use Cypher query class to use reusable helper methods
        query = CypherQueryBuilder(
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            match_clause=match_clause,
            alias_clause=alias_clause,
            wildcard_properties_list=list_term_wildcard_properties(),
            format_filter_sort_keys=format_term_filter_sort_keys,
        )

        query.full_query = query.build_header_query(
            header_alias=format_term_filter_sort_keys(field_name),
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
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library_name: str | None = None,
        package: str | None = None,
        is_sponsor: bool = False,
        include_removed_terms: bool = False,
    ) -> tuple[str, dict]:
        match_clause = ""
        if is_sponsor:
            ValidationException.raise_if_not(
                package, msg="Package must be provided when fetching sponsor terms."
            )

            match_clause += f"""
                MATCH (package:CTPackage)-[:EXTENDS_PACKAGE]->(parent_package:CTPackage)
                WITH package, parent_package, datetime(package.effective_date + "T23:59:59") AS exact_datetime
                {"WHERE package.name=$package_name" if package else ""}
            """

            if library_name:
                # We will look only in a specific library
                if library_name == "Sponsor":
                    match_clause += """
                        MATCH (:Library {name:"Sponsor"})-->(term_root:CTTermRoot)
                            -[:HAS_ATTRIBUTES_ROOT]->(term_attributes_root:CTTermAttributesRoot)-[attr_v_rel:HAS_VERSION]->(term_attributes_value:CTTermAttributesValue)
                        MATCH (term_root)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[name_v_rel:HAS_VERSION]->(term_name_value:CTTermNameValue)
                        WHERE (name_v_rel.start_date<= exact_datetime < name_v_rel.end_date OR (name_v_rel.end_date IS NULL AND name_v_rel.start_date <= exact_datetime))
                            AND (attr_v_rel.start_date<= exact_datetime < attr_v_rel.end_date OR (attr_v_rel.end_date IS NULL AND attr_v_rel.start_date <= exact_datetime))
                        WITH DISTINCT term_root, term_name_root, term_name_value, term_attributes_root, term_attributes_value, attr_v_rel, name_v_rel
                """
                else:
                    # We must look in the library and the parent package
                    match_clause += """
                        MATCH (parent_package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_TERM]->(:CTPackageTerm)-
                        [:CONTAINS_ATTRIBUTES]->(term_attributes_value:CTTermAttributesValue)<-[attr_v_rel:HAS_VERSION]-(term_attributes_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                        (term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[name_v_rel:HAS_VERSION]->(term_name_value:CTTermNameValue)
                        WHERE name_v_rel.start_date<= exact_datetime < name_v_rel.end_date OR (name_v_rel.end_date IS NULL AND name_v_rel.start_date <= exact_datetime)
                        MATCH (library:Library)-[:CONTAINS_TERM]->(term_root)
                        WITH DISTINCT term_root, term_name_root, term_name_value, term_attributes_root, term_attributes_value, attr_v_rel, name_v_rel
                    """
            else:
                # Otherwise, we need to combine the sponsor terms with the terms in the parent package
                match_clause += """
                CALL {
                    WITH package, parent_package, exact_datetime
                    MATCH (parent_package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_TERM]->(:CTPackageTerm)-
                        [:CONTAINS_ATTRIBUTES]->(term_attributes_value:CTTermAttributesValue)<-[attr_v_rel:HAS_VERSION]-(term_attributes_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                        (term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[name_v_rel:HAS_VERSION]->(term_name_value:CTTermNameValue)
                    WHERE name_v_rel.start_date<= exact_datetime < name_v_rel.end_date OR (name_v_rel.end_date IS NULL AND name_v_rel.start_date <= exact_datetime)
                    RETURN DISTINCT term_root, term_name_root, term_name_value, term_attributes_root, term_attributes_value, attr_v_rel, name_v_rel

                    UNION
                    WITH exact_datetime
                    MATCH (:Library {name:"Sponsor"})-->(term_root:CTTermRoot)
                        -[:HAS_ATTRIBUTES_ROOT]->(term_attributes_root:CTTermAttributesRoot)-[attr_v_rel:HAS_VERSION]->(term_attributes_value:CTTermAttributesValue)
                    MATCH (term_root)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[name_v_rel:HAS_VERSION]->(term_name_value:CTTermNameValue)
                    WHERE (name_v_rel.start_date<= exact_datetime < name_v_rel.end_date OR (name_v_rel.end_date IS NULL AND name_v_rel.start_date <= exact_datetime))
                        AND (attr_v_rel.start_date<= exact_datetime < attr_v_rel.end_date OR (attr_v_rel.end_date IS NULL AND attr_v_rel.start_date <= exact_datetime))
                    RETURN DISTINCT term_root, term_name_root, term_name_value, term_attributes_root, term_attributes_value, attr_v_rel, name_v_rel
                }
                """

        else:
            if package:
                match_clause = """
                MATCH (package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_TERM]->(:CTPackageTerm)-
                [:CONTAINS_ATTRIBUTES]->(term_attributes_value:CTTermAttributesValue)<--(term_attributes_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                (term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue)
                """
            else:
                match_clause = """
                MATCH (term_name_value:CTTermNameValue)<-[:LATEST]-(term_name_root:CTTermNameRoot)<-[:HAS_NAME_ROOT]-(term_root:CTTermRoot)
                -[:HAS_ATTRIBUTES_ROOT]->(term_attributes_root:CTTermAttributesRoot)-[:LATEST]->(term_attributes_value:CTTermAttributesValue)
                """

        filter_query_parameters = {}
        if library_name or package:
            # Build specific filtering for package and library
            # This is separate from generic filtering as the list of filters is predefined
            # We can therefore do this filtering in an efficient way in the Cypher MATCH clause
            (
                filter_statements,
                filter_query_parameters,
            ) = create_term_filter_statement(
                library_name=library_name, package=package, is_sponsor=is_sponsor
            )
            match_clause += filter_statements

        if not package:
            match_clause += f""" OPTIONAL MATCH (ct_codelist_attributes_value:CTCodelistAttributesValue)<-[:LATEST]-(ct_codelist_attributes_root:CTCodelistAttributesRoot)
            <-[:HAS_ATTRIBUTES_ROOT]-(codelist_root:CTCodelistRoot)-[rel_term:HAS_TERM{"" if not include_removed_terms else "|HAD_TERM"}]->(term_root)
            WITH * """
        else:
            # We are listing terms for a specific package, we need to include HAD_TERM relationships also.
            # If not, we would only get terms that are also in the latest version of the package,
            # not those that were in the past.
            match_clause += """ MATCH (ct_codelist_attributes_value:CTCodelistAttributesValue)<-[:LATEST]-(ct_codelist_attributes_root:CTCodelistAttributesRoot)
            <-[:HAS_ATTRIBUTES_ROOT]-(codelist_root:CTCodelistRoot)-[rel_term:HAS_TERM|HAD_TERM]->(term_root) """

        if codelist_uid or codelist_name:
            # Build specific filtering for codelist
            # This is done separately from library and package as we first need to match codelist_root
            (
                codelist_filter_statements,
                codelist_filter_query_parameters,
            ) = create_term_filter_statement(
                codelist_uid=codelist_uid,
                codelist_name=codelist_name,
                is_sponsor=is_sponsor,
                package=package,
            )
            match_clause += codelist_filter_statements
            filter_query_parameters.update(codelist_filter_query_parameters)

        return match_clause, filter_query_parameters

    def count_all(self) -> list[TermCount]:
        """
        Returns the count of CT Terms in the database, grouped by Library

        :return: list[TermCount] - count of CT Terms
        """
        query = """
            MATCH (n:CTTermRoot)<-[:CONTAINS_TERM]-(l:Library)
            RETURN l.name as library_name, count(n) as count
            """

        result, _ = db.cypher_query(query)
        return [TermCount(library_name=item[0], count=item[1]) for item in result]

    def get_change_percentage(self) -> float:
        """
        Returns the percentage of CT Terms with more than one version

        :return: float - percentage
        """
        query = """
            MATCH (r:CTTermNameRoot)-->(v:CTTermNameValue)
            RETURN CASE count(r)
                WHEN 0 THEN 0
                ELSE (count(v)-count(r))/count(r)
                END AS percentage
            """

        result, _ = db.cypher_query(query)
        return result[0][0] if len(result) > 0 else 0.0

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass
