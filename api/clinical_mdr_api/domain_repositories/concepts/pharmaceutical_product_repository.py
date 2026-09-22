from typing import Any

from deepdiff import DeepDiff

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.models.active_substance import (
    ActiveSubstanceRoot,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    LagTimeRoot,
    NumericValueWithUnitRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.pharmaceutical_product import (
    Ingredient,
    IngredientFormulation,
    PharmaceuticalProductRoot,
    PharmaceuticalProductValue,
)
from clinical_mdr_api.domains.concepts.concept_base import _AggregateRootType
from clinical_mdr_api.domains.concepts.pharmaceutical_product import (
    FormulationVO,
    IngredientVO,
    PharmaceuticalProductAR,
    PharmaceuticalProductVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.pharmaceutical_product import (
    PharmaceuticalProduct,
)
from common.config import settings
from common.utils import convert_to_datetime


class PharmaceuticalProductRepository(ConceptGenericRepository):
    root_class = PharmaceuticalProductRoot
    value_class = PharmaceuticalProductValue
    return_model = PharmaceuticalProduct

    # Flat string aliases for wildcard filtering across linked entities
    wildcard_properties_list: list[str] = [
        "uid",
        "external_id",
        "name",
        "library_name",
        "status",
        "version",
        "author_username",
        "_search_derived_pp_name",
        "_search_dosage_form_names",
        "_search_route_of_admin_names",
        "_search_active_substance_inns",
        "_search_active_substance_long_numbers",
        "_search_active_substance_short_numbers",
        "_search_active_substance_analyte_numbers",
        "_search_active_substance_external_ids",
    ]

    # Mapping of sort/filter field names to sortable Cypher aliases
    _SORT_KEY_MAP = {
        "dosage_form": "_search_dosage_form_names",
        "dosage_forms": "_search_dosage_form_names",
        "route_of_administration": "_search_route_of_admin_names",
        "routes_of_administration": "_search_route_of_admin_names",
        "derived_name": "_search_derived_pp_name",
    }

    @classmethod
    def format_filter_sort_keys(cls, key: str) -> str:
        return cls._SORT_KEY_MAP.get(key, key)

    def _create_new_value_node(self, ar: _AggregateRootType) -> VersionValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.save()

        for uid in ar.concept_vo.dosage_form_uids:
            dosage_form_node = CTTermRoot.nodes.get(uid=uid)
            selected_term_node = (
                CTCodelistAttributesRepository().get_or_create_selected_term(
                    dosage_form_node,
                    codelist_submission_value=settings.dosage_form_cl_submval,
                    catalogue_name=settings.sdtm_ct_catalogue_name,
                )
            )
            value_node.has_dosage_form.connect(selected_term_node)

        for uid in ar.concept_vo.route_of_administration_uids:
            roa_node = CTTermRoot.nodes.get(uid=uid)
            selected_term_node = CTCodelistAttributesRepository().get_or_create_selected_term(
                roa_node,
                codelist_submission_value=settings.route_of_administration_cl_submval,
                catalogue_name=settings.sdtm_ct_catalogue_name,
            )
            value_node.has_route_of_administration.connect(selected_term_node)

        for formulation in ar.concept_vo.formulations:
            formulation_node = IngredientFormulation(
                external_id=formulation.external_id
            )
            formulation_node.save()

            for ingredient in formulation.ingredients:
                ingredient_node = Ingredient(
                    external_id=ingredient.external_id,
                    formulation_name=ingredient.formulation_name,
                )
                ingredient_node.save()
                formulation_node.has_ingredient.connect(ingredient_node)

                ingredient_node.has_substance.connect(
                    ActiveSubstanceRoot.nodes.get(uid=ingredient.active_substance_uid)
                )

                if ingredient.strength_uid:
                    ingredient_node.has_strength_value.connect(
                        NumericValueWithUnitRoot.nodes.get(uid=ingredient.strength_uid)
                    )

                if ingredient.half_life_uid:
                    ingredient_node.has_half_life.connect(
                        NumericValueWithUnitRoot.nodes.get(uid=ingredient.half_life_uid)
                    )

                for lag_time_uid in ingredient.lag_time_uids:
                    ingredient_node.has_lag_time.connect(
                        LagTimeRoot.nodes.get(uid=lag_time_uid)
                    )

            value_node.has_formulation.connect(formulation_node)

        return value_node

    def _has_data_changed(self, ar: _AggregateRootType, value: VersionValue) -> bool:
        was_parent_data_modified = super()._has_data_changed(ar=ar, value=value)

        are_props_changed = False
        dosage_form_nodes = [
            node.has_selected_term.get() for node in value.has_dosage_form.all()
        ]
        roa_nodes = [
            node.has_selected_term.get()
            for node in value.has_route_of_administration.all()
        ]
        are_rels_changed = sorted(ar.concept_vo.dosage_form_uids) != sorted(
            [val.uid for val in dosage_form_nodes]
        ) or sorted(ar.concept_vo.route_of_administration_uids) != sorted(
            [val.uid for val in roa_nodes]
        )

        current_formulations = self._get_formulations_from_value_node(value=value)

        return (
            was_parent_data_modified
            or are_props_changed
            or are_rels_changed
            or DeepDiff(
                current_formulations, ar.concept_vo.formulations, ignore_order=True
            )
        )

    def _get_formulations_from_value_node(
        self, value: VersionValue
    ) -> list[FormulationVO]:
        return [
            FormulationVO.from_repository_values(
                external_id=form.external_id,
                ingredients=[
                    IngredientVO.from_repository_values(
                        active_substance_uid=ingredient.has_substance.get().uid,
                        formulation_name=ingredient.formulation_name,
                        external_id=ingredient.external_id,
                        strength_uid=getattr(
                            ingredient.has_strength_value.get_or_none(), "uid", None
                        ),
                        half_life_uid=getattr(
                            ingredient.has_half_life.get_or_none(), "uid", None
                        ),
                        lag_time_uids=[
                            lag_time.uid for lag_time in ingredient.has_lag_time.all()
                        ],
                    )
                    for ingredient in form.has_ingredient.all()
                ],
            )
            for form in value.has_formulation.all()
        ]

    def _get_formulation_ingredients(
        self,
        formulation,
        formulation_ingredients,
        ingredient_substances,
        ingredient_strengths,
        ingredient_half_lives,
        ingredient_lag_times,
    ) -> list[IngredientVO]:
        ingredients = [
            x["fi_rel"].end_node
            for x in formulation_ingredients
            if x["fi_rel"].start_node.element_id == formulation.element_id
        ]

        return [
            IngredientVO.from_repository_values(
                active_substance_uid=next(
                    x["ingr_substance_rel"].end_node.get("uid")
                    for x in ingredient_substances
                    if x["ingr_substance_rel"].start_node.element_id
                    == ingredient_node.element_id
                ),
                formulation_name=ingredient_node.get("formulation_name"),
                external_id=ingredient_node.get("external_id"),
                strength_uid=next(
                    (
                        x["ingr_strength_rel"].end_node.get("uid")
                        for x in ingredient_strengths
                        if x["ingr_strength_rel"].start_node.element_id
                        == ingredient_node.element_id
                    ),
                    None,
                ),
                half_life_uid=next(
                    (
                        x["ingr_half_life_rel"].end_node.get("uid")
                        for x in ingredient_half_lives
                        if x["ingr_half_life_rel"].start_node.element_id
                        == ingredient_node.element_id
                    ),
                    None,
                ),
                lag_time_uids=[
                    x["ingr_lag_time_rel"].end_node.get("uid")
                    for x in ingredient_lag_times
                    if x["ingr_lag_time_rel"].start_node.element_id
                    == ingredient_node.element_id
                ],
            )
            for ingredient_node in ingredients
        ]

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> PharmaceuticalProductAR:
        major, minor = input_dict["version"].split(".")
        ar = PharmaceuticalProductAR.from_repository_values(
            uid=input_dict["uid"],
            concept_vo=PharmaceuticalProductVO.from_repository_values(
                external_id=input_dict.get("external_id"),
                dosage_form_uids=[
                    dosage_form.get("uid")
                    for dosage_form in input_dict.get("dosage_forms")
                ],
                route_of_administration_uids=[
                    routes_of_administration.get("uid")
                    for routes_of_administration in input_dict.get(
                        "routes_of_administration"
                    )
                ],
                formulations=[
                    FormulationVO.from_repository_values(
                        external_id=formulation.get("external_id"),
                        ingredients=self._get_formulation_ingredients(
                            formulation=formulation,
                            formulation_ingredients=input_dict.get(
                                "formulation_ingredients"
                            ),
                            ingredient_substances=input_dict.get(
                                "ingredient_substances"
                            ),
                            ingredient_strengths=input_dict.get("ingredient_strengths"),
                            ingredient_half_lives=input_dict.get(
                                "ingredient_half_lives"
                            ),
                            ingredient_lag_times=input_dict.get("ingredient_lag_times"),
                        ),
                    )
                    for formulation in input_dict["formulations"]
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
                end_date=convert_to_datetime(value=input_dict.get("end_date")),
                major_version=int(major),
                minor_version=int(minor),
            ),
        )
        return ar

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> PharmaceuticalProductAR:
        formulation_nodes = value.has_formulation.all()
        dosage_form_nodes = [
            node.has_selected_term.get() for node in value.has_dosage_form.all()
        ]
        roa_nodes = [
            node.has_selected_term.get()
            for node in value.has_route_of_administration.all()
        ]

        ar = PharmaceuticalProductAR.from_repository_values(
            uid=root.uid,
            concept_vo=PharmaceuticalProductVO.from_repository_values(
                external_id=value.external_id,
                dosage_form_uids=[x.uid for x in dosage_form_nodes],
                route_of_administration_uids=[x.uid for x in roa_nodes],
                formulations=[
                    FormulationVO.from_repository_values(
                        external_id=formulation_node.external_id,
                        ingredients=[
                            IngredientVO.from_repository_values(
                                active_substance_uid=getattr(
                                    ingredient.has_substance.get_or_none(), "uid"
                                ),
                                formulation_name=ingredient.formulation_name,
                                external_id=ingredient.external_id,
                                strength_uid=getattr(
                                    ingredient.has_strength_value.get_or_none(),
                                    "uid",
                                    None,
                                ),
                                half_life_uid=getattr(
                                    ingredient.has_half_life.get_or_none(),
                                    "uid",
                                    None,
                                ),
                                lag_time_uids=[
                                    lag_time.uid
                                    for lag_time in ingredient.has_lag_time.all()
                                ],
                            )
                            for ingredient in formulation_node.has_ingredient.all()
                        ],
                    )
                    for formulation_node in formulation_nodes
                ],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )
        return ar

    def specific_alias_clause(self, **kwargs) -> str:
        return """
            WITH *,
                [(concept_value)-[:HAS_DOSAGE_FORM]->(df_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(dosage_form:CTTermRoot) | dosage_form] AS dosage_forms,
                [(concept_value)-[:HAS_ROUTE_OF_ADMINISTRATION]->(roa_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(route_of_administration:CTTermRoot) | route_of_administration] AS routes_of_administration,
                [(concept_value)-[:HAS_FORMULATION]->(formulation:IngredientFormulation) | formulation] as formulations,
                [(concept_value)-[:HAS_FORMULATION]->(formulation:IngredientFormulation)-[fi_rel:HAS_INGREDIENT]->(ingredient:Ingredient) | {ingredient:ingredient, fi_rel:fi_rel}] as formulation_ingredients,
                [(concept_value)-[:HAS_FORMULATION]->(formulation:IngredientFormulation)-[:HAS_INGREDIENT]->(ingredient:Ingredient)-[ingr_substance_rel:HAS_SUBSTANCE]->(active_substance:ActiveSubstanceRoot) | {active_substance:active_substance, ingr_substance_rel:ingr_substance_rel}] as ingredient_substances,
                [(concept_value)-[:HAS_FORMULATION]->(formulation:IngredientFormulation)-[:HAS_INGREDIENT]->(ingredient:Ingredient)-[ingr_strength_rel:HAS_STRENGTH_VALUE]->(strength:NumericValueWithUnitRoot) | {strength:strength, ingr_strength_rel:ingr_strength_rel}] as ingredient_strengths,
                [(concept_value)-[:HAS_FORMULATION]->(formulation:IngredientFormulation)-[:HAS_INGREDIENT]->(ingredient:Ingredient)-[ingr_half_life_rel:HAS_HALF_LIFE]->(half_life:NumericValueWithUnitRoot) | {half_life:half_life, ingr_half_life_rel:ingr_half_life_rel}] as ingredient_half_lives,
                [(concept_value)-[:HAS_FORMULATION]->(formulation:IngredientFormulation)-[:HAS_INGREDIENT]->(ingredient:Ingredient)-[ingr_lag_time_rel:HAS_LAG_TIME]->(lag_time:LagTimeRoot) | {lag_time:lag_time, ingr_lag_time_rel:ingr_lag_time_rel}] as ingredient_lag_times,

                // Flat string aliases for wildcard filtering across linked entities
                reduce(s='', x IN [(concept_value)-[:HAS_FORMULATION]->(:IngredientFormulation)-[:HAS_INGREDIENT]->(pp_ingr:Ingredient)-[:HAS_SUBSTANCE]->(pp_as:ActiveSubstanceRoot)-[:LATEST]->(pp_as_val:ActiveSubstanceValue) 
                        | coalesce(pp_as_val.inn, pp_as_val.long_number, pp_as_val.short_number, pp_as_val.analyte_number, '?') + ' ' 
                        + coalesce(pp_ingr.formulation_name, '') 
                        + coalesce(' (' + head([(pp_ingr)-[:HAS_STRENGTH_VALUE]->(pp_str:NumericValueWithUnitRoot)-[:LATEST]->(pp_str_val:NumericValueWithUnitValue)-[:HAS_UNIT_DEFINITION]->(pp_unit:UnitDefinitionRoot)-[:LATEST]->(pp_unit_val:UnitDefinitionValue) | CASE WHEN pp_str_val.value = toInteger(pp_str_val.value) THEN toString(toInteger(pp_str_val.value)) ELSE toString(pp_str_val.value) END + ' ' + pp_unit_val.name]) + ')', '')] | s + CASE WHEN s = '' THEN '' ELSE ', ' END + x) AS _search_derived_pp_name,
                reduce(s='', x IN [(concept_value)-[:HAS_DOSAGE_FORM]->(df_ctx2:CTTermContext)-[:HAS_SELECTED_TERM]->(df2:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(df2_val:CTTermNameValue) | df2_val.name] | s + ' ' + coalesce(x, '')) AS _search_dosage_form_names,
                reduce(s='', x IN [(concept_value)-[:HAS_ROUTE_OF_ADMINISTRATION]->(roa_ctx2:CTTermContext)-[:HAS_SELECTED_TERM]->(roa2:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(roa2_val:CTTermNameValue) | roa2_val.name] | s + ' ' + coalesce(x, '')) AS _search_route_of_admin_names,
                reduce(s='', x IN [(concept_value)-[:HAS_FORMULATION]->(:IngredientFormulation)-[:HAS_INGREDIENT]->(:Ingredient)-[:HAS_SUBSTANCE]->(as3:ActiveSubstanceRoot)-[:LATEST]->(as3_val:ActiveSubstanceValue) | as3_val.inn] | s + ' ' + coalesce(x, '')) AS _search_active_substance_inns,
                reduce(s='', x IN [(concept_value)-[:HAS_FORMULATION]->(:IngredientFormulation)-[:HAS_INGREDIENT]->(:Ingredient)-[:HAS_SUBSTANCE]->(as4:ActiveSubstanceRoot)-[:LATEST]->(as4_val:ActiveSubstanceValue) | as4_val.short_number] | s + ' ' + coalesce(x, '')) AS _search_active_substance_short_numbers,
                reduce(s='', x IN [(concept_value)-[:HAS_FORMULATION]->(:IngredientFormulation)-[:HAS_INGREDIENT]->(:Ingredient)-[:HAS_SUBSTANCE]->(as4:ActiveSubstanceRoot)-[:LATEST]->(as4_val:ActiveSubstanceValue) | as4_val.long_number] | s + ' ' + coalesce(x, '')) AS _search_active_substance_long_numbers,
                reduce(s='', x IN [(concept_value)-[:HAS_FORMULATION]->(:IngredientFormulation)-[:HAS_INGREDIENT]->(:Ingredient)-[:HAS_SUBSTANCE]->(as5:ActiveSubstanceRoot)-[:LATEST]->(as5_val:ActiveSubstanceValue) | as5_val.analyte_number] | s + ' ' + coalesce(x, '')) AS _search_active_substance_analyte_numbers,
                reduce(s='', x IN [(concept_value)-[:HAS_FORMULATION]->(:IngredientFormulation)-[:HAS_INGREDIENT]->(:Ingredient)-[:HAS_SUBSTANCE]->(as6:ActiveSubstanceRoot)-[:LATEST]->(as6_val:ActiveSubstanceValue) | as6_val.external_id] | s + ' ' + coalesce(x, '')) AS _search_active_substance_external_ids
                """
