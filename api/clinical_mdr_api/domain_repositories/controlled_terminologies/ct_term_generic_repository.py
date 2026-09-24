from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, cast

from cachetools.keys import hashkey
from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_get_all_query_utils import (
    create_term_filter_statement,
    format_term_filter_sort_keys,
)
from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    ControlledTerminology,
    CTTermNameRoot,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.syntax import SyntaxTemplateRoot
from clinical_mdr_api.domains.controlled_terminologies.utils import TermParentType
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTermName
from clinical_mdr_api.models.controlled_terminologies.ct_term_attributes import (
    CTTermAttributes,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    cached_skip_on,
    calculate_total_count_from_query_result,
    sb_clear_cache,
    validate_filters_and_add_search_string,
)
from common.config import settings
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    NotFoundException,
)


class CTTermGenericRepository(
    LibraryItemRepositoryImplBase, Generic[_AggregateRootType], ABC
):
    root_class = type
    value_class = type
    relationship_from_root: str

    generic_alias_clause = """
        DISTINCT term_root, term_ver_root, term_ver_value, codelist_root, rel_term
        ORDER BY term_ver_value.name
        WITH DISTINCT term_root, term_ver_root, term_ver_value,
        [(catalogue:CTCatalogue)-[:HAS_CODELIST]->(codelist_root) | catalogue.name] AS catalogue_names,
        head([(lib)-[:CONTAINS_TERM]->(term_root) | lib]) AS library,
        codelist_root.uid IN $ts_codelist_uids AS is_ts_term
        WITH
            term_root,
            term_ver_root,
            term_ver_value,
            apoc.coll.dropDuplicateNeighbors(apoc.coll.sort(apoc.coll.flatten(collect(catalogue_names)))) AS catalogue_names,
            library,
            collect(DISTINCT is_ts_term) AS ts_flags
        WITH *, true IN ts_flags AS is_ts_term
        CALL (term_ver_root, term_ver_value) {
                MATCH (term_ver_root)-[hv:HAS_VERSION]-(term_ver_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS rel_data
            }
        WITH
            term_root.uid AS term_uid,
            catalogue_names,
            term_ver_value AS value_node,
            library.name AS library_name,
            library.is_editable AS is_library_editable,
            is_ts_term,
            {
                start_date: rel_data.start_date,
                end_date: NULL,
                status: rel_data.status,
                version: rel_data.version,
                change_description: rel_data.change_description,
                author_id: rel_data.author_id
            } AS rel_data
            CALL (rel_data) {
                OPTIONAL MATCH (author: User)
                WHERE author.user_id = rel_data.author_id
                // RETURN author
                RETURN coalesce(author.username, rel_data.author_id) AS author_username 
            }
        CALL apoc.when(
            coalesce(is_ts_term, false) AND coalesce($include_ts_parameters, true),
            'OPTIONAL MATCH (value_node)-[:RELATED_STUDY_FIELD_SELECTION]->(msf:MetaStudyField)
             OPTIONAL MATCH (msf)-[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(dt_term:CTTermRoot)
             OPTIONAL MATCH (dt_term)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(dt_name:CTTermNameValue)
             OPTIONAL MATCH (value_node)-[:RESPONSE_CODELIST]->(resp_cl:CTCodelistRoot)
             OPTIONAL MATCH (resp_cl)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST_FINAL]->(resp_cl_name:CTCodelistNameValue)
             OPTIONAL MATCH (value_node)-[:RESPONSE_DICTIONARY]->(resp_dict:DictionaryCodelistRoot)
             OPTIONAL MATCH (value_node)-[:VALID_NULL_FLAVOR]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(nf_term:CTTermRoot)
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
            {value_node: value_node}
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

    def generate_uid(self) -> str:
        return CTTermRoot.get_next_free_uid_and_increment_counter()

    def term_specific_exists_by_uid(self, uid: str | None) -> bool:
        """
        Returns True or False depending on if there exists a term with a final version for a given uid
        :return:
        """
        if uid is None:
            return False

        query = """
            MATCH (term_ver_root:CTTermRoot {uid: $uid})
            RETURN term_ver_root
            """
        result, _ = db.cypher_query(query, {"uid": uid})
        return len(result) > 0

    def term_specific_order_by_uid(self, uid: str) -> int | None:
        """
        Returns the latest final version order number if a order number exists for a given term uid
        :return:
        """
        query = """
            MATCH (term_ver_root:CTTermRoot {uid: $uid})<-[rel_term:HAS_TERM]-(codelist_root:CTCodelistRoot)
            RETURN rel_term.order as order
            """
        result, _ = db.cypher_query(query, {"uid": uid})
        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0]
        return None

    def term_specific_order_by_uid_and_cl_submval(
        self, uid: str, cl_submval: str
    ) -> int | None:
        """
        Returns the latest final version order number if a order number exists for a given term uid and codelist submission value
        :return:
        """
        query = """
            MATCH (term_root:CTTermRoot {uid: $uid})<-[:HAS_TERM_ROOT]-(codelist_term:CTCodelistTerm)<-[ht:HAS_TERM]-(:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(cl_attr_value:CTCodelistAttributesValue {submission_value: $cl_submval})
            RETURN ht.order as order
            """
        result, _ = db.cypher_query(query, {"uid": uid, "cl_submval": cl_submval})
        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0]
        return None

    @abstractmethod
    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ControlledTerminology,
        library: Library,
        relationship: VersionRelationship,
        value: ControlledTerminology,
        **_kwargs,
    ) -> _AggregateRootType:
        raise NotImplementedError

    @abstractmethod
    def _create_aggregate_root_instance_from_cypher_result(
        self, term_dict: dict[str, Any]
    ) -> _AggregateRootType:
        """
        Creates aggregate root instances from cypher query result.
        :param terms_dict:
        :return _AggregateRootType:
        """
        raise NotImplementedError

    def term_exists(self, term_uid: str) -> bool:
        query = """
            MATCH (term_root:CTTermRoot {uid: $uid})-[:HAS_NAME_ROOT]->(term_ver_root:CTTermNameRoot)-[:LATEST_FINAL]->(term_ver_value:CTTermNameValue)
            RETURN term_root
            """
        result, _ = db.cypher_query(query, {"uid": term_uid})
        if len(result) > 0 and len(result[0]) > 0:
            return True
        return False

    def get_term_name_and_attributes_by_codelist_uids(self, codelist_uids: list[Any]):
        query = """
            MATCH (codelist:CTCodelistRoot)-[ht:HAS_TERM]->(codelist_term:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root:CTTermRoot)
            -[:HAS_ATTRIBUTES_ROOT]->(term_attr_root:CTTermAttributesRoot)-[:LATEST]->(term_attr_value:CTTermAttributesValue)
            MATCH (term_root)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue)
            WHERE codelist.uid in $codelist_uids and ht.end_date IS NULL
            RETURN
                term_name_value.name as name,
                term_root.uid as term_uid,
                codelist.uid as codelist_uid,
                codelist_term.submission_value as submission_value,
                term_attr_value.preferred_term as nci_preferred_name
            """

        items, prop_names = db.cypher_query(query, {"codelist_uids": codelist_uids})

        return items, prop_names

    def get_term_attributes_by_term_uids(self, term_uids: list[Any]):
        query = """
            MATCH (term_root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(term_attr_root:CTTermAttributesRoot)-[:LATEST]->(term_attr_value:CTTermAttributesValue)
            WHERE term_root.uid in $term_uids
            RETURN term_root.uid as term_uid, term_attr_value.preferred_term as nci_preferred_name
            """

        items, prop_names = db.cypher_query(query, {"term_uids": term_uids})

        return items, prop_names

    def get_codelist_to_term_properties(self, term_uid: str, codelist_uid: str):
        query = """
            MATCH (codelist_root {uid: $codelist_uid})-[ht:HAS_TERM]->(cct:CTCodelistTerm)-[:HAS_TERM_ROOT]->(:CTTermRoot {uid: $term_uid})
            RETURN
                ht.start_date AS start_date,
                ht.end_date AS end_date,
                ht.order AS order,
                ht.ordinal AS ordinal,
                cct.submission_value AS submission_value
            ORDER BY ht.start_date DESC
            LIMIT 1
            """

        items, prop_names = db.cypher_query(
            query, {"term_uid": term_uid, "codelist_uid": codelist_uid}
        )

        if not items or not items[0]:
            return {}

        return dict(zip(prop_names, items[0]))

    def find_all(
        self,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library_name: str | None = None,
        package: str | None = None,
        in_codelist: bool = False,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        include_ts_parameters: bool = True,
        **_kwargs,
    ) -> GenericFilteringReturn[_AggregateRootType]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Terms aggregates.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param codelist_uid:
        :param codelist_name:
        :param library_name:
        :param package:
        :param sort_by:
        :param page_number:
        :param page_size:
        :param filter_by:
        :param filter_operator:
        :param total_count:
        :return GenericFilteringReturn[_AggregateRootType]:
        """
        BusinessLogicException.raise_if(
            self.relationship_from_root not in vars(CTTermRoot),
            msg=f"The relationship of type '{self.relationship_from_root}' was not found in CTTermRoot object",
        )

        # Build match_clause
        match_clause, filter_query_parameters = self._generate_generic_match_clause(
            codelist_uid=codelist_uid,
            codelist_name=codelist_name,
            library_name=library_name,
            package=package,
            in_codelist=in_codelist,
        )

        # Build alias_clause
        alias_clause = self.generic_alias_clause

        _return_model = (
            CTTermAttributes
            if self.is_repository_related_to_attributes()
            else CTTermName
        )

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            implicit_sort_by="term_uid",
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
            return_model=_return_model,
            format_filter_sort_keys=format_term_filter_sort_keys,
        )
        query.parameters.update(filter_query_parameters)
        query.parameters["ts_codelist_uids"] = [
            settings.ts_parmcd_codelist_uid,
            settings.ts_parm_codelist_uid,
        ]
        query.parameters["include_ts_parameters"] = include_ts_parameters
        result_array, attributes_names = query.execute()
        extracted_items = self._retrieve_term_from_cypher_res(
            result_array, attributes_names
        )

        total = calculate_total_count_from_query_result(
            len(extracted_items), page_number, page_size, total_count
        )
        if total is None:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            total = count_result[0][0] if len(count_result) > 0 else 0

        return GenericFilteringReturn(items=extracted_items, total=total)

    def get_distinct_headers(
        self,
        field_name: str,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
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
        )

        # Build alias_clause
        alias_clause = self.generic_alias_clause

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
            format_filter_sort_keys=format_term_filter_sort_keys,
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

    def _retrieve_term_from_cypher_res(
        self, result_array, attribute_names
    ) -> list[_AggregateRootType]:
        """
        Method maps the result of the cypher query into real aggregate objects.
        :param result_array:
        :param attribute_names:
        :return list[_AggregateRootType]:
        """
        terms_ars = []
        for term in result_array:
            term_dictionary = {}
            for term_property, attribute_name in zip(term, attribute_names):
                term_dictionary[attribute_name] = term_property
            terms_ars.append(
                self._create_aggregate_root_instance_from_cypher_result(term_dictionary)
            )

        return terms_ars

    def get_syntax_template_type(
        self, syntax_node: SyntaxTemplateRoot
    ) -> _AggregateRootType:
        """
        This method returns the template type for the provided syntax.

        :param syntax_node: Syntax Root node
        :return _AggregateRootType:
        """
        type_node = syntax_node.has_type.get_or_none()
        if type_node:
            type_node = type_node.has_selected_term.get_or_none()

        return self.find_by_uid(term_uid=type_node.uid)

    def hashkey_ct_term(
        self,
        term_uid: str,
        version: str | None = None,
        status: LibraryItemStatus | None = None,
        at_specific_date: datetime | None = None,
        for_update: bool = False,
        codelist_name: str | None = None,
        include_retired_versions: bool = False,
    ):
        """
        Returns a hash key that will be used for mapping objects stored in cache,
        which ultimately determines whether a method invocation is a hit or miss.

        We need to define this custom hashing function with the same signature as the method we wish to cache (find_by_uid),
        since the target method contains optional/default parameters.
        If this custom hashkey function is not defined, most invocations of find_by_uid method will be misses.
        """
        return hashkey(
            str(type(self)),
            term_uid,
            version,
            status,
            at_specific_date,
            for_update,
            codelist_name,
            include_retired_versions,
        )

    # Bypass the cache on for_update=True so the inner find_by_uid_2 /
    # find_by_uid_optimized calls (which also bypass their caches for
    # for_update=True) actually run and take the Neo4j write lock on this
    # term in the current transaction.
    @cached_skip_on(
        "for_update",
        cache=LibraryItemRepositoryImplBase.cache_store_item_by_uid,
        key=hashkey_ct_term,
        lock=LibraryItemRepositoryImplBase.lock_store_item_by_uid,
    )
    def find_by_uid(
        self,
        term_uid: str,
        version: str | None = None,
        status: LibraryItemStatus | None = None,
        at_specific_date: datetime | None = None,
        for_update: bool = False,
        codelist_name: str | None = None,
        include_retired_versions: bool = False,
    ) -> _AggregateRootType | None:
        ct_term_root: CTTermRoot
        if not codelist_name:
            ct_term_root = CTTermRoot.nodes.get_or_none(uid=term_uid)
        else:
            ct_term_root = CTTermRoot.nodes.filter(
                has_term_root__has_term__has_name_root__has_latest_value__name=codelist_name,
            ).get_or_none(uid=term_uid)[0]
        if ct_term_root is None:
            return None
        # pylint: disable=unnecessary-dunder-call
        ct_term_version_root_node = ct_term_root.__getattribute__(
            self.relationship_from_root
        ).single()
        if issubclass(ct_term_version_root_node.__class__, CTTermNameRoot):
            term_ar = self.find_by_uid_optimized(  # type: ignore[call-overload]
                ct_term_version_root_node.element_id,
                version=version,
                status=status,
                for_update=for_update,
                at_specific_date=at_specific_date,
                include_retired_versions=include_retired_versions,
            )
        else:
            term_ar = self.find_by_uid_2(
                str(ct_term_version_root_node.element_id),
                version=version,
                status=status,
                at_specific_date=at_specific_date,
                for_update=for_update,
            )

        return term_ar

    def find_by_uids(
        self,
        term_uids: list[str],
        status: LibraryItemStatus | None = None,
        at_specific_date: datetime | None = None,
        include_retired_versions: bool = False,
    ) -> list[_AggregateRootType] | None:
        if not term_uids:
            return []
        params = {"term_uids": term_uids}
        cypher_query = """
            MATCH (n:CTTermRoot)
            WHERE n.uid in $term_uids
            MATCH (n)--(ctnr:CTTermNameRoot)
            RETURN COLLECT( DISTINCT elementID(ctnr)) as ctterm_name_element_ids
        """
        ctterm_name_element_ids = db.cypher_query(cypher_query, params=params)[0][0][0]

        # !TODO rename parameter uid to element_ids to be consistent
        element_id_filter = {"uid": {"v": ctterm_name_element_ids, "op": "eq"}}
        term_ars, _ = self.get_all_optimized(
            status=status,
            at_specific_date=at_specific_date,
            filter_by=element_id_filter,
            filter_operator=FilterOperator.OR,
            include_retired_versions=include_retired_versions,
        )

        return term_ars

    def get_all_versions(self, term_uid: str) -> list[_AggregateRootType] | None:
        ct_term_root: CTTermRoot = CTTermRoot.nodes.get_or_none(uid=term_uid)
        if ct_term_root is not None:
            # pylint: disable=unnecessary-dunder-call
            ct_term_ver_root_node = ct_term_root.__getattribute__(
                self.relationship_from_root
            ).single()
            versions = self.get_all_versions_2(str(ct_term_ver_root_node.element_id))
            return versions
        return None

    @sb_clear_cache(
        caches=["cache_store_item_by_uid", "cache_store_term_by_uid_and_submval"]
    )
    def save(self, item: _AggregateRootType) -> None:
        if item.uid is not None and item.repository_closure_data is None:
            self._create(item)
        elif item.uid is not None and not item.is_deleted:
            self._update(item)
        elif item.is_deleted:
            assert item.uid is not None
            self._soft_delete(item.uid)

    def _is_repository_related_to_ct(self) -> bool:
        return True

    @sb_clear_cache(
        caches=["cache_store_item_by_uid", "cache_store_term_by_uid_and_submval"]
    )
    def add_parent(
        self, term_uid: str, parent_uid: str, relationship_type: TermParentType
    ) -> None:
        """
        Method adds term identified by parent_uid as a parent type to the term identified by the term_uid.
        Adding a parent type means creating a HAS_PARENT_TYPE or HAS_PARENT_SUB_TYPE
        relationship from CTTermRoot identified by the term_uid to the CTTermRoot identified by the parent_uid.
        :param term_uid:
        :param parent_uid:
        :param relationship_type:
        :return None:
        """
        ct_term_root_node = CTTermRoot.nodes.get_or_none(uid=term_uid)
        relationship_map = {
            TermParentType.PARENT_TYPE: ct_term_root_node.has_parent_type,
            TermParentType.PARENT_SUB_TYPE: ct_term_root_node.has_parent_subtype,
            TermParentType.SPECIALIZATION: ct_term_root_node.is_specialization_of,
            TermParentType.PREDECESSOR: ct_term_root_node.has_predecessor,
        }

        if relationship_type not in relationship_map:
            raise BusinessLogicException(
                msg=f"'{relationship_type.value}' isn't a valid relationship type."
            )

        relationship = relationship_map[relationship_type]
        parent_node = relationship.get_or_none()

        if (
            parent_node is not None
            and relationship_type != TermParentType.SPECIALIZATION
        ):
            raise AlreadyExistsException(
                msg=f"Term with UID '{term_uid}' already has a "
                f"parent type node with UID '{parent_node.uid}' "
                f"with the relationship of type '{relationship_type.value}'"
            )

        ct_term_root_parent_node = CTTermRoot.nodes.get_or_none(uid=parent_uid)
        relationship.connect(ct_term_root_parent_node)

    @sb_clear_cache(
        caches=["cache_store_item_by_uid", "cache_store_term_by_uid_and_submval"]
    )
    def remove_parent(
        self, term_uid: str, parent_uid: str, relationship_type: TermParentType
    ) -> None:
        """
        Method removes term parent type from the term identified by the term_uid.
        Removing a parent type means deleting a HAS_PARENT_TYPE or HAS_PARENT_SUB_TYPE
        relationship from CTTermRoot identified by the term_uid to the parent type CTTermRoot node.
        :param term_uid:
        :param parent_uid:
        :param relationship_type:
        :return None:
        """
        ct_term_root_node = CTTermRoot.nodes.get_or_none(uid=term_uid)
        relationship_map = {
            TermParentType.PARENT_TYPE: ct_term_root_node.has_parent_type,
            TermParentType.PREDECESSOR: ct_term_root_node.has_predecessor,
            TermParentType.PARENT_SUB_TYPE: ct_term_root_node.has_parent_subtype,
            TermParentType.SPECIALIZATION: ct_term_root_node.is_specialization_of,
        }

        if relationship_type not in relationship_map:
            raise BusinessLogicException(
                msg=f"'{relationship_type.value}' isn't a valid relationship type."
            )

        relationship = relationship_map[relationship_type]
        parent_node = relationship.get_or_none()
        NotFoundException.raise_if(
            parent_node is None,
            msg=f"Term with UID '{term_uid}' has no defined parent type node"
            f" with UID '{parent_uid}' with the relationship of type '{relationship_type.value}'",
        )
        relationship.disconnect(parent_node)

    @abstractmethod
    def is_repository_related_to_attributes(self) -> bool:
        """
        The method created to allow CTTermGenericRepository interface to handle filtering by package
        in different way for CTTermAttributesRepository and for CTTermNameRepository.
        :return:
        """
        raise NotImplementedError

    def find_uid_by_name(self, name: str) -> str | None:
        return self.find_uid_by_field(value=name, field="name")

    def find_uid_by_field(
        self, value: str, field: str = "name", codelist_uid: str | None = None
    ) -> str | None:
        params = {"field": value}

        if not codelist_uid:
            cypher_query = "MATCH"
        else:
            cypher_query = "MATCH (ct_codelist_root:CTCodelistRoot {uid: $codelist_uid})-[:HAS_TERM]->"
            params["codelist_uid"] = codelist_uid

        cypher_query += f"""
            (term_root:CTTermRoot)-[:{cast(str, self.relationship_from_root).upper()}]->(:{self.root_class.__label__})-
            [:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(:{self.value_class.__label__} {{{field}: $field}})
            RETURN term_root.uid
        """
        items, _ = db.cypher_query(cypher_query, params)
        if len(items) > 0:
            return items[0][0]
        return None

    def find_uid_by_submission_value(self, value: str, codelist_uid: str) -> str | None:
        params = {"submval": value, "codelist_uid": codelist_uid}

        cypher_query = """
            MATCH (ct_codelist_root:CTCodelistRoot {uid: $codelist_uid})-[ht:HAS_TERM]->(:CTCodelistTerm {submission_value: $submval})-[:HAS_TERM_ROOT]->(term_root:CTTermRoot)
            WHERE ht.end_date IS NULL
            RETURN term_root.uid
        """
        items, _ = db.cypher_query(cypher_query, params)
        if len(items) > 0:
            return items[0][0]
        return None

    def find_uid_by_submission_values(
        self, term_submval: str, codelist_submval: str
    ) -> str | None:
        params = {"term_submval": term_submval, "codelist_submval": codelist_submval}

        cypher_query = """
            MATCH (ct_codelist_root:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(:CTCodelistAttributesValue {submission_value: $codelist_submval})
            MATCH (ct_codelist_root)-[ht:HAS_TERM]->(:CTCodelistTerm {submission_value: $term_submval})-[:HAS_TERM_ROOT]->(term_root:CTTermRoot)
            WHERE ht.end_date IS NULL
            RETURN term_root.uid
        """
        items, _ = db.cypher_query(cypher_query, params)
        if len(items) > 0:
            return items[0][0]
        return None

    @classmethod
    def get_catalogue_names_for_term_codelists(cls, term_uid: str) -> list[str]:
        """
        Returns distinct catalogue names for all codelists a term currently belongs to.
        :param term_uid: The UID of the term
        :return: List of catalogue names
        """
        cypher_query = """
            MATCH (cat:CTCatalogue)-[:HAS_CODELIST]->(codelist:CTCodelistRoot)-[ht:HAS_TERM WHERE ht.end_date IS NULL]->
                (:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term:CTTermRoot {uid: $term_uid})
            RETURN collect(distinct cat.name) as catalogue_names
        """
        items, _ = db.cypher_query(cypher_query, {"term_uid": term_uid})
        if items and items[0]:
            return items[0][0]
        return []

    @classmethod
    def get_submission_values_for_term(cls, term_uid: str) -> list[str]:
        """
        Returns all existing submission values for a given term.
        Returns empty list if term is not found.
        :param term_uid: The UID of the term
        :return: List of submission values
        """
        cypher_query = """
            MATCH (term_root:CTTermRoot{uid: $term_uid})<-[:HAS_TERM_ROOT]-(codelist_term:CTCodelistTerm)
            RETURN collect(distinct codelist_term.submission_value) as submission_values
        """
        items, _ = db.cypher_query(cypher_query, {"term_uid": term_uid})
        if len(items) > 0 and len(items[0]) > 0:
            return items[0][0]
        return []

    def get_library_name_for_term(self, term_uid: str) -> str | None:
        """
        Returns the library name for a given term.
        :param term_uid: The UID of the term
        :return: Library name or None
        """
        term_root = CTTermRoot.nodes.get_or_none(uid=term_uid)
        if not term_root:
            return None

        library = term_root.has_library.get_or_none()
        if library:
            return library.name
        return None

    def is_library_editable_for_term(self, term_uid: str) -> bool | None:
        """
        Returns whether the library for a given term is editable.
        :param term_uid: The UID of the term
        :return: True if editable, False if not, None if term not found
        """
        term_root = CTTermRoot.nodes.get_or_none(uid=term_uid)
        if not term_root:
            return None

        library = term_root.has_library.get_or_none()
        if library:
            return library.is_editable
        return None

    def _generate_generic_match_clause(
        self,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library_name: str | None = None,
        package: str | None = None,
        in_codelist: bool = False,
    ) -> tuple[str, dict[Any, Any]]:
        if package:
            if self.is_repository_related_to_attributes():
                match_clause = """
                MATCH (package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_TERM]->(:CTPackageTerm)-
                [:CONTAINS_ATTRIBUTES]->(term_ver_value:CTTermAttributesValue)<-[]-(term_ver_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(term_root:CTTermRoot)
                """
            else:
                match_clause = """
                MATCH (package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_TERM]->(:CTPackageTerm)-
                [:CONTAINS_ATTRIBUTES]->(term_attributes_value:CTTermAttributesValue)<-[]-(term_attributes_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                (term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_ver_root:CTTermNameRoot)-[:LATEST_FINAL]->(term_ver_value:CTTermNameValue)
                """
        else:
            match_clause = f"""
            MATCH (term_root:CTTermRoot)-[:{cast(str, self.relationship_from_root).upper()}]->(term_ver_root)-[:LATEST_FINAL]->(term_ver_value)
            """

        filter_query_parameters: dict[Any, Any] = {}
        if library_name or package:
            # Build specific filtering for package and library
            # This is separate from generic filtering as the list of filters is predefined
            # We can therefore do this filtering in an efficient way in the Cypher MATCH clause
            filter_statements, filter_query_parameters = create_term_filter_statement(
                library_name=library_name, package=package
            )
            match_clause += filter_statements

        if in_codelist or (not package and (codelist_uid or codelist_name)):
            # Only include terms that are curently in a codelist,
            # meaning they have at least one HAS_TERM relationship without and end date
            match_clause += " MATCH (codelist_root:CTCodelistRoot)-[rel_term:HAS_TERM WHERE rel_term.end_date IS NULL ]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root) "
        elif not package:
            # Include terms that are not in any codelist, meaning they have no HAS_TERM relationship or only HAS_TERM relationships with an end date.
            match_clause += " OPTIONAL MATCH (codelist_root:CTCodelistRoot)-[rel_term:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root) "
        else:
            # We are listing terms for a specific package, we need to include HAS_TERM relationships with an end date also.
            # If not, we would only get terms that are also in the latest version of the package,
            # not those that were in the past.
            match_clause += " MATCH (codelist_root:CTCodelistRoot)-[rel_term:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root) "

        if codelist_uid or codelist_name:
            # Build specific filtering for codelist
            # This is done separately from library and package as we first need to match codelist_root
            (
                codelist_filter_statements,
                codelist_filter_query_parameters,
            ) = create_term_filter_statement(
                codelist_uid=codelist_uid, codelist_name=codelist_name
            )
            match_clause += codelist_filter_statements
            filter_query_parameters.update(codelist_filter_query_parameters)

        return match_clause, filter_query_parameters

    @sb_clear_cache(
        caches=["cache_store_item_by_uid", "cache_store_term_by_uid_and_submval"]
    )
    def update_term_codelist(
        self,
        term_uid: str,
        codelist_uid: str,
        order: int,
        submission_value: str,
        author: str,
    ) -> None:
        """
        Method adds term identified by term_uid to the codelist identified by codelist_uid.
        Adding a term means creating a HAS_TERM relationship from CTCodelistRoot to CTCodelistTerm,
        and  HAS_TERM_ROOT from CTCodelistTerm to CTTermRoot.
        When codelist identified by codelist_uid is a TemplateParameter, then the added term
        will become TemplateParameter term, which means creating HAS_PARAMETER_TERM relationship from
        CTCodelistNameValue to the CTTermNameRoot and labeling CTTermNameRoot as TemplateParameterTermRoot
        and CTTermNameValue as TemplateParameterTermValue.
        :param codelist_uid:
        :param term_uid:
        :param author:
        :param order:
        :param submission_value:
        :return None:
        """

        # Note: the new HAS_TERM relationship's `ordinal` is carried over from the relationship
        # being ended, so that reordering/changing the submission value of a term never loses
        # the previously assigned ordinal value. `ordinal` is set via a separate SET clause
        # (rather than inside the MERGE's property map) because Neo4j disallows creating a
        # relationship with a null property value inside a MERGE pattern; SET handles null
        # correctly (it simply omits/removes the property).
        query = """
            MATCH (term_root:CTTermRoot {uid: $term_uid})<-[:HAS_TERM_ROOT]-(codeslist_term:CTCodelistTerm)<-[has_term:HAS_TERM]-
                (codelist_root:CTCodelistRoot {uid: $codelist_uid}) WHERE has_term.end_date IS NULL
            WITH term_root, codeslist_term, codelist_root, has_term
            MERGE (term_root)<-[:HAS_TERM_ROOT]-(new_codeslist_term:CTCodelistTerm {submission_value: $submission_value})
            SET has_term.end_date = datetime()
            MERGE (codelist_root)-[new_has_term:HAS_TERM {start_date: has_term.end_date, order: $order, author_id: $author_id}]->(new_codeslist_term)
            SET new_has_term.ordinal = has_term.ordinal
        """
        db.cypher_query(
            query,
            {
                "codelist_uid": codelist_uid,
                "term_uid": term_uid,
                "submission_value": submission_value,
                "order": order,
                "author_id": author,
            },
        )
