from datetime import datetime
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_get_all_query_utils import (
    create_term_attributes_aggregate_instances_from_cypher_result,
    create_term_codelist_vos_from_cypher_result,
    create_term_filter_statement,
    create_term_name_aggregate_instances_from_cypher_result,
    format_term_filter_sort_keys,
    format_term_filter_sort_keys_for_headers_lite,
    list_term_wildcard_properties,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    convert_to_datetime,
    format_generic_header_values,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermNameAR,
    CTTermVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_stats import TermCount
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTermNameAndAttributes,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_codelist import (
    CTTermCodelist,
)
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    calculate_total_count_from_query_result,
    validate_filter_by_dict,
    validate_filters_and_add_search_string,
)
from common.config import settings
from common.exceptions import ValidationException


class CTTermAggregatedRepository:
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
            term_root.uid AS term_uid,
            catalogue_names,
            codelists,
            term_attributes_value AS value_node_attributes,
            term_name_value AS value_node_name,
            library.name AS library_name,
            library.is_editable AS is_library_editable,
            ANY(cl IN codelists WHERE cl.codelist_uid IN $ts_codelist_uids) AS _is_ts_term,
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
            } AS rel_data_name
        CALL apoc.when(
            coalesce(_is_ts_term, false) AND coalesce($include_ts_parameters, true),
            'OPTIONAL MATCH (value_node_name)-[:RELATED_STUDY_FIELD_SELECTION]->(msf:MetaStudyField)
             OPTIONAL MATCH (msf)-[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(dt_term:CTTermRoot)
             OPTIONAL MATCH (dt_term)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(dt_name:CTTermNameValue)
             OPTIONAL MATCH (value_node_name)-[:RESPONSE_CODELIST]->(resp_cl:CTCodelistRoot)
             OPTIONAL MATCH (resp_cl)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST_FINAL]->(resp_cl_name:CTCodelistNameValue)
             OPTIONAL MATCH (value_node_name)-[:RESPONSE_DICTIONARY]->(resp_dict:DictionaryCodelistRoot)
             OPTIONAL MATCH (value_node_name)-[:VALID_NULL_FLAVOR]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(nf_term:CTTermRoot)
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
            {value_node_name: value_node_name}
        ) YIELD value AS ts_props
        WITH *, ts_props.osb_field_name AS osb_field_name,
                ts_props.osb_page_reference AS osb_page_reference,
                ts_props.semantic_data_type_uid AS semantic_data_type_uid,
                ts_props.semantic_data_type_name AS semantic_data_type_name,
                ts_props.response_codelist_uid AS response_codelist_uid,
                ts_props.response_codelist_name AS response_codelist_name,
                ts_props.response_dictionary_uids AS response_dictionary_uids,
                ts_props.valid_null_flavor_term_uids AS valid_null_flavor_term_uids,
                ts_props.valid_null_flavor_term_names AS valid_null_flavor_term_names
    """

    def generic_alias_clause(self, package: str | None = None) -> str:
        if package is not None:
            has_term_where = ""
        else:
            has_term_where = "WHERE rel_term.end_date IS NULL"
        query = f"""
            DISTINCT term_root, term_attributes_root, term_attributes_value, term_name_root, term_name_value
            ORDER BY term_name_value.name
            WITH DISTINCT term_root, term_attributes_root, term_attributes_value, term_name_root, term_name_value, 
            COLLECT {{
                MATCH (codelist_library:Library)-[:CONTAINS_CODELIST]->(codelist_root:CTCodelistRoot)-[rel_term:HAS_TERM]->
                  (codelist_term:CTCodelistTerm)-[rel_term_root:HAS_TERM_ROOT]->(term_root) {has_term_where}
                MATCH (codelist_name_value:CTCodelistNameValue)<-[:LATEST]-(codelist_name_root:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-
                  (codelist_root)-[:HAS_ATTRIBUTES_ROOT]->(codelist_attributes_root:CTCodelistAttributesRoot)-[:LATEST]->(codelist_attributes_value:CTCodelistAttributesValue)
                RETURN {{
                    codelist_uid: codelist_root.uid,
                    codelist_name: codelist_name_value.name,
                    codelist_submission_value: codelist_attributes_value.submission_value,
                    codelist_concept_id: codelist_attributes_value.concept_id,
                    submission_value: codelist_term.submission_value,
                    order: rel_term.order,
                    library_name: codelist_library.name,
                    start_date: rel_term.start_date
                }} AS codelists
            }} AS codelists,
            COLLECT {{
                MATCH (catalogue:CTCatalogue)-[:CONTAINS_PACKAGE]->(:CTPackage)-[:CONTAINS_CODELIST]->
                  (:CTPackageCodelist)-[:CONTAINS_TERM]-(:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]-(term_attributes_value)
                RETURN DISTINCT catalogue.name as catalogue_names
                UNION
                MATCH (catalogue2:CTCatalogue)-[:HAS_CODELIST]->(:CTCodelistRoot)-[cat_cl_ht:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root)
                WHERE cat_cl_ht.end_date IS NULL
                RETURN DISTINCT catalogue2.name as catalogue_names
            }} AS catalogue_names,
            head([(lib)-[:CONTAINS_TERM]->(term_root) | lib]) AS library
            CALL (term_attributes_root, term_attributes_value) {{
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
            CALL (term_name_root, term_name_value) {{
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
            {self.generic_final_alias_clause}
        """
        return query

    def sponsor_alias_clause(self, package: str | None = None) -> str:
        if package is not None:
            has_term_where = ""
        else:
            has_term_where = "WHERE rel_term.end_date IS NULL"
        query = f"""
            DISTINCT term_root, term_attributes_root, term_attributes_value, term_name_root, term_name_value, attr_v_rel, name_v_rel
            ORDER BY term_name_value.name
            WITH DISTINCT term_root, term_attributes_root, term_attributes_value, term_name_root, term_name_value,
            attr_v_rel AS rel_data_attributes, name_v_rel AS rel_data_name,
            COLLECT {{
                MATCH (codelist_library:Library)-[:CONTAINS_CODELIST]->(codelist_root:CTCodelistRoot)-[rel_term:HAS_TERM]->
                  (codelist_term:CTCodelistTerm)-[rel_term_root:HAS_TERM_ROOT]->(term_root) {has_term_where}
                MATCH (codelist_name_value:CTCodelistNameValue)<-[:LATEST]-(codelist_name_root:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-
                  (codelist_root)-[:HAS_ATTRIBUTES_ROOT]->(codelist_attributes_root:CTCodelistAttributesRoot)-[:LATEST]->(codelist_attributes_value:CTCodelistAttributesValue)
                RETURN {{
                    codelist_uid: codelist_root.uid,
                    codelist_name: codelist_name_value.name,
                    codelist_submission_value: codelist_attributes_value.submission_value,
                    codelist_concept_id: codelist_attributes_value.concept_id,
                    submission_value: codelist_term.submission_value,
                    order: rel_term.order,
                    library_name: codelist_library.name,
                    start_date: rel_term.start_date
                }} AS codelists
            }} AS codelists,
            COLLECT {{
                MATCH (catalogue:CTCatalogue)-[:CONTAINS_PACKAGE]->(:CTPackage)-[:CONTAINS_CODELIST]->
                  (:CTPackageCodelist)-[:CONTAINS_TERM]-(:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]-(term_attributes_value)
                RETURN DISTINCT catalogue.name as catalogue_names
                UNION
                MATCH (catalogue2:CTCatalogue)-[:HAS_CODELIST]->(:CTCodelistRoot)-[cat_cl_ht:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root)
                WHERE cat_cl_ht.end_date IS NULL
                RETURN DISTINCT catalogue2.name as catalogue_names
            }} AS catalogue_names,
            head([(lib)-[:CONTAINS_TERM]->(term_root) | lib]) AS library
            MATCH (codelist_root)<-[:CONTAINS_CODELIST]-(codelist_library:Library)
            {self.generic_final_alias_clause}
        """
        return query

    def _create_term_aggregate_instances_from_cypher_result(
        self, term_dict: dict[str, Any]
    ) -> tuple[CTTermNameAR, CTTermAttributesAR, CTTermVO]:
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
        term_codelists = create_term_codelist_vos_from_cypher_result(
            term_dict=term_dict
        )
        return term_name_ar, term_attributes_ar, term_codelists

    def find_all_aggregated_result(
        self,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        is_sponsor: bool = False,
        include_removed_terms: bool = False,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        include_ts_parameters: bool = True,
    ) -> tuple[list[tuple[CTTermNameAR, CTTermAttributesAR, CTTermVO]], int]:
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
        :return tuple[list[tuple[CTTermNameAR, CTTermAttributesAR]], int]:
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

        filter_by = validate_filter_by_dict(filter_by)
        filtering_active = (
            filter_by is not None
            and len(filter_by) > 0
            or library is not None
            or package is not None
            or codelist_name is not None
            or codelist_uid is not None
        )

        # Build alias_clause
        alias_clause = (
            self.sponsor_alias_clause(package=package)
            if is_sponsor
            else self.generic_alias_clause(package=package)
        )

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            implicit_sort_by="term_uid",
            page_number=page_number,
            page_size=page_size,
            one_element_extra=filtering_active,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
            wildcard_properties_list=list_term_wildcard_properties(),
            format_filter_sort_keys=format_term_filter_sort_keys,
            return_model=CTTermNameAndAttributes,
        )

        query.parameters.update(filter_query_parameters)
        query.parameters["ts_codelist_uids"] = [
            settings.ts_parmcd_codelist_uid,
            settings.ts_parm_codelist_uid,
        ]
        query.parameters["include_ts_parameters"] = include_ts_parameters
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

        total = calculate_total_count_from_query_result(
            len(terms_ars),
            page_number,
            page_size,
            total_count,
            extra_requested=filtering_active,
        )
        if 0 < page_size < len(terms_ars):
            terms_ars = terms_ars[:page_size]
        if total is None:
            if not filtering_active:
                count_query = "MATCH (term_root:CTTermRoot) RETURN count(term_root) AS total_count"
                count_result, _ = db.cypher_query(query=count_query)
                total = count_result[0][0] if len(count_result) > 0 else 0
            else:
                total = -1
        return terms_ars, total

    def get_distinct_headers(
        self,
        field_name: str,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
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
        # Delegate list fields (codelists.*) to the lite path which paginates
        # on individual values rather than on per-term grouped lists, giving
        # consistent results with the lite=True endpoint.
        if field_name.startswith("codelists."):
            return self.get_distinct_headers_lite(
                field_name=field_name,
                codelist_uid=codelist_uid,
                codelist_name=codelist_name,
                library=library,
                package=package,
                is_sponsor=is_sponsor,
                search_string=search_string,
                filter_by=filter_by,
                page_size=page_size,
            )

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
            self.sponsor_alias_clause(package=package)
            if is_sponsor
            else self.generic_alias_clause(package=package)
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
            wildcard_properties_list=list_term_wildcard_properties(),
            format_filter_sort_keys=format_term_filter_sort_keys,
            return_model=CTTermNameAndAttributes,
        )
        query.full_query = query.build_header_query(
            header_alias=format_term_filter_sort_keys(field_name),
            page_size=page_size,
        )

        query.parameters.update(filter_query_parameters)
        query.parameters["ts_codelist_uids"] = [
            settings.ts_parmcd_codelist_uid,
            settings.ts_parm_codelist_uid,
        ]
        query.parameters["include_ts_parameters"] = False
        result_array, _ = query.execute()

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    def get_distinct_headers_lite(
        self,
        field_name: str,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        is_sponsor: bool = False,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        page_size: int = 10,
    ) -> list[Any]:
        match_clause, filter_query_parameters = self._generate_generic_match_clause(
            codelist_uid=codelist_uid,
            codelist_name=codelist_name,
            library_name=library,
            package=package,
            is_sponsor=is_sponsor,
        )

        # Set header field name in the `filter_by` dict,
        # which will be used to generate `WHERE toLower(toString(field_name)) CONTAINS ...` clause
        filter_by = validate_filters_and_add_search_string(
            search_string, field_name, filter_by=None
        )

        # Specific match clauses for each field, so that only necessary data is fetched

        if field_name in ["term_uid"]:
            match_clause += """
                WITH DISTINCT term_root.uid AS term_uid
            """

        if field_name in [
            "name.status",
            "name.start_date",
            "name.version",
            "attributes.status",
            "attributes.start_date",
            "attributes.version",
        ]:
            prefix = field_name.split(".")[0]
            root = f"term_{prefix}_root"
            value = f"term_{prefix}_value"

            match_clause += f"""
                WITH DISTINCT term_root, term_attributes_root, term_attributes_value, term_name_root, term_name_value
                
                CALL ({root}, {value}) {{
                    MATCH ({root})-[hv:HAS_VERSION]->({value})
                    WITH hv
                    ORDER BY
                        toInteger(split(hv.version, '.')[0]) ASC,
                        toInteger(split(hv.version, '.')[1]) ASC,
                        hv.end_date ASC,
                        hv.start_date ASC
                    WITH collect(hv) as hvs
                    RETURN last(hvs) AS version_rel
                }}

                WITH    version_rel.status AS {prefix}_status,
                        version_rel.start_date AS {prefix}_start_date,
                        version_rel.version AS {prefix}_version
            """

        elif field_name in [
            "name.name",
            "name.name_sentence_case",
            "name.sponsor_preferred_name",  # Alias of `name.name`
            "attributes.concept_id",
            "attributes.definition",
            "attributes.synonyms",
            "attributes.nci_preferred_name",  # Alias of `preferred_term`
        ]:
            prefix = field_name.split(".")[0]
            db_property, alias = self._get_db_property_and_alias_for_api_field(
                field_name
            )

            match_clause += f"""
                WITH term_{prefix}_value.{db_property} AS {alias}
            """

        elif field_name == "library_name":
            match_clause += """
                WITH DISTINCT term_root,
                    head([(library)-[:CONTAINS_TERM]->(term_root) | library]) AS library
                WITH library.name AS library_name
            """

        elif field_name in [
            "codelists.codelist_uid",
            "codelists.codelist_name",
            "codelists.codelist_submission_value",
            "codelists.submission_value",
            "codelists.codelist_concept_id",
            "codelists.order",
            "codelists.library",
            "codelists.start_date",
        ]:
            db_property, alias = self._get_db_property_and_alias_for_api_field(
                field_name
            )
            match_clause += f"""
            WITH DISTINCT term_root, term_attributes_root, term_attributes_value, term_name_root, term_name_value, 
                COLLECT {{
                    MATCH (codelist_library:Library)-[:CONTAINS_CODELIST]->(codelist_root:CTCodelistRoot)-[rel_term:HAS_TERM]->
                    (codelist_term:CTCodelistTerm)-[rel_term_root:HAS_TERM_ROOT]->(term_root) WHERE rel_term.end_date IS NULL
                    MATCH (codelist_name_value:CTCodelistNameValue)<-[:LATEST]-(codelist_name_root:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-
                    (codelist_root)-[:HAS_ATTRIBUTES_ROOT]->(codelist_attributes_root:CTCodelistAttributesRoot)-[:LATEST]->(codelist_attributes_value:CTCodelistAttributesValue)
                    RETURN {{
                        codelist_uid: codelist_root.uid,
                        codelist_name: codelist_name_value.name,
                        codelist_submission_value: codelist_attributes_value.submission_value,
                        codelist_concept_id: codelist_attributes_value.concept_id,
                        submission_value: codelist_term.submission_value,
                        order: rel_term.order,
                        library: codelist_library.name,
                        start_date: rel_term.start_date
                    }} AS codelists
                }} AS codelists

            WITH DISTINCT [x in codelists | x.{db_property}] AS {alias}
            WITH apoc.coll.toSet(apoc.coll.flatten(collect(DISTINCT {alias}))) AS vals
            UNWIND vals as {alias}
            WITH {alias}
            """

        if field_name in [
            "name.author_username",
            "attributes.author_username",
        ]:
            prefix = field_name.split(".")[0]
            root = f"term_{prefix}_root"
            value = f"term_{prefix}_value"

            match_clause += f"""
                WITH DISTINCT term_root, {root}, {value}

                CALL ({root}, {value}) {{
                    MATCH ({root})-[hv:HAS_VERSION]->({value})
                    WITH hv
                    ORDER BY
                        toInteger(split(hv.version, '.')[0]) ASC,
                        toInteger(split(hv.version, '.')[1]) ASC,
                        hv.end_date ASC,
                        hv.start_date ASC
                    WITH collect(hv) as hvs
                    RETURN last(hvs) AS version_rel
                }}
                CALL (version_rel) {{
                    OPTIONAL MATCH (author: User)
                    WHERE author.user_id = version_rel.author_id
                    RETURN author
                }}
                WITH author.username AS {field_name.replace(".", "_")}
            """

        query = CypherQueryBuilder(
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            match_clause=match_clause,
            alias_clause=field_name.replace(".", "_"),
            return_model=CTTermNameAndAttributes,
            format_filter_sort_keys=format_term_filter_sort_keys_for_headers_lite,
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

    def _get_db_property_and_alias_for_api_field(
        self, field_name: str
    ) -> tuple[str, str]:
        """Some API fields do not map 1:1 to the database properties, so we need a mapping for those.
        For other fields, we just take the part after the dot as the database property.

        :param field_name: The API field name
        :return: A tuple containing the database property name and the alias
        """

        special_mappings = {
            # "api_field_name": "db_property_name"
            "name.sponsor_preferred_name": "name",
            "attributes.nci_preferred_name": "preferred_term",
        }

        db_property = special_mappings.get(field_name, field_name.split(".")[1])
        alias = field_name.replace(".", "_")

        return db_property, alias

    def _generate_generic_match_clause(
        self,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library_name: str | None = None,
        package: str | None = None,
        is_sponsor: bool = False,
        include_removed_terms: bool = False,
    ) -> tuple[str, dict[Any, Any]]:
        match_clause = ""
        if is_sponsor:
            ValidationException.raise_if_not(
                package, msg="Package must be provided when fetching sponsor terms."
            )

            match_clause += f"""
                MATCH (package:CTPackage)-[:EXTENDS_PACKAGE]->(parent_package:CTPackage)
                WITH package, parent_package, datetime(toString(date(package.effective_date)) + 'T23:59:59') AS exact_datetime
                {"WHERE package.name=$package_name" if package else ""}
            """

            if library_name:
                if library_name == settings.cdisc_library_name:
                    # We must look in the library and the parent package
                    match_clause += """
                        MATCH (parent_package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_TERM]->(:CTPackageTerm)-
                        [:CONTAINS_ATTRIBUTES]->(term_attributes_value:CTTermAttributesValue)<-[attr_v_rel:HAS_VERSION]-(term_attributes_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                        (term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[name_v_rel:HAS_VERSION]->(term_name_value:CTTermNameValue)
                        WHERE name_v_rel.start_date<= exact_datetime < name_v_rel.end_date OR (name_v_rel.end_date IS NULL AND name_v_rel.start_date <= exact_datetime)
                        MATCH (library:Library)-[:CONTAINS_TERM]->(term_root)
                        WITH DISTINCT term_root, term_name_root, term_name_value, term_attributes_root, term_attributes_value, attr_v_rel, name_v_rel
                    """
                # We will look only in a specific library
                else:
                    match_clause += """
                        MATCH (:Library {name:$library_name})-->(term_root:CTTermRoot)
                            -[:HAS_ATTRIBUTES_ROOT]->(term_attributes_root:CTTermAttributesRoot)-[attr_v_rel:HAS_VERSION]->(term_attributes_value:CTTermAttributesValue)
                        MATCH (term_root)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[name_v_rel:HAS_VERSION]->(term_name_value:CTTermNameValue)
                        WHERE (name_v_rel.start_date<= exact_datetime < name_v_rel.end_date OR (name_v_rel.end_date IS NULL AND name_v_rel.start_date <= exact_datetime))
                            AND (attr_v_rel.start_date<= exact_datetime < attr_v_rel.end_date OR (attr_v_rel.end_date IS NULL AND attr_v_rel.start_date <= exact_datetime))
                        WITH DISTINCT term_root, term_name_root, term_name_value, term_attributes_root, term_attributes_value, attr_v_rel, name_v_rel
                """
            else:
                # Otherwise, we need to combine the sponsor terms with the terms in the parent package
                match_clause += """
                CALL (package, parent_package, exact_datetime) {
                    MATCH (parent_package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_TERM]->(:CTPackageTerm)-
                        [:CONTAINS_ATTRIBUTES]->(term_attributes_value:CTTermAttributesValue)<-[attr_v_rel:HAS_VERSION]-(term_attributes_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                        (term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[name_v_rel:HAS_VERSION]->(term_name_value:CTTermNameValue)
                    WHERE name_v_rel.start_date<= exact_datetime < name_v_rel.end_date OR (name_v_rel.end_date IS NULL AND name_v_rel.start_date <= exact_datetime)
                    RETURN DISTINCT term_root, term_name_root, term_name_value, term_attributes_root, term_attributes_value, attr_v_rel, name_v_rel

                    UNION
                    WITH exact_datetime
                    MATCH (l:Library WHERE NOT l.name=$cdisc_library_name)-->(term_root:CTTermRoot)
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

        filter_query_parameters: dict[Any, Any] = {}
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
            # We exclude codelists that the term has been removed from, meaning the end_date of HAS_TERM is set
            match_clause += f""" OPTIONAL MATCH (codelist_root:CTCodelistRoot)-[rel_term:HAS_TERM]->
                                  (codelist_term:CTCodelistTerm)-[rel_term_root:HAS_TERM_ROOT]->(term_root)
                                {"WHERE rel_term.end_date IS NULL" if include_removed_terms else ""} WITH *
                            """

        else:
            # We are listing terms for a specific package, we need to include all HAS_TERM relationships, including those with an end_date.
            # If not, we would only get terms that are also in the latest version of the package,
            # not those that were in the past.
            match_clause += " OPTIONAL MATCH (codelist_root:CTCodelistRoot)-[rel_term:HAS_TERM]->(codelist_term:CTCodelistTerm)-[rel_term_root:HAS_TERM_ROOT]->(term_root) "

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

        if is_sponsor:
            if library_name:
                filter_query_parameters["library_name"] = library_name
            else:
                filter_query_parameters["cdisc_library_name"] = (
                    settings.cdisc_library_name
                )
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

    def find_term_codelists(
        self,
        term_uid: str,
        at_specific_date_time: datetime | None = None,
    ) -> list[CTTermCodelist]:
        if at_specific_date_time is not None:
            match_clause = """
                MATCH (term_root:CTTermRoot {uid: $term_uid})<-[:HAS_TERM_ROOT]-(codelist_term:CTCodelistTerm)<-[ht:HAS_TERM]-
                  (codelist_root:CTCodelistRoot)<-[:CONTAINS_CODELIST]-(codelist_library:Library)
                WHERE (ht.end_date IS NULL OR ht.end_date > datetime($at_specific_date_time)) AND ht.start_date <= datetime($at_specific_date_time)
                MATCH (codelist_name_value:CTCodelistNameValue)<-[:LATEST]-(:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-
                  (codelist_root)-[:HAS_ATTRIBUTES_ROOT]->(codelist_attributes_root:CTCodelistAttributesRoot)-[:LATEST]->(codelist_attributes_value:CTCodelistAttributesValue)
                """
        else:
            match_clause = """
                MATCH (term_root:CTTermRoot {uid: $term_uid})<-[:HAS_TERM_ROOT]-(codelist_term:CTCodelistTerm)<-[ht:HAS_TERM]-
                  (codelist_root:CTCodelistRoot)<-[:CONTAINS_CODELIST]-(codelist_library:Library)
                WHERE ht.end_date IS NULL
                MATCH (codelist_name_value:CTCodelistNameValue)<-[:LATEST]-(:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-
                  (codelist_root)-[:HAS_ATTRIBUTES_ROOT]->(codelist_attributes_root:CTCodelistAttributesRoot)-[:LATEST]->(codelist_attributes_value:CTCodelistAttributesValue)
                """
        alias_clause = """
                DISTINCT term_root, codelist_term, codelist_root, codelist_name_value, codelist_attributes_value, codelist_library, ht
                WITH
                    codelist_root.uid AS codelist_uid,
                    codelist_name_value.name AS codelist_name,
                    codelist_attributes_value.submission_value AS codelist_submission_value,
                    codelist_attributes_value.concept_id AS codelist_concept_id,
                    codelist_term.submission_value AS term_submission_value,
                    ht.order AS term_order,
                    ht.ordinal AS term_ordinal,
                    ht.start_date AS term_start_date,
                    codelist_library.name AS library_name
                """
        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            return_model=CTTermCodelist,
        )

        query.parameters["term_uid"] = term_uid
        if at_specific_date_time:
            query.parameters.update({"at_specific_date_time": at_specific_date_time})

        result_array, attributes_names = query.execute()

        return self._create_term_codelists_from_cypher_result(
            result_array, attributes_names
        )

    def _create_term_codelists_from_cypher_result(
        self, result_array: list[Any], attributes_names: list[str]
    ) -> list[CTTermCodelist]:
        codelists = []
        for cl in result_array:
            cl_dictionary = {}
            for prop, name in zip(cl, attributes_names):
                cl_dictionary[name] = prop
            codelists.append(
                CTTermCodelist(
                    codelist_uid=cl_dictionary["codelist_uid"],
                    submission_value=cl_dictionary["term_submission_value"],
                    order=cl_dictionary["term_order"],
                    ordinal=cl_dictionary.get("term_ordinal"),
                    library_name=cl_dictionary["library_name"],
                    codelist_name=cl_dictionary["codelist_name"],
                    codelist_submission_value=cl_dictionary[
                        "codelist_submission_value"
                    ],
                    codelist_concept_id=cl_dictionary["codelist_concept_id"],
                    start_date=convert_to_datetime(cl_dictionary["term_start_date"]),
                )
            )
        return codelists
