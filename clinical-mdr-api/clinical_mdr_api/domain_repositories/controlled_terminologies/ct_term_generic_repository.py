from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Iterable, cast

from cachetools import cached
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
    sb_clear_cache,
    validate_filters_and_add_search_string,
)
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    NotFoundException,
)


class CTTermGenericRepository(LibraryItemRepositoryImplBase[_AggregateRootType], ABC):
    root_class = type
    value_class = type
    relationship_from_root = type

    generic_alias_clause = """
        DISTINCT term_root, term_ver_root, term_ver_value, codelist_root, rel_term
        ORDER BY rel_term.order, term_ver_value.name
        WITH DISTINCT codelist_root, rel_term, term_root, term_ver_root, term_ver_value,
        head([(catalogue)-[:HAS_CODELIST]->(codelist_root) | catalogue]) AS catalogue,
        head([(lib)-[:CONTAINS_TERM]->(term_root) | lib]) AS library
        MATCH (codelist_root)<-[:CONTAINS_CODELIST]-(codelist_library:Library)
        CALL {
                WITH term_ver_root, term_ver_value
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
            codelist_root.uid AS codelist_uid,
            codelist_library.name AS codelist_library_name,
            catalogue.name AS catalogue_name,
            term_ver_value AS value_node,
            rel_term.order AS order,
            library.name AS library_name,
            library.is_editable AS is_library_editable,
            {
                start_date: rel_data.start_date,
                end_date: NULL,
                status: rel_data.status,
                version: rel_data.version,
                change_description: rel_data.change_description,
                author_id: rel_data.author_id
            } AS rel_data
            CALL {
                WITH rel_data
                OPTIONAL MATCH (author: User)
                WHERE author.user_id = rel_data.author_id
                // RETURN author
                RETURN coalesce(author.username, rel_data.author_id) AS author_username 
            }
        WITH *             
        """

    def generate_uid(self) -> str:
        return CTTermRoot.get_next_free_uid_and_increment_counter()

    def term_specific_exists_by_uid(self, uid: str) -> bool:
        """
        Returns True or False depending on if there exists a term with a final version for a given uid
        :return:
        """
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

    @abstractmethod
    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ControlledTerminology,
        library: Library | None,
        relationship: VersionRelationship,
        value: ControlledTerminology,
        **_kwargs,
    ) -> _AggregateRootType:
        raise NotImplementedError

    @abstractmethod
    def _create_aggregate_root_instance_from_cypher_result(
        self, term_dict: dict
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
            MATCH (codelist:CTCodelistRoot)-[:HAS_TERM]->(term_root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(term_attr_root:CTTermAttributesRoot)-[:LATEST]->(term_attr_value:CTTermAttributesValue)
            MATCH (term_root)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue)
            WHERE codelist.uid in $codelist_uids
            RETURN term_name_value.name as name, term_root.uid as term_uid, codelist.uid as codelist_uid, term_attr_value.code_submission_value as code_submission_value, term_attr_value.preferred_term as nci_preferred_name
            """

        items, prop_names = db.cypher_query(query, {"codelist_uids": codelist_uids})

        return items, prop_names

    def get_term_attributes_by_term_uids(self, term_uids: list[Any]):
        query = """
            MATCH (term_root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(term_attr_root:CTTermAttributesRoot)-[:LATEST]->(term_attr_value:CTTermAttributesValue)
            WHERE term_root.uid in $term_uids
            RETURN term_root.uid as term_uid, term_attr_value.code_submission_value as code_submission_value, term_attr_value.preferred_term as nci_preferred_name
            """

        items, prop_names = db.cypher_query(query, {"term_uids": term_uids})

        return items, prop_names

    def find_all(
        self,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library_name: str | None = None,
        package: str | None = None,
        in_codelist: bool = False,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
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
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            total_count=total_count,
            return_model=_return_model,
            format_filter_sort_keys=format_term_filter_sort_keys,
        )
        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()
        extracted_items = self._retrieve_term_from_cypher_res(
            result_array, attributes_names
        )

        total = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                total = count_result[0][0]

        return GenericFilteringReturn.create(items=extracted_items, total=total)

    def get_distinct_headers(
        self,
        field_name: str,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
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
            filter_by=FilterDict(elements=filter_by),
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
        result_array, _ = query.execute()

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    def _retrieve_term_from_cypher_res(
        self, result_array, attribute_names
    ) -> Iterable[_AggregateRootType]:
        """
        Method maps the result of the cypher query into real aggregate objects.
        :param result_array:
        :param attribute_names:
        :return Iterable[_AggregateRootType]:
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
        type_node = syntax_node.has_type.single()
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

    @cached(
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
        if not codelist_name:
            ct_term_root: CTTermRoot = CTTermRoot.nodes.get_or_none(uid=term_uid)
        else:
            ct_term_root: CTTermRoot = CTTermRoot.nodes.filter(
                has_term__has_name_root__has_latest_value__name=codelist_name,
            ).get_or_none(uid=term_uid)[0]
        if ct_term_root is None:
            return None
        # pylint: disable=unnecessary-dunder-call
        ct_term_version_root_node = ct_term_root.__getattribute__(
            self.relationship_from_root
        ).single()
        if issubclass(ct_term_version_root_node.__class__, CTTermNameRoot):
            term_ar = self.find_by_uid_optimized(
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
        term_uids: list,
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

    def get_all_versions(self, term_uid: str) -> Iterable[_AggregateRootType] | None:
        ct_term_root: CTTermRoot = CTTermRoot.nodes.get_or_none(uid=term_uid)
        if ct_term_root is not None:
            # pylint: disable=unnecessary-dunder-call
            ct_term_ver_root_node = ct_term_root.__getattribute__(
                self.relationship_from_root
            ).single()
            versions = self.get_all_versions_2(str(ct_term_ver_root_node.element_id))
            return versions
        return None

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
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

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
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

        if relationship_type == TermParentType.PARENT_TYPE:
            parent_node = ct_term_root_node.has_parent_type.get_or_none()
        else:
            parent_node = ct_term_root_node.has_parent_subtype.get_or_none()

        if parent_node is not None:
            raise AlreadyExistsException(
                msg=f"Term with UID '{term_uid}' already has a "
                f"parent type node with UID '{parent_node.uid}' "
                f"with the relationship of type '{relationship_type.value}'"
            )
        ct_term_root_parent_node = CTTermRoot.nodes.get_or_none(uid=parent_uid)

        if relationship_type == TermParentType.PARENT_TYPE:
            ct_term_root_node.has_parent_type.connect(ct_term_root_parent_node)
        else:
            ct_term_root_node.has_parent_subtype.connect(ct_term_root_parent_node)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
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

        if relationship_type == TermParentType.PARENT_TYPE:
            parent_node = ct_term_root_node.has_parent_type.get_or_none()
        else:
            parent_node = ct_term_root_node.has_parent_subtype.get_or_none()

        NotFoundException.raise_if(
            parent_node is None,
            msg=f"Term with UID '{term_uid}' has no defined parent type node"
            f" with UID '{parent_uid}' with the relationship of type '{relationship_type.value}'",
        )
        if relationship_type == TermParentType.PARENT_TYPE:
            ct_term_root_node.has_parent_type.disconnect(parent_node)
        else:
            ct_term_root_node.has_parent_subtype.disconnect(parent_node)

    @abstractmethod
    def is_repository_related_to_attributes(self) -> bool:
        """
        The method created to allow CTTermGenericRepository interface to handle filtering by package
        in different way for CTTermAttributesRepository and for CTTermNameRepository.
        :return:
        """
        raise NotImplementedError

    def find_uid_by_name(self, name: str) -> str | None:
        cypher_query = f"""
            MATCH (term_root:CTTermRoot)-[:{cast(str, self.relationship_from_root).upper()}]->(or:{self.root_class.__label__})-
            [:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(ov:{self.value_class.__label__} {{name: $name}})
            RETURN term_root.uid
        """
        items, _ = db.cypher_query(cypher_query, {"name": name})
        if len(items) > 0:
            return items[0][0]
        return None

    def _generate_generic_match_clause(
        self,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library_name: str | None = None,
        package: str | None = None,
        in_codelist: bool = False,
    ) -> tuple[str, dict]:
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

        filter_query_parameters = {}
        if library_name or package:
            # Build specific filtering for package and library
            # This is separate from generic filtering as the list of filters is predefined
            # We can therefore do this filtering in an efficient way in the Cypher MATCH clause
            filter_statements, filter_query_parameters = create_term_filter_statement(
                library_name=library_name, package=package
            )
            match_clause += filter_statements

        if in_codelist or (not package and (codelist_uid or codelist_name)):
            match_clause += " MATCH (codelist_root:CTCodelistRoot)-[rel_term:HAS_TERM]->(term_root) "
        elif not package:
            match_clause += " OPTIONAL MATCH (codelist_root:CTCodelistRoot)-[rel_term:HAS_TERM]->(term_root) "
        else:
            # We are listing terms for a specific package, we need to include HAD_TERM relationships also.
            # If not, we would only get terms that are also in the latest version of the package,
            # not those that were in the past.
            match_clause += " MATCH (codelist_root:CTCodelistRoot)-[rel_term:HAS_TERM|HAD_TERM]->(term_root) "

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
