from deepdiff import DeepDiff

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
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
from clinical_mdr_api.domains._utils import ObjectStatus
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
from common.utils import convert_to_datetime


class PharmaceuticalProductRepository(ConceptGenericRepository):
    root_class = PharmaceuticalProductRoot
    value_class = PharmaceuticalProductValue
    return_model = PharmaceuticalProduct

    def _create_new_value_node(self, ar: _AggregateRootType) -> VersionValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.save()

        for uid in ar.concept_vo.dosage_form_uids:
            value_node.has_dosage_form.connect(CTTermRoot.nodes.get(uid=uid))

        for uid in ar.concept_vo.route_of_administration_uids:
            value_node.has_route_of_administration.connect(
                CTTermRoot.nodes.get(uid=uid)
            )

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

        are_rels_changed = sorted(ar.concept_vo.dosage_form_uids) != sorted(
            [val.uid for val in value.has_dosage_form.all()]
        ) or sorted(ar.concept_vo.route_of_administration_uids) != sorted(
            [val.uid for val in value.has_route_of_administration.all()]
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
                    (
                        x["ingr_substance_rel"].end_node.get("uid")
                        for x in ingredient_substances
                        if x["ingr_substance_rel"].start_node.element_id
                        == ingredient_node.element_id
                    ),
                    None,
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
        self, input_dict: dict
    ) -> PharmaceuticalProductAR:
        major, minor = input_dict.get("version").split(".")
        ar = PharmaceuticalProductAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=PharmaceuticalProductVO.from_repository_values(
                external_id=input_dict.get("external_id"),
                dosage_form_uids=list(
                    map(lambda x: x.get("uid"), input_dict.get("dosage_forms"))
                ),
                route_of_administration_uids=list(
                    map(
                        lambda x: x.get("uid"),
                        input_dict.get("routes_of_administration"),
                    )
                ),
                formulations=list(
                    map(
                        lambda x: FormulationVO.from_repository_values(
                            external_id=x.get("external_id"),
                            ingredients=self._get_formulation_ingredients(
                                formulation=x,
                                formulation_ingredients=input_dict.get(
                                    "formulation_ingredients"
                                ),
                                ingredient_substances=input_dict.get(
                                    "ingredient_substances"
                                ),
                                ingredient_strengths=input_dict.get(
                                    "ingredient_strengths"
                                ),
                                ingredient_half_lives=input_dict.get(
                                    "ingredient_half_lives"
                                ),
                                ingredient_lag_times=input_dict.get(
                                    "ingredient_lag_times"
                                ),
                            ),
                        ),
                        input_dict.get("formulations"),
                    )
                ),
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
                end_date=convert_to_datetime(value=input_dict.get("end_date")),
                major_version=int(major),
                minor_version=int(minor),
            ),
        )
        return ar

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> PharmaceuticalProductAR:
        formulation_nodes = value.has_formulation.all()

        ar = PharmaceuticalProductAR.from_repository_values(
            uid=root.uid,
            concept_vo=PharmaceuticalProductVO.from_repository_values(
                external_id=value.external_id,
                dosage_form_uids=[x.uid for x in value.has_dosage_form.all()],
                route_of_administration_uids=[
                    x.uid for x in value.has_route_of_administration.all()
                ],
                formulations=list(
                    map(
                        lambda x: FormulationVO.from_repository_values(
                            external_id=x.external_id,
                            ingredients=[
                                IngredientVO.from_repository_values(
                                    active_substance_uid=getattr(
                                        ingredient.has_substance.get_or_none(),
                                        "uid",
                                        None,
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
                                for ingredient in x.has_ingredient.all()
                            ],
                        ),
                        formulation_nodes,
                    )
                ),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )
        return ar

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
        return """
            WITH *,
                [(concept_value)-[:HAS_DOSAGE_FORM]->(dosage_form:CTTermRoot) | dosage_form] AS dosage_forms,
                [(concept_value)-[:HAS_ROUTE_OF_ADMINISTRATION]->(route_of_administration:CTTermRoot) | route_of_administration] AS routes_of_administration,
                [(concept_value)-[:HAS_FORMULATION]->(formulation:IngredientFormulation) | formulation] as formulations,
                [(concept_value)-[:HAS_FORMULATION]->(formulation:IngredientFormulation)-[fi_rel:HAS_INGREDIENT]->(ingredient:Ingredient) | {ingredient:ingredient, fi_rel:fi_rel}] as formulation_ingredients,
                [(concept_value)-[:HAS_FORMULATION]->(formulation:IngredientFormulation)-[:HAS_INGREDIENT]->(ingredient:Ingredient)-[ingr_substance_rel:HAS_SUBSTANCE]->(active_substance:ActiveSubstanceRoot) | {active_substance:active_substance, ingr_substance_rel:ingr_substance_rel}] as ingredient_substances,
                [(concept_value)-[:HAS_FORMULATION]->(formulation:IngredientFormulation)-[:HAS_INGREDIENT]->(ingredient:Ingredient)-[ingr_strength_rel:HAS_STRENGTH_VALUE]->(strength:NumericValueWithUnitRoot) | {strength:strength, ingr_strength_rel:ingr_strength_rel}] as ingredient_strengths,
                [(concept_value)-[:HAS_FORMULATION]->(formulation:IngredientFormulation)-[:HAS_INGREDIENT]->(ingredient:Ingredient)-[ingr_half_life_rel:HAS_HALF_LIFE]->(half_life:NumericValueWithUnitRoot) | {half_life:half_life, ingr_half_life_rel:ingr_half_life_rel}] as ingredient_half_lives,
                [(concept_value)-[:HAS_FORMULATION]->(formulation:IngredientFormulation)-[:HAS_INGREDIENT]->(ingredient:Ingredient)-[ingr_lag_time_rel:HAS_LAG_TIME]->(lag_time:LagTimeRoot) | {lag_time:lag_time, ingr_lag_time_rel:ingr_lag_time_rel}] as ingredient_lag_times
                """
