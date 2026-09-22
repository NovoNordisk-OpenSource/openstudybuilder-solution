import logging
from textwrap import dedent
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmMethodRoot,
    OdmMethodValue,
)
from clinical_mdr_api.domain_repositories.odms.generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domains.odms.method import OdmMethodAR, OdmMethodVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmFormalExpressionModel,
    OdmTranslatedTextModel,
)
from clinical_mdr_api.models.odms.method import OdmMethod
from common.utils import convert_to_datetime

log = logging.getLogger(__name__)


class MethodRepository(OdmGenericRepository[OdmMethodAR]):
    root_class = OdmMethodRoot
    value_class = OdmMethodValue
    return_model = OdmMethod

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmMethodAR:
        log.debug("Creating OdmMethodAR from version root: uid=%s", root.uid)
        return OdmMethodAR.from_repository_values(
            uid=root.uid,
            odm_vo=OdmMethodVO.from_repository_values(
                oid=value.oid,
                name=value.name,
                method_type=value.method_type,
                formal_expressions=[
                    OdmFormalExpressionModel(
                        context=formal_expression_value.context,
                        expression=formal_expression_value.expression,
                    )
                    for formal_expression_value in value.has_formal_expression.all()
                ],
                translated_texts=[
                    OdmTranslatedTextModel(
                        text_type=translated_text_value.text_type,
                        language=translated_text_value.language,
                        text=translated_text_value.text,
                    )
                    for translated_text_value in value.has_translated_text.all()
                ],
                aliases=[
                    OdmAliasModel(name=alias_value.name, context=alias_value.context)
                    for alias_value in value.has_alias.all()
                ],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> OdmMethodAR:
        major, minor = input_dict["version"].split(".")
        log.debug(
            "Creating OdmMethodAR from cypher result: uid=%s, version=%s",
            input_dict["uid"],
            input_dict["version"],
        )
        odm_method_ar = OdmMethodAR.from_repository_values(
            uid=input_dict["uid"],
            odm_vo=OdmMethodVO.from_repository_values(
                oid=input_dict.get("oid"),
                name=input_dict["name"],
                method_type=input_dict.get("method_type"),
                formal_expressions=[
                    OdmFormalExpressionModel(
                        context=formal_expression["context"],
                        expression=formal_expression["expression"],
                    )
                    for formal_expression in input_dict["formal_expressions"]
                ],
                translated_texts=[
                    OdmTranslatedTextModel(
                        text_type=translated_text["text_type"],
                        language=translated_text["language"],
                        text=translated_text["text"],
                    )
                    for translated_text in input_dict["translated_texts"]
                ],
                aliases=[
                    OdmAliasModel(name=alias["name"], context=alias["context"])
                    for alias in input_dict["aliases"]
                ],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict["library_name"],
                is_library_editable_callback=(
                    lambda _: input_dict["is_library_editable"]
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict["change_description"],
                status=LibraryItemStatus(input_dict.get("status")),
                author_id=input_dict["author_id"],
                author_username=input_dict.get("author_username"),
                start_date=convert_to_datetime(value=input_dict["start_date"]),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

        return odm_method_ar

    def _get_specific_field_mapping(self) -> dict[str, str]:
        """Field mappings for method-specific fields."""
        return {
            "name": "odm_value.name AS name",
            "oid": "odm_value.oid AS oid",
            "method_type": "odm_value.method_type AS method_type",
        }

    def _get_computed_field_expressions(self) -> dict[str, str]:
        """Computed fields requiring complex Cypher expressions."""
        return {
            "formal_expressions": "[(odm_value)-[:HAS_FORMAL_EXPRESSION]->(fev:OdmFormalExpression) | {context: fev.context, expression: fev.expression}] AS formal_expressions",
            "translated_texts": "[(odm_value)-[:HAS_TRANSLATED_TEXT]->(dv:OdmTranslatedText) | {text_type: dv.text_type, language: dv.language, text: dv.text}] AS translated_texts",
            "aliases": "[(odm_value)-[:HAS_ALIAS]->(av:OdmAlias) | {name: av.name, context: av.context}] AS aliases",
        }

    def specific_alias_clause(self, **kwargs) -> str:
        return dedent(
            "WITH *,"
            + ", ".join(self._get_specific_field_mapping().values())
            + ","
            + ", ".join(self._get_computed_field_expressions().values())
        )

    def _get_or_create_value(
        self, root: VersionRoot, ar: OdmMethodAR, force_new_value_node: bool = False
    ) -> VersionValue:
        log.debug(
            "Getting or creating value for OdmMethod: uid=%s, force_new=%s",
            root.uid,
            force_new_value_node,
        )
        new_value = super()._get_or_create_value(root, ar, force_new_value_node)

        self.connect_aliases(ar.odm_vo.aliases, new_value)
        self.connect_translated_texts(ar.odm_vo.translated_texts, new_value)
        self.connect_formal_expressions(ar.odm_vo.formal_expressions, new_value)

        return new_value

    def _create_new_value_node(self, ar: OdmMethodAR) -> OdmMethodValue:
        log.debug("Creating new OdmMethodValue node for uid=%s", ar.uid)
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.oid = ar.odm_vo.oid
        value_node.method_type = ar.odm_vo.method_type

        return value_node

    def _has_data_changed(self, ar: OdmMethodAR, value: OdmMethodValue) -> bool:
        are_odm_properties_changed = super()._has_data_changed(ar=ar, value=value)

        formal_expression_nodes = {
            OdmFormalExpressionModel(
                context=formal_expression_node.context,
                expression=formal_expression_node.expression,
            )
            for formal_expression_node in value.has_formal_expression.all()
        }
        translated_text_nodes = {
            OdmTranslatedTextModel(
                text_type=translated_text_node.text_type,
                language=translated_text_node.language,
                text=translated_text_node.text,
            )
            for translated_text_node in value.has_translated_text.all()
        }
        alias_nodes = {
            OdmAliasModel(name=alias_node.name, context=alias_node.context)
            for alias_node in value.has_alias.all()
        }

        are_rels_changed = (
            set(ar.odm_vo.formal_expressions) != formal_expression_nodes
            or set(ar.odm_vo.translated_texts) != translated_text_nodes
            or set(ar.odm_vo.aliases) != alias_nodes
        )

        return (
            are_odm_properties_changed
            or are_rels_changed
            or ar.odm_vo.oid != value.oid
            or ar.odm_vo.method_type != value.method_type
        )

    def set_all_method_oid_properties_to_null(self, oid):
        log.info("Setting method_oid to null for oid=%s", oid)
        db.cypher_query(
            "MATCH ()-[r:ITEM_REF {method_oid: $oid}]-() SET r.method_oid = null",
            {"oid": oid},
        )
