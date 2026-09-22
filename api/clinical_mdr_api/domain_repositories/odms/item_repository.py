import json
from textwrap import dedent
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
    CTCodelistTerm,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import OdmItemRoot, OdmItemValue
from clinical_mdr_api.domain_repositories.odms.generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domains.odms.item import (
    CTTermItem,
    OdmItemAR,
    OdmItemRefVO,
    OdmItemTermVO,
    OdmItemUnitDefinitionVO,
    OdmItemVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmTranslatedTextModel,
)
from clinical_mdr_api.models.odms.item import (
    OdmItem,
    OdmItemCodelist,
    OdmItemParentGroup,
)
from clinical_mdr_api.services._utils import ensure_transaction
from clinical_mdr_api.utils import db_result_to_list
from common.config import settings
from common.exceptions import NotFoundException
from common.utils import convert_to_datetime, version_string_to_tuple


class ItemRepository(OdmGenericRepository[OdmItemAR]):
    root_class = OdmItemRoot
    value_class = OdmItemValue
    return_model = OdmItem

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmItemAR:
        activity_instances = db.cypher_query(
            dedent(f"""
                MATCH (oiv:OdmItemValue)-[ltai:LINKS_TO_ACTIVITY_ITEM]->(ai:ActivityItem)
                MATCH (ai)<-[:HAS_ACTIVITY_ITEM]-(aicr:ActivityItemClassRoot)-[:LATEST]->(aicv:ActivityItemClassValue)
                MATCH (ai)<-[:CONTAINS_ACTIVITY_ITEM]-(aiv:ActivityInstanceValue)<-[:LATEST]-(air:ActivityInstanceRoot)
                WHERE elementId(oiv) = $element_id

                CALL (aiv) {{
                    MATCH (aiv)-[:CONTAINS_ACTIVITY_ITEM]->(domain_ai:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(:ActivityItemClassRoot)-[:LATEST]->(:ActivityItemClassValue {{name: "domain"}})
                    MATCH (domain_ai)-[:HAS_CT_TERM]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(ctr:CTTermRoot)
                    <-[:HAS_TERM_ROOT]-(cct:CTCodelistTerm)-[:HAS_TERM]-(:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
                    -[:LATEST]->(ctcav:CTCodelistAttributesValue {{submission_value: "{settings.stdm_domain_cl_submval}"}})
                    MATCH (ctr)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(ctnv:CTTermNameValue)
                    RETURN COLLECT(DISTINCT {{
                        submission_value: cct.submission_value,
                        name: ctnv.name
                    }}) AS domain_info
                }}

                OPTIONAL MATCH (aicr)-[:MAPS_VARIABLE_CLASS]->(:VariableClass)-[:HAS_INSTANCE]->(:VariableClassInstance)
                <-[:IMPLEMENTS_VARIABLE]-(:DatasetVariableInstance)<-[:HAS_INSTANCE]-(dv:DatasetVariable)

                WITH
                    air,
                    aiv,
                    aicr,
                    aicv,
                    ltai,
                    domain_info,
                    [
                        result IN COLLECT(
                            DISTINCT CASE
                                WHEN any(d IN domain_info WHERE dv.uid STARTS WITH d.submission_value)
                                THEN {{
                                    matched_domain: head([d IN domain_info WHERE dv.uid STARTS WITH d.submission_value]),
                                    uid: dv.uid
                                }}
                            END
                        )
                        WHERE result IS NOT NULL
                        | {{
                            submission_value: result.matched_domain.submission_value,
                            name: result.matched_domain.name,
                            variable: result.uid
                        }}
                    ] AS dataset_variables

                RETURN DISTINCT
                    air.uid AS activity_instance_uid,
                    aiv.name AS activity_instance_name,
                    aiv.adam_param_code AS activity_instance_adam_param_code,
                    aiv.topic_code AS activity_instance_topic_code,
                    aicr.uid AS activity_item_class_uid,
                    aicv.name AS activity_item_class_name,
                    ltai.order AS order,
                    ltai.primary AS primary,
                    ltai.preset_response_value AS preset_response_value,
                    ltai.value_condition AS value_condition,
                    ltai.value_dependent_map AS value_dependent_map,
                    dataset_variables AS dataset_variables
                """),
            params={"element_id": value.element_id},
        )

        odm_item_group = None
        odm_item_group_rs, _ = db.cypher_query(
            """
            MATCH (oiv:OdmItemValue)<-[:ITEM_REF]-(oigv:OdmItemGroupValue)<-[hv:HAS_VERSION]-(oigr:OdmItemGroupRoot)
            WHERE elementId(oiv) = $element_id
            RETURN
                oigr.uid AS odm_item_group_uid,
                oigv.oid AS odm_item_group_oid,
                oigv.name AS odm_item_group_name
            ORDER BY hv.start_date DESC, hv.end_date DESC
            LIMIT 1
            """,
            params={"element_id": value.element_id},
        )
        if odm_item_group_rs:
            odm_item_group = OdmItemParentGroup(
                uid=odm_item_group_rs[0][0],
                oid=odm_item_group_rs[0][1],
                name=odm_item_group_rs[0][2],
            )

        codelist = value.has_codelist.get_or_none()
        # Load datatype from relationship
        datatype = None
        datatype_rs, _ = db.cypher_query(
            """
            MATCH (oiv:OdmItemValue)-[:HAS_DATA_TYPE]->(ctc:CTTermContext)-[:HAS_SELECTED_TERM]->(tr:CTTermRoot)<-[:HAS_TERM_ROOT]-(ct:CTCodelistTerm)
            MATCH (ctc)-[:HAS_SELECTED_CODELIST]->(cr:CTCodelistRoot)
            MATCH (tr)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(tnv:CTTermNameValue)
            WHERE elementId(oiv) = $element_id
            OPTIONAL MATCH (ct)<-[hr:HAS_TERM]-(cr)
            RETURN
                tr.uid AS term_root_uid,
                tnv.name AS term_name,
                cr.uid AS codelist_root_uid,
                CASE WHEN hr IS NOT NULL THEN ct.submission_value ELSE NULL END AS submission_value
            LIMIT 1
            """,
            params={"element_id": value.element_id},
        )
        if datatype_rs:
            datatype = CTTermItem(
                uid=datatype_rs[0][0],
                name=datatype_rs[0][1],
                codelist_uid=datatype_rs[0][2],
                submission_value=datatype_rs[0][3],
            )

        # Load external question from relationship
        external_question = None
        external_question_rs, _ = db.cypher_query(
            """
            MATCH (oiv:OdmItemValue)-[:HAS_EXTERNAL_QUESTION]->(ctc:CTTermContext)-[:HAS_SELECTED_TERM]->(tr:CTTermRoot)<-[:HAS_TERM_ROOT]-(ct:CTCodelistTerm)
            MATCH (ctc)-[:HAS_SELECTED_CODELIST]->(cr:CTCodelistRoot)
            MATCH (tr)-[:HAS_NAME_ROOT]->(tnr:CTTermNameRoot)-[:LATEST]->(tnv:CTTermNameValue)
            WHERE elementId(oiv) = $element_id
            OPTIONAL MATCH (ct)<-[hr:HAS_TERM]-(cr)
            MATCH (tnr)-[hv:HAS_VERSION]->(tnv)
            RETURN
                tr.uid AS term_root_uid,
                tnv.name AS term_name,
                hv.version AS term_version,
                cr.uid AS codelist_root_uid,
                CASE WHEN hr IS NOT NULL THEN ct.submission_value ELSE NULL END AS submission_value
            LIMIT 1
            """,
            params={"element_id": value.element_id},
        )
        if external_question_rs:
            external_question = CTTermItem(
                uid=external_question_rs[0][0],
                name=external_question_rs[0][1],
                version=external_question_rs[0][2],
                codelist_uid=external_question_rs[0][3],
                submission_value=external_question_rs[0][4],
            )

        return OdmItemAR.from_repository_values(
            uid=root.uid,
            odm_vo=OdmItemVO.from_repository_values(
                oid=value.oid,
                name=value.name,
                prompt=value.prompt,
                datatype=datatype,
                length=value.length,
                significant_digits=value.significant_digits,
                sas_field_name=value.sas_field_name,
                sds_var_name=value.sds_var_name,
                origin=value.origin,
                comment=value.comment,
                odm_item_group=odm_item_group,
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
                unit_definition_uids=[
                    unit_definition.uid
                    for unit_definition in value.has_unit_definition.all()
                ],
                external_question=external_question,
                codelist=(
                    OdmItemCodelist(
                        uid=codelist.uid,
                        allows_multi_choice=value.has_codelist.relationship(
                            codelist
                        ).allows_multi_choice
                        or False,
                    )
                    if codelist
                    else None
                ),
                term_uids=[
                    term.uid
                    for term_context in value.has_codelist_term.all()
                    if (term := term_context.has_selected_term.get_or_none())
                ],
                activity_instances=db_result_to_list(activity_instances),
                vendor_element_uids=[
                    vendor_element_root.uid
                    for vendor_element_value in value.has_vendor_element.all()
                    if (vendor_element_root := vendor_element_value.has_root.single())
                ],
                vendor_attribute_uids=[
                    vendor_attribute_root.uid
                    for vendor_attribute_value in value.has_vendor_attribute.all()
                    if (
                        vendor_attribute_root := vendor_attribute_value.has_root.single()
                    )
                ],
                vendor_element_attribute_uids=[
                    vendor_element_attribute_root.uid
                    for vendor_element_attribute_value in value.has_vendor_element_attribute.all()
                    if (
                        vendor_element_attribute_root := vendor_element_attribute_value.has_root.single()
                    )
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
    ) -> OdmItemAR:
        major, minor = input_dict["version"].split(".")

        # Parse datatype from dict to CTTermItem
        datatype = None
        if datatype_dict := input_dict.get("datatype"):
            datatype = CTTermItem(
                uid=datatype_dict["uid"],
                name=datatype_dict["name"],
                codelist_uid=datatype_dict["codelist_uid"],
                submission_value=datatype_dict.get("submission_value"),
            )

        # Parse external question from dict to CTTermItem
        external_question = None
        if external_question_dict := input_dict.get("external_question"):
            external_question = CTTermItem(
                uid=external_question_dict["uid"],
                name=external_question_dict["name"],
                version=external_question_dict["version"],
                codelist_uid=external_question_dict["codelist_uid"],
                submission_value=external_question_dict.get("submission_value"),
            )

        odm_item_ar = OdmItemAR.from_repository_values(
            uid=input_dict["uid"],
            odm_vo=OdmItemVO.from_repository_values(
                oid=input_dict.get("oid"),
                name=input_dict["name"],
                prompt=input_dict.get("prompt"),
                datatype=datatype,
                length=input_dict.get("length"),
                significant_digits=input_dict.get("significant_digits"),
                sas_field_name=input_dict.get("sas_field_name"),
                sds_var_name=input_dict.get("sds_var_name"),
                origin=input_dict.get("origin"),
                comment=input_dict.get("comment"),
                odm_item_group=(
                    OdmItemParentGroup(
                        uid=input_dict["odm_item_group"]["uid"],
                        oid=input_dict["odm_item_group"].get("oid"),
                        name=input_dict["odm_item_group"].get("name"),
                    )
                    if input_dict.get("odm_item_group", None)
                    else None
                ),
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
                unit_definition_uids=input_dict["unit_definition_uids"],
                external_question=external_question,
                codelist=(
                    OdmItemCodelist(
                        uid=input_dict["codelist"]["uid"],
                        allows_multi_choice=input_dict["codelist"][
                            "allows_multi_choice"
                        ]
                        or False,
                    )
                    if input_dict.get("codelist", None)
                    else None
                ),
                term_uids=input_dict["term_uids"],
                activity_instances=input_dict["activity_instances"],
                vendor_element_uids=input_dict["vendor_element_uids"],
                vendor_attribute_uids=input_dict["vendor_attribute_uids"],
                vendor_element_attribute_uids=input_dict[
                    "vendor_element_attribute_uids"
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

        return odm_item_ar

    def _get_specific_field_mapping(self) -> dict[str, str]:
        """Item specific field mappings - simple fields only."""
        return {
            "name": "odm_value.name AS name",
            "oid": "odm_value.oid AS oid",
            "prompt": "odm_value.prompt AS prompt",
            "length": "odm_value.length AS length",
            "significant_digits": "odm_value.significant_digits AS significant_digits",
            "sas_field_name": "odm_value.sas_field_name AS sas_field_name",
            "sds_var_name": "odm_value.sds_var_name AS sds_var_name",
            "origin": "odm_value.origin AS origin",
            "comment": "odm_value.comment AS comment",
        }

    def _get_computed_field_expressions(self) -> dict[str, str]:
        """Item computed field expressions."""
        # pylint: disable=line-too-long
        return {
            "datatype": """head(COLLECT {
                MATCH (odm_value)-[:HAS_DATA_TYPE]->(data_type_context:CTTermContext)
                MATCH (data_type_context)-[:HAS_SELECTED_TERM]->(data_type_term:CTTermRoot)-[:HAS_NAME_ROOT]->(data_type_name_root:CTTermNameRoot)-[:LATEST]->(data_type_name_value:CTTermNameValue)
                MATCH (data_type_context)-[:HAS_SELECTED_CODELIST]->(data_type_codelist:CTCodelistRoot)
                OPTIONAL MATCH (data_type_codelist)-[:HAS_TERM]->(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(data_type_term)
                RETURN {uid: data_type_term.uid, name: data_type_name_value.name, codelist_uid: data_type_codelist.uid, submission_value: clt.submission_value}
            }) AS datatype""",
            "external_question": """head(COLLECT {
                MATCH (odm_value)-[:HAS_EXTERNAL_QUESTION]->(external_question_context:CTTermContext)
                MATCH (external_question_context)-[:HAS_SELECTED_TERM]->(external_question_term:CTTermRoot)-[:HAS_NAME_ROOT]->(external_question_name_root:CTTermNameRoot)-[:LATEST]->(external_question_name_value:CTTermNameValue)
                MATCH (external_question_context)-[:HAS_SELECTED_CODELIST]->(external_question_codelist:CTCodelistRoot)
                OPTIONAL MATCH (external_question_codelist)-[:HAS_TERM]->(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(external_question_term)
                MATCH (external_question_name_root)-[hv:HAS_VERSION]->(external_question_name_value)
                RETURN {uid: external_question_term.uid, name: external_question_name_value.name, version: hv.version, codelist_uid: external_question_codelist.uid, submission_value: clt.submission_value}
            }) AS external_question""",
            "odm_item_group": "head([(odm_value)<-[:ITEM_REF]-(oigv:OdmItemGroupValue)<-[:HAS_VERSION]-(oigr:OdmItemGroupRoot) | {uid: oigr.uid, oid:oigv.oid, name: oigv.name }]) AS odm_item_group",
            "translated_texts": "[(odm_value)-[:HAS_TRANSLATED_TEXT]->(dv:OdmTranslatedText) | {text_type: dv.text_type, language: dv.language, text: dv.text}] AS translated_texts",
            "aliases": "[(odm_value)-[:HAS_ALIAS]->(av:OdmAlias) | {name: av.name, context: av.context}] AS aliases",
            "unit_definitions": "[(odm_value)-[hud:HAS_UNIT_DEFINITION]->(udr:UnitDefinitionRoot)-[:LATEST]->(udv:UnitDefinitionValue) | {uid: udr.uid, name: udv.name, mandatory: hud.mandatory, order: hud.order}] AS unit_definitions",
            "codelist": "head([(odm_value)-[hc:HAS_CODELIST]->(ctcr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(ctcav:CTCodelistAttributesValue) | {uid: ctcr.uid, name: ctcav.name, preferred_term: ctcav.preferred_term, allows_multi_choice: hc.allows_multi_choice}]) AS codelist",
            "terms": """[(odm_value)-[hct:HAS_CODELIST_TERM]->(ctc:CTTermContext)-[:HAS_SELECTED_TERM]->(tr:CTTermRoot) |
            {
                uid: tr.uid,
                display_text: hct.display_text,
                mandatory: hct.mandatory,
                order: hct.order,
                name: head([(tr)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(tnv:CTTermNameValue) | tnv.name]),
                submission_value: head(
                    [(tr)<-[:HAS_TERM_ROOT]->(cct:CTCodelistTerm)<-[:HAS_TERM]-(:CTCodelistRoot)<-[:HAS_CODELIST]-(odm_value) | cct.submission_value]
                )
            }] AS terms""",
            "vendor_elements": "[(odm_value)-[hve:HAS_VENDOR_ELEMENT]->(vev:OdmVendorElementValue)<-[:HAS_VERSION]-(ver:OdmVendorElementRoot) | {uid: ver.uid, name: vev.name, compatible_types: vev.compatible_types, value: hve.value}] AS vendor_elements",
            "vendor_attributes": "[(odm_value)-[hva:HAS_VENDOR_ATTRIBUTE]->(vav:OdmVendorAttributeValue)<-[:HAS_VERSION]-(var:OdmVendorAttributeRoot) | {uid: var.uid, name: vav.name, data_type: vav.data_type, value_regex: vav.value_regex, compatible_types: vav.compatible_types, value: hva.value}] AS vendor_attributes",
            "vendor_element_attributes": "[(odm_value)-[hvea:HAS_VENDOR_ELEMENT_ATTRIBUTE]->(vav:OdmVendorAttributeValue)<-[:HAS_VERSION]-(var:OdmVendorAttributeRoot) | {uid: var.uid, name: vav.name, data_type: vav.data_type, value_regex: vav.value_regex, compatible_types: vav.compatible_types, value: hvea.value}] AS vendor_element_attributes",
        }

    def specific_alias_clause(self, **kwargs) -> str:
        return dedent(
            "WITH *,"
            + ", ".join(self._get_specific_field_mapping().values())
            + ","
            + ", ".join(self._get_computed_field_expressions().values())
            + f"""
            CALL (*) {{
                MATCH (odm_value)-[ltai:LINKS_TO_ACTIVITY_ITEM]->(ai:ActivityItem)
                MATCH (ai)<-[:HAS_ACTIVITY_ITEM]-(aicr:ActivityItemClassRoot)-[:LATEST]->(aicv:ActivityItemClassValue)
                MATCH (ai)<-[:CONTAINS_ACTIVITY_ITEM]-(aiv:ActivityInstanceValue)<-[:LATEST]-(air:ActivityInstanceRoot)

                CALL (aiv) {{
                    MATCH (aiv)-[:CONTAINS_ACTIVITY_ITEM]->(domain_ai:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(:ActivityItemClassRoot)-[:LATEST]->(:ActivityItemClassValue {{name: "domain"}})
                    MATCH (domain_ai)<-[:HAS_ACTIVITY_ITEM]-(:ActivityItemClassRoot)-[:LATEST]->(:ActivityItemClassValue {{name: "domain"}})
                    MATCH (domain_ai)-[:HAS_CT_TERM]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(ctr:CTTermRoot)
                    <-[:HAS_TERM_ROOT]-(cct:CTCodelistTerm)-[:HAS_TERM]-(:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
                    -[:LATEST]->(ctcav:CTCodelistAttributesValue {{submission_value: "{settings.stdm_domain_cl_submval}"}})
                    MATCH (ctr)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(ctnv:CTTermNameValue)
                    RETURN COLLECT(DISTINCT {{
                        submission_value: cct.submission_value,
                        name: ctnv.name
                    }}) AS domain_info
                }}

                OPTIONAL MATCH (aicr)-[:MAPS_VARIABLE_CLASS]->(:VariableClass)-[:HAS_INSTANCE]->(:VariableClassInstance)
                <-[:IMPLEMENTS_VARIABLE]-(:DatasetVariableInstance)<-[:HAS_INSTANCE]-(dv:DatasetVariable)
                WITH
                    air,
                    aiv,
                    aicr,
                    aicv,
                    ltai,
                    domain_info,
                    [
                        result IN COLLECT(
                            DISTINCT CASE
                                WHEN any(d IN domain_info WHERE dv.uid STARTS WITH d.submission_value)
                                THEN {{
                                    matched_domain: head([d IN domain_info WHERE dv.uid STARTS WITH d.submission_value]),
                                    uid: dv.uid
                                }}
                            END
                        )
                        WHERE result IS NOT NULL
                        | {{
                            submission_value: result.matched_domain.submission_value,
                            name: result.matched_domain.name,
                            variable: result.uid
                        }}
                    ] AS dataset_variables
                RETURN COLLECT(DISTINCT {{
                    activity_instance_uid: air.uid,
                    activity_instance_name: aiv.name,
                    activity_instance_adam_param_code: aiv.adam_param_code,
                    activity_instance_topic_code: aiv.topic_code,
                    activity_item_class_uid: aicr.uid,
                    activity_item_class_name: aicv.name,
                    order: ltai.order,
                    primary: ltai.primary,
                    preset_response_value: ltai.preset_response_value,
                    value_condition: ltai.value_condition,
                    value_dependent_map: ltai.value_dependent_map,
                    dataset_variables: dataset_variables
                }}) AS activity_instances
            }}

            """
            + """
            WITH *,
            apoc.coll.toSet([unit_definition in unit_definitions | unit_definition.uid]) AS unit_definition_uids,
            apoc.coll.toSet([term in terms | term.uid]) AS term_uids,
            apoc.coll.toSet([vendor_element in vendor_elements | vendor_element.uid]) AS vendor_element_uids,
            apoc.coll.toSet([vendor_attribute in vendor_attributes | vendor_attribute.uid]) AS vendor_attribute_uids,
            apoc.coll.toSet([vendor_element_attribute in vendor_element_attributes | vendor_element_attribute.uid]) AS vendor_element_attribute_uids
            """
        )

    def _get_or_create_value(
        self, root: VersionRoot, ar: OdmItemAR, force_new_value_node: bool = False
    ) -> VersionValue:
        current_latest = root.has_latest_value.single()

        new_value = super()._get_or_create_value(root, ar, force_new_value_node)

        self.manage_vendor_relationships(
            current_latest, new_value, ar.should_disconnect_relationships
        )
        self.connect_translated_texts(ar.odm_vo.translated_texts, new_value)
        self.connect_aliases(ar.odm_vo.aliases, new_value)

        new_value.has_codelist.disconnect_all()
        if ar.odm_vo.codelist is not None:
            codelist = CTCodelistRoot.nodes.get_or_none(uid=ar.odm_vo.codelist.uid)
            new_value.has_codelist.connect(
                codelist,
                {"allows_multi_choice": ar.odm_vo.codelist.allows_multi_choice},
            )

        for activity_instance in ar.odm_vo.activity_instances:
            db.cypher_query(
                dedent("""
                    MATCH (air:ActivityInstanceRoot {uid: $activity_instance_uid})-[:LATEST]->(aiv:ActivityInstanceValue)
                    -[:CONTAINS_ACTIVITY_ITEM]->(ai:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(:ActivityItemClassRoot {uid: $activity_item_class_uid})
                    MATCH (oiv:OdmItemValue)
                    WHERE elementId(oiv) = $element_id

                    MERGE (oiv)-[:LINKS_TO_ACTIVITY_ITEM {
                        order: $order,
                        primary: $primary,
                        preset_response_value: $preset_response_value,
                        value_condition: $value_condition,
                        value_dependent_map: $value_dependent_map
                    }]->(ai)
                    """),
                params={
                    "element_id": new_value.element_id,
                    "activity_instance_uid": activity_instance["activity_instance_uid"],
                    "activity_item_class_uid": activity_instance[
                        "activity_item_class_uid"
                    ],
                    "order": activity_instance["order"],
                    "primary": activity_instance["primary"],
                    "preset_response_value": activity_instance["preset_response_value"],
                    "value_condition": activity_instance["value_condition"],
                    "value_dependent_map": activity_instance["value_dependent_map"],
                },
            )

        return new_value

    def _create_new_value_node(self, ar: OdmItemAR) -> OdmItemValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.oid = ar.odm_vo.oid
        value_node.prompt = ar.odm_vo.prompt
        value_node.length = ar.odm_vo.length
        value_node.significant_digits = ar.odm_vo.significant_digits
        value_node.sas_field_name = ar.odm_vo.sas_field_name
        value_node.sds_var_name = ar.odm_vo.sds_var_name
        value_node.origin = ar.odm_vo.origin
        value_node.comment = ar.odm_vo.comment

        # Connect datatype relationship
        value_node.has_data_type.disconnect_all()
        if ar.odm_vo.datatype is not None:
            data_type_term = CTTermRoot.nodes.get(uid=ar.odm_vo.datatype.uid)
            selected_term_node = (
                CTCodelistAttributesRepository().get_or_create_selected_term(
                    data_type_term,
                    codelist_submission_value=settings.ddf_odm_data_type_cl_submval,
                )
            )
            value_node.has_data_type.connect(selected_term_node)

        # Connect external question relationship
        value_node.has_external_question.disconnect_all()
        if ar.odm_vo.external_question is not None:
            external_question_term = CTTermRoot.nodes.get(
                uid=ar.odm_vo.external_question.uid
            )
            selected_term_node = (
                CTCodelistAttributesRepository().get_or_create_selected_term(
                    external_question_term,
                    codelist_uid=ar.odm_vo.external_question.codelist_uid,
                )
            )
            value_node.has_external_question.connect(selected_term_node)

        return value_node

    def _has_data_changed(self, ar: OdmItemAR, value: OdmItemValue) -> bool:
        are_odm_properties_changed = super()._has_data_changed(ar=ar, value=value)

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
        unit_definition_uids = {
            unit_definition.uid for unit_definition in value.has_unit_definition.all()
        }
        if codelist := value.has_codelist.get_or_none():
            rel = value.has_codelist.relationship(codelist)
            codelist = (codelist.uid, rel.allows_multi_choice or False)
        else:
            codelist = None

        # Get datatype from relationship
        if _datatype := value.has_data_type.get_or_none():
            _datatype = (
                _datatype.has_selected_term.get_or_none().uid,
                _datatype.has_selected_codelist.get_or_none().uid,
            )
        else:
            _datatype = (None, None)

        # Get external question from relationship
        if _external_question := value.has_external_question.get_or_none():
            _external_question = (
                _external_question.has_selected_term.get_or_none().uid,
                _external_question.has_selected_codelist.get_or_none().uid,
            )
        else:
            _external_question = (None, None)

        term_uids = {
            term.uid
            for term_context in value.has_codelist_term.all()
            for term in term_context.has_selected_term.all()
        }

        activity_instances, _ = db.cypher_query(
            dedent("""
                MATCH (oiv:OdmItemValue)-[ltai:LINKS_TO_ACTIVITY_ITEM]->(ai:ActivityItem)
                MATCH (ai)<-[:HAS_ACTIVITY_ITEM]-(aicr:ActivityItemClassRoot)
                MATCH (ai)<-[:CONTAINS_ACTIVITY_ITEM]-(:ActivityInstanceValue)<-[:LATEST]-(air:ActivityInstanceRoot)
                WHERE elementId(oiv) = $element_id

                RETURN DISTINCT
                    air.uid AS activity_instance_uid,
                    aicr.uid AS activity_item_class_uid,
                    ltai.order AS order,
                    ltai.primary AS primary,
                    ltai.preset_response_value AS preset_response_value,
                    ltai.value_condition AS value_condition,
                    ltai.value_dependent_map AS value_dependent_map
                """),
            params={"element_id": value.element_id},
        )

        ar_activity_instances = [
            [
                activity_instance["activity_instance_uid"],
                activity_instance["activity_item_class_uid"],
                activity_instance["order"],
                activity_instance["primary"],
                activity_instance["preset_response_value"],
                activity_instance["value_condition"],
                activity_instance["value_dependent_map"],
            ]
            for activity_instance in ar.odm_vo.activity_instances
        ]

        are_rels_changed = (
            set(ar.odm_vo.translated_texts) != translated_text_nodes
            or set(ar.odm_vo.aliases) != alias_nodes
            or set(ar.odm_vo.unit_definition_uids) != unit_definition_uids
            or (
                getattr(ar.odm_vo.codelist, "uid", None),
                getattr(ar.odm_vo.codelist, "allows_multi_choice", None),
            )
            != codelist
            or set(ar.odm_vo.term_uids) != term_uids
            or sorted(ar_activity_instances) != sorted(activity_instances)
        )

        return (
            are_odm_properties_changed
            or are_rels_changed
            or ar.odm_vo.oid != value.oid
            or ar.odm_vo.prompt != value.prompt
            or (
                ar.odm_vo.datatype.uid if ar.odm_vo.datatype else None,
                ar.odm_vo.datatype.codelist_uid if ar.odm_vo.datatype else None,
            )
            != _datatype
            or (
                (
                    ar.odm_vo.external_question.uid
                    if ar.odm_vo.external_question
                    else None
                ),
                (
                    ar.odm_vo.external_question.codelist_uid
                    if ar.odm_vo.external_question
                    else None
                ),
            )
            != _external_question
            or ar.odm_vo.length != value.length
            or ar.odm_vo.significant_digits != value.significant_digits
            or ar.odm_vo.sas_field_name != value.sas_field_name
            or ar.odm_vo.sds_var_name != value.sds_var_name
            or ar.odm_vo.origin != value.origin
            or ar.odm_vo.comment != value.comment
        )

    def find_by_uid_with_item_group_relation(
        self, uid: str, item_group_uid: str, item_group_version: str
    ) -> OdmItemRefVO:
        rs, _ = db.cypher_query(
            """
            MATCH (:OdmItemGroupRoot {uid: $item_group_uid})-[:HAS_VERSION {version: $item_group_version}]->(:OdmItemGroupValue)
            -[ref:ITEM_REF]->(value:OdmItemValue)

            MATCH (value)<-[hv_rel:HAS_VERSION]-(:OdmItemRoot {uid: $uid})
            WITH value, ref, hv_rel
            ORDER BY hv_rel.start_date DESC
            WITH value, ref, collect(hv_rel) AS hv_rels

            RETURN
                value.oid AS oid,
                value.name AS name,
                hv_rels[0].version AS version,
                ref.order_number AS order_number,
                ref.mandatory AS mandatory,
                ref.key_sequence AS key_sequence,
                ref.method_oid AS method_oid,
                ref.imputation_method_oid AS imputation_method_oid,
                ref.role AS role,
                ref.role_codelist_oid AS role_codelist_oid,
                ref.collection_exception_condition_oid AS collection_exception_condition_oid,
                ref.vendor AS vendor
            """,
            params={
                "uid": uid,
                "item_group_uid": item_group_uid,
                "item_group_version": item_group_version,
            },
        )

        return OdmItemRefVO.from_repository_values(
            uid=uid,
            oid=rs[0][0],
            name=rs[0][1],
            version=rs[0][2],
            item_group_uid=item_group_uid,
            order_number=rs[0][3],
            mandatory=rs[0][4],
            key_sequence=rs[0][5],
            method_oid=rs[0][6],
            imputation_method_oid=rs[0][7],
            role=rs[0][8],
            role_codelist_oid=rs[0][9],
            collection_exception_condition_oid=rs[0][10],
            vendor=json.loads(rs[0][11]) if rs[0][11] else {},
        )

    def _get_latest_version_for_status(
        self, root: VersionRoot, value: VersionValue, status: LibraryItemStatus
    ) -> VersionRelationship:
        all_rels = root.has_version.all_relationships(value)
        rels = [rel for rel in all_rels if rel.status == status.value]
        if len(rels) == 0:
            raise RuntimeError(f"No HAS_VERSION was found with status {status}")
        latest = max(rels, key=lambda r: version_string_to_tuple(r.version))
        return latest

    def find_term_with_item_relation_by_item_uid(self, uid: str, term_uid: str):
        def _get_relationship():
            if ct_term_attributes_value_draft:
                rel_data = self._get_latest_version_for_status(
                    ct_term_attributes_root,
                    ct_term_attributes_value,
                    LibraryItemStatus.DRAFT,
                )
                if rel_data and not rel_data.end_date:
                    return rel_data

            if ct_term_attributes_value_final:
                rel_data = self._get_latest_version_for_status(
                    ct_term_attributes_root,
                    ct_term_attributes_value,
                    LibraryItemStatus.FINAL,
                )
                if not rel_data.end_date:
                    return rel_data

            raise NotFoundException(
                msg=f"No DRAFT or FINAL found for CT Term with UID '{ct_term_root.uid}'."
            )

        item_root = self.root_class.nodes.get_or_none(uid=uid)
        item_value = item_root.has_latest_value.single()

        ct_term_root = CTTermRoot.nodes.get_or_none(uid=term_uid)
        ct_term_name_root = ct_term_root.has_name_root.get_or_none()
        ct_term_name_value = ct_term_name_root.has_latest_value.get_or_none()
        ct_term_attributes_root = ct_term_root.has_attributes_root.get_or_none()
        ct_term_attributes_value = (
            ct_term_attributes_root.has_latest_value.get_or_none()
        )
        ct_term_attributes_value_draft = (
            ct_term_attributes_root.latest_draft.get_or_none()
        )
        ct_term_attributes_value_final = (
            ct_term_attributes_root.latest_final.get_or_none()
        )

        rel = next(
            (
                item_value.has_codelist_term.relationship(term_context)
                for term_context in item_value.has_codelist_term.all()
                if (term := term_context.has_selected_term.get_or_none())
                and term.uid == ct_term_root.uid
            ),
            None,
        )

        codelist_uid = item_value.has_codelist.get_or_none().uid
        cl_term_nodes = (
            CTCodelistTerm.nodes.traverse("has_term_root", "has_term").filter(
                has_term__uid=codelist_uid, has_term_root__uid=term_uid
            )
        ).all()

        submission_value = next(
            (
                cl_term[0].submission_value
                for cl_term in cl_term_nodes
                if cl_term[4].end_date is None
            ),
            None,
        )

        if rel and submission_value:
            return OdmItemTermVO.from_repository_values(
                uid=uid,
                name=ct_term_name_value.name,
                mandatory=rel.mandatory,
                order=rel.order,
                display_text=rel.display_text,
                version=_get_relationship().version,
                submission_value=submission_value,
            )
        return None

    def find_unit_definition_with_item_relation_by_item_uid(
        self, uid: str, unit_definition_uid: str
    ):
        item_root = self.root_class.nodes.get_or_none(uid=uid)
        if not item_root:
            raise ValueError(f"ODM Item with UID '{uid}' not found.")

        item_value = item_root.has_latest_value.get_or_none()
        if not item_value:
            raise ValueError(f"Latest value for ODM Item '{uid}' not found.")

        unit_definition_root = UnitDefinitionRoot.nodes.get_or_none(
            uid=unit_definition_uid
        )
        unit_definition_value = unit_definition_root.has_latest_value.single()

        rel = item_value.has_unit_definition.relationship(unit_definition_root)

        if rel:
            return OdmItemUnitDefinitionVO.from_repository_values(
                uid=uid,
                name=unit_definition_value.name,
                mandatory=rel.mandatory,
                order=rel.order,
            )
        return None

    def remove_all_codelist_terms_from_item(self, item_uid: str):
        db.cypher_query(
            """
                MATCH (:OdmItemRoot {uid: $uid})-[:LATEST]->(:OdmItemValue)-[r:HAS_CODELIST_TERM]->(:CTTermContext)
                DELETE r
                """,
            params={"uid": item_uid},
        )

    @ensure_transaction(db)
    def _connect_relationships_to_new_value_node(
        self, root: VersionRoot, _: VersionValue
    ) -> None:
        """
        Upgrades all incoming ITEM_REF relationships to the second latest version to point
        to the latest version of OdmItemValue, preserving relationship properties.
        """
        query = f"""
        MATCH (root:{self.root_class.__name__} {{uid: $root_uid}})-[ver_rel:HAS_VERSION]->(value:{self.value_class.__name__})

        WITH root, ver_rel, value
        ORDER BY ver_rel.start_date DESC, ver_rel.end_date DESC
        LIMIT 2
        WITH root, collect(value) AS values
        WITH root, values[0] as latest_value, values[1] as second_latest_value

        MATCH (:OdmItemGroupRoot)-[p_ver_rel:HAS_VERSION]->(parent_value:OdmItemGroupValue)-[ref_rel:ITEM_REF]->(second_latest_value)
        WHERE p_ver_rel.end_date IS NULL AND p_ver_rel.status = "Draft"

        WITH latest_value, ref_rel, parent_value,
            ref_rel.order_number AS order_number,
            ref_rel.mandatory AS mandatory,
            ref_rel.key_sequence AS key_sequence,
            ref_rel.method_oid AS method_oid,
            ref_rel.imputation_method_oid AS imputation_method_oid,
            ref_rel.role AS role,
            ref_rel.role_codelist_oid AS role_codelist_oid,
            ref_rel.collection_exception_condition_oid AS collection_exception_condition_oid,
            ref_rel.vendor AS vendor

        CREATE (parent_value)-[new_ref_rel:ITEM_REF]->(latest_value)

        SET new_ref_rel.order_number = order_number,
            new_ref_rel.mandatory = mandatory,
            new_ref_rel.key_sequence = key_sequence,
            new_ref_rel.method_oid = method_oid,
            new_ref_rel.imputation_method_oid = imputation_method_oid,
            new_ref_rel.role = role,
            new_ref_rel.role_codelist_oid = role_codelist_oid,
            new_ref_rel.collection_exception_condition_oid = collection_exception_condition_oid,
            new_ref_rel.vendor = vendor

        DELETE ref_rel
        """
        db.cypher_query(query, {"root_uid": root.uid})
