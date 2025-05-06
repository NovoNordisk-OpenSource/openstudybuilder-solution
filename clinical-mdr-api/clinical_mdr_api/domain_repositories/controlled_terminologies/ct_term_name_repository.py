from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_get_all_query_utils import (
    create_simple_term_instances_from_cypher_result,
    create_term_name_aggregate_instances_from_cypher_result,
    format_term_filter_sort_keys,
    list_term_wildcard_properties,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_aggregated_repository import (
    CTTermAggregatedRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_generic_repository import (
    CTTermGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermNameRoot,
    CTTermNameValue,
    CTTermRoot,
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
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermCodelistVO,
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
)


class CTTermNameRepository(
    CTTermGenericRepository[CTTermNameAR], CTTermAggregatedRepository
):
    root_class = CTTermNameRoot
    value_class = CTTermNameValue
    relationship_from_root = "has_name_root"

    def _create_simple_term_instances_from_cypher_result(
        self,
        term_dict: dict,
    ) -> tuple[SimpleTermModel]:
        """
        Method creates a tuple of CTTermNameAR and CTTermAttributesAR objects for one CTTermRoot node.
        The term_dict is a find_all_aggregated_result method result for one CTTermRoot node.

        :param term_dict:
        :return (CTTermNameAR, CTTermAttributesAR):
        """

        return create_simple_term_instances_from_cypher_result(term_dict=term_dict)

    def find_all_name_simple_result(
        self,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        is_sponsor: bool = False,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[SimpleTermModel]:
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
        match_clause, filter_query_parameters = (
            CTTermAggregatedRepository._generate_generic_match_clause(
                self,
                codelist_uid=codelist_uid,
                codelist_name=codelist_name,
                library_name=library,
                package=package,
                is_sponsor=is_sponsor,
            )
        )

        # Build alias_clause
        alias_clause = (
            self.sponsor_alias_clause
            if is_sponsor
            else CTTermAggregatedRepository.generic_alias_clause
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
                self._create_simple_term_instances_from_cypher_result(term_dictionary)
            )

        total = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                total = count_result[0][0]

        return GenericFilteringReturn.create(items=terms_ars, total=total)

    def term_specific_exists_by_name_in_codelists(
        self, term_name: str, codelist_uids: list[str]
    ) -> bool:
        """
        We allow duplicates in the following scenarios:
            - the conflicting term is retired
            - the conflicting term belongs to another codelist
        """
        query = """
            MATCH (term_ver_root:CTTermNameRoot)-[:LATEST]->(term_ver_value:CTTermNameValue {name: $term_name})
            OPTIONAL MATCH (term_ver_root)-[retired:HAS_VERSION {status: 'Retired'}]-(term_ver_value)
            WITH * WHERE NOT (retired IS NOT NULL AND retired.end_date IS NULL)
            MATCH (codelist_root:CTCodelistRoot)-[:HAS_TERM]-(term_root:CTTermRoot)-[:HAS_NAME_ROOT]-(term_ver_root)
            WHERE codelist_root.uid IN $codelist_uids
            RETURN term_ver_value
            """
        result, _ = db.cypher_query(
            query, {"term_name": term_name, "codelist_uids": codelist_uids}
        )

        return len(result) > 0

    def _create_aggregate_root_instance_from_cypher_result(
        self, term_dict: dict
    ) -> CTTermNameAR:
        return create_term_name_aggregate_instances_from_cypher_result(
            term_dict=term_dict, is_aggregated_query=False
        )

    def _create_ar(
        self,
        root: CTTermNameRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: CTTermNameValue,
        study_count: int = 0,
        **_kwargs,
    ) -> CTTermNameAR:
        codelists: list[CTTermCodelistVO] = []

        for codelist_root in _kwargs["ctterm_names"]["codelists"]:
            codelists.append(
                CTTermCodelistVO(
                    codelist_uid=codelist_root["uid"],
                    order=codelist_root["order"],
                    library_name=codelist_root["codelist_library_name"],
                )
            )

        return CTTermNameAR.from_repository_values(
            uid=_kwargs["ctterm_names"]["ctterm_root_uid"],
            ct_term_name_vo=CTTermNameVO.from_repository_values(
                codelists=codelists,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                catalogue_name=_kwargs["ctterm_names"]["catalogue"],
                queried_effective_date=_kwargs["ctterm_names"][
                    "queried_effective_date"
                ],
                date_conflict=_kwargs["ctterm_names"]["date_conflict"],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: CTTermNameRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: CTTermNameValue,
        **_kwargs,
    ) -> CTTermNameAR:
        ct_term_root_node = root.has_root.single()
        ct_codelist_root_node = ct_term_root_node.has_term.single()
        if not ct_codelist_root_node:
            ct_codelist_root_node = ct_term_root_node.had_term.single()

        codelists: list[CTTermCodelistVO] = []

        for codelist_root in ct_term_root_node.has_term.all():
            codelists.append(
                CTTermCodelistVO(
                    codelist_uid=codelist_root.uid,
                    order=codelist_root.has_term.relationship(ct_term_root_node).order,
                    library_name=codelist_root.has_library.single().name,
                )
            )

        return CTTermNameAR.from_repository_values(
            uid=ct_term_root_node.uid,
            ct_term_name_vo=CTTermNameVO.from_repository_values(
                codelists=codelists,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                catalogue_name=ct_codelist_root_node.has_codelist.single().name,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _is_new_version_necessary(self, ar: CTTermNameAR, value: VersionValue) -> bool:
        return self._has_data_changed(ar, value)

    def _get_or_create_value(
        self, root: CTTermNameRoot, ar: CTTermNameAR
    ) -> CTTermNameValue:
        for itm in root.has_version.filter(
            name=ar.ct_term_vo.name, name_sentence_case=ar.ct_term_vo.name_sentence_case
        ):
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
        new_value = self.value_class(
            name=ar.ct_term_vo.name, name_sentence_case=ar.ct_term_vo.name_sentence_case
        )
        self._db_save_node(new_value)
        return new_value

    def _has_data_changed(self, ar: CTTermNameAR, value: VersionValue):
        return (
            ar.ct_term_vo.name != value.name
            or ar.ct_term_vo.name_sentence_case != value.name_sentence_case
        )

    def _create(self, item: CTTermNameAR) -> CTTermNameAR:
        """
        Creates new CTTermNameAR, checks possibility based on library setting, then creates database representation,
        Creates CTTermNameRoot and CTTermNameValue database objects,
        recreates AR based on created database model and returns created AR.
        Saving into database is necessary due to uid creation process that require saving object to database.
        """
        relation_data: LibraryItemMetadataVO = item.item_metadata
        root = self.root_class()
        value = self.value_class(
            name=item.ct_term_vo.name,
            name_sentence_case=item.ct_term_vo.name_sentence_case,
        )
        self._db_save_node(root)

        (
            root,
            value,
            _,
            _,
            _,
        ) = self._db_create_and_link_nodes(
            root, value, self._library_item_metadata_vo_to_datadict(relation_data)
        )

        ct_term_root_node = CTTermRoot.nodes.get_or_none(uid=item.uid)
        ct_term_root_node.has_name_root.connect(root)
        self._maintain_parameters(item, root, value)

        return item

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        """
        Method maintains TemplateParameterTermRoot and TemplateParameterTermValue labels when saving CTTermNameAR.
        :param versioned_object:
        :param root:
        :param value:
        :return None:
        """

        maintain_order_query = """
            MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})-[has_term:HAS_TERM]->
                (term_root:CTTermRoot {uid:$term_uid})
            CALL apoc.do.case([

                // CTTermRoot was just created and order is not set yet  
                has_term.order IS NULL,
                'SET has_term.order = $order',

                // order was changed, HAS_TERM relationship has to be updated
                has_term.order <> $order,
                'CREATE (codelist_root)-[had_term:HAD_TERM]->(term_root)
                SET had_term.start_date=has_term.start_date
                SET had_term.end_date=datetime()
                SET had_term.author_id=$author_id
                SET had_term.order=has_term.order
                DELETE has_term
                CREATE (codelist_root)-[new_has_term:HAS_TERM]->(term_root)
                SET new_has_term.start_date=datetime()
                SET new_has_term.end_date=NULL
                SET new_has_term.author_id=$author_id
                SET new_has_term.order=$order'
            ], 
            '',
            {
                has_term: has_term, 
                order: $order,
                codelist_root: codelist_root,
                term_root: term_root,
                author_id: $author_id
            })
            YIELD value
            RETURN value            
        """

        maintain_template_parameter_query = """
            MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})-[:HAS_NAME_ROOT]->()-[:LATEST]->
                (codelist_ver_value:TemplateParameter)
            WITH codelist_root, codelist_ver_value
            MATCH (term_root:CTTermRoot {uid: $term_uid})-[:HAS_NAME_ROOT]->(term_ver_root)-[:LATEST]->(term_ver_value)
            MERGE (codelist_ver_value)-[hpt:HAS_PARAMETER_TERM]->(term_ver_root)
            SET term_ver_root:TemplateParameterTermRoot
            SET term_ver_value:TemplateParameterTermValue
        """

        if len(versioned_object.ct_term_vo.codelists) > 0:
            db.cypher_query(
                maintain_order_query,
                {
                    "codelist_uid": versioned_object.ct_term_vo.codelists[
                        0
                    ].codelist_uid,
                    "term_uid": versioned_object.uid,
                    "order": versioned_object.ct_term_vo.codelists[0].order,
                    "author_id": versioned_object.item_metadata.author_id,
                },
            )
            db.cypher_query(
                maintain_template_parameter_query,
                {
                    "codelist_uid": versioned_object.ct_term_vo.codelists[
                        0
                    ].codelist_uid,
                    "term_uid": versioned_object.uid,
                },
            )
        TemplateParameterTermRoot.generate_node_uids_if_not_present()

    def is_repository_related_to_attributes(self) -> bool:
        """
        The method created to allow CTTermGenericRepository interface to handle filtering by package
        in different way for CTTermAttributesRepository and for CTTermNameRepository.
        :return:
        """
        return False
