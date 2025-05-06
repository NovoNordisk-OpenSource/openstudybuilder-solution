from typing import cast

from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    UnitDefinitionRoot,
    UnitDefinitionValue,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.dictionary import UCUMTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameterTermRoot,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    CTTerm,
    UnitDefinitionAR,
    UnitDefinitionValueVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
)
from common.utils import convert_to_datetime


class UnitDefinitionRepository(ConceptGenericRepository[UnitDefinitionAR]):
    value_class = UnitDefinitionValue
    root_class = UnitDefinitionRoot
    user: str
    return_model = UnitDefinitionModel

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
        return """
        WITH *,
            concept_value.si_unit as si_unit,
            concept_value.display_unit AS display_unit,
            concept_value.master_unit as master_unit,
            concept_value.convertible_unit as convertible_unit,
            concept_value.us_conventional_unit as us_conventional_unit,
            concept_value.use_complex_unit_conversion as use_complex_unit_conversion,
            concept_value.use_molecular_weight AS use_molecular_weight,
            concept_value.legacy_code AS legacy_code,
            concept_value.conversion_factor_to_master as conversion_factor_to_master,
            concept_value.order as order,
            concept_value.comment as comment,
            [(concept_value)-[:HAS_CT_UNIT]->(term_root)-[:HAS_NAME_ROOT]-()-[:LATEST_FINAL]-(value) 
                | {uid:term_root.uid, name: value.name}] AS ct_units,
            [(concept_value)-[:HAS_UNIT_SUBSET]->(term_root)-[:HAS_NAME_ROOT]-()-[:LATEST_FINAL]-(value) 
                | {uid:term_root.uid, name: value.name}] AS unit_subsets,
            head([(concept_value)-[:HAS_CT_DIMENSION]->(term_root)-[:HAS_NAME_ROOT]-()-[:LATEST_FINAL]-(value) 
                | {uid:term_root.uid, name: value.name}]) AS unit_dimension,
            head([(concept_value)-[:HAS_UCUM_TERM]->(ucum_term_root)-[:LATEST_FINAL]->(value) 
                | {uid:ucum_term_root.uid, name:value.name}]) AS ucum
        """

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library)
        filter_parameters = []
        if kwargs.get("dimension") is not None:
            unit_dimension_name = kwargs.get("dimension")
            filter_by_unit_dimension_name = """
            head([(concept_value)-[:HAS_CT_DIMENSION]->(term_root)-[:HAS_NAME_ROOT]->
            (term_name_root)-[:LATEST_FINAL]->(term_name_value) | 
            term_name_value.name])=$unit_dimension_name"""
            filter_parameters.append(filter_by_unit_dimension_name)
            filter_query_parameters["unit_dimension_name"] = unit_dimension_name
        if kwargs.get("subset") is not None:
            subset_value = kwargs.get("subset")
            filter_by_subset_name = """
            $subset_value IN [(concept_value)-[:HAS_UNIT_SUBSET]->(term_root)-[:HAS_NAME_ROOT]->
            (term_name_root)-[:LATEST_FINAL]->(term_name_value) | term_name_value.name]"""
            filter_parameters.append(filter_by_subset_name)
            filter_query_parameters["subset_value"] = subset_value
        extended_filter_statements = " AND ".join(filter_parameters)
        if filter_statements_from_concept != "":
            if len(extended_filter_statements) > 0:
                filter_statements_to_return = " AND ".join(
                    [filter_statements_from_concept, extended_filter_statements]
                )
            else:
                filter_statements_to_return = filter_statements_from_concept
        else:
            filter_statements_to_return = (
                "WHERE " + extended_filter_statements
                if len(extended_filter_statements) > 0
                else ""
            )
        return filter_statements_to_return, filter_query_parameters

    def _create_ar(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> UnitDefinitionAR:
        ar_root = cast(UnitDefinitionRoot, root)
        ar_value = cast(UnitDefinitionValue, value)

        ct_units = []
        for ct_unit in _kwargs["unit_definition"]["ct_units"]:
            ct_term = CTTerm(
                uid=ct_unit["uid"],
                name=ct_unit["name"],
            )
            ct_units.append(ct_term)

        unit_subsets = []
        for unit_subset in _kwargs["unit_definition"]["unit_subsets"]:
            unit_subset_term = CTTerm(
                uid=unit_subset["uid"],
                name=unit_subset["name"],
            )
            unit_subsets.append(unit_subset_term)
        result = UnitDefinitionAR.from_repository_values(
            library=LibraryVO.from_repository_values(
                library_name=library.name, is_editable=library.is_editable
            ),
            uid=ar_root.uid,
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            unit_definition_value=UnitDefinitionValueVO.from_repository_values(
                name=ar_value.name,
                definition=ar_value.definition,
                si_unit=ar_value.si_unit,
                display_unit=ar_value.display_unit,
                master_unit=ar_value.master_unit,
                convertible_unit=ar_value.convertible_unit,
                us_conventional_unit=ar_value.us_conventional_unit,
                use_complex_unit_conversion=ar_value.use_complex_unit_conversion,
                use_molecular_weight=ar_value.use_molecular_weight,
                legacy_code=ar_value.legacy_code,
                conversion_factor_to_master=ar_value.conversion_factor_to_master,
                order=ar_value.order,
                comment=ar_value.comment,
                ct_units=ct_units,
                unit_subsets=unit_subsets,
                unit_dimension_uid=_kwargs["unit_definition"]["ct_dimension_uid"],
                ucum_uid=_kwargs["unit_definition"]["ucum_term_uid"],
                ucum_name=None,
                unit_dimension_name=None,
                is_template_parameter=_kwargs["unit_definition"]["bool_template"],
            ),
        )
        return result

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> UnitDefinitionAR:
        ar_root = cast(UnitDefinitionRoot, root)
        ar_value = cast(UnitDefinitionValue, value)

        ct_units = []
        for ct_unit in value.has_ct_unit.all():
            ct_term = CTTerm(
                uid=ct_unit.uid,
                name=ct_unit.has_name_root.get().latest_final.get().name,
            )
            ct_units.append(ct_term)

        unit_subsets = []
        for unit_subset in value.has_unit_subset.all():
            unit_subset_term = CTTerm(
                uid=unit_subset.uid,
                name=unit_subset.has_name_root.get().latest_final.get().name,
            )
            unit_subsets.append(unit_subset_term)

        ct_dimension = ar_value.has_ct_dimension.get_or_none()
        ucum_term = ar_value.has_ucum_term.get_or_none()

        result = UnitDefinitionAR.from_repository_values(
            library=LibraryVO.from_repository_values(
                library_name=library.name, is_editable=library.is_editable
            ),
            uid=ar_root.uid,
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            unit_definition_value=UnitDefinitionValueVO.from_repository_values(
                name=ar_value.name,
                definition=ar_value.definition,
                si_unit=ar_value.si_unit,
                display_unit=ar_value.display_unit,
                master_unit=ar_value.master_unit,
                convertible_unit=ar_value.convertible_unit,
                us_conventional_unit=ar_value.us_conventional_unit,
                use_complex_unit_conversion=ar_value.use_complex_unit_conversion,
                use_molecular_weight=ar_value.use_molecular_weight,
                legacy_code=ar_value.legacy_code,
                conversion_factor_to_master=ar_value.conversion_factor_to_master,
                order=ar_value.order,
                comment=ar_value.comment,
                ct_units=ct_units,
                unit_subsets=unit_subsets,
                unit_dimension_uid=ct_dimension.uid if ct_dimension else None,
                ucum_uid=ucum_term.uid if ucum_term else None,
                ucum_name=None,
                unit_dimension_name=None,
                is_template_parameter=self.is_concept_node_a_tp(concept_node=value),
            ),
        )
        return result

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> UnitDefinitionAR:
        major, minor = input_dict.get("version").split(".")

        ct_units = []
        for ct_unit in input_dict.get("ct_units"):
            ct_units.append(CTTerm(uid=ct_unit.get("uid"), name=ct_unit.get("name")))
        unit_subsets = []
        for unit_subset in input_dict.get("unit_subsets"):
            unit_subsets.append(
                CTTerm(uid=unit_subset.get("uid"), name=unit_subset.get("name"))
            )

        unit_dimension = input_dict.get("unit_dimension")
        unit_dimension_uid = unit_dimension.get("uid") if unit_dimension else None
        unit_dimension_name = unit_dimension.get("name") if unit_dimension else None

        ucum = input_dict.get("ucum")
        ucum_uid = ucum.get("uid") if ucum else None
        ucum_name = ucum.get("name") if ucum else None
        return UnitDefinitionAR.from_repository_values(
            uid=input_dict.get("uid"),
            unit_definition_value=UnitDefinitionValueVO.from_repository_values(
                name=input_dict.get("name"),
                definition=input_dict.get("definition"),
                si_unit=input_dict.get("si_unit"),
                display_unit=input_dict.get("display_unit"),
                master_unit=input_dict.get("master_unit"),
                convertible_unit=input_dict.get("convertible_unit"),
                us_conventional_unit=input_dict.get("us_conventional_unit"),
                use_complex_unit_conversion=input_dict.get(
                    "use_complex_unit_conversion"
                ),
                use_molecular_weight=input_dict.get("use_molecular_weight"),
                legacy_code=input_dict.get("legacy_code"),
                conversion_factor_to_master=input_dict.get(
                    "conversion_factor_to_master"
                ),
                ct_units=ct_units,
                unit_subsets=unit_subsets,
                unit_dimension_uid=unit_dimension_uid,
                ucum_uid=ucum_uid,
                ucum_name=ucum_name,
                unit_dimension_name=unit_dimension_name,
                order=input_dict.get("order"),
                comment=input_dict.get("comment"),
                is_template_parameter=input_dict.get("template_parameter"),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict.get("library_name"),
                is_library_editable_callback=(
                    lambda _: input_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("change_description"),
                status=LibraryItemStatus(input_dict.get("status")),
                author_id=input_dict.get("author_id"),
                author_username=input_dict.get("author_username"),
                start_date=convert_to_datetime(value=input_dict.get("start_date")),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

    def _create_new_value_node(self, ar: UnitDefinitionAR) -> VersionValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.legacy_code = ar.concept_vo.legacy_code
        value_node.convertible_unit = ar.concept_vo.convertible_unit
        value_node.display_unit = ar.concept_vo.display_unit
        value_node.master_unit = ar.concept_vo.master_unit
        value_node.si_unit = ar.concept_vo.si_unit
        value_node.us_conventional_unit = ar.concept_vo.us_conventional_unit
        value_node.use_complex_unit_conversion = (
            ar.concept_vo.use_complex_unit_conversion
        )
        value_node.use_molecular_weight = ar.concept_vo.use_molecular_weight
        value_node.conversion_factor_to_master = (
            ar.concept_vo.conversion_factor_to_master
        )
        value_node.order = ar.concept_vo.order
        value_node.comment = ar.concept_vo.comment
        value_node.save()

        if ar.concept_vo.ucum_uid:
            value_node.has_ucum_term.connect(
                UCUMTermRoot.nodes.get(uid=ar.concept_vo.ucum_uid)
            )
        if ar.concept_vo.unit_dimension_uid:
            value_node.has_ct_dimension.connect(
                CTTermRoot.nodes.get(uid=ar.concept_vo.unit_dimension_uid)
            )

        for ct_unit in ar.concept_vo.ct_units:
            value_node.has_ct_unit.connect(CTTermRoot.nodes.get(uid=ct_unit.uid))
        for unit_subset in ar.concept_vo.unit_subsets:
            value_node.has_unit_subset.connect(
                CTTermRoot.nodes.get(uid=unit_subset.uid)
            )

        return value_node

    def _has_data_changed(
        self, ar: UnitDefinitionAR, value: UnitDefinitionValue
    ) -> bool:
        ucum_term = value.has_ucum_term.get_or_none()
        unit_dimension = value.has_ct_dimension.get_or_none()
        ar_ct_units = set(unit.uid for unit in ar.concept_vo.ct_units)
        ar_unit_subsets = set(subset.uid for subset in ar.concept_vo.unit_subsets)
        value_ct_unit_nodes = value.has_ct_unit.all()
        value_ct_units = set(unit.uid for unit in value_ct_unit_nodes)
        value_ct_unit_subset_nodes = value.has_unit_subset.all()
        value_ct_unit_subsets = set(ss.uid for ss in value_ct_unit_subset_nodes)
        return (
            ar.concept_vo.name != value.name
            or ar.concept_vo.name_sentence_case != value.name_sentence_case
            or ar.concept_vo.definition != value.definition
            or ar.concept_vo.ucum_uid != self._get_uid_or_none(ucum_term)
            or ar.concept_vo.unit_dimension_uid != self._get_uid_or_none(unit_dimension)
            or ar.concept_vo.convertible_unit != value.convertible_unit
            or ar.concept_vo.display_unit != value.display_unit
            or ar.concept_vo.master_unit != value.master_unit
            or ar.concept_vo.si_unit != value.si_unit
            or ar.concept_vo.us_conventional_unit != value.us_conventional_unit
            or ar.concept_vo.use_complex_unit_conversion
            != value.use_complex_unit_conversion
            or ar.concept_vo.legacy_code != value.legacy_code
            or ar.concept_vo.use_molecular_weight != value.use_molecular_weight
            or ar.concept_vo.conversion_factor_to_master
            != value.conversion_factor_to_master
            or ar.concept_vo.order != value.order
            or ar.concept_vo.comment != value.comment
            or ar_ct_units != value_ct_units
            or ar_unit_subsets != value_ct_unit_subsets
        )

    def _maintain_parameters(
        self,
        versioned_object: UnitDefinitionAR,
        root: UnitDefinitionRoot,
        value: UnitDefinitionValue,
    ) -> None:
        if versioned_object.concept_vo.is_template_parameter:
            # neomodel can't add custom label to already existing node, we have to manage that by executing cypher query
            # unit definitions should link to the template parameter with the name of the associated unit dimension
            unit_subsets = value.has_unit_subset.all()
            if unit_subsets:
                for unit_subset in unit_subsets:
                    template_parameter_name = (
                        unit_subset.has_name_root.single()
                        .has_latest_value.single()
                        .name
                    )
                    query = """
                        MATCH (template_parameter:TemplateParameter {name:$template_parameter_name})
                        MATCH (concept_root:ConceptRoot {uid: $uid})-[:LATEST]->(concept_value)
                        MERGE (template_parameter)-[:HAS_PARAMETER_TERM]->(concept_root)
                    """
                    db.cypher_query(
                        query,
                        {
                            "uid": versioned_object.uid,
                            "template_parameter_name": template_parameter_name,
                        },
                    )
            query = """
                MATCH (concept_root:ConceptRoot {uid: $uid})-[:LATEST]->(concept_value)
                MATCH (unit:TemplateParameter {name: "Unit"})
                MERGE (unit)-[:HAS_PARAMETER_TERM]->(concept_root)
                SET concept_root:TemplateParameterTermRoot
                SET concept_value:TemplateParameterTermValue
            """
            db.cypher_query(
                query,
                {
                    "uid": versioned_object.uid,
                },
            )
            TemplateParameterTermRoot.generate_node_uids_if_not_present()

    def master_unit_exists_by_unit_dimension(self, unit_dimension: str) -> bool:
        cypher_query = f"""
            MATCH (or:{self.root_class.__label__})-[:LATEST]->(ov:{self.value_class.__label__} {{master_unit: true}})
            -[:HAS_CT_DIMENSION]->(term_root:CTTermRoot {{uid: $unit_dimension_uid}})
            RETURN or.uid
        """
        items, _ = db.cypher_query(cypher_query, {"unit_dimension_uid": unit_dimension})

        return len(items) > 0

    def exists_by_legacy_code(self, legacy_code: str) -> bool:
        cypher_query = f"""
            MATCH (or:{self.root_class.__label__})-[:LATEST]->(ov:{self.value_class.__label__} {{legacy_code: $legacy_code}})
            RETURN or.uid
        """
        items, _ = db.cypher_query(cypher_query, {"legacy_code": legacy_code})

        return len(items) > 0

    def check_exists_by_name(self, name: str) -> bool:
        cypher_query = f"""
            MATCH (or:{self.root_class.__label__})-[:LATEST]->(ov:{self.value_class.__label__} {{name: $name }})
            RETURN or.uid, ov.name
        """
        items, _ = db.cypher_query(cypher_query, {"name": name})

        return len(items) > 0

    def get_dimension_names_by_unit_definition_uids(
        self,
        unit_definition_uids: list[str],
    ) -> list[str]:
        cypher_query = """
MATCH (udr:UnitDefinitionRoot)-[:LATEST]->(udv:UnitDefinitionValue)
WHERE udr.uid IN $unit_definition_uids
MATCH (udv)-[:HAS_CT_DIMENSION]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(CTTermNameRoot)-[:LATEST]->(ctnv:CTTermNameValue)
RETURN ctnv.name
"""

        items, _ = db.cypher_query(
            cypher_query, {"unit_definition_uids": unit_definition_uids}
        )
        return [item[0] for item in items]
