from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_get_all_query_utils import (
    create_term_name_aggregate_instances_from_cypher_result,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_aggregated_repository import (
    CTTermAggregatedRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_generic_repository import (
    CTTermGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
    CTTermNameRoot,
    CTTermNameValue,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.dictionary import (
    DictionaryCodelistRoot,
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
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.config import settings


class CTTermNameRepository(  # type: ignore[misc]
    CTTermGenericRepository[CTTermNameAR], CTTermAggregatedRepository
):
    root_class = CTTermNameRoot
    value_class = CTTermNameValue
    relationship_from_root = "has_name_root"

    # Per-call flag controlling whether TS-parameter graph traversals run
    # when materialising aggregates (set by find_all / find_by_uid /
    # get_all_versions before delegating to the base implementation).
    _include_ts_parameters: bool = True

    def find_all(self, *args, **kwargs):
        include_ts_parameters = kwargs.get("include_ts_parameters", True)
        self._include_ts_parameters = include_ts_parameters
        try:
            return super().find_all(*args, **kwargs)
        finally:
            self._include_ts_parameters = True

    def term_specific_exists_by_name_in_codelists(
        self, term_name: str, term_uid: str
    ) -> bool:
        """
        We allow duplicates in the following scenarios:
            - the conflicting term is retired
            - the conflicting term belongs to another codelist
        """
        query = """
            MATCH (term_root:CTTermRoot {uid: $term_uid})<-[:HAS_TERM_ROOT]-(:CTCodelistTerm)<-[ht:HAS_TERM WHERE ht.end_date IS NULL]-(clr:CTCodelistRoot)
            MATCH (clr)-[clht:HAS_TERM WHERE clht.end_date IS NULL]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(cttr:CTTermRoot WHERE cttr.uid <> $term_uid)-[:HAS_NAME_ROOT]->(cttnr:CTTermNameRoot)-[hnv:HAS_VERSION WHERE hnv.end_date IS NULL AND hnv.status <> "Retired"]->(cttnv:CTTermNameValue {name: $term_name})
            RETURN cttnv
            """
        result, _ = db.cypher_query(
            query, {"term_name": term_name, "term_uid": term_uid}
        )

        return len(result) > 0

    def _create_aggregate_root_instance_from_cypher_result(
        self, term_dict: dict[str, Any]
    ) -> CTTermNameAR:
        return create_term_name_aggregate_instances_from_cypher_result(
            term_dict=term_dict, is_aggregated_query=False
        )

    @staticmethod
    def _empty_ts_data() -> dict[str, Any]:
        return {
            "osb_field_name": None,
            "semantic_data_type_uid": None,
            "semantic_data_type_name": None,
            "response_codelist_uid": None,
            "response_codelist_name": None,
            "response_dictionary_uids": None,
            "valid_null_flavor_term_uids": None,
            "valid_null_flavor_term_names": None,
            "osb_page_reference": None,
        }

    @staticmethod
    def _ts_rel_data_from_value(
        value: CTTermNameValue,
        is_ts_term: bool | None = None,
    ) -> dict[str, Any]:
        """Load TS relationship targets from a CTTermNameValue node in a single Cypher query.

        The extra relationship traversals are only performed when the term belongs to one of
        the two TS parameter codelists (TSPARMCD / TSPARM), avoiding unnecessary graph hops
        for the vast majority of CT terms that are unrelated to TS parameters.

        When *is_ts_term* is supplied by the caller (who already has the codelist UID at hand),
        the `exists()` membership check inside the query is skipped entirely.
        """
        empty_ts_data = {
            "osb_field_name": None,
            "semantic_data_type_uid": None,
            "semantic_data_type_name": None,
            "response_codelist_uid": None,
            "response_codelist_name": None,
            "response_dictionary_uids": None,
            "valid_null_flavor_term_uids": None,
            "valid_null_flavor_term_names": None,
            "osb_page_reference": None,
        }

        if is_ts_term is False:
            return empty_ts_data

        if is_ts_term is True:
            # Caller already verified membership — run traversals directly, no exists() check.
            result, _ = db.cypher_query(
                """
                MATCH (ctnv:CTTermNameValue)
                WHERE elementId(ctnv) = $eid
                OPTIONAL MATCH (ctnv)-[:RELATED_STUDY_FIELD_SELECTION]->(msf:MetaStudyField)
                OPTIONAL MATCH (msf)-[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(dt_term:CTTermRoot)
                OPTIONAL MATCH (dt_term)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(dt_name:CTTermNameValue)
                OPTIONAL MATCH (ctnv)-[:RESPONSE_CODELIST]->(cl:CTCodelistRoot)
                OPTIONAL MATCH (cl)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST_FINAL]->(cl_name:CTCodelistNameValue)
                OPTIONAL MATCH (ctnv)-[:RESPONSE_DICTIONARY]->(dcr:DictionaryCodelistRoot)
                OPTIONAL MATCH (ctnv)-[:VALID_NULL_FLAVOR]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(nf_term:CTTermRoot)
                OPTIONAL MATCH (nf_term)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST_FINAL]->(nf_name:CTTermNameValue)
                RETURN
                    msf.osb_field_name              AS osb_field_name,
                    dt_term.uid                     AS semantic_data_type_uid,
                    dt_name.name                    AS semantic_data_type_name,
                    cl.uid                          AS response_codelist_uid,
                    cl_name.name                    AS response_codelist_name,
                    collect(DISTINCT dcr.uid)       AS response_dictionary_uids,
                    collect(DISTINCT nf_term.uid)   AS valid_null_flavor_term_uids,
                    collect(DISTINCT nf_name.name)  AS valid_null_flavor_term_names,
                    msf.osb_page_reference          AS osb_page_reference
                """,
                {"eid": value.element_id_property},
            )
        else:
            # Membership unknown — use exists() guard inside the query.
            result, _ = db.cypher_query(
                """
                MATCH (ctnv:CTTermNameValue)
                WHERE elementId(ctnv) = $eid
                WITH ctnv,
                     exists(
                         (ctnv)<-[:HAS_VERSION]-(:CTTermNameRoot)<-[:HAS_NAME_ROOT]-(:CTTermRoot)
                         <-[:HAS_TERM_ROOT]-(:CTCodelistTerm)<-[:HAS_TERM]-(:CTCodelistRoot {uid: $parmcd_uid})
                     ) OR exists(
                         (ctnv)<-[:HAS_VERSION]-(:CTTermNameRoot)<-[:HAS_NAME_ROOT]-(:CTTermRoot)
                         <-[:HAS_TERM_ROOT]-(:CTCodelistTerm)<-[:HAS_TERM]-(:CTCodelistRoot {uid: $parm_uid})
                     ) AS is_ts_term
                OPTIONAL MATCH (ctnv)-[:RELATED_STUDY_FIELD_SELECTION]->(msf:MetaStudyField) WHERE is_ts_term
                OPTIONAL MATCH (msf)-[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(dt_term:CTTermRoot) WHERE is_ts_term
                OPTIONAL MATCH (dt_term)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(dt_name:CTTermNameValue) WHERE is_ts_term
                OPTIONAL MATCH (ctnv)-[:RESPONSE_CODELIST]->(cl:CTCodelistRoot) WHERE is_ts_term
                OPTIONAL MATCH (cl)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST_FINAL]->(cl_name:CTCodelistNameValue) WHERE is_ts_term
                OPTIONAL MATCH (ctnv)-[:RESPONSE_DICTIONARY]->(dcr:DictionaryCodelistRoot) WHERE is_ts_term
                OPTIONAL MATCH (ctnv)-[:VALID_NULL_FLAVOR]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(nf_term:CTTermRoot) WHERE is_ts_term
                OPTIONAL MATCH (nf_term)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST_FINAL]->(nf_name:CTTermNameValue) WHERE is_ts_term
                RETURN
                    msf.osb_field_name              AS osb_field_name,
                    dt_term.uid                     AS semantic_data_type_uid,
                    dt_name.name                    AS semantic_data_type_name,
                    cl.uid                          AS response_codelist_uid,
                    cl_name.name                    AS response_codelist_name,
                    collect(DISTINCT dcr.uid)       AS response_dictionary_uids,
                    collect(DISTINCT nf_term.uid)   AS valid_null_flavor_term_uids,
                    collect(DISTINCT nf_name.name)  AS valid_null_flavor_term_names,
                    msf.osb_page_reference          AS osb_page_reference
                """,
                {
                    "eid": value.element_id_property,
                    "parmcd_uid": settings.ts_parmcd_codelist_uid,
                    "parm_uid": settings.ts_parm_codelist_uid,
                },
            )

        if not result:
            return empty_ts_data
        row = result[0]
        return {
            "osb_field_name": row[0],
            "semantic_data_type_uid": row[1],
            "semantic_data_type_name": row[2],
            "response_codelist_uid": row[3],
            "response_codelist_name": row[4],
            "response_dictionary_uids": tuple(row[5]) or None,
            "valid_null_flavor_term_uids": tuple(row[6]) or None,
            "valid_null_flavor_term_names": tuple(row[7]) or None,
            "osb_page_reference": row[8],
        }

    def _create_ar(
        self,
        root: CTTermNameRoot,
        library: Library,
        relationship: VersionRelationship,
        value: CTTermNameValue,
        study_count: int = 0,
        **_kwargs,
    ) -> CTTermNameAR:
        ct_term_root_node = root.has_root.single()
        ct_codelist_term = ct_term_root_node.has_term_root.single()
        ct_codelist_root_node = (
            ct_codelist_term.has_term.single() if ct_codelist_term else None
        )

        catalogue_names = (
            [cat.name for cat in ct_codelist_root_node.has_codelist.all()]
            if ct_codelist_root_node
            else []
        )

        return CTTermNameAR.from_repository_values(
            uid=_kwargs["ctterm_names"]["ctterm_root_uid"],
            ct_term_name_vo=CTTermNameVO.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                catalogue_names=catalogue_names,
                queried_effective_date=_kwargs["ctterm_names"][
                    "queried_effective_date"
                ],
                date_conflict=_kwargs["ctterm_names"]["date_conflict"],
                reference=value.reference,
                required_level=value.required_level,
                cardinality=value.cardinality,
                notes=value.notes,
                osb_field_name=_kwargs["ctterm_names"].get("osb_field_name"),
                osb_page_reference=_kwargs["ctterm_names"].get("osb_page_reference"),
                semantic_data_type_uid=_kwargs["ctterm_names"].get(
                    "semantic_data_type_uid"
                ),
                semantic_data_type_name=_kwargs["ctterm_names"].get(
                    "semantic_data_type_name"
                ),
                response_codelist_uid=_kwargs["ctterm_names"].get(
                    "response_codelist_uid"
                ),
                response_codelist_name=_kwargs["ctterm_names"].get(
                    "response_codelist_name"
                ),
                response_dictionary_uids=tuple(
                    u
                    for u in (
                        _kwargs["ctterm_names"].get("response_dictionary_uids") or []
                    )
                    if u
                )
                or None,
                valid_null_flavor_term_uids=tuple(
                    u
                    for u in (
                        _kwargs["ctterm_names"].get("valid_null_flavor_term_uids") or []
                    )
                    if u
                )
                or None,
                valid_null_flavor_term_names=tuple(
                    n
                    for n in (
                        _kwargs["ctterm_names"].get("valid_null_flavor_term_names")
                        or []
                    )
                    if n
                )
                or None,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: CTTermNameRoot,
        library: Library,
        relationship: VersionRelationship,
        value: CTTermNameValue,
        **_kwargs,
    ) -> CTTermNameAR:
        ct_term_root_node = root.has_root.single()

        # A CT term may belong to multiple codelists (one CTCodelistTerm node per
        # codelist). Using `.single()` here would arbitrarily pick one — and if a
        # TS-parameter term is also a member of another codelist, the picked one
        # may not be the TS codelist, causing `is_ts_term` to be wrongly False
        # and the TS-relationship fetch to be skipped (returning empty TS data
        # even though the graph relationships exist). Inspect all linked
        # codelists instead, mirroring the behaviour of the optimised find_all/
        # find_by_uid Cypher query.
        ct_codelist_root_nodes = [
            cl_root
            for ct_codelist_term in ct_term_root_node.has_term_root.all()
            for cl_root in ct_codelist_term.has_term.all()
        ]

        catalogue_names = list(
            {
                cat.name
                for cl_root in ct_codelist_root_nodes
                for cat in cl_root.has_codelist.all()
            }
        )

        ts_codelist_uids = (
            settings.ts_parmcd_codelist_uid,
            settings.ts_parm_codelist_uid,
        )
        is_ts_term = any(
            cl_root.uid in ts_codelist_uids for cl_root in ct_codelist_root_nodes
        )

        ts_data = (
            self._ts_rel_data_from_value(value, is_ts_term=is_ts_term)
            if self._include_ts_parameters
            else self._empty_ts_data()
        )

        return CTTermNameAR.from_repository_values(
            uid=ct_term_root_node.uid,
            ct_term_name_vo=CTTermNameVO.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                catalogue_names=catalogue_names,
                reference=value.reference,
                required_level=value.required_level,
                cardinality=value.cardinality,
                notes=value.notes,
                **ts_data,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _is_new_version_necessary(self, ar: CTTermNameAR, value: VersionValue) -> bool:
        return self._has_data_changed(ar, value)

    def _get_or_create_value(
        self, root: CTTermNameRoot, ar: CTTermNameAR, force_new_value_node: bool = False
    ) -> CTTermNameValue:
        if not force_new_value_node:
            for itm in root.has_version.filter(
                name=ar.ct_term_vo.name,
                name_sentence_case=ar.ct_term_vo.name_sentence_case,
                reference=ar.ct_term_vo.reference,
                required_level=ar.ct_term_vo.required_level,
                cardinality=ar.ct_term_vo.cardinality,
                notes=ar.ct_term_vo.notes,
            ):
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

        new_value = self.value_class(
            name=ar.ct_term_vo.name,
            name_sentence_case=ar.ct_term_vo.name_sentence_case,
            reference=ar.ct_term_vo.reference,
            required_level=ar.ct_term_vo.required_level,
            cardinality=ar.ct_term_vo.cardinality,
            notes=ar.ct_term_vo.notes,
        )
        self._db_save_node(new_value)
        return new_value

    def _has_data_changed(self, ar: CTTermNameAR, value: VersionValue):
        vo = ar.ct_term_vo
        if (
            vo.name != value.name
            or vo.name_sentence_case != value.name_sentence_case
            or vo.reference != value.reference
        ):
            return True
        if (
            vo.required_level != value.required_level
            or vo.cardinality != value.cardinality
            or vo.notes != value.notes
        ):
            return True

        # Compare relationship targets
        existing = self._ts_rel_data_from_value(value)
        if vo.osb_field_name != existing["osb_field_name"]:
            return True
        if vo.osb_page_reference != existing["osb_page_reference"]:
            return True
        if vo.semantic_data_type_uid != existing["semantic_data_type_uid"]:
            return True
        if vo.response_codelist_uid != existing["response_codelist_uid"]:
            return True
        if frozenset(vo.response_dictionary_uids or ()) != frozenset(
            existing["response_dictionary_uids"] or ()
        ):
            return True
        if frozenset(vo.valid_null_flavor_term_uids or ()) != frozenset(
            existing["valid_null_flavor_term_uids"] or ()
        ):
            return True
        return False

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
            reference=item.ct_term_vo.reference,
            required_level=item.ct_term_vo.required_level,
            cardinality=item.ct_term_vo.cardinality,
            notes=item.ct_term_vo.notes,
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
        Maintains TemplateParameterTermRoot/Value labels and wires TS relationships
        (RELATED_STUDY_FIELD_SELECTION, RESPONSE_CODELIST, RESPONSE_DICTIONARY,
        VALID_NULL_FLAVOR) whenever a CTTermNameAR is saved.
        """
        maintain_template_parameter_query = """
            MATCH (term_root:CTTermRoot {uid: $term_uid})-[:HAS_NAME_ROOT]->(term_ver_root)-[:LATEST]->(term_ver_value)
            MATCH (term_root)<-[:HAS_TERM_ROOT]-(codelist_term:CTCodelistTerm)<-[:HAS_TERM]-
              (codelist_root:CTCodelistRoot)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST]->(codelist_ver_value:TemplateParameter)
            MERGE (codelist_ver_value)-[hpt:HAS_PARAMETER_TERM]->(term_ver_root)
            SET term_ver_root:TemplateParameterTermRoot
            SET term_ver_value:TemplateParameterTermValue
        """
        db.cypher_query(
            maintain_template_parameter_query,
            {
                "term_uid": versioned_object.uid,
            },
        )
        TemplateParameterTermRoot.generate_node_uids_if_not_present()

        # Wire TS parameter relationships
        vo = versioned_object.ct_term_vo

        if not hasattr(vo, "osb_field_name") or vo.osb_field_name is None:
            return

        # If the value node already has a RELATED_STUDY_FIELD_SELECTION relationship,
        # it's a reused node (has_data_changed returned False) — all rels are already correct.
        # If it doesn't, it's a new node and we need to create all TS relationships.
        if value.related_study_field_selection.get_or_none() is not None:
            return

        # RELATED_STUDY_FIELD_SELECTION + HAS_SEMANTIC_DATA_TYPE on MetaStudyField.
        # MetaStudyField uniqueness key is (osb_field_name, semantic_data_type_uid):
        # multiple MSFs may share an `osb_field_name` provided each is connected
        # to a different semantic data type (or to none). `osb_page_reference` is
        # a property of the MetaStudyField, shared by all CT terms linked to it
        # via RELATED_STUDY_FIELD_SELECTION.
        if vo.semantic_data_type_uid:
            ct_codelist_repo = CTCodelistAttributesRepository()
            dt_term = CTTermRoot.nodes.get(uid=vo.semantic_data_type_uid)
            ctx_node = ct_codelist_repo.get_or_create_selected_term(
                dt_term,
                codelist_submission_value=settings.data_type_cl_submval,
                catalogue_name=settings.ddf_ct_catalogue_name,
            )
            # MERGE on the (MSF, HAS_SEMANTIC_DATA_TYPE, ctx) pattern so that an
            # MSF with the same osb_field_name but a different (or absent) SDT
            # is not reused.
            result_msf, _ = db.cypher_query(
                """
                MATCH (ctx:CTTermContext) WHERE elementId(ctx) = $ctx_eid
                OPTIONAL MATCH (existing:MetaStudyField {osb_field_name: $name})
                    -[:HAS_SEMANTIC_DATA_TYPE]->(ctx)
                FOREACH (_ IN CASE WHEN existing IS NULL THEN [1] ELSE [] END |
                    CREATE (:MetaStudyField {osb_field_name: $name})-[:HAS_SEMANTIC_DATA_TYPE]->(ctx)
                )
                WITH ctx, $name AS name, $page_ref AS page_ref
                MATCH (msf:MetaStudyField {osb_field_name: name})-[:HAS_SEMANTIC_DATA_TYPE]->(ctx)
                SET msf.osb_page_reference = page_ref
                RETURN msf
                """,
                {
                    "name": vo.osb_field_name,
                    "page_ref": vo.osb_page_reference,
                    "ctx_eid": ctx_node.element_id_property,
                },
                resolve_objects=True,
            )
            msf_node = result_msf[0][0]
        else:
            # No semantic data type — find or create an MSF with osb_field_name
            # that has no HAS_SEMANTIC_DATA_TYPE relationship.
            result_msf, _ = db.cypher_query(
                """
                OPTIONAL MATCH (existing:MetaStudyField {osb_field_name: $name})
                WHERE NOT (existing)-[:HAS_SEMANTIC_DATA_TYPE]->()
                FOREACH (_ IN CASE WHEN existing IS NULL THEN [1] ELSE [] END |
                    CREATE (:MetaStudyField {osb_field_name: $name})
                )
                WITH $name AS name
                MATCH (msf:MetaStudyField {osb_field_name: name})
                WHERE NOT (msf)-[:HAS_SEMANTIC_DATA_TYPE]->()
                SET msf.osb_page_reference = $page_ref
                RETURN msf
                """,
                {"name": vo.osb_field_name, "page_ref": vo.osb_page_reference},
                resolve_objects=True,
            )
            msf_node = result_msf[0][0]

        value.related_study_field_selection.connect(msf_node)

        # RESPONSE_CODELIST
        if vo.response_codelist_uid:
            cl_node = CTCodelistRoot.nodes.get(uid=vo.response_codelist_uid)
            value.response_codelist.connect(cl_node)

        # RESPONSE_DICTIONARY
        if vo.response_dictionary_uids:
            for d_uid in vo.response_dictionary_uids:
                dict_node = DictionaryCodelistRoot.nodes.get(uid=d_uid)
                value.response_dictionary.connect(dict_node)

        # VALID_NULL_FLAVOR
        if vo.valid_null_flavor_term_uids:
            ct_codelist_repo = CTCodelistAttributesRepository()
            for nf_uid in vo.valid_null_flavor_term_uids:
                nf_term = CTTermRoot.nodes.get(uid=nf_uid)
                ctx_node = ct_codelist_repo.get_or_create_selected_term(
                    nf_term,
                    codelist_submission_value=settings.null_flavor_cl_submval,
                    catalogue_name=settings.sdtm_ct_catalogue_name,
                )
                value.valid_null_flavor.connect(ctx_node)

    def is_repository_related_to_attributes(self) -> bool:
        """
        The method created to allow CTTermGenericRepository interface to handle filtering by package
        in different way for CTTermAttributesRepository and for CTTermNameRepository.
        :return:
        """
        return False
