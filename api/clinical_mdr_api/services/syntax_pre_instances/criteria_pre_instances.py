from neomodel import db

from clinical_mdr_api.domain_repositories.syntax_pre_instances.criteria_pre_instance_repository import (
    CriteriaPreInstanceRepository,
)
from clinical_mdr_api.domains.syntax_pre_instances.criteria_pre_instance import (
    CriteriaPreInstanceAR,
)
from clinical_mdr_api.models.syntax_pre_instances.criteria_pre_instance import (
    CriteriaPreInstance,
    CriteriaPreInstanceVersion,
)
from clinical_mdr_api.services.syntax_instances.criteria import CriteriaService


class CriteriaPreInstanceService(CriteriaService[CriteriaPreInstanceAR]):
    aggregate_class = CriteriaPreInstanceAR
    repository_interface = CriteriaPreInstanceRepository
    version_class = CriteriaPreInstanceVersion
    template_uid_property = "criteria_template_uid"

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CriteriaPreInstanceAR
    ) -> CriteriaPreInstance:
        return CriteriaPreInstance.from_criteria_pre_instance_ar(item_ar)

    def create_ar_from_input_values(
        self,
        template,
        generate_uid_callback=None,
        study_uid: str | None = None,
        template_uid: str | None = None,
        include_study_endpoints: bool = False,
    ) -> CriteriaPreInstanceAR:
        item_ar = super().create_ar_from_input_values(
            template=template,
            generate_uid_callback=generate_uid_callback,
            next_available_sequence_id_callback=self.repository.next_available_sequence_id,
            study_uid=study_uid,
            template_uid=template_uid,
            include_study_endpoints=include_study_endpoints,
        )

        (
            indications,
            categories,
            sub_categories,
            _,
            _,
            _,
            template_type,
        ) = self._get_indexings(
            template,
            self.repository.get_template_type_uid(
                self._repos.criteria_template_repository.root_class.nodes.get_or_none(
                    uid=template_uid
                )
            ),
        )

        item_ar._type = template_type
        item_ar._indications = indications
        item_ar._categories = categories
        item_ar._subcategories = sub_categories

        return item_ar

    @db.transaction
    def create_new_version(self, uid: str) -> CriteriaPreInstance:
        item = self.repository.find_by_uid(uid, for_update=True)
        item._create_new_version(author_id=self.author_id)
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def edit_draft(self, uid, template):
        item = self.repository.find_by_uid(uid, for_update=True)
        parameter_terms = self._create_parameter_entries(
            template, template_uid=item.template_uid
        )

        template_vo = self.parametrized_template_vo_class.from_input_values_2(
            template_uid=item.template_uid,
            template_sequence_id=item.template_sequence_id,
            parameter_terms=parameter_terms,
            library_name=item.template_library_name,
            get_final_template_vo_by_template_uid_callback=self._get_template_vo_by_template_uid,
        )
        item.edit_draft(
            author_id=self.author_id,
            change_description=template.change_description,
            template=template_vo,
            guidance_text=template.guidance_text,
        )

        self.repository.save(item)

        return self._transform_aggregate_root_to_pydantic_model(item)
