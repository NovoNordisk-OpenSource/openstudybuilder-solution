from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Generic, Iterable, cast

from cachetools import cached
from cachetools.keys import hashkey
from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories._utils.helpers import is_codelist_in_final
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_get_all_query_utils import (
    create_codelist_filter_statement,
    format_codelist_filter_sort_keys,
)
from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CodelistTermRelationship,
    ControlledTerminology,
    CTCatalogue,
    CTCodelistRoot,
    CTCodelistTerm,
    CTTermContext,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameterTermRoot,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_term import (
    CTSimpleCodelistTermAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributes,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_name import (
    CTCodelistName,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    calculate_total_count_from_query_result,
    sb_clear_cache,
    validate_filters_and_add_search_string,
)
from common import exceptions


class CTCodelistGenericRepository(
    LibraryItemRepositoryImplBase, Generic[_AggregateRootType], ABC
):

    root_class = type
    value_class = type
    relationship_from_root: str
    generic_alias_clause = """
        DISTINCT codelist_root, codelist_ver_root, codelist_ver_value
        ORDER BY codelist_root.uid
        WITH DISTINCT codelist_root, codelist_ver_root, codelist_ver_value, 
        [(cat:CTCatalogue)-[:HAS_CODELIST]->(codelist_root) | cat.name] AS catalogue_names,
        head([(lib)-[:CONTAINS_CODELIST]->(codelist_root) | lib]) AS library
        CALL (codelist_ver_root, codelist_ver_value) {
                MATCH (codelist_ver_root)-[hv:HAS_VERSION]-(codelist_ver_value)
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
            codelist_root.uid AS codelist_uid,
            catalogue_names,
            head([(codelist_root)-[:HAS_PARENT_CODELIST]->(ccr:CTCodelistRoot) | ccr.uid]) AS parent_codelist_uid,
            [(codelist_root)<-[:HAS_PARENT_CODELIST]-(ccr:CTCodelistRoot) | ccr.uid] AS child_codelist_uids,
            codelist_ver_value AS value_node,
            CASE WHEN codelist_ver_value:TemplateParameter THEN true ELSE false END AS is_template_parameter,
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
            CALL (rel_data) {
                OPTIONAL MATCH (author: User)
                WHERE author.user_id = rel_data.author_id
                // RETURN author
                RETURN coalesce(author.username, rel_data.author_id) AS author_username 
            }
        WITH * 
    """

    def generate_uid(self) -> str:
        return CTCodelistRoot.get_next_free_uid_and_increment_counter()

    @classmethod
    def is_ct_node_a_tp(cls, ct_value_node) -> bool:
        labels = ct_value_node.labels()
        for label in labels:
            if "TemplateParameter" in label:
                return True
        return False

    @abstractmethod
    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ControlledTerminology,
        library: Library,
        relationship: VersionRelationship,
        value: ControlledTerminology,
    ) -> _AggregateRootType:
        raise NotImplementedError

    @abstractmethod
    def _create_aggregate_root_instance_from_cypher_result(
        self, codelist_dict: dict[str, Any]
    ) -> _AggregateRootType:
        """
        Creates aggregate root instances from cypher query result.
        :param codelist_dict:
        :return _AggregateRootType:
        """
        raise NotImplementedError

    @abstractmethod
    def is_repository_related_to_attributes(self) -> bool:
        raise NotImplementedError

    def find_uid_by_name(self, name: str) -> str | None:
        cypher_query = f"""
            MATCH (codelist_root:CTCodelistRoot)-[:{cast(str, self.relationship_from_root).upper()}]->(:{self.root_class.__label__})-
            [:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(:{self.value_class.__label__} {{name: $name}})
            RETURN codelist_root.uid
        """
        items, _ = db.cypher_query(cypher_query, {"name": name})
        if len(items) > 0:
            return items[0][0]
        return None

    def find_all(
        self,
        catalogue_name: str | None = None,
        library_name: str | None = None,
        package: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        **_kwargs,
    ) -> GenericFilteringReturn[_AggregateRootType]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Codelists aggregates.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param catalogue_name:
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
        exceptions.BusinessLogicException.raise_if(
            self.relationship_from_root not in vars(CTCodelistRoot),
            msg=f"The relationship of type '{self.relationship_from_root}' was not found in CTCodelistRoot object",
        )

        # Build match_clause
        # Build specific filtering for catalogue, package and library
        # This is separate from generic filtering as the list of filters is predefined
        # We can therefore do this filtering in an efficient way in the Cypher MATCH clause
        filter_statements, filter_query_parameters = create_codelist_filter_statement(
            catalogue_name=catalogue_name, library_name=library_name, package=package
        )
        match_clause = self._generate_generic_match_clause(package=package)
        match_clause += filter_statements

        # Build alias_clause
        alias_clause = self.generic_alias_clause

        _return_model = (
            CTCodelistAttributes
            if self.is_repository_related_to_attributes()
            else CTCodelistName
        )
        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
            return_model=_return_model,
            format_filter_sort_keys=format_codelist_filter_sort_keys,
        )
        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()
        extracted_items = self._retrieve_codelists_from_cypher_res(
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
        search_string: str = "",
        catalogue_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
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
            catalogue_name=catalogue_name, library_name=library, package=package
        )
        match_clause = self._generate_generic_match_clause(package=package)
        match_clause += filter_statements

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
        package: str | None = None,
    ):
        if package:
            if self.is_repository_related_to_attributes():
                match_clause = """
                MATCH (package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
                (codelist_ver_value:CTCodelistAttributesValue)<-[]-(codelist_ver_root:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                    (codelist_root:CTCodelistRoot)
                """
            else:
                match_clause = """
                MATCH (package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
                (codelist_attributes_value:CTCodelistAttributesValue)<-[]-(codelist_attributes_root:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                    (codelist_root:CTCodelistRoot)-[:HAS_NAME_ROOT]->(codelist_ver_root:CTCodelistNameRoot)-[:LATEST_FINAL]->(codelist_ver_value:CTCodelistNameValue)
                """
        else:
            match_clause = f"""
            MATCH (codelist_root:CTCodelistRoot)-[:{cast(str, self.relationship_from_root).upper()}]-(codelist_ver_root)-[:LATEST_FINAL]->(codelist_ver_value)
            """

        return match_clause

    def _retrieve_codelists_from_cypher_res(
        self, result_array, attribute_names
    ) -> list[_AggregateRootType]:
        """
        Method maps the result of the cypher query into real aggregate objects.
        :param result_array:
        :param attribute_names:
        :return Iterable[_AggregateRootType]:
        """
        codelist_ars = []
        for codelist in result_array:
            codelist_dictionary = {}
            for codelist_property, attribute_name in zip(codelist, attribute_names):
                codelist_dictionary[attribute_name] = codelist_property
            codelist_ars.append(
                self._create_aggregate_root_instance_from_cypher_result(
                    codelist_dictionary
                )
            )

        return codelist_ars

    def _lock_object2(self, codelist_uid: str) -> None:
        # Grab write lock on the codelist root, so that no terms can be added it to it while we update it.
        db.cypher_query(
            "MATCH (node:CTCodelistRoot) WHERE node.uid = $uid "
            "CALL apoc.lock.nodes([node])",
            {"uid": codelist_uid},
        )

    def find_by_uid(
        self,
        codelist_uid: str,
        version: str | None = None,
        status: LibraryItemStatus | None = None,
        at_specific_date: datetime | None = None,
        for_update: bool = False,
    ) -> _AggregateRootType | None:
        ct_codelist_root: CTCodelistRoot = CTCodelistRoot.nodes.get_or_none(
            uid=codelist_uid
        )
        if ct_codelist_root is None:
            return None

        if for_update:
            self._lock_object2(codelist_uid)

        # pylint: disable=unnecessary-dunder-call
        ct_codelist_name_root_node = ct_codelist_root.__getattribute__(
            self.relationship_from_root
        ).single()
        codelist_ar = self.find_by_uid_2(
            uid=str(ct_codelist_name_root_node.element_id),
            version=version,
            status=status,
            at_specific_date=at_specific_date,
            for_update=for_update,
        )

        return codelist_ar

    def get_all_versions(
        self, codelist_uid: str
    ) -> Iterable[_AggregateRootType] | None:
        ct_codelist_root: CTCodelistRoot = CTCodelistRoot.nodes.get_or_none(
            uid=codelist_uid
        )
        if ct_codelist_root is not None:
            # pylint: disable=unnecessary-dunder-call
            ct_codelist_name_root_node = ct_codelist_root.__getattribute__(
                self.relationship_from_root
            ).single()
            versions = self.get_all_versions_2(
                str(ct_codelist_name_root_node.element_id)
            )
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

    def codelist_exists(self, codelist_uid: str) -> bool:
        query = """
            MATCH (codelist_root:CTCodelistRoot {uid: $uid})-[:HAS_NAME_ROOT]->
            (codelist_ver_root:CTCodelistNameRoot)-[:LATEST]->(codelist_ver_value:CTCodelistNameValue)
            RETURN codelist_root
            """
        result, _ = db.cypher_query(query, {"uid": codelist_uid})
        if len(result) > 0 and len(result[0]) > 0:
            return True
        return False

    @sb_clear_cache(
        caches=["cache_store_item_by_uid", "cache_store_term_by_uid_and_submval"]
    )
    def add_term(
        self,
        codelist_uid: str,
        term_uid: str,
        author_id: str,
        order: int,
        submission_value: str,
        ordinal: float | None = None,
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
        :param author_id:
        :param order:
        :param submission_value:
        :return None:
        """
        ct_codelist_node = CTCodelistRoot.nodes.get_or_none(uid=codelist_uid)
        exceptions.ValidationException.raise_if(
            ct_codelist_node is None,
            msg=f"Codelist with UID '{codelist_uid}' doesn't exist.",
        )

        ct_term_node = CTTermRoot.nodes.get_or_none(uid=term_uid)
        exceptions.ValidationException.raise_if(
            ct_term_node is None, msg=f"Term with UID '{term_uid}' doesn't exist."
        )

        # Single Cypher query to check all duplicate conditions at once,
        # replacing the N+1 loop that made 3 DB calls per existing term.
        duplicate_check_query = """
            MATCH (new_term:CTTermRoot {uid: $term_uid})-[:HAS_NAME_ROOT]->()-[:LATEST]->(new_name_val)
            WITH new_term, new_name_val
            MATCH (codelist:CTCodelistRoot {uid: $codelist_uid})-[ht:HAS_TERM]->(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(existing_term:CTTermRoot)
            WHERE ht.end_date IS NULL
            MATCH (existing_term)-[:HAS_NAME_ROOT]->()-[:LATEST]->(existing_name_val)
            WITH new_term, new_name_val, clt, existing_term, existing_name_val,
                 CASE WHEN existing_term.uid = $term_uid THEN 'uid' ELSE NULL END AS uid_match,
                 CASE WHEN clt.submission_value = $submission_value THEN 'submission_value' ELSE NULL END AS sv_match,
                 CASE WHEN existing_name_val.name = new_name_val.name THEN 'name' ELSE NULL END AS name_match
            WHERE uid_match IS NOT NULL OR sv_match IS NOT NULL OR name_match IS NOT NULL
            RETURN
                coalesce(uid_match, sv_match, name_match) AS match_type,
                clt.submission_value AS existing_submission_value,
                existing_name_val.name AS existing_name
            LIMIT 1
        """
        results, _ = db.cypher_query(
            duplicate_check_query,
            {
                "codelist_uid": codelist_uid,
                "term_uid": term_uid,
                "submission_value": submission_value,
            },
        )
        if results:
            match_type, existing_sv, existing_name = results[0]
            if match_type == "uid":
                raise exceptions.AlreadyExistsException(
                    msg=f"Codelist with UID '{codelist_uid}' already has a Term with UID '{term_uid}'.",
                )
            if match_type == "submission_value":
                raise exceptions.AlreadyExistsException(
                    msg=f"Codelist with UID '{codelist_uid}' already has a Term with submission value '{existing_sv}'.",
                )
            if match_type == "name":
                raise exceptions.AlreadyExistsException(
                    msg=f"Codelist with UID '{codelist_uid}' already has a Term with name '{existing_name}'.",
                )

        ct_codelist_term_node = ct_term_node.has_term_root.get_or_none(
            submission_value=submission_value
        )
        if not ct_codelist_term_node:
            ct_codelist_term_node = CTCodelistTerm(
                submission_value=submission_value
            ).save()
            ct_term_node.has_term_root.connect(ct_codelist_term_node)

        ct_codelist_node.has_term.connect(
            ct_codelist_term_node,
            {
                "start_date": datetime.now(timezone.utc),
                "end_date": None,
                "author_id": author_id,
                "order": order,
                "ordinal": ordinal,
            },
        )

        # Validate that the term is added to a codelist that isn't in a draft state.
        exceptions.BusinessLogicException.raise_if_not(
            is_codelist_in_final(ct_codelist_node),
            msg=f"Term with UID '{term_uid}' cannot be added to Codelist with UID '{codelist_uid}' as the codelist is in a draft state.",
        )

        query = """
            MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})-[:HAS_NAME_ROOT]->()-[:LATEST]->
                (codelist_ver_value:TemplateParameter)
            WITH codelist_ver_value
            MATCH (term_root:CTTermRoot {uid: $term_uid})-[:HAS_NAME_ROOT]->(term_ver_root)-[:LATEST]->(term_ver_value)
            MERGE (codelist_ver_value)-[:HAS_PARAMETER_TERM]->(term_ver_root)
            SET term_ver_root:TemplateParameterTermRoot
            SET term_ver_value:TemplateParameterTermValue
        """
        db.cypher_query(query, {"codelist_uid": codelist_uid, "term_uid": term_uid})
        TemplateParameterTermRoot.generate_node_uids_if_not_present()

    @sb_clear_cache(
        caches=["cache_store_item_by_uid", "cache_store_term_by_uid_and_submval"]
    )
    def remove_term(self, codelist_uid: str, term_uid: str, author_id: str) -> None:
        """
        Method removes term identified by term_uid from the codelist identified by codelist_uid.
        Removing a term means deleting existing HAS_TERM relationship from CTCodelistRoot to CTTermRoot and
        creating HAD_TERM relationship from CTCodelistRoot to CTTermRoot.
        When term that is being removed is a TemplateParameter value, then also HAS_PARAMETER_TERM relationship from
        CTCodelistNameValue node to the CTTermNameRoot node is deleted. We leave the TemplateParameterTermRoot
        and template_parameter_term labels as other codelist may use that term as TemplateParameter value.
        :param codelist_uid:
        :param term_uid:
        :param author_id:
        :return None:
        """

        ct_codelist_node = CTCodelistRoot.nodes.get_or_none(uid=codelist_uid)
        exceptions.ValidationException.raise_if(
            ct_codelist_node is None,
            msg=f"Codelist with UID '{codelist_uid}' doesn't exist.",
        )

        # Acquire a lock first
        self._lock_object2(codelist_uid)

        ct_term_node = CTTermRoot.nodes.get_or_none(uid=term_uid)
        exceptions.ValidationException.raise_if(
            ct_term_node is None, msg=f"Term with UID '{term_uid}' doesn't exist."
        )

        for ct_codelist_term_node in ct_codelist_node.has_term.all():
            ct_term_end_node = ct_codelist_term_node.has_term_root.single()
            if ct_term_end_node.uid == term_uid:
                has_term_relationship: CodelistTermRelationship = (
                    ct_codelist_node.has_term.relationship(ct_codelist_term_node)
                )
                has_term_relationship.author_id = author_id
                has_term_relationship.end_date = datetime.now(timezone.utc)
                has_term_relationship.save()

                # Validate that the term is removed from a codelist that isn't in a draft state.
                exceptions.BusinessLogicException.raise_if_not(
                    is_codelist_in_final(ct_codelist_node),
                    msg=f"Term with UID '{term_uid}' cannot be removed from Codelist with UID '{codelist_uid}' as the codelist is in a draft state.",
                )

                query = """
                    MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})-[:HAS_NAME_ROOT]->()-[:LATEST]->
                        (codelist_ver_value:TemplateParameter)-[r:HAS_PARAMETER_TERM]-(term_ver_root)
                    DELETE r
                """
                db.cypher_query(query, {"codelist_uid": codelist_uid})
                break
        else:
            raise exceptions.NotFoundException(
                msg=f"Codelist with UID '{codelist_uid}' doesn't have a Term with UID '{term_uid}'."
            )

    def _is_repository_related_to_ct(self) -> bool:
        """
        The method created to allow CTCodelistGenericRepository interface to handle filtering by package
        in different way for CTCodelistAttributesRepository and for CTCodelistNameRepository.
        :return bool:
        """
        return True

    # Small helper method for finding a codelist uid by name
    def get_codelist_uid_by_name(self, name: str) -> str | None:
        query = """
            MATCH (codelist_root:CTCodelistRoot)-[:HAS_NAME_ROOT]->(codelist_ver_root:CTCodelistNameRoot)-[:LATEST_FINAL]->(codelist_ver_value:CTCodelistNameValue)
            WHERE codelist_ver_value.name = $name
            RETURN codelist_root.uid
        """
        result, _ = db.cypher_query(query, {"name": name})
        if len(result) > 0:
            return result[0][0]
        return None

    # Small helper method for finding a codelist uid by submission value
    def get_codelist_uid_by_submission_value(self, submval: str) -> str | None:
        query = """
            MATCH (codelist_root:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(codelist_ver_root:CTCodelistAttributesRoot)-[:LATEST_FINAL]->(codelist_ver_value:CTCodelistAttributesValue)
            WHERE codelist_ver_value.submission_value = $submval
            RETURN codelist_root.uid
        """
        result, _ = db.cypher_query(query, {"submval": submval})
        if len(result) > 0:
            return result[0][0]
        return None

    # Small helper to check if a term with a given uid exits in the codelist with a given uid
    def term_exists_in_codelist(
        self,
        codelist_uid: str,
        term_uid: str,
        at_specific_date=None,
        allow_removed_terms: bool = False,
    ) -> bool:
        if at_specific_date is not None:
            raise NotImplementedError(
                "This method does not yet support at_specific_date parameter"
            )
        if allow_removed_terms:
            end_date_clause = ""
        else:
            end_date_clause = "WHERE ht.end_date IS NULL"
        query = f"""
            MATCH (codelist_root:CTCodelistRoot {{uid: $codelist_uid}})-[ht:HAS_TERM]->(codelist_term:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root:CTTermRoot {{uid: $term_uid}})
            {end_date_clause}
            RETURN codelist_term
        """
        result, _ = db.cypher_query(
            query, {"codelist_uid": codelist_uid, "term_uid": term_uid}
        )
        if len(result) > 0:
            return True
        return False

    def hashkey_codelist_term(
        self,
        term_uid: str | None,
        codelist_submission_value: str | None,
        at_specific_date_time: datetime | None = None,
        is_date_conflict: bool = False,
    ):
        """
        Returns a hash key that will be used for mapping objects stored in cache,
        which ultimately determines whether a method invocation is a hit or miss.

        We need to define this custom hashing function with the same signature as the method we wish to cache (find_by_uid_2),
        since the target method contains optional/default parameters.
        If this custom hashkey function is not defined, most invocations of find_by_uid_2 method will be misses.
        """
        return hashkey(
            term_uid,
            codelist_submission_value,
            at_specific_date_time,
            is_date_conflict,
        )

    # Get the details of a term - codelist relationship
    @cached(
        cache=LibraryItemRepositoryImplBase.cache_store_term_by_uid_and_submval,
        key=hashkey_codelist_term,
        lock=LibraryItemRepositoryImplBase.lock_store_term_by_uid_and_submval,
    )
    def get_codelist_term_by_uid_and_submval(
        self,
        term_uid: str | None,
        codelist_submission_value: str | None,
        at_specific_date_time: datetime | None = None,
        is_date_conflict: bool = False,
    ) -> CTSimpleCodelistTermAR | None:
        if term_uid is None or codelist_submission_value is None:
            return None
        params: dict[str, Any]
        params = {"cl_submval": codelist_submission_value, "term_uid": term_uid}
        if not is_date_conflict and at_specific_date_time is not None:
            ht_date = """
                WHERE (ht.start_date <= datetime($at_specific_date) < datetime(ht.end_date))
                OR (ht.end_date IS NULL AND (ht.start_date <= datetime($at_specific_date)))
            """
            cl_attrs_date = """
                WHERE (cl_attrs_hv.start_date <= datetime($at_specific_date) < datetime(cl_attrs_hv.end_date))
                OR (cl_attrs_hv.end_date IS NULL AND (cl_attrs_hv.start_date <= datetime($at_specific_date)))
            """
            cl_name_date = """
                WHERE (cl_name_hv.start_date <= datetime($at_specific_date) < datetime(cl_name_hv.end_date))
                OR (cl_name_hv.end_date IS NULL AND (cl_name_hv.start_date <= datetime($at_specific_date)))
            """
            term_name_date = """
                WHERE (term_name_hv.start_date <= datetime($at_specific_date) < datetime(term_name_hv.end_date))
                OR (term_name_hv.end_date IS NULL AND (term_name_hv.start_date <= datetime($at_specific_date)))
            """
            version_rel_type = "HAS_VERSION"
            params["at_specific_date"] = at_specific_date_time
        else:
            ht_date = "WHERE ht.end_date IS NULL"
            cl_attrs_date = ""
            cl_name_date = ""
            term_name_date = ""
            version_rel_type = "LATEST_FINAL"

        query = f"""
            MATCH (codelist_root:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(codelist_attrs_root:CTCodelistAttributesRoot)-[cl_attrs_hv:{version_rel_type}]->
              (codelist_attrs_value:CTCodelistAttributesValue {{submission_value: $cl_submval}})
            {cl_attrs_date}
            MATCH (codelist_root)-[ht:HAS_TERM]->(codelist_term:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_root:CTTermRoot {{uid: $term_uid}})
            {ht_date}
            OPTIONAL MATCH (codelist_root)-[:HAS_NAME_ROOT]->(codelist_name_root:CTCodelistNameRoot)-[cl_name_hv:{version_rel_type}]->(codelist_name_value:CTCodelistNameValue)
            {cl_name_date}
            OPTIONAL MATCH (term_root)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[term_name_hv:{version_rel_type}]->(term_name_value:CTTermNameValue)
            {term_name_date}
            OPTIONAL MATCH (term_root)-[:HAS_ATTRIBUTES_ROOT]->(term_attributes_root:CTTermAttributesRoot)-[term_attributes_hv:{version_rel_type}]->
              (term_attributes_value:CTTermAttributesValue)
            RETURN
                term_root.uid AS term_uid,
                term_name_value.name AS term_name,
                term_attributes_value.preferred_term AS preferred_term,
                codelist_term.submission_value AS submission_value,
                ht.order AS order,
                codelist_name_value.name AS codelist_name,
                codelist_root.uid AS codelist_uid,
                $cl_submval AS codelist_submission_value
        """
        result_array, attribute_names = db.cypher_query(query, params)
        if len(result_array) > 0:
            data_dict = {
                attribute_name: result_array[0][index]
                for index, attribute_name in enumerate(attribute_names)
            }
            data_dict["date_conflict"] = is_date_conflict
            if data_dict["codelist_name"] is None:
                # fallback, query for the first codelist name version
                cl_name_query = """
                    MATCH (cl_root:CTCodelistRoot {uid: $cl_uid})-[:HAS_NAME_ROOT]->(cl_name_root:CTCodelistNameRoot)-[cl_name_hv:HAS_VERSION]->
                      (cl_name_value:CTCodelistNameValue)
                    WITH cl_name_value ORDER BY cl_name_hv.start_date ASC
                    RETURN cl_name_value.name AS cl_name LIMIT 1
                """
                result, _ = db.cypher_query(
                    cl_name_query,
                    {
                        "cl_uid": data_dict["codelist_uid"],
                    },
                )
                if len(result) > 0:
                    data_dict["codelist_name"] = result[0][0]
            if data_dict["term_name"] is None:
                # fallback, query for the first term name version
                term_name_query = """
                    MATCH (term_root:CTTermRoot {uid: $term_uid})-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[term_name_hv:HAS_VERSION]->
                      (term_name_value:CTTermNameValue)
                    WITH term_name_value ORDER BY term_name_hv.start_date ASC
                    RETURN term_name_value.name AS term_name LIMIT 1
                """
                result, _ = db.cypher_query(
                    term_name_query,
                    {
                        "term_uid": term_uid,
                    },
                )
                if len(result) > 0:
                    data_dict["term_name"] = result[0][0]
            return CTSimpleCodelistTermAR.from_result_dict(data_dict)
        if at_specific_date_time is not None:
            return self.get_codelist_term_by_uid_and_submval(
                term_uid,
                codelist_submission_value,
                at_specific_date_time=None,
                is_date_conflict=True,
            )
        return None

    @staticmethod
    def get_codelist_submval_by_uid(codelist_uid: str):
        query = """
            MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(codelist_attrs_value:CTCodelistAttributesValue)
            RETURN codelist_attrs_value.submission_value AS submission_value
        """
        rs = db.cypher_query(query, {"codelist_uid": codelist_uid})

        if rs[0]:
            return rs[0][0][0]

        return None

    def get_catalogue_names_for_codelist(self, codelist_uid: str) -> list[str]:
        """
        Returns all catalogue names for a given codelist.
        A codelist can belong to more than one catalogue.
        :param codelist_uid: The UID of the codelist
        :return: List of catalogue names (may be empty)
        """
        query = """
        MATCH (cat:CTCatalogue)-[:HAS_CODELIST]->(codelist:CTCodelistRoot {uid: $codelist_uid})
        RETURN collect(distinct cat.name) AS catalogue_names
        """
        results, _ = db.cypher_query(query, {"codelist_uid": codelist_uid})
        if results and results[0][0] is not None:
            return results[0][0]
        return []

    def get_paired_codelist_uid(self, codelist_uid: str) -> str | None:
        """
        Returns the paired codelist UID if the codelist is part of a codelist pair.
        Returns None if no pairing exists.
        :param codelist_uid: The UID of the codelist
        :return: Paired codelist UID or None
        """
        query = """
            MATCH (codelist:CTCodelistRoot {uid: $codelist_uid})
            OPTIONAL MATCH (codelist)-[:PAIRED_CODE_CODELIST]->(paired_code:CTCodelistRoot)
            OPTIONAL MATCH (codelist)<-[:PAIRED_CODE_CODELIST]-(paired_name:CTCodelistRoot)
            RETURN coalesce(paired_code.uid, paired_name.uid) AS paired_uid
        """
        results, _ = db.cypher_query(query, {"codelist_uid": codelist_uid})
        if results and results[0][0] is not None:
            return results[0][0]
        return None

    def is_term_in_codelist(self, term_uid: str, codelist_uid: str) -> bool:
        """
        Checks if a term is currently in a codelist (has an active HAS_TERM relationship).
        :param term_uid: The UID of the term
        :param codelist_uid: The UID of the codelist
        :return: True if the term is in the codelist, False otherwise
        """
        results = CTCodelistRoot.nodes.filter(
            uid=codelist_uid,
            has_term__has_term_root__uid=term_uid,
            **{"has_term|end_date__isnull": True},
        )[:1]
        return len(results) > 0

    def get_or_create_selected_term(
        self,
        term_node,
        codelist_submission_value: str | None = None,
        codelist_uid: str | None = None,
        catalogue_name: str | None = None,
        allow_removed_terms: bool = False,
    ):
        if codelist_uid is None and codelist_submission_value is None:
            raise ValueError(
                "Either codelist_uid or codelist_submission_value must be provided"
            )
        if codelist_submission_value is not None:
            codelist_uid = self.get_codelist_uid_by_submission_value(
                codelist_submission_value
            )
        if codelist_uid is None:
            raise exceptions.ValidationException(
                msg=f"The codelist identified by submission value {codelist_submission_value} was not found."
            )
        if catalogue_name is not None:
            sdtm_catalogue_node = CTCatalogue.nodes.get(name=catalogue_name)
        else:
            sdtm_catalogue_node = None
        cl_root_node = CTCodelistRoot.nodes.get(uid=codelist_uid)

        if cl_root_node is None:
            raise exceptions.ValidationException(
                msg=f"The codelist identified by uid {codelist_uid} was not found."
            )
        if not self.term_exists_in_codelist(
            codelist_uid, term_node.uid, allow_removed_terms=allow_removed_terms
        ):
            raise exceptions.ValidationException(
                msg=f"The term identified by uid {term_node.uid} was not found in the codelist identified by uid {codelist_uid}"
            )
        if (
            sdtm_catalogue_node is not None
            and not cl_root_node.has_codelist.is_connected(sdtm_catalogue_node)
        ):
            raise exceptions.ValidationException(
                msg=f"The codelist identified by {codelist_uid} is not connected to the catalogue identified by {catalogue_name}"
            )

        # check if a matching selected term already exists
        query = """
            MATCH (ct_codelist_root:CTCodelistRoot {uid: $ct_codelist_uid})<-[:HAS_SELECTED_CODELIST]-(ct_term_context:CTTermContext)
                -[:HAS_SELECTED_TERM]->(ct_term_root:CTTermRoot {uid: $ct_term_uid})
        """
        if sdtm_catalogue_node is not None:
            query += """
                MATCH (ct_codelist_root)<-[:HAS_CODELIST]-(:CTCatalogue {name: $sdtm_catalogue_name})
            """
        query += "RETURN DISTINCT ct_term_context"
        selected_term_nodes, _ = db.cypher_query(
            query,
            {
                "ct_codelist_uid": cl_root_node.uid,
                "ct_term_uid": term_node.uid,
                "sdtm_catalogue_name": (
                    sdtm_catalogue_node.name if sdtm_catalogue_node else None
                ),
            },
            resolve_objects=True,
        )
        if len(selected_term_nodes) and len(selected_term_nodes[0]) > 0:
            return selected_term_nodes[0][0]

        selected_term_node = CTTermContext()
        selected_term_node.save()
        selected_term_node.has_selected_term.connect(term_node)
        selected_term_node.has_selected_codelist.connect(cl_root_node)
        return selected_term_node
